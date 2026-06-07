from __future__ import annotations

from datetime import datetime, timedelta
from itertools import count
from typing import Any
import uuid

from fastapi import APIRouter, HTTPException

from backend.db import db_get_json, db_list_json, db_put_json
from backend.schemas import (
    AiFeedbackRequest,
    AiPlanRequest,
    LocationInput,
    QueueTicketRequest,
    ReservationRequest,
    RouteGenerateRequest,
)
from backend.services.planning import (
    current_queue_for_meta,
    duration_to_minutes,
    generate_route_options,
    is_peak_hour,
    load_711_data,
    people_group,
)


router = APIRouter()
_ai_queue_counter = count(1)
AI_TICKETS: dict[str, dict[str, Any]] = {}
AI_RESERVATIONS: dict[str, dict[str, Any]] = {}
FEEDBACK: list[dict[str, Any]] = []


@router.get("/health")
def ai_health() -> dict[str, Any]:
    return {
        "ok": True,
        "llm_available": False,
        "llm_model": "mock",
        "commute_provider": "MockCommute",
        "places_provider": "MockPlaces",
        "amap_configured": False,
    }


@router.get("/pois")
def ai_list_pois() -> list[dict[str, Any]]:
    return load_711_data("mock_pois.json")


@router.get("/restaurants")
def ai_list_restaurants() -> list[dict[str, Any]]:
    return load_711_data("mock_restaurants.json")


@router.get("/restaurants/{restaurant_id}/queue")
def ai_get_restaurant_queue(restaurant_id: str) -> dict[str, Any]:
    meta = restaurant_meta(restaurant_id)
    speed = meta.get("queue_speed_per_minute", 0.5) or 0.5
    current = current_queue_for_meta(meta)
    return {
        "restaurant_id": restaurant_id,
        "current_queue": current,
        "estimated_wait_minutes": round(current / speed, 1) if current else 0,
        "is_peak_hour": is_peak_hour(),
    }


@router.post("/plan")
def ai_plan(req: AiPlanRequest) -> dict[str, Any]:
    location = LocationInput(city="上海", area=req.intent.origin_name or "当前位置")
    route_req = RouteGenerateRequest(
        location=location,
        time_slot=req.intent.time_slot,
        people=f"{req.intent.people_count}人",
        moods=req.intent.moods,
        discover_items=req.intent.sub_categories,
    )
    generated = generate_route_options(route_req)
    top_routes = [
        {
            "route_id": route["id"],
            "label": route["label"],
            "summary": route["summary"],
            "stops": [
                {
                    "poi_id": f"poi_{idx + 1}",
                    "poi_name": stop["name"],
                    "category": stop.get("category", ""),
                    "arrival_time": stop.get("time", ""),
                    "stay_minutes": duration_to_minutes(stop.get("dur", "")),
                    "transit_mode": stop.get("transitMode"),
                    "transit_minutes": stop.get("transitMin"),
                    "intro": " · ".join(stop.get("meta", [])),
                }
                for idx, stop in enumerate(route["stops"])
            ],
        }
        for route in generated["routes"]
    ]
    return {
        "top_routes": top_routes,
        "debate_transcript": [
            {"agent": "system", "message": "当前 backend 使用 711-AI 兼容降级规划，接口字段保持一致。"}
        ],
        "pre_brief": "已根据时间、人数和兴趣生成 3 条候选路线。",
        "reachable_radius_km": 5,
        "max_pois_per_day": 4,
        "time_window": req.intent.time_slot,
        "llm_degraded": True,
        "navigation_degraded": True,
        "candidate_routes_count": len(generated["routes"]),
        "dropped_categories": [],
    }


@router.post("/feedback")
def ai_feedback(req: AiFeedbackRequest) -> dict[str, Any]:
    updated_profile = {
        "user_id": req.user_id,
        "last_rating": req.user_rating,
        "choice_route_id": req.user_choice_route_id,
        "deleted_poi_ids": req.user_deleted_poi_ids,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
    }
    item = {"type": "711-ai", **req.model_dump(), "updated_profile": updated_profile}
    FEEDBACK.append(item)
    db_put_json("feedback", uuid.uuid4().hex, item)
    return {"ok": True, "updated_profile": updated_profile}


