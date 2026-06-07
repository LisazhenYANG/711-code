"""
POI 评分 - PRD 五.1 两套公式。

- 选了类别:  距离 ×0.45 + 榜单 ×0.45 + 人数适配 ×0.10
- 没选类别:  距离 ×0.30 + 榜单 ×0.30 + 人数适配 ×0.10 + RAG语义 ×0.30
  再乘:     天气乘数(室内外) × 价格系数

所有原始分先归一到 [0,1] 再加权。
动态权重支持来自 user_profile 的偏好倾斜。
"""
from __future__ import annotations
from typing import Optional


# 人数适配规则: 完全匹配=1.0, 相邻档=0.6, 不匹配=0.2
GROUP_ORDER = ["独行", "情侣", "小团", "大队", "亲子"]


def people_count_to_group(count: int) -> str:
    if count <= 1:
        return "独行"
    if count == 2:
        return "情侣"
    if count <= 4:
        return "小团"
    return "大队"


def people_fit_score(poi_fit_groups: list[str], current_group: str) -> float:
    if not poi_fit_groups:
        return 0.5
    if current_group in poi_fit_groups:
        return 1.0
    # 相邻档判定
    if current_group in GROUP_ORDER:
        cur_idx = GROUP_ORDER.index(current_group)
        for g in poi_fit_groups:
            if g not in GROUP_ORDER:
                continue
            if abs(GROUP_ORDER.index(g) - cur_idx) == 1:
                return 0.6
    return 0.2


def weather_multiplier(indoor: bool, weather_condition: str) -> float:
    """
    晴天:    室内/室外都 1.0
    小雨:    室外 ×0.5,  室内 ×1.3
    大雨/雪: 室外 ×0.15, 室内 ×1.8
    暴雨:    室外硬过滤(返回 0.0)
    """
    w = (weather_condition or "晴").strip()
    if w in ("暴雨", "极端"):
        return 0.0 if not indoor else 1.8
    if w in ("大雨", "雪"):
        return 1.8 if indoor else 0.15
    if w in ("小雨", "阴"):
        return 1.3 if indoor else 0.5
    return 1.0


def price_coefficient(
    avg_price: float, budget_per_person: Optional[float]
) -> float:
    """超预算 ×0.6,在预算 ×1.0,特别划算(<60% 预算) ×1.1。"""
    if not budget_per_person or budget_per_person <= 0:
        return 1.0
    if avg_price > budget_per_person:
        return 0.6
    if avg_price < 0.6 * budget_per_person:
        return 1.1
    return 1.0


def normalize_rank(rank_score_0_to_5: float) -> float:
    return max(0.0, min(1.0, rank_score_0_to_5 / 5.0))


def normalize_distance_inverse(
    distance_km: float, reachable_radius_km: float
) -> float:
    """距离越近分越高,圈外为 0,圈内线性归一。"""
    if reachable_radius_km <= 0:
        return 0.0
    if distance_km > reachable_radius_km:
        return 0.0
    return 1.0 - distance_km / reachable_radius_km


class ScoringWeights:
    """权重档,动态可调。"""
    def __init__(
        self,
        w_distance: float,
        w_rank: float,
        w_people: float,
        w_semantic: float = 0.0,
    ):
        self.w_distance = w_distance
        self.w_rank = w_rank
        self.w_people = w_people
        self.w_semantic = w_semantic

    @classmethod
    def with_category(cls) -> "ScoringWeights":
        """选了类别的默认权重。"""
        return cls(0.45, 0.45, 0.10, 0.0)

    @classmethod
    def without_category(cls) -> "ScoringWeights":
        """没选类别的默认权重。"""
        return cls(0.30, 0.30, 0.10, 0.30)

    def adjust_by_profile(self, sensitivity: dict | None) -> "ScoringWeights":
        """根据用户画像微调权重 - 自迭代 harness 接入点。"""
        if not sensitivity:
            return self
        distance_sens = sensitivity.get("distance", 0.5)
        # 距离敏感的用户加权距离 +20%,降低榜单
        if distance_sens > 0.7:
            self.w_distance *= 1.2
            self.w_rank *= 0.85
        elif distance_sens < 0.3:
            self.w_distance *= 0.85
            self.w_rank *= 1.15
        # 归一化
        total = self.w_distance + self.w_rank + self.w_people + self.w_semantic
        if total > 0:
            self.w_distance /= total
            self.w_rank /= total
            self.w_people /= total
            self.w_semantic /= total
        return self


def score_poi(
    poi: dict,
    distance_km: float,
    reachable_radius_km: float,
    current_group: str,
    weights: ScoringWeights,
    weather_condition: str,
    budget_per_person: Optional[float],
    semantic_score: float = 0.0,
) -> dict:
    """
    返回 {score, breakdown}。
    POI 不应在调用前被加上距离字段,这里读取已经传入的 distance_km。
    """
    dist_n = normalize_distance_inverse(distance_km, reachable_radius_km)
    rank_n = normalize_rank(poi.get("rank_score", 3.0))
    people_n = people_fit_score(poi.get("fit_group", []), current_group)

    base = (
        weights.w_distance * dist_n
        + weights.w_rank * rank_n
        + weights.w_people * people_n
        + weights.w_semantic * semantic_score
    )

    weather_mul = weather_multiplier(poi.get("indoor", True), weather_condition)
    price_mul = price_coefficient(poi.get("avg_price", 0), budget_per_person)

    final = base * weather_mul * price_mul

    return {
        "score": round(final, 4),
        "breakdown": {
            "distance_n": round(dist_n, 3),
            "rank_n": round(rank_n, 3),
            "people_n": round(people_n, 3),
            "semantic_n": round(semantic_score, 3),
            "weather_mul": weather_mul,
            "price_mul": price_mul,
            "weights": {
                "distance": weights.w_distance,
                "rank": weights.w_rank,
                "people": weights.w_people,
                "semantic": weights.w_semantic,
            },
        },
    }
