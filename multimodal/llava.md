# LLaVA (Large Language-and-Vision Assistant)

> 前置：[Transformer](../llm/transformer.md)与[CLIP](clip.md)。审校日期：2026-11-13；已对照官方资料核对经典版本与示例结构，未执行模型推理或性能测试。

> **连接视觉和语言模型，实现多模态对话**

---

## 概述

**LLaVA** 于 2023 年提出，是一个连接视觉编码器和 LLM 的多模态模型。

核心思想：**将图像向量作为 LLM 的输入，实现图文对话**

---

## 架构

```
图像 → CLIP ViT → 投影连接器 → LLM 输入嵌入
文本 → LLM Token

拼接后输入 LLM
```

### 关键组件

1. **视觉编码器**：CLIP ViT
2. **投影连接器**：原始 LLaVA 使用线性映射，LLaVA-1.5 使用两层 MLP；不要把不同版本的连接器混成一个固定结构。
3. **语言模型**：Vicuna / LLaMA

---

## 训练方法

### 两阶段训练

1. **预训练**
   - 冻结视觉编码器和 LLM
   - 只训练投影层
   - 使用图像-文本对

2. **微调**
   - 训练投影连接器和 LLM；原始全量微调配方更新 LLM 参数，LoRA 等变体需另行注明
   - 使用多模态对话数据
   - 端到端优化

---

## 实战代码

以下是 LLaVA-1.5 的调用示例，未在本仓库实跑。需安装兼容的 PyTorch、Transformers、Pillow，并自行准备有使用权限的 `image.jpg`。首次运行会下载 7B 模型，默认 CPU 加载需要充足内存；迁移到 GPU 时需统一模型与输入设备、精度并测量显存。这里没有给出已验证的最低硬件或依赖版本。

提示格式针对 `llava-hf/llava-1.5-7b-hf`；其他 checkpoint 应使用其模型卡或 processor 的 chat template，不能直接套用。接口细节参见 [Transformers LLaVA 文档](https://huggingface.co/docs/transformers/model_doc/llava)。

### 多模态对话

```python
import torch
from PIL import Image
from transformers import AutoProcessor, LlavaForConditionalGeneration

model = LlavaForConditionalGeneration.from_pretrained("llava-hf/llava-1.5-7b-hf")
processor = AutoProcessor.from_pretrained("llava-hf/llava-1.5-7b-hf")
model.eval()

prompt = "USER: <image>\nWhat's in this image?\nASSISTANT:"
image = Image.open("image.jpg").convert("RGB")

inputs = processor(text=prompt, images=image, return_tensors="pt")

with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=100)
response = processor.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(response)
```

### 复杂推理

此片段沿用上一段的模型、processor 和图片；生成的“故事情节”属于推测，应与图中可见事实分开解释。

```python
prompt = """USER: <image>
请详细描述这张图片中的：
1. 主要物体
2. 场景背景
3. 颜色和风格
4. 可能的故事情节

ASSISTANT:"""

inputs = processor(text=prompt, images=image, return_tensors="pt")
with torch.inference_mode():
    output = model.generate(**inputs, max_new_tokens=200)
response = processor.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(response)
```

---

## LLaVA 家族

以下为经典版本沿革，参数量为语言基座的常用标称规模，不是当前排名或完整型号清单。

| 版本 | 发布阶段 | 代表语言基座规模 | 主要变化 |
| --- | --- | --- | --- |
| LLaVA-1.5 | 2023-10 | Vicuna 7B / 13B | 两层 MLP 连接器与改进训练配方 |
| LLaVA-NeXT（最初也称 LLaVA-1.6） | 2024-01 | Vicuna 7B / 13B、Mistral 7B、Yi 34B | 动态高分辨率、改进 OCR 与视觉指令数据 |
| LLaVA-NeXT Stronger | 2024-05 | Llama-3 8B、Qwen-1.5 72B / 110B | 扩展语言基座；能力需按具体 checkpoint 与任务评估 |

来源：[官方 Model Zoo](https://github.com/haotian-liu/LLaVA/blob/main/docs/MODEL_ZOO.md)、[2024-01 发布说明](https://llava-vl.github.io/blog/2024-01-30-llava-next/)、[2024-05 发布说明](https://llava-vl.github.io/blog/2024-05-10-llava-next-stronger-llms/)。这些是作者报告的模型与配方，不是本仓库复现结果。

---

## 应用场景

- 💬 多模态对话
- 🔍 图像理解
- 🎨 视觉推理
- 📊 OCR + 语义理解
- 📐 数学图像理解

---

## 优势

- ✅ 强大的对话能力
- ✅ 灵活的多模态理解
- ✅ 可以处理复杂指令
- ✅ 开源且可部署

---

## 限制

- ❌ 计算成本高（需要大模型）
- ❌ 长文本推理仍有挑战
- ❌ 视觉细节理解有限

---

## 相关资源

- [LLaVA GitHub](https://github.com/haotian-liu/LLaVA)
- [LLaVA Paper](https://arxiv.org/abs/2304.08485)
- [Hugging Face Models](https://huggingface.co/models?search=llava)

---

读完后可尝试解释视觉编码器、连接器和语言模型的职责，并用同一图片记录正确回答与幻觉案例。理解架构不等于已验证模型在实际任务上的可靠性。
