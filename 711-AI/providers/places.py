"""
PlacesProvider - 周边搜索抽象层。

两个实现:
- AmapPlaces:  调高德 /v3/place/around 拿真实餐厅
- MockPlaces:  从 data/mock_restaurants.json 按距离过滤

无 AMAP_API_KEY 时自动降级到 MockPlaces。
"""
from __future__ import annotations
from abc import ABC, abstractmethod
import os
import json
import time
import logging
from pathlib import Path
import httpx
from algorithm.geo import haversine_km

logger = logging.getLogger(__name__)


class PlacesProvider(ABC):
    @abstractmethod
    def search_around(
        self,
        center_lat: float,
        center_lng: float,
        keyword: str = "",
        types: str = "",
        radius_m: int = 1000,
        max_results: int = 25,
    ) -> list[dict]:
        """返回标准化后的店铺列表。每个 dict 至少含:
        id, name, lat, lng, address, distance_m, rating, avg_price,
        cuisine, sub_category, open_hours, supports_queue_ticket,
        supports_table_booking, tags, intro,
        base_queue_at_peak, queue_speed_per_minute, typical_wait_minutes_at_peak,
        max_party_size, has_private_room, is_halal, is_vegetarian_friendly, has_seafood
        """
        ...


# ─────────────────────────────────────────────────────────────
#  Mock 实现 - 离线餐厅库
# ─────────────────────────────────────────────────────────────

_MOCK_RESTAURANTS: list[dict] | None = None


def _load_mock_restaurants() -> list[dict]:
    global _MOCK_RESTAURANTS
    if _MOCK_RESTAURANTS is not None:
        return _MOCK_RESTAURANTS
    path = Path(__file__).parent.parent / "data" / "mock_restaurants.json"
    if not path.exists():
        logger.warning("data/mock_restaurants.json 不存在,MockPlaces 返回空")
        _MOCK_RESTAURANTS = []
        return _MOCK_RESTAURANTS
    with path.open("r", encoding="utf-8") as f:
        _MOCK_RESTAURANTS = json.load(f)
    return _MOCK_RESTAURANTS


class MockPlaces(PlacesProvider):
    """离线降级 - 用 mock_restaurants.json + 距离过滤。"""

    def search_around(
        self, center_lat, center_lng, keyword="", types="",
        radius_m=1000, max_results=25,
    ) -> list[dict]:
        all_r = _load_mock_restaurants()
        results = []
        for r in all_r:
            d_km = haversine_km(center_lat, center_lng, r["lat"], r["lng"])
            d_m = d_km * 1000
            if d_m > radius_m:
                continue
            # keyword 软匹配 - 命中菜系/名字/小类
            if keyword:
                hay = " ".join([
                    r.get("cuisine", ""),
                    r.get("sub_category", ""),
                    r.get("name", ""),
                    " ".join(r.get("tags", [])),
                ])
                if keyword not in hay:
                    continue
            out = dict(r)
            out["distance_m"] = round(d_m, 1)
            results.append(out)
        results.sort(key=lambda x: x["distance_m"])
        return results[:max_results]


# ─────────────────────────────────────────────────────────────
#  Amap 实现 - 真实周边搜索
# ─────────────────────────────────────────────────────────────


