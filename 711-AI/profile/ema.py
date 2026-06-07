"""
EMA (指数滑动平均) 更新逻辑 - 自迭代 Harness 的更新策略。

为什么用 EMA: 新信号占 0.1-0.2,避免一次差评把画像带偏。
"""
from __future__ import annotations
from profile.schema import UserProfile


# EMA 系数 - 新信号占比
ALPHA_AGENT_WEIGHT = 0.15      # agent 权重(慢慢倾斜)
ALPHA_DIMENSION = 0.20         # 维度敏感度(略快一些)
ALPHA_SATISFACTION = 0.30      # 满意度(快速反映近期感受)


def ema(old: float, new: float, alpha: float) -> float:
    return (1 - alpha) * old + alpha * new


def update_agent_weight(
    profile: UserProfile, dominant_agent: str, signal: float
) -> None:
    """
    signal: +1 = 这个 agent 主导的路线被选中
           -1 = 这个 agent 力推的 POI 被删除
    """
    if dominant_agent not in profile.agent_weights:
        return
    cur = profile.agent_weights[dominant_agent]
    # 目标值: signal=1 -> 推向 1.3, signal=-1 -> 推向 0.7
    target = 1.0 + 0.3 * signal
    profile.agent_weights[dominant_agent] = round(
        ema(cur, target, ALPHA_AGENT_WEIGHT), 4
    )


def update_distance_sensitivity(profile: UserProfile, signal: float) -> None:
    """signal: 用户改参数减少了步行量 -> 距离敏感度上升。"""
    cur = profile.dimension_sensitivity.get("distance", 0.5)
    target = max(0.0, min(1.0, cur + signal))
    profile.dimension_sensitivity["distance"] = round(
        ema(cur, target, ALPHA_DIMENSION), 4
    )


def update_satisfaction(profile: UserProfile, score_1_to_5: int) -> None:
    norm = max(1, min(5, score_1_to_5)) / 5.0
    profile.avg_satisfaction = round(
        ema(profile.avg_satisfaction or norm, norm, ALPHA_SATISFACTION), 4
    )


def mark_loved_category(profile: UserProfile, category: str) -> None:
    profile.loved_categories[category] = profile.loved_categories.get(category, 0) + 1
    # 控制 top 20
    if len(profile.loved_categories) > 20:
        sorted_items = sorted(profile.loved_categories.items(), key=lambda x: -x[1])
        profile.loved_categories = dict(sorted_items[:20])


def mark_disliked_poi(profile: UserProfile, poi_id: str) -> None:
    if poi_id not in profile.disliked_pois:
        profile.disliked_pois.append(poi_id)
        # 限长
        profile.disliked_pois = profile.disliked_pois[-100:]


def mark_loved_poi(profile: UserProfile, poi_id: str) -> None:
    if poi_id not in profile.loved_pois:
        profile.loved_pois.append(poi_id)
        profile.loved_pois = profile.loved_pois[-100:]
