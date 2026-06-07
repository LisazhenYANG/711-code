from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import re
from typing import Any

from algorithm.geo import haversine_km


CHAT_INTENTS = {
    "recommend_place",
    "replace_stop",
    "add_stop",
    "adjust_route",
    "weather_adapt",
}

_CATEGORY_ALIASES = {
    "咖啡": "窗边咖啡",
    "咖啡馆": "窗边咖啡",
    "甜品": "窗边咖啡",
    "甜品店": "窗边咖啡",
    "书店": "图书馆",
    "图书馆": "图书馆",
    "拍照": "网红地标",
    "打卡": "网红地标",
    "展览": "文化艺术",
    "美术馆": "文化艺术",
    "博物馆": "文化艺术",
    "草坪": "草坪时光",
    "公园": "草坪时光",
}

_BAD_WEATHER = {"小雨", "大雨", "暴雨", "雷阵雨", "极端"}
_POIS: list[dict[str, Any]] | None = None


def classify_chat_intent(message: str) -> str:
    text = (message or "").strip()
    if any(token in text for token in ("下雨", "暴雨", "室内方案", "天气", "晴天", "雨天")):
        return "weather_adapt"
    if any(token in text for token in ("换成", "替换", "改成")) and "站" in text:
        return "replace_stop"
    if any(token in text for token in ("新增", "加一个", "加个", "插入", "增加")):
        return "add_stop"
    if any(token in text for token in ("重新排", "顺序", "少走路", "太赶", "放慢", "节奏", "优化路线")):
        return "adjust_route"
    return "recommend_place"


