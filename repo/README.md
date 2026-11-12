_This project has been created as part of the 42 curriculum by ssekikaw, hyoshida._

# A-Maze-ing

## Description（概要）

`config.txt` を読み込んで迷路を生成し、セルごとの壁を 16 進数でエンコードした
ファイルに書き出し、ターミナル上にインタラクティブなメニュー付きで表示する
Python 製の迷路ジェネレーターです。メニューでは「再生成」「最短経路の表示/非表示」
「壁の色の切り替え」ができます。生成できる迷路には 2 種類あります。

- **完全迷路（`PERFECT=True`）**: 入口から出口までの経路がちょうど 1 本で、ループがない迷路。
- **プレイアブル迷路（`PERFECT=False`、デフォルト）**: パックマン風の盤面。
  全セルが連結していて、四隅と中央が開いており、少なくとも 2 本の独立した経路があり、
  本物の行き止まりは取り除かれています（「ブレイディング」）。行き止まりに見えてよいのは、
  中央に描かれる必須の完全孤立パターン **「42」** に接するセルだけです。

迷路生成のロジックは、独立した pip インストール可能なパッケージ `mazegen` に
切り出してあり、後続のプロジェクトから再利用できます。

## Instructions（使い方）

**Python 3.10 以上**が必要です。

```bash
make install        # sudo 不要。仮想環境 .venv を作り pip で python-dotenv, flake8, mypy, pytest, build を入れる
make install-mlx MLX_WHL=<mlx-2.2-py3-none-any.whl>   # 任意: GUI 用の MLX
make run             # python3 a_maze_ing.py config.txt（MLX があれば GUI、無ければ端末表示）
make run-ascii       # 常に端末表示
make debug           # 同上を pdb 下で実行
make lint            # flake8 + mypy（必須フラグ）
make lint-strict     # flake8 + mypy --strict
make test            # pytest tests/（開発用、評価対象外）
make build           # mazegen-1.0.0{.tar.gz,-py3-none-any.whl} を再ビルド
make clean
```

直接実行する場合:

```bash
python3 a_maze_ing.py config.txt
```

デフォルトの `config.txt` がリポジトリ直下にあります。

出力ファイルがサブジェクトのルール（壁の整合性、完全/プレイアブルの判定、行き止まり、
ループ）を満たすか確認するには、42 が配布している `maze_analyzer.py`
（このリポジトリには含まれません）を使います。

```bash
python3 maze_analyzer.py maze.txt                  # デフォルトの閾値
python3 maze_analyzer.py maze.txt --max-dead-ends 0 # ボーナスの確認
```

### config.txt の形式

1 行に 1 つの `KEY=VALUE`。`#` で始まる行は無視されます。

