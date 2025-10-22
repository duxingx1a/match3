import numpy as np

import recognize


def find_best_move(matrix: np.ndarray, simulations: int = 3) -> tuple[tuple[tuple[int, int], tuple[int, int]], int, int]:
    """
    找出能引发最长连锁的移动
    评分 = (连锁轮数 * 1000 + 总消除数)  # 权重确保连锁优先
    参数:
        matrix: 棋盘矩阵
        simulations: 每个移动的模拟次数
    返回:
        best_move: 最佳移动位置 ((r1, c1), (r2, c2))
        best_elim: 预计最大消除数量
        best_chain: 预计最大连锁轮数
    
    """
    rows, cols = matrix.shape
    best_move = ((0, 0), (0, 0))
    best_score = -1
    best_elim = 0
    best_chain = 0
    # 遍历所有可能的相邻交换
    for i in range(rows):
        for j in range(cols):
            # 向右交换
            if j < cols - 1:
                max_elim, max_chain = evaluate_move_expectation(matrix, i, j, i, j + 1, simulations)
                score = max_elim + max_chain * 10  # 连锁优先

                if score > best_score and max_chain > 0:
                    best_score = score
                    best_move = ((i, j), (i, j + 1))
                    best_elim = max_elim
                    best_chain = max_chain

            # 向下交换
            if i < rows - 1:
                max_elim, max_chain = evaluate_move_expectation(matrix, i, j, i + 1, j, simulations)
                score = max_elim + max_chain * 10

                if score > best_score and max_chain > 0:
                    best_score = score
                    best_move = ((i, j), (i + 1, j))
                    best_elim = max_elim
                    best_chain = max_chain

    return best_move, best_elim, best_chain


def simulate_swap(matrix: np.ndarray, r1: int, c1: int, r2: int, c2: int, seed: int = 42) -> tuple[int, int]:
    """
    模拟交换并返回 (总消除数, 连锁轮数)
    增加 seed 参数以支持多次模拟
    参数:
        matrix: 棋盘矩阵
        r1, c1: 第一个方块位置
        r2, c2: 第二个方块位置
        seed: 随机种子，默认为 42
    返回:
        (total_eliminated, chain_rounds)
    """
    if seed is not None:
        np.random.seed(seed)

    board = matrix.copy()
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]

    total_eliminated = 0
    chain_rounds = 0

    while True:
        eliminated_this_round = find_and_eliminate(board)
        if eliminated_this_round == 0:
            break
        total_eliminated += eliminated_this_round
        chain_rounds += 1
        simulate_fall(board)

    return total_eliminated, chain_rounds


def evaluate_move_expectation(matrix: np.ndarray, r1: int, c1: int, r2: int, c2: int, simulations: int = 10) -> tuple[int, int]:
    """
    对一次移动进行多次模拟，返回最大连锁轮数和最大总消除
    参数:
        matrix: 棋盘矩阵
        r1, c1: 第一个方块位置
        r2, c2: 第二个方块位置
        simulations: 模拟次数
    返回:
        (max_eliminated, max_chain): 最大消除数量和最大连锁轮
    """

    max_chain = 0
    max_elim = 0
    for i in range(simulations):
        elim, chain = simulate_swap(matrix, r1, c1, r2, c2, seed=i)  # 随机种子
        max_elim = max(max_elim, elim)
        max_chain = max(max_chain, chain)

    return max_elim, max_chain


def find_and_eliminate(board: np.ndarray) -> int:
    """
    查找并消除水平和垂直方向上连续3个或以上的相同方块
    返回本次消除的数量
    """
    rows, cols = board.shape
    to_eliminate = set()

    # 水平方向检测
    for i in range(rows):
        j = 0
        while j < cols:
            if board[i][j] == 0:
                j += 1
                continue
            color = board[i][j]
            count = 1
            while j + count < cols and board[i][j + count] == color:
                count += 1
            if count >= 3:
                for k in range(count):
                    to_eliminate.add((i, j + k))
            j += count if count > 1 else 1

    # 垂直方向检测
    for j in range(cols):
        i = 0
        while i < rows:
            if board[i][j] == 0:
                i += 1
                continue
            color = board[i][j]
            count = 1
            while i + count < rows and board[i + count][j] == color:
                count += 1
            if count >= 3:
                for k in range(count):
                    to_eliminate.add((i + k, j))
            i += count if count > 1 else 1

    # 执行消除
    for r, c in to_eliminate:
        board[r][c] = 0

    return len(to_eliminate)


def simulate_fall(board):
    """
    模拟方块下落，并在顶部生成新的随机方块（1-6）
    """
    rows, cols = len(board), len(board[0])

    for j in range(cols):
        # 收集该列非零元素，从底部排列
        col_vals = []
        for i in range(rows):
            if board[i][j] != 0:
                col_vals.append(board[i][j])

        # 从底部填充
        for i in range(rows - 1, -1, -1):
            if col_vals:
                board[i][j] = col_vals.pop()
            else:
                board[i][j] = np.random.randint(1, 7)  # 新方块 1~6


