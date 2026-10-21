# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発ルール

**このセクションは他のすべてのセクションに優先する。作業を始める前に必ず読むこと。**

### 正式な情報源

**リポジトリ内のドキュメントを唯一の正式な情報源とする。**
過去の会話や記憶よりも、以下を常に優先する：

- `CLAUDE.md` および `docs/specs/` 配下の対象仕様書
- `docs/pision_cloud_notes.md`
- Git履歴
- 現在のコード

会話の記憶は資料の代替にならない。正式仕様・既知問題・禁止事項はすべて上記に記録されている。

### 作業開始時の確認順序

作業を始めるときは、必ずこの順番で確認してから回答・実装する：

1. `CLAUDE.md` および `docs/specs/` 配下の対象仕様書（対象機能に対応するもの）
2. `docs/pision_cloud_notes.md`
3. Git履歴（必要に応じて `git log` / `git blame` / `git diff`）
4. 現在のコード

### 基本ルール

- **推測で実装しない。**
- **過去仕様へ勝手に戻さない。**
- **Git履歴と資料を優先する。**
- 不明点は**まず資料とGit履歴を確認**し、それでも分からない場合だけユーザーへ確認する。

### 未コミット状態でアプリを動かしたまま検証しない（2026-08-10 確定・`55e7752`）

**このリポジトリはアプリ自身が `git stash` / `--autostash` を実行する。**

- `_git_auto_pull()`（streamlit_app.py 2650行・`main()` からセッション1回）＝
  `git stash` → `git pull --rebase` → `git stash pop`
- `_git_auto_push()`（2672行・保存/画像生成のたび）＝ `git pull --rebase --autostash`

この数秒の窓では**作業ツリーが HEAD へ戻る**。**Streamlit は rerun のたびにスクリプトを
読み直す**ため、窓に入った rerun は**HEAD版（＝修正前）のコードで実行される**。
その結果、未コミットの修正は「ファイルには存在するのに効かない」状態になり、
旧コードが設定JSONを壊し続ける（2026-08-10 に⑤の機種名が3回全消しされた事故の真因）。

**運用ルール：**
1. 保存系バグの修正を実機確認するときは、**未コミットのままアプリを動かし続けない**
2. 手順は必ず **アプリ停止 → コードのみ先にコミット → 設定データ復元 → 再起動 → 実機確認**
3. **「データ復元 → その後コミット」の順にしない**（復元した値が stash 窓の旧コードで再び壊れる）
4. `_git_auto_push()` の対象には **`store_settings` が含まれる**。壊れた設定JSONが
   そのまま commit / push され Cloud へ伝播し得るので、破壊を検知したら**まずアプリを停止**する
5. reflog の `reset: moving to HEAD` は stash/autostash の痕跡。設定JSONが壊れた時刻と
   突き合わせると、この経路かどうかを判別できる

### 大きな変更の手順（必須）

以下の順序を必須とする。**ユーザー承認より前に実装しない。**

1. 調査
2. 原因報告
3. 最小修正案
4. ユーザー承認
5. 実装
6. ローカル確認
7. コミット
8. push
9. 結果報告

### コミット前

- **ローカル確認必須。**
- **不要な変更を含めない**（対象ファイルのみをコミットする）。

### コミット後

必ず以下を報告する：

- コミットID
- 変更ファイル
- 変更内容
- push結果
- GitHub main HEAD
- Cloudへの影響
- 確認結果

## アプリの起動

```
cd C:\Users\23-3\Desktop\画像作成
py -3.14 -m streamlit run streamlit_app.py
```

構文チェック：
```
py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"
```

依存ライブラリのインストール：
```
py -3.14 -m pip install -r requirements_streamlit.txt
```

ファイル編集後は必ず構文チェックを実行すること。Edit ツールで日本語を含むファイルを編集する際、Unicode 文字列の完全一致が取れない場合は `py -3.14 - << 'PYEOF'` 形式の Python スクリプトで直接書き換える。

## Streamlit 再起動手順（Windows）

1. 起動中のターミナルで `Ctrl + C` を押して停止する
2. 止まらない場合は別のコマンドプロンプトで以下を実行する：
   ```
   netstat -ano | findstr :8501
   ```
3. 表示された一番右の PID 番号を使って強制終了する：
   ```
   taskkill /PID PID番号 /F
   ```
