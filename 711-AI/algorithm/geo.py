"""
几何与路径算法 - 纯确定性,不依赖 LLM。

- haversine: 地球大圆距离
- adaptive_kmeans: 自适应 K 值聚类
- cluster_visit_order: 簇访问顺序(方向轴投影,避免回头路)
- two_opt: 短路径 TSP 启发式
- route_overlap_ratio: 路线重合度
"""
from __future__ import annotations
import math
from typing import Iterable
import numpy as np
from sklearn.cluster import KMeans


EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """两点间大圆距离(km)。"""
    r1, r2 = math.radians(lat1), math.radians(lat2)
    dr = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dr / 2) ** 2 + math.cos(r1) * math.cos(r2) * math.sin(dl / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def max_pairwise_distance_km(points: list[tuple[float, float]]) -> float:
    """点集中最大两两距离。"""
    if len(points) < 2:
        return 0.0
    max_d = 0.0
    for i in range(len(points)):
        for j in range(i + 1, len(points)):
            d = haversine_km(*points[i], *points[j])
            if d > max_d:
                max_d = d
    return max_d


def adaptive_kmeans(
    points: list[tuple[float, float]],
) -> tuple[list[int], list[tuple[float, float]], int]:
    """
    自适应 K 值:
      最大间距 < 3km  -> K=2
      3-7km           -> K=3
      >7km            -> K=3 (并由调用方提示用户"今天范围较大")

    返回 (labels, centroids, K)。
    points 数量 < K 时 K 自动降为 len(points)。
    """
    if not points:
        return [], [], 0
    max_d = max_pairwise_distance_km(points)
    K = 2 if max_d < 3 else 3
    K = min(K, len(points))
    if K <= 1:
        return [0] * len(points), [points[0]], 1
    arr = np.array(points)
    km = KMeans(n_clusters=K, n_init=10, random_state=42).fit(arr)
    centroids = [(float(c[0]), float(c[1])) for c in km.cluster_centers_]
    return [int(x) for x in km.labels_], centroids, K


def cluster_visit_order(
    origin: tuple[float, float],
    centroids: list[tuple[float, float]],
) -> list[int]:
    """
    方向轴投影:把各簇质心投影到 origin->最远簇质心 的向量上,
    按投影值升序得到自然的"单向推进"访问顺序。
    返回 centroid 索引的排序列表。
    """
    if not centroids:
        return []
    if len(centroids) == 1:
        return [0]
    # 找最远簇质心
    dists = [haversine_km(origin[0], origin[1], c[0], c[1]) for c in centroids]
    farthest_idx = int(np.argmax(dists))
    farthest = centroids[farthest_idx]
    # 方向向量
    vx, vy = farthest[0] - origin[0], farthest[1] - origin[1]
    vlen = math.hypot(vx, vy)
    if vlen == 0:
        return list(range(len(centroids)))
    vx, vy = vx / vlen, vy / vlen
    # 投影值
    projs = []
    for i, c in enumerate(centroids):
        dx, dy = c[0] - origin[0], c[1] - origin[1]
        proj = dx * vx + dy * vy
        projs.append((proj, i))
    projs.sort()
    return [i for _, i in projs]


def route_length_km(points: list[tuple[float, float]]) -> float:
    """路径总长度(欧氏 haversine)。"""
    return sum(
        haversine_km(*points[i], *points[i + 1]) for i in range(len(points) - 1)
    )


def two_opt(
    points: list[tuple[float, float]],
    fixed_indices: set[int] | None = None,
    max_iter: int = 200,
) -> list[int]:
    """
    2-opt 路径优化,返回访问顺序索引列表。
    fixed_indices: 锚点位置,不参与交换。

    对 N≤8 个点这其实是杀鸡用牛刀,但实现简单且效果稳。
    """
    n = len(points)
    if n <= 2:
        return list(range(n))
    if fixed_indices is None:
        fixed_indices = set()

    order = list(range(n))

    def total_length(order_):
        return sum(
            haversine_km(*points[order_[i]], *points[order_[i + 1]])
            for i in range(len(order_) - 1)
        )

    improved = True
    it = 0
    while improved and it < max_iter:
        improved = False
        it += 1
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                if i in fixed_indices or j in fixed_indices:
                    continue
                new_order = order[:i] + order[i:j + 1][::-1] + order[j + 1:]
                if total_length(new_order) < total_length(order) - 1e-6:
                    order = new_order
                    improved = True
    return order


def route_overlap_ratio(route_a_poi_ids: list[str], route_b_poi_ids: list[str]) -> float:
    """两条路线 POI 重合度 = 交集 / min(集合大小)。"""
    a, b = set(route_a_poi_ids), set(route_b_poi_ids)
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


def compactness_score(total_commute_minutes: float) -> float:
    """紧凑性系数 = 1 / (1 + 总通勤分/60),范围 (0, 1]。"""
    return 1.0 / (1.0 + total_commute_minutes / 60.0)
