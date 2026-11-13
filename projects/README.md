# 练习选题与实践方法

> 适用：已有 Python 与基本建模概念的学习者。审校日期：2026-11-13；已静态审校任务表述、指标与代码前置条件，未实现或实跑完整项目。

本页提供可自行选择的练习方向和开发方法，**不包含已经交付或验证的完整项目**。表中的周期与难度只是规划参考，取决于个人基础、数据和硬件。LLM 学习可先从 [RAG 流程片段](../llm/rag-from-scratch.md) 与 [评估指标](../llm/rag-evaluation.md) 开始。

---

## 🎯 为什么做项目？

学了很多理论，不知道怎么用？

**项目能帮你：**
- ✅ 巩固知识（用过才忘不掉）
- ✅ 建立作品集（求职加分）
- ✅ 发现问题（理论学习看不到）
- ✅ 积累经验（踩坑是最好的老师）

---

## 📋 练习方向

### 新人友好（1-2 周）

| 项目 | 技术栈 | 难度 |
|------|--------|------|
| **房价预测** | 线性回归 + Pandas | ⭐ |
| **手写数字识别** | CNN + PyTorch | ⭐⭐ |
| **情感分析** | BERT + HuggingFace | ⭐⭐ |

### 进阶项目（2-4 周）

| 项目 | 技术栈 | 难度 |
|------|--------|------|
| **推荐系统** | 协同过滤 + 深度学习 | ⭐⭐ |
| **图像分类器** | ResNet + 迁移学习 | ⭐⭐ |
| **问答机器人** | RAG + LangChain | ⭐⭐⭐ |

### 高级项目（1-2 月）

| 项目 | 技术栈 | 难度 |
|------|--------|------|
| **多模态 Agent** | LLaVA + LangChain | ⭐⭐⭐ |
| **定制 LLM** | LoRA 微调 | ⭐⭐⭐ |
| **实时分析系统** | MLOps + 部署 | ⭐⭐⭐ |

---

## 🚀 项目开发流程

### 1. 确定目标

```
问题 → 目标 → 指标
```

例子：
- 问题：预测房价
- 目标：在固定测试集上，使 MAE 低于训练集房价中位数预测基线；具体目标按业务误差容忍度确定
- 指标：MAE、RMSE、R²，并注明房价单位；回归任务不能直接使用未定义的“准确率 > 80%”

### 2. 收集数据

- 公开数据集（Kaggle、UCI，先核查许可与字段含义）。
- 经过授权的自有或公开数据采集。
- 自己标注。
- 合成数据（单独标记来源，并用真实数据验证泛化）。

### 3. 数据探索

以下为流程片段，不能独立运行：`df` 需先加载为清洗前的数据表，省略号需替换成具体列名。后续 `X`、`y` 也需按任务定义；这些步骤未在本仓库以完整数据集实跑。

```python
import pandas as pd
import matplotlib.pyplot as plt

# 查看数据
df.head()
df.info()
df.describe()

# 可视化
df.hist()
df.plot.scatter(...)
```

### 4. 特征工程

```python
# 特征选择
# 特征转换
# 特征缩放
# 处理缺失值
```

### 5. 模型训练

```python
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = LinearRegression()
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
```

这只是独立同分布数据的随机划分示意。时间序列或同一实体的多条记录应按时间或实体分组切分；预处理只能在训练集上拟合，防止测试信息泄漏。

### 6. 评估优化

```python
from sklearn.metrics import mean_squared_error, r2_score

mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MSE: {mse}, R²: {r2}")
```

### 7. 部署上线

```python
# FastAPI
# Streamlit
# Docker
# 云服务
```

---

## 💡 项目技巧

### 1. 从小开始

- ❌ 不要一开始就想做大项目
- ✅ 先跑通简单版本，再逐步复杂化

### 2. 记录过程

```
项目笔记结构：
## [项目名]
### 目标
### 数据
### 模型
### 结果
### 踩坑
### 改进方向
```

### 3. 寻求反馈

- 在 GitHub 上开源
- 写博客分享
- 参加竞赛或 hackathon

---

## 📚 学习资源

### 数据集

- [Kaggle Datasets](https://www.kaggle.com/datasets)
- [UCI Machine Learning Repository](https://archive.ics.uci.edu/ml/)
- [Google Dataset Search](https://datasetsearch.research.google.com/)

### 工具

- [Jupyter](https://jupyter.org/)
- [Google Colab](https://colab.research.google.com/)
- [Hugging Face Spaces](https://huggingface.co/spaces)

### 灵感

- [Awesome Machine Learning](https://github.com/josephmisiti/awesome-machine-learning)
- [Papers with Code](https://paperswithcode.com/)

---

## 🎯 行动清单

选择一个项目，开始动手！

- [ ] 确定项目目标
- [ ] 收集数据
- [ ] 探索数据
- [ ] 训练模型
- [ ] 评估结果
- [ ] 部署上线
- [ ] 写文档分享

---

**祝你项目成功！** 🚀
