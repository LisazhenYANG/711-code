"""
LangGraph 装配。

主图: intent -> profile_load -> reachable -> time_slots -> candidates
            -> score -> cluster_and_pool -> route_gen -> filter_rank
            -> debate -> real_navigation -> food_recommend -> END

意图解析有追问循环(condition edge),最多 2 轮。
反馈写回是独立小图(只走 feedback_write)。

real_navigation 和 food_recommend 都只针对 Top-3,延迟和 API 成本可控:
  - real_navigation: 3 路线 × 2-4 段 = 6-12 次 Amap direction 调用
  - food_recommend: 3 路线 × 1-2 个 meal_block = 3-6 次 Amap place/around 调用
"""
from __future__ import annotations
from langgraph.graph import StateGraph, END

from state import TripState
from graph.nodes import (
    node_intent_parse, should_followup,
    node_profile_load, node_reachable, node_time_slots,
    node_candidates, node_score, node_cluster_and_pool,
    node_route_gen, node_filter_rank, node_debate,
    node_real_navigation, node_food_recommend,
    node_feedback_write,
)


def build_planning_graph():
    g = StateGraph(TripState)

    g.add_node("intent", node_intent_parse)
    g.add_node("profile_load", node_profile_load)
    g.add_node("reachable", node_reachable)
    g.add_node("time_slots", node_time_slots)
    g.add_node("candidates", node_candidates)
    g.add_node("score", node_score)
    g.add_node("cluster_and_pool", node_cluster_and_pool)
    g.add_node("route_gen", node_route_gen)
    g.add_node("filter_rank", node_filter_rank)
    g.add_node("debate", node_debate)
    g.add_node("real_navigation", node_real_navigation)
    g.add_node("food_recommend", node_food_recommend)

    g.set_entry_point("intent")
    g.add_conditional_edges(
        "intent",
        should_followup,
        {
            "followup": "intent",
            "proceed": "profile_load",
        },
    )
    g.add_edge("profile_load", "reachable")
    g.add_edge("reachable", "time_slots")
    g.add_edge("time_slots", "candidates")
    g.add_edge("candidates", "score")
    g.add_edge("score", "cluster_and_pool")
    g.add_edge("cluster_and_pool", "route_gen")
    g.add_edge("route_gen", "filter_rank")
    g.add_edge("filter_rank", "debate")
    g.add_edge("debate", "real_navigation")
    g.add_edge("real_navigation", "food_recommend")
    g.add_edge("food_recommend", END)

    return g.compile()


def build_feedback_graph():
    g = StateGraph(TripState)
    g.add_node("feedback_write", node_feedback_write)
    g.set_entry_point("feedback_write")
    g.add_edge("feedback_write", END)
    return g.compile()


_planning = None
_feedback = None


def get_planning_graph():
    global _planning
    if _planning is None:
        _planning = build_planning_graph()
    return _planning


def get_feedback_graph():
    global _feedback
    if _feedback is None:
        _feedback = build_feedback_graph()
    return _feedback
