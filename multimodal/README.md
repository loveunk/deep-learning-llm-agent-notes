# 多模态模型：经典架构与入门示例

> 前置：Python 与 [Transformer](../llm/transformer.md) 基础。审校日期：2026-11-13；已静态审校经典架构与示例边界，未下载模型或执行推理；学习时长和硬件表现不属于实测结果。

本目录用 CLIP、BLIP 和 LLaVA 解释图文对齐、连接器与视觉指令微调。它是经典架构入门，不是当前模型排行榜。部署选型需另查具体版本的官方模型卡、许可、硬件要求与自己的任务评估。

---

## 🎯 学习目标

建议先用 **2 小时** 建立概览，模型下载和实验耗时另计：
1. 什么是多模态模型
2. 主流模型和架构
3. 如何使用多模态模型
4. 经典应用方向与选型时需要核实的条件

---

## 📚 快速模式（30 分钟）

### 什么是多模态？

**多模态 = 处理多种类型的数据**

常见模态：
- 📝 **文本**（Text）
- 🖼️ **图像**（Image）
- 🎬 **视频**（Video）
- 🔊 **音频**（Audio）
- 📊 **数据**（Structured Data）

### 为什么需要多模态？

**人类是多模态的：**
- 看图 + 读文 = 更好理解
- 听声音 + 看表情 = 准确判断情绪
- 触觉 + 视觉 = 更好感知世界

**AI 也应该一样！**

### 应用场景

| 任务 | 输入 | 输出 | 例子 |
|------|------|------|------|
| **图文理解** | 图像 + 文本 | 文本/分类 | "这张图片里有什么？" |
| **图像生成** | 文本 | 图像 | "画一只猫" |
| **视频理解** | 视频 + 文本 | 文本/分类 | "这段视频在讲什么？" |
| **音频理解** | 音频 + 文本 | 文本/分类 | "这首歌的情绪是什么？" |

### 实战：用 CLIP 做图文检索

代码片段未实跑。需 PyTorch、Transformers、Pillow 与本地 `cat.jpg`；首次运行会下载模型。以下计算是在给定候选文本中的相对得分，并不是校准后的现实正确率。

```python
from transformers import CLIPProcessor, CLIPModel
import torch
from PIL import Image

# 加载模型
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# 输入
image = Image.open("cat.jpg")
texts = ["a cat", "a dog", "a car"]

# 处理
inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)

# 推理
outputs = model(**inputs)
logits_per_image = outputs.logits_per_image  # 图像和文本的相似度
probs = logits_per_image.softmax(dim=1).tolist()[0]

# 结果
for text, prob in zip(texts, probs):
    print(f"{text}: {prob:.2%}")
# 输出取决于图片和候选文本；此处不预填未经测量的概率。
```

---

## 📖 深度模式（2 小时）

### 经典多模态模型

#### 1. CLIP (Contrastive Language-Image Pre-training)

**提出：** OpenAI (2021)

**核心思想：** 对比学习，把图像和文本映射到同一空间

```
图像编码器 → 图像向量
文本编码器 → 文本向量

对比损失：同一对的向量应该接近，不同对的向量应该远离
```

**应用：**
- 零样本图像分类
- 图文检索
- 图像生成引导

#### 2. BLIP (Bootstrapping Language-Image Pre-training)

**提出：** Salesforce (2022)

**核心创新：**
- 理解 + 生成 双任务
- CAPTION (生成描述)
- RETRIEVAL (检索)

**应用：**
- 图像描述
- 图文检索
- 视觉问答

#### 3. LLaVA (Large Language-and-Vision Assistant)

**提出：** 2023

**核心思想：** 连接视觉编码器和 LLM

```
图像 → CLIP ViT → 图像向量
文本 → LLM

将图像向量作为 LLM 的输入
```

**应用：**
- 多模态对话
- 图像理解
- 视觉推理

#### 4. GPT-4V

**提出：** OpenAI (2023)

**特点：**
- 强大的多模态能力
- 理解复杂场景
- 可解释输入图片；具体输出能力取决于所用模型与接口

#### 5. 其他重要模型

| 模型 | 公司 | 特点 |
|------|------|------|
| **DALL·E** | OpenAI | 文本生成图像 |
| **Stable Diffusion** | Stability AI | 开源图像生成 |
| **Midjourney** | Midjourney | 艺术风格图像生成 |
| **Flamingo** | DeepMind | 少样本视觉学习 |

---

## 架构对比

### CLIP 架构

```
图像 → Vision Transformer (ViT) → 图像向量
文本 → Text Transformer → 文本向量

对比损失：拉近相关对，推开不相关对
```

### BLIP-2 架构（2023）

```
图像 → 冻结的 ViT → Q-Former → 可训练投影 → 冻结的 LLM
文本 → 冻结的 LLM

训练 Q-Former 及连接投影，冻结图像编码器与 LLM
```

