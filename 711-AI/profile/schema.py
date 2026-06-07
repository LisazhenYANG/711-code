"""
用户画像 schema - 自迭代 Harness 的唯一持久化对象。

健康禁忌绝对不进这张表(对齐 PRD 3.1)。
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import time


@dataclass
class UserProfile:
    user_id: str

    # 三派 agent 权重(EMA 更新),默认均为 1.0
    agent_weights: dict[str, float] = field(default_factory=lambda: {
        "experience": 1.0,   # 体验派
        "pragmatic": 1.0,    # 实用派
        "personal": 1.0,     # 懂你派
    })

    # 维度敏感度(0=不敏感, 1=极敏感)
    dimension_sensitivity: dict[str, float] = field(default_factory=lambda: {
        "distance": 0.5,
        "price": 0.5,
        "compactness": 0.5,
        "indoor_outdoor": 0.0,   # -1 偏室外, +1 偏室内
    })

    # 类别偏好(命中次数,top 20 保留)
    loved_categories: dict[str, int] = field(default_factory=dict)

    # POI 黑白名单
    disliked_pois: list[str] = field(default_factory=list)
    loved_pois: list[str] = field(default_factory=list)

    # 整体满意度
    avg_satisfaction: float = 0.0
    total_plans: int = 0

    last_updated: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "UserProfile":
        # 容错字段缺失
        defaults = cls(user_id=d.get("user_id", "anon"))
        for k, v in d.items():
            if hasattr(defaults, k):
                setattr(defaults, k, v)
        return defaults

    @classmethod
    def new(cls, user_id: str) -> "UserProfile":
        return cls(user_id=user_id)

    def is_cold_start(self) -> bool:
        """冷启动:不信任画像,用全局默认权重。"""
        return self.total_plans < 3