@router.post("/booking/queue")
def ai_book_queue(req: QueueTicketRequest) -> dict[str, Any]:
    meta = restaurant_meta(req.restaurant_id)
    if not meta.get("supports_queue_ticket", True):
        raise HTTPException(status_code=400, detail={"error": "restaurant_does_not_support_queue"})
    now = datetime.now()
    position = current_queue_for_meta(meta) + next(_ai_queue_counter)
    speed = meta.get("queue_speed_per_minute", 0.5) or 0.5
    wait_minutes = position / speed
    ticket_no = f"{'A' if is_peak_hour(now) else 'Q'}{position:03d}-{req.restaurant_id[-3:]}"
    ticket = {
        "ticket_no": ticket_no,
        "restaurant_id": req.restaurant_id,
        "restaurant_name": meta.get("name", ""),
        "user_id": req.user_id,
        "people_count": req.people_count,
        "people_group": people_group(req.people_count),
        "issued_at": now.isoformat(timespec="seconds"),
        "queue_position_at_issue": position,
        "status": "waiting",
        "estimated_wait_minutes": round(wait_minutes, 1),
        "estimated_call_time": (now + timedelta(minutes=wait_minutes)).isoformat(timespec="seconds"),
        "queue_speed_per_minute": speed,
        "type": "queue_ticket",
    }
    AI_TICKETS[ticket_no] = ticket
    db_put_json("ai_tickets", ticket_no, ticket)
    return ticket


@router.get("/booking/queue/{ticket_no}")
def ai_get_queue_ticket(ticket_no: str) -> dict[str, Any]:
    ticket = db_get_json("ai_tickets", ticket_no) or AI_TICKETS.get(ticket_no)
    if not ticket:
        raise HTTPException(status_code=404, detail={"error": "ticket_not_found"})
    if ticket["status"] != "waiting":
        return ticket
    issued = datetime.fromisoformat(ticket["issued_at"])
    elapsed_min = max(0.0, (datetime.now() - issued).total_seconds() / 60)
    moved = int(elapsed_min * ticket.get("queue_speed_per_minute", 0.5))
    remaining = max(0, ticket["queue_position_at_issue"] - moved)
    out = dict(ticket)
    out["queue_position_now"] = remaining
    out["estimated_wait_remaining_minutes"] = round(remaining / ticket.get("queue_speed_per_minute", 0.5), 1)
    out["ready_to_call"] = True if remaining == 0 else ("approaching" if remaining <= 2 else False)
    return out


@router.delete("/booking/queue/{ticket_no}")
def ai_cancel_queue_ticket(ticket_no: str) -> dict[str, Any]:
    ticket = db_get_json("ai_tickets", ticket_no) or AI_TICKETS.get(ticket_no)
    if not ticket:
        raise HTTPException(status_code=400, detail={"error": "ticket_not_found", "ticket_no": ticket_no})
    if ticket["status"] != "waiting":
        raise HTTPException(status_code=400, detail={"error": f"cannot_cancel_in_status_{ticket['status']}"})
    ticket["status"] = "cancelled"
    ticket["cancelled_at"] = datetime.now().isoformat(timespec="seconds")
    AI_TICKETS[ticket_no] = ticket
    db_put_json("ai_tickets", ticket_no, ticket)
    return ticket


@router.post("/booking/queue/{ticket_no}/seat")
def ai_seat_queue_ticket(ticket_no: str) -> dict[str, Any]:
    ticket = db_get_json("ai_tickets", ticket_no) or AI_TICKETS.get(ticket_no)
    if not ticket:
        raise HTTPException(status_code=400, detail={"error": "ticket_not_found"})
    ticket["status"] = "seated"
    ticket["seated_at"] = datetime.now().isoformat(timespec="seconds")
    AI_TICKETS[ticket_no] = ticket
    db_put_json("ai_tickets", ticket_no, ticket)
    return ticket


