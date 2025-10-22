import numpy as np
from collections import deque


def find_best_move(matrix):
    """
    找出单次移动能达到最多消除的移动方案
    """
    rows, cols = len(matrix), len(matrix[0])
    best_move = None
    max_eliminated = 0

    # 尝试所有可能的相邻交换（水平和垂直）
    for i in range(rows):
        for j in range(cols):
            # 尝试向右交换
            if j < cols - 1:
                eliminated = simulate_swap(matrix, i, j, i, j + 1)
                if eliminated > max_eliminated:
                    max_eliminated = eliminated
                    best_move = ((i, j), (i, j + 1))

            # 尝试向下交换
            if i < rows - 1:
                eliminated = simulate_swap(matrix, i, j, i + 1, j)
                if eliminated > max_eliminated:
                    max_eliminated = eliminated
                    best_move = ((i, j), (i + 1, j))

    return best_move, max_eliminated


def simulate_swap(matrix, r1, c1, r2, c2):
    """
    模拟交换两个方块并计算消除数量，修复连锁消除问题
    """
    # 创建棋盘副本
    board = [row[:] for row in matrix]

    # 执行交换
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]

    # 计算消除数量
    total_eliminated = 0
    eliminated_this_round = 1

    # 使用固定随机种子确保结果可重现
    np.random.seed(42)

    while eliminated_this_round > 0:
        eliminated_this_round = find_and_eliminate(board)
        total_eliminated += eliminated_this_round

        if eliminated_this_round > 0:
            # 模拟方块下落
            simulate_fall(board)

    return total_eliminated


def find_and_eliminate(board):
    """
    查找并标记要消除的方块，返回消除数量
    """
    rows, cols = len(board), len(board[0])
    to_eliminate = set()

    # 检查水平方向的连续相同方块
    for i in range(rows):
        j = 0
        while j < cols - 2:
            if board[i][j] != 0 and board[i][j] == board[i][j + 1] == board[i][j + 2]:
                # 找到至少3个连续相同
                count = 3
                while j + count < cols and board[i][j] == board[i][j + count]:
                    count += 1

                for k in range(count):
                    to_eliminate.add((i, j + k))

                j += count
            else:
                j += 1

    # 检查垂直方向的连续相同方块
    for j in range(cols):
        i = 0
        while i < rows - 2:
            if board[i][j] != 0 and board[i][j] == board[i + 1][j] == board[i + 2][j]:
                # 找到至少3个连续相同
                count = 3
                while i + count < rows and board[i][j] == board[i + count][j]:
                    count += 1

                for k in range(count):
                    to_eliminate.add((i + k, j))

                i += count
            else:
                i += 1

    # 消除标记的方块
    for i, j in to_eliminate:
        board[i][j] = 0

    return len(to_eliminate)


def simulate_fall(board):
    """
    模拟方块下落过程
    """
    rows, cols = len(board), len(board[0])

    for j in range(cols):
        # 从底部向上处理每一列
        write_ptr = rows - 1

        # 将非零元素移到底部
        for i in range(rows - 1, -1, -1):
            if board[i][j] != 0:
                board[write_ptr][j] = board[i][j]
                if write_ptr != i:
                    board[i][j] = 0
                write_ptr -= 1

        # 顶部空位用随机新方块填充
        for i in range(write_ptr, -1, -1):
            board[i][j] = np.random.randint(1, 5)


def visualize_move(matrix, move):
    """
    可视化显示移动的整个过程
    """
    board = [row[:] for row in matrix]
    (r1, c1), (r2, c2) = move

    print(f"原始棋盘:")
    print_board(board)

    print(f"\n执行移动: 交换位置 ({r1}, {c1}) 和 ({r2}, {c2})")
    print(f"交换 {board[r1][c1]} (位置[{r1},{c1}]) 和 {board[r2][c2]} (位置[{r2},{c2}])")

    # 执行交换
    board[r1][c1], board[r2][c2] = board[r2][c2], board[r1][c1]
    print(f"\n交换后棋盘:")
    print_board(board)

    # 显示消除过程
    total_eliminated = 0
    round_num = 1
    np.random.seed(420)  # 固定随机种子

    while True:
        eliminated_this_round = find_and_eliminate(board)

        if eliminated_this_round == 0:
            break

        print(f"\n第{round_num}轮消除: {eliminated_this_round}个方块")
        print_board(board, f"第{round_num}轮消除后")
        total_eliminated += eliminated_this_round

        # 模拟下落
        simulate_fall(board)
        print_board(board, f"第{round_num}轮下落后")

        round_num += 1

    print(f"\n总消除数量: {total_eliminated}")
    return total_eliminated

def get_color_name(color_id):
    """根据颜色ID获取颜色名称"""
    color_ids = {'anger': 1, 'custom': 2, 'magic': 3, 'hp': 4, 'super': 5}
    for name, id_val in color_ids.items():
        if id_val == color_id:
            return name
    return "unknown"

def print_board(board, title="棋盘"):
    """打印棋盘状态，使用颜色名称"""
    print(f"{title}:")
    print("   " + "   ".join([f"列{i}" for i in range(len(board[0]))]))
    for i, row in enumerate(board):
        color_row = [get_color_name(cell) for cell in row]
        print(f"行{i}: " + "  ".join([f"{color:8}" for color in color_row]))


# 测试您提供的新棋盘
if __name__ == "__main__":
    matrix = [
    [3, 4, 1, 3, 4, 2, 3, 2],
    [1, 1, 2, 4, 4, 3, 4, 4],
    [1, 3, 4, 4, 2, 4, 4, 3],
    [3, 1, 4, 1, 2, 3, 3, 2],
    [2, 2, 3, 2, 1, 4, 1, 4],
    [4, 2, 2, 1, 3, 1, 2, 3],
    [2, 1, 1, 2, 1, 2, 1, 4],
]

    print("=== 分析新棋盘 ===")
    best_move, max_eliminated = find_best_move(matrix)

    if best_move:
        (r1, c1), (r2, c2) = best_move
        print(f"\n最佳移动: 交换位置 ({r1}, {c1}) 和 ({r2}, {c2})")
        print(f"预计消除方块数量: {max_eliminated}")
        print(f"移动描述: 将第{r1+1}行第{c1+1}列的{matrix[r1][c1]}与第{r2+1}行第{c2+1}列的{matrix[r2][c2]}交换")

        # 可视化这个最佳移动
        print("\n=== 详细消除过程 ===")
        actual_eliminated = visualize_move(matrix, best_move)

    else:
        print("\n没有找到有效的消除移动")