| キー | 説明 | 例 |
|---|---|---|
| `WIDTH` | 迷路の幅（セル数、5 以上） | `WIDTH=20` |
| `HEIGHT` | 迷路の高さ（セル数、5 以上） | `HEIGHT=15` |
| `ENTRY` | 入口の座標 `x,y` | `ENTRY=0,0` |
| `EXIT` | 出口の座標 `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | 出力ファイル名 | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | `True` / `False` | `PERFECT=False` |
| `SEED` | 任意。同じ迷路を再現したいときに指定 | `SEED=42` |

不正な値（キーの欠落、範囲外の入口/出口、整数でないサイズ、ファイルが見つからない、など）は、
stderr に分かりやすいメッセージを出して 0 以外の終了コードで終了します。
プログラムがクラッシュすることはありません。

## 迷路生成アルゴリズム

1. **ランダム化再帰バックトラッカー**（スタックを使った反復版）が、「42」パターン用に
   予約されたセルを除くすべてのセルに対して全域木を掘ります。予約セルは構成上、
   完全に閉じたまま孤立します。`PERFECT=True` の場合は、これがそのまま最終結果です。
2. `PERFECT=False` の場合は、この全域木の上にさらに 2 つの処理を行います。
   - **ループの追加**: 隣り合うセル間でまだ閉じている壁をいくつか開き、
     独立した経路（ループ）を作ります。
   - **ブレイディング**: 残っている行き止まりの閉じた壁を 1 つ開く操作を、
     本物の行き止まりがなくなるまで繰り返します（「42」パターンに面した壁は
     開けられないため、その行き止まりは許容します）。

   どちらの処理も、完全に開いた 3x3 のセルブロックができてしまう壁の開放は拒否します
   （「幅 2 セルを超える通路を作らない」ルール）。新しい開口部を含むすべての 3x3 の窓を
   調べて判定します。

### このアルゴリズムを選んだ理由

再帰バックトラッカーは、自然に長く曲がりくねった単一経路を作る（`PERFECT=True` に向く）うえ、
拡張が簡単だからです。既存の全域木の上にループやブレイディングを足すほうが、
ループと連結性を一から同時に作るよりずっと見通しがよく、生成器全体を小さくて読みやすい
1 つのモジュールに収められます。

## 再利用できる部分とその使い方

`mazegen/` 配下のすべて（`Direction`、`Maze`、`MazeGenerator`、`MazeGenerationError`）は、
`config.txt`・出力ファイル形式・ターミナル表示のいずれにも依存せず、`(row, col)` 座標と
壁のビットマスクだけを扱います。`a_maze_ing.py`（python-dotenv で `config.txt` を読み、
出力ファイルを書く）と `display.py` はこのプログラム固有で、再利用パッケージには含めません。
パッケージ版の説明は `README_mazegen.md`（wheel/sdist に同梱）にもあります。

### 生成器のインスタンス化と使い方

```python
from mazegen import MazeGenerator

