"""
辩论运行器 - 协调三派 agent + 主持人。

流程:
  Round 1: 三派并行发言(各看完所有候选路线发表立场)
  Round 2: 三派轮流反驳(看到对方 Round 1 后)
  Final:   主持人归类 Top-3 + 写文案

辩论 transcript 全部保留,供前端展示。
LLM 调不通时降级: 返回算法层质量分 Top-3 + 模板化文案。
"""
from __future__ import annotations
import json
import logging
from typing import Optional
from providers.llm import LLMClient, get_llm
from agents.personas import (
    EXPERIENCE_AGENT, PRAGMATIC_AGENT, PERSONAL_AGENT,
    HOST_AGENT, DEBATE_AGENTS,
)

logger = logging.getLogger(__name__)


def _route_brief(route: dict) -> dict:
    """精简路线信息给 agent,避免 prompt 过长。"""
    return {
        "route_id": route["route_id"],
        "stops": [
            {
                "name": s["poi_name"],
                "category": s.get("category_sub", ""),
                "rank_score": s.get("rank_score"),
                "good_review_rate": s.get("good_review_rate"),
                "stay_min": s.get("stay_minutes"),
                "transit_to_next_min": s.get("transit_to_next_minutes", 0),
                "tags": s.get("tags", []),
            }
            for s in route["stops"]
        ],
        "total_commute_min": route.get("total_commute_minutes"),
        "total_score": round(route.get("total_score", 0), 2),
        "compactness": round(route.get("compactness", 0), 3),
        "zone_id": route.get("zone_id"),
    }


def _profile_brief(profile: dict | None) -> dict:
    if not profile:
        return {"cold_start": True}
    return {
        "loved_categories": list(profile.get("loved_categories", {}).keys())[:5],
        "disliked_pois": profile.get("disliked_pois", [])[-10:],
        "loved_pois": profile.get("loved_pois", [])[-10:],
        "avg_satisfaction": profile.get("avg_satisfaction", 0),
        "total_plans": profile.get("total_plans", 0),
    }


def _round1_user_prompt(
    candidate_routes_brief: list[dict],
    intent: dict,
    profile_brief: dict,
    agent_key: str,
) -> str:
    base = (
        "下面是用户的意图,以及算法生成的可行候选路线集合。\n"
        "请你以你的人格,从你关心的维度,挑出你最支持的 1-2 条、最反对的 1-2 条。\n"
        "明确引用 route_id。\n\n"
        f"## 用户意图\n{json.dumps(intent, ensure_ascii=False, indent=2)}\n\n"
    )
    if agent_key == "personal":
        base += f"## 用户画像\n{json.dumps(profile_brief, ensure_ascii=False, indent=2)}\n\n"
    base += (
        f"## 候选路线\n{json.dumps(candidate_routes_brief, ensure_ascii=False, indent=2)}\n\n"
        "请输出 JSON,格式:\n"
        '{"stance": [{"route_id": "...", "lean": "support|oppose", "reason": "..."}],'
        ' "speech": "你以人格化语气说的一段话"}\n'
        "约束: speech 必须是单行字符串(不换行),不超过 80 字。"
    )
    return base


def _round2_user_prompt(
    candidate_routes_brief: list[dict],
    round1_transcript: list[dict],
    agent_key: str,
) -> str:
    return (
        "你已经发表了第一轮观点。现在请看完其他派系的发言,选 1-2 条你最想反驳或附议的论点,做出回应。\n"
        "如果对方说服了你,也可以让步。\n\n"
        f"## 第一轮发言\n{json.dumps(round1_transcript, ensure_ascii=False, indent=2)}\n\n"
        f"## 候选路线提要\n{json.dumps(candidate_routes_brief, ensure_ascii=False, indent=2)}\n\n"
        "请输出 JSON,格式:\n"
        '{"replies": [{"to_agent": "...", "route_id": "...", "agreement": "agree|disagree", "reason": "..."}],'
        ' "speech": "你的回应"}\n'
        "约束: speech 必须是单行字符串(不换行),不超过 80 字。"
    )


def _host_prompt(
    candidate_routes_brief: list[dict], debate_transcript: list[dict]
) -> str:
    n = min(len(candidate_routes_brief), 3)
    return (
        "你是主持人。三派已经辩论完毕,请你:\n"
        f"1) 从候选路线中挑出 Top-{n} (route_id 必须原样复制下面的候选路线,不要编造)\n"
        "2) 给每条贴标签: 「精华首选」「轻松漫游」「小众惊喜」(每条一个,不重复)\n"
        "3) 给每条写 15-25 字描述\n\n"
        f"## 候选路线 (共{n}条)\n{json.dumps(candidate_routes_brief, ensure_ascii=False, indent=2)}\n\n"
        f"## 辩论 transcript\n{json.dumps(debate_transcript, ensure_ascii=False, indent=2)}\n\n"
        "输出 JSON:\n"
        '{"top3": [{"route_id": "从候选路线原样复制", "label": "...", "summary": "...", "key_argument_from": "..."}],'
        ' "host_remark": "20-40 字小结,点明分歧由谁的论点压过谁"}'
    )


