from PIL import Image
import os

from matplotlib import pyplot as plt
import numpy as np
from recognize import screenshot_window, show_image
import recognize


def _img_key(img: Image.Image):
    """把 Image 变成可哈希的 bytes"""
    return img.tobytes()


def crop_and_save(image: Image.Image, output_folder: str, crop_ratio: float = 0.4):
    """
    自适应分辨率版
    将棋盘区域按 8×8 网格切割，保存中间 crop_size×crop_size 部分
    参数:
        image: 棋盘区域 PIL Image（尺寸一定是 8 的倍数）
        output_folder: 保存路径
        crop_ratio: 中间要切多大（默认 40%） 因为背景颜色不同 需要取中心确保精准
    """
    seen = set()
    if not 0 < crop_ratio <= 1:
        raise ValueError("crop_ratio 必须在 (0, 1] 之间")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # 图片的大小
    width, height = image.size  # 实际像素
    print(f"棋盘尺寸: {width}×{height}")

    block_w = width // 8  # 单格宽
    block_h = height // 8  # 单格高
    # 百分比 → 像素
    crop_w = int(block_w * crop_ratio)
    crop_h = int(block_h * crop_ratio)
    for row in range(8):
        for col in range(8):
            x0 = col * block_w
            y0 = row * block_h

            # 中心对齐
            left = x0 + (block_w - crop_w) // 2
            upper = y0 + (block_h - crop_h) // 2
            right = left + crop_w
            lower = upper + crop_h

            cropped = image.crop((left, upper, right, lower))
            key = _img_key(cropped)
            if key in seen:  # 已经切过一样的图
                continue
            seen.add(key)
            cropped.save(os.path.join(output_folder, f"crop_{row}_{col}.png"))
    print(f"切割完成，比例 {crop_ratio:.0%}，文件夹: {output_folder}")


def cal(folder: str = "output_images1"):
    # 1. 按文件名排序取前 6 张
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.png')])[:6]

    if len(files) < 6:
        raise RuntimeError(f"目录里 png 不足 6 张，实际只有 {len(files)} 张")

    # 2. 遍历计算
    for idx, fname in enumerate(files, 1):
        img = Image.open(os.path.join(folder, fname)).convert('RGB')
        arr = np.array(img, dtype=np.int32)  # 避免溢出

        # RGB 分别求和 → 平均
        rgb_sum = arr.sum(axis=(0, 1))  # 形状 (3,)
        pixel_cnt = arr.size // 3  # 总像素数
        rgb_avg = rgb_sum / pixel_cnt  # 形状 (3,)

        print(f"图{idx}: {fname}  ->  平均RGB (R={rgb_avg[0]:.1f}, G={rgb_avg[1]:.1f}, B={rgb_avg[2]:.1f})")


def cal_template():
    # 三组 RGB 矩阵  6×3
    rgb_1080 = np.array([[94.2, 155.0, 65.9], [74.3, 162.5, 201.1], [130.0, 54.6, 140.8],
                         [151.6, 151.3, 151.0], [158.9, 40.6, 13.5], [93.6, 177.1, 124.9]])
    rgb_2k = np.array([[93.8, 152.0, 64.6], [74.4, 162.1, 200.2], [129.4, 53.5, 140.1],
                       [149.5, 148.4, 147.6], [159.3, 41.4, 13.9], [93.6, 176.4, 124.2]])
    rgb_4k = np.array([[93.7, 153.8, 65.2], [74.3, 162.5, 201.1], [129.3, 53.7, 140.2],
                       [150.7, 150.1, 149.6], [159.7, 41.0, 13.7], [94.3, 176.7, 123.9]])

    # 跨分辨率统一字典
    uni_rgb = rgb_1080 + rgb_2k + rgb_4k
    uni_rgb = uni_rgb / 3.0  # 6×3  逐元素平均

    COLOR_DB = {
        'blue': tuple(uni_rgb[0]),
        'yellow': tuple(uni_rgb[1]),
        'purple': tuple(uni_rgb[2]),
        'bone': tuple(uni_rgb[3]),
        'red': tuple(uni_rgb[4]),
        'green': tuple(uni_rgb[5]),
    }
    COLOR_IDS = {'blue': 1, 'bone': 2, 'green': 3, 'purple': 4, 'red': 5, 'yellow': 6}
    print("统一字典：", COLOR_DB)


def process(img):
    img_np = np.asarray(img)
    h, w = img_np.shape[:2]

    # 0. 单个方块尺寸 & 中心 40 % 区域
    block_h = h // 8
    block_w = w // 8
    margin_y = int(block_h * 0.3)
    margin_x = int(block_w * 0.3)
    cy0, cy1 = margin_y, block_h - margin_y
    cx0, cx1 = margin_x, block_w - margin_x

    # 1. 分离三通道（保持你原来的 BGR 顺序）
    img_r = img_np[..., 2]
    img_g = img_np[..., 1]
    img_b = img_np[..., 0]

    # 2. 一次性把 8×8 网格切出来，形状 (8,8,c_h,c_w)
    def _mean_center(channel):
        view = channel.reshape(8, block_h, 8, block_w).transpose(0, 2, 1, 3)
        return view[:, :, cy0:cy1, cx0:cx1].mean(axis=(2, 3))

    mean_r = _mean_center(img_r)[0, :6]  # 只要第一行 0~5 号
    mean_g = _mean_center(img_g)[0, :6]
    mean_b = _mean_center(img_b)[0, :6]

    # 3. 按你原来的格式打印
    totalsr = mean_r.astype(int).tolist()
    totalsg = mean_g.astype(int).tolist()
    totalsb = mean_b.astype(int).tolist()

    print(f'在R通道中{totalsr}')
    print(f'在G通道中{totalsg}')
    print(f'在B通道中{totalsb}')

    for i in range(6):
        print(f'第{i + 1}个方块平均RGB值为({totalsr[i]},{totalsg[i]},{totalsb[i]})')
        print(sum([totalsr[i], totalsg[i], totalsb[i]]))


if __name__ == "__main__":
    # cal_template()
    output_folder = "output_images"
    img, _ = screenshot_window("《星际争霸II》", debug=True)
    process(img)

    # cal(output_folder)
    # if img:
    #     recognize.show_image(img)
    # crop_and_save(img, output_folder)
