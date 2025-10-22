import numpy as np


def find_and_eliminate(board: np.ndarray) -> int:
    """
    查找并消除水平和垂直方向上连续3个或以上的相同方块
    返回本次消除的数量
    """
    rows, cols = len(board), len(board[0])
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

board = np.array([
    [1, 1, 1, 2],
    [0, 1, 0, 2],
    [0, 1, 0, 2],
    [0, 0, 0, 0]
])
print(find_and_eliminate(board))
print(board)
