_This project has been created as part of the 42 curriculum by ssekikaw._

# A-Maze-ing

## Description

A maze generator in Python that reads a `config.txt`, generates a maze
(optionally **perfect**: a single path with no loop), writes it to a file
using a per-cell hexadecimal wall encoding, and displays it in the
terminal with an interactive menu (regenerate / show-hide the shortest
path / rotate wall colours).

By default (`PERFECT=False`) the maze is instead a **playable, Pac-Man-style
board**: fully connected, the four corners and the centre are open, at
least two independent routes exist, and real dead-ends are eliminated
("braiding") -- only cells touching the mandatory, fully-isolated **"42"**
pattern drawn in the middle may look like a dead-end.

The maze-generation logic itself lives in a standalone, pip-installable
package, `mazegen`, so it can be reused by later projects.

## Instructions

Requires **Python 3.10+**.

```bash
make install        # python-dotenv, flake8, mypy, pytest, build
make run             # python3 a_maze_ing.py config.txt
make debug           # same, under pdb
make lint            # flake8 + mypy (mandatory flags)
make lint-strict     # flake8 + mypy --strict
make test            # pytest tests/ (dev-only, not graded)
make build           # rebuilds mazegen-1.0.0{.tar.gz,-py3-none-any.whl}
make clean
```

Or directly:

```bash
python3 a_maze_ing.py config.txt
```

A default `config.txt` is provided at the repository root.

To verify an output file against the subject's rules (wall coherence,
perfect-vs-playable, dead-ends, loops), use the 42-provided
`maze_analyzer.py` (not part of this repository):

```bash
python3 maze_analyzer.py maze.txt                  # default thresholds
python3 maze_analyzer.py maze.txt --max-dead-ends 0 # check the bonus
```

### config.txt format

One `KEY=VALUE` pair per line; lines starting with `#` are ignored.

| Key | Description | Example |
|---|---|---|
| `WIDTH` | maze width in cells (>= 5) | `WIDTH=20` |
| `HEIGHT` | maze height in cells (>= 5) | `HEIGHT=15` |
| `ENTRY` | entry coordinates `x,y` | `ENTRY=0,0` |
| `EXIT` | exit coordinates `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | output filename | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | `True`/`False` | `PERFECT=False` |
| `SEED` | optional, for a reproducible maze | `SEED=42` |

Any malformed value (missing key, out-of-bounds entry/exit, non-integer
size, file not found, ...) is reported with a clear message on stderr and
a non-zero exit code -- the program never crashes.

## Maze generation algorithm

1. **Randomized recursive backtracker** (iterative, stack-based) digs a
   spanning tree over every cell except the ones reserved for the "42"
   pattern, which stay fully closed and isolated by construction. This
   alone is the final result for `PERFECT=True`.
2. For `PERFECT=False`, two extra passes run on top of that spanning tree:
   - **Loop addition**: a handful of still-closed walls between adjacent
     cells are opened to create independent routes (loops).
   - **Braiding**: any remaining dead-end has one of its closed walls
     opened, repeated until no *real* dead-end is left (a wall facing the
     "42" pattern cannot be opened, so those are tolerated).
   Both passes reject any wall opening that would create a fully-open 3x3
   block of cells (the "no corridor wider than 2 cells" rule), by checking
   every 3x3 window that would contain the new opening.

### Why this algorithm

A recursive backtracker was chosen because it naturally produces a long,
winding single path (good for `PERFECT=True`) and is simple to adapt:
adding loops/braiding on top of an existing spanning tree is far easier
to reason about than generating loops and connectivity from scratch, and
it keeps the whole generator in one small, readable module.

## What is reusable, and how

Everything under `mazegen/` (`Direction`, `Maze`, `MazeGenerator`,
`MazeGenerationError`) has no dependency on `config.txt`, the output-file
format, or the terminal display -- it only deals with `(row, col)`
coordinates and wall bitmasks. See `README_mazegen.md` (packaged with the
wheel/sdist) for the short usage documentation requested by the subject.
`a_maze_ing.py` (reads `config.txt` with python-dotenv and writes the
output file) and `display.py` are specific to this
program and stay out of the reusable package.

## Visual representation

Terminal ASCII rendering (1 cell = 2x2 characters), run with
`python3 a_maze_ing.py config.txt`:

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
Choice? (1-4):
```

A short demo recording is available as `../demo.mp4` (see
`../explanation.html` for context).

## Team and project management

- Solo project. **ssekikaw** (Sekikawa Sakura) designed the maze model,
  the generation/loop/braiding algorithm and the packaging; implementation,
  linting and verification were done with AI assistance (see Resources).
- Planning: read the subject -> write `REQUIREMENTS.md` (with the data
  model and generation flow as Mermaid diagrams) -> implement `mazegen`
  first (it has no other dependency) -> implement config/output/display on
  top of it -> verify against the provided `maze_analyzer.py` across many
  sizes/seeds/PERFECT combinations -> package and document. The verification
  step caught one real bug (wall colours never rotated, because two
  distinct characters shared the same dict key) and one test assumption
  that was too strict (a cell touching the "42" pattern is tolerated as a
  dead-end, it isn't a bug) -- both are detailed in `../REPORT.md`.
- What worked well: writing the reusable `mazegen` package before the CLI
  kept the generation logic easy to unit-test in isolation. Running the
  official `maze_analyzer.py` across dozens of size/seed/PERFECT
  combinations early caught the colour bug immediately instead of at
  review time.
- What could be improved: a graphical (MLX) display was not implemented
  (ASCII was judged sufficient per the subject); the "42" pattern uses a
  compact 3x5 pixel font, which stays recognisable but is still small at
  typical maze sizes.
- Tools used: Python 3.11 (pyenv), flake8, mypy (incl. `--strict`),
  pytest, `python -m build`, and the 42-provided `maze_analyzer.py` for
  spec-accurate verification.

## Resources

- *Mazes for Programmers* (Jamis Buck) -- recursive backtracker and
  braiding algorithms.
- [Wikipedia: Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- Python docs: `enum.IntFlag`, `collections.deque`, `typing`,
  [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/).
- **AI usage**: Claude (Anthropic) was used throughout this project --
  parsing the subject PDF into `REQUIREMENTS.md`, writing the
  implementation (`mazegen`, `a_maze_ing.py` and friends), iterating on
  the generation algorithm against the provided `maze_analyzer.py` until
  it reliably passed both `PERFECT=True` and `PERFECT=False` across many
  sizes/seeds, writing/debugging the pytest suite, building the
  `mazegen` package, and writing this documentation. All generated code
  was run, linted (`flake8`/`mypy --strict`), tested and cross-checked
  against `maze_analyzer.py` before being accepted -- see `../REPORT.md`
  for the full verification log and the bugs caught during that process.
