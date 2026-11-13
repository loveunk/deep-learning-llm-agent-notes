# BERT 系列

> 经典的双向文本编码器，可作为分类、抽取和检索任务的学习起点。

---

## BERT vs GPT

| 特性 | BERT | GPT |
|------|------|-----|
| 架构 | Encoder-only | Decoder-only |
| 任务 | 理解（分类、抽取） | 生成 |
| 训练 | Masked LM + Next Sentence Prediction | Causal LM |
| 方向 | 双向 | 单向 |

## BERT 家族

| 模型 | 特点 |
|------|------|
| BERT-Base | 12层，110M参数 |
| BERT-Large | 24层，340M参数 |
| RoBERTa | 改进的BERT |
| ALBERT | 参数共享 |
| DeBERTa | 解耦注意力 |

## 经典任务

下面仅演示任务类的初始化。基础 BERT checkpoint 没有针对这些下游任务训练好的分类/抽取头，新初始化的任务头需要用标注数据训练，不能直接视为可用的分类器或问答模型。运行需兼容的 PyTorch、Transformers 及模型下载环境，本仓库未实跑这些片段。

### 文本分类

```python
from transformers import BertForSequenceClassification

model = BertForSequenceClassification.from_pretrained('bert-base-uncased')
```

### 命名实体识别

```python
from transformers import BertForTokenClassification

model = BertForTokenClassification.from_pretrained('bert-base-cased')
```

### 问答系统

```python
from transformers import BertForQuestionAnswering

model = BertForQuestionAnswering.from_pretrained('bert-large-uncased-whole-word-masking')
```

---

**继续学习 [微调方法](fine-tuning.md)！**
