# A-Maze-ing — 実装レポート

42 Tokyo cursus 課題 `A-Maze-ing`（`en.subject.pdf` v2.3）について、要件整理 →
実装 → 検証 → ドキュメント化までを行った記録。**このファイル自体は提出物ではない**
（`amazing/` 直下の `REQUIREMENTS.md` / `explanation.html` / `demo.mp4` と同様）。
提出物は `repo/` にある。

## 1. 何が要求されていたか

課題PDFの要点（詳細は `REQUIREMENTS.md` に Mermaid 図つきで整理済み）:

1. `python3 a_maze_ing.py config.txt` で起動する迷路生成器を Python 3.10+ で実装
2. config.txt（`KEY=VALUE`）から WIDTH/HEIGHT/ENTRY/EXIT/OUTPUT_FILE/PERFECT を読む
3. 迷路は seed で再現可能、各セルは北東南西の壁0〜4枚、entry/exitは盤面内の別セル
4. "42" 模様を除く全セルが連結、外周は壁で閉鎖、3x3以上の開けた空間は禁止
5. `PERFECT=True` は唯一経路、`PERFECT=False`（既定）は Pac-Man 用の周回可能盤面
   （四隅と中央が開通、独立経路2つ以上、行き止まりは稀＝ボーナスは0）
6. 出力ファイルは1セル1桁16進数のグリッド＋entry/exit座標＋最短経路(N/E/S/W)
7. ターミナルASCII表示＋対話操作（再生成／経路表示切替／壁色変更）
8. 迷路生成ロジックを再利用可能なpipパッケージ（`mazegen-*`）として配布
9. README.md / LICENSE.md / Makefile / .gitignore、flake8・mypyクリーン
10. すべてのエラーを握りつぶさず、分かりやすいメッセージで非クラッシュ

## 2. 何をしたか

| 成果物 | 内容 |
|---|---|
| `repo/mazegen/` | 再利用可能な迷路生成パッケージ（`Direction`, `Maze`, `MazeGenerator`） |
| `repo/a_maze_ing.py` | メインプログラム。config.txt の読み込み（python-dotenv）・必須値の確認・型変換、迷路生成の呼び出し、出力ファイル（16進数グリッド＋フッタ）の書き出し、対話表示の起動 |
| `repo/display.py` | ターミナルASCII表示＋対話メニュー |
| `repo/mazegen-1.0.0-py3-none-any.whl` / `.tar.gz` | ビルド済みパッケージ（`python -m build`） |
| `repo/README.md` / `README_mazegen.md` / `LICENSE.md` / `Makefile` / `.gitignore` | 要求されたドキュメント・設定一式 |
| `repo/tests/test_mazegen.py` | pytest（開発用、非提出・非採点） |
| `REQUIREMENTS.md` | 要件整理（Mermaidのクラス図・フローチャート付き） |
| `explanation.html` | 実装解説HTML（`_kakun_practice/learning/py00.html` のスタイルを踏襲） |
| `demo.mp4` + `demo_frame_*.png` | 実行・対話操作のデモ動画（詳細は §4） |

### アルゴリズムの要旨

1. **反復版・再帰バックトラッカー**で "42" 模様セルを除いた全セルの全域木を掘る
   （これだけで `PERFECT=True` が完成）。
2. `PERFECT=False` では、その木の上に **ループ追加**（独立経路を複数作る）と
   **ブレイディング**（残った行き止まりを解消）を重ねる。
3. どちらの操作も、壁を開ける前に該当する全ての3x3窓をチェックし、
   「3x3以上の開けた空間」を作る開放を拒否する。

## 3. 検証結果

### 3.1 静的検査

```
flake8 .                    → 0 エラー
mypy . --strict              → 0 エラー（必須フラグ構成でも0エラー）
pytest tests/ -q              → 5 passed
```

### 3.2 42提供 `maze_analyzer.py` によるスペック準拠確認

- 7サイズ（9x9, 9x7, 13x9, 20x15, 30x20, 15x13, 40x25）× `PERFECT` True/False ×
  3 seed = **42通り**すべて: PERFECT=True は `"PERFECT maze"`、PERFECT=False は
  `"Pac-Man-USABLE"` 判定で合格。
