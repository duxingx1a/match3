import recognize
import pyautogui
import time
from pynput import keyboard
from threading import Thread
import eliminate

# 全局控制变量
running = False
clicking = False  # 防止重复启动多个线程
target_coordinates = ((0, 0), (0, 0))


def transform_to_screen_coords(r, c, left=1740, top=134, cell_size=96):
    """
    将逻辑坐标 (r, c) 转换为屏幕上的点击坐标（格子中心）
    
    参数:
        r: 行索引 (0-7)
        c: 列索引 (0-7)
        left: 棋盘左上角 x 坐标
        top: 棋盘左上角 y 坐标
        cell_size: 每个格子的边长，默认 96
    
    返回:
        (x, y): 屏幕上的像素坐标（中心点）
    """
    x = left + c * cell_size + cell_size // 2
    y = top + r * cell_size + cell_size // 2
    return x, y


# --- 新增辅助函数 ---
def mats_equal(mat1, mat2):
    if mat1 is None and mat2 is None:
        return True
    if mat1 is None or mat2 is None:
        return False
    return (mat1 == mat2).all()


def auto_click_loop():
    """自动点击循环"""
    global running, clicking
    print("💡 点击线程已启动，等待启动信号...")
    while True:
        img = recognize.screenshot_window("《星际争霸II》")
        if img:
            mat = recognize.convert_image_to_mat(img)
            # e.print_board(mat)
            best_move, _, _ = eliminate.find_best_move(mat)
            target_coordinates = best_move
            if running and target_coordinates:
                (x1, y1), (x2, y2) = target_coordinates
                print(f'🖱️ 执行点击: ({x1}, {y1}) <-> ({x2}, {y2})')
                x1, y1 = transform_to_screen_coords(x1, y1)
                x2, y2 = transform_to_screen_coords(x2, y2)
                pyautogui.click(x=x1, y=y1)
                time.sleep(0.03)  # 小延迟，避免太快
                pyautogui.click(x=x2, y=y2)
                # 控制点击频率（每秒约5次）
                time.sleep(0.03)
            else:
                # 暂停状态，减少CPU占用
                time.sleep(0.1)
        else:
            print("\n没有找到窗口")
            break


def on_press(key):
    """键盘监听回调函数"""
    global running, clicking

    try:
        if key == keyboard.Key.f1:
            if not running:
                running = True
                print("🟢 自动点击已启动 (F1)")
                if not clicking:
                    start_clicking_thread()
        elif getattr(key, "char", None) and key.char.lower() in ("x", "c", "v", "b"):
            if running:
                running = False
                print("🟡 自动点击已暂停 (X/C/V/B)")
        elif key == keyboard.Key.f2:
            if running:
                running = False
                print("🟡 自动点击已暂停 (F2)")

    except AttributeError:
        pass


def start_clicking_thread():
    """启动点击线程（只启动一次）"""
    global clicking
    if not clicking:
        clicking = True
        thread = Thread(target=auto_click_loop, daemon=True)
        thread.start()


def main():
    print("🎮 自动点击程序已启动")
    print("📌 按 F1 开始自动点击")
    print("⏸️  按 F2 暂停点击")
    print("❌ 按 Ctrl+C 退出程序（终端）")

    # 启动键盘监听
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # 保持主程序运行
    try:
        while True:
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n👋 程序已退出")


if __name__ == "__main__":
    main()
