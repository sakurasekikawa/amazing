"""mazegen: 再利用可能な迷路生成パッケージ。

``PERFECT=True`` で唯一経路の迷路、``PERFECT=False`` でループを持つ
Pac-Man 盤面を生成できる（42 "A-Maze-ing" 課題向け）。

Example:
    最小の使用例::

        from mazegen import MazeGenerator

        generator = MazeGenerator(width=20, height=15, seed=42)
        maze = generator.generate(entry=(0, 0), exit=(19, 14), perfect=False)

        maze.to_hex_rows()      # 出力ファイル用の16進数グリッド
        maze.shortest_path()    # 入口から出口までの最短経路 (Direction のリスト)
"""

from .directions import ALL_WALLS, Cell, Direction
from .generator import Maze, MazeGenerationError, MazeGenerator

__all__ = [
    "ALL_WALLS",
    "Cell",
    "Direction",
    "Maze",
    "MazeGenerationError",
    "MazeGenerator",
]
__version__ = "1.0.0"
