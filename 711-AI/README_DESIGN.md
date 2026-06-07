# 说明文档 - Travel Route Engine

> 本地出游路线推荐引擎。给定用户意图(出发地、时间、人数、心情),返回 Top-3 路线 + 4 个 AI 人格的辩论过程。
> 越用越懂用户。

---

## 一、这是什么

一个**两层混合架构**的旅行路线规划引擎:

```
┌─────────────────────────────────────────────────────────────┐
│  确定性算法层                                                  │
│  保证可行性、距离合理、时间够、健康约束满足、天气适配                 │
│  产出 8-12 条可行候选路线                                       │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Agent 评议层 (4 个 LLM 人格)                                  │
│  体验派(榜单口碑) / 实用派(通勤距离) / 懂你派(用户画像)            │
│  + 主持人(归类 Top-3、贴标签、写文案)                            │
│  辩论 transcript 作为产品特性展示给用户                          │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
                  Top-3 + 辩论过程
                           ↓
                  用户反馈 → EMA 更新画像
                           ↓
                  下次规划自动用新画像
```

**核心设计原则**: 硬约束(可达圈/开放时间/健康禁忌/暴雨过滤等)交给确定性算法,**LLM 不能违反硬约束**。软偏好(哪条最好玩、贴什么标签)交给 agent 辩论,人格化对话本身就是产品价值。

---

## 二、为什么这么设计

| 选择 | 原因 |
|---|---|
| 算法层 + Agent 层混合,而不是纯 LLM | 纯 LLM 拼路线会忽略硬约束(超距、跨时段、违背健康禁忌)。算法层保证可行,Agent 只在可行候选里挑。 |
| 4 个 agent,不是 1 个 | 一个 agent 给出推荐看起来像黑盒;多人格辩论让用户看到"为什么选这条",而且不同维度的论点会真正发生冲突,提升结果质量。 |
| 辩论过程展示给用户 | 用户原话: 想要"活性与优雅"。Top-3 是结果,辩论是过程,过程本身是产品差异化点。 |
| EMA 更新画像而不是覆盖 | 一次差评不应该把整个画像带偏。EMA(新信号占 15-30%)让画像稳定演进。 |
| 三层 Harness 分开做 | Eval(测试)、Agent(LangGraph)、Self-Improvement(画像)三件事性质不同,工程上分层。 |

---

## 三、目录结构

```
travel_route_engine/
├── README.md                   # 使用文档(怎么跑)
├── README_DESIGN.md            # 本文件 - 说明文档(为什么这么做)
├── requirements.txt
├── .env.example                # 环境变量模板,key 待你填
├── demo.py                     # 端到端 demo
├── state.py                    # LangGraph 全局状态对象 TripState
│
├── data/
│   └── mock_pois.json          # 36 个 POI 假数据(基于 HTML 原型扩展)
│
├── algorithm/                  # 确定性算法层(不依赖 LLM)
│   ├── geo.py                  # haversine / K-Means / 2-opt / 方向轴投影
│   ├── scoring.py              # 两套评分公式 + 天气/价格/人数乘数 + 画像调权
│   └── time_budget.py          # 可达圈 / 时间窗口 / 餐饮挖洞 / 类别砍
│
├── providers/                  # 可插拔外部依赖
│   ├── commute.py              # CommuteProvider 抽象 + MockCommute + AmapCommute(占位,自动降级)
│   ├── llm.py                  # DeepSeek 客户端(OpenAI 兼容 API)
│   └── embedding.py            # 向量化抽象 + MockEmbedding(词袋 RAG)
│
├── profile/                    # ★ 自迭代 Harness
│   ├── schema.py               # UserProfile dataclass
│   ├── ema.py                  # EMA 更新策略 (agent_weights / dimension / satisfaction)
│   └── store.py                # JSON 文件持久化(MVP,生产换 DB)
│
├── agents/                     # ★ 4 个 AI 人格
│   ├── personas.py             # 体验派 / 实用派 / 懂你派 / 主持人 的 system prompt
│   └── debate.py               # 2 轮辩论 + 主持人归类(含 LLM 不可用时的降级)
│
├── graph/                      # ★ LangGraph 编排
│   ├── nodes.py                # 11 个图节点的实现
│   └── builder.py              # 装配主图 + 反馈写回图
│
├── api/
│   └── main.py                 # FastAPI: POST /plan  POST /feedback  GET /health  GET /pois
│
└── evals/                      # ★ Eval Harness(MVP 占位)
    ├── README.md
    ├── golden_set/sample.json  # 5 个测试用例
    ├── scorers/feasibility.py  # 硬约束达成率打分
    └── runners/run_eval.py     # 跑分入口
```

---

## 四、规划主图数据流

每个节点的职责、输入、输出:

