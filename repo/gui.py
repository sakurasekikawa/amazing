"""迷路の GUI 表示（MiniLibX / MLX）と、キー操作（課題PDF第V章）。

ターミナル版（``display.py``）と同じ「壁と通路の格子」を使い、1マスを
``tile`` ピクセル四方の正方形として画像バッファに塗って、ウィンドウに貼る。
操作は課題PDFの必須3つ（再生成・最短経路の表示/非表示・壁の色の切り替え）。

MLX は Linux 専用（42 配布の ``mlx-2.2-py3-none-any.whl``）。入っていない
環境では :func:`mlx_available` が False を返すので、呼び出し側が
ターミナル表示に切り替える。
"""

from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, List, Tuple

from display import (WALL_COLORS, _ENTRY, _EXIT, _OPEN, _PATH, _PATTERN,
                     _WALL, _build_grid)
from mazegen import Maze

RGB = Tuple[int, int, int]

#: 壁の色（``display.WALL_COLORS`` と同じキー）の RGB。
WALL_RGB: Dict[str, RGB] = {
    "light_gray": (208, 208, 208),
    "cyan": (95, 215, 215),
    "green": (95, 175, 95),
    "yellow": (215, 175, 95),
    "blue": (95, 135, 215),
}
_FIXED_RGB: Dict[str, RGB] = {
    _OPEN: (18, 18, 18),       # 通路
    _PATTERN: (255, 135, 0),   # "42" 模様
    _ENTRY: (215, 95, 215),    # 入口
    _EXIT: (215, 0, 0),        # 出口
    _PATH: (0, 255, 255),      # 最短経路
}

_MAX_WIDTH, _MAX_HEIGHT = 1000, 700   # 迷路部分の最大ピクセル数
_FOOTER_HEIGHT = 56                   # 操作説明を書く下端の帯
_TEXT_COLOR = 0xFFFFFF
_HELP_LINES = (
    "1/R: re-generate   2/P: show-hide path   3/C: wall colour",
    "4/Q/Esc: quit",
)

# mlx の keycode は X11 keysym（文字キーは ASCII、Esc は 65307）
_KEY_REGEN = (ord("1"), ord("r"))
_KEY_PATH = (ord("2"), ord("p"))
_KEY_COLOR = (ord("3"), ord("c"))
_KEY_QUIT = (ord("4"), ord("q"), 27, 65307)
_EVENT_CLOSE = 33   # ClientMessage: ウィンドウの × ボタン


def mlx_available() -> bool:
    """MLX の Python ラッパー (``mlx``) を import できるか。"""
    try:
        importlib.import_module("mlx")
    except ImportError:
        return False
    return True