4. 再起動する：
   ```
   cd C:\Users\23-3\Desktop\画像作成
   py -3.14 -m streamlit run streamlit_app.py
   ```

**注意：** Streamlit 再起動後は必ずブラウザを F5 でリロードすること。`!` コマンドは Windows の通常のコマンドプロンプトでは使用できない。

## 画像が更新されない場合の対応

既存の PNG/JPG は自動上書きされないことがある。出力フォルダの古い画像を削除してから再生成すること。

```
del C:\Users\23-3\Desktop\画像作成\機種別\*.jpg
del C:\Users\23-3\Desktop\画像作成\機種別\*.png
```

またはエクスプローラーで該当フォルダを開いて `Ctrl+A` → `Delete` で削除してから、アプリ上で再生成を実行する。

## アーキテクチャ概要

### メインアプリ（streamlit_app.py）

全機能を1ファイルに集約した Streamlit アプリ。PIL で画像を直接生成する（旧スクリプトは Playwright + dataframe_image を使用）。

**ファイル内のセクション構成（コメントの■番号に対応）：**

| セクション | 内容 |
|-----------|------|
| ①設定データ | `STORES`、`IMAGE_CONDITIONS`、`COLUMN_ALIASES`、`DEFAULT_STORE_CONFIG`、`MIN_COL_WIDTHS` |
| ②デザイン定数 | 色定数（`C_*`）、`ROW_H`、`HEADER_H`、`TITLE_H`、`IMG_FONT_SZ` など |
| ③フォント | `load_font()` — MochiyPopOne → Meiryo → MSゴシック の優先順 |
| ④データユーティリティ | `normalize_df()`、`load_name_map()`、`fmt_diff()` など |
| ⑤テーブル描画 | `draw_table_image()` — 全画像種に共通の PIL 描画エンジン |
| ⑥画像ハンドラー | `generate_全台データ画像()` など4種の手動生成関数 |
| ⑦ハンドラーマップ | `IMAGE_HANDLERS` dict |
| ⑧Streamlit ページ | `show_store_page()` / `show_image_type_page()` / `show_work_page()` / `show_auto_page()` / `main()` |

### 自動処理パイプライン（run_auto_pipeline）

Excel 1ファイルから3ステップで全画像を生成する：

- **Step 1** (`run_step1_main`) — 全台系 PNG（全台データ）＋ 全台プラス機種別 JPG
- **Step 2** (`run_step2_juggler`) — ジャグラーシリーズ優秀台 JPG（台数が少ない機種は Step3 へ overflow）
- **Step 3** (`run_step3_other`) — 非ジャグラーの高配分・その他の優秀台ピックアップ JPG

各 step 関数はデータを収集して戻り値に含め、`run_auto_pipeline` が集約して `generate_report_text()` に渡す。

### 機種別画像の生成フロー（_build_machine_img）

1. `draw_table_image()` でテーブル部分（タイトル・ピンクバーなし）を描画
2. PIL で青タイトルバー（BAR_H=62px）＋赤ライン（LINE_H=6px）を結合
3. ピンクサマリーバーを追加（`summary_stat` が None なら省略）
4. `_save_jpeg()` で 250KB に近い品質の JPEG に保存

### 画像サイズの設計方針

`draw_table_image()` は `scale=150/96≈1.5625` を掛けて旧 Playwright（DPI=150）と同寸法にする。

- `MIN_COL_WIDTHS` の値は CSS の `content幅 + padding(8px×2=16px)` の合計。`scale` 倍した値が最小列幅（ピクセル）。`0` にすると自動（テキスト幅で決定）。
- `ROW_H` / `HEADER_H` は CSS 相当値（`× scale` で実ピクセルになる）。
- `BAR_H` / `LINE_H` は `_build_machine_img` 内でのみ使われ、スケールなし（絶対ピクセル）。

## 主要な設定場所

新機種・新店舗の追加や判定条件の変更はすべてファイル先頭の設定セクションで行う：

- **店舗追加** — `STORES` と `STORE_CONFIG` の両方に追記
- **ジャグラー機種追加** — `DEFAULT_STORE_CONFIG["juggler_jobs"]`（機種名, 合算確率閾値, 差枚ボーナス）
- **個別画像を作らない機種** — `DEFAULT_STORE_CONFIG["manual_exclude"]`（1000枚以上のみ「その他」へ）
- **店舗別並びスクリプト** — `STORE_NARABI_SCRIPT`

