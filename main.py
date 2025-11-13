import win32con, win32gui
import pyautogui
import time
from pynput import keyboard
from threading import Thread
import eliminate
import recognize

# 全局控制变量
running = False
clicking = False  # 防止重复启动多个线程
should_exit = False
target_coordinates = ((0, 0), (0, 0))


def transform_to_screen_coords(r, c, left, top, cell_size):
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


def auto_click_loop():
    """自动点击循环"""
    global running, clicking, should_exit
    print("💡 点击线程已启动，等待启动信号...")
    while True:
        img, window_location = recognize.screenshot_window("《星际争霸II》")
        if not img or not window_location:
            print("\n没有找到窗口")
            break
        left, top, right, bottom = window_location
        cell_size = (right - left) // 8  # 自动适配任意分辨率
        mat = recognize.convert_image_to_mat(img)
        best_move, best_elim, best_chain, total_moves = eliminate.find_best_move(mat,1)
        if running and best_move:
            (r1, c1), (r2, c2) = best_move
            x1, y1 = transform_to_screen_coords(r1, c1, left, top, cell_size)
            x2, y2 = transform_to_screen_coords(r2, c2, left, top, cell_size)
            print(f'🖱️ 执行点击: ({r1},{c1})->({r2},{c2})  屏幕({x1},{y1})<->({x2},{y2})')
            print(f'预计消除方块: {best_elim}, 连锁: {best_chain}, 可移动方块数量: {total_moves}')
            pyautogui.click(x=x1, y=y1)
            time.sleep(0.05)  # 小延迟，避免太快
            pyautogui.click(x=x2, y=y2)
            # 控制点击频率（每秒约5次）
            time.sleep(0.05)
        else:
            # 暂停状态，减少CPU占用
            time.sleep(0.1)

def single_move():
    """按 F3 只执行一次最优交换"""
    img, window_location = recognize.screenshot_window("《星际争霸II》")
    if not window_location or not img:
        print("\n没有找到窗口")
        return
    left, top, right, bottom = window_location
    cell_size = (right - left) // 8
    mat = recognize.convert_image_to_mat(img)
    best_move, best_elim, best_chain, total_moves = eliminate.find_best_move(mat,1)
    if not best_move:
        print("🚫 棋盘无可用移动")
        return

    (r1, c1), (r2, c2) = best_move
    x1, y1 = transform_to_screen_coords(r1, c1, left, top, cell_size)
    x2, y2 = transform_to_screen_coords(r2, c2, left, top, cell_size)

    print(f'🔧 F3 单次点击: ({r1},{c1})<->({r2},{c2})  屏幕({x1},{y1})<->({x2},{y2})')
    print(f'预计消除方块: {best_elim}, 连锁: {best_chain}, 可移动方块数量: {total_moves}')
    pyautogui.click(x1, y1)
    time.sleep(0.05)
    pyautogui.click(x2, y2)


def on_press(key):
    """键盘监听回调函数"""
    global running, clicking, should_exit

    try:
        if key == keyboard.Key.space:
            if not running:
                running = True
                print("🟢 自动点击已启动 (Space)")
                if not clicking:
                    start_clicking_thread()
        elif getattr(key, "char", None) and key.char.lower() in ("x", "c", "v", "b"):
            if running:
                running = False
                print("🟡 自动点击已暂停 (X/C/V/B)")
                time.sleep(0.3)  # 等待半秒，确保先前鼠标移动完成
                # 2K 母版尺寸 & 硬编码偏移
                BASE_W, BASE_H = 2560, 1440
                BASE_X, BASE_Y = 940, 700  # 2K 下想去的点

                # 取当前客户区宽高（不额外返回值，只内部再抓一次）
                hwnd = win32gui.FindWindow(None, None)
                while hwnd:
                    if "《星际争霸II》" in win32gui.GetWindowText(hwnd):
                        break
                    hwnd = win32gui.GetWindow(hwnd, win32con.GW_HWNDNEXT)
                if hwnd:
                    left, top, right, bottom = win32gui.GetClientRect(hwnd)
                    cw, ch = right - left, bottom - top
                    sx, sy = cw / BASE_W, ch / BASE_H
                    target_x = int(BASE_X * sx)
                    target_y = int(BASE_Y * sy)
                    pyautogui.moveTo(target_x, target_y)

        elif key == keyboard.Key.f2:
            should_exit = True
            print("🟡 自动点击已结束 (F2)")
        elif key == keyboard.Key.f3:  # ← 新增
            single_move()
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
    print("📌 按 Space 开始自动点击")
    print("⏸️ 按 X/C/V/B 暂停自动点击")
    print("❌ 按 F2 退出程序")
    print("🔧 按 F3 执行一次单次移动")
    print("❌ 按 Ctrl+C 退出程序（终端）")

    # 启动键盘监听
    listener = keyboard.Listener(on_press=on_press)
    listener.start()

    # 保持主程序运行
    try:
        while True:
            if should_exit:
                print("\n👋 程序正在退出...")
                listener.stop()  # 停止键盘监听
                break  # 退出主循环
            time.sleep(0.01)
    except KeyboardInterrupt:
        print("\n👋 程序已退出")


if __name__ == "__main__":
    main()
