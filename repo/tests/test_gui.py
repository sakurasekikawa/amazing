"""gui.py の動作確認（偽の mlx モジュールで MLX 無しでも回す。開発用）。"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Any, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import gui  # noqa: E402
from mazegen import MazeGenerator  # noqa: E402


class FakeMlx:
    """mlx.Mlx と同じ呼び出し口を持つ記録用の偽物。"""

    def __init__(self) -> None:
        self.calls: List[str] = []
        self.hooks: dict[str, Any] = {}
        self.buf = bytearray()
        self.size_line = 0

    def mlx_init(self) -> int:
        return 1

    def mlx_new_window(self, ptr: int, w: int, h: int, title: str) -> int:
        self.calls.append(f"window {w}x{h}")
        return 2

    def mlx_new_image(self, ptr: int, w: int, h: int) -> int:
        self.size_line = w * 4 + 8   # 行末にパディングがあっても崩れないか
        self.buf = bytearray(self.size_line * h)
        return 3

    def mlx_get_data_addr(self, img: int) -> Tuple[Any, int, int, int]:
        return memoryview(self.buf), 32, self.size_line, 1

    def mlx_put_image_to_window(self, *args: Any) -> None:
        self.calls.append("put")

    def mlx_string_put(self, *args: Any) -> None:
        self.calls.append("text")

    def mlx_clear_window(self, *args: Any) -> None:
        pass

    def mlx_key_hook(self, win: int, cb: Any, param: Any) -> None:
        self.hooks["key"] = cb

    def mlx_expose_hook(self, win: int, cb: Any, param: Any) -> None:
        self.hooks["expose"] = cb

    def mlx_hook(self, win: int, ev: int, mask: int, cb: Any,
                 param: Any) -> None:
        self.hooks[f"ev{ev}"] = cb

    def mlx_loop(self, ptr: int) -> None:
        self.calls.append("loop")

    def mlx_loop_exit(self, ptr: int) -> None:
        self.calls.append("exit")

    def mlx_destroy_image(self, *args: Any) -> None:
        pass

    def mlx_destroy_window(self, *args: Any) -> None:
        pass

    def mlx_release(self, *args: Any) -> None:
        pass


def _window(monkeypatch: Any) -> Tuple[gui.MazeWindow, FakeMlx]:
    fake_module = types.ModuleType("mlx")
    fake = FakeMlx()
    fake_module.Mlx = lambda: fake  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "mlx", fake_module)
    maze = MazeGenerator(10, 8, seed=3).generate((0, 0), (7, 9), False)
    written: List[int] = []
    window = gui.MazeWindow(
        maze,
        lambda: MazeGenerator(10, 8, seed=4).generate((0, 0), (7, 9), False),
        "out.txt", lambda path, m: written.append(1))
    window.written = written  # type: ignore[attr-defined]
    return window, fake


def test_tile_fits_limit() -> None:
    maze = MazeGenerator(50, 40, seed=1).generate((0, 0), (39, 49), False)
    t = gui.tile_size(maze)
    assert t >= 2
    assert (maze.width * 2 + 1) * t <= 1000
    assert (maze.height * 2 + 1) * t <= 700


def test_entry_pixel_colour_and_padding(monkeypatch: Any) -> None:
    window, fake = _window(monkeypatch)
    window.run()
    t = window.tile
    # format=1 (A,R,G,B): 入口マス (1,1) の中心は入口色 (215, 95, 215)
    off = (t + t // 2) * fake.size_line + (t + t // 2) * 4
    assert tuple(fake.buf[off:off + 4]) == (255, 215, 95, 215)
    assert fake.calls[-1] == "loop" or "loop" in fake.calls


def test_keys_toggle_and_regenerate(monkeypatch: Any) -> None:
    window, fake = _window(monkeypatch)
    window.run()
    before = bytes(fake.buf)
    window.on_key(ord("2"), None)          # 経路表示
    assert window.show_path and bytes(fake.buf) != before
    window.on_key(ord("2"), None)
    assert not window.show_path and bytes(fake.buf) == before
    window.on_key(ord("3"), None)          # 壁の色
    assert window.color_index == 1 and bytes(fake.buf) != before
    window.on_key(ord("1"), None)          # 再生成 + ファイル書き出し
    assert window.written == [1]
    window.on_key(65307, None)             # Esc
    assert fake.calls[-1] == "exit"
