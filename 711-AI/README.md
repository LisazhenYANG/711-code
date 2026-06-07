# Travel Route Engine

本地出游路线推荐引擎,基于 LangGraph 编排:确定性算法层产候选,多 Agent 辩论挑 Top-3。

## 架构

```
意图解析 → 用户画像加载 → 可达圈 → 时间槽 → 候选召回(+RAG)
        → POI 评分 → 候选池 → 聚类+簇序 → Zone路线 + 全局路线
        → 过滤排序产 8-12 条可行候选
        → 4 Agent 辩论(体验/实用/懂你 + 主持)
        → Top-3 + 辩论 transcript
        → 用户反馈 → 画像 EMA 更新
```

- 确定性算法层 (`algorithm/`):保证可行性、距离、聚类、2-opt
- Agent 评议层 (`agents/`):3 派人格 + 1 主持,用 DeepSeek 跑辩论
- 自迭代 Harness (`profile/`):EMA 更新用户画像,越用越懂
- Eval Harness (`evals/`):golden set + 自动跑分(占位,MVP 后扩)

## 快速开始

```bash
pip install -r requirements.txt
cp .env.example .env
# 把 DEEPSEEK_API_KEY 填进 .env

# 跑 demo (会调 LLM,需要 key)
python demo.py

# 只跑算法层,不调 LLM (验证候选生成)
python demo.py --no-llm

# 启动 API
uvicorn main:app --reload --port 8000
```

## 可插拔接口

- `providers/commute.py`: `CommuteProvider` 抽象,内置 `MockCommute`(haversine 估算) 和 `AmapCommute`(高德,占位)
- `providers/llm.py`: DeepSeek 客户端
- `providers/embedding.py`: 向量化,内置 mock

## 数据流

POI 数据见 `data/mock_pois.json`,包含字段:
`id / 名字 / 大类 / 小类 / 经纬度 / 开放时间 / 榜单分(0-5) / 好评率(0-1) / 室内外 / 默认停留时长 / 适配人群 / 均价 / 是否免费 / 是否需预约 / 票价档位 / 标签 / 简介`

用户画像见 `profile/schema.py`,EMA 更新逻辑见 `profile/ema.py`。
