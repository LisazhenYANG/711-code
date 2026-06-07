from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.db import db_get_json, db_put_json
from backend.schemas import RouteActionRequest
from backend.services.planning import (
    meal_to_stop,
    optimize_route,
    custom_place_to_stop,
    recommendation_to_stop,
    seed_bookings,
    seed_plan,
    set_transit,
    todos_for_route,
    with_timing,
)


def load_app_state() -> dict[str, Any]:
    state = db_get_json("kv", "app_state")
    if state:
        state.pop("share_link", None)
        active_plan = state.get("active_plan")
        if isinstance(active_plan, dict):
            active_plan.pop("members", None)
        save_app_state(state)
        return state
    state = {
        "active_plan": seed_plan(),
        "locked_indexes": [0],
        "hidden_indexes": [],
        "bookings": seed_bookings(seed_plan()["route"]),
        "packing_list": ["预约二维码", "充电宝", "轻便鞋", "小伞"],
        "history": [],
        "last_action": None,
    }
    save_app_state(state)
    return state


def save_app_state(state: dict[str, Any]) -> None:
    db_put_json("kv", "app_state", state)


def route_payload(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "active_plan": state["active_plan"],
        "route": state["active_plan"]["route"],
        "locked_indexes": state.get("locked_indexes", [0]),
        "hidden_indexes": state.get("hidden_indexes", []),
        "bookings": state.get("bookings", []),
        "packing_list": state.get("packing_list", []),
        "history": state.get("history", []),
        "last_action": state.get("last_action"),
    }


def apply_route_action(req: RouteActionRequest) -> dict[str, Any]:
    state = load_app_state()
    route = req.route or state["active_plan"]["route"]
    locked = set(req.locked_indexes or state.get("locked_indexes", [0]))
    hidden = set(req.hidden_indexes or state.get("hidden_indexes", []))
    route_changed = False
    action_payload: dict[str, Any] = {"type": req.action}

    if req.action == "lock" and req.index is not None:
        locked.symmetric_difference_update({req.index})
    elif req.action == "delete" and req.index is not None:
        if req.index in locked:
            state["last_action"] = {"type": "lock_blocked", "index": req.index}
        else:
            hidden.add(req.index)
    elif req.action == "restore":
        hidden.clear()
    elif req.action == "optimize":
        route = optimize_route(route, sorted(locked))
        hidden.clear()
        route_changed = True
    elif req.action == "add_place":
        if req.value.strip():
            route.append(custom_place_to_stop(req.value, len(route)))
        else:
            route.append(recommendation_to_stop(req.recommendation_index or 0, len(route)))
        hidden.clear()
        route_changed = True
    elif req.action == "add_meal":
        route.append(meal_to_stop(len(route), req.value or "lunch"))
        hidden.clear()
        route_changed = True
    elif req.action == "transit" and req.index is not None:
        route = set_transit(route, req.index, req.value)
        route_changed = True
    elif req.action == "heart":
        action_payload["choice"] = req.value or "ignore"
    elif req.action == "archive":
        archived = dict(state["active_plan"])
        archived["status"] = "已完成"
        archived["archivedAt"] = datetime.now().isoformat(timespec="seconds")
        state.setdefault("history", []).append(archived)

    state["active_plan"]["route"] = [
        with_timing(stop, idx, "下午") for idx, stop in enumerate(route)
    ]
    state["active_plan"]["todos"] = todos_for_route(state["active_plan"]["route"])
    state["locked_indexes"] = sorted(locked)
    state["hidden_indexes"] = sorted(hidden)
    if route_changed:
        state["bookings"] = merge_bookings(
            seed_bookings(state["active_plan"]["route"]),
            state.get("bookings", []),
        )
    action_payload["at"] = datetime.now().isoformat(timespec="seconds")
    state["last_action"] = action_payload
    save_app_state(state)
    return route_payload(state)


def merge_bookings(
    fresh_bookings: list[dict[str, Any]], previous_bookings: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    previous_by_key = {
        booking_key(item): item
        for item in previous_bookings
        if item.get("name") and item.get("category")
    }
    merged = []
    for item in fresh_bookings:
        previous = previous_by_key.get(booking_key(item))
        if previous and previous.get("qr"):
            merged.append({**item, **previous})
        elif previous and previous.get("status") in {"purchased", "confirmed"}:
            merged.append({**item, **previous})
        else:
            merged.append(item)
    return merged


def booking_key(item: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(item.get("name", "")),
        str(item.get("category", "")),
        str(item.get("time", item.get("ticketTime", ""))),
    )
