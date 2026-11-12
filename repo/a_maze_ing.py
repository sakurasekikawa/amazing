#!/usr/bin/env python3
"""A-Maze-ing: config.txt から迷路を生成し、ファイル出力とターミナル表示を行う。

42 "A-Maze-ing" 課題のメインプログラム。迷路生成そのものは再利用可能な
``mazegen`` パッケージに委譲し、このファイルは
設定の読み込み・ファイル出力・対話的表示のみを担当する。

Usage:
    python3 a_maze_ing.py config.txt            # MLX があれば GUI、無ければ端末
    python3 a_maze_ing.py config.txt --ascii    # 常に端末表示
"""

from __future__ import annotations

import random
import sys
from dataclasses import dataclass
from typing import List, Optional, Tuple

from dotenv import dotenv_values

from display import run_interactive
from gui import mlx_available, run_gui
from mazegen import Maze, MazeGenerationError, MazeGenerator

REQUIRED_KEYS = ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT")


@dataclass(frozen=True)
class Config:
    """読み込み・型変換済みの設定値。座標は内部表現の (row, col) = (y, x)。"""

    width: int
    height: int
    entry: Tuple[int, int]
    exit: Tuple[int, int]
    output_file: str
    perfect: bool
    seed: Optional[int]


def read_config(path: str) -> Config:
    """config.txt を読み、型変換した :class:`Config` を返す。

    Raises:
        OSError: ファイルが開けないとき。
        ValueError: 必須の値が欠けている、または数値・x,y・True/False
            として読めないとき。
    """
    # ファイルが無くても dotenv は空を返すだけなので、自分で開いて渡す
    with open(path, encoding="utf-8") as stream:
        values = dotenv_values(stream=stream)
    # 値が空の行や "=" の無い行は値が None / "" になるので、ここで落とす
    raw = {key: value for key, value in values.items() if value}
    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ValueError(f"missing value(s): {', '.join(missing)}")

    if raw["PERFECT"] not in ("True", "False"):
        raise ValueError(f"PERFECT must be True or False, "
                         f"got {raw['PERFECT']!r}")
    width, height = int(raw["WIDTH"]), int(raw["HEIGHT"])
    # config の座標は x,y だが、迷路内部は (row, col) = (y, x)
    entry_x, entry_y = map(int, raw["ENTRY"].split(","))
    exit_x, exit_y = map(int, raw["EXIT"].split(","))
    seed = int(raw["SEED"]) if "SEED" in raw else None
    return Config(width, height, (entry_y, entry_x), (exit_y, exit_x),
                  raw["OUTPUT_FILE"], raw["PERFECT"] == "True", seed)


def build_maze(config: Config, seed: Optional[int] = None) -> Maze:
    """``config`` から1つの迷路を生成する。

    Args:
        config: 検証済みの設定。
        seed: 指定があればこのシードを使う（省略時は config.seed、それも
            無ければ毎回ランダム）。
    """
    used_seed = seed if seed is not None else config.seed
    generator = MazeGenerator(config.width, config.height, used_seed)
    return generator.generate(config.entry, config.exit, config.perfect)


def write_maze_file(path: str, maze: Maze) -> None:
    """``maze`` を課題PDF IV.5 の形式で ``path`` に書き出す。

    16進数グリッド → 空行 → entry "x,y" → exit "x,y" → 最短経路 (NESW)。
    各行は改行で終わる。書き込めないときは OSError。
    """
    (entry_y, entry_x), (exit_y, exit_x) = maze.entry, maze.exit
    path_letters = "".join(step.letter for step in maze.shortest_path())
    lines = maze.to_hex_rows() + [
        "", f"{entry_x},{entry_y}", f"{exit_x},{exit_y}", path_letters
    ]
    with open(path, "w", encoding="utf-8") as stream:
        stream.write("\n".join(lines) + "\n")


def main(argv: List[str]) -> int:
    """エントリポイント。常に正常終了か、分かりやすいエラーで非ゼロ終了する。"""
    use_gui = "--ascii" not in argv
    args = [arg for arg in argv if arg != "--ascii"]
    if len(args) != 1:
        print("Usage: python3 a_maze_ing.py <config.txt> [--ascii]",
              file=sys.stderr)
        return 1

    config_path = args[0]
    try:
        config = read_config(config_path)
        maze = build_maze(config)
        write_maze_file(config.output_file, maze)

        def regenerate() -> Maze:
            return build_maze(config, seed=random.randrange(2**31))

        show = run_interactive
        if use_gui and mlx_available():
            show = run_gui
        elif use_gui:
            print("MLX not found: using the terminal display "
                  "(install mlx-2.2 for the GUI).", file=sys.stderr)
        try:
            show(maze, regenerate, config.output_file, write_maze_file)
        except RuntimeError as error:   # ディスプレイ無し等で窓が開けない
            print(f"GUI unavailable ({error}): using the terminal display.",
                  file=sys.stderr)
            run_interactive(maze, regenerate, config.output_file,
                            write_maze_file)
    except ValueError as error:
        print(f"Configuration error: {error}", file=sys.stderr)
        return 1
    except MazeGenerationError as error:
        print(f"Cannot generate maze: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"File error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
