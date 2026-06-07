# 使用文档 - Travel Route Engine

> 这份文档教你从拿到代码到完整跑起来。
> 想看架构设计和为什么这么做,看 `README_DESIGN.md`。

---

## 0. 你需要准备的东西

- **Python 3.10 或更高** (用了 `list[int]` 这种新语法)
- **DeepSeek API Key** (不需要也能跑,会走降级模式)
- (可选) **高德 API Key**: 不填就用估算的通勤时长

---

## 1. 一次跑通的完整步骤

### Step 1: 进入项目目录

```bash
cd travel_route_engine
```

### Step 2: 装依赖

强烈建议用虚拟环境,避免污染系统 Python:

```bash
python3 -m venv .venv
source .venv/bin/activate         # macOS / Linux
# .venv\Scripts\activate          # Windows

pip install -r requirements.txt
```

装完会有: langgraph, langchain-core, pydantic, fastapi, uvicorn, httpx, numpy, scikit-learn, python-dotenv, openai

### Step 3: 配置环境变量

```bash
cp .env.example .env
```

打开 `.env`,**把你的 DeepSeek API Key 填进 `DEEPSEEK_API_KEY=` 后面**:

```
DEEPSEEK_API_KEY=sk-你的key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro

AMAP_API_KEY=         # 留空就用 Mock 通勤,不影响功能
LOG_LEVEL=INFO
PROFILE_STORE_PATH=./data/user_profiles.json
```

### Step 4: 先跑算法层验证 (不调 LLM,快,2 秒内)

```bash
python demo.py --no-llm
```

应该看到:
- 可达半径、时间窗口、可排 POI 数
- 候选池大小(20-30 之间)
- 候选路线数(3-8 条)
- **降级模式的 Top-3**(标签是模板化的"精华首选/轻松漫游/小众惊喜")
- 一条 system 兜底说明

**如果这步报错**,后面的步骤都白搭,先看下方"排错"章节。

### Step 5: 跑完整版 (含 4 Agent 辩论,需要 LLM,大约 15-25 秒)

```bash
python demo.py
```

应该看到:
- 算法层产出 8-12 条候选路线
- **辩论 transcript**(体验派/实用派/懂你派各发言 1-2 次,主持人最后归类)
- Top-3 带 LLM 生成的 15-25 字描述
- 主持人小结

如果跑成功了,**核心引擎已经能用了**。

### Step 6: (可选) 起 API 服务

```bash
uvicorn main:app --reload --port 8000
```

打开浏览器访问 `http://localhost:8000/docs` 可以看到 Swagger UI,可以直接在网页上调接口测。

### Step 7: (可选) 跑 Eval

```bash
python evals/runners/run_eval.py --no-llm
```

5 个 case 应该 4-5 个通过(LLM 关闭时主持人降级可能影响个别 case 通过)。

```bash
python evals/runners/run_eval.py
```

加上 LLM 跑完整 eval,大约 1-2 分钟。

---

## 2. 几个常用入口

### 2.1 改 demo 的输入测不同场景

打开 `demo.py`,改 `initial` 字典里的字段:

```python
initial = {
    "user_id": "demo_user",            # 改这个测不同用户的画像积累
    "intent": {
        "origin_lat": 31.2280,         # 出发点经纬度
        "origin_lng": 121.4490,
        "time_slot": "下午",            # 随时 / 下午 / 全天
        "people_count": 2,             # 1 / 2 / 3-4 / 5+
        "transport_mode": "transit",   # walk / transit / drive
        "moods": ["静下来"],            # 大类
        "sub_categories": ["窗边咖啡"], # 小类,可以留空让 RAG 召回
        "free_text": "想找个安静的下午", # 自由文本,RAG 会用
        "budget_per_person": 200,
    },
    "weather": {"condition": "晴"},    # 晴 / 小雨 / 大雨 / 暴雨
}
```

### 2.2 测画像累积效果

```bash
# 第一次:冷启动,用默认权重
python demo.py --user-id alice --feedback

# 再跑两次,total_plans 达到 3 后画像生效
python demo.py --user-id alice --feedback
python demo.py --user-id alice --feedback

# 看画像文件
cat data/user_profiles.json
```

`--feedback` 会模拟"用户选了第一条 + 评分 5 星"。多跑几次能看到 agent_weights 在动。

### 2.3 在代码里直接调

