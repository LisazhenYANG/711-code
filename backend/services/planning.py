from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

from backend.data.seeds import MEALS, RECOMMENDATIONS, SPOTS
from backend.schemas import RouteGenerateRequest


def load_711_data(filename: str) -> list[dict[str, Any]]:
    path = Path(__file__).resolve().parents[2] / "711-AI" / "data" / filename
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_stops(req: RouteGenerateRequest) -> list[dict[str, Any]]:
    wanted = req.discover_items or req.moods
    stops = [stop_for_name(name, idx) for idx, name in enumerate(wanted[:3])]
    if len(stops) < 3:
        stops.extend(SPOTS[len(stops) : 3])
    return [with_timing(stop, idx, req.time_slot) for idx, stop in enumerate(stops[:4])]


def generate_route_options(req: RouteGenerateRequest) -> dict[str, Any]:
    base_stops = build_stops(req)
    routes = [
        {
            "id": "route-soft",
            "name": f"{req.location.area or req.location.city}慢悠悠之旅",
            "label": "轻松首选",
            "summary": route_summary(req, "节奏轻一点，保留发呆和临时调整空间"),
            "stops": base_stops,
        },
        {
            "id": "route-photo",
            "name": "出片灵感路线",
            "label": "好拍版本",
            "summary": route_summary(req, "把采光、展览和街区质感排在前面"),
            "stops": rotate_stops(base_stops, 1),
        },
        {
            "id": "route-hidden",
            "name": "小众惊喜路线",
            "label": "小众版本",
            "summary": route_summary(req, "少走热门点，多留一些本地感选择"),
            "stops": rotate_stops(base_stops, 2),
        },
    ]
    return {
        "routes": routes,
        "weather": weather(req.location.city),
        "outfit": outfit(),
        "request": req.model_dump(),
    }


def stop_for_name(name: str, idx: int) -> dict[str, Any]:
    mapping = {
        "窗边咖啡": {
            "name": "梧桐窗边咖啡",
            "category": "咖啡店",
            "imgs": ["☕"],
            "dur": "约1h",
            "lat": 31.2297,
            "lng": 121.4489,
        },
        "图书馆": {
            "name": "静安区图书馆",
            "category": "图书馆",
            "imgs": ["📚"],
            "dur": "约1.5h",
            "lat": 31.2322,
            "lng": 121.4437,
        },
        "书店": {
            "name": "静雅书局",
            "category": "书店",
            "imgs": ["📚"],
            "dur": "约1h",
            "lat": 31.2305,
            "lng": 121.4468,
        },
        "手工坊": {
            "name": "可纸工坊",
            "category": "手工坊",
            "imgs": ["✂️"],
            "dur": "约1.5h",
            "lat": 31.2267,
            "lng": 121.4472,
        },
        "展览": {
            "name": "UCCA · 当代艺术",
            "category": "展览",
            "imgs": ["🎨"],
            "dur": "约1.5h",
            "lat": 31.2249,
            "lng": 121.4554,
        },
        "桌游": {
            "name": "慢局桌游社",
            "category": "桌游",
            "imgs": ["🎲"],
            "dur": "约2h",
            "lat": 31.2275,
            "lng": 121.4523,
        },
    }
    fallback_coords = [
        (31.2288, 121.4485),
        (31.2309, 121.4528),
        (31.2265, 121.4561),
        (31.2330, 121.4496),
    ]
    lat, lng = fallback_coords[idx % len(fallback_coords)]
    return mapping.get(
        name,
        {
            "name": name,
            "category": name,
            "imgs": ["📍"],
            "dur": "约1h",
            "rank": idx + 1,
            "lat": lat,
            "lng": lng,
        },
    )


def with_timing(stop: dict[str, Any], idx: int, time_slot: str) -> dict[str, Any]:
    starts = {"上午": 9, "下午": 13, "全天": 10, "随时": 11}
    hour = starts.get(time_slot, 13) + idx * 2
    return {
        **stop,
        "time": stop.get("time", f"{hour:02d}:00"),
        "meta": stop.get("meta", ["建议停留 " + stop.get("dur", "约1h")]),
        "transitMode": None if idx == 0 else stop.get("transitMode", "walk" if idx % 2 else "metro"),
        "transitMin": None if idx == 0 else stop.get("transitMin", 8 + idx * 4),
    }


def rotate_stops(stops: list[dict[str, Any]], offset: int) -> list[dict[str, Any]]:
    if not stops:
        return []
    return stops[offset:] + stops[:offset]


def route_summary(req: RouteGenerateRequest, suffix: str) -> str:
    moods = "、".join(req.moods) if req.moods else "随心"
    people = req.people or "2人"
    return f"{people}在{req.location.area or req.location.city}{moods}，{suffix}"


def weather(city: str) -> dict[str, str]:
    return {"city": city, "date": "今天", "temp": "24-29°C", "condition": "多云转晴", "rain": "15%", "suitable": "适合出行"}


def outfit() -> dict[str, Any]:
    return {"top": "短袖T恤", "outer": "薄外套或针织开衫", "shoes": "舒适走路鞋", "umbrella": True, "sunscreen": True}


def booking_type(category: str) -> str:
    return {
        "展览": "门票",
        "手工坊": "体验预约",
        "餐厅": "餐厅预约",
        "桌游": "主推套餐",
        "SPA护理": "主推服务",
    }.get(category, "预约")


def duration_to_minutes(duration: str) -> int:
    text = str(duration)
    if "2h" in text or "2小时" in text:
        return 120
    if "1.5h" in text or "1.5" in text:
        return 90
    if "45" in text:
        return 45
    return 60


