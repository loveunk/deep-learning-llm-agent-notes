# RAG 评估

> 前置：[RAG 基本流程](rag.md)与 Python 基础。审校日期：2026-11-13；已静态核对指标口径并通过文中检索纯函数测试，未进行 embedding、生成模型或性能基准实测。

RAG 系统不能只靠“看起来回答得不错”来判断。评估要拆成两部分：检索是否找到正确资料，生成是否忠实使用资料。

## 为什么要单独评估 RAG

一个 RAG 答错，可能有四种原因：

1. 文档库没有答案。
2. 有答案，但检索没找到。
3. 检索找到了，但排序太靠后。
4. 上下文里有答案，但模型生成错了。

如果不拆开评估，你不知道该改 chunk、embedding、rerank、prompt，还是换模型。

## 最小评估集

先做 20-50 条人工标注样例。

```json
{
  "id": "q-001",
  "question": "过拟合的常见缓解方法有哪些？",
  "expected_answer": "正则化、增加数据、早停、降低模型复杂度等。",
  "relevant_doc_ids": ["overfitting-001", "regularization-002"],
  "must_have": ["正则化", "增加数据", "早停"],
  "must_not_have": ["训练更久一定能解决"]
}
```

字段解释：

- `question`：真实用户问题。
- `expected_answer`：参考答案，不要求逐字一致。
- `relevant_doc_ids`：能支持答案的文档 ID；本例统一按文档粒度标注。
- `must_have`：必须出现的关键点。
- `must_not_have`：不能出现的错误说法。

## 检索评估

### Recall@k

前 k 个结果覆盖了多少相关文档。对每个有相关文档的问题单独计算，再对问题取平均（宏平均）。

```text
Recall@k(q) = 前 k 个结果中不同的相关 doc_id 数 / 该问题全部相关 doc_id 数
宏平均 Recall@k = mean(Recall@k(q))
```

适合判断：chunking、embedding、query rewrite 是否有效。

### Hit Rate@k

至少命中一个相关文档的问题比例，也叫 Success@k。每个问题恰好有一个相关文档时，它与 Recall@k 的定义一致；有多个相关文档时，两者一般不等价。

```text
Hit Rate@k = 至少命中一个相关 doc_id 的问题数 / 有相关文档的问题数
```

例如某问题有两个相关文档，只找回一个：Recall@k 是 0.5，Hit Rate@k 是 1。

### MRR@k

第一个正确结果越靠前，分数越高。这里只检查前 k 个结果，未命中记 0，因此明确称为 MRR@k。

```text
MRR@k = mean(前 k 项首次命中的排名倒数；未命中为 0)
```

适合判断：排序是否合理。

### Precision@k

前 k 个结果中有多少是相关的。

适合判断：上下文是否被无关 chunk 污染。

## 生成评估

### Answer correctness

答案是否覆盖关键点。

可以人工打分：

| 分数 | 含义 |
| --- | --- |
| 0 | 完全错误 |
| 1 | 部分正确但遗漏关键点 |
| 2 | 基本正确 |
| 3 | 完整且清楚 |

### Faithfulness

答案是否被检索上下文支持。

重点检查：

- 是否出现上下文没有的人名、数字、日期。
- 引用是否真的支持对应句子。
- 是否把多个 chunk 的信息错误拼接。

### Citation quality

引用质量比“有没有引用”更重要。

坏引用：

- 引用的 chunk 只包含相关术语，但不支持结论。
- 一个引用支撑不了整段答案。
- 引用编号和答案句子对应不上。

好引用：

- 每个关键结论都有直接依据。
- 引用足够具体。
- 缺资料时明确说资料不足。

## 端到端指标

| 指标 | 说明 |
| --- | --- |
| 答案通过率 | 人工或 LLM-as-judge 认为可接受的比例 |
| 幻觉率 | 答案中无依据事实的比例 |
| 拒答正确率 | 资料不足时是否拒答 |
| 平均延迟 | 从问题到最终答案 |
| 平均成本 | 单次请求成本，包括检索、rerank、生成 |
| 引用命中率 | 答案引用是否命中标注文档 |

## 评估脚本骨架

以下函数只评估检索，不调用模型。约定：`retrieve_fn` 返回按相关性排序的结果，每项含 `doc_id`；k 限制原始结果槽位。重复 `doc_id` 不增加 Recall 的命中数，但占用原来的排名位置，不自动补取结果。这样同一文档的多个 chunk 不会虚增文档覆盖率。若要评估 chunk 级检索，应统一使用 `chunk_id` 与对应标注，不能混用两种粒度。