```python
from graph.builder import get_planning_graph

graph = get_planning_graph()
result = graph.invoke({
    "user_id": "alice",
    "intent": {
        "origin_lat": 31.2280,
        "origin_lng": 121.4490,
        "time_slot": "下午",
        "people_count": 2,
        "people_group": "情侣",
        "transport_mode": "walk",
        "moods": [],
        "sub_categories": ["窗边咖啡", "图书馆"],
        "free_text": "",
    },
    "weather": {"condition": "晴"},
    "follow_up_rounds": 0,
    "candidate_pool": [],
    "candidate_routes": [],
    "debate_transcript": [],
    "top_routes": [],
})

for r in result["top_routes"]:
    print(r["label"], r["summary"])
```

---

## 3. API 用法

启动: `uvicorn main:app --reload --port 8000`

### POST /plan

```bash
curl -X POST http://localhost:8000/plan \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "intent": {
      "origin_lat": 31.2280,
      "origin_lng": 121.4490,
      "time_slot": "下午",
      "people_count": 2,
      "transport_mode": "transit",
      "moods": ["静下来"],
      "sub_categories": ["窗边咖啡", "图书馆"],
      "free_text": "想找个安静的下午"
    },
    "weather": {"condition": "晴"}
  }'
```

返回:

```json
{
  "top_routes": [
    {
      "route_id": "route_zone_0",
      "label": "精华首选",
      "summary": "在静安书店和咖啡之间慢慢游走",
      "stops": [
        {
          "poi_id": "p003",
          "poi_name": "静雅书局",
          "arrival_time": "13:00",
          "leave_time": "14:00",
          "stay_minutes": 60,
          "transit_to_next_minutes": 8
        }
      ],
      "total_commute_minutes": 28,
      "quality_score": 0.847,
      "debate_highlights": [...]
    }
  ],
  "debate_transcript": [
    {
      "agent": "experience",
      "persona_label": "体验派",
      "round": 1,
      "content": "这条路上的静雅书局好评率 94%,值得专程一去..."
    }
  ],
  "pre_brief": "实用派看重通勤,但体验派以好评率说服了大家",
  "llm_degraded": false
}
```

### POST /feedback

```bash
curl -X POST http://localhost:8000/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "alice",
    "user_choice_route_id": "route_zone_0",
    "user_deleted_poi_ids": [],
    "user_rating": 5,
    "top_routes": [...],
    "debate_transcript": [...]
  }'
```

`top_routes` 和 `debate_transcript` 就是 `/plan` 返回的原样回传。

### GET /health

```bash
curl http://localhost:8000/health
```

返回:

```json
{
  "ok": true,
  "llm_available": true,
  "llm_model": "deepseek-v4-pro",
  "commute_provider": "MockCommute",
  "amap_configured": false
}
```

启动后先打这个接口,确认 `llm_available: true` 再去 `/plan`。

### GET /pois

返回 36 个 mock POI 的全量数据,方便前端调试。

---

## 4. 排错

### 4.1 `ModuleNotFoundError: No module named 'graph'`

**原因**: 你不在项目根目录,或者目录里没有 `__init__.py`。

**解决**:
```bash
cd travel_route_engine     # 确保在根目录
ls graph/__init__.py       # 确认有这个文件,没有就 touch graph/__init__.py
```

每个子包目录都要有 `__init__.py`,包括: `algorithm/`、`providers/`、`profile/`、`agents/`、`graph/`、`api/`、`evals/scorers/`、`evals/runners/`。

如果是空的也要在,文件存在比内容更重要。

### 4.2 `ImportError: cannot import name 'X' from 'profile'`

**原因**: Python 标准库里有个 `profile` 模块(性能分析器),如果你的 PYTHONPATH 顺序不对会撞名。

**解决**: 在项目根目录跑,不要从 `profile/` 目录里跑。如果还撞,把 `profile/` 改名为 `user_profile/` 并全局替换 import。

### 4.3 `RuntimeError: DEEPSEEK_API_KEY 未设置`

**原因**: `.env` 没创建,或 key 没填,或没生效。

**解决**:
```bash
ls -la .env                              # 确认文件存在
cat .env | grep DEEPSEEK_API_KEY         # 确认填了
# 如果在 IDE 里跑,确认 IDE 加载了 .env(PyCharm 需要装 EnvFile 插件)
```

