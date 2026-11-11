"""迷路生成のコアロジック。

アルゴリズム（README / REQUIREMENTS.md にも記載）:

1. **再帰バックトラッカー法**で "42" 模様のセルを除いた全セルを結ぶ
   全域木（スパニングツリー）を掘る。この時点で PERFECT=True の
   「唯一の経路しかない迷路」が完成する。
2. PERFECT=False（デフォルト）の場合は、Pac-Man 盤面にするために:
   a. ループ用の壁をいくつか追加で開け、独立した経路を複数作る。
   b. 行き止まりに繋がる壁を開けて行き止まりを解消する（braiding）。
   どちらの操作も「3x3以上の開けた空間を作らない」制約を守りながら行う。

全体を通して :class:`MazeGenerator` が唯一の公開エントリーポイントで、
他のプロジェクトから ``pip install`` して再利用できるように設計している。
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Set

from .directions import ALL_WALLS, Cell, Direction
from .pattern import locate_42_cells

#: ループ追加・ブレイディングを打ち切るまでの最大試行回数（無限ループ防止）。
_MAX_BRAID_PASSES = 6


class MazeGenerationError(Exception):
    """迷路が生成できない設定（サイズ・入口出口など）のときに送出する。"""


@dataclass
class Maze:
    """生成された迷路: 壁グリッド・入口・出口・付随情報を保持する。

    Attributes:
        width: 幅（セル数）。
        height: 高さ（セル数）。
        walls: ``walls[row][col]`` が、そのセルで閉じている壁のビット集合。
        entry: 入口セル ``(row, col)``。
        exit: 出口セル ``(row, col)``。
        perfect: ``True`` なら唯一経路の迷路、``False`` なら周回可能な盤面。
        pattern_cells: "42" 模様として完全に孤立させたセルの集合。
        seed: 生成に使った乱数シード（再現用）。
        warnings: 生成中に発生した非致命的な警告（例: "42" 模様を省略した等）。
    """

    width: int
    height: int
    walls: List[List[Direction]]
    entry: Cell
    exit: Cell
    perfect: bool
    pattern_cells: frozenset[Cell]
    seed: int
    warnings: List[str] = field(default_factory=list)

    def to_hex_rows(self) -> List[str]:
        """出力ファイル用: 1セル1桁の16進数文字列を行ごとに返す。"""
        return [
            "".join(format(int(cell), "x") for cell in row)
            for row in self.walls
        ]

    def shortest_path(self) -> List[Direction]:
        """entry から exit までの最短経路を方向のリストとして返す（BFS）。"""
        prev: Dict[Cell, "tuple[Cell, Direction]"] = {}
        visited: Set[Cell] = {self.entry}
        queue: deque[Cell] = deque([self.entry])
        while queue:
            current = queue.popleft()
            if current == self.exit:
                break
            for direction in Direction:
                if self.walls[current[0]][current[1]] & direction:
                    continue
                nxt = (
                    current[0] + direction.step[0],
                    current[1] + direction.step[1],
                )
                if not self._in_bounds(nxt) or nxt in visited:
                    continue
                visited.add(nxt)
                prev[nxt] = (current, direction)
                queue.append(nxt)

        if self.exit not in visited:
            return []  # 設計上は到達不能にはならないが、念のため安全に返す

        path: List[Direction] = []
        node = self.exit
        while node != self.entry:
            node, direction = prev[node]
            path.append(direction)
        path.reverse()
        return path

    def _in_bounds(self, cell: Cell) -> bool:
        row, col = cell
        return 0 <= row < self.height and 0 <= col < self.width


class MazeGenerator:
    """再利用可能な迷路生成器。

    Example:
        基本的な使い方::

            from mazegen import MazeGenerator

            generator = MazeGenerator(width=20, height=15, seed=42)
            maze = generator.generate(
                entry=(0, 0), exit=(19, 14), perfect=False
            )

            maze.to_hex_rows()      # 出力ファイル用の16進数表現
            maze.shortest_path()    # [Direction.EAST, Direction.SOUTH, ...]

        ``seed`` を省略するとランダムなシードが選ばれ、``maze.seed`` で
        後から確認できる（同じシードを渡せば同じ迷路を再現できる）。
    """

    def __init__(
        self, width: int, height: int, seed: Optional[int] = None
    ) -> None:
        """Args:
            width: 迷路の幅（セル数、1以上）。
            height: 迷路の高さ（セル数、1以上）。
            seed: 乱数シード。``None`` なら自動で選ばれる。
        """
        if width < 1 or height < 1:
            raise MazeGenerationError("width and height must be positive")
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randrange(2**31)

    def generate(self, entry: Cell, exit: Cell, perfect: bool) -> Maze:
        """1つの迷路を生成する。

        Args:
            entry: 入口セル ``(row, col)``。
            exit: 出口セル ``(row, col)``。
            perfect: ``True`` で唯一経路の迷路、``False`` で周回可能な盤面。

        Returns:
            生成された :class:`Maze`。

        Raises:
            MazeGenerationError: 入口/出口が盤面外、または同一の場合。
        """
        self._validate_endpoints(entry, exit)
        rng = random.Random(self.seed)

        pattern_cells, warning = locate_42_cells(self.width, self.height)
        if entry in pattern_cells or exit in pattern_cells:
            pattern_cells, warning = frozenset(), (
                "the '42' pattern would overlap the entry/exit cell; "
                "skipping it."
            )

        walls: List[List[Direction]] = [
            [ALL_WALLS for _ in range(self.width)] for _ in range(self.height)
        ]
        carvable: List[Cell] = [
            (row, col)
            for row in range(self.height)
            for col in range(self.width)
            if (row, col) not in pattern_cells
        ]

        self._carve_spanning_tree(walls, carvable, entry, rng)
        if not perfect:
            self._add_loops(walls, carvable, rng)
            self._braid_dead_ends(walls, carvable, rng)

        return Maze(
            width=self.width,
            height=self.height,
            walls=walls,
            entry=entry,
            exit=exit,
            perfect=perfect,
            pattern_cells=pattern_cells,
            seed=self.seed,
            warnings=[warning] if warning else [],
        )

    # -- 内部ヘルパー -------------------------------------------------- #

    def _validate_endpoints(self, entry: Cell, exit: Cell) -> None:
        for name, cell in (("entry", entry), ("exit", exit)):
            row, col = cell
            if not (0 <= row < self.height and 0 <= col < self.width):
                raise MazeGenerationError(
                    f"{name} x={col}, y={row} is outside the "
                    f"{self.width}x{self.height} grid"
                )
        if entry == exit:
            raise MazeGenerationError("entry and exit must be different cells")

    def _carve_spanning_tree(
        self,
        walls: List[List[Direction]],
        carvable: Sequence[Cell],
        entry: Cell,
        rng: random.Random,
    ) -> None:
        """反復版・再帰バックトラッカー法で全域木を掘る。

        entry は呼び出し元の generate() で、"42" 模様と重ならないことが
        既に保証されているので、常に carvable に含まれる。
        """
        carvable_set = set(carvable)
        visited = {entry}
        stack = [entry]
        while stack:
            current = stack[-1]
            directions = list(Direction)
            rng.shuffle(directions)
            advanced = False
            for direction in directions:
                nxt = self._neighbour(current, direction)
                if nxt in carvable_set and nxt not in visited:
                    walls[current[0]][current[1]] &= ~direction
                    walls[nxt[0]][nxt[1]] &= ~direction.opposite
                    visited.add(nxt)
                    stack.append(nxt)
                    advanced = True
                    break
            if not advanced:
                stack.pop()

    def _add_loops(
        self,
        walls: List[List[Direction]],
        carvable: Sequence[Cell],
        rng: random.Random,
    ) -> None:
        """周回経路（ループ）を作るために、閉じた壁をいくつか開ける。"""
        carvable_set = set(carvable)
        target_extra = max(2, len(carvable) // 25)
        candidates = self._closed_edges(walls, carvable_set)
        rng.shuffle(candidates)
        opened = 0
        for cell, direction, other in candidates:
            if opened >= target_extra:
                break
            if self._would_make_big_room(walls, cell, other):
                continue
            self._open_wall(walls, cell, direction)
            opened += 1

    def _braid_dead_ends(
        self,
        walls: List[List[Direction]],
        carvable: Sequence[Cell],
        rng: random.Random,
    ) -> None:
        """行き止まりに繋がる壁を開けて、行き止まりを可能な限りなくす。"""
        carvable_set = set(carvable)
        for _ in range(_MAX_BRAID_PASSES):
            dead_ends = [
                cell for cell in carvable if self._is_dead_end(walls, cell)
            ]
            if not dead_ends:
                break
            rng.shuffle(dead_ends)
            for cell in dead_ends:
                closed = [
                    direction
                    for direction in Direction
                    if walls[cell[0]][cell[1]] & direction
                ]
                options = [
                    (direction, self._neighbour(cell, direction))
                    for direction in closed
                ]
                options = [
                    (direction, other)
                    for direction, other in options
                    if other in carvable_set
                ]
                rng.shuffle(options)
                for direction, other in options:
                    if self._would_make_big_room(walls, cell, other):
                        continue
                    self._open_wall(walls, cell, direction)
                    break

    def _is_dead_end(self, walls: List[List[Direction]], cell: Cell) -> bool:
        bits = walls[cell[0]][cell[1]]
        open_count = sum(1 for direction in Direction if not bits & direction)
        return open_count == 1

    def _closed_edges(
        self, walls: List[List[Direction]], carvable_set: Set[Cell]
    ) -> List["tuple[Cell, Direction, Cell]"]:
        """隣接していて、かつまだ壁で隔てられている2セルの組を列挙する。"""
        edges: List["tuple[Cell, Direction, Cell]"] = []
        for cell in carvable_set:
            for direction in (Direction.EAST, Direction.SOUTH):
                other = self._neighbour(cell, direction)
                closed = walls[cell[0]][cell[1]] & direction
                if other in carvable_set and closed:
                    edges.append((cell, direction, other))
        return edges

    def _neighbour(self, cell: Cell, direction: Direction) -> Cell:
        return cell[0] + direction.step[0], cell[1] + direction.step[1]

    def _open_wall(
        self, walls: List[List[Direction]], cell: Cell, direction: Direction
    ) -> None:
        other = self._neighbour(cell, direction)
        walls[cell[0]][cell[1]] &= ~direction
        walls[other[0]][other[1]] &= ~direction.opposite

    def _would_make_big_room(
        self, walls: List[List[Direction]], a: Cell, b: Cell
    ) -> bool:
        """a-b の壁を開けると3x3以上の開けた部屋ができてしまうかを調べる。

        両セルを含みうるすべての3x3の窓について、内部の12本の壁が
        (このa-b間を開けたと仮定して) 全て開いているかを確認する。
        """
        if self.height < 3 or self.width < 3:
            return False
        row_hi, col_hi = max(a[0], b[0]), max(a[1], b[1])
        row_lo, col_lo = min(a[0], b[0]), min(a[1], b[1])
        top_range = range(max(0, row_hi - 2), min(row_lo, self.height - 3) + 1)
        left_range = range(max(0, col_hi - 2), min(col_lo, self.width - 3) + 1)
        for top in top_range:
            for left in left_range:
                if self._window_fully_open(walls, top, left, a, b):
                    return True
        return False

    def _window_fully_open(
        self,
        walls: List[List[Direction]],
        top: int,
        left: int,
        extra_a: Cell,
        extra_b: Cell,
    ) -> bool:
        def is_open(p: Cell, q: Cell) -> bool:
            if (p, q) == (extra_a, extra_b) or (p, q) == (extra_b, extra_a):
                return True
            dc = q[1] - p[1]
            direction = Direction.EAST if dc == 1 else Direction.SOUTH
            return not (walls[p[0]][p[1]] & direction)

        cells = [[(top + r, left + c) for c in range(3)] for r in range(3)]
        for r in range(3):
            for c in range(2):
                if not is_open(cells[r][c], cells[r][c + 1]):
                    return False
        for r in range(2):
            for c in range(3):
                if not is_open(cells[r][c], cells[r + 1][c]):
                    return False
        return True
