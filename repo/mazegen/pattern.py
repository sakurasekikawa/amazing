"""迷路の中央に浮かぶ、完全に孤立した "42" 模様を作る。

課題PDF IV.4: 「視覚的に "42" という文字が完全に閉じたセル群で
描かれていること」「サイズ的に収まらない場合は模様を省略し、
コンソールにエラーメッセージを出すこと」という要件に対応する。
"""

from __future__ import annotations

from typing import FrozenSet, Optional, Tuple

from .directions import Cell

# 3x5 のドット絵フォント（定番の電卓風ブロック体）。"X" が閉じたセルになる。
_DIGIT_4 = (
    "X.X",
    "X.X",
    "XXX",
    "..X",
    "..X",
)
_DIGIT_2 = (
    "XXX",
    "..X",
    "XXX",
    "X..",
    "XXX",
)

PATTERN_HEIGHT = len(_DIGIT_4)
# 2桁の間に1列の隙間を空ける。この隙間列はどの行も必ず "." なので、
# 迷路の中心列がここに重なれば中心セルは常に開いたままになる。
PATTERN_WIDTH = len(_DIGIT_4[0]) + 1 + len(_DIGIT_2[0])
# 外周からの最低マージン（境界ぎりぎりに模様を置かないため）。
MARGIN = 1
MIN_WIDTH_FOR_PATTERN = PATTERN_WIDTH + 2 * MARGIN
MIN_HEIGHT_FOR_PATTERN = PATTERN_HEIGHT + 2 * MARGIN


def locate_42_cells(
    width: int, height: int
) -> Tuple[FrozenSet[Cell], Optional[str]]:
    """迷路の中央で "42" の形になるセルの座標を求める。

    壁はここでは触らない。MazeGenerator がこれらのセルを掘る対象から
    外すことで、結果として完全に閉じたセルとして残る。

    Args:
        width: 迷路の幅（セル数）。
        height: 迷路の高さ（セル数）。

    Returns:
        (閉じたセルの集合, 収まらなかった場合の警告メッセージ)。
        収まる場合は警告は ``None``。
    """
    top = (height - PATTERN_HEIGHT) // 2
    left = (width - PATTERN_WIDTH) // 2
    if top < MARGIN or left < MARGIN:
        min_size = f"{MIN_WIDTH_FOR_PATTERN}x{MIN_HEIGHT_FOR_PATTERN}"
        return frozenset(), (
            f"maze is {width}x{height}, too small for the '42' pattern "
            f"(needs at least {min_size}); skipping it."
        )

    cells = set()
    for row in range(PATTERN_HEIGHT):
        line = _DIGIT_4[row] + "." + _DIGIT_2[row]
        for col, char in enumerate(line):
            if char == "X":
                cells.add((top + row, left + col))
    return frozenset(cells), None
