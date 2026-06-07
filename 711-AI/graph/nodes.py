"""
LangGraph 节点 - 全部串起来。

每个节点签名: (state: TripState) -> dict (partial state update)
LangGraph 会自动合并返回的 partial state 到 state 上。
"""
from __future__ import annotations
import json
import logging
import os
from itertools import combinations
from pathlib import Path
from typing import Optional

from state import TripState, Intent, POI, Route, RouteStop, DebateMessage
from algorithm.geo import (
    haversine_km, adaptive_kmeans, cluster_visit_order,
    two_opt, route_overlap_ratio, compactness_score,
)
from algorithm.scoring import (
    ScoringWeights, score_poi, people_count_to_group,
)
from algorithm.time_budget import (
    compute_reachable_radius_km, compute_time_window,
    compute_max_pois, trim_excess_categories,
)
from providers.commute import CommuteProvider, get_default_commute_provider
from providers.embedding import get_embedder
from providers.llm import get_llm
from providers.places import PlacesProvider, get_default_places_provider
from profile.store import load_profile, save_profile
from profile.schema import UserProfile
from profile.ema import (
    update_agent_weight, update_distance_sensitivity,
    update_satisfaction, mark_loved_category,
    mark_disliked_poi, mark_loved_poi,
)
from agents.debate import run_debate
from algorithm.food_recommend import recommend_for_route

logger = logging.getLogger(__name__)

_SUB_CATEGORY_ALIASES = {
    "咖啡": "窗边咖啡",
    "咖啡馆": "窗边咖啡",
    "喝咖啡": "窗边咖啡",
    "coffee": "窗边咖啡",
    "cafe": "窗边咖啡",
    "展": "文化艺术",
    "展览": "文化艺术",
    "艺术展": "文化艺术",
    "手工坊": "DIY工坊",
    "手作": "DIY工坊",
    "diy": "DIY工坊",
    "桌游": "剧本杀",
    "桌面游戏": "剧本杀",
    "电影": "私人影院",
    "影院": "私人影院",
    "美术馆": "文化艺术",
    "博物馆": "文化艺术",
    "书店": "图书馆",
    "看书": "图书馆",
    "图书": "图书馆",
}

_MAIN_CATEGORY_ALIASES = {
    "城市漫游": "热门打卡",
    "citywalk": "热门打卡",
    "拍照": "热门打卡",
    "出片": "热门打卡",
    "放松": "静下来",
}


