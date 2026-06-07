"""
时间预算与可达圈 - PRD 五.2 时间填充逻辑 + 我们补的"类别超额砍掉垫底"。
"""
from __future__ import annotations
from datetime import datetime


# 基础半径(km) - 三档,对齐我们这次定的方案
BASE_RADIUS = {
    "walk": 2.0,
    "transit": 13.0,    # 公共交通 10-15 取中
    "drive": 12.0,
}

# 时间系数 - 基于可用时间(小时)
def time_coefficient(available_hours: float) -> float:
    if available_hours > 6:
        return 1.5
    if available_hours >= 3:
        return 1.0
    return 0.6


def compute_reachable_radius_km(
    transport_mode: str, available_hours: float
) -> float:
    base = BASE_RADIUS.get(transport_mode, BASE_RADIUS["transit"])
    return base * time_coefficient(available_hours)


# 时间窗口
TIME_WINDOWS = {
    "随时": None,        # 取当前时间向上取整到下一个整点 -> 21:00
    "上午": (9, 13),
    "下午": (13, 21),
    "全天": (9, 21),
}

# 餐饮时段(start_hour, end_hour),不占 POI 配额
FOOD_BLOCKS = [(12, 13.5), (18, 19.5)]


def compute_time_window(
    time_slot: str, now_hour: float | None = None
) -> dict:
    """返回 {start, end, available_hours, food_blocks_within}"""
    if time_slot == "随时":
        cur = now_hour if now_hour is not None else datetime.now().hour
        start = float(int(cur) + 1)  # 向上取整
        end = 21.0
    elif time_slot in TIME_WINDOWS and TIME_WINDOWS[time_slot]:
        start, end = TIME_WINDOWS[time_slot]
        start, end = float(start), float(end)
    else:
        start, end = 13.0, 21.0

    if end <= start:
        end = start + 1.0  # 最少 1 小时,避免负数

    food_within = [
        (max(fs, start), min(fe, end))
        for fs, fe in FOOD_BLOCKS
        if fe > start and fs < end
    ]
    food_within = [(s, e) for s, e in food_within if e > s]

    return {
        "start": start,
        "end": end,
        "available_hours": end - start,
        "food_blocks_within": food_within,
    }


def compute_max_pois(
    time_window: dict,
    avg_stay_minutes: float = 75,
    commute_minutes_per_segment: float = 20,
    activity_ratio: float = 0.85,
) -> int:
    """
    可排 POI 数 = floor(纯POI可用时间 × 85% / (平均停留 + 通勤))

    PRD: 规划阶段通勤预估值取 20 分钟/段。
    """
    food_minutes = sum((e - s) * 60 for s, e in time_window["food_blocks_within"])
    pure_minutes = time_window["available_hours"] * 60 - food_minutes
    if pure_minutes <= 0:
        return 0
    capacity_minutes = pure_minutes * activity_ratio
    per_poi = avg_stay_minutes + commute_minutes_per_segment
    return max(0, int(capacity_minutes // per_poi))


def trim_excess_categories(
    selected_categories: list[str],
    max_pois: int,
    category_top_scores: dict[str, float],
) -> tuple[list[str], list[str]]:
    """
    当用户选的类别数 > 可排数时,按"该类别下最高 POI 得分"砍掉垫底类别。
    返回 (保留的类别, 被砍掉的类别)。

    呼应 PRD"选太多->根据平均游玩时间精简"。
    """
    if len(selected_categories) <= max_pois:
        return selected_categories, []
    ranked = sorted(
        selected_categories,
        key=lambda c: category_top_scores.get(c, 0.0),
        reverse=True,
    )
    kept = ranked[:max_pois]
    dropped = ranked[max_pois:]
    return kept, dropped