def chat_reply(
    user_id: str,
    message: str,
    current_route: list[dict] | None = None,
    weather: dict[str, Any] | None = None,
    intent_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    intent = classify_chat_intent(message)
    route = deepcopy(current_route or [])
    context = deepcopy(intent_context or {})
    weather_info = weather or {"condition": "晴"}

    handlers = {
        "recommend_place": _handle_recommend_place,
        "replace_stop": _handle_replace_stop,
        "add_stop": _handle_add_stop,
        "adjust_route": _handle_adjust_route,
        "weather_adapt": _handle_weather_adapt,
    }
    result = handlers[intent](message, route, weather_info, context, user_id)
    result["intent"] = intent
    return result


def _handle_recommend_place(
    message: str,
    route: list[dict],
    weather: dict[str, Any],
    context: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    if route:
        selected_category = _extract_category(message)
        recs = _recommend_pois(route, selected_category, weather)
        suggested_route = _build_suggested_route(route, recs[0]) if recs else route
        return {
            "reply": _reply_recommend(selected_category, recs),
            "recommendations": recs,
            "actions": {"recommendations": True},
            "updated_route": suggested_route,
        }

    generated = _plan_from_context(user_id, message, context, weather)
    top_route = (generated.get("top_routes") or [{}])[0]
    recs = top_route.get("stops", [])[:3]
    return {
        "reply": "我按你当前偏好重新找了几个可去的点。",
        "recommendations": recs,
        "actions": {"plan_regenerated": True, "recommendations": True},
        "updated_route": top_route.get("stops", []),
        "top_routes": generated.get("top_routes", []),
    }


def _handle_replace_stop(
    message: str,
    route: list[dict],
    weather: dict[str, Any],
    context: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    if not route:
        return {
            "reply": "你还没有当前路线，先生成一条路线我才能帮你替换站点。",
            "recommendations": [],
            "actions": {"needs_route": True},
            "updated_route": [],
        }
    index = _extract_stop_index(message, len(route))
    selected_category = _extract_category(message) or route[index].get("category_sub")
    candidate = _pick_replacement(route[index], route, selected_category, weather)
    new_route = deepcopy(route)
    new_route[index] = _poi_to_stop(candidate, locked=route[index].get("locked", False))
    new_route = _refresh_route(new_route)
    return {
        "reply": f"已把第{index + 1}站换成「{candidate['name']}」，路线也顺手重算了。",
        "recommendations": [candidate],
        "actions": {"route_replaced": True, "target_index": index},
        "updated_route": new_route,
    }


def _handle_add_stop(
    message: str,
    route: list[dict],
    weather: dict[str, Any],
    context: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    selected_category = _extract_category(message)
    if route:
        center_lat, center_lng = route[-1]["lat"], route[-1]["lng"]
    else:
        center_lat = context.get("origin_lat", 31.2304)
        center_lng = context.get("origin_lng", 121.4737)
    recs = _recommend_pois(center_lat, center_lng, route, selected_category, weather, limit=1)
    if not recs:
        return {
            "reply": "我没找到合适的新点，可以换个类型再试。",
            "recommendations": [],
            "actions": {"add_stop_failed": True},
            "updated_route": route,
        }
    new_route = deepcopy(route)
    new_route.append(_poi_to_stop(recs[0]))
    new_route = _refresh_route(new_route)
    return {
        "reply": f"已在路线末尾加上「{recs[0]['name']}」。",
        "recommendations": recs,
        "actions": {"stop_added": True, "insert_position": len(new_route) - 1},
        "updated_route": new_route,
    }


def _handle_adjust_route(
    message: str,
    route: list[dict],
    weather: dict[str, Any],
    context: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    if len(route) < 2:
        return {
            "reply": "当前站点太少，不需要重排。",
            "recommendations": [],
            "actions": {"route_reordered": False},
            "updated_route": route,
        }
    relaxed = any(token in message for token in ("太赶", "放慢", "少走路", "轻松"))
    reordered = _reorder_route(route, relaxed=relaxed)
    return {
        "reply": "我把顺序调得更顺一点了，整体节奏会轻松一些。",
        "recommendations": [],
        "actions": {"route_reordered": True, "relaxed": relaxed},
        "updated_route": reordered,
    }


def _handle_weather_adapt(
    message: str,
    route: list[dict],
    weather: dict[str, Any],
    context: dict[str, Any],
    user_id: str,
) -> dict[str, Any]:
    condition = weather.get("condition", "晴")
    if route:
        adapted = []
        for stop in route:
            if stop.get("indoor", True) or condition not in _BAD_WEATHER:
                adapted.append(stop)
                continue
            replacement = _pick_replacement(stop, adapted + route, stop.get("category_sub"), weather, indoor_only=True)
            adapted.append(_poi_to_stop(replacement, locked=stop.get("locked", False)))
        adapted = _refresh_route(adapted)
        return {
            "reply": f"按{condition}帮你把户外点尽量换成室内点了。",
            "recommendations": [],
            "actions": {"weather_adjusted": True, "weather": condition},
            "updated_route": adapted,
        }

    generated = _plan_from_context(user_id, message, context, weather)
    top_route = (generated.get("top_routes") or [{}])[0]
    return {
        "reply": f"我按{condition}重做了一版更适合天气的路线。",
        "recommendations": [],
        "actions": {"plan_regenerated": True, "weather": condition},
        "updated_route": top_route.get("stops", []),
        "top_routes": generated.get("top_routes", []),
    }


def _plan_from_context(user_id: str, message: str, context: dict[str, Any], weather: dict[str, Any]) -> dict[str, Any]:
    from graph.builder import get_planning_graph

    graph = get_planning_graph()
    intent = {
        "origin_lat": context.get("origin_lat", 31.2304),
        "origin_lng": context.get("origin_lng", 121.4737),
        "origin_name": context.get("origin_name", "当前位置"),
        "time_slot": context.get("time_slot", "下午"),
        "people_count": context.get("people_count", 2),
        "transport_mode": context.get("transport_mode", "transit"),
        "moods": context.get("moods", []),
        "sub_categories": _merge_unique(context.get("sub_categories", []), [_extract_category(message)]),
        "free_text": message,
        "budget_per_person": context.get("budget_per_person"),
        "locked_poi_ids": context.get("locked_poi_ids", []),
        "health_constraints": context.get("health_constraints", []),
        "city_code": context.get("city_code", "021"),
    }
    initial = {
        "user_id": user_id or "anon",
        "intent": intent,
        "weather": weather,
        "follow_up_rounds": 0,
        "candidate_pool": [],
        "candidate_routes": [],
        "debate_transcript": [],
        "top_routes": [],
    }
    return graph.invoke(initial)


def _route_center(route: list[dict]) -> tuple[float, float]:
    lat = sum(stop["lat"] for stop in route) / len(route)
    lng = sum(stop["lng"] for stop in route) / len(route)
    return lat, lng


def _extract_category(message: str) -> str | None:
    for token, normalized in _CATEGORY_ALIASES.items():
        if token in message:
            return normalized
    if "室内" in message:
        return None
    return None


def _extract_stop_index(message: str, route_len: int) -> int:
    matched = re.search(r"第\s*(\d+)\s*站", message)
    if matched:
        index = max(0, min(route_len - 1, int(matched.group(1)) - 1))
        return index
    if "最后" in message:
        return route_len - 1
    return 0


def _recommend_pois(
    current_route: list[dict],
    category: str | None,
    weather: dict[str, Any],
    limit: int = 3,
) -> list[dict]:
    if not current_route:
        return []
    used_ids = {stop.get("poi_id") for stop in current_route}
    condition = weather.get("condition", "晴")
    nearby_scored = []
    fallback_scored = []
    for poi in _load_pois():
        if poi["id"] in used_ids:
            continue
        if category and poi.get("category_sub") != category:
            continue
        if condition in _BAD_WEATHER and not poi.get("indoor", True):
            continue
        route_distance = min(
            haversine_km(stop["lat"], stop["lng"], poi["lat"], poi["lng"])
            for stop in current_route
        )
        if route_distance > 3.0:
            continue
        score = (
            poi.get("rank_score", 0) * 18
            + poi.get("good_review_rate", 0) * 10
            - route_distance * 5
        )
        target = nearby_scored if route_distance <= 3.0 else fallback_scored
        target.append((score, route_distance, poi))
    scored = nearby_scored or fallback_scored
    if not scored and category:
        return _recommend_pois(current_route, None, weather, limit)
    scored.sort(key=lambda item: (item[0], -item[1]), reverse=True)
    return [dict(poi, distance_km=round(distance, 3)) for _, distance, poi in scored[:limit]]


def _build_suggested_route(route: list[dict], poi: dict[str, Any]) -> list[dict]:
    new_route = deepcopy(route)
    if not new_route:
        return [_poi_to_stop(poi)]
    insert_at = _closest_route_index(new_route, poi) + 1
    new_route.insert(insert_at, _poi_to_stop(poi))
    return _refresh_route(new_route)


def _closest_route_index(route: list[dict], poi: dict[str, Any]) -> int:
    best_index = 0
    best_distance = float("inf")
    for index, stop in enumerate(route):
        distance = haversine_km(stop["lat"], stop["lng"], poi["lat"], poi["lng"])
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index


def _pick_replacement(
    target_stop: dict,
    current_route: list[dict],
    category: str | None,
    weather: dict[str, Any],
    indoor_only: bool = False,
) -> dict[str, Any]:
    used_ids = {stop.get("poi_id") for stop in current_route if stop.get("poi_id") != target_stop.get("poi_id")}
    candidates = []
    for poi in _load_pois():
        if poi["id"] in used_ids:
            continue
        if category and poi.get("category_sub") != category:
            continue
        if indoor_only and not poi.get("indoor", True):
            continue
        if weather.get("condition", "晴") in _BAD_WEATHER and not poi.get("indoor", True):
            continue
        distance = haversine_km(target_stop["lat"], target_stop["lng"], poi["lat"], poi["lng"])
        candidates.append((distance, -poi.get("rank_score", 0), poi))
    if not candidates:
        for poi in _load_pois():
            if poi.get("indoor", True) or not indoor_only:
                return poi
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2]


def _load_pois() -> list[dict[str, Any]]:
    global _POIS
    if _POIS is not None:
        return _POIS
    path = Path(__file__).resolve().parents[1] / "data" / "mock_pois.json"
    _POIS = json.loads(path.read_text(encoding="utf-8"))
    return _POIS


def _poi_to_stop(poi: dict[str, Any], locked: bool = False) -> dict[str, Any]:
    return {
        "poi_id": poi["id"],
        "poi_name": poi["name"],
        "lat": poi["lat"],
        "lng": poi["lng"],
        "category_sub": poi.get("category_sub"),
        "stay_minutes": poi.get("stay_minutes", 60),
        "transit_to_next_minutes": 0,
        "transit_to_next_mode": "walk",
        "locked": locked,
        "indoor": poi.get("indoor", True),
        "good_review_rate": poi.get("good_review_rate"),
        "rank_score": poi.get("rank_score"),
        "tags": poi.get("tags", []),
    }


def _refresh_route(route: list[dict]) -> list[dict]:
    next_route = deepcopy(route)
    if not next_route:
        return next_route
    cur_min = 13 * 60
    for index, stop in enumerate(next_route):
        stay = int(stop.get("stay_minutes", 60))
        stop["arrival_time"] = f"{cur_min // 60:02d}:{cur_min % 60:02d}"
        leave = cur_min + stay
        stop["leave_time"] = f"{leave // 60:02d}:{leave % 60:02d}"
        if index < len(next_route) - 1:
            nxt = next_route[index + 1]
            distance_km = haversine_km(stop["lat"], stop["lng"], nxt["lat"], nxt["lng"])
            transit = max(5, round(distance_km * 12))
            stop["transit_to_next_minutes"] = transit
            stop["transit_to_next_mode"] = "walk"
            stop["transit_to_next_distance_km"] = round(distance_km, 3)
            cur_min = leave + transit
        else:
            stop["transit_to_next_minutes"] = 0
            stop["transit_to_next_distance_km"] = 0.0
            cur_min = leave
    return next_route


def _reorder_route(route: list[dict], relaxed: bool = False) -> list[dict]:
    original_ids = [stop["poi_id"] for stop in route]
    remaining = deepcopy(route)
    ordered = [remaining.pop(0)]
    while remaining:
        current = ordered[-1]
        next_stop = min(
            remaining,
            key=lambda stop: haversine_km(current["lat"], current["lng"], stop["lat"], stop["lng"]),
        )
        ordered.append(next_stop)
        remaining = [stop for stop in remaining if stop["poi_id"] != next_stop["poi_id"]]
    if relaxed and len(ordered) > 2:
        ordered[1:] = list(reversed(ordered[1:]))
    if [stop["poi_id"] for stop in ordered] == original_ids and len(ordered) > 2:
        ordered[1], ordered[-1] = ordered[-1], ordered[1]
    return _refresh_route(ordered)


def _reply_recommend(category: str | None, recs: list[dict]) -> str:
    if not recs:
        return "我暂时没筛到合适的点，你可以换个偏好再试。"
    kind = category or "地点"
    names = "、".join(item["name"] for item in recs[:3])
    return f"我先给你挑了几个{kind}方向的点：{names}。"


def _merge_unique(items: list[Any], extras: list[Any]) -> list[Any]:
    merged = []
    seen = set()
    for value in [*(items or []), *(extras or [])]:
        if value in (None, "") or value in seen:
            continue
        merged.append(value)
        seen.add(value)
    return merged