- 20x15 固定で PERFECT=False を **seed 1〜59（59通り）** 追加実行し、
  全て `Pac-Man-USABLE` かつ **real dead-ends = 0**（`--max-dead-ends 0` のボーナス
  条件）を達成。
- 5x5（"42"模様が入らない極小サイズ）で、模様を省略しコンソールに警告を出すことを確認。
- 設定エラー系（ファイル無し／必須キー欠落／entry=exit／座標範囲外／WIDTH非整数／
  `=` の無い行／引数無し）が全て非クラッシュ・分かりやすいメッセージ・非ゼロ終了に
  なることを確認。
- `mazegen-1.0.0-py3-none-any.whl` をクリーンな venv に単体インストールし、
  `from mazegen import MazeGenerator` だけで動作することを確認。

### 3.3 発見したバグ・誤りとその修正

1. **実バグ：壁色ローテーションが機能していなかった。**
   `display.py` で "42" 模様セルの描画文字を壁と同じ `"#"` にしていたため、
   色パレット辞書 `{_WALL: wall_color, _PATTERN: ...}` で **キーが衝突**し、
   後勝ちで全ての `#`（壁もパターンも）が常にパターン色（青）になっていた
   （メニュー「3」が実質何もしていなかった）。
   → `_PATTERN` を別文字 `"@"` に変更して解決。実際にレンダリング結果を
   `re.search` で色コードを突き合わせて確認してから直した。
2. **テストの誤り（本物のバグではない）：** 初版の pytest は「開口部が1つのセル」を
   単純に「行き止まり」としてカウントしており、"42"模様に隣接するため原理的に
   開けられないセル（`maze_analyzer.py` の `enclosed` 扱い）まで「行き止まり」に
   数えてしまい、seed=7 で誤って失敗していた。42提供の analyzer の「real vs
   42-enclosed」の区別をテストにも反映して修正。生成アルゴリズム自体は元から
   正しかった（analyzer 本体で確認済み）。

## 4. デモ動画について（補足）

ユーザー指示の `/ego-e2e-kit:e2e-shot` を実際に起動したところ、このスキルは
**ego-browser（ブラウザ）経由のWebアプリE2Eテスト専用**で、対象URL/ポートの
入力を前提としていた。本課題はターミナルCLIでありURL/ポートを持たないため、
このスキルは適用できなかった。

代替として、以下の自前パイプラインで実際の実行・対話操作を記録した:

1. `pexpect` で `python3 a_maze_ing.py config.txt` を疑似端末越しに駆動し、
   「1:再生成→2:経路表示→3:色変更→3:色変更→2:経路非表示→4:終了」を
   実際に送信、生の出力（ANSI含む）を1本のログに記録。
2. `pyte` でそのログを端末バッファとして再生し、各操作の区切りごとに
   `Pillow` でPNGフレームを書き出す（キャプチャと描画を分離することで、
   最初に試した「キャプチャ中にその場で描画する」版で発生したブロッキングの
   問題を回避した）。
3. `ffmpeg` でPNG連番を `demo.mp4` にエンコード。

最初に書いたキャプチャ+描画を同時に行うバージョンは120秒経っても終了せず
（`select`ループ内でのPIL描画がpty読み出しを圧迫し、子プロセスの出力がブロック
したとみられる）、バックグラウンドタスクごと停止して上記の2段階方式に書き直した。

### 4.1 `/ego-e2e-kit:e2e-shot` 自体の実行結果

上記の判断で終わらせず、`/ego-e2e-kit:e2e-shot` を改めて正式に最後まで実行した。
テスト対象を「ターミナルCLI」ではなく、同スキルが本来対象とする**Webページ**、
すなわち要件4で作成した `explanation.html`（このHTML自体がプログラムの実行結果
と対話操作を統合した成果物）に据え、`doctor.sh` での依存確認→設定確認→
テストケース宣言→ego-browserでの実操作・スクリーンショット→報告、という
スキルの手順をそのまま踏んだ。

