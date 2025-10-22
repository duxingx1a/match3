from PIL import Image
import os

from recognize import screenshot_window


def crop_and_save(image, output_folder):
    '''将图像按96x96的网格切割，并保存每个小方块的中间70x70部分到指定文件夹
    参数:
        image: PIL Image 对象
        output_folder: 保存截图的文件夹路径
    '''
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    # 图片的大小
    width, height = image.size
    # 每个小方块的大小
    block_size = 96
    # 需要截取的中间部分大小
    crop_size = 50

    for i in range(0, width, block_size):
        for j in range(0, height, block_size):
            left = i + (block_size - crop_size) // 2
            upper = j + (block_size - crop_size) // 2
            right = left + crop_size
            lower = upper + crop_size

            # 截取区域
            cropped_image = image.crop((left, upper, right, lower))
            # 保存截图
            output_path = os.path.join(output_folder, f"crop_{i//block_size}_{j//block_size}.png")
            cropped_image.save(output_path)

if __name__ == "__main__":
    img = screenshot_window("《星际争霸II》")
    output_folder = "output_images"
    crop_and_save(img, output_folder)
