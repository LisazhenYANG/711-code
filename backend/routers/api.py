from __future__ import annotations

from datetime import datetime
from typing import Any
import uuid

from fastapi import APIRouter, HTTPException, Request, status

from backend.data.seeds import (
    MEALS,
    MEAL_SLOTS,
    RECOMMENDATIONS,
    SPOTS,
    USER_PROFILES,
    VENUE_CATEGORIES,
)
from backend.db import db_delete_json, db_get_json, db_list_json, db_put_json
from backend.schemas import (
    BookingCheckoutRequest,
    FeedbackRequest,
    RouteActionRequest,
    RouteGenerateRequest,
    TripCreateRequest,
)
from backend.services.app_state import (
    apply_route_action,
    load_app_state,
    save_app_state,
)
from backend.services.planning import (
    booking_type,
    generate_route_options,
    outfit,
    seed_bookings,
    todos_for_route,
    weather,
)


router = APIRouter()
TRIPS: dict[str, dict[str, Any]] = {}
FEEDBACK: list[dict[str, Any]] = []


@router.get("/api/health")
def health(request: Request) -> dict[str, Any]:
    return {
        "ok": True,
        "service": "manyou-backend",
        "version": request.app.version,
    }


@router.get("/api/catalog")
def catalog() -> dict[str, Any]:
    return {
        "spots": SPOTS,
        "venue_categories": VENUE_CATEGORIES,
        "meal_slots": MEAL_SLOTS,
        "meals": MEALS,
    }


@router.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    state = load_app_state()
    active_plan = state["active_plan"]
    trips = state.get("history", [])
    return {
        "weather": weather("上海"),
        "location": "上海·静安区",
        "date": "6月6日 周六",
        "active_plan": active_plan,
        "locked_indexes": state.get("locked_indexes", [0]),
        "hidden_indexes": state.get("hidden_indexes", []),
        "bookings": state.get("bookings", seed_bookings(active_plan["route"])),
        "packing_list": state.get("packing_list", ["预约二维码", "充电宝", "轻便鞋", "小伞"]),
        "history": trips,
        "recommendations": RECOMMENDATIONS,
        "last_action": state.get("last_action"),
    }


@router.get("/api/recommendations")
def recommendations() -> dict[str, Any]:
    return {"recommendations": RECOMMENDATIONS}


@router.get("/api/preferences/{user_id}")
def user_preferences(user_id: str) -> dict[str, Any]:
    profile = USER_PROFILES.get(user_id) or USER_PROFILES["demo"]
    return {"user_id": user_id, **profile}


@router.post("/api/route/action")
def route_action(req: RouteActionRequest) -> dict[str, Any]:
    return apply_route_action(req)


@router.post("/api/routes/generate")
def generate_routes(req: RouteGenerateRequest) -> dict[str, Any]:
    generated = generate_route_options(req)
    base_stops = generated["routes"][0]["stops"]
    state = load_app_state()
    state["active_plan"]["route"] = base_stops
    state["active_plan"]["todos"] = todos_for_route(base_stops)
    state["locked_indexes"] = [0]
    state["hidden_indexes"] = []
    state["bookings"] = seed_bookings(base_stops)
    state["last_action"] = {
        "type": "generate_route",
        "at": datetime.now().isoformat(timespec="seconds"),
    }
    save_app_state(state)
    return generated


@router.post("/api/bookings/checkout")
def checkout(req: BookingCheckoutRequest) -> dict[str, Any]:
    results = []
    for item in req.items:
        product = item.selected_product
        paid = item.paid or bool(product)
        ticket_no = uuid.uuid4().hex[:8].upper()
        results.append(
            {
                "name": item.name,
                "category": item.category,
                "bookingType": item.booking_type or booking_type(item.category),
                "status": "purchased" if paid else "pending",
                "code": f"QR-2026-{ticket_no}" if paid else None,
                "qr": paid,
                "ticketTime": item.time,
                "ticketPrice": product.price if product else "",
                "selectedProduct": product.model_dump() if product else None,
            }
        )
    packing = ["身份证", "学生证", "充电宝", "雨伞", "水", "纸巾"]
    if results:
        packing.append("预约二维码/购票凭证")
    state = load_app_state()
    current_bookings = state.get("bookings", [])
    merged = []
    for idx, result in enumerate(results):
        icon = current_bookings[idx].get("icon") if idx < len(current_bookings) else None
        merged.append({"icon": icon, "statusText": "已购票" if result["qr"] else "待确认", **result})
    state["bookings"] = merged
    state["packing_list"] = packing
    state["last_action"] = {"type": "checkout", "at": datetime.now().isoformat(timespec="seconds")}
    save_app_state(state)
    return {"trip_id": req.trip_id, "results": merged, "packing_list": packing}


@router.post("/api/trips", status_code=status.HTTP_201_CREATED)
def create_trip(req: TripCreateRequest) -> dict[str, Any]:
    trip_id = f"trip-{uuid.uuid4().hex[:8]}"
    trip = {
        "id": trip_id,
        "title": req.title,
        "city": req.city,
        "date": req.date,
        "createdAt": datetime.now().isoformat(),
        "route": req.route,
        "weather": req.weather or weather(req.city),
        "outfit": req.outfit or outfit(),
        "bookingChecklist": req.booking_checklist,
        "bookingResults": req.booking_results,
        "packingList": req.packing_list,
        "chatHistory": req.chat_history,
    }
    TRIPS[trip_id] = trip
    db_put_json("trips", trip_id, trip)
    return trip


@router.get("/api/trips")
def list_trips() -> dict[str, Any]:
    trips = db_list_json("trips") or list(TRIPS.values())
    return {"trips": trips}


@router.get("/api/trips/{trip_id}")
def get_trip(trip_id: str) -> dict[str, Any]:
    trip = db_get_json("trips", trip_id) or TRIPS.get(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail={"error": "trip_not_found"})
    return trip


@router.delete("/api/trips/{trip_id}")
def delete_trip(trip_id: str) -> dict[str, Any]:
    deleted = db_delete_json("trips", trip_id)
    if trip_id in TRIPS:
        del TRIPS[trip_id]
        deleted = True
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "trip_not_found"})
    return {"ok": True}


@router.post("/api/feedback")
def save_feedback(req: FeedbackRequest) -> dict[str, Any]:
    item = req.model_dump()
    item["createdAt"] = datetime.now().isoformat()
    FEEDBACK.append(item)
    db_put_json("feedback", uuid.uuid4().hex, item)
    return {"ok": True, "feedback_count": len(db_list_json("feedback"))}