class AmapPlaces(PlacesProvider):
    """
    高德 place/around 实现:
      https://restapi.amap.com/v3/place/around?location=lng,lat&keywords=...&radius=...&key=...

    无 key 或调用失败 → 自动降级到 MockPlaces。
    """

    def __init__(self, api_key: str | None = None, fallback: PlacesProvider | None = None):
        self.api_key = api_key or os.getenv("AMAP_API_KEY", "")
        self.fallback = fallback or MockPlaces()
        self._client = httpx.Client(timeout=8.0)
        self._min_interval = 1.2
        self._last_call = 0.0
        self._available = bool(self.api_key)
        if not self._available:
            logger.info("AmapPlaces: 未配置 AMAP_API_KEY,使用 MockPlaces 降级")

    def search_around(
        self, center_lat, center_lng, keyword="", types="",
        radius_m=1000, max_results=25,
    ) -> list[dict]:
        if not self._available:
            return self.fallback.search_around(
                center_lat, center_lng, keyword, types, radius_m, max_results
            )
        try:
            r = self._call_amap(center_lat, center_lng, keyword, types, radius_m)
            if not r:
                raise RuntimeError("amap returned empty")
            return self._normalize(r, center_lat, center_lng)[:max_results]
        except Exception as e:
            logger.warning("AmapPlaces 调用失败,降级: %s", e)
            return self.fallback.search_around(
                center_lat, center_lng, keyword, types, radius_m, max_results
            )

    def _call_amap(self, lat, lng, keyword, types, radius_m) -> dict | None:
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

        params = {
            "key": self.api_key,
            "location": f"{lng:.6f},{lat:.6f}",
            "radius": min(50000, radius_m),
            "extensions": "all",
            "offset": 25,
            "page": 1,
        }
        if keyword:
            params["keywords"] = keyword
        if types:
            params["types"] = types
        resp = self._client.get("https://restapi.amap.com/v3/place/around", params=params)
        resp.raise_for_status()
        data = resp.json()
        if data.get("status") != "1":
            logger.warning("AmapPlaces status != 1: %s", data.get("info"))
            return None
        return data

    def _normalize(self, raw: dict, center_lat: float, center_lng: float) -> list[dict]:
        """高德 POI → 我们统一格式。许多字段需要从 biz_ext / type 字段推测。"""
        out = []
        for p in raw.get("pois", []):
            try:
                loc = p.get("location", "")  # "lng,lat"
                if "," not in loc:
                    continue
                lng_s, lat_s = loc.split(",")
                lng_f, lat_f = float(lng_s), float(lat_s)
                d_m = float(p.get("distance", haversine_km(center_lat, center_lng, lat_f, lng_f) * 1000))
                biz = p.get("biz_ext") or {}
                cost = biz.get("cost", "")
                rating = biz.get("rating", "")
                try:
                    avg_price = float(cost) if cost else 0
                except (ValueError, TypeError):
                    avg_price = 0
                try:
                    rating_f = float(rating) if rating else 4.0
                except (ValueError, TypeError):
                    rating_f = 4.0

                # 高德 type 字段格式 "餐饮服务;中餐厅;本帮江浙菜"
                types_str = p.get("type", "") or ""
                cuisine = _amap_type_to_cuisine(types_str)
                sub = types_str.split(";")[-1] if types_str else ""

                out.append({
                    "id": p.get("id") or f"amap_{lng_s}_{lat_s}",
                    "name": p.get("name", ""),
                    "cuisine": cuisine,
                    "sub_category": sub,
                    "lat": lat_f,
                    "lng": lng_f,
                    "address": p.get("address", ""),
                    "distance_m": d_m,
                    "rating": rating_f,
                    "avg_price": avg_price,
                    "open_hours": [[10, 22]],  # 高德 around 不返回营业时间,默认值
                    "supports_queue_ticket": True,
                    "supports_table_booking": avg_price >= 80,
                    "max_party_size": 10,
                    "has_private_room": avg_price >= 150,
                    "is_halal": "清真" in (p.get("name", "") + types_str),
                    "is_vegetarian_friendly": "素" in (p.get("name", "") + types_str),
                    "has_seafood": "海鲜" in types_str or "日料" in cuisine,
                    "tags": [],
                    "intro": p.get("name", ""),
                    "base_queue_at_peak": 5 if rating_f >= 4.5 else 2,
                    "queue_speed_per_minute": 0.5,
                    "typical_wait_minutes_at_peak": 10 if rating_f >= 4.5 else 4,
                    "_source": "amap",
                })
            except Exception as e:
                logger.debug("normalize 跳过一条 amap poi: %s", e)
                continue
        return out


_CUISINE_KEYWORDS = {
    "本帮菜": ["本帮", "江浙", "上海菜"],
    "川菜": ["川菜", "四川", "麻辣", "火锅"],
    "粤菜": ["粤", "广", "潮汕", "潮州"],
    "湘菜": ["湘", "湖南"],
    "东北菜": ["东北", "东三省"],
    "日料": ["日", "寿司", "拉面", "居酒屋"],
    "韩餐": ["韩", "韩式", "烤肉"],
    "西餐": ["西餐", "意餐", "法餐", "披萨", "意式", "法式", "Pizza"],
    "东南亚": ["泰", "越南", "新马"],
    "快餐": ["快餐", "汉堡", "麻辣烫"],
    "面食": ["面", "粉", "饺", "小笼", "馄饨"],
    "咖啡馆": ["咖啡", "Coffee"],
    "轻食": ["轻食", "沙拉", "健康"],
    "清真": ["清真", "兰州", "新疆"],
    "素食": ["素", "斋"],
}


def _amap_type_to_cuisine(amap_type: str) -> str:
    if not amap_type:
        return "其他"
    for cui, kws in _CUISINE_KEYWORDS.items():
        for kw in kws:
            if kw in amap_type:
                return cui
    return "其他"


# ─────────────────────────────────────────────────────────────
#  Default provider 工厂
# ─────────────────────────────────────────────────────────────

_default_places: PlacesProvider | None = None


def get_default_places_provider() -> PlacesProvider:
    global _default_places
    if _default_places is None:
        if os.getenv("AMAP_API_KEY"):
            _default_places = AmapPlaces()
        else:
            _default_places = MockPlaces()
    return _default_places
