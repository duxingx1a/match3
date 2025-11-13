"""
跨分辨率（1080P/2K/4K）通用棋盘识别
统一颜色字典 + 像素平均距离
"""
import os
import numpy as np
import win32gui, win32ui, win32con
import ctypes
from PIL import Image
import matplotlib.pyplot as plt
from typing import Tuple

# 启用 DPI 感知（Windows 10 及以上）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception as e:
    print("DPI 感知设置失败：", e)

# ------------------- 1. 棋盘区域比例（2K 母版） -------------------
BASE_W, BASE_H = 2560, 1440
BOARD_L, BOARD_T, BOARD_R, BOARD_B = 1740, 134, 2508, 902
REL_L = BOARD_L / BASE_W
REL_T = BOARD_T / BASE_H
REL_R = BOARD_R / BASE_W
REL_B = BOARD_B / BASE_H

# ------------------- 2. 跨分辨率统一颜色字典 -------------------
COLOR_NAMES = ['blue', 'bone', 'green', 'purple', 'red', 'yellow']
COLOR_IDS = {'blue': 1, 'bone': 2, 'green': 3, 'purple': 4, 'red': 5, 'yellow': 6, 'unknown': 7}
THRESHOLD = 3
# 6 个颜色的 R 通道中心值（跨分辨率平均）
#   green,blue,purple,bone,red,yellow
# 4K   [64, 200, 139, 147, 13, 122]
# 2K   [62, 201, 139, 144, 14, 120]
# 1080P[63, 202, 139, 146, 13, 119]
# mean=[63, 201, 139, 146, 13, 120]
#根据以上数据计算得到：
TEMPLATE_R = np.array([201, 146, 63, 139, 13, 120])

# [201, 62, 14, 144, 139, 120]


def screenshot_window(title_keyword: str = "《星际争霸II》", debug=False) -> Tuple[Image.Image | None, Tuple[int, int, int, int] | None]:
    """截取指定标题关键字的窗口截图
    
    参数:
        title_keyword: 窗口标题关键字，默认 "《星际争霸II》"
        debug: 是否打印调试信息，默认 False
        
    返回:
        截图的PIL Image对象，若未找到窗口则返回None
        棋盘坐标(left, top, right, bottom)，若未找到窗口则返回None
    """
    # 找到窗口句柄
    hwnd = win32gui.FindWindow(None, None)
    while hwnd:
        if title_keyword in win32gui.GetWindowText(hwnd):
            break
        hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)

    if not hwnd:
        print("未找到窗口")
        return None, None
    # 获取实际分辨率
    left, top, right, bottom = win32gui.GetClientRect(hwnd)
    cw, ch = right - left, bottom - top
    if cw == 0 or ch == 0:
        print("客户区尺寸为 0")
        return None, None
    # 棋盘坐标
    left = int(REL_L * cw)
    top = int(REL_T * ch)
    right = int(REL_R * cw)
    bottom = int(REL_B * ch)
    width = right - left
    height = bottom - top

    # 创建设备上下文
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()
    # 创建位图
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
    saveDC.SelectObject(saveBitMap)
    # 截图（窗口即使被遮挡也能截）
    saveDC.BitBlt((0, 0), (width, height), mfcDC, (left, top), win32con.SRCCOPY)
    # 转换为PIL图像
    bmpinfo = saveBitMap.GetInfo()
    bmpstr = saveBitMap.GetBitmapBits(True)
    img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)
    # 清理资源
    win32gui.DeleteObject(saveBitMap.GetHandle())
    saveDC.DeleteDC()
    mfcDC.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwndDC)
    if debug:
        print(f"游戏窗口 {cw}×{ch}")
        print(f"棋盘尺寸 {width}×{height}")
        print(f"┌{left:^5},{top:^5}------┐")
        print(f"│{width:>8}×{height:<8}│")
        print(f"└------{right:^5},{bottom:^5}┘")

    return img, (left, top, right, bottom)


def classify_color(color: int) -> str:
    """
    将单通道颜色值归类到最近的标准色。

    参数:
        color (int): 待归类的颜色值（0-255）。

    返回:
        str: 最近的标准色名称；若与所有中心点的距离均大于阈值，则返回 'unknown'。
    """
    # 计算与 6 个中心的绝对差
    diff = np.abs(TEMPLATE_R - color)
    # 找最小差，若 <= 阈值则命中，否则 unknown
    idx = diff.argmin()
    return COLOR_NAMES[idx] if diff[idx] <= THRESHOLD else 'unknown'


