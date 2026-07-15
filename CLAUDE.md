# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## 判定条件（2026-05-22 現在）

### 全台系（Step1）
以下を**すべて**満たす場合のみ機種別 JPG を生成：
1. 全台が「+1,000枚以上」または「G数 ≥ 2,000G かつ差枚プラス」のいずれかを満たす（台単位の判定）
2. 2台以上

### 高配分（Step3）
- マスク：`差枚 >= 1000`（G数・RB 不問）
- 生成条件：`+1000枚台数 >= max(2, ceil(総台数 / 2))`
  - 2台機種は両方が 1000枚以上の場合のみ（1台だけでは生成しない）

## 旧スクリプト群

`convert_20260408.py` が基準スクリプト（上野新館）。店舗日付ごとに派生スクリプトが存在するが、すべて Playwright + `dataframe_image` を使用する旧方式。新規・修正スクリプトは `convert_20260408.py` のスタイルに合わせる。

- `convert_narabi_*.py` — 台並び画像。`RANGES = []` で自動検出、直接指定も可。`_patch_and_run_narabi()` 経由で Streamlit アプリから subprocess 実行される。
- `convert_suebangai.py` — 末尾番台画像。`TAIL_DIGIT` を変えるだけで対応する末尾を変更できる。
- `convert_filter_batch.py` — 高配分フィルター一括生成（旧方式）。
- `convert_1000plus_test.py` — 1000枚以上優秀台ピックアップ（旧方式）。

並び・末尾画像はオンデマンド生成（通常の自動フローには含めない）。

## Streamlit ページ遷移

`st.session_state.page` でページを管理し `st.query_params` に同期することでブラウザの戻る/進むボタンを有効化している：

```
store（店舗選択）→ image_type（画像種類選択）→ work（個別生成）
                                              → auto（一括自動処理）
```

`_navigate()` でページ遷移、`_sync_from_query_params()` で URL から状態復元、`popstate` イベントリスナー（`components.html` 経由）でブラウザ履歴と連動。

**ブラウザの戻る/進む/Alt＋←/マウスの戻る・進むでページ遷移できることは正式仕様**（2026-07-15・`31c2dcb`）。popstate は `main()` の**既存 autocomplete 用 components.html に統合**されており、**新しい components.html は追加しない**。popstate 処理で行ってよいのは `window.parent` への popstate 登録・二重登録防止フラグ・`location.reload()` のみで、親DOM操作／`removeChild`／`MutationObserver`／Streamlit内部DOM操作は禁止。

過去に removeChild 対策で popstate を撤去して戻る/進むが壊れた経緯があるため（真因は autocomplete 側の MutationObserver）、**同じ理由で再撤去しないこと**。ページ遷移まわりを変更する際は必ずこの実装との互換性を確認する。詳細は `docs/pision_cloud_notes.md` の「ブラウザ履歴対応（正式仕様）」を参照。

## 機種名変換

`機種名変換.xlsx`（2行目をヘッダーとして読み込む、B列=変換前, C列=変換後）を `load_name_map()` でキャッシュ。完全一致 → 正規化一致（スペース・全角除去）の順で変換。`@st.cache_data` でセッション中は再読み込みしない。
