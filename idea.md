

## 最终需求

### 你每天只做一件事

* 输入一条 `今天学到的东西`（任意领域、任意长度）。

### 系统全自动做这些

1. **把每日输入结构化**（提炼、抽概念、建立可能的前置/后继、标注证据）
2. **自动构建知识体系**（树状大纲 + 主线链路）
3. **自动找漏洞**（前置缺失、定义不清、缺例子、孤岛、跳跃）
4. **按周/月/季/年分层输出报告**（长度不限，但必须结构化、可追溯）

---

## MVP 方案

### 形态

* 独立网页（FastAPI + SQLite + 极简 HTML）
* 2 个页面足够：

  * `/`：输入框（提交一条）
  * `/review`：选择周/月/季/年 → 生成并展示报告（可反复刷新重生成）

### 生成策略

* **每日入库时做一次“Entry Enrichment”**（让后续周/月/季/年更稳）
* 周/月/季/年报告：取窗口内所有 enrich 结果，让 AI 生成体系 + 漏洞

> 你说输出不限：那我们把“长输出”放在 report 里，同时用 JSON 保持结构，页面只负责渲染结构（树/列表），内容可以很长但不会乱。

---

## 数据结构（极简且可扩展）

### 表 1：daily_entry

* `id` UUID
* `created_at`
* `entry_text` TEXT  （你输入的原文）
* `enrich_json` JSON TEXT（AI 自动结构化结果）
* `enrich_version` TEXT（便于未来升级算法重新生成）
* `user_id` TEXT（先固定 "local"，上云再启用多用户）

### 表 2：review_report

* `id` UUID
* `period_type` TEXT：`week|month|quarter|year`
* `period_key` TEXT：`2026-W06 / 2026-02 / 2026-Q1 / 2026`
* `time_start`, `time_end`
* `report_json` JSON TEXT（体系树/主线/漏洞/指标/引用）
* `generated_at`
* `report_version` TEXT
* `user_id` TEXT

### （可选但建议）表 3：job

为未来上云异步任务铺路，本地也能同步写入：

* `id` UUID
* `job_type` TEXT：`enrich_entry|generate_report`
* `status` TEXT：`queued|running|succeeded|failed`
* `params_json` TEXT
* `result_ref` TEXT
* `error` TEXT
* `created_at`, `updated_at`

---

## 核心：稳定的 JSON 输出规范（你后续 UI 才能“像产品”）

### 1) 每日 enrich_json 结构（Entry Enrichment）

目标：**让所有领域都能落在“概念—命题—关系—证据—疑点”框架里**。

```json
{
  "summary": "一句话总结",
  "entities": [
    {"name": "概念/实体", "type": "concept|person|place|tool|theory|event|other"}
  ],
  "claims": [
    {"text": "结论/方法/规律/观点", "type": "definition|rule|procedure|insight|fact|question"}
  ],
  "relations": [
    {"from": "概念A", "to": "概念B", "type": "depends_on|part_of|causes|contrasts|applies_to|example_of"}
  ],
  "prerequisites": [
    {"concept": "可能需要的前置", "why": "为什么需要"}
  ],
  "examples": [
    {"text": "例子/应用/类比（如果有）", "source": "from_entry"}
  ],
  "open_questions": [
    {"question": "这条里隐含的疑问/不确定点"}
  ],
  "signals": {
    "clarity": 0.0,
    "is_fragment": false,
    "is_actionable": false
  }
}
```

说明：

* `clarity` 让 AI 自评清晰度（漏洞检测会用到）
* `is_fragment` 标记“像碎片笔记”还是“相对完整”
* 领域不限：用 `entities/claims/relations` 统一表达

### 2) 周/月/季/年 report_json 结构（知识体系 + 漏洞）

目标：**树状知识体系 + 一条主线 + 漏洞列表 + 证据可追溯**。