### LLaVA 架构

```
图像 → CLIP ViT → 投影连接器 → LLM 输入嵌入
文本 → LLM Token

拼接后输入 LLM
```

---

## 调用片段：理解多模态输入输出

下面展示独立调用片段，不包含完整项目。需自行准备图片、兼容依赖与硬件；模型/API 的版本可用性和效果未在本仓库实跑验证。图像生成片段额外依赖 `diffusers`、`transformers`、`accelerate` 及支持相应精度的 CUDA 环境。

### 片段 1: 图文问答

```python
from transformers import BlipProcessor, BlipForQuestionAnswering
from PIL import Image

# 加载模型
processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")

# 加载图像
image = Image.open("image.jpg")

# 提问
question = "What is in this image?"

# 处理
inputs = processor(image, question, return_tensors="pt")

# 推理
out = model.generate(**inputs)
answer = processor.decode(out[0], skip_special_tokens=True)

print(answer)
```

### 片段 2: 图像生成

```python
import torch
from diffusers import StableDiffusionPipeline

# 加载模型
pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")

# 生成
prompt = "A cat sitting on a couch, digital art"
image = pipe(prompt).images[0]

# 保存
image.save("cat.png")
```

### 片段 3: 图像描述

```python
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

image = Image.open("image.jpg")

inputs = processor(image, return_tensors="pt")

out = model.generate(**inputs)
caption = processor.decode(out[0], skip_special_tokens=True)

print(caption)
```

---

## 多模态模型的应用

### 1. 内容创作

- 根据文本生成图像
- 图像编辑
- 视频生成

### 2. 搜索和检索

- 以图搜图
- 文本搜图
- 图文混合检索

### 3. 医疗诊断

- 医学影像分析
- 结合病历诊断
- 辅助手术

### 4. 教育

- 图文教学
- 交互式学习
- 视频理解

### 5. 自动驾驶

- 场景理解
- 多传感器融合
- 决策辅助

---

## 多模态的挑战

| 挑战 | 说明 |
|------|------|
| **对齐** | 如何让不同模态对齐到同一语义空间 |
| **数据** | 高质量多模态数据稀缺 |
| **计算** | 处理图像和视频需要大量计算 |
| **评估** | 如何评估多模态理解能力 |
| **偏见** | 可能继承多个模态的偏见 |

---

## 应用方向举例（历史模型）

以下名称用于理解任务类型，不代表 2026 年最新方案，也不是经过本仓库比较后的选型推荐。

### 1. 视频多模态

- 视频理解（Video-LLaVA、InternVideo）
- 视频生成（Sora、Runway）

### 2. 音频多模态

- 语音理解（Whisper）
- 语音合成（TTS）
- 音频分类

### 3. 3D 多模态

- 3D 物体识别
- 3D 生成
- 场景理解

### 4. 传感器融合

- 激光雷达 + 摄像头
- 多模态自动驾驶

---

## 从任务找到经典学习入口

| 任务 | 经典示例（非当前推荐排名） |
|------|----------|
| **图文检索** | CLIP, BLIP |
| **图像理解** | LLaVA, GPT-4V |
| **图像生成** | Stable Diffusion, DALL·E |
| **视频理解** | Video-LLaVA, InternVideo |
| **音频理解** | Whisper |

实际选型时，先固定任务样例，再核查具体 checkpoint/API 版本、支持的输入输出模态、许可、上下文或分辨率限制、硬件/费用，并比较质量、延迟与失败案例。本文不维护完整的最新模型清单。

---

## 💡 学习建议

### 必须理解

- ✅ 对比学习的概念
- ✅ 视觉编码器（ViT）
- ✅ 如何连接视觉和语言模型
- ✅ 零样本学习

### 可以简化

- 💡 具体的数学推导
- 💡 训练细节（预训练 + 微调）

---

## 📝 总结

### 关键要点

- ✅ 多模态 = 处理多种数据类型
- ✅ CLIP 是基础架构
- ✅ LLaVA 连接视觉和 LLM
- ✅ 应用广泛（搜索、生成、理解）

### 下一步

- [ ] 用 CLIP 做图文检索
- [ ] 用 Stable Diffusion 生成图像
- [ ] 尝试 LLaVA 进行图文对话
- [ ] 关注最新的多模态论文

---

## 🔗 相关资源

- [CLIP Paper](https://arxiv.org/abs/2103.00020)
- [BLIP Paper](https://arxiv.org/abs/2201.12086)
- [LLaVA Paper](https://arxiv.org/abs/2304.08485)
- [Hugging Face Multimodal](https://huggingface.co/docs/transformers/multimodal)

---

**继续学习 [LLM](../llm/README.md) 或 [深度学习](../deep-learning/README.md)！** 🚀
