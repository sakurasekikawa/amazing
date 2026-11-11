# mazegen

Reusable perfect / playable maze generator, built for the 42 "A-Maze-ing"
project and designed to be imported by later projects
(`pip install mazegen-1.0.0-py3-none-any.whl`).

## Instantiate and use

```python
from mazegen import MazeGenerator

generator = MazeGenerator(width=20, height=15, seed=42)
maze = generator.generate(entry=(0, 0), exit=(14, 19), perfect=False)
```

- `entry` / `exit` are `(row, col)` tuples, not `(x, y)`.
- `perfect=True` produces a maze with exactly one path between entry and
  exit (no loops). `perfect=False` (the default use case) produces a
  Pac-Man-style board: fully connected, at least two independent routes,
  and no real dead-end (the only "dead-ends" left are cells touching the
  isolated "42" pattern, which cannot be opened by design).

## Custom parameters

- `width`, `height`: grid size in cells.
- `seed`: optional `int`. Omit it to get a random maze (the chosen seed is
  then available as `generator.seed` / `maze.seed` so it can be reproduced
  later).

## Accessing the generated structure and a solution

```python
maze.walls            # List[List[Direction]] - one wall bitmask per cell
maze.to_hex_rows()     # one hex-digit string per row (output-file format)
maze.shortest_path()   # List[Direction] from entry to exit (BFS)
maze.pattern_cells     # frozenset of cells forming the "42" pattern
maze.warnings          # e.g. "42 pattern skipped, maze too small"
```

Note: this structure (`Maze.walls`, a 2D list of `Direction` bitmasks) is
the generator's own internal representation. It is **not** the same as the
output file format produced by `a_maze_ing.py` -- `to_hex_rows()` is the
conversion helper for that.

## License

MIT, see `LICENSE.md` at the repository root. The reuse and distribution of
this generator by later projects is explicitly allowed.
