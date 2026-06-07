"""
FastAPI 入口。

端点:
  POST /plan                       规划路线
  POST /feedback                   写回画像
  POST /chat                       对话式路线编辑/推荐

  GET  /restaurants/{rid}/queue    查询餐厅当前队列(不取号)
  POST /booking/queue              取号
  GET  /booking/queue/{ticket_no}  查询取号状态(含到点提醒字段)
  DELETE /booking/queue/{ticket_no} 取消取号
  POST /booking/queue/{ticket_no}/seat  标记已就座
  POST /booking/reservation        预订桌位
  GET  /booking/reservation/{rid}  查预订
  DELETE /booking/reservation/{rid} 取消预订
  GET  /bookings/user/{user_id}    列出用户活跃订单(沉浸模式用)

  GET  /health
  GET  /pois
  GET  /restaurants                返回 mock 餐厅库
"""
from __future__ import annotations
import logging
import os
import json
from datetime import datetime
from typing import Optional, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from graph.builder import get_planning_graph, get_feedback_graph
from graph.nodes import (
    _load_pois,
    node_intent_parse,
    node_profile_load,
    node_reachable,
    node_time_slots,
    node_candidates,
    node_score,
    node_cluster_and_pool,
    node_route_gen,
    node_filter_rank,
)
from agents.chat import chat_reply
from providers.llm import get_llm
from providers.commute import get_default_commute_provider, AmapCommute
from providers.places import get_default_places_provider, _load_mock_restaurants
from providers import booking_mock as bm

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Travel Route Engine", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ════════════════════════════════════════════════════════════
#  Pydantic 模型
# ════════════════════════════════════════════════════════════


class IntentInput(BaseModel):
    origin_lat: float = Field(..., description="出发地纬度")
    origin_lng: float = Field(..., description="出发地经度")
    origin_name: str = "当前位置"
    time_slot: str = Field("下午", description="随时/上午/下午/全天")
    people_count: int = Field(2, ge=1, le=20)
    transport_mode: str = Field("transit", description="walk/transit/drive")
    moods: list[str] = Field(default_factory=list)
    sub_categories: list[str] = Field(default_factory=list)
    free_text: str = ""
    budget_per_person: Optional[float] = None
    locked_poi_ids: list[str] = Field(default_factory=list)
    health_constraints: list[str] = Field(default_factory=list)
    city_code: str = Field("021", description="高德公交城市编码,上海=021")


class PlanRequest(BaseModel):
    user_id: str = "anon"
    intent: IntentInput
    weather: Optional[dict] = None


class FeedbackRequest(BaseModel):
    user_id: str
    intent: Optional[dict] = None
    top_routes: list[dict] = Field(default_factory=list)
    debate_transcript: list[dict] = Field(default_factory=list)
    user_choice_route_id: Optional[str] = None
    user_deleted_poi_ids: list[str] = Field(default_factory=list)
    user_rating: Optional[int] = None


class ChatRequest(BaseModel):
    user_id: str = "anon"
    message: str = Field(..., description="用户对路线助手说的话")
    current_route: list[dict[str, Any]] = Field(default_factory=list)
    weather: Optional[dict[str, Any]] = None
    intent_context: Optional[dict[str, Any]] = None


class QueueTicketRequest(BaseModel):
    restaurant_id: str
    user_id: str
    people_count: int = Field(2, ge=1, le=20)


class ReservationRequest(BaseModel):
    restaurant_id: str
    user_id: str
    people_count: int = Field(2, ge=1, le=20)
    reserve_for_time: str = Field(..., description="ISO 8601 datetime, e.g. 2026-06-02T18:30:00")
    special_requests: str = ""


# ════════════════════════════════════════════════════════════
#  健康/库存查询
# ════════════════════════════════════════════════════════════


@app.get("/health")
def health():
    llm = get_llm()
    return {
        "ok": True,
        "llm_available": llm.available,
        "llm_model": llm.model,
        "commute_provider": type(get_default_commute_provider()).__name__,
        "places_provider": type(get_default_places_provider()).__name__,
        "amap_configured": bool(os.getenv("AMAP_API_KEY")),
    }


@app.get("/pois")
def list_pois():
    return _load_pois()


@app.get("/restaurants")
def list_restaurants(
    lat: float = 31.2304,
    lng: float = 121.4737,
    keyword: str = "",
    slot: str = "lunch",
    radius_m: int = 5000,
    limit: int = 12,
):
    """优先返回真实周边餐厅；失败或未配置时自动降级到本地库。"""
    provider = get_default_places_provider()
    meal_keyword = {
        "lunch": "午餐",
        "dinner": "晚餐",
    }.get(slot, "")
    merged_keyword = " ".join(part for part in [keyword.strip(), meal_keyword] if part).strip()
    restaurants = provider.search_around(
        center_lat=lat,
        center_lng=lng,
        keyword=merged_keyword,
        types="050000",
        radius_m=radius_m,
        max_results=max(1, min(limit, 20)),
    )
    if not restaurants and merged_keyword:
        restaurants = provider.search_around(
            center_lat=lat,
            center_lng=lng,
            keyword=keyword.strip(),
            types="050000",
            radius_m=radius_m,
            max_results=max(1, min(limit, 20)),
        )
    return restaurants