generator = MazeGenerator(width=20, height=15, seed=42)
maze = generator.generate(entry=(0, 0), exit=(14, 19), perfect=False)
```

- `entry` / `exit` は `(x, y)` ではなく **`(row, col)`** のタプルです。
- `perfect=True` は入口から出口までの経路がちょうど 1 本（ループなし）の迷路を作ります。
  `perfect=False` はパックマン風の盤面（全連結、独立した経路が 2 本以上、本物の行き止まりなし）を
  作ります。残る「行き止まり」は、孤立した「42」パターンに接するセルだけです。

### カスタムパラメータ

- `width`, `height`: グリッドのサイズ（セル数）。
- `seed`: 任意の `int`。省略するとランダムな迷路になります。その場合も、使われたシードは
  `generator.seed` / `maze.seed` で取得でき、後から再現できます。

### 生成された構造と解へのアクセス

```python
maze.walls            # List[List[Direction]] - セルごとの壁ビットマスク
maze.to_hex_rows()     # 1 行 1 文字列の 16 進数（出力ファイル形式）
maze.shortest_path()   # 入口から出口までの List[Direction]（BFS）
maze.pattern_cells     # 「42」パターンを構成するセルの frozenset
maze.warnings          # 例: "42 pattern skipped, maze too small"
```

この構造（`Maze.walls`、`Direction` ビットマスクの 2 次元リスト）は生成器の内部表現であり、
`a_maze_ing.py` が出力するファイル形式とは**同じではありません**。変換には
`to_hex_rows()` を使います。

ライセンスは MIT です。リポジトリ直下の `LICENSE.md` を参照してください。
後続プロジェクトでの再利用・配布は明示的に許可されています。

## Visual representation（表示）

### GUI（MiniLibX）

`mlx`（42 配布の `mlx-2.2-py3-none-any.whl`、Linux 専用）が入っていると、
`make run` は MLX のウィンドウで迷路を表示します。壁・入口（マゼンタ）・出口（赤）・
最短経路（シアン）・「42」パターン（オレンジ）を色分けして描きます。ウィンドウ下端に操作説明があります。

| キー | 操作 |
|---|---|
| `1` / `R` | 新しい迷路を生成して表示（出力ファイルも書き直す） |
| `2` / `P` | 最短経路の表示/非表示 |
| `3` / `C` | 壁の色を切り替え |
| `4` / `Q` / `Esc`、ウィンドウの × | 終了 |

`mlx` が無い、またはウィンドウを開けない（ディスプレイが無いなど）場合は、
自動で下記のターミナル表示に切り替わります。実装は `gui.py` です。

### ターミナル（ASCII）

ターミナルの ASCII 描画（1 セル = 2x2 文字）です。`python3 a_maze_ing.py config.txt` で実行します。

```
=== A-Maze-ing ===
1. Re-generate a new maze
2. Show / Hide the shortest path
3. Rotate the wall colours
4. Quit
Choice? (1-4):
```

短いデモ動画は `../demo.mp4` にあります（背景は `../explanation.html` を参照）。

## Team and project management（チームとプロジェクト管理）

- ソロプロジェクトです。**ssekikaw**（関川桜）が迷路のモデル、生成/ループ/ブレイディングの
  アルゴリズム、パッケージングを設計しました。実装・リンター対応・検証は AI の支援を受けて
  行いました（Resources を参照）。
- 計画: サブジェクトを読む → `REQUIREMENTS.md` を書く（データモデルと生成フローを
  Mermaid 図で記述）→ 他に依存しない `mazegen` を先に実装 → その上に config / 出力 / 表示を実装 →
  配布の `maze_analyzer.py` で、多数のサイズ・シード・PERFECT の組み合わせを検証 →
  パッケージ化とドキュメント化。検証の段階で、実際のバグ 1 件（2 つの異なる文字が同じ dict キーを
  共有していたため壁の色が回転しなかった）と、厳しすぎたテストの前提 1 件（「42」パターンに接する
  セルは行き止まりとして許容され、バグではない）が見つかりました。どちらも `../REPORT.md` に
  詳しく記載しています。
- うまくいった点: CLI より先に再利用可能な `mazegen` パッケージを書いたため、生成ロジックを
  単独でユニットテストしやすくなりました。公式の `maze_analyzer.py` を早い段階で数十通りの
  サイズ/シード/PERFECT の組み合わせに対して回したため、色のバグをレビュー時ではなく
  すぐに見つけられました。
- 改善できる点: 「42」パターンはコンパクトな 3x5 のピクセルフォントを使っており、読み取れる大きさではありますが、
  一般的な迷路サイズでは小さめです。
- 使用したツール: Python 3.11（pyenv）、flake8、mypy（`--strict` を含む）、pytest、
  `python -m build`、および仕様どおりの検証のための 42 配布の `maze_analyzer.py`。

## Resources（参考資料）

- *Mazes for Programmers*（Jamis Buck）— 再帰バックトラッカーとブレイディングのアルゴリズム。
- [Wikipedia: Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
- Python ドキュメント: `enum.IntFlag`、`collections.deque`、`typing`、
  [Packaging Python Projects](https://packaging.python.org/en/latest/tutorials/packaging-projects/)。
- **AI の利用**: このプロジェクト全体で Claude（Anthropic）を使いました。内容は、
  サブジェクト PDF の `REQUIREMENTS.md` への整理、実装（`mazegen`、`a_maze_ing.py` など）、
  配布の `maze_analyzer.py` に対して `PERFECT=True` / `PERFECT=False` の両方で多数のサイズ・シードを
  安定して通すまでの生成アルゴリズムの改善、pytest スイートの作成とデバッグ、`mazegen` パッケージの
  ビルド、このドキュメントの執筆です。生成されたコードはすべて、受け入れる前に実行し、
  リント（`flake8` / `mypy --strict`）とテストを通し、`maze_analyzer.py` と照合しました。
  検証ログと、その過程で見つかったバグは `../REPORT.md` にまとめています。