<!-- CLAUDE-SPLIT-KEEP-END -->
## 仕様書の参照ルールと仕様目次

### 仕様書の参照ルール

- 2026-10-21 に正式仕様の本文を `docs/specs/` 配下へテーマ別に移した。各節は旧 CLAUDE.md から1文字も変えずに機械的に切り出している。
- **作業前に、対象の機能・ページ・店舗に対応する `docs/specs/` の仕様書を必ず読む。**複数にまたがる場合は該当するものをすべて読む。どれに当たるか分からないときは `docs/specs/README.md`（全節索引）で探す。
- 仕様書の `VERBATIM-BEGIN` 〜 `VERBATIM-END` の間は正式記録の原文。**書き換え・要約・統合・削除をしない。**
- 新しい正式仕様は、対象の `docs/specs/` ファイルの末尾（マーカーの外）へ追記し、下の目次と `docs/specs/README.md` も更新する。
- 分割が原文と完全一致していることは `py -3.14 tools/verify_claude_split.py` で確認できる。

### 仕様目次

| ファイル | 対象 |
|---|---|
| [`docs/specs/cloud_infra.md`](docs/specs/cloud_infra.md) | Cloud↔GitHub同期・store_settings運用・機種画像/機種名変換の同期・packages.txt・未知pageの無限rerun |
| [`docs/specs/top_ui_tools.md`](docs/specs/top_ui_tools.md) | ページ遷移・トップ／スマホメニュー・おすすめ・本日の仕事・機能選択ボタン・サイドバー・機種名変換 |
| [`docs/specs/input_persistence.md`](docs/specs/input_persistence.md) | auto_page_inputs.json・②個別画像の日付単位保存・⑤オススメの永続化・初期値の受け渡し・同日再取得 |
| [`docs/specs/result_extraction.md`](docs/specs/result_extraction.md) | 判定条件・旧スクリプト・②全台除外・📝記入部分のみ・🎯掲載台を選ぶ・その他／ジャグラーの再振り分け・_dedup_previews |
| [`docs/specs/narabi_retsu.md`](docs/specs/narabi_retsu.md) | 列画像・列仕掛けの表記と除外・並び記入枠・⑧列画像の補正後差枚 |
| [`docs/specs/result_images.md`](docs/specs/result_images.md) | 表画像デザイン・スランプグラフ・液晶はめ込み／停止・#FFFFCB背景・side画像・青タイトルバー・パネル対象・手入力画像のスランプ |
| [`docs/specs/result_text.md`](docs/specs/result_text.md) | 結果テキストの記号・表記・新小岩⑤・新大久保はにぃポスト・渋谷新館オススメポスター |
| [`docs/specs/result_post_stores.md`](docs/specs/result_post_stores.md) | 新宿歌舞伎町3系統・新小岩⑤ジャグラー・稲毛/新小岩/3店舗のslotterguild取得・gap猫撤去・マイジャグVI・ジャグラー閾値記憶 |
| [`docs/specs/rote.md`](docs/specs/rote.md) | ローテ画像・ランキング・週間／月間オススメ表・ローテ結果テキスト・渋谷新館／新宿歌舞伎町ローテ |
| [`docs/specs/article_common.md`](docs/specs/article_common.md) | 記事用の共通処理・HQ化・⑧再実行・日付切替保存（B2）・2F/3F・高配分と末尾の重複・記事コメント同期 |
| [`docs/specs/article_takadanobaba.md`](docs/specs/article_takadanobaba.md) | 高田馬場の記事用ページとWordPress下書き連携 |
| [`docs/specs/article_shibuya_page.md`](docs/specs/article_shibuya_page.md) | 渋谷新館の記事用ページ・⑤オススメ・⑥ランキング／全台データ・パネル・液晶 |
| [`docs/specs/article_shibuya_wp_comment.md`](docs/specs/article_shibuya_wp_comment.md) | 渋谷新館のWordPress下書き・本文構成・ななこ/ギルドX・投稿者・記事コメント |
| [`docs/specs/article_kabukicho.md`](docs/specs/article_kabukicho.md) | 新宿歌舞伎町の記事用ページ・画像・WordPress・記事コメント・ポスター |
| [`docs/specs/other_yg.md`](docs/specs/other_yg.md) | その他配下（プレサス飯田橋・BEAM新井薬師・ラ・カータ鶴ヶ島）・YG用店舗・YG一覧・YG画像デザイン |