# ------------------- 4. 统一颜色识别 -------------------
def convert_image_to_mat(img: Image.Image) -> np.ndarray:
    """
    将棋盘 PIL 图像转换为 8×8 数值矩阵（单通道 R 均值 + 最近邻归类）。
    跨分辨率兼容：block 大小随图像动态计算，只取中心 40 % 区域求平均，
    消除边框/阴影干扰。

    参数:
        img (Image.Image): 棋盘截图，尺寸为 8 的倍数。

    返回:
        np.ndarray: 8×8 int 矩阵，元素为 COLOR_IDS 定义的颜色编号。
    """
    img_np = np.asarray(img)
    h, w = img_np.shape[:2]
    # 0. 单个方块尺寸 & 中心 40 % 区域
    block_h = h // 8
    block_w = w // 8
    margin = int(block_h * 0.3)  # 上下左右对称留 30 %
    y0, y1 = margin, block_h - margin
    x0, x1 = margin, block_w - margin

    # 1. 取 R 通道 BGR取2
    img_r = img_np[:, :, 2]
    view = img_r.reshape(8, block_h, 8, block_w).transpose(0, 2, 1, 3)  # (8,8,block_h,block_w)
    center = view[:, :, y0:y1, x0:x1]  # 中心 40 %
    mean_r = center.mean(axis=(2, 3))  # (8,8)

    # 3. 逐个送进 judge 得到颜色编号
    board = np.zeros((8, 8), dtype=int)
    for i in range(8):
        for j in range(8):
            color_name = classify_color(int(mean_r[i, j]))
            board[i, j] = COLOR_IDS[color_name]
    return board


def reconstruct_board_image(matrix: np.ndarray, block: int) -> Image.Image:
    """
    根据 8×8 数值矩阵重建彩色棋盘，尺寸与截图像素 1:1。

    参数:
        matrix (np.ndarray): 8×8 整数矩阵，元素为 COLOR_IDS 定义的颜色编号（1-6）。
        block (int): 单个方块的像素边长（= 截图高度 // 8），决定输出图像大小。

    返回:
        Image.Image: 8*block × 8*block 的 RGB 拼图，每格按编号填充对应模板色；
                     无法加载模板时回退灰色块。
    """
    color_map = {1: 'blue.png', 2: 'bone.png', 3: 'green.png', 4: 'purple.png', 5: 'red.png', 6: 'yellow.png'}
    board_img = Image.new('RGB', (8 * block, 8 * block))
    fallback = Image.new('RGB', (block, block), (200, 200, 200))

    for i in range(8):
        for j in range(8):
            val = matrix[i, j]
            if val in color_map:
                try:
                    tile = Image.open(os.path.join('template', color_map[val])).convert('RGB')
                    # 统一缩放到当前 block 大小
                    tile = tile.resize((block, block), Image.Resampling.LANCZOS)
                    board_img.paste(tile, (j * block, i * block))
                    continue
                except Exception:
                    pass
            board_img.paste(fallback, (j * block, i * block))
    return board_img


def show_image(img: Image.Image, title: str = "Image", figsize=(8, 8), cmap=None):
    """
    使用 matplotlib 显示 PIL 图像
    参数:
        img: PIL Image 对象
        title: 图像标题
        figsize: 图像显示大小
        cmap: 颜色映射（如灰度图用 'gray'）
    """
    plt.figure(figsize=figsize)
    plt.imshow(img, cmap=cmap)
    plt.title(title, fontsize=14)
    plt.axis('off')
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 若直接运行此文件，则为调试模式，显示识别结果
    img, _ = screenshot_window("《星际争霸II》", True)
    if img:
        mat = convert_image_to_mat(img)
        print("识别出的棋盘矩阵：")
        formatted_matrix = ',\n    '.join('[' + ', '.join(map(str, row)) + ']' for row in mat)
        print("\nmatrix = [")
        print("    " + formatted_matrix + ",")
        print("]")

        h = img.height
        block = h // 8
        reconstructed_img = reconstruct_board_image(mat, block)

        fig, axes = plt.subplots(1, 2, figsize=(16, 8))  # 宽图，适合左右布局
        axes[0].imshow(img)
        axes[0].set_title("original", fontsize=14, fontweight='bold')
        axes[0].axis('off')
        axes[1].imshow(reconstructed_img)
        axes[1].set_title("reconstructed", fontsize=14, fontweight='bold')
        axes[1].axis('off')
        plt.tight_layout()
        plt.subplots_adjust(top=0.9)
        plt.show()
