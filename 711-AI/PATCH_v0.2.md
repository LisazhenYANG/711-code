# PATCH v0.2 - 真实路网导航 + 餐厅推荐 + Mock 取号/预订

> 在你 `139dddd` 这个 commit 之上的增量。所有改动已经基于你最新的代码,直接覆盖即可。

---

## 一、文件清单

### 新文件 (5 个)

| 路径 | 用途 |
|------|------|
| `providers/places.py` | 高德 place/around 客户端 + 离线 mock 餐厅库 |
| `providers/booking_mock.py` | 取号 + 预订桌位状态机,JSON 文件持久化 |
| `algorithm/food_recommend.py` | 餐厅推荐核心算法 - 锚点选择、硬过滤、菜系分桶、Top 3 |
| `data/mock_restaurants.json` | 149 家虹口区 mock 餐厅(15 个菜系)|
| `_gen_restaurants.py` | 餐厅数据生成器(一次性脚本,以后改餐厅数据用)|

### 修改文件 (5 个)

| 路径 | 改了什么 |
|------|---------|
| `state.py` | Route + RouteStop 加新字段(navigation_to_next, food_recommendations 等) |
| `providers/commute.py` | 实现 AmapCommute._call_amap 调用高德 direction API,返回 steps + polyline |
| `graph/nodes.py` | 加 `node_real_navigation` + `node_food_recommend`,RouteStop 加 lat/lng |
| `graph/builder.py` | 主图加挂两个新节点 |
| `main.py` | 加 8 个 booking 相关 endpoint |
| `demo.py` | 演示新输出 |

### 自动产生的运行时文件 (.gitignore 加进去)

```
data/booking_tickets.json   # mock 取号/预订状态持久化
data/user_profiles.json     # 已存在
```

---

## 二、流程图变化

**旧主图**:
```
intent → profile_load → reachable → time_slots → candidates
       → score → cluster_and_pool → route_gen → filter_rank
       → debate → END
```

**新主图**(末尾加两个节点,只为 Top-3 跑):
```
intent → ... → debate → real_navigation → food_recommend → END
```

`real_navigation` 调用次数: Top-3 × 每条 2-4 段 = 6-12 次 Amap direction
`food_recommend` 调用次数: Top-3 × 1-2 个 meal_block = 3-6 次 Amap place/around

每次规划 Amap 调用总量 **10~18 次**(只在 Top-3 出来后调)。

---

## 三、Top-3 路线输出新结构

```jsonc
{
  "route_id": "route_zone_0",
  "label": "精华首选",
  "summary": "...",
  "stops": [
    {
      "poi_id": "HK001",
      "poi_name": "...",
      "lat": 31.265,                // 新
      "lng": 121.490,               // 新
      "arrival_time": "13:00",
      "leave_time": "14:30",
      "stay_minutes": 90,
      "transit_to_next_minutes": 12,
      "transit_to_next_mode": "walk",
      "transit_to_next_distance_km": 0.78,    // 新
      "navigation_to_next": {                 // 新 - 在 App 内自渲染用
        "total_distance_m": 781,
        "total_duration_s": 720,
        "polyline": "121.49,31.265;121.50,31.270;...",
        "steps": [
          {
            "instruction": "沿欧阳路向东步行 200 米",
            "distance_m": 200,
            "duration_s": 144,
            "polyline": "...",
            "road_name": "欧阳路",
            "action": "向东直行"
          }
        ],
        "transit_segments": [        // 公交模式专属
          {"type": "walking", ...},
          {"type": "bus", "line_name": "13路", "departure_stop": "...", ...}
        ]
      }
    }
  ],
  "navigation_enriched": true,      // 新
  "navigation_source": "amap",      // 新 - amap | mock
  "food_recommendations": [         // 新
    {
      "meal_block": "午餐",
      "block_time": "12:00-13:30",
      "anchor": {
        "type": "near_poi",
        "anchor_lat": 31.265,
        "anchor_lng": 121.490,
        "anchor_name": "...",
        "anchor_poi_id": "HK001"
      },
      "buckets": [
        {
          "cuisine": "本帮菜",
          "matched_loved": false,
          "bucket_top_score": 0.847,
          "restaurants": [
            {
              "id": "R001",
              "name": "老吉士(永和路店)",
              "cuisine": "本帮菜",
              "lat": 31.27, "lng": 121.489,
              "distance_m": 320,
              "rating": 4.6,
              "avg_price": 100,
              "supports_queue_ticket": true,
              "supports_table_booking": true,
              "max_party_size": 10,
              "current_queue": 8,           // 实时(mock)
              "queue_wait_minutes": 16.0,   // 实时(mock)
              "is_peak_hour": true,
              ...
            }
          ]
        }
      ],
      "empty_reason": null
    }
  ]
}
```

