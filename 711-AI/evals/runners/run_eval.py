"""
Eval 跑分入口。

用法:
  python evals/runners/run_eval.py
  python evals/runners/run_eval.py --no-llm   只测算法层
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path

# 把项目根加入 path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-llm", action="store_true")
    parser.add_argument("--golden", default=str(ROOT / "evals" / "golden_set" / "sample.json"))
    args = parser.parse_args()

    if args.no_llm:
        os.environ.pop("DEEPSEEK_API_KEY", None)

    from graph.builder import get_planning_graph
    from evals.scorers.feasibility import score_case

    with open(args.golden, "r", encoding="utf-8") as f:
        cases = json.load(f)

    graph = get_planning_graph()
    passed = 0
    failed = 0
    durations: list[float] = []

    print(f"\n跑 {len(cases)} 个 eval case...\n")

    for case in cases:
        cid = case["case_id"]
        initial = {
            "user_id": f"eval_{cid}",
            "intent": case["intent"],
            "weather": case.get("weather", {"condition": "晴"}),
            "follow_up_rounds": 0,
            "candidate_pool": [],
            "candidate_routes": [],
            "debate_transcript": [],
            "top_routes": [],
        }
        t0 = time.time()
        try:
            result = graph.invoke(initial)
            dur = time.time() - t0
            durations.append(dur)
            result["dropped_categories"] = result.get("intent", {}).get("_dropped_categories", [])
            score = score_case(case, result)
            tag = "✅" if score["passed"] else "❌"
            print(f"{tag} {cid:40s}  {dur:5.1f}s  routes={score['details'].get('route_count', 0)}")
            if not score["passed"]:
                for f in score["failures"]:
                    print(f"     · {f}")
                failed += 1
            else:
                passed += 1
        except Exception as e:
            dur = time.time() - t0
            durations.append(dur)
            print(f"💥 {cid:40s}  {dur:5.1f}s  exception: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"通过: {passed}/{len(cases)}   失败: {failed}/{len(cases)}")
    if durations:
        durations.sort()
        p50 = durations[len(durations) // 2]
        p95 = durations[int(len(durations) * 0.95)]
        print(f"延迟 P50={p50:.1f}s  P95={p95:.1f}s")
    print(f"{'=' * 60}")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
