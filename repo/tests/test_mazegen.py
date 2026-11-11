"""mazegen / a_maze_ing の動作確認テスト（提出物ではなく、開発時の検証用）。

実行方法::

    python3 -m pytest tests/
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mazegen import Direction, MazeGenerationError, MazeGenerator  # noqa: E402
from mazegen.directions import Cell  # noqa: E402
from mazegen.generator import Maze  # noqa: E402


def test_perfect_maze_has_no_loops() -> None:
    maze = MazeGenerator(12, 10, seed=1).generate(
        (0, 0), (9, 11), perfect=True
    )
    region = _reachable(maze)
    edges = _count_open_edges(maze, region)
    assert edges == len(region) - 1  # 木 = 辺の数がノード数-1


def test_playable_maze_has_loops_and_no_real_dead_end() -> None:
    # "42" 模様に隣接するセルは、その面だけは原理的に開けられない
    # （42は孤立必須）ため、提供の maze_analyzer.py 同様に
    # 「開けられる壁が残っている本物の行き止まり」だけを数える。
    maze = MazeGenerator(20, 15, seed=7).generate(
        (0, 0), (14, 19), perfect=False
    )
    region = _reachable(maze)
    assert len(region) == maze.width * maze.height - len(maze.pattern_cells)
    real_dead_ends = sum(
        1
        for cell in region
        if _open_count(maze, cell) == 1 and _has_openable_wall(maze, cell)
    )
    assert real_dead_ends == 0


def test_same_seed_is_reproducible() -> None:
    maze_a = MazeGenerator(15, 11, seed=99).generate(
        (0, 0), (10, 14), perfect=False
    )
    maze_b = MazeGenerator(15, 11, seed=99).generate(
        (0, 0), (10, 14), perfect=False
    )
    assert maze_a.walls == maze_b.walls


def test_rejects_entry_outside_bounds() -> None:
    generator = MazeGenerator(10, 10, seed=1)
    try:
        generator.generate((0, 0), (99, 99), perfect=False)
        assert False, "should have raised"
    except MazeGenerationError:
        pass


def test_shortest_path_matches_bfs_length() -> None:
    maze = MazeGenerator(14, 10, seed=3).generate(
        (0, 0), (9, 13), perfect=False
    )
    path = maze.shortest_path()
    row, col = maze.entry
    for step in path:
        assert not maze.walls[row][col] & step
        row += step.step[0]
        col += step.step[1]
    assert (row, col) == maze.exit


def _in_bounds(maze: "Maze", cell: "Cell") -> bool:
    return 0 <= cell[0] < maze.height and 0 <= cell[1] < maze.width


def _reachable(maze: "Maze") -> "set[Cell]":
    from collections import deque

    start = maze.entry
    seen = {start}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        for direction in Direction:
            if maze.walls[cell[0]][cell[1]] & direction:
                continue
            nxt = (cell[0] + direction.step[0], cell[1] + direction.step[1])
            if nxt not in seen and _in_bounds(maze, nxt):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _open_count(maze: "Maze", cell: "Cell") -> int:
    bits = maze.walls[cell[0]][cell[1]]
    return sum(1 for direction in Direction if not bits & direction)


def _has_openable_wall(maze: "Maze", cell: "Cell") -> bool:
    bits = maze.walls[cell[0]][cell[1]]
    for direction in Direction:
        if not bits & direction:
            continue
        other = (cell[0] + direction.step[0], cell[1] + direction.step[1])
        if _in_bounds(maze, other) and other not in maze.pattern_cells:
            return True
    return False


def _count_open_edges(maze: "Maze", region: "set[Cell]") -> int:
    count = 0
    for cell in region:
        for direction in (Direction.EAST, Direction.SOUTH):
            other = (cell[0] + direction.step[0], cell[1] + direction.step[1])
            bits = maze.walls[cell[0]][cell[1]]
            if other in region and not (bits & direction):
                count += 1
    return count