---

## 四、Booking API 一览

### 取号(立即排队)

```
POST /booking/queue
  body: {restaurant_id, user_id, people_count}
  resp: {ticket_no, queue_position_at_issue, estimated_wait_minutes,
         estimated_call_time, ...}

GET /booking/queue/{ticket_no}
  resp: {..., queue_position_now, estimated_wait_remaining_minutes,
         ready_to_call: false | "approaching" | true}
  说明: 自动按 (now - issued_at) × queue_speed 衰减位置

DELETE /booking/queue/{ticket_no}
POST /booking/queue/{ticket_no}/seat    # 标记已就座
```

### 预订指定时间

```
POST /booking/reservation
  body: {restaurant_id, user_id, people_count,
         reserve_for_time: "ISO 8601", special_requests}
  resp: {reservation_id, status: "confirmed" | "pending_restaurant_confirm",
         remind_at, arrive_window_start, arrive_window_end}
  说明: rating >= 4.7 的店"待商家确认"(10 分钟后自动 confirmed),
        其他直接 confirmed

GET /booking/reservation/{reservation_id}
  resp: {..., minutes_until_reservation, reminder_status}
        # reminder_status: "approaching" | "now" | None

DELETE /booking/reservation/{reservation_id}
```

### 用户活跃订单(沉浸模式用)

```
GET /bookings/user/{user_id}
  resp: {
    tickets: [...with ready_to_call computed...],
    reservations: [...with minutes_until_reservation computed...]
  }
```

### 餐厅查询(不取号)

```
GET /restaurants/{rid}/queue        # 实时队列状态
GET /restaurants                    # 全部 mock 餐厅
```

---

## 五、沉浸模式接入指引

本期不做实时推送,但所有数据点位都已经埋好。前端轮询 `GET /bookings/user/{user_id}`(频率 30 秒-1 分钟),按以下信号决策提醒:

| 信号 | 触发条件 | 用户感受 |
|------|---------|---------|
| `ticket.ready_to_call == "approaching"` | 队列剩 ≤ 2 桌 或 ≤ 5 分钟 | "快到号了,5 分钟内出现在 X 餐厅" |
| `ticket.ready_to_call == true` | queue_position_now == 0 | "叫到您的号了!" |
| `reservation.reminder_status == "approaching"` | 用餐时间前 5-30 分钟 | "30 分钟后用餐,出发!" |
| `reservation.reminder_status == "now"` | 用餐时间 ±5 分钟 | "已到用餐时间,商家正在等您" |
| `reservation` 自动转 `no_show` | 用餐时间过 15 分钟仍未 seated | 后台埋点 |

下一期把这个轮询接到 WebSocket / 服务端推送上即可,数据不动。

---

## 六、配置变化

`.env.example` 不需要改(`AMAP_API_KEY` 上次已经留好位置)。如果想用真实数据:

```bash
# 启用真实路网 + 真实餐厅
AMAP_API_KEY=你的高德 key

# 可选:改 booking 存储位置
BOOKING_STORE_PATH=./data/booking_tickets.json
```

---

## 七、如何应用

把所有新文件 + 修改文件按目录覆盖到你的仓库,然后:

```bash
# 验证语法和流程
python3 demo.py --no-llm --feedback --book

# 完整(需要 DeepSeek key)
python3 demo.py --feedback --book

# 启 API
uvicorn main:app --reload --port 8000

# 浏览器打开 http://localhost:8000/docs 看所有 endpoint
```

---

## 八、已知 trade-off / 后续可优化

1. **AmapCommute 一段一调** - 没做缓存,同一对坐标重复调会重复消耗。可以加一个 LRU 缓存到 `providers/commute.py`。
2. **餐厅推荐针对短路线会重复** - 比如 13:00-14:00 的路线,午餐和晚餐 block 锚点会落在同一个最后 POI 上,展示重复。可以在 food_recommend 里加去重:相同锚点 + 相同时段视为一份。
3. **健康禁忌目前只覆盖 3 种**(海鲜过敏/清真/素食),后续需要时按相同 pattern 扩展 `HEALTH_FILTERS` 字典。
4. **`loved_categories` 字段复用** - 餐厅推荐目前从 user_profile 的 `loved_categories` 读菜系偏好,但这个字段之前存的是 POI 小类(剧本杀/咖啡等)。重叠时(如"咖啡馆"既是 POI 也是菜系)能命中;但纯餐厅菜系(如"川菜")需要 profile/ema 也开始追踪。建议下次反馈写回时也把"用户选的餐厅菜系"写进 `loved_categories`,或单开 `loved_cuisines` 字段。
5. **convert_venues.py 跑过后** mock_pois.json 会被覆盖。我没动这个文件,虹口 240 POI 数据保持原样。