- 対象: `file://.../amazing/explanation.html`（ローカルファイル、ポート不要）
- テストケース: 「実装解説HTMLが要件4通り正しく表示・操作できるか」
- 前提条件: ローカルファイルのみで完結（外部依存は mermaid CDN のみ、SRI付き）

| ID | エッジケース | 確認方法 | 結果 |
|---|---|---|---|
| 1 | データモデルの Mermaid classDiagram が描画される | `document.querySelectorAll('.mermaid svg')` の数 | ✅ 2件中1件目がSVG化 |
| 2 | 生成アルゴリズムの Mermaid flowchart が描画される | 同上2件目 | ✅ |
| 3 | デモ動画 `<video>` が再生可能な状態まで読み込まれる | `video.readyState` | ✅ `4`（HAVE_ENOUGH_DATA） |
| 4 | 起動直後/経路表示のスクリーンショット2枚が読み込まれる | `img.complete && naturalWidth>0` | ✅ 2/2 |
| 5 | 要件対応表・検証結果表が描画される | `table` 要素数 | ✅ 2件 |
| 6 | 目次(TOC)リンクが9個あり、クリックで該当セクションへ遷移する | `.toc a[href='#verify']` クリック→`#verify`のbounding rect | ✅ viewport内に遷移 |
| 7 | 注意書き(note)ボックスが表示される | `.note` 要素数 | ✅ 3件 |
| 8 | モバイル幅(390px)でもレイアウトが崩れない（横スクロール無し） | CDP `Emulation.setDeviceMetricsOverride` 390x844 → `scrollWidth`/`clientWidth` | ✅ 差分0、`.layout`が1カラムに切替（スクショ`e2e_03_mobile_top.png`） |
| 9 | モバイル幅で表（§7検証結果）が横に溢れない | 同条件でのスクリーンショット | ✅ 縦積みで収まる（`e2e_04_mobile_table.png`） |
| 10 | ページ読み込みでコンソールエラー/例外が出ない | `Runtime.consoleAPICalled`(error/warning) と `Runtime.exceptionThrown` を再読み込みして収集 | ✅ 0件/0件 |

根拠スクリーンショットは `amazing/e2e_evidence/`（`e2e_01_toc_nav.png`,
`e2e_02_demo_section.png`, `e2e_03_mobile_top.png`, `e2e_04_mobile_table.png`）
に保存。全10ケース合格、不具合は見つからなかった。

**`e2e-shot` 自身から作ったTEST動画**: `e2e-shot` はスクリーンショットまでしか
作らない（動画合成機能を持たない）ため、上記検証で実際に撮影した9枚の
スクリーンショット（起動直後／アルゴリズム図／デモ動画セクション／コード・解説
タブ切替／TOC遷移後／モバイル幅2枚 ほか）を `ffmpeg` の concat demuxer で
そのまま時系列に結合し、`amazing/e2e_shot_video.mp4`（28.5秒）として書き出した。
中身は `e2e-shot` が実際に見た画面そのものなので、「`e2e-shot` を使ってTEST動画を
作成する」という要求に対して最も文字どおりの対応になる。

結論: `/ego-e2e-kit:e2e-shot` は「ブラウザで動くもの」専用のため、ターミナルCLI
本体の動作確認には使えなかったが、要件4のHTML成果物に対しては指示どおり正式に
実行し、全項目で合格を確認したうえで、その実撮影スクリーンショットからTEST動画
（`e2e_shot_video.mp4`）も作成した。CLI自体の実行確認は §3.2（`maze_analyzer.py`
による42通り+59通りの自動検証）および §4 冒頭のデモ動画（`pexpect`/`pyte`/
`ffmpeg`による実セッション録画）で担保している。

### 4.2 `ego-e2e-kit:test-mov` による正式なTEST動画の作成