空评估集和非正整数 k 会报错；`relevant_doc_ids` 为空的无答案问题单独计为跳过，不进入这三个指标的分母，应另测拒答正确率。若全是无答案问题则报错，避免报告没有意义的检索分数。

```python
def evaluate_retrieval(dataset, retrieve_fn, k=5):
    if isinstance(k, bool) or not isinstance(k, int) or k <= 0:
        raise ValueError("k 必须是正整数")
    dataset = list(dataset)
    if not dataset:
        raise ValueError("评估集不能为空")

    hits = 0
    recalls = []
    reciprocal_ranks = []
    skipped = 0

    for item in dataset:
        relevant = set(item["relevant_doc_ids"])
        if not relevant:
            skipped += 1
            continue

        results = list(retrieve_fn(item["question"], top_k=k))[:k]
        result_ids = [result["doc_id"] for result in results]
        matched = relevant.intersection(result_ids)

        if matched:
            hits += 1
        recalls.append(len(matched) / len(relevant))

        rank = None
        for i, doc_id in enumerate(result_ids, start=1):
            if doc_id in relevant:
                rank = i
                break

        reciprocal_ranks.append(0 if rank is None else 1 / rank)

    evaluated = len(recalls)
    if evaluated == 0:
        raise ValueError("没有含相关文档标注的问题；请单独评估无答案问题")

    return {
        f"hit_rate_at_{k}": hits / evaluated,
        f"recall_at_{k}": sum(recalls) / evaluated,
        f"mrr_at_{k}": sum(reciprocal_ranks) / evaluated,
        "evaluated_queries": evaluated,
        "skipped_queries": skipped,
    }
```

本函数的多相关文档、重复结果、无命中、空集与截断行为由 [纯函数测试](https://github.com/loveunk/deep-learning-llm-agent-notes/blob/master/tests/test_content_examples.py) 覆盖。运行：`python3 -m unittest discover -s tests -p 'test_content_examples.py'`。这些测试不代表 embedding 或生成模型的效果验证。

## 改动实验记录

每次只改一个变量。**下表数字均为教学示意，不是本仓库实测结果，也不是模型或框架的性能承诺。** 实际记录需补上评估集版本、模型与依赖版本、硬件、运行命令、计时口径和原始结果链接。

| 实验 | chunk size | overlap | top-k | rerank | Recall@5 | 通过率 | P95 延迟 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 500 | 50 | 5 | no | 0.72 | 0.61 | 2.1s |
| smaller chunk | 300 | 50 | 5 | no | 0.78 | 0.66 | 2.3s |
| add rerank | 300 | 50 | 20->5 | yes | 0.81 | 0.73 | 3.7s |

没有实验记录，就很难解释系统为什么变好或变差。

## 常见诊断

### 检索没命中

检查：

- 问题是否需要 query rewrite。
- chunk 是否切断答案。
- embedding 模型是否适合中文或领域术语。
- metadata filter 是否过严。
- 是否需要 hybrid search。

### 命中了但答案错

检查：

- top-k 是否太多，导致噪声进入上下文。
- prompt 是否要求仅依据 context。
- 模型是否忽略引用。
- 是否需要 citation check。

### 答案正确但引用错

检查：

- 引用粒度是否太粗。
- chunk metadata 是否缺失。
- 是否需要让模型逐句给引用。

### 资料不足却强答

检查：

- prompt 是否允许“资料不足”。
- 评估集中是否包含无法回答的问题。
- 是否需要加拒答分类器或二次校验。

## LLM-as-judge 的注意事项

LLM 可以辅助评估，但不能完全替代人工。

建议：

- 用明确 rubric。
- 把标准答案和引用上下文都给 judge。
- 对高风险样例人工复核。
- 固定 judge 模型和 prompt，避免评估漂移。

## 下一步

- 如果检索指标差，回到 [Embedding 与向量检索](embeddings.md)。
- 如果生成忠实度差，回到 [Prompt 与上下文工程](prompting.md)。
- 如果需要自动化多步骤修复，学习 [Agent 工作流](agent-workflows.md)。

## 参考资料

- Recall 定义：[Introduction to Information Retrieval](https://nlp.stanford.edu/IR-book/html/htmledition/an-example-information-retrieval-problem-1.html)
- Ragas: https://docs.ragas.io/
- DeepEval: https://docs.confident-ai.com/
- Arize Phoenix: https://docs.arize.com/phoenix
- LangSmith Evaluation: https://docs.smith.langchain.com/evaluation
