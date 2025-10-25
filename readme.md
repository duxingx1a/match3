# 星际争霸II 消除游戏自动化工具

一个基于 Python 的自动化工具,用于《星际争霸II》中的消除类小游戏。该工具通过图像识别技术分析棋盘状态,并自动计算最佳移动策略以实现最长连锁消除。

## 功能特性

- 🎯 **自动识别棋盘**: 使用模板匹配技术识别 8×8 棋盘上的方块
- 🧠 **智能决策**: 模拟所有可能的移动,选择能产生最长连锁的最佳方案
- 🖱️ **自动操作**: 自动执行鼠标点击完成方块交换
- ⌨️ **热键控制**: 支持快捷键启动/暂停/退出
- 📊 **可视化调试**: 提供棋盘重建和最佳移动标注功能

## 项目结构

```
sc2-match3-bot/
├── main.py           # 主程序入口,处理自动点击和键盘监听
├── recognize.py      # 图像识别模块,截图和棋盘识别
├── eliminate.py      # 消除逻辑和最佳移动计算
├── requirements.txt  # 项目依赖
└── template/         # 模板图像文件夹
    ├── blue.png
    ├── bone.png
    ├── green.png
    ├── purple.png
    ├── red.png
    └── yellow.png
```

## 环境要求

- Windows 操作系统
- Python 3.9+
- 《星际争霸II》游戏窗口

## 安装步骤

1. **克隆或下载项目**

2. **安装依赖**
```bash
pip install -r requirements.txt
```

依赖包含:
- `numpy==2.3.4` - 数组计算
- `opencv_python==4.9.0.80` - 图像处理
- `Pillow==12.0.0` - 图像操作
- `PyAutoGUI==0.9.54` - 鼠标控制
- `pynput==1.7.7` - 键盘监听
- `pywin32==305.1` - Windows API 调用

3. **准备模板图像**

在 `template/` 文件夹中放置 6 种方块的模板图像:
- `blue.png` - 蓝色方块
- `bone.png` - 骨头方块
- `green.png` - 绿色方块
- `purple.png` - 紫色方块
- `red.png` - 红色方块
- `yellow.png` - 黄色方块

## 使用方法

### 1. 启动程序

```bash
python main.py
```

### 2. 调整游戏窗口

- 确保《星际争霸II》游戏窗口标题包含 "《星际争霸II》"
- 棋盘区域默认坐标: `(1740, 134)` 到 `(2508, 902)`
- 如需调整,修改 [recognize.py](recognize.py) 中的坐标参数

### 3. 使用热键控制

| 热键 | 功能 |
|------|------|
| `Space` | 开始自动点击 |
| `X / C / V / B` | 暂停自动点击(用于释放技能) |
| `F2` | 退出程序 |
| `Ctrl+C` | 强制退出(终端) |

### 4. 调试模式

运行 [eliminate.py](eliminate.py) 可进行单次分析和可视化:

```bash
python eliminate.py
```

这将显示:
- 识别出的棋盘矩阵
- 最佳移动建议
- 预计消除数量和连锁轮数
- 带标记的棋盘图像

## 核心算法

### 棋盘识别 ([`recognize.convert_image_to_mat`](recognize.py))

1. 截取游戏窗口的棋盘区域
2. 将每个格子分割为 96×96 像素
3. 提取中心 50×50 区域进行模板匹配
4. 使用归一化相关系数法找到最佳匹配

### 最佳移动计算 ([`eliminate.find_best_move`](eliminate.py))

1. 遍历所有可能的相邻交换(112 种组合)
2. 对每个移动进行 3 次模拟(因随机掉落)
3. 评分公式: `评分 = 连锁轮数 × 10 + 总消除数`
4. 返回评分最高的移动

### 消除模拟 ([`eliminate.simulate_swap`](eliminate.py))

1. 交换两个方块
2. 检测并消除水平/垂直 3 连
3. 模拟方块下落和随机生成
4. 重复直到无可消除方块
5. 记录总消除数和连锁轮数

## 配置参数

### 棋盘坐标 ([recognize.py](recognize.py))

```python
left = 1740    # 棋盘左上角 X 坐标
top = 134      # 棋盘左上角 Y 坐标
right = 2508   # 棋盘右下角 X 坐标
bottom = 902   # 棋盘右下角 Y 坐标
```

### 点击延迟 ([main.py](main.py))

```python
time.sleep(0.03)  # 两次点击之间的延迟(秒)
```

### 模拟次数 ([eliminate.py](eliminate.py))

```python
simulations = 3  # 每个移动的模拟次数
```

## 工具函数

### 图像裁剪 ([utils.py](utils.py))

用于生成模板图像:

```bash
python utils.py
```

将游戏截图按 96×96 网格裁剪,提取中心 50×50 区域保存到 `output_images/` 文件夹。

## 性能优化建议

1. **减少模拟次数**: 降低 `simulations` 参数可提升速度,但可能影响准确性
2. **调整点击延迟**: 根据游戏响应速度调整 `time.sleep()` 值
3. **优化模板匹配**: 使用更精确的模板图像可提高识别准确率

## 注意事项

⚠️ **重要提示**:
- 本工具仅用于学习和研究目的
- 使用自动化工具可能违反游戏服务条款
- 请谨慎使用,风险自负

## 故障排除

### 问题: 无法找到窗口

- 确认游戏窗口标题包含 "《星际争霸II》"
- 检查窗口是否最小化或被遮挡

### 问题: 识别不准确

- 更新 `template/` 文件夹中的模板图像
- 调整 [`recognize.convert_image_to_mat`](recognize.py) 中的匹配阈值 (默认 0.5)
- 运行 [utils.py](utils.py) 查看实际方块图像

### 问题: 点击位置偏移

- 检查 DPI 缩放设置
- 调整 [recognize.py](recognize.py) 中的坐标参数
- 确认 `cell_size=96` 是否与实际一致