§4.1 の検証を終えたあと、同じ `ego-e2e-kit` プラグインに **動画そのものを作る
姉妹スキル `ego-e2e-kit:test-mov`** が同梱されていることに気づいた
（`e2e-shot` はスクリーンショットのみで動画は作らない）。これはVOICEVOX音声・
字幕・注目箇所の赤枠を自動合成した1ケース1本の動画を作るスキルで、
「TEST動画を作成すること」という要求により正確に合致する。

依存（`ego-browser` / `ffmpeg` / `ffprobe` / `VOICEVOX`）を `doctor.sh mov` で
確認したうえで、`explanation.html` を対象に `scenario.json` を8ステップ分書き、
`ego-e2e-kit:test-mov` の `make.sh` で実際に動画を生成した。

- 対象: `file://.../amazing/explanation.html`
- 8ステップ：①タイトル/バッジ ②要件対応表 ③データモデル(Mermaid) ④生成アルゴリズム
  (Mermaid) ⑤コード/解説タブの切替 ⑥デモ動画セクション ⑦検証結果表 ⑧再利用パッケージ
- 各ステップで赤枠が対象要素を正しく囲んでいるか、期待する文言(`expect`)が
  実際に画面に出ているかを自動判定
- 実行結果: `{"verdict":"pass","failed":[],"missing":[],"frames":189}`
  （全8ステップの `expect` が合格、赤枠の対象も全て見つかった）
- 成果物: `amazing/e2e_test.mp4`（48秒、VOICEVOXナレーション「春日部つむぎ」
  ・字幕トラック付き）。仕上がりは `sheet.png`（各ステップの最終フレーム一覧）
  で目視確認し、字幕が赤枠や重要情報を隠していないことを確認済み。

この動画を `explanation.html` の §6 に埋め込み、CLI実演の `demo.mp4` と並べて
掲載した。

## 5. 要件チェックリスト（最終確認）

| 要件 | 状態 |
|---|---|
| Python3.10+ / flake8 / 例外処理 / 型ヒント+mypy / docstring | ✅ |
| Makefile（install/run/debug/clean/lint/lint-strict） | ✅ |
| `python3 a_maze_ing.py config.txt` | ✅ |
| config.txt 必須6キー＋コメント無視 | ✅ |
| エラーを握りつぶさず明確なメッセージ | ✅（§3.2で確認） |
| seedで再現可能な乱数生成 | ✅（pytestで同一seed→同一迷路を確認） |
| 各セル0-4枚の壁、矛盾しない符号化 | ✅（壁開放は両側同時操作） |
| entry/exit: 存在・別・盤面内、外周は壁 | ✅ |
| "42"模様以外は全連結、孤立なし | ✅（analyzerで`disconnected_corridors=0`確認） |
| 3x3以上の開けた空間禁止 | ✅（`_would_make_big_room`） |
| "42"模様、入らない場合は省略+警告 | ✅（5x5で確認） |
| PERFECT=True: 唯一経路 | ✅（analyzerで`loops=0`確認） |
| PERFECT=False: 連結・四隅中央・ループ2+・行き止まり稀 | ✅（`Pac-Man-USABLE`判定） |
| 出力ファイル形式（16進数/空行/entry/exit/経路/全行\n） | ✅ |
| ターミナルASCII表示 | ✅ |
| 対話操作（再生成/経路表示/色変更） | ✅（デモ動画で実演） |
| 再利用可能クラス＋pipパッケージ＋ドキュメント | ✅（`mazegen`, `README_mazegen.md`） |
| LICENSE.md（再利用許諾を明記） | ✅（MIT） |
| README.md 必須記載事項一式 | ✅ |
| （ボーナス）行き止まり0の盤面 | ✅（59/59 seedで達成） |

## 6. 未実施・スコープ外にしたこと

- MLXによるグラフィカル表示は実装していない（課題はASCII/MLXの**どちらか**を
  要求しており、ASCIIを選択）。
- `repo/` は独立したGitリポジトリとして初期化し、初回コミット（19ファイル）を
  作成済み（`git log --oneline` で確認可能）。remoteは未設定。42のvogsphereから
  払い出される専用リポジトリが発行され次第、それを `origin` として接続・pushする
  想定（`py00` 等、他のcursus課題と同じ運用）。
