# AI 工程阅读与判断

这个板块把外部技术文章接到本仓库的 RAG、Agent 和评估学习路径上。每次精选应帮助读者做出一个工程选择，或设计一个可以验证的实验。

筛选文章时优先回答三个问题：

1. 这篇文章补充了仓库里的哪个主题。
2. 读者读完后能带走什么工程判断。
3. 哪个结论值得验证，基线、指标和可能失败的条件是什么。

## 推荐阅读方式

如果你正在系统学习，建议先读对应的仓库章节，再读外部文章：

| 学习方向 | 仓库章节 | 阅读索引 |
| --- | --- | --- |
| Agent 基础 | [AI Agent](../llm/agent.md) | [Agent](topics/agent.md) |
| 编程智能体 | [AI 编程智能体](../llm/coding-agents.md) | [Coding Agents](topics/coding-agents.md) |
| Harness / Loop | [Harness Engineering](../llm/harness-engineering.md)、[Loop Engineering](../llm/loop-engineering.md) | [LLM 应用工程](topics/llm-engineering.md) |
| RAG | [RAG](../llm/rag.md)、[RAG 评估](../llm/rag-evaluation.md) | [RAG](topics/rag.md) |
| 多模态 | [多模态总览](../multimodal/README.md) | [多模态](topics/multimodal.md) |
| 推理与部署 | [API 与模型选型](../llm/api-and-models.md) | [模型推理与基础设施](topics/infra.md) |

## 已有精选归档

- [2026 年 6 月精选（历史归档）](2026/06.md)

当前已整理的精选停留在 2026 年 6 月，包含更早的基础文章。自动候选收集不等于新增精选；这里不会把历史归档标成近期发布，也不会为维持更新频率编造新摘要。

## 选文标准

优先收录：

- 官方技术博客、论文、工程复盘、开源项目设计文档。
- 能对应到本仓库学习路径的文章，例如 Agent、RAG、评估、MCP、推理部署、多模态。
- 有清晰工程细节的文章，例如架构、失败模式、评估方法、上线经验。
- 观点可验证、可复盘、不是纯营销发布的内容。

暂不收录：

- 单纯模型发布新闻。
- 只比较排行榜、没有方法论的文章。
- 没有一手信息来源的二次转述。
- 无法长期帮助学习者建立判断的热点争议。

## 条目格式

每条文章控制在 150-250 字中文摘要，格式见 [template.md](template.md)。

必须包含：

- 链接、来源、日期。
- 主题和难度。
- 推荐阅读前置章节。
- 推荐理由。
- 摘要。
- 读完应该带走什么。
- 对仓库主线的工程判断或实验价值。
- 作者结果、本仓库复验、尚未验证之间的证据边界。

## 更新节奏

1. GitHub Actions 每周一 01:30 UTC（北京时间 09:30）收集最近 7 天候选；使用 UTC ISO 周作为期号，例如 `Reading candidates 2026-W46`。
2. 每周最多创建一个候选 issue，最多 12 条、每个来源最多 2 条。同周已存在的 issue（包括已关闭的）不会再次创建，也不会覆盖正文或评论。允许零候选。
3. 人工打开原文，按 [模板](template.md) 写出判断和验证建议；有价值才进入月度精选，数量不设下限。自动化只发布链接和元数据，不发布自动生成的文章摘要。
4. 手动触发 workflow 默认只生成预览 artifact；勾选 `publish` 才尝试创建当周 issue。历史读取失败、全部来源抓取失败会使任务失败，避免把缺数据当成没有新内容。

每次运行会保存候选 Markdown、发布判断 JSON 和历史日报审阅计划。部分来源失败会在报告中列出，候选列表不能据此视为完整覆盖。

## 跨期去重与候选状态

去重依次使用月度精选中的 `- 链接：` 字段、[人工状态表](candidate-status.json)、GitHub 全部分页中的历史机器人候选 issue（open / closed）。历史 issue 正文中的 `- Link:` 是旧日报的去重依据；不会根据关闭状态猜测“已经精选”。

URL 仅移除已知追踪参数（`utm_*`、`fbclid` 等）；保留 `id`、`q`、版本等语义查询参数、路径尾斜杠和 hash 路由，避免误合并不同内容。不同域名、重定向、arXiv 新版本仍需人工判断。

状态表由人工随评审 PR 更新，不由抓取程序改写。可使用以下条目结构（示意，不能把示例 URL 写进实际状态表）：

```json
{
  "url": "https://example.org/article?id=42",
  "status": "rejected",
  "reason": "缺少可验证的工程细节",
  "reviewed_at": "YYYY-MM-DD",
  "issue_number": 123
}
```

| 状态 | 含义 | 后续处理 |
| --- | --- | --- |
| `pending` | 已进入人工评审队列 | 在原 issue 中评审，不重新推送 |
| `selected` | 已精选 | 关联月度条目，保留判断依据 |
| `rejected` | 不收录 | 记录原因，后续不自动重复推荐 |
| `deferred` | 暂缓、等待更多证据 | 人工在原 issue 跟进，不自动重发 |

状态表初始为空；已有月度精选自动参与排除，无需重复录入。未经人工检查的历史日报不会被批量标成 `selected` 或 `rejected`。

## 本地预览与历史日报清理

本地生成候选时若不提供 GitHub 历史，只能检查月度归档和状态表，输出明确标记为预览，发布判断始终为 false。完整只读流程如下，需要已登录的 GitHub CLI：

```bash
gh api --paginate --slurp 'repos/loveunk/deep-learning-llm-agent-notes/issues?state=all&per_page=100' > /tmp/reading-history.json
python3 tools/collect_reading_candidates.py --history /tmp/reading-history.json --require-history --output /tmp/reading-candidates.md --metadata-output /tmp/reading-candidates.json --cleanup-plan /tmp/reading-cleanup-plan.json
```

只生成历史日报审阅计划、不抓取 RSS：

```bash
python3 tools/collect_reading_candidates.py --history /tmp/reading-history.json --cleanup-only --cleanup-plan /tmp/reading-cleanup-plan.json
```

计划列出旧日报、重复链接指向的更早 issue、需要保留的独有链接、评论数、正文哈希及更新时间。它不执行关闭、编辑或发评论，也不提供批量关闭命令。任何实际清理前，都应重新读取当前正文和全部评论，保留人工结论及独有候选，再单独决定是否关闭。零评论也不代表正文没有被人工修改；关闭后的历史仍继续参与去重。

## 可信来源

来源列表见 [sources.md](sources.md)。自动收集的 RSS 源配置见 [sources.json](sources.json)。

自动候选收集覆盖官方实验室、Agent/工程博客、论文源、个人博客和中文来源。关键词分数只负责粗筛，不能证明文章质量；新闻、产品宣传与二手来源还需要人工判断其一手证据和可迁移的工程价值。
