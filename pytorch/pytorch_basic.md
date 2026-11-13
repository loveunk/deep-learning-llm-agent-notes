# PyTorch 基础阅读入口

本页帮助你按顺序读懂张量、自动微分、模型定义与训练循环，为后续阅读 [Transformer](../llm/transformer.md) 和[微调方法](../llm/fine-tuning.md)打基础。

> 审校日期：2026-11-13。已核实下列官方教程入口，并静态查看历史样例；本次未安装或运行 PyTorch，没有训练结果或硬件兼容性结论。本页是学习导航，不是完整训练项目。

## 前置知识

- 能读写 Python 函数、类与循环。
- 理解数组形状、矩阵乘法与基本广播；可先看 [NumPy](../python/numpy/README.md)。
- 知道损失函数、梯度下降、训练集与测试集分别解决什么问题。
- 先按自己的操作系统和设备配置环境；CPU、CUDA 与其他加速设备的安装条件不同。不要直接照搬旧代码中的 `.cuda()`。

## 学习顺序与目标

### 1. 张量：先看形状、类型与设备

阅读官方 [Tensors](https://docs.pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html)。

- 能解释一个批次的 `shape`，区分逐元素乘法与矩阵乘法。
- 能检查 `dtype`、`device`，说明广播改变了哪些维度。
- 能识别“数据与模型不在同一设备”和“整数标签与浮点输入混淆”等常见问题。

### 2. Autograd：理解梯度从哪里来

阅读官方 [Automatic Differentiation](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html)。

- 理解 `requires_grad`、`backward()` 与参数 `.grad` 的关系。
- 能说明梯度默认会累加，因此通常每一步先清零；有意做梯度累积时另设策略。
- 区分停止梯度记录与切换模型训练/评估模式，两者并不互相替代。

### 3. nn.Module：把运算组织成模型

阅读官方 [Build the Neural Network](https://docs.pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html)。

- 知道层和参数通常在 `__init__` 中定义，输入到输出的计算在 `forward` 中描述。
- 能沿一次前向传播写出各层输入、输出的形状。
- 能说明 `model.parameters()`、`train()`、`eval()` 的用途。

### 4. 训练循环：分开更新与评估

阅读官方 [Optimizing Model Parameters](https://docs.pytorch.org/tutorials/beginner/basics/optimization_tutorial.html)。

先读懂顺序：取一个批次 → 前向计算 → 计算损失 → 清梯度 → 反向传播 → 优化器更新。验证阶段通常切到 `eval()` 并关闭梯度记录，不更新参数。

检查自己能否解释：损失与标签格式是否匹配、梯度是否存在、参数是否更新，以及为什么训练损失下降不能证明泛化变好。

## 仓库中的历史样例

以下文件保留供阅读和排错，**未在当前依赖环境复测**，不承诺直接运行成功，也不把它们的历史输出当作本仓库当前结果。

| 文件 | 可以观察什么 | 阅读时留意 |
| --- | --- | --- |
| [linear_regression.py](samples/linear_regression.py) | 手工参数、反向传播与更新 | 包含 ReLU 和零初始化，需检查梯度路径；不是已验证的线性回归基线 |
| [TwoLayerFCSample.py](samples/TwoLayerFCSample.py) | `nn.Module`、优化器与两层网络 | 使用随机数据并硬编码 `.cuda()`，不能据此判断真实任务效果 |
| [MnistClassification.py](samples/MnistClassification.py) | 数据加载、训练/测试分离 | 需 torchvision、TensorBoard 相关依赖和 MNIST 下载环境 |
| [ResNetFinetune.py](samples/ResNetFinetune.py) | 替换分类头、参数更新范围 | 旧权重接口、阶段命名与最佳权重恢复逻辑需要复核 |

运行历史样例前，先记录 Python、PyTorch、torchvision 与设备版本，确认数据路径和下载行为。遇到报错时先缩小到相关张量或单个批次，不要直接启动长时间训练。

## 学完后的自查

- [ ] 能画出一次前向与反向传播的数据流。
- [ ] 能区分 `eval()`、关闭梯度记录和冻结参数。
- [ ] 能通过形状、梯度和参数变化定位一次训练失败。
- [ ] 能把训练表现、测试表现与未验证的推测分开记录。

继续阅读官方 [Learn the Basics](https://docs.pytorch.org/tutorials/beginner/basics/intro.html)，或回到 [LLM 学习路径](../llm/README.md)。
