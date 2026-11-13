# 贡献指南

本仓库面向有 Python 基础的中文开发者，重点维护 RAG / Agent 的设计、评估与失败排查。欢迎贡献可核查的纠错、教学片段、复现记录和工程判断。

## 从一个小任务开始

| 任务 | 交付与验收 |
| --- | --- |
| 复核一个指标 | 给定义、出处和一个边界案例，例如有多个相关文档时的 Recall@k |
| 验证一个代码片段 | 给依赖版本、命令、输入、输出和验证日期；区分真实 API 与离线替身 |
| 补充失败案例 | 描述现象、定位过程、改变的变量、结果和仍未解决的问题 |
| 补 5 条评估题 | 标注问题、相关资料、预期答案、无答案情况和数据来源 |
| 修复一个失效链接 | 给原位置、替代原始来源，并检查引用含义仍然一致 |
| 精读一篇文章 | 使用 [阅读模板](reading/template.md)，说明它改变了哪项工程判断 |

提交前可先查 [现有 Issue](https://github.com/loveunk/deep-learning-llm-agent-notes/issues)。复现与失败案例使用 [专用模板](https://github.com/loveunk/deep-learning-llm-agent-notes/issues/new?template=reproduction.md)，明确范围后即可贡献，不必建设完整应用。

## 每篇内容的最低标准

1. **问题与适用范围**：谁在什么条件下需要它，何时不适用。
2. **前置知识**：链接必要章节，避免要求读者先学完整套理论。
3. **最小数据流或教学片段**：解释输入、输出及省略的部分。
4. **失败与验证**：给可检查的指标、边界案例或排错步骤。
5. **来源与时效**：重要技术结论链接论文、官方文档或原项目；版本敏感的接口注明核对日期和具体版本。
6. **验证范围**：分别标明静态审校、离线测试、真实模型/API 实跑，不能用其中一种代替另一种。

站点支持可选 front matter：`maintenance_status`（维护/验证范围说明）和 `reviewed_at`（内容复核日期）。只有实际复核后才更新日期。正文也可直接写明范围；不要统一把全部历史页标成“已验证”。

## 代码与数字的证据要求

| 类型 | 必须说明 |
| --- | --- |
| 伪代码/教学片段 | 省略的对象、外部依赖、数据和配置，不能暗示复制即可运行 |
| 离线可运行函数 | 调用方式、预期输出和关键边界；关键指标应有回归测试 |
| 真实模型/API 示例 | 模型/checkpoint、依赖版本、环境、日期、命令、输出、资源/费用范围 |
| 教学示意数字 | 在表格或图旁明确标为“示意，非实测” |
| 作者实测 | 数据、配置、原始结果、运行条件、样本数与局限 |
| 第三方结果 | 原文出处、作者报告的条件；不写成本仓库复现结果 |

不提交 API key、token、私人数据或未经授权的业务材料。第三方材料按 [资料来源说明](SOURCES.md) 标注；引用不能只给一个无法追溯的截图。

## 提交前检查

本地离线检查使用 Python 3.11+：

```bash
python3 tools/check_local_links.py
python3 -m unittest discover -s tests -v
```

站点验证使用 Ruby 3.3+、Bundler 与 Node.js 22+（依赖安装首次需要网络）：

```bash
bundle install
ruby tests/test_inline_math.rb
bundle exec jekyll build --baseurl /deep-learning-llm-agent-notes
python3 tools/check_site.py --site _site --baseurl /deep-learning-llm-agent-notes
node --test tests/test_site_search.cjs
for script in assets/js/*.js; do node --check "$script"; done
```

PR 的文档质量工作流执行这些检查。站点检查覆盖生成 HTML 的站内路径、资源和锚点；外部站点可用性与技术结论仍需人工核查。它不证明所有历史模型示例能够实跑。

## 让成果便于引用与反馈

分享时链接具体章节或固定 commit，交代解决的问题、证据类型、一个失败案例和结论边界。可使用 [发布说明模板](https://github.com/loveunk/deep-learning-llm-agent-notes/blob/master/.github/RELEASE_TEMPLATE.md)。未测量的提升不写成成果，未核实的复现不计入成功案例。

维护者在合并 PR 后保留贡献者记录；有充分证据的复现案例可链接到对应章节。机器人候选 Issue 数量不作为社区活跃度指标。