```
①  node_intent_parse  (意图解析)
   入: 用户填的 chips + 自由文本
   出: 结构化 intent (origin/time/people/transport/moods/sub_categories/budget/health/...)
   特性: 缺必填 → 最多 2 轮追问;LLM 解析自由文本里的预算、健康禁忌、关键词

②  node_profile_load  (画像加载)
   入: user_id
   出: user_profile (agent_weights / dimension_sensitivity / loved_pois / disliked_pois ...)
   备注: 自迭代 Harness 接入点 ①

③  node_reachable  (可达圈)
   入: transport_mode + time_slot
   出: reachable_radius_km
   规则: walk=2/transit=13/drive=12 (km),× 时间系数(>6h ×1.5, 3-6h ×1.0, <3h ×0.6)

④  node_time_slots  (时间窗口)
   入: time_slot
   出: time_window {start, end, available_hours, food_blocks_within} + max_pois_per_day
   规则: 餐饮时段(12-13:30, 18-19:30)不占 POI 配额,
         可排数 = floor(纯POI时间 × 85% / (75min 停留 + 20min 通勤))

⑤  node_candidates  (候选召回 + 硬过滤)
   入: 全量 POI + intent + radius + weather + profile
   出: candidate_pool (符合所有硬约束的 POI 集)
   硬过滤层级:
     - 健康禁忌(膝盖不好 → 排除长时间户外大景区)
     - 可达圈
     - 开放时间与时间窗口重叠
     - 暴雨 → 排除户外
     - 选了类别 → 必须匹配类别;没选 → RAG 语义召回 top 40
     - 画像黑名单

⑥  node_score  (POI 评分)
   入: candidate_pool + intent + weights
   出: 每个 POI 带 score + breakdown
   公式:
     选了类别:  距离 ×0.45 + 榜单 ×0.45 + 人数适配 ×0.10
     没选类别:  距离 ×0.30 + 榜单 ×0.30 + 人数适配 ×0.10 + RAG语义 ×0.30
   再乘:        天气乘数(室内外) × 价格系数
   画像调权:    distance_sensitivity 高 → 距离权重 ×1.2  (自迭代 Harness 接入点 ②)

⑦  node_cluster_and_pool  (聚类 + 簇序 + 类别砍)
   入: scored candidates + max_pois_per_day
   出: clusters [{zone_id, members, centroid, order}]
   逻辑:
     - 每类取 top max(3, 总数/类别数)
     - 类别数 > 可排数 → 按"该类别下最高 POI 分"砍掉垫底类别
     - K-Means: 最大间距<3km → K=2, 否则 K=3
     - 方向轴投影: origin → 最远簇质心 的方向,各簇按投影值升序得访问顺序

⑧⑨ node_route_gen  (各 Zone 路线 + 全局最优)
   入: clusters + scored_pool + 锚点
   出: candidate_routes (8-12 条可行路线)
   逻辑:
     - Zone 内每类选最高分,缺类别从其他区跨区引入(标记 cross_zone)
     - 2-opt 优化访问顺序,锚点不参与交换
     - 通勤时长由 CommuteProvider 计算
     - 全局最优 = 各类全局第一拼起来,2-opt 后若与 zone 路线重合 <60% 才加入

⑩  node_filter_rank  (过滤排序)
   入: candidate_routes
   出: 去重后的 candidate_routes (重合 >60% 留高分),top 12

⑪  node_debate  (4 Agent 辩论)
   入: candidate_routes + intent + profile
   出: top_routes (Top-3 带 label + summary) + debate_transcript
   流程:
     Round 1: 三派并行表态(各自 JSON 输出 stance + speech)
     Round 2: 三派轮流反驳(看完 Round 1 后)
     Host:    主持人挑 Top-3、贴标签(精华首选/轻松漫游/小众惊喜)、写 15-25 字描述
   降级: LLM 不可用 → 算法 quality_score Top-3 + 模板化标签

→ END
```

**反馈写回是独立小图**(`build_feedback_graph`):

```
node_feedback_write
  入: user_choice_route_id, user_deleted_poi_ids, user_rating, debate_transcript
  出: 更新后的 user_profile (写回磁盘)
  EMA 更新:
    - 选了哪条 → 主导 agent 权重 +Δ
    - 删了哪个 POI → 推它的 agent 权重 -Δ + 加进 disliked
    - 评分 → avg_satisfaction EMA 更新
    - 选中路线的 POI 类别 → loved_categories +1
```

---

## 五、关键设计决策

### 5.1 评分公式两套版本

PRD 第五章规定:用户选了类别和没选类别的评分逻辑不同。

- **选了类别**:用户已经表达明确偏好,不需要 RAG 兜底,权重集中在距离 / 榜单 / 人数。
- **没选类别**:用户表达模糊,需要从自由文本里抽语义,所以加 30% 语义相似度权重(降一些距离 / 榜单的权重让出来)。