```json
{
  "outline_tree": {
    "title": "本周期知识体系",
    "children": [
      {
        "path": "主题A",
        "coverage": 72,
        "node_summary": "主题A的核心概括",
        "evidence_entry_ids": ["..."],
        "children": [
          {
            "path": "主题A > 子主题A1",
            "coverage": 55,
            "node_summary": "子主题概括",
            "evidence_entry_ids": ["..."],
            "children": [
              {
                "path": "主题A > 子主题A1 > 概念X",
                "coverage": 40,
                "node_summary": "概念X是什么、解决什么问题",
                "evidence_entry_ids": ["..."],
                "children": []
              }
            ]
          }
        ]
      }
    ]
  },
  "mainline": {
    "title": "最强主线",
    "steps": [
      {
        "step_title": "前置：概念/背景",
        "path_ref": "主题A > 子主题A1 > 概念X",
        "evidence_entry_ids": ["..."],
        "notes": "为什么这是前置"
      }
    ],
    "mainline_score": 0.0
  },
  "gaps": [
    {
      "gap_title": "缺少 XXX 的前置定义",
      "gap_type": "missing_prerequisite",
      "severity": 1,
      "where": "主题A > 子主题A1",
      "why": "原因解释",
      "evidence_entry_ids": ["..."],
      "fix_suggestion": "建议补什么",
      "minimal_task": "一个 10-30 分钟可完成的动作"
    }
  ],
  "isolated_items": [
    {"entry_id": "...", "why_isolated": "为什么挂不上体系"}
  ],
  "metrics": {
    "entry_count": 0,
    "topic_count": 0,
    "scatter_score": 0.0,
    "gap_count": 0
  },
  "repair_plan": [
    {
      "priority": 1,
      "task": "下周期要做的事",
      "related_gaps": ["..."],
      "expected_effect": "补上哪个洞"
    }
  ]
}
```

---

## 漏洞判据（让“指出漏洞”更可信）

即使报告由 AI 写，仍要求它按规则判定：

* **missing_prerequisite**：主线/节点出现，但 prerequisites 从未在窗口内被覆盖或解释
* **unclear_definition**：概念出现多次，但 `signals.clarity` 低且缺 definition 类型 claim
* **no_examples**：节点 coverage 不低，但 examples 为空或极少
* **isolated_item**：该条目无法映射到体系树任何节点（或只能挂到“杂项”）
* **big_leap**：主线相邻 steps 的 prerequisites 不连贯，且中间缺过渡解释

---

## 最小可用 Prompt 模板（直接拿去用）

### A) 每日结构化（Entry Enrichment Prompt）

系统消息（要点）：

* 输出必须是 JSON，字段严格按 schema
* 不要发散胡编；不确定就写到 open_questions
* 尽量抽象成“概念/命题/关系”

用户消息：

* `今天学到的东西：{entry_text}`

### B) 周/月/季/年报告生成（Report Prompt）

系统消息（要点）：

* 生成知识体系树（不限长度但层级清晰）
* 必须给出主线（如果主线弱要说明原因，并降低 score）
* 必须列漏洞，漏洞必须关联证据 entry_ids
* 输出必须是 JSON

用户消息：

* `周期：{period_type} {period_key}`
* `本周期条目（按时间）：[{id, created_at, summary, entities, claims, relations, prerequisites, examples, signals}...]`

> 你后期如果加 embedding/聚类，只需要在这里多给一个 “cluster_suggestions” 字段，prompt 不用推倒重来。

---

## 页面展示建议（输出不限也不乱）

* 左侧：可折叠 `outline_tree`
* 右侧上：`mainline.steps`（点击显示关联的 entry 原文）
* 右侧下：`gaps`（按 severity 排序，点开看 why + minimal_task）
* 底部：`repair_plan`

---

## 扩展性保证（未来上云）

* 预留 `user_id`
* `job` 表让生成流程随时切到异步队列
* SQLite → Postgres 不影响 schema 思路
* `enrich_version/report_version` 让你升级算法后可批量重算

---

如果你下一步就是“先做一个样本”，我建议最小落地顺序：

1. `POST /entries`：存 entry_text → 调用 LLM → enrich_json 入库
2. `POST /reports/{period_type}/{period_key}:generate`：拉窗口 entries → 调用 LLM → report_json 入库
3. 两个页面渲染 JSON（先用简单 `<pre>` 展示也能 demo）

你如果告诉我你打算调用的大模型 API 是 **OpenAI 兼容**还是 **自建/其他**（只要说明：是否支持 JSON mode/structured output），我就能把上面 schema 对应的**Pydantic 模型 + FastAPI 路由骨架**一次性给你，直接跑起来。