def tile_size(maze: Maze) -> int:
    """迷路全体が最大サイズに収まる、1マスのピクセル数（最小 2）を返す。"""
    cols, rows = maze.width * 2 + 1, maze.height * 2 + 1
    return max(2, min(_MAX_WIDTH // cols, _MAX_HEIGHT // rows))


def render_rows(maze: Maze, show_path: bool, wall_color: str,
                tile: int) -> List[List[RGB]]:
    """迷路を「1ピクセル行 = RGB のリスト」の列として描く（純粋関数）。"""
    colors = {_WALL: WALL_RGB[wall_color], **_FIXED_RGB}
    pixel_rows: List[List[RGB]] = []
    for grid_row in _build_grid(maze, show_path):
        line = [colors[kind] for kind in grid_row for _ in range(tile)]
        pixel_rows.extend([line] * tile)
    return pixel_rows


def _pack(color: RGB, image_format: int) -> bytes:
    """RGB を mlx の画像フォーマット（0: B8G8R8A8 / 1: A8R8G8B8）に詰める。

    ここでの B8G8R8A8 はメモリ上のバイト順が B,G,R,A。A8R8G8B8 は A,R,G,B。
    """
    red, green, blue = color
    if image_format == 0:
        return bytes((blue, green, red, 255))
    return bytes((255, red, green, blue))


class MazeWindow:
    """MLX のウィンドウ1枚と、その上の迷路の状態（表示中の迷路・経路・色）。"""

    def __init__(self, maze: Maze, regenerate: Callable[[], Maze],
                 output_path: str,
                 write_output: Callable[[str, Maze], None]) -> None:
        mlx_module: Any = importlib.import_module("mlx")
        self.mlx = mlx_module.Mlx()
        self.maze = maze
        self.regenerate = regenerate
        self.output_path = output_path
        self.write_output = write_output
        self.show_path = False
        self.color_names = list(WALL_COLORS)
        self.color_index = 0
        self.error = ""

        self.tile = tile_size(maze)
        self.img_width = (maze.width * 2 + 1) * self.tile
        self.img_height = (maze.height * 2 + 1) * self.tile

        self.ptr = self.mlx.mlx_init()
        if not self.ptr:
            raise RuntimeError("mlx_init failed (no display?)")
        self.win = self.mlx.mlx_new_window(
            self.ptr, self.img_width, self.img_height + _FOOTER_HEIGHT,
            "A-Maze-ing")
        if not self.win:
            raise RuntimeError("mlx_new_window failed")
        self.img = self.mlx.mlx_new_image(
            self.ptr, self.img_width, self.img_height)

    # ---- 描画 ----
    def draw(self) -> None:
        """現在の状態を画像バッファに塗り、ウィンドウに貼り直す。"""
        data, _bpp, size_line, image_format = self.mlx.mlx_get_data_addr(
            self.img)
        rows = render_rows(self.maze, self.show_path,
                           self.color_names[self.color_index], self.tile)
        last_line: List[RGB] = []
        packed = b""
        for y, line in enumerate(rows):
            if line is not last_line:   # 同じ行オブジェクトは再計算しない
                packed = b"".join(_pack(c, image_format) for c in line)
                last_line = line
            start = y * size_line
            data[start:start + len(packed)] = packed
        self.mlx.mlx_put_image_to_window(self.ptr, self.win, self.img, 0, 0)
        self._draw_footer()

    def _draw_footer(self) -> None:
        y = self.img_height + 8
        for text in _HELP_LINES:
            self.mlx.mlx_string_put(
                self.ptr, self.win, 8, y, _TEXT_COLOR, text)
            y += 18
        if self.error:
            self.mlx.mlx_string_put(
                self.ptr, self.win, 8, y, 0xFF5555, self.error[:100])

    # ---- イベント ----
    def on_key(self, keycode: int, _param: Any) -> None:
        """キー押下。必須操作 3 つ + 終了。"""
        if keycode in _KEY_REGEN:
            self.maze = self.regenerate()
            try:
                self.write_output(self.output_path, self.maze)
                self.error = ""
            except OSError as os_error:
                self.error = f"could not write {self.output_path}: {os_error}"
            self.mlx.mlx_clear_window(self.ptr, self.win)
        elif keycode in _KEY_PATH:
            self.show_path = not self.show_path
        elif keycode in _KEY_COLOR:
            self.color_index = (self.color_index + 1) % len(self.color_names)
        elif keycode in _KEY_QUIT:
            self.close()
            return
        else:
            return
        self.draw()

    def on_expose(self, _param: Any) -> None:
        """ウィンドウが隠れて再表示されたときの描き直し。"""
        self.draw()

    def on_close(self, _param: Any) -> None:
        """ウィンドウの × ボタン。"""
        self.close()

    def close(self) -> None:
        """イベントループを抜ける（後始末は :meth:`run` の最後で行う）。"""
        self.mlx.mlx_loop_exit(self.ptr)

    def run(self) -> None:
        """フックを登録して、閉じられるまでイベントループを回す。"""
        self.mlx.mlx_key_hook(self.win, self.on_key, None)
        self.mlx.mlx_expose_hook(self.win, self.on_expose, None)
        self.mlx.mlx_hook(self.win, _EVENT_CLOSE, 0, self.on_close, None)
        self.draw()
        self.mlx.mlx_loop(self.ptr)
        self.mlx.mlx_destroy_image(self.ptr, self.img)
        self.mlx.mlx_destroy_window(self.ptr, self.win)
        self.mlx.mlx_release(self.ptr)


def run_gui(
    initial_maze: Maze,
    regenerate: Callable[[], Maze],
    output_path: str,
    write_output: Callable[[str, Maze], None],
) -> None:
    """MLX ウィンドウで迷路を表示し、キー操作で対話する。

    Raises:
        ImportError: MLX が無いとき。
        RuntimeError: ウィンドウを開けない（ディスプレイが無いなど）とき。
    """
    MazeWindow(initial_maze, regenerate, output_path, write_output).run()