def optimize_route(route: list[dict[str, Any]], locked: list[int]) -> list[dict[str, Any]]:
    if len(route) <= 2:
        return route
    locked_set = set(locked)
    movable = [stop for idx, stop in enumerate(route) if idx not in locked_set]
    movable = list(reversed(movable))
    next_route = []
    movable_idx = 0
    for idx, stop in enumerate(route):
        if idx in locked_set:
            next_route.append(stop)
        else:
            next_route.append(movable[movable_idx])
            movable_idx += 1
    return next_route


def recommendation_to_stop(index: int, route_index: int) -> dict[str, Any]:
    item = RECOMMENDATIONS[index % len(RECOMMENDATIONS)]
    category = "展览" if "展" in item["title"] else ("咖啡店" if "咖啡" in item["title"] else "散步")
    return with_timing(
        {
            "name": item["title"],
            "category": category,
            "dur": item["duration"],
            "imgs": item["gallery"],
            "meta": [item["subtitle"], item["reason"]],
            "prices": [["推荐项目", item["price"]]],
        },
        route_index,
        "下午",
    )


def custom_place_to_stop(name: str, route_index: int) -> dict[str, Any]:
    clean_name = name.strip() or "自定义地点"
    category = "餐厅" if "餐" in clean_name or "饭" in clean_name else "自定义地点"
    if "咖啡" in clean_name:
        category = "咖啡店"
    elif "展" in clean_name or "馆" in clean_name:
        category = "展览"
    return with_timing(
        {
            "name": clean_name,
            "category": category,
            "dur": "约1h",
            "imgs": ["📍"],
            "meta": ["你手动添加的地点", "可在路线中继续调整"],
            "prices": [],
        },
        route_index,
        "下午",
    )


def meal_to_stop(route_index: int, slot: str = "lunch") -> dict[str, Any]:
    selected_name = ""
    if "|" in slot:
        slot, selected_name = slot.split("|", 1)
    meals = MEALS.get(slot) or MEALS["lunch"]
    meal = next((item for item in meals if item["name"] == selected_name), None)
    if meal is None:
        if selected_name.strip():
            meal = {
                "name": selected_name.strip(),
                "cuisine": "餐厅",
                "rating": "4.5",
                "wait": "待查询",
                "price": "待查询",
            }
        else:
            meal = meals[0]
    slot_time = {
        "breakfast": "09:00",
        "lunch": "12:30",
        "dinner": "18:30",
    }.get(slot, "12:30")
    return with_timing(
        {
            "name": meal["name"],
            "category": "餐厅",
            "dur": "约1h",
            "imgs": ["🍜"],
            "meta": [meal["cuisine"], f"评分 {meal['rating']}", f"排队 {meal['wait']}"],
            "prices": [["人均", meal["price"]]],
            "time": slot_time,
        },
        route_index,
        "下午",
    )


def set_transit(route: list[dict[str, Any]], index: int, mode: str) -> list[dict[str, Any]]:
    if index < 0 or index >= len(route):
        return route
    minutes = {"walk": 10, "metro": 15, "taxi": 8, "bus": 20}.get(mode, 10)
    next_route = [dict(stop) for stop in route]
    next_route[index]["transitMode"] = mode
    next_route[index]["transitMin"] = minutes
    return next_route


def todos_for_route(route: list[dict[str, Any]]) -> list[dict[str, Any]]:
    todos = []
    for stop in route:
        category = stop.get("category", "")
        if category in {"展览", "手工坊", "餐厅", "桌游"}:
            todos.append({"done": False, "label": f"确认 {stop.get('name', '')} 的{booking_type(category)}"})
    todos.append({"done": False, "label": "带充电宝和雨伞"})
    return todos


def seed_plan() -> dict[str, Any]:
    route = [with_timing(stop, idx, "下午") for idx, stop in enumerate(SPOTS)]
    return {
        "id": "seed-active",
        "title": "静安慢悠悠之旅",
        "status": "进行中",
        "duration": "半天",
        "route": route,
        "todos": [
            {"done": True, "label": "预约 UCCA 展览票"},
            {"done": False, "label": "带充电宝和雨伞"},
        ],
    }


def seed_bookings(route: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for stop in route:
        prices = stop.get("prices") or []
        first_price = prices[0] if prices else ["预约", ""]
        category = stop.get("category", "")
        if category in {"展览", "手工坊", "桌游", "餐厅", "咖啡店"}:
            items.append(
                {
                    "icon": (stop.get("imgs") or ["📍"])[0],
                    "name": stop.get("name", ""),
                    "category": category,
                    "bookingType": booking_type(category),
                    "time": stop.get("time", "待定"),
                    "status": "pending",
                    "statusText": "待支付" if category == "展览" else "待预约",
                    "selectedProduct": {"name": first_price[0], "price": first_price[1]},
                    "code": None,
                    "qr": False,
                }
            )
    return items


def is_peak_hour(now: datetime | None = None) -> bool:
    now = now or datetime.now()
    hour = now.hour + now.minute / 60
    return 11.5 <= hour <= 13.5 or 17.5 <= hour <= 19.5


def current_queue_for_meta(meta: dict[str, Any], now: datetime | None = None) -> int:
    base = int(meta.get("base_queue_at_peak", 5))
    if is_peak_hour(now):
        return base
    return max(0, base // 3)


def people_group(count: int) -> str:
    if count <= 1:
        return "独行"
    if count == 2:
        return "情侣"
    if count <= 4:
        return "小团"
    return "大队"
