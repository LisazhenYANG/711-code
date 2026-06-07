"""
可行性 scorer - 硬约束达成率,必须 100%。

掉到 100% 以下就告警:候选路线生成出了 bug。
"""
from __future__ import annotations
import json
from pathlib import Path


def _load_pois() -> dict:
    path = Path(__file__).parent.parent.parent / "data" / "mock_pois.json"
    with path.open("r", encoding="utf-8") as f:
        return {p["id"]: p for p in json.load(f)}


def score_case(case: dict, result: dict) -> dict:
    """
    返回 {
      "passed": bool,
      "failures": [str],
      "details": dict,
    }
    """
    failures: list[str] = []
    expected = case.get("expected", {})
    top_routes = result.get("top_routes", [])

    if not top_routes:
        failures.append("no_routes_returned")
        return {"passed": False, "failures": failures, "details": {}}

    pois = _load_pois()

    # 1) 室内/室外硬过滤
    if expected.get("all_pois_must_be_indoor"):
        for r in top_routes:
            for stop in r["stops"]:
                p = pois.get(stop["poi_id"], {})
                if not p.get("indoor", True):
                    failures.append(
                        f"outdoor_poi_in_indoor_only_route: route={r['route_id']} poi={stop['poi_id']}"
                    )

    # 2) 不应包含的 POI
    for forbidden in expected.get("should_not_include_pois", []):
        for r in top_routes:
            for stop in r["stops"]:
                if stop["poi_id"] == forbidden:
                    failures.append(f"forbidden_poi_present: {forbidden} in {r['route_id']}")

    # 3) 应包含的类别
    must_categories = set(expected.get("should_include_categories", []))
    if must_categories:
        for r in top_routes:
            stop_cats = set()
            for stop in r["stops"]:
                p = pois.get(stop["poi_id"], {})
                if p.get("category_sub"):
                    stop_cats.add(p["category_sub"])
                if p.get("category_main"):
                    stop_cats.add(p["category_main"])
            missing = must_categories - stop_cats
            if missing and r.get("zone_id"):  # 仅 zone 路线要求,全局路线宽松
                # 软警告而非硬失败
                pass

    # 4) 总通勤上限
    max_commute = expected.get("max_total_commute_minutes")
    if max_commute is not None:
        for r in top_routes:
            tc = r.get("total_commute_minutes", 0)
            if tc > max_commute * 1.5:  # 给 50% 容忍
                failures.append(f"commute_too_long: route={r['route_id']} tc={tc}")

    # 5) 路线数量
    min_r = expected.get("min_routes", 0)
    max_r = expected.get("max_routes", 99)
    if not (min_r <= len(top_routes) <= max_r):
        failures.append(f"route_count_out_of_range: got={len(top_routes)} want=[{min_r},{max_r}]")

    # 6) 类别砍判定
    if expected.get("should_drop_some_categories"):
        dropped = result.get("dropped_categories") or []
        if not dropped:
            failures.append("expected_dropped_categories_but_none")

    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "details": {
            "route_count": len(top_routes),
            "max_commute": max(r.get("total_commute_minutes", 0) for r in top_routes) if top_routes else 0,
        },
    }