@router.post("/booking/reservation")
def ai_book_reservation(req: ReservationRequest) -> dict[str, Any]:
    meta = restaurant_meta(req.restaurant_id)
    if not meta.get("supports_table_booking", False):
        raise HTTPException(status_code=400, detail={"error": "restaurant_does_not_support_booking"})
    if req.people_count > meta.get("max_party_size", 8):
        raise HTTPException(status_code=400, detail={"error": "party_too_large", "max_party_size": meta.get("max_party_size", 8)})
    try:
        target = datetime.fromisoformat(req.reserve_for_time)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_datetime_format"})
    reservation_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    status_value = "pending_restaurant_confirm" if meta.get("rating", 4.0) >= 4.7 else "confirmed"
    reservation = {
        "reservation_id": reservation_id,
        "restaurant_id": req.restaurant_id,
        "restaurant_name": meta.get("name", ""),
        "user_id": req.user_id,
        "people_count": req.people_count,
        "people_group": people_group(req.people_count),
        "reserve_for_time": target.isoformat(timespec="seconds"),
        "issued_at": datetime.now().isoformat(timespec="seconds"),
        "status": status_value,
        "confirm_hint": "高人气餐厅,商家会在 10 分钟内确认" if status_value.startswith("pending") else "自动确认",
        "special_requests": req.special_requests,
        "type": "reservation",
        "remind_at": (target - timedelta(minutes=30)).isoformat(timespec="seconds"),
        "arrive_window_start": (target - timedelta(minutes=5)).isoformat(timespec="seconds"),
        "arrive_window_end": (target + timedelta(minutes=15)).isoformat(timespec="seconds"),
    }
    AI_RESERVATIONS[reservation_id] = reservation
    db_put_json("ai_reservations", reservation_id, reservation)
    return reservation


@router.get("/booking/reservation/{reservation_id}")
def ai_get_reservation(reservation_id: str) -> dict[str, Any]:
    reservation = db_get_json("ai_reservations", reservation_id) or AI_RESERVATIONS.get(reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail={"error": "reservation_not_found"})
    out = dict(reservation)
    minutes_until = (datetime.fromisoformat(out["reserve_for_time"]) - datetime.now()).total_seconds() / 60
    out["minutes_until_reservation"] = round(minutes_until, 1)
    if 5 < minutes_until <= 30:
        out["reminder_status"] = "approaching"
    elif -5 <= minutes_until <= 5:
        out["reminder_status"] = "now"
    return out


@router.delete("/booking/reservation/{reservation_id}")
def ai_cancel_reservation(reservation_id: str) -> dict[str, Any]:
    reservation = db_get_json("ai_reservations", reservation_id) or AI_RESERVATIONS.get(reservation_id)
    if not reservation:
        raise HTTPException(status_code=400, detail={"error": "reservation_not_found"})
    if reservation["status"] not in ("confirmed", "pending_restaurant_confirm"):
        raise HTTPException(status_code=400, detail={"error": f"cannot_cancel_in_status_{reservation['status']}"})
    reservation["status"] = "cancelled"
    reservation["cancelled_at"] = datetime.now().isoformat(timespec="seconds")
    AI_RESERVATIONS[reservation_id] = reservation
    db_put_json("ai_reservations", reservation_id, reservation)
    return reservation


@router.get("/bookings/user/{user_id}")
def ai_user_bookings(user_id: str) -> dict[str, Any]:
    tickets = db_list_json("ai_tickets") or list(AI_TICKETS.values())
    reservations = db_list_json("ai_reservations") or list(AI_RESERVATIONS.values())
    return {
        "tickets": [
            ai_get_queue_ticket(ticket["ticket_no"])
            for ticket in tickets
            if ticket["user_id"] == user_id and ticket["status"] == "waiting"
        ],
        "reservations": [
            ai_get_reservation(reservation["reservation_id"])
            for reservation in reservations
            if reservation["user_id"] == user_id and reservation["status"] in ("confirmed", "pending_restaurant_confirm")
        ],
    }


def restaurant_meta(restaurant_id: str) -> dict[str, Any]:
    restaurants = ai_list_restaurants()
    for restaurant in restaurants:
        if restaurant.get("id") == restaurant_id:
            return restaurant
    return {
        "id": restaurant_id,
        "name": "未知餐厅",
        "base_queue_at_peak": 5,
        "queue_speed_per_minute": 0.5,
        "supports_queue_ticket": True,
        "supports_table_booking": True,
        "max_party_size": 8,
        "rating": 4.0,
    }
