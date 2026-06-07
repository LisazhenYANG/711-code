from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


_DEFAULT_GEO_BASE_URL = "https://geoapi.qweather.com"
_DEFAULT_WEATHER_BASE_URL = "https://devapi.qweather.com"
_DEFAULT_TIMEOUT_S = 8
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
_CITY_ADM = {
    "上海": "上海",
    "北京": "北京",
    "广州": "广东",
    "深圳": "广东",
    "杭州": "浙江",
    "南京": "江苏",
}


def fallback_weather(city: str) -> dict[str, str]:
    return {
        "city": city,
        "date": "今天",
        "temp": "24-29°C",
        "condition": "多云转晴",
        "rain": "15%",
        "suitable": "适合出行",
        "source": "mock",
    }


def fetch_weather(city: str) -> dict[str, str]:
    api_key = _config_value("WEATHER_API_KEY")
    if not api_key:
        return fallback_weather(city)

    try:
        location_id, resolved_city = _lookup_location(city)
        weather = _get_json(
            f"{_config_value('WEATHER_API_BASE_URL', _DEFAULT_WEATHER_BASE_URL).rstrip('/')}/v7/weather/now",
            {"location": location_id, "lang": "zh", "unit": "m"},
            api_key,
        )
        now = weather.get("now") or {}
        if weather.get("code") != "200" or not now:
            return fallback_weather(city)
        temp = (now.get("temp") or "").strip()
        feels_like = (now.get("feelsLike") or "").strip()
        rain = (now.get("precip") or "").strip()
        condition = (now.get("text") or "天气良好").strip()
        return {
            "city": resolved_city,
            "date": "今天",
            "temp": f"{temp}°C" if temp else "--",
            "condition": condition,
            "rain": f"{rain}mm" if rain else "--",
            "feels_like": f"{feels_like}°C" if feels_like else "--",
            "wind": (now.get("windDir") or "").strip(),
            "suitable": _suitable_text(condition),
            "source": "qweather",
        }
    except Exception:
        return fallback_weather(city)


def _lookup_location(city: str) -> tuple[str, str]:
    api_key = _config_value("WEATHER_API_KEY")
    query = {"location": city, "range": "cn", "number": 1, "lang": "zh"}
    adm = _CITY_ADM.get(city)
    if adm:
        query["adm"] = adm
    payload = _get_json(
        f"{_config_value('WEATHER_GEO_BASE_URL', _DEFAULT_GEO_BASE_URL).rstrip('/')}/geo/v2/city/lookup",
        query,
        api_key,
    )
    locations = payload.get("location") or []
    if payload.get("code") != "200" or not locations:
        raise ValueError(f"city lookup failed for {city}")
    item = locations[0]
    return str(item.get("id") or city), str(item.get("name") or city)


def _get_json(base_url: str, params: dict[str, Any], api_key: str) -> dict[str, Any]:
    query = urlencode({k: v for k, v in params.items() if v not in (None, "")})
    request = Request(
        f"{base_url}?{query}",
        headers={"X-QW-Api-Key": api_key, "Accept": "application/json"},
    )
    with urlopen(request, timeout=_DEFAULT_TIMEOUT_S) as response:
        return json.loads(response.read().decode("utf-8"))


def _suitable_text(condition: str) -> str:
    if any(token in condition for token in ("暴雨", "大雨", "雷", "雪")):
        return "建议优先室内行程"
    if "雨" in condition:
        return "建议带伞出行"
    if any(token in condition for token in ("晴", "多云", "阴")):
        return "适合出行"
    return "注意天气变化"


def _config_value(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value:
        return value.strip()
    if not _ENV_PATH.exists():
        return default
    for line in _ENV_PATH.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        env_key, env_value = stripped.split("=", 1)
        if env_key.strip() == key:
            return env_value.strip()
    return default
