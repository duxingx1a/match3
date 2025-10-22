import win32gui
import win32ui
import win32con
from PIL import Image
import ctypes
import cv2
import os
import numpy as np
from typing import Optional
import matplotlib.pyplot as plt
# 启用 DPI 感知（Windows 10 及以上）
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception as e:
    print("DPI 感知设置失败：", e)


def screenshot_window(title_keyword: str) -> Optional[Image.Image]:
    """截取指定标题关键字的窗口截图
    
    参数:
        title_keyword: 窗口标题关键字
    返回:
        截图的PIL Image对象，若未找到窗口则返回None
    """
    # 找到窗口句柄
    hwnd = win32gui.FindWindow(None, None)
    while hwnd:
        if title_keyword in win32gui.GetWindowText(hwnd):
            break
        hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)

    if not hwnd:
        print("未找到窗口")
        return None
    #棋盘坐标
    left = 1740
    top = 134
    right = 2508
    bottom = 902
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

    return img


def preprocess_image(image_array: np.ndarray) -> np.ndarray:
    """对图像进行预处理，转换为灰度并应用高斯模糊，便于匹配模板
    
    参数:
        image_array: 输入的图像数组
    返回:
        预处理后的图像数组
    """
    gray = cv2.cvtColor(image_array, cv2.COLOR_BGR2GRAY) if len(image_array.shape) > 2 and image_array.shape[2] == 3 else image_array
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return blurred


def convert_image_to_mat(image: Image.Image) -> np.ndarray:
    """将PIL图像转换为棋盘矩阵表示
    
    参数:
        image: PIL Image 对象
    返回:
        8x8的numpy数组，表示棋盘状态
    """

    # 将PIL图像转换为OpenCV图像格式
    open_cv_image = np.array(image)
    open_cv_image = open_cv_image[:, :, ::-1].copy()  # 将RGB转换为BGR

    # 转换为灰度图像
    gray = cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2GRAY)

    # 定义模板（这里需要你提前准备好每个方块的模板图像）
    templates = {
        'blue': cv2.imread('template/blue.png', 0),
        'bone': cv2.imread('template/bone.png', 0),
        'green': cv2.imread('template/green.png', 0),
        'purple': cv2.imread('template/purple.png', 0),
        'red': cv2.imread('template/red.png', 0),
        'yellow': cv2.imread('template/yellow.png', 0)
    }

    # 为每种颜色分配一个唯一的整数标识符
    color_ids = {'blue': 1, 'bone': 2, 'green': 3, 'purple': 4, 'red': 5, 'yellow': 6}

    # 每个小方块的大小
    block_size = 96
    # 需要截取的中间部分大小
    crop_size = 50
    board = np.zeros((8, 8), dtype=int)
    # 遍历棋盘每个位置
    for i in range(8):
        for j in range(8):
            # 计算方块区域
            x = j * block_size + (block_size - crop_size) // 2
            y = i * block_size + (block_size - crop_size) // 2

            # 截取50x50的中间区域
            tile = gray[y:y + crop_size, x:x + crop_size]
            # 预处理
            tile = preprocess_image(tile)
            # 模板匹配
            best_match = ''
            best_match_value = 0.0
            for color, template in templates.items():
                # 调整模板大小为50x50
                template = preprocess_image(template)
                template = cv2.resize(template, (crop_size, crop_size))

                # 进行模板匹配
                result = cv2.matchTemplate(tile, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                # 保存最佳匹配结果
                if max_val > best_match_value:
                    best_match_value = max_val
                    best_match = color
            # 如果最佳匹配值大于阈值，则记录匹配结果,7代表未识别到
            board[i, j] = color_ids[best_match] if best_match_value > 0.5 else 7
    return board


def reconstruct_board_image(matrix: np.ndarray) -> Image.Image:
    """
    根据8x8的棋盘矩阵，使用模板图像重建完整棋盘图
    参数:
        matrix: 8x8 numpy数组，值对应颜色编号
                1: blue,  2: bone,  3: green,
                4: purple,5: red,   6: yellow,
                7: empty (可用 empty.png 或灰色块)
    返回:
        PIL Image 对象，大小为 768x768
    """
    # 颜色ID到文件名的映射
    color_map = {
        1: 'blue.png',
        2: 'bone.png',
        3: 'green.png',
        4: 'purple.png',
        5: 'red.png',
        6: 'yellow.png',
    }

    fallback_color = (200, 200, 200)  # 灰色
    fallback_image = Image.new('RGB', (96, 96), fallback_color)

    # 创建空白大图（768x768）
    board_image = Image.new('RGB', (768, 768))
    template_dir = 'template'
    for i in range(8):  # 行
        for j in range(8):  # 列
            value = matrix[i, j]
            col = j
            row = i

            # 获取对应模板路径
            if value in color_map:
                template_path = os.path.join(template_dir, color_map[value])
            else:
                # 未知值（如7）使用 fallback
                board_image.paste(fallback_image, (col * 96, row * 96))
                continue

            # 加载模板图像
            try:
                tile_img = Image.open(template_path).convert('RGB')
                # 统一调整为 96x96
                tile_img = tile_img.resize((96, 96), Image.Resampling.LANCZOS)
                board_image.paste(tile_img, (col * 96, row * 96))
            except Exception as e:
                print(f"加载模板失败 {template_path}: {e}")
                board_image.paste(fallback_image, (col * 96, row * 96))

    return board_image

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
    img = screenshot_window("《星际争霸II》")
    if img:
        mat = convert_image_to_mat(img)
        # print("识别出的棋盘矩阵：")
        # formatted_matrix = ',\n    '.join('[' + ', '.join(map(str, row)) + ']' for row in mat)
        # print("\nmatrix = [")
        # print("    " + formatted_matrix + ",")
        # print("]")

        # 重建棋盘图像
        reconstructed_img = reconstruct_board_image(mat)
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))  # 宽图，适合左右布局
        axes[0].imshow(img)
        axes[0].set_title("original", fontsize=14, fontweight='bold')
        axes[0].axis('off')

        axes[1].imshow(reconstructed_img)
        axes[1].set_title("reconstructed", fontsize=14, fontweight='bold')
        axes[1].axis('off')

        plt.tight_layout()
        plt.subplots_adjust(top=0.9)  # 调整上方间距，避免重叠
        plt.show()