@app.get("/restaurants/{rid}/queue")
def get_restaurant_queue(rid: str):
    """查餐厅当前队列状态(不取号)。"""
    return bm.get_restaurant_current_queue(rid)


# ════════════════════════════════════════════════════════════
#  规划主图
# ════════════════════════════════════════════════════════════


@app.post("/plan")
def plan(req: PlanRequest):
    graph = get_planning_graph()
    initial = {
        "user_id": req.user_id,
        "intent": req.intent.model_dump(),
        "weather": req.weather or {"condition": "晴"},
        "follow_up_rounds": 0,
        "candidate_pool": [],
        "candidate_routes": [],
        "debate_transcript": [],
        "top_routes": [],
    }
    try:
        result = graph.invoke(initial)
    except Exception as e:
        logging.exception("plan failed")
        raise HTTPException(status_code=500, detail=str(e))
    return {
        "top_routes": result.get("top_routes", []),
        "debate_transcript": result.get("debate_transcript", []),
        "pre_brief": result.get("pre_brief", ""),
        "reachable_radius_km": result.get("reachable_radius_km"),
        "max_pois_per_day": result.get("max_pois_per_day"),
        "time_window": result.get("time_window"),
        "llm_degraded": result.get("llm_degraded", False),
        "navigation_degraded": result.get("navigation_degraded", False),
        "candidate_routes_count": len(result.get("candidate_routes", [])),
        "dropped_categories": result.get("intent", {}).get("_dropped_categories", []),
    }


@app.post("/plan/stream")
def plan_stream(req: PlanRequest):
    def emit(payload: dict[str, Any]) -> bytes:
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    def summarize_route(route: dict[str, Any]) -> list[dict[str, Any]]:
        stops = route.get("stops") or []
        return [
            {
                "name": stop.get("poi_name", ""),
                "category": stop.get("category_sub", "地点"),
                "time": stop.get("arrival_time", "待定"),
                "dur": f"约{stop.get('stay_minutes', 60)} 分",
                "meta": [],
                "imgs": [],
                "lat": stop.get("lat"),
                "lng": stop.get("lng"),
                "transitMode": stop.get("transit_to_next_mode"),
                "transitMin": stop.get("transit_to_next_minutes"),
            }
            for stop in stops
        ]

    def generate():
        yield emit({"type": "status", "message": "正在理解你的偏好..."})
        initial = {
            "user_id": req.user_id,
            "intent": req.intent.model_dump(),
            "weather": req.weather or {"condition": "晴"},
            "follow_up_rounds": 0,
            "candidate_pool": [],
            "candidate_routes": [],
            "debate_transcript": [],
            "top_routes": [],
        }
        try:
            yield emit({"type": "status", "message": "正在召回候选地点..."})
            state = dict(initial)
            state.update(node_intent_parse(state))
            state.update(node_profile_load(state))
            state.update(node_reachable(state))
            state.update(node_time_slots(state))

            yield emit({"type": "status", "message": "正在筛选合适地点..."})
            state.update(node_candidates(state))
            state.update(node_score(state))

            yield emit({"type": "status", "message": "正在生成路线..."})
            state.update(node_cluster_and_pool(state))
            state.update(node_route_gen(state))
            state.update(node_filter_rank(state))
            candidate_routes = state.get("candidate_routes") or []
            top_routes = candidate_routes[:3]
            if top_routes:
                names = [
                    stop.get("poi_name", "")
                    for stop in top_routes[0].get("stops", [])
                    if stop.get("poi_name")
                ]
                pre_brief = "我先帮你整理出一版路线：" + " -> ".join(names[:3])
            else:
                pre_brief = "这次没有筛出合适路线。"
            result = {
                **state,
                "top_routes": top_routes,
                "pre_brief": pre_brief,
                "debate_transcript": [],
                "llm_degraded": True,
                "navigation_degraded": True,
            }
        except Exception as e:
            logging.exception("plan stream failed")
            yield emit({"type": "error", "message": str(e)})
            return

        route = (result.get("top_routes") or [{}])[0]
        stops = summarize_route(route) if route else []
        yield emit({"type": "status", "message": "正在整理推荐路线..."})
        yield emit(
            {
                "type": "final",
                "message": result.get("pre_brief", "我已经整理好一版今日路线。"),
                "payload": {
                    "stops": stops,
                    "candidate_routes_count": len(result.get("candidate_routes", [])),
                },
            }
        )

    return StreamingResponse(generate(), media_type="application/x-ndjson")