### 5.2 可达圈三档

我们之前讨论时定的:

```
walk     基础半径 2 km
transit  基础半径 13 km   (公共交通 10-15 km 取中)
drive    基础半径 12 km   (市区拥堵驾车 ≈ 公交)
```

乘时间系数: 全天 ×1.5,半天 ×1.0,小于 3 小时 ×0.6。

### 5.3 类别超额裁剪

PRD 提到"选太多类别 → 根据平均游玩时间精简",但没说怎么选保留哪个。

**实现策略**: 按"该类别下最高 POI 分"排序,保留头部 max_pois 个类别,砍掉垫底的。被砍的类别会在响应里返回 `dropped_categories`,前端可以提示用户。

### 5.4 人数适配

PRD 没明确人数适配的分数。**我们的规则**:

- 完全匹配 → 1.0
- 相邻档(独行↔情侣 / 情侣↔小团 / 小团↔大队) → 0.6
- 不匹配 → 0.2

档位顺序: 独行 < 情侣 < 小团(3-4 人) < 大队(5+ 人)。亲子是独立类。

### 5.5 天气乘数

```
晴     室内/室外 ×1.0
小雨   室外 ×0.5    室内 ×1.3
大雨   室外 ×0.15   室内 ×1.8
暴雨   室外硬过滤   室内 ×1.8
```

### 5.6 跨区引入

某个 zone 内缺某个类别(用户选了 3 类但 zone 里只有 2 类的 POI)时,从其他区拉一个最近的同类 POI 进来,在 route 里 `cross_zone=true` 标记。前端应该显示"稍远的小推荐"提示。

### 5.7 锚点

用户在 intent 里给 `locked_poi_ids`(必须去的点),进入 2-opt 时这些点的位置固定,只重排其他点。算法不会移走或删除锚点。

### 5.8 路线去重

PRD 规定 Top-3 之间 POI 重合度 < 60%,防止"3 条路线长得一样"。

`route_overlap_ratio(A, B) = |A ∩ B| / min(|A|, |B|)`

`filter_rank` 节点按 quality_score 排序贪心保留:每加一条新路线,与已保留路线重合 >60% 就跳过。

---

## 六、Agent 辩论机制

### 6.1 人格设定

| Agent | 关心维度 | 语气 | 不该谈什么 |
|---|---|---|---|
| 体验派 ✨ | 榜单/好评率/特色/口碑 | 热情、画面感、形容词多 | 通勤时间、用户历史 |
| 实用派 📍 | 通勤分钟/紧凑性/总距离 | 冷静、爱算账、用数字 | 否定高分点(只反对绕路) |
| 懂你派 🧭 | 用户画像/历史/自由文本 | 像老朋友提醒 | 复述榜单、算通勤 |
| 主持人 🎙️ | 协调 + 归类 + 标签 + 文案 | 克制、不抢戏 | 自己发表观点 |

人格语气分明很重要,否则辩论看起来像一个人在自言自语。

### 6.2 辩论流程

```
Round 1 (并行):
  每个派系: 看完所有候选路线 → 输出 stance(支持/反对哪条) + speech(3-5 句)

Round 2 (顺序,可选):
  每个派系: 看完 Round 1 别人的发言 → 选 1-2 条反驳或附议

Host (最后):
  看完整个 transcript → 挑 Top-3 → 贴标签 → 写 15-25 字描述
```

每个 agent 强制 JSON 输出,主持人特别低 temperature(0.3)保稳定。

### 6.3 标签规则

主持人按以下规则分配三个标签(每条 Top-3 一个,不重复):

- **精华首选**: 体验派最推 / 总分最高 / 榜单口碑顶
- **轻松漫游**: 实用派最推 / 通勤最短 / 紧凑性最优
- **小众惊喜**: 好评率高但榜单分中等 / 懂你派识别为非主流但符合用户

### 6.4 降级策略

LLM 不可用(没 key、超时、JSON 解析失败)时:

- 不抛错让用户看到红屏
- 按算法层 `quality_score` 排序取 Top-3
- 标签按"总分最高=精华、通勤最短=轻松、剩下=小众"模板化分配
- 响应里 `llm_degraded=true`,前端可提示"AI 评议不可用,显示算法推荐"

---

## 七、自迭代 Harness 详解

### 7.1 user_profile 字段

```python
@dataclass
class UserProfile:
    user_id: str
    agent_weights:        {experience, pragmatic, personal: 1.0}     # 三派权重
    dimension_sensitivity: {distance, price, compactness, indoor_outdoor}  # 维度敏感度
    loved_categories:     {小类: 命中次数}  # top 20
    disliked_pois:        [poi_id]  # 最近 100 个
    loved_pois:           [poi_id]  # 最近 100 个
    avg_satisfaction:     0.0~1.0
    total_plans:          int       # 冷启动判断: < 3 不信任画像
    last_updated:         timestamp
```

