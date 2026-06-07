# Eval Harness

每次改算法、改 agent prompt、改评分权重,都跑一遍这里看分数有没有掉。

## 跑分

```bash
python evals/runners/run_eval.py            # 完整跑(LLM 在线时含 agent 辩论)
python evals/runners/run_eval.py --no-llm   # 只测算法层
```

## 文件结构

```
evals/
  golden_set/
    sample.json       MVP 占位的 5 个 case,后续扩到 30-50
  runners/
    run_eval.py       跑分入口
  scorers/
    feasibility.py    硬约束达成率(必须 100%,掉到 100% 以下就告警)
```

## 扩展 golden set

往 `sample.json` 加新 case,字段:

```json
{
  "case_id": "case_XXX_short_description",
  "description": "测试什么场景",
  "intent": {...},
  "weather": {"condition": "晴"},
  "expected": {
    "min_routes": 1,
    "max_routes": 3,
    "max_total_commute_minutes": 120,
    "all_pois_must_be_indoor": false,
    "should_include_categories": [],
    "should_not_include_pois": [],
    "should_drop_some_categories": false
  }
}
```

## 未来可加的 scorers

- `quality.py` - Top-3 与人工标注的重合度
- `debate_quality.py` - LLM-as-judge 评估 agent 发言是否符合人格
- `stability.py` - 同输入跑 3 次的方差
- `latency.py` - P50/P95 延迟监控,对照 PRD 8 秒红线

## CI 接入

把 `python evals/runners/run_eval.py --no-llm` 加进 CI,任何 PR 跑一遍。
带 LLM 的完整 eval 放在 nightly,因为耗时和成本高。