@app.post("/feedback")
def feedback(req: FeedbackRequest):
    graph = get_feedback_graph()
    initial = {
        "user_id": req.user_id,
        "intent": req.intent or {},
        "top_routes": req.top_routes,
        "debate_transcript": req.debate_transcript,
        "user_choice_route_id": req.user_choice_route_id,
        "user_deleted_poi_ids": req.user_deleted_poi_ids,
        "user_rating": req.user_rating,
    }
    try:
        result = graph.invoke(initial)
    except Exception as e:
        logging.exception("feedback failed")
        raise HTTPException(status_code=500, detail=str(e))
    return {"ok": True, "updated_profile": result.get("user_profile")}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        return chat_reply(
            user_id=req.user_id,
            message=req.message,
            current_route=req.current_route,
            weather=req.weather or {"condition": "晴"},
            intent_context=req.intent_context or {},
        )
    except Exception as e:
        logging.exception("chat failed")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def emit(payload: dict[str, Any]) -> bytes:
        return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")

    def generate():
        yield emit({"type": "status", "message": "正在理解你的需求..."})
        if req.current_route:
            yield emit({"type": "status", "message": "正在结合当前路线寻找更合适的调整..."})
        else:
            yield emit({"type": "status", "message": "正在召回候选地点并生成路线..."})
        try:
            result = chat_reply(
                user_id=req.user_id,
                message=req.message,
                current_route=req.current_route,
                weather=req.weather or {"condition": "晴"},
                intent_context=req.intent_context or {},
            )
        except Exception as e:
            logging.exception("chat stream failed")
            yield emit({"type": "error", "message": str(e)})
            return
        yield emit({"type": "status", "message": "正在整理回复..."})
        yield emit(
            {
                "type": "final",
                "message": result.get("reply", "我已经处理好了。"),
                "payload": result,
            }
        )

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ════════════════════════════════════════════════════════════
#  Booking - 取号 (queue_ticket)
# ════════════════════════════════════════════════════════════


@app.post("/booking/queue")
def book_queue(req: QueueTicketRequest):
    t = bm.take_queue_ticket(req.restaurant_id, req.user_id, req.people_count)
    if "error" in t:
        raise HTTPException(status_code=400, detail=t)
    return t


@app.get("/booking/queue/{ticket_no}")
def get_queue_ticket(ticket_no: str):
    t = bm.get_ticket(ticket_no)
    if not t:
        raise HTTPException(status_code=404, detail={"error": "ticket_not_found"})
    return t


@app.delete("/booking/queue/{ticket_no}")
def cancel_queue_ticket(ticket_no: str):
    r = bm.cancel_ticket(ticket_no)
    if "error" in r:
        raise HTTPException(status_code=400, detail=r)
    return r


@app.post("/booking/queue/{ticket_no}/seat")
def seat_queue_ticket(ticket_no: str):
    r = bm.mark_ticket_seated(ticket_no)
    if "error" in r:
        raise HTTPException(status_code=400, detail=r)
    return r


# ════════════════════════════════════════════════════════════
#  Booking - 预订 (reservation)
# ════════════════════════════════════════════════════════════


@app.post("/booking/reservation")
def book_reservation(req: ReservationRequest):
    try:
        target = datetime.fromisoformat(req.reserve_for_time)
    except ValueError:
        raise HTTPException(status_code=400, detail={"error": "invalid_datetime_format"})
    r = bm.reserve_table(
        req.restaurant_id, req.user_id, req.people_count,
        target, req.special_requests,
    )
    if "error" in r:
        raise HTTPException(status_code=400, detail=r)
    return r


@app.get("/booking/reservation/{reservation_id}")
def get_reservation(reservation_id: str):
    r = bm.get_reservation(reservation_id)
    if not r:
        raise HTTPException(status_code=404, detail={"error": "reservation_not_found"})
    return r


@app.delete("/booking/reservation/{reservation_id}")
def cancel_reservation(reservation_id: str):
    r = bm.cancel_reservation(reservation_id)
    if "error" in r:
        raise HTTPException(status_code=400, detail=r)
    return r


# ════════════════════════════════════════════════════════════
#  Booking - 用户活跃订单 (沉浸模式用)
# ════════════════════════════════════════════════════════════


@app.get("/bookings/user/{user_id}")
def user_bookings(user_id: str):
    """沉浸模式定时拉取,根据 ready_to_call / minutes_until_reservation
    判断是否要给用户推提醒。"""
    return bm.list_user_bookings(user_id)
