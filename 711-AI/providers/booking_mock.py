"""
Mock 取号 + 预订系统。

两条产品线:
1. 取号 (queue ticket) - 立即排队,等叫号
2. 预订 (reservation)  - 指定时间预订桌位

数据持久化 → data/booking_tickets.json (跟 user_profiles 同等级)

队列动力学:
- 每家餐厅有 base_queue_at_peak、queue_speed_per_minute (从 mock_restaurants.json 读)
- 取号时 current_queue +1,新票 queue_position = current_queue
- 查询时按 (now - issued_at) × queue_speed 自动衰减,模拟前面桌进店
- estimated_call_time = issued_at + queue_position / queue_speed_per_minute 分钟

为「沉浸模式」的实时提醒预留字段:
- estimated_call_time 让前端可以提前 N 分钟提醒
- ticket 和 reservation 都有 status 状态机,前端轮询查变化

本期不做真实推送,但数据结构和接口能直接对接。
"""
from __future__ import annotations
import json
import os
import threading
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Optional
import logging

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()


# ─────────────────────────────────────────────────────────────
#  存储 - JSON 文件
# ─────────────────────────────────────────────────────────────


def _store_path() -> Path:
    p = os.getenv("BOOKING_STORE_PATH", "./data/booking_tickets.json")
    return Path(p)


_EMPTY = {
    "tickets": {},          # ticket_no → ticket dict
    "reservations": {},     # reservation_id → reservation dict
    "restaurant_state": {}, # restaurant_id → {current_queue, last_calls, last_updated_ts}
}


def _read_all() -> dict:
    path = _store_path()
    if not path.exists():
        return {**_EMPTY, "tickets": {}, "reservations": {}, "restaurant_state": {}}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for k in ("tickets", "reservations", "restaurant_state"):
            data.setdefault(k, {})
        return data
    except (json.JSONDecodeError, OSError):
        return {**_EMPTY, "tickets": {}, "reservations": {}, "restaurant_state": {}}


def _write_all(data: dict) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


# ─────────────────────────────────────────────────────────────
#  Restaurant 静态数据(用来读默认队列速度等)
# ─────────────────────────────────────────────────────────────


_RESTAURANT_CACHE: dict | None = None


def _load_restaurants() -> dict:
    global _RESTAURANT_CACHE
    if _RESTAURANT_CACHE is not None:
        return _RESTAURANT_CACHE
    path = Path(__file__).parent.parent / "data" / "mock_restaurants.json"
    if not path.exists():
        _RESTAURANT_CACHE = {}
        return _RESTAURANT_CACHE
    with path.open("r", encoding="utf-8") as f:
        arr = json.load(f)
    _RESTAURANT_CACHE = {r["id"]: r for r in arr}
    return _RESTAURANT_CACHE


def _restaurant_meta(rid: str) -> dict:
    """返回餐厅的 mock 元数据。若是 amap 返回的 id 走默认值。"""
    rmap = _load_restaurants()
    if rid in rmap:
        return rmap[rid]
    # amap POI id 走默认
    return {
        "id": rid,
        "name": "未知餐厅",
        "base_queue_at_peak": 5,
        "queue_speed_per_minute": 0.5,
        "supports_queue_ticket": True,
        "supports_table_booking": True,
    }


# ─────────────────────────────────────────────────────────────
#  时间工具 - 决定餐厅当前的 base queue
# ─────────────────────────────────────────────────────────────


def _is_peak_hour(now: datetime | None = None) -> bool:
    """11:30-13:30 和 17:30-19:30 视为高峰。"""
    now = now or datetime.now()
    h = now.hour + now.minute / 60.0
    return (11.5 <= h <= 13.5) or (17.5 <= h <= 19.5)


