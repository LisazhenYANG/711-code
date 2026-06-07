"""
TripState - LangGraph 全局状态对象。

每个节点读一部分、写一部分。重新规划/编辑模式带着它再进图。
健康禁忌只在 state 里活一次会话,不持久化(对齐 PRD 3.1)。
"""
from __future__ import annotations
from typing import TypedDict, Optional, Any
from typing_extensions import NotRequired


class Intent(TypedDict, total=False):
    """意图字段(2.1 解析输出)"""
    origin_lat: float
    origin_lng: float
    origin_name: str
    time_slot: str               # 随时 / 上午 / 下午 / 全天
    people_count: int            # 1/2/3-4/5+
    people_group: str            # 独行/情侣/小团/大队 - 由 people_count 派生
    transport_mode: str          # walk / transit / drive
    moods: list[str]             # 用户选的大类 ['休闲娱乐', '静下来']
    sub_categories: list[str]    # 用户选的小类 ['剧本杀', '窗边咖啡']
    free_text: str               # 自由文本输入
    budget_per_person: NotRequired[float]
    health_constraints: NotRequired[list[str]]  # 只活在 state,不落库
    locked_poi_ids: NotRequired[list[str]]      # 锚点
    city_code: NotRequired[str]  # 高德公交查询用,默认 "021"(上海)


class POI(TypedDict, total=False):
    id: str
    name: str
    category_main: str
    category_sub: str
    lat: float
    lng: float
    open_hours: list[list[int]]
    rank_score: float
    good_review_rate: float
    indoor: bool
    stay_minutes: int
    fit_group: list[str]
    avg_price: float
    free: bool
    need_booking: bool
    ticket_tiers: list[dict]
    tags: list[str]
    intro: str
    # 运行时附加
    score: NotRequired[float]
    score_breakdown: NotRequired[dict]
    distance_km: NotRequired[float]


class NavigationStep(TypedDict, total=False):
    """单步导航指示 - 用于在 App 内自渲染步骤列表"""
    instruction: str
    distance_m: int
    duration_s: int
    polyline: str
    road_name: str
    action: str


class Navigation(TypedDict, total=False):
    """单段路线的导航数据 - 真实路网 (Amap) 或 mock"""
    total_distance_m: int
    total_duration_s: int
    polyline: str                          # 全段折线
    steps: list[NavigationStep]
    transit_segments: NotRequired[list[dict]]  # 公交方式专属:walking + bus 混合段


class RouteStop(TypedDict, total=False):
    poi_id: str
    poi_name: str
    lat: float                  # NEW: 用于餐厅锚点定位 + 前端画地图
    lng: float                  # NEW
    category_sub: NotRequired[str]
    rank_score: NotRequired[float]
    good_review_rate: NotRequired[float]
    tags: NotRequired[list[str]]
    arrival_time: str           # "09:00"
    leave_time: str
    stay_minutes: int
    transit_to_next_minutes: int
    transit_to_next_mode: str
    transit_to_next_distance_km: NotRequired[float]
    navigation_to_next: NotRequired[Navigation]   # NEW: 真实路网导航数据
    cross_zone: bool
    locked: bool


class Route(TypedDict, total=False):
    route_id: str
    stops: list[RouteStop]
    total_commute_minutes: int
    total_score: float
    compactness: float
    quality_score: float
    zone_id: Optional[str]
    label: NotRequired[str]
    summary: NotRequired[str]
    debate_highlights: NotRequired[list[dict]]
    # === Top-3 才有的增强字段 ===
    navigation_enriched: NotRequired[bool]       # 是否已用真实路网刷过
    navigation_source: NotRequired[str]          # "amap" | "mock"
    food_recommendations: NotRequired[list[dict]]  # 餐厅推荐(按 meal_block)


class DebateMessage(TypedDict):
    agent: str
    persona_label: str
    stance: str
    target_route_id: Optional[str]
    content: str
    round: int


class TripState(TypedDict, total=False):
    # === 输入 ===
    user_id: str
    intent: Intent

    # === 加载阶段 ===
    user_profile: NotRequired[dict]
    weather: NotRequired[dict]
    follow_up_rounds: int
    follow_up_question: NotRequired[str]

    # === 算法层中间产物 ===
    reachable_radius_km: float
    time_window: NotRequired[dict]
    max_pois_per_day: int
    candidate_pool: list[POI]
    clusters: NotRequired[list[dict]]

    # === 路线候选 ===
    candidate_routes: list[Route]

    # === Agent 辩论 ===
    debate_transcript: list[DebateMessage]
    debate_rounds_completed: int

    # === 最终输出 ===
    top_routes: list[Route]
    pre_brief: NotRequired[str]

    # === 反馈通道 ===
    user_choice_route_id: NotRequired[str]
    user_deleted_poi_ids: NotRequired[list[str]]
    user_rating: NotRequired[int]

    # === 系统/降级 ===
    errors: NotRequired[list[str]]
    commute_degraded: NotRequired[bool]
    llm_degraded: NotRequired[bool]
    navigation_degraded: NotRequired[bool]    # NEW: 真实路网调用是否降级