不想配 key 就用 `--no-llm` 模式跑,功能完整,只是降级。

### 4.4 `openai.AuthenticationError: 401`

**原因**: Key 错了 / 过期 / 用错 base_url。

**解决**:
- 确认 `DEEPSEEK_BASE_URL=https://api.deepseek.com`(不是 openai.com)
- 去 DeepSeek 后台确认 key 还有效

### 4.5 `json.JSONDecodeError: Expecting value`

**原因**: DeepSeek 返回的不是合法 JSON。

**解决**:
- 看下 `LOG_LEVEL=DEBUG` 打印的原始 content,有可能是 prompt 没写好被它当对话回了
- 已经强制 `response_format={"type": "json_object"}` 兜底,如果还出问题大概率是网络问题重试一下

### 4.6 跑完只有 0-1 条路线返回

**原因**:
- 出发地经纬度错了,可达圈内一个 POI 都没有
- 类别选得太偏(比如选了"特色景区"但 mock 数据里只有 5 个,全是户外又赶上暴雨)
- 时间窗口太短(`time_slot=随时` 但当前已是晚上 20:00)

**排查方法**: 看 demo 输出的"候选池大小"。
- 候选池 < 5 → 放宽可达圈(改 `transport_mode=transit` 或 `drive`)
- 候选池 ≥ 10 但路线 < 3 → 类别选得太互斥,试试只选 1-2 个类

### 4.7 辩论很慢 (>30s)

**原因**: DeepSeek 偶尔会慢,或 Round 2 跑得太满。

**解决**:
- 调用 `run_debate` 时传 `enable_round2=False`,只跑一轮
- 在 `agents/debate.py` 里把 Round 1 的 `temperature` 从 0.7 调到 0.5,输出更确定
- 临时降级测试用 `--no-llm`

### 4.8 同一个用户跑多次,画像没变化

**原因**: 冷启动保护(`total_plans < 3` 时画像不生效)。

**解决**: 加 `--feedback` 跑至少 3 次,从第 4 次开始画像才会影响评分。

```bash
for i in 1 2 3 4; do python demo.py --user-id alice --feedback; done
```

### 4.9 数据文件没找到

**原因**: 路径相对的,在哪儿跑很重要。

**解决**: 永远在项目根目录(`travel_route_engine/`)跑,别 cd 进子目录。

---

## 5. 测试不同场景的 quick recipe

把这些直接抄到 `demo.py` 的 `initial.intent` 里试:

### 静安 citywalk
```python
"transport_mode": "walk",
"moods": ["静下来"],
"sub_categories": ["窗边咖啡", "图书馆"],
"free_text": "梧桐道下走走",
```

### 雨天室内 (天气改 `"大雨"`)
```python
"transport_mode": "transit",
"moods": ["休闲娱乐"],
"sub_categories": [],
"free_text": "下雨天找点室内的事做",
```

### 大队聚会 (5 人 + 剧本杀)
```python
"people_count": 5,
"transport_mode": "drive",
"moods": ["休闲娱乐"],
"sub_categories": ["剧本杀", "密室逃脱"],
"budget_per_person": 150,
```

### 健康禁忌 (膝盖不好)
```python
"transport_mode": "transit",
"moods": ["热门打卡"],
"sub_categories": [],
"free_text": "膝盖不好,少走点路",
"health_constraints": ["膝盖不好"],
```

### 锚点 (今晚必须去外滩)
```python
"transport_mode": "drive",
"moods": ["热门打卡"],
"sub_categories": ["网红地标"],
"locked_poi_ids": ["p018"],   # 外滩
```

---

## 6. 下一步

跑通之后,你可能想:

- **接前端**: HTML 原型的 chips → POST /plan 的 intent。返回的 `top_routes[i].stops` 直接绘制到 p3/p4 页面的路线卡 + 地图。
- **接高德**: 填 `AMAP_API_KEY` 到 `.env`,实现 `providers/commute.py` 里的 `_call_amap` 方法(我已经留好接口位置,httpx 调用即可)。
- **扩 POI 库**: 编辑 `data/mock_pois.json`,加新 POI。schema 看任意一条参考。
- **扩 Eval**: 往 `evals/golden_set/sample.json` 加新 case,把验证范围从 5 扩到 30+。

详细的架构、设计决策、为什么这么做,看 `README_DESIGN.md`。