def _current_queue_for(rid: str, now: datetime | None = None) -> int:
    """根据时间和店本身的 base 算当前队列。
    高峰期 = base_queue;平峰 = base // 3。"""
    meta = _restaurant_meta(rid)
    base = meta.get("base_queue_at_peak", 5)
    if _is_peak_hour(now):
        return base
    return max(0, base // 3)


# ─────────────────────────────────────────────────────────────
#  取号 (queue ticket)
# ─────────────────────────────────────────────────────────────


def take_queue_ticket(
    restaurant_id: str,
    user_id: str,
    people_count: int,
    issued_at: datetime | None = None,
) -> dict:
    """立即取号。返回 ticket dict。"""
    issued_at = issued_at or datetime.now()
    meta = _restaurant_meta(restaurant_id)
    if not meta.get("supports_queue_ticket", True):
        return {"error": "restaurant_does_not_support_queue", "restaurant_id": restaurant_id}

    with _LOCK:
        data = _read_all()
        # 餐厅当前队列状态
        rstate = data["restaurant_state"].get(restaurant_id) or {}
        # 自动衰减历史队列
        baseline = _current_queue_for(restaurant_id, issued_at)
        if rstate:
            last_ts = rstate.get("last_updated_ts", 0)
            elapsed_min = max(0.0, (issued_at.timestamp() - last_ts) / 60.0)
            decayed = max(0, rstate.get("current_queue", baseline) - int(elapsed_min * meta.get("queue_speed_per_minute", 0.5)))
            # 但不能低于 baseline,因为新顾客会持续来
            current_queue = max(decayed, baseline) if rstate.get("current_queue", 0) > 0 else baseline
        else:
            current_queue = baseline

        # 加上当前这位用户
        new_position = current_queue + 1
        # 生成票号 - 字母 + 编号
        prefix = "Q" if not _is_peak_hour(issued_at) else "A"
        ticket_no = f"{prefix}{new_position:03d}-{restaurant_id[-3:]}"
        speed = meta.get("queue_speed_per_minute", 0.5) or 0.5
        wait_minutes = new_position / speed
        estimated_call_time = issued_at + timedelta(minutes=wait_minutes)

        ticket = {
            "ticket_no": ticket_no,
            "restaurant_id": restaurant_id,
            "restaurant_name": meta.get("name", ""),
            "user_id": user_id,
            "people_count": people_count,
            "people_group": _people_group(people_count),
            "issued_at": issued_at.isoformat(timespec="seconds"),
            "queue_position_at_issue": new_position,
            "status": "waiting",
            "estimated_wait_minutes": round(wait_minutes, 1),
            "estimated_call_time": estimated_call_time.isoformat(timespec="seconds"),
            "queue_speed_per_minute": speed,
            "type": "queue_ticket",
        }
        data["tickets"][ticket_no] = ticket
        data["restaurant_state"][restaurant_id] = {
            "current_queue": new_position,
            "last_updated_ts": issued_at.timestamp(),
        }
        _write_all(data)
        return ticket


def get_ticket(ticket_no: str, now: datetime | None = None) -> dict | None:
    """查询票,返回最新状态(队列前进了多少)。"""
    now = now or datetime.now()
    with _LOCK:
        data = _read_all()
        t = data["tickets"].get(ticket_no)
        if not t:
            return None
        if t["status"] != "waiting":
            return t  # 已完成态直接返回

        meta = _restaurant_meta(t["restaurant_id"])
        speed = meta.get("queue_speed_per_minute", 0.5) or 0.5
        issued = datetime.fromisoformat(t["issued_at"])
        elapsed_min = max(0.0, (now - issued).total_seconds() / 60.0)
        moved = int(elapsed_min * speed)
        remaining = max(0, t["queue_position_at_issue"] - moved)
        wait_left = remaining / speed
        estimated_call = issued + timedelta(minutes=t["queue_position_at_issue"] / speed)

        t_out = dict(t)
        t_out["queue_position_now"] = remaining
        t_out["estimated_wait_remaining_minutes"] = round(wait_left, 1)
        t_out["estimated_call_time"] = estimated_call.isoformat(timespec="seconds")

        # 如果已到点附近,标记 ready_to_call(沉浸模式提醒用)
        if remaining == 0:
            t_out["ready_to_call"] = True
        elif remaining <= 2 or wait_left <= 5:
            t_out["ready_to_call"] = "approaching"  # 还有 2 桌内 或 5 分钟内
        else:
            t_out["ready_to_call"] = False

        return t_out


def cancel_ticket(ticket_no: str) -> dict:
    """取消票。"""
    with _LOCK:
        data = _read_all()
        t = data["tickets"].get(ticket_no)
        if not t:
            return {"error": "ticket_not_found", "ticket_no": ticket_no}
        if t["status"] != "waiting":
            return {"error": f"cannot_cancel_in_status_{t['status']}", "ticket_no": ticket_no}
        t["status"] = "cancelled"
        t["cancelled_at"] = datetime.now().isoformat(timespec="seconds")
        data["tickets"][ticket_no] = t
        _write_all(data)
        return t


def mark_ticket_seated(ticket_no: str) -> dict:
    """手动标记已就座(沉浸模式或前端按钮触发)。"""
    with _LOCK:
        data = _read_all()
        t = data["tickets"].get(ticket_no)
        if not t:
            return {"error": "ticket_not_found"}
        t["status"] = "seated"
        t["seated_at"] = datetime.now().isoformat(timespec="seconds")
        data["tickets"][ticket_no] = t
        _write_all(data)
        return t


# ─────────────────────────────────────────────────────────────
#  预订 (reservation)
# ─────────────────────────────────────────────────────────────


def reserve_table(
    restaurant_id: str,
    user_id: str,
    people_count: int,
    reserve_for_time: datetime,
    special_requests: str = "",
) -> dict:
    """预订指定时间的桌位。"""
    meta = _restaurant_meta(restaurant_id)
    if not meta.get("supports_table_booking", False):
        return {"error": "restaurant_does_not_support_booking", "restaurant_id": restaurant_id}
    max_party = meta.get("max_party_size", 8)
    if people_count > max_party:
        return {"error": "party_too_large", "max_party_size": max_party, "your_count": people_count}

    reservation_id = f"R-{uuid.uuid4().hex[:8].upper()}"
    issued_at = datetime.now()

    # 给一个 fake confirmation status:超过 95% 评分的店"待商家确认",其他"已自动确认"
    rating = meta.get("rating", 4.0)
    if rating >= 4.7:
        status = "pending_restaurant_confirm"
        confirm_hint = "高人气餐厅,商家会在 10 分钟内确认"
    else:
        status = "confirmed"
        confirm_hint = "自动确认"

    reservation = {
        "reservation_id": reservation_id,
        "restaurant_id": restaurant_id,
        "restaurant_name": meta.get("name", ""),
        "user_id": user_id,
        "people_count": people_count,
        "people_group": _people_group(people_count),
        "reserve_for_time": reserve_for_time.isoformat(timespec="seconds"),
        "issued_at": issued_at.isoformat(timespec="seconds"),
        "status": status,
        "confirm_hint": confirm_hint,
        "special_requests": special_requests,
        "type": "reservation",
        # 沉浸模式接入字段
        "remind_at": (reserve_for_time - timedelta(minutes=30)).isoformat(timespec="seconds"),
        "arrive_window_start": (reserve_for_time - timedelta(minutes=5)).isoformat(timespec="seconds"),
        "arrive_window_end": (reserve_for_time + timedelta(minutes=15)).isoformat(timespec="seconds"),
    }
    with _LOCK:
        data = _read_all()
        data["reservations"][reservation_id] = reservation
        _write_all(data)
    return reservation


def get_reservation(reservation_id: str, now: datetime | None = None) -> dict | None:
    """查询预订。如果是 pending_restaurant_confirm 且过了 10 分钟,自动转 confirmed。"""
    now = now or datetime.now()
    with _LOCK:
        data = _read_all()
        r = data["reservations"].get(reservation_id)
        if not r:
            return None
        # 自动转换状态
        if r["status"] == "pending_restaurant_confirm":
            issued = datetime.fromisoformat(r["issued_at"])
            if (now - issued).total_seconds() > 600:
                r["status"] = "confirmed"
                r["confirm_hint"] = "已确认"
                data["reservations"][reservation_id] = r
                _write_all(data)
        # 计算"距离用餐时间"
        target = datetime.fromisoformat(r["reserve_for_time"])
        minutes_until = (target - now).total_seconds() / 60.0
        r_out = dict(r)
        r_out["minutes_until_reservation"] = round(minutes_until, 1)
        if minutes_until <= 30 and minutes_until > 5:
            r_out["reminder_status"] = "approaching"
        elif -5 <= minutes_until <= 5:
            r_out["reminder_status"] = "now"
        elif minutes_until < -15:
            # 过了预订时间太久,no_show
            if r["status"] == "confirmed":
                r["status"] = "no_show"
                data["reservations"][reservation_id] = r
                _write_all(data)
            r_out["status"] = r["status"]
        return r_out


def cancel_reservation(reservation_id: str) -> dict:
    with _LOCK:
        data = _read_all()
        r = data["reservations"].get(reservation_id)
        if not r:
            return {"error": "reservation_not_found"}
        if r["status"] not in ("confirmed", "pending_restaurant_confirm"):
            return {"error": f"cannot_cancel_in_status_{r['status']}"}
        r["status"] = "cancelled"
        r["cancelled_at"] = datetime.now().isoformat(timespec="seconds")
        data["reservations"][reservation_id] = r
        _write_all(data)
        return r


# ─────────────────────────────────────────────────────────────
#  辅助
# ─────────────────────────────────────────────────────────────


def list_user_bookings(user_id: str) -> dict:
    """列出某用户所有有效的票和预订(沉浸模式查询全部活跃订单用)。"""
    with _LOCK:
        data = _read_all()
    active_tickets = [
        get_ticket(no) for no, t in data["tickets"].items()
        if t.get("user_id") == user_id and t["status"] == "waiting"
    ]
    active_tickets = [t for t in active_tickets if t]
    active_reservations = [
        get_reservation(rid) for rid, r in data["reservations"].items()
        if r.get("user_id") == user_id and r["status"] in ("confirmed", "pending_restaurant_confirm")
    ]
    active_reservations = [r for r in active_reservations if r]
    return {
        "tickets": active_tickets,
        "reservations": active_reservations,
    }


def get_restaurant_current_queue(restaurant_id: str, now: datetime | None = None) -> dict:
    """对外查询餐厅当前队列长度,不取号。前端推荐结果展示用。"""
    now = now or datetime.now()
    meta = _restaurant_meta(restaurant_id)
    speed = meta.get("queue_speed_per_minute", 0.5) or 0.5
    with _LOCK:
        data = _read_all()
        rstate = data["restaurant_state"].get(restaurant_id) or {}
    baseline = _current_queue_for(restaurant_id, now)
    if rstate:
        last_ts = rstate.get("last_updated_ts", 0)
        elapsed_min = max(0.0, (now.timestamp() - last_ts) / 60.0)
        decayed = max(0, rstate.get("current_queue", baseline) - int(elapsed_min * speed))
        current = max(decayed, baseline)
    else:
        current = baseline
    return {
        "restaurant_id": restaurant_id,
        "current_queue": current,
        "estimated_wait_minutes": round(current / speed, 1) if current else 0,
        "is_peak_hour": _is_peak_hour(now),
    }


def _people_group(count: int) -> str:
    if count <= 1: return "独行"
    if count == 2: return "情侣"
    if count <= 4: return "小团"
    return "大队"
