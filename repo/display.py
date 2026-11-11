"""迷路のターミナル表示と、対話的メニュー（課題PDF第V章）。

1セルを (2*row+1, 2*col+1) に置いた「壁と通路の格子」を作り、
格子の1マスを「背景色つきの半角スペース2個」で塗りつぶして描く。
文字ではなく色ブロックで描くので、MLX を使わなくても
課題PDF p.12 の例のようなタイル状の見た目になる。
"""

from __future__ import annotations

import sys
from typing import Callable, Dict, List

from mazegen import Direction, Maze

# 格子の各マスの種類
_WALL = "#"
_OPEN = " "
_PATTERN = "@"
_ENTRY = "E"
_EXIT = "X"
_PATH = "o"

#: "3. Rotate the wall colours" で巡回させる壁の色（256色パレット番号）。
WALL_COLORS: Dict[str, int] = {
    "light_gray": 252,
    "cyan": 80,
    "green": 71,
    "yellow": 179,
    "blue": 68,
}
_FIXED_COLORS: Dict[str, int] = {
    _OPEN: 233,      # 通路: ほぼ黒
    _PATTERN: 208,   # "42" 模様: 壁の色（巡回）とかぶらない明るいオレンジ
    _ENTRY: 170,     # 入口: マゼンタ
    _EXIT: 160,      # 出口: 赤
    _PATH: 51,       # 最短経路: 明るいシアン
}
_RESET = "\033[0m"


def _block(color: int, width: int) -> str:
    """背景色 ``color`` のブロックを ``width`` マス分（1マス=2文字）返す。"""
    return f"\033[48;5;{color}m" + "  " * width + _RESET


def _build_grid(maze: Maze, show_path: bool) -> List[List[str]]:
    """壁・通路・模様・入口/出口・経路を表す文字の格子を作る。"""
    rows, cols = maze.height * 2 + 1, maze.width * 2 + 1
    grid = [[_WALL] * cols for _ in range(rows)]

    for row in range(maze.height):
        for col in range(maze.width):
            is_pattern = (row, col) in maze.pattern_cells
            grid[2 * row + 1][2 * col + 1] = _PATTERN if is_pattern else _OPEN
            bits = maze.walls[row][col]
            if not bits & Direction.EAST and col + 1 < maze.width:
                grid[2 * row + 1][2 * col + 2] = _OPEN
            if not bits & Direction.SOUTH and row + 1 < maze.height:
                grid[2 * row + 2][2 * col + 1] = _OPEN

    if show_path:
        # セルだけでなく、セル間の通路マスも塗って線がつながって見えるようにする
        row, col = maze.entry
        for step in maze.shortest_path():
            grid[2 * row + 1 + step.step[0]][2 * col + 1 + step.step[1]] = (
                _PATH
            )
            row += step.step[0]
            col += step.step[1]
            grid[2 * row + 1][2 * col + 1] = _PATH

    entry_row, entry_col = maze.entry
    exit_row, exit_col = maze.exit
    grid[2 * entry_row + 1][2 * entry_col + 1] = _ENTRY
    grid[2 * exit_row + 1][2 * exit_col + 1] = _EXIT
    return grid


def render(maze: Maze, show_path: bool, wall_color: str) -> str:
    """迷路を色ブロックの複数行文字列として描画する。

    Args:
        maze: 描画する迷路。
        show_path: True なら entry→exit の最短経路を表示する。
        wall_color: 壁の色の名前（``WALL_COLORS`` のキー）。
    """
    colors = {_WALL: WALL_COLORS[wall_color], **_FIXED_COLORS}
    lines = []
    for grid_row in _build_grid(maze, show_path):
        # 同じ色が続く区間はまとめて1回のエスケープで出す（出力量を減らす）
        parts, start = [], 0
        for i in range(1, len(grid_row) + 1):
            if i == len(grid_row) or grid_row[i] != grid_row[start]:
                parts.append(_block(colors[grid_row[start]], i - start))
                start = i
        lines.append("".join(parts))
    return "\n".join(lines)


MENU_TEXT = (
    "=== A-Maze-ing ===\n"
    "1. Re-generate a new maze\n"
    "2. Show / Hide the shortest path\n"
    "3. Rotate the wall colours\n"
    "4. Quit"
)


def run_interactive(
    initial_maze: Maze,
    regenerate: Callable[[], Maze],
    output_path: str,
    write_output: Callable[[str, Maze], None],
) -> None:
    """ターミナルで対話的にメニューを回す（課題PDF第V章の操作要件）。

    Args:
        initial_maze: 起動直後に表示する迷路。
        regenerate: 新しい迷路を1つ生成して返すコールバック。
        output_path: 再生成のたびに書き直す出力ファイルのパス。
        write_output: 迷路をファイルに書き出すコールバック。
    """
    maze = initial_maze
    show_path = False
    color_names = list(WALL_COLORS)
    color_index = 0
    # 書き込み失敗（実際のエラー）だけ、画面クリアで消えないよう保持する
    error: str = ""

    while True:
        if sys.stdout.isatty():
            # 端末なら毎回画面をクリアし、同じ位置に描き直す
            print("\033[2J\033[H", end="")
        print(render(maze, show_path, color_names[color_index]))
        for warning in maze.warnings:
            print(f"[warning] {warning}")
        if error:
            print(f"[error] {error}")
        print()
        print(MENU_TEXT)
        try:
            choice = input("Choice? (1-4): ").strip()
        except EOFError:
            print()
            break

        if choice == "1":
            maze = regenerate()
            try:
                write_output(output_path, maze)
                error = ""
            except OSError as os_error:
                error = f"could not write {output_path}: {os_error}"
        elif choice == "2":
            show_path = not show_path
        elif choice == "3":
            color_index = (color_index + 1) % len(color_names)
        elif choice == "4":
            break
        # 1-4以外はメニューを出し直すだけ（メッセージ無しで再入力させる）
