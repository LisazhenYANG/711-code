"""
CommuteProvider - 通勤时长 + 真实导航数据抽象层。

两个实现:
- MockCommute: haversine + 速度估算,无外部依赖。**也返回 mock 的简化 steps**。
- AmapCommute: 调高德 direction API,返回真实路网时长 + 逐步指示 + polyline。

AmapCommute 调不通自动降级到 MockCommute。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Literal
import os
import time
import logging
import httpx
from algorithm.geo import haversine_km

logger = logging.getLogger(__name__)

TransportMode = Literal["walk", "transit", "drive"]

# 速度估算(km/h),用于 mock 通勤时长
SPEED_KMH = {
    "walk": 5.0,
    "transit": 22.0,
    "drive": 30.0,
}


class CommuteResult(dict):
    """{
        minutes: float,
        distance_km: float,
        mode: str,
        navigation: {
            total_distance_m: int,
            total_duration_s: int,
            polyline: str,                       # 全路径折线 (高德格式: "lng1,lat1;lng2,lat2;...")
            steps: [
                {
                    instruction: "...",          # 中文指示
                    distance_m: int,
                    duration_s: int,
                    polyline: str,
                    road_name: str,
                    action: str,                 # 向左转/直行/右转 等
                }
            ],
            transit_segments: [...] | None       # 公交模式专属,可空
        },
        source: "amap" | "mock"
    }"""
    pass


class CommuteProvider(ABC):
    @abstractmethod
    def get_commute(
        self,
        from_lat: float,
        from_lng: float,
        to_lat: float,
        to_lng: float,
        mode: TransportMode = "walk",
        city: str | None = None,
    ) -> CommuteResult:
        ...


# ════════════════════════════════════════════════════════════
#  Mock 实现
# ════════════════════════════════════════════════════════════


class MockCommute(CommuteProvider):
    """haversine + 速度估算 + 1.3 路网系数。**也返回简化的 mock steps,前端能渲染。**"""

    def get_commute(self, from_lat, from_lng, to_lat, to_lng, mode="walk", city=None):
        d_km = haversine_km(from_lat, from_lng, to_lat, to_lng)
        d_road_km = d_km * 1.3
        speed = SPEED_KMH.get(mode, SPEED_KMH["walk"])
        minutes = (d_road_km / speed) * 60
        seconds = int(minutes * 60)
        distance_m = int(d_road_km * 1000)

        # 生成几条简化的 mock steps
        steps = _make_mock_steps(
            from_lat, from_lng, to_lat, to_lng, mode, distance_m, seconds
        )
        polyline = f"{from_lng:.6f},{from_lat:.6f};{to_lng:.6f},{to_lat:.6f}"

        return CommuteResult(
            minutes=round(minutes, 1),
            distance_km=round(d_road_km, 3),
            mode=mode,
            navigation={
                "total_distance_m": distance_m,
                "total_duration_s": seconds,
                "polyline": polyline,
                "steps": steps,
                "transit_segments": None,
            },
            source="mock",
        )


def _make_mock_steps(from_lat, from_lng, to_lat, to_lng, mode, total_m, total_s):
    """生成 mock 的 2-3 步指示,够前端在 App 内展示。"""
    if total_m < 100:
        return [{
            "instruction": f"步行 {total_m} 米到达目的地",
            "distance_m": total_m,
            "duration_s": total_s,
            "polyline": f"{from_lng:.6f},{from_lat:.6f};{to_lng:.6f},{to_lat:.6f}",
            "road_name": "",
            "action": "直行",
        }]
    mid_lat = (from_lat + to_lat) / 2
    mid_lng = (from_lng + to_lng) / 2
    mode_verb = {"walk": "步行", "drive": "驾车", "transit": "前往"}.get(mode, "前往")
    return [
        {
            "instruction": f"{mode_verb} {total_m // 2} 米",
            "distance_m": total_m // 2,
            "duration_s": total_s // 2,
            "polyline": f"{from_lng:.6f},{from_lat:.6f};{mid_lng:.6f},{mid_lat:.6f}",
            "road_name": "",
            "action": "直行",
        },
        {
            "instruction": f"继续 {total_m - total_m // 2} 米到达目的地",
            "distance_m": total_m - total_m // 2,
            "duration_s": total_s - total_s // 2,
            "polyline": f"{mid_lng:.6f},{mid_lat:.6f};{to_lng:.6f},{to_lat:.6f}",
            "road_name": "",
            "action": "直行",
        },
    ]


# ════════════════════════════════════════════════════════════
#  Amap 实现
# ════════════════════════════════════════════════════════════


_AMAP_ENDPOINTS = {
    "walk": "https://restapi.amap.com/v3/direction/walking",
    "drive": "https://restapi.amap.com/v3/direction/driving",
    "transit": "https://restapi.amap.com/v3/direction/transit/integrated",
}


class AmapCommute(CommuteProvider):
    """
    高德 direction API 实现。

    Walking/Driving 响应结构:
      route.paths[0].{distance, duration, steps[].{instruction, distance, duration, polyline, road, action}}

    Transit 响应结构:
      route.transits[0].{distance, duration, segments[].{walking/bus}}

    任何失败 → 降级到 MockCommute,**降级时也返回 mock steps**(前端不会看到空)。
    """

    def __init__(
        self,
        api_key: str | None = None,
        fallback: CommuteProvider | None = None,
        timeout_s: float = 8.0,
        min_interval_s: float = 1.2,
    ):
        self.api_key = api_key or os.getenv("AMAP_API_KEY", "")
        self.fallback = fallback or MockCommute()
        self._available = bool(self.api_key)
        self._client = httpx.Client(timeout=timeout_s)
        self._min_interval = min_interval_s
        self._last_call = 0.0
        if not self._available:
            logger.info("AmapCommute: 未配置 AMAP_API_KEY,使用 MockCommute 降级")

    def get_commute(self, from_lat, from_lng, to_lat, to_lng, mode="walk", city=None):
        if not self._available:
            return self.fallback.get_commute(from_lat, from_lng, to_lat, to_lng, mode, city)
        try:
            r = self._call_amap(from_lat, from_lng, to_lat, to_lng, mode, city)
            if r is None:
                raise RuntimeError("amap returned no route")
            return r
        except Exception as e:
            logger.warning("AmapCommute 调用失败,降级: %s", e)
            return self.fallback.get_commute(from_lat, from_lng, to_lat, to_lng, mode, city)

    def _call_amap(self, from_lat, from_lng, to_lat, to_lng, mode, city) -> CommuteResult | None:
        url = _AMAP_ENDPOINTS.get(mode)
        if not url:
            return None
        # QPS 限流
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

        params = {
            "key": self.api_key,
            "origin": f"{from_lng:.6f},{from_lat:.6f}",
            "destination": f"{to_lng:.6f},{to_lat:.6f}",
        }
        if mode == "transit":
            # 公交需要城市
            params["city"] = city or "021"  # 上海默认
            params["strategy"] = 0
        try:
            resp = self._client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.warning("amap direction http 失败: %s", e)
            return None
        if data.get("status") != "1":
            logger.warning("amap direction status≠1: %s", data.get("info"))
            return None

        if mode == "transit":
            return self._parse_transit(data, from_lat, from_lng, to_lat, to_lng)
        return self._parse_walk_or_drive(data, mode)

    def _parse_walk_or_drive(self, data: dict, mode: str) -> CommuteResult | None:
        route = data.get("route") or {}
        paths = route.get("paths") or []
        if not paths:
            return None
        path = paths[0]
        distance_m = int(path.get("distance") or 0)
        duration_s = int(path.get("duration") or 0)
        minutes = duration_s / 60.0
        steps_raw = path.get("steps") or []
        steps_out = []
        polyline_chunks = []
        for s in steps_raw:
            poly = s.get("polyline", "")
            steps_out.append({
                "instruction": s.get("instruction", ""),
                "distance_m": int(s.get("distance") or 0),
                "duration_s": int(s.get("duration") or 0),
                "polyline": poly,
                "road_name": s.get("road") or "",
                "action": s.get("action") or s.get("assistant_action") or "直行",
            })
            if poly:
                polyline_chunks.append(poly)
        overall_polyline = ";".join(polyline_chunks)
        return CommuteResult(
            minutes=round(minutes, 1),
            distance_km=round(distance_m / 1000.0, 3),
            mode=mode,
            navigation={
                "total_distance_m": distance_m,
                "total_duration_s": duration_s,
                "polyline": overall_polyline,
                "steps": steps_out,
                "transit_segments": None,
            },
            source="amap",
        )

    def _parse_transit(self, data: dict, from_lat, from_lng, to_lat, to_lng) -> CommuteResult | None:
        route = data.get("route") or {}
        transits = route.get("transits") or []
        if not transits:
            return None
        # 取第一个方案(最佳)
        t = transits[0]
        duration_s = int(t.get("duration") or 0)
        # 公交的 distance 不一定准确,有的版本要从 segments 累加
        try:
            distance_m = int(t.get("distance") or 0)
        except (ValueError, TypeError):
            distance_m = int(haversine_km(from_lat, from_lng, to_lat, to_lng) * 1300)

        # 把 segments 拆成 transit_segments,并且也合成扁平 steps 列表方便前端展示
        transit_segments = []
        steps_flat = []
        polyline_chunks = []
        for seg in t.get("segments") or []:
            walking = seg.get("walking") or {}
            bus = seg.get("bus") or {}

            if walking and walking.get("steps"):
                # 步行段
                walk_steps_raw = walking.get("steps") or []
                walk_dist = int(walking.get("distance") or 0)
                walk_dur = int(walking.get("duration") or 0)
                transit_segments.append({
                    "type": "walking",
                    "distance_m": walk_dist,
                    "duration_s": walk_dur,
                    "steps_count": len(walk_steps_raw),
                })
                for s in walk_steps_raw:
                    poly = s.get("polyline", "")
                    steps_flat.append({
                        "instruction": s.get("instruction", ""),
                        "distance_m": int(s.get("distance") or 0),
                        "duration_s": int(s.get("duration") or 0),
                        "polyline": poly,
                        "road_name": s.get("road") or "",
                        "action": s.get("action") or "步行",
                    })
                    if poly:
                        polyline_chunks.append(poly)

            if bus and bus.get("buslines"):
                # 公交段
                bl = bus["buslines"][0] if bus["buslines"] else {}
                bus_dist = int(bl.get("distance") or 0)
                bus_dur = int(bl.get("duration") or 0)
                line_name = bl.get("name", "公交线路")
                dep = bl.get("departure_stop", {}).get("name", "")
                arr = bl.get("arrival_stop", {}).get("name", "")
                via_n = bl.get("via_num", "0")
                transit_segments.append({
                    "type": "bus",
                    "line_name": line_name,
                    "departure_stop": dep,
                    "arrival_stop": arr,
                    "via_stops": int(via_n) if str(via_n).isdigit() else 0,
                    "distance_m": bus_dist,
                    "duration_s": bus_dur,
                })
                steps_flat.append({
                    "instruction": f"乘坐 {line_name},{dep} → {arr}(经停 {via_n} 站)",
                    "distance_m": bus_dist,
                    "duration_s": bus_dur,
                    "polyline": bl.get("polyline", ""),
                    "road_name": line_name,
                    "action": "公交",
                })
                if bl.get("polyline"):
                    polyline_chunks.append(bl["polyline"])

        return CommuteResult(
            minutes=round(duration_s / 60.0, 1),
            distance_km=round(distance_m / 1000.0, 3),
            mode="transit",
            navigation={
                "total_distance_m": distance_m,
                "total_duration_s": duration_s,
                "polyline": ";".join(polyline_chunks),
                "steps": steps_flat,
                "transit_segments": transit_segments,
            },
            source="amap",
        )


def get_default_commute_provider() -> CommuteProvider:
    if os.getenv("AMAP_API_KEY"):
        return AmapCommute()
    return MockCommute()