def _normalize_terms(terms: list[str], aliases: dict[str, str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for term in terms or []:
        value = aliases.get(str(term).strip(), str(term).strip())
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized


# ════════════════════════════════════════════════════════════
#  POI 库加载(全局,启动时一次)
# ════════════════════════════════════════════════════════════

_POIS: list[POI] | None = None
_POI_EMBEDDINGS: dict[str, dict[str, float]] | None = None


def _load_pois() -> list[POI]:
    global _POIS, _POI_EMBEDDINGS
    if _POIS is not None:
        return _POIS
    path = Path(__file__).parent.parent / "data" / "mock_pois.json"
    with path.open("r", encoding="utf-8") as f:
        _POIS = json.load(f)
    embedder = get_embedder()
    _POI_EMBEDDINGS = {p["id"]: embedder.encode_poi(p) for p in _POIS}
    return _POIS


# ════════════════════════════════════════════════════════════
#  ① 意图解析
# ════════════════════════════════════════════════════════════

REQUIRED_FIELDS = ["origin_lat", "origin_lng", "time_slot", "people_count"]


def node_intent_parse(state: TripState) -> dict:
    """
    HTML 已经给到结构化 chips,这里主要做:
    1. 校验必填
    2. 派生 people_group
    3. 用 LLM 把自由文本拆出额外字段(预算/期望打卡点/健康禁忌等)
    4. 如缺必填 且追问 <2 轮 -> 走追问分支(由条件边决定)
    """
    intent: Intent = dict(state.get("intent", {}))  # copy
    follow_ups = state.get("follow_up_rounds", 0)

    # 派生 people_group
    if "people_count" in intent and "people_group" not in intent:
        intent["people_group"] = people_count_to_group(intent["people_count"])

    # 自由文本解析(如果 LLM 可用)
    free_text = intent.get("free_text", "").strip()
    llm = get_llm()
    if free_text and llm.available:
        try:
            messages = [
                {"role": "system", "content":
                 "你是意图解析器。从用户的自由文本里抽取以下字段,返回 JSON:\n"
                 "{budget_per_person: 数字或null, locked_pois: 字符串数组(用户明确说必须去的点),"
                 " health_constraints: 数组(如'膝盖不好''心脏病'),"
                 " sub_categories_extra: 数组(用户提到的小类如'剧本杀''咖啡'),"
                 " preference_keywords: 数组(如'少赶路''想出片')}\n"
                 "无法识别的字段返回 null 或空数组。"
                },
                {"role": "user", "content": free_text},
            ]
            parsed = llm.chat_json(messages, temperature=0.1, max_tokens=800)
            if parsed.get("budget_per_person"):
                intent["budget_per_person"] = float(parsed["budget_per_person"])
            if parsed.get("health_constraints"):
                intent["health_constraints"] = parsed["health_constraints"]
            if parsed.get("sub_categories_extra"):
                existing = set(intent.get("sub_categories", []))
                existing.update(parsed["sub_categories_extra"])
                intent["sub_categories"] = list(existing)
            # preference_keywords 不写进 intent,留给 RAG 用 free_text 本身
        except Exception as e:
            logger.warning("意图解析 LLM 失败,跳过: %s", e)

    # 必填校验
    missing = [f for f in REQUIRED_FIELDS if f not in intent or intent[f] in (None, "")]
    if missing and follow_ups < 2:
        return {
            "intent": intent,
            "follow_up_rounds": follow_ups + 1,
            "follow_up_question": f"还差几个信息: {', '.join(missing)}。能补充一下吗?",
        }
    # 超 2 轮就用默认值兜底
    if "time_slot" not in intent:
        intent["time_slot"] = "下午"
    if "people_count" not in intent:
        intent["people_count"] = 2
        intent["people_group"] = "情侣"
    if "transport_mode" not in intent:
        intent["transport_mode"] = "transit"
    if "moods" not in intent:
        intent["moods"] = []
    if "sub_categories" not in intent:
        intent["sub_categories"] = []
    intent["moods"] = _normalize_terms(intent.get("moods") or [], _MAIN_CATEGORY_ALIASES)
    intent["sub_categories"] = _normalize_terms(
        intent.get("sub_categories") or [], _SUB_CATEGORY_ALIASES
    )

    return {"intent": intent, "follow_up_question": ""}


def should_followup(state: TripState) -> str:
    """条件边:决定是否回到追问。"""
    if state.get("follow_up_question"):
        return "followup"
    return "proceed"


# ════════════════════════════════════════════════════════════
#  ② 用户画像加载
# ════════════════════════════════════════════════════════════

def node_profile_load(state: TripState) -> dict:
    user_id = state.get("user_id", "anon")
    profile = load_profile(user_id)
    return {"user_profile": profile.to_dict()}


# ════════════════════════════════════════════════════════════
#  ③ 可达圈
# ════════════════════════════════════════════════════════════

def node_reachable(state: TripState) -> dict:
    intent = state["intent"]
    # 简单 hours 估算(基于 time_slot)
    slot_hours = {"随时": 6, "下午": 6, "全天": 10}.get(intent.get("time_slot", "下午"), 6)
    radius = compute_reachable_radius_km(
        intent.get("transport_mode", "transit"),
        slot_hours,
    )
    return {"reachable_radius_km": round(radius, 2)}


# ════════════════════════════════════════════════════════════
#  ④ 时间槽拆分
# ════════════════════════════════════════════════════════════

def node_time_slots(state: TripState) -> dict:
    intent = state["intent"]
    tw = compute_time_window(intent.get("time_slot", "下午"))
    max_pois = compute_max_pois(tw)
    return {"time_window": tw, "max_pois_per_day": max_pois}


# ════════════════════════════════════════════════════════════
#  ⑤ 候选召回 + 硬过滤(+ RAG)
# ════════════════════════════════════════════════════════════

def _is_open_during(poi: dict, time_window: dict) -> bool:
    """POI 在用户时间窗口内是否开放(部分重叠即可)。"""
    open_hours = poi.get("open_hours") or [[0, 24]]
    if not open_hours:
        return True
    ws, we = time_window["start"], time_window["end"]
    for start, end in open_hours:
        # 跨夜简化处理
        if end < start:
            end += 24
        if not (end <= ws or start >= we):
            return True
    return False


def _in_reachable_circle(poi: dict, origin: tuple[float, float], radius_km: float) -> bool:
    d = haversine_km(origin[0], origin[1], poi["lat"], poi["lng"])
    return d <= radius_km


def _match_category(poi: dict, intent: Intent) -> bool:
    """硬约束:命中用户选的小类 或 大类。"""
    subs = intent.get("sub_categories") or []
    moods = intent.get("moods") or []
    if not subs and not moods:
        return True   # 没选类别,语义召回阶段再筛
    return (
        (poi.get("category_sub") in subs) or
        (poi.get("category_main") in moods)
    )


def node_candidates(state: TripState) -> dict:
    pois = _load_pois()
    intent = state["intent"]
    origin = (intent["origin_lat"], intent["origin_lng"])
    radius = state["reachable_radius_km"]
    tw = state["time_window"]

    # 天气硬过滤(暴雨排除室外)
    weather = (state.get("weather") or {}).get("condition", "晴")

    has_categories = bool(intent.get("sub_categories")) or bool(intent.get("moods"))

    # === 硬过滤 ===
    pool: list[POI] = []
    for poi in pois:
        # 健康禁忌:简单实现"膝盖不好"->排除高停留户外大景区
        if "膝盖不好" in (intent.get("health_constraints") or []):
            if not poi.get("indoor", True) and poi.get("stay_minutes", 0) > 150:
                continue
        if not _in_reachable_circle(poi, origin, radius):
            continue
        if not _is_open_during(poi, tw):
            continue
        if weather in ("暴雨", "极端") and not poi.get("indoor", True):
            continue
        if has_categories:
            if not _match_category(poi, intent):
                continue
        pool.append(poi)

    # === RAG 召回(没选类别) ===
    if not has_categories and intent.get("free_text"):
        embedder = get_embedder()
        query_vec = embedder.encode_text(intent["free_text"])
        scored = []
        for poi in pool:
            sim = embedder.cosine(query_vec, _POI_EMBEDDINGS[poi["id"]])
            poi_copy = dict(poi)
            poi_copy["_semantic_score"] = sim
            scored.append(poi_copy)
        # 按相似度截前 40 个,避免后面评分过载
        scored.sort(key=lambda p: p.get("_semantic_score", 0), reverse=True)
        pool = scored[:40]

    # === 计算距离 ===
    for poi in pool:
        poi["distance_km"] = haversine_km(
            origin[0], origin[1], poi["lat"], poi["lng"]
        )

    # === 排除画像黑名单 ===
    profile = state.get("user_profile") or {}
    disliked = set(profile.get("disliked_pois", []))
    pool = [p for p in pool if p["id"] not in disliked]

    return {"candidate_pool": pool}


# ════════════════════════════════════════════════════════════
#  ⑥ POI 评分
# ════════════════════════════════════════════════════════════

def node_score(state: TripState) -> dict:
    intent = state["intent"]
    pool = state["candidate_pool"]
    radius = state["reachable_radius_km"]
    weather = (state.get("weather") or {}).get("condition", "晴")
    profile = state.get("user_profile")
    has_categories = bool(intent.get("sub_categories")) or bool(intent.get("moods"))

    # 权重:选了类别走 with_category,否则走 without
    weights = ScoringWeights.with_category() if has_categories else ScoringWeights.without_category()
    # 画像调权(自迭代 harness 接入点)
    if profile and not UserProfile.from_dict(profile).is_cold_start():
        weights = weights.adjust_by_profile(profile.get("dimension_sensitivity"))

    current_group = intent.get("people_group", "情侣")

    scored: list[POI] = []
    for poi in pool:
        sem = float(poi.get("_semantic_score", 0.0))
        result = score_poi(
            poi=poi,
            distance_km=poi["distance_km"],
            reachable_radius_km=radius,
            current_group=current_group,
            weights=weights,
            weather_condition=weather,
            budget_per_person=intent.get("budget_per_person"),
            semantic_score=sem,
        )
        poi["score"] = result["score"]
        poi["score_breakdown"] = result["breakdown"]
        scored.append(poi)

    scored.sort(key=lambda p: p["score"], reverse=True)
    return {"candidate_pool": scored}


# ════════════════════════════════════════════════════════════
#  ⑦ 候选池构建 + 类别砍 + 聚类
# ════════════════════════════════════════════════════════════

def _build_candidate_per_category(
    scored_pool: list[POI], selected_cats: list[str]
) -> dict[str, list[POI]]:
    """每类取 top max(3, 总POI数/类别数)。"""
    if not selected_cats:
        return {"_all": scored_pool[:12]}
    n_per = max(3, len(scored_pool) // max(1, len(selected_cats)))
    out: dict[str, list[POI]] = {c: [] for c in selected_cats}
    # 简化:按小类匹配,fallback 按大类
    for poi in scored_pool:
        sub = poi.get("category_sub")
        main = poi.get("category_main")
        for cat in selected_cats:
            if (sub == cat or main == cat) and len(out[cat]) < n_per:
                out[cat].append(poi)
                break
    return out


def node_cluster_and_pool(state: TripState) -> dict:
    intent = state["intent"]
    scored = state["candidate_pool"]
    max_pois = state["max_pois_per_day"]

    selected = list(intent.get("sub_categories") or []) or list(intent.get("moods") or [])
    if not selected:
        selected = ["_all"]

    # 类别 -> top N
    per_cat = _build_candidate_per_category(scored, selected)
    if selected != ["_all"] and not any(per_cat.get(cat) for cat in selected):
        fallback_selected = list(intent.get("moods") or []) or ["_all"]
        per_cat = _build_candidate_per_category(scored, fallback_selected)
        selected = fallback_selected

    # 类别太多砍掉垫底(用每类首位 POI 分作为类别分)
    cat_top = {c: (per_cat[c][0]["score"] if per_cat[c] else 0.0) for c in selected}
    kept_cats, dropped_cats = trim_excess_categories(selected, max_pois, cat_top)
    if dropped_cats:
        logger.info("类别超额砍掉: %s (max_pois=%d)", dropped_cats, max_pois)

    # 合并候选(去重)
    merged: list[POI] = []
    seen_ids = set()
    for c in kept_cats:
        for poi in per_cat.get(c, []):
            if poi["id"] not in seen_ids:
                merged.append(poi)
                seen_ids.add(poi["id"])

    # 地理聚类
    points = [(p["lat"], p["lng"]) for p in merged]
    labels, centroids, K = adaptive_kmeans(points)

    # 簇访问顺序
    origin = (intent["origin_lat"], intent["origin_lng"])
    visit_order = cluster_visit_order(origin, centroids)

    clusters = []
    for zone_pos, c_idx in enumerate(visit_order):
        members = [merged[i] for i, lab in enumerate(labels) if lab == c_idx]
        clusters.append({
            "zone_id": f"zone_{zone_pos}",
            "members": members,
            "centroid": centroids[c_idx],
            "order": zone_pos,
            "categories_kept": kept_cats,
        })

    return {
        "candidate_pool": merged,
        "clusters": clusters,
        "intent": {**intent, "_dropped_categories": dropped_cats},
    }


# ════════════════════════════════════════════════════════════
#  ⑧ 各 Zone 路线生成 + ⑨ 全局最优
# ════════════════════════════════════════════════════════════

def _build_route_stops(
    pois_in_order: list[POI],
    intent: Intent,
    commute: CommuteProvider,
) -> list[RouteStop]:
    """按访问顺序构造 stops,通过通勤 provider 计算 transit。"""
    mode = intent.get("transport_mode", "transit")
    tw_start = 9.0 if intent.get("time_slot") == "全天" else 13.0
    cur_minutes = int(tw_start * 60)

    stops: list[RouteStop] = []
    for i, poi in enumerate(pois_in_order):
        arrival_min = cur_minutes
        stay = poi.get("stay_minutes", 60)
        leave_min = arrival_min + stay

        transit_min = 0
        transit_mode = mode
        if i < len(pois_in_order) - 1:
            nxt = pois_in_order[i + 1]
            r = commute.get_commute(poi["lat"], poi["lng"], nxt["lat"], nxt["lng"], mode)
            transit_min = int(r["minutes"])
            transit_mode = r["mode"]

        cur_minutes = leave_min + transit_min

        stops.append({
            "poi_id": poi["id"],
            "poi_name": poi["name"],
            "lat": poi["lat"],                  # NEW: 餐厅锚点定位 + 前端画图
            "lng": poi["lng"],                  # NEW
            "category_sub": poi.get("category_sub"),
            "rank_score": poi.get("rank_score"),
            "good_review_rate": poi.get("good_review_rate"),
            "tags": poi.get("tags", []),
            "arrival_time": f"{arrival_min // 60:02d}:{arrival_min % 60:02d}",
            "leave_time": f"{leave_min // 60:02d}:{leave_min % 60:02d}",
            "stay_minutes": stay,
            "transit_to_next_minutes": transit_min,
            "transit_to_next_mode": transit_mode,
            "cross_zone": False,
            "locked": poi["id"] in (intent.get("locked_poi_ids") or []),
        })
    return stops


def _build_route(
    pois_in_order: list[POI],
    intent: Intent,
    commute: CommuteProvider,
    route_id: str,
    zone_id: str | None,
) -> Route:
    stops = _build_route_stops(pois_in_order, intent, commute)
    total_commute = sum(s["transit_to_next_minutes"] for s in stops)
    total_score = sum(p.get("score", 0) for p in pois_in_order)
    comp = compactness_score(total_commute)
    quality = total_score * comp

    return {
        "route_id": route_id,
        "stops": stops,
        "total_commute_minutes": total_commute,
        "total_score": round(total_score, 3),
        "compactness": round(comp, 3),
        "quality_score": round(quality, 3),
        "zone_id": zone_id,
    }


def _commute_provider_singleton() -> CommuteProvider:
    """单例 commute provider,避免每节点重复创建。"""
    if not hasattr(_commute_provider_singleton, "_p"):
        _commute_provider_singleton._p = get_default_commute_provider()
    return _commute_provider_singleton._p


def node_route_gen(state: TripState) -> dict:
    """
    ⑧ 各 Zone 路线 + ⑨ 全局最优
    """
    clusters = state.get("clusters") or []
    intent = state["intent"]
    scored_pool = state["candidate_pool"]
    selected_cats = clusters[0]["categories_kept"] if clusters else []
    max_pois = state.get("max_pois_per_day", 3)
    commute = _commute_provider_singleton()
    candidate_routes: list[Route] = []

    origin = (intent["origin_lat"], intent["origin_lng"])
    locked_ids = set(intent.get("locked_poi_ids") or [])
    single_category_mode = len(selected_cats) == 1 and selected_cats != ["_all"]

    # === 各 Zone 路线 ===
    for cluster in clusters:
        members = cluster["members"]
        if not members:
            continue
        zone_pois: list[POI] = []
        # 每个类别选 zone 内得分最高,缺类别就跨区引入最近同类
        cat_picked_ids = set()
        for cat in (selected_cats if selected_cats != ["_all"] else ["_all"]):
            zone_for_cat = [
                p for p in members
                if (p.get("category_sub") == cat or p.get("category_main") == cat or cat == "_all")
                and p["id"] not in cat_picked_ids
            ]
            if zone_for_cat:
                pick = max(zone_for_cat, key=lambda p: p["score"])
                zone_pois.append(pick)
                cat_picked_ids.add(pick["id"])
            elif cat != "_all":
                # 跨区引入
                cross = [
                    p for p in scored_pool
                    if (p.get("category_sub") == cat or p.get("category_main") == cat)
                    and p["id"] not in cat_picked_ids
                ]
                if cross:
                    pick = max(cross, key=lambda p: p["score"])
                    pick = dict(pick)
                    pick["_cross_zone"] = True
                    zone_pois.append(pick)
                    cat_picked_ids.add(pick["id"])

        if single_category_mode and len(zone_pois) < 2:
            same_category = [
                p for p in members
                if p.get("category_sub") == selected_cats[0]
                and p["id"] not in cat_picked_ids
            ]
            same_category = sorted(
                same_category, key=lambda p: p.get("score", 0), reverse=True
            )
            for poi in same_category:
                zone_pois.append(poi)
                cat_picked_ids.add(poi["id"])
                if len(zone_pois) >= min(3, max_pois):
                    break

        if len(zone_pois) < 2:
            continue

        # 锚点固定:把锁定的 POI 移到前面、标记 fixed_indices
        locked_in_zone = [i for i, p in enumerate(zone_pois) if p["id"] in locked_ids]

        # 2-opt 排序
        points = [(p["lat"], p["lng"]) for p in zone_pois]
        order = two_opt(points, fixed_indices=set(locked_in_zone))
        ordered = [zone_pois[i] for i in order]

        route = _build_route(
            ordered, intent, commute,
            route_id=f"route_zone_{cluster['order']}",
            zone_id=cluster["zone_id"],
        )
        # 标记跨区
        for stop, poi in zip(route["stops"], ordered):
            if poi.get("_cross_zone"):
                stop["cross_zone"] = True
        candidate_routes.append(route)

    # === ⑨ 全局最优(各类别全局第一) ===
    if selected_cats and selected_cats != ["_all"]:
        global_picks: list[POI] = []
        picked_ids = set()
        if single_category_mode:
            global_picks = [
                p for p in scored_pool
                if p.get("category_sub") == selected_cats[0]
            ][: min(4, max_pois)]
        else:
            for cat in selected_cats:
                top = [
                    p for p in scored_pool
                    if (p.get("category_sub") == cat or p.get("category_main") == cat)
                    and p["id"] not in picked_ids
                ]
                if top:
                    pick = max(top, key=lambda p: p["score"])
                    global_picks.append(pick)
                    picked_ids.add(pick["id"])

        if len(global_picks) >= 2:
            points = [(p["lat"], p["lng"]) for p in global_picks]
            order = two_opt(points)
            ordered = [global_picks[i] for i in order]
            global_route = _build_route(
                ordered, intent, commute,
                route_id="route_global_best",
                zone_id=None,
            )
            # 重合度 <60% 才加入
            existing_ids_sets = [
                [s["poi_id"] for s in r["stops"]] for r in candidate_routes
            ]
            global_ids = [s["poi_id"] for s in global_route["stops"]]
            max_overlap = max(
                (route_overlap_ratio(global_ids, ids) for ids in existing_ids_sets),
                default=0.0,
            )
            if max_overlap < 0.6:
                candidate_routes.append(global_route)

    return {"candidate_routes": candidate_routes}


# ════════════════════════════════════════════════════════════
#  ⑩ 过滤 + 排序
# ════════════════════════════════════════════════════════════

def node_filter_rank(state: TripState) -> dict:
    routes = state.get("candidate_routes", [])
    # 两两去重(重合 >60% 留高分)
    keep: list[Route] = []
    sorted_routes = sorted(routes, key=lambda r: r.get("quality_score", 0), reverse=True)
    for r in sorted_routes:
        rids = [s["poi_id"] for s in r["stops"]]
        dup = False
        for k in keep:
            k_ids = [s["poi_id"] for s in k["stops"]]
            if route_overlap_ratio(rids, k_ids) > 0.6:
                dup = True
                break
        if not dup:
            keep.append(r)
    # 限制候选集大小,辩论 token 控制
    keep = keep[:12]
    return {"candidate_routes": keep}


# ════════════════════════════════════════════════════════════
#  ⑪ Agent 辩论 + ⑫ 最终输出
# ════════════════════════════════════════════════════════════

def node_debate(state: TripState) -> dict:
    routes = state.get("candidate_routes", [])
    if not routes:
        return {
            "debate_transcript": [],
            "top_routes": [],
            "errors": (state.get("errors") or []) + ["no candidate routes"],
        }

    debate_result = run_debate(
        candidate_routes=routes,
        intent=state["intent"],
        profile=state.get("user_profile"),
    )

    # 把 top3 的 route_id 映射回完整 route 对象,带上 label / summary
    route_by_id = {r["route_id"]: r for r in routes}
    sorted_routes = sorted(routes, key=lambda x: x.get("quality_score", 0), reverse=True)
    top_routes: list[Route] = []
    seen_ids = set()

    llm_matched = 0
    for i, entry in enumerate(debate_result["top3"]):
        rid = entry.get("route_id", "")
        r = route_by_id.get(rid)
        # 模糊匹配:如果精确 ID 没命中,按位置取
        if r is None and i < len(sorted_routes):
            r = sorted_routes[i]
        if r is None or r["route_id"] in seen_ids:
            continue
        r = dict(r)
        r["label"] = entry.get("label", "")
        r["summary"] = entry.get("summary", "")
        r["source"] = "llm"
        r["debate_highlights"] = [
            t for t in debate_result["transcript"]
            if t.get("target_route_id") == r["route_id"]
        ]
        top_routes.append(r)
        seen_ids.add(r["route_id"])
        llm_matched += 1

    # 补缺:LLM 返回的 top3 不够数,按算法质量分补齐
    if len(top_routes) < min(3, len(routes)):
        for r in sorted_routes:
            if len(top_routes) >= 3:
                break
            if r["route_id"] in seen_ids:
                continue
            r = dict(r)
            r["label"] = ""
            r["summary"] = ""
            r["source"] = "algorithm"
            top_routes.append(r)
            seen_ids.add(r["route_id"])

    return {
        "debate_transcript": debate_result["transcript"],
        "top_routes": top_routes,
        "pre_brief": debate_result.get("host_remark", ""),
        "llm_degraded": debate_result.get("degraded", False),
    }


# ════════════════════════════════════════════════════════════
#  反馈写回(由 /feedback 接口或交互后单独调用,不在主图里)
# ════════════════════════════════════════════════════════════

def node_feedback_write(state: TripState) -> dict:
    """
    根据用户的选择和反馈更新画像。
    """
    user_id = state.get("user_id", "anon")
    profile = load_profile(user_id)

    chosen_id = state.get("user_choice_route_id")
    deleted_ids = state.get("user_deleted_poi_ids") or []
    rating = state.get("user_rating")

    top_routes = state.get("top_routes") or []
    transcript = state.get("debate_transcript") or []

    # 1) 选中路线 -> 主导 agent 权重 +
    if chosen_id:
        # 找该路线主导发言的 agent
        sup_counts: dict[str, int] = {}
        for t in transcript:
            if t.get("target_route_id") == chosen_id and t.get("agent") in ("experience", "pragmatic", "personal"):
                # 解析 structured stance:这里简化为 support 计 +1
                sup_counts[t["agent"]] = sup_counts.get(t["agent"], 0) + 1
        if sup_counts:
            dominant = max(sup_counts, key=sup_counts.get)
            update_agent_weight(profile, dominant, +1)
        # 标记 loved POIs / categories
        chosen_route = next((r for r in top_routes if r["route_id"] == chosen_id), None)
        if chosen_route:
            for stop in chosen_route["stops"]:
                mark_loved_poi(profile, stop["poi_id"])
                if stop.get("category_sub"):
                    mark_loved_category(profile, stop["category_sub"])

    # 2) 删除的 POI -> 推它的 agent 扣分
    for pid in deleted_ids:
        mark_disliked_poi(profile, pid)
        for t in transcript:
            structured = t.get("structured") or []
            for s in structured:
                # 简单匹配:在结构化字段里找到这个 POI 被力推过
                if isinstance(s, dict) and pid in str(s.get("reason", "")):
                    if t["agent"] in ("experience", "pragmatic", "personal"):
                        update_agent_weight(profile, t["agent"], -1)
                    break

    # 3) 评分
    if rating is not None:
        update_satisfaction(profile, rating)

    profile.total_plans += 1
    save_profile(profile)
    return {"user_profile": profile.to_dict()}


# ════════════════════════════════════════════════════════════
#  ⑫ 真实路网导航 - 仅 Top-3 调高德
# ════════════════════════════════════════════════════════════


def _places_provider_singleton() -> PlacesProvider:
    if not hasattr(_places_provider_singleton, "_p"):
        _places_provider_singleton._p = get_default_places_provider()
    return _places_provider_singleton._p


def node_real_navigation(state: TripState) -> dict:
    """
    为 Top-3 路线刷上真实路网数据(amap),没有 key 时 mock 也能返回 steps。

    现状: 此前 route_gen 用 commute provider 拿了估算时长,但没拿 steps;
    这里**重新调一次** commute.get_commute,把 navigation 字段填上,
    并用真实路网时长覆盖 transit_to_next_minutes(差异可能比较大,
    会影响后续 arrival_time 的精度,这里**重新推算 arrival_time/leave_time**)。
    """
    intent = state["intent"]
    top_routes = state.get("top_routes") or []
    if not top_routes:
        return {}

    commute = _commute_provider_singleton()
    mode = intent.get("transport_mode", "transit")
    city_code = intent.get("city_code", "021")
    degraded_any = False
    enriched_routes = []

    for r in top_routes:
        stops = r.get("stops") or []
        if not stops:
            enriched_routes.append(r)
            continue

        # 起始时间 - 从 route stops 推回(沿用之前算的)
        first_stop = stops[0]
        try:
            h, m = first_stop["arrival_time"].split(":")
            cur_min = int(h) * 60 + int(m)
        except (KeyError, ValueError):
            cur_min = 13 * 60

        source_set = set()
        new_stops = []
        new_total_commute = 0
        for i, stop in enumerate(stops):
            new_stop = dict(stop)
            stay = stop.get("stay_minutes", 60)
            arrival_min = cur_min
            leave_min = arrival_min + stay

            transit_min = 0
            transit_distance_km = 0.0
            nav = None
            if i < len(stops) - 1:
                nxt = stops[i + 1]
                try:
                    cr = commute.get_commute(
                        stop["lat"], stop["lng"],
                        nxt["lat"], nxt["lng"],
                        mode=mode, city=city_code,
                    )
                    transit_min = int(cr["minutes"])
                    transit_distance_km = cr.get("distance_km", 0.0)
                    nav = cr.get("navigation")
                    source_set.add(cr.get("source", "mock"))
                except Exception as e:
                    logger.warning("real_navigation 单段失败: %s", e)
                    degraded_any = True
                    transit_min = stop.get("transit_to_next_minutes", 15)

            new_stop["arrival_time"] = f"{arrival_min // 60:02d}:{arrival_min % 60:02d}"
            new_stop["leave_time"] = f"{leave_min // 60:02d}:{leave_min % 60:02d}"
            new_stop["transit_to_next_minutes"] = transit_min
            new_stop["transit_to_next_distance_km"] = round(transit_distance_km, 3)
            if nav:
                new_stop["navigation_to_next"] = nav
            new_total_commute += transit_min
            cur_min = leave_min + transit_min
            new_stops.append(new_stop)

        new_r = dict(r)
        new_r["stops"] = new_stops
        new_r["total_commute_minutes"] = new_total_commute
        new_r["navigation_enriched"] = True
        new_r["navigation_source"] = "amap" if "amap" in source_set else "mock"
        enriched_routes.append(new_r)

    return {
        "top_routes": enriched_routes,
        "navigation_degraded": degraded_any,
    }


# ════════════════════════════════════════════════════════════
#  ⑬ 餐厅推荐 - 仅 Top-3,分桶 Top 3
# ════════════════════════════════════════════════════════════


def node_food_recommend(state: TripState) -> dict:
    """为 Top-3 路线生成餐厅推荐。"""
    intent = state["intent"]
    top_routes = state.get("top_routes") or []
    if not top_routes:
        return {}

    time_window = state.get("time_window") or {}
    profile = state.get("user_profile")
    places = _places_provider_singleton()

    out_routes = []
    for r in top_routes:
        try:
            recs = recommend_for_route(
                route=r,
                intent=intent,
                user_profile=profile,
                time_window=time_window,
                places=places,
            )
        except Exception as e:
            logger.exception("food_recommend 失败 route=%s: %s", r.get("route_id"), e)
            recs = []
        new_r = dict(r)
        new_r["food_recommendations"] = recs
        out_routes.append(new_r)

    return {"top_routes": out_routes}