def print_board(board, title="棋盘"):
    """打印棋盘状态"""
    print(f"{title}:")
    for i, row in enumerate(board):
        print(f"行{i}: " + "  ".join([f"{cell:2}" for cell in row]))


def visualize_move(matrix, move):
    """
    可视化一次移动的真实连锁过程
    """
    board = matrix.copy()
    (r1, c1), (r2, c2) = move

    print(f"原始棋盘:")
    print_board(board)

    print(f"交换前: ({r1},{c1})={matrix[r1][c1]}, ({r2},{c2})={matrix[r2][c2]}")
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
    print(f"交换后: ({r1},{c1})={board[r1][c1]}, ({r2},{c2})={board[r2][c2]}")
    print_board(board)

    total_eliminated = 0
    round_num = 1

    while True:
        eliminated_this_round = find_and_eliminate(board)
        if eliminated_this_round == 0:
            break
        print(f"\n第{round_num}轮消除: {eliminated_this_round}个方块")
        print_board(board, f"第{round_num}轮消除后")

        total_eliminated += eliminated_this_round

        simulate_fall(board)
        print_board(board, f"第{round_num}轮下落后")
        round_num += 1

    chain_count = round_num - 1
    print(f"\n总消除数量: {total_eliminated}, 连锁轮数: {chain_count}")
    return total_eliminated, chain_count


from PIL import Image, ImageDraw, ImageFont


def draw_best_move_on_board_image(img, best_move):
    """
    在 768x768 的棋盘图像上绘制最佳移动
    img: PIL.Image 对象，768x768，表示 8x8 棋盘
    best_move: ((r1, c1), (r2, c2))
    """
    # 创建可绘制对象
    draw = ImageDraw.Draw(img)

    # 字体（避免警告）
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    # 颜色
    MARK_COLOR = (255, 0, 0)  # 红色标记
    ARROW_COLOR = (255, 255, 0)  # 黄色箭头

    cell_w, cell_h = 96, 96  # 768 / 8 = 96

    if best_move:
        (r1, c1), (r2, c2) = best_move

        # --- 1. 计算中心点 ---
        x1 = c1 * cell_w + cell_w // 2
        y1 = r1 * cell_h + cell_h // 2
        x2 = c2 * cell_w + cell_w // 2
        y2 = r2 * cell_h + cell_h // 2

        # --- 2. 画红圈标记 ---
        radius = 20
        draw.ellipse([(x1 - radius, y1 - radius), (x1 + radius, y1 + radius)], outline=MARK_COLOR, width=4, fill=None)
        draw.ellipse([(x2 - radius, y2 - radius), (x2 + radius, y2 + radius)], outline=MARK_COLOR, width=4, fill=None)

        # --- 3. 画双向箭头 ---
        # Pillow 不支持直接画箭头，我们用 line + text 模拟
        draw.line([(x1, y1), (x2, y2)], fill=ARROW_COLOR, width=5)

        # --- 4. 标注文字 ---
        draw.text((x1 - 40, y1 - 40), "Start", fill=MARK_COLOR, font=font, stroke_fill=(255, 255, 255), stroke_width=2)
        draw.text((x2 - 30, y2 - 40), "End", fill=MARK_COLOR, font=font, stroke_fill=(255, 255, 255), stroke_width=2)

    return img


# ========================
# 主程序入口
# ========================
if __name__ == "__main__":
    img = recognize.screenshot_window("《星际争霸II》")
    if img:

        matrix = recognize.convert_image_to_mat(img)
        print(matrix)

    print("=== 分析新棋盘 ===")
    best_move, avg_elim, avg_chain = find_best_move(matrix, simulations=10)

    if best_move:
        (r1, c1), (r2, c2) = best_move
        print(f"\n最佳移动: 交换位置 ({r1}, {c1}) 和 ({r2}, {c2})")
        print(f"预计平均消除数量: {avg_elim:.1f}")
        print(f"预计平均连锁轮数: {avg_chain:.1f}")
        val1 = matrix[r1][c1]
        val2 = matrix[r2][c2]
        print(f"移动描述: 交换第{r1+1}行第{c1+1}列的 {val1} 与 第{r2+1}行第{c2+1}列的 {val2}")

        print("\n=== 详细消除过程（一次实际模拟）===")
        actual_eliminated, actual_chain = visualize_move(matrix, best_move)
        print(f"实际结果: 消除 {actual_eliminated} 个，连锁 {actual_chain} 轮")
    else:
        print("\n没有找到有效的消除移动")
    if img:
        img_with_mark = img.copy()  # 保留原图
        draw_best_move_on_board_image(img_with_mark, best_move)
        img_with_mark.show()  # 显示结果