def run_debate(
    candidate_routes: list[dict],
    intent: dict,
    profile: dict | None,
    llm: LLMClient | None = None,
    enable_round2: bool = True,
) -> dict:
    """
    返回:
      {
        "transcript": [DebateMessage, ...],
        "top3": [{route_id, label, summary, key_argument_from}],
        "host_remark": "...",
        "degraded": bool,
      }
    """
    if llm is None:
        llm = get_llm()

    if not llm.available:
        return _fallback(candidate_routes, reason="LLM 不可用,使用算法层兜底")

    briefs = [_route_brief(r) for r in candidate_routes]
    profile_brief = _profile_brief(profile)

    transcript: list[dict] = []

    # ── Round 1 ──
    try:
        round1_outputs = {}
        for agent in DEBATE_AGENTS:
            messages = [
                {"role": "system", "content": agent["system"]},
                {"role": "user", "content": _round1_user_prompt(briefs, intent, profile_brief, agent["key"])},
            ]
            result = llm.chat_json(messages, temperature=0.7)
            round1_outputs[agent["key"]] = result
            transcript.append({
                "agent": agent["key"],
                "persona_label": agent["name"],
                "round": 1,
                "stance": "support",
                "target_route_id": (result.get("stance") or [{}])[0].get("route_id"),
                "content": result.get("speech", ""),
                "structured": result.get("stance", []),
            })
    except Exception as e:
        logger.exception("Round 1 失败,降级: %s", e)
        return _fallback(candidate_routes, reason=f"辩论 Round 1 失败: {e}")

    # ── Round 2 (可选) ──
    if enable_round2:
        try:
            for agent in DEBATE_AGENTS:
                r1_others = [
                    t for t in transcript
                    if t["round"] == 1 and t["agent"] != agent["key"]
                ]
                messages = [
                    {"role": "system", "content": agent["system"]},
                    {"role": "user", "content": _round2_user_prompt(briefs, r1_others, agent["key"])},
                ]
                result = llm.chat_json(messages, temperature=0.6)
                transcript.append({
                    "agent": agent["key"],
                    "persona_label": agent["name"],
                    "round": 2,
                    "stance": "rebuttal",
                    "target_route_id": (result.get("replies") or [{}])[0].get("route_id"),
                    "content": result.get("speech", ""),
                    "structured": result.get("replies", []),
                })
        except Exception as e:
            logger.warning("Round 2 失败但有 Round 1 可用,继续: %s", e)

    # ── 主持人归类 ──
    try:
        messages = [
            {"role": "system", "content": HOST_AGENT["system"]},
            {"role": "user", "content": _host_prompt(briefs, transcript)},
        ]
        host_result = llm.chat_json(messages, temperature=0.3)
        top3 = host_result.get("top3", [])
        host_remark = host_result.get("host_remark", "")
        transcript.append({
            "agent": "host",
            "persona_label": HOST_AGENT["name"],
            "round": 3,
            "stance": "arbitrate",
            "target_route_id": None,
            "content": host_remark,
            "structured": top3,
        })
    except Exception as e:
        logger.exception("主持人归类失败,降级: %s", e)
        fallback = _fallback(candidate_routes, reason=f"主持人失败: {e}")
        fallback["transcript"] = transcript + fallback["transcript"]
        return fallback

    return {
        "transcript": transcript,
        "top3": top3,
        "host_remark": host_remark,
        "degraded": False,
    }


def _fallback(candidate_routes: list[dict], reason: str = "") -> dict:
    """
    LLM 不可用兜底:按算法层质量分排序取 Top-3,标签按通勤/榜单/好评率简单分配。
    """
    if not candidate_routes:
        return {"transcript": [], "top3": [], "host_remark": reason, "degraded": True}

    sorted_routes = sorted(
        candidate_routes,
        key=lambda r: r.get("quality_score", 0),
        reverse=True,
    )
    top3 = sorted_routes[:3]

    # 标签分配:精华(总分最高)/轻松(通勤最短)/小众(好评率最高的非精华)
    labeled = []
    if top3:
        labeled.append({
            "route_id": top3[0]["route_id"],
            "label": "精华首选",
            "summary": "综合评分最高,集中而不亏的一条",
            "key_argument_from": "algorithm",
            "source": "algorithm",
        })
    if len(top3) > 1:
        # 通勤最短的
        easy = min(top3[1:], key=lambda r: r.get("total_commute_minutes", 9999))
        labeled.append({
            "route_id": easy["route_id"],
            "label": "轻松漫游",
            "summary": "通勤最短,慢悠悠也走得下来",
            "key_argument_from": "algorithm",
            "source": "algorithm",
        })
    if len(top3) > 2:
        remaining = [r for r in top3 if r["route_id"] not in {l["route_id"] for l in labeled}]
        if remaining:
            labeled.append({
                "route_id": remaining[0]["route_id"],
                "label": "小众惊喜",
                "summary": "包含口碑出色但不那么热门的点",
                "key_argument_from": "algorithm",
                "source": "algorithm",
            })

    return {
        "transcript": [{
            "agent": "system",
            "persona_label": "系统",
            "round": 0,
            "stance": "fallback",
            "target_route_id": None,
            "content": f"(降级模式) {reason}",
            "structured": [],
        }],
        "top3": labeled,
        "host_remark": "(降级输出) 算法层质量分排序",
        "degraded": True,
    }
