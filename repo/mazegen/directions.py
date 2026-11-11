"""迷路の壁の向きを表す型と定数。

ビット値は出力ファイル仕様（課題PDF表 IV.5）と完全に一致させている:
North=bit0(1), East=bit1(2), South=bit2(4), West=bit3(8)。
ビットが立っている = その方向の壁は閉じている。
"""

from __future__ import annotations

from enum import IntFlag
from typing import Dict, Tuple

#: (row, col) 形式のセル座標。row は Y、col は X に対応する。
Cell = Tuple[int, int]


class Direction(IntFlag):
    """壁1枚を表すビットフラグ。"""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

    @property
    def opposite(self) -> "Direction":
        """隣のセルから見たときの同じ壁。"""
        return _OPPOSITE[self]

    @property
    def step(self) -> Cell:
        """この向きに1マス進んだときの (row, col) の増分。"""
        return _STEP[self]

    @property
    def letter(self) -> str:
        """出力ファイルの経路表現で使う1文字 (N/E/S/W)。"""
        return _LETTER[self]


_OPPOSITE: Dict[Direction, Direction] = {
    Direction.NORTH: Direction.SOUTH,
    Direction.SOUTH: Direction.NORTH,
    Direction.EAST: Direction.WEST,
    Direction.WEST: Direction.EAST,
}
_STEP: Dict[Direction, Cell] = {
    Direction.NORTH: (-1, 0),
    Direction.EAST: (0, 1),
    Direction.SOUTH: (1, 0),
    Direction.WEST: (0, -1),
}
_LETTER: Dict[Direction, str] = {
    Direction.NORTH: "N",
    Direction.EAST: "E",
    Direction.SOUTH: "S",
    Direction.WEST: "W",
}

#: 4方向すべてが閉じている状態（"42" 模様の完全孤立セルに使う）。
ALL_WALLS = Direction.NORTH | Direction.EAST | Direction.SOUTH | Direction.WEST