**健康禁忌绝对不进画像** - PRD 3.1 明确规定。

### 7.2 EMA 系数

```
agent_weight:        alpha=0.15  (新信号占 15%,慢慢倾斜)
dimension:           alpha=0.20  (略快)
avg_satisfaction:    alpha=0.30  (快速反映近期感受)
```

新值 = (1-α) × 旧值 + α × 目标值。

### 7.3 反馈信号 → 更新规则

| 用户行为 | 触发更新 |
|---|---|
| 选了 Top-3 中某条 | 该条主导 agent 的 weight 推向 1.3 |
| 删除了某个 POI | 力推它的 agent weight 推向 0.7;POI 加进 disliked |
| 重新规划且改了"少走点路" | distance_sensitivity 上升 |
| 复盘卡评分 1-5 | avg_satisfaction EMA 更新 |
| 选中路线的所有 POI | category 加进 loved_categories,POI 加进 loved_pois |

### 7.4 调权接入点

`node_score` 里:

```python
if profile and not is_cold_start(profile):
    weights = weights.adjust_by_profile(profile["dimension_sensitivity"])
```

距离敏感度 > 0.7 → 距离权重 ×1.2(榜单权重相应下调);
距离敏感度 < 0.3 → 距离权重 ×0.85(榜单权重相应上调)。

调整后整体权重归一化,保证和为 1。

---

## 八、可插拔接口

替换以下任一文件可不动其他代码切换实现:

| 接口 | 当前实现 | 替换方式 |
|---|---|---|
| `providers/commute.py` | MockCommute(haversine + 速度估算) | 填入 AMAP_API_KEY 自动切换到 AmapCommute;实现 `_call_amap` 方法即可 |
| `providers/llm.py` | DeepSeek(OpenAI 兼容) | 改 base_url 和 model 即可换其他兼容厂商 |
| `providers/embedding.py` | MockEmbedding(词袋) | 实现 EmbeddingProvider 接口,可换 sentence-transformers / OpenAI embedding |
| `profile/store.py` | JSON 文件 | 改 `load_profile` / `save_profile` 即可换 Redis / Postgres |

---

## 九、Eval Harness 节奏

**MVP 阶段**:5 个 case 的占位 golden set,保证算法层硬约束 100% 通过即可。

**MVP 后**(建议):

- 扩 golden set 到 30-50 个,覆盖各种边界(暴雨/健康禁忌/超大半径/锚点冲突等)
- 加 LLM-as-judge scorer 评辩论质量(每个 agent 发言是否符合人格)
- 加稳定性 scorer(同输入跑 3 次方差)
- CI: `python evals/runners/run_eval.py --no-llm` 每 PR 跑一遍,带 LLM 的 nightly 跑

---

## 十、已知 trade-off 与 PRD 偏离

| 项 | PRD 期望 | 当前实现 | 备注 |
|---|---|---|---|
| 延迟 | 8s 红线 | 单轮辩论 ~15s,双轮 ~25s | 用流式输出 + 进度条 UI 缓解 |
| 通勤时长 | 高德实时 | 默认 MockCommute(haversine 估算) | AMAP_API_KEY 填了自动切换 |
| 健康禁忌 | 完整覆盖 | 当前仅实现"膝盖不好"规则 | 其他禁忌字段已预留,加规则即可 |
| 餐饮挖洞 | 12-13:30, 18-19:30 | 已实现,不占 POI 配额 | 但不主动推餐厅(本期 scope 外) |
| 心跳推送 | 实时位置触发 | 不在本期 | scope 限定路线生成 |

---

## 十一、给后续维护者的建议

- **不要在算法层调 LLM**: 算法层是确定性的,加 LLM 让它不可重现,Eval 会变难。
- **新增 agent 人格**: 在 `agents/personas.py` 加新对象 + 加到 `DEBATE_AGENTS`,辩论循环会自动包含。但超过 4 个非主持 agent 会让辩论 transcript 过长,token 成本暴涨,建议优先在现有人格里加强表达力。
- **画像字段扩展**: 在 `profile/schema.py` 加字段 + 在 `profile/ema.py` 写对应更新函数。务必给所有字段默认值,旧画像才能向前兼容。
- **改硬约束 vs 改软约束**: 硬约束(可达圈、健康、暴雨)改 `algorithm/`;软偏好(标签倾向、文案风格)改 agent prompt。混了会让 bug 难追。
- **永远先跑 eval 再合代码**: `python evals/runners/run_eval.py --no-llm` 是底线;改 prompt 后跑 LLM 版才放心。
