# BLIP 系列

> 前置：[CLIP](clip.md)与 Python 基础。审校日期：2026-11-13；静态核对了家族年份、架构说明与示例结构，未下载权重或运行推理。

> **理解 + 生成双任务的多模态模型**

---

## 概述

**BLIP** (Bootstrapping Language-Image Pre-training) 由 Salesforce 在 2022 年提出。

创新点：**同时训练理解和生成能力**

---

## BLIP vs CLIP

| 特性 | CLIP | BLIP |
|------|------|------|
| 任务 | 对比学习 | 理解 + 生成 |
| 能力 | 图文匹配 | 图文理解 + 描述生成 |
| 架构 | 对比学习 | 多任务学习 |

---

## BLIP 家族

| 模型 | 论文首次提交 | 特点 |
|------|----------|------|
| BLIP | 2022.01 | 首次提出 |
| BLIP-2 | 2023.01 | 冻结 ViT + Q-Former |
| xGen-MM（BLIP-3） | 2024.08 | 开放多模态训练框架，支持交错图文输入 |

日期按论文首次提交时间记录：[BLIP](https://arxiv.org/abs/2201.12086)、[BLIP-2](https://arxiv.org/abs/2301.12597)、[BLIP-3](https://arxiv.org/abs/2408.08872)。本表用于版本沿革，不是当前性能排名。

---

## BLIP-2 核心创新

### Q-Former 架构

```
图像 → 冻结的 ViT → Q-Former → 可训练投影 → 冻结的 LLM
文本 → 冻结的 LLM

优势：
- 冻结图像编码器与 LLM，训练 Q-Former 及连接到 LLM 的投影层
- 利用强大的预训练模型
- 训练成本大幅降低
```

---

## 实战代码

以下片段针对 BLIP，需兼容的 PyTorch、Transformers、Pillow 和本地 `image.jpg`，首次运行会下载模型。尚未在本仓库验证依赖组合或硬件开销；不应把 BLIP 的调用类直接用于 BLIP-2 / BLIP-3。

### 图像描述生成

```python
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

image = Image.open("image.jpg")

# 无条件描述
inputs = processor(image, return_tensors="pt")
out = model.generate(**inputs)
caption = processor.decode(out[0], skip_special_tokens=True)
print(f"Caption: {caption}")

# 条件描述
inputs = processor(image, text="a photo of", return_tensors="pt")
out = model.generate(**inputs)
caption = processor.decode(out[0], skip_special_tokens=True)
print(f"Caption: {caption}")
```

### 视觉问答 (VQA)

```python
from transformers import BlipProcessor, BlipForQuestionAnswering
from PIL import Image

processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")

image = Image.open("image.jpg")
question = "What color is the cat?"

inputs = processor(image, question, return_tensors="pt")
out = model.generate(**inputs)
answer = processor.decode(out[0], skip_special_tokens=True)
print(f"Answer: {answer}")
```

---

## 应用场景

- 📝 图像描述生成
- ❓ 视觉问答
- 🔍 图文检索
- 📊 图像-文本对过滤

---

**继续学习 [LLaVA](llava.md)！**
