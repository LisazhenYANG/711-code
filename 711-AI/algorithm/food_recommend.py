"""
餐厅推荐 - 锚点选择 + 硬过滤 + 软加权 + 菜系分桶 Top 3。

核心逻辑:
1. 遍历路线的 food_blocks_within(只取在用户时间窗口内的餐饮时段)
2. 对每个 food_block:
   - 锚点选择: 步行/公交 → 此时正在的 POI 周围;驾车 → 此时跨越的段中点
   - 调 places provider 拿候选(半径按交通方式调整)
   - 硬过滤: 预算 / 健康禁忌 / 营业状态 / disliked
   - 按菜系分桶
   - 每桶按 (评分 × 距离衰减 × 价格匹配 × 画像偏好) 排序,取 Top 3
   - 桶之间按"用户画像偏好菜系优先"排序

输出按食时段挂在 Route 上。
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional
from algorithm.geo import haversine_km
from providers.places import PlacesProvider
from providers.booking_mock import get_restaurant_current_queue

logger = logging.getLogger(__name__)


# 菜系到关键词的映射 - 调高德 around 时按菜系查
CUISINE_QUERY_KEYWORD = {
    "本帮菜": "本帮菜",
    "川菜": "川菜",
    "粤菜": "粤菜",
    "湘菜": "湘菜",
    "东北菜": "东北菜",
    "日料": "日料",
    "韩餐": "韩餐",
    "西餐": "西餐",
    "东南亚": "东南亚",
    "快餐": "快餐",
    "面食": "面食",
    "咖啡馆": "咖啡",
    "轻食": "轻食",
    "清真": "清真",
    "素食": "素食",
}


# 搜索半径(米)按交通方式分档
RADIUS_BY_MODE = {
    "walk": 600,        # 步行用户接受 5-8 分钟绕路
    "transit": 800,     # 公交用户稍宽
    "drive": 1500,      # 驾车 1.5 公里 ≈ 3-5 分钟
}


# 健康禁忌 → 餐厅过滤规则
HEALTH_FILTERS = {
    "海鲜过敏": lambda r: not r.get("has_seafood", False),
    "清真": lambda r: r.get("is_halal", False),
    "素食": lambda r: r.get("is_vegetarian_friendly", False),
    # "膝盖不好" / "孕妇" 等不影响餐厅,这里忽略
}


# ─────────────────────────────────────────────────────────────
#  锚点选择
# ─────────────────────────────────────────────────────────────


def _hhmm_to_float(hhmm: str) -> float:
    """'13:30' → 13.5"""
    h, m = hhmm.split(":")
    return int(h) + int(m) / 60.0


def find_anchor(
    route: dict,
    food_block: tuple[float, float],
    transport_mode: str,
) -> Optional[dict]:
    """
    给定一条路线 + 一个 food_block 时段,决定餐厅搜索的锚点。

    步行/公交 → 找用户在 food_block 起点时所处的 POI(到达了但未离开)
                或最近的 POI(若在通勤途中,取下一站 POI)
    驾车      → 同样找该时段用户最可能在的段中点,锚点是经纬度坐标

    返回:
        {
          "type": "near_poi" | "along_segment",
          "anchor_lat": ..., "anchor_lng": ...,
          "anchor_name": "...",
          "anchor_poi_id": "..." | None,
          "anchor_stop_idx": int,
        }
    或 None(没有合适锚点)
    """
    block_start, block_end = food_block
    block_mid = (block_start + block_end) / 2

    stops = route.get("stops") or []
    if not stops:
        return None

    # 找用户在 block_mid 时所处的 stop
    for idx, stop in enumerate(stops):
        try:
            arr = _hhmm_to_float(stop["arrival_time"])
            lv = _hhmm_to_float(stop["leave_time"])
        except (KeyError, ValueError):
            continue
        if arr <= block_mid <= lv:
            # 用户此时正在这个 POI 里
            poi_lat = stop.get("lat") or stop.get("poi_lat")
            poi_lng = stop.get("lng") or stop.get("poi_lng")
            # 注意:RouteStop 里没存 lat/lng,我们要从 stops 字段读 - 后面在 build_route_stops 时附上
            return {
                "type": "near_poi",
                "anchor_lat": poi_lat,
                "anchor_lng": poi_lng,
                "anchor_name": stop.get("poi_name", ""),
                "anchor_poi_id": stop.get("poi_id"),
                "anchor_stop_idx": idx,
            }

    # 用户在某段通勤途中
    for idx in range(len(stops) - 1):
        try:
            lv = _hhmm_to_float(stops[idx]["leave_time"])
            next_arr = _hhmm_to_float(stops[idx + 1]["arrival_time"])
        except (KeyError, ValueError):
            continue
        if lv <= block_mid <= next_arr:
            # 在 idx → idx+1 路上
            cur, nxt = stops[idx], stops[idx + 1]
            cur_lat = cur.get("lat") or cur.get("poi_lat")
            cur_lng = cur.get("lng") or cur.get("poi_lng")
            nxt_lat = nxt.get("lat") or nxt.get("poi_lat")
            nxt_lng = nxt.get("lng") or nxt.get("poi_lng")
            if None in (cur_lat, cur_lng, nxt_lat, nxt_lng):
                continue
            if transport_mode == "drive":
                # 取段中点
                return {
                    "type": "along_segment",
                    "anchor_lat": (cur_lat + nxt_lat) / 2,
                    "anchor_lng": (cur_lng + nxt_lng) / 2,
                    "anchor_name": f"{cur.get('poi_name')} → {nxt.get('poi_name')} 途中",
                    "anchor_poi_id": None,
                    "anchor_stop_idx": idx,
                }
            else:
                # 步行/公交,以下一站为锚点(更符合"逛完一个去吃个饭再去下一个"的体验)
                return {
                    "type": "near_poi",
                    "anchor_lat": nxt_lat,
                    "anchor_lng": nxt_lng,
                    "anchor_name": nxt.get("poi_name", ""),
                    "anchor_poi_id": nxt.get("poi_id"),
                    "anchor_stop_idx": idx + 1,
                }

    # 兜底:取最后一个 stop
    last = stops[-1]
    last_lat = last.get("lat") or last.get("poi_lat")
    last_lng = last.get("lng") or last.get("poi_lng")
    if last_lat is None:
        return None
    return {
        "type": "near_poi",
        "anchor_lat": last_lat,
        "anchor_lng": last_lng,
        "anchor_name": last.get("poi_name", ""),
        "anchor_poi_id": last.get("poi_id"),
        "anchor_stop_idx": len(stops) - 1,
    }


# ─────────────────────────────────────────────────────────────
#  硬过滤
# ─────────────────────────────────────────────────────────────


def _is_open_at(restaurant: dict, hour_float: float) -> bool:
    """餐厅在某个时点是否营业。"""
    hours = restaurant.get("open_hours") or [[10, 22]]
    for start, end in hours:
        if start <= hour_float <= end or start <= hour_float + 24 <= end:
            return True
    return False


def _passes_hard_filters(
    r: dict,
    budget: Optional[float],
    health_constraints: list[str],
    disliked_ids: set[str],
    people_count: int,
    block_mid_hour: float,
) -> tuple[bool, str]:
    """返回 (是否通过, 失败原因)。"""
    if r.get("id") in disliked_ids:
        return False, "user_disliked"

    if not _is_open_at(r, block_mid_hour):
        return False, "not_open_at_meal_time"

    if budget is not None and r.get("avg_price", 0) > budget * 1.5:
        # 严格超预算 50% 才砍掉,给点弹性
        return False, "over_budget"

    if people_count > r.get("max_party_size", 99):
        return False, "party_too_large"

    for hc in health_constraints or []:
        rule = HEALTH_FILTERS.get(hc)
        if rule and not rule(r):
            return False, f"health_constraint_{hc}"

    return True, ""


# ─────────────────────────────────────────────────────────────
#  软加权评分
# ─────────────────────────────────────────────────────────────


def _score_restaurant(
    r: dict,
    budget: Optional[float],
    loved_cuisines: set[str],
    loved_restaurant_ids: set[str],
    max_radius_m: float,
) -> float:
    """
    返回 0~1 范围分数。
    评分 ×0.40 + 距离衰减 ×0.25 + 价格匹配 ×0.20 + 画像偏好 ×0.15
    """
    rating_n = max(0.0, min(1.0, (r.get("rating", 4.0) - 3.5) / 1.4))  # 3.5~4.9 → 0~1
    dist = r.get("distance_m", max_radius_m)
    dist_n = max(0.0, 1.0 - dist / max_radius_m)

    # 价格匹配 - 完美 1.0,超预算 50% 降到 0.4
    price_n = 1.0
    if budget is not None:
        price = r.get("avg_price", 0)
        if price <= 0:
            price_n = 0.6
        elif price <= budget * 0.6:
            price_n = 1.0    # 便宜还可以
        elif price <= budget:
            price_n = 1.0
        elif price <= budget * 1.3:
            price_n = 0.7
        else:
            price_n = 0.4

    # 画像偏好
    profile_n = 0.5
    if r.get("cuisine") in loved_cuisines:
        profile_n += 0.3
    if r.get("id") in loved_restaurant_ids:
        profile_n += 0.2
    profile_n = min(1.0, profile_n)

    return (
        rating_n * 0.40
        + dist_n * 0.25
        + price_n * 0.20
        + profile_n * 0.15
    )


# ─────────────────────────────────────────────────────────────
#  主入口
# ─────────────────────────────────────────────────────────────


def recommend_for_route(
    route: dict,
    intent: dict,
    user_profile: Optional[dict],
    time_window: dict,
    places: PlacesProvider,
    cuisines_per_block: int = 6,
    per_bucket_top: int = 3,
    enrich_queue_status: bool = True,
) -> list[dict]:
    """
    给一条路线生成餐厅推荐。

    返回 list of food_block_recommendation:
      [
        {
          meal_block: "午餐",
          block_time: "12:00-13:30",
          anchor: {...},
          buckets: [
            {
              cuisine: "本帮菜",
              matched_loved: true,
              restaurants: [{...}, {...}, {...}]
            }
          ],
          empty_reason: null | "no_anchor" | "no_candidates_in_radius" | "all_filtered"
        }
      ]
    """
    transport = intent.get("transport_mode", "transit")
    radius = RADIUS_BY_MODE.get(transport, 800)
    budget = intent.get("budget_per_person")
    health = intent.get("health_constraints") or []
    people = intent.get("people_count", 2)

    profile = user_profile or {}
    loved_categories = profile.get("loved_categories") or {}
    # 把 loved_categories 里的 sub_category 转成菜系桶 - 这里我们假定 profile 也支持 cuisine 偏好
    # 简化:loved_categories 里如果出现菜系名,就视为偏好
    loved_cuisines = {k for k in loved_categories.keys() if k in CUISINE_QUERY_KEYWORD}
    loved_restaurant_ids = set(profile.get("loved_pois") or [])  # 复用 loved_pois 列表存喜欢的餐厅
    disliked_ids = set(profile.get("disliked_pois") or [])

    food_blocks = time_window.get("food_blocks_within") or []
    results = []
    for fb in food_blocks:
        block_label = "午餐" if fb[0] < 14 else "晚餐"
        block_time = f"{int(fb[0]):02d}:{int((fb[0] - int(fb[0])) * 60):02d}-{int(fb[1]):02d}:{int((fb[1] - int(fb[1])) * 60):02d}"
        anchor = find_anchor(route, fb, transport)
        if not anchor or anchor.get("anchor_lat") is None:
            results.append({
                "meal_block": block_label,
                "block_time": block_time,
                "anchor": None,
                "buckets": [],
                "empty_reason": "no_anchor",
            })
            continue

        # 拉所有候选(不分菜系,一次性拉,再分桶)
        candidates = places.search_around(
            center_lat=anchor["anchor_lat"],
            center_lng=anchor["anchor_lng"],
            keyword="",
            types="050000",  # 高德 type 编码: 餐饮服务
            radius_m=radius,
            max_results=80,
        )
        if not candidates:
            results.append({
                "meal_block": block_label,
                "block_time": block_time,
                "anchor": anchor,
                "buckets": [],
                "empty_reason": "no_candidates_in_radius",
            })
            continue

        block_mid_hour = (fb[0] + fb[1]) / 2
        # 硬过滤
        filtered = []
        filter_reasons = {}
        for r in candidates:
            ok, reason = _passes_hard_filters(
                r, budget, health, disliked_ids, people, block_mid_hour
            )
            if ok:
                filtered.append(r)
            else:
                filter_reasons[reason] = filter_reasons.get(reason, 0) + 1
        if not filtered:
            results.append({
                "meal_block": block_label,
                "block_time": block_time,
                "anchor": anchor,
                "buckets": [],
                "empty_reason": "all_filtered",
                "filter_breakdown": filter_reasons,
            })
            continue

        # 分桶 + 排序
        buckets_map: dict[str, list[dict]] = {}
        for r in filtered:
            cui = r.get("cuisine") or "其他"
            buckets_map.setdefault(cui, []).append(r)

        bucket_objs = []
        for cui, items in buckets_map.items():
            for r in items:
                r["_score"] = _score_restaurant(
                    r, budget, loved_cuisines, loved_restaurant_ids, radius
                )
            items.sort(key=lambda x: x["_score"], reverse=True)
            top = items[:per_bucket_top]
            # 补充取号/预订能力 + 当前队列状态
            if enrich_queue_status:
                for r in top:
                    try:
                        q = get_restaurant_current_queue(r["id"])
                        r["current_queue"] = q["current_queue"]
                        r["queue_wait_minutes"] = q["estimated_wait_minutes"]
                        r["is_peak_hour"] = q["is_peak_hour"]
                    except Exception:
                        pass
            bucket_objs.append({
                "cuisine": cui,
                "matched_loved": cui in loved_cuisines,
                "bucket_top_score": top[0]["_score"] if top else 0,
                "restaurants": top,
            })

        # 桶排序:命中 loved 的桶在前;然后按桶顶部餐厅得分降序
        bucket_objs.sort(key=lambda b: (-int(b["matched_loved"]), -b["bucket_top_score"]))
        # 限制每个 block 最多展示的桶数
        bucket_objs = bucket_objs[:cuisines_per_block]

        results.append({
            "meal_block": block_label,
            "block_time": block_time,
            "anchor": anchor,
            "buckets": bucket_objs,
            "empty_reason": None,
        })

    return results
