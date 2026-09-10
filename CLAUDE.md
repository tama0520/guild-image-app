# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 開発ルール

**このセクションは他のすべてのセクションに優先する。作業を始める前に必ず読むこと。**

### 正式な情報源

**リポジトリ内のドキュメントを唯一の正式な情報源とする。**
過去の会話や記憶よりも、以下を常に優先する：

- `CLAUDE.md`
- `docs/pision_cloud_notes.md`
- Git履歴
- 現在のコード

会話の記憶は資料の代替にならない。正式仕様・既知問題・禁止事項はすべて上記に記録されている。

### 作業開始時の確認順序

作業を始めるときは、必ずこの順番で確認してから回答・実装する：

1. `CLAUDE.md`
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

## 判定条件（2026-07-16 現在）

### 全台系（Step1）
以下を**すべて**満たす場合のみ機種別 JPG を生成：
1. 全台が「+1,000枚以上」または「G数 ≥ 2,000G かつ差枚プラス」のいずれかを満たす（台単位の判定）
2. 2台以上

### 高配分（Step3）
- マスク：`差枚 >= 1000`（G数・RB 不問）
- 生成条件：`+1000枚台数 >= max(2, ceil(総台数 / 2))`
  - 2台機種は両方が 1000枚以上の場合のみ（1台だけでは生成しない）

### ⑤オススメ機種ピックアップ（2026-07-16）

**抽出条件「プラス台」は全機種を差枚のみで抽出する（差枚 >= 1）。**
以前はジャグラーだけ「G数 ≥ 2,000 かつ（合算確率 ≤ 閾値 かつ 差枚 ≥ 0）または 差枚 ≥ 1,000」に
絞る専用分岐があったが廃止した（全店舗一律）。「+1,000枚以上」「+2,000枚以上」は元から差枚のみ。
`generate_recommended_block_image()` は `差枚 >= min_diff` の一本道で、`juggler_cfg` 引数は無い。
Step1/Step2/Step3・末尾画像のジャグラー条件は**変更していない**。

**⑤登録機種の抑制ルールは店舗・ページで異なる：**

| 対象 | ⑤登録機種の扱い |
|---|---|
| 通常（全店舗・既定） | ⑤登録を理由に高配分・ジャグラー優秀台の**画像と結果テキストを抑制**し、⑤ブロックへ載せる。全台系（Step1）は⑤を見ないので画像を生成し、`filter_recommended_machines()` が⑤ブロックから機種を外す |
| **新小岩のスランプ付き結果ポスト用のみ** | `_rec_ban_level = with_slump and store == "新小岩"`。⑤登録を理由に**何も抑制しない**（全台系・高配分・ジャグラー画像・結果テキストすべて通常判定）。自動生成画像へ**実際に掲載された台番だけ**を⑤ブロックから**台番単位**で除外する |

新小岩スランプ付きでは⑤は「自動画像に掲載されなかったオススメ機種の優秀台を拾う補完枠」。
⑤ブロックが0台・画像なしになるのは**正常**（自動画像が多い日はB3ジャグラーが空になる）。
⑤機種を通常の「その他の優秀台ピックアップ」へ流さないのは `sonota_exclude` で維持する。
②個別画像・②個別優秀台ピックアップによる抑制は**全店舗・全ページで従来どおり維持**する。

**注意**: `recommended_machines` は ⑤ ∪ ②個別画像 ∪ ②個別優秀台ピックアップ の**マージ集合**。
Step1〜3は区別できないため、⑤だけを外したいときは呼び出し側（`_rec_names` 構築）で分離する。

## 高田馬場 記事用ページの正式仕様（2026-08-04 確定）

以下を**正式仕様**として扱う。仕様変更時はこの節を更新し、**旧仕様へ巻き戻さない**。
関連コミット: `0df63dd` / `101ac8f` / `eb4ab7f` / `efb7f43`

### ① パネル画像

記事用の「表＋スランプ」画像でも通常ページと同じパネル合成仕様を使う。

- 合成順は **表 → パネル → スランプ → 液晶**
- パネル合成時に **crop しない**（`_apply_panel_to_table_img(crop_bar=False)`）。表・ヘッダー・先頭台番を欠けさせない
- **ジャグラーシリーズ優秀台・その他の優秀台ピックアップは末尾画像と同じ 2×2 パネル**
  （`_art_is_multi_machine()` で複数機種画像と判定。かぶぱは `is_multi` 既定 False で従来どおり）
- パネルの**表示順は掲載機種の最小台番昇順**（`_build_variety_panel_grid(order_by_min_ban=True)`）。
  採用機種の**選定条件は差枚上位のまま変更しない**

### ② 並び画像

記事用の並び画像は**生成段階で青タイトルバーなし**（`convert_narabi_pil.py` の `NO_BAR`）。
**生成後に crop して消す方法は禁止**。通常ページは `NO_BAR = False` のまま。

### ③ 末尾画像

記事用も通常ページと同じ仕様。通常末尾3枠／ジャグラー末尾3枠／モード5種／パネル／スランプ／
液晶／結果テキスト。抽出は共通関数 `_build_sue_images()`（通常ページと共用）。

### ④ 末尾除外

末尾画像へ掲載した台は **その他の優秀台・ジャグラーシリーズ優秀台・高配分・バラエティ**から除外する。
通常末尾（`suebangai_tails`）とジャグラー末尾（`jug_suebangai_tails`）は独立。
**🔄その他を更新も同仕様**（OFF台・末尾台を復活させない）。

### ⑤ 結果テキスト

記事用も通常ページと同じ末尾結果テキストを出力する。挿入位置は
**並び → 👑優秀末尾 → 👑バラエティ → 🎁その他**。書式・集計方法は共通
（`_compute_sue_stats_for()` / `suebangai_section()`）。
**サマリーは元データ基準**、**+1,000枚以上の一覧だけ**が掲載台に連動する。

### ⑥ 高解像度画像（高田馬場の記事用のみ）

- `ジャグラーシリーズ優秀台.jpg` / `その他の優秀台ピックアップ.jpg` は**常に2倍**
- さらに**掲載台10台以上**の画像（全台系・高配分・末尾・ジャグラー末尾・バラエティ・並び）も
  **2倍描画＋約1200KB保存**
- 定数: `_ART_HQ_SCALE = 2.0` / `_ART_HQ_MIN_ROWS = 10` / `_ART_HQ_TARGET_KB = 1200`。
  並びは `convert_narabi_pil.py` の `HQ_SCALE` / `HQ_MIN_ROWS`
- **最後に resize で拡大するのは禁止**。表・文字・罫線・スランプを最初から2倍で描画する
- 判定は「候補台数」ではなく **🎯適用後の掲載台数**（描画＝DataFrame行数／合成＝ban_mapの台数）。
  ⑦プレビュー・🔄更新・⑧本番・液晶再合成・ZIP で同じ倍率になる
- 通常ページ・他店舗は従来仕様（既定 1.0）。Cloud のメモリが厳しい場合は
  `_ART_HQ_MIN_ROWS` を引き上げて調整する

### ⑦ 記事用の 🎯 掲載台を選ぶ

対象は **高配分／ジャグラーシリーズ優秀台／その他の優秀台／通常末尾／ジャグラー末尾**
（既存の②個別優秀台 `art_kojin`・⑤バラエティ `art_variety` は従来どおり）。

- 記事用専用 kind **`art_high` / `art_juggler` / `art_sonota` / `art_suebangai`** を使い、
  通常ページの `high` / `juggler` / `sonota` / `suebangai` と session_state を混在させない
- **pipeline は無変更**。`_art_pipeline_exclude(state)` が読み取り専用の投影 dict を
  `exclude_units=` へ渡す。末尾は `_build_sue_images(exclude_kind="art_suebangai")`
- OFF台は 表・パネル選定・スランプ・液晶・ban_map・ZIP・結果テキストの+1,000枚一覧へ反映。
  **サマリー集計・候補判定・重複除外は掲載台選択前の正式データ基準を維持**
- 全台OFF は画像を生成せず、古い同名画像を削除し、**孤児パネルから復帰可能**

### ⑨ ②個別画像（2026-08-05 確定・`b694d7e`）

**巻き戻し禁止。**

- **②個別画像「全台」へ入力した機種は、自動全台系（Step1）で生成しない。**
  `run_step1_main()` / `run_auto_pipeline()` の引数 `kojin_zentai_machines`（既定 `set()`）で
  **候補段階から除外**する。生成後の重複除去で対処しない（`_dedup_previews` を代替に使わない）。
  渡すのは**記事用の⑦プレビュー・⑧本番の2か所だけ**。
  **`recommended_machines` は流用しない**（⑤オススメ・②個別優秀台の全台系まで全店舗で消えるため）。
  これで ⑦・🔄・⑧・ZIP・ban_map・`zen_dai_list`（結果テキストの👑全台系濃厚機種）が
  すべて②個別側の1件へ揃う。
  Excel に該当台が無い場合は `continue` の**前**に既存の `_rm_stale_image()` で古い同名画像を削除する
  （②個別が生成する経路では削除しない）。
- **②個別画像「優秀台」は青タイトルバーを描画しない。**
  ⑦・⑧とも **`_build_machine_img_no_bar()`** を使う（Step2／Step3／その他の優秀台の
  `article_mode` と同じ扱い）。**生成後の crop は禁止**。
  **クラウン＋機種名＋勝率/総差枚/平均のサマリーエリアは追加しない**
  （それは②個別「全台」の `_build_article_machine_img()` の仕様）。
- 通常ページの優秀台画像は**従来どおり青バー付き**（`_build_machine_img`）。
- 画像名・保存先・高解像度判定・ban_map・パネル・スランプ・液晶・🎯掲載台選択は無変更。

### ⑧ 横版（`_side.jpg`）

通常ページ・かぶぱポストが対象（**記事用に `_side.jpg` は作らない**）。

- 縦版と横版は**同じ正式キーを共有**する。`_unit_ex_img_key()` / `_gap_sel_key()` は**変更しない**
- 🎯掲載台選択・液晶選択は縦版と横版で共有。**横版専用の🎯UIは作らない**（縦版側に1つだけ）
- 全台OFF では **縦版・横版・`NN_` 付き**を共通ヘルパー `_rm_stale_image(output_dir, base_fn, log)`
  で削除する（連番除去後の**完全一致のみ**。部分一致・曖昧一致は禁止。
  `_kabupa_rm_stale()` はこのヘルパーへ委譲）
- **🔄その他を更新後は横版の `_gap_base` も更新**（更新後の表・スランプへ差し替え／
  空きが2コマ未満なら base を外す）。液晶を選び直しても更新後の状態を維持する
- 横版の生成条件（**16台以上・秋葉原は横版なし**）と、縦版・横版の「生成する」チェックの
  独立制御は変更しない

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

## Cloud ↔ GitHub 同期の正式仕様（2026-08-05 確定・`f3ff59c`）

`weekly_items.json` / `rote_machines.json` の Cloud 側同期は以下を**正式仕様**とする。
**巻き戻し禁止。**関連コミット: `f3ff59c`（復旧は `5d16a90`）

### 守るべき5点

1. **Cloud 起動時は GitHub 上の最新 JSON を取得してから動作する**
   （`_github_sync_on_start()`・セッション1回のみ・対象は `_GH_SYNC_FILES`）
2. **保存前に読み込み時 SHA と現在の SHA を比較し、不一致なら絶対に PUT しない**
   （`_github_push_file(..., base_sha=)`）
3. **競合時は最新を取得して保存を中止する。自動マージは禁止**
   メッセージは `他の環境で更新されたため保存を中止しました。最新データを読み込みました。`
4. **409 発生時も古い内容を再送しない**（旧リトライループは廃止済み。再導入禁止）
5. **ローカル（Windows）の既存保存フローは変更しない**
   （`_git_auto_pull()` / `_git_auto_push()` は無変更。分岐は `_IS_CLOUD` のみ）

### なぜ

`_IS_CLOUD = platform.system() != "Windows"`。Cloud 側にはローカルの起動時 `git pull` が無く、
コンテナ内 JSON は**デプロイ時スナップショット**のまま古くなる。旧実装は SHA を競合検出にしか
使わず**全文 PUT** していたため、古い session_state がリモートの新しい内容を丸ごと消した。
2026-08-05 12:15 の `805d63d` が 00:57 の `579fd65`（渋谷新館 8/4 分のチェック）を完全に
巻き戻した事故がこれにあたる。旧 409 リトライは**新しい SHA で古い内容を再送**するため、
競合時にむしろ確実に上書きしていた。

### 実装上の注意

- PUT 成功時は応答の `content.sha` を `_gh_sha_key(repo_path)` へ記録し、次回保存の基準にする
- 取得内容が JSON として壊れている場合は書き戻さない（コンテナ内ファイルを守る）
- `base_sha` が未設定（起動時同期に失敗した等）のときは従来どおり保存する
- 競合で中止した場合、そのセッションの未保存編集は入れ直しが必要。**黙ってマージしない**

### 運用

- 「ローカルで入力 → その後 Cloud のセッションが動く」が事故条件だった。修正後は構造的に発生しない
- Cloud への反映には **Reboot／再デプロイが必要**

## ②個別画像「全台」は自動全台系（Step1）から除外する（2026-08-05 確定・`7b433da`）

**全ページ共通の正式仕様。巻き戻し禁止。**
関連コミット: `b694d7e`（記事用）→ `7b433da`（通常ページ・スランプ付き・かぶぱへ統一）

- **②個別画像「全台」へ入力した機種は、Step1（自動全台系）の候補段階から除外する。**
  対象は**記事用・通常ページ・スランプ付き・新宿歌舞伎町かぶぱのすべて**。
- **重複画像は生成後に除去するのではなく、最初から生成しない。**
  `_dedup_previews()` は正式仕様のまま維持するが、**この重複の対処に使わない**。
- 実装は `run_step1_main()` / `run_auto_pipeline()` の引数 **`kojin_zentai_machines`（既定 `set()`）**。
  渡すのは **`show_auto_page` の⑦フルプレビュー・⑧本番**と
  **`show_auto_article_page` の⑦プレビュー・⑧本番**の**計4か所**。
  `show_auto_page` は通常ページ・スランプ付き・かぶぱの共用のため、2か所で3経路に効く。
- **`recommended_machines` は流用しない**（⑤オススメ・②個別優秀台の全台系まで全店舗で消えるため）。
- ⑦プレビュー・🔄その他を更新・⑧本番・ZIP・結果テキスト・ban_map の**すべてで同じ仕様**。
  `result["files"]`・`zen_dai_list` の重複も発生させない
  （＝結果テキストの👑全台系濃厚機種は②個別側の1行だけ）。
- **②個別「全台」が空欄なら従来どおり自動全台系を生成する**（既定 `set()`）。
- 記事用では、Excel に該当台が無い場合に `continue` の**前**で `_rm_stale_image()` を呼び、
  古い同名画像を削除する（②個別が生成する経路では削除しない）。
- 記事用・②個別「優秀台」・⑤オススメ・⑤バラエティ・高配分・ジャグラー・末尾・
  ジャグラー末尾・並び・🎯掲載台選択・高解像度・パネル・スランプ・液晶・画像名・保存先・
  Cloud↔GitHub 同期は**無変更**。

**なぜ**: 旧実装では Step1 と②個別の2経路が同じ `{機種名}.jpg` を作っていた。⑧は後勝ちで
1枚に収まるが、⑦プレビューに同名2件・`result["files"]` に同一パス2件・`zen_dai_list` に
2エントリが積まれ、**結果テキストの👑全台系濃厚機種が2行**になっていた。Step1 版は
ジャグラーのみ G 数フィルターをかけるため、**プレビューと本番で表の行数が変わる**恐れもあった。

## スランプ付き②個別画像の「ページを広げる」と台番範囲廃止（2026-08-06 確定・`dc9f726` → `6efdd2c`）

**正式仕様。巻き戻し禁止。**対象は
**【秋葉原・上野新館・上野本館・新小岩】スランプ付き結果ポスト用の②個別画像のみ**。

対象店舗はモジュール定数 **`_KOJIN_Y_EXPAND_SLUMP_STORES`**（frozenset）で一元管理する。
この集合は「②優秀台を最大48枠へ拡張できる」と「台番範囲UI・台番範囲由来の処理を使わない」の
**2仕様がセットで成立する店舗**を表す。**店舗ごとにコードを複製しない**。店舗追加は集合への追記だけで行う。

判定は `show_auto_page()` 内の共通フラグ
**`_no_kojin_narabi = with_slump and store in _KOJIN_Y_EXPAND_SLUMP_STORES`**、
拡張可否は **`_ky_expandable = _no_kojin_narabi`**。
`_no_kojin_narabi` は **`kojin_enabled` の分岐より前**（ブロック外）で定義する
— `kojin_enabled=False` でも `_manual_sonota_auto_bans()` 経路から参照されるため。
店舗ごとの `_akihab_slump` / `_ueno_slump` を**復活させない**。

- **全台（`kojin_z_*`）は従来どおり12枠**。拡張ボタンは付けない。
- **優秀台（`kojin_y_*`）は初期12枠 →「▼ ページを広げる（最大48個まで入力）」で最大48枠**。
- 拡張状態は既存キー **`kojin_y_expand_{store}`**（session_state のみ・JSON保存しない）、
  ボタンは **`kojin_y_expand_btn_{store}`**。`st.rerun()` 直呼び・独自JSは追加しない。
- **13枠目以降に保存値があれば、ボタン未押下でも自動展開**する（`_has_extra_ky`）。
  F5・再起動・再デプロイ後もこれで入力欄が見える。
- **保存キーは既存の `kojin_y_0`〜`kojin_y_47` をそのまま使う。新規キーを作らない。**
  `_auto_input_keys()` / `_persistent_keys()` は元から全店舗48枠対応のため**変更しない**。
- **値の収集は表示枠数と無関係**（`range(_ky_count)` で常に0〜47を読む）。折りたたみ中でも値は落ちない。
- **対象4店舗のスランプ付きでは「並び台番範囲 優秀台」のUIを表示しない。**
  UIゲートは `not _no_kojin_narabi and store != "溝の口新館" and store != "新宿歌舞伎町"`
  （溝の口新館・かぶぱの既存専用条件は維持）。
  UIを隠すだけでなく `kojin_narabi_ranges_text` / `kojin_narabi_title` /
  `kojin_narabi2_ranges_text` / `kojin_narabi2_title` の**下流も空文字固定**し、
  保存済み値が残っていても**台番範囲画像・ban_map・結果テキスト・ZIP・
  その他自動抽出の除外用台番集合を生成/登録しない**。
- **`_manual_sonota_auto_bans()` の呼び出し3経路**（📝記入部分のみプレビュー・⑧本番2経路）は
  **session_state を直読みしてはならない**。必ず
  `"" if _no_kojin_narabi else st.session_state.get(f"kojin_narabi_range_{store}", "")`
  の形で `_no_kojin_narabi` を通す（ピンクバーなし側 `kojin_narabi2_range` も同様）。
  ここを直読みに戻すと**UIを消しても保存済み台番範囲が生き残る**（`dc9f726` 時点の不備・
  `6efdd2c` で是正）。ローカル変数への単純差し替えも禁止
  （`kojin_enabled=False` のとき対象外店舗の挙動が変わる）。
- **通常結果ポスト用（`with_slump=False`）は全店舗で従来どおり優秀台12枠＋台番範囲UIを維持**。
- 追加した13〜48枠目は**専用ロジックを作らず**、既存の `kojin_yushu_machines` リスト経由で
  ⑦プレビュー・🔄その他を更新・📝記入部分のみ・⑧本番・ZIP・結果テキスト・ban_map・
  パネル・スランプ・液晶・🎯掲載台選択・液晶再合成へ既存枠と同じように反映される
  （下流はすべて index 非依存）。
- 同一機種を複数枠へ入力したときの扱いは変更しない（`_dedup_previews()` で位置=先頭・
  内容=後勝ち、本番は同名ファイルへ上書き）。
- **秋葉原の `force_1k`**（②優秀台を+1,000枚以上のみに絞る）は
  `force_1k=(with_slump and store == "秋葉原")` のインライン判定のまま。
  **`_KOJIN_Y_EXPAND_SLUMP_STORES` と混ぜない**（上野新館・上野本館・新小岩には適用しない）。
- **新宿歌舞伎町かぶぱ（`_is_kabupa` 分岐が優先・3/6枠）・溝の口新館・
  高田馬場の記事用（`art_*` は別キー体系）・他店舗は不変。**
  `_dedup_previews` / `_pv_ck_key` / `_unit_ex_img_key` / `_gap_sel_key` / 横版生成条件 /
  高解像度仕様 / パネル選定 / 液晶選択 / Cloud↔GitHub同期 / ブラウザ履歴も**無変更**。

## with_slump店舗へ拡大：📝②個別優秀台OFFの再振り分けと⑦フルモードの結果テキスト整合（2026-08-07 確定・`ce2fafc`）

**正式仕様。巻き戻し禁止。**下記「秋葉原📝：…（`fd42ccf`）」の仕組みを
**スランプ付き結果ポスト用の5店舗＝稲毛・上野新館・上野本館・新小岩・秋葉原**へ広げ、
あわせて**⑦フルモードの結果テキスト欠落**を直したもの。
**新宿歌舞伎町（かぶぱ）は除外**（結果テキストが `_build_kabupa_result_text()` の別系統）。
**通常ページ（`with_slump=False`）・高田馬場記事用も対象外。**

### ① 📝経路の対象店舗

- `_manual_son_upd`（🔄側）/ `_manual_son_upd_e`（⑧側）＝
  **`with_slump and store != "新宿歌舞伎町"`**。
- ②個別優秀台の「生成する」をOFF → 🔄その他を更新 → ⑧ の状態を、
  **プレビュー＝⑧本番画像＝ban_map＝ZIP＝👑その他の優秀台**で一致させる。
- OFFした機種の**差枚 +1,000枚以上**の台だけをその他へ回す（⑦と同じ既存条件）。
- ⑧は**OFF画像を生成前にスキップ**し、`_save_jpeg`/`_exec_order`/ban_map/`_m_high` に載せない
  → **`👑高配分機種` に載らない**。`_rm_stale_image()` で旧画像を削除。
- 最終 **`_se_df_e`** を画像・ban_map・スランプ・パネル・液晶・ZIP・結果テキストの**唯一の正**とする
  （結果テキストは `locals().get("_se_df_e")` で流用し再計算しない）。
- **`_sonota_split=True` の店舗（上野新館・上野本館・新小岩）でも、📝経路は
  `sonota_extra_title.strip() or "その他の優秀台ピックアップ"` の1枚へ統合**し、
  `その他の優秀台+N,000枚以上.jpg` を新規生成しない。⑦の `_sonota_split` 仕様は無変更。

### ② `_manual_unit_df/di` の保存は🎯フラグから切り離す

**`_manual_unit_ky`（🎯パネル用）の内側で保存してはならない。**

```python
if _manual_unit_ky:                       # 🎯パネル用（従来どおり・広げない）
    st.session_state[_aprev_unit_key] = _manual_unit_src
    st.session_state[_unit_snap_key]  = _unit_ex_snapshot(...)
if _manual_unit_ky or (with_slump and store != "新宿歌舞伎町"):   # 📝再振り分け用
    st.session_state[f"_manual_unit_df_{store}"] = _df_m
    st.session_state[f"_manual_unit_di_{store}"] = _diff_m
```

**`_aprev_unit_key` / `_unit_snap_key` / `_manual_unit_src` は従来どおり `_manual_unit_ky` 限定。
上野新館・上野本館・新小岩・稲毛の📝に🎯パネルを追加しない**（パネルは `_aprev_unit_key` に
要素があるときだけ描画されるため、df/di を保存しても増えない）。

**なぜ**: `_manual_son_upd` の店舗条件だけ広げても、`_manual_unit_df/di` が
`_manual_unit_ky`（＝かぶぱ＋秋葉原のみ）の内側でしか保存されていなかったため、
上野新館等では🔄のフォールバックで **`_pv_df = None`** のままとなり、
`if _pv_df is not None and _pv_diff is not None:` のガードで**再振り分けブロックごと
スキップ**されていた（🔄を押しても何も起きない）。

### ③ ⑦フルモードの結果テキスト整合

**高配分OFF・全台系OFF・並びOFF・②個別優秀台OFF の4経路はいずれも `_extra_dfs` 経由で
「その他の優秀台」画像へ再振り分けされる**が、結果テキストは pipeline の元
`result["excellent_list"]` をそのまま使っていたため**反映されていなかった**。

- **`_extra_dfs` / `_extra_diffs` から作った追加分だけ**を、既存 `excellent_list` へ
  **台番単位で重複除去して追加**する。**既存 `excellent_list` の内容・順序・項目は変更しない**
  （＝案A方式の全面置換は採用しない。`excellent_list` と `sonota_excellent_list` は別フィールド）。
- 追加分は結果テキスト用に**再抽出しない**（画像へ足したのと同じ `_extra_dfs` を正とする）。
- **`_jug_ex_dfs`（ジャグラー側）の台は `👑その他の優秀台` へ追加しない。**
  既存分岐（`_extra_dfs` → その他 ／ `_jug_ex_dfs` → ジャグラー）を維持する。
- 追加リストは `if _extra_dfs:` の内側でのみ定義し、`locals().get()` で参照する。
  **チェックOFFが1件も無ければ従来の結果テキストと完全に同一。**
- 表示順は既存 `generate_report_text()` の差枚降順のまま。

### 無変更

秋葉原 `fd42ccf` の📝正式仕様すべて（`_manual_regen` / `force_1k` 4経路統一 / `_m_son_extra_bans` /
`_se_df_e` 基準 / 🎯パネル / B/C一致 / 分割画像なし）・`_manual_unit_ky` 自体・②個別優秀台の
🎯OFFと `diffs` の連動（別件）・サマリー計算・④末尾・ジャグラー末尾・`_sonota_split` の⑦仕様・
かぶぱ・通常ページ・高田馬場記事用・Cloud↔GitHub同期・ブラウザ履歴。

## 秋葉原📝：②個別優秀台のチェックOFFをプレビュー・⑧本番・その他画像・結果テキストで一致させる（2026-08-07 確定・`fd42ccf`）

**正式仕様。巻き戻し禁止。**対象は
**【秋葉原】スランプ付き結果ポスト用 → 📝記入部分のみプレビュー → ②個別画像「優秀台」。**
判定は **`_manual_son_upd`（🔄側）/ `_manual_son_upd_e`（⑧側）＝ `with_slump and store == "秋葉原"`**
かつ `_manual_preview_mode_{store}`。他店舗・⑦・かぶぱには適用しない。

### ① 🔄その他を更新（📝由来）

- `{機種名}（優秀台）.jpg` の「生成する」をOFF → 🔄で、その機種のうち
  **差枚 +1,000枚以上の台だけ**を「その他の優秀台」へ再振り分けする（⑦/🔄と同じ既存条件）。
  **機種全台をそのまま入れない。**
- 📝は `_aprev_df_key` を持たないため、**`_manual_unit_df_{store}` / `_manual_unit_di_{store}`
  をフォールバック利用**する（既存キー・新規キーを作らない）。
- **⑦由来の `_pv_ex` / `_pv_hr` / `_pv_zen` / `_pv_narabi`・ジャグラー情報は📝へ持ち込まない**
  （同一セッションで先に⑦を実行していると残るため明示的に空にする）。
  `run_auto_pipeline()` のフルプレビューへ戻さない。**Re:ゼロ2／いざ!番長／シンフォギア勇気／
  南国育ちSPECIAL 等、記入していない自動抽出画像を追加しない。**
- その他画像は **`sonota_extra_title.strip() or "その他の優秀台ピックアップ"` の1枚へ統合**。
  既存対象台とOFF由来台を統合し、**台番重複除去・既存正式順序**を維持する。
  **📝では `その他の優秀台+1,000枚以上.jpg` / `+2,000枚以上` / `+3,000枚以上` を新規生成しない。**

### ② ⑧本番はOFF画像を「生成前」にスキップ

②個別優秀台の**画像生成前**に既存 `_pv_ck_key()` を確認する。名前は📝プレビューと同じ
**`f"{_make_safe_fn(_metit)}.jpg"`**。OFFなら:

- `_save_jpeg()` を呼ばない／`_exec_order`・ban_map・`_m_high` に追加しない
- **`_rm_stale_image()`** で古い同名画像（縦版・横版・`NN_`付き）を削除
- OFF機種の **+1,000枚以上台**をローカル集合 **`_m_son_extra_bans`** へ収集して `continue`

**「全部生成して後から削除する」方式へ戻さない。** `_m_son_extra_bans` は⑧処理内の
ローカル集合で、**新しい session_state キー・JSON は作らない**。候補台は既存
`_kojin_yushu_filter(..., force_1k=True)` 通過後の DataFrame から取る。

### ③ ⑧のその他画像＝最終 `_se_df_e` を唯一の正とする

元のその他対象台と `_m_son_extra_bans` を統合して **`_se_df_e`** を作る。
**元その他0台でもOFF由来台があれば1枚生成／両方0なら生成しない。**
`_se_df_e` を **その他画像・ban_map・スランプ・パネル・液晶・ZIP・結果テキスト**の正とする。

### ④ 結果テキストも `_se_df_e` を正とする

`👑その他の優秀台` 用の `_m_excel` を**別途再計算しない**。
**`locals().get("_se_df_e")`** で取得してそのまま変換し `generate_report_text()` へ渡す
（`kojin_enabled=False` で未定義になり得るため `locals()` を使う。既存
`_sel_from_ban_out(locals().get("_sue_bans_out_e"))` と同じ流儀）。

**プレビュー＝⑧本番画像＝ban_map＝ZIP＝結果テキスト**の台番集合を一致させる。
「画像にいるのにテキストにいない／その逆」へ戻さない。

**OFFした②個別優秀台は生成前 `continue` で `_m_high` に入らないため
`👑高配分機種` に載らない**（追加の除外処理は不要）。その機種からその他へ移った台だけを
`👑その他の優秀台` へ載せる。**独自セクションは作らない。**書式は既存
`generate_report_text()` のまま（`🚩【台番】機種名→+差枚`・差枚降順）。

### ⑤ B/C は同じ結果

**B**（📝→OFF→🔄→⑧）と **C**（📝→OFF→🔄押さず→⑧）で、OFF画像なし・その他画像の台番集合・
`👑その他の優秀台` の内容・`👑高配分機種` からのOFF機種除外がすべて一致する。
⑧は🔄の押下有無を参照せず、**既存 `_pv_ck_key()` から最終状態を再現**する。

### ⑥ 診断ログ

OFF検出時の `🗑️ チェック外し対象: {機種名}（優秀台）.jpg（その他へ N台）` は残してよい。
**新しい状態管理には使わない。**

### 無変更

②個別優秀台の🎯OFFと `diffs` の連動（別件・未対応）・サマリー計算・④末尾・ジャグラー末尾・
⑦フルプレビュー側・かぶぱ・上野新館・上野本館・新小岩・高田馬場記事用・Cloud↔GitHub同期・
ブラウザ履歴。**かぶぱ等の📝⑧にも「②優秀台OFFがその他へ回らない」同じ不備が残っているが、
今回の対象外**（必要になったら別途対応する）。

## 秋葉原スランプ付き：📝経路の②個別優秀台🎯・force_1k統一・`_manual_regen`（2026-08-07 確定・`9faaee3`）

**正式仕様。巻き戻し禁止。**対象は
**【秋葉原】スランプ付き結果ポスト用 → ②個別画像 → 優秀台。**

### ① 📝記入部分のみプレビューでも🎯を使える

- ⑦フルプレビューだけでなく **📝記入部分のみプレビューでも「🎯 掲載台を選ぶ」を使用できる**。
- 秋葉原の📝経路で🎯対象にするのは **②個別画像「優秀台」だけ**。
  **④末尾・⑤バラエティには追加しない。**
- **`_kabupa_unit` / `_kabupa_unit_e` 自体の意味は広げない**（広げると④末尾・⑤バラエティの
  パネルまで秋葉原に付く）。専用判定
  **`_manual_unit_ky` / `_manual_unit_ky_e`**（`= _kabupa_unit(_e) or (with_slump and store == "秋葉原")`）
  で②個別優秀台だけを対象にする。
- **新宿歌舞伎町かぶぱの既存📝🎯仕様は変更しない。**
  **上野新館・上野本館・新小岩など他店舗の📝経路には今回の🎯を追加しない。**

### ② force_1k を全経路で統一

秋葉原の②個別優秀台は `_kojin_yushu_filter()` へ渡す `force_1k` を
**⑦フルプレビュー／📝記入部分のみプレビュー／📝モードの⑧本番／通常の⑧本番**の
**4経路すべてで `force_1k=(with_slump and store == "秋葉原")` に統一**する。

揃えないと同じ機種でも候補台番集合が経路ごとに変わり、`_unit_ex_img_key()` が別キーになって
🎯選択を共有できない。⑦・📝・⑧は既存の `_unit_ex_state()` / `_unit_ex_pick()` /
`_unit_ex_img_key()` を共用し、**同じ機種・同じ候補台番集合なら同じ🎯選択状態を共有**する。
独自キー・別state・別snapshotは作らない。

### ③ `_manual_regen`（📝由来の🎯再生成）

- 🎯変更による再生成のモード判定は **`_manual_regen`** を使う。
  **`_kabupa_manual_regen` というかぶぱ限定名称へ戻さない。**
- 意味は「**現在が📝プレビュー由来で、🎯変更による再生成なら、フルプレビューではなく
  📝経路を再生成する**」。対象は **新宿歌舞伎町** と **秋葉原のスランプ付き結果ポスト用**。

  ```python
  _manual_regen = (
      _unit_regen
      and (store == "新宿歌舞伎町" or (with_slump and store == "秋葉原"))
      and bool(st.session_state.get(f"_manual_preview_mode_{store}", False))
  )
  if _manual_regen:
      _unit_regen = False   # フルプレビュー経路には入れない
  ```

- **`_manual_regen=True` のとき `run_auto_pipeline()` のフルプレビュー経路へ入れない。**
  📝で記入していない自動抽出画像（全台系・高配分・ジャグラー・その他）を追加しない。
  **Re:ゼロ2／いざ!番長／シンフォギア勇気／南国育ちSPECIAL 等が勝手に増える状態へ戻さない。**
- **📝由来の🎯再生成では `_manual_preview_mode_{store}` を維持する**（pop しない）。
  そのため 📝→🎯→🔄→⑧本番 と進んでも⑧は**記入部分のみモードのまま**処理される。
  pop は「🔍 プレビュー生成」を押したフル経路（`if _full_prev_btn or _unit_regen:` の内側）だけ。
- **⑦フルプレビュー由来は従来仕様を維持**する。⑦では `_manual_preview_mode_` が無いため
  `_manual_regen=False` となり、`_unit_regen=True` のまま従来どおりフル再構築する。
- session_state キーは既存の **`_manual_preview_mode_{store}`** をそのまま使う。新規キーを作らない。

### ④ 全台OFF・枠index

全台OFF時は既存仕様のまま — 画像を生成しない／孤児パネルから戻せる／⑧本番で古い
縦版・横版・連番付き画像を `_rm_stale_image()` で削除／ZIP・ban_map・スランプ・パネル・
液晶に残さない。**優秀台1〜48枠すべてで同じ🎯仕様**とし、**枠indexによる別処理は禁止**
（`kojin_yushu_machines` の機種名ループのまま）。

### 無変更

優秀台最大48枠・UI1〜8枠のみ店舗単位永続・UI9〜48枠はExcel／日付単位・全台12枠・
台番範囲なし・`_KOJIN_Y_EXPAND_SLUMP_STORES`・`_no_kojin_narabi`・`_unit_ex_state()`・
`_unit_ex_pick()`・`_unit_ex_img_key()`・`_render_unit_ex_panel()`・`_unit_snap_key`・
`_aprev_unit_key`・`_manual_unit_df/di`・`_dedup_previews()`・`_gap_sel_key()`・
`recommended_machines`・横版条件・高解像度・パネル選定・液晶・**秋葉原の画像ドロップ処理**・
Cloud↔GitHub同期・ブラウザ履歴。

**別件（今回の正式仕様に含めない）**: 結果テキストの `diffs` が🎯OFFに連動していない件。

## 秋葉原②個別「優秀台」の永続化範囲は UI 1〜8枠目だけ（2026-08-07 確定・`611a452`）

**正式仕様。巻き戻し禁止。**対象は
**【秋葉原】スランプ付き結果ポスト用 → ②個別画像 → 優秀台（`kojin_y_*`）の保存範囲だけ。**

- **UI 1〜8枠目（index 0〜7）のみ店舗単位で永続化**する
  （`auto_page_persistent_inputs.json`・Excelをまたいで保持）。
- **UI 9〜48枠目（index 8〜47）は Excel／日付単位**（`auto_page_inputs.json`）で保存する。
  **別日の Excel を取得したとき、その日付に保存値がなければ空欄にする。**
- `_persistent_keys()` の**秋葉原専用分岐は `range(8)` を正式仕様**とする。
  **秋葉原について `range(48)` へ戻さない。** 他店舗共通の末尾 return（`range(48)` ＋
  `kojin_z` 12個）は**変更しない**。
- **`_auto_input_keys()` は従来どおり48枠**（`kojin_y_0`〜`kojin_y_47`）を対象とし、
  9〜48枠目の**日付単位保存は維持**する。保存キー自体は変えない。
- 優秀台の**初期12枠＋「ページを広げる」で最大48枠**というUI仕様、
  **13枠目以降にその日付の保存値があれば自動展開**する仕様は維持する
  （`_KOJIN_Y_EXPAND_SLUMP_STORES` / `kojin_y_expand_{store}`）。
- 秋葉原の**全台 `kojin_z_*` は従来どおり日付単位**（永続対象外）。
- **上野新館・上野本館・新小岩など他店舗の48枠 店舗単位永続は変更しない。**
- 台番範囲なし・`force_1k`・`_KOJIN_Y_EXPAND_SLUMP_STORES`・`_no_kojin_narabi`・
  ⑦／🔄／📝／⑧／ZIP・ban_map・パネル・スランプ・液晶・🎯掲載台を選ぶ等は**無変更**。

**なぜ（今回判明した原因）**: 導入時（`b876c86` 2026-06-23）は `range(8)` で UI 1〜8枠目だけが
店舗単位永続だった。**2026-07-14 に `3e5ee1d`（`range(8)`→`range(21)`）→ `a9cf4e1`（→`range(48)`）**
と拡張された際、**UI 9枠目以降まで意図せず店舗単位永続**になった。その結果
`auto_page_persistent_inputs.json` の `kojin_y_8_秋葉原 = "戦コレ6"` が
`_restore_auto_inputs()` の永続値優先パス（保存値なし＝5185行／保存値が空文字＝5193行）で
毎回復元され、**別日の Excel へ切り替えても9枠目から消えない**状態になっていた。
`range(8)` へ戻すことで UI 9枠目以降を本来の日付単位保存へ戻した。

**既存データ**: `auto_page_persistent_inputs.json` の `kojin_y_8_秋葉原 = "戦コレ6"` は
**残したまま**（今後は永続対象外なので参照されない）。`auto_page_inputs.json` の
**8/3〜8/6 の4エントリ**に保存済みの `kojin_y_8_秋葉原 = "戦コレ6"` も**変更しない**。
その4日は日付単位の保存値として9枠目に表示されるのが**正常**。

## 秋葉原スランプ付き②個別「その他の優秀台ピックアップ」タイトルの既定表示（2026-08-07 確定・`78240d3`）

**正式仕様。巻き戻し禁止。**対象は
**【秋葉原】スランプ付き結果ポスト用 → ②個別画像 → 「その他の優秀台ピックアップ」のタイトル欄だけ。**

- **未設定・保存値なし・空文字保存のいずれでも「その他の優秀台ピックアップ」を表示する。**
- **ユーザーが任意の非空タイトルを保存している場合はその値を最優先し、既定文言で上書きしない。**
- **`placeholder` での対応は禁止。**既存キー **`sonota_extra_title_{store}`** の**実値**として
  session_state へ入れる。新しい保存キー・新しいタイトル処理・新しいフォールバック関数は作らない。
- 実装はタイトル `text_input` の**直前**の3行だけ。

  ```python
  _se_ttl_key = f"sonota_extra_title_{store}"
  if with_slump and store == "秋葉原" and not st.session_state.get(_se_ttl_key, ""):
      st.session_state[_se_ttl_key] = "その他の優秀台ピックアップ"
  ```

- **`_restore_auto_inputs()` / `_save_auto_inputs()` / `_auto_input_keys()` /
  `_persistent_keys()` / `_merge_auto_entry()` は変更しない。**
- **⑦フルプレビュー・🔄その他を更新・📝記入部分のみ・⑧本番・ZIP の既存フォールバック
  （`sonota_extra_title.strip() or "その他の優秀台ピックアップ"`）は変更しない。**
  既定文言使用時の生成結果は修正前と同一。
- **秋葉原以外の店舗・ページへは適用しない**（上野新館・上野本館・新小岩・通常結果ポスト用・
  新宿歌舞伎町かぶぱ・高田馬場の記事用〔`art_sonota_extra_title_*` は別キー体系〕はすべて不変）。
- 秋葉原の**優秀台48枠・全台12枠・台番範囲なし・`force_1k`**、および抽出条件・差枚条件・
  画像生成条件・🎯掲載台を選ぶ・ban_map・パネル・スランプ・液晶・液晶再合成・高解像度・
  画像サイズ／画像名／保存先・`_dedup_previews` / `_pv_ck_key` / `_unit_ex_img_key` /
  `_gap_sel_key`・Cloud↔GitHub同期・ブラウザ履歴は**無変更**。

**なぜ**: 原因は `value=` の書き方ではない。**Streamlit は `key` が既に session_state に存在すると
`value=` を無視する**。`_restore_auto_inputs()` は Excel 切り替え時に保存値なしなら `""` を、
空文字保存なら `""` をそのまま session_state へ書き込むため、**Excel をアップロードした店舗**では
`value=` の既定文言が効かず空欄になる。restore を通らない店舗（Excel はそのままで後から移動した
店舗）だけ既定文言が表示されていた＝上野新館が「正しく実装されていた」わけではない。
実データでも秋葉原は20件すべて `""`、上野新館は16件が既定文言／7件が `""` だった。

## ⑤オススメ機種ピックアップの永続化（2026-08-10 確定・`55e7752`）

**正式仕様。巻き戻し禁止。**⑤の機種名・タイトル・抽出条件は
**`store_settings/{store}.json` に店舗単位で永続**する（日付・Excel単位ではない）。
`auto_page_inputs.json` / `auto_page_persistent_inputs.json` は⑤を一切扱わない。

- **保存キー**：`recommended_machines_1〜6`（各9枠）／`recommended_title_1〜6`／
  `recommended_filter_1〜6`／`rec_enabled`。**新しいキー・新しいJSONを作らない。**
- **widgetキー**：`rec_m{1-6}_{0-8}_{店舗}`／`rec_title_{n}_{店舗}`／`rec_f_{n}_{店舗}`

### ① 保存は「キーの存在」で分岐する（`_save_rec_machines()`）

- `rec_m*` が session_state に**ある** → 現在値を保存（**空欄はユーザーの意図的クリアとして空を保存**）
- **ない** → `store_settings` の既存値を維持（**空で潰さない**）

`_save_rec_titles` / `_save_rec_enabled` / `_save_persistent_inputs` と同じ方針。
**`st.session_state.get(key, "")` で無条件に全枠を書き戻す実装へ戻さない。**

### ② ウィジェットの seed は保存値（`default=`）

B1〜B6の `render_machine_autocomplete_input()` へ **`default=_rec_saved_m[n][_i]`** を渡す。
`_init_recommended_settings()` は読み込み済みの保存値 `{ブロック: 9枠}` を返し、
追加のJSON読み込みをせずこれに流用する。**`default=""` のままにしない。**

Streamlit は描画されなかったウィジェットのキーを session_state から破棄するため、
`default=""` だと⑤OFF→ON・データ取得の rerun 後の再描画で**空文字が seed され**、
それが on_change 保存で JSON へ焼き付く。seed は**キー不在時のみ**なので、
**ユーザーが空へ変更した枠を復活させることはない**（意図的クリアは維持される）。

### ③ 抽出条件は保存値から index 復元

`_REC_F_OPTS` / `_REC_F_DEFAULT` / `_rec_f_index(store, n)` を使い、
**B1〜B6すべての radio へ `index=_rec_f_index(store, n)`** を渡す。
解決順は **session_state → 保存値 → 正式既定値（B1=+1,000枚以上／B2〜B6=プラス台）**。
`index=` を付けない radio に戻すと、キー破棄後の再描画で先頭「プラス台」へ落ちる。

### ④ ▶▶実行時の一括保存も同じガード

`show_auto_page` の実行時一括保存も `_save_rec_machines()` と**同一思想**（キーあり→現在値／
キーなし→既存値維持）に統一する。**別の保存ロジックを作らない。**

### ⑤ 適用範囲

⑤を使う**全店舗共通**。店舗特例・日付特例を作らない。

## ⑤機種名の初期値は value= でフロントへ渡す（2026-08-10 確定・`39f1f1e`）

**正式仕様。巻き戻し禁止。**上記 `55e7752` の永続化仕様に対する**追加の必須条件**。
`55e7752` だけでは全消しは止まらず、同日 15:30 に新小岩の26機種が再度全消しした。

### 真因

**session_state への事前 seed だけではブラウザ側へ初期値が渡らない。**
`_init_recommended_settings()` が `rec_m*` を session_state へ入れても、
**そのセッションで⑤が一度も描画されていない状態から初めてONにした初回描画**では、
入力欄54枠が**すべて空でレンダリング**される（サーバ側 session_state には値がある）。
次に何か操作すると**フロントがその空値を返し**、`on_change=_save_rec_machines` が
「キーは存在し値は空＝ユーザーの意図的クリア」と判定して `store_settings` を全消しする。

`55e7752` のガード（キーあり→現在値／キーなし→既存値維持）は
「キーが破棄されて未描画になる」ケース用で、
**「キーは生きているが中身がフロント由来の空になる」ケースは防げない。**

ダミー環境で **「初回⑤ON → DOM全54枠が空 → rerun → `[SAVE] 非空数=0` が9件発火 → 全消し」**
を完全再現して確定した。

### 正式修正（案A2・2か所だけ）

1. **`_init_recommended_settings()` は `rec_m*` を session_state へ事前 seed しない**
   （`if k.startswith("rec_m"): continue`）。
   `rec_enabled` / `rec_title_*` / `rec_f_*` / `result_extra_note_*` の seed は**従来どおり**。
2. **`render_machine_autocomplete_input()` は `st.text_input(..., value=default, ...)` を渡す。**
   事前 seed（`if key not in st.session_state: st.session_state[key] = default`）は**使わない**。

**「seed だけで value= を渡さない」実装へ戻さない。** それが事故そのもの。
⑤の呼び出し6ブロックは `default=_rec_saved_m[n][_i]` を渡し済みで**変更不要**。
`_save_rec_machines()` / `_save_rec_titles()` / `_save_rec_enabled()` / ▶▶一括保存は**無変更**。

### 実機確認（Chrome実ブラウザ）

⑤未描画の新規セッションから初回ONで **26/54枠が正常表示**。
**初回ON直後に F5 せず rerun しても26機種を保持**（修正前はここで全消し）。
⑤OFF→ON・F5・日付変更でも保持。意図的な**1枠クリア・ブロック全枠クリアは従来どおり可能**。
**Streamlit の警告は出ない。**

### 共通関数の他の利用箇所

`render_machine_autocomplete_input()` は②個別画像・記事用個別画像・ローテ・週間表でも使う。
**session_state に既存値があれば Streamlit 側でそちらが優先され、警告も出ない**ため挙動は不変。
ローテ（西武新宿5件）・週間表（高田馬場93件）で実機確認済み。

### 別案件（今回は未修正）

- **②個別画像・記事用個別画像も同じ構造の潜在リスクを持つ**（`default` を渡さず
  session_state seed に依存）。保存経路が `_save_auto_inputs`（Excel単位マージ）で
  ⑤と異なるため、影響範囲は別途調査する。
- **⓪日付取得後に②個別画像の入力欄が一時的に消える**挙動は `39f1f1e` 以前から存在する
  別問題。HEAD版コードとのA/B比較で同一と確認済み。今回の修正対象外。

### 新小岩の正式設定

B1=5 / B2=4 / B3=8 / B4=9 の**合計26機種**（`rec_enabled` の既定は `false`）。

## store_settings の正データ源と Cloud 運用ルール（2026-08-10 確定・調査のみ／コード変更なし）

**正式運用ルール。巻き戻し禁止。**⑤オススメ機種ピックアップと高田馬場の記事用⑤バラエティが
保存される `store_settings/{store}.json` の扱いを定める。**今回は同期機能を実装していない。**

### 現状の構造（コードで確認済みの事実）

- **`store_settings` には Cloud → GitHub の同期経路が1本も無い。**
  - `_GH_SYNC_FILES`（2512行）は **`weekly_items.json` / `rote_machines.json` のみ**。
    `store_settings` は含まれない。
  - `save_store_settings()`（4898行）は**ファイル書き込みだけ**で、
    `_github_push_file()` も `_git_auto_push()` も呼ばない。
  - `_git_auto_push()`（2672行）の `targets` には `"store_settings"` が入っているが、
    呼び出し4か所（10793 / 12313 / 14851 / 17153行）はすべて **`if not _IS_CLOUD:`**。
  - `_github_push_file()` の呼び出しは2か所だけ（15179＝ローテ／15376＝週間）。
- **Cloud 上の編集値は Cloud コンテナ内のファイルにだけ存在する。**
  再デプロイ／Reboot でコンテナが作り直されると消える。
- **GitHub 側で `store_settings` が更新されても Cloud は自動で取り込まない。**
  `_github_sync_on_start()`（2567行）は `_GH_SYNC_FILES` しか pull しないため、
  反映は**再デプロイ時のみ**。
- ローカルは `_git_auto_pull()` / `_git_auto_push()` で双方向に通っている
  （ただし push は**画像生成時のみ**。⑤を編集しただけでは push されない）。

### store_settings に入っているもの（全12店舗・実キー22種）

| カテゴリ | キー |
|---|---|
| ⑤オススメ機種ピックアップ（19種） | `rec_enabled` / `recommended_machines_1〜6` / `recommended_title_1〜6` / `recommended_filter_1〜6` |
| 高田馬場 記事用⑤バラエティ（3種） | `art_variety_range` / `art_variety_enabled` / `art_variety_mode` |

画像・Excel・日付単位の入力は含まれない（それらは `auto_page_inputs.json` 側）。

### 正式運用ルール

1. **`store_settings` の正データ源は GitHub とする。**
2. **⑤の設定変更はローカルで行う。** ローカルで変更 → GitHub へ反映 → Cloud は
   GitHub 上の正式設定を使う。
3. **Streamlit Cloud 上では⑤オススメ機種ピックアップの設定を編集しない。**
   Cloud で編集してもコンテナ内にしか保存されず、GitHub／ローカルへは同期されない。
   再デプロイ等で消えるため**正式設定として扱わない**。
4. **高田馬場の記事用⑤バラエティ（`art_variety_*`）も同様に Cloud 上では編集しない。**
5. **2026-08-10 に Cloud の新小岩⑤ブロック5に現れた
   「虚構推理／BIRDIE WING／戦国乙女4／バイオRE:3／ULTRAMAN最終決戦」は正式設定ではない。**
   リポジトリの全JSONにも git 全履歴（`git log -S --all`）にも存在せず、
   **Cloud で入力された Cloud-only 値**である。
   **GitHub HEAD の `store_settings/新小岩.json` を正とし、B5空欄が正式状態。**
   新小岩⑤の正式値は **B1=5 / B2=4 / B3=8 / B4=9 の合計26機種、B5・B6は空**。
6. **双方向同期は今回は実装しない。**将来必要になった場合の別案件とする。
   実装する場合は **「起動時 GitHub→Cloud pull ＋ SHA確認付き Cloud→GitHub push」を必ずセット**で
   設計する。**push だけを追加する実装は禁止**（Cloud の古いコンテナ値が GitHub の新しい設定を
   上書きする事故が確実に起きる）。
7. **将来実装する場合に必ず回帰確認する項目**：
   日本語ファイル名のURLエンコード（現行 `_github_fetch_file` / `_github_push_file` は
   `urllib.parse.quote` を通していない）／SHA競合／409／同一店舗の同時編集／
   起動時の複数GET（12店舗＝12往復）／高田馬場 `art_variety_*` への影響／
   ⑤の `39f1f1e` 正式仕様／②の `0e7dc4c` 正式仕様。

### なぜ同期を実装しないか

`store_settings` に入るのは⑤と記事用バラエティだけで変更頻度が低く、
「ローカルで整えて push → Cloud は再デプロイで受け取る」で運用が成立する。
12ファイル×双方向の同期を足すと、日本語パス・起動時の往復回数・同一店舗の同時編集など
新しい事故クラスが増える。今回の Cloud-only 値は**同期の欠如ではなく
「Cloud で編集した」ことが原因**なので、運用ルールで断つのが最小リスク。

## ②個別画像の初期値受け渡しと保存タイミング（2026-08-10 確定・`0e7dc4c`）

**正式仕様。巻き戻し禁止。**通常ページ②と記事用②の両方が対象。
⑤で起きた事故（`39f1f1e`）と同型の問題が②にも構造的に存在していたものを塞いだ。

### 共通の真因

ウィジェットが**未描画の run を挟んだ後の初回描画**では、session_state に値があっても
ブラウザ側は空でレンダリングされる。その空値がフロントから返り、保存へ回って
既存の機種名を潰す。初期値は `default=` → `st.text_input(value=)` で
**ブラウザまで届けなければならない**。

### 通常ページ②

- 事故経路：保存値あり → **②「個別画像も生成する」OFF**（未描画 run）→ **②ON**
  → ブラウザDOMが全枠空 → その後の rerun で**毎レンダー保存（7138行）**が
  `auto_page_inputs.json` を空化する。
  永続JSONは `_save_persistent_inputs()` の非空ガードで守られるが、
  **秋葉原の `kojin_z` 全12枠・`kojin_y` 9〜48枠、高田馬場、新宿歌舞伎町の `kojin_z`**
  は永続対象外なので恒久的損失になり得た。
- **`_kojin_default(excel_name, store, key) -> str`** を新設（読み取り専用）。
  `auto_page_inputs.json` / `auto_page_persistent_inputs.json` / `_persistent_keys(store)` /
  店舗別特例を **`_restore_auto_inputs()` とまったく同じルール**で解決する。
  解決順は「新宿歌舞伎町の `kojin_y_*` は常に `""`」→「保存値あり（永続キーかつ空なら永続値）」
  → 「永続キーかつ永続値あり」→ `""`。
- `kojin_z_*` / `kojin_y_*` の描画へ **`default=_kojin_default(...)`** を渡す。
- **9店舗 × 9データパターン × 全キー＝5724ケースで既存復元仕様との不一致0**を確認済み。
  `_kojin_default()` を変更するときは同じ等価性検証をやり直すこと。

### 記事用②

- **`_art_kojin_default(excel_name, store, key) -> str`** を新設。
  参照するのは **`article_page_inputs.json` の該当Excelエントリだけ**。
  **通常②の `auto_page_persistent_inputs.json`（永続値）を記事用へ流用しない**
  （記事用は Excel／日付単位で完結する別体系）。
- `art_kojin_z_*` / `art_kojin_y_*` の描画へ `default=_art_kojin_default(...)` を渡す。
- **`_save_article_inputs()` は全置換をやめてマージ方式**にする。
  全置換だと②をOFFにしただけで未描画キーが entry から**丸ごと削除**され、
  記事用には永続ファイルが無いため復旧できなかった。
- **順序問題（記事用固有）**：`_restore_article_inputs()` は未保存キーへ `""` を
  **plain な session_state 値**として入れる。これは widget 由来ではないので
  Streamlit の未描画キー破棄の対象にならず、**②が未描画でも 24/24 キーが `""` で常駐**する。
  ②ONクリックの `on_change` は**ウィジェット描画より前**に走るため、
  通常の `_save_article_inputs()` では保存済み機種名を `""` で潰していた。
- 対策として **`_save_article_inputs(store, skip_kojin: bool = False)`** と
  **`_save_article_enabled(store)`**（②チェックボックス専用コールバック）を正式採用する。
  チェックボックスの `on_change` は `_save_article_inputs` ではなく
  **`_save_article_enabled`** を使う。

### `art_kojin_z_*` / `art_kojin_y_*` の保存ルール

**「値が空か」ではなく「その保存タイミングで保存してよい状態か」で判定する。**

| 条件 | 挙動 |
|---|---|
| `skip_kojin=True` | 保存対象から除外 → 既存値を維持 |
| `art_kojin_enabled` が False | 保存対象から除外 → 既存値を維持 |
| `skip_kojin=False` かつ `enabled=True` | 現在値を保存（**`""` も意図的クリアとして保存**） |

`art_kojin_*` 以外のキーは従来どおり「キーの存在」だけで判定する。
**「空文字なら保存しない」実装へ倒さない**（意図的クリアが壊れる）。
**新しい session_state フラグは作らない**（`_art_kojin_drawn` のような描画フラグ案は不採用）。

### 実機・ダミー確認（全PASS）

**記事用②**：OFFで既存値維持／OFF中に別ウィジェットを変更しても維持／OFF→ONで空上書きなし／
初回描画から保存値がDOM表示／session_state 一致／rerun保持／⑧実行後も保持／
1枠クリア可能／全枠クリア可能／F5保持／日付変更→戻すで保持／再取得保持／Streamlit警告なし。

**通常②**：OFF→ON・rerun・F5・日付変更・再取得のすべてで保持（実アプリ・新小岩8/9で
②24件と⑤26件が同時に正常表示）。

### 店舗特例（すべて維持）

- **秋葉原**：`kojin_z` 全12枠は日付単位（別日で空）／`kojin_y` は index 0〜7 のみ永続
- **高田馬場**：通常②は日付単位・永続対象外
- **新宿歌舞伎町**：`kojin_y` は毎回空欄
- **記事用②**：`article_page_inputs.json` のみ・永続値の流用なし

### 今回の対象外（同時に修正しないこと）

- **「⓪日付取得後に②の入力欄が一時的に消える問題」は未修正。**
  原因は `_restore_auto_inputs()` 5207行が「保存値に `kojin_enabled` が無い Excel」で
  `False` へリセットすること（＝`kojin_enabled` の復元ロジックの別問題）。
  データ損失ではない。**②の初期値・保存の修正と一緒に直さない。**
- **⑤オススメ機種ピックアップは `39f1f1e` の正式仕様を維持**する。今回いっさい変更していない。

## 自動処理ページの入力値保存（auto_page_inputs.json）

Excel ファイル名をキーに、店舗ごとの入力値を保存する。**全置換は禁止・マージ方式が正式仕様**（2026-07-16・`95c6d54`）。

- Excel切り替え時は、切り替え**前**の店舗（`st.session_state["_auto_prev_store"]`）のキーセットで旧Excelを保存する。未保持の初回は現在の店舗へフォールバック。
- 保存は `_merge_auto_entry()` を使い、**session_state に存在するキーだけ**を既存エントリへ上書きする。存在しないキーは**削除しない**。
- 判定は `if k in st.session_state`（キーの存在）のみ。値が `""` や `False` でもそのまま保存する（意図的なクリアを反映）。
- `_save_auto_inputs()` も同じマージ方式。

**なぜ**: 旧コードは `data[excel_name] = {k: ... for k in _auto_input_keys(store) ...}` の全置換だった。`_auto_input_keys(store)` は現在の店舗のキーしか生成しないため、店舗をまたぐExcel切り替えで旧店舗固有キー（`kojin_z_0_高田馬場` 等）が**構造上コピーされず消滅**していた。実データを失ったエントリが17件（5月以降・継続発生）。

**運用上の注意**:
- 起動中の Streamlit は毎レンダーでこのJSONを自動保存し `_git_auto_push` で push する。**手作業で編集・復元するときは必ずアプリを停止してから**行う（さもないと上書きされる）。
- 「キー数が少ない＝欠損」ではない。`_auto_input_keys` は機能追加で枠が増えてきた（`kojin_y` 12→48枠など）ため、古いエントリはスキーマが小さいだけ。判定は「**空でない値を失ったか**」で行う。
- 過去の欠損16件は**未復元**（2026-07-16 時点）。復元元コミットは「実データが最多だった時点」であり意図的な削除と区別できないため、**一括復元しない**。必要になった店舗・日付だけ個別判断で復元する。

## スランプ空きコマの液晶はめ込み — 選択キー

液晶の選択単位は**機種名ではなく「画像に掲載された台番集合」**（2026-07-16・`4695044`）。`_gap_sel_key(store, bans, machine)` が正式キーを返す。

- 台番が異なる同一機種の画像（例: 並び画像2枚）は**別々の液晶を選択できる**
- 同じ台番の縦版と横版は選択を**共有**する（キーにファイル名・`_side`・レイアウト種別を含めない）
- ⑦プレビュー・⑧実行・保存画像・ZIPで同じ選択を使う。「はめ込まない」も画像単位
- 台番が取得できない場合**のみ**、従来の機種名単位キー `_gap_sel_{store}_m_{機種名}` へフォールバック
- キー生成は `hashlib.md5(f"{store}|{machine}|{ソート済み台番}")[:12]`。**組み込み `hash()` は禁止**（プロセス毎に値が変わる）
- `_on_gap_screen_change` は**同じ正式キーを持つプレビュー画像をすべて再合成**する（縦横の片方が古いまま残るのを防ぐ）。無関係な画像は再合成しない。`_gap_base` は再選択のたびに使うため pop しない
- 選択は session_state のみ（JSON永続化しない・店舗/日付/Excel切替で既定 `screens[0]` へ戻る）

**注意**: 液晶セレクタの `_IS_CLOUD` 分岐（ローカル=radio／Cloud=selectbox）は `c21f20f` で撤去済み。現在は **Cloud/ローカル共通のネイティブサムネradio＋`on_change`方式**。再導入しないこと。`st.rerun()` 直呼び・親DOM操作・`removeChild`・`MutationObserver`・`components.html` 追加も禁止（`docs/pision_cloud_notes.md` 参照）。

空き2コマ以上の判定（`_gap_fillable`）・既定値・機種選定・中央配置・`_GAP_SCREEN_SHRINK`・秋葉原の可変列判定は変更しない。設計書: `docs/superpowers/specs/2026-07-10-slump-gap-screen-fill-design.md`。

## ⑦プレビューの同名画像正規化（_dedup_previews）

⑦プレビューのリストへ**同一ファイル名の画像を複数入れてはならない**（2026-08-02・`02937be`）。

`_pv_ck_key(店舗|Excel|ファイル名)` は表示位置を含まない安定キーのため、同名要素が並ぶと
`st.checkbox` が同じ key で二重登録され **`StreamlitDuplicateElementKey`** で落ちる
（Streamlit Cloud で発生。ローカルで再現しなかったのは環境差ではなく、開いていた
Excel・店舗の入力差）。

- **正規化は `_dedup_previews()` を使い、`st.session_state[_aprev_key]` へ保存する直前で行う。**
  適用は3経路 — フルプレビュー `_prev_img_list` / 📝記入部分のみ `_manual_imgs` /
  🔄その他を更新後 `_new_prev`。
- **位置＝最初の出現位置**（画像順の正式仕様を維持。⑧の `_order` も
  `if _fn not in _order` で最初の位置を採用）。
- **内容＝最後の要素（後勝ち）**。②個別画像は `run_auto_pipeline` の**後**に同名で
  上書き保存されるため、本番の実効的な上書き順に一致する。**単純な先頭固定にしないこと**
  （プレビューと⑧本番の出力内容がずれる）。
- 異なるファイル名は削除しない。**縦版と横版（`_side`）は別名なので統合されない**（独立制御は既存仕様）。
- **`_pv_ck_key()` は変更しない。キーへ index・乱数を足すのも禁止**
  （キーはファイル名から約20箇所で逆引きされており、逆引きが壊れる）。
- 記事用ページは連番キー（`art_prev_ck_{store}_{index}`）のままで**対象外**。

**同名が積まれる経路（根本要因・未修正）**: `_prev_img_list` は
`kojin_zentai_machines` / `kojin_yushu_machines` を重複除去せずループするため、②個別画像の枠へ
**同じ機種名を2回入力**すると同名が2つ積まれる。また `run_step1_main` は
`recommended_machines` を持たないため、②全台の機種が Step1 条件も満たすと同名がもう1つ積まれる。
入力側の重複そのものは**変更していない**（同名は本番でも1ファイルへ上書きされるため出力は不変）。

`_gap_sel_key`・🎯掲載台選択（`_unit_ex_img_key`）・ban_map・結果テキスト・ZIP・判定条件は
この修正で**変更していない**。

## 新宿歌舞伎町ローテ：①〜⑥各1機種＝1枚（2026-08-12 確定・`c59dd90`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】ローテ用のみ**。
「1カテゴリ＝1機種＝1枚の画像」方式とする。

### ① 対象店舗の限定

モジュール定数 **`_ROTE_SINGLE_STORES: frozenset[str] = frozenset({"新宿歌舞伎町"})`** で一元管理し、
`show_rote_page()` 内のフラグ **`_rote_single = store in _ROTE_SINGLE_STORES`** で分岐する。
**店舗ごとにコードを複製しない。店舗追加は集合への追記だけで行う。**

**他店舗の既存仕様は変更しない**（西武新宿・新大久保等の「①②それぞれ最大6機種を1枚へまとめる」／
渋谷新館の週間表連動／上野本館の月間表連動／高田馬場／溝の口本館／その他）。
**新宿歌舞伎町専用分岐を他店舗へ一般化しない。**

### ② UI

- **①〜⑥の6カテゴリ**。各カテゴリは **「機種名1」の入力欄1個だけ**
- レイアウトは **2列×3段**（①②／③④／⑤⑥）
- 見出しは **`機種名を入力①（部分一致・1機種）`**。**他店舗の文言
  （`…（部分一致・最大6機種・入力順に表示）`）は変更しない**
- widgetキーは既存体系のまま **`rote1_mname_0`〜`rote6_mname_0`**。新キーを作らない
- 初期値は `default=st.session_state.get(f"_rote_init_{store}_{n}_0", "")` を
  `render_machine_autocomplete_input()` へ渡す（`39f1f1e` の `value=default` 仕様を踏襲）

### ③ 保存形式と後方互換（`preserve_tail`）

`rote_machines.json` の既存キー体系を使う。**新しいJSONファイルを作らない。**

| カテゴリ | ① | ② | ③ | ④ | ⑤ | ⑥ |
|---|---|---|---|---|---|---|
| 保存先 | `set1[0]` | `set2[0]` | `set3[0]` | `set4[0]` | `set5[0]` | `set6[0]` |

- `_save_rote_machines()` に **`inputs4/5/6` と `preserve_tail: bool = False`** を追加。
  **`preserve_tail=True` では各 set の index 0 だけを更新し、既存の index 1 以降を破壊せず残す。**
  非対象店舗は従来の全置換パス（`else` 分岐）をそのまま通る
- 呼び出しは2か所（機種名入力の `on_change` / 「🎰 画像を生成する」）とも `preserve_tail=True`
- **既存JSONの自動移行・削除・並べ替えはしない。**
  新宿歌舞伎町の **`set2[1] = "炎炎ノ消防隊2"` はJSON上で保持**し、**新UIでは使用しない**。
  **③へ自動移動しない。削除しない。**
- 復元は `set1`〜`set6` をループで `_rote_init_{store}_{n}_{i}` へ（`_i < len()` ガードは維持）。
  保存値が無いカテゴリは空

### ④ 画像生成

- **①〜⑥を完全に独立したカテゴリとして扱う。** 入力済みカテゴリごとに
  **通常ローテ画像1枚＋ランキング画像1枚**を生成する
- **複数カテゴリの機種を1枚へ合算しない**（ランキングもカテゴリ内の1機種のみ）
- **未入力カテゴリは生成しない**
- **`generate_rote_image()` / `generate_ranking_image()` 本体は変更しない。**
  呼び出し側から**そのカテゴリの1要素リストを渡す**方式を正式とする
  （他店舗の複数機種合成仕様を壊さないため）

### ⑤ ファイル名

既存の命名規則を維持する。

- 通常画像：**`{機種名}ローテ.png`**（機種名が空なら `ローテ①.png`〜`ローテ⑥.png`）
- ランキング：**`ranking_{機種名}ローテ.png`**（同 `ranking_ローテ①.png`〜`⑥`）
- **カテゴリ番号を自動で付け足す方式にしない。**

### ⑥ 同一機種の重複入力は生成中止

**①〜⑥に同じ機種名が2カテゴリ以上ある場合は画像生成を中止する。**
（同じファイル名になり後勝ちで上書きされるため。重複入力そのものを入力ミスとして扱う）

- 判定は `if _rote_gen_clicked:` 直下で `_dup_macs` を作り、既存分岐へ
  **`elif _dup_macs:`** を1つ足すだけ。`else:` 側の生成処理は変更しない
- 停止するので **通常画像・ランキング画像・ZIP・結果テキスト・出力フォルダ作成
  （`os.makedirs`）・`_save_rote_machines()`・`_git_auto_push()` のいずれも実行されない**
- 警告は
  `同じ機種が複数カテゴリに入力されています。①〜⑥にはそれぞれ異なる機種を入力してください。`
  ＋ `重複機種：{機種名}`（複数あれば入力順に一意化して列挙）
- **入力値を自動クリアしない／カテゴリを自動移動しない／
  重複検知処理が `rote_machines.json` を書き換えない。**
  ユーザーが画面上で修正して再実行する方式とする
- 未入力・空白のみのカテゴリは判定対象外。前後空白は `strip()` で吸収
- **重複禁止は `_ROTE_SINGLE_STORES` の店舗にだけ適用する。他店舗へ適用しない**
  （他店舗は1カテゴリ複数機種が正常な入力のため）
- 機種名入力時の通常保存は禁止しない。**重複状態でも保存・復元自体はできる。**
  「🎰 画像を生成する」を押した時点で重複が残っていれば中止する

### ⑦ 結果テキスト・プレビュー・⓪データ表

- 結果テキストは **①〜⑥の入力済み機種をカテゴリ順にフラット化**して
  `_generate_rote_result_text()` へ渡す。ポスター行の **「×」連結仕様は維持**
  （例: `🏆真打吉宗×モンハンライズ×炎炎ノ消防隊2ポスター🏆`）。台番ブロックも①〜⑥が対象
- プレビューは **2列×最大3段**。**生成されたカテゴリだけ**表示し、
  未入力カテゴリの空枠・DLボタンは出さない。DLボタンキーは `rote_dl_btn1`〜`6`
- ⓪データ表の機種フィルタは対象店舗のみ `("1"…"6")`、**他店舗は従来の `("1","2")` のまま**

### ⑧ 回帰確認（2026-08-12 実施・全PASS）

**新宿歌舞伎町**：①=`set1[0]`／②=`set2[0]` が初回描画から表示・③〜⑥は空／
F5・rerun・日付変更・店舗切替→戻る・アプリ再起動で保持／未入力カテゴリは生成なし／
各カテゴリ1機種だけの通常画像（1機種464px < 2機種632px で混在なしを確認）／
ランキングもカテゴリ内のみ（①120px < ①②合算224px）／
結果テキストの×連結と台番ブロック／②③重複で生成中止・警告表示・出力フォルダ未作成・
JSONのSHA256不変・HEAD不変（自動push未実行）・入力値保持／
③をクリアすれば通常どおり生成へ進む／Streamlit警告・例外なし。

**他店舗**：西武新宿（①6枠に5機種・②6枠）／新大久保（①6枠に5機種）／
渋谷新館（①6枠＋週間オススメ表①連動・②入力欄なし）／
上野本館（①②入力欄なし・月間オススメ表①②③のみ・`monthly_start` 維持）がいずれも従来どおり。
`_save_rote_machines()` を非対象店舗で再保存してもJSONがバイト等価。

**別件仕様への影響なし**：⑤オススメ機種ピックアップ（`39f1f1e`）・②個別画像（`0e7dc4c`）・
`render_machine_autocomplete_input()` / `_kojin_default()` / `_art_kojin_default()` /
`_save_rec_machines()` はいっさい変更していない。

## 新宿歌舞伎町ローテ：①〜⑥の機種名入力UI（2026-08-12 確定・`17efb21`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】ローテ用の①〜⑥各1機種UIだけ**。
**表示のみの仕様**で、保存・復元・画像生成・ランキング画像・結果テキスト・重複判定・
ファイル名・⓪データ表フィルタは**いっさい変更しない**（`c59dd90` の正式仕様をそのまま維持）。

### ① 見出し

- **「機種名を入力①」〜「機種名を入力⑥」だけを表示する。**
- **「（部分一致・1機種）」は表示しない。**
- 他店舗の **「機種名を入力①（部分一致・最大6機種・入力順に表示）」は変更しない。**

### ② 入力欄のラベル

- 入力欄の上に出る **「機種名 1」ラベルを表示しない。**
- 非表示には **`label_visibility="collapsed"`** を使う。
  **`"hidden"` を使わない** — `"hidden"` はラベル文字だけ消して**縦の余白が残る**ため、
  見出しと入力欄の間に隙間ができる。`"collapsed"` は余白ごと消えるので、
  見出しの直下に入力欄が来る。
- **ラベル文字列自体は空にしない。** 呼び出しは従来どおり
  `f"機種名 1{' ' * (_n - 1)}"` を渡し、**表示だけ抑制する**
  （空文字にすると Streamlit が `label got an empty value` 警告を出す）。

### ③ 共通関数への追加（`render_machine_autocomplete_input`）

```python
def render_machine_autocomplete_input(
    label: str, key: str, candidates: list[str], default: str = "",
    on_change=None, on_change_args: tuple = (),
    label_visibility: str = "visible",      # ← 追加
) -> None:
    ...
    st.text_input(label, key=key, value=default, placeholder="機種名を入力",
                  label_visibility=label_visibility, **_kw)
```

- **既定値は必ず `"visible"`。** 既定を変更してはならない。
- 実呼び出しは**合計16箇所**（docstring内の言及は件数に含めない）。
  **`"collapsed"` を渡すのは新宿歌舞伎町ローテの呼び出し1箇所だけ。**
- **他15箇所は引数を渡さず `"visible"` のまま**（②個別画像・記事用②・⑤オススメ6ブロック・
  週間表・ローテ他店舗①②・機種名変換）。ラベル表示は従来どおり。
- **`st.text_input(..., value=default)` は削らない**（⑤ `39f1f1e` の正式仕様）。

### ④ 維持するもの

プレースホルダー **「機種名を入力」**／オートコンプリート候補ボタン／**2列×3段**レイアウト／
`_ROTE_SINGLE_STORES`／`rote1_mname_0`〜`rote6_mname_0`／`_rote_init_*` の復元／
`rote_machines.json` の保存形式・`set1`〜`set6`・`preserve_tail`／`on_change`／
F5・店舗切替での保持／**⑤ `39f1f1e`・② `0e7dc4c` は無変更**。

## 新小岩②個別画像は日付（Excel）単位で保存する（2026-08-13 確定・`cf1e27a` / `ed62a6b`）

**正式仕様。巻き戻し禁止。**対象は**【新小岩】の②個別画像 `kojin_z_* / kojin_y_*` だけ**。
コード修正 `cf1e27a`、データ修正 `ed62a6b`。

- **新小岩の②個別画像は店舗単位 persistent の対象外**とする。
  新しい日付を**初めて取得したときは空欄**で始まり、**同じ日付を再取得したときだけ**
  `auto_page_inputs.json` の Excel 単位 saved 値から復元する。
  **別日に入力した②の機種名を引き継がない。**
- 実装は `_persistent_keys()` に定数
  **`_KOJIN_DATE_SCOPED_STORES: frozenset[str] = frozenset({"新小岩"})`** の分岐を追加し、
  該当店舗は `{f"variety_range_{store}"}` だけを返す（高田馬場と同じ扱い）。
  **店舗ごとにコードを複製しない。店舗追加は集合への追記だけで行う。**
- **`variety_range_新小岩` は従来どおり店舗単位 persistent。**
- **`auto_page_persistent_inputs.json` に残る新小岩の旧②値24件は削除せず残置する。**
  現行コードでは参照されない（⑤の `kojin_y_8_秋葉原` と同じ扱い）。
- **`_restore_auto_inputs()` / `_kojin_default()` / `render_machine_autocomplete_input()` /
  `st.text_input(..., value=default)` は変更していない。**
  両者が同じ `_persistent_keys()` を参照する構造を維持する（`0e7dc4c` の正式仕様）。
- **⑤オススメ機種 `rec_m*` の `store_settings` 永続化（`39f1f1e`）とは完全に別仕様。**
  ②へ⑤の永続化・初期値引き継ぎを適用しない。
- **他店舗の②保存仕様は今回変更していない**（既定は `kojin_y` 48枠＋`kojin_z` 12枠の店舗単位
  persistent のまま。新宿歌舞伎町・高田馬場・秋葉原の既存特例も不変）。

**なぜ**: 2026/8/12 の新小岩を初めて取得したのに②へ機種名が入っていた。原因は
`_restore_auto_inputs()` の永続キー優先パスで、`auto_page_persistent_inputs.json["新小岩"]` の
24件がそのまま流入していた。新小岩は `_persistent_keys()` の既定 return に落ちるため、
②が店舗単位で永続していたのが実態（バグではなく当時の設計どおりの挙動）。
`ed62a6b` で `20260812_新小岩_20S.xlsx` の `kojin_z_0〜4` / `kojin_y_0〜18` の24キーを
空へ戻した（エントリ削除はしない）。

**実機確認（2026-08-13・全PASS）**: 8/12初回取得で②24枠すべて空欄／8/12で優秀台1枠へ入力→
F5→同じ8/12を再取得で復元／②保存値の無い8/11を取得しても8/12の値・永続値を引き継がない／
⑤オススメ機種は B1=5 / B2=4 / B3=8 / B4=9 の26機種と `rec_enabled` が従来どおりで回帰なし。
コードレベルでも `_restore_auto_inputs()` と `_kojin_default()` の解決結果が
**9店舗×10Excel×60キー＝5400ケースで不一致0**。

## 新小岩②の日付切替安全化（2026-08-13 確定・`53990e5` / `e64bfac` / `f238897`）

**正式仕様。巻き戻し禁止。**上記「新小岩②個別画像は日付（Excel）単位で保存する」の追加防御。
対象は**【新小岩】の②個別画像 `kojin_z_* / kojin_y_*` だけ**。

### 保存してよい条件（不変条件）

新小岩の②を `auto_page_inputs.json` へ書き込んでよいのは、次の**2条件を両方**満たすときだけ。
1つでも欠ければ**②60キー全体**を保存対象から外し、既存 saved 値をそのまま維持する。
**残っている枠だけの部分保存も禁止。**判定は `_merge_auto_entry()` の**1か所へ集約**する
（呼び出し側へ if を散らさない）。

1. **scope 整合** — `_kojin_scope_excel_{store}` == 保存先Excel名。
   `_restore_auto_inputs()` の完了時にだけ記録する内部キーで、`_auto_input_keys()` に
   含めないため JSON へは出ない。**scope 未設定（None/空）も保存禁止**
   （restore を通った証拠が無いため）。
2. **完全性** — **`kojin_z_0〜11` + `kojin_y_0〜47` の全60キー**が session_state に存在する
   （`_kojin_keys()`）。

`show_auto_page()` 側では、保存・②描画より**前**に現在Excelについて restore 済みであることを
保証する（scope 不一致なら restore を実行）。

### なぜ完全性チェックが要るか（Streamlit widget GC）

Streamlit は「前の run で描画され、今の run で描画されなかった」widget のキーを
session_state から**削除**する。②を**48枠展開**した状態で日付を切り替えると、日付切替 run では
②が未描画になるため**可視枠が消え、折りたたみ中で plain 値だった枠（`kojin_y_12〜47` 等）
だけが残る**欠損状態になる。この状態は scope が旧Excelと一致したままなので**scope判定だけでは
検出できず**、「②合計非空=0」を旧日付へ書いて実入力を全消しする（8/6 の14件消失の直接原因）。
実機診断で `保存先=8/6 / scope=8/6 / ②合計非空=0 / z:存在0件 / y:存在36件[12〜47]` を捕捉して確定した。
`kojin_y_12〜18` だけが別日へ焼き付く現象（8/2）も同じ機構。

### 無変更

`value=default`（⑤ `39f1f1e`）／`_kojin_default()` の解決ルール／`_restore_auto_inputs()` の
基本仕様／widget key 体系／session_state キーの直接 del はしない／
`_KOJIN_DATE_SCOPED_STORES`（現在**新小岩のみ**）／⑤ `rec_m*`・`store_settings`／記事用②／
他店舗の②／`variety_range_*`／`kojin_enabled`／末尾・その他 auto 入力。

### 実機確認（2026-08-13・全PASS）

8/6の実入力14件を表示 → **48枠展開** → 8/12へ切替で**8/6の14件は破壊されず**、
**8/12への流入0件**（hidden枠も空）／8/12→8/6で**14件復元**／visible枠（12枠目）の同日入力を保存／
hidden枠（20枠目）の同日入力を保存／別日（8/10）へ切替後も旧日付の値を維持／⑤回帰なし。
擬似 session_state でも A〜J の全ケース PASS。

### 過去汚染データの整理（`e64bfac`）

旧コード時代に永続値が日付エントリへ焼き付いた分を、エントリ・キー単位で整理した。

| 日付 | 整理内容 |
|---|---|
| 8/2 | 永続由来の hidden 値 `kojin_y_12〜18`（7件）を除去 |
| 8/6 | **実入力14件（`kojin_z_0〜4` / `kojin_y_0〜8`）を残し**、永続由来の `kojin_y_9〜18`（10件）のみ除去 |
| 8/10 | 永続値と完全一致の②24件を除去 |
| 8/11 | 本来存在しないテスト／汚染エントリを削除 |
| 8/12 | ②60キーを空へ復旧 |

`auto_page_persistent_inputs.json` の新小岩の旧②24件は**削除せず残置**（現行コードでは未参照）。

## 上野新館②個別画像の日付単位保存（2026-08-13 確定・`2ffac04`）

**正式仕様。巻き戻し禁止。**対象は**【上野新館】の②個別画像だけ**。

- **上野新館を `_KOJIN_DATE_SCOPED_STORES` へ追加**した（集合への追記のみ。**店舗専用ロジックの複製なし**）。
- 上野新館の② **`kojin_z_0〜11` / `kojin_y_0〜47` は店舗単位 persistent の対象外**。
  `_persistent_keys("上野新館")` は **`variety_range_上野新館` の1キーだけ**を返す（61キー → 1キー）。
- **未保存日の初回取得は②全枠空欄。**同じ日付の saved 値だけを
  `auto_page_inputs.json` から復元する。
- **日付保存が空欄なら旧 persistent 値を復活させない。**
- **`variety_range_上野新館` は従来どおり店舗単位 persistent。**
- `auto_page_persistent_inputs.json` の上野新館の旧②値（`kojin_z_0〜3` = うみねこ2／
  ハピジャグV／ミスジャグ／クレアの秘宝伝、`kojin_y_15` = マイジャグV ほか計19件）は
  **削除せず残置**（新仕様では参照されない）。
- 新小岩で実装済みの **scope管理（`_kojin_scope_excel_{store}`）・scope未設定/不一致で②保存禁止・
  ②60キー完全性チェック・部分保存禁止・48枠展開後の widget GC 対策**を、同じ集合を参照して
  **共通利用**する。
- **他店舗の②保存仕様は今回変更していない**（上野本館・稲毛・西武新宿・渋谷新館・溝の口本館／新館・
  赤坂見附・新大久保は従来どおり61キー。新宿歌舞伎町・高田馬場・秋葉原の既存特例も不変）。

**なぜ**: 上野新館②は店舗単位 persistent のままだったため、日付エントリへ空文字で保存した枠に対し
`_restore_auto_inputs()`（5213-5215行）/ `_kojin_default()`（5249-5253行）の
**「永続キーは保存値が空でも永続値を優先」パス**が働き、**ユーザーが消した古い機種名が
再取得時に復活**していた（8/12で `kojin_z_0〜3` と `kojin_y_15` が復活）。
`_save_persistent_inputs()` は「非空のときだけ上書き」なので、枠を空にしても永続値は消えない。

**実機確認（2026-08-13・全PASS）**: 8/12では前日入力した優秀台14件だけが復元／
古い `kojin_z_0〜3` は復活しない／古い `kojin_y_15` も復活しない／48枠展開後も旧 persistent 値は
出ない／未保存日（8/11）は全枠空欄／8/12→8/11で14件の流入なし／8/11→8/12で14件復元／
**48枠展開状態の日付切替でも8/12の14件を破壊しない**／⑤・`variety_range` 回帰なし。
擬似 session_state でも A〜G の全ケース PASS（`_restore_auto_inputs()` と `_kojin_default()` の
解決結果は12Excel×60キーで不一致0）。

## 上野本館②個別画像の日付単位保存（2026-08-13 確定・`b96012a`）

**正式仕様。巻き戻し禁止。**対象は**【上野本館】の②個別画像だけ**。

- **上野本館を `_KOJIN_DATE_SCOPED_STORES` へ追加**した（集合への追記のみ。**店舗専用ロジックの複製なし**）。
- 上野本館の② **`kojin_z_0〜11` / `kojin_y_0〜47` は店舗単位 persistent の対象外**。
  `_persistent_keys("上野本館")` は **`variety_range_上野本館` の1キーだけ**を返す（61キー → 1キー）。
- **未保存日の初回取得は②全枠空欄。**同じ日付の saved 値だけを復元する。
- **saved が空欄なら旧 persistent 値を復活させない。**
- **`variety_range_上野本館` は従来どおり店舗単位 persistent。**
- `auto_page_persistent_inputs.json` の **`kojin_z_0_上野本館 = ミスジャグ`** は
  **削除せず残置**（新仕様では参照されない）。既存22日付の saved 値も変更しない。
- 新小岩・上野新館と同じ **scope管理（`_kojin_scope_excel_{store}`）・scope未設定/不一致で②保存禁止・
  ②60キー完全性チェック・部分保存禁止・48枠展開後の widget GC 対策**を**共通利用**する。
- **他店舗の②保存仕様は今回変更していない**（稲毛・西武新宿・渋谷新館・溝の口本館／新館・赤坂見附・
  新大久保は従来どおり61キー。新宿歌舞伎町・高田馬場・秋葉原の既存特例も不変）。

**なぜ**: 上野新館とまったく同じ構造。日付エントリへ空文字で保存した枠に対し
`_restore_auto_inputs()` / `_kojin_default()` の「永続キーは保存値が空でも永続値を優先」パスが働き、
**`kojin_z_0_上野本館 = ミスジャグ` が21日付で復活**していた（未保存日の初回取得にも流入）。

**実機確認（2026-08-13・全PASS）**: saved空欄の 8/5 で**ミスジャグ復活なし**／saved値ありの 7/3 で
日付固有の優秀台5件だけ復元（ミスジャグの追加なし）／未保存日 8/11 は全枠空欄／
**7/3を48枠展開→8/11へ切替でも7/3の5件を破壊しない**／8/11へ7/3値の流入なし／
8/11→7/3で5件復元／同日入力保存が正常／⑤・`variety_range` 回帰なし。
擬似 session_state でも A〜H の全ケース PASS（`_restore_auto_inputs()` と `_kojin_default()` の
解決結果は1440ケースで不一致0）。

## 稲毛②個別画像の日付単位保存（2026-08-18 確定・`4431fad` / `41c4222`）

**正式仕様。巻き戻し禁止。**対象は**【稲毛】の②個別画像だけ**。

- **稲毛を `_KOJIN_DATE_SCOPED_STORES` へ追加**した（集合への追記のみ。**店舗専用ロジックの複製なし**）。
- 稲毛の② **`kojin_z_0〜11` / `kojin_y_0〜47` は店舗単位 persistent の対象外**。
  `_persistent_keys("稲毛")` は **`variety_range_稲毛` の1キーだけ**を返す（61キー → 1キー）。
- **未保存日の初回取得は②全枠空欄。**同じ日付の saved 値だけを
  `auto_page_inputs.json` から復元する。
- **saved が空欄なら旧 persistent 値を復活させない。**
- **`variety_range_稲毛` は従来どおり店舗単位 persistent。**
- `auto_page_persistent_inputs.json` に残る稲毛②の旧11件（`kojin_z_0〜4` = Lハナビ／戦国乙女5／
  モンハンライズ／戦コレ6／戦国乙女4、`kojin_y_0〜5` = マギレコ／ゴージャグ3／東京喰種／
  ゴージャグ3／戦国乙女5／マイジャグV）は**削除せず残置**（新仕様では参照されない）。
- 新小岩・上野新館・上野本館と同じ **scope管理（`_kojin_scope_excel_{store}`）・scope未設定/不一致で
  ②保存禁止・②60キー完全性チェック・部分保存禁止・widget GC 対策**を、同じ集合を参照して
  **共通利用**する。
- **他店舗の②保存仕様は今回変更していない**（上野本館・西武新宿・渋谷新館・溝の口本館／新館・
  赤坂見附・新大久保は従来どおり61キー。新宿歌舞伎町・高田馬場・秋葉原の既存特例も不変）。

**なぜ**: 上野新館・上野本館とまったく同じ構造。稲毛は `_persistent_keys()` の既定 return に
落ちるため②が店舗単位 persistent のままで、`_restore_auto_inputs()` / `_kojin_default()` の
「保存値にキーが無ければ永続値を優先」パスから、**8/17を初めて取得したときに永続値11件が流入**し、
そのまま毎レンダー保存で日付エントリへ焼き付いていた。

**8/17の汚染データ整理（`41c4222`）**: `20260817_稲毛_20S.xlsx` の**②60キーをすべて空へ戻した**。
上記11件は persistent と完全一致する流入値でユーザーの実入力ではない。
**エントリ自体は削除せず、②以外の29キー**（`kojin_enabled` / 末尾 / ジャグラー末尾 / narabi /
sonota_extra / variety / kojin_pick）**は現在値のまま維持**。他店舗・他日付は変更していない。

**実機確認（2026-08-18・全PASS）**: 8/17初回表示で②24枠すべて空欄／persistent旧11件の復活なし／
同日入力（優秀台1枠目）が8/17へだけ保存され F5・再取得で復元／未保存日 8/16 は②全枠空欄／
8/17の値が8/16へ流入しない／8/16→8/17で同日値だけ復元／②OFF→ON・日付切替で 8/17 の saved 値を
破壊しない／稲毛固有機能（①データ表・並び台番範囲・個別機種の優秀台ピックアップ・
その他の優秀台ピックアップ・③並び・④末尾・ジャグラー末尾・⑤・⑥・⑦・⑧）の回帰なし／
新小岩・上野新館・上野本館の回帰なし。擬似 session_state でも A〜I の16項目すべて PASS
（他店舗12店 × 41Excel = 43,788ケースで `_restore_auto_inputs()` の結果に不一致0）。

**別件（今回の対象外）**: **「⓪日付取得後に②個別画像の入力欄が一時的に描画されない」既知事象**は
`39f1f1e` 以前から存在する別問題で、今回の修正対象ではない（描画ゲートは `if kojin_enabled:` のみで
今回いっさい変更していない）。データ損失ではなく、リロード・再取得で正常に描画され値も保持される。
詳細は「②個別画像の初期値受け渡しと保存タイミング（2026-08-10 確定・`0e7dc4c`）」の
「今回の対象外」を参照。

## 残り6店舗②個別画像の日付単位保存（2026-08-18 確定・`3dfa9f0`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館・西武新宿・新大久保・溝の口本館・溝の口新館・
赤坂見附】の②個別画像だけ**。これで②が店舗単位 persistent（61キー）の店舗はゼロになった。

- **上記6店舗を `_KOJIN_DATE_SCOPED_STORES` へ追加**した（集合への追記のみ。**店舗専用ロジックの複製なし**）。
- 6店舗の② **`kojin_z_0〜11` / `kojin_y_0〜47` は店舗単位 persistent の対象外**。
  `_persistent_keys(store)` は **`variety_range_{store}` の1キーだけ**を返す（61キー → 1キー）。
- **未保存日の初回取得は②全枠空欄。**同じ日付の saved 値だけを
  `auto_page_inputs.json` から復元する。
- **saved が空欄なら旧 persistent 値を復活させない。**
- **`variety_range_*` は従来どおり店舗単位 persistent を維持。**
- `auto_page_persistent_inputs.json` に残る6店舗の旧②値（渋谷新館5件・西武新宿3件・
  新大久保3件・溝の口新館2件・溝の口本館0件・赤坂見附0件）は**削除せず残置**
  （新仕様では参照されない）。
- 新小岩で導入した **scope管理（`_kojin_scope_excel_{store}`）・②60キー完全性チェック**を
  同じ集合を参照して**共通利用**する。
- **scope 未設定／不一致では②を保存しない。**
- **②60キーが欠損しているときは部分保存しない**（残っている枠だけの保存も禁止）。
- `_restore_auto_inputs()` / `_kojin_default()` / `_merge_auto_entry()` の**ロジック本体は無変更**。

**なぜ**: 6店舗はいずれも `_persistent_keys()` の**既定61キー return に落ちていただけ**で、
②を別日へ持ち越す明示的な正式仕様は CLAUDE.md・Git履歴・コードコメントのどこにも無い。
61キー既定は導入時 `b876c86` の `range(8)` が `3e5ee1d`／`a9cf4e1`（秋葉原の機能追加）で
一般拡張された結果であり、店舗ごとの意図ではない。監査時点で
「saved が空欄なのに旧 persistent 値が復活する」日が渋谷新館33日・西武新宿25日・
溝の口新館11日・新大久保1日あった（溝の口本館・赤坂見附は persistent② が0件のため予防的追加）。

**監査結果（2026-08-18）**:

| 区分 | 店舗 | `_persistent_keys()` |
|---|---|---|
| **61キー既定** | **なし（ゼロ）** | — |
| 9キー特例 | 秋葉原（②優秀台 UI 1〜8枠のみ永続・`611a452`） | 9 |
| 既存特例 | 新宿歌舞伎町（②優秀台は毎回空欄）／高田馬場（日付単位） | 1 |
| ②日付単位 | 上記2店を含む**12店舗**（`_KOJIN_DATE_SCOPED_STORES` は10店） | 1 |

**確認結果（全PASS）**: 対象6店舗で**未保存日への persistent 流入なし**／**saved空欄日で旧値復活なし**
（旧コードなら渋谷新館5件・西武新宿3件・溝の口新館2件が復活する日で検証）／
**saved値あり日はその日付の saved のみ復元**（西武新宿6/13=2件・溝の口新館6/24=2件・
新大久保7/27=3件が完全一致、余計な追加なし）／**同日入力の保存・復元が正常**／
**別日への流入なし**／**`variety_range_*` 維持**／**既存4店舗（新小岩・上野新館・上野本館・稲毛）
への回帰なし**／秋葉原・新宿歌舞伎町・高田馬場の既存特例も不変
（対象外7店 × 46Excel = 28,658ケースで `_restore_auto_inputs()` の結果に不一致0）。
実機確認は渋谷新館・西武新宿・溝の口新館・新大久保、コード検証は6店舗すべてで実施。

### 【別案件・保留】日付往復時に別日の saved 値が空上書きされる事象

**今回の6店舗日付単位化とは切り離して保留する。推測での修正はしない。**

- 2026-08-18 の実機確認中、**渋谷新館 8/4 で `kojin_y_0`=SAOII / `kojin_y_1`=ファンキー2 /
  `sonota_extra_title` の3件が一度だけ空上書きされた**（値は HEAD から復元済み）。
- **再現条件・根本原因とも未確定。**単一セッション／複数セッション／②OFF→ON／日付往復／
  サーバー再起動＋古いタブ再接続のいずれでも**再現せず**、診断ログを注入したサンドボックスでも
  **破壊イベントを捕捉できなかった**。
- 判明した構造的事実のみ記録する：`sonota_extra_title` を含む**②以外の29キーには日付scopeガードが無く**、
  session_state に存在すれば保存先Excelへ無条件に書かれる／`auto_page_inputs.json` には
  **排他制御が無く last writer wins**（`_save_auto_inputs()` は毎回最新JSONを読み直すため
  古い辞書の保持はない）／日付切替runの入口では widget GC により②キーが不完全（実測36/60）で、
  結果として②の完全性チェックと「キー不在」が偶然の防御になっている。
- **今回の6店舗追加が原因ではない**ことは確認済み。`_merge_auto_entry()` の `_skip_kojin` は
  対象店舗に制限を加えるだけで、**変更後の書き込みは変更前の厳密な部分集合**
  （②キーの書き込み 60 → 2、変更後だけが書き込むキーは無し）。
- **今後、本番で再発した場合にその時点の操作・ログを使って再調査する。**

## 機種名変換

`機種名変換.xlsx`（2行目をヘッダーとして読み込む、B列=変換前, C列=変換後）を `load_name_map()` でキャッシュ。完全一致 → 正規化一致（スペース・全角除去）の順で変換。`@st.cache_data` でセッション中は再読み込みしない。

## 高田馬場 記事用WordPress下書き連携（2026-08-21 確定・`17b17be`）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】の📰記事用ページだけ**。
生成済みの記事用画像から WordPress（https://slotterguild3.com）へ**下書き（draft）を1件作成**する。
実装は **`wp_client.py`（新規）** と **`streamlit_app.py` の2ブロック（+87行）**のみ。
既存の記事用画像生成・Pision取得・②〜⑤の入力仕様・他店舗はいっさい変更していない。

### ① 対象と起動導線

- **高田馬場の記事用ページのみ**（`if store == "高田馬場":` で分岐）。**他店舗へ展開しない。**
- ⑧本番の内側で `wp_client.build_payload()` の結果を
  `st.session_state["_art_wp_payload_高田馬場"]` へ保存する。`result` は**読むだけ**。
  保存は **`_git_auto_push()` より前**に行う（stash 窓に入れないため）。
- 送信ボタン **「📝 WordPress下書きを作成」**（key=`art_wp_draft`）は
  **⑧とは独立した別ボタン**。⑧の実行で自動送信はしない。
- payload が無い（＝⑧未実行）ときはボタン自体を表示しない。

### ② 投稿設定（変更禁止）

| 項目 | 値 |
|---|---|
| `WP_STATUS` | **`"draft"`**（**publish は絶対に作らない**） |
| `WP_CATEGORY_ID` | **24**（エスパス高田馬場） |
| `WP_AUTHOR_ID` | **14** |
| tags / featured_media / excerpt / template / meta | **送らない** |

- **新規 draft の作成だけ**を行う。**既存投稿を update しない。**
- **既存メディアを削除しない**（テストメディアも含む）。
- 書式の基準は **58109型**の記事。

### ③ 認証（`st.secrets` → `os.getenv`）

`wp_client._secret(name)` が **`st.secrets` を優先し、無ければ `os.getenv`** を返す。

- `streamlit` は**関数内 try import**（`requests` / `PIL` と同じ流儀）。
  トップレベル import しない。**Streamlit 外の通常 Python から import しても壊れない。**
- **`streamlit_app.py` の `get_secret_value()` は使わない**（循環 import になるため）。
- ローカルは `.env`（`load_dotenv` 済み）→ `os.getenv` で従来どおり動く。
- **Cloud Secrets（Settings → Secrets・TOML）に必要な3キー**：

  ```
  WP_SITE_URL
  WP_USER
  WP_APP_PASSWORD
  ```

- **認証情報をコードへ直書きしない。値をログ・画面・例外へ出さない。**
  `config_ready()` のメッセージは**キー名のみ**（`未設定: WP_SITE_URL, …`）。
- 3値が揃わないときは `config_ready() == False` を返し、
  UI は警告を出して**ボタンまで到達しない**（誤送信しない安全側の失敗）。
- `.env` は git 管理外（`.gitignore`）。**commit しない。**

### ④ 本文構成（`plan_blocks()` / `build_content()`）

上から順に：

1. **全台系濃厚機種** — H2 →（**H3 + 画像**）× 機種数。H3 は `h3_zendai()`
   （`機種名 (プラス台数/総台数台+) ➡平均 ±○○枚`）。平均差枚の降順。
2. **1/2系以上の高配分機種** — H2 →（**H3 + 画像**）× 機種数。
   **赤文字の機種一覧は出力しない**（`blk_para_high()` は定義のみ残置・未使用）。
   H3 は**全台系と同じ `h3_zendai()` を流用**する（新書式を作らない）。
   画像は `_resolve_high_images()` が**自動 `_高配分.jpg` と手動 `（優秀台）.jpg` を判別**する。
   **記事用ページでユーザーが手動指定した高配分画像＋自動抽出された高配分画像の両方**を使う。
3. **ジャグラー** — H2 → 個別高配分画像（あれば H3 + 画像）→ **ジャグラーシリーズ優秀台.jpg**。
   **青文字の機種一覧は出力しない**（`blk_para_juggler()` は定義のみ残置・未使用）。
4. **並び** — H2 →（H3 `h3_narabi()` + 画像）× 並び数。
5. **その他単品優秀台** — H2 → **その他の優秀台ピックアップ.jpg**。
6. **シマズをチェック！** — 見出しのみ（画像は人間が挿入する）。
7. **店舗情報・過去の結果はコチラ** ボタン（`blk_button()` / slug=`espace-takadanobaba`）。

ジャグラー統合画像・その他ピックアップは `optional`（無ければ本文へ入れないだけで中止しない）。

### ⑤ 長尺画像のWordPress送信用分割

- サイトは**長辺 2560px 超の画像を 2560px へ縮小**する（2026-08-20 実測）。
  縦長1枚のままだと**幅が453px等まで潰れる**ため、`WP_MAX_SIDE = WP_SPLIT_MAX_H = 2560` として
  **各片の高さを2560px以下**に収め、縮小を回避して元の幅を保つ。
- 対象は **ジャグラーシリーズ優秀台.jpg / その他の優秀台ピックアップ.jpg** のような縦長画像
  （`needs_split()` の判定による。特定ファイル名の決め打ちではない）。
- **切れ目は表の行境界へスナップする**（`_row_boundaries()` / `_snap_cut()` /
  `_CUT_SEARCH = 200` / `_UNIFORM_STD = 12`）。**行の途中で切らない。**
  さらに **JPEGのDCTブロックに合わせて8px境界（`_MCU = 8`）へ寄せる**
  （実測: 平均差 4.556 → 0.540）。
- **リサイズは一切しない（crop のみ）。分割片の間に余白を入れない。**
  WordPress上で1枚の縦長画像のようにつながって見えること。
- 保存は **`_SPLIT_QUALITY = 95` / `_SPLIT_SUBSAMPLING = 0`（4:4:4）**。
  **省略すると PIL 既定の 4:2:0 になり、「台番帯の色が変わる」「荒くなる」**（実測で確定）。
- **原本は読み取るだけ**。分割は `tempfile.mkdtemp(prefix="wp_split_")` の
  **送信用一時コピー**に対して行う。一時ファイルは**成功・失敗とも自動削除しない**
  （失敗時の再調査のため）。

### ⑥ 画質定数（1200へ戻さない）

```
_ART_HQ_SCALE     = 2.0
_ART_HQ_TARGET_KB = 5500
_ART_HQ_MIN_ROWS  = 10
```

`_ART_HQ_TARGET_KB` は **1200 → 5500** へ変更した（`streamlit_app.py`）。
2倍描画で画素数が20倍以上になるため、1200KBでは圧縮が強すぎて
**レインボー階調が15〜40段まで潰れ**、パネル・台番帯・文字・罫線が劣化していた。
5500KBは実質的に `_save_jpeg()` の上限 q95 を使わせるための余裕値。
変更後、対象2枚は約1.24MB → 約5MB台になった。
**理由なく 1200 へ戻さない。別方式へ変更しない。**

### ⑦ 送信処理（All-or-Nothing・二重作成防止）

`create_takadanobaba_draft()`：

- **送信前に必須ファイルを検証**し、欠けていれば**1枚もアップロードせず中止**する
  （UI にも不足ファイル名を表示し、ボタンを disabled にする）。
- 画像を**逐次アップロード**し、**途中で失敗したらその場で中断して投稿を作成しない**。
- **アップロード済みメディアを自動削除しない**。UI に media ID を表示し、
  不要なら WordPress 管理画面で人間が削除する。
- **二重作成防止**：作成済みなら投稿IDと編集URLを表示し、
  **「もう一度作成する」にチェックしない限りボタンを押せない**
  （session_state キー `_art_wp_post_{store}_{dir_stem}`）。送信中は `_art_wp_busy_{store}` で二重押下を防ぐ。
- 日本語ファイル名は Phase 1 で実証した方式（`Content-Disposition` の `filename*`）で送る。

### ⑧ Cloud 互換性

- パスは `os.path.join` のみ（Linux可）／一時ファイルは `tempfile`／通信は `requests`／
  画像は `pillow`。**`requirements.txt` への追加は不要**（pillow・requests・python-dotenv は既存）。
- **Cloud で追加設定が必要なのは上記 Secrets 3キーだけ。**
- **Cloud 実機確認は未実施**（2026-08-21 時点）。ローカルのみ確認済み。

### ⑨ 実機確認済み事項（2026-08-20・ローカル）

- ローカルから **WordPress 下書きの作成に成功**し、プレビューを目視確認した。
- **18ファイルの送信を確認**。
- **高配分画像の H3（機種名＋台数＋平均差枚）が正常**に表示される。
- **表示幅に問題なし**（分割により幅が潰れない）。
- **レインボー背景の画質が改善**（ジャグラー・その他優秀台とも）。
- **パネル部分・台番帯・文字・罫線**いずれも改善を確認。

### ⑩ ファイルの扱い

- **本実装**: `wp_client.py`（新規）／`streamlit_app.py` の WordPress 2ブロック＋`_ART_HQ_TARGET_KB`。
- **`wp_test.py` / `WordPress連携テスト.jpg` は Phase 1 のテスト用**で、
  **本番コードからの参照は0件**。**正式 commit の対象外**とし、untracked のまま保持する。
  削除もしない。
- `.env` は commit しない。

### ⑪ Cloud 実機確認と403の原因（2026-08-21 確定）

**Streamlit Cloud からの下書き作成が動作することを実機で確認した。**
ローカル専用機能ではない。以下は実測結果であり、推測を含まない。

#### Cloud で動かすための前提

1. **Cloud Secrets（Settings → Secrets）へ3キーを登録する。**

   ```
   WP_SITE_URL / WP_USER / WP_APP_PASSWORD
   ```

   Cloud に `.env` は存在しないため、`_secret()` の `st.secrets` 経路で読む。
   **値はコードへ直書きしない。commit しない。**
2. **push しただけでは Cloud へ反映されないことがある。**
   2026-08-21 の実測では、push（`17b17be` 03:37 UTC / `733aa5c` 03:38 UTC）後も
   Cloud は旧 `1cf78b9` を実行し続け、**WordPress セクションが表示されなかった**。
   **Secrets 保存による再起動でもコードは更新されない**（プロセス再起動のみ）。
   **Manage app → Reboot を明示実行**して初めて
   `Pulling code changes from Github...` → `Updated app!` が出て `733aa5c` が反映された。
   稼働中コードの判定は、**ログのトレースバックの行番号を実ファイルと突き合わせる**のが確実
   （旧20382行 / 新20467行）。

#### 403 の原因（確定）

Reboot 後の初回送信は **1枚目のアップロードで `status=403` / 非JSON HTML 2,843バイト**で失敗した。

- **WordPress 本体ではない。** REST API は認証・権限エラーを**必ず JSON で返す**
  （実測: 未認証 GET `/wp/v2/users/me` → 401 / 142バイト / `rest_not_logged_in`）。
- Cloudflare / Sucuri 等の CDN型WAF は不使用（`CF-Ray` / `X-Sucuri-ID` なし。`Server: nginx`）。
- セキュリティプラグインでもない。有効なのは **CloudSecure WP Security** だけで、
  その **「REST API 無効化」「シンプルWAF」はいずれも OFF**（XML-RPC無効化等は ON）。
- サーバーは **エックスサーバー**（`sv16415.xserver.jp` / `ns1〜5.xserver.jp`）。

**原因は Xserver の「WordPressセキュリティ設定 → 国外アクセス制限設定 → REST APIアクセス制限」。**
Streamlit Cloud は **AWS の国外IP** から接続するため、この設定が ON の間は
`POST /wp-json/wp/v2/media` が**サーバー側でHTMLの403として遮断**されていた。
**ローカル（国内IP）では同一コード・同一認証で成功していた**ため、差分は送信元IPだけだった。

**対処＝「REST APIアクセス制限」を OFF にする。**
管理画面・XML-RPC の国外アクセス制限は ON のまま維持できる。
**Xserver の国外アクセス制限にIP許可リストは無く、Cloud の送信元IPも固定されない**ため、
「Cloud のIPだけ許可」という運用はできない。

#### 実機確認結果（2026-08-21・Cloud から実行・全成功）

REST APIアクセス制限を OFF にした後、Cloud の記事用ページから **8/19・8/20 の2日分**を
⑧実行 →「📝 WordPress下書きを作成」で送信し、**いずれも成功**した。

| 対象日 | 投稿ID | タイトル | media | status / category / author |
|---|---|---|---|---|
| 8/19 | **59621** | `8月19日(水)│エスパス高田馬場│` | **18件**（ID 59603〜59620） | draft / 24 / 14 |
| 8/20 | **59644** | `8月20日(木)│エスパス高田馬場│` | **21件**（ID 59623〜59643） | draft / 24 / 14 |

- 送信対象は表示上10枚だが、**長尺画像の分割により実際のメディアは18件・21件**になる（仕様どおり）。
- **403 は解消**。401 / 403 / 429 / 500 系のエラーは**0件**。
- メディア総数 48,338 → 48,377（**+39件＝18+21**）。**既存メディアの削除・変更なし。**
- **既存投稿の update は発生していない**（本機能は新規 draft 作成のみで、update/DELETE を実装しない）。
- カテゴリ「エスパス高田馬場」= **term_id 24**、投稿者 `t.ui` = **user_id 14** を管理画面で確認。
- Cloud の **最大 RSS は 1,148.1 MB**。`run_auto_pipeline` は 899.5 → 921.0 MB。
  **Killed / OOM / MemoryError / Connection reset は0件**。
  ただし Cloud の上限（約1GB）に近いため、**⑧と送信の間にコンテナ再起動が起きると
  `session_state` の payload が消え、ボタンが消える**（実際に1度発生）。
  **⑧完了後は間を置かずに送信する**こと。再起動しても WordPress へは何も送られない
  （実測: メディア0件・投稿0件）。

#### 参考（本機能とは無関係の変化）

同日 14:13 に既存の下書き **ID 59566** がゴミ箱へ移動している（ゴミ箱 10 → 11件）。
**本機能は投稿の削除・ゴミ箱移動を一切実装していない**ため、これは人手による操作である。

### ⑫ 記事上部ポスター・テキスト・日付別セッション保持（2026-08-21 確定）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】の📰記事用ページだけ**。
関連コミット: `eccc2cc`（feat: 記事に上部ポスターとテキスト欄を追加）→
**`166c05a`（fix: ポスターを日付ごとにセッション保持）**。
`wp_client.py` の `build_poster()` / 分割処理 / 投稿設定は**この2commitで確定済み・以後変更しない**。

#### 記事上部の正式順序

```
その日の見出し
  ↓
ポスター（複数枚は横結合した1枚）
  ↓
ポスター下文章
  ↓
X手動挿入用の空段落 × 3
  ↓
Xリンク下文章
  ↓
全台系          ← ここから下は既存のまま（一切変更しない）
  ↓
高配分 / ジャグラー / 並び / その他優秀台 / シマズ / 店舗情報ボタン
```

#### ① 入力UI（テキスト3枠）

- **その日の見出し**：1行入力（`art_wp_top_heading_{store}`）
- **ポスター下文章**：複数行（`art_wp_top_text_poster_{store}`）
- **Xリンク下文章**：複数行（`art_wp_top_text_x_{store}`）
- 3枠とも **Excel（日付）単位で保存**する。`_article_input_keys()` に登録し、
  保存は既存の `_save_article_inputs(store, skip_kojin=True)`（マージ方式）を使う。
  **②個別画像の機種名を巻き込まないため `skip_kojin=True` を必ず渡す**（`0e7dc4c` の正式仕様）。
- 改行で段落を分ける。空欄ならブロックごと出力しない。

#### ② ポスターUI

- 位置は **記事用の①Excelアップロードの直後**（②個別画像の直前）。`_sec_num()` で採番する。
- **複数枚アップロード可**（jpg / jpeg / png）。
- 表示は **「保存済みポスター：N枚」＋小プレビュー＋1枚単位の🗑️削除＋すべて削除＋新規追加欄**。
- 並びは **左から 1, 2, 3 … の順で結合**する。番号をプレビューに表示する。
- **新規追加は常に末尾へ追加**する。
- **ドラッグ並べ替えは未実装**（今回の対象外）。
- **file_uploader へ保存済みファイルを戻す実装はしない**
  （Streamlit にアップロード済み状態を復元する API が無いため。保存済み一覧と新規追加欄を分ける）。

#### ③ ポスター結合（`wp_client.build_poster()`・変更禁止）

- **元画像を1枚1枚保持**し、⑧のたびに**保存済み元画像から作り直す**（結合済み画像は保持しない）。
- 2枚以上は **横一列**に連結。**最も小さい高さへ統一**（拡大しない）・**アスペクト比維持**・
  **クロップなし**・**余白なし**・縮小は **`Image.LANCZOS`**。
- **長辺が `WP_MAX_SIDE`(2560) を超えるときだけ**全体を縮小する。`WP_MAX_SIDE` は変更しない。
- 保存は **`POSTER_QUALITY = 95` / `POSTER_SUBSAMPLING = 0`（4:4:4）**。
- **PNG等の透過は白背景へ合成**してから JPEG 化する。
- 出力は **`POSTER_FN = "_wp_poster.jpg"`**（`output_dir` 直下）。**ZIPにも収録**される。
- 既存の**長尺画像分割（`split_image_for_wp`）とは別用途**。`_SPLIT_QUALITY` / `_SPLIT_SUBSAMPLING` /
  `_MCU` / 行境界分割には**一切触れない**。

#### ④ 日付別セッション保持（正式キー）

```
_art_poster_imgs_{store}_{excel}   … 保存済み元画像 [{"name","fid","data"}, …]
_art_poster_seen_{store}_{excel}   … 取り込み済み file_id の一覧
```

- **ウィジェットキーではない通常の session_state 値**として持つ。
  file_uploader のキーは Streamlit の **stale widget GC**
  （`session_state._remove_stale_widgets()`：前の run で描画され今の run で描画されなかった
  ウィジェットの状態を削除する）で消えるため、**日付を往復するとアップロード済みファイルが失われる**。
  上記キーは GC の対象外なので復元できる。
- キーに **店舗と Excel名（日付）の両方**を含める。**別日への流入は構造的に起きない。**
- 保持するのは **filename / file_id / bytes**。
- **重複追加防止は `UploadedFile.file_id`**（Streamlit 1.56.0 で一意ID・`__eq__`/`__hash__` も file_id 基準）。
  取り込み済み集合にある file_id は追加しない。
- **削除しても `seen` からは外さない。** 外すと file_uploader に残っている同じファイルが
  次の rerun で再取り込みされ、**削除した画像が復活する**。
- 削除は `on_click=_art_poster_delete(store, excel, fid)`。**`st.rerun()` の直呼びはしない。**

#### ⑤ 正式な制限（今回の対象外）

**「同一セッション中の日付往復で復元」までが正式仕様。**
次をまたいだ復元は**実装しない**：**F5 / ブラウザ再接続 / ローカルアプリ再起動 /
Cloud Reboot / コンテナ再作成**。

**画像を JSON・base64・GitHub へ永続化しない**（`article_page_inputs.json` にも入れない）。
`_git_auto_push()` の対象にも画像を追加しない。

#### ⑥ ⑧実行時の参照経路

- **file_uploader の現在値を正として使わない。**
- **`_art_poster_list(store, excel)` の保存済み元画像が唯一の正。**
- `元画像 bytes → tempfile.mkdtemp() へ書き出し → build_poster() → output_dir/_wp_poster.jpg`。
- **`wp_client.build_poster()` は変更しない**（呼び出し側からパスのリストを渡すだけ）。

#### ⑦ ポスター0枚のときの古い `_wp_poster.jpg` 対策

ローカルの `output_dir` は実行をまたいで残るため、**前回の `_wp_poster.jpg` が残っていると
`plan_blocks()` の `os.path.isfile()` 判定で拾われ、古いポスターが本文へ混入する**
（テストで実証済み）。

→ **保存済みポスターが0枚のときだけ、既存の共通ヘルパー
`_rm_stale_image(output_dir, POSTER_FN)` を呼ぶ。**
連番除去後の**完全一致のみ削除**で、**他の画像には触れない**。
無差別な DELETE は実装しない。

#### ⑧ 上部要素が全部空のとき

**見出し・ポスター・ポスター下文章・Xリンク下文章の4項目がすべて空なら、
空段落×3 も含めて上部を1ブロックも出力しない。**
このとき **WordPress 本文全体が実装前とバイト単位で完全一致**する（テストで確認済み）。
1つでもあれば空段落×3 を出力する。

#### ⑨ X（旧Twitter）の手動挿入

- **Gutenberg の空 paragraph ブロック × 3**（`<!-- wp:paragraph --><p class="wp-block-paragraph"></p>`）。
- **spacer ブロック / `<br>` 連続 / `&nbsp;` は使わない**（後から URL を貼る用途に向かないため）。
- 実機で **クリック可能・`contenteditable`・キャレットを置ける**ことを確認済み。
  そこへ URL を貼れば WordPress が埋め込みへ変換する。
- **X の URL 自体はアプリで入力しない**（入力UIも作らない）。

#### ⑩ 既存WordPress仕様は維持

`status=draft` / `category=24` / `author=14` / `st.secrets → os.getenv` / All-or-Nothing /
既存投稿の update なし / 既存メディア削除なし / DELETE なし / 長尺分割 / `WP_MAX_SIDE=2560` /
q95 / 4:4:4 / 高配分 / ジャグラー / 並び / その他優秀台 / シマズ / 店舗情報ボタン —— **すべて無変更**。

#### ⑪ 実機確認結果（2026-08-21・全PASS）

**ローカル（コード `166c05a`）**

- 8/19 でポスター2枚 → 結合 **1695×1199 / 988 KB / q95 / 4:4:4**（量子化テーブルが quality=95 と完全一致）
- WordPress 下書き **ID 59688** / media **19件** / draft・24・14
- 本文上部の順序が正常・**Gutenberg の空段落3つを実操作で確認**（クリック・キャレット可）
- 8/19 → 8/20 で**非流入**、8/20 → 8/19 で**2枚復元**
- 0枚時に **古い `_wp_poster.jpg` が削除**され、送信対象が **11枚 → 10枚**（13.74MB → 12.78MB）

**Cloud（`166c05a` 稼働を行番号照合で実測・Reboot不要）**

- 8/19 に A+B → 8/20 で **0枚** → 8/19 で **A+B 復元**
- B削除後の日付往復でも**削除状態を維持**（B は復活しない）→ 再追加で**2枚復帰**
- ⑧成功・結合 **1695×1199 / 988 KB**
- 送信対象 **11枚 / 13.74 MB** → WordPress 下書き **ID 59708** / media **19件** /
  **status=draft / category=24 / author=14**
- Gutenberg の上部順序が正常・**空段落3つを実操作で確認**（`contenteditable: true` / キャレット内包）
- 送信後の日付往復でも **2枚復元**
- 0枚時に送信対象が **11枚 → 10枚**（12.77MB）となり**古いポスターを除外**
- **最大 RSS 513.8 MB**（`run_auto_pipeline` 202.1 → 267.0 MB）。
  **Killed / OOM / MemoryError / Oh no. / 予期しない restart は0件**

**Cloud 実機確認は正式に完了**とする。

#### ⑫ 補足（Cloud を操作するときの注意）

アプリ所有者としてログインした状態では、Streamlit Cloud は**アプリを iframe 内に描画**する。
この状態ではブラウザ自動操作のファイルアップロードが届かない。
**`https://<app>.streamlit.app/~/+/?page=…` （iframe の実URL）を直接開く**と最上位描画になり、
通常どおり操作できる。アプリの挙動には影響しない。

## 高田馬場 記事用WordPress：機種H3の表記と全台系／高配分の並び順（2026-08-24 確定・`ed79440` / `9c83eef`）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】記事用 → WordPress下書きの機種H3だけ**。
実装は **`wp_client.py` のみ**（`h3_zendai()` と `plan_blocks()` の高配分ソート1行）。
**`streamlit_app.py` は変更していない。**

関連コミット:
`ed79440`（fix: 高田馬場WordPress見出し表記と高配分順を調整）→
`9c83eef`（fix: 高田馬場WordPressでマイナス平均差枚を非表示）

### ① H3表記

`h3_zendai()` の出力書式を次のとおりとする。

| 平均差枚 | 出力 | 例 |
|---|---|---|
| **0以上** | `機種名(○/○台+)→平均+○枚` | `うみねこ2(2/2台+)→平均+2,450枚` |
| **マイナス** | `機種名(○/○台+)` | `機種A(1/2台+)` |

- 機種名と `(` の間に**スペースを入れない**。
- 括弧は**左右とも半角** `(` `)`。**全角 `）`（`_PAREN_R`）を使わない。**
- 矢印は **`→` U+2192**。定数 **`_ARROW_R2 = "&#x2192;"`** を新設した。
  **既存の `_ARROW_R`（➡ U+27A1）は他関数が使うので削除・変更しない。**
- 「平均」と符号の間、符号と数字の間に**スペースを入れない**。
- **マイナスのときは `→平均-○枚` を丸ごと出さない。**
  `→` / `平均` / `-` / `枚` / 桁区切り `,` のいずれも残さない。
- **0 は表示対象**。`機種A(1/2台+)→平均+0枚` とする（0をマイナス扱いしない）。
- 判定は `int(item['all_avg_diff']) < 0`。**`int()` は `fmt_signed()` と同じ丸めにして、
  表示と分岐の判定をずらさないために掛ける**（float が来ても表示と分岐が一致する）。

旧書式は `戦国乙女4 (3/3台+） ➡平均 +5,317枚` だった。**この旧書式へ戻さない。**

### ② 対象H3（3セクション共通）

`h3_zendai()` を使う **全台系 / 高配分 / ジャグラー個別高配分**の**共通仕様**とする。

- **記事内で書式を混在させない。ジャグラーだけ旧書式に分けない。**
- ただし**ジャグラーの順序・画像・抽出条件は変更しない**。変えるのは**H3文字列の表記だけ**。
- **`h3_narabi()`（並び）は対象外**。`▶`（`_ARROW_TRI`）＋マイナスも平均を表示する
  従来書式のまま**変更しない**。
- `line_high()` は本文へ出力しない既存の未使用関数のまま（**変更しない**）。

### ③ 並び順

**全台系・高配分とも `all_avg_diff` の実値で平均差枚降順。**

- **全台系**（`plan_blocks()`）＝**既存仕様・無変更**。
  `zen = sorted(payload["zen_dai"], key=lambda x: -int(x.get("all_avg_diff", 0)))` をそのまま維持する。
- **高配分**＝`_resolve_high_images()` で**画像セットを確定した後**に降順ソートする。

  ```python
  high_imgs = _resolve_high_images(payload["high"], out_dir)
  high_imgs = sorted(high_imgs,
                     key=lambda h: -int(h["entry"].get("all_avg_diff", 0)))
  ```

- **手動高配分／自動高配分による優先順位は付けない。**純粋に平均差枚だけで降順にする。
  `_resolve_high_images()` の画像解決・手動/自動判定・重複除去には**触れない**。
- **同値は Python の安定ソートで現在の相対順を維持**する。
- **H3と画像は同じ dict（`entry` / `file`）なのでセット単位で動く。**
  H3と画像を別々に並び替える実装は**禁止**。

**重要：マイナス平均差枚のH3で平均表示を省略しても、ソートには実際の `all_avg_diff` を使う。**
**マイナス機種を除外しない。0扱いもしない。**表示を省くのは**表示だけの仕様**である。

### ④ Cloud実機確認結果（2026-08-24）

**8/20（投稿ID 60151 / status=draft / category=24 / author=14）**

- H3新表記 PASS。旧 `&#x27a1;` ・全角括弧・余分なスペースは本文全体で0件。
- 高配分が **+1,850 / +1,710 / +1,550 / +770 / +625 / +588 / +30** の**完全降順**。
- H3と画像のズレ **0件**。
- この日は全台系が0件のため、全台系の並び順は8/23で確認した。

**8/23（投稿ID 60179 / status=draft / category=24 / author=14）**

- 全台系が **うみねこ2 +2,450 / 戦国乙女4 +1,700 / ディスクアップUR +650 /
  異世界かるてっと +550** の**実値降順** PASS。
- 高配分が **ヴァルヴレイヴ2 +4,875 / ワールドダイスター +2,783 / スマスロ化物語 +2,000 /
  東京喰種 +957 / モンキーターンV +447 / 炎炎ノ消防隊2 +431 / カバネリ海門決戦 +253** の
  **実値降順** PASS。
- H3と画像のズレ **0件**。
- ジャグラー・並び・その他優秀台・記事上部・シマズ・店舗情報ボタンは**非回帰 PASS**。
- WordPress の 401 / 403 / 429 / 5xx は **0件**。最大 RSS **801.2 MB**。
  **Killed / OOM / MemoryError / unexpected restart は0件。**

**修正前後の比較（同一データ）**: 8/23 は旧コードでも下書き（60128）が作られていたため、
同じ日のデータで before/after を直接比較できた。旧コードの高配分は
`+447 / +957 / +2,783 / +4,875 / +253 / +2,000 / +431` と**未ソート**で、
H3も `うみねこ2 (2/2台+） &#x27a1;平均 +2,450枚` の旧書式だった。

### ⑤ マイナス平均差枚の確認状況（誤記しないこと）

**マイナス時の表示省略は「純粋関数テストで確認済み・Cloud実データに該当なし」である。**
**「Cloud実機確認済み」と書かない。**

- Cloud実機の **8/20・8/23 とも、全台系／高配分にマイナス平均差枚の機種が存在しなかった**
  （最小は高配分のカバネリ海門決戦 +253枚）。全台系・高配分の**全11機種のH3に `平均` が
  含まれている**ことを機械確認しており、**`avg < 0` の分岐は実データでは1度も通っていない**。
- 一方、**純粋関数テストでは `-1` / `-500` / `-10000` の全ケースで
  `機種名(○/○台+)` だけが出力**され、`→`（実体参照・生 U+2192 の両方）/ `平均` / `-` / `枚` /
  桁区切り `,` の**残骸が無い**ことを確認済み。
- **`+3,000 / +1,000 / +100 / -100 / -500` をシャッフル投入したテストで、
  マイナス2機種もソート対象に残り**、全台系・高配分とも**実値降順**になること、
  および**マイナス機種のH3だけ平均表示が消える**ことを確認済み。
- 境界値 `0` は `→平均+0枚`、`+1` は `→平均+1枚` と表示されることも確認済み。
- 以上をもって**正式仕様として採用する**。実データにマイナス機種が現れた日に、
  自然な運用の中で表示を確認すればよい（そのために追加の下書きを作る必要はない）。

### ⑥ 無変更（今回いっさい触れていない）

記事上部ポスター / ポスター下文章 / X用空段落×3 / Xリンク下文章 / ジャグラーの順序・画像 /
並び（`h3_narabi()` 含む）/ その他優秀台 / シマズ / 店舗情報ボタン / 長尺画像分割 /
`WP_MAX_SIDE=2560` / q95 / 4:4:4 / `_SPLIT_QUALITY` / `_SPLIT_SUBSAMPLING` / `_MCU` /
`POSTER_QUALITY` / `POSTER_SUBSAMPLING` / `status=draft` / `category=24` / `author=14` /
All-or-Nothing / 既存投稿の update なし / 既存メディア削除なし / DELETE なし /
`st.secrets → os.getenv` / `build_payload()` / `_resolve_high_images()` /
`高解像度（_ART_HQ_*）` / Pision取得 / 既存の記事用画像生成 / 他店舗。

## 高田馬場 記事用WordPress：並びH3表記（2026-08-24 確定・`deb3e97`）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】記事用 → WordPress下書きの並びH3だけ**。
実装は **`wp_client.py` の `ban_range_str()` と `h3_narabi()` のみ**。
**`streamlit_app.py` は変更していない。**

関連コミット: `deb3e97`（fix: 高田馬場WordPressの並び見出し表記を調整）
直前の機種H3仕様（`ed79440` / `9c83eef`）とは**別の節・別の関数**であることに注意する。

### ① 並びH3の表記

| | 表記 |
|---|---|
| 旧 | `【4台並び】2045番台〜2048番台 東京喰種▶平均+4,650枚` |
| **新** | **`【4台並び】東京喰種(2045〜2048番台)→平均+4,650枚`** |

- **`【N台並び】` は維持**（「列」の自動判定はしない従来仕様のまま）。
- **機種名を台番より前へ置く。**
- 機種名と `(` の間に**スペースを入れない**。
- 括弧は**半角** `(` `)`。
- 台番範囲の `〜` は **`_WAVE_BAN` U+301C** を維持する。
- **開始側には「番台」を付けない。**
- **「番台」は括弧内の最後に1回だけ付ける。**
- 矢印は **`_ARROW_R2`（`&#x2192;` → U+2192）**。**`▶`（`_ARROW_TRI`）は使わない。**
- `→平均` の間、`平均` と符号の間に**スペースを入れない**。

`_ARROW_TRI` は**この関数でのみ使っていたため未使用になったが、定数定義は残す**
（`_ARROW_R` と同じ扱い。削除しない）。`_ARROW_R2` は**機種H3と並びH3で共用**する。

### ② 飛び地の区切りは半角 `+`（`・` を使わない）

```
【4台並び】東京喰種(2078〜2080+2187番台)→平均+1,200枚
【5台並び】機種A(100〜102+200+300番台)→平均+1,000枚
```

- 連続区間は `100〜102` の形式。
- **飛び地の区切りは半角 `+`。旧表記の `・` へ戻さない。**
- **途中の区間に「番台」を付けない。**
- **括弧内の最後にだけ「番台」を1回付ける。**

単独1台は数値の直後に付ける:

```
【1台並び】東京喰種(2187番台)→平均+500枚
```

### ③ 複数機種にまたがる並び

**`machine` の既存生成ロジック（`streamlit_app.py:4623-4630`）は変更しない。**
1機種＝`東京喰種` ／ 2機種＝`A+B` ／ 3機種以上＝`A～Z`。H3へはそのまま置く。

```
【4台並び】機種A+機種B(2045〜2048番台)→平均+1,200枚
【5台並び】機種A～機種E(100〜104番台)→平均+900枚
```

**機種名側の `～`（`_TILDE_FW` U+FF5E）と台番範囲側の `〜`（`_WAVE_BAN` U+301C）は
別のUnicode文字**であり、**どちらも既存仕様のまま維持する**（統一しない）。

### ④ マイナス平均差枚は表示する（機種H3とは別仕様）

**並びは平均差枚がマイナスでも `→平均-○枚` を表示する。**

```
【4台並び】東京喰種(2045〜2048番台)→平均-500枚
```

**全台系・高配分・ジャグラー個別高配分の「マイナスなら平均部分を非表示」（`9c83eef`）は
並びへ適用しない。** `h3_narabi()` は `fmt_signed()` を無条件に呼ぶ一本道を維持する。
0 は `→平均+0枚` と表示する。

### ⑤ 実装位置

**`ban_range_str()`**

- 連続 run を `2078〜2080` の形式にする（開始側に「番台」を付けない）。
- 飛び地は `+` で連結する。
- **最後に「番台」を1回だけ付与**して返す。
- 呼び出しは `h3_narabi()` の**1箇所のみ**（他から使われていないことを確認済み）。

**`h3_narabi()`**

- 機種名を前へ出し、台番を**半角括弧**で囲む。
- 矢印は **`_ARROW_R2`**。
- 平均差枚は従来どおり **`fmt_signed()`**。

**並びの抽出条件・台数判定・開始／終了台番の判定・順序・並び画像・画像ファイル名
（`narabi_file_name()`）・`ban_range`・平均差枚の計算には触れない。**
**`h3_zendai()` は変更しない。**

### ⑥ Cloud実機確認結果（2026-08-24・正式完了）

**2026/8/23 を使用。正式draft: 投稿ID 60237 / status=draft / category=24 / author=14 / media 27件。**

Cloud で `deb3e97` が稼働していることは、**同一8/23データの旧投稿 60179 との出力差分**で実測した。

```
旧(60179): 【4台並び】2045番台〜2048番台 東京喰種▶平均+4,650枚
新(60237): 【4台並び】東京喰種(2045〜2048番台)→平均+4,650枚
```

**実機で確認した並びH3（5件すべてPASS）**

```
【4台並び】東京喰種(2045〜2048番台)→平均+4,650枚
【4台並び】東京喰種(2083〜2086番台)→平均+4,000枚
【4台並び】モンキーターンV(2034〜2037番台)→平均+3,125枚
【3台並び】スマスロ化物語(2122〜2124番台)→平均+2,933枚
【3台並び】カバネリ海門決戦(2105〜2107番台)→平均+3,333枚
```

確認済み: 機種名が台番より前 ／ 半角括弧 ／ 開始側に「番台」なし ／
「番台」は括弧内末尾に1回 ／ **`▶` は本文全体で0件** ／ `→` を使用 ／ 不要スペースなし ／
台番範囲は U+301C ／ **H3と画像のズレ0件** ／ **並び順は旧コードと完全一致**。

本文中の `・` は2件のみで、いずれも **H2見出し「並び・列仕掛けも！」** と
**ボタン「店舗情報・過去の結果はコチラ」**（従来からの固定文言）であり、並びH3ではない。

### ⑦ 飛び地の確認状況（誤記しないこと）

**飛び地の表示は「純粋関数テストで確認済み・Cloud実データ該当なし」である。**
**「Cloud実機確認済み」と書かない。**

- **8/23 の Cloud 実データには飛び地の並びが存在しなかった**（5件すべて連続範囲）ため、
  Cloud実機での飛び地表示確認は**未実施**。
- 純粋関数テストでは次の2件が**完全一致でPASS**している。

  ```
  【4台並び】東京喰種(2078〜2080+2187番台)→平均+1,200枚
  【5台並び】機種A(100〜102+200+300番台)→平均+1,000枚
  ```

- あわせて **`・` なし ／ 半角 `+` 使用 ／ 途中区間に「番台」なし ／
  「番台」は括弧内末尾に1回だけ ／ `〜` は U+301C** を機械確認済み。
- 確認のためだけに追加の下書きを作る必要はない。実データに飛び地が現れた日に確認すればよい。

### ⑧ マイナス並びの確認状況（誤記しないこと）

**マイナス並びの表示も「純粋関数テストで確認済み・Cloud実データ該当なし」である。**
**「Cloud実機確認済み」と書かない。**

- 8/23 の並び5件は**すべて平均差枚がプラス**（+4,650 / +4,000 / +3,333 / +3,125 / +2,933）
  だったため、Cloud実機でのマイナス表示確認は**未実施**。
- 純粋関数テストでは `【4台並び】東京喰種(2045〜2048番台)→平均-500枚` および
  `-12,345枚` が**PASS済み**。0 の `→平均+0枚` も確認済み。

### ⑨ 非回帰（同一データでの全ブロック比較）

同一8/23データの**旧投稿 60179 と新投稿 60237 を機械比較**した。

```
ブロック数: 50 → 50
並びH3の text 以外の差分: 0件
```

**並び順 / 並び画像 / H3と画像の対応 / 全台系 / 高配分 / ジャグラー / `h3_zendai()` /
その他優秀台 / 記事上部 / X用空段落×3 / シマズ / 店舗情報 / 長尺分割 /
`WP_MAX_SIDE=2560` / q95 / 4:4:4 / `status=draft` / `category=24` / `author=14` /
All-or-Nothing** は**すべて不変**。

### ⑩ Cloud安定性（2026-08-24 実測）

- **最大 RSS 682.1 MB**
- WordPress の **401 / 403 / 429 / 5xx は0件**
- **Killed / OOM / MemoryError / unexpected restart / Connection reset は0件**
- **Traceback 0件**

### ⑪ 補足

**今回 Claude Code が作成した正式確認用の下書きは 60237 のみ**である。
同日に存在する**投稿 60208 は Claude Code が作成したものではない**ため、
本仕様の記録対象に含めない（原因推測・削除・変更もしない）。

## 高田馬場 記事用：末尾モードの表示名・全台/優秀台ボタン廃止・バラエティの青バー（2026-08-25 確定・`6fdf731`）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】の📰記事用ページだけ**。
実装は **`streamlit_app.py` の3か所のみ**（+23行／−83行）。
**`wp_client.py` は変更していない。**通常結果ポスト用・他店舗はいっさい変更していない。

### ① 末尾モードの表示名（`format_func` で表示だけ変える）

**内部値・`article_page_inputs.json` の保存値は従来のまま維持する。**

| 内部値（保存値・比較に使う値） | UI表示 |
|---|---|
| `全台` | 全台 |
| `プラス台（ピンクバー付き）` | **プラス台（平均差枚付き）** |
| `優秀台（ピンクバー付き）` | **優秀台（平均差枚付き）** |
| `プラス台（ピンクバーなし）` | **プラス台（平均差枚なし）** |
| `優秀台（ピンクバーなし）` | **優秀台（平均差枚なし）** |

- 変換は **`_ART_SUE_MODE_LABELS` / `_art_sue_mode_label()`** と、記事用の2つの radio
  （`art_suebangai_mode` / `art_jug_sue_mode`）へ渡す **`format_func=_art_sue_mode_label`** だけで行う。
- **`_a_sue_mode_opts` / `_a_jug_mode_opts` の選択肢リストを新名称へ書き換えてはならない。**
  書き換えると (a) `if st.session_state.get(...) not in _a_sue_mode_opts: pop(...)` のガードが発火して
  **保存済みモードが黙って捨てられ「全台」へ戻る**、(b) `_build_sue_images()` の
  文字列比較8ブロックがすべて不一致になり画像仕様が変わる。
- **`article_page_inputs.json` には旧内部値を保存し続ける**（実機で
  「UIで新表示を選ぶ → JSONは `優秀台（ピンクバー付き）`」を確認済み）。
- **`_build_sue_images()` 本体・`_art_sue_settings()`・`_article_input_keys()`・
  `_save_article_inputs()` / `_restore_article_inputs()` は無変更。**
- **通常結果ポスト用（`show_auto_page`）の表記は変更しない。**
  `format_func` を通常ページの radio（`7802` / `7967` 付近）へ広げない。

**「ピンクバー付き／なし」が実際に制御しているもの**は `_build_sue_images()` の
`summary_stat`（`_stat_of`）の有無だけである。記事用（`article_mode=True`）は
ピンクバーを1本も描かず、**付き→`_build_article_machine_img()`（表＋白サマリー：
クラウン＋タイトル＋総差枚／平均／勝率／台数）／なし→`_build_machine_img_no_bar()`（表のみ）**
になる。旧名称は通常ページのピンク帯由来の名残で、記事用の見た目と一致していなかった。

### ② ⑤末尾画像の「全台」「優秀台」ボタンは正式廃止

モード選択の下にあった単発保存ボタン（`art_sue_zentai_btn` / `art_sue_yushu_btn`）と、
その専用生成処理を**丸ごと削除した**。**復活させない。**

廃止できる根拠（削除前に全参照を追って確認済み。参照は4行だけで当該ブロック内に閉じていた）:

- **⑦プレビュー・⑧本番・WordPress本文のいずれからも参照されない**
  （プレビュー／⑧は `_art_sue_settings()` → `_build_sue_images()` 経由。
  `wp_client.plan_blocks()` は末尾画像を本文へ出さない）
- **`article_page_inputs.json` への保存／復元に無関係**（`_article_input_keys()` に両キーは無い）
- **`st.button` なので保持する session_state 値が無い**。
  ⑤バラエティの「常時mount」対策（`f87eed7`）は**値を持つウィジェット用**であり、
  ボタンは対象外。削除しても消える値はない
- **モード側で完全代替できる**（ボタンは末尾①のみ／全台・差枚>0 だけ。
  モードは末尾①②③＋ジャグラー末尾①②③、記事用の体裁、パネル・スランプ・
  ban_map・🎯掲載台選択に対応する上位互換）
- **旧ボタンは `output_dir` へ画像を直接書いていた**ため、`result["files"]`・ban_map・
  スランプ・WordPress のどこにも登録されないまま**ZIPにだけ紛れ込んでいた**。
  生成経路そのものを消したので、この混入は構造的に起こらない

### ③ 記事用バラエティ画像は青タイトルバーなし

**モードに関係なく（全台／プラス台／優秀台のすべて）青タイトルバーなしを正式仕様とする。**

- ⑦プレビュー・⑧本番の両方で **`_build_machine_img(..., no_bar=True)`** を使う。
- **共通の `_build_machine_img()` 本体は変更しない**（`no_bar` 引数は既存）。
  全店舗・全画像種で共用しているため、本体の書き換えは禁止。
- **青バーを透明化するのではなく、バー領域そのものを作らない。**
  `no_bar=True` は `BAR_H + LINE_H` ぶんキャンバス高さを縮めて生成するため、
  **空白が残らず、crop ではないので表の先頭行も欠けない。**
- **ピンクサマリーバーは既存仕様どおり**（全台モードでは従来どおり表示される）。
- 合成後の並びは **`[パネル] → [表] → [スランプ]`**（従来は表の上に青バーがあった）。
- **通常結果ポスト用・他店舗のバラエティ画像は従来どおり青タイトルバーあり。**
  `show_auto_page` 側の呼び出し（`8714` / `9376` ほか）へ `no_bar` を渡さない。

### ④ 無変更（今回いっさい触れていない）

`_build_machine_img()` 本体 ／ `_build_sue_images()` 本体 ／ `_apply_panel_to_table_img()` ／
`_attach_slump_to_table()` ／ `_build_machine_img_no_bar()` ／ `_build_article_machine_img()` ／
`wp_client.py` ／ 通常結果ポスト側のモード表示 ／ 他店舗 ／ 末尾抽出条件 ／
バラエティ抽出条件 ／ 台番範囲 ／ パネル ／ スランプ ／ 液晶選択 ／ 高解像度判定
（`_ART_HQ_*`）／ ban_map ／ ZIP 対象 ／ 🎯掲載台を選ぶ ／ WordPress 仕様
（`status=draft` / `category=24` / `author=14` / 長尺分割 / `WP_MAX_SIDE=2560` / q95 / 4:4:4）／
記事上部ポスター ／ Cloud↔GitHub 同期 ／ ブラウザ履歴。

### ⑤ 純粋テスト結果（全PASS）

- 記事用モード5種の**内部値が従来と同一**／表示だけ新名称5種
- 保存済み `優秀台（ピンクバー付き）` が新表示へ変換され、**ガードに掛からず値が捨てられない**／
  未知値はそのまま返す
- 通常ページ（`show_auto_page` 全域）が HEAD~1 と**バイト単位で完全一致**
- 旧ボタンの参照（`art_sue_zentai_btn` / `art_sue_yushu_btn` / `sue_zentai` / `sue_yushu`）**0件**
- 上記④の各関数の**本体に差分なし**
- `no_bar=True` で **幅不変・高さのみ `BAR_H+LINE_H`（993px幅なら 76+6=82px）減**、
  **最上行が白でなく表ヘッダー色**（＝空白なし）、**表本体の画素がバイト完全一致**、
  `no_bar=False` 側は最上行が `rgb(38,76,161)`＝**青バーあり**。
  **ピンクバーあり（全台相当）・なし（優秀台相当）の両方で確認**
- `_vstack_images` は幅不変・隙間なし／`_attach_slump_to_table` の追加高さは
  `no_bar` の有無で不変

### ⑥ ローカル実機確認結果（2026-08-25・正式HEAD `6fdf731` で起動して実施）

**8/24 のデータ（`art_suebangai_mode = "優秀台（ピンクバー付き）"` が保存済みの日付）を使用。**

- 通常末尾・ジャグラー末尾とも**新表示5種** PASS
- 既存保存値 `優秀台（ピンクバー付き）` が UI 上 **`優秀台（平均差枚付き）` として選択済みで復元**
- **UIで新表示を選んでも JSON には旧内部値で保存**される
  （`art_jug_sue_mode` に `優秀台（ピンクバー付き）` が保存されることを確認。
  `平均差枚` 表記での保存は0件）
- 「全台」「優秀台」ボタンは**DOM上0件**（末尾①="8" 入力済みの状態でも非表示）。
  **ボタン跡の余白なし・周辺UIの配置崩れなし**
- **モードだけで末尾プレビューを生成できた**（`末尾8番台の優秀台.jpg` 1460×4598・高解像度2倍）。
  ジャグラー末尾側も同様
- `バラエティの優秀台.jpg`（994×1408）で **上部120行の青 `#264CA1` ピクセルが0個**＝
  **青バーなし**。y=0 からパネル画像が始まり**青バー分の空白なし**
- **パネル（2×2）正常・スランプ（3列）正常・液晶はめ込み正常
  （最終行の空きコマに中央配置）・表の先頭行が欠けない・台番帯正常・列幅正常**
- **通常ページ側の非回帰はコードのバイト一致で確認**（UI巡回より強い証拠のため、
  保護対象外ファイルを不要に汚さない方針で採用）
- **他店舗への波及なし**（変更は全て `show_auto_article_page` 内で、
  呼び出しは `store == "高田馬場"` の記事用1経路のみ）

### ⑦ 確認状況の正確な記録（誤記しないこと）

- **バラエティ「全台」モードは「純粋テストで確認済み・追加の実機確認は未実施」である。**
  **「実機確認済み」と書かない。**実機で切り替えると `_save_art_variety()` が
  `store_settings/高田馬場.json` を書き換えて差分が発生し、復旧に checkout が必要になるため、
  設定ファイルを汚さない判断で実施しなかった。純粋テストでは青バーなし・空白なし・幅不変・
  高さ −82px・表画素完全一致・ピンクサマリー維持を PASS 済み。
- **日付切替は「rerun 維持は実機確認済み・追加の日付切替試験は未実施」である。**
  日付単位保存ロジックは今回いっさい変更しておらず、既存保存ファイルへ不要な差分を
  作らないため追加試験を行わなかった。
- **⑧本番は不具合ではなく、意図的に実施していない。**
  `article_page_inputs.json` に**今回と無関係な既存差分**があり、同ファイルは
  **`_git_auto_push()` の targets に含まれる**（`weekly_items.json` /
  `auto_page_inputs.json` / `auto_page_persistent_inputs.json` /
  `article_page_inputs.json` / `rote_machines.json` / `store_settings`）。
  ⑧を実行するとその既存差分まで自動 commit / push されるため、
  機能確認のためだけにこのリスクを取らない判断とした。
  **WordPress 通信は0件**（POST / media upload / draft作成 / update / DELETE いずれも未実施）。

## 高田馬場 記事用：高配分画像の「優秀台ピックアップ」細タイトルバー（2026-08-25 確定・`d5ba1bb`）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】記事用の高配分機種画像だけ**。
実装は **`streamlit_app.py` の5か所のみ**（ヘルパー新設＋適用4経路／+76行・−13行）。
**`wp_client.py` は変更していない。**通常結果ポスト用・他店舗はいっさい変更していない。

### ① 対象画像（自動・手動の両方）

| 種別 | ファイル名 | 生成箇所 |
|---|---|---|
| **自動高配分** | `{機種名}_高配分.jpg` | pipeline の `if article_mode:` 分岐2か所（`run_step2_juggler` のジャグラー系／`run_step3_other` の非ジャグラー） |
| **手動高配分**（②個別画像「優秀台」） | `{機種名}（優秀台）.jpg` | `show_auto_article_page` の⑦プレビュー／⑧本番の2か所 |

**両方に同じ細い青タイトルバーを付ける。**片方だけに付ける状態へ戻さない。
`wp_client._resolve_high_images()` が自動 `_高配分.jpg` と手動 `（優秀台）.jpg` の
**両方を高配分として扱う**ため、この4か所で過不足がない。

⑦プレビューは自動高配分を**再生成しない**（pipeline の成果物を `_art_fpm` から取り出すだけ）。
そのため pipeline の2か所を直せば**⑦・⑧・ZIP・ban_map・WordPress がすべて同一画像**になる。

### ② 正式な画像構成

```
パネルあり:                     パネルなし:
[パネル]                        [青タイトルバー「優秀台ピックアップ」]
[青タイトルバー「優秀台ピックアップ」]   [表]
[表]                            [スランプ]
[スランプ]
```

**追加の空白・隙間を入れない。**

### ③ タイトルバー仕様

| 項目 | 値 |
|---|---|
| 文字 | **`優秀台ピックアップ`** |
| 背景 | **`#0080FF` = RGB(0,128,255)** の単色（グラデーションにしない） |
| 文字色 | **白** |
| 配置 | **水平中央・垂直中央** |
| 幅 | 画像幅いっぱい |
| **バー高** | 表のデータ行と同じ **`round(ROW_H * 150/96 * hq)`** → **等倍44px／高解像度2倍88px** |

完成イメージ（`aaa.jpg`）の実測に合わせた**細いバー**とする。
`aaa.jpg` は幅1387pxでバー高62px＝比率0.0447、実装は幅993pxで44px＝比率0.0450でほぼ一致。
**既存 `_build_machine_img` の `BAR_H = w×73/950`（比率0.0768・濃紺 `#264CA1`）のような
太い青タイトルバーへ戻さない。色も `#264CA1` を使わない。**

### ④ 実装（新設・純粋関数）

```python
_ART_HIGH_BAR_TEXT   = "優秀台ピックアップ"
_ART_HIGH_BAR_BG     = (0, 128, 255)     # #0080FF
_ART_HIGH_BAR_FG     = (255, 255, 255)   # 白
_ART_HIGH_BAR_FONT_R = 0.72              # フォントサイズ / バー高

def _art_high_title_bar(table_img, hq_scale=1.0) -> Image
```

- `_build_machine_img_no_bar()` が返した**表画像の上端**へバーを足して**新しい画像を返す**。
  **表本体は1pxも変更しない。**
- 文字がバーに収まらない場合はフォントを縮めるガードを持つ（通常は1回で確定）。
- **既存の共通関数本体は変更しない**（呼び出し側でラッパーを被せるだけ）。
- **適用は上記4経路だけ。**それ以外の `_build_machine_img_no_bar()` 呼び出しへ広げない。

### ⑤ パネル・スランプとの位置関係

- タイトルバーを**表画像へ焼き込む**方式のため、後段の
  **`_apply_panel_to_table_img(crop_bar=False)`** が `_vstack_images(パネル, 画像)` で
  **上に積むだけ**で `[パネル][青バー][表]` になる。
  パネル未登録の機種（`_build_panel_row()` が `None`）は元画像がそのまま返るので
  `[青バー][表]` になる。**追加の分岐は不要。**
- **`_attach_slump_to_table()` は変更しない。**表画像の幅だけを見て下に3列で連結するため、
  スランプの追加量・配置・液晶はめ込み仕様は**バーの有無で不変**。

### ⑥ 対象外（今回のバーを付けない）

**バラエティ／④末尾／ジャグラーシリーズ優秀台の統合画像／その他の優秀台ピックアップ統合画像／
個別機種の通常優秀台ピックアップ／全台系／並び／通常結果ポスト／他店舗。**

特に直前に正式化した **「高田馬場 記事用バラエティ＝青タイトルバーなし」（`6fdf731`）を維持する。**
バラエティは `_build_machine_img(..., no_bar=True)` の別経路であり、今回の4か所に含まれない。

### ⑦ 純粋テスト結果（全PASS）

- 幅不変／高さが **等倍+44px・2倍+88px ちょうど**増える
- バー背景が **`#0080FF` 単色**（バー領域の最頻色 90.4%〜91.6%）
- **バー最上行が青**（上に空白なし）、**バー直下が表の先頭行とバイト一致**（下に空白なし）
- **表本体の画素がバイト完全一致**
- 文字が白・**水平中央（誤差1px）・垂直中央（誤差1px）**・バー内に収まる
- **hq=1/2 でバー高比率（0.0450 / 0.0451）と文字高比率（0.682 / 0.682）が一致**
- `_vstack_images(パネル, バー付き表)` が `[パネル][青バー][表]` 順・隙間なし
- パネルなしで `[青バー][表]` 順・隙間なし
- **`_attach_slump_to_table()` の追加量がバー有無で不変**、最終 `[パネル][青バー][表][スランプ]` が成立
- バラエティ `no_bar=True` 経路に今回のバーが付かない
- **`_art_high_title_bar(` の出現は定義1＋呼び出し4件ちょうど**、
  `_build_machine_img_no_bar()` の呼び出し総数は **9→9 で不変**
- **通常ページ `show_auto_page` 全域が HEAD とバイト完全一致**
- 変更禁止関数（`_build_machine_img` / `_build_machine_img_no_bar` /
  `_build_article_machine_img` / `_apply_panel_to_table_img` / `_attach_slump_to_table` /
  `_build_panel_row` / `_build_sue_images`）の**本体がすべてバイト一致**

### ⑧ ローカル実機確認結果（2026-08-25・正式HEAD `d5ba1bb` で起動して実施）

**2026/8/24 のデータで⑦プレビューを実行。**

**自動高配分 10件すべてにバーあり**（アズールレーン／戦コレ6／からくりサーカス／戦国乙女5／
とある禁書目録2／ヴァルヴレイヴ2／やじきた／真打吉宗／SAOII／スマスロ北斗の拳）。

**手動高配分**は 8/24 の②が未入力だったため、③個別画像をONにし優秀台1枠目へ `戦コレ6` を
入力して検証した。**`戦コレ6（優秀台）.jpg` が生成されバーあり**。同時に自動側の
`戦コレ6_高配分.jpg` は既存仕様どおり抑制された（10件→9件）。
**自動・手動とも `[パネル][優秀台ピックアップ][表][スランプ]` の構成が一致**し、
「自動だけバーあり／手動だけバーなし」のような差は発生していない。

実測: バーは実機JPEG後の検出で約40〜42px（**生成値自体は44px**。圧縮境界による検出差）。
文字の水平中央差は −1〜−2px。バーの top 位置は 351〜417px ＝**パネルの下**。

**非回帰（すべてPASS）**: パネル正常／表の先頭行正常／台番帯正常／列幅正常／スランプ正常／
液晶はめ込み正常（`戦国乙女5_高配分.jpg` の空きコマに中央配置）／**パネルとバーの間に隙間なし**／
**バーと表の間に隙間なし**／**バラエティは青タイトルバーなしを維持**／
**対象外画像53件すべてに `#0080FF` バーなし**（全台系・並び・末尾・ジャグラー統合・
その他優秀台統合・個別ピックアップ・バラエティ）／通常ページはコードのバイト一致／他店舗へ波及なし。

### ⑨ `aaa.jpg` との比較

完成イメージ `aaa.jpg` と実機を比較し、**青の明るさ・バーの細さ・文字サイズ・中央配置・
表とのバランス**が近いことを確認した。
**完全なピクセル一致は目的とせず、「表の台番行と同程度の細いバー」を正式仕様とする。**

### ⑩ ⑧本番の未実施理由（誤記しないこと）

**⑧は不具合による未実施ではない。**`article_page_inputs.json` に**今回と無関係な既存差分**があり、
同ファイルは **`_git_auto_push()` の targets に含まれる**（`weekly_items.json` /
`auto_page_inputs.json` / `auto_page_persistent_inputs.json` / `article_page_inputs.json` /
`rote_machines.json` / `store_settings`）。⑧を実行するとその既存差分まで自動 commit / push
されるため、意図的に実施しなかった。**今回の描画経路は⑦プレビューで実機確認済み。**
**WordPress 通信は0件**（POST / media upload / draft作成 / update / DELETE いずれも未実施）。

### ⑪ 実機確認で触れた設定値について

手動高配分の確認のため `art_kojin_enabled` / `art_kojin_y_0_高田馬場` を一時的に操作したが、
**確認後に元の値（`False` / `""`）へ復元済み**であることを JSON で検証した。
アプリの毎レンダー保存によりファイルのハッシュ自体は変化しているが、**②の値は確認前と同一**。
`article_page_inputs.json` は**この仕様の commit に含めない**。**JSON を直接編集して戻すこともしない。**

## 高田馬場 記事用WordPress：末尾・バラエティ追加と本文順（2026-08-25 確定・`bf2c005`）

**正式仕様。巻き戻し禁止。**対象は**【高田馬場】記事用のWordPress下書き本文だけ**。
正式コード commit は **`bf2c005`**（**`streamlit_app.py` と `wp_client.py` の2ファイルのみ**・+65／−11）。
**記事用画像の生成ロジックはいっさい変更していない。**⑧が既に保存した正式画像を
本文の正しい位置へ載せるだけの変更である。

### ① 正式な本文順

| 順 | セクション | H2文言 |
|---|---|---|
| 1 | 記事上部 | ユーザー入力の見出し（任意） |
| 2 | 全台系 | `全台系濃厚機種が複数` |
| 3 | 高配分 | `1/2系以上の高配分機種が大量` |
| 4 | **末尾** | **`末尾`** ★新設 |
| 5 | 並び | `並び・列仕掛けも！` |
| 6 | **バラエティ** | **`バラエティ`** ★新設 |
| 7 | ジャグラー | `ジャグからも高配分機種多数！` |
| 8 | その他 | `その他単品優秀台も多数` |
| 9 | シマズ | `シマズをチェック！` |
| 10 | 店舗情報ボタン | `wp:loos/button`（SWELL）・**本文末尾** |

**旧順（… → ジャグラー → 並び → その他 …）へ戻さない。**
H2定数は **`H2_SUEBANGAI = "末尾"` / `H2_VARIETY = "バラエティ"`**。
煽り文言（「末尾狙いも機能！」等）にはしない。既存6定数の文字列は変更しない。

### ② 末尾セクション

- **⑧が実際に生成した正式ファイル名をそのまま WordPress payload へ渡す。**
  `streamlit_app.py` の payload 構築で
  `_art_wp_pl["suebangai"] = [_fn for _fn, _bns in _art_sue_ban_e.items() if _bns]`。
  **wp_client 側でファイル名を再生成・再推測しない**（`app_safe_fn` による再構成をしない）。
- **掲載順は `_art_sue_ban_e` の挿入順＝⑧の生成順**
  （通常末尾①②③ → ジャグラー末尾①②③）。**新しいソートを追加しない。**
- **ジャグラー末尾も同じ「末尾」セクションへまとめる**（ジャグラーセクションへ入れない）。
- 掲載台0台で画像を作らなかった末尾は `if _bns` で payload から除く。
- 末尾モード（UI表示名「平均差枚付き／なし」・**内部保存値は従来の「ピンクバー付き／なし」**）は
  **無変更**（`6fdf731` の正式仕様を維持）。
  廃止した「全台／優秀台」単発ボタン由来の画像を復活させない。

### ③ バラエティセクション

- 同様に **`_art_wp_pl["variety"] = [_art_var_fn_e] if _art_var_fn_e else []`**。
  ⑧は最大1枚（`バラエティ.jpg` / `バラエティの優秀台.jpg`）。
- 配置は **並び → バラエティ → ジャグラー**。
- **記事用バラエティ＝青タイトルバーなし（`6fdf731`）を維持**。今回いっさい触れていない。

### ④ 画像0枚時は H2 ごと省略（前詰め）

新設ヘルパー **`_existing_files(files, output_dir)`**（`wp_client.py`）が
「ファイル名リストのうち **`os.path.isfile()` で実在するものだけ**を順序を保って返す」。
`plan_blocks()` は **1枚以上あるときだけ H2 を append** する。

- **末尾の実在0枚 → 「末尾」H2ごと出さない。**
- **バラエティの実在0枚 → 「バラエティ」H2ごと出さない。**
- 存在しないセクションは完全に省略し、**後続セクションを前詰め**する。
- **payload にファイル名があっても `output_dir` に実ファイルが無ければ H2 を出さない**
  （⑦でチェックを外した画像は⑧が `os.remove` するため、この判定で自動的に追従する）。
- **旧 payload で `suebangai` / `variety` キー自体が無くても例外を出さない**
  （`payload.get(...)` と `(files or [])` の二重ガード）。`None` / `[]` / 空文字 / 空白も安全。
- **`optional=True` は使わない。**`optional` は「見出しを残して画像だけ省く」挙動で今回の要件と逆。
  必ず**先に実在確認してから H2＋画像をまとめて追加**する。
- **既存の「その他」セクションは H2 を無条件 append する従来挙動のまま**（今回変更していない）。

### ⑤ 前詰め4パターン（純粋テストで確認）

| パターン | H2順 |
|---|---|
| ① 末尾あり・バラあり | 全台系 → 高配分 → **末尾** → 並び → **バラエティ** → ジャグラー → その他 → シマズ |
| ② 末尾なし・バラあり | 全台系 → 高配分 → 並び → **バラエティ** → ジャグラー → その他 → シマズ |
| ③ 末尾あり・バラなし | 全台系 → 高配分 → **末尾** → 並び → ジャグラー → その他 → シマズ |
| ④ 両方なし | 全台系 → 高配分 → 並び → ジャグラー → その他 → シマズ |

**②③④は「純粋テストで確認済み・実データでの実機確認は未実施」である。**
**「実機確認済み」と書かない。** 8/24 の実データは末尾・バラエティが**両方存在した**ため、
実機で確認できたのは①のパターンだけである。

あわせて純粋テストで次を確認済み：payload に名前はあるが実ファイルなし → H2ごと省略 ／
旧payload（キーなし）・`None`・`[]`・空文字・空白・存在しないファイル名で例外なし ／
`collect_files()` が末尾・バラエティを `found` に含め `missing_required` は0件 ／
送信対象が全ユニーク（重複アップロード増なし） ／ `build_content()` の最終HTMLに
空の末尾H2・バラエティH2が残らない ／ **末尾・バラエティを空にしたとき HEAD版と
plan のブロック集合・ブロック数・各セクションの中身・送信対象ファイル集合が完全一致**
（差はジャグラー/並びの順序のみ＝意図した変更）。

### ⑥ 非回帰（純粋テスト）

- **HEAD にあった関数のうち本体が変わったのは `plan_blocks` のみ**、
  **新設関数は `_existing_files` のみ**（`wp_client.py` の全関数を機械比較）
- `h3_zendai` / `h3_narabi` / `_resolve_high_images` / `narabi_file_name` / `collect_files` /
  `build_content` / `build_payload` / `plan_split` / `upload_media` / `create_draft` /
  `create_takadanobaba_draft` / `split_image_for_wp` / `build_poster` / `app_safe_fn` /
  `narabi_safe_fn` / `high_file_name` / `is_manual_high` / `fmt_signed` / `ban_range_str` —
  **すべて本体バイト一致**
- `streamlit_app.py` は**本体が変わったのは `show_auto_article_page` のみ**・新設関数なし・
  差分は**1ハンク（payload 追加11行・削除0行）**
- **`show_auto_page`（通常ページ全域）が HEAD とバイト完全一致**
- `_build_machine_img` / `_build_machine_img_no_bar` / `_art_high_title_bar` /
  `_build_sue_images` / `_apply_panel_to_table_img` / `_attach_slump_to_table` /
  `_build_article_machine_img` / `_build_panel_row` の**8関数すべてバイト一致**
- **`build_payload()` のシグネチャは変更していない**（payload キーは呼び出し側で追加）

### ⑦ ⑦プレビュー順は変更しない

**WordPress本文順だけを変更した。⑦プレビューは従来順のまま維持する。**
⑦は `全台系 → 高配分 → 並び → 末尾 → ジャグラー → その他 → バラエティ` の順で、
**WordPress本文順とは意図的に異なる**。⑦をWordPress順へ揃える必要はない。
`show_auto_article_page` の payload 追加箇所より前が HEAD とバイト完全一致であることで裏付け済み。

### ⑧ ローカル実機確認結果（2026-08-25・正式HEAD `bf2c005` で起動して実施）

**2026/8/24 のデータ**（末尾①=8／末尾②=7・モード「全台」、バラエティ「+1,000枚以上の優秀台」）。

- ⑦プレビュー・⑧本番とも **末尾2枚（`末尾8番台の優秀台.jpg` / `末尾7番台の優秀台.jpg`）**、
  **バラエティ1枚（`バラエティの優秀台.jpg`）** が従来どおり生成。出力フォルダに実在を確認
- ⑧の「生成されたファイル」一覧・ZIP（`_make_zip_bytes(output_dir)` でフォルダ丸ごと）に両方含まれる
- **WordPress 送信対象に末尾・バラエティが追加された**：送信前表示 **30枚 / 24.33 MB**
- **新規 draft を1件だけ作成**（ボタンは1回のみクリック）

| 項目 | 値 |
|---|---|
| 投稿ID | **60486** |
| タイトル | `8月24日(月)│エスパス高田馬場│` |
| status / category / author | **`draft` / `[24]` / `14`** |
| 実アップロード media | **39枚**（送信対象30枚が長尺分割で39片） |

- **本文の H2 順が正式順と完全一致**（REST API の `content.raw` で機械確認）
- **「末尾」H2直下は末尾画像のみ**、順序は **末尾8（3片）→ 末尾7（3片）**＝⑧の生成順
- **「バラエティ」H2直下はバラエティ画像1枚のみ**、**並びの直後・ジャグラーの直前**
- 本文の画像39枚＝media 39枚で整合、**同一画像の重複掲載0件**
- **WordPress エラー0件**（401 / 403 / 429 / 5xx / Traceback / MemoryError なし）。
  **既存投稿の update・DELETE・公開なし**

**非回帰（すべてPASS）**：全台系H3（`喰霊零Re(2/2台+)→平均+1,950枚` 形式・矢印 `&#x2192;`・
旧 `&#x27a1;` 0件）／高配分H3同形式／**マイナス平均のH3は「平均」非表示**（SAOII・スマスロ北斗）／
高配分の平均差枚降順 `[5933, 2050, 1388, 1256, 1030, 462, 225, 221]`／全台系降順 `[1950, 50]`／
並びH3の新表記（`【5台並び】カバネリ海門決戦(2171〜2175番台)→平均-520枚`・旧 `▶` 0件）／
**並びはマイナス平均も表示**／ジャグラー順序・統合画像／その他（分割5片）／シマズ／記事上部／
**X用空段落3つ**／店舗情報ボタン（`wp:loos/button` 1件・本文末尾）／長尺分割・2560px・q95・4:4:4／
All-or-Nothing。

### ⑨ ⑧実行の安全確認（毎回行うこと）

`_git_auto_push()` の targets（`weekly_items.json` / `auto_page_inputs.json` /
`auto_page_persistent_inputs.json` / `article_page_inputs.json` / `rote_machines.json` /
`store_settings`）と**現在の未コミット差分を機械照合し、交差0件を確認してから⑧を実行する**。
今回は `wrt_machines.json` / `機種名変換.xlsx` の既存差分が targets 外だったため安全に実行できた
（実行後も両ファイルの sha256 は無変化）。交差がある場合は⑧を実行しない。

### ⑩ メモリ実測（ローカル値であることを明記）

**ローカル実機の PeakWorkingSet 最大 1,624.7 MB**（実行後の現在値 917.5 MB）。
**OOM / killed / unexpected restart は0件。**

**これはローカル実測であり、Cloud の実機値ではない。**
Cloud はメモリ上限がローカルより厳しいため、**Cloud で同等のデータ量（39片・24.33MB送信）を
送る際は RSS を確認すること**。
**今回の Cloud 安定性を「確認済み」と書かない**（Cloud 実機確認は未実施）。

### ⑪ 今回の正式確認に含めないもの（別案件）

**二重作成防止UIの動作は今回の正式確認に含めない。**
実機確認では、下書き作成に成功したあとも WordPress 作成ボタンが `disabled=false` のままで、
「もう一度作成する」チェックボックスも DOM 上に確認できなかった。
ただし**今回作成した draft は 60486 の1件のみで、ボタンは1回しか押していない**。
この挙動は今回の変更範囲外（`create_takadanobaba_draft` は本体バイト無変更）であり、
原因調査・修正は**別案件**とする。
**「二重作成防止が正常確認済み」とは書かない。**


## 渋谷新館 ローテ用：月間オススメ表①の空欄日保持（2026-08-26 確定・`f23e0e4`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】ローテ用 → 📅 月間オススメ表①（t2）だけ**。
正式コード commit は **`f23e0e4`**（`fix: 渋谷新館月間表で空欄日を日付キーから反映`・
**`streamlit_app.py` のみ**・1ハンク +15 −3）。

### ① 正式仕様

**「（空欄にする）」ONの日は、その日を月間表から除外しない。前日までで画像を打ち切らない。**

- **その日の日付列を表示する**
- **その日の領域（列）を作る**
- **オススメ内容だけ空欄にする**

2026/08/26（東京喰種）の例では **8/20・8/21・8/22・8/23・8/24・8/25・8/26** の7列を出し、
**8/26は日付ラベルのみ・内容は空欄**とする。

### ② 月途中の空欄も同仕様（最終日の特例ではない）

```
8/24 印あり
8/25 「（空欄にする）」ON  ← 空欄のまま列を残す
8/26 印あり
```

**8/25を削除して 8/24 → 8/26 へ詰めない。**3日をそのまま表示する。

### ③ 原因（「条件追加」ではなく「読み取り形式の是正」）

**「（空欄にする）」の保存・復元自体は正常だった。**渋谷新館 t2 は日付キー方式
**`blank_date_checks`** で保存されており、実データも
`blank_date_checks["2026-08-26"] = true` が正しく入っていた。

一方、画像生成側は従来 **位置配列 `blank_days`** を読んでいたため、8/26 は
「通常印なし ＋ 空欄フラグ false」となり、既存の
**「印あり OR 空欄ON」**という最終列判定で 8/25 までトリムされていた。

**よってこの修正は「空欄ONを判定条件へ新たに追加する」ものではなく、
「正しい保存形式から空欄状態を読む」ものである。**判定条件そのものは元から正しい。

### ④ 修正箇所

**`show_rote_page()` 内の週間／月間表画像生成時の `_wt_blank` 読み出し部分のみ。**
t2 / t4 / t5 は **`blank_date_checks`（日付キー方式）を優先**して読む。
旧位置配列モードの互換のため、**必要な場合だけ** `blank_days` へフォールバックする。

### ⑤ フォールバックの正式仕様（無条件フォールバック禁止）

**「日付キーが無ければ常に `blank_days`」としてはならない。**
上野本館 t4 / t5 の実データに**旧 `blank_days=True` が残っており**、無条件フォールバックすると
既存挙動が変わることを実測で確認した。

正式条件は **UI が位置配列方式で保存していた旧経路だけ**フォールバックする:

```python
_wt_blank_pos = (_load_weekly_blank_days(store, _wtn)
                 if (_rd is None and store != "上野本館") else [])
```

- **`_rd is None` かつ `store != "上野本館"` の場合のみ**位置配列フォールバック
- **上野本館は常に日付キーモードとして扱う**
- UI 側の
  `_use_excel_date = _tn in (2,4,5) and (excel_date is not None or store == "上野本館")`
  と**読み出し側を鏡合わせ**にする

**「無条件フォールバック」へ戻さない。**

### ⑥ 機種非依存

**東京喰種専用の修正ではない。**判定に使うのは **blank / checks / 日付** のみで、
**機種名は条件に使わない**。**東京喰種をハードコードしない。**
月間オススメ表①の対象機種すべてへ共通仕様として適用する。

### ⑦ 純粋テスト（全PASS）

| # | 条件 | 期待／結果 |
|---|---|---|
| ① | 8/20〜8/25印あり・8/26印なし＋blank=true | `last_col=6`・**8/26まで残る** |
| ② | 8/26印なし＋blank=false | 従来どおり**8/25まで** |
| ③ | 8/24印あり・8/25 blank=true・8/26印あり | **8/25を含め3日すべて残る** |
| ④ | 途中に複数 blank=true | **列削除・前詰めなし** |
| ⑤ | `blank_date_checks=true` / `blank_days=false` | **日付キーの true を優先** |
| ⑥ | 日付キーなし・旧位置配列モードで `blank_days=true` | **true をフォールバック** |
| ⑦ | 両方なし／false | false |

### ⑧ ローカル実機確認結果（2026-08-26・正式HEAD `f23e0e4`）

対象：渋谷新館 ローテ用 ／ 8/26 Excel ／ 東京喰種。
出力：`20260826_エスパス渋谷新館\東京喰種表.png`（デスクトップ直下の出力フォルダ）

- **8/26(水) 列あり**・**8/25打ち切り解消**・**8/20〜8/26の7列**
- **8/26の内容は完全空欄**（日付ラベルのみ・6項目すべて○なし・白セル）
- **8/25の鈴屋什造・クロナナシロ等の印が8/26へ伝播していない**（コピーなし）
- **勝手な補完なし**・**日付順正常**
- 画像サイズ **修正前 1616×684 → 修正後 1776×684**。
  **幅 +160px ＝日付列1つ分だけ増加／高さ684pxは不変**
- **列幅・行高・タイトルバー・黄色セル・ベージュ項目列・罫線・フォント・色は従来どおり**
- UI上で 8/26 の「（空欄にする）」にチェックがある**保存状態のまま生成**。
  **JSONの直接編集はしていない**
- 同じ生成で `東京喰種表.png` / `スマスロ北斗の拳表.png` / `ジャグラー系表.png`、
  および `東京喰種ローテ` / `北斗転生2ローテ` / `スマスロ北斗の拳ローテ` / ランキング /
  結果テキスト / ZIP も**従来どおり正常生成**

### ⑨ 上野本館の非回帰（実データ確認済み）

上野本館 **t2 / t4 / t5 × 開始日4種 × `_rd` 有無**で、
**`_wt_blank` / `_wt_last_col` / 日付ラベル / checks がHEAD版と完全一致**。

特に **t4 の `blank_days=[F,T,F,F,F,F,F]`**、**t5 の `blank_days=[F,F,T,F,F,F,F]`** という
**旧残留データを新ロジックが拾わない**ことを確認した（上野本館は日付キーモードのため
この旧位置配列をフォールバックしない）。

### ⑩ t1 / t3

**t1（週間オススメ表①）・t3（週間オススメ表②）は `_wtn in (2, 4, 5)` の対象外**で、
**従来の位置配列方式のまま**。今回変更していない。

### ⑪ Cloud

**Cloud Reboot は未実施。Cloud 実機確認も未実施。**
**今回の正式確認はローカル実機である。**「Cloud実機確認済み」とは書かない。

### ⑫ 無変更（今回いっさい触れていない）

「（空欄にする）」UI ／ widget key ／ `blank_date_checks` の保存処理 ／
`blank_days` の保存処理 ／ 復元処理 ／ `weekly_items.json` 構造 ／ `date_checks` ／
印の種類 ／ 画像レイアウト ／ 画像サイズ計算 ／ 列幅 ／ 行高 ／ フォント ／ 色 ／
ファイル名 ／ ZIP ／ 月間オススメ表②③ ／ 週間①② ／ ローテ画像 ／ ローテ抽出 ／
ランキング ／ 結果テキスト ／ 通常結果ポスト ／ 記事用 ／ 他店舗。

## 渋谷新館 記事用ページ（2026-08-28 確定・`73db0ba` / `0478dd5` / `a9d236a` / `d121e54`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の📰記事用ページだけ**。
高田馬場の記事用を土台に流用しているが、**記事仕様は店舗別**とする。
**仕組みは流用してよいが、記事仕様を店舗共通にしてはならない。**
高田馬場・秋葉原の記事用へ影響を出さないこと。

正式HEAD: **`d121e54`**（HEAD = origin/main 一致を確認済み）

### 正式コミットの流れ

| commit | 内容 |
|---|---|
| `73db0ba` | 記事用入力の**店舗切替分離**（`_ART_SHARED_KEYS` の16キー＋`art_current_excel`＋`_art_prev_excel` を店舗変更時にクリア。`_art_prev_store` scope ガードを `_save_article_inputs()` へ追加） |
| `5dc22e6` | 渋谷新館に「記事用」入口を追加 |
| `0478dd5` | 渋谷新館の記事用UI骨格（`_ART_STRUCT_V2_STORES`） |
| `a9d236a` | ⑥オススメ優秀台の初期実装（記入式・単純9枠。**最終仕様ではない**） |
| **`d121e54`** | **⑤オススメ入力を6ブロック化（現在の正式）** |

### ① 正式な採番（渋谷新館のみ）

```
📄 Excelファイルをアップロード   ← 番号外
① 冒頭部分
② 高配分
③ 並び
④ 末尾
⑤ オススメ機種の優秀台
⑥ 差枚数ランキング＆島図
🔍 プレビュー                   ← 番号外
▶▶ 自動処理を開始               ← 番号外
```

ゲートは **`_ART_STRUCT_V2_STORES = frozenset({"渋谷新館"})`** → `_art_v2`。
採番は `_sec_num()` のカウンタ方式なので、**見出しブロックを消せば後続が自動で前詰め**される。
**手動で番号を書き換えない。**

**高田馬場・秋葉原の採番（①Excel ②ポスター画像 ③個別画像 ④並び画像 ⑤末尾画像
⑥バラエティ画像 ⑦プレビュー ⑧実行）は変更しない。**

### ② 全台系：独立UI見出しは出さないが、自動生成は維持する

**「UI見出しなし」≠「全台系画像を生成しない」。**

- 渋谷新館では **「全台系」という独立見出しを表示しない**。
- ただし **`run_step1_main()` / `zen_dai_list` による自動全台系の抽出・画像生成は従来どおり維持**する。
  **削除しない。**
- 記事へ載せたい全台機種を手動指定する場合は、**②高配分内の既存「個別画像 → 全台」
  （`art_kojin_z_0`〜`art_kojin_z_11` の12枠）** を使う。この入力欄は従来どおり表示する。
- 実機8/27で **`東京リベンジャーズ.jpg` / `ウルトラミラジャグ.jpg`** が自動全台系画像として
  正常生成されることを確認済み。

**理由**: 自動全台系を廃止すると `zen_dai_list` が手動分だけになり、⑤の除外集合・結果テキストの
👑全台系・WordPressの全台系H2まで波及する。今回は**見出しだけを消す（案A）**を正式採用した。

### ③ その他の優秀台：独立UI見出しは出さないが、自動生成は維持する

- **「その他の優秀台」という独立見出しを表示しない。設定UI・ON/OFFも作らない。**
- **`run_step3_other()` による `その他の優秀台ピックアップ.jpg` の自動生成は維持**する。
  該当0台なら画像なし（既存の `return` 経路）。
- 実機8/27でプレビューに自動生成されることを確認済み。
- **`run_step3_other()` 本体・その他優秀台の抽出条件・ファイル名は変更していない。**

### ④ ⑤ オススメ機種の優秀台（記入式・6ブロック）

新小岩スランプ付き結果ポスト用⑤を**参考**にしたが、**記事用の独自仕様**とする。
**新小岩⑤（6ブロック×9枠・`store_settings` 保存・ブロック単位で1枚へ統合・
`generate_recommended_block_image()` が青バーへタイトル描画）とは別物。**

| 項目 | 渋谷新館 記事用⑤ |
|---|---|
| ブロック数 | **6**（2列×3段で配置） |
| 各ブロック | **タイトル1欄 ＋ 機種6欄**（機種欄は**3列×2段**） |
| 合計 | **タイトル6欄 ／ 機種36欄 ＝ 42キー** |
| ON/OFFチェック | **作らない** |
| 定数 | `_ART_OSUSUME_STORES = frozenset({"渋谷新館"})` ／ `_ART_OSUSUME_BLOCKS = 6` ／ `_ART_OSUSUME_PER_BLOCK = 6` |

**正式キー（店舗suffix付き）**:

```
art_osusume_title_0_{store} 〜 art_osusume_title_5_{store}      … 6個
art_osusume_m_0_0_{store}   〜 art_osusume_m_5_5_{store}        … 36個
```

- **`_article_input_keys(store)` に登録**し、**`article_page_inputs.json` の
  日付（Excel名）単位**で保存・復元する。
- 保存は既存 **`_save_article_inputs(store)`** の `on_change`。**新しい保存関数を作らない。**
- 初期値は **`_art_kojin_default(excel, store, key)` → `value=default`** でブラウザまで渡す
  （⑤ `39f1f1e` の「seed だけで `value=` を渡さない実装へ戻さない」に準拠）。
- 機種欄は既存 **`render_machine_autocomplete_input()`** を再利用（**関数本体は無変更**）。
- **店舗suffix付きなので `_ART_SHARED_KEYS` へは足さない。**

### ⑤ 旧9キーの扱い

旧仕様（`a9d236a`）の **`art_osusume_m_0_{store}` 〜 `art_osusume_m_8_{store}`（9キー）** は
**正式入力対象から外した**（`_article_input_keys()` から除去済み）。

- **既存JSONに残っていても削除しない。**（`kojin_y_8_秋葉原` `611a452`・新小岩② `cf1e27a` と同じ「残置」）
- **新42キーへの自動移行コードを作らない。**
- **今後いっさい読み込まない。**
- 実機で、旧9キーに6機種が残っている 8/27 を開いても **新UIは42枠すべて空欄**で始まることを確認済み。

### ⑥ ブロックタイトルは画像へ描画しない

**最重要。**

- ブロックタイトルを **`_art_high_title_bar()` / `_build_machine_img()` /
  `_build_machine_img_no_bar()` / `_build_article_machine_img()` /
  `generate_recommended_block_image()` へ渡してはならない。**
- タイトルは `article_page_inputs.json` に保存するだけで、**将来のWordPress記事の
  小見出し（H3等）として使う値**である。
- 実機で「メイン機種をチェック！」「こちらの機種も要注目！」を入力しても、
  生成JPEGに**この文字が描かれていない**ことを確認済み。

**⑤の各機種画像に描く青タイトルバーは固定文言**:

| 対象 | バー文言 | 色 | バー高 |
|---|---|---|---|
| **⑤ オススメ** | **`オススメ機種の優秀台`**（`_ART_OSUSUME_BAR_TEXT`） | `#0080FF` | 43px（等倍） |
| **③ 高配分** | **`優秀台ピックアップ`**（`_ART_HIGH_BAR_TEXT`・`d5ba1bb`） | `#0080FF` | 43px（等倍） |

**この2つの文言を混ぜない。`_art_high_title_bar()` の `text` 既定値は変更しない。**

### ⑦ ⑤の掲載済み除外（機種単位）

⑤へ入力された機種でも、**自動全台系・高配分ですでに画像掲載されている機種は⑤から除外**する。

- 判定は既存 **`filter_recommended_machines(machines, df, zen_names, high_names, ban_level=False)`**
  をそのまま使う。**新しい条件を作らない。**（重複除去・入力順維持も同関数が行う）
- `zen_names` = `zen_dai_list[].name` ＋ ②個別「全台」の入力機種
- `high_names` = **`high_ratio_list` のうち `has_image=True` のものだけ** ＋ ②個別「優秀台」の入力機種
- **`has_image=False` の機種は⑤で画像生成してよい**（高配分画像が作られていないため）。
- **`recommended_machines` は流用しない**（⑦その他・ジャグラー統合まで巻き込むため）。

**実機8/27の結果（期待と一致）**:

| 入力 | 結果 |
|---|---|
| スマスロ北斗の拳 | **⑤生成**（`has_image=False` のため誤除外されない・4台） |
| 東京喰種 | 高配分掲載済みで除外 |
| マイジャグV | 高配分掲載済みで除外 |
| ウルトラミラジャグ | **全台系**掲載済みで除外 |
| ネオアイム | 高配分掲載済みで除外 |
| ファンキー2 | **⑤生成**（7台） |

### ⑧ ⑤の画像生成

- **1機種につき1画像。ブロック単位で1枚へ統合しない。**
- ファイル名は **`{機種名}_オススメ優秀台.jpg`**（`_make_safe_fn` 経由）。
- 優秀台の抽出は既存 **`_kojin_yushu_filter()`**。**新しい条件を作らない。**
- **優秀台0台の機種は画像を作らない。**
- **入力順を維持**する（ブロック1→6、各ブロック内は機種1→6）。
- **同一機種が複数ブロックにあるときは最初の1回だけ採用**する。
- **ブロックタイトルが空でも、機種が入っていれば画像を生成する。**
- **タイトルも機種6枠もすべて空のブロックは完全に無視**する（plan にも含めない）。
- 実装は **`_art_osusume_images()`**（⑦プレビュー・⑧本番で共用）。
  画像順は**④末尾の後・ジャグラー統合の前**。

### ⑨ WordPress用 plan（保持のみ・送信はまだしない）

新設ヘルパー **`_art_osusume_plan(blocks, gen_fns)`** が、ブロックタイトルと
**そのブロックから実際に生成された画像**の対応を返す。

```python
[
  {"title": "メイン機種をチェック！",
   "images": ["スマスロ北斗の拳_オススメ優秀台.jpg", "ファンキー2_オススメ優秀台.jpg"]}
]
```

- ⑦プレビュー・⑧本番とも `st.session_state[f"_art_osu_plan_{store}"]` へ保存する。
- **画像0枚のブロックは plan に含めない。**
- **タイトル空欄＋機種ありのブロックは `title=""` のまま残す**（将来H3なしで画像だけ掲載）。
- **現時点ではWordPress送信に使用していない。`wp_client.py` は無変更。**

関連する新設ヘルパー: **`_art_osusume_collect(store)`**（session_state から6ブロック分を読むだけ・
保存はしない）／**`_art_osusume_flat(blocks)`**（入力順のフラットリスト）。

### ⑩ 店舗切替分離（`73db0ba` を維持）

- 店舗変更時に **`_ART_SHARED_KEYS`（16キー）・`art_current_excel`・`_art_prev_excel` をクリア**し、
  `_art_prev_store` を更新する。
- **`_save_article_inputs()` の scope ガード**（`_art_prev_store != store` なら書かない）を維持する。
- **`art_upload` は pop しない**（Streamlit の stale widget GC で消えることを実機確認済み）。
- 渋谷新館⑤の新42キーは**店舗suffix付き**なので `_ART_SHARED_KEYS` への追加は不要。
- 実機で **渋谷新館 → 高田馬場 → 秋葉原 → 渋谷新館** の往復を確認し、
  **混在なし・8/27の値が同じブロック／同じ順序で復元**されることを確認済み。

### ⑪ 実機確認結果（2026-08-28・ローカル・正式HEAD `d121e54`）

8/27 確定データ（433台）でプレビューを実行し、**15枚**を確認：

```
 1. 東京リベンジャーズ.jpg          ← 自動全台系（維持されている）
 2. ウルトラミラジャグ.jpg          ← 自動全台系
 3-11. 高配分9枚
12. スマスロ北斗の拳_オススメ優秀台.jpg   ← ⑤
13. ファンキー2_オススメ優秀台.jpg        ← ⑤
14. ジャグラーシリーズ優秀台.jpg
15. その他の優秀台ピックアップ.jpg        ← 自動生成（維持されている）
```

確認済み: 採番①〜⑥ ／ 全台系見出し0件 ／ その他の優秀台見出し0件 ／
⑤は6ブロック・タイトル6・機種36・ON/OFFなし ／ 旧9キーがUIへ出ない ／
新42キーの日付保存と復元 ／ 店舗切替で混在なし ／ ⑤バーは固定文言・
ブロックタイトル非描画 ／ ③高配分バーは「優秀台ピックアップ」のまま ／
高田馬場・秋葉原は①〜⑧のまま非回帰（⑤UIのwidget 0件） ／
`weekly_items.json` / `rote_machines.json` / `store_settings` / `wp_client.py` は不変 ／
例外・Traceback 0件。

**⑧本番は実行していない。WordPress通信も0件。**

### ⑫ 現時点で未実装（次回の作業）

**優先Step 1 — ⑤掲載台番を「その他の優秀台」から除外する。**

- **機種単位ではなく「⑤画像に実際に掲載された台番」の除外を基本とする。**
- 台番集合は既に取得できる： **⑦プレビュー＝`_art_osu_bans` ／ ⑧本番＝`_art_osu_bans_e`**
  （いずれも `_art_osusume_images()` が返す `{ファイル名: 掲載台番リスト}`）。
- 除外の合流先候補は `run_step3_other()` の
  **`_ex_bans = narabi_bans | suebangai_bans`**。
  `suebangai_bans` へ混ぜず、**`osusume_bans: set[int] = set()` を1引数追加して OR する**のが安全
  （既定 `set()` なので他店舗・他ページは不変）。
- **順序の課題**: 現在 `_art_osusume_images()` は `zen_names` / `high_names` を得るため
  **`run_auto_pipeline()` の後**に呼ばれている。除外を効かせるには pipeline を2回呼ぶか、
  ⑤を先に確定する構造変更が要る。**調査してから実装すること。**
- 実機8/27では **スマスロ北斗の拳の 2038・2044** が⑤とその他優秀台で重複している。
  **これは既知の未対応事項であり、現時点の不具合ではない。**

**Step 2 — ⑤とジャグラーシリーズ優秀台の重複整理。**
ファンキー2 のようなジャグラー機種が⑤へ載ると、ジャグラー統合画像にも同じ台が入り得る。
`run_step2_juggler()` も `narabi_bans` / `jug_sue_bans` を受ける構造なので同じ形で渡せる。
**これも既知の未対応事項。**

**Step 3 — ⑥ 差枚数ランキング＆島図の実装。**

**Step 4 — 渋谷新館のWordPress対応。**
⑤のブロックタイトルを記事の小見出しとして使う。
`plan_blocks_shibuya()` の新設を想定し、**既存 `plan_blocks()`（高田馬場用）は変更しない**。
その他の優秀台は `_existing_files()` パターンへ揃え、**0枚なら見出しごと省略・前詰め**とする。

**上記4件はいずれも今回未実装。`wp_client.py` も無変更。**

### ⑬ 非回帰対象（渋谷新館を改修するときは必ず確認）

**高田馬場の記事用 ／ 秋葉原の記事用 ／ 通常結果ポスト ／ スランプ付き結果ポスト ／ ローテ用。**

特に **`run_auto_pipeline` / `run_step1_main` / `run_step2_juggler` / `run_step3_other` /
`_kojin_yushu_filter` / `filter_recommended_machines` / `render_machine_autocomplete_input` /
`_save_article_inputs` / `_restore_article_inputs` / `_art_kojin_default` /
`_build_machine_img` 系 / `_art_high_title_bar`** などの**共通処理を変更する場合は、
必ず他店舗への影響を先に調査**すること。今回の `d121e54` ではこれらの関数本体を
**1つも変更していない**（変更したのは `_article_input_keys()` と `show_auto_article_page()` の2つ、
新設は `_art_osusume_collect` / `_art_osusume_flat` / `_art_osusume_plan` の3つだけ）。

## 渋谷新館 記事用ページ：⑤重複除外と⑥差枚数ランキング（2026-08-31 確定・`551c9d5` / `d477a91` / `1bd0e3b` / `39b652d`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の📰記事用ページだけ**。
「渋谷新館 記事用ページ（2026-08-28 確定・`73db0ba` / `0478dd5` / `a9d236a` / `d121e54`）」の
⑫で保留していた項目のうち、**Step 1・Step 2・Step 3-1 を正式実装・実機確認済み**にしたもの。
高田馬場・秋葉原の記事用へ影響を出さないこと。

### 正式コミットの流れ

| commit | 内容 |
|---|---|
| `551c9d5` | **Step 1**: ⑤オススメ台を「その他の優秀台」から除外 |
| `d477a91` | **Step 2**: ⑤オススメ台を「ジャグラーシリーズ優秀台」から除外 |
| `1bd0e3b` | **Step 3-1**: ⑥差枚数ランキング画像を追加 |
| `39b652d` | Step 3-1 の初期順位を50位に修正（未保存日で20位になっていた不具合） |

---

## Step 1：⑤オススメ機種と「その他の優秀台」の台番重複除外（`551c9d5`）

⑤「オススメ機種の優秀台」に**実際に掲載される台**は、
「その他の優秀台ピックアップ」へ**重複掲載しない**。

**除外は機種単位ではなく台番単位。**⑤に入力された機種の全台を除外するのではなく、
既存の⑤抽出条件を満たして⑤掲載候補となった台番だけを「その他の優秀台」から外す。

### 実装

- `run_auto_pipeline()` に **`osusume_machines: set[str] = set()`**（既定＝従来動作）
- `run_step3_other()` に **`osusume_bans: set[int] = frozenset()`** を追加し、
  既存の **`_ex_bans = narabi_bans | suebangai_bans | set(osusume_bans)`** へ OR する
  （並び台・末尾台とまったく同じ既存の除外機構に相乗りする）
- **ジャグラー overflow → その他 の入口にも同じ `osusume_bans` を適用する。**
  「その他」へ入る入口が複数ある以上、通常経路だけ除外して overflow を素通しにすると
  不整合になるため。**この overflow 対応は正式採用済み。削除しないこと**
  （`run_step2_juggler` / `jug_pool_df` / ジャグラーシリーズ優秀台画像には影響しない）
- 呼び出しは `show_auto_article_page` の**⑦プレビューと⑧本番の2か所**。
  `art_osusume_machines` は渋谷新館でのみ非空なので、**他店舗は空集合＝従来動作**

### なぜ機種単位フィルターを事前に掛けないか

⑤候補台番の算出では**全台系・高配分の機種単位フィルターを掛けない**。
全台系・高配分で画像化された機種の台は `run_step3_other` が元から「その他」へ回さないため、
事前に除外しても結果は変わらない（余分に消える台がない）。これで
「⑤は pipeline の後にしか確定しない」という循環を解いている。

### 8/27 渋谷新館の正式確認値

```
⑤スマスロ北斗の拳 : 2001 / 2038 / 2042 / 2044
⑤ファンキー2      : 2151 / 2155 / 2157 / 2159 / 2160 / 2161 / 2165
その他の優秀台     : 36台 → 33台
その他から消えた台 : 2001 / 2038 / 2044
⑤ ∩ その他        = 0台
```

**`2042` は元から「その他」の条件を満たしていない**ため、⑤のON/OFFによる
「その他」側の差分には現れない。

---

## Step 2：⑤オススメ機種と「ジャグラーシリーズ優秀台」の台番重複除外（`d477a91`）

⑤に**実際に掲載される台**は「ジャグラーシリーズ優秀台」へも**重複掲載しない**。
こちらも**機種単位ではなく台番単位**。⑤に載っていない同一機種の台は、既存条件を
満たす限り従来どおり統合画像へ残る。

### 実装

- `run_auto_pipeline()` 内で **`_osusume_bans` を1回だけ算出**し、
  **`run_step2_juggler` と `run_step3_other` の両方へ渡す**
  （Step 1 で追加した算出処理を Step2 の前へ移動しただけ）
- 算出は既存の **`_kojin_yushu_filter()`** を再利用する。パイプラインが既に持つ
  `df` / `diff_raw`（差枚補正済み）/ `cfg` だけを使い、**df の再取得・差枚補正の複製・
  ⑤抽出条件の別実装は禁止**（二重実装は将来必ずズレる）
- `run_step2_juggler()` に `osusume_bans` を追加し、
  **`_jug_pool_osu = set(osusume_bans) & set(jug_bans_all)`** を作る

### ★ `osusume_bans` をそのまま `jug_excellent_list` から引いてはいけない

`osusume_bans` には**⑤入力機種のうち全台系・高配分で自前の画像を持つ機種の台**も含まれる
（8/27 では 東京喰種・マイジャグV・ウルトラミラジャグ・ネオアイム）。
`jug_excellent_list` は**全ジャグラー機種の +1,000枚台**を集めるため、そのまま引くと
**統合画像から消えていない台まで結果テキストから落ちる**（実測で41台の過剰除外）。

必ず **`_jug_pool_osu`（＝実際にジャグラー統合プールへ入った⑤台）だけ**に限定する。

### 除外位置

プール確定・`jug_bans_all` 算出・**`≤5台 overflow 判定`・`sonota_exclude` 判定の後**、
既存の🎯除外（`exclude_units["juggler"]`）と**同じ位置**で引く。
抽出条件・overflow判定・画像生成可否は「除外前」の `combined` で確定済みなので、
ここで台を減らしても**画像カテゴリの再判定は起こらない**。
`jug_excellent_list` も同じ `_jug_pool_osu` で絞り、**画像と結果テキストを一致**させる。

### 8/27 渋谷新館の正式確認値

```
ジャグラーシリーズ優秀台 : 14台 → 7台
消えた台 : 2151 / 2155 / 2157 / 2159 / 2160 / 2161 / 2165
残る台   : 2147 / 2169 / 2171 / 2229 / 2233 / 2234 / 2241
⑤ ∩ ジャグラーシリーズ優秀台 = 0台
```

**⑤画像自体の掲載内容は Step 1 以前から変更しない**（実機で media ハッシュ一致を確認済み）。

### 無変更

`run_step2_juggler` の抽出条件・差枚条件・対象機種条件・並び順・画像デザイン・
ファイル名・スランプ・パネル・液晶／`jug_pool_df` の生成方法／
`generate_report_text()`（結果テキストの関数・条件・文言・並び順）。

---

## Step 3-1：⑥ 差枚数ランキング画像（`1bd0e3b` / `39b652d`）

⑥「差枚数ランキング＆島図」のうち、**差枚数ランキングは実装・実機確認まで完了**。
**島図は未実装。後日別Stepとして実装する。今回の続きで勝手に島図を実装しないこと。**

### ランキング仕様

| 項目 | 値 |
|---|---|
| ファイル名 | **`差枚数ランキング.jpg`** |
| デフォルト | **50位まで** |
| UI選択肢 | **20 / 25 / 30 / 35 / 40 / 45 / 50位まで** |
| 対象 | **1位から選択順位まで**（35位を選べば 1〜35位。順位を飛ばさない） |
| 並び順 | **差枚降順 → 同差枚は台番昇順**（安定ソート `kind="mergesort"`） |
| 列 | **ベスト / 台番 / 機種名 / ゲーム数 / BIG / REG / AT / 差枚数**（8列） |

- 実データが選択順位に満たない場合は**ある分だけ**。**ダミー行を作らない。**
- **BIG / REG / AT の3列を正式採用**する。**AT列を落とさない。**
  8/27 の1〜2位（SAOII）は `BIG 0 / REG 0 / AT 94` で、ATを落とすと無情報行になる。
- 使用データは**記事用パイプラインの補正済み差枚**（⑦=`_apdf`/`_apdi`、
  ⑧=`result["df"]`/`result["diff_raw"]`）。**`_pipeline_calc_d` の二重適用禁止・
  生データの読み直し禁止。**
- 回転数は既存 `round_games()` + `fmt_games()`、差枚は既存 **`fmt_diff()`**、
  列名変換は既存 `_DISPLAY_RENAME`（BB→BIG / RB→REG / 差枚→差枚数）。
  **新しい丸め方・書式を作らない。**

### デザイン

- **黒タイトルバー**（`_ART_RANK_TITLE_BG = "#111111"`）＋**白文字**「差枚数ランキング」中央
- **薄グレーのヘッダー**（`#E9E9E9`）
- データ行は**薄水色／白の交互背景**（`#DCEBFB` / `#FFFFFF`）。**行全体の背景色**であって
  差枚に比例するバーではない
- 差枚は既存書式の**青文字**（`C_PLUS` / マイナスは `C_MINUS`）
- **差枚数セル内に水色バー／ゲージを描画しない。値に比例した矩形も描画しない。**
  背景はその行の交互色のまま

**描画はランキング専用ヘルパー `_art_ranking_image()` 内に閉じること。**
**共通の `draw_table_image()` や既存画像のデザインを変更してはいけない**
（黒バー・交互背景を共通側へ入れると全画像・全店舗へ波及する）。
既存部品（`load_font` / `_text_w` / `CELL_PAD` / `ROW_H` / `HEADER_H` / `TITLE_H` /
`IMG_FONT_SZ` / `TITLE_FONT_SZ` / `_format_display_cols` / `C_BORDER` 等）は流用する。

### 実機確認サイズ（8/27・渋谷新館）

```
50位版: 1093 × 2319 px
35位版: 1093 × 1659 px
20位版: 1093 ×  999 px
```

**横幅は同一で高さだけ変化する。**
`50 → 35 → 20 → 50` の切替を実機確認済みで、**最後の50位版は最初の50位版と
media ハッシュ一致**。

### ⑦と⑧

**⑦プレビューと⑧本番は同じ `_art_ranking_image()`・同じ件数を使う。別実装にしない。**
⑦は `_art_pil` の末尾（記事の最後）へ、⑧は `_save_jpeg` → `result["files"].append`。

### 保存・復元

- 保存キーは **`art_ranking_limit_{store}`**（店舗suffix方式）。
  `_article_input_keys()` へ1行追加し、既存の `_save_article_inputs()` /
  `_restore_article_inputs()` 経路へ乗せる。**新しい保存システムを作らない。**
- **未保存日は必ず「50位まで」。**保存済みの日付はその日付で選択した順位を復元する。
  **別日へ値を引き継がない**（Excel＝日付単位）。

### ★ 初期値判定の正式仕様（`39b652d`・巻き戻し禁止）

**`_restore_article_inputs()` は未保存の plain キーへ `""` を入れる**ため、
**「キーが session_state に存在するか」だけで初期値を判定してはいけない。**
判定すると seed が走らず、選択肢に無い `""` のまま `st.selectbox` が
**options[0]＝20位**を採用する（⑤ `39f1f1e`・② `0e7dc4c` と同型の事故）。

また **`_art_kojin_default()` は文字列用**なので、**int で保存されるランキング件数の
復元には使用しない**（str 以外を `""` へ潰すため復元できない）。

正式実装は次のとおり。**この形を維持すること。**

```python
_rk_key = f"art_ranking_limit_{store}"
if st.session_state.get(_rk_key) not in _ART_RANK_LIMITS:
    try:
        _rk_saved = int(_load_article_inputs_json()
                        .get(st.session_state.get("art_current_excel") or "", {})
                        .get(_rk_key) or 0)
    except (TypeError, ValueError):
        _rk_saved = 0
    st.session_state[_rk_key] = (_rk_saved if _rk_saved in _ART_RANK_LIMITS
                                 else _ART_RANK_DEFAULT)
```

解決結果（純粋テストで全PASS）：

| 保存値 | 結果 | | 保存値 | 結果 |
|---|---|---|---|---|
| 未保存 / キーなし / `None` / `""` | **50** | | `"35"` | **35** |
| `20` / `25` / `35` / `50` | そのまま | | `"abc"` / `10` / `60` | **50** |

`_restore_article_inputs()` / `_save_article_inputs()` / `_article_input_keys()` /
`_art_kojin_default()` の**共通仕様は変更しない**（他の記事用入力にも関係するため）。

---

## 非回帰で必ず守るもの（渋谷新館 記事用を今後変更するとき）

- ⑤スマスロ北斗の拳の掲載内容 ／ ⑤ファンキー2の掲載内容
- **⑤と「その他の優秀台」の台番重複ゼロ**
- **⑤と「ジャグラーシリーズ優秀台」の台番重複ゼロ**
- 全台系 ／ 高配分 ／ 並び ／ 末尾 ／ その他の優秀台 ／ ジャグラーシリーズ優秀台
- 結果テキスト ／ 記事用の既存②〜⑤
- **高田馬場の記事用 ／ 秋葉原の記事用**
- **新小岩の通常／スランプ付き結果ポスト**、特に **`b530bee` の⑤OFF→その他再振り分け仕様**
- 通常ページ ／ **ローテ用ランキング**

**`generate_ranking_image()` はローテ用の別機能**（2列・レインボー・`ranking_〜ローテ.png`）。
**渋谷新館の記事用ランキングのために変更しないこと。**

---

## 次回の再開地点

次回は渋谷新館の記事用ページ⑥「差枚数ランキング＆島図」の**「島図」実装から再開**する。

ただし**次回もいきなり実装しない**。必ず最初に

1. `CLAUDE.md`
2. `docs/pision_cloud_notes.md`
3. Git履歴
4. 現在コード

の順で確認し、そのうえで島図について
**「現在使えるデータ・既存関数・店舗設定・画像生成方法・保存方法」**を調査して、
**原因／構造／最小実装案／影響範囲を報告し、ユーザーの承認を得てから実装する。**

## 全店舗共通：③ 列画像（列仕掛け）（2026-09-01 確定・`1410753`）

**正式仕様。巻き戻し禁止。**対象は**③「並び画像」が存在する店舗・ページすべて**。
正式コード commit は **`1410753`**（`feat: ③並び画像に列仕掛け画像を追加`・
**`streamlit_app.py` と `convert_narabi_pil.py` の2ファイルのみ**・+249／−16）。push済み。
**HEAD = origin/main = `1410753f520ab74792d533d3f7c5d62351a54f62` を正式基準とする。**

列画像は「新しい画像生成方式」ではなく、
**既存の並び画像生成方式を使って、別の台番範囲から追加画像を作る機能**である。
違いは ①入力する台番範囲が独立 ②タイトルが「機種名（列仕掛け）」 ③ファイル名が衝突しない、の3点だけ。

### ① 対象範囲

**店舗名をハードコードしない。**既存の **`STORE_NARABI_SCRIPT`**（13店舗すべて）に乗る
③並び画像の経路へ追加してある。UI追加箇所は `if store in STORE_NARABI_SCRIPT:` の内側の2か所だけ
（`show_auto_page` と `show_auto_article_page`）。

| 経路 | 関数 | 到達 |
|---|---|---|
| 通常結果ポスト用 | `show_auto_page(with_slump=False)` | ○ |
| スランプ付き結果ポスト用 | `show_auto_page(with_slump=True)` | ○ |
| 新宿歌舞伎町かぶぱ | `show_auto_page(with_slump=True)` | ○ |
| 記事用 | `show_auto_article_page()` | ○ |

**ページごとの既存仕様差（スランプ・パネル・液晶・横版・青バー有無・高解像度など）は、
その店舗・ページの並び画像仕様をそのまま継承する。**
「列画像は全店舗で完全に1種類の画像」にはしない。

### ② UI

```
③ 並び画像
 □ 並び画像も生成する
     台番範囲
 □ 列画像を作成する        ← 追加
     台番範囲（列）        ← 列ONのときだけ表示
```

**並びと列は完全に独立してON/OFFできる。**正式に成立する4パターン:

| | 並び | 列 | 生成 |
|---|---|---|---|
| A | ON | OFF | 従来の並び画像だけ |
| **B** | **OFF** | **ON** | **列画像だけ（並び画像0枚）** |
| C | ON | ON | 並び＋列の両方 |
| D | OFF | OFF | どちらも生成しない |

**B が正式仕様。列ONを並びONの子条件にしてはならない。**

### ③ 台番入力

既存の **`parse_ranges()` / `ranges_to_bans()` をそのまま再利用**する。
**列専用の台番パーサーを新設しない。**入力形式・エラー処理も並びと同じ
（`2001-2004` ／ 複数は `2001-2004,2031-2038` ／ スポット `508+424` ／ カンマ・スペース・改行区切り）。

### ④ 保存キー

| ページ | ON/OFF | 台番範囲 | 保存先 |
|---|---|---|---|
| 通常・スランプ付き・かぶぱ | `retsu_enabled` | `retsu_ranges_input` | `auto_page_inputs.json`（`_auto_input_keys()` 経由） |
| 記事用 | `art_retsu_enabled` | `art_retsu_ranges_input` | `article_page_inputs.json`（`_article_input_keys()` ＋ `_ART_SHARED_KEYS`） |

**既存の保存・復元システムへ乗せるだけ。新しい保存システム・新しいJSONを作らない。**
店舗／日付スコープは各ページの既存方式に従う。
`_restore_auto_inputs()` / `_save_auto_inputs()` / `_merge_auto_entry()` /
`_save_article_inputs()` / `_restore_article_inputs()` は**本体を変更していない**。

### ⑤ 列画像の中身

**タイトル以外はそのページの並び画像仕様を継承する。**
対象台番／台番順／機種名／ゲーム数／BIG／REG／AT／合算確率／差枚数／差枚補正／
表デザイン／列幅／行高／フォント／背景／罫線／ピンクサマリーバー／スランプ／パネル／液晶／横版。
**列画像専用の新デザインを作らない。**

### ⑥ 正式タイトル

**列画像に「(N台並び)」の台数表記を付けない。**機種名の並べ方は並び画像と同一。

| 機種数 | 列画像のタイトル |
|---|---|
| 1機種 | `スマスロ北斗の拳（列仕掛け）` |
| 2機種 | `A+B（列仕掛け）` |
| 3機種以上 | `A～Z（列仕掛け）`（先頭～末尾。例 `スマスロ北斗の拳～ヴァルヴレイヴ2（列仕掛け）`） |

**括弧は全角 `（列仕掛け）`。**
**通常の並び画像は従来どおり `スマスロ北斗の拳(4台並び)` を維持する。
今回の列追加によって並びタイトルを1文字でも変えてはならない。**

実装は共通ヘルパー **`_col_group_title()`**（新設）と `convert_narabi_pil.py` の
**`machine_label()` / `make_col_title()`**。`make_title()`（並び用）の出力は不変。

### ⑦ ファイル名

タイトルと同じ文字列＋`.jpg`。既存の安全化処理（`_make_safe_fn()` / `make_safe()`）を使う。
同名タイトルが複数あるときは並び画像と同じ規則で `（開始～終了）` を付与する。

```
スマスロ北斗の拳（列仕掛け）.jpg
スマスロ北斗の拳+からくりサーカス2（列仕掛け）.jpg
スマスロ北斗の拳～ヴァルヴレイヴ2（列仕掛け）.jpg
```

並び画像は `(N台並び)` を含むため**ファイル名は衝突しない**。

### ⑧ 列は「表示用の追加画像」＝除外集合へ合流させない（案E1・最重要）

**列画像へ掲載した台番を、他カテゴリの抽出除外に使ってはならない。**
次のいずれへも合流させない:

`narabi_bans` ／ `osusume_bans` ／ その他の優秀台の除外 ／ ジャグラーシリーズ優秀台の除外 ／
⑤オススメの除外 ／ `excellent_list` の除外 ／ 結果テキスト用の集合。

**列のON/OFFによって 全台系・高配分・その他の優秀台・ジャグラーシリーズ優秀台・⑤オススメ・
結果テキスト の内容が変化してはならない。**

### ⑨ 独立 ban_map

列画像は**専用の ban_map** を持つ。用途は**スランプ・パネル・液晶・横版などの既存後処理へ
正しい掲載台番を渡すことだけ**で、**抽出除外には使わない**。

| ページ | 変数 | session_state キー |
|---|---|---|
| 通常系 | `_col_ban_map` | `auto_preview_col_{store}` |
| 記事用 | `_art_col_map` | `art_preview_col_{store}` |

**並び用の `_narabi_ban_map` / `auto_preview_narabi_{store}` / `_art_nb_map` /
`art_preview_narabi_{store}` へ列を混ぜてはならない。**
並び側は「⑦でチェックを外したときにジャグラー／その他へ再振り分けする」処理に使われており、
列を混ぜると**除外していない台をその他へ足してしまう**ため。

列の掲載台番は `_build_col_items()`（新設）が
`(DataFrame, タイトル, ファイル名, 台番リスト)` で返す。抽出・台番順・同名時の
`（開始～終了）` 付与は並び画像とまったく同じ規則。

### ⑩ `convert_narabi_pil.py`

- **`COL_RANGES = []`（既定・空リスト）** と **`COL_SUFFIX = "（列仕掛け）"`** を追加。
- 並びと列を **`_JOBS`（並び → 列 の順）** の同一ループで扱う構造にした。
- `_patch_and_run_narabi(..., col_ranges=None)` を追加。**既定 None＝`COL_RANGES` を
  書き換えないので、従来の並び画像だけが生成される。**
- **非回帰（純粋テストで確認済み）**:
  **列OFF時、生成JPEGがHEAD版と SHA256 完全一致。**
  **並びON＋列ONでも、既存の並び画像のJPEG SHA256 は不変。**

### ⑪ 並びOFF・列ON時の自動検出抑止（巻き戻し禁止）

**`convert_narabi_pil.py` は `RANGES=[]` のとき「3台以上の並びを自動検出」する既存仕様**を持つ。
そのため単純に「並びOFF・列ON」で `RANGES=[]` を渡すと、
**ユーザーが指定していない自動検出の並び画像まで生成される**問題があった（実装中に検出）。

`1410753` では **`elif COL_RANGES:` 分岐を追加**し、
**列専用実行時は自動検出経路へ落とさない**よう修正済み。

```
並びOFF / 列ON → 列画像だけ生成 → 並び画像0枚
```

**この条件を巻き戻してはならない。**`COL_RANGES` が空のときは従来どおり自動検出へ落ちる
（既定動作は不変）。

### ⑫ 結果テキスト・WordPress

- **`generate_report_text()` は変更していない。`nami_list` に列画像を追加しない。**
  **列のON/OFFで結果テキストは変化しない。**
- **`wp_client.py` は変更していない。`payload["nami"]` にも列画像を入れない。**
  列画像はWordPress本文へ自動追加しない。**WordPress対応が必要になったら別Stepとする。**

### ⑬ 実機確認結果（2026-09-01・ローカル・正式HEAD `1410753`）

**渋谷新館 結果ポスト用 ／ 2026/8/31 の確定データ（433台）で実施。**

入力した列の台番範囲: `2001-2004, 2003-2006, 2003-2009`

| 生成された列画像 | 掲載台番 |
|---|---|
| `スマスロ北斗の拳（列仕掛け）.jpg` | 2001〜2004（1機種） |
| `スマスロ北斗の拳+からくりサーカス2（列仕掛け）.jpg` | 2003〜2006（2機種） |
| `スマスロ北斗の拳～ヴァルヴレイヴ2（列仕掛け）.jpg` | 2003〜2009（3機種） |

並び画像 `スマスロ北斗の拳(4台並び).jpg` は従来どおり。
**同一範囲 2001-2004 の並び画像と列画像を並べて比較**し、表・列構成・罫線・色・
ピンクバーの集計値（総差枚 −5,900／平均 −1,475／勝率 0.0%(0/4台)）が**一致**、
**違いはタイトルのみ**であることを確認した。

**A〜D の4パターン（⑦プレビュー・すべてPASS）**

| | 並び | 列 | 枚数 | 内訳 |
|---|---|---|---|---|
| A | ON | OFF | 11 | 自動10＋並び1 |
| B | OFF | ON | 13 | 自動10＋列3（**並び画像0枚**） |
| C | ON | ON | 14 | 自動10＋並び1＋列3 |
| D | OFF | OFF | 10 | 自動10のみ |

**非回帰（列OFF vs 列ON で同一）**

高配分: 喰霊零Re 2/2 ／ ワールドダイスター 2/2 ／ とんスキ 2/2 ／ ネオアイム 14/14 ／
戦コレ6 2/2 ／ マイジャグV 10/10 ／ 東京喰種 11/11
ジャグラーシリーズ優秀台: **18台** ／ その他の優秀台: **41台** ／ 全台系: 南国育ちSPECIAL

⑤オススメはこの確認ケースではOFF。結果テキストへ列を追加していない。
`payload["nami"]` にも列を入れていない。**⑧本番は未実行・WordPress通信0件。**

保存・復元: `retsu_enabled` / `retsu_ranges_input` が当日エントリへ保存され、
**ページ再読込＋データ再取得後にON＋台番範囲が復元**されることを確認した。
記事用（渋谷新館）でも ③並び 内に「列画像を作成する」が表示され、
**採番①〜⑥はずれていない**ことを確認した。

### ⑭ 確認状況の正確な記録（誤記しないこと）

**スランプ・パネル・液晶・横版は「実機確認済み」と書かない。**
今回の実機ケース（渋谷新館 結果ポスト用）はこれらの対象外だったため、**実機では未確認**である。
コードおよび純粋テスト上は、**列専用 ban_map から既存の共通後処理へ入る構造**を確認済み。
スランプ付きページで列画像を使う日が来たら、その運用の中で確認すればよい。

### ⑮ 実機確認中に検出した別案件（列画像とは無関係）

実機確認中、`auto_page_inputs.json` の **`20260831_渋谷新館_20S.xlsx`** で
既存入力5キー（`narabi_ranges_input` / `kojin_z_0_渋谷新館` / `kojin_y_0_渋谷新館` /
`kojin_narabi_range_渋谷新館` / `kojin_narabi_title_渋谷新館`）が空になっているのを検出した。

**今回の列画像実装 `1410753` が原因ではない。**

- `_restore_auto_inputs()` は保存値を無条件に session_state へ入れ、
  **Streamlit は key が既存だと `value=` を無視する**ため、保存値が非空なら③の入力欄に
  表示されたはずである。**実機確認の最初の描画時点で空欄だった**＝
  **その時点で保存値がすでに空**だった。
- 既知の **「⓪取得直後の空描画」＋「7960行の毎レンダー `_save_auto_inputs()`」** による
  空保存問題と同系統の可能性が高い。ただし**実行runを特定できないため原因確定とはしない**。
- 今回の実装では **`_restore_auto_inputs` / `_save_auto_inputs` / `_merge_auto_entry` を
  変更していない**。`retsu` 追加による既存widgetの順序・rerunタイミングも変えていない
  （既存キーの列挙順・JSONのキー順は不変）。

**この空保存問題は列画像とは別案件。今回は修正しない。**

### ⑯ `auto_page_inputs.json` の復旧結果（2026-09-01）

- 実機テスト後、渋谷新館8/31の上記**5キーをHEAD値へ復元**し、テスト用に付いた
  **`retsu_enabled` / `retsu_ranges_input` の2キーを削除**して、
  **当該エントリをHEADと完全一致（89キー・キー順も一致）へ戻した**。
  復元は対象エントリのスライス内だけを限定修正し、`git checkout` / `restore` / `reset` /
  `stash` / `clean` は使っていない（他エントリを巻き添えにしないため）。
- **`20260831_上野本館_20S.xlsx`** は、`retsu_*` を含まないことから
  **旧コード（`45025c9`）のセッションが正規のUI操作で新規作成した**ものと判断できる。
  値の消失は無く、**そのまま保護する**。
- **最終的な `auto_page_inputs.json` の HEAD との差分は
  「`20260831_上野本館_20S.xlsx` の新規エントリ」だけ**である。
  **今後これを勝手に削除しないこと。**

### ⑰ 今後の非回帰確認項目（列画像を改修するとき）

- **並びOFF・列ONで並び画像が勝手に生成されない**（⑪の自動検出抑止）
- 列OFF時の既存並び画像（JPEG一致）／列タイトル／通常の並びタイトル
- **列台番を他カテゴリの除外へ使わない**
- 結果テキスト ／ WordPress ／ スランプ ／ パネル ／ 液晶 ／ 横版 ／ ZIP ／ 保存復元
- 既存の正式仕様: 新小岩 `b530bee` ／ 渋谷新館 `551c9d5` `d477a91` `1bd0e3b` `39b652d` ／
  高田馬場記事用 ／ 秋葉原記事用 ／ ローテ用 ／ 末尾・ジャグラー末尾
- 共通関数（`generate_report_text` / `draw_table_image` / `generate_ranking_image` /
  `run_step1〜3` / `run_auto_pipeline` / `_build_machine_img` 系 / `_build_sue_images` /
  `parse_ranges` / `ranges_to_bans` / 保存復元系）は `1410753` で**1つも変更していない**。
  改修時も同じ原則を守ること。

### ⑱ 別案件として残す問題

結果ポスト用の **「⓪データ取得直後 → 一部入力widgetが空描画 → 毎レンダー保存で既存値が
空保存され得る」** 事象は**別案件**。今回は修正していない。

今後対応する場合は、**いきなり保存ガードを広げない**。必ず
**1) 再現条件の特定 → 2) 対象店舗・日付の実測 → 3) restore/save 順序の確認 →
4) 最小修正案 → 5) 非回帰範囲** の順で調査してから着手すること。

## 全店舗共通：③ 列仕掛け タイトル余白・結果テキスト（2026-09-01 確定・`9ec653e`）

**正式仕様。巻き戻し禁止。**直前の
「## 全店舗共通：③ 列画像（列仕掛け）（2026-09-01 確定・`1410753`）」の**追加修正**であり、
**同節の一部（結果テキストの扱い）を上書きする**。`1410753` 節は削除・書き換えしない。

正式コード commit: **`9ec653ebfb5b5b852f7005e297d7d22b5724397c`**
（`fix: 列仕掛けのタイトル表示と結果テキストを修正`・
**`streamlit_app.py` と `convert_narabi_pil.py` の2ファイルのみ**・+108／−14）。push済み。
**HEAD = origin/main = `9ec653e` を正式基準とする。**

### ⓪ `1410753` から上書きされた点（1つだけ）

| | 旧（`1410753`） | **新（`9ec653e`・正式）** |
|---|---|---|
| 結果テキスト | **列仕掛けは結果テキストへ入れない** | **`👑列仕掛け` として記載する** |

**旧仕様へ巻き戻してはならない。**
これ以外（案E1・独立ban_map・`COL_RANGES`/`COL_SUFFIX`・自動検出抑止・タイトル文字列・
ファイル名・4パターン・保存キー・WordPress非追加・かぶぱ対象外）は
**`1410753` 節のまま有効**である。

---

## A. 列画像タイトルの余白（修正1）

### ① 症状と原因

`1410753` の時点でタイトル文字列自体は `スマスロ北斗の拳（列仕掛け）` で正しかったが、
**Mochiy Pop One は全角括弧も1em幅**で、グリフが em の中央寄りに描かれるため、
`（` の左に約半角の空きが出て、**機種名と `（列仕掛け）` の間に隙間が見えていた**
（FONT_SZ=42 で実測 **22.00px**）。

既存の `（優秀台）` は **2パーツ描画＋`GAP_TITLE = -22`** でこれを詰めていたが、
`（列仕掛け）` は補正のない一括描画へ落ちていたのが原因。

### ② 正式仕様

**列画像の青タイトルバーは、機種名と `（列仕掛け）` の間に不自然な空白を作らない。
`○○（優秀台）` と同じ詰まり方にする。**
1機種・2機種・3機種以上のすべてで同じ。

### ③ 実装（`streamlit_app.py`）

```python
# 青タイトルバーで「機種名」と後置語の間を詰める対象（末尾一致・判定順は固定）。
_TITLE_SUB_PARTS: tuple[str, ...] = ("（優秀台）", "（列仕掛け）")
...
# _build_machine_img() 内
SUB = next((_s for _s in _TITLE_SUB_PARTS if title.endswith(_s)), None)
if SUB:
    ... 既存の2パーツ描画（GAP_TITLE = -22）...
```

- **`GAP_TITLE = -22` と2パーツ描画のロジック自体は変更していない。**
  変えたのは「どのサフィックスを対象にするか」だけ。
- **判定順（`（優秀台）` が先）を入れ替えない。**
- **この2つ以外のサフィックスを足さない**（他画像へ波及する）。
- **`（優秀台）` の画像は旧版と画素完全一致。通常の並び画像タイトルも画素完全一致。**

### ④ 実装（`convert_narabi_pil.py`＝⑧本番）

⑧本番の列画像は subprocess 側で描かれるため、**同じ補正を script にも入れる**
（入れないとプレビューと本番で見た目が食い違う）。

- `COL_SUFFIX` で終わるタイトルのときだけ2パーツ描画（`GAP_TITLE = -22`）。
- **並び画像は従来どおり一括描画**（`COL_SUFFIX` で終わらないため分岐に入らない）。
- フォント縮小ループの幅計算も2パーツ幅で行う（`_title_w()`）。
- **記事用は `NO_BAR=True` でタイトルバーを描かないため対象外。**

### ⑤ 非回帰（純粋テストで確認済み）

- **列OFF：並び画像のJPEGが HEAD版と SHA256 完全一致**
- **列ON：並び画像のJPEGは不変**
- **列画像はタイトルバー領域だけ変化し、表部分（赤線・表・ピンクバー）は画素完全一致**
- `（優秀台）` 画像・通常並びタイトル画像は**画素完全一致**
- 列タイトルの総幅がちょうど **22px 詰まる**

---

## B. 結果テキストの `👑列仕掛け`（修正2）

### ① 正式形式

```
👑列仕掛け
🍡{機種名}
{台番範囲}番台({台数}台並び)→平均{平均差枚}枚
```

見出しの絵文字は店舗別の `e2`（既定 `👑`／新小岩 `🍀` 等）。既存の並び仕掛けと同じ整形。

**実機確認例（渋谷新館 2026/8/31）**

```
👑列仕掛け
🍡スマスロ北斗の拳
2001-2004番台(4台並び)→平均-1,475枚
🍡スマスロ北斗の拳+からくりサーカス2
2003-2006番台(4台並び)→平均-1,550枚
🍡スマスロ北斗の拳～ヴァルヴレイヴ2
2003-2009番台(7台並び)→平均-1,714枚
```

### ② 掲載位置・順序

**`👑並び仕掛け` → `👑列仕掛け` → （末尾・バラエティ等）→ `👑その他の優秀台` の順。**
**列が0件なら `👑列仕掛け` の見出しごと出力しない**（末尾・バラエティと同じ流儀）。
複数の列範囲は**ユーザーが入力した順**（＝列画像の生成順）で並べる。

### ③ 機種名

**結果テキストの機種名へ `（列仕掛け）` を付けない**（見出しで区別する）。
表記は列画像のタイトルと整合させる。

| 機種数 | 表記 |
|---|---|
| 1機種 | `🍡スマスロ北斗の拳` |
| 2機種 | `🍡スマスロ北斗の拳+からくりサーカス2` |
| 3機種以上 | `🍡スマスロ北斗の拳～ヴァルヴレイヴ2` |

### ④ 台数・台番範囲

- **入力した列範囲ごとに1項目。**
- 台数は **「終了台番 − 開始台番 + 1」を使わない**。**実在する掲載台数**を使う
  （`_build_col_items()` が返す DataFrame の行数＝列画像の行数）。
  **欠番があっても画像と結果テキストで台数が食い違わないこと。**
- 台番範囲は**実在する掲載台番**から判定し、書式は既存の並びと同じ
  （連続＝`2001-2012` ／ 1台＝`2001` ／ 飛び地＝`2005+2006+2009`）。

### ⑤ 平均差枚（補正済み・二重補正禁止）

**列仕掛けの平均は、列画像に載っている補正済み差枚を使う。
＝列画像のピンクバーの平均と結果テキストの平均を一致させる。**

- データ源は `_pipeline_calc_d` **適用済み**の `result["df"]`（通常・記事用）／
  `_df_exec_m`（📝）の `差枚` 列。**`_pipeline_calc_d` を再適用しない（二重補正の禁止）。**
- 生差枚と補正済み差枚を混在させない。
- 丸め・符号表記は並びと同じ（`int(round(mean))` ＋ `fmt_diff()`）。
  プラスは `+`、マイナスは `-`。

**実機一致（渋谷新館 8/31）**

| 範囲 | 画像のピンクバー平均 | 結果テキスト |
|---|---|---|
| 2001-2004 | −1,475枚 | `平均-1,475枚` |
| 2003-2006 | −1,550枚 | `平均-1,550枚` |
| 2003-2009 | −1,714枚 | `平均-1,714枚` |

### ⑥ 既存 `👑並び仕掛け` は変更しない（最重要）

**機種名・台番範囲・台数・平均差枚・順序・文言のすべてを変更していない。**
**既存並びの平均差枚は従来どおり補正前（`diff_raw_original`）基準のまま。**
**「並びの平均も列に合わせて補正済みにする」変更は禁止。**
列だけが補正済み基準である（末尾画像で先に確定した `48b1635` と同じ考え方）。

### ⑦ 実装構造

| 要素 | 役割 |
|---|---|
| **`_build_retsu_report_items(df, ranges)`**（新規） | `_build_col_items()` を使い、`nami_list` と同形の dict（`title` / `count` / `avg_diff` / `machine` / `ban_range` / `bans`）を**入力順**で返す。機種名は列タイトルから `（列仕掛け）` を除いたもの |
| **`_nami_like_section(items)`**（新規） | **旧 `nami_section()` の中身をそのまま切り出した**共通整形。並び・列で共用 |
| **`nami_section()`** | `return _nami_like_section(nami_list)` の1行になった。**出力は構造的に不変** |
| **`retsu_section()`**（新規） | `return _nami_like_section(retsu_list or [])` |
| **`generate_report_text(..., retsu_list=None)`** | 任意引数を1つ追加。**`None` / 空なら見出しごと出さず、出力は追加前と完全一致** |

**`run_auto_pipeline()` は変更していない。**列は `result` に入れず、呼び出し側で組み立てる。

### ⑧ 案E1は引き続き正式仕様

**「結果テキストへ出す」≠「除外集合へ混ぜる」。**
列台番を **`narabi_bans` / `osusume_bans` / `nami_list` / `excellent_list` /
その他の優秀台の除外 / ジャグラーシリーズ優秀台の除外** へ**合流させない**。
列のON/OFFで 全台系・高配分・ジャグラーシリーズ優秀台・その他の優秀台・⑤オススメ・
既存の並び仕掛け の抽出結果が変化してはならない。

### ⑨ `result["nami_list"]` は変更しない

**列を `nami_list` へ混ぜない。**列は `retsu_list` の別系統で渡す。既存並びデータを汚染しない。

### ⑩ WordPress

**`wp_client.py` は変更なし。`payload["nami"]` も変更なし。**
`build_payload()` は `result["nami_list"]` を直接読むため、
`generate_report_text()` の変更は **WordPress本文へ波及しない**。
**WordPressへ列仕掛けを追加していない。必要なら別Step。**

### ⑪ かぶぱは対象外

**新宿歌舞伎町かぶぱは `_build_kabupa_result_text()` の別系統**で、今回の `👑列仕掛け` に
含めていない。**勝手に追加しない。**必要なら別Step。

### ⑫ 対象経路

`generate_report_text()` を使う既存4経路
（**通常結果ポスト用 ／ スランプ付き結果ポスト用 ／ 📝記入部分のみ ／ 記事用**）。
**店舗名のハードコードはしない。**`retsu_ok and retsu_ranges` があるときだけ列結果を足す。

---

## C. 実機確認結果（2026-09-01・ローカル・正式HEAD `9ec653e`）

**渋谷新館 結果ポスト用 ／ 2026/8/31 の確定データ（433台）。**
並び＝保存済みの実データ10範囲、列＝`2001-2004, 2003-2006, 2003-2009`。

- 列画像タイトルの隙間が**1機種・2機種・3機種以上のすべてで解消**（拡大目視）。
  `スマスロ北斗の拳（優秀台）` と同じ詰まり方。
- 表・罫線・背景色・ピンクバー・掲載台番・ファイル名は修正前と同一。
- **`ネオアイム(4台並び)` 等の並び画像タイトルは従来どおり**（半角括弧・変化なし）。

**列OFF ⇔ 列ON の非回帰（同一の並び設定で比較）**

| | 列OFF | 列ON |
|---|---|---|
| ⑦プレビュー枚数 | **22枚** | **25枚**（差は列画像3枚だけ） |
| 全台系 | 南国育ちSPECIAL | 同一 |
| 高配分 | 各機種の掲載台数 | 同一 |
| ジャグラーシリーズ優秀台 | **18台** | **18台** |
| その他の優秀台 | **30台** | **30台** |
| バラエティ | 3台 | 3台 |
| ⑤オススメ | このケースではOFF | 同一 |
| 既存の並び仕掛け | — | **完全一致** |

**列OFF時は列画像なし・結果テキストに `👑列仕掛け` なし**で、従来の結果テキストを維持する。

### ⑬ ⑧本番の確認方法（押していない）

**⑧「自動処理を開始」は `_git_auto_push()` による自動commit/pushを伴うため実機では押していない。**
代わりに **`convert_narabi_pil.py` を⑧と同じ書き換えロジックで直接実行**して確認した。

```
旧: スマスロ北斗の拳 （列仕掛け）   ← 隙間あり
新: スマスロ北斗の拳（列仕掛け）    ← 隙間なし
```

同時に **並び画像のJPEGは SHA256 一致**、**列画像の表部分は画素完全一致**、
**並びOFF・列ONで列だけ生成**も確認済み。**WordPress通信は0件。**

### ⑭ 結果テキストの確認方法（誤記しないこと）

**結果テキストは⑧を押さずに確認した。**実機プレビューに表示された**補正済み差枚をそのまま**
`_build_retsu_report_items()` / `generate_report_text()` へ与え、
**列画像のピンクバー平均と結果テキストの平均が一致**することを機械確認した。
**「⑧本番の結果テキストを実機で確認済み」とは書かない。**

### ⑮ 実機確認による JSON の変化（正常保存のみ）

`auto_page_inputs.json` の **`20260831_渋谷新館_20S.xlsx`** に

```
retsu_enabled       = true
retsu_ranges_input  = "2001-2004, 2003-2006, 2003-2009"
```

の**2キーが追加**されただけ。**非空→空 0件／別店舗・別日への流出 0件／
大量の空キー追加 0件。**正常なUI操作による保存であり、**JSONの直接編集はしていない。**

---

## D. 今後の非回帰確認項目（列仕掛けを触るとき）

- **機種名と `（列仕掛け）` の隙間を復活させない**
- **`（優秀台）` の見た目を変えない／通常の並びタイトルを変えない**
- **列画像の表・色・罫線・ピンクバー・ファイル名を変えない**
- **`👑列仕掛け` を消さない**（`1410753` の「結果テキストへ入れない」へ戻さない）
- **列画像の平均と列結果テキストの平均を一致させる**（補正済み・二重補正禁止）
- **既存の `👑並び仕掛け` を変えない**（平均は補正前基準のまま）
- **列台番を他カテゴリの除外へ使わない（案E1）／`nami_list` へ混ぜない**
- **WordPress（`wp_client.py` / `payload["nami"]`）へ勝手に列を入れない**
- **かぶぱ（`_build_kabupa_result_text()`）へ勝手に追加しない**
- 並びOFF・列ONで並び画像が勝手に生成されない（`elif COL_RANGES:` の自動検出抑止）
- 列専用ban_map（`auto_preview_col_{store}` / `art_preview_col_{store}`）・スランプ・
  パネル・液晶・横版・ZIP・保存復元
- 既存の正式仕様：**`1410753`** ／ 新小岩 `b530bee` ／ 渋谷新館 `551c9d5` `d477a91`
  `1bd0e3b` `39b652d` ／ 高田馬場・秋葉原の記事用 ／ ローテ ／ 末尾・ジャグラー末尾
- 共通関数（`run_auto_pipeline` / `run_step1〜3` / `draw_table_image` /
  `generate_ranking_image` / `_build_col_items` / `_col_group_title` /
  `_render_retsu_option` / `_patch_and_run_narabi` / `_build_machine_img_no_bar` /
  `_build_sue_images` / `parse_ranges` / `ranges_to_bans` / 保存復元系 /
  `_build_kabupa_result_text`）は `9ec653e` で**1つも変更していない**。改修時も同じ原則を守る。

## 全店舗共通：③ 列仕掛け 括弧半角化（2026-09-01 確定・`42ea146`）

**正式仕様。巻き戻し禁止。**

| 項目 | 値 |
|---|---|
| **正式基準 HEAD** | **`42ea146ea406bce5bc22efaa7fd41930cfd36fe6`** |
| **実装 commit** | **`c7b4057987ffe2c839ea03943b53815ea21df2f6`**（`fix: 列仕掛けの括弧を半角に統一`・`streamlit_app.py` / `convert_narabi_pil.py` の2ファイルのみ・+73／−45） |

**`42ea146` は `888808c` と `c7b4057` の merge commit**であり、
**アプリコード（`streamlit_app.py` / `convert_narabi_pil.py`）は `c7b4057` と差分0**である。
コード仕様を確認するときは **`c7b4057` を実装 commit として参照**すること。

これは
「## 全店舗共通：③ 列画像（列仕掛け）（2026-09-01 確定・`1410753`）」および
「## 全店舗共通：③ 列仕掛け タイトル余白・結果テキスト（2026-09-01 確定・`9ec653e`）」
に続く追加修正であり、**両節は削除・書き換えしない**。

### ⓪ `9ec653e` から上書きされた点

| | 旧（`1410753` / `9ec653e`） | **新（`c7b4057` / `42ea146`・正式）** |
|---|---|---|
| 画像内タイトル | `スマスロ北斗の拳（列仕掛け）`（**全角**） | **`スマスロ北斗の拳(列仕掛け)`（半角）** |
| ファイル名 | `…（列仕掛け）.jpg` | **`…(列仕掛け).jpg`** |
| 同名重複時 | `…（列仕掛け）（2001～2002）.jpg` | **`…(列仕掛け)(2001～2002).jpg`** |
| タイトル描画 | `（列仕掛け）` も2パーツ描画＋`GAP_TITLE=-22` | **列は一括描画（補正なし）** |

**旧の全角表記へ戻してはならない。**
これ以外（案E1・独立ban_map・`COL_RANGES`・自動検出抑止・保存キー・`👑列仕掛け` の結果テキスト・
WordPress非追加・かぶぱ対象外）は **`1410753` / `9ec653e` のまま有効**である。

### ① 正式表記（列仕掛けの括弧はすべて半角）

```
1機種    : スマスロ北斗の拳(列仕掛け)
2機種    : スマスロ北斗の拳+からくりサーカス2(列仕掛け)
3機種以上: スマスロ北斗の拳～ヴァルヴレイヴ2(列仕掛け)
```

ファイル名も同一（`…(列仕掛け).jpg`）。**画像内タイトルとファイル名は必ず同じ表記**。

### ② 同名重複時のファイル名

```
正式: スマスロ北斗の拳(列仕掛け)(2001～2002).jpg
旧  : スマスロ北斗の拳（列仕掛け）（2001～2002）.jpg   ← 戻さない
```

**範囲内の `～`（U+301C）は今回変更していない。**半角化したのは括弧だけ。
**並び画像の重複名は従来どおり全角** `○○(4台並び)（2001～2004）.jpg`。
`convert_narabi_pil.py` の重複名生成は並びと列で共用のため、
**`title.endswith(COL_SUFFIX)` で列だけを厳密に分岐**する。並び側を半角化してはならない。

### ③ 機種名本体の括弧は変更しない（最重要）

半角化の対象は **「列仕掛けサフィックス」と「列画像の同名重複時に付く台番範囲」だけ**。
**機種名本体に元からある括弧は絶対に変更しない。**

```
正式: マイジャグ(V)(列仕掛け).jpg      ← 機種名の (V) はそのまま
```

**ファイル名全体に対する `replace("（", "(")` / `replace("）", ")")` のような
無差別置換は禁止**（機種名を壊すため）。

### ④ タイトル描画方式

| 対象 | 描画 | GAP_TITLE=-22 |
|---|---|---|
| **列仕掛け `(列仕掛け)`** | **一括描画** | **使わない（対象外）** |
| 優秀台 `（優秀台）` | 2パーツ描画（従来どおり） | **維持** |
| 並び `(4台並び)` | 一括描画（従来どおり） | 使わない |

**`_TITLE_SUB_PARTS` の対象は `("（優秀台）",)` だけ。
`(列仕掛け)` をここへ追加してはならない。**

**「列仕掛けの括弧前に隙間がある」という理由で再び `GAP_TITLE=-22` を列へ適用しない。**
実測（Mochiy Pop One・FONT_SZ=42）:

| | 括弧前のインク間隔 |
|---|---|
| 列 `(列仕掛け)`（半角・一括描画） | **約4px** |
| 並び `(4台並び)` | **約4px** |
| 旧 `（列仕掛け）`（全角・補正なし） | 約27px |

半角括弧は送り幅19px・左サイドベアリング4px、全角括弧は送り幅42px・左サイドベアリング27px。
**半角へ `-22` を掛けると18px重なる**ため、補正は有害である。

### ⑤ `convert_narabi_pil.py`（⑧本番）

- **`COL_SUFFIX = "(列仕掛け)"` が正式値。**
- `9ec653e` で追加した**列タイトル専用の2パーツ描画は撤去済み**。
  列タイトルは並びと同じ一括描画。
- **列OFF時・列ON時とも、既存の並び画像JPEGへ影響を与えてはならない。**

### ⑥ 旧全角ファイルの削除（新規・正式）

括弧半角化により、出力フォルダに旧形式 `…（列仕掛け）.jpg` が残るため、
**⑧本番で新しい列画像を生成する際に、その新名へ1対1対応する旧全角名だけを削除**する。

| 関数 | 役割 |
|---|---|
| **`_col_legacy_fn(new_fn)`** | 新名から旧全角名を**構造的に**組み立てる。末尾の「列サフィックス」と「重複範囲サフィックス」だけを変換。形が一致しなければ `None`（＝何もしない） |
| **`_rm_legacy_col_image(output_dir, new_fn, log)`** | 上記の旧名を既存 **`_rm_stale_image()`** へ渡して削除（連番除去後の**完全一致のみ**・`NN_` 付きと `_side.jpg` も対象） |

呼び出しは**⑧本番の3経路だけ**（通常⑧・📝⑧・記事用⑧）。⑦プレビューでは呼ばない。

**1対1対応の例**

```
新: スマスロ北斗の拳(列仕掛け).jpg              → 旧: スマスロ北斗の拳（列仕掛け）.jpg
新: スマスロ北斗の拳(列仕掛け)(2001～2002).jpg  → 旧: スマスロ北斗の拳（列仕掛け）（2001～2002）.jpg
新: マイジャグ(V)(列仕掛け).jpg                 → 旧: マイジャグ(V)（列仕掛け）.jpg   ← (V) は不変
新: カバネリ海門決戦(4台並び).jpg               → None（並び画像には反応しない）
```

### ⑦ 削除してはいけない画像

旧全角列画像の削除処理で、次を削除してはならない。
**フォルダ全体の掃除・部分一致・曖昧一致は禁止。**

並び画像 ／ 優秀台画像 ／ ジャグラーシリーズ優秀台 ／ その他の優秀台 ／ バラエティ ／
**別の列範囲の画像** ／ 機種名が似ているだけの画像 ／ **機種名本体に括弧を持つ別画像**

一時フォルダでの実テストで、次が**残る**ことを確認済み:

```
マイジャグ(V)(4台並び).jpg
スマスロ北斗の拳(4台並び).jpg
ネオアイム(3台並び)（2121～2123）.jpg     ← 並びの重複名は全角のまま
スマスロ北斗の拳（優秀台）.jpg
ジャグラーシリーズ優秀台.jpg
バラエティ.jpg
ハピジャグV～ウルトラミラジャグ（列仕掛け）.jpg   ← 今回生成しない別の列画像
```

### ⑧ ⑦と⑧のファイル名は必ず一致させる

⑦プレビュー側の **`_build_col_items()`** と ⑧本番側の **`convert_narabi_pil.py`** は、
**必ず同じ列ファイル名を生成する**こと。

```
スマスロ北斗の拳(列仕掛け).jpg
スマスロ北斗の拳+からくりサーカス2(列仕掛け).jpg
スマスロ北斗の拳～ヴァルヴレイヴ2(列仕掛け).jpg
重複時: スマスロ北斗の拳(列仕掛け)(2001～2002).jpg
```

**片側だけ変更することは禁止。**名前がずれると
チェック状態（`_pv_ck_key`）／⑦で外した画像の削除／掲載順（`_order`）／ban_map／
スランプ／パネル／液晶／横版 の紐づけが壊れる。

### ⑨ `👑列仕掛け` の結果テキストは `9ec653e` のまま

今回変更したのは **画像タイトル・ファイル名・列タイトルの描画方法・旧全角ファイル削除**だけ。

```
👑列仕掛け
🍡スマスロ北斗の拳
2001-2004番台(4台並び)→平均-1,475枚
```

機種名へ `(列仕掛け)` は付けない。台番範囲・実在台数・平均差枚（**補正済み差枚基準**）・
入力順・正負記号もすべて `9ec653e` の正式仕様を維持する。
**`generate_report_text` / `nami_section` / `_nami_like_section` / `retsu_section` は
今回の実装で実行コードを変更していない**（バイト一致を確認済み）。

### ⑩ 今回変更していないもの（括弧変更と混同しない）

案E1（列台番を他カテゴリの除外集合へ入れない）／独立ban_map
（`auto_preview_col_{store}` / `art_preview_col_{store}`）／`narabi_bans`・`osusume_bans`・
`nami_list` へ列を混ぜない／`run_auto_pipeline`／既存の並び仕掛け／全台系／高配分／
ジャグラーシリーズ優秀台／その他の優秀台／バラエティ／⑤オススメ／
保存復元キー（`retsu_enabled` / `retsu_ranges_input` / `art_retsu_enabled` /
`art_retsu_ranges_input`）／WordPress `payload["nami"]`／`wp_client.py`／かぶぱの既存仕様。

### ⑪ 実機確認結果（2026-09-01・ローカル・`c7b4057` で起動）

**渋谷新館 結果ポスト用 ／ 2026/8/31 の確定データ（433台）／⑦プレビュー。**

確認した列タイトル（拡大目視）:

```
スマスロ北斗の拳(列仕掛け)
スマスロ北斗の拳+からくりサーカス2(列仕掛け)
スマスロ北斗の拳～ヴァルヴレイヴ2(列仕掛け)
```

すべて半角括弧。ファイル名も同じ半角括弧。旧形式の新規生成は0件。
**「拳」と「(」の間に不自然な隙間なし・重なりもなし**で、同一画面の
`ネオアイム(3台並び)` と同程度の自然な間隔。
`スマスロ北斗の拳（優秀台）` は従来どおりの詰まり方。並び画像も従来どおり
（重複名 `ネオアイム(3台並び)（2121～2123）.jpg` は全角のまま）。

**列OFF ⇔ 列ON の比較（同一の並び設定）**

| | 列OFF | 列ON |
|---|---|---|
| ⑦プレビュー枚数 | 22枚 | 25枚（差は列3枚だけ） |
| 全台系 / 高配分 | 同一 | 同一 |
| ジャグラーシリーズ優秀台 | 18台 | 18台 |
| その他の優秀台 | 30台 | 30台 |
| バラエティ | 3台 | 3台 |
| 既存の並び画像 | 同一 | 同一 |

⓪取得直後に**並びの実データ10範囲・列の台番範囲がいずれも正しく復元**されることを
操作前に確認済み（空保存なし）。JSONの変化は
`20260831_渋谷新館_20S.xlsx` の `retsu_enabled` の値変更のみで、
**非空→空 0件・別日/別店舗への流出0件**。

### ⑫ 純粋テストで確定した非回帰条件（今後も必ず満たすこと）

- **`（優秀台）` 画像は旧版と画素完全一致**
- **並び画像（`(4台並び)` タイトル）は旧版と画素完全一致**
- **列OFF時の並び画像JPEGは HEAD版と SHA256 一致／列ON時も並びJPEGは不変**
- **列画像の表・ピンクバーは変更前と画素一致**（変わるのはタイトルバーだけ）
- **⑦と⑧の列ファイル名が一致**
- **旧全角の列画像だけ安全に削除／無関係画像は削除しない／機種名の括弧は無傷**
- **`👑列仕掛け` の結果テキストは修正前と同一**
- **`wp_client.py` 無変更**／**案E1 維持**

### ⑬ 履歴の注意（誤認しないこと）

- **`411bcf67ad3ac29e686870726430b94286972ba5`（`auto: 画像生成後の設定を保存`）は
  アプリの⑧実行による `auto_page_inputs.json` の自動commit**であり、
  列仕掛けの括弧半角化のコード commit ではない。
- **`888808cc73dd1e6b58bfd3e8e890e56256a844cf`（`Added Dev Container Folder`）は
  `.devcontainer/devcontainer.json` 1ファイルだけの追加**で、列仕掛けコードとは無関係。
- push競合の解消時に `888808c` と `c7b4057` を merge して **`42ea146`** を作成した
  （`--no-ff`・`c7b4057` のcommit IDは書き換えていない）。
  **`42ea146` で列コードが直接変更されたわけではない**（アプリ2ファイルは `c7b4057` と差分0）。

## 機種画像紐づけ：Cloud反映時の注意（2026-09-01 確定・調査のみ／コード変更なし）

**正式な運用ルール。**「ローカル／GitHub には機種画像紐づけがあるのに Cloud の
🖼️ 機種画像紐づけ 一覧に出ない」ときの切り分け手順を定める。**今回コードは変更していない。**

### ① 何が起きたか（戦国恋姫の実例）

- 戦国恋姫の紐づけと画像は **`45025c9`（2026-09-01 14:55:47・`update machine_image_master`）で
  commit・push 済み**で、当時の main にも現在の main にも含まれていた。
  同 commit の変更は次の**5ファイルだけ**である。

  ```
  masters/machine_image_master.xlsx
  assets/machine_images/sengokukoihime_panel.png
  assets/machine_images/sengokukoihime_01.png
  assets/machine_images/sengokukoihime_02.png
  assets/machine_images/sengokukoihime_03.png
  ```

- それにもかかわらず、**Cloud の一覧には当初表示されなかった**。
- **Cloud を Reboot したところ、`🖼️ 機種画像紐づけ` の一覧に戦国恋姫が正常表示された（実機確認済み）**。

  | 簡略名 | 画像グループID | パネル | 液晶 | 状態 |
  |---|---|---|---|---|
  | 戦国恋姫 | `sengokukoihime` | **あり** | **3枚** | **OK** |

- **原因は「未push」ではない。**必要ファイルはすでに push 済みで、
  **Cloud 側が古い状態を保持していたため表示されず、Reboot で最新 main を取り込んで正常反映した**。
  **今後この事象を「未push」と記録しないこと。**

### ② 構造（コードで確認済みの事実）

- 紐づけマスタ：**`masters/machine_image_master.xlsx`**（列 `簡略名` / `画像グループID`）
- 画像：**`assets/machine_images/{画像グループID}_panel.*` / `{画像グループID}_01.*` …**
- 定数：`_MACHINE_IMAGE_MASTER_PATH` / `_MACHINE_IMAGES_DIR`（ともに **`BASE_DIR` 配下＝リポジトリ内**）
- 読み出し：`load_machine_image_master()` → `get_machine_images(簡略名)` →
  `_find_panel_image()` / `_find_screen_images()` → `show_machine_image_page()` が表示
- 外部ストレージ・Secrets・別APIは使わない。**リポジトリ内の実ファイルを直接読む**ため、
  **main へ push したうえで Cloud が新しいコミットを取り込めば反映される**。

### ③ 同じ事象が起きたときの手順（むやみに再登録・再commitしない）

1. **`origin/main` にマスタと画像が存在するか**を先に確認する。
   ```
   git ls-tree -r --name-only origin/main assets/machine_images | Select-String "{画像グループID}"
   git ls-tree -r --name-only origin/main masters
   git log --oneline -- assets/machine_images/{画像グループID}_panel.png
   git merge-base --is-ancestor <その commit> origin/main
   ```
   併せて `git status --porcelain --ignored -- masters assets` が空（未追跡・変更なし）かを見る。
2. **Cloud が最新 main を取り込んでいるか**を確認する。
3. **必要なら Cloud を Reboot する**（Manage app → Reboot）。
   push だけでは反映されないことがある（「⑪ Cloud 実機確認と403の原因」の節と同じ現象）。
4. 1〜3で解決する場合、**画像の再登録・再commit・再pushは不要**。

### ④ ローカルで出ないときは「古いプロセス」を疑う

**`load_machine_image_master()` は `@st.cache_data`（引数なし）**で、
**プロセス生存中はマスタファイルの更新を検知しない**。
そのため、マスタを更新した時刻より**前に起動していた Streamlit セッション**では
新しい紐づけが出ないことがある。
（`append_machine_image_master()` / 紐づけ追加の経路は `load_machine_image_master.clear()` を
呼ぶので、**同じプロセス内で登録した場合は反映される**。）

→ **ローカルで出ないときは、まず Streamlit を再起動して再確認する。**
再登録やマスタの直接編集を先に行わない。

### ⑤ 今回いっさい変更していないもの

`masters/machine_image_master.xlsx` ／ `assets/machine_images/` の画像 ／ `機種名変換.xlsx` ／
`streamlit_app.py` の機種画像関連コード。**戦国恋姫のための追加 commit / push も不要**である
（必要ファイルはすべて `45025c9` で main に入っている）。

なお `機種名変換.xlsx` には**戦国恋姫とは無関係の未コミット差分**（HEAD 1067行 → 現在 1074行・
`Lストファイ6` / `Lリゼロ2` / `L喰霊-零-Re` / `Lうしおととら 白面決戦` / `エウレカ4` 系の**+7行**）が
存在する。**恋姫の行はHEADと現在で同一（3件）**であり、今回の件と混同しないこと。

## 機種名変換：保存時GitHub自動同期（2026-09-01 確定・`fae637e` / `bde3afb`）

**正式仕様。巻き戻し禁止。**対象は**機種名変換ページの保存経路と `機種名変換.xlsx` の1ファイルだけ**。

| 項目 | 値 |
|---|---|
| **正式基準 HEAD** | **`bde3afb`**（= origin/main） |
| `fae637e` | `update: 機種名変換マスタを更新` — **`機種名変換.xlsx` 1ファイルだけ**をcommit / push。未反映だった9行を main へ正式反映 |
| `bde3afb` | `feat: 機種名変換の保存時にGitHubへ自動同期` — **`streamlit_app.py` のみ** |

### ① 今回の発端（原因を誤認しないこと）

西武新宿の機種名変換で

```
Lバイオハザード ヴィレッジ        → バイオヴィレッジ
スマスロ バイオハザード ヴィレッジ → バイオヴィレッジ
```

をローカルで追加したのに、**Cloud では未登録**だった。
調査の結果、**ローカルの `機種名変換.xlsx` には存在するが `origin/main` には存在しない**状態だった。

未commit差分はバイオヴィレッジ2行だけではなく、**次の9行**だった。

| # | 変換前 | 変換後 |
|---|---|---|
| 1 | `Lストファイ6` | スト6 |
| 2 | `Lリゼロ2` | Re：ゼロ2 |
| 3 | `Lパチスロ 喰霊-零-Re` | 喰霊零Re |
| 4 | `L喰霊-零-Re` | 喰霊零Re |
| 5 | `Lうしおととら 白面決戦` | うしおととら |
| 6 | `スマスロ交響詩篇エウレカセブン4 HI-EVOLUTION` | エウレカ4 |
| 7 | `L交響詩篇エウレカセブン4` | エウレカ4 |
| 8 | `Lバイオハザード ヴィレッジ` | バイオヴィレッジ |
| 9 | `スマスロ バイオハザード ヴィレッジ` | バイオヴィレッジ |

この9行は **`fae637e` で `機種名変換.xlsx` 1ファイルだけをcommit / push**し、`origin/main` へ正式反映済み。

**この事象の原因を「Cloud Reboot不足」と誤認しないこと。**
今回の直接原因は
**「ローカルの `機種名変換.xlsx` だけが更新され、GitHub main へ同期されていなかった」**ことである。

### ② Reboot だけでは直らないケース（戦国恋姫と区別する）

**`origin/main` に変換行自体が存在しない場合、Cloud Reboot だけでは絶対に直らない。**
先に `機種名変換.xlsx` を GitHub main へ反映する必要がある。

| 事象 | 状態 | 対処 |
|---|---|---|
| 戦国恋姫の機種画像紐づけ | 必要ファイルは **push済み**、Cloud が古かった | **Cloud Reboot で解決** |
| **今回の機種名変換** | 必要な変換行が **`origin/main` に存在しなかった** | **Reboot だけでは解決しない**（先に main へ反映） |

### ③ `bde3afb` 以前の保存仕様

機種名変換画面の保存経路は3つあったが、いずれも

```
機種名変換.xlsx をローカル保存 → load_name_map.clear() → st.rerun()
```

**だけ**で、`git add` / `commit` / `push` は**一切行っていなかった**。
そのため「ローカルで保存したが手動pushを忘れる」と **Cloud では未登録のまま**になる構造だった。

### ④ 機種画像紐づけとの違い（誤認しないこと）

既存の **`_sync_machine_image_master()` は機種画像紐づけ専用**である。

- 対象：**`masters/machine_image_master.xlsx`** / **`assets/machine_images`**
- **`機種名変換.xlsx` は対象外**だった。

**「以前同期機能を作ったから機種名変換にも効いている」と誤認しないこと。**

### ⑤ `bde3afb` の正式仕様

機種名変換画面の**保存成功後**に **`_sync_name_map()`** を使い、
**`機種名変換.xlsx` だけ**を GitHub main へ自動同期する。

- **対象ファイルは必ず `機種名変換.xlsx` の1ファイルだけ。**
- **`_git_auto_push()` の targets へは追加していない。**
  **画像生成時に `機種名変換.xlsx` を巻き込む仕様ではない。**

### ⑥ 対象となる3保存経路（一部だけ同期する状態へ戻さない）

| # | タブ | ボタン |
|---|---|---|
| ① | 📋マスタ管理 | `💾 マスタを保存` |
| ② | 🔄変換実行 | `📝 N件をマスタに追加` |
| ③ | 🔍pisionチェック | `📝 N件をマスタに追加` |

**正式順序：保存 → `load_name_map.clear()` → `_sync_name_map_ui(...)` → `st.rerun()`**

### ⑦ ローカル同期の正式判定順（最重要）

```
git fetch origin main
  ↓
behind 判定
  ↓
ahead 判定
  ↓
機種名変換.xlsx の差分判定
  ↓
add（1ファイル）
  ↓
パス限定 commit
  ↓
push
```

**差分判定より先に ahead / behind を確認することが正式仕様。**

### ⑧ `behind > 0`（GitHub側が進んでいる）

自動同期を**停止**する。
**`pull` / `merge` / `rebase` / `reset` / `force push` / `autostash` を自動実行してはならない。**
UI には

```
GitHub側に新しいcommitがあります。自動でmerge/rebaseは行いません。手動で確認してください
```

と分かる形で通知する。

### ⑨ `ahead > 0`（未pushのローカルcommitがある）

ローカル HEAD に**未pushのcommitが1件でも存在する場合は自動同期を停止**する。
**そのcommitが機種名変換由来か別案件由来かは問わない。自動push禁止。**

理由：**`git push origin main` はブランチ単位**であり、**別件の未pushcommitまで一緒に反映する危険**があるため。
**「機種名変換のcommitだから自動pushしてよい」という判定は禁止。**
このとき**新しいcommitも作らない**（未pushcommitの積み上がりも防ぐ）。

### ⑩ 正常状態（`ahead == 0` かつ `behind == 0`）

このときだけ `機種名変換.xlsx` の差分を確認する。

| 差分 | 挙動 |
|---|---|
| なし | **`変更なし（同期不要）`**。**commitなし・pushなし** |
| あり | `機種名変換.xlsx` だけを stage → `機種名変換.xlsx` だけを commit → push |

### ⑪ stage / commit の安全条件

自動同期で使用してよいのは **`git add -- 機種名変換.xlsx`** だけ。

- **禁止：`git add .` / `git add -A` / `git commit -a`**
- **commit も pathspec 限定**（`git commit -m ... -- 機種名変換.xlsx`）
- **すでに別ファイルが stage されていても、機種名変換の commit へ含めない。**
- **既存 stage を勝手に解除することも禁止。**

### ⑫ push 拒否時

- **ローカル保存と commit は残す。**
- **rollback しない / reset しない / force push しない。**
- UI には
  **「ローカル保存とcommitは完了したが、GitHubへのpushは未完了」**と明確に表示する。

### ⑬ push拒否後の重要な欠陥と修正（順序を巻き戻さない）

`bde3afb` 実装途中に発見して修正した欠陥。

**旧案の問題**

```
push拒否 → ローカルcommitだけ残る → ワークツリーはclean
        → 次回同期で「変更なし（同期不要）」と誤判定
```

さらにその後保存すると、**未pushcommitが 1件 → 2件 と積み上がる**問題もあった。

**正式修正**：差分確認より**先**に

```
ahead = git rev-list --count origin/main..HEAD
```

を確認し、**`ahead > 0` なら即停止**する。
そのため push 拒否後の次回同期は

```
未pushcommitがあります。安全のため自動同期を停止します
```

となり、**`変更なし（同期不要）` とは絶対に表示しない。**
**この判定順を巻き戻してはならない。**

### ⑭ 分岐状態（`ahead > 0` かつ `behind > 0`）

**自動解決禁止。**分岐状態として停止する。**merge / rebase 等を勝手に行わない。**

### ⑮ Cloud 側

Cloud では **Git コマンドを使用せず、GitHub Contents API 経路**を使う。安全条件：

- **`GITHUB_TOKEN` 必須**
- **現在 SHA を取得**
- **読み込み時 SHA と現在 SHA が不一致なら PUT しない**
- **409 は再送しない**
- **競合は自動解決しない**

**既存の安全仕様（`f3ff59c` の思想）を弱めないこと。**

### ⑯ Cloud Reboot

**GitHub main への自動同期成功と、Streamlit Cloud のコンテナ反映は別問題である。**
**自動同期処理から Cloud Reboot は実行しない。**
同期成功後に Cloud で変換が見えない場合は Reboot を確認する。

### ⑰ 実機確認結果（2026-09-01・ローカル・正式HEAD `bde3afb`）

**西武新宿 / 2026/08/31 確定データ**

```
登録済み: 75 件 ／ 未登録: 0 件
Lバイオハザード ヴィレッジ → バイオヴィレッジ   ← 画面で確認
```

`load_name_map()` でも次の3表記すべてが **`バイオヴィレッジ`** へ変換されることを確認済み。

```
Lバイオハザード ヴィレッジ
スマスロ バイオハザード ヴィレッジ
バイオハザード ヴィレッジ
```

### ⑱ 差分なし同期の実測（本番リポジトリ）

差分なし状態で `_sync_name_map()` を実行した実測結果：

```
戻り値: (True, "変更なし（同期不要）")
HEAD 不変 / origin/main 不変 / git status 不変 / 機種名変換.xlsx 不変
stage 空 / 新commitなし / pushなし
```

**不要な commit を生成しない**ことを確認済み。

### ⑲ 安全性テスト結果（一時リポジトリ・全PASS）

| ケース | 結果 |
|---|---|
| ahead0 / behind0 / 差分なし | **変更なし**（commit・pushなし） |
| ahead0 / behind0 / 差分あり | **Excelだけcommit / push成功** |
| ahead1 | **自動pushしない** |
| behind1 | **自動同期停止** |
| ahead1 / behind1 | **自動解決しない** |
| push拒否 | **local commit残存**（rollbackしない） |
| push拒否後の再同期 | **ahead1で停止／「変更なし」と誤認しない** |
| 他ファイルの未commit差分 | **巻き込まない** |
| 他ファイルstage済み | **機種名変換commitへ含めない／stage状態は保持** |
| 正常push後の再同期 | **変更なし** |

### ⑳ 無変更の既存機能

**`_sync_machine_image_master()` / `_git_auto_push()` / `load_name_map()` / `_save_master_df()` /
`run_auto_pipeline` / `generate_report_text` / 画像生成系 / WordPress系 / 機種画像紐づけ /
ban_map系** はいっさい変更していない。

**特に `_git_auto_push()` の targets へ `機種名変換.xlsx` を追加してはならない。**

### ㉑ 非回帰で守ること（機種名変換周りを変更するとき）

- **3保存経路すべてで同期する**
- **差分判定より前に ahead / behind を判定する**
- **未pushcommitがあれば停止する**
- **GitHub側が進んでいれば停止する**
- **push拒否で rollback しない**
- **次回の ahead 判定で停止する（「変更なし」と誤認しない）**
- **他ファイルの差分・stage を巻き込まない**
- **差分なしなら commit を作らない**
- **Cloud の競合を自動解決しない**

## 全店舗共通：③ 列仕掛け台を優秀台の重複掲載から除外（2026-09-02 確定・`5ef8bde`）

**正式仕様。巻き戻し禁止。**対象は**③「列画像を作成する」で指定した掲載台**だけ。
正式コード commit は **`5ef8bdeda2e3de1f1ab0d405c69214bf406c50a2`**
（`fix: 列仕掛け台を優秀台の重複掲載から除外`・**`streamlit_app.py` の1ファイルのみ**・+46／−8）。push済み。

これは
「## 全店舗共通：③ 列画像（列仕掛け）（2026-09-01 確定・`1410753`）」
「## 全店舗共通：③ 列仕掛け タイトル余白・結果テキスト（2026-09-01 確定・`9ec653e`）」
「## 全店舗共通：③ 列仕掛け 括弧半角化（2026-09-01 確定・`42ea146`）」
に続く追加修正であり、**3節とも削除・書き換えしない**。

### ⓪ `1410753`（案E1）から上書きされた点

| | 旧（`1410753`） | **新（`5ef8bde`・正式）** |
|---|---|---|
| 列台の他カテゴリ除外 | **どのカテゴリの除外集合へも合流させない** | **「その他のジャグラーシリーズ優秀台」「その他の優秀台ピックアップ」の2カテゴリだけ除外集合へ合流させる** |

**上書きされたのはこの1点だけ。**`1410753` / `9ec653e` / `42ea146` のそれ以外
（列画像生成・列専用ban_map・自動検出抑止・`COL_RANGES`／`COL_SUFFIX`・タイトル・
ファイル名・保存キー・`👑列仕掛け` の結果テキスト・WordPress非追加・かぶぱ対象外）は
**すべてそのまま有効**である。

### ① 正式仕様

- **③で「列仕掛け」として指定された掲載台番は、
  「その他のジャグラーシリーズ優秀台」と「その他の優秀台ピックアップ」へ重複掲載しない。**
- **ただし**、列台を除外した結果ジャグラー統合プールが既存条件の**5台以下**になった場合は、
  残った**「列指定ではないジャグラー優秀台」**を既存仕様どおり Step3 の
  「その他の優秀台」へ **overflow させる**。
- **この overflow は並び指定時とまったく同じ既存挙動であり、列だけ特別扱いして止めない。**
- **overflow 先へ移動するのは非列台のみ。列指定台そのものは overflow 先にも掲載しない。**

### ② 原因

**`retsu_ranges` が `run_auto_pipeline()` へ一度も渡されていなかった。**
列画像は pipeline を呼んだ**後**に `_build_col_items(_pv_df, retsu_ranges)` で生成されるため、
Step2／Step3 の除外集合は列台の存在を知り得なかった。
`1410753` の案E1（列台をどの除外集合へも合流させない）がそのまま出た状態である。

### ③ 正式な retsu_bans 経路

```
retsu_ranges（parse_ranges の結果）
  → ranges_to_bans()
  → run_auto_pipeline(retsu_bans=...)
      → run_step2_juggler(retsu_bans=...)
      → run_step3_other(retsu_bans=...)
```

呼び出しは **`run_auto_pipeline` の4か所**（通常⑦プレビュー・通常⑧本番・
記事用⑦プレビュー・記事用⑧本番）で、いずれも
**`retsu_bans=(ranges_to_bans(retsu_ranges) if retsu_ok else set())`**。
**列OFF時は `set()`＝既定＝従来動作。**

### ④ `run_step2_juggler()`

```python
_jug_all_bans = narabi_bans | suebangai_bans | set(retsu_bans)
```

除外位置は既存のまま（`all_for_m` の絞り込み）。高配分判定・台数集計・カテゴリ判定は
**除外前の `all_for_m_orig` 基準**で不変。統合プール（`pool_dfs`）と `jug_excellent_list` は
除外後の `filtered_ex` 基準なので、**画像と結果テキストが一致**する。

### ⑤ `run_step3_other()`

```python
_ex_bans = narabi_bans | suebangai_bans | set(osusume_bans) | set(retsu_bans)
```

`grp_ex` 経由で「その他の優秀台」画像と `excellent_list` の両方へ効く。
`all_plus` 等の判定は除外前の `grp` 基準で不変。

### ⑥ 📝記入部分のみモード

**`_manual_sonota_auto_bans()` に引数 `retsu_ranges=None`（既定＝従来動作）を追加**し、
並びとは**別ループ**で列range由来の台番を `_exc_ban` へ加算する。

```python
for _bl in (narabi_ranges or []):      # 既存（並び）
    _exc_ban |= {int(b) for b in _bl}
for _cl in (retsu_ranges or []):       # 追加（列・列専用）
    _exc_ban |= {int(b) for b in _cl}
```

呼び出しは**4か所**（📝プレビュー・🔄その他を更新・⑧本番2経路）で
`retsu_ranges=(retsu_ranges if retsu_ok else [])`。

**通常・記事用・📝の3経路で列仕掛けの除外仕様を統一する。**
ページ／モードによって列の除外有無が変わる状態へ戻さない。

### ⑦ `narabi_bans` は変更していない（最重要・巻き戻し禁止）

**「列台を優秀台から除外するために `narabi_bans` へ列を混ぜる」実装へ将来戻してはならない。**
理由：

1. `narabi_bans` は `run_step2_juggler` の **`has_narabi_jug`** でも使われ、
   ジャグラー統合画像のタイトル（`ジャグラーシリーズの優秀台` ⇄ `その他のジャグラーシリーズの優秀台`）
   を左右する。列ONだけでタイトルが変わる＝非回帰違反。
2. `narabi_bans` は `generate_recommended_block_image()` / `_rec_off_bans()` にも同名引数で流れ、
   ⑤オススメの抽出へ波及するおそれがある。
3. 案E1の「列は並びから独立」という構造が崩れる。

**必ず列専用の `retsu_bans` / `retsu_ranges` を1本足し、上記④⑤⑥の3か所にだけ合流させること。**

### ⑧ `has_narabi_jug` は変更していない

`has_narabi_jug = bool(narabi_bans) and not df[...]` は**そのまま**。
**列は統合画像のタイトル判定に影響しない。**

### ⑨ 案E1は維持している（無変更）

**本体がバイト単位で無変更**であることを機械確認済み：

`_build_col_items()` ／ `_col_group_title()` ／ `_build_retsu_report_items()` ／
`_patch_and_run_narabi()` ／ `_nami_like_section()` ／ `generate_report_text()` ／
`_narabi_checked_bans()` ／ `_rec_off_bans()` ／ `_collect_published_bans()` ／
`generate_recommended_block_image()` ／ `run_step1_main()` ／ `_build_sue_images()` ／
**`wp_client.py` 全体**。

維持しているもの：列画像生成 ／ 並び画像生成 ／
**列専用ban_map（`auto_preview_col_{store}` / `art_preview_col_{store}`）** ／
`result["nami_list"]`（列を混ぜない）／ `payload["nami"]`（列を混ぜない）／
`👑並び仕掛け` ／ `👑列仕掛け` ／ スランプ ／ パネル ／ 液晶 ／ 横版 ／ 掲載順 ／
保存キー（`retsu_enabled` / `retsu_ranges_input` / `art_retsu_enabled` / `art_retsu_ranges_input`）。

### ⑩ `ranges_to_bans(retsu_ranges)` を使う理由

除外は必ず **`~df["台番"].isin(...)`** の形で使うため、**df に存在しない台番が集合に含まれていても無害**。
したがって

```
ranges_to_bans(retsu_ranges) ∩ 実在台番  ==  _build_col_items() が返す掲載台番の和集合
```

が恒等的に成立する。**並び仕掛けが `ranges_to_bans(narabi_ranges)` をそのまま渡す既存仕様と同形**であり、
「pipeline は自前で df を読むので UI 側で実在台番を先に確定できない」という循環も生じない。
**列だけ別方式（実在台番を先に確定してから渡す）へ変更しない。**

### ⑪ 実機確認結果（2026-09-02・ローカル・正式HEAD `5ef8bde`）

**渋谷新館 結果ポスト用 ／ 2026/9/1 の確定データ（433台）／⑦プレビュー。**
列指定＝**`2229-2237`（ゴージャグ3）**。

| | 列OFF（＝修正前の挙動） | 列ON（修正後） |
|---|---|---|
| ジャグラーシリーズ優秀台 | **12台**（2027 / 2149 / 2154 / 2160 / 2176 / **2229・2230・2231・2232・2233・2234・2235**） | **画像なし**（プール5台以下→overflow） |
| その他の優秀台ピックアップ | **33台** | **38台** |
| `ゴージャグ3(列仕掛け).jpg` | — | **2229〜2237 の9台を正常掲載** |
| プレビュー枚数 | 23枚 | 23枚 |

- **列指定台 2229〜2235 がジャグラー統合から除外された。**
- **その他の優秀台に 2229〜2237 は0台。**
- **2176（ゴージャグ3・列範囲外）など無関係な台は従来どおり掲載。**
- 全台系・高配分・並び・カバネリ等の画像は列OFF/ONで同一。

### ⑫ overflow の正式仕様（誤認しないこと）

列台を除外した結果、ジャグラー統合プールが**既存条件の5台以下**になった場合は、
**残った非列台を既存仕様どおり Step3「その他の優秀台」へ overflow させる。**

2026/9/1 の実データでは

```
2027（ハピジャグV）/ 2149（ファンキー2）/ 2154（ファンキー2）
2160（ファンキー2）/ 2176（ゴージャグ3・列範囲外）
```

の**5台**がこれに該当し、**その他の優秀台が 33台 → 38台**になった。

**これは新規ロジックによる追加ではなく、`run_step2_juggler` の既存 overflow 仕様
（「5台以下なら overflow として Step 3 へ渡す」）による正常挙動である。**
**「その他優秀台が33→38台になったから不具合」と誤認しないこと。**
並び指定時とまったく同じ挙動なので**変更しない**。

**重要：overflow してよいのは列指定ではない残存台だけ。
列指定台そのものを Step3 へ復活させてはならない**
（`run_step3_other` の `_ex_bans` に `retsu_bans` が入っているため構造的に起こらない）。

### ⑬ 純粋テスト結果（HEAD版と現在版を同一データで比較・全PASS）

- **列OFF：HEAD版と戻り値・生成JPEGの SHA256 が完全一致**
- 列ON：ジャグラー統合プール 9→6台／その他 6→4台、いずれも列台だけが減る
- **`added == set()`** ／ **`removed <= retsu_bans`** を
  `jug_pool_bans` / `jug_excellent` / `sonota_excellent` の3集合で assert
- **並び＋列 同時ON**：両方の台が2カテゴリへ載らない／**並びのみは HEAD と一致**
- **欠番を含む range**（例 2001-2012 で 2005 欠番）：実在台だけに影響。
  `ranges_to_bans ∩ 実在 == _build_col_items() の掲載台` を確認
- **高配分 `high_ratio_list` 不変**
- 📝：列OFFは HEAD 一致／列ONで増えたのは列rangeだけ
- ⑨に挙げた12関数＋`wp_client.py` の本体バイト一致

**列OFF時は修正前HEADと完全一致する。**これを壊す変更をしない。

### ⑭ 非回帰（今回いっさい影響を与えていない）

全台系（Step1）／高配分（個別画像・判定は除外前基準）／並び画像／列画像／バラエティ／
末尾・ジャグラー末尾／⑤オススメ機種ピックアップ／記事用②個別画像／結果テキストの
`👑高配分機種`・`👑並び仕掛け`・`👑列仕掛け`／WordPress（`wp_client.py` / `payload["nami"]`）／
新宿歌舞伎町かぶぱ（`_build_kabupa_result_text()`）／スランプ・パネル・液晶・横版・ZIP・保存復元。

### ⑮ ⑧本番・WordPress

**⑧「自動処理を開始」は実行していない**（`auto_page_inputs.json` の既存差分を
`_git_auto_push()` が巻き込むため意図的に未実行）。⑧経路は純粋テストとコード経路の確認まで。
**WordPress 通信は0件**（POST / media upload / draft作成 / update / DELETE いずれも未実施）。

### ⑯ 実装時の既存差分・stash

commit 時点の既存差分

```
M  auto_page_inputs.json
M  wrt_machines.json
?? WordPress連携テスト.jpg
?? wp_test.py
```

は **`5ef8bde` に含めていない**（`git add streamlit_app.py` のみ・pathspec 限定 commit。
`git add .` / `git add -A` / `commit -a` は使用していない）。**stash は4件のまま維持**。

`auto_page_inputs.json` の HEAD との差分は
**`20260901_渋谷新館_20S.xlsx` の新規エントリ1件のみ**で、既存エントリの値変更・消失は0件。
実機確認中に列チェックOFFで一時的に空になった `retsu_ranges_input` は、確認後に**UI上で
`2229-2237` へ戻し**、`retsu_enabled: true` とともに元の値であることを検証済み
（**JSONの直接編集はしていない**）。

### ⑰ 作業順序（CLAUDE.md の既存ルールに従った）

「未コミット状態でアプリを動かしたまま検証しない（`55e7752`）」に従い、
**純粋テスト全PASS → アプリ停止 → `streamlit_app.py` のみ commit → 再起動 → ⑦実機確認**
の順で実施した。stash 窓で旧コードが動く事故を避けるため、**この順序を維持すること。**

### ⑱ 今後の非回帰確認項目（列仕掛けの除外を触るとき）

- **`narabi_bans` へ列を混ぜない**（⑦の3理由）
- **`has_narabi_jug` を変えない**
- **列OFF時は HEAD と完全一致**（生成JPEGの SHA256 まで）
- **`added == set()` / `removed <= retsu_bans`** を機械確認する
- **overflow 仕様を列だけ止めない／列台を overflow 先へ復活させない**
- 通常・記事用・📝の3経路で除外仕様を統一したままにする
- `ranges_to_bans(retsu_ranges)` 方式を維持する
- 案E1（列専用ban_map・`nami_list`・`payload["nami"]`・`👑列仕掛け`）を維持する
- 既存の正式仕様：**`1410753` / `9ec653e` / `42ea146`** ／ 新小岩 `b530bee` ／
  渋谷新館 `551c9d5` `d477a91` `1bd0e3b` `39b652d` ／ 高田馬場・秋葉原の記事用 ／
  ローテ ／ 末尾・ジャグラー末尾

## 全店舗共通：③並び画像の記入枠直下プレビュー廃止（2026-09-02 確定・`bbf9aec`）

**正式仕様。巻き戻し禁止。**対象は**③「並び画像」の台番範囲入力欄の直下に出ていた
個別プレビューボタン**だけ。
正式コード commit は **`bbf9aec8627d4f15b4f191a27fbb52907f63c7a0`**
（`fix: ③並び画像の記入枠直下のプレビューボタンを廃止`・
**`streamlit_app.py` の1ファイルのみ**・+2／−71）。push済み。

### ① 対象（全店舗・全ページ共通）

**店舗名のハードコードはしない。** ③のUIは2箇所の実装で全ページをカバーする。

| 実装 | 対象ページ |
|---|---|
| **`show_auto_page`** | 通常結果ポスト用 ／ スランプ付き結果ポスト用 ／ 新宿歌舞伎町かぶぱ ／ **📝記入部分のみモード** |
| **`show_auto_article_page`** | 記事用 |

③のブロックは各関数に **`if store in STORE_NARABI_SCRIPT:` の1つだけ**で、
`with_slump` や📝モードによる分岐を持たない。したがって
**2箇所を直せば全店舗・全ページで消える。**

### ② 廃止したUI

```
③ 並び画像
  並び画像も生成する
  台番範囲（入力欄）
  並び指定: [...]        ← キャプションは維持
  🔍 プレビュー生成       ← ★これを廃止
  列画像を作成する
  台番範囲（列）
```

廃止した widget key は次の**2つだけ**。

```
narabi_preview_btn        （show_auto_page）
art_narabi_preview_btn    （show_auto_article_page）
```

**この2ボタンは今後復活させない。**

### ③ 今後の正式な確認方法

**並び画像・列画像のプレビュー確認は、③直下ではなく⑦「プレビュー生成」で行う。**
したがって **「③にプレビューが無い」ことは不具合ではない。**
`auto_preview_btn`（⑦）は従来どおり残っている。

### ④ 削除したもの

上記2ボタンの描画と、**そのボタンを押した場合だけ実行されていた専用処理**（③直下ボタン専用経路）。

- Excel再読込（`_read_uploaded_df` / `pd.read_excel`）
- `normalize_df`
- `apply_name_conversion`
- 範囲ごとの `_build_machine_img`（プレビュー画像生成）
- `narabi_previews_{store}` / `art_narabi_previews_{store}` への保存
- `narabi_prev_rt_{store}` / `art_narabi_prev_rt_{store}` への保存
- `narabi_ck_*` / `art_narabi_ck_*` の初期化
- このボタン専用の `st.rerun()`

**共通関数は1つも削除していない。**

### ⑤ 削除していないもの（正式仕様として維持）

「並び画像も生成する」チェック ／ 台番範囲入力欄 ／ `parse_ranges` ／
**`narabi_ranges = _parsed_ranges`** ／ **`narabi_ok = uploaded is not None`** ／
**`並び指定: [...]` キャプション** ／ 列画像UI ／ `retsu_ranges` ／
`_render_retsu_option` ／ `_patch_and_run_narabi` ／ 並び画像生成本体 ／ 列画像生成本体 ／
⑦プレビュー ／ ⑧本番 ／ 保存・復元（`narabi_enabled` / `narabi_ranges_input` /
`art_narabi_*` / `retsu_*` / `art_retsu_*`）／ `👑並び仕掛け` ／ `👑列仕掛け` ／
WordPress関連（`wp_client.py` / `payload["nami"]`）。

### ⑥ 重要：残置コードについて（勝手に整理しない）

③直下ボタンの削除により、**従来の `_previews` 表示・チェックボックス側の分岐など、
到達しなくなった既存コードが一部残っている。今回は意図的に削除していない。**

理由：今回の目的は **「③直下のプレビューボタンを表示しない」という最小変更**であり、
**未使用コードの整理・リファクタ・名称変更は対象外**だから。

**今後、「未使用に見える」という理由だけで勝手に削除しないこと。**
削除が必要なら、**影響範囲を別途調査してユーザーの承認を得てから**行う。

### ⑦ 非回帰実績（2026-09-02・ローカル実機・正式HEAD `bbf9aec`）

**渋谷新館 結果ポスト用 ／ 2026/9/1 の確定データ（433台）で⑦プレビューを実行。**

- **プレビュー23枚を正常生成**
- **並び画像10件を正常生成**（北斗転生2(3台並び) / 東京喰種(3台並び) / ネオアイム(6台並び) ほか）
- **`ゴージャグ3(列仕掛け).jpg` を正常生成**（2229〜2237）
- **その他の優秀台38台**で前回（`5ef8bde` 確認時）と一致
- **`5ef8bde` の列仕掛け台の優秀台重複除外も維持**（2229〜2237 はその他・ジャグラー統合に0台）

UI確認：**通常 ／ スランプ付き（新小岩）／ 記事用（渋谷新館）** のいずれも
③直下にボタンが無く、台番範囲・`並び指定:`・列画像UIは従来どおり表示される。
📝記入モードは `show_auto_page` の同一ブロックのため同じ描画。
⑦`auto_preview_btn`・④末尾`sue_preview_btn`・ジャグラー末尾`jug_sue_preview_btn`・
📝`manual_only_preview_btn`・記事用`art_preview_btn` は**すべて残存**を確認。

### ⑧ 変更範囲

- **`streamlit_app.py` のみ**（**+2 / −71**・**2ハンクだけ**。追加はコメント2行のみ）
- 本体が変わった関数は **`show_auto_page` / `show_auto_article_page` の2つだけ**
- **その他の関数はすべてバイト一致**（`parse_ranges` / `ranges_to_bans` /
  `_patch_and_run_narabi` / `_build_col_items` / `_render_retsu_option` /
  `_build_retsu_report_items` / `generate_report_text` / `run_auto_pipeline` /
  `run_step1_main` / `run_step2_juggler` / `run_step3_other` / `_save_auto_inputs` /
  `_restore_auto_inputs` / `_merge_auto_entry` / `_save_article_inputs` /
  `_restore_article_inputs` / `_auto_input_keys` / `_article_input_keys` /
  `_build_machine_img` / `_narabi_checked_bans` を機械確認）
- **`wp_client.py` 無変更**／`st.button` の key 集合の差は上記2件ちょうど・追加ボタン0件

### ⑨ Git履歴上の注意（誤認しないこと）

`bbf9aec` の親側には、`77aa860`（`docs: 列仕掛け台の優秀台重複除外仕様を記録`）の**後**に
**アプリの自動commit**

```
3f73e38  auto: 画像生成後の設定を保存
```

が存在する。これは `_git_auto_push()` によるもので**手作業のコード変更ではない**。
**`bbf9aec` は `3f73e38` を起点に実装された正式commit**である。
この自動commitにより、それまで未コミットだった `auto_page_inputs.json` の差分が
取り込まれ、作業開始時の既存差分は
`M wrt_machines.json` / `?? WordPress連携テスト.jpg` / `?? wp_test.py` の**3件**だった
（stash は4件のまま）。

### ⑩ 今後の禁止事項

- **`narabi_preview_btn` を復活させない**
- **`art_narabi_preview_btn` を復活させない**
- **③直下に別名のプレビューボタンを新設しない**
- **「以前ここにプレビューがあった」という理由で戻さない**
- **⑦プレビューと③旧プレビューを二重化しない**
- **今回残置したコード（`_previews` 表示・チェックボックス分岐など）を承認なしで整理・削除しない**
- ③の `narabi_ranges` / `narabi_ok` の決定ロジック・保存キー・列画像UIを一緒に変更しない

## 📝記入部分のみモード：その他の優秀台とジャグラーシリーズ優秀台の分離（2026-09-02 確定・`0f0697f`）

**正式仕様。巻き戻し禁止。**対象は**📝「記入部分のみプレビュー」経路（＝pipeline を通らない経路）だけ**。
正式コード commit は **`0f0697f5008b6bb5783ea0c32c5e668ed9c1e361`**
（`feat: 📝記入モードでその他優秀台とジャグラー優秀台を分離`・
**`streamlit_app.py` の1ファイルのみ**・+214／−20）。push済み。

### ① 原因

**`_manual_sonota_auto_extract()` にジャグラー判定が一切なかった。**
除外していたのは ②の機種名（`exc_mac`）と台番集合（`exc_ban`＝②個別ピック・並び・列・末尾・
ジャグラー末尾）だけで、**`cfg["juggler_series"]` を見ていなかった**。

通常⑦/⑧は pipeline が `run_step2_juggler` → `run_step3_other`（冒頭で
`if machine in juggler_series: continue`）とカテゴリを分けているが、
**📝経路は pipeline を通らない**ためこの分離が存在せず、ジャグラーシリーズの台が
「その他の優秀台ピックアップ」へ混入していた。

### ② 正式なカテゴリ分離

📝記入部分のみモードでは次の**3カテゴリを独立**させる。

```
① ②個別画像（全台／優秀台／個別ピック）
② その他の優秀台ピックアップ   … 非ジャグラーのみ
③ ジャグラーシリーズ優秀台     … ジャグラーのみ
```

掲載台番について**常に次を満たす**：

```
individual ∩ other   == ∅
individual ∩ juggler == ∅
other      ∩ juggler == ∅
```

### ③ 新UI「ジャグラーシリーズ優秀台」

既存の「その他の優秀台ピックアップ」自動抽出と**同じ `st.radio` / `horizontal=True`** で統一する。

| 項目 | 値 |
|---|---|
| 文言 | `下記の条件で「ジャグラーシリーズ優秀台」を自動抽出（📝記入部分のみモード）` |
| 選択肢 | **`なし` / `優秀台` / `+1,000枚以上` / `+2,000枚以上`**（`_JUG_AUTO_OPTS`） |
| 通常ページの保存キー | **`jug_extra_auto_{store}`**（`auto_page_inputs.json`） |
| 記事用の保存キー | **`art_jug_extra_auto_{store}`**（`article_page_inputs.json`） |
| スコープ | **Excel（日付）単位**＝`sonota_extra_auto_*` / `art_sonota_extra_auto_*` と完全に同じ |
| 未保存日の初期値 | **「なし」** |
| 不正値 | 選択肢に無い値なら**「なし」へフォールバック**（描画前と読み出し後の二重ガード） |

- **新しいJSON・新しい保存システムは作らない。**
  `_auto_input_keys()` / `_article_input_keys()` へキーを1つ足し、
  `_restore_auto_inputs()` / `_restore_article_inputs()` の**既存「ラジオは有効な選択肢を既定に」分岐**へ
  `startswith(("sonota_extra_auto_", "jug_extra_auto_"))` の形で相乗りするだけ。
- **`_save_auto_inputs()` / `_save_article_inputs()` / `_merge_auto_entry()` は本体無変更。**

### ④ その他の優秀台からジャグラーを外す方法

`_manual_sonota_auto_extract()` に引数 **`exc_series`（既定 空＝従来動作）** を追加し、
マスクへ `& (~df["機種名"].isin(exc_series))` を足す。
呼び出しは **`exc_series=_jug_sonota_exc_series(store, with_slump)`**。

**ジャグラー設定が「なし」でも、ジャグラーを「その他」へ戻さない**
（＝ジャグラー統合を作るページでは、ジャグラー=なし なら**その台はどの画像にも出さない**のが正式）。

### ⑤ ★ 例外：`jug_no_merge_image` のページ（表現を誤らないこと）

**「ジャグラーをその他から常に除外する」とは記録しない。正式には次のとおり。**

> **ジャグラー統合画像を生成するページでは、その他の優秀台からジャグラーを除外する。
> 既存の `jug_no_merge_image` によりジャグラー統合画像を生成しないページでは、
> 台が消失しないよう従来どおりその他へ掲載する。**

理由：`jug_no_merge_image`（現在は **秋葉原のスランプ付き**）は
**ジャグラー統合画像を作らない**既存の正式仕様（`fd42ccf`）なので、ここでその他からも除外すると
**対象台がどの画像にも掲載されず消える**。

実装は新設ヘルパー **`_jug_sonota_exc_series(store, with_slump=False)`**：

```python
if with_slump and store == "秋葉原":
    return set()            # = pipeline へ渡す jug_no_merge_image と同じ判定
return set(get_store_config(store).get("juggler_series", set()))
```

- **`jug_no_merge_image` の意味・判定条件は変更しない**（`jug_no_merge_image=(with_slump and store == "秋葉原")` のまま）。
- **新しい `store == "秋葉原"` 等の別ハードコードを追加しない。**
  ここでの1件は**既存判定の再利用**であり、判定を増やす目的で書き足してはならない。
- 将来 `jug_no_merge_image` の対象が変わるときは、**この関数も同じ判定を参照するように保つ**。

### ⑥ ジャグラー側の抽出（既存判定の再利用のみ）

新設 **`_manual_juggler_auto_extract(df, diff, mode, cfg, exc_ban)`**。

- 対象機種は **`cfg["juggler_series"]`**。**機種名の文字列ハードコードは禁止。**
- `mode == "優秀台"` → 機種ごとに **既存の `_kojin_yushu_filter(機種名, grp, dr, cfg)`** をそのまま使う
- `mode == "+1,000枚以上" / "+2,000枚以上"` → **既存の `_SONOTA_AUTO_THR`** の閾値
- **「優秀台」判定を今回のためにコピー実装しない。**
- 台番昇順（その他の自動抽出と同じ流儀）

### ⑦ ②個別画像との重複除外は **ban 単位**

- ②個別画像へ**実際に掲載された台番だけ**をジャグラー統合から除外する。
  取得元は既存の ban_map（📝プレビュー＝**`_manual_ban_map`** ／ ⑧本番＝**`_m_exec_ban_map_e`** ／
  記事用＝**`_art_ky_bans`**）。**新しい session_state キー・別 ban 管理を作らない。**
- **機種名単位で丸ごと除外してはならない。**
  ②に同じジャグラー機種があっても、**②に掲載されていない優秀台は統合画像へ残す。**
- ②以外の除外（並び・列・末尾・ジャグラー末尾・個別ピック）は既存
  **`_manual_sonota_auto_bans()`** の戻り値をそのまま使う（新しい除外ロジックを作らない）。
- 記事用のジャグラー側は列台（`retsu_ranges`）も除外する（`5ef8bde` と同じ考え方）。
  **記事用「その他」への列除外は従来どおり行わない**（既存挙動を変えない）。

### ⑧ タイトルとファイル名

新設 **`_manual_jug_title(②全台+②優秀台の機種名, cfg)`**。
判定の考え方は `run_step2_juggler` の `has_other_jug_img` と同じ。

| ②個別画像の状態 | 青タイトルバー |
|---|---|
| **ジャグラーシリーズが1機種以上ある** | **`その他のジャグラーシリーズの優秀台`** |
| ジャグラーシリーズが無い（②が空を含む） | **`ジャグラーシリーズの優秀台`**（既存タイトルを維持） |

- **ファイル名は既存どおり `ジャグラーシリーズ優秀台.jpg`。**
  タイトル判定だけを変え、ファイル名・ban_map・後続処理へ影響させない。
- **既存タイトルを全面的に「その他の…」へ置き換えない。**
- 記事用は**青タイトルバーを描かない既存仕様**（`_build_machine_img_no_bar`）を維持するため、
  タイトル文字列は画像へ描かれない。

### ⑨ 結果テキスト（独自フォーマットを作らない）

調査の結果、**通常 pipeline は
`excellent_list = jug_excellent + sonota_excellent` の和集合**（`(name, ban)` で重複除去）で、
**`👑その他の優秀台` にジャグラー統合の台も一緒に載る**構造だった。
`generate_report_text()` に `jug_excellent_list` 引数は無く、**専用のジャグラーセクションは存在しない**。

→ 📝⑧でも **`_m_excel` へ「その他画像の台」＋「ジャグラー画像の台」を
`(name, ban)` 重複除去で和集合**として入れる。

- **画像だけあって結果テキストから消える／二重掲載になる**状態にしない。
- **`generate_report_text()` は本体無変更**。新しいセクション・新しい書式を作らない。

### ⑩ 記事用への適用

記事用📝にも同じカテゴリ分離を適用する。ただし**通常ページの処理をコピーしない**：

- 青タイトルバーなし（`_build_machine_img_no_bar`）・`_art_hq_scale_for` の高解像度判定を維持
- ②実掲載台は **`_art_ky_bans`** から取得
- 保存キーは `art_*` 体系（`art_jug_extra_auto_{store}`）
- ②個別画像・バラエティ・⑤オススメ・保存復元・記事用の既存正式仕様は無変更
- 記事用📝の除外集合は1か所へ集約（②ピック・並び・台番範囲）。**その他側の挙動は従来と同じ**

### ⑪ 通常 pipeline は無変更（最重要）

**`run_auto_pipeline` / `run_step1_main` / `run_step2_juggler` / `run_step3_other` /
`_kojin_yushu_filter` / `filter_recommended_machines` / `generate_report_text` /
`_manual_sonota_auto_bans` / `_build_col_items` / `_build_machine_img` / `_build_sue_images` /
`_save_auto_inputs` / `_save_article_inputs` / `_merge_auto_entry` は本体バイト無変更。**
`wp_client.py` も無変更。**通常⑦/⑧の出力は修正前と一致する。**

変更したのは `_manual_sonota_auto_extract` / `_auto_input_keys` / `_article_input_keys` /
`_restore_auto_inputs` / `_restore_article_inputs` / `show_auto_page` / `show_auto_article_page`。
新設は **`_manual_juggler_auto_extract` / `_manual_jug_title` / `_jug_sonota_exc_series` の3つだけ**。

### ⑫ 純粋テスト結果（A〜T・全PASS）

| # | 内容 |
|---|---|
| A | その他=なし／ジャグラー=なし → 追加画像なし |
| B | その他=+1,000／ジャグラー=なし → **その他にジャグラー0台**・ジャグラーをその他へ戻さない |
| C | その他=なし／ジャグラー=+1,000 → ジャグラー画像だけ生成 |
| D | 両方+1,000 → 2カテゴリ別々・**重複0** |
| E/F | ②非ジャグラーはその他から除外／**②実掲載台だけ**ジャグラー統合から除外。②に2台だけ載ったケースで**残りの優秀台は統合へ残る** |
| G/H | タイトル切替（②にジャグラーあり／なし） |
| I〜L | `優秀台` は **`_kojin_yushu_filter()` の結果と完全一致**・`+1,000` / `+2,000` 正常 |
| M | ②台番テキスト入力あり経路は従来どおり |
| N〜Q | pipeline系16関数バイト一致・`5ef8bde`（列仕掛け除外）維持・👑並び／👑列 不変 |
| R/S | 新JSONなし・未保存日「なし」・キー追加のみ |
| T | `wp_client.py` 無変更・payload 変更なし |

**修正前→修正後（同一データ）**

```
修正前その他: [2001,2002,2003,2006,2011,2014, 3001,3002,3011,3012]
修正後その他: [3001,3002,3011,3012]
新ジャグラー: [2001,2002,2003,2006,2011,2014]
→ 消えたのはジャグラー台だけ／moved ⊆ juggler_after／非ジャグラー台は不変
```

### ⑬ 例外の確認結果（2026-09-02・純粋テスト）

| # | 確認 | 結果 |
|---|---|---|
| 1 | 秋葉原スランプ付き | `_jug_sonota_exc_series("秋葉原", True) == set()` ／ **その他の掲載台番が修正前と完全一致** ／ ジャグラー台がその他に残り**消失しない** |
| 2 | ジャグラー統合を作るページ | その他に**ジャグラー0台**・ジャグラー画像へ正常掲載（その他から消えた台と一致） |
| 3 | `jug_no_merge_image` | 判定式・引数の扱いとも**修正前と同一**（差分は `_jug_sonota_exc_series` の docstring 内の言及1件のみ） |
| 4 | pipeline | `run_auto_pipeline` / `run_step1_main` / `run_step2_juggler` / `run_step3_other` ほか**バイト一致** |

### ⑭ 実機確認結果（2026-09-02・ローカル・正式HEAD `0f0697f`）

**渋谷新館 結果ポスト用 ／ 2026/9/1 の確定データ（433台）／📝記入部分のみプレビュー。**

| 設定 | 結果 |
|---|---|
| ②=バジ絆2天膳・モンハンライズ ／ その他=+1,000 ／ **ジャグラー=なし** | その他画像に**ジャグラー0台**・ジャグラー画像なし |
| ジャグラー=**+1,000枚以上** | **`ジャグラーシリーズの優秀台`** を生成（②にジャグラー無し＝既存タイトル） |
| ②へ**ネオアイム**（ジャグラー）を追加 | ②に `ネオアイム（優秀台）.jpg`／統合の青バーが **`その他のジャグラーシリーズの優秀台`** へ切替／統合の中身は 2143〜2244 で**ネオアイム(2108〜2142)は0台**／その他は東京喰種・北斗転生2・戦国乙女5等で**ジャグラー0台** |

新UIが既存ラジオと同じ見た目・**初期値「なし」**で表示されることも確認した。
**⑧「自動処理を開始」は未実行。WordPress 通信は0件。**

### ⑮ 実機確認で保存された値（コード commit には含めていない）

`auto_page_inputs.json` の `20260901_渋谷新館_20S.xlsx` に
**新キー `jug_extra_auto_渋谷新館 = "+1,000枚以上"`** が保存された（正常な保存動作）。
併せて `kojin_y_0_渋谷新館` / `sonota_extra_auto_渋谷新館` / `narabi_enabled` /
`retsu_enabled` / `suebangai_mode` が UI 操作どおりに変化している。
**`0f0697f` は `streamlit_app.py` 1ファイルのみの commit で、これらは含めていない。**

### ⑯ 今後の禁止事項

- **「ジャグラーをその他から常に除外する」と書き換えない**（⑤の正式表現を維持する）
- **`jug_no_merge_image` の意味・判定条件を変えない**／`fd42ccf` の秋葉原仕様を壊さない
- **`_jug_sonota_exc_series()` 以外に `store == "秋葉原"` 等の判定を足さない**
- **②を機種名単位でジャグラー統合から除外しない**（ban 単位を維持）
- **「優秀台」判定をコピー実装しない**（`_kojin_yushu_filter()` を再利用する）
- **ジャグラー機種名をハードコードしない**（`cfg["juggler_series"]` を使う）
- **ファイル名 `ジャグラーシリーズ優秀台.jpg` を変えない**
- **結果テキストに専用ジャグラーセクションを新設しない**（`excellent_list` の和集合を維持）
- **通常 pipeline（`run_step2_juggler` / `run_step3_other` / `run_auto_pipeline`）を変更しない**
- **新しいJSON・新しい保存システムを作らない**（日付単位・未保存日は「なし」を維持）

## プレビュー掲載チェック後の再配分・結果テキスト同期（2026-09-02 確定・`f719581` / `20c4ac3`）

**正式仕様。巻き戻し禁止。**
正式コード commit は **`f719581`（本体・`streamlit_app.py` のみ・+181／−12）** と
**`20c4ac3`（📝再抽出後の再描画補正・+5）**。
**最終正式HEAD = `20c4ac39129bcd7a09be8388bfce5b29e5b20c0b`。**

直前の「📝記入部分のみモード：その他の優秀台とジャグラーシリーズ優秀台の分離
（2026-09-02 確定・`0f0697f`）」の**厳密化**であり、同節は削除・書き換えしない。

### ① 発端（2つの不具合）

**【不具合①】** 📝記入部分のみプレビューで
②優秀台＝`ハピジャグV` ／ その他＝`+1,000枚以上` ／ ジャグラー＝`優秀台` としてプレビュー生成 →
**②ハピジャグV画像をチェックOFFして「その他を更新」しても、ハピジャグVの優秀台が
「ジャグラーシリーズ優秀台」へ戻らなかった。**

**【不具合②】** 通常⑦プレビューで高配分画像等をチェックOFF → 「その他を更新」 →
**画像上はその優秀台が「その他の優秀台」へ再配分されるのに、結果テキストは
チェックOFF前のカテゴリに残っていた**（画像の最終掲載状態と結果テキストが不一致）。

### ② 不具合①の原因（4点）

1. **`0f0697f` の除外集合が②画像生成時点の
   `_manual_ban_map` / `_m_exec_ban_map_e` / `_art_ky_bans` を使い、
   現在のプレビューチェック状態を見ていなかった。**
   そのため②画像をチェックOFFしてもその台番が除外集合へ残っていた。
2. **📝の「その他を更新」は pipeline 結果 `_pv_df` 前提の既存ブロックでは動かず、
   既存 `_manual_son_upd` は `with_slump` 限定**だった。
   渋谷新館等（`with_slump=False`）では②OFF後の再振り分けが1行も走らなかった。
3. **ジャグラー統合タイトルが「②に記入された機種名」基準**で、
   現在チェックONの②画像を見ていなかった。
4. **通常⑦の既存「②優秀台OFF→ジャグラー戻し」が `diff >= 1000` 固定**で、
   新しい `なし` / `優秀台` / `+1,000枚以上` / `+2,000枚以上` の設定と不整合だった。

### ③ ★最重要：②除外集合の正式な正本

**②個別画像の除外集合の正本は、**

- 「②入力欄に記入されている機種」でもなく、
- 「一度②画像として生成された台」でもなく、
- **「現在プレビューでチェックONになっている②画像の実掲載台番」**である。

```
②ハピジャグV ON  → 実掲載台 2001 / 2002 / 2003 を除外
②ハピジャグV OFF → 除外集合から解除
                  → 現在のジャグラー抽出条件を満たせばジャグラー統合へ戻る
```

**機種名単位で除外しない。ban 単位で判定する。**
**②画像を一度生成した ≠ その台を永久に除外。**

### ④ `_manual_kojin_on()`（新設・正式ヘルパー）

`_manual_kojin_on(df, diff, store, excel_name, previews, kojin_zentai_machines,
kojin_yushu_machines, cfg, force_1k=False) -> (set[int], list[str])`

役割：

- **現在チェックONの②画像を判定**（`_pv_ck_key()` を使う）
- **その画像の実掲載台番を取得**（ban 単位）
- **現在掲載中の②機種名を取得**（タイトル判定用）
- 抽出は既存 **`_resolve_kojin_name()` / `_kojin_yushu_filter()`** を再利用

**新しい優秀台判定は作っていない。**
今後「現在掲載ONの②」を解決するときは**この関数を正式ヘルパーとして使う**。

### ⑤ ジャグラーへの再配分（📝）

```
②画像OFF
  → 現在ONの②だけで除外ban を再計算（_manual_kojin_on）
  → _manual_juggler_auto_extract()
  → 現在のジャグラー設定で再抽出
```

設定 **`なし` / `優秀台` / `+1,000枚以上` / `+2,000枚以上`** に正しく連動する。

- `優秀台` → **`_kojin_yushu_filter()` の正式判定を再利用**
- `+1,000枚以上` / `+2,000枚以上` → **既存 `_SONOTA_AUTO_THR` の閾値を再利用**
- **新しい独自判定は禁止。**

### ⑥ ジャグラー＝「なし」のとき

**②ジャグラー画像をチェックOFFしても、ジャグラー設定が「なし」ならジャグラー統合画像へ戻さない。**
**さらに、ジャグラー統合画像を生成する通常ページではその台を勝手に「その他」へも戻さない。**
`b600ad3` の「その他／ジャグラーのカテゴリ分離」を維持する。

### ⑦ タイトル判定も「現在チェックONの②画像」が正本

| 現在ONの②画像 | 青タイトルバー |
|---|---|
| ジャグラーシリーズ機種**あり** | **`その他のジャグラーシリーズの優秀台`** |
| ジャグラーシリーズ機種**なし** | **`ジャグラーシリーズの優秀台`** |

```
②ハピジャグVを一度生成 → チェックOFF → 他に②ジャグラー画像のONなし
  → タイトルは「ジャグラーシリーズの優秀台」へ戻る
```

**入力欄にハピジャグVが残っていても「その他の～」にはしない。**
実装は `_manual_jug_title(_kon_macs_m / _kon_macs_e, cfg)`。
**②入力欄（`kojin_zentai_machines + kojin_yushu_machines`）基準へ戻さない。**

### ⑧ 📝専用の再抽出（既存 `_manual_son_upd` は無変更）

- **既存 `_manual_son_upd` の意味・条件・用途は変更していない**
  （`fd42ccf` / `ce2fafc` の既存店舗条件を維持）。
- 今回、**📝専用の新しい判定／再抽出経路 `_manual_cat_upd`** を🔄「その他を更新」へ追加した
  （条件は「📝プレビュー由来」かつ **`not _manual_son_upd`**）。
- **通常 pipeline 用の既存「その他を更新」と、📝記入部分のみ用の再抽出を
  無理に一本化していない。**
- `20c4ac3`: 📝経路（`_pv_df` なし）は後段の `if _updated:` に載らないため、
  **再抽出が成功したときだけ `st.rerun()`** する。
  **`st.rerun()` は `try` の外に置く**（`except Exception` が RerunException を
  飲み込むと再描画されないため）。この配置を変えない。

### ⑨ 通常⑦のジャグラー戻し（設定連動）

**②優秀台OFF→ジャグラー統合へ戻す既存経路そのものは維持。**
ただし **`diff >= 1000` 固定をやめ**、現在選択されている「ジャグラーシリーズ優秀台」の
設定へ連動させる（抽出は `_manual_juggler_auto_extract()` を再利用）。

| 設定 | 戻る台 |
|---|---|
| `優秀台` | **+1,000枚未満でも `_kojin_yushu_filter()` 条件を満たせば戻る** |
| `+2,000枚以上` | +2,000枚以上だけ |
| `なし` | **戻らない**（その他へも回さない） |

**`_mymask = _mydiff >= 1000` の固定へ戻さない。**

### ⑩ 不具合②：結果テキストの同期方式

**`generate_report_text()` 本体は変更していない**（バイト一致）。

正式方式：

- 既存 pipeline の **`high_ratio_list` / `zen_dai_list` をそのまま正本として使う**
- **現在チェックOFFになっている高配分／全台系画像に対応する項目だけを、
  呼び出し直前に除外する**（`_aprev_hr_key` / `_aprev_zen_key` の既存マップから
  OFFのプレビュー名 → 機種名を逆引き）
- **全面的な再構築はしない。画像ファイル名を解析して結果テキストを作り直さない。**

### ⑪ 高配分OFF

| 状態 | 結果テキスト |
|---|---|
| 高配分画像 **ON** | `👑高配分機種` に掲載 |
| 高配分画像 **OFF** | **その機種を `👑高配分機種` から除外** |

その画像で独占していた優秀台が既存の「その他を更新」処理で「その他の優秀台」へ
再配分された場合、結果テキストでも **`👑その他の優秀台`** へ入る。
**画像と結果テキストの最終状態を揃える。**

### ⑫ 全台系OFF

全台系も高配分と同じ考え方。
**全台系画像OFF → `👑全台系濃厚機種` から除外。**
その他条件を満たす台が既存再配分でその他へ移った場合は、結果テキストもその最終状態へ合わせる。

### ⑬ チェックONの項目は不変

**`high_ratio_list` / `zen_dai_list` をゼロから作り直してはいない。**
チェックONの項目については **内容・順序・表記を従来どおり維持**し、
**OFFになった項目だけ除外する**。
`ce2fafc` の「既存リストを不用意に全面置換しない」思想を維持する。

### ⑭ `excellent_list`

既存 `ce2fafc` の
**「その他への追加は `_son_excel_add` 等で既存 `excellent_list` へ追加する」**構造は維持。
**`generate_report_text()` への独自フォーマット追加なし。**
`👑その他の優秀台` は既存 `excellent_list` の書式をそのまま使う。

### ⑮ 秋葉原スランプ付き（例外の維持）

`b600ad3` の正式例外を維持する。
**`_jug_sonota_exc_series()` と `jug_no_merge_image` の意味・判定条件は無変更。**
ジャグラー統合画像を作らない既存ページでは、**台が消失しないよう従来どおりその他へ掲載**する。
今回の修正で **`store == "秋葉原"` 等の新しい別判定は増やしていない。**

### ⑯ `5ef8bde` / `0f0697f` / `b600ad3` の維持（非回帰）

- **`5ef8bde`**: 列仕掛け台の優秀台重複除外
- **`0f0697f`**: 📝で「②個別画像」「その他の優秀台」「ジャグラーシリーズ優秀台」を3カテゴリ分離
- **`b600ad3`**: 上記正式仕様の記録＋秋葉原例外

今回の変更は **「現在ONの②だけを除外対象にする」よう厳密化したもの**で、
**3カテゴリ分離の思想は変更していない。**

### ⑰ 実機確認（2026-09-02・ローカル・正式HEAD `20c4ac3`）

**渋谷新館 ／ 2026/9/1 ／ ②優秀台＝ハピジャグV ／ その他＝+1,000枚以上 ／ ジャグラー＝優秀台**

初期状態：

- `ハピジャグV（優秀台）` → **2027**
- ジャグラー統合タイトル → **`その他のジャグラーシリーズの優秀台`**

②ハピジャグV画像を **OFF** → 「その他を更新」（**🔄 1回**）：

- **2027 ハピジャグV +800枚 がジャグラー統合へ復帰**
  （**+1,000枚未満でも「優秀台」条件を満たすため正常**）
- タイトルが **`ジャグラーシリーズの優秀台`** へ戻った
- **その他画像にはジャグラー0台のまま**

### ⑱ 結果テキストの確認範囲（誤記しないこと）

**高配分／全台系OFF後の結果テキスト修正は「純粋テストで確認済み」である。**
⑧「自動処理を開始」を押していないため、**実機での結果テキスト生成確認は未実施**。
**「実機確認済み」と記録しない。**

（純粋テストでは、全ON時に元と完全一致／高配分OFFで `👑高配分機種` から消える／
全台系OFFで `👑全台系濃厚機種` から消える／ONの項目は内容・順序が不変、を確認済み。）

### ⑲ 記事用の境界（重要）

- **`show_auto_article_page` はバイト一致で無変更。**
- 記事用⑦/⑧について、**今回の「②チェックOFF後の📝再抽出」は追加していない。**
- 記事用📝には通常ページと同じ「その他を更新」経路が存在しないため、**今回の対象外**。
- したがって **「記事用も今回完全対応済み」とは記録しない。**
- 将来記事用へ同じ仕様を適用する場合は、**別途調査・承認が必要。**

### ⑳ 変更範囲

| 項目 | 内容 |
|---|---|
| `f719581` | 本体 ／ `streamlit_app.py` ／ **+181 / −12** |
| `20c4ac3` | 📝再抽出後の再描画補正 ／ **+5** |
| 最終正式HEAD | **`20c4ac39129bcd7a09be8388bfce5b29e5b20c0b`** |
| 変更した既存関数 | **`show_auto_page` のみ** |
| 新規関数 | **`_manual_kojin_on()`** |
| その他 | 上記以外の関数は**バイト一致**（`generate_report_text` / `run_auto_pipeline` / `run_step1_main` / `run_step2_juggler` / `run_step3_other` / `_kojin_yushu_filter` / `_manual_sonota_auto_bans` / `_manual_sonota_auto_extract` / `_manual_juggler_auto_extract` / `_manual_jug_title` / `_jug_sonota_exc_series` / `_build_col_items` / `_build_sue_images` / `_save_auto_inputs` / `_restore_auto_inputs` / `show_auto_article_page` ほか）。`wp_client.py` も無変更 |

### ㉑ 今後の禁止事項

- **②除外を「記入機種名」基準へ戻さない**
- **一度生成した②画像を永久ban扱いしない**
- **チェックOFFの②画像を除外集合へ残さない**
- **タイトルを②入力欄基準へ戻さない**
- **通常⑦のジャグラー戻しを `diff >= 1000` 固定へ戻さない**
- **`_manual_son_upd` の既存条件を今回仕様のために広げない**
- **`high_ratio_list` / `zen_dai_list` を全面再構築しない**
- **チェックON項目の順序を変えない**
- **`generate_report_text()` に独自フォーマットを追加しない**
- **記事用も対応済みと誤認しない**
- `st.rerun()` を `try` の内側へ移さない（`20c4ac3`）
- `_jug_sonota_exc_series()` / `jug_no_merge_image` を変更しない（秋葉原例外）

## 📝⑧：②チェックOFFの生成前スキップと結果テキスト同期（2026-09-02 確定・`2860b2f`）

**正式仕様。巻き戻し禁止。**
直前の「プレビュー掲載チェック後の再配分・結果テキスト同期（2026-09-02 確定・`f719581` / `20c4ac3`）」
の**追加修正**であり、同節および `0f0697f` / `b600ad3` / `ce2fafc` / `fd42ccf` の各節は
削除・書き換えしない。

### ① 今回の不具合

📝記入部分のみモードで

```
②個別画像の優秀台へ ハピジャグV を指定
  → 📝記入部分のみプレビューを生成
  → プレビューで「ハピジャグV（優秀台）」のチェックをOFF
  → 「その他を更新」
  → ジャグラーシリーズ優秀台画像へハピジャグVが正常に復帰
  → ⑧実行
```

とした場合、**画像上では②ハピジャグVがOFFになっているにもかかわらず**、結果テキストの

```
👑高配分機種
🎖️ハピジャグV(4/7台)→平均+264枚
```

**が残っていた。** これを今回修正した。

### ② 直接原因

📝⑧は **pipeline の `high_ratio_list` / `zen_dai_list` をそのまま使わず**、
②優秀台の生成時に **`_m_high`**、②全台の生成時に **`_m_zen`** を**自前で構築**している。

ところが従来は、②画像のチェックOFFを**生成前に見る処理が `_manual_son_upd_e` の対象経路に
限定**されていた。そのため**西武新宿のような `with_slump=False` の📝ページ**では

```
OFFになっている②画像でも一度生成
  → _m_high.append() / _m_zen.append()
  → 後段で画像ファイルだけ削除
```

という順序になり、**「最終画像には存在しない②画像」が結果テキスト用の
`_m_high` / `_m_zen` には残る**という不整合が発生していた。

### ③ 正式修正：②OFFは「生成後削除」ではなく「生成前スキップ」

```python
_manual_cat_off_e = _manual_son_upd_e or _is_manual_mode
```

の考え方により、**📝モードでは全店舗で、現在チェックOFFになっている②画像を生成前にスキップする。**

| OFF対象 | 正式挙動 |
|---|---|
| **②優秀台** | ②画像を生成しない ／ `_m_exec_ban_map_e` に入れない ／ **`_m_high.append()` に到達しない** |
| **②全台** | ②画像を生成しない ／ `_m_exec_ban_map_e` に入れない ／ **`_m_zen.append()` に到達しない** |

**重要：「一度生成してから後段でファイルだけ消す」実装へ戻してはならない。**
結果テキスト用カテゴリも含めて整合させるため、**📝⑧では生成前スキップが正本**。

### ④ `_manual_son_upd_e` は広げていない

- 既存 **`_manual_son_upd_e` の定義・意味・店舗条件は変更していない**
  （`_manual_son_upd_e = (with_slump and store != "新宿歌舞伎町")` のまま）。
- **`_m_son_extra_bans` へ台を回す既存分岐も `_manual_son_upd_e` 限定のまま維持**している。

これは `ce2fafc` / `fd42ccf` の既存仕様を守り、**今回の📝専用再抽出経路と
従来の「その他へ回す」経路を二重適用しない**ため。

**今後、「📝でも必要だから」という理由だけで `_manual_son_upd_e` 自体の適用範囲を
全店舗へ広げてはならない。**

### ⑤ 結果テキスト直前の保険フィルタ

生成前スキップを正本とするが、結果テキスト生成直前にも保険として
**`_m_high_rt` / `_m_zen_rt`** を作り、**最終掲載ONではない②画像に対応する項目だけを
`_m_high` / `_m_zen` から除外**している。

**これは「除外だけ」である。** 次を禁止する：

- リストの全面再構築
- 独自集計
- 別判定での再抽出
- ON項目の並べ替え
- ON項目の内容変更
- ON項目の表記変更

**ON項目については、既存の内容・順序・表記をそのまま維持する。**

### ⑥ ジャグラー画像への復帰との関係

②でジャグラー機種を指定していた場合でも、

```
その②画像をチェックOFF → その他を更新 → ジャグラー設定に該当
```

なら、**「現在ONの②画像の実掲載台番だけを除外正本とする」`f719581` / `20c4ac3` の
正式仕様に従い、OFFになった台はジャグラーシリーズ優秀台画像へ再び候補として戻る。**

今回の実機例（②優秀台＝ハピジャグV ／ ジャグラー＝優秀台）では、②ハピジャグVをOFFした後、
**ハピジャグVの対象台がジャグラーシリーズ優秀台画像へ正常復帰した。この挙動は維持する。**

### ⑦ ★重要：画像の「優秀台」と結果テキストの閾値は別

**ジャグラーシリーズ優秀台「画像」の抽出条件と、結果テキスト `👑その他の優秀台` の
掲載条件は別物。**

- ジャグラー設定が **「優秀台」** の場合、既存 **`_kojin_yushu_filter()`** を満たせば
  **+2,000枚未満でもジャグラー画像へ掲載されてよい**
- 一方、結果テキストの **`👑その他の優秀台` は既存の `excellent_min_diff=2000` を維持する**

つまり

```
ジャグラー画像には載る  ≠  必ず結果テキストの👑その他の優秀台にも載る
```

である。**ここを将来一本化しないこと。**

### ⑧ C-3 は不採用

調査時に検討した **「`generate_report_text()` へ『閾値を無視して必ず excellent に載せる台』の
ような任意引数を追加する案（C-3）」は正式に不採用。追加してはならない。**

- **`generate_report_text()` 本体は今回変更していない**
- **`excellent_min_diff` も変更していない**
- **ジャグラー設定に合わせて `excellent_min_diff` を下げる実装も禁止**

### ⑨ 結果テキストの正式基準（実データ）

西武新宿 8/31 の実機確認では、ハピジャグVの対象台として

```
3086番台 → +2,000枚
3083番台 → +1,100枚
```

が存在した。②ハピジャグVをOFFし、ジャグラー優秀台画像へ復帰した後の結果テキストでは

| 台 | 結果テキスト |
|---|---|
| **3086番台 +2,000枚** | **`👑その他の優秀台` へ掲載** |
| **3083番台 +1,100枚** | **`👑その他の優秀台` へ非掲載** |

**これが正式な期待結果。+1,100枚を掲載しないことは不具合ではない**
（`excellent_min_diff=2000` が正常に維持されている証拠）。

### ⑩ `👑高配分機種` ・`👑全台系濃厚機種` の正式仕様

📝⑧で②画像をOFFした場合：

- **②優秀台OFF → `_m_high` に残さない → `👑高配分機種` に残さない**
- **②全台OFF → `_m_zen` に残さない → `👑全台系濃厚機種` に残さない**

**「画像はOFFなのに結果テキストには残る」状態を再発させてはならない。**

### ⑪ 実機確認（2026-09-02・ローカル）

**店舗：西武新宿 ／ 日付：2026/8/31**

設定：②優秀台＝`ハピジャグV` ／ その他＝`+1,000枚以上` ／ ジャグラー＝`優秀台`

操作：📝記入部分のみプレビュー → ②ハピジャグV **OFF** → 🔄その他を更新 → **⑧実行**

生成画像：

```
01_スマスロ北斗の拳（優秀台）.jpg
02_ジャグラーシリーズ優秀台.jpg
03_マイジャグV(列仕掛け).jpg
02_その他の優秀台ピックアップ.jpg
```

**`ハピジャグV（優秀台）.jpg` は生成されていない。**
ジャグラー画像タイトルは **`ジャグラーシリーズの優秀台`** へ正常復帰。

結果テキスト：

```
👑高配分機種
（なし）                                 ← 修正前に残っていたハピジャグVが消えた

👑その他の優秀台
…
📍【3086番台】ハピジャグV→+2,000枚      ← 掲載
（+1,100枚の3083番台は非掲載）
```

**WordPress通信0件。**

### ⑫ 非回帰（今回変更していない）

**`generate_report_text()` 本体 ／ `excellent_min_diff` ／ `run_auto_pipeline()` ／
`run_step1_main()` ／ `run_step2_juggler()` ／ `run_step3_other()` ／
`_kojin_yushu_filter()` ／ `_manual_kojin_on()` ／ `_manual_juggler_auto_extract()` ／
`_manual_sonota_auto_extract()` ／ `_manual_jug_title()` ／ `_jug_sonota_exc_series()` ／
`_build_col_items()` ／ `_build_sue_images()` ／ `show_auto_article_page()` ／
`_build_kabupa_result_text()` ／ `wp_client.py`**

また次の正式仕様を維持している：

- **`5ef8bde`** 列仕掛け除外
- **`0f0697f` / `b600ad3`** 3カテゴリ分離
- **`f719581` / `20c4ac3`** 現在ONの②基準
- **`ce2fafc` / `fd42ccf`** 既存その他再配分
- **秋葉原 `jug_no_merge_image` 例外**

**全ON時は修正前と完全一致。**

### ⑬ 記事用は今回の対象外

**`show_auto_article_page` は今回変更していない。**
**今回の修正を理由に、記事用へ同じ処理を推測でコピーしてはならない。**
記事用へ適用する必要が出た場合は
**1) 現在の処理経路を調査 → 2) 影響範囲を報告 → 3) 最小修正案を提示 → 4) 承認後に実装** とする。

### ⑭ Git履歴（誤認しないこと）

正式コード修正：

```
2860b2f  fix: 📝⑧でチェックOFFの②画像を生成前にスキップする
         変更対象: streamlit_app.py のみ ／ +37 / −3
         変更関数: show_auto_page のみ ／ 新規関数: なし
```

その後、**実機⑧確認によりアプリの `_git_auto_push()` が設定保存を自動commit/push**し、

```
9c1d866  auto: 画像生成後の設定を保存
```

が作成された。したがって現在の正式HEADは
**`9c1d86602c18d4d25369ea75a615cca3265d4907`** であり、**`2860b2f` はその祖先**。
**`2860b2f` が消えた・上書きされたと誤認しないこと。**

### ⑮ 今後の禁止事項

1. **📝⑧でOFFの②画像を一度生成してから削除する方式へ戻さない**
2. **OFFの②優秀台を `_m_high` に残さない**
3. **OFFの②全台を `_m_zen` に残さない**
4. **`_manual_son_upd_e` の対象範囲を今回の修正を理由に広げない**
5. **`_m_son_extra_bans` の既存条件を勝手に広げない**
6. **`generate_report_text()` に C-3 相当の強制掲載引数を追加しない**
7. **`excellent_min_diff=2000` をジャグラー設定に連動させない**
8. **「ジャグラー画像の優秀台」と「`👑その他の優秀台` の+2,000枚基準」を一本化しない**
9. **結果テキスト用 `_m_high` / `_m_zen` を全面再構築しない**
10. **現在ONの項目の内容・順序・表記を変更しない**
11. **`f719581` / `20c4ac3` の「現在チェックONの②画像の実掲載台番が除外正本」を巻き戻さない**
12. **秋葉原 `jug_no_merge_image` 例外を壊さない**
13. **記事用へ推測でコピーしない**
14. **今回無関係な未使用コード整理・リファクタリングをしない**

## 青タイトルバー：長いタイトルのみ自動縮小（2026-09-02 確定・`2959b99`）

**正式仕様。巻き戻し禁止。**
正式コード commit は **`2959b99c35844ab98cf1aaca21a48876d83be84c`**
（`fix: 青タイトルバーの長いタイトルを自動縮小する`）。
**正式HEAD = `2959b99c35844ab98cf1aaca21a48876d83be84c`**。

### ① 今回の問題

長い並び／列タイトルで、**青タイトルバーの左右端と文字の間隔がほぼ無くなる**ケースがあった。

実例：

```
ジャグラーガールズ+ウルトラミラジャグ(4台並び)
```

旧⑧本番画像ではタイトルが**左右ほぼギリギリ**になっていた
（幅991pxの実出力で左6px / 右4px。旧 `convert_narabi_pil.py` は
`while text_w > w - 20`＝片側10pxまで許容、しかも2pt刻みだった）。

### ② 正式仕様

青タイトルバーのタイトルは

> **「現在のフォントサイズで安全余白を確保できる場合は従来サイズを完全維持し、
> 安全余白を確保できない長いタイトルだけ縮小する」**

を正式仕様とする。**一律縮小は禁止。**

### ③ 安全余白の正式計算

```python
safety_padding = max(1, round(BAR_H * 30 / 76))   # 片側
max_text_width = w - 2 * safety_padding
```

**標準 `BAR_H=76px` 時に片側30px**を基準とする。
**固定30pxではなく BAR_H 比例であることが重要。**

理由：**高解像度画像（記事用 `hq_scale=2.0` 等）でも相対的な余白を維持するため**
（既存の `BAR_H = round(w * 73 / 950)` / `FONT_SZ = round(BAR_H * 40 / 73)` と同じ比例思想）。

**この BAR_H 比例を固定pxへ変更しないこと。**

### ④ 約5mmという基準

既存の DPI150 換算（表は `scale = 150/96` で旧Playwright DPI150と同寸）を基準とすると
**1mm ≒ 5.906px** なので、**30px は約5mm相当**の安全余白を意図した値。

ただし**実装上の正本は「5mm」という物理値ではなく**

```python
max(1, round(BAR_H * 30 / 76))
```

**の計算式**である。**将来DPIや画像サイズだけを見て勝手に固定pxへ変更しないこと。**

### ⑤ フォント縮小方法

**縮小は1pt刻み。** 現在サイズから1ptずつ下げ、**PIL `textbbox` による実描画幅が
最大許容文字幅以下になる最初のサイズ**、つまり

> **「安全余白を確保できる最大フォントサイズ」**

を採用する。

**2pt刻みへ戻さないこと**（理由：必要以上に小さくなるのを防ぐため。
旧実装の `reduced_size -= 2` では 40→38 と飛んでいた）。

### ⑥ 判定方法

判定は必ず **PIL `textbbox` 等による実際の描画文字幅**を使用する。

**文字数による判定は禁止。**
日本語・英数字・記号で文字幅が異なるため、
**「○文字以上なら縮小」のような実装へ変更しないこと。**

### ⑦ タイトル文字列は加工禁止

**フォントサイズだけを調整する。** 次を禁止：

- 省略
- 「…」への置換
- 改行
- 2行化
- タイトル文字列の短縮
- `(N台並び)` の削除
- `(列仕掛け)` の削除

**タイトル全文を維持する。**

### ⑧ 短いタイトルの完全非回帰

現在サイズで安全余白内に収まるタイトルは **1ptも変更しない。**

実測確認済み（いずれも **42pt のまま**・修正前と**画素バイト一致**）：

- `スマスロ北斗の拳(3台並び)`
- `マイジャグV(列仕掛け)`
- `東京喰種+カバネリ海門決戦(4台並び)`

短いタイトルについては、**文字サイズ・位置・見た目を従来から変えないこと。**

### ⑨ 長いタイトルの実測基準

実測テストでは

```
ジャグラーガールズ+ウルトラミラジャグ(4台並び)   42pt → 39pt
```

となった。**これは39ptをハードコードしたものではなく、実描画幅による共通判定の結果**
（40ptでは最大許容幅を超えることも確認済み＝収まる最大サイズを採用している）。

さらに長いタイトル
（`ジャグラーガールズ～ウルトラミラジャグ+スマスロ北斗の拳(9台並び)`）では
**28ptまで縮小**するケースも確認済み。

**タイトル名別のフォントサイズハードコードは禁止。**

### ⑩ ★重要：青タイトルバーには2つの描画経路がある

| | 場所 | 用途 |
|---|---|---|
| **A** | **`streamlit_app.py` の `_build_machine_img()`** | ⑦プレビュー等の共通描画（並び・列・②個別・ジャグラー統合・その他優秀台・末尾・バラエティ・⑤オススメ） |
| **B** | **`convert_narabi_pil.py`** | **⑧本番の並び／列画像**（`_patch_and_run_narabi()` が subprocess 実行） |

この2経路で

- **BAR_H比例の安全余白**
- **実描画幅判定**
- **1pt刻み**

という**計算思想を統一する。片方だけ変更して挙動をズラさないこと。**
（今回の不具合は、まさに B だけが `w - 20` / 2pt刻みという別基準だったことが原因。）

### ⑪ `_build_machine_img()` は共通適用

今回、**並び／列だけに限定する案は不採用**。
`_build_machine_img()` の青タイトルバーを使用する画像には**共通ルールを適用**する。

例：②個別画像 ／ ジャグラー統合 ／ その他優秀台 ／ 末尾 ／ バラエティ ／ ⑤オススメ ／ 並び ／ 列

ただし**短いタイトルは従来サイズのまま**なので、
**通常画像の見た目を一律変更するものではない。**

### ⑫ 「（優秀台）」の2パーツ描画

`_build_machine_img()` の「（優秀台）」を別パーツで描画するタイトルについても、
**同じ最大幅の中に収まるよう判定する**（`_fit_title_font([main_text, sub_text], GAP_TITLE)`）。

**既存 `GAP_TITLE = -22` の意味・位置関係は変更しない。**

### ⑬ 記事用

記事用の **`no_bar=True` / `NO_BAR=True` は青タイトルバーを描画しないため今回の対象外。**
**記事用へ独自の青バー縮小処理を追加しないこと。**

### ⑭ 変更禁止領域（今回の仕様を理由に変更しない）

タイトル文字列生成 ／ 青バー高さ ／ 青バー色 ／ 赤線 ／ 画像サイズ ／ 表本体 ／ 列幅 ／ 行高 ／
台番 ／ 機種名 ／ ゲーム数 ／ BIG・REG ／ 合算確率 ／ 差枚数 ／ 総差枚 ／ 平均 ／ 勝率 ／
並び抽出 ／ 列抽出 ／ 優秀台判定 ／ ②個別画像の抽出仕様 ／ ジャグラー優秀台 ／
その他優秀台 ／ 結果テキスト ／ 保存復元 ／ WordPress

### ⑮ 実画像確認結果（⑧本番描画経路で新旧比較）

長いタイトル `ジャグラーガールズ+ウルトラミラジャグ(4台並び)`（画像幅1035px・BAR_H=80px・安全余白32px）：

| | 左余白 | 右余白 | 実測字幅 |
|---|---|---|---|
| **旧** | 約27px | 約26px | 982px |
| **新** | **約39px** | **約37px** | 959px |

**タイトル全文を維持したまま安全余白を確保。**

短いタイトル `スマスロ北斗の拳(3台並び)` ／ `マイジャグV(列仕掛け)` は
**修正前後で完全同一**（左右余白・字幅とも一致）。

⑦プレビュー経路でも、**青バー以下の赤線・表・ピンクバー等は画素バイト一致**、
画像サイズ・青バー色 `(38, 76, 161)` も不変。

### ⑯ 正式commit

```
2959b99c35844ab98cf1aaca21a48876d83be84c
fix: 青タイトルバーの長いタイトルを自動縮小する

変更ファイル: streamlit_app.py ／ convert_narabi_pil.py
変更量:       streamlit_app.py      +24 / −0
              convert_narabi_pil.py  +8 / −3
変更関数:     _build_machine_img のみ（他はバイト一致）
```

なお `2959b99` の1つ前 `0e26815 auto: 画像生成後の設定を保存` は
アプリの `_git_auto_push()` による自動commit（`auto_page_inputs.json` のみ）であり、
コード変更ではない。

### ⑰ 今後の禁止事項

1. **安全余白を固定pxへ勝手に変更しない**
2. **BAR_H比例を外さない**
3. **1pt刻みを2pt刻みへ戻さない**
4. **文字数判定へ変更しない**
5. **長いタイトルを省略しない**
6. **改行・2行化しない**
7. **`(N台並び)` / `(列仕掛け)` を削除しない**
8. **短いタイトルを一律縮小しない**
9. **タイトル別のフォントサイズをハードコードしない**
10. **`streamlit_app.py` だけ直して `convert_narabi_pil.py` を放置しない**
11. **`convert_narabi_pil.py` だけ直して `streamlit_app.py` を放置しない**
12. **記事用へ推測でコピーしない**
13. **`GAP_TITLE = -22` を今回の理由で変更しない**
14. **表本体や画像サイズを今回の理由で変更しない**

## 新小岩スランプ付き：⑤ジャグラー枠を正本とし通常統合画像を抑止（2026-09-02 確定・`1301431`）

**正式仕様。巻き戻し禁止。**対象は**【新小岩】スランプ付き結果ポスト用だけ**。
正式コード commit は **`1301431ef67b1982622dcfcc331c0c9b039a3a5e50`**
（`fix: 新小岩スランプ付きで⑤ジャグラー枠を正本とし統合画像を作らない`・
**`streamlit_app.py` の1ファイルのみ**・**+15 / −2**・**変更関数は `run_step2_juggler()` のみ**・
**新規関数なし**）。push済み。**HEAD = origin/main = `1301431` を正式基準とする。**

### ① 今回の問題

【新小岩】【スランプ付き結果ポスト用】では、通常 pipeline の

```
ジャグラーシリーズ優秀台.jpg
```

と、⑤オススメ機種ピックアップの

```
オススメ_その他のジャグラーシリーズの優秀台_1000枚以上.jpg
```

が**両方生成され、ジャグラー優秀台の掲載内容が重複していた。**

⑤B3の正式設定（`store_settings/新小岩.json`）:

| 項目 | 値 |
|---|---|
| タイトル | **その他のジャグラーシリーズの優秀台** |
| 対象機種 | マイジャグV ／ ネオアイム ／ ファンキー2 ／ ゴージャグ3 ／ ジャグラーガールズ ／ ミスジャグ ／ ハピジャグV ／ ウルトラミラジャグ |
| 閾値 | **+1,000枚以上** |
| ファイル名 | `オススメ_その他のジャグラーシリーズの優秀台_1000枚以上.jpg` |

**この⑤側を、新小岩スランプ付きのジャグラー優秀台画像の正本とする。**

### ② 直接原因

`run_step2_juggler()` には従来、**`sonota_exclude` と `juggler_jobs` が重なる場合に
通常ジャグラー統合画像を作らず overflow としてその他へ回す**既存分岐がある。

しかし新小岩スランプ付きでは **`rec_ban_level = True`** の既存正式仕様により、
**そのスキップ分岐から意図的に除外**されていた。その結果、

- 通常の `ジャグラーシリーズ優秀台.jpg`
- ⑤オススメのジャグラー画像

が**同時に生成**されていた。

これは **`a85d5b2` / `e3d6d9c`** で確定していた
**「新小岩⑤は補完枠／`jug_pool` との重複掲載可」**という過去仕様の結果である。
**今回 `1301431` で、この部分だけを正式に上書きした。**

### ③ 今回の正式仕様

新小岩スランプ付きで、**⑤のジャグラー枠が有効で、実際にジャグラー対象機種が存在する場合**は
**⑤オススメ側を正本**とする。

| | ファイル |
|---|---|
| **○ 生成する** | `オススメ_その他のジャグラーシリーズの優秀台_1000枚以上.jpg` |
| **× 生成しない** | `ジャグラーシリーズ優秀台.jpg` |

### ④ 条件付き停止（無条件停止へ変えない）

**重要：「新小岩スランプ付きだから常に通常ジャグラー画像を止める」という仕様ではない。**

既存の

```
sonota_exclude & _juggler_names
```

**が成立する場合だけ止める。**

したがって

- **⑤自体がOFF**
- **⑤ジャグラー対象が存在しない**

場合は、**`ジャグラーシリーズ優秀台.jpg` を従来どおり生成する。**
**⑤画像も通常画像も両方消える完全消失状態を防ぐ。**
**この条件付き停止を無条件停止へ変えないこと。**

### ⑤ `rec_ban_level` の正式な役割

今回の分岐では既存 **`rec_ban_level`** を利用する。

```
rec_ban_level=True（＝新小岩スランプ付き）
  かつ
sonota_exclude & _juggler_names が成立
  → 通常ジャグラー統合画像を抑止
```

**新しい `store == "新小岩"` 等の別ハードコードを追加していない。**
**今後も同じ意味を重複ハードコードしないこと。**

### ⑥ その他への overflow は禁止

今回の新小岩スランプ付きは**秋葉原例外とは意味が違う**。
新小岩では**⑤オススメ側に正式な掲載先がある**ため、通常ジャグラー統合画像を作らない場合でも
**ジャグラー台を「その他の優秀台」へ overflow しない。**

| 項目 | 正式な扱い |
|---|---|
| 通常ジャグラー統合画像 | **作らない** |
| `overflow_df` | **None** |
| `overflow_diff` | **None** |
| ⑤オススメ画像 | **正式な掲載先** |

### ⑦ `run_step2_juggler()` の正式分岐

`1301431` で追加した正式な考え方：

```python
_juggler_names = {m for m, _, _ in juggler_jobs}

if rec_ban_level and (sonota_exclude & _juggler_names):
    通常ジャグラー統合画像を生成しない
    overflow もしない
    jug_bans_all は維持
    jug_excellent_list 等の既存戻り値は維持
```

戻り値の意味と順序：

```
generated / overflow_df / overflow_diff / high_ratio_list /
jug_excellent_list / jug_pool_df / jug_bans_all
```

**今回のために戻り値の順序や意味を変えてはいけない。**

### ⑧ `jug_bans_all` は維持

通常ジャグラー統合画像を作らなくても **`jug_bans_all` は従来どおり保持する。**
⑦UIや既存の除外・チェック処理がこの値を参照するため。
**画像を作らないことを理由に `jug_bans_all` まで空にしないこと。**

### ⑨ ★+1,000枚未満のジャグラー優秀台は掲載先がなくなって構わない

従来の `ジャグラーシリーズ優秀台.jpg` では、**+1,000枚未満でも既存のジャグラー優秀台判定を
満たす台が掲載される場合があった**。一方 ⑤B3は **+1,000枚以上**が正式な抽出条件である。

今回、新小岩スランプ付きでは⑤B3を正本にしたため、

> **「+1,000枚未満だが従来のジャグラー統合画像では掲載対象だった台」は掲載先がなくなって構わない。**

**これは正式仕様。**以下の救済は**すべて禁止**：

- その他の優秀台へ回す
- 別ジャグラー画像を作る
- ⑤B3の閾値を下げる
- 通常ジャグラー統合画像を部分的に残す
- 結果テキストだけへ強制追加する

### ⑩ ⑤B3の仕様は変更しない

今回の修正は**通常ジャグラー画像を止めるだけ**。⑤B3については

**対象機種 ／ タイトル ／ +1,000枚以上 ／ 掲載台番 ／ 画像デザイン ／ ファイル名 ／ 生成条件**

を変更していない。**`generate_recommended_block_image()` および⑤オススメ関連処理は無変更。**
**今後もこの修正を理由に⑤B3側を変更しないこと。**

### ⑪ その他の優秀台への逆流禁止

`run_step3_other()` は**ジャグラー機種を通常候補から除外する既存仕様**である。
今回、**唯一の流入経路だった Step2 の overflow を発生させない**ことで、
新小岩スランプ付きのジャグラー台が「その他の優秀台」へ**逆流しない**。

```
⑤へ掲載 → その他へは戻さない
```

**「通常ジャグラー画像が無いからその他へ戻す」という変更は禁止。**

### ⑫ 秋葉原 `jug_no_merge_image` とは別仕様（一本化禁止）

既存 **`jug_no_merge_image`** および **`_jug_sonota_exc_series()`** は今回**無変更**。

| 店舗 | 意味 |
|---|---|
| **秋葉原スランプ付き** | 通常ジャグラー統合画像を作らない → **台を消失させないためその他へ overflow** |
| **新小岩スランプ付き** | ⑤に正式なジャグラー掲載先がある → 通常ジャグラー統合画像を作らない → **その他へ overflow しない** |

**意味が正反対である。この2仕様を一本化しないこと。秋葉原例外 `b600ad3` を維持する。**

### ⑬ 結果テキスト

今回 **`generate_report_text()` は変更していない。**

新小岩⑤B3対象機種は既存処理で **`jug_excellent_list` から除外**されており、
⑤側の **`generate_recommended_result_text()`** が結果テキストを担当する。
したがって**通常ジャグラー画像を止めても結果テキストの追加修正は不要**。
**この修正を理由に `generate_report_text()` の構造を変更しないこと。**

### ⑭ 📝記入部分のみモード

📝記入部分のみモードは pipeline を通らず **`_manual_juggler_auto_extract()`** 等の別経路を使う。
今回の `1301431` は **`run_step2_juggler()` だけの変更**なので、
**`0f0697f` / `b600ad3` の📝3カテゴリ分離仕様には影響しない。**
**今回の仕様を📝へ推測コピーしないこと。**

### ⑮ 記事用

記事用についても今回の目的で専用コードは変更していない。
記事用へ同じ仕様を適用したい場合は

1. 現在経路の調査
2. 影響範囲報告
3. 最小修正案
4. ユーザー承認
5. 実装

の順にする。**今回対応済みと誤認しないこと。**

### ⑯ 他店舗・新小岩通常ページ

**`rec_ban_level=False` の経路は修正前と同じ挙動を維持**している。したがって

- 他店舗
- 新小岩 `with_slump=False`
- 既存の通常結果ポスト用

は**今回の変更対象外**。既存の
**「⑤にジャグラーあり → 通常統合画像を作らず overflow」**という従来挙動を変更しない。

### ⑰ 実データ確認（新小岩 2026/9/1・464台・pipeline直呼び）

| | 修正前 | 修正後 |
|---|---|---|
| `ジャグラーシリーズ優秀台.jpg` | **あり** | **なし** |
| `jug_pool_df` | **13台** | **None / 0台** |
| `excellent_list`（その他） | **30件** | **30件・完全一致** |
| ジャグラー逆流 | — | **なし** |
| `jug_bans_all` / `high_ratio_list` / `zen_dai_list` | — | **一致** |

**差分ファイルは `ジャグラーシリーズ優秀台.jpg` の1件だけ。**

なお実測手法について：HEAD版のコピーを別ディレクトリへ置くと
**`BASE_DIR = os.path.dirname(os.path.abspath(__file__))`** がずれて
`機種名変換.xlsx` / `store_settings` を読めず、機種名変換の結果まで変わってしまう。
**HEAD版との実データ比較は必ず同一ディレクトリに置いて行うこと。**

### ⑱ ⑤OFF時の非回帰（必須）

**⑤OFF、または⑤にジャグラー対象が無いケースでは、修正前後の `run_step2_juggler()` の
戻り値が完全一致する。**＝通常の `ジャグラーシリーズ優秀台.jpg` が従来どおり生成される。
**この非回帰は必須。将来の修正でも必ず確認すること。**

### ⑲ 保護対象（今回バイト一致／無変更）

`jug_no_merge_image` 関連 ／ `_jug_sonota_exc_series()` ／ `run_step3_other()` ／
`generate_report_text()` ／ `generate_recommended_block_image()` ／
`generate_recommended_result_text()` ／ `_manual_juggler_auto_extract()` ／
⑤オススメ生成処理 ／ `wp_client.py`。**新規関数なし。**

### ⑳ 正式commit

```
1301431ef67b1982622dcfcc331c0c9b039a3a5e50
fix: 新小岩スランプ付きで⑤ジャグラー枠を正本とし統合画像を作らない

変更ファイル: streamlit_app.py のみ
変更量:       +15 / −2
変更関数:     run_step2_juggler() のみ
新規関数:     なし
```

### ㉑ 今後の禁止事項

1. **新小岩スランプ付きで⑤ジャグラー枠が有効なのに通常ジャグラー統合画像を復活させない**
2. **新小岩スランプ付きで通常ジャグラー画像停止時にその他へ overflow させない**
3. **+1,000枚未満台を救済しない**
4. **⑤B3の +1,000枚以上を今回の理由で変更しない**
5. **⑤B3の対象機種・タイトル・ファイル名を変更しない**
6. **⑤OFFでも通常ジャグラー画像を止める無条件仕様へ変えない**
7. **`rec_ban_level` と同義の新店舗ハードコードを増やさない**
8. **`jug_bans_all` を空にしない**
9. **秋葉原 `jug_no_merge_image` と一本化しない**
10. **`_jug_sonota_exc_series()` を今回の理由で変更しない**
11. **`run_step3_other()` を今回の理由で変更しない**
12. **`generate_report_text()` を今回の理由で変更しない**
13. **📝へ推測コピーしない**
14. **記事用へ推測コピーしない**
15. **他店舗の既存 overflow 仕様を変更しない**
16. **今回無関係なリファクタ・未使用コード整理をしない**

## ⑦プレビューのON/OFFは非widgetのOFF集合を正本にする（2026-09-02 確定・`00a472a`）

**正式仕様。巻き戻し禁止。**対象は**⑦プレビュー「生成する」チェックを使う全店舗・全経路**
（通常結果ポスト用／スランプ付き結果ポスト用／新宿歌舞伎町かぶぱ／📝記入部分のみ）。
正式コード commit は **`00a472a`**（`fix: ⑦プレビューのON/OFFを非widgetのOFF集合で正本化する`・
**`streamlit_app.py` の1ファイルのみ**・**+85 / −40**・32ハンク）。push済み。

### ① 事象

【新小岩】スランプ付き結果ポスト用・2026/8/30 で

```
⑦プレビュー生成
  → ToLOVEるトランス_高配分.jpg を OFF
  → 🔄その他を更新
  → ⑦プレビュー上では 2060 / 2334 が「その他の優秀台」へ移動（正常）
  → その後の再生成等で checkbox の widget state が消失
  → ⑧実行
```

としたとき、⑧の完成フォルダに **`08_ToLOVEるトランス_高配分.jpg` が復活**し、
**その他の優秀台へ再配分した 2060 / 2334 も消えていた**。
結果テキストにも `🎖️ToLOVEるトランス(2/3台)→平均+1,650枚` が残っていた。
＝**⑦の最終状態が⑧へ引き継がれない**不整合。

### ② 根本原因

**⑦の画像ON/OFF状態を `auto_prev_ck_*` の Streamlit widget state だけに保持していた。**

⑦プレビューのグリッドは
`if _auto_previews is None or _unit_regen or _manual_regen:` の **`else:` 側でのみ描画**される。
そのため**プレビュー再生成・🎯掲載台変更・液晶再選択など checkbox が描画されない run** を挟むと
**Streamlit の stale widget GC** がキーを削除し、旧実装の

```python
if key not in st.session_state:
    st.session_state[key] = True          # ← これが原因
```

によって**勝手にONへ戻っていた**。⑧・🔄・結果テキスト同期はいずれも
`st.session_state.get(_pv_ck_key(...), True)` を直接読んでいたため、
**画像の復活・その他への再配分の消失・結果テキストの不整合が同時に発生**した。

**この単純seedへ絶対に戻さないこと。**

なお ⑧側の再配分機構（OFF画像を `os.remove` し `_extra_dfs` へ回す）自体は元から存在し、
`with_slump` や店舗による除外条件も無い。**壊れていたのは判定の正本だけ**である。

### ③ 正式仕様

**画像のOFF状態を widget state だけの正本にしない。**
**店舗＋Excel（日付）単位の非widget session_state に「OFF画像名の集合」を持ち、それを正本とする。**

```
_pv_off_key(store, excel_name) → f"_pv_off_{store}_{os.path.splitext(excel_name)[0]}"
例: _pv_off_新小岩_20260830_新小岩_20S
値: OFF になっている画像ファイル名の set
```

**`_pv_ck_key()` は変更・廃止しない**（キー体系も不変。`auto_prev_ck_*` のままで、
約20箇所の逆引きを壊さない）。

### ④ 正式ヘルパー（5つ）

| 関数 | 役割 |
|---|---|
| **`_pv_off_key(store, excel_name)`** | OFF集合を持つ非widgetキーを返す（店舗＋Excel日付単位） |
| **`_pv_off_set(store, excel_name)`** | 現在OFFの画像ファイル名の集合を返す（OFF状態の正本） |
| **`_pv_off_toggle(store, excel_name, fname)`** | checkbox の `on_change`。ON→集合から `discard` ／ OFF→集合へ `add` |
| **`_pv_is_on(store, excel_name, fname)`** | **最終ON/OFF判定の共通関数**。widget state があればその現在値、無ければ `fname not in OFF集合` |
| **`_pv_set_on(store, excel_name, fname)`** | プレビューへ新規追加した画像をONにする（widget値True＋OFF集合からも除外） |

### ⑤ ON/OFF の更新

```python
st.checkbox("生成する", key=_ck_key, label_visibility="collapsed",
            on_change=_pv_off_toggle, args=(store, uploaded.name, _ptitle))
```

- **OFF → OFF集合へ add**
- **ON → OFF集合から discard**
- **一度OFFにした画像をONへ戻したら、以後ONを維持する。「一度OFFなら永久OFF」にしてはならない。**
  ON復帰後にプレビュー再生成・液晶再選択・⑧実行をしてもONのままであること。

### ⑥ widget GC 後の復元

```python
_pv_off_now = _pv_off_set(store, uploaded.name)     # グリッド描画の直前に1回だけ読む
...
if _ck_key not in st.session_state:
    st.session_state[_ck_key] = _ptitle not in _pv_off_now
```

**「キーが無い＝True」へ戻さない。**OFF集合にある画像は False、無い画像は True で復元する。

### ⑦ 共通判定への統一

**⑧実行 ／ 🔄その他を更新 ／ 結果テキスト同期 ／ 並び・列 ／ ⑤オススメ ／ ②関連**など、
従来 `st.session_state.get(_pv_ck_key(...), True)` を直接読んでいた既存経路は
**`_pv_is_on()` の共通判定へ統一**した（該当26箇所 → 0箇所）。
新規追加プレビューのON化は **`_pv_set_on()`** に統一（7箇所）。

**各所へ `st.session_state.get(_pv_ck_key(...), True)` を再びコピペしない。
独自のON/OFF判定を再実装しない。**

**ただし横版の `default=False` 判定は別物なので今回の仕様へ巻き込まない。**

```python
if (_pv_is_on(store, uploaded.name, _var_fn_ex)
        or st.session_state.get(
            _pv_ck_key(store, uploaded.name, _var_side_fn), False)):
```

この `, False)` は「キーが無ければ横版は未チェック扱い」という既存の意図であり、
`_pv_is_on()`（キー無し＝ON扱い）へ置き換えてはならない。

### ⑧ 日付スコープ

**OFF集合は必ず店舗＋Excel（日付）単位。**

- **8/30 のOFFを 9/1 へ持ち越さない。**
- **他店舗へ持ち越さない。**
- **同じ 8/30 へ戻ればOFF状態は復元される。**

### ⑨ pipeline は無変更

今回**生成前skipへの拡大はしていない。`run_auto_pipeline()` の署名も変更していない。**

```
pipeline が画像生成 → ⑧でOFF判定 → os.remove → その他へ再配分
```

という既存構造を維持したまま、**ON/OFF判定の正本だけを壊れないようにした**。
**勝手に生成前skipへ拡大しないこと。**

### ⑩ 実機確認結果（2026-09-02・ローカル・新小岩 2026/8/30・⑧実行）

**ToLOVEるトランスOFF時**

- `ToLOVEるトランス_高配分.jpg` **なし**（連番は繰り上がり・欠番なし）
- 結果テキストの **`👑高配分機種` から `🎖️ToLOVEるトランス` が消滅**
- **`🚩【2060番台】ToLOVEるトランス→+4,350枚` → `👑その他の優秀台`**
- **`🚩【2334番台】ToLOVEるトランス→+3,750枚` → `👑その他の優秀台`**
- ⑦のその他画像にも 2060 / 2334 が掲載されていることを画面で確認

**OFF→ON へ戻した場合**

- **`08_ToLOVEるトランス_高配分.jpg` が復活**
- **`🎖️ToLOVEるトランス(2/3台)→平均+1,650枚` が復活**（199行目・修正前と同一）
- **2060 / 2334 はその他から消滅**
- **修正前ベースラインへ完全復帰**

**日付切替**：8/30でOFF → 9/1取得＋⑦生成で**12枚すべてON（持ち越し0）** →
8/30へ戻して⑦生成で**OFFが復元**。

### ⑪ widget GC 再現テスト（P①②・両方PASS）

| | 操作 | 結果 |
|---|---|---|
| **P①** | OFF → 🔄その他を更新 → **液晶再選択** | **OFF保持** |
| **P②** | OFF → 🔄 → **🎯掲載台変更＋🔄（＝プレビュー全再生成 `_unit_regen` 経路）** | **OFF保持**・その他の再配分も維持 |

**どちらの後に⑧を実行しても高配分画像は復活しない。**⑧完了後もOFF表示が保持される。

**注**: ⑦「プレビュー生成」ボタンはプレビュー存在中は表示されない仕様のため、
P②は**同じ全再生成経路である🎯変更＋🔄**で実施した（旧実装でOFFが消えていた経路そのもの）。

### ⑫ 非回帰

**A〜P すべてPASS。純粋テスト42項目PASS / FAIL 0。**

**バイト一致（本体無変更）**：`generate_report_text()` ／ `run_auto_pipeline` ／
`run_step1_main` ／ `run_step2_juggler` ／ `run_step3_other` ／ `_kojin_yushu_filter` ／
`_pv_ck_key` ／ `_dedup_previews` ／ `_manual_juggler_auto_extract` ／
`_manual_sonota_auto_extract` ／ `_jug_sonota_exc_series` ／ `_build_machine_img` ／
`_build_sue_images` ／ `generate_recommended_block_image` ／
`generate_recommended_result_text` ／ `filter_recommended_machines` ／
`_rm_stale_image` ／ **`show_auto_article_page`（記事用）** ／ **`wp_client.py`**。

**変更したのは `show_auto_page` と、判定を共通化した3ヘルパー**
（`_manual_kojin_on` / `_narabi_checked_bans` / `_rec_checked_bans`。
差分は各2行＝`st.session_state.get(_pv_ck_key(...), True)` → `_pv_is_on(...)` だけ）。
**新規は上記5ヘルパーのみ。**

**全画像ON時は修正前と完全一致**（OFF集合が空なら `_pv_is_on` は旧 `.get(key, True)` と論理同値）。

維持している既存正式仕様：**`1301431`（新小岩⑤ジャグラー枠が正本・通常統合画像を作らない）**／
**秋葉原 `jug_no_merge_image` 例外**／`_rec_ban_level` の判定式／結果テキストの
`excellent_min_diff=2000`／📝3カテゴリ分離（`0f0697f` / `b600ad3`）／
②の現在ON ban 正本（`f719581` / `20c4ac3` / `2860b2f`）／列仕掛け（`1410753` 〜 `5ef8bde`）。

**記事用（`art_prev_ck_*` の別キー体系）は今回の対象外。**

### ⑬ Git履歴（誤認しないこと）

```
00a472a  fix: ⑦プレビューのON/OFFを非widgetのOFF集合で正本化する   ← 正式コードcommit（streamlit_app.py のみ）
4708793  auto: 画像生成後の設定を保存                              ← ⑧のアプリ自動commit
HEAD = origin/main = 47087934f4b47f604600fc24655dd43ce523df27
```

`4708793` は `_git_auto_push()` による `auto_page_inputs.json` の自動commitで、
**コード変更ではない**。**`00a472a` が消えた・上書きされたと誤認しないこと**（`4708793` の祖先）。

**実機確認より前にコードをコミットしている。**これは
「未コミット状態でアプリを動かしたまま検証しない（`55e7752`）」の必須ルール
（`_git_auto_push()` の stash 窓で HEAD版＝修正前コードが走り設定JSONを壊し得る）に従ったため。
実行前に `_git_auto_push()` の targets と既存差分の交差が **0件**であることを確認している。

### ⑭ `auto_page_inputs.json` について

作業後に残る `M auto_page_inputs.json` は、**日付切替の実機テストで 9/1 を開いたことによる
アプリの正常な毎レンダー保存**（`20260901_新小岩_20S.xlsx` エントリの新規追加。既存値の変更・消失0）。
⑧の自動commit `4708793` は 8/30 エントリへの既定3キー追加
（`retsu_enabled` / `retsu_ranges_input` / `jug_extra_auto_新小岩`）のみ。

**この仕様の記録作業では `auto_page_inputs.json` を編集・restore・reset・checkout・commit しない。**

### ⑮ 保護対象

```
M auto_page_inputs.json
M wrt_machines.json
?? WordPress連携テスト.jpg
?? wp_test.py
stash 4件
```

**すべて保持する**（stage / commit / restore / reset / checkout / stash / 削除 / 編集をしない）。

### ⑯ 禁止事項

1. **widget state だけを正本へ戻す**
2. **キーが無い場合に無条件 True へ seed する**（`if key not in st.session_state: = True`）
3. **OFF集合の日付スコープを外す**（店舗のみ・グローバルにしない）
4. **`_pv_ck_key()` のキー体系を変更する**（index・乱数の追加も禁止）
5. **各所へ独自のON/OFF判定を再実装／`st.session_state.get(_pv_ck_key(...), True)` を再コピペする**
6. **横版の `default=False` 判定を今回の仕様へ巻き込む**
7. **`run_auto_pipeline()` の署名変更**
8. **生成前skipへの勝手な拡大**
9. **結果テキストの閾値変更**（`excellent_min_diff=2000` を触らない）
10. **`1301431` の巻き戻し**
11. **秋葉原 `jug_no_merge_image` 例外の変更**
12. **記事用への推測コピー**

## 記事用：パネル非対象店舗の⑦・🔄でもスランプを正常合成する（2026-09-03 確定・`bd9fa40`）

**正式仕様。巻き戻し禁止。**対象は**記事用ページの⑦プレビューと🔄「その他を更新」のスランプ合成だけ**。
正式コード commit は **`bd9fa40949cb9206d45b98ae5aa7a645c9554fb4`**
（`fix: 記事用プレビューのスランプ合成NameErrorを修正`・**`streamlit_app.py` の1ファイルのみ**・
**+10／−2**・**2ハンク**）。push済み。
**HEAD = origin/main = `bd9fa40` を正式基準とする。**

### ① 発生した不具合（パネルとスランプを混同しないこと）

**【渋谷新館】記事用ページ／2026/9/2 データ**で⑦プレビューを生成したとき、

- 表画像は生成される
- **しかしスランプグラフが表示されない**
- パネルも表示されない

という状態だった。

**このうち「パネルが表示されない」ことはバグではない。**
現在の正式仕様は **`_ARTICLE_PANEL_STORES = {"高田馬場"}`** であり、
**渋谷新館は記事用パネルの対象外**だからである。

**今回のバグは「パネルではなくスランプが表示されなかったこと」である。**
**この区別を必ず維持すること。**「パネルも出ていない」という当初の症状報告に引きずられて、
パネル側を修正対象にしてはならない。

### ② 根本原因

`show_auto_article_page()` の**記事用⑦プレビュー**と**🔄「その他を更新」**のスランプ合成処理で、
**パネル処理用の `if` の内側でしか定義されない変数**

```
_bare_pv2   （⑦プレビュー）
_bare_u     （🔄その他を更新）
```

を、**`if` の外側にあるスランプ処理から参照**していた。

```python
if store in _ARTICLE_PANEL_STORES:                 # 高田馬場のときだけ真
    _bare_pv2 = re.sub(r"^\d{2}_", "", _fn_pv2)    # ← if の内側でしか代入されない
    ...
_hq_pv2 = _art_hq_scale_for(_bare_pv2, store, len(_bans_pv2))   # ← if の外側で参照
```

そのため **`_ARTICLE_PANEL_STORES` に含まれない店舗**では、その変数が定義されないまま参照され

```
NameError: name '_bare_pv2' is not defined
NameError: name '_bare_u' is not defined
```

が発生していた。**対象例：渋谷新館・秋葉原**など、記事用パネル対象外の店舗。

**この漏れは `101ac8f`（2026-08-04 17:26・高田馬場記事用の高解像度化）で
`_hq_pv2 = _art_hq_scale_for(_bare_pv2, ...)` を `if` の外へ追加したときに作り込まれた。**
当時は記事用が高田馬場だけだったため顕在化せず、`5dc22e6`（2026-08-28・渋谷新館の記事用入口追加）
以降の渋谷新館では**最初から一度もスランプが出ていなかった**。

### ③ なぜ画面上でエラーにならなかったか

`NameError` は**スランプ合成ブロック全体を囲む外側の**

```python
except Exception:
    pass  # スランプ取得失敗時は表のみプレビュー
```

で握り潰されていた。そのため

- Streamlit 画面がエラー停止する
- `NameError` が画面へ表示される

のではなく、**スランプ合成処理だけが静かにスキップされる**状態になっていた。
症状は **「画像（表）は生成されるが、スランプだけ無い」**。ログも警告も出ない。

**今回 `except Exception: pass` 自体は変更・削除していない。**
**今回の修正を理由に、今後この例外処理を無断で変更・削除しないこと。**

### ④ 正式な修正（2箇所だけ）

**⑦記事用プレビュー**

```python
# 旧
_hq_pv2 = _art_hq_scale_for(_bare_pv2, store, len(_bans_pv2))

# 新（正式）
_hq_pv2 = _art_hq_scale_for(
    re.sub(r"^\d{2}_", "", _fn_pv2),
    store,
    len(_bans_pv2),
)
```

**🔄「その他を更新」**

```python
# 旧
_hq_u = _art_hq_scale_for(_bare_u, store, len(_bans_u))

# 新（正式）
_hq_u = _art_hq_scale_for(
    re.sub(r"^\d{2}_", "", _fn_u),
    store,
    len(_bans_u),
)
```

**⑧本番ですでに使われていた正式な計算方法 `re.sub(r"^\d{2}_", "", _fn_*)` へ揃えただけ**である。
新しい pipeline も新しい関数も作っていない。店舗ハードコードも増やしていない。

### ⑤ ★最重要：パネル判定とスランプ判定は別物

**記事用で「パネル対象店舗ではない」ことと「スランプを付けない」ことは、まったく別の条件である。**

現在 `_ARTICLE_PANEL_STORES = {"高田馬場"}` なので：

| 店舗 | 記事用パネル | 記事用スランプ |
|---|---|---|
| 高田馬場 | **あり** | **あり** |
| 渋谷新館 | **なし（仕様）** | **あり（対象画像へ正常合成する）** |
| 秋葉原 | **なし（仕様）** | **あり（対象画像へ正常合成する）** |

**「パネル非対象店舗だからスランプ処理まで止める」という実装にしてはならない。**
**パネルの店舗ゲート（`_ARTICLE_PANEL_STORES`）と、スランプの合成処理・高解像度判定を
結び付けないこと。**
スランプ合成ブロックの入口は `if _pv_api_key_sl and _art_pr.get("ok") and _art_pil:` であって、
**店舗ゲートを持たないのが正式**である。

### ⑥ `_ARTICLE_PANEL_STORES` は今回変更していない

今回 **`_ARTICLE_PANEL_STORES = {"高田馬場"}` は1文字も変更していない。**
**渋谷新館を追加していない。秋葉原も追加していない。**

したがって **「今回の修正で渋谷新館にもパネルを表示するようになった」と今後誤認しないこと。**
**渋谷新館の記事用パネル非表示は現在の正式仕様であり、そのまま維持する。**

パネルを追加したい場合は**別案件**として、
**調査 → 原因／現仕様報告 → 最小案 → ユーザー承認 → 実装**の順で行うこと。
なお `_art_hq_scale_for()` も同じ定数で高解像度を判定しているため、
`_ARTICLE_PANEL_STORES` へ店舗を足すと**その店舗の記事用画像がすべて2倍描画になる副作用**がある。

### ⑦ `_ARTICLE_GAP_FILL_STORES` も無変更

**`_ARTICLE_GAP_FILL_STORES = {"高田馬場"}` も今回無変更。**
液晶はめ込み仕様は今回の修正とは無関係である。

**渋谷新館へ、今回の修正を根拠にパネル・液晶はめ込みを追加してはいけない。**

### ⑧ ⑧本番は元から正常だった

記事用⑧本番では、問題の `_bare_pv2` / `_bare_u` を使わず

```python
_hq_sl = _art_hq_scale_for(re.sub(r"^\d{2}_", "", _fp_sl), store, len(_bans_sl))
```

と**インラインで再計算**していたため、今回の `NameError` 問題は**存在していなかった**。
**今回⑧本番のコードは変更していない**（`_bare_sl` の出現数も 3 → 3 で不変）。

したがって今回の修正は、**⑦記事用プレビューと🔄その他を更新の2経路を、
すでに正常だった⑧本番の方式へ揃えたもの**である。
**⑧本番側を今回の修正に合わせてさらに変更しないこと。**

### ⑨ 実機確認（渋谷新館）

**渋谷新館／記事用／2026/9/2／確定データ 433台**で⑦プレビューを実行し、**26枚**を生成。

対象画像でスランプが正常合成されたことを目視確認した：

```
L攻殻機動隊_高配分.jpg（4台）        とある禁書目録2_高配分.jpg（6台）
ゴッドイーター_高配分.jpg（2台）      戦国乙女5_高配分.jpg（10台）
モンハンライズ_高配分.jpg（2台）      ネオアイム_高配分.jpg（12台）
かぐや様_高配分.jpg（2台）           東京喰種_高配分.jpg（16台）
マイジャグV_高配分.jpg（18台）        カバネリ海門決戦_高配分.jpg（8台）
並び13枚（北斗転生2(2台並び) 等）
ジャグラーシリーズ優秀台.jpg（15台）
その他の優秀台ピックアップ.jpg（28台）
```

**`差枚数ランキング.jpg` は ban_map の対象外のため表のみで正常**（不具合ではない）。

**修正前はスランプ0枚だったものが、修正後は対象画像へ正常に合成された。**
**パネルは26枚すべてで非表示のまま**であることも確認済み（＝⑥の正式仕様を維持）。

### ⑩ 🔄「その他を更新」の確認

🔄「その他を更新」後も**スランプが消えず、正常に維持される**ことを確認済み。

さらに再合成ループを直接通すため、**`かぐや様_高配分.jpg` を OFF にして🔄を実行**する確認も行い、

- OFF状態は正常反映（チェックボックス未チェックを目視確認）
- 他画像のスランプは維持
- **⑦プレビューOFF状態の非widget正本仕様（`00a472a`）も維持**

を確認した。その他が28台のまま変化しなかったのは、**かぐや様の2台が +600枚 / +400枚＝
+1,000枚未満で再振り分け対象外**のため（正常）。確認後、チェックはONへ復帰済み。

**今回の修正を理由に `_pv_is_on()` や非widget OFF集合の仕様を変更しないこと。**

### ⑪ 高田馬場の非回帰

**高田馬場／記事用／2026/9/2／344台**で実機確認済み。

- **パネル正常**（ディスクアップUR／喰霊零Re／真打吉宗のパネルが表の上に表示）
- **ジャグラー統合・その他優秀台の 2×2 パネル正常**
- **スランプ正常**
- **白サマリー正常**（勝率／総差枚／平均）
- **採番正常**（①Excel ②ポスター … ⑦プレビュー）

あわせて、旧 `_bare_*` と新しい `re.sub(r"^\d{2}_", "", _fn_*)` の結果が
**9種のファイル名パターン（連番あり／なし、その他、ジャグラー統合、末尾、バラエティ、並び、
列仕掛け、高配分）すべてで一致**することを確認済み。

したがって **パネル対象店舗である高田馬場では、修正前後で高解像度判定を変えていない。**

### ⑫ 秋葉原について（誤記しないこと）

**秋葉原では実機画面確認をしていない。**

ただし**コード実行レベル**で

```
修正前： NameError: name '_bare_pv2' is not defined
修正後： ⑦・🔄とも正常に _art_hq_scale_for() まで到達
```

を確認済みで、**⑦／🔄／⑧の三者が同じ引数になる**ことも9パターンで確認している。

**「秋葉原も実機確認済み」と誤って記録しないこと。**
**コード実行レベルでの確認であることを明記する。**

### ⑬ 液晶はめ込み確認について（誤記しないこと）

高田馬場 9/2 のデータでは、**最終行に2コマ以上の空きがある対象画像が存在せず**
（`_gap_fillable` の条件を満たすケースが出なかった）、**液晶はめ込みの実機確認はできていない。**

ただし **`_ARTICLE_GAP_FILL_STORES` および `_gap_sel_key` 系は無変更**であり、
`_hq` の値も従来と一致するため、**今回の修正で液晶仕様を変更した事実はない。**

**「液晶も実機確認済み」とは記録しないこと。**

### ⑭ 非回帰（今回いっさい変更していない）

**関数のバイト一致を機械確認済み：**

`show_auto_page` ／ `_composite_slump_onto_images()` ／ `_art_hq_scale_for()` ／
`_apply_panel_to_table_img()` ／ `_attach_slump_to_table()` ／ `_build_panel_row()` ／
`_build_variety_panel_grid()` ／ `draw_slump_graph()` ／ `run_auto_pipeline()` ／
`run_step1_main()` ／ `run_step2_juggler()` ／ `run_step3_other()` ／ `generate_report_text()` ／
`_attach_slump_to_table_side()` ／ `_build_slump_title_img()` ／ `_art_ranking_image()` ／
`_save_article_inputs()` ／ `_restore_article_inputs()` ／ `_art_kojin_default()` ／ `_pv_is_on()`

**ファイル無変更（md5一致）：** `wp_client.py` ／ `convert_narabi_pil.py`

**以下の正式仕様も変更していない：**

⑦プレビューOFF状態の非widget正本（`00a472a`）／`_pv_is_on()`／②現在ON実掲載台番
（`f719581` / `20c4ac3` / `2860b2f`）／📝3カテゴリ分離（`0f0697f` / `b600ad3`）／
新小岩⑤ジャグラー正本（`1301431`）／青タイトルバー長文自動縮小（`2959b99`）／
列仕掛け・並び（`1410753` / `9ec653e` / `42ea146` / `5ef8bde`）／通常結果ポスト用pipeline／
結果テキスト／WordPress／秋葉原 `jug_no_merge_image`。

### ⑮ 正式commit（履歴の誤認を防ぐ）

```
bd9fa40949cb9206d45b98ae5aa7a645c9554fb4
fix: 記事用プレビューのスランプ合成NameErrorを修正

変更ファイル: streamlit_app.py のみ
変更量:       +10 / −2（2ハンク）
変更関数:     show_auto_article_page() のみ
新規関数:     なし
```

**なお、push前に一度作成されたローカル commit `7ededd5` は、commitメッセージの先頭に
誤って `@` が混入していたため（Bash に PowerShell の here-string 記法を渡したミス）、
未push状態でメッセージのみ `--amend` して `bd9fa40` になった。コード差分は完全同一
（`git diff 7ededd5 bd9fa40` の差分行数 0）。**

**GitHub へ push された正式 commit は `bd9fa40` のみで、force push や公開履歴の書き換えは
行っていない**（`82d0eb3..bd9fa40` の通常 fast-forward）。
**今後 `7ededd5` を正式 commit と誤認しないこと。**

### ⑯ 今後の禁止事項

1. **`_bare_pv2` / `_bare_u` をスランプ側で再利用する形へ戻さない**
2. **パネル用 `if` 内のローカル変数を `if` 外のスランプ処理から参照しない**
3. **「パネル非対象＝スランプ非対象」と解釈しない**
4. **渋谷新館を無断で `_ARTICLE_PANEL_STORES` に追加しない**
5. **秋葉原を無断で `_ARTICLE_PANEL_STORES` に追加しない**
6. **`_ARTICLE_GAP_FILL_STORES` を今回の修正理由で広げない**
7. **液晶はめ込み仕様を今回の修正に混ぜない**
8. **⑧本番の正常コードを無断変更しない**
9. **`except Exception: pass` を今回の修正を理由に無断変更しない**
10. **`_art_hq_scale_for()` 本体を変更しない**
11. **通常結果ポスト用 pipeline へ今回の修正をコピーしない**
12. **記事用以外へ推測で適用しない**
13. **パネル対応が必要になった場合は別案件として調査から始める**
14. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館記事用：パネル・液晶はめ込み・液晶選択UIを正式追加（2026-09-03 確定・`148d672`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の📰記事用ページだけ**。
正式コード commit は **`148d672a9a04e67d33278a1d48568f10549a73cc`**
（`feat: 渋谷新館の記事用にパネルと液晶選択を追加`・**`streamlit_app.py` の1ファイルのみ**・
**25 lines changed（+15 / −10）**・**11ハンク**）。push済み（通常push・fast-forward・force pushなし）。
**HEAD = origin/main = `148d672` を正式基準とする。**

### ① 変更前の正式仕様（`5da4667` 時点）

直前の記録 commit `5da4667`（`docs: 記事用スランプ合成のパネル非対象店舗仕様を記録`）の時点では

```python
_ARTICLE_PANEL_STORES    = {"高田馬場"}
_ARTICLE_GAP_FILL_STORES = {"高田馬場"}
```

であり、記事用の正式仕様は次のとおりだった。

| 店舗 | パネル | 液晶はめ込み | 液晶選択UI | スランプ |
|---|---|---|---|---|
| 高田馬場 | あり | あり | あり | あり |
| 渋谷新館 | **なし** | **なし** | **なし** | あり |
| 秋葉原 | なし | なし | なし | あり |

**`5da4667` の記録は、その時点では正しい正式仕様である。**
**「`5da4667` が間違っていた」とは扱わないこと。**
本節は、その後の `148d672` によって**渋谷新館の部分だけが正式に上書きされた**ことを記録するものである。

### ② 今回の要望・発端

渋谷新館の記事用で **2026/9/2** のデータを取得して確認したところ、

- スランプグラフは **`bd9fa40` の修正により正常表示された**
- しかし**機種パネルが表示されない**
- 表＋スランプの最終行に**2コマ以上の空きがあっても液晶が入らない**
- **液晶を選択するUIも表示されない**

という状態だった。

高田馬場の記事用には既に「パネル」「液晶はめ込み」「液晶選択UI」が実装されていたため、
**同じ機能を渋谷新館の記事用にも正式追加する**ことにした。

### ③ `148d672` で確定した新しい正式仕様

```python
_ARTICLE_PANEL_STORES    = {"高田馬場", "渋谷新館"}
_ARTICLE_GAP_FILL_STORES = {"高田馬場", "渋谷新館"}
```

記事用の現在の正式仕様は次のとおり。

| 店舗 | パネル | 液晶はめ込み | 液晶選択UI | スランプ | HQ倍率 |
|---|---|---|---|---|---|
| **高田馬場** | **あり** | **あり** | **あり** | あり | **2.0倍** |
| **渋谷新館** | **あり** ★新規 | **あり** ★新規 | **あり** ★新規 | あり | **1.0倍** |
| **秋葉原** | なし | なし | なし | あり | 1.0倍 |

**★「渋谷新館は記事用パネル非対象」という `5da4667` 時点の仕様は、`148d672` により正式に上書きされた。**
現在の正式仕様は本節（`148d672`）である。

**ただし `5da4667` の既存記録そのものは変更しない。**
過去の仕様と「どの commit で仕様変更されたのか」を Git履歴と CLAUDE.md の両方から
追跡できる状態を維持するためである。

### ④ ★最重要：HQ 2倍描画は別仕様（同一集合で管理しない）

**パネル対象店舗と HQ 対象店舗を同じ集合で管理してはならない。**

`148d672` より前は `_ARTICLE_PANEL_STORES` が
**「パネル合成のゲート」と「記事用の高解像度2倍描画のゲート」の2役を兼ねていた**。
そのため渋谷新館をこの定数へ足すだけだと、**渋谷新館の記事用画像まで2倍描画になる副作用**があった。

これを避けるため **`_ART_HQ_STORES` を新設して HQ ゲートを分離**した。正式値は次のとおり。

```python
_ART_HQ_STORES = {"高田馬場"}
```

| 店舗 | HQ倍率 |
|---|---|
| 高田馬場 | **2.0倍** |
| 渋谷新館 | **1.0倍** |
| 秋葉原 | **1.0倍** |

**渋谷新館を `_ARTICLE_PANEL_STORES` に追加したからといって、`_ART_HQ_STORES` へ追加してはいけない。**

**設計意図**：HQ 2倍（および `_ART_HQ_TARGET_KB = 5500`）は
**WordPress へ画像を送る店舗の画質担保のための仕様**であり、
WordPress 連携は `store == "高田馬場"` でゲートされている（記事用⑧の payload 保存とボタンの2箇所）。
**渋谷新館の記事用に WordPress 送信経路は無い**ため、2倍描画は画質メリットが無く
Cloud のメモリと出力サイズだけが増える。パネル合成・液晶はめ込みはどちらも**倍率に依存しない**
（パネルは `img.width` に合わせて等分、液晶は箱サイズ相対で中央配置）ため、
**「パネル対象」「液晶対象」「HQ対象」を別ゲートとして扱うことが正式仕様**になった。

将来 渋谷新館の WordPress 対応を実装する際に `_ART_HQ_STORES` へ渋谷新館を足せば、
そのとき初めて2倍描画が有効になる。

### ⑤ 各ゲートの正式な役割（安易に一本化しない）

| 定数 | 役割 | 現在値 |
|---|---|---|
| **`_ARTICLE_PANEL_STORES`** | 記事用で**機種パネルを付ける**店舗 | **`{"高田馬場", "渋谷新館"}`** |
| **`_ARTICLE_GAP_FILL_STORES`** | 記事用で**最終行の空きへ液晶をはめ込み、液晶選択UIを利用する**店舗 | **`{"高田馬場", "渋谷新館"}`** |
| **`_ART_HQ_STORES`** | 記事用画像を**HQ倍率で描画する**店舗 | **`{"高田馬場"}`** |

**この3つを今後安易に一本化しないこと。**

参照箇所（`148d672` 時点）:
- `_ARTICLE_PANEL_STORES` … パネル合成の3箇所（⑦プレビュー／🔄その他を更新／⑧本番）
- `_ARTICLE_GAP_FILL_STORES` … 液晶合成・meta保存・選択UI・🔄・⑧の6箇所
- `_ART_HQ_STORES` … `_art_hq_scale_for()` の入口1箇所 ＋ `hq_scale=` 7箇所
  （⑦pipeline／⑦末尾／⑦⑤オススメ／⑧pipeline／⑧並び・列subprocess／⑧末尾／⑧⑤オススメ）

### ⑥ 通常ページ用ゲートは変更していない

```python
_PANEL_STORES    = {"新宿歌舞伎町"}                                              # 無変更
_GAP_FILL_STORES = {"新宿歌舞伎町", "上野新館", "上野本館", "新小岩", "秋葉原"}   # 無変更
```

**今回の変更は記事用ページ側の仕様である。**
通常結果ポスト用・スランプ付き結果ポスト用などの既存ゲートへ渋谷新館を追加したわけではない。
**今回を根拠に通常ページ側へ仕様を拡張しないこと。**

### ⑦ 液晶はめ込み条件（既存判定をそのまま利用）

渋谷新館の記事用でも**高田馬場と同じ既存判定**を利用する。
**新しい液晶判定ロジックは作っていない。**

```python
def _gap_fillable(n: int, cols: int) -> bool:
    """グラフ n 枚を cols 列で並べたとき、最終行の空きが2以上か（液晶をはめ込めるか）。"""
    rows = math.ceil(n / cols)
    return (cols * rows - n) >= 2
```

記事用は **3列固定**で判定する。既存の

`_gap_fillable()` ／ `_gap_screen_paths_for_bans()` ／ `_resolve_gap_screen()` ／
`_gap_sel_key()` ／ `_on_gap_screen_change()`

をそのまま利用する。

**「表＋スランプの空きが2コマ以上ある場合」という既存条件を変更しないこと。**
**1コマしか空いていない場合へ無理にはめ込まないこと。**

### ⑧ 液晶選択キーの正式仕様を維持

既存正式仕様 **`_gap_sel_key(store, bans, machine)`**（`4695044`）をそのまま使う。

- **機種名単位ではなく、掲載台番集合単位**の選択キー
  （`md5("店舗|機種|ソート済み台番")` の先頭12桁）
- 台番が異なる同一機種の画像は**個別に選択**できる
- 同じ掲載台番の縦版／横版等は**選択を共有**する

**今回の渋谷新館追加を理由に、液晶選択キーを店舗別の別実装にしたり、
機種名単位へ戻したりしないこと。**

session_state キーは既存の **`_art_gap_meta_{store}` / `_art_gap_base_{store}`** を使い、
通常ページの `_gap_meta_` / `_gap_base_` とは分離されたままである（店舗名入りのため衝突しない）。

### ⑨ パネル処理も既存処理を再利用

**渋谷新館専用のパネル描画関数は作っていない。**

`_apply_panel_to_table_img()` ／ `_build_panel_row()` ／ `_build_variety_panel_grid()` ／
`_art_is_multi_machine()` ／ `_narabi_panel_names()`

をそのまま利用する。**渋谷新館専用コピーを作らないこと。**

記事用は `crop_bar=False` で**元画像を一切 crop しない**（`0df63dd` の正式仕様）。
2×2パネルの表示順は**掲載機種の最小台番昇順**（`order_by_min_ban=not crop_bar`）。

### ⑩ `bd9fa40` のスランプ修正を維持

直前の正式修正
**`bd9fa40949cb9206d45b98ae5aa7a645c9554fb4`（`fix: 記事用プレビューのスランプ合成NameErrorを修正`）**
で採用した

```python
re.sub(r"^\d{2}_", "", _fn_pv2)   # ⑦記事用プレビュー
re.sub(r"^\d{2}_", "", _fn_u)     # 🔄その他を更新
re.sub(r"^\d{2}_", "", _fp_sl)    # ⑧本番（元から正常）
```

を**維持する**。**今回のパネル・液晶追加によってこの修正を巻き戻さないこと。**
`_bare_pv2` / `_bare_u` をスランプ側から再び参照する形へ戻すことも禁止。

渋谷新館は **パネルあり ＋ 液晶あり ＋ スランプあり** が正式仕様になった。

### ⑪ 高田馬場の非回帰

高田馬場の記事用は今回の変更前から

- パネル ／ 2×2パネル ／ スランプ ／ 白サマリー ／ 液晶はめ込み ／ 液晶選択UI ／
  **HQ 2倍** ／ 採番（①Excel ②ポスター ③個別 ④並び ⑤末尾 ⑥バラエティ ⑦プレビュー ⑧実行）

が正常だった。**今回もこれを完全維持する。**

**`_ART_HQ_STORES = {"高田馬場"}` は `148d672` 以前の `_ARTICLE_PANEL_STORES` と同一集合**なので、
`_art_hq_scale_for()` と7つの `hq_scale=` の戻り値は**高田馬場について数学的に不変**である。
**この分離により、高田馬場の HQ 2倍を維持したまま渋谷新館だけ 1.0倍にできる設計**になった。

### ⑫ 秋葉原の正式仕様

秋葉原の記事用は今回も

- **パネルなし ／ 液晶なし ／ 液晶選択UIなし ／ スランプあり ／ HQ 1.0倍**

を維持する。

**`_ARTICLE_PANEL_STORES` / `_ARTICLE_GAP_FILL_STORES` / `_ART_HQ_STORES` の
いずれにも秋葉原を追加しない。**
**今回の渋谷新館対応を秋葉原へ横展開しないこと。**

秋葉原へパネル・液晶を追加する場合は**別案件**として
**調査 → 原因・仕様確認 → 修正案 → ユーザー承認 → 実装** の順で行うこと。

### ⑬ 変更した関数と変更していない関数（`git show` で実測）

```
commit 148d672a9a04e67d33278a1d48568f10549a73cc
feat: 渋谷新館の記事用にパネルと液晶選択を追加

 streamlit_app.py | 25 +++++++++++++++----------
 1 file changed, 15 insertions(+), 10 deletions(-)
```

| 項目 | 実測値 |
|---|---|
| 変更ファイル | **`streamlit_app.py` のみ** |
| 変更量 | **+15 / −10（11ハンク）** |
| **新規関数** | **0**（消失関数も0） |
| **変更関数** | **`_art_hq_scale_for()` と `show_auto_article_page()` の2つのみ** |

いずれも**参照する定数名の差し替えだけ**で、ロジック本体は変えていない。

主な変更内容:

1. **`_ART_HQ_STORES = {"高田馬場"}` を新設**（`_ART_HQ_MIN_ROWS` の直後・説明コメント3行つき）
2. `_art_hq_scale_for()` の HQ 判定を `_ARTICLE_PANEL_STORES` → **`_ART_HQ_STORES`** へ
3. `show_auto_article_page()` 内の `hq_scale=` **7箇所**を **`_ART_HQ_STORES`** へ
4. `_ARTICLE_PANEL_STORES` へ **渋谷新館を追加**
5. `_ARTICLE_GAP_FILL_STORES` へ **渋谷新館を追加**

**パネル合成の3箇所（⑦／🔄／⑧）は `_ARTICLE_PANEL_STORES` を参照したまま**である。

### ⑭ 変更禁止・非回帰対象

`148d672` で**バイト一致（本体無変更）を機械確認済み**：

`_apply_panel_to_table_img()` ／ `_build_panel_row()` ／ `_build_variety_panel_grid()` ／
`_gap_sel_key()` ／ `_gap_fillable()` ／ `_gap_screen_paths_for_bans()` ／
`_resolve_gap_screen()` ／ `_on_gap_screen_change()` ／ `_attach_slump_to_table()` ／
`show_auto_page()` ／ `_composite_slump_onto_images()` ／ `run_auto_pipeline()` ／
`generate_report_text()`

**今後この仕様を理由に上記を無断変更しないこと。**

加えて次も今回の対象外（無変更）:

抽出条件 ／ 全台系 ／ 高配分 ／ 並び ／ 列仕掛け ／ ジャグラー ／ その他優秀台 ／
⑤オススメ ／ ②個別画像 ／ ⑦プレビューOFFの非widget正本（`00a472a` / `_pv_is_on()`）／
新小岩⑤ジャグラー正本（`1301431`）／ 青タイトルバー長文縮小（`2959b99`）／
結果テキスト ／ WordPress（`wp_client.py` 無変更）／ 記事用採番。

### ⑮ 正式commit

```
commit ID   : 148d672a9a04e67d33278a1d48568f10549a73cc
メッセージ  : feat: 渋谷新館の記事用にパネルと液晶選択を追加
変更ファイル: streamlit_app.py のみ
変更量      : 25 lines changed / 15 insertions(+) / 10 deletions(-)
push        : 通常push・fast-forward（5da4667..148d672）・force pushなし
```

**関連履歴（新しい順）**

```
148d672  feat: 渋谷新館の記事用にパネルと液晶選択を追加        ← 現在の正式仕様
5da4667  docs: 記事用スランプ合成のパネル非対象店舗仕様を記録   ← 当時の正式仕様（変更しない）
bd9fa40  fix: 記事用プレビューのスランプ合成NameErrorを修正
```

### ⑯ 実機確認結果（2026-09-03・ローカル・正式HEAD `148d672`）

**渋谷新館／記事用／2026/9/2／確定データ 433台**で⑦プレビュー26枚を生成し確認した。

**パネル**
- 単一機種パネル：L攻殻機動隊／とある禁書目録2／ゴッドイーター／戦国乙女5／
  モンハンライズ／ネオアイム 等すべて表の上に正常表示
- **ジャグラーシリーズ優秀台の 2×2 パネル**（HAPPY JUGGLER／Funky JUGGLER／
  GOGO JUGGLER／JUGGLER GIRLS）
- **その他の優秀台ピックアップの 2×2 パネル**（ヴァルヴレイヴ2／北斗の拳／SAO／GOD）
- **並び画像のパネル**（戦国乙女5(4台並び)／ゴッド神々の軌跡(3台並び) 等）
- `差枚数ランキング.jpg` はパネルなし（ban_map 対象外＝仕様どおり）

**液晶はめ込み（空き2コマ以上の画像に入る）**

| 画像 | 台数 | 空き | 液晶 |
|---|---|---|---|
| L攻殻機動隊_高配分 | 4 | 2 | **あり** |
| 戦国乙女5_高配分 | 10 | 2 | **あり** |
| 東京喰種_高配分 | 16 | 2 | **あり** |
| その他の優秀台ピックアップ | 28 | 2 | **あり**（代表機種 SAOII） |
| 戦国乙女5(4台並び) | 4 | 2 | **あり** |

**空き2コマ未満には入らない**（`_gap_fillable(n,3)` の理論値と完全一致）:
とある禁書目録2(6台→空0)／ネオアイム(12→0)／マイジャグV(18→0)／ジャグラー統合(15→0)／
ゴッドイーター(2→1)／モンハンライズ(2→1)／かぐや様(2→1)／カバネリ(8→1)／
並び 2台・3台・5台（空1／空0／空1）。

**液晶選択UI**
- `🖼️ 液晶画像を選ぶ（機種名）` expander が上記5画像に表示
- 展開すると `液晶1 / 液晶2 / 液晶3 / はめ込まない` のラジオ＋サムネイルが
  高田馬場と同じ形式で表示
- **液晶1 → 液晶2 へ変更 → プレビュー画像が即座に差し替わる**
- **「はめ込まない」→ 液晶が消える**
- **再び液晶3を選ぶと復活する（永久OFFにならない）**
- **🔄「その他を更新」後も選択（液晶3）が維持される**

**スランプ**：26枚すべてで従来どおり表示（`bd9fa40` の非回帰）。

**高田馬場の非回帰（344台・⑦プレビュー9枚）**：パネル（DISC UP ULTRA REMIX／喰霊零Re／
真打吉宗）・白サマリー・スランプ・液晶選択UI（`🖼️ 液晶画像を選ぶ（ファンキー2）`＝
ジャグラー統合25台→空き2）・採番①〜⑧すべて従来どおり。

**純粋テスト**：`_art_hq_scale_for()` を **9種のファイル名 × 12種の台数＝108ケース**で検証し、
**高田馬場は導入前後で不一致0**、**渋谷新館・秋葉原は全ケース 1.0**。

### ⑰ 確認状況の正確な記録（誤記しないこと）

- **秋葉原は実機確認していない。**コードレベル（定数への非追加と108ケースの HQ 判定）で
  確認したものである。**「秋葉原も実機確認済み」と書かない。**
- **⑧本番は実行していない。**記事用⑧には `_git_auto_push()` があり、
  `article_page_inputs.json` に既存差分があるため、無関係な差分を自動 commit / push する
  危険を避けて意図的に実行していない。⑦プレビューと🔄までで確認した。
  **WordPress 通信は0件。**

### ⑱ 今後の禁止事項

1. **`5da4667` の既存記録を削除・書き換えない**
2. **「`5da4667` が誤りだった」と扱わない**（当時は正しい正式仕様）
3. **現在の正式仕様は `148d672` で上書きされたものとして扱う**
4. **`_ARTICLE_PANEL_STORES` と `_ART_HQ_STORES` を再び同一視しない**
5. **渋谷新館を HQ 2倍（`_ART_HQ_STORES`）へ勝手に追加しない**
6. **秋葉原へパネル・液晶を勝手に追加しない**
7. **通常ページの `_PANEL_STORES` / `_GAP_FILL_STORES` へ今回を根拠に追加しない**
8. **液晶判定ロジックを渋谷新館専用に複製しない**
9. **パネル処理を渋谷新館専用に複製しない**
10. **`_gap_sel_key()` を機種名単位へ戻さない**
11. **「2コマ以上」という液晶条件を勝手に変更しない**
12. **`bd9fa40` のスランプ修正を巻き戻さない**
13. **高田馬場の HQ 2倍を壊さない**
14. **今回を理由に pipeline・抽出・結果テキストを変更しない**
15. **無関係なリファクタ・未使用コード整理をしない**
16. **CLAUDE.md の既存節を圧縮・統合・削除しない**

## 渋谷新館 記事用：実行見出しを「⑦ 実行」・HQ 2倍を正式採用（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の📰記事用ページだけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館の記事用実行表示とHQ生成を更新`・2026-09-04・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**・`streamlit_app.py` は**2ハンク**）。

### ⓪ `148d672` から上書きされた点（履歴を消さないこと）

| | 旧（`148d672`・当時の正式仕様） | **新（2026-09-04・現在の正式仕様）** |
|---|---|---|
| 渋谷新館の記事用HQ | **HQ2倍の対象にしない**（`_ART_HQ_STORES = {"高田馬場"}`） | **HQ2倍の対象にする**（`_ART_HQ_STORES = {"高田馬場", "渋谷新館"}`） |
| 実行の見出し | `### ▶▶ 自動処理を開始`（番号外） | **`### ⑦ 実行`** |

**「渋谷新館 記事用ページ：パネル・液晶はめ込み・液晶選択UIを正式追加（2026-09-03 確定・`148d672`）」
の節は削除・書き換えしない。**同節の禁止事項⑤
「渋谷新館を HQ 2倍（`_ART_HQ_STORES`）へ勝手に追加しない」は
**`148d672` 時点の正式仕様として正しい記録**であり、
**本節（2026-09-04）でユーザー承認のうえ正式に変更された**という履歴として残す。
`148d672` のパネル・液晶・`_ARTICLE_GAP_FILL_STORES`・`_gap_sel_key` 等の仕様は
**すべてそのまま有効**である。

### ① 実行見出しは全店舗共通で「{丸数字} 実行」

```python
# 旧: st.markdown("### ▶▶ 自動処理を開始" if _art_v2 else f"### {_sec_num()} 実行")
st.markdown(f"### {_sec_num()} 実行")
```

- **`_art_v2`（＝渋谷新館）だけ見出しを別文言にする条件式は廃止**した。
- 番号は既存の **`_sec_num()` のカウンタ方式**で決まる。**手書きしない。**
  表示されないセクションがあれば自動で前詰めされる。
- **プレビューは従来どおり番号外**（`### 🔍 プレビュー` のまま）。

| 店舗 | `_art_v2` | 消費するセクション | 実行の見出し |
|---|---|---|---|
| **渋谷新館** | True | ①冒頭 ②高配分 ③並び ④末尾 ⑤オススメ ⑥ランキング＆島図 | **⑦ 実行** |
| 高田馬場 | False | ①Excel ②ポスター ③個別 ④並び ⑤末尾 ⑥バラエティ ⑦プレビュー | **⑧ 実行**（不変） |
| 秋葉原 | False | 同上 | **⑧ 実行**（不変） |

### ② 実行ボタン本体のラベルは変更しない

**`st.button("▶▶ 自動処理を開始", key="art_run", ...)` は共通UIなので今回変更していない。**
高田馬場・秋葉原と共用のため、**渋谷新館のためにボタンラベルを書き換えてはならない。**
変えたのは**見出し（`st.markdown`）1行だけ**である。

### ③ `_ART_HQ_STORES` へ渋谷新館を追加（最小修正）

```python
_ART_HQ_STORES = {"高田馬場", "渋谷新館"}
```

- **高田馬場用のHQ処理をコピーして渋谷新館専用の別処理を作らない。**
  **店舗追加はこの集合への追記だけで行う。**
- **`_ART_HQ_SCALE = 2.0` / `_ART_HQ_MIN_ROWS = 10` / `_ART_HQ_TARGET_KB = 5500` /
  `_ART_HQ_FNS` / `_art_hq_scale_for()` / `_pipeline_hq()` / `_save_jpeg()` は無変更。**

| 店舗 | HQ 2.0x |
|---|---|
| **高田馬場** | **対象** |
| **渋谷新館** | **対象（今回追加）** |
| 秋葉原 | **対象外** |

判定は既存のまま：

* **固定2画像**（`その他の優秀台ピックアップ.jpg` / `ジャグラーシリーズ優秀台.jpg`）→ **2.0倍**
* それ以外 → **掲載台10台以上で 2.0倍 ／ 10台未満は 1.0倍**（画像種別は問わない）
* **最初から2倍解像度で描画する**（出来上がりを resize で拡大しない）

### ④ gate は3つのまま分離を維持する（一本化禁止）

| 定数 | 役割 | 現在値 |
|---|---|---|
| `_ARTICLE_PANEL_STORES` | 記事用のパネル合成 | `{"高田馬場", "渋谷新館"}` |
| `_ARTICLE_GAP_FILL_STORES` | 記事用の液晶はめ込み・液晶選択UI | `{"高田馬場", "渋谷新館"}` |
| `_ART_HQ_STORES` | 記事用のHQ 2倍描画 | `{"高田馬場", "渋谷新館"}` |

現時点で3つとも同じ集合になったが、**意味が違うので統合してはならない。**
パネル・液晶は倍率に依存せず、HQはWordPress送信・Cloudメモリの都合で
将来また分かれ得る（`148d672` の分離理由をそのまま維持する）。

### ⑤ HQ対象外（独自解像度の画像）

**`hq_scale` 引数を持たない画像は今回の集合の影響を受けない。**

| 画像 | 関数 | hq_scale |
|---|---|---|
| **差枚数ランキング.jpg** | `_art_ranking_image(df, diff_raw, limit, scale)` | **引数なし＝HQ対象外** |
| **島図.jpg** | `shimazu_renderer.render(df, store)` | **引数なし＝HQ対象外** |

- **島図は 3451 × 6490 を維持する。2倍化しない。**
- **`bceda28`（島図の右端黒帯104px削除／`range.c1` 106→77）を完全維持する。**
- 今回 **`shimazu_renderer.py` と `masters/shimazu_渋谷新館.json` には触れていない。**
- 差枚数ランキングは **1093px幅のまま**（50位で 1093×2319）。

### ⑥ 実測（渋谷新館 2026/9/2 確定データ 433台・同一Excelで hq=1.0 と 2.0 を実行）

| ファイル | 修正前 | KB | 修正後 | KB |
|---|---|---|---|---|
| その他の優秀台ピックアップ.jpg | 1083×1496 | 668 | **2160×2992** | 1801 |
| ジャグラーシリーズ優秀台.jpg | 993×792 | 329 | **1985×1584** | 893 |
| マイジャグV_高配分.jpg（18台） | 993×880 | 246 | **1985×1760** | 1000 |
| 東京喰種_高配分.jpg（16台） | 994×792 | 249 | **1986×1584** | 888 |
| ネオアイム_高配分.jpg（12台） | 992×616 | 255 | **1979×1232** | 679 |
| 戦国乙女5_高配分.jpg（10台） | 994×528 | 222 | **1984×1056** | 591 |
| 10台未満の高配分6枚 | 992〜1081×… | 81〜203 | **バイト完全一致（MD5一致）** | 同 |
| 差枚数ランキング.jpg | 1093×2319 | — | **1093×2319（不変）** | — |
| 島図.jpg | 3451×6490 | — | **3451×6490（不変）** | — |

**2倍画像を1/2へ縮小して1倍版と比較したところ、サイズ完全一致・画素差の中央値0。**
＝レイアウト・表内容・行数・列数・台番・機種名・差枚・色・フォントは不変で、
差はネイティブ2倍描画によるアンチエイリアスのみ。

JPEG設定（`_save_jpeg`）は無変更：**quality 1〜95 のバイナリサーチ ／ `subsampling=0`（4:4:4）
／ `optimize` 不使用**。非HQは target 250KB、HQは target 5500KB（実際は q95 上限で頭打ち）。
並び・列（`convert_narabi_pil.py`）はHQ時 target 1200KB（無変更）。

### ⑦ 実機確認（2026-09-04・ローカル・渋谷新館 記事用 9/2 ⑦プレビュー14枚）

UI に **`🔍 プレビュー` → `⑦ 実行` → ボタン `▶▶ 自動処理を開始`** と表示されることを確認。
①〜⑥の採番も従来どおり。高田馬場・秋葉原は **⑧ 実行** のまま。

パネル合成（単機種／ジャグラー統合・その他の2×2）・スランプ合成・
液晶はめ込み・液晶選択UI（`🖼️ 液晶画像を選ぶ（…）`）はいずれも正常。
島図は 433/433 突合・色階級（+1,000=42 / +2,000=22 / +3,000=18 / +5,000=16 /
+10,000=5 / 色なし=330・合計433）とも `bceda28` 時点と一致。

**⑧本番は未実行**（`_git_auto_push()` を避けるため）。**WordPress 通信0件／Cloud Reboot 未実施。**

### ⑧ 非回帰（本体バイト一致を機械確認）

`show_auto_page`（通常ページ全域）／`run_auto_pipeline`／`run_step1_main`／
`run_step2_juggler`／`run_step3_other`／`_art_hq_scale_for`／`_pipeline_hq`／`_save_jpeg`／
`_build_machine_img`／`_build_machine_img_no_bar`／`_art_high_title_bar`／
`_build_article_machine_img`／`_apply_panel_to_table_img`／`_attach_slump_to_table`／
`_build_sue_images`／`_art_ranking_image`／`_patch_and_run_narabi`／`_build_panel_row`／
`_gap_fillable`／`_gap_sel_key` — **すべて一致**。新規関数・消失関数**0**。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は無変更。**

### ⑨ 高配分500KB化は未実装（今後の別案件）

今回 **`_ART_HQ_HIGH_TARGET_KB` 等の追加はしていない。**
調査結果として、HQ化後の高配分2倍画像は **591KB〜1000KB程度**である。

将来 500KB前後へ収める場合の**第一候補**は
**「2倍解像度を維持したまま JPEG 圧縮率だけで 500KB へ収束させる」**方式。
`_save_jpeg()` が既に目標サイズへのバイナリサーチを持つため、最小変更は

* 定数 `_ART_HQ_HIGH_TARGET_KB = 500` を1つ追加
* `{機種名}_高配分.jpg` を保存している**2箇所だけ**
  （`run_step2_juggler` / `run_step3_other`）の `target_kb` を差し替え

で足りる。記事用②の手動高配分 `{機種名}（優秀台）.jpg` も揃えるなら
`show_auto_article_page` の⑧側も同じ定数にする。
**quality 固定化・解像度を下げる方式は採らない**（画像ごとにサイズが暴れる／目的と逆行）。
**別案件として調査→承認のうえ実装すること。**

### ⑩ 今後の禁止事項

1. **`148d672` の節を削除・書き換えない**（当時の正式仕様として履歴を残す）
2. **渋谷新館を `_ART_HQ_STORES` から外さない**
3. **秋葉原を `_ART_HQ_STORES` へ勝手に追加しない**
4. **`_ARTICLE_PANEL_STORES` / `_ARTICLE_GAP_FILL_STORES` / `_ART_HQ_STORES` を一本化しない**
5. **高田馬場のHQ処理を渋谷新館専用に複製しない**
6. **差枚数ランキング・島図をHQ対象へ入れない／2倍化しない**
7. **島図の 3451×6490 と `bceda28` の右端黒帯削除を巻き戻さない**
8. **実行見出しの番号を手書きしない**（`_sec_num()` のカウンタ方式を維持）
9. **実行ボタンのラベル `▶▶ 自動処理を開始` を渋谷新館のために書き換えない**
10. **`_ART_HQ_SCALE` / `_ART_HQ_MIN_ROWS` / `_ART_HQ_TARGET_KB` / `_save_jpeg` を今回の理由で変更しない**
11. **高配分500KB化を承認なしに実装しない**
12. **今回を理由に pipeline・抽出条件・判定・結果テキスト・WordPress を変更しない**
13. **無関係なリファクタ・未使用コード整理をしない**

## 記事用：全台系・高配分のHQ化と渋谷新館 島図のJPEG品質（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**記事用ページを持つ3店舗（高田馬場・渋谷新館・秋葉原）の
記事用ページだけ**。正式コード commit は本節と**同一の commit**
（`feat: 記事用の全台系高配分と島図の画質を改善`・2026-09-04・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**目的は容量削減ではなく「WordPress 掲載時に鮮明に見えること」**である。

### ⓪ 記事用ページ対象店舗（コードから確定）

`show_image_type_page()` で `📰 記事用`（`key="auto_article_btn"` → `_navigate("auto_article")`）
を出すのは **高田馬場・渋谷新館・秋葉原の3店舗だけ**。
**店舗名を記憶で決め打ちせず、必ずこの3か所のボタン定義から確認すること。**

---

## A. 記事用「全台系・高配分」を掲載台数に関係なくネイティブ2.0x

### ① 荒く見えていた原因（WordPress 側ではない）

`wp_client.py` をコードで確認した結果:

| 項目 | 実態 |
|---|---|
| アップロード時 resize | **なし**（`upload_media()` はファイルをそのまま送信） |
| JPEG 再圧縮 | **なし**（縦長画像の分割のみ。crop だけでリサイズしない） |
| 本文が使う画像 | **`sizeSlug:"full"` ＋ `source_url`＝原寸URL**（`blk_image()`）。thumbnail / medium / large は**使っていない** |
| サイト側の縮小 | **長辺 2560px 超だけを 2560px へ縮小**（`WP_MAX_SIDE = 2560`） |

**→ WordPress 側で縮小も再圧縮もしていない。**
原因は**元画像が 1.0倍（約993px幅）で生成されていたこと**。
掲載台が `_ART_HQ_MIN_ROWS`(10) 未満の全台系・高配分は 1.0倍のままだった。
2倍描画（約1985px幅）は長辺2560未満なので**サイト側で縮小されずそのまま掲載される**。

### ② 正式仕様

**記事用の「全台系」「高配分」だけ、掲載台数に関係なくネイティブ 2.0倍で描画する。**
**2台・4台・6台・8台・10台以上のすべてで 2.0倍。**

```python
# 記事用ページを持つ店舗（記事用の全台系・高配分を高解像度で描く対象）
_ART_ZH_HQ_STORES = frozenset({"高田馬場", "渋谷新館", "秋葉原"})

def _art_zh_hq(store) -> float          # 対象店舗なら _ART_HQ_SCALE(2.0)、他は 1.0
def _pipeline_zh_hq(zh_hq_scale, hq_scale, n_rows) -> float
def _art_zh_fn_set(zen_dai_list, kojin_zentai_machines) -> set
```

- pipeline に **`zh_hq_scale: float = 1.0`（既定＝従来動作）** を追加し、
  `run_auto_pipeline` → `run_step1_main` / `run_step2_juggler` / `run_step3_other` へ通す。
- 記事用の⑦プレビュー・⑧本番が **`zh_hq_scale=_art_zh_hq(store)`** を渡す。
- **`_pipeline_zh_hq()` は zh_hq_scale>1 のとき掲載台数を見ない。
  既定(1.0)なら従来どおり `_pipeline_hq()` の10台判定へフォールバックする。**
- ②個別画像「全台」も同じ 2.0倍へ揃え、既定250KB保存を `_ART_HQ_TARGET_KB` へ切替。

### ③ ★合成側の倍率を描画側と必ず一致させる

スランプ結合 `_attach_slump_to_table(hq_scale=...)` の倍率が描画側とズレると
**スランプ・余白の比率が壊れる**。そのため `_art_hq_scale_for()` にも同じ判定を入れた。

```python
def _art_hq_scale_for(bare_fn, store, n_rows=0, zh_fns=frozenset()):
    if store in _ART_ZH_HQ_STORES and (bare_fn.endswith("_高配分.jpg") or bare_fn in zh_fns):
        return _ART_HQ_SCALE
    ...  # 以降は従来どおり
```

- **高配分は `_高配分.jpg` の接尾辞**で一意に判別できる。
- **全台系はファイル名が `{機種名}.jpg` で判別できない**ため、
  `_art_zh_fn_set()` が `result["zen_dai_list"]` と②個別「全台」の入力機種名から
  ファイル名集合を作り、**`st.session_state[f"_art_zh_fns_{store}"]`** で
  ⑦プレビュー・🔄その他を更新・⑧本番の**3つの合成ループへ共有**する。
  ⑦は `f"{機種名}.jpg"`、⑧は `_make_safe_fn()` 経由なので**両方の名前を入れる**。
- **「マーカーが無いファイル名は全台系」といった推測判定にしない**
  （②個別ピック・末尾・バラエティ・並び・列を巻き込むため）。

### ④ ★既存HQ仕様を巻き込まない（gate を一本化しない）

| 定数 | 役割 | 値 |
|---|---|---|
| `_ART_HQ_STORES` | 記事用の**既存HQ**（固定2画像は2.0x／それ以外は**10台以上で2.0x**） | **`{"高田馬場", "渋谷新館"}`（変更なし）** |
| **`_ART_ZH_HQ_STORES`** | **記事用の全台系・高配分だけ 台数無関係に 2.0x** | **`{"高田馬場", "渋谷新館", "秋葉原"}`** |

**この2つを統合してはならない。**
**秋葉原は全台系・高配分だけ 2.0x** であり、
**ジャグラーシリーズ優秀台・その他の優秀台ピックアップ・並び・列・末尾・バラエティ・
⑤オススメは従来どおり 1.0x のまま**である。
**秋葉原を `_ART_HQ_STORES` へ追加してはならない。**

実測した gate マトリクス（`_art_hq_scale_for` の戻り値）:

| store | 高配分(2台) | 全台系(2台) | ジャグ統合 | 末尾(2台) | 固定2画像 |
|---|---|---|---|---|---|
| 高田馬場 | **2.0** | **2.0** | 2.0 | 1.0 | 2.0 |
| 渋谷新館 | **2.0** | **2.0** | 2.0 | 1.0 | 2.0 |
| **秋葉原** | **2.0** | **2.0** | **1.0** | **1.0** | **1.0** |
| 通常ページの店舗 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### ⑤ 500KB は正式値として採用しない

**「500KB固定」「500KB上限」をコードへ入れてはならない。**

- `_save_jpeg()` は **quality 1〜95 のバイナリサーチ ／ `subsampling=0`（4:4:4）／
  `optimize` 不使用**。**quality の上限が 95** なので、
  2倍描画した全台系・高配分は q95 でも自然に **約200KB〜1000KB** に収まる。
  「500KBまで容量を使って画質を上げる」余地は**存在しない**（既に最高品質）。
- **既に500KBを超えている画像を500KBへ再圧縮する処理を追加しない**
  （マイジャグV 1000KB・戦国乙女5 959KB・東京喰種 888KB 等は**そのまま**）。
- 画像内容によって 200 / 300 / 400 / 500 / 600 / 900 / 1000KB と変動する状態を**許容する**。
- **`_save_jpeg()` を複製した新しいJPEG保存関数を作らない。**

### ⑥ 後から resize する方式は禁止

**完成画像を `resize` で2倍にしてはならない。**
既存の描画 pipeline へ HQ 倍率を渡し、**文字・表・罫線・スランプ・パネル・液晶を
最初から2倍スケールで描く**方式のみを正式とする。

ネイティブ描画であることの実測根拠:

- **幅が正確な2倍にならない**（995→1983／2×=1990、1081→2154／2×=2162）。
  列幅がフォント実測から**再レイアウト**されている。
- **中間調（40〜215）の画素割合が一貫して低い**
  （2x実描画 19.96% ／ 1xをLANCZOSで2倍拡大 26.01%）＝エッジがぼけていない。
- 2x を50%へ縮小すると **1x とサイズ完全一致・画素差の中央値0**（レイアウト不変）。

### ⑦ 実測（2026/9/2 実データ・3店舗）

| 店舗 | ファイル | 台数 | 修正前 | KB | 修正後 | KB |
|---|---|---|---|---|---|---|
| 渋谷新館 | かぐや様_高配分 | 2 | 1081×176 | 82 | **2154×352** | **206** |
| 渋谷新館 | ゴッドイーター_高配分 | 2 | 992×176 | 81 | **1979×352** | **203** |
| 渋谷新館 | L攻殻機動隊_高配分 | 4 | 995×264 | 120 | **1983×528** | **318** |
| 渋谷新館 | とある禁書目録2_高配分 | 6 | 993×352 | 159 | **1986×704** | **422** |
| 渋谷新館 | カバネリ海門決戦_高配分 | 8 | 993×440 | 203 | **1980×880** | **543** |
| 渋谷新館 | ネオアイム／マイジャグV／戦国乙女5／東京喰種 | 10〜18 | — | 591〜1000 | **変化なし** | 同 |
| 高田馬場 | 喰霊零Re（**全台系**） | — | 991×342 | 95 | **1980×678** | **252** |
| 高田馬場 | ディスクアップUR（**全台系**） | — | 995×342 | 102 | **1983×678** | **265** |
| 秋葉原 | ゾンビランドサガ（**全台系**） | — | 993×342 | 98 | **1985×678** | **259** |
| 秋葉原 | 戦国乙女5_高配分 | — | 992×836 | 255 | **1980×1672** | **959** |
| 全店舗 | ジャグラーシリーズ優秀台／その他の優秀台 | — | — | — | **完全に不変** | 同 |

**実UI確認（渋谷新館 9/2・⑦プレビュー14枚）**: `L攻殻機動隊`(4台)・`とある禁書目録2`(6台)・
`ゴッドイーター`(2台) いずれも **パネル＋青バー＋表＋スランプ＋液晶はめ込み**が正常で、
**修正前後の縦横比が完全一致**（例 968/992=0.9758 → 1425/1460=0.976）＝
描画側と合成側の倍率が一致している。

### ⑧ 通常ページは対象外（非回帰を実測）

- **通常ページのパイプライン出力が HEAD版と MD5 完全一致**
  （新小岩10枚／西武新宿4枚／渋谷新館12枚＝**26枚すべて一致・不一致0**。
  `BASE_DIR` がずれると機種名変換・`store_settings` を読めず結果が変わるため、
  **HEAD版は同一ディレクトリへ一時配置して比較**した）。
- `show_auto_page` ／ `_save_jpeg` ／ `_pipeline_hq`（本体）／ `_build_machine_img_no_bar` ／
  `_art_high_title_bar` ／ `_build_article_machine_img` ／ `_apply_panel_to_table_img` ／
  `_attach_slump_to_table` ／ `_build_sue_images` ／ `_art_ranking_image` ／
  `_patch_and_run_narabi` ／ `_build_panel_row` ／ `_gap_sel_key` ／ `_art_osusume_images`
  — **すべてバイト一致**。
- **`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は無変更。**

---

## B. 渋谷新館 島図の JPEG 品質（解像度は上げない）

### ⑨ 荒く見えていた原因＝**quality=1 まで潰れていた**

⑧の保存が **`_save_jpeg(_sz_img_e, _sz_out_e)`＝既定 `target_kb=250`** だった。
島図は **3451×6490＝約22.4Mpx**。250KB は **0.011 B/画素**で、
**q=1 でも約870KB** あるため到達不能 → バイナリサーチが **q=1** を選んでいた。

```
バイナリサーチ経路 (q, KB): [(48,1858),(24,1479),(12,1197),(6,1002),(3,888),(1,870),(0,870)…]
★ 実際に選ばれる quality = 1     PSNR 24.9dB / 平均画素差 4.902
```

**解像度不足ではない**（台番セル1つが約127×59px ある）。
⑦プレビューは PIL のままなので綺麗で、**⑧の保存物だけが荒かった**。

### ⑩ 正式仕様

**島図の解像度は上げない。3451 × 6490 を維持する。**
**`shimazu_renderer.py` と `masters/shimazu_渋谷新館.json` は変更しない。**
**島図を resize する処理を追加しない。**

```python
_ART_SHIMAZU_TARGET_KB = 3000        # 島図専用
_save_jpeg(_sz_img_e, _sz_out_e, target_kb=_ART_SHIMAZU_TARGET_KB)
```

| | pixel size | KB | quality | PSNR |
|---|---|---|---|---|
| **修正前** | 3451×6490 | **871** | **1** | **24.9dB** |
| **修正後** | **3451×6490（不変）** | **約2983** | **約88** | **44.1dB** |

**4000KB / q95 は採用しない。3000KB を正式値とする。**
**全台系・高配分の目安（500KB）と島図の 3000KB を混同しない。**

### ⑪ 島図の維持確認（渋谷新館 2026-09-02・433台）

**3451×6490 ／ 433/433 ／ missing 0 ／
+1,000=42 ／ +2,000=22 ／ +3,000=18 ／ +5,000=16 ／ +10,000=5 ／ 色なし=330（合計433）／
右端黒帯104px削除（`bceda28`）維持 ／ WRAP_OVERRIDE ／ X_ADJ=1.163 ／ フォント ／ 改行 ／
凡例 ／ 設備 ／ 2F/3F ／ gradient ／ レインボー ／ 台番座標** — **すべて維持**。

### ⑫ WordPress 手貼り時の長辺2560px縮小は**未解決**（別案件）

島図は **`wp_client` の payload に入っていない**（WordPress連携は `store == "高田馬場"` 限定）。
手貼りすると**サイト側の長辺2560px制限**で **3451×6490 → 約1361×2560** へ縮小される。
**幅3451px自体が2560を超えるため、画像側の品質改善だけでは解決しない。**

**今回は修正していない。今回勝手に分割処理を追加してはならない。**
今後「島図をWordPress掲載用に分割する」方法を**別案件**として検討する。

---

### ⑬ 今後の禁止事項

1. **`_ART_ZH_HQ_STORES` と `_ART_HQ_STORES` を統合しない**（役割が違う）
2. **秋葉原を `_ART_HQ_STORES` へ追加しない**（全台系・高配分だけが2.0x）
3. **ジャグラー統合／その他の優秀台／並び／列／末尾／バラエティ／⑤オススメの
   既存HQ仕様（10台判定・固定2画像）を変更しない**
4. **通常ページへ zh_hq_scale を渡さない**（既定 1.0 のまま＝出力不変）
5. **`zh_hq_scale` の既定値を 1.0 以外にしない**（通常ページの非回帰が壊れる）
6. **合成側 `_art_hq_scale_for()` の `zh_fns` を渡し忘れない**
   （描画2.0x・合成1.0x になるとスランプと余白の比率が壊れる）
7. **全台系を「マーカーが無いファイル名」で推測判定しない**
8. **500KB を固定値・上限としてコードへ入れない／`_save_jpeg` を複製しない**
9. **完成画像を resize で2倍にしない**（最初から2倍で描く）
10. **島図の解像度を上げない／resize しない／`shimazu_renderer.py`・座標マスタを変更しない**
11. **島図の `_ART_SHIMAZU_TARGET_KB` を 250 へ戻さない／全台系・高配分の値と混同しない**
12. **`bceda28` の右端黒帯104px削除を巻き戻さない**
13. **島図のWordPress用分割を承認なしに実装しない**
14. **`wp_client.py` の `sizeSlug:"full"` / `source_url` / `WP_MAX_SIDE=2560` を変更しない**
15. **今回を理由に抽出条件・全台系判定・高配分判定・Pision取得・機種名変換・
    パネル選択・液晶選択・スランプ抽出・並び／末尾／ジャグラー／その他／オススメ判定を変更しない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 記事用：並び・列画像のHQ化（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**記事用ページを持つ3店舗
（高田馬場・渋谷新館・秋葉原）の記事用ページの「並び」「列」だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 記事用の並び列画像をHQ化`・2026-09-04・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**`convert_narabi_pil.py` は無変更。**
直前の `e1b5835`（記事用の全台系・高配分HQ化と島図のJPEG品質）は**すべて維持**する。

### ① 修正前に低解像度だった原因（推測ではなくコードと実測で確定）

**⑦プレビューと⑧本番で描画エンジンが違うが、倍率判定のルールは同じ
「10台以上のときだけ2倍」＋「店舗 gate」だった。**

| 経路 | 描画 | 倍率判定 |
|---|---|---|
| **⑦プレビュー** | `show_auto_article_page()` 内で**アプリ内直接描画**（`_build_machine_img(..., no_bar=True, hq_scale=…)`） | `_art_hq_scale_for()` → **10台未満は 1.0x**／**秋葉原は `_ART_HQ_STORES` 外で常に 1.0x** |
| **⑧本番** | **`convert_narabi_pil.py` を subprocess 実行**（`_patch_and_run_narabi()`） | script の `_hq_run = HQ_SCALE if (HQ_SCALE > 1.0 and len(group) >= HQ_MIN_ROWS) else 1.0`・**`HQ_MIN_ROWS = 10`**／**秋葉原は `HQ_SCALE` 自体が 1.0** |

実データの並びは **2〜6台が大半**なので、ほぼすべてが
**約993〜1122px幅の 1.0x 画像**のままだった。
**列画像も並びと同じ `_JOBS` ループ／同じ `_build_machine_img` を使うため、まったく同じ原因**である。
`e1b5835` で全台系・高配分の台数判定を外した `zh_hq_scale` は pipeline 側の仕組みで、
**並び・列はこの経路を通らない**ため取り残されていた。

### ② 正式仕様

**記事用の「並び」「列」だけ、掲載台数に関係なくネイティブ 2.0倍で描画する。**
**2台・3台・4台・5台・6台・8台・9台・10台以上のすべてで 2.0倍。**

```python
# 記事用ページを持つ3店舗（記事用の並び・列を高解像度で描く対象）
_ART_NARABI_HQ_STORES = frozenset({"高田馬場", "渋谷新館", "秋葉原"})

# subprocess 側の HQ_MIN_ROWS を上書きする値。1＝台数を見ない。
_ART_NARABI_HQ_MIN_ROWS = 1

_ART_NARABI_FN_RE  = re.compile(r"\(\d+台並び\)")
_ART_RETSU_FN_MARK = "(列仕掛け)"

def _art_is_narabi_fn(bare_fn) -> bool   # 並び・列のファイル名判定
def _art_narabi_hq(store) -> float       # 対象店舗なら _ART_HQ_SCALE(2.0)、他は 1.0
```

### ③ ★3種類のHQ gate は役割が違う。今後も統合しない

| 定数 | 役割 | 値 |
|---|---|---|
| `_ART_HQ_STORES` | 記事用の**従来の一般的なHQ**（固定2画像は2.0x／それ以外は**10台以上で2.0x**） | **`{"高田馬場", "渋谷新館"}`（変更なし）** |
| `_ART_ZH_HQ_STORES` | 記事用**「全台系・高配分」専用**（台数無関係2.0x・`e1b5835`） | **`{"高田馬場", "渋谷新館", "秋葉原"}`（変更なし）** |
| **`_ART_NARABI_HQ_STORES`** | **記事用「並び・列」専用**（台数無関係2.0x） | **`{"高田馬場", "渋谷新館", "秋葉原"}`** |

**`_ART_HQ_STORES` と `_ART_ZH_HQ_STORES` の意味・値を今回変更していない。**
**秋葉原を `_ART_HQ_STORES` へ追加してはならない。**
秋葉原は**全台系・高配分（`e1b5835`）と並び・列（本節）だけ**が 2.0x で、
**ジャグラーシリーズ優秀台・その他の優秀台・末尾・バラエティ・⑤オススメ・
差枚数ランキング・島図は従来どおり 1.0x** のままである。

### ④ ⑦プレビュー（アプリ内直接描画）

```python
# ③ 列画像
hq_scale=_art_narabi_hq(store)
# ③ 並び画像
hq_scale=_art_narabi_hq(store)
```

**`_art_hq_scale_for(fn, store, len(group))` から `_art_narabi_hq(store)` へ置き換えた**
（台数を渡さない＝台数判定をしない）。
**記事用の並び・列にパネルは元から付かない。パネル仕様を新たに追加しない。**

### ⑤ ⑧本番（subprocess）

`_patch_and_run_narabi()` に **`hq_min_rows: int | None = None`** を追加した。

```python
if hq_min_rows is not None:
    code = re.sub(r'^HQ_MIN_ROWS\s*=\s*\d+', f'HQ_MIN_ROWS = {int(hq_min_rows)}',
                  code, flags=re.MULTILINE)
```

記事用⑧からだけ次を渡す:

```python
hq_scale=_art_narabi_hq(store),
hq_min_rows=_ART_NARABI_HQ_MIN_ROWS,
```

- **`convert_narabi_pil.py` 本体は変更しない。**
  既存の「実行時に一時コピーのソースを patch する」方式をそのまま使う。
- **通常ページなど、引数を渡さない既存呼び出しは `hq_min_rows=None`** となり
  `HQ_MIN_ROWS` も `HQ_SCALE` も書き換わらない＝**従来動作を完全維持**する。

### ⑥ ★描画側と合成側の倍率を一致させる

`_art_hq_scale_for()` へ次を追加した（スランプ・液晶の合成倍率が描画とズレると
表だけ2倍・スランプだけ1倍のような破綻が起きるため）。

```python
if store in _ART_NARABI_HQ_STORES and _art_is_narabi_fn(bare_fn):
    return _ART_HQ_SCALE
```

`_art_is_narabi_fn()` は次を判定する:

- 並び `{機種名}(N台並び).jpg` … 正規表現 `\(\d+台並び\)`
- 列 `{機種名}(列仕掛け).jpg` … 文字列 `(列仕掛け)`
- **同名重複時に末尾へ付く `（開始～終了）` / `(開始～終了)` 付きも部分一致で拾う**

**表・文字・台番・スランプ・液晶をすべて同じ倍率で合成すること。**

### ⑦ JPEG保存は変更しない

`convert_narabi_pil.py` の**既存HQ仕様をそのまま使う**:

```
TARGET_BYTES = (1200 if _hq_run > 1.0 else 250) * 1024
quality 上限 95 ／ subsampling = 0（4:4:4）
```

**500KB固定・500KB上限は実装しない。**
実測では **223〜783KB** に自然に収まり、**すべて q95 に到達**している
（＝これ以上品質を上げられない）。**容量を無理に調整しない。**

### ⑧ 実測（渋谷新館 2026-09-02・⑧subprocess経路）

| 画像 | 台数 | 修正前 | KB | 修正後 | KB |
|---|---|---|---|---|---|
| スマスロ北斗の拳(2台並び) | 2 | 1035×176 | 94 | **2062×348** | 230 |
| スマスロ北斗の拳+からくりサーカス2(3台並び) | 3 | 1122×224 | 115 | **2235×442** | 289 |
| からくりサーカス2+スマスロ北斗の拳(4台並び) | 4 | 1122×270 | 138 | **2235×534** | 347 |
| ゴージャグ3(9台並び) | 9 | 1035×500 | 211 | **2062×988** | 542 |
| 東京喰種(**列仕掛け**・2台) | 2 | 1035×176 | 92 | **2062×348** | 223 |
| ゴージャグ3(**列仕掛け**・9台) | 9 | 1035×500 | 211 | **2062×988** | 542 |
| **ファンキー2(15台並び)** | 15 | 2062×1524 | 783 | **2062×1524** | 783 |

**15台並びは修正前から HQ 対象だったため 2.0x のまま変化なし**（劣化させない）。
quality は前後とも **q95 / 4:4:4** で不変。

⑦プレビュー経路（アプリ内描画）も同様に
`991×184 → 1982×368`（2台並び）、`993×492 → 1984×984`（列9台）等へ 2倍化した。

### ⑨ ネイティブ2.0x であること（resize ではない）

**完成済み画像を `resize` で2倍にしてはならない。**実測根拠:

- **2.0x を50%縮小すると 1.0x と同サイズ・画素差の中央値0**
  （レイアウト・文字位置・罫線・台番・スランプ位置が一致）
- **幅が単純な正確2倍にならない**（1035→2062／2×=2070、1122→2235／2×=2244＝**−8〜−9px**）。
  **フォント実測から列幅を再計算している**証拠。
- **LANCZOS 単純拡大より中間調（ぼけ）画素が一貫して 4.5〜5.5pt 少ない**
  （例 2x実描画 18.91% ／ 1xを2倍拡大 23.32%）＝エッジが鮮明。

### ⑩ 通常ページは不変（実測）

- 通常ページと同じ呼び方（`no_bar` / `hq_scale` / `hq_min_rows` を渡さない）で並び・列を生成し、
  **HEAD版と MD5 完全一致（6画像・不一致0）** を確認した。
- **`show_auto_page` はバイト一致（無変更）。**

### ⑪ 非回帰（本体バイト一致を機械確認）

`show_auto_page` ／ `run_auto_pipeline` ／ `run_step1_main` ／ `run_step2_juggler` ／
`run_step3_other` ／ `_save_jpeg` ／ `_pipeline_hq` ／ `_pipeline_zh_hq` ／ `_art_zh_fn_set` ／
`_build_machine_img` ／ `_build_machine_img_no_bar` ／ `_art_high_title_bar` ／
`_build_article_machine_img` ／ `_apply_panel_to_table_img` ／ `_attach_slump_to_table` ／
`_build_sue_images` ／ `_art_ranking_image` ／ `_build_col_items` ／ `_build_panel_row` ／
`_gap_sel_key` ／ `_art_osusume_images` — **すべて一致**。
新規関数は **`_art_is_narabi_fn` / `_art_narabi_hq` の2つだけ**、消失関数0。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` /
`masters/shimazu_渋谷新館.json` は無変更。**

維持している既存正式仕様:

- **`e1b5835`**: 記事用3店舗の**全台系・高配分は台数無関係2.0x**（`_ART_ZH_HQ_STORES` 不変）
- ジャグラーシリーズ優秀台 ／ その他の優秀台ピックアップ ／ 末尾 ／ バラエティ ／
  ⑤オススメ ／ 差枚数ランキング（1093px幅）
- **島図 3451×6490 ／ `_ART_SHIMAZU_TARGET_KB = 3000` ／ `bceda28` の右端黒帯104px削除**
- 並び・列の抽出条件 ／ 台番 ／ 機種 ／ Pision取得 ／ 機種名変換 ／
  スランプ抽出条件 ／ 液晶選択 ／ パネル仕様 — **今回変更したのは解像度だけ**

### ⑫ ⑦プレビュー実機確認（2026-09-04・渋谷新館 9/2・20枚）

並び4枚・列2枚がいずれも native 幅 1980〜2235px（Streamlit の表示上限1460に張り付き）で生成され、
スランプが表と同倍率で整列、`東京喰種(列仕掛け)` に液晶が中央配置で合成、
`🎯 掲載台を選ぶ（9台中 9台を掲載）` 等のチェックUIも正常。
既存の高配分10枚・ジャグラー統合・その他の優秀台・**差枚数ランキング（1093px のまま）**・
**島図（1460×2745＝3451:6490 のまま）** も壊れていない。

**⑧本番は未実行**（`_git_auto_push()` を避けるため）。**WordPress 通信0件／Cloud Reboot 未実施。**

### ⑬ 今後の禁止事項

1. **`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` を統合しない**
2. **秋葉原を `_ART_HQ_STORES` へ追加しない**
3. **`_ART_NARABI_HQ_MIN_ROWS` を 10 に戻さない**
4. **⑦だけ・⑧だけ直さない**（両経路で 2.0x を保証する）
5. **描画側と合成側の倍率をズラさない**（`_art_is_narabi_fn` の判定を外さない）
6. **`convert_narabi_pil.py` 本体を書き換えない**（実行時 patch 方式を維持）
7. **`_patch_and_run_narabi()` の `hq_min_rows` 既定を None 以外にしない**
   （通常ページの非回帰が壊れる）
8. **完成画像を resize で2倍にしない**（最初から2倍で描く）
9. **JPEG保存方式を変更しない／500KB固定・上限を入れない**
10. **記事用の並び・列にパネル仕様を追加しない**
11. **`e1b5835` の全台系・高配分HQ仕様を巻き戻さない**
12. **島図の 3451×6490 と `_ART_SHIMAZU_TARGET_KB = 3000` を変更しない**
13. **並び・列の抽出条件・台番・機種・液晶選択・スランプ抽出条件を今回を理由に変更しない**
14. **通常ページ（`show_auto_page`）を変更しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用：WordPress下書き作成に対応（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の📰記事用ページの WordPress 下書き作成だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館の記事用WordPress下書きに対応`・2026-09-04・
**`streamlit_app.py` / `wp_client.py` / `CLAUDE.md` の3ファイルのみ**）。
**高田馬場の既存WordPress仕様は本文HTMLのMD5まで完全に不変。**

### ① WordPress対応店舗

```python
# streamlit_app.py
_ART_WP_STORES = frozenset({"高田馬場", "渋谷新館"})
```

**秋葉原は対象外**（記事用ページはあるが `📝 WordPress下書きを作成` を出さない）。
従来は `if store == "高田馬場":` の**店舗名直接比較が2か所**（⑧のpayload保存・ボタン表示）だったが、
どちらもこの集合へ置き換えた。**店舗追加はこの集合と `WP_STORE_CATEGORY` の両方が必要。**

### ② 投稿先カテゴリは店舗別・接続先は全店舗共通

**接続先（`WP_SITE_URL` / `WP_USER` / `WP_APP_PASSWORD`）は全店舗共通の1組だけ**で、
店舗別の Secrets は存在しない（同じ slotterguild3.com の別カテゴリへ投稿する）。
**新しい Secrets を追加しない。**

```python
# wp_client.py
WP_STORE_CATEGORY = {
    "高田馬場": {"id": 24, "slug": "espace-takadanobaba"},
    "渋谷新館": {"id": 19, "slug": "espace-shibuyashin"},
}
def store_category(store) -> dict | None   # 未登録は None
```

**渋谷新館の値は 2026-09-04 に `GET /wp-json/wp/v2/categories` で実測確認済み**（参照のみ・変更通信0件）。

```
id=19  name='エスパス渋谷新館'  slug='espace-shibuyashin'  count=174  parent=0
id=20  name='エスパス渋谷本館'  slug='espace-shibuyahon'   ← 別店舗。取り違えないこと
id=24  name='エスパス高田馬場'  slug='espace-takadanobaba' ← 既存値と一致（裏付け済み）
```

- **カテゴリ term_id / slug を推測で入れてはならない。**管理画面か GET で確認した値だけを登録する。
- **未登録の店舗は `create_takadanobaba_draft()` が1枚も送らずに中止**し、UIもボタンを出さず警告を出す
  （誤ったカテゴリへ下書きを作らないため）。
- `build_content(..., category_slug=...)` / `create_draft(..., category_id=...)` は
  **既定値が高田馬場**なので、引数を渡さない既存呼び出しは従来動作のまま。
- `WP_STATUS="draft"` / `WP_AUTHOR_ID=14` / `WP_MAX_SIDE=2560` / 認証方式 / `upload_media()` /
  All-or-Nothing / 既存投稿の update・DELETE なし は**無変更**。

### ③ 渋谷新館の本文掲載順（正式）

```
全台系濃厚機種が複数
  ↓
1/2系以上の高配分機種が大量
  ↓
末尾
  ↓
並び・列仕掛けも！        ← 並び と 列 を **同じH2内** に置く
  ↓
ジャグからも高配分機種多数！
  ↓
その他単品優秀台も多数
  ↓
オススメ機種の優秀台      ★新規
  ↓
差枚数ランキング          ★新規
  ↓
島図                      ★新規
  ↓
店舗情報・過去の結果はコチラ（ボタン）
```

記事上部（見出し／ポスター／ポスター下文章／X用空段落×3／Xリンク下文章）は高田馬場と共通。
**バラエティは渋谷新館の記事用では生成されない**ので、実ファイルが無く H2 ごと省略される。

### ④ ★ `plan_blocks()` は店舗名で分岐しない（payload 駆動）

追加した4セクションは **payload に該当キーがあり、かつ実ファイルが存在するときだけ**出る。
**高田馬場は列・⑤・ランキング・島図の画像を作らないため、ブロックが1つも増えない。**
`plan_blocks()` に `store == …` の判定を入れてはならない。

| セクション | payload キー | 実在判定 |
|---|---|---|
| 列 | `retsu`（`[{file,title,machine,count,avg_diff,bans}, …]`） | `os.path.isfile()` |
| ⑤オススメ | `osusume`（`[{title, images:[…]}, …]`） | `_existing_files()` |
| 差枚数ランキング | `ranking`（`["差枚数ランキング.jpg"]`） | `_existing_files()` |
| 島図 | `shimazu`（`["島図.jpg"]`） | `_existing_files()` |

**⑦でチェックを外して⑧が `output_dir` から削除した画像は、実在判定で自然に本文へ入らない**
（checkbox と WordPress 送信リストの連動は従来どおり「実ファイルの有無」で行う）。

### ⑤ 列画像

- **並びと同じ H2「並び・列仕掛けも！」の中**へ、並び画像のあとに続けて置く
  （このH2は元から「列」を含む文言なので新設しない）。
- H3 は新設した **`h3_retsu()`**：

  ```
  【列仕掛け】東京喰種(2101〜2102番台)→平均+1,050枚
  ```

  並びの `【N台並び】…` と違い **台数表記をしない**（画像タイトルと同じ流儀・`42ea146`）。
  **`h3_narabi()` 本体は変更しない**（並びの表記へ波及させないため）。
- ファイル名は **⑧の subprocess と同じ規則で作られる `_build_col_items()` の結果**を
  呼び出し側からそのまま渡す。**`wp_client` 側でファイル名を再生成・再推測しない。**
  同名重複時の `（開始～終了）` 付きもこの経路でそのまま反映される。

### ⑥ ⑤オススメ機種の優秀台

- H2 は **「オススメ機種の優秀台」**（記事用画面の⑤の見出しと同じ文言）。
- **ブロックタイトルを H3 として本文へ出す**。これは `_art_osusume_plan()` が
  「将来のWordPress H3用」として持っていた対応表（`_art_osu_plan_{store}`）をそのまま使う。
  **ブロックタイトルは画像には描かれない**（`d121e54` の正式仕様を維持）。
- 画像順は **⑧の生成順**（ブロック1→6・各ブロック内は機種1→6）。
- 実ファイルが1枚も無いブロックは出さず、**全ブロック空なら H2 ごと省略**する。

### ⑦ 差枚数ランキング

H2 は **「差枚数ランキング」**（記事用⑥「差枚数ランキング＆島図」の小見出しと同じ文言）。
`差枚数ランキング.jpg`（1093×2319）は長辺 2560px 未満なので**分割も縮小も起きない**。

### ⑧ 島図

H2 は **「島図」**（記事用⑥の小見出しと同じ文言）。

- **`H2_SHIMAZU = "シマズをチェック！"` は高田馬場のまま維持する。**
  高田馬場では「見出しのみ・画像は人間が挿入」する枠で、位置（その他の直後・ボタンの直前）も
  渋谷新館の島図と同じだが、**流用せず別のH2にした**。
  判定は payload 駆動：**島図画像がある店舗は「島図」H2＋画像／無い店舗は従来どおり
  「シマズをチェック！」の見出しのみ**。
- **島図の仕様は一切変更していない**：**3451×6490** ／ **`_ART_SHIMAZU_TARGET_KB = 3000`** ／
  `shimazu_renderer.py` ／ `masters/shimazu_渋谷新館.json` ／ `bceda28` の右端黒帯104px削除。

#### ★ 既知の未修正事項：WordPress側の幅2560px縮小

`needs_split()` は **高さだけ**で判定する（`h > 2560`）。島図は縦3分割されるが
**幅3451pxはそのまま残る**ため、各片の長辺が 3451px > `WP_MAX_SIDE`(2560) となり
**サイト側で 0.742倍（幅2560px）へ縮小される**（分割しない場合は 1361×2560＝0.394倍）。

```
島図.jpg 3451×6490 → needs_split=True → 3分割（各片 約3451×2164）→ 保存後 幅2560
```

**今回は修正しない。次案件で対応する。**
**`needs_split()` / `split_count()` / 島図renderer / 島図master / JPEG生成を変更してはならない。**

他の画像はすべて幅2560px未満なので縮小されない（実測）:

| 画像 | サイズ | 分割 | 保存後幅 |
|---|---|---|---|
| 全台系・高配分（HQ後） | 1979〜1986×352〜1584 | なし | 縮小なし |
| 並び・列（HQ後） | 2062×348〜988 | なし | 縮小なし |
| ⑤オススメ | 1985×700〜900 | なし | 縮小なし |
| ジャグラーシリーズ優秀台 | 1985×2971 | 2枚 | 1985 |
| その他の優秀台ピックアップ | 2160×8934 | 4枚 | 2160 |
| 差枚数ランキング | 1093×2319 | なし | 1093 |
| **島図** | **3451×6490** | **3枚** | **2560（★縮小あり）** |

### ⑨ モック検証結果（渋谷新館 2026/9/2 相当・WordPress変更通信なし）

```
タイトル : 9月2日(水)│エスパス渋谷新館│
category : 19 / espace-shibuyashin   status=draft   author=14
本文21枚 → 分割後の実アップロード27枚
必須不足 0 件 ／ 任意不足 0 件
```

列2枚・⑤オススメ2枚・差枚数ランキング・島図が**すべて本文に入る**ことを確認。
⑦でチェックを外して⑧が削除した想定の `モンハンライズ_高配分.jpg` は**本文に入らない**ことも確認。

### ⑩ 高田馬場の完全非回帰（同一payloadで HEAD `a0102ad` と比較）

| 項目 | HEAD | 修正後 |
|---|---|---|
| **本文HTML MD5** | **`c35ac89ea13c`** | **`c35ac89ea13c`** |
| タイトル | `9月2日(水)│エスパス高田馬場│` | 同左 |
| 送信対象・画像順 | 9枚（ポスター→全台系2→高配分2→末尾→バラエティ→ジャグ統合→その他） | 同左 |
| H2順 | …その他 → **シマズをチェック！** → ボタン | 同左 |
| category | **id=24 / slug=`espace-takadanobaba`** | 同左 |
| 分割判定・必須/任意不足 | — | 同左 |

**すべて一致。** 高田馬場の タイトル／本文／画像順／送信対象／見出し／category／slug／
分割判定／認証／`WP_STATUS=draft`／`author=14` は**変更禁止**。

### ⑪ 無変更（今回いっさい触れていない）

`needs_split()` / `split_count()` / `split_image_for_wp()` / `plan_split()` / `upload_media()` /
`build_payload()` / `_resolve_high_images()` / `h3_zendai()` / `h3_narabi()` / `narabi_file_name()` /
`build_title()` / `_existing_files()` / `collect_files()` ／
`convert_narabi_pil.py` ／ `shimazu_renderer.py` ／ `masters/shimazu_渋谷新館.json` ／
Pision取得 ／ 機種名変換 ／ 抽出条件（全台系・高配分・末尾・ジャグラー・その他・並び・列・⑤） ／
パネル ／ 液晶 ／ スランプ ／ ZIP ／ JPEG生成。

HQ仕様も不変：
`_ART_HQ_STORES = {"高田馬場","渋谷新館"}` ／
`_ART_ZH_HQ_STORES = {"高田馬場","渋谷新館","秋葉原"}` ／
`_ART_NARABI_HQ_STORES = {"高田馬場","渋谷新館","秋葉原"}` ／ `_ART_SHIMAZU_TARGET_KB = 3000`。

**新規関数は `wp_client.store_category()` / `wp_client.h3_retsu()` の2つだけ**、消失関数0。
`streamlit_app.py` で本体が変わったのは `show_auto_article_page()` のみ・新規関数0。

### ⑫ 今回のWordPress通信

**カテゴリ確認の `GET /wp-json/wp/v2/categories` のみ**（参照）。
**POST / PUT / PATCH / DELETE / media upload / 下書き作成は0件。**
Cloud Reboot も未実行。

### ⑬ 今後の禁止事項

1. **`plan_blocks()` に店舗名の分岐を入れない**（payload 駆動を維持）
2. **高田馬場の本文HTMLを変えない**（MD5 `c35ac89ea13c` を壊さない）
3. **`WP_STORE_CATEGORY` の高田馬場（24 / `espace-takadanobaba`）を変更しない**
4. **カテゴリ term_id / slug を推測で追加しない**（GET か管理画面で確認した値だけ）
5. **秋葉原を `_ART_WP_STORES` へ追加しない**
6. **接続先を店舗別にしない／新しい Secrets を足さない**
7. **`H2_SHIMAZU`（シマズをチェック！）を渋谷新館へ流用しない／高田馬場から消さない**
8. **`h3_narabi()` を `h3_retsu()` のために変更しない**
9. **列のファイル名を `wp_client` 側で再生成しない**（`_build_col_items()` の結果を渡す）
10. **⑤のブロックタイトルを画像へ描かない**（`d121e54` を維持）
11. **島図の解像度・`_ART_SHIMAZU_TARGET_KB`・renderer・master を変更しない**
12. **`needs_split()` / `split_count()` を今回の理由で変更しない**（幅2560px問題は別案件）
13. **HQ gate 3種（`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES`）を変更しない**
14. **記事画像生成ロジック（抽出・パネル・液晶・スランプ・ZIP・JPEG）を変更しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 WordPress：本文構成の見直しとランキング/島図の画質・1枚絵化（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用 WordPress 本文と画像の扱いだけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館のWordPress本文と画像品質を改善`・2026-09-04・
**`streamlit_app.py` / `wp_client.py` / `CLAUDE.md` の3ファイルのみ**）。
実ページを確認したうえで確定した4点（ジャグラーH3／ランキング＆島図の統合／
ランキングHQ／島図1枚絵）を反映したもの。
**高田馬場のWordPress本文は本文HTMLのMD5まで完全に不変。**

### ① ジャグラー統合画像の直前へH3（渋谷新館のみ）

```
H2 ジャグからも高配分機種多数！
  ↓
H3 その他のジャグラーシリーズの優秀台      ★渋谷新館のみ
  ↓
ジャグラーシリーズ優秀台.jpg
```

- 文言は **`H3_JUGGLER_COMB = "その他のジャグラーシリーズの優秀台"`**（`wp_client.py`）。
- **`ジャグラーシリーズ優秀台.jpg` が実在するときだけ**出す
  （`if jug_comb and payload.get("juggler_comb_h3")`）。
  **画像が無いときにH3だけ残ることはない**（モックで実証済み）。
- 出す店舗は `streamlit_app.py` の
  **`_ART_WP_JUG_H3_STORES = frozenset({"渋谷新館"})`** → `payload["juggler_comb_h3"]`。
  **高田馬場はこのキーを持たないのでH3は出ない。**
- **`plan_blocks()` に店舗名の判定を入れない**（payload 駆動を維持）。

### ② 差枚数ランキングと島図を1つのH2へ統合

```
H2 差枚数ランキング&島図
  ↓
差枚数ランキング.jpg
  ↓
空 paragraph ブロック × 5
  ↓
島図.jpg
```

- 定数 **`H2_RANK_SHIMAZU = "差枚数ランキング&amp;島図"`**。
  **HTML内部は `&amp;` で保持する**。raw の `&` は Gutenberg のブロック検証で
  「予期しない内容」エラーになるため。**WordPress上の表示は「差枚数ランキング&島図」。**
- **独立した `H2 差枚数ランキング` / `H2 島図` / `H3 島図` は本文へ出さない。**
  定数 `H2_RANKING` / `H2_SHIMAZUZ` は**履歴として残置・未使用**（`_ARROW_TRI` と同じ扱い）。
- **高田馬場の `H2 シマズをチェック！` は従来どおり維持する。**

### ③ 5行ぶんの余白は空 paragraph ブロック × 5

```python
RANK_SHIMAZU_GAP_PARAS = 5      # blk_empty_para() を5回
```

```html
<!-- wp:paragraph -->
<p class="wp-block-paragraph"></p>
<!-- /wp:paragraph -->
```

記事上部の「X貼付用の空段落×3」と**同じ方式**。
**スペーサーブロック・`<br>`連続・`&nbsp;`・CSS/テーマ変更は使わない**（正式仕様）。

### ④ ランキング/島図の ON/OFF 4パターン（モック実証済み）

| 状態 | 本文 |
|---|---|
| **ランキングON / 島図ON** | `H2 差枚数ランキング&島図` → ランキング画像 → **空段落×5** → 島図画像 |
| **ランキングON / 島図OFF** | `H2 差枚数ランキング&島図` → ランキング画像のみ（**空段落0**） |
| **ランキングOFF / 島図ON** | `H2 差枚数ランキング&島図` → 島図画像のみ（**空段落0**） |
| **両方OFF** | **H2ごと非表示**（渋谷新館） |

- **空段落は「両方そろっているときだけ」入れる**（片方だけのとき余白が浮かない）。
- 両方OFFの判定は **`elif "ranking" not in payload and "shimazu" not in payload:`**。
  渋谷新館はキーを必ず渡すので**H2ごと消え**、
  **キー自体を持たない高田馬場だけ `H2 シマズをチェック！` が残る。**
- ⑦でチェックを外して⑧が `output_dir` から削除した画像は
  `_existing_files()` の実在判定で自然に本文から外れる（既存仕様の維持）。

### ⑤ 差枚数ランキングのネイティブ2.0x描画

**低解像度だった原因（2つ）**

1. `_art_ranking_image(..., scale=150/96)` が**固定**で、HQ の仕組みに一度も接続されていなかった。
2. ⑧が **`_save_jpeg` の既定 target 250KB** で保存しており、**実測 q=60 / 246KB** まで潰れていた。

**採用した方式：ネイティブ2.0x（後から resize しない）**

```python
def _art_ranking_image(df, diff_raw, limit=…, scale=150/96, hq_scale=1.0):
    _hq = hq_scale if hq_scale and hq_scale > 0 else 1.0
    scale = scale * _hq
    ...
    fn_title = load_font(round(TITLE_FONT_SZ * _hq))
    _title_h = round(TITLE_H * _hq)
```

関数は元から `scale` で font / row_h / header_h / pad / 最小列幅を決めていたため、
**唯一スケールされていなかった `TITLE_H` / `TITLE_FONT_SZ` も `_hq` 倍**にした。
**既定 `hq_scale=1.0` は従来と完全に同一。**

| | pixel size | KB | quality | subsampling |
|---|---|---|---|---|
| **修正前** | **1093×2319** | **約246** | **60** | 4:4:4 |
| **修正後** | **2181×4638** | **約2803** | **95** | 4:4:4 |

**ネイティブ2倍の根拠（実測）**
- 2x を50%縮小 → **1x とサイズ完全一致・画素差の中央値0**
- **幅が正確な2倍にならない**（1093→**2181**／2×=2186＝**−5px**）＝列幅をフォント実測から再計算
- **中間調（ぼけ）画素 2x実描画 4.70% ／ 1xをLANCZOS 2倍拡大 10.88%**

**専用 gate**

```python
_ART_RANK_HQ_STORES = frozenset({"渋谷新館"})
def _art_rank_hq(store) -> float          # 対象なら _ART_HQ_SCALE(2.0)
```

**`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` とは統合しない。**
⑦プレビューと⑧本番は**同じ `hq_scale=_art_rank_hq(store)`** を使う（片方だけHQは禁止）。
⑧の保存目標は他のHQ画像と同じ `_ART_HQ_TARGET_KB` へ引き上げる。
`_art_ranking_image()` の呼び出しは⑦/⑧の2か所だけで、いずれも `_ART_RANK_STORES`
（＝渋谷新館）の内側なので**他店舗・通常ページへ影響しない**。

### ⑥ ★ランキングはWordPressで2分割する（1枚絵化しない）

2181×4638 は高さ2560超なので**既存の分割処理で2枚**になる。

```
2181×2336 ／ 2181×2302   → 各片の長辺 < 2560 → 縮小されず 幅2181px を維持
（修正前は分割なしで 幅1093px）
```

**幅2181pxを維持して文字を高精細に見せることを優先する。ランキングを1枚絵にしない。**

### ⑦ ★島図はWordPressでは1枚絵にする

**2Fだけ拡大されていた直接原因**：島図が `plan_split()` で**縦3分割され、
WordPress へ3つの別メディアとしてアップロード**されていたため。
テーマのライトボックスはクリックしたメディアだけを開くので、1枚目（上部＝2F）しか開かなかった。

```python
# wp_client.py
WP_NOSPLIT_FILES = frozenset({"島図.jpg"})

def plan_split(found, tmp_dir):
    for f in found:
        if f["file"] in WP_NOSPLIT_FILES:
            continue          # needs_split() すら呼ばない
```

| 項目 | 値 |
|---|---|
| 島図の元画像 | **3451×6490 ／ `_ART_SHIMAZU_TARGET_KB = 3000`（変更なし）** |
| WordPress アップロード枚数 | **1枚** |
| 本文の image block 数 | **1個** |
| WordPress 側の保存サイズ（予測） | **約 1361×2560**（core の big-image しきい値2560で `-scaled.jpg` が作られ `source_url` はそれを指す） |

- **クリック・拡大時に 2F＋3F を含む島図全体が1枚として表示される**ことを優先する。
- **約1361×2560へ縮小されることは了承済みの正式仕様**。今回これを問題としない。
- サイト設定・PHP・テーマ・サーバー設定を変えずに2560px縮小を避けつつ1枚絵にする方法は
  現在のAPI/サイト仕様には無い（`WP_MAX_SIDE=2560` はサイト側の挙動）。
- **`shimazu_renderer.py` / `masters/shimazu_渋谷新館.json` / 島図canvas・レイアウト・文字・色・
  JPEG生成は変更しない。**

### ⑧ 既存の分割処理は変更しない（島図だけの例外）

**`needs_split()` / `split_count()` / `split_image_for_wp()` の本体はバイト一致で無変更。**
除外は `plan_split()` の入口で `WP_NOSPLIT_FILES` を見るだけ。

| 画像 | 分割 |
|---|---|
| ジャグラーシリーズ優秀台.jpg（1985×2971） | **2分割（従来どおり）** |
| その他の優秀台ピックアップ.jpg（2160×8934） | **4分割（従来どおり）** |
| 差枚数ランキング.jpg（HQ後 2181×4638） | **2分割** |
| **島図.jpg（3451×6490）** | **分割しない（1枚絵）** |

**高田馬場の分割仕様にも影響しない。**

### ⑨ 高田馬場の完全非回帰（同一payloadで比較）

| 項目 | before | after |
|---|---|---|
| **本文HTML MD5** | **`c35ac89ea13c`** | **`c35ac89ea13c`** |
| タイトル | `9月2日(水)│エスパス高田馬場│` | 同左 |
| 送信対象・画像順（9枚） | ポスター→全台系2→高配分2→末尾→バラエティ→ジャグ統合→その他 | 同左 |
| `H2 シマズをチェック！` | あり | **あり（維持）** |
| category | id=24 / slug=`espace-takadanobaba` | 同左 |
| 分割判定・必須/任意不足 | — | 同左 |

**高田馬場に `その他のジャグラーシリーズの優秀台` H3 も
`差枚数ランキング&島図` H2 も追加しない。島図の1枚絵例外も影響しない。**

### ⑩ 無変更（バイト一致を機械確認）

`needs_split` / `split_count` / `split_image_for_wp` / `upload_media` / `create_draft` /
`h3_zendai` / `h3_narabi` / `h3_retsu` / `narabi_file_name` / `build_content` /
`collect_files` / `_existing_files` / `_resolve_high_images` ／
`convert_narabi_pil.py` ／ `shimazu_renderer.py` ／ `masters/shimazu_渋谷新館.json`。

不変の定数：
`_ART_WP_STORES = {"高田馬場","渋谷新館"}` ／
`WP_STORE_CATEGORY = {高田馬場:24/espace-takadanobaba, 渋谷新館:19/espace-shibuyashin}` ／
`_ART_HQ_STORES` ／ `_ART_ZH_HQ_STORES` ／ `_ART_NARABI_HQ_STORES` ／
`_ART_SHIMAZU_TARGET_KB = 3000` ／ `WP_MAX_SIDE = 2560` ／ `WP_STATUS = "draft"` ／
`WP_AUTHOR_ID = 14`。

**新規関数は `streamlit_app._art_rank_hq()` の1つだけ**、消失関数0。
Pision取得／抽出条件／パネル／液晶／スランプ／ZIP／全台系・高配分HQ／並び・列HQ も無変更。

### ⑪ 今回のWordPress通信

**変更通信0件。** media upload / 下書き作成 / POST / PUT / PATCH / DELETE いずれも未実行。
検証はすべてローカルのモックで行った。Cloud Reboot も未実行。

### ⑫ 今後の禁止事項

1. **`plan_blocks()` に店舗名の分岐を入れない**（payload 駆動を維持）
2. **高田馬場の本文HTML MD5 `c35ac89ea13c` を壊さない**
3. **高田馬場へ `その他のジャグラーシリーズの優秀台` / `差枚数ランキング&島図` を追加しない**
4. **高田馬場の `シマズをチェック！` を消さない**
5. **H2の `&` を raw に戻さない**（`&amp;` で保持）
6. **ジャグラーH3を画像の実在チェックなしで出さない**
7. **5行余白をスペーサーブロック・`<br>`・`&nbsp;`・CSSへ置き換えない**
8. **`_ART_RANK_HQ_STORES` を既存3 gate へ統合しない**
9. **ランキングを1枚絵にしない**（2分割で幅2181pxを維持する）
10. **⑦だけHQ／⑧だけHQ の状態を作らない**
11. **島図を再び分割対象に戻さない**（`WP_NOSPLIT_FILES` を外さない）
12. **`needs_split()` / `split_count()` / `split_image_for_wp()` 本体を変更しない**
13. **島図の 3451×6490 と `_ART_SHIMAZU_TARGET_KB=3000`・renderer・master を変更しない**
14. **島図の約1361×2560縮小を理由にサイト設定・PHP・テーマ・サーバー設定を変更しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 WordPress：記事冒頭の「ななこポスト」セクション（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用 WordPress 本文の冒頭だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館の記事冒頭にななこポストを追加`・2026-09-04・
**`streamlit_app.py` / `wp_client.py` / `CLAUDE.md` の3ファイルのみ**）。
**高田馬場のWordPress本文は本文HTMLのMD5まで完全に不変。**

### ① 挿入位置

**記事上部（Xリンク下文章）の直後・`H2 全台系濃厚機種が複数` の直前**で固定。

```
既存の記事上部（見出し／ポスター／ポスター下文章／空段落×3／Xリンク下文章）
  ↓
H2 ななこポストに仕掛けのヒントを確認！        ★ここから
  ↓
固定の導入文
  ↓
【太字】↓前日の夜に配信されたポストがコチラ
  ↓
X投稿の埋め込み（Gutenberg標準 wp:embed）
  ↓
固定文「今回の結果から考えると下記のヒントを確認することができました！」
  ↓
■ヒント × 最大6件（「■」だけ赤＋太字）
  ↓
固定の締め文                                  ★ここまで
  ↓
H2 全台系濃厚機種が複数（以降は従来どおり）
```

**`plan_blocks()` に店舗名の判定は入れない。** `payload["nanako"]` を持つ店舗だけ出る
（`streamlit_app._ART_NANAKO_STORES = frozenset({"渋谷新館"})`）。
**高田馬場はこのキーを渡さないので1ブロックも増えない。**

### ② 固定文章（`wp_client.py` の定数・入力欄にしない）

| 定数 | 文言 |
|---|---|
| `NANAKO_H2` | ななこポストに仕掛けのヒントを確認！ |
| `NANAKO_LEAD` | 前日の夜に配信される渋谷ななこのポストには仕掛けのヒントが隠されていることが多く、今回もポストから仕掛けのヒントと思しき箇所を複数確認！ |
| `NANAKO_URL_LEAD` | ↓前日の夜に配信されたポストがコチラ（**太字段落**） |
| `NANAKO_HINT_LEAD` | 今回の結果から考えると下記のヒントを確認することができました！ |
| `NANAKO_OUTRO` | このように、ななこポストからは連日仕掛けのヒントを確認できているため、打ちに行く際は必ずチェックしておきましょう！ |
| `NANAKO_HINT_MARK` | ■ |
| `NANAKO_MARK_COLOR` | **#e60012** |
| `NANAKO_HINT_COUNT` | 6 |

### ③ 入力UIと保存（日付単位）

記事用ページの「Xリンク下の文章」キャプションの直後に配置。**既存採番①〜⑧は変更しない。**

- **前日のななこポスト Xリンク × 1**
- **ヒント1〜6（2列×3段）**

| session_state キー | 内容 |
|---|---|
| `art_nanako_url_渋谷新館` | 前日のXポストURL |
| `art_nanako_hint_0_渋谷新館` 〜 `art_nanako_hint_5_渋谷新館` | ヒント1〜6 |

- 保存は **既存の `article_page_inputs.json`（Excelファイル名＝日付でスコープ）**。
  **新しい保存ファイルを作らない。**
- `_article_input_keys(store)` へ**7キーを登録**し、既存の
  `_save_article_inputs(store, skip_kojin=True)` / `_restore_article_inputs()` に乗せる。
  **`on_change` は必ず `args=(store, True)`＝`skip_kojin=True`**（②個別画像を巻き込まない・`0e7dc4c`）。
- **実UI検証（2026-09-04）**: 9/2 で入力 → **9/1 へ切替でURL・ヒント全欄が空（混入なし）** →
  **9/2 へ戻すと完全復元**。
- **この保存経路を変更しない。**

### ④ ★X投稿はGutenberg標準の embed ブロックで出す

**paragraph + `<a>` のURLリンクにしない。**
markup は**推測せず、同じサイトの既存投稿（ID 60367）の `content.raw` を GET で読んで確認した実物**
に合わせている。生成結果は**その既存ブロックと文字列完全一致**する。

```html
<!-- wp:embed {"url":"…","type":"rich","providerNameSlug":"x","responsive":true} -->
<figure class="wp-block-embed is-type-rich is-provider-x wp-block-embed-x"><div class="wp-block-embed__wrapper">
URL
</div></figure>
<!-- /wp:embed -->
```

- **`providerNameSlug` は `"x"`**（サイト上には旧 `"twitter"` の投稿も残るが、現行Gutenbergが
  出すのは `"x"`）。
- ブロック属性は **`json.dumps(..., separators=(",",":"))`**、figure内のURLテキストは **`esc()`**。
  **生の文字列連結はしない。**

### ⑤ URL の判定（`normalize_x_url()`）

`urlsplit` ＋ 正規表現1本だけ。**独自URLパーサーを作らない。**

| 入力 | 扱い |
|---|---|
| `https://x.com/<handle>/status/<数字>` | **採用** |
| `https://twitter.com/<handle>/status/<数字>` | **採用（ドメインを書き換えない）** |
| 末尾スラッシュあり | 採用 |
| `?s=20&t=…` などのクエリ・フラグメント | **自動除去して採用**（HTML内の `&` によるブロック検証ずれを避ける） |
| `http://`（https でない） | **拒否** |
| `javascript:` / `data:` | **拒否** |
| 他ドメイン | **拒否** |
| `/status/` なし・status が非数値 | **拒否** |
| 空文字・空白 | **拒否** |

**`twitter.com` → `x.com` の書き換えはしない。**
サイトの `GET /wp-json/oembed/1.0/proxy` が **x.com / twitter.com のどちらでも 200 を返す**ことを
実測済み（どちらも canonical `x.com` を返す）。

**不正URLは「Xなし」と同じ扱い**（`plan_blocks()` は `normalize_x_url()` の結果で判定する）。

### ⑥ ヒント行の「■」だけ赤＋太字

```html
<!-- wp:paragraph -->
<p class="wp-block-paragraph"><strong style="color:#e60012">■</strong>ヒソカ→見た目がピエロ→ピエロ→北斗</p>
<!-- /wp:paragraph -->
```

- **「■」だけが `<strong style="color:#e60012">`。後ろの本文は装飾なし。**
  **段落全体を赤・太字にしない。**
- **入力欄へ「■」を打つ必要はない**（出力時に自動で付ける）。
- **空欄のヒントは出力しない。**途中が空でも詰めて、入力済みのヒントだけ出す
  （空の「■」を作らない）。
- インラインstyleのみ。**テーマCSSは変更しない。**

### ⑦ エスケープ

`wp_client` に escape が無かったため **`esc()`（`html.escape(..., quote=True)`）を新設**。

- **ヒント本文は必ず `esc()` を通す**（実測: `<script>` → `&lt;script&gt;`、`&` → `&amp;`、
  `"` → `&quot;`、`'` → `&#x27;`）。
- embed の属性は `json.dumps`、figure内URLは `esc()`。
- **ユーザー入力を生のままHTMLへ連結しない。**

### ⑧ 条件分岐（モック実証済み）

| パターン | 出力 |
|---|---|
| **Xあり＋ヒントあり** | H2 → 導入文 → 太字 → X embed → ヒントlead → ヒント → 締め文 |
| **Xなし＋ヒントあり** | **太字とX embed をセットで非表示**／ヒント部分は表示 |
| **Xあり＋ヒントなし** | H2 → 導入文 → 太字 → X embed（**ヒントlead・ヒント・締め文をまとめて非表示**） |
| **Xなし＋ヒントなし** | **H2 ＋ 固定導入文のみ** |
| **不正URL** | **Xなしと同じ扱い** |
| **途中空欄** | 入力済みのヒントだけ表示 |

**入力が1件も無くても H2＋固定導入文までは出す**（セクションごと消さない）。

### ⑨ `blk_para_link()` は削除（正式）

最初 paragraph+`<a>` 方式で作った `blk_para_link()` は **ななこポスト専用**だったため、
embed 化に伴い**削除した**（定義・使用・dispatch すべて0件を機械確認）。
**残骸を戻さない。**

### ⑩ 高田馬場の完全非回帰

| 項目 | before | after |
|---|---|---|
| **本文HTML MD5** | **`c35ac89ea13c`** | **`c35ac89ea13c`** |
| タイトル／画像順（9枚）／送信対象／分割判定／カテゴリ | — | すべて一致 |
| `H2 シマズをチェック！` | あり | **あり（維持）** |

**高田馬場へ「ななこポスト」セクションを追加しない。**

### ⑪ 渋谷新館の既存WordPress仕様は不変

ジャグラーH3「その他のジャグラーシリーズの優秀台」／`H2 差枚数ランキング&島図`／
ランキングと島図の間の**空段落×5**／ランキングHQ（`_ART_RANK_HQ_STORES={"渋谷新館"}`・
2181×4638・WordPressで2分割）／**島図 3451×6490・1枚絵**（`WP_NOSPLIT_FILES={"島図.jpg"}`）／
店舗情報ボタン ── **すべて維持**。

定数も不変：`_ART_WP_STORES = {"高田馬場","渋谷新館"}` ／
`WP_STORE_CATEGORY = {高田馬場:24/espace-takadanobaba, 渋谷新館:19/espace-shibuyashin}` ／
`_ART_HQ_STORES` ／ `_ART_ZH_HQ_STORES` ／ `_ART_NARABI_HQ_STORES` ／
`_ART_RANK_HQ_STORES` ／ `_ART_SHIMAZU_TARGET_KB = 3000`。

`convert_narabi_pil.py` / `shimazu_renderer.py` / `masters/shimazu_渋谷新館.json` も**無変更**。
新規関数は `wp_client` の **`esc` / `blk_para_bold` / `blk_para_hint` / `normalize_x_url` /
`blk_embed_x`** の5つだけ、消失は `blk_para_link` のみ（同セッション内で追加→削除）。

### ⑫ 今回のWordPress通信

**変更通信0件。** POST / PUT / PATCH / DELETE / media upload / draft作成はすべて未実行。
行ったのは **markup 確認のための `GET /wp/v2/posts` と `GET /oembed/1.0/proxy`（参照のみ）** だけ。
Cloud Reboot も未実行。

### ⑬ 今後の禁止事項

1. **X投稿を paragraph+`<a>` のURLリンクへ戻さない**（Gutenberg標準 embed を維持）
2. **embed の markup を推測で書き換えない**（実サイトの保存形と一致させる）
3. **`providerNameSlug` を `"twitter"` へ戻さない**
4. **`twitter.com` → `x.com` の書き換えを足さない**
5. **クエリ除去をやめない**（`&` がHTMLへ入るとブロック検証がずれる）
6. **`normalize_x_url()` を通さずに embed を出さない**（javascript: / data: の混入防止）
7. **ヒント本文の `esc()` を外さない／ユーザー入力を生でHTMLへ連結しない**
8. **段落全体を赤・太字にしない**（赤＋太字は「■」だけ）
9. **`NANAKO_MARK_COLOR` を理由なく変えない**
10. **入力欄へ「■」を打たせる仕様にしない**
11. **空欄のヒントを出さない**（空の「■」を作らない）
12. **`plan_blocks()` に店舗名の分岐を入れない**（payload 駆動を維持）
13. **高田馬場へ「ななこポスト」を追加しない／MD5 `c35ac89ea13c` を壊さない**
14. **`blk_para_link()` を復活させない**
15. **保存に新しいJSONを作らない**（`article_page_inputs.json` の日付スコープを維持）
16. **`skip_kojin=True` を外さない**（②個別画像を巻き込む）
17. **渋谷新館の既存WordPress仕様（ジャグラーH3・ランキング&島図・空段落×5・島図1枚絵）を変えない**
18. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 ななこポスト：X埋め込みホストとヒント表示の修正（2026-09-04・実WordPress検証で確定）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】のななこポストセクションだけ**。
正式コード commit は本節と**同一の commit**
（`fix: 渋谷新館のX埋め込みとヒント表示を修正`・2026-09-04・
**`wp_client.py` と `CLAUDE.md` の2ファイルのみ**。`streamlit_app.py` はバイト無変更）。

直前の「渋谷新館 WordPress：記事冒頭の「ななこポスト」セクション（2026-09-04）」の
**3点を supersede する**。**同節は削除・書き換えしない**（当時の判断の記録として残す）。

### ⓪ 上書きされた3点

| | 旧（同日の前ノード） | **新（本節・正式）** |
|---|---|---|
| 埋め込みURLのホスト | 「**入力されたドメインをそのまま使う**（x.com / twitter.com を書き換えない）」 | **`blk_embed_x()` の中だけ `twitter.com` へ正規化する** |
| ヒントの色・太字 | 「**「■」だけ**赤＋太字」 | **「■＋ヒント本文」の1行まるごと**を赤＋太字 |
| ヒントの段落 | **1ヒント＝1 paragraph** | **ヒント一覧全体を1 paragraph にまとめ `<br>` で改行** |

---

## A. X埋め込みが「プロフィール表示」になっていた件

### ① 入力・保存・payload にバグは無かった（実測で確定）

実際に入力された `https://x.com/espace_shibuya/status/2095096899892031838` について、
**status ID が最後まで1箇所も変わっていない**ことを追跡で確認した。

```
入力URL → article_page_inputs.json（20260903_渋谷新館_20S.xlsx）
        → session_state → normalize_x_url() → payload["nanako"]["url"]
        → plan_blocks() → build_content()
        → 実下書き ID 61889 の content.raw
```

**すべて `/status/2095096899892031838` のまま。**
プロフィールURLへ短縮された箇所は無い。
→ 「保存されていない」「normalizeが壊す」「payloadで置換」「embed markupが原因」は**すべて否定**。

### ② ★確定原因＝WordPress oEmbed の解決結果（ホスト差）

同じ status ID でホストだけ変えて `GET /wp-json/oembed/1.0/proxy` を実行した結果:

| 渡したURL | status | 返る `html` | 記事上の見え方 |
|---|---|---|---|
| **`https://x.com/…/status/…`** | 200 | **空文字** | `author_name` / `author_url` しか無く、**「渋谷ななこ (@espace_shibuya) on X」というプロフィール相当表示**になる |
| **`https://twitter.com/…/status/…`** | 200 | **`<blockquote class="twitter-tweet">…` に投稿本文入り** | **その投稿そのものが埋め込まれる** |

**サイト上で正常に埋め込まれている既存投稿（ID 60367）も `twitter.com` で保存されている。**

> 前ノードで「x.com / twitter.com どちらも 200 なので書き換え不要」と記録したのは
> **status コードだけを見て `html` の中身を確認していなかったため**。
> 本節は `html` まで確認したうえでの確定仕様であり、**こちらが優先する**。

### ③ 正式仕様：入力URLと埋め込みURLを分ける

```python
_X_EMBED_HOST = "twitter.com"

def blk_embed_x(url):
    u = normalize_x_url(url)          # 入力の検証仕様は**変更しない**
    ...
    _p = urlsplit(u)
    u = urlunsplit((_p.scheme, _X_EMBED_HOST, _p.path, "", ""))   # ホストだけ揃える
```

- **記事用UIは今までどおり `x.com` / `twitter.com` の両方を入力できる。**
  `normalize_x_url()` の検証仕様（https限定・`/status/<数字>` 必須・クエリ/フラグメント除去・
  `javascript:` `data:` 他ドメインは拒否）は**そのまま維持**。
- **`blk_embed_x()` の中だけ**でホストを `twitter.com` へ置き換える。
  **status ID・path は絶対に変更しない。**
- **`providerNameSlug` は `"x"` のまま**（既存投稿 60367 と同じ）。
  **URLホスト=`twitter.com` ／ providerNameSlug=`"x"` の組み合わせが正式。**
  ここを `"twitter"` へ変えない。

実測（修正後）:

```
入力 https://x.com/espace_shibuya/status/2095096899892031838
入力 https://twitter.com/espace_shibuya/status/2095096899892031838
  → どちらも embed URL は
     https://twitter.com/espace_shibuya/status/2095096899892031838
  → 属性・figure内の両方が twitter.com（x.com の出現 0）
  → oEmbed: html 非空 ／ html に status ID あり ／ 実投稿本文（「やっほー ななこだよ🐾👊…」）を取得
```

---

## B. ヒント表示（全文を赤＋太字・段落間の空きをなくす）

### ④ 修正前（実下書き 61889 の content.raw）

```html
<p class="wp-block-paragraph"><strong style="color:#e60012">■</strong>神→ゴッド神々の軌跡、ゴッドイーター</p>
<p class="wp-block-paragraph"><strong style="color:#e60012">■</strong>激闘→北斗転生2</p>
```

「■」だけ赤・本文は黒。さらに **1ヒント＝1 paragraph** だったため、
テーマの paragraph margin でヒント同士が大きく空いていた。

### ⑤ 修正後（正式）

```html
<!-- wp:paragraph -->
<p class="wp-block-paragraph"><strong style="color:#e60012">■ヒント1<br>■ヒント2<br>■ヒント3</strong></p>
<!-- /wp:paragraph -->
```

- **「■＋ヒント本文」の1行まるごと**を `<strong style="color:#e60012">` で包む
  （**赤＋太字**）。`NANAKO_MARK_COLOR = #e60012` は維持。
- **ヒント一覧全体を1つの `wp:paragraph`** にまとめ、各ヒントを **`<br>`** で改行する。
  段落が1つなので**段落間 margin が発生しない**。
- **`<br>` 連打・`&nbsp;`・spacer ブロック・CSS/テーマ変更は使わない。**
- この「1 paragraph ＋ `<strong>` ＋ `<br>` で複数行」という形は、
  **同じサイトの人手作成の既存投稿（ID 61647 / 61673）で実際に使われている**
  Gutenberg 標準の改行（Shift+Enter）と同じ構造。これを正式根拠とする。
- 実装は **`blk_para_hints(hints)`**（新規）。**旧 `blk_para_hint(text)` は削除**。
  plan の項目は `{"type": "para_hints", "hints": [...]}` の**1個だけ**。

### ⑥ 空欄・エスケープ（従来どおり）

- 入力欄は6枠のまま。**入力されたものだけを順番どおり出力**する。
  例: 1/3/5 のみ入力 → **`■ヒント1` / `■ヒント3` / `■ヒント5` の3行**。
  **空の「■」は出さない。**
- ヒント本文は**必ず `esc()`（`html.escape(..., quote=True)`）を通してから `<strong>` 内へ入れる**。
  生のユーザー入力をHTMLへ直接連結しない（`<script>` → `&lt;script&gt;` を実測確認）。

### ⑦ 実測（モック）

| パターン | ヒント paragraph 数 | 行数 |
|---|---|---|
| 1件 | **1** | 1 |
| 3件 | **1** | 3 |
| 6件 | **1** | 6 |
| 途中空欄 1/3/5 | **1** | **3** |

---

## C. 変更範囲と非回帰

**変更したのは `wp_client.py` の1ファイルだけ**（`CLAUDE.md` を除く）。

| 区分 | 関数 |
|---|---|
| 新規 | `blk_para_hints()` |
| 削除 | `blk_para_hint()` |
| 変更 | `blk_embed_x()` ／ `plan_blocks()` ／ `build_content()` |

- **`streamlit_app.py` はバイト無変更。**
  入力UI・`art_nanako_url_{store}` / `art_nanako_hint_0〜5_{store}`・
  `_article_input_keys()`・`article_page_inputs.json` の**日付スコープ保存は一切変更していない**。
- **高田馬場の本文HTML MD5 は `c35ac89ea13c` のまま完全一致。**
- 渋谷新館の既存仕様は**すべて維持**:
  ななこH2／固定導入文／X案内太字／ヒントlead／締め文／`H2 全台系濃厚機種が複数`／
  ジャグラーH3「その他のジャグラーシリーズの優秀台」／`H2 差枚数ランキング&島図`／
  ランキングと島図の間の**空段落×5**／ランキングHQ（2181×4638・WordPressで2分割）／
  **島図 3451×6490・1枚絵**（`WP_NOSPLIT_FILES={"島図.jpg"}`）／店舗情報ボタン。
- 条件分岐（Xあり＋ヒントあり／Xなし＋ヒントあり／Xあり＋ヒントなし／Xなし＋ヒントなし／
  不正URL＝Xなし扱い／途中空欄）も**すべて従来どおり**。
- 定数は不変: `_ART_WP_STORES` ／ `WP_STORE_CATEGORY` ／ `WP_NOSPLIT_FILES` ／
  `_ART_HQ_STORES` ／ `_ART_ZH_HQ_STORES` ／ `_ART_NARABI_HQ_STORES` ／
  `_ART_RANK_HQ_STORES` ／ `_ART_SHIMAZU_TARGET_KB = 3000`。
- `convert_narabi_pil.py` / `shimazu_renderer.py` / `masters/shimazu_渋谷新館.json` も無変更。

## D. 今回のWordPress通信

**変更通信0件。** POST / PUT / PATCH / DELETE / media upload / draft作成はすべて未実行。
**既存の下書き 61889 も変更していない。**
行ったのは調査のための **GET のみ**:
`GET /wp/v2/posts?context=edit`（既存投稿の markup と 61889 の content.raw 確認）／
`GET /wp-json/oembed/1.0/proxy`（x.com と twitter.com の応答比較）。
Cloud Reboot も未実行。

## E. 今後の禁止事項

1. **embed のホストを `x.com` に戻さない**（oEmbed の html が空になり、プロフィール表示に戻る）
2. **`providerNameSlug` を `"twitter"` へ変えない**（`"x"` のまま）
3. **`normalize_x_url()` の入力検証を embed 用の正規化と混同しない**
   （入力は x.com / twitter.com 両方可・埋め込み時だけホストを揃える）
4. **status ID / path を書き換えない**
5. **クエリ・フラグメント除去をやめない**
6. **「■だけ赤太字」へ戻さない**（1行まるごと赤＋太字）
7. **1ヒント＝1 paragraph に戻さない**（段落間 margin が復活する）
8. **`<br>` 連打・`&nbsp;`・spacer・CSS/テーマ変更で余白調整しない**
9. **`esc()` を外さない／ユーザー入力を生でHTMLへ連結しない**
10. **空欄ヒントを出さない**（空の「■」を作らない）
11. **`blk_para_hint()`（単数）を復活させない**
12. **`streamlit_app.py` のUI・保存キー・日付スコープ保存を変更しない**
13. **高田馬場の本文HTML MD5 `c35ac89ea13c` を壊さない**
14. **前ノードの記録を削除・改変しない**（supersede した事実を残す）
15. **無関係なリファクタ・未使用コード整理をしない**

## ⑧再実行時の FileExistsError（WinError 183）を修正（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**並び／列画像を一時フォルダから `output_dir` へ移す2箇所だけ**。
正式コード commit は本節と**同一の commit**
（`fix: 画像再生成時の同名ファイル移動エラーを修正`・2026-09-04・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**画像の内容・ファイル名・WordPress処理は一切変更していない。**

### ① 発生したエラー

渋谷新館の記事用⑧を**同じ日付・同じ店舗で再実行**したときに発生した。

```
FileExistsError: [WinError 183] 既に存在するファイルを作成することはできません。
  src: …60903_渋谷新館\並び画像\カバネリ海門決戦(3台並び)（3170～3172）.jpg
  dst: …60903_渋谷新館\カバネリ海門決戦(3台並び)（3170～3172）.jpg
  streamlit_app.py の os.rename(...) で停止
```

### ② 確定原因

1. **`output_dir` は再利用される。** `os.makedirs(output_dir, exist_ok=True)` のみで、
   **既存ファイルを消す処理が無い**（`rmtree` は存在しない）。
   → **前回⑧で生成された並び／列画像が、正式ファイル名のまま `output_dir` 直下に残る。**
2. **記事用⑧には連番プレフィックス（`NN_`）の付与も剥がしも無い**
   （`_seq` / de-prefix があるのは通常ページ側と📝側だけ）。
   → 記事用の `output_dir` には**常に素のファイル名**が残る。
3. そこへ今回の再生成物を **`os.rename(src, dst)`** で移そうとした。
   **Windows の `os.rename()` は宛先が既に存在すると必ず失敗する**（WinError 183）。
   **POSIX の rename は上書きするため、Cloud / Linux では顕在化していなかった。**

**⑧は何度でも押せる通常操作**（⑧ → WordPress下書き確認 → 修正 → 再度⑧）なので、
**「既存ファイルを手で消してから実行」は解決策にしない。**

### ③ 正式修正：`os.rename` → `os.replace`（2箇所のみ）

| 箇所 | 関数 | 対象 |
|---|---|---|
| `show_auto_page()` | 通常／スランプ付き／かぶぱ／📝 | 並び画像・列画像（同一ループ） |
| `show_auto_article_page()` | 記事用⑧ | 並び画像・列画像（同一ループ） |

```python
# 修正前
os.rename(os.path.join(narabi_dir, _nf), os.path.join(output_dir, _nf))
# 修正後
os.replace(os.path.join(narabi_dir, _nf), os.path.join(output_dir, _nf))
```

**無関係な `os.rename` / `os.replace` は変更しない。**
`shutil.move` は導入しない。`os.remove(dst)` してから rename する二段階処理も採らない。

### ④ `os.replace` を選んだ根拠

- **src は今回新規生成した並び／列成果物**、**dst は前回⑧が作った同一論理成果物**。
  同じ正式ファイル名のまま**最新版へ更新するのが正しい**。
- `narabi_dir = os.path.join(output_dir, "並び画像")` なので **src / dst は常に同一FS**、
  dst は常にファイル。
- **Windows でも既存 dst を置換でき、POSIX / Linux でも同じ意味**（Cloud 互換）。
- **本プロジェクトは既に「再実行時の同名成果物の置換」に `os.replace` を使っている**
  （連番プレフィックスの剥がし・付け直し／📝側の連番付与など計5箇所）。同じ考え方の踏襲。

### ⑤ 並び・列の両方が対象（列専用の修正は作らない）

`convert_narabi_pil.py` は **並び画像と列仕掛け画像を同じ `SPLIT_DIR`（＝`narabi_dir`）へ出力**し、
**同じ移動ループを通る**。したがって**この2箇所の修正で並び・列の双方が解決**する。
**列専用の別修正を追加しない。**

### ⑥ 正式ファイル名は変更しない

```
カバネリ海門決戦(3台並び)（3170～3172）.jpg   ← このまま
```

**`_timestamp` / `_2` / ランダム suffix を付けて衝突を避けることは禁止。**
**同じ論理成果物は同じ正式ファイル名のまま、再実行で最新版へ置換される。**
全角／半角括弧の表記も不変。

### ⑦ 店舗

記事用は**共通経路**なので、**高田馬場・渋谷新館・秋葉原のすべて**が同じ再実行安全性を持つ。
**渋谷新館だけの店舗特例は作らない。**各店舗固有の生成仕様は一切変更していない。
通常ページ側も同じ理由で置換にした（⑦でチェックを外した等で連番なしの成果物が残ると
同じ衝突が起き得るため）。

### ⑧ tempdir での再現・修正確認（実データ不使用）

**修正前（`os.rename`）**

```
1回目移動 : OK
2回目（同名を再生成）: ★FileExistsError [WinError 183]
                       …60903_渋谷新館\カバネリ海門決戦(3台並び)（3170～3172）.jpg
```

**修正後（`os.replace`）**

```
1回目移動 : OK
2回目移動 : OK（エラーなし）
  dst が最新版へ置換      : True（内容が「2回目の内容」）
  他の並び画像も更新      : True
  src 移動済み            : True
  並び画像フォルダ削除    : True
  ★別名の手動配置ファイル : 内容ごと無変更
  ファイル名不変          : True（suffix付き別名の生成なし）
```

**実データ（`C:\Users\23-3\Desktop\20260903_渋谷新館`）には一切触れていない。**

### ⑨ 非回帰（commit直前に再確認）

| 項目 | 結果 |
|---|---|
| **高田馬場 WordPress 本文HTML MD5** | **`c35ac89ea13c` → `c35ac89ea13c`（完全一致）** |
| ななこポスト X embed | 不変（`_X_EMBED_HOST = "twitter.com"` / `providerNameSlug="x"`） |
| ヒント表示 | 不変（「■＋全文」を `#e60012` ＋ `strong`／1 paragraph ＋ `<br>`） |
| ランキングHQ | 不変（`_ART_RANK_HQ_STORES = {"渋谷新館"}`） |
| 島図1枚絵 | 不変（`WP_NOSPLIT_FILES = {"島図.jpg"}` / `_ART_SHIMAZU_TARGET_KB = 3000`） |
| 日付保存 | 不変（`art_nanako_*` 7キーを含む既存仕様） |
| HQ各gate | 不変（`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` / `_ART_RANK_HQ_STORES`） |

**変更した関数は `show_auto_page` と `show_auto_article_page` の2つだけ**（各1行＋コメント）。
新規／消失関数0。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` /
`masters/shimazu_渋谷新館.json` はすべて無変更。**

### ⑩ 今回の通信

**WordPress 通信0件**（GET / POST / PUT / PATCH / DELETE / media upload / draft作成すべてなし）。
Cloud Reboot もなし。実データでの⑧実行もしていない。

### ⑪ 今後の禁止事項

1. **一時フォルダ → `output_dir` の移動を `os.rename` へ戻さない**（Windowsで再実行が落ちる）
2. **`shutil.move` や `os.remove(dst)` + rename の二段階処理へ置き換えない**
3. **無関係な `os.rename` / `os.replace` を一括で書き換えない**
4. **衝突回避のためにファイル名へ suffix / timestamp / 連番を足さない**
5. **列画像に専用の移動・削除処理を作らない**（並びと同じループで扱う）
6. **`output_dir` を毎回 `rmtree` する方式にしない**（他カテゴリの成果物やユーザー配置物を消す）
7. **「既存ファイルを手動削除してから実行」を解決策にしない**
8. **渋谷新館だけの店舗特例にしない**（記事用は共通経路として直す）
9. **`convert_narabi_pil.py` の出力先・ファイル名規則を変えない**
10. **高田馬場の WordPress 本文HTML MD5 `c35ac89ea13c` を壊さない**
11. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用①冒頭：ギルドポスト Xリンク（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用①冒頭部分だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館の記事冒頭にギルドX投稿を追加`・2026-09-04・
**`streamlit_app.py` / `wp_client.py` / `CLAUDE.md` の3ファイルのみ**）。
**高田馬場・秋葉原の記事用は本文HTMLを含め完全に不変。**

### ① 正式な出力順（渋谷新館の記事冒頭）

```
その日の見出し
  ↓
ポスター（あれば）
  ↓
ポスター下の文章
  ↓
ギルドポスト Xリンク（X投稿の埋め込み）      ★新規
  ↓
Xリンク下の文章
  ↓
ななこポスト（H2「ななこポストに仕掛けのヒントを確認！」以下）
  ↓
H2 全台系濃厚機種が複数（以降は従来どおり）
```

**渋谷新館では、旧「X手貼り用の空段落×3」を廃止する。**
代わりにURL入力欄からX投稿を自動で埋め込む。

**高田馬場・秋葉原は従来どおり空段落×3を維持する。**
**`X_EMPTY_PARAS = 3` を変更しない。**

**`H2 差枚数ランキング&島図` のランキングと島図の間にある空段落×5
（`RANK_SHIMAZU_GAP_PARAS = 5`）は別仕様。今回いっさい変更していない。**

### ② 店舗ゲートと新規保存キー

```python
# streamlit_app.py
_ART_GUILD_X_STORES = frozenset({"渋谷新館"})
```

| キー | 内容 |
|---|---|
| **`art_guild_x_url_{store}`（新規）** | ギルドポストのX投稿URL |
| `art_wp_top_text_x_{store}`（**既存を流用**） | 「Xリンク下の文章」 |

- **「Xリンク下の文章」に新しいキーを作らない。**既存 `art_wp_top_text_x_{store}` を正式流用する。
- `_article_input_keys(store)` へ **`art_guild_x_url_{store}` の1キーだけ**追加し、
  既存の **`article_page_inputs.json`（Excelファイル名＝日付でスコープ）** に保存する。
  **新しい保存ファイル・新しい保存関数を作らない。**
- `on_change` は既存の **`_save_article_inputs`／`args=(store, True)`＝`skip_kojin=True`**
  （②個別画像を巻き込まない・`0e7dc4c` の正式仕様）。
- UIは **`_ART_GUILD_X_STORES` の店舗だけ**縦並び（ポスター下文章 → ギルドX → Xリンク下文章）で表示し、
  **対象外店舗は従来の2カラム表示・従来キャプションのまま**。

### ③ ★ `plan_blocks()` は店舗名で分岐しない（payload 駆動）

```python
_has_guild_key = "guild_x" in payload
_guild_x = normalize_x_url(payload.get("guild_x")) if _has_guild_key else ""
...
if _has_guild_key:
    if _guild_x:
        plan.append({"type": "embed_x", "url": _guild_x})
else:
    for _ in range(X_EMPTY_PARAS):
        plan.append({"type": "empty_para"})
```

- **`guild_x` キーを渡した店舗だけ**が「空段落×3 → X埋め込み」へ切り替わる。
- **高田馬場・秋葉原は `guild_x` キー自体を渡さない**ので、
  `empty_para` × 3 の従来動作が完全に維持される（実測で3個を確認）。
- **`plan_blocks()` に `store == …` の判定を入れてはならない。**

### ④ X埋め込みは既存関数を再利用（新しいX処理を作らない）

**`normalize_x_url()` と `blk_embed_x()` をそのまま使う。**
**ギルドポスト専用のURL処理・専用のembedブロック生成関数を新設しない。**

| 項目 | 正式仕様 |
|---|---|
| 入力できるホスト | **`x.com` / `twitter.com` の両方** |
| WordPress embed のホスト | **`twitter.com` へ統一**（`_X_EMBED_HOST`） |
| `providerNameSlug` | **`"x"`** |
| status ID | **維持**（書き換えない） |
| query / fragment | **除去** |
| `http://` / `javascript:` / `data:` / 他ドメイン / `/status/` なし / status が非数値 | **拒否＝埋め込まない** |
| 空欄・不正URL | **「URLなし」と同じ扱い**（そのブロックを出さないだけで中止しない） |

**ななこポストのX実装（`34d0244` の正式仕様）は今回いっさい変更していない。**

### ⑤ URL検証の実測（9パターン）

```
https://x.com/slotterguild/status/1234567890123456789        → 埋め込む
https://twitter.com/…/status/1234567890123456789             → 埋め込む
https://x.com/…/status/…?s=20&t=ab                           → クエリ除去して埋め込む
https://x.com/…/status/…#frag                                → フラグメント除去して埋め込む
http://x.com/a/status/1                                      → 埋め込まない
javascript:alert(1)                                          → 埋め込まない
https://evil.com/a/status/1                                  → 埋め込まない
https://x.com/a                                              → 埋め込まない
（空文字）                                                    → 埋め込まない
```

生成される embed 属性は **ホスト `twitter.com` ／ `providerNameSlug":"x"` ／ status ID 維持**。

### ⑥ 実UI日付往復テスト（2026-09-04・全PASS）

**渋谷新館の記事用ページで、実際のUI操作だけで検証した（JSONの直接編集はしていない）。**

| ステップ | 結果 |
|---|---|
| **日付A = 2026/09/03** 取得 → ギルドX欄へ `https://x.com/slotterguild/status/2090764602548367826` を入力 | **`20260903_渋谷新館_20S.xlsx` へ `art_guild_x_url_渋谷新館` として保存** |
| **日付B = 2026/09/02** 取得 | **ギルドX欄は空欄・9/3の値の混入0件**（見出し／ポスター下／Xリンク下／ななこもすべて空） |
| **日付A = 2026/09/03** へ戻す | **URLが完全復元** |

同時に維持を確認した既存キー：
`art_wp_top_heading_渋谷新館`（「3のつく日は仕掛けが満載」）／
`art_wp_top_text_poster_渋谷新館`（「ああああああ」）／
`art_wp_top_text_x_渋谷新館`（「いいいいいいいいい」）／
`art_nanako_url_渋谷新館` ＋ `art_nanako_hint_0〜5_渋谷新館`。

**日付スコープ保存（Excelファイル名単位）が正しく効いていることを実UIで確認済み。**

### ⑦ 高田馬場の非回帰（MD5基準の扱いに注意）

- **過去の正式基準である高田馬場の本文HTML MD5 `c35ac89ea13c` は引き続き有効**であり、
  **削除・上書きしてはならない。**
- 今回の検証では、**HEAD版 `wp_client.py` と現行を同一 payload で比較して完全一致**することを確認した。
  そのとき算出した `1fae8c5ddff2` / `158a937f4a24` は**この検証で使った payload に対する値**であり、
  **新しい正式基準として `c35ac89ea13c` を置き換えるものではない。**
- 高田馬場は **`empty_para` 3個 ／ `embed_x` 0個**（＝空段落×3の従来動作）を実測で確認済み。

### ⑧ HTMLエスケープについて（今回の対象外・誤記しないこと）

- **ギルドポストのX URL** は `normalize_x_url()` の検証を通り、
  embed 属性は `json.dumps`、figure 内URLは `esc()` を通るため**保護されている**。
- 一方、**「ポスター下の文章」「Xリンク下の文章」は既存の `blk_para()` 経由で
  エスケープされない既存仕様のまま**である（今回の追加によって生じた問題ではない）。
  **今回いっさい変更していない。**必要なら**別案件**として調査・承認のうえ対応する。

### ⑨ 無変更（今回いっさい触れていない）

`X_EMPTY_PARAS = 3` ／ `RANK_SHIMAZU_GAP_PARAS = 5` ／
ななこポスト（`NANAKO_*` / `_X_EMBED_HOST = "twitter.com"` / `providerNameSlug="x"` /
`blk_para_hints()` / `NANAKO_MARK_COLOR = #e60012` / `NANAKO_HINT_COUNT = 6`）／
`normalize_x_url()` 本体 ／ `blk_embed_x()` 本体 ／ `esc()` ／
`_ART_WP_STORES = {"高田馬場","渋谷新館"}` ／
`WP_STORE_CATEGORY`（高田馬場 24 / `espace-takadanobaba`・渋谷新館 19 / `espace-shibuyashin`）／
`WP_NOSPLIT_FILES = {"島図.jpg"}` ／ `WP_MAX_SIDE = 2560` ／ `WP_STATUS = "draft"` ／
`WP_AUTHOR_ID = 14` ／ `_ART_HQ_STORES` ／ `_ART_ZH_HQ_STORES` ／ `_ART_NARABI_HQ_STORES` ／
`_ART_RANK_HQ_STORES` ／ `_ART_SHIMAZU_TARGET_KB = 3000` ／ `_ART_HQ_TARGET_KB = 5500` ／
`bceda28` の島図右端黒帯104px削除 ／ 抽出条件 ／ パネル ／ 液晶 ／ スランプ ／ ZIP ／
Pision取得 ／ 機種名変換。

**`convert_narabi_pil.py` / `shimazu_renderer.py` / `masters/shimazu_渋谷新館.json` は無変更。**
**`MEMORY.md` は今回変更していない。**

### ⑩ 今回のWordPress通信

**0件。** GET / POST / PUT / PATCH / DELETE / media upload / draft作成のいずれも未実行。
**Cloud Reboot もなし。**検証はすべてローカルのモックと実UI操作で行った。

### ⑪ `article_page_inputs.json` の扱い

実UI日付往復テストにより `20260903_渋谷新館_20S.xlsx` へ
`art_guild_x_url_渋谷新館` が保存され、同ファイルは dirty になっている。

- **この commit には含めない**（commit 対象は
  `streamlit_app.py` / `wp_client.py` / `CLAUDE.md` の3件のみ）。
- **`reset` / `restore` / `checkout` で戻すことも禁止。**そのまま未stageで保護する。
- 以後アプリの `_git_auto_push()` により自動commitされた場合は、
  **その時点のHEADを正として扱い、過去HEADへ戻さない。**

### ⑫ 今後の禁止事項

1. **渋谷新館で空段落×3を復活させない**（X埋め込みへ置き換え済み）
2. **高田馬場・秋葉原の空段落×3を削らない／`X_EMPTY_PARAS = 3` を変更しない**
3. **`RANK_SHIMAZU_GAP_PARAS = 5` を今回の理由で変更しない**
4. **`plan_blocks()` に店舗名の分岐を入れない**（`guild_x` キーの有無で判定する）
5. **「Xリンク下の文章」に新しいキーを作らない**（`art_wp_top_text_x_{store}` を流用）
6. **ギルドX専用のURL処理・embed生成関数を新設しない**
   （`normalize_x_url()` / `blk_embed_x()` を再利用）
7. **embed のホストを `x.com` へ戻さない**（`twitter.com` を維持）
8. **`providerNameSlug` を `"twitter"` へ変えない**
9. **status ID / path を書き換えない／query・fragment 除去をやめない**
10. **不正URLをそのまま embed しない**
11. **ななこポストの既存X実装を変更しない**
12. **保存に新しいJSONを作らない**（`article_page_inputs.json` の日付スコープを維持）
13. **`skip_kojin=True` を外さない**
14. **高田馬場の本文HTML MD5 `c35ac89ea13c` を削除・上書きしない**
    （`1fae8c5ddff2` / `158a937f4a24` を新しい正式基準にしない）
15. **`article_page_inputs.json` を今回の commit へ含めない／reset・restore・checkout しない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 WordPress：記事用画像をすべて1枚絵で送る（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用WordPress送信時の画像分割だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館のWordPress画像をすべて1枚絵に変更`・2026-09-04・
**`wp_client.py` と `CLAUDE.md` の2ファイルのみ**・`wp_client.py` は **+19 / −2**・3ハンク）。
**`streamlit_app.py` は今回いっさい変更していない。**

### ① 発端（実WordPress記事の確認結果）

島図は既に1枚絵で送っていたが、**高配分・差枚数ランキングなどの縦長画像は
Python側で複数枚へ分割**されており、記事上でクリック拡大しても
**片方しか開けず画像全体を1枚で確認できなかった。**

### ② 正式仕様

**渋谷新館の記事用WordPress画像は、高さに関係なくPython側で分割しない。**

```
元画像1ファイル → WordPress media 1件 → Gutenberg wp:image 1個
```

- **高さ2560px超でも分割しない。**
- **渋谷新館では `split_image_for_wp()` を1度も呼ばない。**
- 対象は**渋谷新館の記事用WordPress画像すべて**：
  ポスター／全台系／高配分／末尾／並び／列／ジャグラー／その他優秀台／
  ⑤オススメ／差枚数ランキング／島図。
- **今後、機種名・掲載台数・画像サイズが変わっても渋谷新館なら自動的に nosplit**
  になる**店舗単位仕様**とする。**ファイル名列挙方式にはしない。**

### ③ 正式 gate（`WP_NOSPLIT_FILES` とは独立・統合禁止）

```python
_ART_WP_NOSPLIT_STORES: "frozenset[str]" = frozenset({"渋谷新館"})
```

| 定数 | 単位 | 値 | 役割 |
|---|---|---|---|
| **`WP_NOSPLIT_FILES`** | **ファイル名** | **`{"島図.jpg"}`（不変）** | 島図だけを全店舗で1枚絵にする既存例外 |
| **`_ART_WP_NOSPLIT_STORES`** | **店舗** | **`{"渋谷新館"}`** | その店舗の**全画像**を1枚絵にする |

**両者は別仕様として独立に維持する。**
**「店舗gateがあるからファイル名gateは不要」と整理・統合・削除してはならない。**

### ④ `plan_split()` の正式仕様

```python
def plan_split(found, tmp_dir, store: str = "") -> dict:
    from PIL import Image
    result: dict[str, list[dict]] = {}
    if store in _ART_WP_NOSPLIT_STORES:
        return result                    # ← 早期return（空dict）
    ...  # 以降は従来のまま（WP_NOSPLIT_FILES → needs_split → split_image_for_wp）
```

- **早期returnにより `WP_NOSPLIT_FILES` / `needs_split()` / `split_image_for_wp()` の
  いずれへも進まない。**
- **`store` の既定は `""`。**引数を渡さない呼び出しは**完全に従来動作**。
- **対象外店舗（高田馬場）は従来どおり**。

### ⑤ `create_takadanobaba_draft()` の正式仕様

```python
split_map = plan_split(found, tmp_dir, store=_store)
```

`_store = payload.get("store", WP_STORE)` は**同関数内の先頭付近で既に確定済み**
（カテゴリ解決に使っている値）なので、**store情報の受け渡しに波及は無い**。
**`plan_split()` の呼び出し元はリポジトリ全体でこの1箇所だけ**
（`streamlit_app.py` は `collect_files()` しか呼ばず、送信前プレビューの「送信対象 N枚」も
分割前の枚数）。

### ⑥ 分割判定の正確な条件（誤認しないこと）

**分割は「カテゴリだから」ではなく、例外なく「高さ > 2560px だから」である。**

```python
def needs_split(w, h, max_h=WP_SPLIT_MAX_H) -> bool:   # WP_SPLIT_MAX_H = WP_MAX_SIDE = 2560
    return h > max_h            # 幅・ファイル名・カテゴリ・店舗は見ていない
```

したがって高配分・並び・列などは**掲載台数が増えて高さが2560を超えた日だけ分割**されていた
（日によって挙動が変わる状態だった）。**この関数は今回変更していない。**

### ⑦ WordPress側の `-scaled.jpg` は許容

今回禁止したのは **Python側の `split_image_for_wp()` による複数ファイル化**だけ。

```
元画像1枚 → media 1件 → 必要ならWordPress内部で -scaled.jpg 生成   … OK（正式）
元画像1枚 → Python側で2〜4枚へcrop → media 複数件                  … 渋谷新館では禁止
```

渋谷新館では長辺2560px超の画像がサイト側で縮小され `-scaled.jpg` が作られるが、
**画像全体を1枚絵として拡大できることを優先する**（島図と同じ考え方）。

### ⑧ ローカル検証結果（2026-09-04・WordPress通信0件）

合成画像14枚（実サイズに準拠）で実測。

**渋谷新館（`store="渋谷新館"`）**

```
split_map                 : {}（空dict）
split_image_for_wp 呼び出し : 0回（一時フォルダの生成ファイルも0件）
元画像 14件 → 送信 media 14件（完全一致）
SHA256 : 全件が原本と一致／送信パスは元ファイルそのもの
JPEG再圧縮・crop : なし
```

| 画像 | サイズ | 結果 |
|---|---|---|
| 高配分（2560超） | 1985×2900 | **1 media** |
| 末尾 | 1460×4598 | **1 media** |
| 並び（2560超） | 2062×2600 | **1 media** |
| 列（2560超） | 2062×3000 | **1 media** |
| ジャグラー統合 | 1985×2971 | **1 media** |
| その他優秀台 | 2160×8934 | **1 media** |
| 差枚数ランキング | 2181×4638 | **1 media** |
| 島図 | 3451×6490 | **1 media** |

ポスター／全台系／高配分2560以下／並び・列の通常サイズ／⑤オススメも**すべて1 media**。
`build_content()` は `split_map` が空のとき単一ブロック分岐へ入り、
**`wp:image` は1個・連結クラスなし**であることも確認済み。

**送信media数「14」はコードに固定していない**（gate は店舗のみで判定するため、
記事内容により枚数は変動する）。

### ⑨ 高田馬場の非回帰（実測）

```
2560以下 → 従来どおり1枚 ／ 2560超 → 従来どおり分割
split_image_for_wp 呼び出し数 : 7回（store指定あり／なしで同数）
分割数・分割後ファイル名・寸法 : store指定あり／なし（＝修正前の呼び方）で完全一致
WP_NOSPLIT_FILES の島図例外   : 維持（高田馬場でも島図は1 media）
```

**本文HTMLは HEAD版 `wp_client.py` と現行を同一payloadで比較して完全一致。**

**過去の正式基準 `c35ac89ea13c` はそのまま正式基準として残す。**
今回の検証payloadで出た `1fae8c5ddff2` / `158a937f4a24` は
**その検証payloadに対する値であり、正式基準へ置き換えない。**

### ⑩ 無変更（本体バイト一致を機械確認）

`needs_split()` ／ `split_count()` ／ `split_image_for_wp()` ／ `collect_files()` ／
`build_content()` ／ `blk_image()` ／ `plan_blocks()` ／ `build_title()` ／
`upload_media()` ／ `create_draft()` ／ `build_poster()` ／ `_existing_files()` ／
`blk_embed_x()` ／ `normalize_x_url()` ／ `blk_para_hints()`。

定数も不変：`WP_NOSPLIT_FILES = {"島図.jpg"}` ／ `WP_MAX_SIDE = 2560` ／
`WP_SPLIT_MAX_H = 2560` ／ `WP_STATUS = "draft"` ／ `WP_AUTHOR_ID = 14` ／
`_ART_WP_STORES = {"高田馬場","渋谷新館"}`（**秋葉原は対象外のまま**）／
`WP_STORE_CATEGORY`。

**画像生成仕様は完全に不変**：画像生成サイズ／native 2x／JPEG quality／subsampling／
正式ファイル名／`_ART_HQ_STORES`・`_ART_ZH_HQ_STORES`・`_ART_NARABI_HQ_STORES`・
`_ART_RANK_HQ_STORES` の**HQ gate 4種**／島図 3451×6490／`_ART_SHIMAZU_TARGET_KB = 3000`／
スランプ／パネル／液晶／`os.replace`。**nosplit gate と HQ gate を統合しない。**

**X関連・本文仕様も不変**：ななこX／ギルドX／`_X_EMBED_HOST = "twitter.com"`／
`providerNameSlug="x"`／ギルドXリンク下文章／渋谷新館の旧空段落×3廃止／
**高田馬場の空段落×3維持（`X_EMPTY_PARAS = 3`）**／
**ランキング&島図の空段落×5（`RANK_SHIMAZU_GAP_PARAS = 5`）**／Gutenberg本文順序。

**新規関数0・消失関数0。**変更関数は `plan_split()` と `create_takadanobaba_draft()` の2つだけ。

### ⑪ 今回の通信

**WordPress 通信0件**（GET / POST / PUT / PATCH / DELETE / media upload / draft作成すべてなし）。
検証はすべてローカルの合成画像とモックで実施。**Cloud Reboot も未実行。**

### ⑫ 今後の禁止事項

1. **渋谷新館でPython側の画像分割を復活させない**
2. **`_ART_WP_NOSPLIT_STORES` と `WP_NOSPLIT_FILES` を統合・整理・削除しない**
3. **`WP_NOSPLIT_FILES = {"島図.jpg"}` を変更しない**
4. **渋谷新館をファイル名列挙方式（`WP_NOSPLIT_FILES` への大量追加）へ切り替えない**
5. **`plan_split()` の `store` 既定値 `""` を変更しない**（対象外店舗の従来動作が壊れる）
6. **早期returnの位置を下げない**（`needs_split()` / `split_image_for_wp()` へ進ませない）
7. **`needs_split()` / `split_count()` / `split_image_for_wp()` 本体を変更しない**
8. **`WP_MAX_SIDE` / `WP_SPLIT_MAX_H` を店舗別にしない／値を変更しない**
9. **高田馬場の分割仕様（分割数・ファイル名・寸法・切れ目・JPEG品質・本文構造）を変更しない**
10. **秋葉原を `_ART_WP_STORES` へ追加しない**
11. **nosplit gate を HQ gate 4種と統合しない**
12. **画像生成側（サイズ・2x・quality・subsampling・ファイル名・島図・スランプ・パネル・液晶）を変更しない**
13. **X関連・空段落仕様・Gutenberg本文順序を変更しない**
14. **高田馬場の本文HTML MD5 `c35ac89ea13c` を削除・上書きしない**
15. **WordPress側の `-scaled.jpg` 生成を理由にサイト設定・PHP・テーマ・サーバー設定を変更しない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用：WordPress投稿者の選択（2026-09-04）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用ページと、その WordPress 下書きの
投稿者（author）だけ**。正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館のWordPress投稿者選択を追加`・2026-09-04・
**`streamlit_app.py` / `wp_client.py` / `CLAUDE.md` の3ファイルのみ**・
`streamlit_app.py` +60/−2・`wp_client.py` +41/−3）。
**高田馬場は投稿者UIを持たず、従来どおり `WP_AUTHOR_ID = 14` 固定**（本文HTMLも不変）。

### ① 修正前の状態

`author` は **payload にも `create_takadanobaba_draft()` にも存在せず**、
`create_draft()` の中でモジュール定数を直接参照していた（`"author": WP_AUTHOR_ID`）。
そのため**高田馬場・渋谷新館とも user_id 14（`t.ui`）固定**だった。

### ② UI（渋谷新館のみ・①冒頭部分より上）

```
WordPress投稿者
  ○ t.ito
  ○ r.iio
  ○ k.furukawa
  ○ t.ui
  ○ m.suzuki
  ○ m.takahashi
① 冒頭部分
```

- **`st.radio()` の縦並び**（`horizontal` は指定しない）。**1名だけ選択可能。**
  チェックボックス6個で排他制御する実装にはしない。
- **初期状態は未選択**（`index=None`）。**勝手に `t.ui` 等を初期選択しない。**
- **番号外のブロック**として `st.markdown(f"### {_sec_num()} …冒頭部分…")` の**直前**に置く。
  `_sec_num()` はカウンタ方式なので**①〜⑦の採番はずれない**（手書きしない）。
- 未選択のときは `⚠️ 投稿者が未選択です。選択するまで WordPress下書きは作成できません。`
  をキャプション表示する。

**店舗ゲート（既存gateと統合しない）**

```python
_ART_WP_AUTHOR_STORES = frozenset({"渋谷新館"})
_ART_WP_AUTHORS = ("t.ito", "r.iio", "k.furukawa", "t.ui", "m.suzuki", "m.takahashi")
```

**高田馬場・秋葉原には表示しない。`_ART_WP_STORES` は変更しない**（秋葉原はWordPress対象外のまま）。

### ③ username → 正式 WordPress user ID（推測禁止）

**2026-09-04 に `GET /wp-json/wp/v2/users?per_page=100&page=1&context=edit` で実測**
（参照のみ・変更通信0件・15件取得）。`username` / `slug` / `name` の3つが一致した値を採用した。

```python
# wp_client.py（store_category() の直後）
WP_AUTHOR_MAP: "dict[str, int]" = {
    "t.ito":       13,
    "r.iio":        8,
    "k.furukawa":   4,
    "t.ui":        14,   # 既存記録（CLAUDE.md）の WP_AUTHOR_ID = 14 と一致
    "m.suzuki":     7,
    "m.takahashi":  2,
}
```

- **仮ID・推測IDは1件も入れていない。**
- **`t.ui` = 14** は既存記録（「投稿者 `t.ui` = user_id 14 を管理画面で確認」）と一致しており裏付けがある。
- 同サイトには他にも 'i.sasaki'(1) / 'd.okazaki'(3) / 'k.nomura'(5) / 'm.oomori'(6) /
  'r.saito'(9) / 's.yamashina'(11) / 't.hoshino'(12) / 't.yamashina'(15) / 's.azuma'(16)
  が存在するが、**今回の対象は上記6名だけ**。**IDを推測で追記してはならない**
  （別人の投稿になる）。追加が必要なら管理画面か GET で確認した値だけを足す。

### ④ 保存・復元（日付＝Excel単位）

| 項目 | 値 |
|---|---|
| 保存キー | **`art_wp_author_{store}`**（渋谷新館は `art_wp_author_渋谷新館`） |
| 保存値 | **username の文字列**（例 `"t.ito"`）。**user ID は保存しない** |
| 保存先 | 既存 **`article_page_inputs.json`**（Excelファイル名＝日付でスコープ） |
| 保存 | 既存 **`_save_article_inputs(store, True)`**（**`skip_kojin=True` 必須**・②個別画像を巻き込まない） |
| 復元 | 既存 **`_restore_article_inputs()`** |

- `_article_input_keys(store)` へ**1行追加**しただけ。
  **`_save_article_inputs()` / `_restore_article_inputs()` の本体は変更していない。**
- **未保存の日付は未選択。別日付の投稿者を引き継がない。**
- **user ID ではなく username を保存する理由**: JSONを人が読んで分かる／サイト側でIDが
  変わっても `WP_AUTHOR_MAP` 1箇所で追従できる／未保存既定が `""` の既存文字列経路と整合する
  （ID保存だと `0` や `""` と「未選択」の区別が曖昧になる）。

### ⑤ ★初期値の解決（キーの有無で判定しない）

**「session_state にキーがあるから前回値を使う」判定にしてはならない。必ず値の妥当性で判定する。**

```python
_au_key = f"art_wp_author_{store}"
if st.session_state.get(_au_key) not in _ART_WP_AUTHORS:
    _au_saved = _art_kojin_default(st.session_state.get("art_current_excel"),
                                   store, _au_key)
    st.session_state[_au_key] = _au_saved if _au_saved in _ART_WP_AUTHORS else None
```

**2つの構造的理由から、この seed は省略できない。**

1. `_restore_article_inputs()` は未保存キーへ **`""`** を入れる。
   **Streamlit の radio は session_state 値が options に無いと例外**になるため、
   `""` → `None` の変換が必要。
2. radio は **widget キー**なので、未描画の run を挟むと
   **stale widget GC で session_state から消える**。session_state だけを見ると
   GC 後に「未選択」へ化け、その `None` が保存されて**保存済み値を潰す**
   （②個別画像 `0e7dc4c`・⑤ `39f1f1e`・⑥ランキング `39b652d` と同型の事故）。

フォールバックには**新しい復元経路を作らず**、既存の**読み取り専用ヘルパー
`_art_kojin_default()`**（該当Excelエントリを読むだけ・str用）を再利用する。
**`""` / `None` / 未知 username は必ず未選択（`None`）へ落とす**ので、
勝手な選択の復活は起きない。

### ⑥ 送信時の author は「送信直前の選択値」

**⑧実行時点では投稿者を固定しない。**

```
⑧実行 → 投稿者を変更 → WordPress下書きを作成
  → 変更後の投稿者が author になる
```

実装は **WordPress下書きブロックの入口**（ボタン描画の直前）で

```python
if store in _ART_WP_AUTHOR_STORES:
    _wp_author = st.session_state.get(f"art_wp_author_{store}") or ""
    if _wp_author not in _ART_WP_AUTHORS:
        _wp_author = ""
    _wp_pl["author_user"] = _wp_author
```

**⑧の payload 構築（`build_payload()` 直後のブロック）へ author を入れてはならない**
（⑧時点で凍結すると、選び直した投稿者が反映されず**古い投稿者で送る事故**になる）。

### ⑦ payload 駆動（`plan_blocks` と同じ思想・店舗名を2ファイルへ重複させない）

**`author_user` キーを payload へ渡した店舗だけが投稿者必須**になる。
`wp_client.py` 側に店舗名リストを持たせない（`_ART_WP_AUTHOR_STORES` の二重管理を避ける）。

```python
# create_takadanobaba_draft() … カテゴリ検証の直後
_author_id = WP_AUTHOR_ID
if "author_user" in payload:
    _au = str(payload.get("author_user") or "").strip()
    _author_id = WP_AUTHOR_MAP.get(_au, 0)
    if not _author_id:
        return {"ok": False, "stage": "config", "uploaded": [], "error": …}
```

**高田馬場は `author_user` キーを渡さない**ので `WP_AUTHOR_ID`（14）のまま。

### ⑧ 未選択時は下書きを作らない（二重防御・フォールバック禁止）

| 層 | 実装 |
|---|---|
| **UI** | `st.button(..., disabled=… or _wp_no_author)` ＋ `❌ WordPress投稿者が未選択です` を表示 |
| **wp_client** | `create_takadanobaba_draft()` の**カテゴリ検証の直後**（`plan_blocks()` / `collect_files()` / `plan_split()` / `upload_media()` より**前**）で中止 |

返却は **`ok=False` / `stage="config"` / `uploaded=[]`**。
**`WP_AUTHOR_ID`（14）へのフォールバックは禁止。**未知 username も同じく中止する。

### ⑨ `create_draft()` の最小変更

```python
def create_draft(title, content, category_id=WP_CATEGORY_ID,
                 author_id: int = WP_AUTHOR_ID) -> dict:
    ...
    "author": int(author_id),
```

**既定は `WP_AUTHOR_ID`（14）**なので、**引数を渡さない呼び出しは修正前と同じ POST body**。
**`WP_AUTHOR_ID = 14` の定義は削除・変更しない**（高田馬場の非回帰の土台）。

### ⑩ ローカル検証結果（2026-09-04・WordPress通信0件）

`upload_media` / `create_draft` を spy へ差し替え、**実HTTPを発生させずに**確認した。

| 確認 | 結果 |
|---|---|
| 渋谷新館の6名 | **13 / 8 / 4 / 14 / 7 / 2**（`category=[19]`・`ok=True`） |
| 未選択（空文字・None）／未知 username | **`ok=False` / `stage="config"` / `uploaded=0` /
`upload_media` 0回 / `create_draft` 0回 / `plan_split` 0回** |
| 高田馬場 | **author=14 / category=[24]** |
| `create_draft` 引数省略 | **author=14** |
| UI表示判定 | 渋谷新館のみ True（高田馬場・秋葉原・新小岩は False） |

**日付往復（実関数 `_restore_article_inputs()` / `_save_article_inputs()` /
`_art_kojin_default()` を使用・`article_page_inputs.json` は一時ファイルへ差し替え）**

```
日付A 9/3（未保存）→ 未選択
日付A で t.ito 選択 → JSON へ "t.ito" 保存（②個別キーを巻き込まない）
日付B 9/2         → 未選択・t.ito の混入0（Bで保存してもAは無傷）
日付A へ戻す      → "t.ito" 完全復元
日付A で m.suzuki へ変更 → JSON 更新・送信直前 payload も m.suzuki → ID=7
widget GC を挟む → 保存値 m.suzuki から復元・その後の保存で壊れない
未知値が保存されていた場合 → 未選択へ倒す
日付跨ぎ混入 0件
```

### ⑪ 実UIテストは commit 後に行う（誤記しないこと）

**実 Streamlit UI での日付往復テストは、この commit の時点では未実施である。**
**「実UIで確認済み」と書かない。**

理由：`_git_auto_pull()` は**起動時に無条件で `git stash` を実行**する。未コミットの実装2ファイルと
**保護対象（`wrt_machines.json` / `article_page_inputs.json`）・stash 4件**を巻き込むため、
未コミット状態でアプリを起動しない判断とした（`55e7752` の必須ルールと同じ）。
正式手順は **コードを commit / push → アプリ再起動 → 実UIで日付往復テスト**
（`00a472a` と同じ順序）。

### ⑫ 非回帰（本体バイト一致を機械確認）

**高田馬場の本文HTMLは HEAD版と完全一致。**
（正式基準 **`c35ac89ea13c` はそのまま維持**。検証payloadで出た `1fae8c5ddff2` /
`158a937f4a24` を新しい正式基準へ置き換えない。）

バイト一致：`plan_split()` ／ `needs_split()` ／ `split_count()` ／ `split_image_for_wp()` ／
`collect_files()` ／ `build_content()` ／ `plan_blocks()` ／ `blk_image()` ／ `blk_embed_x()` ／
`normalize_x_url()` ／ `blk_para_hints()` ／ `upload_media()` ／ `build_poster()` ／
`build_payload()`。**新規関数0・消失関数0。**

不変の定数：**`_ART_WP_NOSPLIT_STORES = {"渋谷新館"}`（全画像1枚絵）** ／
`WP_NOSPLIT_FILES = {"島図.jpg"}` ／ `WP_MAX_SIDE = 2560` ／ `WP_STATUS = "draft"` ／
`WP_AUTHOR_ID = 14` ／ `WP_STORE_CATEGORY`（高田馬場24・渋谷新館19）／
`_ART_WP_STORES = {"高田馬場","渋谷新館"}` ／ `X_EMPTY_PARAS = 3` ／
`RANK_SHIMAZU_GAP_PARAS = 5` ／ `_X_EMBED_HOST = "twitter.com"` ／
`NANAKO_MARK_COLOR = "#e60012"` ／ **HQ gate 4種**（`_ART_HQ_STORES` /
`_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` / `_ART_RANK_HQ_STORES`）／
`_ART_SHIMAZU_TARGET_KB = 3000`。

ギルドX ／ ななこX ／ `providerNameSlug="x"` ／ ランキング&島図 ／ 空段落×5 ／
画像生成処理 ／ 島図 ／ スランプ ／ パネル ／ 液晶 も**すべて無変更**。
`convert_narabi_pil.py` / `shimazu_renderer.py` / `masters/shimazu_渋谷新館.json` も無変更。

### ⑬ 今回の通信

**WordPress 変更通信0件**（POST / PUT / PATCH / DELETE / media upload / draft作成なし）。
user ID 確認の **GET `/wp/v2/users` を1回**だけ実施（参照のみ）。**Cloud Reboot も未実行。**

### ⑭ 今後の禁止事項

1. **未選択時に `WP_AUTHOR_ID`（14）へフォールバックしない**
2. **未知 username を黙って通さない**（必ず中止）
3. **UI側の disabled だけにしない**（`wp_client` の二重防御を外さない）
4. **停止位置を `upload_media()` の後ろへ下げない**（画像0件で止める）
5. **⑧実行時点で author を固定しない**（送信直前の選択値を使う）
6. **保存値を user ID へ変えない**（username を保存する）
7. **初期値を「キーの有無」で判定しない**（値の妥当性で判定する）
8. **widget GC 用の seed フォールバックを外さない**／`_art_kojin_default()` 以外の
   新しい復元経路を増やさない
9. **未保存日付に別日付の投稿者を引き継がない**
10. **`_save_article_inputs()` の `skip_kojin=True` を外さない**
11. **`WP_AUTHOR_ID = 14` / `create_draft()` の `author_id` 既定を変更しない**
12. **`WP_AUTHOR_MAP` へ推測IDを追記しない**（管理画面か GET で確認した値だけ）
13. **高田馬場へ投稿者UIを追加しない／本文HTML MD5 `c35ac89ea13c` を壊さない**
14. **秋葉原を `_ART_WP_STORES` / `_ART_WP_AUTHOR_STORES` へ追加しない**
15. **`_ART_WP_AUTHOR_STORES` を既存gate（`_ART_WP_NOSPLIT_STORES` / HQ gate 4種）と統合しない**
16. **`wp_client.py` 側へ店舗名リストを持たせない**（payload 駆動を維持）
17. **nosplit・X関連・ランキング&島図・空段落・画像生成処理を今回の理由で変更しない**
18. **「実UIで日付往復を確認済み」と誤記しない**（commit 後に実施する）
19. **無関係なリファクタ・未使用コード整理をしない**

## 記事用：日付切替時の保存値上書きと表示defaultの自動保存を修正（2026-09-03 確定・`62168f1` / `7d6cdfa`）

**正式仕様。巻き戻し禁止。**対象は**記事用ページ（高田馬場・渋谷新館・秋葉原）の
日付依存保存widgetだけ**。正式コード commit は

| commit | 内容 |
|---|---|
| **`62168f1cdc6ef55e5a79b19b79b9b38731a9ca97`** | `fix: 記事用の日付切替で保存値が上書きされる問題を修正`（案A ＋ B2） |
| **`7d6cdfa3571047de1b5a8c1caf3bb7ff941c7cc4`** | `fix: 記事用の既定タイトルが自動保存される問題を修正`（表示default副作用） |

いずれも **`streamlit_app.py` のみ**。**`wp_client.py` / `article_page_inputs.json` /
`wrt_machines.json` は無変更。**

### ① 実事故（2026-09-03・渋谷新館）

```
9/2 → ⑧実行 → ページ/セッション遷移 → 9/3 → 🔄取得
```

の付近で、**9/3 の保存済み値が 9/2 側の 空／default 値で上書きされた。**

**破壊された11キー**

```
art_wp_top_heading_渋谷新館
art_wp_top_text_poster_渋谷新館
art_wp_top_text_x_渋谷新館
art_guild_x_url_渋谷新館
art_nanako_url_渋谷新館
art_nanako_hint_0_渋谷新館
art_nanako_hint_1_渋谷新館
art_narabi_enabled
art_suebangai_enabled
art_wp_author_渋谷新館
art_ranking_limit_渋谷新館
```

当時の 9/3 は正常値 **86キー**で、**11キーだけが破壊され、他75キーは正常**だった。

### ② 根本原因（restore順序だけではない）

**Streamlit の stable widget key を日付を跨いで使い回していたこと**が真因。

```
新日付を restore
  ↓
ブラウザ側に残っていた旧日付の widget 値が、同じ key へ返る
  ↓
on_change callback が発火
  ↓
旧日付値 → logical session_state → _save_article_inputs() → 新日付JSON
```

したがって **`_restore_article_inputs()` 完了後の scope guard だけでは防げない。**

### ③ 案A（正式・ただし二次防御）

`_restore_article_inputs()` 完了時に**現在 restore 済みの Excel を記録**し、
保存時に **`current excel == restored excel`** を確認する。
**scope 不一致なら記事用の保存を拒否する。**

```python
# _save_article_inputs() 冒頭
if st.session_state.get("_art_restored_excel") != excel_name:
    return
# _restore_article_inputs() 末尾
st.session_state["_art_restored_excel"] = excel_name
```

**これは二次防御であり、単独では形(b)（ブラウザ旧値エコーバック）を防げない。**
**案A単独へ戻さないこと。**

### ④ B1 は正式不採用

**同じ widget key のまま `value=` / `index=` だけを入れ替える方式は採用しない。**

理由：**Streamlit 1.56 は、key が既に session_state にある場合 `value=` を無視する**
（`SessionState._getitem` の優先順位 `_new_session_state` ＞ `_new_widget_state` ＞ `_old_state`。
`elements/lib/policies.py` の警告も同じ意味）。
`value=` / `index=` だけでは、ブラウザ／既存 widget 状態との競合を完全には防げない。

**★ 過去記録の supersede**：本 CLAUDE.md には
**「初期値は `value=default` でフロントへ渡す（`39f1f1e`）」「②も `default=` で渡す（`0e7dc4c`）」**
という正式記録がある。**これらの節は削除・書き換えしない**（当時の正式仕様として正しく、
⑤・②の全消し事故を止めた修正である）。
ただし **「`value=` を渡していれば日付跨ぎでも安全」という解釈は、今回の実事故により
記事用の日付依存 widget については正式に supersede された。**
`value=` は **key が session_state に無いときだけ**効くため、
**日付を跨いで同じ widget key を使い回す限り、`value=` だけでは保存値を守れない。**

### ⑤ B2（正式仕様）

記事用の日付依存保存 widget は、**logical key と 表示 widget key を分離**する。

| | key |
|---|---|
| **表示 widget key** | **`_artw_{excel_stem}_{logical_key}`**（日付／Excel ごとに widget identity が変わる） |
| **logical key** | **従来キーを維持**（JSON schema も従来のまま） |

```python
def _art_widget_key(excel_name, logical_key) -> str:
    _stem = os.path.splitext(str(excel_name or "_none"))[0]
    return f"_artw_{_stem}_{logical_key}"
```

- **`_artw_*` は JSON へ絶対に保存しない**（`_article_input_keys()` に入れない）。
- 日付が変われば widget identity も変わるため、**旧日付のブラウザ値が新日付の widget へ
  エコーバックされる経路が構造的に消える。**

### ⑥ B2 の callback

widget 変更時は **display widget → logical key → `_save_article_inputs()`** へ同期する。
callback は **`expected_excel` guard** を持ち、
**旧日付 widget の遅延 callback が来ても現在日付へ保存しない。**

```python
def _on_article_widget_change(store, logical_key, widget_key, expected_excel, skip_kojin=True):
    if st.session_state.get("art_current_excel") != expected_excel:
        return
    ...
```

### ⑦ 対象欄数（正式監査結果）

**記事用の保存対象 stateful widget＝35呼び出し／103欄。すべて B2 対応済み。
危険経路 X＝0。**

### ⑧ autocomplete（記事用60欄）

| 区分 | 欄数 |
|---|---|
| ②全台 | 12 |
| ②優秀台 | 12 |
| ⑤オススメ | 36 |
| **計** | **60** |

- **共通関数 `render_machine_autocomplete_input()` の本体は変更しない。**
- **記事用の3 callsite だけ**が日付スコープ display key を渡す。
  **非記事用17 callsite は変更なし。**
- autocomplete 内部の query / button key も**渡された display key 由来**なので、
  自動的に日付スコープ化される。

### ⑨ 純粋テスト（B2）

```
test_b2   35 PASS
test_b2b  22 PASS
test_b2c  26 PASS
合計      83 PASS / 0 FAIL
```

確認：**危険経路 X=0 ／ 11キー破壊0 ／ 9/3 86/86一致 ／ `_artw_*` の JSON 混入0**。

### ⑩ 実UI確認（`62168f1`・再発なし）

```
9/3 → 9/2 → ⑧ → 記事用離脱 → 高田馬場／秋葉原 → 渋谷新館再入場 → 9/3
```

を実UIで再現した結果：

- **9/3 は 86/86 一致**
- **11キー破壊0**
- **9/2 側の `'' / False / None / 50` が 9/3 へ混入0**
- **高田馬場・秋葉原も例外0**

---

## 表示default の自動保存副作用（`7d6cdfa`）

### ⑪ 事象

B2 導入後、**`art_sonota_extra_title_渋谷新館`** で次の副作用を検知した。

```
raw="" → UI default「その他の優秀台ピックアップ」
      → 毎run の無条件 display→logical 同期
      → 別 widget の save
      → default が JSON へ自動保存
```

**ユーザーは title 欄を編集していなかった。**

### ⑫ 原因

`_art_txt()` の **`st.session_state[logical] = _cur` 相当の無条件同期**。
`empty_default` を使う **`art_sonota_extra_title` だけ**で新規に発生した。

### ⑬ 正式仕様

`raw == ""` のとき：

| | 値 |
|---|---|
| UI 表示 | **「その他の優秀台ピックアップ」** |
| logical | **`""`** |
| JSON | **`""`** |

- **別 widget の操作だけでは default を保存しない。**
- **ユーザーが title 欄を実際に編集したときだけ** display → logical → JSON へ保存する。
- **ユーザーが明示的に「その他の優秀台ピックアップ」と入力した場合は、正式入力値として保存してよい。**
- **★ 値の一致で「未編集」と判定しない**（`_cur == empty_default` 方式は禁止）。

### ⑭ 正式方式（編集イベント記録）

```python
def _art_edited_key(widget_key: str) -> str:
    return f"_artw_edited_{widget_key}"
```

- **`_art_edited_key()` は session_state 専用。JSON 保存対象外。**
- **`_on_article_widget_change()` で編集済みを記録**する。
- `_art_txt()` は
  **未編集 → raw を維持 ／ 編集済み → display 値を logical へ同期。**

### ⑮ 下流補完（JSON raw="" でも生成物は壊れない）

画像生成・⑦プレビュー・⑧本番は
**`.strip() or "その他の優秀台ピックアップ"`** で補完する（既存仕様）。
したがって **JSON raw="" でも生成物は不変**。
**WordPress は⑧が生成済みのファイルを使うため影響なし。**

### ⑯ 純粋テスト（表示default）

```
新規（test_default） 31 PASS / 0 FAIL
既存B2             83 PASS / 0 FAIL
合計              114 PASS / 0 FAIL
```

確認：**35呼び出し103欄 ／ 危険経路 X=0 ／ 11キー破壊0 ／ 9/3 86/86 ／
`_artw_*` の JSON 混入0**。

### ⑰ 実UI確認（`7d6cdfa`・再発なし）

9/3 の `art_sonota_extra_title_渋谷新館` は **raw=""**。

| 操作 | JSON raw |
|---|---|
| ②ON（UI は「その他の優秀台ピックアップ」を表示） | **`""` 維持** |
| ②OFF | **`""` 維持** |
| 記事用離脱 → 再入場 | **`""` 維持** |
| 9/3 → 9/2 → 9/3 | **`""` 維持** |

**9/3 は 86/86 一致・11キー破壊0。**

### ⑱ 確認状況の正確な記録（誇張しないこと）

**text_input への自動操作ツールの制約により、
「任意タイトルの実入力」「既定文言の明示入力」の2ケースだけは実UI未確認である。**
**「実UI確認済み」と書かない。**
ただし**純粋テスト CASE3 / CASE4 で PASS 済み**。

### ⑲ 既存仕様との関係（今回いっさい変更していない）

本節は**記事用の日付依存 widget の保存安全性に関する追加仕様**であり、次を変更しない。

記事用② ／ ⑤オススメ ／ ⑧本番 ／ 高田馬場 ／ 渋谷新館 ／ 秋葉原 ／ WordPress ／
画像生成 ／ HQ 各 gate ／ 島図 ／ 投稿者選択 ／ X埋め込み ／
`render_machine_autocomplete_input()` 共通helper ／ `_article_input_keys()` の JSON schema ／
通常結果ポスト用 ／ スランプ付き ／ ローテ用。

### ⑳ 今後の禁止事項

1. **記事用の日付依存 widget で stable widget key を日付跨ぎで使い回さない**
2. **B1（同じ key のまま `value=` / `index=` 差し替え）へ戻さない**
3. **案A（scope guard）単独へ戻さない**（B2 とセットで運用する）
4. **`_artw_*` / `_artw_edited_*` を JSON 保存対象へ入れない**
5. **`expected_excel` guard を外さない**
6. **`render_machine_autocomplete_input()` 本体を変更しない／非記事用 callsite を巻き込まない**
7. **表示default を無条件に logical へ同期しない**
8. **値の一致で「未編集」と判定しない**（`_cur == empty_default` 方式の禁止）
9. **ユーザーが明示入力した既定文言を `""` へ落とさない**
10. **下流の `.strip() or "その他の優秀台ピックアップ"` 補完を外さない**
11. **`39f1f1e` / `0e7dc4c` の既存節を削除・書き換えない**（supersede は追記で記録する）
12. **`article_page_inputs.json` の JSON schema・logical キー名を変更しない**
13. **実UI未確認の2ケースを「実UI確認済み」と記録しない**
14. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 WordPress：実環境確認（2026-09-05・draft 62014）

**正式な実環境確認記録。巻き戻し禁止。**対象は**【渋谷新館】の記事用 WordPress 連携だけ**。
本節は**コード変更を伴わない実環境確認の記録**であり、`CLAUDE.md` 以外のファイルは変更していない。
**既存節は削除・圧縮・書き換えしない**（過去の「ランキング2分割」「島図のみ nosplit」
「クリック拡大は未確認」等の記録もそのまま残す）。本節はそれらを **supersede 形式で上書き**する。

### ⓪ supersede 一覧（過去記録は残したうえで、現在の正式はこちら）

| 項目 | 旧記録 | **現在の正式（本節・実環境確認済み）** |
|---|---|---|
| 差枚数ランキング | 「WordPressで2分割する（1枚絵化しない）」 | **1 source = 1 media = 1 block（分割0）** |
| nosplit の範囲 | 「島図だけを1枚絵にする（`WP_NOSPLIT_FILES`）」 | **渋谷新館は全画像 nosplit**（`_ART_WP_NOSPLIT_STORES`）。`WP_NOSPLIT_FILES` は**独立に維持** |
| クリック拡大 | 「`linkDestination:"none"` のため未確認」 | **実ブラウザで確認済み（SWELL の Luminous ライトボックスで1枚全体を表示）** |

### ① 実下書きテストの対象

| 項目 | 値 |
|---|---|
| 店舗 / 日付 | **渋谷新館 / 2026-09-03** |
| post ID | **62014** |
| status | **`draft`** |
| author | **7** |
| category | **19** |
| title | **`9月3日(木)│エスパス渋谷新館│`** |

### ② 投稿者選択の実環境確認

```
UI保存値: m.suzuki  →  WP_AUTHOR_MAP: m.suzuki = 7  →  実draft: author = 7
```

**`author=14` へのフォールバックは未使用。**
渋谷新館の投稿者選択（`art_wp_author_渋谷新館` に username を保存 → 送信直前に user ID へ解決）は
**実環境で機能することを確認済み**。

### ③ ⑧生成の実測

**成功／例外0／WinError183 0／auto commit 発生なし（HEAD不変）。**
WordPress 送信対象：**26画像 / 43.09 MB**。

### ④ 1枚絵 upload の正式確認

渋谷新館は **`_ART_WP_NOSPLIT_STORES` 対象**。実測：

```
plan_split(store="渋谷新館")  →  {}（空dict）
split_image_for_wp            →  0回
```

WordPress 実送信の結果：

| 項目 | 実測 |
|---|---|
| source 画像 | **26** |
| media upload | **26** |
| Gutenberg image block | **26** |
| Python split | **0** |
| 分割痕跡（`_N.jpg`） | **0件** |

**`1 source = 1 media = 1 Gutenberg image block` を実環境で確認済み。**

### ⑤ 長尺画像もすべて1枚絵

**高配分 / 末尾 / 並び・列 / ジャグラー / その他優秀台 / 差枚数ランキング / 島図**の
すべてで `1 source = 1 media = 1 block` を確認した。代表実測（source サイズ）：

```
その他の優秀台ピックアップ.jpg   2161×14252
末尾5番台.jpg                    2161×18035
東京喰種_高配分.jpg              1986×8248
差枚数ランキング.jpg             2181×2878
島図.jpg                         3451×6490
```

### ⑥ WordPress 側の長辺2560px縮小（Python split とは別物）

サイト側がアップロード時に**長辺2560pxへ縮小**する動作を実測した。

| 画像 | source | **WordPress 保存版** |
|---|---|---|
| 島図 | 3451×6490 | **1361×2560** |
| 差枚数ランキング | 2181×2878 | **1940×2560** |
| 末尾5番台 | 2161×18035 | **307×2560** |
| その他の優秀台ピックアップ | 2161×14252 | **388×2560** |
| 東京喰種_高配分 | 1986×8248 | **616×2560** |

**これは許容仕様。** 重要なのは**途中 crop ではなく、画像全体を縦横比維持で縮小**している点。
**Python 側の split（複数ファイル化）とは明確に区別すること。**

### ⑦ 実通信の内訳

```
media upload : 26件
draft create : 1件（ボタンは1回だけクリック）
publish      : 0
update       : 0
delete       : 0
```

作成 draft **62014** は `status=draft` / `author=7` / `categories=[19]`。

### ⑧ 本文構成の実環境確認

実 draft で確認した順序：

```
記事上部 → ギルドX → ななこポスト → 全台系 → 高配分 → 末尾 → 並び・列
→ ジャグラー → その他優秀台 → （⑤オススメ） → 差枚数ランキング&島図 → 店舗情報ボタン
```

**⑤オススメは 9/3 では⑤ブロック未入力・画像0件のため、H2「オススメ機種の優秀台」自体を出さない。**
**これは正式仕様どおりで不具合ではない。**

### ⑨ X埋め込みの実環境確認

| | 入力 | 実 draft の embed |
|---|---|---|
| ギルドX | `x.com/...` | **`twitter.com/...`**・status ID **`2095102999077253437`** 保持 |
| ななこX | `x.com/...` | **`twitter.com/...`**・status ID **`2095096899892031838`** 保持 |

**`providerNameSlug` は `x`。本文中の `x.com` 出現は0件**（すべて `twitter.com` へ正規化済み）。

### ⑩ ヒント表示の実環境確認

**1 Gutenberg paragraph** にまとめ、複数行は **`<br>`** で改行。
各行は **「■＋本文全体」を `<strong style="color:#e60012">` が包む**（**赤 `#e60012` かつ太字**）。

### ⑪ ジャグラーH3の実環境確認

```
H2 ジャグからも高配分機種多数！
  → 個別ジャグラーH3 → 画像
  → H3 その他のジャグラーシリーズの優秀台 → ジャグラーシリーズ優秀台.jpg
```

**orphan H3 は0件。**

### ⑫ 差枚数ランキング&島図の実環境確認

```
H2 差枚数ランキング&島図
  → 差枚数ランキング画像
  → 空段落 × 5
  → 島図画像
```

**単独の「島図」H2/H3 は0件。「シマズをチェック！」も0件。**渋谷新館の正式仕様どおり。

### ⑬ 高田馬場の非回帰

**今回の実通信は渋谷新館のみ。** 高田馬場はコード／plan レベルで従来仕様の維持を確認した。

- **nosplit 対象外**（`_ART_WP_NOSPLIT_STORES` に含まない）
- **高さ > 2560 で split 対象**（`needs_split(1985,2560)=False` / `(1985,2561)=True`）
- **author = 14** ／ **category = 24** ／ **slug = `espace-takadanobaba`**

**正式 baseline `c35ac89ea13c` は基準として維持する。今回変更扱いしない。**

### ⑭ クリック拡大の実環境確認

draft 62014 の WordPress プレビューを**実ブラウザで**確認した。対象5画像
（その他の優秀台ピックアップ / 末尾5番台 / 東京喰種_高配分 / 差枚数ランキング / 島図）は
**すべてクリック可能**（`cursor: zoom-in`）で、クリックすると
**SWELL テーマの Luminous ライトボックスが開き、1枚全体を表示**する。
**途中切り出しなし。分割メディアなし。**

### ⑮ ★クリック拡大の技術的由来（混同しないこと）

**クリック拡大は `blk_image()` のリンク実装ではない。**

| | 実測 |
|---|---|
| `content.raw` の `linkDestination` | **`"none"`（26ブロックすべて）** |
| 画像用 `<a href>` | **0件**（`content.raw` の `<a>` 1件は店舗情報ボタン） |
| rendered DOM | **画像26枚すべて `<a>` に包まれていない** |
| **SWELL がフロント描画時に付与** | **`data-luminous` を26画像すべてへ付与** → Luminous ライトボックスが動作 |

**正式記録：「1枚絵 upload」はアプリ側仕様、「クリック拡大」は現在の SWELL テーマ機能。
この2つを混同しない。**

### ⑯ ライトボックスの実測

対象画像すべてで **ライトボックス内画像の URL == `data-luminous`（`sameAsSrc: true`）**。
＝ **その WordPress 保存版メディア全体を直接ライトボックス表示している**。
**attachment page ではない。別画像でもない。**

### ⑰ 2560px 縮小後も「全体」表示

WordPress 保存版が長辺2560へ縮小されていても、**1枚全体としてライトボックス表示**される。

```
島図                       1361×2560
差枚数ランキング           1940×2560
その他の優秀台ピックアップ   388×2560
末尾5番台                   307×2560
東京喰種_高配分             616×2560
```

いずれも**アスペクト比維持・上端〜下端まで同一画像・途中 crop なし**。
（島図は 2F＋3F が同一画像内に、差枚数ランキングは 1位〜30位が1枚に収まることを目視確認。）

### ⑱ ★テーマ依存の注意

**クリック拡大は SWELL テーマ側の Luminous 機能である。**
将来 **テーマ変更 / SWELL 設定変更 / Luminous 無効化**が行われると、
`linkDestination:"none"` のままでは**クリック拡大が失われる可能性がある**。

**現環境ではコード修正不要。`<a href>` の追加や `linkDestination` の変更は行わない。**

### ⑲ 正式判定

| 項目 | 状態 |
|---|---|
| 投稿者選択 | **実環境確認済み** |
| category / status | **実環境確認済み** |
| X埋め込み | **実環境確認済み** |
| 本文構成 | **実環境確認済み** |
| 全画像1枚絵 upload | **実環境確認済み** |
| Python split 0 | **実環境確認済み** |
| クリック拡大 | **SWELL環境で実環境確認済み** |

**正式結論：「1枚絵＋クリック拡大：現状仕様で完了」**

### ⑳ 関連する正式commit

```
74ead1c   feat: 渋谷新館の記事用WordPress下書きに対応
34d0244   fix: 渋谷新館のX埋め込みとヒント表示を修正
2e8d661   fix: 画像再生成時の同名ファイル移動エラーを修正
b3bb277   feat: 渋谷新館の記事冒頭にギルドX投稿を追加
c31b860   feat: 渋谷新館のWordPress画像をすべて1枚絵に変更
0a02431   feat: 渋谷新館のWordPress投稿者選択を追加
62168f1   fix: 記事用の日付切替で保存値が上書きされる問題を修正
7d6cdfa   fix: 記事用の既定タイトルが自動保存される問題を修正
40d7b91   docs: 記事用の日付切替保存仕様を正式化
```

### ㉑ 今後の禁止事項

1. **渋谷新館で Python 側の画像分割を復活させない**（`_ART_WP_NOSPLIT_STORES` を外さない）
2. **差枚数ランキングを2分割へ戻さない**
3. **`WP_NOSPLIT_FILES = {"島図.jpg"}` と `_ART_WP_NOSPLIT_STORES` を統合・整理・削除しない**
4. **クリック拡大のために `<a href>` を追加したり `linkDestination` を変更したりしない**
5. **「クリック拡大はアプリ側の実装」と誤記しない**（SWELL テーマの Luminous 機能）
6. **WordPress 側の長辺2560px縮小を Python split と混同しない／サイト設定・PHP・テーマ・
   サーバー設定を変更しない**
7. **⑤オススメが未入力日に H2 ごと省略されることを不具合として扱わない**
8. **高田馬場の split 仕様・author=14・category=24・baseline `c35ac89ea13c` を変更しない**
9. **draft 62014 を公開・編集・削除しない**（検証用として残す）
10. **本節および過去節を削除・圧縮・書き換えない**（supersede は追記で記録する）
11. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用：ポスター削除UIのコンパクト化・ななこヒント10件・②タイトル（2026-09-05）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用ページのUIと、ななこヒントの枠数だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館の記事用入力を改善`・2026-09-05・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**`wp_client.py` は変更なし（git diff 0）。**
既存節は削除・圧縮・統合しない。

### ① ポスター削除ボタンは「機能維持・見た目だけコンパクト化」

**「🗑️ 削除」「すべて削除」はどちらも必要な機能なので残す。**調査で次を確認した。

| ボタン | 位置 | widget key | 処理 | 実際の削除対象 |
|---|---|---|---|---|
| 🗑️ 削除 | `show_auto_article_page` のポスターUI | `art_poster_del_{Excel名}_{file_id}` | `_art_poster_delete(store, excel, fid)` | **session_state `_art_poster_imgs_{store}_{excel}` から該当1枚を除くだけ** |
| すべて削除 | 同上 | `art_poster_clear_{Excel名}` | `_art_poster_clear(store, excel)` | **同キーを `[]` にするだけ** |

- **どちらもファイル実体・`article_page_inputs.json`・`output_dir` には触れない。**
- **`_art_poster_seen_*`（取り込み済み file_id）は意図的に残す。**外すと file_uploader に
  残っている同じ `UploadedFile` が次の rerun で再取り込みされ、削除した画像が復活する。
- キーに 店舗＋Excel名（日付）を含むため、**別日付・別店舗へ波及しない。**
- ⑧は `_art_poster_list()` を**唯一の正**として読み、0枚なら
  `_rm_stale_image(output_dir, POSTER_FN)` で前回の `_wp_poster.jpg` を消す。
  **つまり「すべて削除」は「ポスターあり → ポスターなし」へ戻す唯一の手段。**
- **削除ボタンを消してはならない。**消すと (a) 誤アップロードの取り消し不能
  （`seen` に残るので同ファイル再追加も不可）(b) ポスターなしへ戻せない
  (c) 2枚以上のときの順序修正ができない。
- **`_ART_POSTER_DEL_HIDE_STORES` のような非表示ゲートは作らない**（今回不採用）。

**変更したのは表示だけ。**

```python
_pv_cols = st.columns(4 if _art_v2 else min(4, len(_poster_saved)))
...
st.button("🗑️ 削除", ..., use_container_width=(not _art_v2))
```

- 旧実装は `st.columns(min(4, 枚数))` だったため、**ポスター1枚のとき1列＝全幅**になり、
  `use_container_width=True` の「🗑️ 削除」が画面いっぱいに伸びていた。
- **渋谷新館（`_art_v2`＝`_ART_STRUCT_V2_STORES`）だけ**列数を常に4に固定し、
  ボタンをコンテナ幅いっぱいにしない。
- **高田馬場・秋葉原は従来どおり**（`min(4, 枚数)` ＋ `use_container_width=True`）。
- 「すべて削除」は元から通常サイズなので**変更していない**。
- **`_art_poster_delete()` / `_art_poster_clear()` / `_art_poster_list()` /
  `_art_poster_key()` / `_art_poster_seen_key()` は本体バイト一致（無変更）。**
  session_state 仕様・`_art_poster_seen_*` 仕様・⑧のポスター処理・WordPress処理も無変更。

### ② ななこポストのヒントを1〜6 → 1〜10 へ

```python
_ART_NANAKO_HINTS = 10      # 旧 6
```

**変更はこの1定数だけ。** 参照3か所（UI／`_article_input_keys()`／⑧payload）が
すべて `range(_ART_NANAKO_HINTS)` なので自動的に追従する。

| 項目 | 内容 |
|---|---|
| 画面表示 | **ヒント1〜ヒント10**（2列レイアウト） |
| 内部index | **0〜9** |
| 既存 logical key | **`art_nanako_hint_0_渋谷新館` 〜 `_5_` は変更しない** |
| 追加 logical key | **`art_nanako_hint_6_渋谷新館` 〜 `_9_渋谷新館`** |
| 保存先 | 既存 `article_page_inputs.json`（Excel＝日付単位） |

- **B2（日付スコープ）を維持。**ヒント欄は共通ヘルパー `_art_txt()` 経由なので、
  表示キーは **`_artw_{excel_stem}_{logical_key}`**、保存は logical key、
  `_on_article_widget_change` の **`expected_excel` ガード**と
  `_save_article_inputs()` の **`_art_restored_excel` ガード**、**`skip_kojin=True`** が
  そのまま効く。**stable widget key を新規導入していない。**
- **過去データ互換**：保存に無い 6〜9 は `_restore_article_inputs()` が `""` を入れるので
  **空欄扱い**。既存1〜6はそのまま復元される。
  **過去JSONの一括変換・一括書き換えはしない。**
- **許容事項（承認済み）**：その日付で何か1欄でも編集して保存が走ると、
  過去日付エントリにも `art_nanako_hint_6..9 = ""` が**追記**される。
  値は空で挙動は同一、既存1〜6は不変、**閲覧だけでは保存は走らない**（on_change 未発火）。
  既存キー追加時と同じ挙動なので、**これを避けるための追加ロジックは入れない。**

### ③ WordPress本文仕様は不変（`wp_client.py` 無変更）

- **`NANAKO_HINT_COUNT = 6` は参照0件の未使用定数。理由なく変更・削除しない。**
- 実処理 `blk_para_hints()` / `plan_blocks()` は**リスト長非依存**
  （`[h for h in items if h]` で非空だけ抽出）なので10件でもそのまま動く。
- 仕様は従来どおり：**非空ヒントだけ出力／途中が空でも後ろの非空を出す／
  「■＋本文全体」を `<strong style="color:#e60012">` で包む（赤＋太字）／
  複数ヒントは1 Gutenberg paragraph 内で `<br>` 改行**。
- **X URL の有無による既存条件分岐も変更しない。**

### ④ ②セクションのタイトル（表示のみ）

```python
st.markdown(f"### {_sec_num()} {'全台系・高配分' if _art_v2 else '個別画像'}")
```

- **渋谷新館（`_art_v2`）だけ `高配分` → `全台系・高配分`。**
- **高田馬場・秋葉原の `個別画像` は変更しない。**
- この文字列は**WordPress と共有していない**（H2 は `wp_client.py` の別定数
  `H2_ZENDAI = "全台系濃厚機種が複数"` / `H2_HIGH = "1/2系以上の高配分機種が大量"`）。
- **全台系抽出／高配分抽出／画像ファイル名／保存キー／session_state key／
  `article_page_inputs.json` schema／WordPress H2／WordPress本文／⑧出力／ZIP／
  `_sec_num()` のカウンタ方式は変更していない。**

### ⑤ 変更範囲（機械確認）

- **`streamlit_app.py` のみ**（+14 / −5・3ハンク）。**新規関数0・消失関数0。**
- **本体が変わった関数は `show_auto_article_page()` の1つだけ**。
  `_art_poster_delete` / `_art_poster_clear` / `_art_poster_list` / `_art_poster_key` /
  `_art_poster_seen_key` / `_save_article_inputs` / `_restore_article_inputs` /
  `_art_widget_key` / `_art_saved_value` / `_on_article_widget_change` /
  `_art_edited_key` / `_art_kojin_default` / `_on_article_kojin_enabled` /
  `_save_article_enabled` / **`show_auto_page`（通常ページ全域）** は**すべてバイト一致**。
- **`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は無変更。**

### ⑥ 純粋テスト結果（全PASS）

ヒント10件・途中空欄（1/3/7/10のみ）→ **`■A` / `■C` / `■G` / `■J` の4行**、
**1 paragraph・`<br>`3個・`#e60012`＋`<strong>`・空の「■」0件**。
ヒント0件で `para_hints` を出さず H2 は出る／X URL なしで `embed_x` を出さずヒントは出る。
既存定数の維持も確認：`NANAKO_HINT_COUNT=6` ／ 渋谷新館 category **19** /
`espace-shibuyashin` ／ 高田馬場 **24** ／ `m.suzuki=7` ／ `WP_AUTHOR_ID=14` ／
`_ART_WP_NOSPLIT_STORES={"渋谷新館"}` ／ `WP_NOSPLIT_FILES={"島図.jpg"}` ／
`plan_split(store="渋谷新館")=={}`（Python split 0）／ `RANK_SHIMAZU_GAP_PARAS=5` ／
`X_EMPTY_PARAS=3` ／ `twitter.com` 正規化 ／ `providerNameSlug="x"` ／
`H2_ZENDAI` / `H2_HIGH` 不変。
**高田馬場の baseline `c35ac89ea13c` は、`wp_client.py` が git diff 0 であることで維持を確認した。**

### ⑦ 今後の禁止事項

1. **ポスターの「🗑️ 削除」「すべて削除」を機能ごと消さない**
2. **`_art_poster_delete()` / `_art_poster_clear()` を変更しない**
3. **`_art_poster_seen_*` を削除時に外さない**（削除した画像が復活する）
4. **⑧の `_art_poster_list()` 基準・`_rm_stale_image(output_dir, POSTER_FN)` を変えない**
5. **高田馬場・秋葉原のポスターUI（全幅ボタン）を今回の理由で変更しない**
6. **`_ART_NANAKO_HINTS` を 6 へ戻さない**
7. **`art_nanako_hint_0〜5` の logical key を変更しない**
8. **ヒント欄に stable widget key を導入しない**（B2 の日付スコープを維持）
9. **過去日付JSONを一括変換・一括書き換えしない**
10. **空キー追記を避けるための追加ロジックを入れない**（最小修正を維持）
11. **`wp_client.NANAKO_HINT_COUNT` を理由なく変更・削除しない**
12. **ヒント本文の仕様（非空のみ・1 paragraph・`<br>`・赤＋太字）を変えない**
13. **②タイトルの変更を高田馬場・秋葉原へ波及させない**
14. **②タイトルを理由に抽出ロジック・画像名・保存キー・WordPress H2 を変更しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用：列仕掛けのパネル欠落修正とジャグラー統合の最大2パネル（2026-09-05）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用ページのパネル表示だけ**。
正式コード commit は本節と**同一の commit**
（`fix: 渋谷新館の記事用パネル表示を修正`・2026-09-05・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**`wp_client.py` / `convert_narabi_pil.py` は変更なし（git diff 0）。**
既存節は削除・圧縮・統合しない。

### ① 列仕掛け画像にパネルが付かなかった直接原因

`北斗転生2(列仕掛け).jpg` の生成物は**表＋スランプは正常なのにパネルだけ無かった**。
原因は**パネル画像の欠落でも店舗ゲートでもなく、機種名の照合失敗**である。

`_apply_panel_to_table_img()` の単一機種分岐は、ファイル名から機種名を復元する際に
**`.jpg` / `_高配分` / `（優秀台）` / `・2F・3F` の4つしか除去しない**。
**`(列仕掛け)` を除去しないため** `北斗転生2(列仕掛け)` のまま
`get_machine_images()` へ渡り、`machine_image_master.xlsx` の `北斗転生2` と一致せず
`_build_panel_row()` が `None` を返して**元画像がそのまま返っていた**。

```
北斗転生2(列仕掛け).jpg  → _mn='北斗転生2(列仕掛け)'  ← ★不一致（パネルなし）
北斗転生2(3台並び).jpg   → 「台並び」判定で並び分岐へ（正常）
北斗転生2（優秀台）.jpg   → _mn='北斗転生2'（正常）
```

`北斗転生2 → hokutotensei2` はマスタに登録済み、`hokutotensei2_panel.png` も実在していた。

**列画像は「台並び」に一致しないため並び専用分岐に入らず、単一機種分岐へ落ちていた**のが構造的な原因。
2機種以上の列は `_art_is_multi_machine()` が True になり、**並びとは違う 2×2 グリッド**へ入っていた。

### ② 正式仕様：列仕掛けは記事用で「並び」と同じパネル選定ルール

**列専用のパネル処理・レイアウトは作らない。既存の並び経路へ乗せる。**

| 掲載機種数 | パネル |
|---|---|
| 1機種 | **1枚**（`_build_panel_row` で全幅） |
| 2機種 | **横並び2枚**（台番昇順） |
| 3機種以上 | **差枚最大の1機種**（既存の並び仕様どおり） |

実装は3点だけ。**`_narabi_panel_names()` / `_build_panel_row()` / `_art_is_narabi_fn()` は無変更で再利用。**

1. **`_art_is_multi_machine()`** … `"台並び" in bare_fn or _art_is_narabi_fn(bare_fn)` で False を返す
   （列を 2×2 グリッドへ誤って入れない）。この関数は**記事用3か所からのみ呼ばれる**ので他店舗へ波及しない。
2. **`_apply_panel_to_table_img()`** … 引数 **`narabi_like: bool = False`** を追加し、
   `_is_narabi = ("台並び" in bare_fn) or narabi_like` として既存の並び判定2か所を置き換える。
3. 記事用の**⑦プレビュー／🔄その他を更新／⑧本番の3呼び出しだけ**
   **`narabi_like=_art_is_narabi_fn(_bare)`** を渡す。

### ③ ★`narabi_like` の既定は必ず False（かぶぱへ波及させない）

**`_apply_panel_to_table_img()` は新宿歌舞伎町かぶぱ（通常ページ・`_PANEL_STORES`・`crop_bar=True`）
とも共用**している。**関数内で無条件に「列＝並び扱い」にしてはならない**
（かぶぱの列画像の挙動まで変わる）。
**既定 `False` のまま、記事用3呼び出しだけで明示的に有効化する。**

### ④ ⑦・🔄・⑧は必ず同じ結果

列画像の ban_map は **⑦＝`_art_col_map` ／ ⑧＝`art_preview_col_{store}`** としてスランプ合成ループへ
マージ済みで、**3経路とも同じ `_apply_panel_to_table_img()` を通る**。
そのため上記修正で **⑦・🔄・⑧が自動的に一致**する。
**「⑦だけパネルあり／⑧だけあり」を作ってはならない。**

構成は `[パネル] → [表] → [スランプ]`（記事用は `NO_BAR` で青バーが無く `crop_bar=False` なので
crop は発生しない）。

### ⑤ 正式仕様：ジャグラーシリーズ優秀台のパネルは最大2機種（渋谷新館のみ）

`ジャグラーシリーズ優秀台.jpg` は **`_ART_MULTI_PANEL_FNS` に固定登録**されているため
`_art_is_multi_machine()` が常に True → `_build_variety_panel_grid()`（最大4機種・2×2）へ入る。
3機種だと `[2枚][1枚]` になり**右下が空白**になっていた。

**渋谷新館の記事用の `ジャグラーシリーズ優秀台.jpg` だけ、パネルを最大2機種にする。**

| 掲載機種数 | パネル |
|---|---|
| 1機種 | 1枚（既存の1枚表示のまま。無理に2枚にしない） |
| 2機種 | 横並び2枚 |
| **3機種以上** | **上位2機種だけを横並び2枚**（2×2にしない） |

実装：

```python
_ART_JUG_PANEL2_STORES: "frozenset[str]" = frozenset({"渋谷新館"})

def _art_panel_max(store, bare_fn) -> int:
    if store in _ART_JUG_PANEL2_STORES and bare_fn == "ジャグラーシリーズ優秀台.jpg":
        return 2
    return 4
```

- `_build_variety_panel_grid(..., max_panels: int = 4)` を追加し、`if len(_chosen) >= 4` を
  **`>= max_panels`** にするだけ。**既定4は必ず維持。**
- `_apply_panel_to_table_img(..., max_panels: int = 4)` を追加してそのまま透過。
- 記事用3呼び出しだけ **`max_panels=_art_panel_max(store, _bare)`** を渡す。
- **2枚のとき既存の `_rows` 計算がそのまま1行2列＝横並び2枚**になる。
  **新しい描画ロジック・新レイアウトは追加しない。**

### ⑥ 選定ルール・パネル未登録・同率は既存のまま（変更禁止）

- 順位は既存正式仕様の **「機種ごとの最高差枚が大きい順」を変更しない。**
  **合計差枚／平均差枚／プラス台合計などの新しい順位ロジックを作らない。**
- **パネル未登録の機種は `continue` で飛ばして次順位を繰り上げる**（既存）。
  したがって「**パネルが存在する機種の中から既存順位で最大2機種**」となり、
  1位がパネル未登録でも1枚に減らない。
- **同率のtie-breakは追加しない**（Pythonの安定ソートのまま）。
- 表示順は記事用の既存仕様どおり **`order_by_min_ban=True`＝掲載台の最小台番昇順**。

2026/9/4 の実データ（ファンキー2 9台 / ゴージャグ3 6台 / ジャグラーガールズ 2台）では、
**合計・プラス台合計・平均・最高差枚のどの基準でも上位2機種は
「ファンキー2 / ゴージャグ3」で一致**することを確認済み。

### ⑦ 表・スランプは絶対に減らさない

**減らすのは上部のパネル枚数だけ。**
3機種以上が掲載されていても、**表・スランプ・掲載台・抽出条件は従来どおり全機種**を維持する
（ジャグラーガールズも表とスランプには残る）。
`_build_variety_panel_grid()` はパネル画像だけを返す関数で、表・スランプ・`ban_map` に触れない。

### ⑧ 対象外（波及させない）

**最大2パネルは「渋谷新館 × ジャグラーシリーズ優秀台.jpg」だけ。**

| 対象 | 挙動 |
|---|---|
| 渋谷新館 その他の優秀台／バラエティ／末尾 | **従来どおり最大4枚（2×2）** |
| **高田馬場 記事用** | **従来どおり最大4枚（2×2）** |
| **秋葉原 記事用** | 従来どおり**パネルなし**（`_ARTICLE_PANEL_STORES` に無い） |
| 新宿歌舞伎町かぶぱ・通常ページ・他店舗 | **従来どおり** |

全台系・高配分・並び・列・⑤オススメ・ランキング・島図へも波及させない。

### ⑨ 無変更（バイト一致を機械確認）

`show_auto_page` ／ `_narabi_panel_names` ／ `_build_panel_row` ／ `_art_is_narabi_fn` ／
`_composite_slump_onto_images` ／ `_art_hq_scale_for` ／ `_gap_sel_key` ／ `_gap_fillable` ／
`_gap_screen_paths_for_bans` ／ `_resolve_gap_screen` ／ `_on_gap_screen_change` ／
`_attach_slump_to_table` ／ `run_auto_pipeline` ／ `run_step2_juggler` ／ `run_step3_other` ／
`_build_machine_img` ／ `_build_sue_images` ／ `_art_ranking_image` ／ `_save_jpeg` ／
`_insert_panel_into_machine_img` ／ `_vstack_images` ／ `_pipeline_hq` ／ `_art_zh_fn_set`。

定数も不変：`_PANEL_STORES = {"新宿歌舞伎町"}` ／
`_ARTICLE_PANEL_STORES = {"高田馬場", "渋谷新館"}` ／
`_ARTICLE_GAP_FILL_STORES` ／ `_ART_HQ_STORES` ／ `_ART_ZH_HQ_STORES` ／
`_ART_NARABI_HQ_STORES` ／ `_ART_RANK_HQ_STORES` ／ `_ART_SHIMAZU_TARGET_KB` ／
`_ART_WP_NOSPLIT_STORES` ／ `WP_STORE_CATEGORY`。

**液晶はめ込み・HQ・解像度・JPEG品質・WordPress（本文構成／category 19／author／X／ななこ／
ランキング&島図／nosplit）・JSON schema・`article_page_inputs.json` は変更していない。**

**新規関数は `_art_panel_max()` の1つだけ**、消失関数0。
本体が変わったのは `_art_is_multi_machine` / `_apply_panel_to_table_img` /
`_build_variety_panel_grid` / `show_auto_article_page` の4つだけ。

### ⑩ 今後の禁止事項

1. **`(列仕掛け)` を並び扱いにする分岐を外さない**（パネル欠落が再発する）
2. **列専用のパネル処理・レイアウトを新設しない**（`_narabi_panel_names` を再利用する）
3. **`narabi_like` の既定を True にしない**（かぶぱの列画像が変わる）
4. **関数内で無条件に「列＝並び扱い」にしない**
5. **⑦／🔄／⑧のいずれか1つだけに引数を渡さない**（3経路で必ず一致させる）
6. **`max_panels` の既定 4 を変更しない**
7. **`_ART_JUG_PANEL2_STORES` へ高田馬場・秋葉原・かぶぱを追加しない**
8. **最大2パネルを その他の優秀台／バラエティ／末尾／全台系／高配分／並び／列／⑤オススメへ広げない**
9. **選定順位（機種ごとの最高差枚）を合計・平均・プラス台合計へ変更しない**
10. **パネル未登録機種の繰り上げ（`continue`）をやめない**
11. **新しい同率tie-breakを追加しない**
12. **パネルを減らすために表・スランプ・掲載台・抽出条件を減らさない**
13. **液晶はめ込み（`_ARTICLE_GAP_FILL_STORES` / `_gap_sel_key` / `_gap_fillable`）を変更しない**
14. **HQ 4ゲート・解像度・JPEG品質を変更しない**
15. **`wp_client.py` / `convert_narabi_pil.py` / JSON schema を変更しない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 WordPress：記事本文の画像表示幅を統一（2026-09-05・A-2a）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用WordPress本文の画像表示幅だけ**。
正式コード commit は本節と**同一の commit**
（`fix: 渋谷新館のWordPress画像表示幅を統一`・2026-09-05・
**`wp_client.py` と `CLAUDE.md` の2ファイルのみ**）。
**`streamlit_app.py` は差分0。元JPEGの生成サイズ・画質・分割仕様は一切変更していない。**
既存節は削除・圧縮・統合・並べ替えしない。

### ① 直接原因（実測で確定）

記事内で **マイジャグV_高配分 / ジャグラーシリーズ優秀台 / その他の優秀台ピックアップ /
ネオアイム_高配分 / カバネリ海門決戦_高配分** だけが左右に余白を残して小さく表示されていた。
因果は次の1本道で、**画像カテゴリではなく「縦横比」で決まる**。

```
① 渋谷新館は全画像 Python側 nosplit（_ART_WP_NOSPLIT_STORES・正式仕様）
      ↓ 縦長画像がそのまま1枚で送られる
② WordPress が長辺 2560px へ縮小して保存（-scaled ではなく本体を縮小）
      ↓ 長辺が“高さ”なので縦長なほど幅が巻き添えで縮む
      例 1985×7107 → 715×2560（幅 0.36倍）
③ blk_image() は width/height/style/srcset を出さない
      ↓ ブラウザは media の intrinsic width をそのまま採用
④ SWELL main.css は  img{border-style:none;height:auto;max-width:100%}
      ★width 指定が無い → max-width は縮めるだけで広げない
⑤ intrinsic width < 本文カラム幅 の画像だけ原寸表示 → 左右に余白
```

**元JPEGの幅はどれも 1980〜2180 でほぼ同じ**（幅の違いは元画像に由来しない）。
**幅を上げても長辺が高さである限り同じ比率で縮むため、元画像の変更は解決策にならない。**

実測（draft 62065・24ブロック）では **ブロック属性・figure class・img class が全24件で完全に同一**、
`width` / `height` / `srcset` / `sizes` / `style` は全件なし ＝ **HTML側に差は無かった**。

### ② A-1（style だけ足す案）は Gutenberg 検証に失敗 — 履歴として記録

最初に `img` へ `style="width:100%"` だけを足す最小案（A-1）を実装し、
**検証用 draft 62102** を作成した。content.raw は意図どおり出力されたが、
編集画面で画像ブロックが

> **「このブロックには、想定されていないか無効なコンテンツが含まれています。」**

となった。**A-1 は不採用。**（「復旧を試みる」は押していない。62102 は未編集・未公開のまま残置）

原因は、Gutenberg が「属性から再生成した HTML」と「保存済み HTML」を突き合わせるため、
**style だけでは不一致になる**こと。

### ③ Gutenberg が期待する保存形（同サイトの実データから確定）

**推測せず、このサイトの人手作成投稿を全走査して採取した**
（走査 399投稿／`is-resized` を含む画像ブロック **702件**、`"width"` 属性を含む **698件**。
`alignwide` / `aligncenter` / img の HTML `width=` は **0件**）。

```html
<!-- wp:image {"id":61649,"width":"605px","sizeSlug":"full","linkDestination":"none"} -->
<figure class="wp-block-image size-full is-resized"><img src="…" alt="" class="wp-image-61649" style="width:605px;height:auto"/></figure>
<!-- /wp:image -->
```

（出典 post 61647）**`605px` を `100%` に置き換えた形が A-2a。**

### ④ 正式仕様（A-2a）— 3点セットで出す

**`full_width=True` のときは、必ず次の3点を同時に出す。1つだけ足す中間形式を作らない。**

| # | 箇所 | 出力 |
|---|---|---|
| 1 | ブロック属性 | **`"width":"100%"`**（`id` の直後・`sizeSlug` の前） |
| 2 | figure class | **`wp-block-image size-full is-resized`** |
| 3 | img style | **`style="width:100%;height:auto"`** |

- **`height:auto` を省かない**（縦横比の維持と、Gutenberg の期待形との一致に必要）。
- **`alignwide` / `alignfull` / `aligncenter` / HTML の `width=` `height=` / `srcset` / `sizes`
  は追加しない。**
- `id` / `sizeSlug` / `linkDestination` / `className` / `src` / `alt` / `img class` は
  `full_width` の有無にかかわらず**変更しない**。

### ⑤ 店舗限定と実装

```python
_ART_WP_FULLWIDTH_STORES: "frozenset[str]" = frozenset({"渋谷新館"})
```

- `blk_image(media_id, src, join=False, full_width=False)`
- `build_content(..., full_width=False)` が透過
- `create_takadanobaba_draft()` が
  **`full_width=(_store in _ART_WP_FULLWIDTH_STORES)`** を渡す
- **既定は必ず `False`。** `False` のときの出力は変更前と**バイト単位で同一**。

**★`_ART_WP_NOSPLIT_STORES` と統合しない。役割が別。**

| 定数 | 役割 |
|---|---|
| `_ART_WP_NOSPLIT_STORES` | 画像を Python 側で**分割しない**店舗 |
| **`_ART_WP_FULLWIDTH_STORES`** | WordPress 本文上の**表示幅**を100%にする店舗 |

### ⑥ ファイル名・カテゴリで分岐しない

小さく見えるかどうかは **WordPress保存後の intrinsic width が本文幅を下回るか**で決まるため、
「マイジャグだけ」「その他優秀台だけ」のような**ファイル名分岐は作らない**。
**渋谷新館の記事用画像すべてへ同じ full-width 指定を適用する。**
元々カラム幅以上ある画像（島図1361 / ランキング1204 / ポスター1040 等）は
`max-width:100%` により見た目が実質変わらない。

### ⑦ 純粋テスト（50項目・全PASS）

A-2a 出力が実例（605px→100%）と**構造完全一致**／`width` は `id` の直後／
`is-resized` あり／`style="width:100%;height:auto"`／`sizeSlug:"full"`／
`linkDestination:"none"`／src・media ID 不変／余計な属性0／
**`full_width=False` は HEAD と完全一致**／**高田馬場の本文HTMLはバイト一致で
`width` / `is-resized` / `style` の混入0**／渋谷新館は全画像ブロックに3点セット／
画像ブロック数・本文順 不変／`build_content` の既定 False。

**バイト一致（無変更）**：`plan_blocks` / `collect_files` / `plan_split` / `needs_split` /
`split_count` / `split_image_for_wp` / `upload_media` / `create_draft` / `build_poster` /
`build_title` / `store_category` / `normalize_x_url` / `blk_embed_x` / `blk_para_hints` /
`h3_zendai` / `h3_narabi` / `h3_retsu` / `_resolve_high_images` / `_existing_files` / `esc` /
`narabi_file_name` / `blk_h2` / `blk_h3` / `blk_para` / `blk_button` / `blk_empty_para`。
**変更関数は `blk_image` / `build_content` / `create_takadanobaba_draft` の3つだけ・新規/消失関数0。**

定数も不変：`WP_NOSPLIT_FILES` / `_ART_WP_NOSPLIT_STORES` / `WP_MAX_SIDE=2560` /
`WP_STATUS="draft"` / `WP_STORE_CATEGORY` / `WP_AUTHOR_MAP` / `WP_AUTHOR_ID=14` /
`_X_EMBED_HOST` / `NANAKO_*` / `H2_RANK_SHIMAZU` / `RANK_SHIMAZU_GAP_PARAS=5` / `H2_SHIMAZU`。

### ⑧ 実機確認（検証用 draft **62118**・全PASS）

| 項目 | 実測 |
|---|---|
| post ID / status / category / author | **62118 / `draft` / `[19]` / `2`（m.takahashi）** |
| media | **15件**（新規アップロードのみ） |
| **Gutenberg validation error** | **0件**。リストビューで15画像ブロックすべてが「画像」として正常認識（サムネイル表示あり）。段落・H2・H3・SWELLボタンも正常 |
| 本文カラム幅 | **784px**（内幅 **752px**） |
| **全15画像の表示幅** | **すべて 752px（＝本文幅いっぱい）で統一・NG 0** |
| 縦横比 | **15枚すべて intrinsic ratio と表示 ratio が完全一致** |

**対象画像（拡大されたもの）**

| 画像 | intrinsic W | 表示W |
|---|---|---|
| マイジャグV_高配分 | 715 | **752** |
| ジャグラーシリーズ優秀台 | 715 | **752** |
| その他の優秀台ピックアップ | 719 | **752** |
| ネオアイム_高配分 | 839 | **752** |
| カバネリ海門決戦_高配分 | 840 | **752** |

**正常画像の非回帰**：東京喰種_高配分(998) / ワールドダイスター(1984) / ハピジャグV(1534) /
スマスロ北斗の拳4台並び(1760) / 北斗転生2 3台並び(2062) / 北斗転生2 列仕掛け(1559) /
ミスジャグ_高配分(1979) / 差枚数ランキング(1204) / 島図(1361) / ポスター(1040)
— いずれも **752px** のままで見た目に変化なし。

**SWELL Luminous**：15画像すべてに `data-luminous` が付与され、`<a>` ラップは0件
（`linkDestination:"none"` を維持）。マイジャグV_高配分をクリックすると
**Luminous ライトボックスが開き、同じメディア（715×2560）の画像全体を表示**。
クリック拡大先は変わっていない。

**レスポンシブ**：本文カラムを 360px に狭めた状態で全15枚が **328px** へ追従し、
**カラムはみ出し0・横スクロール0・縦横比NG 0**。

### ⑨ 画質についての注記（了承済み）

715px の画像は本文幅 752px へ **約1.05倍**拡大表示される（本文カラム784pxの環境）。
**画像の再エンコード・アップスケール・リサイズは行っていない。CSS の表示幅だけ。**
画質を落とさず幅を確保する方法は分割しかないが、**渋谷新館の全画像nosplitは正式仕様**のため
今回は対象外とする。

### ⑩ 確認状況の正確な記録（誤記しないこと）

- **レスポンシブは「本文カラム幅をローカルDOM上で360pxに狭めた測定」である。**
  ブラウザウィンドウのリサイズが当該タブのビューポートへ反映されなかったため、
  **実スマホ幅での確認ではない。**「スマホ実機確認済み」と書かない。
- **検証用 draft 62102（A-1・validation error あり）と 62118（A-2a・error なし）は
  どちらも公開・編集・削除していない。**そのまま残置する。

### ⑪ 今後の禁止事項

1. **3点セットのうち1つでも欠いた形へ戻さない**（style だけ＝A-1 は検証エラー）
2. **`height:auto` を省かない**
3. **`"width"` を `id` の直後以外へ移さない／`is-resized` を外さない**
4. **`full_width` の既定 `False` を変更しない**（高田馬場の本文HTMLが壊れる）
5. **高田馬場・秋葉原へ `width` / `is-resized` / `style` を混入させない**
6. **`_ART_WP_FULLWIDTH_STORES` と `_ART_WP_NOSPLIT_STORES` を統合しない**
7. **ファイル名・画像カテゴリで分岐しない**
8. **`alignwide` / `alignfull` / `aligncenter` / HTML `width=` `height=` / `srcset` / `sizes` を足さない**
9. **`linkDestination:"none"` を変えない**（SWELL Luminous を壊す）
10. **元JPEGの生成サイズ・画質・パネル・液晶・HQ・`streamlit_app.py` を変更しない**
11. **`plan_split` / `needs_split` / `split_count` / `split_image_for_wp` / `WP_MAX_SIDE` を変更しない**
12. **本文構成（category 19 / author / X / ななこ / ジャグラーH2H3 / ランキング&島図 /
    空段落×5 / 店舗情報ボタン / 本文順）を変更しない**
13. **サイト設定・PHP・テーマ・SWELL の CSS を変更しない**
14. **draft 62102 / 62118 を公開・編集・削除しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用⑤：ブロック5・6だけ機種名枠を9個へ拡張（2026-09-07）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用⑤「オススメ機種の優秀台」の
ブロック5・6の機種名入力枠数だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館のオススメ機種入力枠を拡張`・2026-09-07・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**・`streamlit_app.py` は **+33 / −7**・4ハンク）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**
既存節は削除・圧縮・統合・並べ替えしない。

### ① 正式な枠数

| ブロック | 0-based index | 機種名枠 | UIレイアウト |
|---|---|---|---|
| ブロック1〜4 | 0〜3 | **6枠（変更なし）** | 3列×2段 |
| **ブロック5** | **4** | **9枠** | **3列×3段** |
| **ブロック6** | **5** | **9枠** | **3列×3段** |

**他店舗（高田馬場・秋葉原ほか）は全ブロック6枠のまま。**
タイトル欄は従来どおり各ブロック1欄（計6欄）。

### ② 定数とヘルパー（店舗・ブロック条件を3か所へ個別ハードコードしない）

```python
_ART_OSUSUME_BLOCKS          = 6                     # 既存・不変
_ART_OSUSUME_PER_BLOCK       = 6                     # 既存・既定値として残す
_ART_OSUSUME_PER_BLOCK_EXTRA = 9
_ART_OSUSUME_EXTRA_BLOCKS    = frozenset({4, 5})     # 0-based＝ブロック5・6
_ART_OSUSUME_EXTRA_STORES    = frozenset({"渋谷新館"})

def _art_osusume_per_block(store: str, n: int) -> int:
    if store in _ART_OSUSUME_EXTRA_STORES and n in _ART_OSUSUME_EXTRA_BLOCKS:
        return _ART_OSUSUME_PER_BLOCK_EXTRA
    return _ART_OSUSUME_PER_BLOCK
```

**★店舗ゲート `_ART_OSUSUME_EXTRA_STORES` を必ず維持する。**
`_article_input_keys()` は店舗非依存に⑤キーを組み立てるため、ゲートを外すと
**高田馬場・秋葉原の `article_page_inputs.json` エントリへ空キー6件が増える。**

### ③ 変更した3か所（すべて同じヘルパーを使う）

| # | 箇所 | 変更 |
|---|---|---|
| 1 | `_article_input_keys()` | `range(_ART_OSUSUME_PER_BLOCK)` → **`range(_art_osusume_per_block(store, _n))`** |
| 2 | `_art_osusume_collect()` | 同上 |
| 3 | ⑤UI（`show_auto_article_page`） | `_mrows = [st.columns(3) for _ in range(2)]` の**固定2段を廃止** → `_cnt = _art_osusume_per_block(store, _n)` / `_mrows = [st.columns(3) for _ in range(math.ceil(_cnt / 3))]` / flatten を **`[:_cnt]`** で切る |

**★UI だけ・collect だけを直してはならない。**
旧実装は UI が 3列×2段の直書き、`_article_input_keys()` と `_art_osusume_collect()` が
定数参照という**2系統**だったため、片方だけ直すと
「UIは9枠なのに収集は6件まで」＝**7〜9欄目が黙って無視される**状態になる。
**`range(_ART_OSUSUME_PER_BLOCK)` の直接参照は残さない**（現在0件）。

### ④ 保存キー（既存命名規則をそのまま延長・別形式を作らない）

```
logical  : art_osusume_m_{_n}_{_i}_{store}
追加分   : art_osusume_m_4_6/_7/_8_渋谷新館 ／ art_osusume_m_5_6/_7/_8_渋谷新館
display  : _artw_{excel_stem}_{logical_key}
編集記録 : _artw_edited_{widget_key}（session_state 専用・JSON へ保存しない）
```

`_article_input_keys("渋谷新館")` の⑤部分は **タイトル6 ＋ 機種42 ＝ 48キー**
（旧42キー）。`_article_input_keys("高田馬場")` / `("秋葉原")` は **42キーで順序まで従来と一致**。

旧廃止キー `art_osusume_m_{i}_{store}`（index 1個の9枠形式・8/27 エントリに9件残置）とは
**形が違うので衝突しない**。現行コードは読まない。**削除もしない。**

### ⑤ 保存・復元は既存正式仕様をそのまま踏襲（新関数・新JSONを作らない）

追加欄も既存 **`_art_mac()`** で描くため、次がすべて自動的に効く：

`_art_widget_key()` の日付スコープ display key ／ `_on_article_widget_change` ／
**`expected_excel` ガード** ／ **`_art_restored_excel` ガード** ／ `_art_prev_store` 店舗ガード ／
display→logical bridge ／ `_artw_edited_*` ／ `_restore_article_inputs()` ／
`_save_article_inputs()`（マージ方式）／ 初期値は `_art_kojin_default()` → `value=`。

**stable widget key へ戻さない。保存用の新関数・新JSONを作らない。**
追加欄は `empty_default` を持たないので、`7d6cdfa` の「表示 default が raw へ焼き付く」
副作用には該当しない。

### ⑥ 過去データ

**`article_page_inputs.json` の一括 migration は不要・実施しない。**
保存に無いキーは `_restore_article_inputs()` が `""` を入れ、`_art_kojin_default()` も `""`
を返すので**過去日付では空欄表示**。
実データ確認時点で**ブロック5・6の機種名に値のあるエントリは0件**（⑤に値があるのは
8/27 渋谷新館＝ブロック1・2、9/5 渋谷新館＝ブロック1・2＋タイトル1〜3のみ）。

**既知の許容事項**：対象日付で何か1欄でも編集して保存が走ると、そのエントリへ
`art_osusume_m_4_6..8 / m_5_6..8 = ""` が**空値で追記**される（`_ART_NANAKO_HINTS` を
6→10 にしたときと同種）。**ページ表示・日付切替だけでは保存は走らない**
（保存は `on_change` 発火時のみ）。**これを避けるための追加ロジックは入れない。**

### ⑦ 画像生成・⑦・⑧・ZIP・WordPress は件数非依存（無変更）

**⑤は「1機種＝1画像」の既存仕様を維持する。9機種を1枚に統合しない。**
ブロック5に9機種入れれば最大9枚、ブロック6も最大9枚。

本体を**変更していない**関数：
`_art_osusume_images()` ／ `_art_osusume_flat()` ／ `_art_osusume_plan()` ／
`filter_recommended_machines()` ／ `_kojin_yushu_filter()` ／ `_pipeline_hq()` ／
`_make_safe_fn()` ／ `_build_machine_img_no_bar()` ／ `_art_high_title_bar()` ／
`show_auto_page()`（通常ページ全域）。

- ⑦プレビューと⑧本番は**同じ `art_osusume_machines`・同じ `_art_osusume_images()`** を使う
- ZIP は `output_dir` を丸ごと固めるので `{機種名}_オススメ優秀台.jpg` が増えれば自動で入る
- WordPress は `payload["osusume"]`（`_art_osu_plan_{store}`）→ `plan_blocks()` が
  ブロック単位ループ＋`_existing_files()` 実在判定で**件数非依存**
- パネル・スランプ・液晶・HQ は1画像単位処理のため**枠数増で影響なし**

**`wp_client.py` は変更禁止（diff 0 を維持）。**
`_ART_WP_FULLWIDTH_STORES` ／ Gutenberg `width:"100%"` ／ `is-resized` ／
`style="width:100%;height:auto"` ／ `_ART_WP_NOSPLIT_STORES`（全画像nosplit）／
category 19 ／ author ／ Guild X ／ ななこ ／ ランキング&島図 ／ Luminous は**完全非対象**。

### ⑧ 純粋テスト結果（45 PASS / 0 FAIL）

`_art_osusume_per_block` が渋谷新館 `[6,6,6,6,9,9]`・他店舗（高田馬場/秋葉原/新小岩/西武新宿/稲毛）
`[6]*6` ／ `_article_input_keys("渋谷新館")` の⑤が title6＋機種42＝48キー・ブロック別
`{0..3}=6 {4,5}=9`・追加6キー存在・重複なし ／ **他店舗の⑤キーは42キーで順序まで完全一致・
`art_osusume_m_[45]_[678]_` の混入0** ／ `_art_osusume_collect()` が `[6,6,6,6,9,9]`
（高田馬場は `[6]*6`）／ `_art_osusume_flat()` の順序（ブロック1→6・枠1→n）と
7〜9欄目の取り込み・件数24 ／ `_art_osusume_plan()` がブロック5の9枚を引き当て・
7〜9欄目の画像を含む・全18枚 ／ `_artw_*` の保存キー混入0 ／
display key が `_artw_20260905_渋谷新館_20S_art_osusume_m_4_6_渋谷新館` 形式・日付違いで別キー ／
6枠→2段・9枠→3段 ／ 3か所すべてヘルパー使用・`range(_ART_OSUSUME_PER_BLOCK)` 直参照0 ／
`_art_osusume_images()` に件数スライス・上限なし・1機種1画像維持。

### ⑨ 今後の禁止事項

1. **ブロック1〜4を9枠にしない**（6枠のまま）
2. **`_ART_OSUSUME_EXTRA_STORES` の店舗ゲートを外さない**（他店舗JSONへ空キーが増える）
3. **他店舗を `_ART_OSUSUME_EXTRA_STORES` へ追加しない**
4. **`_ART_OSUSUME_PER_BLOCK = 6` の既定値を9へ変えない**
5. **UI・保存キー生成・collect のどれか1か所だけ直さない**（3か所で同じヘルパーを使う）
6. **UIの段数を再び固定 `range(2)` へ戻さない**
7. **`range(_ART_OSUSUME_PER_BLOCK)` の直接参照を復活させない**
8. **`_art_mac()` 以外の入力widget関数を新設しない／stable widget key へ戻さない**
9. **保存用の新関数・新JSONを作らない**
10. **logical key の命名規則を変えない**（`art_osusume_m_{n}_{i}_{store}` の延長のみ）
11. **旧廃止キー `art_osusume_m_{i}_{store}` を読み込まない／削除しない**
12. **過去JSONへ空キーを事前追加しない／一括 migration しない**
13. **⑤の「1機種＝1画像」をブロック単位1枚統合へ変えない**
14. **`_art_osusume_images()` / `_art_osusume_plan()` / `_art_osusume_flat()` /
    `filter_recommended_machines()` / `_kojin_yushu_filter()` に件数上限を入れない**
15. **`wp_client.py` を変更しない（diff 0）／WordPress本文仕様を変更しない**
16. **通常ページ（`show_auto_page`）を変更しない**
17. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用⑤：オススメ優秀台を1ブロック＝1画像へ（2026-09-07）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用⑤「オススメ機種の優秀台」の
画像化方法だけ**。正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館のオススメ優秀台をブロック画像化`・2026-09-07・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**
既存節は削除・圧縮・統合・並べ替えしない。

### ⓪ 何を変えたか（変えていないもの）

| | 旧 | **新（正式）** |
|---|---|---|
| 画像の粒度 | **1機種＝1画像**（`{機種名}_オススメ優秀台.jpg`） | **1ブロック＝1画像**（`オススメ優秀台_ブロックN.jpg`） |
| 水色タイトルバー | `_art_high_title_bar(text=_ART_OSUSUME_BAR_TEXT)` を付ける | **付けない** |
| ⑦プレビュー | ban_map 未登録＝**表だけ**（パネル・スランプなし） | **ban_map 登録＝パネル＋表＋スランプの完成形** |
| 液晶はめ込み | ⑧では入り得た | **⑤だけ付けない**（専用例外） |
| スランプ内機種名 | なし | **複数機種のブロックだけ表示** |

**変えていないもの（絶対に変更しない）**：
`filter_recommended_machines()`（空白除去・重複除去・②全台系除外・②高配分除外・
②手入力機種の除外・自動生成機種の除外・Excel未存在の除外）／
`_kojin_yushu_filter()` の優秀台抽出条件／⑤の9枠仕様／入力保存・日付スコープ。
**今回変えたのは「抽出後の DataFrame をどう画像化するか」だけ。**

### ① 新関数（⑦⑧共用・1本だけ）

```python
_ART_OSUSUME_FN_FMT = "オススメ優秀台_ブロック{n}.jpg"

def _art_osusume_fn(n: int) -> str              # n は0-based → 表示は1-based
def _art_is_osusume_fn(bare_fn: str) -> bool    # ⑦⑧で同じ判定を使う
def _art_osusume_block_images(blocks, df, diff_raw, store,
                              zen_names, high_names, hq_scale=1.0)
    # 戻り値: ([(ファイル名, PIL画像, ブロックindex)], {ファイル名: 掲載台番}, 除外ログ)
```

**⑦と⑧で別々のブロック生成ロジックを作らない**（`_art_osusume_images()` は廃止・削除済み）。
判定は **`_art_is_osusume_fn()` の1本に集約**し、⑦・⑧で条件をズラさない。

### ② 除外＝フラット1回（重複機種は最初のブロックだけ）

**`filter_recommended_machines()` はブロックごとに呼んではならない。**
ブロックごとに呼ぶと `seen` による**全体重複除去が効かず**、同一機種を複数ブロックへ
入力したときに重複掲載される（現行仕様の破壊）。

正式手順：
1. `_art_osusume_flat(blocks)` で全ブロックをフラット化
2. **`filter_recommended_machines(..., ban_level=False)` を1回だけ**呼ぶ
3. `_valid` を集合化し、ブロックを回して所属へ戻す
4. 関数内ローカル `_used` で **同一機種は最初のブロックだけ採用**

### ③ ブロック単位の表

各ブロックで、`_valid` に残った機種だけを既存 **`_kojin_yushu_filter(_m, _grp, _dr, _cfg)`**
（引数は従来と同一）へ通し、空 DataFrame を除いて `pd.concat` する。

並び順は**新小岩⑤（`generate_recommended_block_image`）と同じ考え方**を流用：

```python
_sel["_grp_order"] = _sel.groupby("機種名")["台番"].transform("min")
_sel = _sel.sort_values(["_grp_order", "台番"]).drop(columns=["_grp_order"]).reset_index(drop=True)
```

＝**機種グループ＝その機種の最小台番昇順／グループ内＝台番昇順**。
**`generate_recommended_block_image()` 本体は呼ばない・変更しない**（抽出が
`差枚 >= min_diff` の一本道で、記事用⑤の `_kojin_yushu_filter` と条件が違う）。

### ④ 水色タイトルバーなし

⑤は **`_build_machine_img_no_bar(_sel, hq_scale=_hq)`** の表本体だけを使う。
**`_art_high_title_bar()` は呼ばない。**
ただし **`_art_high_title_bar()` と `_ART_OSUSUME_BAR_TEXT` の定義は削除しない**
（前者は記事用高配分の4か所が使用中。後者は参照0になるが履歴として残置）。

### ⑤ 完成画像は「パネル → 表 → スランプ」

合成は既存の記事用共通処理（`_apply_panel_to_table_img` → `draw_slump_graph` →
`_attach_slump_to_table`）で行う。**新しい画像合成システムを作らない。**

### ⑥ パネル（既存関数のみ・最大4）

- `_apply_panel_to_table_img(..., show_mn=True相当, is_multi=True相当, max_panels=_art_panel_max(store, bare))`
- **⑤は 1機種でも `_build_variety_panel_grid()` のグリッド経路へ入れる。**
  理由：`_apply_panel_to_table_img` の先頭 `if not show_mn and not _is_narabi:` は
  **ファイル名から機種名を復元する単一機種経路**で、ブロック単位ファイル名では
  機種名が復元できず**1機種ブロックのパネルが消える**。
  そのため ⑤ は `_show_mn or _is_sue or _is_multi or _is_osu` / `is_multi=_is_multi or _is_osu`
  を渡してグリッド経路へ固定する。**関数本体は変更しない。**
- 枚数は既存 **`_art_panel_max()`（⑤は4）**。**⑤専用の最大値を作らない。**

| 残機種数 | 1 | 2 | 3 | 4 | 5〜9 |
|---|---|---|---|---|---|
| パネル | 1 | 2 | 3 | 4 | **上位4機種** |

選定順位（機種ごとの最高差枚降順）・パネル未登録機種の繰り上げ・表示は台番昇順
（`order_by_min_ban=True`）は**すべて既存のまま**。
**ジャグラー統合だけ最大2（`_ART_JUG_PANEL2_STORES`）という既存別仕様にも触らない。**

### ⑦ ★パネル判定と機種名判定は別物（同じ boolean で雑に処理しない）

| | 条件 |
|---|---|
| **パネル** | ⑤なら**常に**グリッド経路（1機種でも1枚） |
| **スランプ内機種名** | **実際に2機種以上のときだけ**表示 |

```python
_is_osu    = _art_is_osusume_fn(bare)
_osu_multi = _is_osu and _art_is_multi_machine(bare, bans, ban2mac)   # ＝2機種以上
...
machine_name = _dn if (_show_mn or _osu_multi) else None
```

`_art_is_multi_machine()` は非既知ファイル名なら「掲載台の機種が2種類以上」を返すので、
**1機種ブロック → `machine_name=None` ／ 複数機種ブロック → 機種名あり**になる。
**「⑤だから常に machine_name を表示」する実装は禁止。**
**⑤ファイル名を `_ART_MULTI_PANEL_FNS` へ追加してはならない**（常に True になる）。
描画は既存 `draw_slump_graph()` の**黄色文字＋黒縁取り**。**新しい文字描画処理を作らない。**

### ⑧ 液晶は⑤だけ付けない

⑦・⑧のスランプ合成ループで、**⑤ブロック画像のときだけ**

```python
if _is_osu_XX:
    _gap_img_XX = None      # 液晶なし・メタも登録しない（⑦のセレクタも出ない）
elif <既存の液晶分岐>:
    ...
```

**`_ARTICLE_GAP_FILL_STORES` / `_gap_screen_paths_for_bans()` / `_gap_fillable()` /
`_gap_sel_key()` / `_resolve_gap_screen()` そのものは変更しない。**⑤を対象外にする最小分岐だけ。

### ⑨ 表掲載台＝bans＝スランプ対象台

`_bans[fn]` には **`_sel["台番"]`（＝表の行）だけ**を入れる。
入力しただけで `_kojin_yushu_filter` を通らなかった台はスランプに入らない。
②全台系・②高配分で除外された機種は**表・パネル・スランプすべてに出ない**。

### ⑩ ファイル名（固定・タイトル非依存）

```
オススメ優秀台_ブロック1.jpg 〜 オススメ優秀台_ブロック6.jpg
```

**ブロックタイトルも機種名もファイル名へ入れない**（タイトルを変えても過去参照が壊れない）。
命名元は **`_ART_OSUSUME_FN_FMT` / `_art_osusume_fn()` の1か所**で、
生成・⑦・⑧・plan・stale削除がすべてこれを使う。

### ⑪ 空ブロック

掲載0のブロックは **画像を作らない**（⑦表示なし・⑧保存なし・ZIP対象外・plan なし・H3 なし）。
⑧では**固定6ファイル名のうち生成しなかったものだけ** `_rm_stale_image()` で削除する。

**★旧仕様 `{機種名}_オススメ優秀台.jpg` は自動削除しない。**
`glob("*_オススメ優秀台.jpg")` 等の**無差別削除は禁止**（他日付・他処理への影響を避ける）。
旧ファイルが `output_dir` に残った場合は **ZIP に混入し得る**が、WordPress 本文へは
payload 経由でしか載らないので出ない。

### ⑫ `_art_osusume_plan()`

機種名からファイル名を再構成する方式を**廃止**し、**ブロックindex → 画像1枚**にした。

```python
_art_osusume_plan(blocks, {ブロックindex: ファイル名})
  → [{"title": ブロックタイトル, "images": [1枚]}, …]
```

**payload 構造 `[{"title","images"}]` は不変。**画像が無いブロックは含めない。
ブロックタイトルの **UI・保存・復元・WordPress H3 は従来どおり維持**
（画像には描かれない＝`d121e54` の正式仕様のまま）。

### ⑬ WordPress（`wp_client.py` は変更禁止・diff 0）

`plan_blocks()` / `collect_files()` / `_existing_files()` / `build_content()` は
**1機種1画像を前提としていない**ので、そのまま動く。最終構造：

```
H2 オススメ機種の優秀台
H3 ブロック1タイトル      （空タイトルならH3なし）
   オススメ優秀台_ブロック1.jpg
H3 ブロック2タイトル
   オススメ優秀台_ブロック2.jpg
…
```

空ブロックは画像もH3も出ない（`_art_osusume_plan` と `_existing_files` の二重防御）。
**full-width（`_ART_WP_FULLWIDTH_STORES` / `"width":"100%"` /
`wp-block-image size-full is-resized` / `style="width:100%;height:auto"`）と
nosplit（`_ART_WP_NOSPLIT_STORES`）は完全非対象**で、⑤ブロック画像も自動的に乗る。

### ⑭ ⑦・🔄・⑧

- **⑦**：`_art_osusume_block_images()` の bans を **`_pv_bm_sl` へ登録**する。
  これにより⑦時点で「パネル＋表＋スランプ」の完成形が表示される。
  **⑦だけ表のみ、という不一致を作らない。**
- **⑧**：同じ関数・同じ ban_map（`_art_bm_sl`）。⑦と
  対象機種・対象台番・機種順・台順・表・パネル・スランプ・機種名条件・ファイル名が一致する。
- **🔄「その他を更新」**：`_upd_bm` は 🔄 が作り直す
  「その他の優秀台ピックアップ.jpg」「ジャグラーシリーズ優秀台.jpg」の**2つだけ**を持つ。
  ⑤ブロック画像は入らないため**合成済みのまま素通し**になる（二重合成しない）。
  **⑤を `_upd_bm` へ追加してはならない。**

### ⑮ HQ・保存target

**新しいHQゲートは作らない。**
`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` / `_ART_RANK_HQ_STORES`
は**役割が別なので統合禁止**・値も不変。

⑤は従来どおり `_pipeline_hq(hq_scale, len(_sel))`（渋谷新館は**掲載台10台以上で2倍**）。
⑧の保存だけ、**2倍描画のときに250KBへ潰さない**よう次を適用する：

```python
target_kb=(_ART_HQ_TARGET_KB if _pipeline_hq(...) > 1.0 else 250)
```

**新しいHQ定数は作らず `_ART_HQ_TARGET_KB` を再利用する。他画像の保存targetは変更しない。**

### ⑯ 純粋テスト結果（83 PASS / 0 FAIL）

1ブロック2機種→1画像 ／ 2ブロック→2画像 ／ 空ブロック→画像なし ／ 全空→0画像 ／
②全台系・②高配分の台が bans に無い・除外ログ ／ **新旧で掲載台集合が完全一致**
（旧3画像→新2画像で台番集合は同じ＝抽出条件不変の証明）／ 表掲載台番==bans ／
機種最小台番昇順＋台番昇順 ／ `_art_high_title_bar(` 呼び出し0・定義は残存・
`_ART_OSUSUME_BAR_TEXT` 参照は定義1のみ ／ 1機種 multi False・2機種 multi True・
⑤名は `_ART_MULTI_PANEL_FNS` 外 ／ **23関数の本体バイト一致**
（`draw_slump_graph` / `_apply_panel_to_table_img` / `_build_variety_panel_grid` /
`_build_panel_row` / `_art_panel_max` / `_art_is_multi_machine` / `_attach_slump_to_table` /
`filter_recommended_machines` / `_kojin_yushu_filter` / `generate_recommended_block_image` /
`_art_osusume_collect` / `_art_osusume_flat` / `_art_hq_scale_for` / `_pipeline_hq` /
`_art_high_title_bar` / `_build_machine_img_no_bar` / `_gap_fillable` / `_gap_sel_key` /
`_article_input_keys` / `_art_osusume_per_block` / `_rm_stale_image` / `_save_jpeg` /
**`show_auto_page`**）／ パネル 1→1・2→2・3→3・4→4・5→4・9→4 ／
`_art_panel_max` は⑤=4・ジャグラー統合=2 ／ ファイル名固定・タイトル変更で不変 ／
plan 1ブロック1画像・空ブロック非掲載・タイトル空は `title=""` ／
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は git 基準で diff 0** ／
⑤入力キー48維持 ／ `per_block [6,6,6,6,9,9]` 維持・他店舗全6 ／
高田馬場・秋葉原の⑤キーは42のまま ／ HQ4ゲート不変。

### ⑰ 今後の禁止事項

1. **1機種＝1画像へ戻さない**
2. **`filter_recommended_machines()` をブロックごとに呼ばない**（全体重複除去が壊れる）
3. **同一機種が複数ブロックへ重複掲載される実装にしない**
4. **`_kojin_yushu_filter()` の抽出条件を変えない／⑤専用条件を作らない**
5. **`generate_recommended_block_image()` を呼ばない・変更しない**（新小岩の⑤仕様）
6. **⑤へ水色タイトルバーを戻さない**／`_art_high_title_bar()`・`_ART_OSUSUME_BAR_TEXT` の**定義を削除しない**
7. **⑤専用のパネル生成処理・最大パネル数を新設しない**（`_art_panel_max` の4を使う）
8. **⑤ファイル名を `_ART_MULTI_PANEL_FNS` へ追加しない**
9. **パネル判定とスランプ機種名判定を同じ boolean にまとめない**
10. **1機種ブロックで機種名を表示しない／複数機種ブロックで表示を止めない**
11. **`draw_slump_graph()` に新しい文字描画処理を足さない**
12. **⑤へ液晶はめ込みを付けない／液晶の共通仕様（`_ARTICLE_GAP_FILL_STORES` ほか）を変更しない**
13. **表掲載台と bans・スランプ対象台をズラさない**
14. **ファイル名へブロックタイトル・機種名を入れない／命名元を増やさない**
15. **旧 `{機種名}_オススメ優秀台.jpg` を glob で無差別削除しない**
16. **空ブロックで画像・plan・H3 を出さない**
17. **⑦の ban_map 登録を外さない**（⑦だけ表のみに戻さない）
18. **⑤を 🔄 の `_upd_bm` へ追加しない**（二重合成になる）
19. **`wp_client.py` を変更しない（diff 0）／payload 構造・full-width・nosplit を変更しない**
20. **HQ4ゲートを統合・変更しない／新しいHQ定数を作らない**
21. **⑤の9枠仕様（`_ART_OSUSUME_PER_BLOCK` 6 ／ `_EXTRA` 9 ／ `_EXTRA_BLOCKS {4,5}` ／
    `_EXTRA_STORES {"渋谷新館"}` ／ `_art_osusume_per_block()`）を巻き戻さない**
22. **入力保存・復元・日付スコープ（display key / `expected_excel` / `_art_restored_excel` /
    `_artw_edited_*`）を変更しない**
23. **高田馬場・秋葉原・新小岩・通常ページへ波及させない**
    （通常ページの `_show_mn` の `startswith("オススメ")` も無変更）
24. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用⑤：最終1機種ブロックのパネルを全幅にする（2026-09-07）

**正式仕様。巻き戻し禁止。**直前の
「## 渋谷新館 記事用⑤：オススメ優秀台を1ブロック＝1画像へ（2026-09-07）」の**追加修正**であり、
同節は削除・書き換えしない（同節⑥の「⑤は1機種でもグリッド経路へ固定する」だけを本節が上書きする）。
正式コード commit は本節と**同一の commit**
（`fix: オススメ優秀台の単一機種パネル表示を修正`・2026-09-07・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**

### ⓪ 症状と原因

9/5 の⑦プレビューで、⑤ブロック画像が最終的に「北斗転生2」1機種だけになったとき、
**パネルが画像上部の左半分だけに表示され、右半分が大きく白く空いていた。**

原因は、直前実装が **⑤なら1機種でも `is_multi=True` を渡してグリッド経路へ固定**していたこと。
`_build_variety_panel_grid()` は **2列固定（`_cell_w = max(1, width // 2)`）** なので、
パネル1枚だと**左半分だけ埋まり右半分が白**になる。
（`_apply_panel_to_table_img` の単一機種経路は `_build_panel_row([機種名], img.width)` を使い、
`_cell_w = width // len(panels)` ＝ **全幅**になる。）

### ① 正式仕様

| ⑤ブロックの**最終掲載機種数** | パネル |
|---|---|
| **1機種** | **高配分などの単一機種画像と同じ経路**。パネルを**表と同じ横幅いっぱい**に表示 |
| **2機種以上** | 従来どおり `_build_variety_panel_grid()`（2列グリッド・`_art_panel_max()`＝⑤は4） |

**判定は「⑤に入力された機種数」ではなく、**
**②全台系・②高配分などの既存除外 ＋ `_kojin_yushu_filter()` を通過して
その画像の表へ実際に掲載された機種数**（＝`bans` → `ban2mac` の一意機種数）で行う。
入力3機種でも除外後に1機種だけ残れば**1機種ブロック**として全幅パネルにする。

### ② 実装（呼び出し側だけ・共通関数は本体無変更）

新設ヘルパー1本のみ：

```python
def _art_osusume_panel_fn(bare_fn: str, bans: list, ban2mac: dict) -> str:
    """⑤ブロック画像のパネル合成へ渡すファイル名を返す。
    最終掲載が1機種だけなら「{機種名}.jpg」を返し、単一機種パネル（全幅）経路へ入れる。
    2機種以上・⑤以外は bare_fn をそのまま返す（従来の分岐を一切変えない）。"""
    if not _art_is_osusume_fn(bare_fn):
        return bare_fn
    _macs = {ban2mac.get(str(_b)) for _b in (bans or [])}
    _macs = {str(_m).strip() for _m in _macs if _m and str(_m).strip()}
    if len(_macs) != 1:
        return bare_fn
    return f"{_make_safe_fn(next(iter(_macs)))}.jpg"
```

⑦プレビュー・⑧本番の**2か所**で、パネル呼び出しを次のように変える（それ以外は不変）：

```python
_pfn = _art_osusume_panel_fn(_bare, _bans, ban2mac)      # ⑤1機種なら「{機種名}.jpg」
_apply_panel_to_table_img(
    img, _pfn, _bans, ban2mac, ban2diff,
    _show_mn or _is_sue or _is_multi or _osu_multi,       # ← _is_osu ではなく _osu_multi
    _is_sue, crop_bar=False,
    is_multi=_is_multi or _osu_multi,                    # ← 同上
    narabi_like=_art_is_narabi_fn(_bare),                # 判定は**実ファイル名**で行う
    max_panels=_art_panel_max(store, _bare))             # 同上
```

- **`_apply_panel_to_table_img()` / `_build_variety_panel_grid()` / `_build_panel_row()` /
  `_insert_panel_into_machine_img()` / `_narabi_panel_names()` は本体バイト無変更**
  （かぶぱ・他記事用画像へ影響を出さないため）。
- **`narabi_like` と `max_panels` は必ず実ファイル名 `_bare` で判定する。**
  `_pfn`（合成用の擬似名）で判定しないこと。
- **`_is_osu_*` をパネル引数へ渡さない**（1機種でグリッドへ入ってしまう）。
  使うのは **`_osu_multi_*`＝`_is_osu and _art_is_multi_machine(...)`（＝2機種以上）**。

### ③ ★ファイル名から機種名を復元しない

⑤のファイル名は `オススメ優秀台_ブロックN.jpg` で**機種名を含まない**ため、
通常の単一機種画像のような**ファイル名からの機種名復元はできない**。
機種名は必ず **`bans` → `ban2mac`** から取る。
**出力ファイル名 `オススメ優秀台_ブロックN.jpg` は変更しない**
（`_pfn` は `_apply_panel_to_table_img()` へ渡すだけの合成用で、保存名・plan・ban_map には使わない）。

### ④ スランプ内機種名は別判定（変更なし）

| 最終掲載機種数 | スランプ内 `machine_name` |
|---|---|
| 1機種 | **なし（None）** |
| 2機種以上 | **あり** |

**単一機種パネル対応のために `machine_name` を出す変更は禁止。**
`draw_slump_graph()` 本体・`machine_name` 条件式は今回変更していない。

### ⑤ 画像全体仕様は維持

`パネル → 表 → スランプ` の構成 ／ **水色タイトルバーなし** ／ **液晶なし**（⑤専用例外）／
表掲載台＝`bans`＝スランプ対象台 ／ ファイル名 ／ 除外・優秀台抽出
（`filter_recommended_machines()` / `_kojin_yushu_filter()` / フラット1回＋最初のブロックのみ採用）／
`_art_osusume_block_images()` の生成結果 ／ 9枠仕様 ／ HQ ／ 保存target ／
`_art_osusume_plan()` ／ WordPress（payload・H2/H3・full-width・nosplit）── **すべて無変更**。

🔄「その他を更新」は `_upd_bm` が「その他の優秀台」「ジャグラー統合」の2つだけを持つため、
⑤は**素通し**（二重パネル合成なし）。今回も触っていない。

### ⑥ 純粋テスト結果（81 PASS / 0 FAIL）

⑤1機種 → 単一機種経路（機種名が返る・`_pfn = M1.jpg`）／**パネル高さが全幅スケール
（幅400・パネル200×100 → 高さ200）**／**右半分に白余白なし（左右のピクセルが同一）**／
**旧実装では右半分が白だったことを同一入力で再現**／⑤1機種は
`_art_is_multi_machine=False`＝`machine_name None`／
⑤2機種→2枚(1段)・3機種→3枚(2段)・4機種→4枚(2段)・5機種→4枚・9機種→4枚（すべて
`_pfn` はブロック名のまま・`multi=True`＝機種名あり）／
**非⑤8種 × 3店舗＝24ケースで変更前後の画像バイト・戻り値が完全一致**
（`M1_高配分.jpg` / `M1.jpg` / その他の優秀台 / ジャグラー統合 / `M1(3台並び).jpg` /
`M1(列仕掛け).jpg` / 末尾 / バラエティ）／`_art_panel_max` は⑤=4・ジャグラー統合=2 維持／
**26関数の本体バイト一致**（上記パネル5関数・`draw_slump_graph`・`_attach_slump_to_table`・
`_art_osusume_block_images`・`_art_osusume_plan`・`filter_recommended_machines`・
`_kojin_yushu_filter`・`generate_recommended_block_image`・`show_auto_page` 等）／
⑤の液晶なし分岐・水色バーなし・ファイル名規則・`bans` 仕様・9枠仕様 維持／
`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は git 基準で diff 0／
`_art_osusume_panel_fn(` の出現は定義1＋⑦1＋⑧1＝3。

### ⑦ 今後の禁止事項

1. **⑤で1機種でもグリッド経路へ固定する実装へ戻さない**（`is_multi=... or _is_osu` は禁止）
2. **パネル引数に `_is_osu_*` を渡さない**（使うのは `_osu_multi_*`＝2機種以上）
3. **判定を「⑤に入力した機種数」にしない**（除外・優秀台抽出後の**表掲載機種数**で判定）
4. **機種名をファイル名から復元しない**（`bans` → `ban2mac` から取る）
5. **`オススメ優秀台_ブロックN.jpg` の出力ファイル名を変えない**／`_pfn` を保存名・plan・ban_map へ使わない
6. **`narabi_like` / `max_panels` を `_pfn` で判定しない**（必ず実ファイル名 `_bare`）
7. **`_apply_panel_to_table_img()` / `_build_variety_panel_grid()` / `_build_panel_row()` /
   `_insert_panel_into_machine_img()` / `_narabi_panel_names()` の本体を変更しない**
8. **2機種以上のパネル仕様（2→2 / 3→3 / 4→4 / 5〜9→上位4・最高差枚順・未登録繰り上げ・
   表示は台番昇順）を変更しない**
9. **ジャグラー統合の最大2（`_ART_JUG_PANEL2_STORES`）を変更しない**
10. **単一機種パネル対応のために `machine_name` を表示する変更をしない**
11. **⑦だけ／⑧だけ直さない**（両方 `_art_osusume_panel_fn()` を通す）
12. **⑤を 🔄 の `_upd_bm` へ追加しない**（二重パネル合成になる）
13. **除外・優秀台抽出・9枠・HQ・保存target・液晶なし・水色バーなし・WordPress を変更しない**
14. **高配分・全台系・その他優秀台・ジャグラー・末尾・並び・列・ランキング・島図・
    新小岩・高田馬場・秋葉原へ波及させない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用⑤：店舗単位永続化・抽出条件・ジャグラー統合画像のWP plan（2026-09-07）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用⑤「オススメ機種の優秀台」と、
WordPress plan のジャグラー統合画像だけ**。
正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館のオススメ条件と設定保存を拡張`・2026-09-07・
**`streamlit_app.py` / `wp_client.py` / `store_settings/渋谷新館.json` / `CLAUDE.md` の4ファイル**）。
既存節は削除・圧縮・統合・並べ替えしない（本節は⑤の
「1ブロック＝1画像」「単一機種パネル全幅」の各節を**上書きせず補う**）。

### ⓪ 変更点3つ

| | 旧 | **新（正式）** |
|---|---|---|
| ⑤の保存 | `article_page_inputs.json` の**日付（Excel）単位** | **`store_settings/{store}.json` の店舗単位**（日付をまたいで保持） |
| ⑤の最終抽出 | `_kojin_yushu_filter()`（機種種別の複合条件） | **ブロックごとの抽出条件（差枚閾値）**＝新小岩⑤と同じ |
| WP plan のジャグラー統合画像 | `FN_JUGGLER` を**無条件**に append（`optional=True`） | **実ファイルがあるときだけ** append |

---

## A. ⑤設定の店舗単位永続化

### ① 保存先と新規キー

**`store_settings/{store}.json`**（`load_store_settings` / `save_store_settings` を再利用。
**新しいJSONは作らない**）。

```json
"art_osusume_titles":   [str×6],
"art_osusume_machines": [[B1の6枠],[B2の6枠],[B3の6枠],[B4の6枠],[B5の9枠],[B6の9枠]],
"art_osusume_filters":  [str×6]
```

**★通常ページ⑤の `recommended_title_*` / `recommended_machines_*` /
`recommended_filter_*` / `rec_enabled` とは絶対に共用しない。**
渋谷新館の `store_settings` には**通常ページ⑤の `recommended_*` が既に実在**するため、
共用すると通常ページと記事用が混ざる。

### ② session_state キー（日付スコープに乗せない）

```
art_osu_title_{n}_{store}      n=0..5
art_osu_m_{n}_{i}_{store}      n=0..5, i=0..枠数-1
art_osu_f_{n}_{store}          n=0..5
```

**★`_art_widget_key()`（`_artw_{excel_stem}_…`）／`_art_txt()`／`_art_mac()` は⑤で使わない。**
店舗suffixのみのキーにすることで、日付を変えても widget identity が変わらず値が残る。
**②その他の記事用入力（②個別画像・ななこ・バラエティ・ランキング・記事上部など）は
従来どおり日付単位**。日付スコープの正式仕様
（display key / `expected_excel` ガード / `_art_restored_excel` ガード / `_artw_edited_*`）は
**そのまま維持**する。**日付スコープ全体の解除は禁止。**

### ③ 新設ヘルパー

```python
_ART_OSU_TITLES_KEY / _ART_OSU_MACHINES_KEY / _ART_OSU_FILTERS_KEY
def _art_osu_title_key(store, n) / _art_osu_mac_key(store, n, i) / _art_osu_f_key(store, n)
def _art_osu_settings(store) -> {"titles": […], "machines": [[…]], "filters": […]}   # 読み取り専用
def _art_osu_f_index(store, n) -> int      # session_state → 保存値 → 既定「プラス台」
def _save_art_osusume(store) -> None       # on_change 即保存
```

### ④ ★保存の存在ガード（新小岩と同一思想）

```
session_state にキーが ある  → 現在値を保存（**空欄も意図的クリアとして保存**）
キーが ない（未描画）        → 既存の保存値を維持（空で潰さない）
```

これにより **1枠クリア・全枠クリア・タイトル削除が最新設定として保存され、
日付を変えても古い値が復活しない**。
**「空欄だから過去値を復活」する実装へ戻さない**（削除できなくなる）。

### ⑤ 初期値の渡し方

- タイトル：`st.text_input(key=…, value=_osu_saved["titles"][n])`
- 機種名：**`render_machine_autocomplete_input(..., default=…)`**（＝`st.text_input(value=default)`。
  ⑤ `39f1f1e` の「seed だけで `value=` を渡さない実装へ戻さない」に準拠）
- 抽出条件：`st.radio(..., index=_art_osu_f_index(store, n))`
  （未描画 run で key が破棄されても保存値がラジオ先頭へ落ちない。新小岩 `_rec_f_index()` と同じ思想）

`on_change` は3ウィジェットすべて **`_save_art_osusume`**。

### ⑥ 日付単位保存の対象から⑤を外す

`_article_input_keys()` から**⑤の48キー（title 6＋機種 42）を削除**した。
**②その他のキーは1つも変更していない**（純粋テストで「⑤以外のキー列が変更前と完全一致」を確認）。
**`_save_article_inputs()` / `_restore_article_inputs()` は本体バイト無変更。**

### ⑦ 9/5 設定の初期移行（1回だけ・実施済み）

`article_page_inputs.json` の **`20260905_渋谷新館_20S.xlsx`** の⑤実値を読み取り、
`store_settings/渋谷新館.json` の `art_osusume_titles` / `art_osusume_machines` へ**1回だけ**反映した。
**推測で機種名を書かず、JSON実値のみを移行。**

| ブロック | タイトル | 機種（非空） |
|---|---|---|
| B1 | 週間オススメ北斗シリーズ | スマスロ北斗の拳 / 北斗転生2 |
| B2 | 月間オススメ東京喰種 | 東京喰種 |
| B3 | 月間オススメカバネリ海門決戦 | カバネリ海門決戦 |
| B4 | 3Fオススメ | ゴッド神々の軌跡 / 戦国乙女5 |
| B5 | 月間オススメジャグラーシリーズ | マイジャグV / ネオアイム / ファンキー2 / ゴージャグ3 / ハピジャグV / ジャグラーガールズ / ミスジャグ / ウルトラミラジャグ |
| B6 | （空） | （空） |

**機種合計 14件**。`art_osusume_filters` は**6ブロックすべて「プラス台」**（新規のため既定値）。
**ランタイムの自動 migration 処理は作らない**（今回1回の反映のみ）。

### ⑧ 過去 `article_page_inputs.json` の⑤キー

**削除・移動・掃除しない。**`art_osusume_title_*` / `art_osusume_m_*` は各日付エントリに残置し、
**以後参照しないだけ**（`kojin_y_8_秋葉原`・新小岩②の前例と同じ扱い）。
9/5 エントリの⑤48キーが残っていることを純粋テストで確認済み。

### ⑨ Cloud での制約（新小岩⑤と同じ）

**`store_settings` には Cloud→GitHub の同期経路が無い**（正式運用ルール 2026-08-10）。
⑤設定は**ローカルで編集 → commit/push → Cloud は再デプロイ/Reboot で受け取る**運用。
**今回 GitHub 同期機能は作らない。**

---

## B. ⑤の抽出条件（ブロック単位）

### ⑩ UI

各ブロックの機種名入力欄の**下**に
**`st.radio("抽出条件", _ART_OSU_F_OPTS, horizontal=True)`**。

| 表示＝内部値 | min_diff | 意味 |
|---|---|---|
| **プラス台** | **1** | **差枚 >= 1（★±0枚は含めない）** |
| **+1,000枚以上** | **1000** | 差枚 >= 1000 |
| **+2,000枚以上** | **2000** | 差枚 >= 2000 |

```python
_ART_OSU_F_OPTS: list[str] = list(_REC_F_OPTS)   # 新小岩の選択肢を再利用（本体は変更しない）
_ART_OSU_F_THR = {"プラス台": 1, "+1,000枚以上": 1000, "+2,000枚以上": 2000}
_ART_OSU_F_DEFAULT = "プラス台"
def _art_osu_thr(filter_value) -> int            # 不正値・未設定は「プラス台」＝1
```

**★`_rec_f_index()` は共用しない**（読むキーが `recommended_filter_{n}` で別体系）。
記事用は `_art_osu_f_index()`。

### ⑪ ★⑤の最終抽出は差枚閾値方式（`_kojin_yushu_filter` を使わない）

```python
_thr   = _art_osu_thr(_b.get("filter"))
_sel_m = _grp[(_dr >= _thr).values].copy()      # 新小岩⑤と同じ一本道
```

**`_kojin_yushu_filter()` 本体は変更・削除しない**（他ページ・高配分・その他優秀台・
②個別・pipeline が使用中。本体バイト一致を確認済み）。**⑤の新経路から外すだけ。**

### ⑫ 抽出順序（機種単位除外は必ず先）

```
1. ⑤全ブロックをフラット化（_art_osusume_flat）
2. filter_recommended_machines(..., ban_level=False) を **1回だけ**
   （空白・重複・②全台系・②高配分・②手入力済み・Excel未存在を除外）
3. 同一機種は最初のブロックだけ採用（_used）
4. 各ブロックで機種ごとの全台 DataFrame を取得
5. **そのブロックの抽出条件で差枚フィルタ**
6. concat
7. 機種グループ＝最小台番昇順／グループ内＝台番昇順
8. 画像生成（_build_machine_img_no_bar）
```

**`filter_recommended_machines()` をブロックごとに呼ばない**（全体重複除去が壊れる）。

### ⑬ 9/5 の 2252番台 ±0枚

新仕様では「プラス台＝差枚 >= 1」なので **9/5 ブロック1の `2252番台 ±0枚` は掲載対象外**。
以前の6台から5台になるのは**意図した正しい挙動**で、**不具合ではない**。

---

## C. 画像仕様（既存正式仕様をすべて維持）

- **表掲載台 ＝ `bans` ＝ スランプ対象台**（`_sel` を唯一の正とする）。新抽出条件で台が減れば
  表・スランプも同じ台だけになる。
- **最終掲載機種数が1機種 → 単一機種パネル全幅／2機種以上 → 複数機種パネルグリッド（最大4）**。
  判定は**入力機種数ではなく新抽出条件後の最終掲載機種数**（`_art_osusume_panel_fn()` /
  `_art_is_multi_machine()` が `bans`→`ban2mac` から判定するので自動追従）。
- **1機種 → スランプ内 `machine_name` なし／2機種以上 → あり。**
- **水色タイトルバーなし ／ ⑤は液晶なし。**
- **ファイル名 `オススメ優秀台_ブロック1〜6.jpg` は不変。**
- ⑦プレビューと⑧本番は**同じ `_art_osusume_collect()` / `_art_osusume_block_images()`**
  を使い、抽出条件も同じ店舗単位保存値から渡すので**条件がズレない**。

---

## D. ジャグラー統合画像の WordPress plan

### ⑭ 画像生成ロジックは変更しない

⑤へジャグラーが実掲載された日は、**既存の `run_step2_juggler()` が台番単位の除外
（`_jug_pool_osu = osusume_bans ∩ jug_bans_all`）で統合画像を作らない**（`d477a91`）。
**`run_step2_juggler` / `juggler_jobs` / `osusume_bans` / `_jug_pool_osu` は本体バイト無変更。**
**新しい「ジャグラー」文字列判定は追加しない**（`cfg["juggler_series"]` が正）。

### ⑮ 直した箇所（`wp_client.plan_blocks()` の1か所だけ）

```python
if jug_comb:
    if payload.get("juggler_comb_h3"):
        plan.append({"type": "h3", "text": H3_JUGGLER_COMB})
    plan.append({"type": "image", "file": FN_JUGGLER,
                 "label": "ジャグラーシリーズ優秀台", "optional": True})
```

旧実装は `FN_JUGGLER` の image 項目を**無条件**に append していたため、
統合画像を作らない日は `collect_files()` の `missing_optional` に入り
**「ℹ️ 次の画像は見つからないため本文へ入れません: ジャグラーシリーズ優秀台.jpg」**が毎回出ていた。

- **統合画像が実在する日の plan は旧実装と完全一致**（純粋テストで dict 一致を確認）。
- **個別ジャグラー高配分画像（`jug_imgs`）が実在する日は H2／H3／個別画像を従来どおり維持。**
- `build_payload` / `collect_files` / `build_content` / full-width / nosplit /
  Luminous（`linkDestination:"none"`）/ category / author / `WP_STATUS` / `WP_MAX_SIDE` は**無変更**。
- **`wp_client.py` で本体が変わったのは `plan_blocks` のみ**・新規/消失関数0。

---

## E. 純粋テスト結果（105 PASS / 0 FAIL）

**永続化**：9/5設定の移行一致（machines/titles とも元JSONと完全一致・14件）／B1〜4=6枠・B5〜6=9枠／
filters 6件=プラス台／`recommended_*` を壊していない／新キー3種が存在／
保存直後の値／**session_state を空にしても保存値から復元（＝日付切替後も同じ設定）**／
collect も同値／変更後が以後の最新設定／**1枠クリア・全枠クリア・タイトル空欄が保存され復活しない**／
filter が日付越しに保持／未描画枠は既存値を維持／index 解決順。

**日付scope非回帰**：**32関数の本体バイト一致**（`_save_article_inputs` / `_restore_article_inputs` /
`_art_widget_key` / `_art_saved_value` / `_on_article_widget_change` / `_art_kojin_default` /
`_kojin_yushu_filter` / `filter_recommended_machines` / `generate_recommended_block_image` /
`_save_rec_machines` / `_save_rec_titles` / `_save_rec_enabled` / `_rec_f_index` /
`run_step2_juggler` / `run_step3_other` / `run_auto_pipeline` / パネル系5関数 /
`draw_slump_graph` / `_attach_slump_to_table` / `_art_high_title_bar` / `_save_jpeg` /
**`show_auto_page`** ほか）／⑤48キーだけ `_article_input_keys` から消え、
**⑤以外のキー列は3店舗すべてで変更前と完全一致**／過去 `article_page_inputs.json` の⑤48キーは残置。

**抽出条件**：閾値 1/1000/2000・不正値は1／プラス台で **±0枚（104）を除外**／
負差枚は全条件で除外／②全台系・②高配分の除外が先／同一機種は最初のブロックのみ／
表掲載台==bans／並び順（機種最小台番昇順＋台番昇順）。

**画像**：1機種 multi=False（全幅・machine_name None）／2機種 multi=True（grid・あり）／
最大4パネル／水色バーなし／**⑤生成が `_kojin_yushu_filter(_m` を呼ばない**／液晶なし分岐／
ファイル名不変／plan は1ブロック1画像。

**ジャグラー/WP**：統合画像なしで `missing_optional` に `FN_JUGGLER` が入らない／
plan に `FN_JUGGLER` が入らない／**旧実装では入っていたことを同一 payload で再現**／
H2 は従来どおり出る／画像なしなら H3 統合も出ない／**統合画像実在時は plan が旧実装と完全一致**／
個別 `jug_imgs` のみでも H2＋H3＋個別画像を維持／`run_step2_juggler` 本体一致／
**`wp_client` の変更関数は `plan_blocks` のみ**／**高田馬場の本文HTMLが旧実装と完全一致**／
full-width・nosplit・Luminous・category/author/status/WP_MAX_SIDE 不変／
`convert_narabi_pil.py` / `shimazu_renderer.py` diff 0／9枠仕様維持。

---

## F. 今後の禁止事項

1. **⑤を日付単位保存（`article_page_inputs.json`）へ戻さない**
2. **⑤のキーを通常ページ⑤の `recommended_*` と共用しない**
3. **⑤に `_art_widget_key()` / `_art_txt()` / `_art_mac()` の日付スコープを再適用しない**
4. **②その他の記事用入力を店舗単位へ変えない／日付スコープ全体を解除しない**
5. **保存の存在ガード（キーあり→現在値・空も保存／キーなし→既存維持）を崩さない**
6. **「空欄だから過去値を復活」する実装にしない**
7. **`render_machine_autocomplete_input(default=)` → `value=` を外さない**（⑤ `39f1f1e`）
8. **`st.radio(index=_art_osu_f_index(...))` を外さない**（保存値が先頭へ落ちる）
9. **`_rec_f_index()` / `_save_rec_*` / `_REC_F_OPTS` / `_REC_F_DEFAULT` /
   `generate_recommended_block_image()` を変更しない**（新小岩は参考実装として読むだけ）
10. **⑤の最終抽出へ `_kojin_yushu_filter()` を戻さない／`_kojin_yushu_filter()` 本体を変更・削除しない**
11. **「プラス台」を `>= 0` にしない**（`>= 1`。±0枚は含めない）
12. **`filter_recommended_machines()` をブロックごとに呼ばない／機種単位除外を抽出条件より後にしない**
13. **表掲載台＝bans＝スランプ対象台をズラさない**
14. **単一機種パネル全幅・machine_name条件・水色バーなし・液晶なし・ファイル名を変えない**
15. **`run_step2_juggler` / `osusume_bans` / `_jug_pool_osu` を変更しない／
    「ジャグラー」文字列判定を追加しない**
16. **`FN_JUGGLER` を実ファイルの有無に関係なく plan へ append する実装へ戻さない**
17. **`wp_client.py` の `plan_blocks` 以外を変更しない**（build_payload / collect_files /
    build_content / full-width / nosplit / Luminous / category / author）
18. **`store_settings` へ GitHub 同期機能を作らない**（既存運用ルールを維持）
19. **過去 `article_page_inputs.json` の⑤キーを削除・移動・掃除しない**
20. **ランタイムの自動 migration を作らない**
21. **高田馬場・秋葉原・新小岩・通常ページへ波及させない**
22. **9枠仕様（B1〜4=6 / B5〜6=9・`_art_osusume_per_block()`）を巻き戻さない**
23. **無関係なリファクタ・未使用コード整理をしない**

### G. 追記：`_ART_OSU_F_OPTS` の定義位置（2026-09-07・同日修正）

**`_ART_OSU_F_OPTS: list[str] = list(_REC_F_OPTS)` は `_REC_F_OPTS` の定義より後
（`_REC_F_DEFAULT` の直後）に置く。**

初回実装で⑤ヘルパー群と一緒に `_REC_F_OPTS` より前へ置いてしまい、
アプリ起動時に **`NameError: name '_REC_F_OPTS' is not defined`（module 直下）** で
記事用ページが表示できなくなった（ローカル実機で検出・同日修正）。
`_art_osu_thr()` / `_ART_OSU_F_THR` / `_ART_OSU_F_DEFAULT` も同じ位置へ移した。
⑤の他のヘルパー（`_art_osu_settings` / `_save_art_osusume` / `_art_osu_f_index` など）は
`_ART_OSU_F_OPTS` を**関数の中でしか参照しない**ので元の位置のままでよい。

**再発防止**：純粋テストに
**「`python -c "import streamlit_app"` が returncode 0」**と
**「`_REC_F_OPTS` の定義位置が `_ART_OSU_F_OPTS` より前」**の2項目を追加した。
module 直下の定数を追加・移動するときは、**構文チェックだけでなく実 import を必ず通すこと。**

## 渋谷新館 ローテ用：週間オススメ表と月間オススメ表①②③（2026-09-07）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】ローテ用の週間/月間オススメ表の並び・名称・
表示期間だけ**。正式コード commit は本節と**同一の commit**
（`feat: 渋谷新館ローテの月間オススメ表を拡張`・2026-09-07・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**・`streamlit_app.py` は7ハンク）。
**`weekly_items.json` / `rote_machines.json` / `wp_client.py` は変更していない。**
既存節は削除・圧縮・統合・並べ替えしない。

### ① 正式な画面順（渋谷新館 ローテ用）

```
📄 Excelファイルをアップロード
📈 自動取得データを使用中: …xlsx
📅 週間オススメ表            ← t1（①機種名入力の**前**）
機種名を入力①（部分一致・最大6機種・入力順に表示）
📅 月間オススメ表①            ← t2（東京喰種・完全に従来どおり）
📅 月間オススメ表②            ← t4（新規・カバネリ海門決戦）
📅 月間オススメ表③            ← t3（旧「週間オススメ表②」・ジャグラー系）
```

**旧順（①6機種入力 → 週間①(t1) → 週間②(t3) → 月間①(t2)）へ戻さない。**
上野本館は従来どおり（t2 → expander t4 → expander t5）で、**渋谷新館の変更を波及させない**。

### ② table_num と表示名の対応（内部番号は変えない）

| table_num | 渋谷新館の表示名 | 備考 |
|---|---|---|
| **1** | **週間オススメ表**（旧「週間オススメ表①」） | 渋谷新館専用 |
| **2** | 月間オススメ表① | 東京喰種・**無変更** |
| **4** | **月間オススメ表②**（新規） | 上野本館の t4 と同じ番号を共用 |
| **3** | **月間オススメ表③**（旧「週間オススメ表②」） | 渋谷新館専用・`cell_machines` 方式 |

**★`table_num` の番号を振り直さない。**旧番号のまま表示名だけを変えることで、
`weekly_items.json` の `t1` / `t2` / `t3` の既存データ・`weekly_machine_{store}_t{n}` の
session_state キー・ローテ①②③の機種名連動（②=t1 / ③=t2）がそのまま生きる。
**データ移行は不要・実施しない。**

### ③ 月間オススメ表②（t4・新規）

- **①機種名／②タイトル／③項目（最大8＝`_WEEKLY_N_ITEMS`）／④表示期間／⑤表入力**は
  **月間オススメ表①（t2）と同一の共通関数 `show_weekly_table_section()`** で描画する。
  **t4 専用のUI・専用の保存処理・専用の描画関数は作らない。**
- **session_state キー・保存キーは t4 のもの**（`weekly_machine_{store}_t4` /
  `weekly_item_{store}_t4_{i}` / `weekly_ck_{store}_t4_{i}_{j}` /
  `weekly_items.json` の `t4`）。**t2 とは完全に独立**しており、
  **月間①の値・チェック・タイトル・機種名を共有しない。**
- 対象機種は **`カバネリ海門決戦`**（`store_settings/渋谷新館.json` / `rote_machines.json` /
  `article_page_inputs.json` で実データを確認した正式文字列）。
  **コードへハードコードしない。**ユーザーが①機種名欄へ入力する。
- **`weekly_items.json` の渋谷新館には `t4` が存在しない**（実データで確認）ため、
  **初回は全欄空欄**で始まる。これが正常。**空の t4 を事前に書き込まない。**
- 機種名・項目がすべて空なら画像を生成しない（既存の t4/t5 スキップ条件をそのまま使う）。

### ④ 月間オススメ表③（t3）の④は「表示期間」（開始日UIは廃止）

- **`④ 開始日を選択` の date_input は表示しない。**
- 代わりに **`④ 表示期間`** を **月間オススメ表①と同じ計算**で自動表示する
  （渋谷新館は **Excelの日付が最終日・過去7日間**）。
- 実装は**期間計算をコピーせず、既存の分岐条件に `3` を足すだけ**：

  | 箇所 | 変更 |
  |---|---|
  | UI（`show_weekly_table_section`） | `_use_excel_date = _tn in (2, 3, 4, 5) and (excel_date is not None or store == "上野本館")` |
  | 画像生成（`show_rote_page` の保存ループ） | `if _wtn in (2, 3, 4, 5):` で Excel日付から期間を算出 |

  **★生成側にも `3` を足すことが必須。**生成側は `_use_excel_date` を持たず、
  非対象なら `weekly_start_{store}_t{n}`（開始日widget）から `_wt_start` を取るため、
  UI だけ直すと **`_wt_start = None` になり月間オススメ表③の画像が生成されない。**
- **日付文字列をハードコードしない。**期間は必ず Excel 由来（`_rd` / `excel_date`）から求める。
- **⑤表入力は従来どおり `cell_machines` の multiselect 方式**（`t3_ms_{store}_{i}_{j}`・
  正本は `weekly_items.json` の `t3.cell_machines`）。
  `_use_excel_date=True` になっても保存形式は変わらないため**移行不要**。
  開始日変更時の `cell_machines` リセットは既に `if not _use_excel_date:` で守られており、
  **Excel日付モードでは選択が消えない。**
- **`weekly_items.json` の `t3.start_date`（旧 開始日の保存値）は削除しない。**
  以後参照されないだけ（`kojin_y_8_秋葉原`・新小岩②の残置と同じ扱い）。

### ⑤ 復元・保存・画像生成のリスト

| 箇所 | 渋谷新館 | 上野本館 |
|---|---|---|
| 復元 `_wt_tn_list` | **`(1, 2, 3, 4)`** | `(2, 4, 5)`（無変更） |
| 保存/画像生成 `_wt_save_list` | **`(1, 2, 3, 4)`** | `(2, 4, 5)`（無変更） |

**t4 を両方へ追加すること。**片方だけだと「入力しても復元されない」または
「復元されるが画像が出ない」状態になる。

### ⑥ ファイル名（タイトル文字列に依存しない）

機種名が入っていれば **`{機種名}表.png`**、空のときだけ既存のフォールバック名を使う。

| table_num | 機種名あり | 機種名なし（フォールバック・**変更していない**） |
|---|---|---|
| 1 | `{機種名}表.png` | `週間オススメ表①.png` |
| 2 | `{機種名}表.png` | `月間オススメ表.png`（渋谷新館） |
| 4 | `{機種名}表.png` | `月間オススメ表②.png` |
| 3 | `{機種名}表.png` | `週間オススメ表②.png` |

**表示名を変えたことを理由にファイル名規則を変更しない**（過去の出力・運用と揃える）。
保存先は従来どおりローテ用の出力フォルダ、ZIP はフォルダを丸ごと固めるため自動で含まれる。

### ⑦ 結果テキスト（今回の対象外）

`_generate_shibuyashinkan_result_texts()` は従来どおり
**`weekly_items`(t1) / `monthly_items`(t2) / `weekly_items2`(t3)** を受け取る。
**t4 用の結果テキストは今回追加していない。**
**この節を理由に結果テキストの引数・書式・ファイル名を変更しない。**
必要になった場合は別案件として調査→承認のうえ実装する。

### ⑧ 無変更（今回いっさい触れていない）

`show_weekly_table_section()` の①〜⑤の入力仕様・`_WEEKLY_N_ITEMS = 8` ／
`_save_weekly_items()` / `_load_weekly_items()` / `_load_weekly_title()` /
`_load_weekly_machine()` / `_load_weekly_checks()` / `_load_weekly_blank_days()` /
`_load_weekly_blank_date_checks()` / `_load_t3_cell_machines()` /
`_weekly_table_data()` / `_draw_weekly_table_image()` / `_weekly_table_html_image()` /
`_add_margin()` ／ 上野本館の `monthly_start` リセット仕様 ／
**`f23e0e4`（月間オススメ表①の空欄日保持・`blank_date_checks` 優先とフォールバック条件）** ／
`_checked_pins()` ／ ローテ画像 ／ ランキング画像 ／ Cloud↔GitHub同期（`_GH_SYNC_FILES`）／
記事用 ／ 結果ポスト用 ／ Pision取得 ／ 機種名変換 ／ 他店舗。

### ⑨ 今後の禁止事項

1. **画面順（週間 → ①6機種入力 → 月間①②③）を旧順へ戻さない**
2. **`table_num` の番号を振り直さない**（表示名だけを変える）
3. **`weekly_items.json` のキー（`t1`/`t2`/`t3`/`t4`）を改名・移行しない**
4. **月間②（t4）に月間①（t2）の session_state / 保存キーを共有させない**
5. **カバネリ海門決戦をコードへハードコードしない**
6. **月間③（t3）へ `④ 開始日を選択` を復活させない**
7. **`_use_excel_date` と生成側の期間分岐の**どちらか片方だけ**に `3` を足さない**
8. **期間計算を3か所へコピペしない／日付をハードコードしない**
9. **t3 の `cell_machines` 方式を日付キー方式へ変えない／`t3.start_date` を削除しない**
10. **`_wt_tn_list` / `_wt_save_list` のどちらか片方だけに `4` を足さない**
11. **ファイル名規則・保存先・ZIP対象を変更しない**
12. **結果テキストへ t4 を勝手に足さない**
13. **上野本館・他店舗・記事用・結果ポスト用へ波及させない**
14. **`f23e0e4` の空欄日保持仕様を巻き戻さない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 ローテ用：週間UIの整理と月間オススメ表③の有効日判定（2026-09-07）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】ローテ用の「📅週間オススメ表」ブロックと
「📅月間オススメ表③」の表入力だけ**。直前の
「## 渋谷新館 ローテ用：週間オススメ表と月間オススメ表①②③（2026-09-07）」の追加修正であり、
同節は削除・書き換えしない。正式コード commit は本節と**同一の commit**
（`fix: 渋谷新館ローテの週間UIと月間表の日付判定を修正`・2026-09-07・
**`streamlit_app.py` と `CLAUDE.md` の2ファイルのみ**）。
**`weekly_items.json` / `rote_machines.json` / `wp_client.py` は変更していない。**

### ① 「📅週間オススメ表」は見出し＋6機種入力欄だけ

```
📈 自動取得データを使用中: …xlsx
📅 週間オススメ表                          ← 見出しは残す
機種名を入力①（部分一致・最大6機種・入力順に表示）  ← 6枠は残す
📅 月間オススメ表① → ② → ③
```

- **旧週間表の詳細UIは表示しない**：①機種名／②タイトル／③項目（最大8）／
  ④開始日を選択／⑤表入力／`💾 週間オススメ表をPNGで保存`。
- **`show_weekly_table_section(store, table_num=1)` を呼ばない**（`st.markdown` の
  区切り＋見出しだけを出す）。**共通関数 `show_weekly_table_section()` 本体は変更していない**
  （上野本館・月間①②③が共用しているため）。
- **6機種入力欄（`rote1_mname_0〜5`）は完全に従来どおり**。
  session_state / `rote_machines.json` の保存・復元 / `_rote_init_*` / `_on_rote_name_change` /
  ローテ画像・ランキング画像・結果テキストは**いっさい変更していない**。

### ② 旧週間表（t1）の保存値は削除せず、session_state へ復元するだけ

**`weekly_items.json` の `t1`（items / title / checks / start_date / machine_name /
blank_days）は削除・移行しない。**

UIが無くなると t1 の widget キーが作られないため、**そのままでは**
渋谷新館の **ローテ②の機種名（`weekly_machine_{store}_t1` 由来）・結果テキストの
`weekly_items`・週間オススメ表①の画像生成**が空になってしまう。
そこで見出しの直後で**保存値を session_state へ1回だけ seed** する
（フラグ `_weekly_t1_seeded_{store}`）：

```
weekly_machine_{store}_t1 / weekly_title_{store}_t1 /
weekly_item_{store}_t1_{i} / weekly_ck_{store}_t1_{i}_{j} / weekly_start_{store}_t1
```

- これらは**widget キーではない通常の session_state 値**になるので stale widget GC で消えない。
- **`_wt_tn_list` / `_wt_save_list` の `1` は外さない。**外すと週間オススメ表①の画像・
  ローテ②の機種名が消える。**seed によって出力は従来と同一**になる。
- **この seed を消して「UIが無いから t1 は未参照」にしてはならない。**

### ③ 月間オススメ表③（t3）の未来日・対象外日にチェックを残さない

#### 原因（月間①との違い）

| | 保存形式 | 9/7（Excel日付）列 |
|---|---|---|
| **月間①（t2）** | **日付キー `date_checks`**（無ければ `checks` + `start_date` から**日付へ変換**して読む＝`_load_weekly_date_checks`） | その日付の保存が無いので**空欄**（正しい） |
| **旧 月間③（t3）** | **位置キー `cell_machines`（"i,j"）を位置そのままで復元** | 旧 `start_date=8/31` 基準の位置6（＝8/31+6日＝9/6）のデータが、新しい表示期間（9/1〜9/7）の**最終列 9/7 に出ていた** |

**＝「未来日にチェックが残る」現象は、位置キーを新しい日付窓へそのまま当てていたことが原因。**
今日・現在日付・9/7 などの特定日付の問題ではない。

#### 正式仕様

**月間オススメ表③は月間オススメ表①と同じ「日付キーを正とし、無ければ旧形式を
`start_date` から日付へ変換して読む」方式にする。**

- 新設ローダー **`_load_t3_cell_date_machines(store)`**
  → `{date_iso: {"i": [機種, …]}}`。
  `t3.cell_date_machines` が空なら **`cell_machines` + `t3.start_date` から変換**する
  （`_load_weekly_date_checks` とまったく同じ思想）。
- 保存は `_save_weekly_items(..., cell_date_machines=…)`（新規引数）。
  **表示期間内の日付だけを更新し、期間外の既存日付は保持**する。
- **旧 `cell_machines`（位置キー）と `t3.start_date` は削除しない。**
  新規保存では書き換えず、**読み取り時のフォールバック元としてのみ残置**する。
- したがって **保存済みチェックがあっても、その日付に該当しない列（未来日・対象外日）には
  表示されない**。有効日列の既存チェックは**日付どおりに維持**される。
- **特定日付のハードコード・`today` 判定・「最終列だけOFF」のような実装は禁止。**

#### UI・PNG・本番生成で同じ判定を使う

| 経路 | 実装 |
|---|---|
| ⑤表入力（multiselect） | `_use_excel_date` のとき `_load_t3_cell_date_machines()` から現在の表示期間へ復元（`_cm_dict3`） |
| `💾 月間オススメ表③をPNGで保存` | **UIと同じ `_cm_dict3` を使う**（旧実装は `_load_t3_cell_machines()` を直読みしていた） |
| `🎰 画像を生成する`（本番・ZIP） | `_load_t3_cell_date_machines()` を正とし、空のときだけ旧位置キーへフォールバック |

**UIだけ直して画像に残る（またはその逆）状態を作らない。**

### ④ 月間①・②への影響

- **月間①（t2）は無変更**（`date_checks` / `blank_date_checks` / `f23e0e4` の空欄日保持仕様を維持）。
- **月間②（t4）は t2 と同じ日付キー方式**の共通経路に乗っているため、追加対応は不要。
- t3 の **`blank_days`（（空欄にする）行）は位置キーのまま**で今回変更していない。
  必要になった場合は別案件として調査・承認のうえ対応する。

### ⑤ 純粋テスト（7 PASS / 0 FAIL）

旧位置キーと `start_date` が残置されている ／ 日付キーへ変換できる ／
変換後の日付が 8/31〜9/6 に収まる ／ **表示期間 9/1〜9/7 で最終列（9/7）が空になる** ／
有効日列（9/1〜9/6）の既存チェックは維持される ／
**旧実装なら最終列にデータが残っていたことを同一データで再現** ／
表示期間外の日付（8/31）は表に出ない。

### ⑥ 今後の禁止事項

1. **旧週間表の詳細UI（①〜⑤・PNG保存）を復活させない**／`show_weekly_table_section(…, table_num=1)` を呼び戻さない
2. **`📅週間オススメ表` の見出しと6機種入力欄を消さない**
3. **6機種入力欄の session_state / 保存 / 復元 / 画像生成 / ローテ処理を変更しない**
4. **`weekly_items.json` の `t1` / `t3.cell_machines` / `t3.start_date` を削除・移行しない**
5. **t1 の session_state seed を削除しない**（ローテ②の機種名・結果テキスト・週間①画像が壊れる）
6. **`_wt_tn_list` / `_wt_save_list` から `1` を外さない**
7. **月間③を位置キー直読みへ戻さない**
8. **特定日付・`today`・「最終列だけOFF」のハードコード判定を入れない**
9. **UI・個別PNG・本番生成のどれか1つだけに有効日判定を入れない**
10. **`_load_weekly_date_checks()` / `date_checks` / `blank_date_checks` / `f23e0e4` の月間①仕様を変更しない**
11. **`show_weekly_table_section()` 本体を今回の理由で書き換えない**（上野本館・月間①②が共用）
12. **他店舗・記事用・結果ポスト用・新小岩・高田馬場・秋葉原・WordPress へ波及させない**
13. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 ローテ用：生成物の再編・北斗統合・カバネリ・月間ジャグラー（2026-09-07）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】ローテ用の生成物と結果テキストだけ**。
直前2節（`76070d0` / `509ec07`）の追加修正であり、両節は削除・書き換えしない。
正式コード commit は **`a011c33`**（`feat: 渋谷新館ローテの生成物と結果テキストを再編`・
**`streamlit_app.py` の1ファイルのみ**・+87／−36）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は無変更。**

### ① 旧「週間オススメ表」の詳細表画像は生成しない

- 対象ファイルは **`{t1機種名}表.png`**（実データでは `スマスロ北斗の拳表.png`。
  機種名が空なら `週間オススメ表①.png`）。
- UIを廃止（`509ec07`）しても**生成側の `_wt_save_list` に `1` が残っていた**ため出力が続いていた。
  正式値は **`_wt_save_list = (2, 3, 4) if store == "渋谷新館" else (2, 4, 5)`**。
- **`_wt_tn_list`（復元）からは `1` を外さない。**ローテ②の機種名・結果テキストが
  t1 の保存値に依存しているため。
- **週間オススメ表の見出しと6機種入力欄（`rote1_mname_0〜5`）はそのまま。**
  6機種のローテ画像・ランキング・保存・復元・`rote_machines.json` は無変更。
- **`weekly_items.json` の `t1`（machine / title / items / checks / start_date / blank_days）は
  削除しない。**`509ec07` の session_state seed をそのまま維持する
  （これを消すとローテ②の機種名と結果テキストが壊れる）。

### ② 週間オススメ（北斗シリーズ）の結果テキストを1ファイルへ統合

**正式ファイル名は `{6機種入力の先頭機種}結果.txt`**（実データでは **`北斗転生2結果.txt`**）。
**`スマスロ北斗の拳結果.txt`（旧テキスト②）は渋谷新館ローテでは生成しない。**

本文構成（実出力）：

```
9/6(日)👨‍💻結果👨‍💻
エスパス渋谷新館

🔥北斗シリーズ🔥
🔥週間オススメポスター🔥

👊スマスロ北斗の拳👊
📌5,000枚超📌
💫2044番台
…
👊北斗転生2👊
📌3,000枚超📌
💫2069番台
…
```

- **掲載順は「週間オススメ表の機種（t1＝`machine_inputs2`）→ 6機種入力（`machine_inputs1`）」**の
  重複除去順。**機種名をコードへハードコードしない**（現在の設定値をそのまま使う）。
- 系列見出しは定数 **`_SHIBUYA_WEEKLY_SERIES = "北斗シリーズ"`**。
  機種名からは導出できないため、既存の `🤡ジャグラーシリーズ🤡` と同じ「固定文言」として持つ。
- **差枚帯・台番の算出は既存 `_tier_block()` をそのまま再利用**
  （`📌10,000枚超📌` / `📌5,000枚超📌` / `📌3,000枚超📌` / `📌1,000枚超📌`、
  差枚 >= 1000 のみ、**差枚降順→台番昇順**）。**新しい閾値・並び順を作らない。**
  今回のサンプルに1,000枚帯が無くても**帯を削らない**。
- **各機種の台番はその機種自身の実データ**から算出する（`_tier_block([機種名])`）。
- **当日データに1台も無い機種はセクションごと出さない**（片方だけデータがある日は
  存在する方だけ本文へ）。両方無い日も**ヘッダー＋🔥見出しは出す**（既存の空データ時と同じ）。
- 旧テキスト②の戻り値は `""` を返すだけにし、**ファイル書き出しを削除**した
  （`_generate_shibuyashinkan_result_texts` の戻り値は5要素・`text2` は互換のため残置）。

### ③ 月間オススメ表②（カバネリ）のローテ画像と結果テキスト

- 機種は **月間オススメ表②（t4）の①機種名**を正とする（`weekly_machine_{store}_t4`）。
  **機種名をコードへハードコードしない。**実データの正式文字列は **`カバネリ海門決戦`**。
- 渋谷新館は `machine_inputs4 = [t4機種]` を設定し、ローテ画像の生成対象を
  **`_n_cat = 4`**（①〜④）へ拡張する。**既存の `generate_rote_image()` をそのまま使う。**
  ランキング画像は従来どおり渋谷新館では作らない。
- **ファイル名は既存規則 `{機種名}ローテ.png` / `{機種名}結果.txt` に従う**
  → **`カバネリ海門決戦ローテ.png` / `カバネリ海門決戦結果.txt`**。
  （希望名「カバネリのローテ.png」ではなく既存命名規則を優先。以後この名前を変更しない。）
- 結果テキスト（テキスト⑤）の構成：

```
{日付}👨‍💻結果👨‍💻
エスパス渋谷新館

🚂{t4機種名}🚂
🚂月間オススメポスター🚂

✅毎日何かしらの仕掛けアリ!?
📍{t4の③項目1}
…
📌5,000枚超📌 / 📌3,000枚超📌 / 📌1,000枚超📌 …（実データ）
```

- **📍の説明5項目は「月間オススメ表②の③項目」から出す**（月間①＝t2 と同じ構造）。
  **機種固有の文言をコードへ埋め込まない。**実運用値は
  `オールスター(全台系!?)` / `来栖2分割(高配分◎!?)` / `来栖3分割(高配分〇!?)` /
  `甲鉄城(列!?)` / `ボーイミーツガール(並び!?)`（`weekly_items.json` の t4 items）。
- 差枚帯は**既存 `_tier_block()` を再利用**（別実装しない）。
- t4機種が未設定なら結果テキストを書き出さない（例外を出さない）。
- ZIP は `_make_zip_bytes(_rote_out_dir)` でフォルダを丸ごと固めるため、
  カバネリの画像・テキストも自動的に含まれる。

### ④ 月間オススメ表③（ジャグラー）を「月間」表記へ

| 対象 | 正式 |
|---|---|
| 画像の黒バー | **`月間オススメ ジャグラーシリーズ`** |
| 結果テキスト | **`🚨月間オススメポスター🚨`** |

- **黒バーの文字列は `weekly_items.json` の `t3.title`（②タイトル入力のユーザー値）由来**で、
  コードのハードコードではない。今回アプリのUIから正規の保存経路で
  `週間オススメ ジャグラーシリーズ` → **`月間オススメ ジャグラーシリーズ`** へ更新した。
- あわせて**コード側の既定タイトルも t3 は「月間オススメ」**にした
  （UI `_default_title` / 生成側 `_wt_default_title` / t3 個別PNGボタンの fallback。
  いずれも `_tn == 1` / `_wtn == 1` のときだけ「週間オススメ」）。
- 結果テキストは `🚨週間オススメポスター🚨` → **`🚨月間オススメポスター🚨`** の1行のみ変更。
  **`🤡ジャグラーシリーズ🤡`・日付・店舗名・`✅毎日何かしらの仕掛けアリ!?`・📍項目・
  差枚結果・機種別結果・台番・絵文字は変更しない。**
- **他店舗の「週間」表記は一括変更しない**（上野本館・その他は無変更）。

### ⑤ 古い生成物を正式出力として誤収集しない

ローカルの出力フォルダ（`Desktop/{YYYYMMDD}_{店舗}`）は日をまたいで再利用され、
**ZIP はフォルダを丸ごと固める**ため、廃止した生成物が残ると混入する。

そこで**渋谷新館の結果テキスト書き出し直後に、今回の正式出力名と一致しないものだけ**を削除する。

| 削除対象（完全一致のみ） | 由来 |
|---|---|
| `{t1機種名}表.png`（無ければ `週間オススメ表①.png`） | 旧週間詳細表画像 |
| `{t1機種名}結果.txt`（＝旧テキスト②） | 北斗統合前の単独ファイル |

- **今回の正式出力（`_sh_r1_fn` / `_sh_r3_fn` / `_sh_r4_fn` / カバネリ）と同名なら削除しない。**
- **glob・部分一致・フォルダ一括削除は禁止。**ユーザーが置いた無関係ファイルには触れない。
- 実機で `スマスロ北斗の拳表.png` / `スマスロ北斗の拳結果.txt` を出力フォルダへ置いた状態から
  ⑦生成を実行し、**2ファイルとも削除され、他の生成物は正常**であることを確認済み。

### ⑥ 速報・確定の両対応

日付は既存どおり **Excelファイル名の `YYYYMMDD`（`_rd`）** から求め、曜日も既存処理を使う。
**速報専用の分岐・日付のハードコードはしない。**

### ⑦ 実機確認（2026-09-07・ローカル・確定 9/6 データ 433台・`🎰 画像を生成する` 実行）

出力フォルダ `Desktop/20260906_渋谷新館`：

```
カバネリ海門決戦ローテ.png      ← ★新規
カバネリ海門決戦結果.txt        ← ★新規
カバネリ海門決戦表.png          （月間②の表）
ジャグラー系表.png              黒バー＝月間オススメ ジャグラーシリーズ ★
ジャグラー系結果.txt            🚨月間オススメポスター🚨 ★
スマスロ北斗の拳ローテ.png      （維持）
北斗転生2ローテ.png             （維持）
北斗転生2結果.txt               ★2機種統合（スマスロ北斗の拳→北斗転生2）
東京喰種ローテ.png / 東京喰種結果.txt / 東京喰種表.png（月間①・非回帰）
```

**`スマスロ北斗の拳表.png` と `スマスロ北斗の拳結果.txt` は生成されず、
残置分も削除された**ことを実ファイルで確認。

**注意（誤記しないこと）**：9/7 は確定データが未公開・速報も再取得できなかったため、
**実機確認は確定 9/6 データで実施した**。日付ソースに依存しないロジックのため
9/7速報でも同一に動作するが、**「9/7速報で実機確認済み」とは書かない。**

### ⑧ 純粋テスト（22 PASS / 0 FAIL）

ヘッダー日付＋店舗 ／ 🔥北斗シリーズ🔥 ／ 🔥週間オススメポスター🔥 ／
スマスロ北斗の拳が先 ／ 機種ごとに自機種の台番 ／ 既存差枚帯の再利用 ／ 旧テキスト②が空 ／
ジャグラー月間表記＋その他本文維持 ／ カバネリ見出し・固定リード・📍項目・実データ差枚 ／
月間①非回帰 ／ 片方だけデータ→存在する方のみ ／ データ皆無でもヘッダー維持 ／
カバネリ未設定でも例外なし ／ `_wt_save_list=(2,3,4)` ／ t3既定タイトルが月間 ／
`_n_cat=4` ／ 旧ファイル削除処理の存在 ／ 旧テキスト②の書き出し0件。

### ⑨ 無変更

`generate_rote_image()` / `generate_ranking_image()` / `_draw_weekly_table_image()` /
`_weekly_table_html_image()` / `_tier_block()` の条件 / `_rote_match_sub()` /
`_save_rote_machines()` / `_load_weekly_*` / `_save_weekly_items()` の既存引数 /
`_make_zip_bytes()` / 月間①（t2・`f23e0e4`）/ 月間②③の日付キー判定（`509ec07`）/
上野本館 / 他店舗 / 記事用 / 結果ポスト用 / 新小岩 / WordPress。

### ⑩ 今後の禁止事項

1. **`_wt_save_list` に `1` を戻さない**（旧週間詳細表画像を復活させない）
2. **`_wt_tn_list` から `1` を外さない／t1 の session_state seed を消さない**
3. **`weekly_items.json` の `t1` / `t3.cell_machines` / `t3.start_date` を削除しない**
4. **週間オススメ表の見出し・6機種入力欄・ローテ処理を変更しない**
5. **`スマスロ北斗の拳結果.txt` を渋谷新館ローテで再び生成しない**（他店舗・他ページは対象外）
6. **北斗統合の掲載順（t1機種→6機種入力）を入れ替えない／機種名をハードコードしない**
7. **`_tier_block()` の帯・条件・並び順を変更しない／帯を削らない**
8. **カバネリ専用の説明文をコードへ埋め込まない**（t4の③項目から出す）
9. **`カバネリ海門決戦ローテ.png` / `カバネリ海門決戦結果.txt` の命名規則を変えない**
10. **t3 の既定タイトルを「週間オススメ」へ戻さない**
11. **ジャグラー結果テキストの `🚨月間オススメポスター🚨` を戻さない／他の本文を変えない**
12. **他店舗の「週間」表記を一括変更しない**
13. **古いファイル対策を glob・部分一致・フォルダ一括削除にしない**
14. **出力フォルダのユーザーファイルを無条件削除しない**
15. **速報／確定で別ロジックにしない・日付をハードコードしない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 ローテ用：週間ローテ画像の機種別分割・月間ジャグラー分数拡張（2026-09-07・`475a6c2`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】ローテ用だけ**。
正式コード commit は **`475a6c2`（`fix: 渋谷新館ローテ画像とジャグラー入力範囲を修正`・
`streamlit_app.py` のみ・+34 / −21）**。直前の `a011c33`（生成物・北斗統合・カバネリ・
月間ジャグラー）の節は削除・書き換えしない。

### ① 週間オススメの ローテ画像は機種ごとに1枚

**「結果テキストの統合単位」と「ローテ画像の生成単位」を明確に分離する。**

| 対象 | 単位 |
|---|---|
| **結果テキスト** | **統合1本 `北斗転生2結果.txt`**（`a011c33` の仕様を維持） |
| **ローテ画像** | **機種ごとに1枚**（`スマスロ北斗の拳ローテ.png` / `北斗転生2ローテ.png`） |

- 画像の対象機種は **6機種入力欄（`machine_inputs2` → `machine_inputs1`）** の順で
  `_wk_img_macs` へ**機種名で重複除去**して積む。1機種だけ設定でも動く。
- `_cat_inputs` / `_cat_names` を渋谷新館だけ
  `[[1機種], …] + [machine_inputs3, machine_inputs4]` へ組み替え、
  `_n_cat = len(_cat_inputs)`（他店舗は 3）で `None` 埋めする。
- **結果テキスト用の `_r_macs` は従来どおり**（`_r1_mac` は `set1[0]`＝`北斗転生2`）。
  画像名だけ **`_img_macs`** を別に持つ。
  **`_r_macs` を機種別へ変えてはならない**（統合テキストが `スマスロ北斗の拳結果.txt` へ改名される）。
- **`スマスロ北斗の拳表.png` / `スマスロ北斗の拳結果.txt` を復活させない**
  （`_wt_save_list = (2, 3, 4)`・stale 削除は完全一致のみ）。
- `_maru = _ROTE_MARU[_ci_i] if _ci_i < len(_ROTE_MARU) else str(_ci_i + 1)` の
  index ガードを外さない。

### ② 月間オススメ表③ ジャグラーの分数選択肢を 分母1〜10 へ

```python
_T3_SPECIAL_OPTS = [f"対象台が{_n}/{_d}でプラス差枚"
                    for _d in range(10, 0, -1) for _n in range(_d, 0, -1)]   # 55件
```

- **案A（選択肢の拡張）を採用**。自由入力（案B）は不採用
  （表記ゆれ・バリデーションが増える／変更行数も多い）。
- 表記は**そのまま保存・復元・描画**する（`9/10` を `90%` や `9台` へ変換しない）。
- **既存の 1/1〜5/5 はすべて選択肢に残る**ので保存値が空欄へ戻らない。
- 対象項目は `_T3_SPECIAL_ITEM_KEYS = ("バーベルとらっぴ", "椅子に座るピエロ")` のみ・
  `max_selections=1` も不変。t3 は渋谷新館専用なので他店舗へ影響しない。
- 順序は **分母降順→分子降順**（`10/10` が先頭・`1/1` が末尾）。

### ③ t3 保存の存在ガード（データ欠落の再発防止）

`_on_ms_save()` は表示中の窓を丸ごと書き戻すため、**widget キーが GC された列の値が
黙って消える**事故が起きた（`cell_date_machines["2026-09-05"]["1"]` の消失）。

```python
_sel = (st.session_state.get(_msk2, [])
        if _msk2 in st.session_state
        else _cm_dict3.get(f"{_ci2},{_cj2}", []))
```

**キーあり→現在値／キーなし→既存値維持**（⑤ `55e7752` と同思想）。
**この存在ガードを外さない。**
消失した 9/5 の値は**アプリUI上で再選択して復旧**した（**JSON の直接編集はしない**）。

### ④ 確認結果

- 純粋テスト **36 PASS / 0 FAIL**（選択肢55件・`9/10` 描画・legacy 値の復元可否・
  `_wk_img_macs` / `_n_cat` / `_img_macs` 構造・t1 表画像の非生成・stale 削除・存在ガード）
- 実機：合成 `20260906_渋谷新館_20S.xlsx` で🎰を実行し
  **`スマスロ北斗の拳ローテ.png`（460×608）と `北斗転生2ローテ.png`（460×608）が同寸＝機種別**、
  `カバネリ海門決戦ローテ.png` / `東京喰種ローテ.png` / `ジャグラー系表.png` も従来どおり、
  **`北斗転生2結果.txt` は統合1本**、`スマスロ北斗の拳表.png` / `スマスロ北斗の拳結果.txt` は**0件**
- UIで `対象台が9/10でプラス差枚` が選択肢に出ることを確認（**保存はしていない**）

### ⑤ 今後の禁止事項

1. **週間ローテ画像を再び1枚へまとめない**
2. **`_r_macs` を機種別へ変えない**（統合テキストのファイル名が壊れる）
3. **`スマスロ北斗の拳表.png` / `スマスロ北斗の拳結果.txt` を復活させない**
4. **`_wt_save_list` に 1 を戻さない**
5. **分数の選択肢を 1/1〜5/5 へ戻さない／自由入力へ変えない／`n>d` を許可しない**
6. **分数表記を `%` や `台` へ変換しない**
7. **`_on_ms_save()` の存在ガードを外さない**
8. **`weekly_items.json` を直接編集して値を復旧しない**
9. **月間表記・`cell_date_machines` の日付キー優先仕様を巻き戻さない**
10. **他店舗・他ページへ波及させない／無関係なリファクタをしない**

## 渋谷新館 記事用：⑥「全台データ」画像（2026-09-08）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用⑥だけ**。
正式コード commit は本節と**同一の実装 commit**
（`feat: 渋谷新館記事に全台データ画像を追加`・2026-09-08・
**`streamlit_app.py` と `wp_client.py` の2ファイルのみ**・129 insertions / 2 deletions）。
既存節は削除・圧縮・統合・並べ替えしない。

### ① 追加したもの

差枚数ランキングの直後に、その日の全台集計（勝率／総差枚／平均差枚）をまとめた
**小型サマリー画像 `全台データ.jpg`** を自動生成する。

```
差枚数ランキング
  ↓
全台データ      ← 平均差枚 +50枚以上のときだけ
  ↓
島図
```

### ② 店舗gate（渋谷新館のみ）

```python
_ART_ZENDAI_STORES  = frozenset({"渋谷新館"})
_ART_ZENDAI_FN      = "全台データ.jpg"
_ART_ZENDAI_TITLE   = "全台データ"
_ART_ZENDAI_MIN_AVG = 50
```

**高田馬場・秋葉原・新小岩・通常結果ポスト用・スランプ付き・ローテ用へは追加しない。**

### ③ ★集計は既存 `_stat_from_diff()` の再利用（二重実装しない）

新設ヘルパー **`_art_zendai_stat(diff_raw)`** は
**既存 `_stat_from_diff()` をそのまま呼ぶだけ**である。

| 指標 | 定義（既存のまま） |
|---|---|
| 母集団 | **その日の取得データの全台**（`len(diff_raw)`＝渋谷新館は433台） |
| 勝率 | **差枚 > 0 の台数 / 全台数**（±0枚は勝ち扱いしない） |
| 総差枚 | 全台の差枚合計 |
| 平均差枚 | **`int(round(mean))`** |

**この定義は記事用⓪の「総差枚サマリー」（`_art_meta_v`）の式と完全に同一**
（`total` / `plus`=差枚>0 / `total_diff`=sum / `avg_diff`=int(round(sum/total))）。
**勝率・平均の定義を新しく決め直さない。0枚を勝ち扱いへ変えない。**

### ④ ★入力は「差枚数ランキングと同じ補正後データ」

母集団の式は⓪サマリーと同一だが、**入力する差枚は
パイプラインの `_pipeline_calc_d` 適用後**（⑦=`_apdi` / ⑧=`result["diff_raw"]`）とする。
＝**差枚数ランキングとまったく同じデータ源**。

- **`_pipeline_calc_d` を再適用しない（二重適用の禁止）。**
- 理由：同じH2の中でランキングの直後に並ぶため、生差枚を使うと
  **記事内でランキングの数値と全台データの数値が食い違う**（実測 2026/9/5 は
  生 +76,400／平均+176 に対し補正後 +82,950／平均+192）。
  末尾画像の `48b1635`（画像と結果テキストを補正後で統一）と同じ考え方。
- **勝率は補正で符号が変わらないため生・補正後で同一**
  （2026/9/5 はどちらも 46.2% (200/433台)）。

### ⑤ 生成条件（丸め後の表示値で判定）

**`avg_diff >= 50` のときだけ生成する。**

| 平均差枚 | 挙動 |
|---|---|
| +51枚以上 | **生成** |
| **+50枚（ちょうど）** | **生成** |
| +49枚以下・0枚・マイナス | **生成しない** |

**判定に使うのは `_stat_from_diff()` の `avg_diff`＝`int(round(mean))`＝
画面・画像に表示されるのと同じ値**である。
内部平均 49.6 は表示 **+50枚** になるので**生成する**（表示と判定をズラさない）。
**`raw値 >= 50` のような別判定を作らない。**

### ⑥ データ欠損時

`diff_raw` が `None` / 空 / 全欠損なら **`None` を返して生成しない**。
**欠損を0として集計しない。**WordPress 処理全体をこの補助画像1枚で落とさない
（`_art_zendai_image()` が `None` を返すだけで、後続は従来どおり進む）。

### ⑦ 画像仕様

| 項目 | 値 |
|---|---|
| ファイル名 | **`全台データ.jpg`**（固定名。ランキング・島図と同じ流儀） |
| サイズ | 実測 **468 × 196 px**（内容に応じて幅が伸びる） |
| 描画 | **`_art_zendai_image()` 内で完結**。共通の `draw_table_image()` は変更しない |
| フォント | 既存 **`load_font()`**（タイトル30 / 項目28 / 数値32） |
| 書式 | 既存 **`fmt_diff()`**（`+82,950枚` / `-12,300枚` / `±0枚`） |
| 保存 | 既存 **`_save_jpeg()` の既定 250KB**（小型のため専用値を作らない） |

表示内容（3行固定）:

```
全台データ                       ← 紫のタイトルバー・白文字
勝率     44.8% (194/433台)
総差枚   +27,500枚
平均     +64枚
```

配色は専用定数 `_ART_ZENDAI_TITLE_BG` / `_BODY_BG` / `_LABEL_FG` / `_VALUE_FG` /
`_BORDER` を持つ。**既存の `C_*` / `_ART_RANK_*` は変更しない。**

### ⑧ HQは対象外（既存gateを増やさない・統合しない）

小型画像なので **HQ倍率は既定 1.0**、保存も既定 250KB。

**`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` /
`_ART_RANK_HQ_STORES` のいずれへも追加しない。統合もしない。**
**全台データ専用のHQ gate（`_ART_ZENDAI_HQ_*`）も作らない。**

### ⑨ ⑦プレビューと⑧本番は同じ生成コア

**呼び出しは2か所だけ**で、どちらも同じ `_art_zendai_image()`：

| 経路 | 入力 |
|---|---|
| ⑦プレビュー | `_art_zendai_image(_apdi)` |
| ⑧本番 | `_art_zendai_image(result.get("diff_raw"))` |

**プレビュー専用の別計算を作らない。**同じ日付・同じ取得データなら
勝率・総差枚・平均差枚が一致する。
⑦は `_art_pil` へ **ランキングの後・島図の前**に append する。
`None` のときは append しないので**空枠・壊れた画像枠は残らない**。

**ban_map（`_pv_bm_sl` / `_art_bm_sl`）へは登録しない**
→ ランキング・島図と同じくスランプ／パネル／液晶の合成ループを素通りする。

### ⑩ stale対策（完全一致のみ・glob禁止）

`output_dir` は営業日ごとに再利用されるため、**⑧で生成しない日は
既存の共通ヘルパー `_rm_stale_image(output_dir, _ART_ZENDAI_FN, _log)` を呼ぶ。**

- 削除は**連番除去後の完全一致のみ**（`全台データ.jpg` / `NN_全台データ.jpg` /
  `全台データ_side.jpg`）。
- **glob による広範囲削除・部分一致・フォルダ全削除は禁止。**
  実テストで `差枚数ランキング.jpg` / `島図.jpg` / `東京喰種_高配分.jpg` /
  `その他の優秀台ピックアップ.jpg` / `01_全台データ_別物.jpg` が**残る**ことを確認済み。
- これにより「前日+100枚→生成 / 翌日+20枚→非生成」でも、
  前日の画像が**プレビュー・ZIP・WordPress upload・本文**へ入らない。
  WordPress 側は `_existing_files()` の実在判定で自動的に追従する。

### ⑪ WordPress（H2は増やさない）

`payload["zendai_data"]` を新設（渋谷新館のみ `[_ART_ZENDAI_FN]`、他店舗は渡さない）。
`wp_client.plan_blocks()` で**変更したのは「差枚数ランキング&島図」ブロックの1か所だけ**。

```
H2 差枚数ランキング&島図        ← 既存H2を維持。新しいH2を作らない
   差枚数ランキング画像
   全台データ画像               ← 条件成立時のみ
   空段落 × 5
   島図画像
```

- **空段落の位置と個数は従来どおり「島図の直前に5個」**（`RANK_SHIMAZU_GAP_PARAS = 5`）。
  **ランキング→全台データの間には空段落を入れない（0個）。**
  条件未達の日は従来どおり ランキング→空段落5個→島図。
- 条件未達なら**画像自体が無い**ので `_existing_files()` が空になり、
  **media upload も本文掲載も発生しない**（「生成しているがWPだけ非表示」にしない）。
- **既存の渋谷新館WordPress仕様はすべて維持**：
  fullwidth（`"width":"100%"` / `wp-block-image size-full is-resized` /
  `style="width:100%;height:auto"`）／ one-piece（1画像=1media=1block）／
  nosplit（`_ART_WP_NOSPLIT_STORES`）／ Luminous（`linkDestination":"none"`・`<a>`なし）／
  Gutenberg validation。**新画像だけ別HTML形式にしない。**
- **高田馬場は `zendai_data` キーを渡さない**ので plan・本文HTMLが従来と完全一致
  （`H2_SHIMAZU`「シマズをチェック！」も維持）。

### ⑫ 変更していないもの

`_stat_from_diff` ／ `_pipeline_calc_d` ／ `_art_ranking_image` ／ `_art_ranking_limit` ／
`_rm_stale_image` ／ `_save_jpeg` ／ `draw_table_image` ／ `_build_machine_img` 系 ／
`_build_sue_images` ／ `_art_osusume_block_images` ／ `run_auto_pipeline` ／
`run_step1_main` ／ `run_step2_juggler` ／ `run_step3_other` ／ `_kojin_yushu_filter` ／
`filter_recommended_machines` ／ `generate_report_text` ／ `show_auto_page` ／
`show_rote_page` ／ 記事用②⑤ ／ 全台系 ／ 高配分 ／ 末尾 ／ 並び・列 ／ ジャグラー ／
その他優秀台 ／ 島図（`_ART_SHIMAZU_TARGET_KB = 3000`）／ 投稿者選択 ／
`shimazu_renderer.py` ／ `convert_narabi_pil.py`。

**新規関数は `_art_zendai_stat` / `_art_zendai_image` の2つだけ・消失関数0。
`wp_client.py` で本体が変わったのは `plan_blocks` のみ。**

### ⑬ 確認結果（2026-09-08）

**純粋テスト 66 PASS / 0 FAIL。**
集計（母集団433台・勝率・総差枚・平均・符号・カンマ）／
境界値（+49非生成 / +50生成 / +51生成 / 0 / -100 / **内部49.6→表示+50→生成** /
48.8→表示+49→非生成 / None / 空 / 全NaN）／
画像（3行の書式・文字切れなし・極端な桁数）／
プレビュー順・WP順・空段落個数・upload条件・H2維持・fullwidth・one-piece・
Luminous・Gutenberg validation・stale（完全一致削除・無関係画像は残る）／
**既存関数のバイト一致・高田馬場の plan と本文HTMLの完全一致**。

**ローカル実機（⑦プレビュー・渋谷新館 2026/9/7・確定433台）**

```
差枚数ランキング.jpg → 全台データ.jpg → 島図.jpg   ← 順序どおり
全台データ.jpg : 勝率 44.8% (194/433台) / 総差枚 +27,500枚 / 平均 +64枚
```

純粋テストが同一データで算出した値と一致。空枠・壊れた枠なし。

### ⑭ 確認状況の正確な記録（誤記しないこと）

- **「平均+50枚未満で生成しない」ケースの実機確認は未実施。**
  取得できた渋谷新館の確定データ 9/5・9/6・9/7 は補正後平均が
  **+192 / +119 / +64枚** ですべて条件成立だったため、実データで未達の日が無かった。
  **純粋テストでは境界値・欠損すべてPASS済み。**「実機確認済み」と書かない。
- **⑧本番は実行していない。**`_git_auto_push()` が
  `article_page_inputs.json` 等を自動commitするため意図的に⑦までとした
  （既存の記事用実装と同じ判断）。
- **WordPress 通信は0件**（POST / PUT / PATCH / DELETE / media upload / draft作成なし）。
  検証はローカルのモックと純粋テストのみ。**Cloud Reboot も未実施。**

### ⑮ 今後の禁止事項

1. **勝率・総差枚・平均差枚を別ロジックで再実装しない**（`_stat_from_diff()` を使う）
2. **母集団を「20スロのみ」「稼働台のみ」等へ勝手に変えない**（全台＝`len`）
3. **±0枚を勝ち扱いにしない**
4. **入力を生差枚へ戻さない／`_pipeline_calc_d` を再適用しない**
5. **判定を `raw値 >= 50` へ変えない**（表示値 `int(round(mean))` で判定する）
6. **+50枚ちょうどを非生成にしない**
7. **欠損を0として画像を作らない**
8. **⑦だけ／⑧だけ直さない**（同じ `_art_zendai_image()` を通す）
9. **ban_map へ登録しない**（スランプ・パネル・液晶を付けない）
10. **HQ gate 4種へ追加・統合しない／専用HQ定数を作らない**
11. **新しいH2を作らない**（`差枚数ランキング&島図` を維持）
12. **空段落の位置・個数（島図の直前に5個）を変えない**
13. **条件未達の日に「生成はするがWPだけ非表示」にしない**
14. **stale削除を glob・部分一致・フォルダ全削除にしない**
15. **fullwidth / one-piece / nosplit / Luminous / Gutenberg 仕様を新画像だけ別形式にしない**
16. **差枚数ランキング・島図そのもの（抽出・順位・デザイン・HQ・ファイル名・WP処理）を変更しない**
17. **他店舗・他ページへ展開しない**
18. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用：⑥「全台データ」画像の数値は結果テキストと共通処理（2026-09-08 追記）

**正式仕様。巻き戻し禁止。**直前の
「## 渋谷新館 記事用：⑥「全台データ」画像（2026-09-08）」の**追加修正**であり、
同節は削除・書き換えしない（③④の「`_stat_from_diff()` 再利用」「補正後差枚を使う」は
本節で**より厳しく**なる）。
正式コード commit は本節と**同一の commit**
（`fix: 全台データ画像の数値を結果テキストと共通処理へ一本化`・2026-09-08・
**`streamlit_app.py` の1ファイルのみ**・+60 −21）。
**`wp_client.py` / `shimazu_renderer.py` / `convert_narabi_pil.py` は diff 0。**

### ① 結果テキストの全台データ数値の生成箇所（調査結果）

**`generate_report_text()` 内のクロージャ `summary_section()`** が唯一の生成箇所。

```
📈{M/D}の結果📈
🏆総差枚：+27,500枚      ← total = 合計
🏆平均差枚：+64枚        ← avg   = int(round(total / 台数))
🌋万枚オーバーが…／💥+5,000枚…／💥+3,000枚…／💎…台が+1,000枚オーバー！
```

- **入力は `diff_raw` 引数**。記事用⑧は **`diff_raw=result.get("diff_raw")`**、
  つまり `run_auto_pipeline()` 内で **`df["差枚"] = df["差枚"].apply(_pipeline_calc_d)` を
  適用した後**の値を渡している（＝いわゆる「盛った」補正後の差枚）。
- 母集団は `diff_raw.dropna()` の全件（渋谷新館は433台）。
- **`summary_section()` は店舗で分岐しない**（全店舗共通で出力される）。
- **`STORE_RESULT_TRANSFORMS["渋谷新館"]` は存在しない**（赤坂見附のみ登録）ので、
  結果テキストの数値は**後段の文字置換でも変化しない**。
- **★結果テキストに「勝率」は出力されていない**（`🏆総差枚` と `🏆平均差枚` の2項目だけ）。

### ② どの数値にどの補正が入っているか（実測）

| 日付 | 生データ 総差枚/平均 | **結果テキスト（補正後）総差枚/平均** | 勝率 |
|---|---|---|---|
| 2026/9/5 | +76,400 / +176 | **+82,950 / +192** | 46.2% (200/433台) |
| 2026/9/6 | +43,500 / +100 | **+51,400 / +119** | 43.2% (187/433台) |
| 2026/9/7 | +20,300 / **+47** | **+27,500 / +64** | 44.8% (194/433台) |

- 補正は **`_pipeline_calc_d()`**（範囲別加算 → 50の倍数へ丸め → 上限19,000）。
  **総差枚・平均差枚の両方にこの補正が乗る。**
- **勝率には補正が入らない。** `_pipeline_calc_d` は符号を反転しないため
  「差枚 > 0 の台数」が生・補正後で同一になる（実測3日とも一致）。
- **`_pipeline_calc_d` を再適用しない（二重適用の禁止）。**

### ③ ★正式な単一実装（二重計算の禁止）

**`_zendai_diff_list()` / `_zendai_total_stat()` を新設**し、
**結果テキストと⑥画像がこの2関数だけを通る**構造にした。

```python
def _zendai_diff_list(diff_raw) -> list[int]      # 欠損を落として int 化
def _zendai_total_stat(diff_raw) -> dict | None   # _stat_from_diff() を返す
```

| 呼び出し元 | 使い方 |
|---|---|
| **結果テキスト `summary_section()`** | `total = _zst["total_diff"]` / `avg = _zst["avg_diff"]` |
| **⑥画像 `_art_zendai_stat()`** | `return _zendai_total_stat(diff_raw)`（**委譲のみ**） |

- **`summary_section()` から `sum(diffs)` / `int(round(total / len(diffs)))` を削除**した。
  **呼び出し側で `sum()` / `mean()` を書かない。**
- `_art_zendai_stat()` は**自前の集計を一切持たない**
  （旧実装の `pd.to_numeric(...)` + `_stat_from_diff()` を削除して委譲へ変更）。
- 画像描画関数 `_art_zendai_image()` にも `sum()` / `mean()` は無い。
- **`_stat_from_diff()` 本体は変更していない**（他の全画像が使用中）。
- `diffs`（🌋/💥/💎 のカウント用リスト）も `_zendai_diff_list()` から取る。
- 結果テキストの**出力は旧実装とバイト一致**（3日分 × 渋谷新館／
  新小岩・高田馬場・秋葉原・西武新宿・上野本館・赤坂見附で完全一致）。

### ④ 画像が参照する最終値

⑥画像の 総差枚／平均差枚 は **`_zendai_total_stat()` の戻り値そのもの**＝
**結果テキストの `🏆総差枚` / `🏆平均差枚` と必ず同値**。

| 画像の行 | 値の出どころ |
|---|---|
| `勝率 44.8% (194/433台)` | `win_count` / `total_count`（**結果テキストに項目が無いため画像だけが持つ**） |
| `総差枚 +27,500枚` | **結果テキストの 🏆総差枚 と同値** |
| `平均 +64枚` | **結果テキストの 🏆平均差枚 と同値** |

**勝率は結果テキストに存在しないため「一致」ではなく「同じ母集団・同じ補正後差枚から算出」
とする。**（`_zendai_total_stat()` が返す `win_count` / `total_count` は結果テキストの
総差枚・平均と**同じ `diff_raw`・同じ全台数**から出るので数値の食い違いは起きない。）
**★結果テキストへ勝率を新規追加してはならない**（既存の結果テキスト出力が変わる）。

### ⑤ +50判定は「結果テキストへ出力される補正後の平均差枚」

生成条件 `avg_diff >= _ART_ZENDAI_MIN_AVG(50)` の `avg_diff` は
**`_zendai_total_stat()["avg_diff"]`＝結果テキストの `🏆平均差枚` と同じ値**である。

**生データの平均で判定しない。**

| ケース | 挙動 |
|---|---|
| 生平均 +47枚 / **結果テキスト平均 +64枚** | **生成する**（2026/9/7 の実データがこれ） |
| 生平均 +48枚 / 結果テキスト平均 +67枚 | **生成する**（純粋テストで確認） |
| 結果テキスト平均 **+50枚ちょうど** | **生成する** |
| 結果テキスト平均 +49枚 | **生成しない** |

**「生平均 >= 50 だが補正後平均 < 50」は補正の性質上発生しない**
（`_pipeline_calc_d` はプラス台を増額するため補正後平均が生平均を下回らない。
探索400通りで該当0件）。**この非対称性を理由に判定を生データへ戻してはならない。**

### ⑥ 確認結果（2026-09-08）

**純粋テスト：`test_match.py` 48 PASS / 0 FAIL ／ `test_zendai.py` 67 PASS / 0 FAIL。**

- 実データ3日分（9/5・9/6・9/7）で **結果テキストの 🏆総差枚／🏆平均差枚 と
  画像の 総差枚／平均 が完全一致**
- **勝率は結果テキストに項目が無い**ことを機械確認（`"勝率" not in txt`）／
  勝率の母集団が結果テキストと同じ433台であることを確認
- 構造テスト：`summary_section` が `_zendai_total_stat` を参照・`sum()`/`mean()` が無い／
  `_art_zendai_stat` は委譲のみ／`_zendai_total_stat` の定義は1つ
- 境界跨ぎ：A 生<50・補正後>=50→生成 ／ B 生>=50・補正後<50は発生しない ／
  C 補正後+50→生成 ／ D 補正後+49→生成しない
- **非回帰：結果テキストが旧実装とバイト一致**（渋谷新館3日＋他6店舗）／
  `diff_raw=None` / 空でも `summary_section` が空を返す挙動も同じ／
  変更関数は `generate_report_text`（内部 `summary_section`）と `_art_zendai_stat` の2つだけ／
  新規は `_zendai_diff_list` / `_zendai_total_stat` の2つだけ・消失0／
  `_stat_from_diff` / `_pipeline_calc_d` / `_art_ranking_image` / `_art_zendai_image` /
  `run_auto_pipeline` / `run_step1〜3` / `show_auto_page` / `show_rote_page` /
  `_build_kabupa_result_text` ほかバイト一致

**ローカル実機（⑦プレビュー・渋谷新館 2026/9/7・確定433台）**

```
差枚数ランキング.jpg → 全台データ.jpg → 島図.jpg
全台データ.jpg : 勝率 44.8% (194/433台) / 総差枚 +27,500枚 / 平均 +64枚
```

**リファクタ前と同一の値**で、結果テキストの `🏆総差枚：+27,500枚` /
`🏆平均差枚：+64枚` と一致。

### ⑦ HEAD版との比較時の注意（再発防止）

**HEAD版 `streamlit_app.py` を一時ディレクトリへ置いて実行してはならない。**
`BASE_DIR = os.path.dirname(os.path.abspath(__file__))` がずれて
`weekly_items.json` / `機種名変換.xlsx` / `store_settings` を読めず、
**`shibuyashinkan_poster_section()` の 📌 行だけが消えて「結果テキストが変わった」と
誤検知する**（今回この誤検知が実際に出た）。
**必ずプロジェクトと同一ディレクトリへ置いて比較し、比較後にその一時コピーを削除する。**
（CLAUDE.md の `1301431` 節にある同趣旨の注意と同じ。）

### ⑧ 今後の禁止事項

1. **画像側で `df["差枚"].sum()` / `.mean()` を書かない**（`_zendai_total_stat()` を使う）
2. **`summary_section()` へ `sum()` / `mean()` を戻さない**
3. **`_zendai_total_stat()` の定義を2つに増やさない／画像用と結果テキスト用に分けない**
4. **`_art_zendai_stat()` に独自集計を戻さない**（委譲のみ）
5. **入力を生差枚へ戻さない／`_pipeline_calc_d` を再適用しない**
6. **+50判定を生データの平均へ戻さない**（結果テキストの補正後平均が正）
7. **結果テキストへ勝率を追加しない**（既存出力が変わる）
8. **`_stat_from_diff()` 本体を変更しない**（全画像が使用中）
9. **結果テキストの 🌋/💥/💎 のカウント条件・文言・並びを変更しない**
10. **他店舗の結果テキストを変えない**（`summary_section` は全店舗共通）
11. **HEAD版を別ディレクトリへ置いて実データ比較しない**
12. **⑥画像のファイル名・生成条件・プレビュー順・WP順・H2・空段落・stale対策・
    fullwidth / one-piece / nosplit / Luminous / Gutenberg 仕様を変更しない**
13. **無関係なリファクタ・未使用コード整理をしない**
## 渋谷新館 記事用：⑤パネル上位2枚・⑤液晶・WordPress構成の見直し（2026-09-08）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用ページと、そのWordPress本文だけ**。
正式コード commit は本節と**同一の実装 commit**
（`fix: 渋谷新館記事のオススメ画像とWordPress構成を修正`・2026-09-08・
**`streamlit_app.py` と `wp_client.py` の2ファイルのみ**・+87／−21）。
既存節は削除・圧縮・統合・並べ替えしない。

### ⓪ 9/6実データの実測（原因の確定）

| 項目 | 実測 |
|---|---|
| ⑤B5 設定 | マイジャグV / ネオアイム / ファンキー2 / ゴージャグ3 / ハピジャグV / ジャグラーガールズ / ミスジャグ / ウルトラミラジャグ（8機種・抽出条件 +1,000枚以上） |
| 除外後の最終掲載 | **ファンキー2 / ゴージャグ3 / ジャグラーガールズ の3機種・10台** |
| 抽出台数・最大差枚 | ファンキー2 2台 +3,500 ／ ゴージャグ3 6台 +2,700 ／ ジャグラーガールズ 2台 +2,100 |
| パネル登録 | **3機種すべて panel=True**（`funkyjug_panel.png` / `gojug_panel.png` / `jugglergirls_panel.png`） |
| 実際に描画されたパネル | **3枚**（欠落ではない） |
| スランプ | 10台・3列・4行・**最終行1台＝空き2マス**・`_gap_fillable(10,3)=True` |

### ① ★パネル「欠損」の正体（パネル画像の欠落ではない）

`_build_variety_panel_grid()` は **2列固定**（`_cell_w = width // 2`）なので、
3枚だと `[1][2] / [3][白]` になり **最下行の右半分が白**になる。
実測で「最下行右半分の白ピクセル 50/50」＝**空セル**であり、
**パネルファイル・機種名照合・machine_image_master には問題がなかった。**
**「画像がなかった」で片付けない。**

### ② ⑤のパネルは最大2機種（3機種以上でも上位2枚）

```python
_ART_OSU_PANEL2_STORES: "frozenset[str]" = frozenset({"渋谷新館"})
```

`_art_panel_max()` に分岐を1つ追加し、対象店舗の⑤
（`_art_is_osusume_fn(bare_fn)`）は **2** を返す。

| 最終掲載機種数 | ⑤のパネル |
|---|---|
| 1機種 | **1枚（全幅）**＝`_art_osusume_panel_fn()` の単一機種経路（`b039deb` の仕様を維持） |
| 2機種 | 2枚（1行2列・従来と同じ） |
| **3機種以上** | **上位2枚だけ（1行2列）→ 空セルが出ない** |

- **上位判定は既存基準のまま**＝`_build_variety_panel_grid()` の
  **「機種ごとの最高差枚が大きい順」**。パネル未登録機種の繰り上げも既存どおり。
  表示順は `order_by_min_ban=True`＝掲載台の最小台番昇順。
  **新しい順位基準を作らない。**
- **`_build_variety_panel_grid()` / `_build_panel_row()` / `_narabi_panel_names()` /
  `_apply_panel_to_table_img()` の本体は変更しない**（既存 `max_panels` を使うだけ）。
- **表・スランプ・掲載台・抽出条件は減らさない。**減るのは上部のパネル枚数だけ
  （ジャグラーガールズは表とスランプに従来どおり掲載される）。
- **★`_ART_JUG_PANEL2_STORES`（ジャグラー統合画像用）とは別仕様。統合しない。**
  高田馬場の⑤は対象外で従来どおり最大4枚。

### ③ ⑤ブロック画像にも液晶をはめ込む

**⑤の液晶除外は「バグ」ではなく明示的な専用例外だった**
（⑦: `if _is_osu_pv2: _gap_img_pv2 = None` ／ ⑧: `if _is_osu_sl: _gap_img_sl = None`）。
今回この2つの分岐を撤去し、⑤も既存の液晶経路へ乗せる。

- **⑤専用の液晶処理は作らない。**既存
  `_gap_screen_paths_for_bans()` / `_gap_sel_key()` / `_gap_fillable()` /
  `_resolve_gap_screen()` / `_attach_slump_to_table()` を**そのまま再利用**する。
- 条件は既存のまま **「3列で並べた最終行の空きが2マス以上」**（`_gap_fillable(n, 3)`）。
  1マスしか空いていない画像へ無理に入れない。
- ⑦の液晶セレクタ（`🖼️ 液晶画像を選ぶ（機種名）`）・`_art_gap_meta_{store}` /
  `_art_gap_base_{store}` への登録も他画像と同じ形で行う（選び直しで再合成される）。

**★液晶選択キーは拡張不要だった。**
`_gap_sel_key(store, bans, machine)` は元から**掲載台番集合単位**（`md5(store|machine|台番)`）で、
⑤ブロックの台番集合は他画像と重複しないため**誤共有は起きない**。
複数機種の代表機種は既存 `_featured_machine_for_bans()`（差枚最大の台の機種）が決める。
**既存キー仕様を変更していない**（機種名単位へ戻さない・ファイル名や `_side` を含めない）。

**★「gap-fill」と「液晶」を別物として扱わない。**
このコードベースの `_GAP_FILL_STORES` / `_ARTICLE_GAP_FILL_STORES` は
**液晶はめ込みの gate そのもの**で、別素材で埋める機能は存在しない。
今回**液晶だけで要件を満たしたので gap-fill 仕様の拡張はしていない。**

### ④ WordPress: 独立ジャグラーセクションを廃止（渋谷新館のみ）

```python
_ART_WP_NO_JUG_SECTION_STORES = frozenset({"渋谷新館"})   # streamlit_app.py
```

`payload["juggler_section"] = False` を渡した店舗では `plan_blocks()` が
H2 **「ジャグからも高配分機種多数！」の塊を丸ごと出さない**。

- **統合画像 `ジャグラーシリーズ優秀台.jpg` は本文へ載せず upload もしない。**
- **★stale対策**：`jug_comb` の**実ファイル存在チェック自体を行わない**
  （`jug_comb = os.path.isfile(...) if (out_dir and _jug_section) else False`）。
  出力フォルダに古い統合画像が残っていても **plan / upload / 本文のどこにも入らない**
  （実測: 古い `ジャグラーシリーズ優秀台.jpg` を置いても plan・collect_files・H2 すべて0件）。
- **キーを持たない店舗（高田馬場・秋葉原）は `payload.get("juggler_section", True)` で
  従来どおり True 扱い**＝1ブロックも変わらない（本文HTMLバイト一致を確認）。
- **⑤にジャグラーがある日だけ削除する、という日別条件にはしない。**
  渋谷新館では**セクション自体を恒久的に廃止**する。

### ⑤ ジャグラー個別高配分は通常「高配分機種」へ統合

`build_payload()` へ **`juggler_series=set()`** を渡すことで
`high_ratio_list` を `high` / `juggler` へ分割させない。

- マイジャグV・ネオアイム・ハピジャグV 等の**個別高配分画像は捨てず**、
  通常「1/2系以上の高配分機種が大量」の中へ入る。
- 並び順は既存の **`all_avg_diff` 降順**のまま。**ジャグラーだけ末尾固定などの
  独自順序を作らない**（実測: とんスキ→真打吉宗→…→ハピジャグV→…→マイジャグV→…と混在）。
- 実測: `len(新high) == len(旧high) + len(旧juggler)`＝**欠落0**。同一画像の重複0。
- **`run_step2_juggler()` / `osusume_bans` / `_jug_pool_osu` / `high_ratio_list` の
  生成側は一切変更しない。**

### ⑥ ★自動ジャグラー優秀台のスキップは既存仕様（逆戻り禁止）

調査結果（Git履歴・現在コードで確定）:

| commit | 内容 |
|---|---|
| **`d477a91`** | `osusume_bans` / `_jug_pool_osu` を導入し、⑤オススメ掲載台をジャグラー統合プールから**台番単位**で除外 |
| **`88547a3`** | `plan_blocks()` の `FN_JUGGLER` を **無条件 append → `if jug_comb:`（実ファイル存在時のみ）** へ変更 |
| `f11883e3` | `_ART_OSU_F_OPTS` の定義位置修正（ジャグラーとは無関係） |

**正確な現仕様は「渋谷新館だから無条件スキップ」ではなく
「統合プールが⑤オススメ掲載台のみになったらスキップ」というデータ駆動の条件付きスキップ**である
（渋谷新館専用の無条件 gate は存在しない）。
実測ログ: **9/5・9/6・9/7 の3日とも
`ジャグラーシリーズ優秀台: ⑤オススメ掲載台のみのため画像なし` → 生成なし。**
⑤に `juggler_series` 9機種のうち8機種が設定済みのため**運用上は毎日スキップ**される。

**この既存挙動を維持する。今回の WordPress 変更で逆戻りさせない。**

### ⑦ WordPress本文の後半順序（正式）

```
… 末尾 → 並び・列仕掛けも！ →（バラエティ）→ オススメ機種の優秀台
  → その他単品優秀台も多数 → 差枚数ランキング&島図 → 店舗情報ボタン
```

**変更前**は `… 並び・列 →（バラエティ）→ ジャグラー → その他単品 → ⑤オススメ → ランキング&島図`。
**⑤オススメを「その他単品」より前へ移した**（`plan_blocks()` 内でブロックの順序を入れ替えただけ）。
**⑤より前へ戻さない。**

`差枚数ランキング&島図` の内部順は**直前の正式仕様を維持**:

```
差枚数ランキング → 全台データ（補正後平均+50枚以上のみ）→ 島図
```

未達日は従来どおり `差枚数ランキング → 島図`（実測で両方確認）。
`H2_RANK_SHIMAZU` は増やさない・空段落は島図の直前に5個のまま。

### ⑧ `その他の優秀台ピックアップ.jpg` の画質（この画像だけ分割を許可）

**原因は生成側ではない。**実測（9/6）:

| | 元サイズ | KB | 縦横比 | WP保存幅 | 752px表示 |
|---|---|---|---|---|---|
| **その他の優秀台ピックアップ** | **2160×8726** | **5,662** | **4.04** | **634px** | **1.19倍“拡大”** |
| 東京喰種_高配分 | 1986×6056 | 3,801 | 3.05 | 840px | 0.90倍縮小 |
| オススメ優秀台_ブロック5 | 1983×4911 | 3,206 | 2.48 | 1034px | 0.73倍縮小 |
| 差枚数ランキング | 2181×4638 | 2,785 | 2.13 | 1204px | 0.62倍縮小 |
| 島図 | 3451×6490 | 3,025 | 1.88 | 1361px | 0.55倍縮小 |

生成側は既に **HQ 2.0倍・q95・4:4:4・5.6MB** で最高品質。
**縦横比が最大のため WordPress の長辺2560px縮小で保存幅が634pxまで落ち、
fullwidth（本文内幅752px）で“拡大”される唯一の画像**だった。

```python
_ART_WP_SPLIT_ALLOW_FILES: "frozenset[str]" = frozenset({FN_SONOTA})   # wp_client.py
```

`plan_split()` の nosplit 早期returnをやめ、**nosplit店舗でも
`_ART_WP_SPLIT_ALLOW_FILES` のファイルだけ既存 `split_image_for_wp()` を通す。**

- 実測: **4分割・各片 2160×2152〜2208 で長辺2560px未満 → WordPress に縮小されず
  保存幅2160pxを維持**（752px表示で2.87倍縮小＝他画像と同等以上に鮮明）。
- 分割片の合計高さ＝元の高さ（8726）で**アスペクト比維持・リサイズなし**。
- **代償**: この画像だけクリック拡大が分割片単位になる（了承済み）。
- **`needs_split()` / `split_count()` / `split_image_for_wp()` / `WP_MAX_SIDE=2560` の
  本体は変更しない。**
- **`WP_NOSPLIT_FILES = {"島図.jpg"}`（全店舗で島図を1枚絵に）とは別仕様。統合しない。**
- **島図・ランキング・全台データ・高配分・⑤オススメ・並び・列は分割されない**（nosplit維持）。
- 分割片も **fullwidth 3点セット**（`"width":"100%"` ／ `wp-block-image size-full is-resized` ／
  `style="width:100%;height:auto"`）と **`linkDestination":"none"`（Luminous）** を維持。
  **新しいリサイズ・アップスケール処理は作っていない。**
- **HQ gate 4種（`_ART_HQ_STORES` / `_ART_ZH_HQ_STORES` / `_ART_NARABI_HQ_STORES` /
  `_ART_RANK_HQ_STORES`）は変更・統合していない。**

### ⑨ 確認結果（2026-09-08）

**純粋テスト 61 PASS / 0 FAIL ＋ 順序テスト 全PASS。**
⑤3機種認識・パネル上限2・1行2列・空セルなし・上位判定＝最高差枚・
空き2マス判定・液晶取得・液晶でスランプと表を潰さない・1機種全幅維持・2機種維持・
4機種画像は最大4維持・B1〜B6非回帰・⑤dedupe/filter/②除外維持・
H2ジャグラー消滅・stale統合画像を拾わない・upload対象外・マイジャグV等が通常高配分へ・
欠落0・重複0・平均差枚降順・後半順序・ランキング内部順・全台データ未達時・
その他優秀台の分割と保存幅2160px・島図と他画像はnosplit維持・fullwidth/Luminous/
Gutenberg validation維持・**高田馬場の plan と本文HTMLが完全一致**・秋葉原WP対象外・
変更関数は `_art_panel_max` / `show_auto_article_page` / `plan_blocks` / `plan_split` の4つだけ・
新規/消失関数0・`shimazu_renderer.py` / `convert_narabi_pil.py` 無変更。

**ローカル実機（⑦プレビュー・渋谷新館 2026/9/6・確定433台）**

- ⑤ブロック5のパネルが **Funky JUGGLER ＋ GOGO JUGGLER の2枚横並び・空白セルなし**
- スランプ最終行の**2マス空きへ液晶がはめ込まれた**
- ⑦に **`🖼️ 液晶画像を選ぶ（ファンキー2）`** セレクタが表示された
- ⑤B1・B4、高配分・並び・その他の各画像も従来どおり生成

### ⑩ 確認状況の正確な記録（誤記しないこと）

- **⑧本番は実行していない。** `_git_auto_push()` がJSONを自動commitするため意図的に⑦まで。
  ⑧側の同一分岐はコードとして⑦と同じ helper を通す（`_is_osu_sl` の除外撤去を確認済み）。
- **WordPress 実送信0件**（POST / PUT / PATCH / DELETE / media upload / draft作成なし）。
  検証はローカルの `plan_blocks` / `collect_files` / `plan_split` / `build_content` と
  モックのみ。**Cloud Reboot も未実施。**
- **分割後の実WordPress上の見た目は未確認**（保存幅2160px維持は `plan_split` の実測値からの算出）。

### ⑪ 今後の禁止事項

1. **⑤のパネル「欠損」を「パネル画像が無い」と誤診しない**（2列グリッドの空セル）
2. **⑤のパネル上限を4へ戻さない**／`_ART_OSU_PANEL2_STORES` を他店舗へ広げない
3. **`_ART_OSU_PANEL2_STORES` と `_ART_JUG_PANEL2_STORES` を統合しない**
4. **上位判定に新しい順位基準（合計差枚・平均・入力順など）を作らない**
5. **`_build_variety_panel_grid()` / `_build_panel_row()` / `_apply_panel_to_table_img()` の
   本体を変更しない**
6. **パネルを減らすために表・スランプ・掲載台・抽出条件を減らさない**
7. **⑤の液晶除外（`if _is_osu…: _gap_img = None`）を復活させない**
8. **⑤専用の液晶処理を新設しない**／`_gap_sel_key()` を機種名単位へ戻さない・キーを拡張しない
9. **液晶条件「空き2マス以上」を変えない**／gap-fill仕様を不要に拡張しない
10. **渋谷新館へ独立ジャグラーセクションを復活させない**
11. **統合画像を「その他単品優秀台」等の別セクションへ移さない**
12. **`jug_comb` の実ファイル存在チェックを渋谷新館で復活させない**（staleが混入する）
13. **`payload.get("juggler_section", True)` の既定 True を変えない**（他店舗が壊れる）
14. **`run_step2_juggler` / `osusume_bans` / `_jug_pool_osu` / `high_ratio_list` を変更しない**
15. **ジャグラー高配分を末尾固定など独自順序にしない**
16. **⑤オススメを「その他単品」より後ろへ戻さない**／`H2_RANK_SHIMAZU` を増やさない
17. **`_ART_WP_SPLIT_ALLOW_FILES` へ他の画像を安易に追加しない**／`WP_NOSPLIT_FILES` と統合しない
18. **`needs_split` / `split_count` / `split_image_for_wp` / `WP_MAX_SIDE` を変更しない**
19. **HQ gate 4種を変更・統合しない**／新しいリサイズ・アップスケール処理を作らない
20. **`_zendai_total_stat()` の全台データ仕様を変更しない**（総差枚・平均は補正後・+50判定も補正後）
21. **高田馬場・秋葉原・新小岩・ローテ用・通常結果ポストへ波及させない**
22. **サイト設定・PHP・テーマ・SWELLのCSSを変更しない**
23. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事コメント自動生成 第1段階：候補生成・選択UI・日付別保存（2026-09-08・`31b9014`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用ページの📝記事コメントだけ**。
正式コード commit は **`31b9014`**（`feat: 渋谷新館の記事コメント候補生成と選択UIを追加`・
**`streamlit_app.py` の1ファイルのみ**・**+848 / −0**）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は無変更（diff 0）。**
既存節は削除・圧縮・統合・並べ替えしない。

### ① 第1段階の範囲（ここから先はまだやらない）

| | 状態 |
|---|---|
| facts層・候補生成・選択UI・日付別保存・⑦確認 | **実装済み（本節）** |
| **WordPress 本文への自動挿入** | **未実装**（第1段階では入れない） |
| **LLM / API による文章生成** | **使わない**（ルールベースのみ） |

⑦プレビュー・⑧本番のどちらを実行しても**コメントは WordPress 本文へ入らない**。
`build_payload()` / `plan_blocks()` / `build_content()` は**無変更**で、
純粋テストで**高田馬場・渋谷新館とも WordPress plan / 本文HTMLが HEAD とバイト一致**、
かつ**本文にコメント文字列が1文字も出現しない**ことを確認済み。

### ② 3層アーキテクチャ（層を混ぜない）

```
実データ（df / diff_raw / pipeline結果）
   ↓  facts層： _art_cmt_facts_*()      … 数値と機種名だけを持つ dict
   ↓  候補層： _art_cmt_cands_*()       … facts だけを見る純粋関数
最終文（人間が選択・編集）
```

- **候補生成関数は df を直接見ない。** facts に無い情報は文章へ入らないので、
  禁止事項（勝率・設定示唆・取材・イベント評価など）が**構造的に書けない**。
- **`random` は使わない。**同じ facts なら常に同じ候補文（決定論的）。
  純粋テストで再生成一致を確認済み。

### ③ ★facts に入れないもの（禁止事項を構造で担保する）

| 禁止 | 担保方法 |
|---|---|
| **勝率** | **どの facts にも勝率キーを持たせない**（結果テキストにも勝率は無い＝公開記事115コメント中0回） |
| **B高配分の平均差枚** | `_art_cmt_facts_high()` が機種ごとの `avg` を **`pop` して落とす** |
| 設定①〜⑥・確定演出・示唆演出・取材内容・イベント評価・新台/復活導入・前日据え置き・次回開催日 | facts に対応キーが無い |

**「候補文の側で書かないよう気をつける」方式にしてはならない。facts から消すのが正式。**

### ④ ★万枚台数は母集団ごとに別キーで持つ（混同禁止）

「その他の優秀台ピックアップ.jpg に実際に掲載された台」と「ホール全体の台」を混同しない。

| 母集団 | キー |
|---|---|
| A 全台系濃厚機種の中 | `n10k`（`_art_cmt_facts_zendai`） |
| B 高配分機種の中 | `n10k`（`_art_cmt_facts_high`） |
| E その他単品優秀台の中 | `n10k`（`_art_cmt_facts_other`・**独自に算出**） |
| F ホール全体 | `c10k`（`_art_cmt_facts_summary`・**独自に算出**） |

実データでの実測（9/5 = 全台系4 / 高配分2 / その他1 / 全体7、9/6 = 0 / 2 / 2 / 5）が
すべて異なることを純粋テストで確認済み。**1つのキーを共用しない。**

### ⑤ A と B は機種が重複しない

`_art_cmt_facts_high()` は **A（全台系）の機種を除外**する。
純粋テストで **A ∩ B = 空** を確認済み。

### ⑥ セクションと候補数

| キー | 見出し | 方式 |
|---|---|---|
| A | 全台系 | **3候補**（① 仕掛け・機種構成重視 ／ ② 出玉・突出結果重視 ／ ③ バランス型） |
| B | 高配分 | **3候補**（① 機種数・構成重視 ／ ② ⑤オススメとの関係重視 ／ ③ 突出出玉＋全体構成） |
| C | 並び・列 | **3候補** |
| **D** | **⑤オススメ機種** | **固定文方式**（`使用する（固定文）` / `使用しない` の2択） |
| E | その他単品優秀台 | **3候補** |
| F | まとめ | **3候補** |

- **D だけ固定文**。公開記事3本で**完全に同一の文章**だったため候補を作らない
  （`_ART_CMT_D_TEXT`）。**D を3候補方式へ変えない。**
- コメント位置の根拠：公開14記事の実測で**各セクションの末尾**（A 18/24・B 14/14・C 13/14・
  E 12/13）。**F は 1/14 しか無い**が、選べるように候補は用意する（既定は未選択）。

### ⑦ ★おすすめは表示だけ

`_art_cmt_recommend(sec, f)` の結果は
**`★おすすめ：候補③ バランス型 （表示のみ・自動では選ばれません）`** として表示するだけ。

- **自動選択しない。初期状態は必ず未選択（`選択してください`）。**
- **★おすすめを既定値にしてはならない。**

### ⑧ ★候補を選んだときだけ最終文へコピーする（最重要）

```
候補③を選択 → 最終文へコピー → 人間が一部修正 → 別の入力欄を操作（rerun）
  → 人間が修正した最終文を候補③の元文章で上書きしない
```

実装は `_on_art_cmt_pick()`（コメント候補 selectbox の `on_change`）だけがコピーする。

```python
if _sel is not None and _sel != _ART_CMT_PICK_UNSET:
    _new = _map.get(_sel, "")
    st.session_state[_txt_wk] = _new          # ← ここ1箇所だけ
    st.session_state[_txt_logical] = _new
    st.session_state[_art_edited_key(_txt_wk)] = True
```

- **毎 run で候補本文を最終文へ書き戻す実装にしてはならない。**
  純粋テストで **`st.session_state[_txt_wk] = _new` の出現がちょうど1箇所**であることを確認済み。
- `_on_art_cmt_pick()` は先頭に **`expected_excel` ガード**を持ち、
  旧日付 widget の遅延 callback で現在日付へ保存しない。

### ⑨ 保存（既存の日付別保存に相乗り・新しいJSONを作らない）

| 項目 | 値 |
|---|---|
| 保存先 | 既存 **`article_page_inputs.json`**（Excelファイル名＝日付でスコープ） |
| logical key | **`art_comment_pick_{A〜F}_{store}`**（選択）／**`art_comment_{A〜F}_{store}`**（最終文）＝**12キー** |
| display widget key | 既存 **`_art_widget_key()`＝`_artw_{excel_stem}_{logical}`** |
| 保存関数 | 既存 **`_save_article_inputs(store, True)`**（**`skip_kojin=True` 必須**） |
| 復元 | 既存 **`_restore_article_inputs()`** |

- **候補①②③の本文そのものは保存しない。facts も保存しない。**
  保存するのは「どれを選んだか」と「最終文」だけ（候補は毎回 facts から再生成する）。
- **`_artw_*` / `_artw_edited_*` は JSON へ保存しない。**
- **`_save_article_inputs()` / `_restore_article_inputs()` / `_art_widget_key()` /
  `_on_article_widget_change()` / `_art_txt()` は本体バイト無変更。**

### ⑩ ★`_article_input_keys()` は必ず店舗ゲートを通す（実装中に検出した不具合）

```python
if store in _ART_COMMENT_STORES:
    for _s, _ in _ART_CMT_SECTIONS:
        keys += [f"art_comment_pick_{_s}_{store}", f"art_comment_{_s}_{store}"]
```

**ゲートを外すと、高田馬場・秋葉原のエントリへ空のコメント12キーが混入する。**
`_ART_OSUSUME_EXTRA_STORES`（⑤9枠）と同じ理由。
初回実装でこのゲートを忘れており、純粋テストで検出して修正した。

### ⑪ 対象店舗

```python
_ART_COMMENT_STORES: "frozenset[str]" = frozenset({"渋谷新館"})
```

**高田馬場にはコメントUIを出さない。秋葉原も対象外。**
既存gate（`_ART_WP_STORES` / `_ART_WP_NOSPLIT_STORES` / `_ART_WP_FULLWIDTH_STORES` /
`_ART_WP_AUTHOR_STORES` / HQ 4種 / `_ART_OSUSUME_*`）と**統合しない**。

### ⑫ 丸め・数値表記は1箇所に集約する

| ヘルパー | 用途 |
|---|---|
| `_cmt_exact` | 台の差枚は**実数**（`+14,300枚`） |
| `_cmt_over_k` | 千単位＋「超」 |
| `_cmt_avg_over` | 平均は百単位＋「超」 |
| `_cmt_hall_total` | ホール総差枚（10万枚以上は万単位・それ未満は実数） |
| `_cmt_hall_avg` | ホール平均は実数 |
| `_cmt_n` / `_cmt_join` / `_cmt_by_size` | 台数・列挙・「3台設置のA・B、4台設置のC」 |

**候補生成関数の中で個別に丸め処理を書かない。**
`_cmt_by_size()` は公開記事8/28の「3台設置のミスジャグとウルトラミラジャグ」と同じ言い回しで、
**同じ設置台数の機種をまとめる**（A候補①で使用）。

### ⑬ 語彙の制約（公開記事の実例だけ使う）

- **「濃厚」は A（全台系）だけ**で使う。B/C/E/F では使わない。
- 「全台プラス」は使用可（公開記事に実例あり）。
- 禁止語（`1/2系` / `据え置き` / `パネル仕掛け` / 取材名 / `ななこ` / `フル稼働` など）は
  純粋テストで**30候補＋D固定文のすべてに出現しないこと**を機械確認する。

### ⑭ 純粋テスト（173 PASS / 0 FAIL）

9/5・9/6 の実データで A〜F の facts 生成／A/B/C/E/F の3候補すべて非空／D固定文／
★おすすめの一致（9/5 A3 B2 C3 E3 F2 ／ 9/6 A3 B3 C2 E3 F2）／再生成の決定論性／
母集団別の万枚台数分離／A∩B=空／**B候補に「平均」を含まない**／
**全候補に勝率を含まない**／禁止語0件／丸め規則／保存12キーと店舗ゲート／
`_artw_` を保存しない／新しいJSONを作らない／初期未選択／コピーは1箇所だけ／
`expected_excel` ガード／**WordPress plan・本文が高田馬場・渋谷新館とも HEAD とバイト一致**／
**変更関数は `_article_input_keys` と `show_auto_article_page` の2つだけ**／
既存の主要関数24本がバイト一致。

### ⑮ ローカル実機確認（2026-09-08・正式HEAD `31b9014`・渋谷新館 9/5・9/6）

**`55e7752` の必須手順どおり「アプリ停止 → コードのみ commit → 再起動 → 実機確認」**で実施
（`_git_auto_push()` の targets と実施前の dirty の交差が**0件**であることを確認済み）。

| 確認項目 | 結果 |
|---|---|
| 見出し順 | `⑥ 差枚数ランキング＆島図` → `🔍 プレビュー` → **`📝 記事コメント`** → `⑦ 実行`（**採番は⑦のまま・番号外**） |
| プレビュー未生成 | `🔍 プレビューを生成すると、その日の実データからコメント候補を作ります。` |
| A/B/C/E/F | 3候補＋`コメントを使用しない`＋`選択してください` |
| **D** | **`使用する（固定文）` / `使用しない` の2択** |
| ★おすすめ | `★おすすめ：候補③ バランス型 （表示のみ・自動では選ばれません）` |
| **初期状態** | **すべて未選択・最終文は空** |
| 候補選択 | 候補③を選ぶと最終文へコピー（182文字） |
| D選択 | 固定文61文字がコピー |
| **手修正の保持** | 最終文へ `【手修正テスト】` を追記 → **別セクションの候補選択・expander操作（rerun）を挟んでも上書きされない** |
| **日付切替** | 9/5 → 9/6 で**コメント欄・最終文とも 9/5 の値が0件（混入なし）** |
| **戻ると復元** | 9/6 → 9/5 で **A=候補③（手修正込み182文字）／B=候補②（184文字）／D=固定文（61文字）／C・E・F=未選択** が完全復元 |
| 使用データ | `st.json` で展開（`全台系機種数:7` / `全台系内の万枚台数:4` / `全台系内の+5,000枚台数:12` など。**勝率キーなし**） |
| WordPress掲載予定コメント | A〜F の現在の最終文を一覧表示＋`第1段階のため、このコメントは WordPress 本文へは挿入されません。` |

**確認後、テスト用に入れた `【手修正テスト】` は UI 上で削除し、
`article_page_inputs.json` に残っていないことを検証済み（JSONの直接編集はしていない）。**

### ⑯ ⑧本番を実行していない理由（不具合ではない）

**⑧「自動処理を開始」は意図的に実行していない。**
実機確認によって `article_page_inputs.json` に 9/5 のコメント12キーが保存されており、
同ファイルは **`_git_auto_push()` の targets に含まれる**ため、⑧を押すと
**確認用の入力値まで自動 commit / push される**。ユーザー指示（「副作用を調査して危険なら実行しない」）
に従い実行しなかった。
**WordPress 本文へコメントが入らないことは純粋テスト（plan・本文HTMLのバイト一致）で確認済み。**
**WordPress 通信は0件**（GET / POST / PUT / PATCH / DELETE / media upload / draft作成すべてなし）。
**Cloud Reboot も未実施。**

### ⑰ 今後の禁止事項

1. **facts に勝率を追加しない／B facts に平均差枚を戻さない**
2. **候補生成関数から df・diff_raw を直接参照しない**（facts 経由）
3. **`random`・LLM・API を使わない**（第1段階はルールベース）
4. **★おすすめを自動選択・既定値にしない／初期未選択を変えない**
5. **毎 run で候補本文を最終文へ書き戻さない**（コピーは候補変更イベント時の1箇所だけ）
6. **`expected_excel` ガードを外さない**
7. **`_article_input_keys()` の `_ART_COMMENT_STORES` ゲートを外さない**（他店舗へ空キーが混入）
8. **候補本文・facts を JSON へ保存しない／`_artw_*` を保存対象へ入れない**
9. **新しいJSON・新しい保存関数を作らない／`skip_kojin=True` を外さない**
10. **D を3候補方式へ変えない／`_ART_CMT_D_TEXT` を勝手に書き換えない**
11. **万枚台数の母集団別キーを1つに統合しない**
12. **A と B の機種重複除去を外さない**
13. **「濃厚」を A 以外で使わない**
14. **丸め処理を候補生成関数の中へ散らさない**
15. **高田馬場・秋葉原へコメントUIを出さない／既存gateと統合しない**
16. **第1段階のまま WordPress 本文へ挿入しない**（挿入は別案件として調査→承認のうえ実装）
17. **`wp_client.py` を変更しない（diff 0）**
18. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事コメント：D⑤オススメ機種も実データから3候補生成へ（2026-09-08・`b427efe` / `52be5eb`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】記事コメントの D「⑤オススメ機種」だけ**。
正式コード commit は **`b427efe`**（`feat: 渋谷新館の記事コメントD⑤を3候補方式へ変更`・
**`streamlit_app.py` のみ**・**+211 / −33**）＋
**`52be5eb`**（`fix: 記事コメントDの旧固定文UI残骸によるNameErrorを解消`・**−3**）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**
既存節は削除・圧縮・統合・並べ替えしない。

### ⓪ 直前節（`31b9014`）から上書きされた点

| | 旧（`31b9014`・当時の正式） | **新（本節・正式）** |
|---|---|---|
| D の方式 | **固定文方式**（`使用する（固定文）` / `使用しない` の2択・`_ART_CMT_D_TEXT`） | **A/B/C/E/F と同じ 実データ→facts→ルールベース→候補①②③** |
| D の UI | 2択 selectbox | **未選択＋候補3件＋「コメントを使用しない」の統一UI** |

**「## 渋谷新館 記事コメント自動生成 第1段階（2026-09-08・`31b9014`）」の節は削除・書き換えしない。**
同節⑥の「D だけ固定文」「D を3候補方式へ変えない」は **`31b9014` 時点の正式記録**であり、
**本節（2026-09-08 の後続仕様）がユーザー承認のうえ supersede した**という履歴として残す。
同節のそれ以外（3層アーキテクチャ／facts に勝率を持たない／★おすすめは表示のみ／
候補選択時だけコピー／日付スコープ保存／店舗ゲート／WordPress 未挿入）は**すべて有効**。

**旧定数 `_ART_CMT_D_TEXT` / `_ART_CMT_D_PICK_USE` は履歴として残置**（参照0件）。
**削除しない。**旧固定文の保存値（`art_comment_pick_D_渋谷新館` に
`使用する（固定文）` 等）が残っていても、選択肢に無い値は未選択へ倒れるだけで**破壊しない**。

### ① ★D の母集団は「⑤オススメ優秀台画像に実際に掲載された台」だけ

**コメント用に別の抽出ロジックを新造してはならない。**⑤画像とコメントの対象台が食い違う。

```
_art_osusume_block_images(...) → (画像, {ファイル名: 掲載台番}, ログ)
                                        ↓ これをそのまま渡す
_art_cmt_osu_rows(blocks, bans_by_fn, df) → ブロック単位の [{name,ban,diff}]
```

- `bans_by_fn` は **`_art_osusume_block_images()` の戻り値そのもの**。
  ブロック↔ファイル名の対応は **`_art_osusume_fn(n)`**（`オススメ優秀台_ブロック{n+1}.jpg`）で解決する。
- **画像が生成されなかったブロックは母集団に入れない**（`bans` が無い＝`continue`）。
- **差枚は⑤画像・結果と同じ補正後の `df["差枚"]`**（⑦=`_apdf` / ⑧=`result["df"]`）。
  **`_pipeline_calc_d` を再適用しない（二重補正の禁止）。**
  ＝画像 +8,500 / コメント +8,450 のような食い違いが構造的に起きない。
- 表記は**既存の記事コメント用ヘルパー `_cmt_exact()` / `_cmt_join()` / `_cmt_n()` を再利用**。
  **D 専用の丸めロジックを作らない。**

### ② facts（`_art_cmt_facts_osusume`）

母集団は⑤掲載台だけ。**勝率キーを持たない。平均差枚も持たない**（公開記事の⑤コメントで0回）。

| キー | 内容 |
|---|---|
| `n_blocks` / `titles` | 生成された⑤ブロック数 / ブロックタイトル |
| `blocks[]` | `idx` / `title` / **`filter`（そのブロックのオススメ種別＝抽出条件）** / `n_units` / `n_machines` / **`top`（そのブロックの最高差枚台）** / `rows` / `by_machine` |
| `n_units` / `n_machines` | ⑤掲載台総数 / 掲載機種数 |
| `by_diff` | 掲載台を差枚降順→台番昇順（`max` はその先頭） |
| `by_machine` | 機種ごとの掲載台数 |
| **`by_machine_max`** | **機種ごとの最高差枚台**を差枚降順（候補①が使う） |
| `n10k` / `n5k` / `n3k` | **⑤内の** +10,000 / +5,000（`_ART_CMT_D_BIG`）/ +3,000（`_ART_CMT_D_REP`）枚台数 |

- **`n10k` は⑤掲載対象内の万枚台数**。A `n10k` / B `n10k` / E `n10k` / F `c10k` と**別キーのまま**。
  **⑤対象外の万枚を「万枚オーバー」として書かない。**
- 0台なら全キーが 0 / 空で返る（候補は空文字3件）。

### ③ 候補①②③は「選ぶ情報」が違う（語尾だけ違う文にしない）

| | 役割 | 選ぶ情報 |
|---|---|---|
| **候補①** 突出差枚重視 | 出玉そのものを主役 | **`by_machine_max` の上位**（＝**異なる機種**を優先）／万枚 or `n5k>=2` で締め方が変わる |
| **候補②** 各種オススメ横断型 | オススメ種別の広がり | **ブロックごとの代表台**（`blocks[].title` ＋ `blocks[].top`）＋ ブロック数・総台数 |
| **候補③** バランス型 | 出玉＋立ち回り誘導 | 上位2機種 ＋ **`_ART_CMT_D_OUTRO`**（旧固定文の良い部分＝「気になる機種の優秀台をチェックしておき、今後の立ち回りに活かしましょう！」） |

- **候補①で同一機種を並べない。** `by_machine_max`（機種ごとの最高差枚を取り、その中から上位）を使う。
- **候補②は生成されなかったブロックに言及しない。** `blocks` にあるものだけを回す。
  **1ブロックだけの日は「各種」「幅広く」を使わない**（`_nb >= 2` のときだけ「各種」）。
  ブロック代表台は**そのブロックの最高差枚台**。⑤の重複ルール（同一機種は最初のブロックのみ）は
  `_art_osusume_block_images()` 側でフラット1回の `filter_recommended_machines` ＋ `_used` により
  既に効いているため、**コメント側で重複除去を再実装しない。**

### ④ 掲載台数に応じた表現（facts ベース・断定しない）

| ⑤掲載台数 | 挙動 |
|---|---|
| **0台** | **候補を作らない**（3件すべて空文字）。UI は `⑤オススメ優秀台の掲載対象がありません…` |
| **1台** | **その1台だけ**を書く。**「多数」「続出」「各種」を使わない** |
| **2台** | 最大2台まで |
| **3台以上** | 2〜3台 |

- 「大量出玉が続出！」は **万枚あり or `n5k >= 2`** のときだけ。
- 「+5,000枚オーバーも複数」は **`n5k >= 2`** のときだけ。
- 「万枚オーバー」は **`n10k >= 1`（⑤掲載対象内）** のときだけ。

### ⑤ ★おすすめ（`_art_cmt_recommend` の D 分岐・表示のみ）

```python
if sec == "D":
    _reps = [b["top"]["diff"] for b in (f.get("blocks") or [])]
    if (f.get("n_blocks", 0) >= 3
            and sum(1 for d in _reps if d >= _ART_CMT_D_REP) >= 3):
        return 2          # 複数ブロックから強い代表台 → 候補②
    if f.get("n10k") or f.get("n5k", 0) >= 2:
        return 1          # 突出した大量出玉が複数 → 候補①
    return 3              # それ以外 → 候補③
```

- **決定論的**（`random` を使わない）。同じ facts なら常に同じ結果。
- **表示のみ。自動選択しない。初期状態は必ず未選択。**
- 実データでの結果：**9/5 → 候補①** ／ **9/6 → 候補②**（判定順は上記のとおり）。

### ⑥ UI は A/B/C/E/F と同じ統一UI

D の特例分岐を撤去し、`_cmt_cands[_sec]` / `_ART_CMT_LABELS[_sec]` の共通ループへ統合した。
`_ART_CMT_LABELS["D"] = ("候補① 突出差枚重視", "候補② 各種オススメ横断型", "候補③ バランス型")`。

- 未選択 → 候補3件 → **コメントを使用しない**
- **★おすすめは表示のみ／未保存日は未選択・最終文は空**
- **候補を選んだときだけ最終文へコピー**（`_on_art_cmt_pick` の1箇所のみ）
- **手修正後の rerun で候補本文へ戻さない**

### ⑦ ★旧D特例の残骸で実際に落ちた（同種の再発防止）

`b427efe` の時点で、旧固定文UIの一部

```python
elif _sec == "D" and not _has:
    st.caption("この日は⑤オススメの画像が無いため、コメントは不要です。")
```

が残っており、**`_has` が未定義のため D セクションで `NameError: name '_has' is not defined`
（`streamlit_app.py:17524`）** となり記事用ページが落ちた。純粋テストでは検出できず、
**実機確認（⑦プレビュー）で初めて出た。**`52be5eb` で当該3行を削除。

**再発防止**：`scratchpad/test_d.py` に
**「`show_auto_article_page` 内でどこにも代入されていないローカル名を参照していないか」を
AST で静的検出する項目（group 27）を追加**した（lambda 引数・comprehension・except 名・
import 名・グローバルを除外して判定）。
**UI の特例分岐を撤去するときは、必ずこの静的チェックと実機確認の両方を通すこと。**

### ⑧ 保存キー（新規追加しない）

D も他セクションと同じ **`art_comment_pick_D_{store}` / `art_comment_D_{store}`** を
**そのまま再利用**する（コメント12キーのまま）。

- **新しい保存キー・新しいJSONを作らない。**
- 保存は既存 `_save_article_inputs(store, True)`（**`skip_kojin=True` 必須**）／
  display key は `_art_widget_key()`＝`_artw_{excel_stem}_{logical}`／
  `expected_excel` ガード・`_art_restored_excel` ガードもそのまま。
- **候補本文・facts は保存しない**（毎回 facts から再生成する）。
- 旧固定文の保存値は破壊しない（選択肢に無ければ未選択へ倒れるだけ）。

### ⑨ 9/5 実測（⑤最終掲載データ・ローカル実機 ⑦プレビュー）

| 項目 | 値 |
|---|---|
| ⑤ブロック数 | **3** |
| ブロック名 | 週間オススメ北斗シリーズ ／ 3Fオススメ ／ 月間オススメジャグラーシリーズ |
| 掲載台数 / 掲載機種数 | **25台 / 8機種** |
| 差枚上位 | **ゴッド神々の軌跡 +8,600 ／ 戦国乙女5 +8,350 ／ ゴージャグ3 +3,400** |
| 万枚台数 / +5,000枚以上 / +3,000枚以上 | **0 / 3 / 6** |
| **★おすすめ** | **候補①（突出差枚重視）** |

```
候補① 突出差枚重視
オススメ機種からは大量出玉が続出！
今回はゴッド神々の軌跡から+8,600枚・戦国乙女5から+8,350枚・ゴージャグ3から+3,400枚など、オススメ機種から大量出玉を確認できました！
+5,000枚オーバーの台も3台と、オススメ機種からの大量出玉が目立つ結果となっていました。

候補② 各種オススメ横断型
週間オススメ北斗シリーズの北斗転生2から+1,600枚、3Fオススメのゴッド神々の軌跡から+8,600枚、月間オススメジャグラーシリーズのゴージャグ3から+3,400枚と、各種オススメから優秀台が登場！
今回は3種類のオススメからあわせて25台の優秀台を確認できており、どのオススメを追いかけてもチャンスがある内容となっていました。

候補③ バランス型
各種オススメ機種の優秀台をピックアップ。
今回はゴッド神々の軌跡から+8,600枚・戦国乙女5から+8,350枚と目立った出玉を確認！
気になる機種の優秀台をチェックしておき、今後の立ち回りに活かしましょう！
```

### ⑩ 9/6 実測（⑤最終掲載データ・ローカル実機 ⑦プレビュー）

| 項目 | 値 |
|---|---|
| ⑤ブロック数 | **3** |
| ブロック名 | 週間オススメ北斗シリーズ ／ 3Fオススメ ／ 月間オススメジャグラーシリーズ |
| 掲載台数 / 掲載機種数 | **20台 / 5機種** |
| 差枚上位 | **戦国乙女5 +16,250 ／ 北斗転生2 +4,900 ／ ファンキー2 +3,500** |
| 万枚台数 / +5,000枚以上 / +3,000枚以上 | **1 / 1 / 7** |
| **★おすすめ** | **候補②（各種オススメ横断型）** |

```
候補① 突出差枚重視
オススメ機種からは大量出玉が続出！
今回は戦国乙女5から+16,250枚・北斗転生2から+4,900枚・ファンキー2から+3,500枚など、オススメ機種から大量出玉を確認できました！
中でも戦国乙女5の+16,250枚は万枚オーバーとなっており、オススメ機種を追いかけた方はチャンスを掴めた1日となっていました。

候補② 各種オススメ横断型
週間オススメ北斗シリーズの北斗転生2から+4,900枚、3Fオススメの戦国乙女5から+16,250枚、月間オススメジャグラーシリーズのファンキー2から+3,500枚と、各種オススメから優秀台が登場！
今回は3種類のオススメからあわせて20台の優秀台を確認できており、どのオススメを追いかけてもチャンスがある内容となっていました。

候補③ バランス型
各種オススメ機種の優秀台をピックアップ。
今回は戦国乙女5から+16,250枚・北斗転生2から+4,900枚と目立った出玉を確認！
気になる機種の優秀台をチェックしておき、今後の立ち回りに活かしましょう！
```

### ⑪ 実機確認（2026-09-08・ローカル・正式HEAD `52be5eb`）

`55e7752` の必須手順どおり **アプリ停止 → コードのみ commit → 再起動 → 実機確認**で実施。

| 確認項目 | 結果 |
|---|---|
| D の見出し | `📝 ⑤オススメ機種`（他セクションと同じ expander） |
| ★おすすめ | 9/5 `候補① 突出差枚重視` ／ 9/6 `候補② 各種オススメ横断型`（いずれも「表示のみ・自動では選ばれません」） |
| 選択肢 | **未選択 ＋ 候補①②③ ＋ コメントを使用しない の5件** |
| 初期状態 | **未選択・最終文は空** |
| 候補選択 → コピー | 9/5 で候補②を選ぶと最終文へコピー |
| 手修正の保持 | 最終文へ `【D手修正テスト】` を追記 → **ctrl+Enter の rerun でも、別セクション（全台系）expander 操作の rerun でも上書きされない** |
| 日付切替 | 9/5 → 9/6 で **9/5 の手修正文の混入0件**／9/6 は D 未選択スタート |
| 9/6 で別候補 | 9/6 で候補③を選択しコピー（`…立ち回りに活かしましょう！`） |
| **戻ると復元** | 9/6 → 9/5 で **D=候補② ＋ 手修正込みの最終文が完全復元**（別日混入0件） |
| NameError / Traceback | **0件** |

確認後、テスト用の `【D手修正テスト】` は **UI 上で削除**した（**JSONの直接編集はしていない**）。

### ⑫ A/B/C/E/F の完全非回帰

`bb56b94`（D変更前）と同一データ（9/5・9/6）で機械比較し、
**A/B/C/E/F の facts JSON・候補①②③の全文・★おすすめがすべて一致**。
⑤画像側も **`bans` マップ・ファイル名・掲載順が `bb56b94` と一致**（**⑤画像生成ロジックは変更禁止**）。
**WordPress plan / 本文にコメントは1文字も入らない**（`wp_client.py` diff 0・第1段階のまま）。

### ⑬ テスト

- **`scratchpad/test_cmt.py`（既存スイート）＝ 173 PASS / 0 FAIL**
- **`scratchpad/test_d.py`（本件用・新規）＝ 97 PASS / 0 FAIL**

test_d.py の主な確認：D facts の生成項目 ／ 3候補の生成 ／ **決定論**（再生成一致）／
**⑤掲載台と完全一致**（対象外台を拾わない）／機種別最高差枚 ／ ブロック代表＝最高差枚台 ／
**万枚母集団＝⑤内のみ** ／ 0台・1台・2台・3台以上 ／ 同一機種複数台 ／
同一機種のブロック重複は最初のみ ／ 候補①②③の役割差 ／ ★おすすめ判定 ／
`_cmt_exact` 使用・独自丸めなし ／ **勝率・平均を持たない** ／ 禁止語0件 ／
保存キー12・店舗ゲート ／ D固定文UIの撤去 ／ 旧定数の残置 ／ Dラベル3種 ／
**コピーは1箇所のみ** ／ `expected_excel` ガード ／ **A/B/C/E/F 完全非回帰** ／
**⑤画像の掲載台・ファイル名順序が旧HEADと一致** ／ 35関数の AST バイト一致 ／
`wp_client.py` diff 0 ／ WP plan にコメント0 ／ 実 import ／
**group 27＝UI 関数内の未定義ローカル参照検出**。

**HEAD 版との比較は必ずプロジェクトと同一ディレクトリへ一時コピーして行い、比較後に削除する**
（`BASE_DIR` がずれると `store_settings` / `機種名変換.xlsx` を読めず誤検知する）。

### ⑭ 今後の禁止事項

1. **D を固定文方式へ戻さない**（`31b9014` の記録は履歴として残す）
2. **`_ART_CMT_D_TEXT` / `_ART_CMT_D_PICK_USE` の定義を削除しない**
3. **D の母集団を⑤画像以外から取らない／コメント用の別抽出を新造しない**
4. **`_art_osusume_block_images()` の `bans` 以外を母集団にしない／`_art_osusume_fn()` 以外で対応を解決しない**
5. **差枚を再計算しない（`_pipeline_calc_d` の二重適用禁止）／D 専用の丸めを作らない**
6. **facts に勝率・平均差枚を追加しない**
7. **`n10k` を他セクションの母集団と統合しない／⑤対象外の万枚を書かない**
8. **候補①で同一機種を並べない**（`by_machine_max` を使う）
9. **候補②で生成されていないブロックに言及しない／1ブロックの日に「各種」「幅広く」を使わない**
10. **1台の日に「多数」「続出」「各種」を使わない／0台で候補を作らない**
11. **候補①②③を語尾だけ違う文にしない**
12. **★おすすめを自動選択・既定値にしない／`random` を使わない**
13. **毎 run で候補本文を最終文へ書き戻さない**（コピーは候補変更イベント時の1箇所だけ）
14. **D 用に新しい保存キー・新しいJSONを作らない／`skip_kojin=True` を外さない**
15. **⑤画像生成ロジック（`_art_osusume_block_images` / パネル / 液晶なし / 水色バーなし / ファイル名）を変更しない**
16. **A/B/C/E/F の facts・候補・★おすすめを変更しない**
17. **第1段階のまま WordPress 本文へ挿入しない／`wp_client.py` を変更しない（diff 0）**
18. **UI の特例分岐を撤去するとき、静的チェック（test_d group 27）と実機確認の両方を省略しない**
19. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事コメント 第2段階：人間が確定した最終文だけをWordPress本文へ挿入（2026-09-08・`2e3a694`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用WordPress本文だけ**。
正式コード commit は **`2e3a694`**（`feat: 渋谷新館の記事コメントをWordPress本文へ挿入（人間確定文のみ）`・
**`streamlit_app.py` と `wp_client.py` の2ファイルのみ**・**+130 / −11**）。
**`convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**
既存節は削除・圧縮・統合・並べ替えしない。

### ⓪ 第1段階から supersede された点（1点だけ）

| | 旧（`31b9014` / `b427efe`・第1段階） | **新（本節・第2段階）** |
|---|---|---|
| WordPress本文 | **コメントは1文字も入らない**（`wp_client.py` diff 0・UIに「第1段階のため挿入されません」） | **人間が確定した最終文だけが入る**（A〜F 各セクション末尾に1回） |

**「## 渋谷新館 記事コメント自動生成 第1段階（2026-09-08・`31b9014`）」の
「WordPress本文へ挿入しない」「`wp_client.py` を変更しない（diff 0）」という記録は
削除・書き換えしない。**当時の正式仕様として正しく、**本節が後続仕様として supersede した**
という履歴として残す。
第1段階・D⑤3候補化（`b427efe` / `52be5eb`）の**それ以外はすべて有効**：
実データ→facts→候補①②③→**人間が明示選択**→最終文へコピー→人間が編集→日付単位保存 ／
facts に勝率なし ／ ★おすすめは表示のみ ／ 候補変更イベント時だけコピー ／
手修正はrerunで保持 ／ D は候補① 突出差枚重視 / ② 各種オススメ横断型 / ③ バランス型。
**候補生成ロジック・facts・おすすめ判定・候補UI・日付保存は今回いっさい変更していない。**

### ① ★WordPressへ送るのは「最終文」だけ

使うのは **`art_comment_A_{store}` 〜 `art_comment_F_{store}`（最終文）**のみ。

- **候補①②③の本文から直接WordPress本文を作らない。**
- **★おすすめ候補を直接使わない・未選択の補完にも使わない。**
- 判定は**pick 状態が正式な使用可否**（文字列を仮定せず、現在の実装値だけを見る）。

```python
_ART_CMT_WP_KEYS = {"A": "zendai", "B": "high", "C": "narabi",
                    "D": "osusume", "E": "other", "F": "summary"}

def _art_comment_pick(store, sec)        # art_comment_pick_{sec}_{store} の現在値
def _art_comment_final_text(store, sec)  # art_comment_{sec}_{store} を strip しただけ
def _art_comment_is_enabled(store, sec)  # ★使用可否の唯一の判定
def _art_wp_comments(store)              # payload["comments"] を作る
```

**`_art_comment_is_enabled()` が True になるのは
「pick が `_ART_CMT_LABELS[sec]` の3候補のいずれか」かつ「最終文が非空」だけ。**

| pick / 最終文 | 挿入 |
|---|---|
| 候補①②③のいずれか ＋ 最終文が非空 | **する** |
| **未選択**（`_ART_CMT_PICK_UNSET` / `None` / `""`） | **しない** |
| **`_ART_CMT_PICK_NONE`（コメントを使用しない）** | **しない（最終文の文字が残っていても送らない）** |
| 旧D固定文の値（`_ART_CMT_D_USE` / `_ART_CMT_D_SKIP`） | **しない**（現在の選択肢に無い） |
| 候補選択済み ＋ **最終文が空**（`""` / 空白 / 改行のみ） | **しない** |

**pick が候補②で最終文が人間編集済みなら、候補②の元文章ではなく編集済み最終文を送る**
（`_art_wp_comments()` は最終文だけを読む）。

### ② 取得タイミングは「送信直前」（⑧時点で固定しない）

`author_user` と同じ流儀で、**WordPress下書き作成ブロックの入口**で現在の確定状態を入れる。

```python
if store in _ART_COMMENT_STORES:
    _wp_pl["comments"] = _art_wp_comments(store)
```

- **⑧の payload 構築（`build_payload()` 直後）へ comments を入れてはならない。**
  ⑧のあとにコメントを選び直しても反映されない＝古い状態で送る事故になる。
- 参照するのは**現在日付の logical キーだけ**（`_restore_article_inputs()` が現在Excelの
  保存値で埋めたもの）。**JSONの直読み・`_artw_*` の参照はしない**ので、
  **別日の値は構造的に混入しない**。日付スコープの正式仕様
  （`_art_restored_excel` / `_art_widget_key()` / `expected_excel` ガード / `skip_kojin=True`）は
  **いっさい変更していない**。

### ③ gate は既存の `_ART_COMMENT_STORES`（渋谷新館のみ）

```python
_ART_COMMENT_STORES = frozenset({"渋谷新館"})   # 第1段階から不変
```

**comments キーを渡すのはこの店舗だけ。**
**高田馬場・秋葉原は `comments` キー自体を持たない**ので本文は1ブロックも変わらない。
**`wp_client.py` 側に店舗名リストを持たせない**（`plan_blocks()` は payload 駆動）。

### ④ 挿入層は `plan_blocks()`（画像split層へ文章ロジックを混ぜない）

`wp_client.py` に**新規は `_comment_paras()` の1関数だけ**、
**本体が変わったのは `plan_blocks()` だけ**。

```python
def _comment_paras(payload, key) -> list[dict]:
    _t = str(((payload.get("comments") or {}) or {}).get(key) or "")
    return [{"type": "para", "text": esc(_ln)} for _ln in _split_para(_t)]
```

- **既存 `para` ブロック経路（`blk_para()`）だけを使う。新しいHTMLを直書きしない。**
- **`build_content` / `collect_files` / `plan_split` / `needs_split` / `split_count` /
  `split_image_for_wp` / `blk_image` / `build_payload` / `_existing_files` / `_split_para` /
  `esc` / `h3_*` はバイト一致（無変更）。**
- ユーザー入力なので **`esc()` を通す**（`&` → `&amp;` 等。実測確認済み）。

### ⑤ 改行は既存 `_split_para()` を再利用（1行＝1段落・空行は落とす）

記事上部の「ポスター下の文章」「Xリンク下の文章」と**同じ既存仕様**に揃える。

```
入力: "1段落目。\n2段落目。\n\n3段落目。"
出力: para「1段落目。」/ para「2段落目。」/ para「3段落目。」
```

- **1個の巨大paragraphへ押し込まない。空の paragraph も作らない。**
- **内容は一切書き換えない**：facts/候補からの再生成・表現調整・句読点変更・
  改行の作り替え・数字の丸め直しを**しない**。するのは**前後空白の除去と空行の除去だけ**
  （`　オススメ機種からは+16,250枚！　` → `オススメ機種からは+16,250枚！` を実測確認）。

### ⑥ 挿入位置（各論理セクションの末尾に1回だけ）

**各H3ごとには入れない。** 現在の後半掲載順（並び・列 → ⑤オススメ → その他単品 →
差枚数ランキング&島図）は**変更していない**。

| | コメント | 位置 |
|---|---|---|
| **A** | 全台系 | H2「全台系濃厚機種が複数」の**最後の全台系画像の直後**（複数H3・複数画像でも1回） |
| **B** | 高配分 | H2「1/2系以上の高配分機種が大量」の**最後の画像の直後**。**渋谷新館はジャグラー系高配分も統合済み**（`_ART_WP_NO_JUG_SECTION_STORES`）なので、統合後の末尾に1回 |
| **C** | 並び・列 | H2「並び・列仕掛けも！」の**最後の並び/列画像の直後**（並びが複数でも1回） |
| **D** | ⑤オススメ | **`オススメ優秀台_ブロック*.jpg` 全ブロックの後に1回**。**ブロック1〜6それぞれの後には入れない** |
| **E** | その他単品 | `その他の優秀台ピックアップ.jpg` の直後に1回 |
| **F** | まとめ | **島図の直後**（ranking → 全台データ conditional → 島図 → **Fコメント**）。**新しいH2は作らない** |

実測した最終順（9/5・9/6・A〜F全選択）:

```
… 全台系画像 → Aコメント → H2高配分 … 高配分画像 → Bコメント
→ H2並び・列 … 並び/列画像 → Cコメント
→ H2オススメ機種の優秀台 … ブロック画像×n → Dコメント
→ H2その他単品優秀台 → その他画像 → Eコメント
→ H2差枚数ランキング&島図 → ランキング → 全台データ → 空段落×5 → 島図 → Fコメント
→ 店舗情報ボタン
```

### ⑦ ★E その他単品と WP split の整合（最重要回帰ポイント）

渋谷新館は **local/preview は one-piece ／ WP送信時だけ `その他の優秀台ピックアップ.jpg` を
分割する例外**（`_ART_WP_NOSPLIT_STORES` ＋ `_ART_WP_SPLIT_ALLOW_FILES`）。

- コメントは **`plan_blocks()` で論理ファイル単位に計画**する。split は `build_content()` 層の
  話なので、**分割片が4枚になる日も Eコメントは最後の piece の直後に1回**だけ入る
  （実測: 4分割で `piece1 … piece4 → Eコメント`／**piece間にコメント0**）。
- **split計画・分割数・連結クラス・画像サイズ・fullwidth・Luminous・Gutenberg 検証は
  いっさい変更していない**（分割画像ブロックのHTMLがコメント有無でバイト一致）。
- **local/preview の one-piece 仕様も変更していない。**

### ⑧ セクションが存在しない日は孤立コメントを出さない

**画像・データが無いセクションのコメントは、最終文が保存されていても出さない。**

| 条件 | 挙動 |
|---|---|
| 全台系0件（`zen_dai` 空） | **Aコメントを出さない**（他は従来どおり1回） |
| 高配分画像0枚 | **Bコメントを出さない** |
| 並び・列とも0件 | **Cコメントを出さない** |
| ⑤ブロック画像0枚 | **Dコメントを出さない** |
| `その他の優秀台ピックアップ.jpg` が無い | **Eコメントを出さない**（H2の扱いは従来どおり変えない） |
| ランキング・全台データ・島図がすべて無い | **Fコメントを出さない**（H2ごと出ないまま） |

E だけは H2 が無条件 append される既存仕様なので、**`os.path.isfile(FN_SONOTA)` を見て
コメントだけを抑止**する（H2側の既存挙動は変更しない）。

### ⑨ UI（⑧実行前に人間が確認できる）

「📄 WordPress掲載予定コメント（現在の最終文）」の表示を第2段階へ更新した。

```
A 全台系：掲載　候補③ バランス型            ← 最終文も表示
B 高配分：掲載　候補② ⑤オススメとの関係重視
C 並び・列：未選択のためコメントは掲載されません
D ⑤オススメ機種：掲載　候補② 各種オススメ横断型
E その他単品優秀台：未選択のためコメントは掲載されません
F まとめ：未選択のためコメントは掲載されません
掲載予定 3 / 6 セクション。★おすすめは自動採用されません（選んだものだけが入ります）。
```

- pick が `コメントを使用しない` → **「掲載しない（「コメントを使用しない」を選択中）」**
- pick は候補だが最終文が空 → **「掲載しない（最終文が空欄のため掲載されません）」**
- **未選択でも⑧・下書き作成は実行できる**（候補を強制選択させない）。未選択は
  「コメントなし」としてスキップし、**UI上で分かるように表示するだけ**。
- 候補説明の注記も **「選んで確定した最終文だけが WordPress 本文へ入ります」**へ更新。

### ⑩ 変更範囲（機械確認）

| ファイル | 変更 |
|---|---|
| `wp_client.py` | **変更関数は `plan_blocks` だけ ／ 新規は `_comment_paras` だけ ／ 消失0** |
| `streamlit_app.py` | **変更関数は `show_auto_article_page` だけ ／ 新規は `_art_comment_pick` / `_art_comment_final_text` / `_art_comment_is_enabled` / `_art_wp_comments` の4つだけ ／ 消失0** |

バイト一致（無変更）を機械確認：
`_art_cmt_facts_*`（A〜F 6種）／`_art_cmt_cands_*`（6種）／`_art_cmt_recommend` ／
`_art_cmt_facts_view` ／ `_art_osusume_block_images` ／ `_art_osusume_plan` ／
`_art_osusume_fn` ／ `_art_ranking_image` ／ `_art_zendai_image` ／ `_zendai_total_stat` ／
`_save_article_inputs` ／ `_restore_article_inputs` ／ `_art_widget_key` ／
`_on_article_widget_change` ／ `_art_txt` ／ `_article_input_keys` ／ `_build_col_items` ／
`_apply_panel_to_table_img` ／ `_art_panel_max` ／ **`show_auto_page`** ／ `show_rote_page` ／
`generate_report_text`。
**コメント保存キーは12のまま**（新キー・新JSONなし）。**D候補ラベルも維持。**

### ⑪ ローカル body 検証（実WordPress通信0件・202 PASS / 0 FAIL）

実データ 9/5・9/6 の payload（pipeline 実行結果 → `build_payload()` ＋ 列・⑤・ランキング・
全台データ・島図）を作り、画像を一時フォルダへ置いて `plan_blocks()` / `build_content()` を検証。
**⑧は押していない。**

| # | 内容 | 結果 |
|---|---|---|
| 1 | 全コメント未選択 → **body が第1段階(`6ef029e`)と完全一致**（plan も一致）。`comments={}` / `None` でも一致 | PASS |
| 2 | Aだけ選択 → 全台系末尾に**1回だけ**・他は0・次は高配分H2 | PASS |
| 3 | A〜F全選択 → **各1回**・出現順 A→B→C→D→E→F・**各コメントの直前が画像** | PASS |
| 4 | 「コメントを使用しない」 → **挿入0** | PASS |
| 5 | 候補選択＋手修正文 → **手修正文が入る** | PASS |
| 6 | 候補選択＋最終文空（`""` / 空白 / 改行） → 入らない | PASS |
| 7 | pick=なし＋最終文の文字が残存 → **入らない** | PASS |
| 8 | 未選択（`None` / `""` / 未選択 / 旧D値）＋文字残存 → 入らない・★おすすめで補完しない・混在（A/B/D/Fだけ）でC/E残骸なし | PASS |
| 9 | ⑤ブロック複数（実データで2枚以上） → **Dは最後のブロック画像の直後に1回** | PASS |
| 10 | その他単品 split 4枚 → **Eは最後のpieceの後に1回**・piece間0・分割画像HTML一致 | PASS |
| 11 | F → **ranking → 全台データ → 空段落×5 → 島図 → Fコメント → ボタン** | PASS |
| 12 | 全台データ未成立 → **ranking → 空段落×5 → 島図 → Fコメント**（全台データ画像は本文に無い） | PASS |
| 13 | セクション不在（A/B/C/D/E/F 各ケース） → **孤立コメントなし**・他は1回のまま | PASS |
| 14 | 9/5 と 9/6 で**別日コメント混入0**・helper はJSON直読みしない | PASS |
| 15 | **高田馬場 body 完全一致**（キーなし／`comments` を誤って渡した場合とも）・`シマズをチェック！` 維持 | PASS |
| 16 | **秋葉原 body 完全一致**・`_ART_WP_STORES` / `_ART_COMMENT_STORES` 外 | PASS |
| 追加 | H2の集合と順序不変 ／ 画像順不変 ／ **画像ブロックHTML完全一致** ／ fullwidth3点セット ／ `linkDestination":"none"`・`<a href` なし ／ コメントは `para` ブロックのみ | PASS |

**高田馬場の正式 baseline `c35ac89ea13c` は引き続き有効。**
今回は現コードの baseline 手順（同一 payload で第1段階版 `wp_client.py` と比較して
**body 完全一致**）で確認した。**MD5 を置き換えない。**

### ⑫ 実UI確認（2026-09-08・ローカル・正式HEAD `2e3a694`）

`55e7752` の手順どおり **アプリ停止 → コードのみ commit → 再起動 → 実機確認**。
渋谷新館 9/5（確定433台）の**保存済みコメント**（A=候補③ / B=候補② / D=候補② /
C・E・F=未選択）で確認：

- 候補説明の注記が **「選んで確定した最終文だけが WordPress 本文へ入ります」**
- 確認表示が **A/B/D=「掲載」＋最終文表示 ／ C/E/F=「未選択のためコメントは掲載されません」**、
  **掲載予定 3 / 6 セクション**、★おすすめ非採用の注記
- NameError / Traceback **0件**

### ⑬ 確認状況の正確な記録（誤記しないこと）

- **実WordPress送信はしていない。** POST / PUT / PATCH / DELETE / media upload /
  下書き作成すべて**0件**。GET も行っていない。**Cloud Reboot も未実施。**
  ユーザーが明示的に依頼したときだけ実施する。
- **「掲載しない（コメントを使用しない）」の実UI表示は未確認**
  （切替操作の時点でブラウザのWebSocketが再接続中でサーバへ届かず、保存値も変わらなかった）。
  **純粋テスト（case 4 / 7）でPASS済み。「実UI確認済み」と書かない。**
- ローカル body 検証は**⑧の実出力フォルダではなく、実データ payload ＋ 一時フォルダの
  画像**で行った（⑧を押さない方針のため）。**「⑧本番の出力で確認した」と書かない。**

### ⑭ 今後の禁止事項

1. **候補①②③の本文・★おすすめを直接WordPressへ入れない**
2. **未選択／`コメントを使用しない`／最終文が空を挿入しない**（pick を使用可否の正とする）
3. **★おすすめで未選択セクションを補完しない**
4. **pick 状態の文字列を仮定しない**（`_ART_CMT_LABELS` / `_ART_CMT_PICK_*` を見る）
5. **comments を⑧の payload 構築時点で固定しない**（送信直前に取得する）
6. **`_ART_COMMENT_STORES` 以外へ comments を渡さない**／`wp_client` 側へ店舗名を持たせない
7. **各H3ごとにコメントを入れない**（各セクション末尾に1回）
8. **Dをブロックごとに入れない**／**Eを split piece ごとに入れない**
9. **Fを島図より前に入れない／新しいH2を作らない／空段落の位置・個数を変えない**
10. **セクション不在の日に孤立コメントを出さない**
11. **コメント挿入のために画像ブロックHTML・split計画・fullwidth・Luminous・
    Gutenberg 仕様を変更しない**
12. **`build_content` / `collect_files` / `plan_split` / `needs_split` / `split_count` /
    `split_image_for_wp` / `blk_para` / `blk_image` / `build_payload` を変更しない**
13. **新しいHTMLを直書きしない**（既存 `para` 経路だけ）／**`esc()` を外さない**
14. **文章を再生成・改変しない**（前後空白と空行の除去だけ）
15. **改行を1段落へ押し込まない／空 paragraph を作らない**
16. **候補生成・facts・おすすめ判定・候補UI・保存キー・日付スコープを変更しない**
17. **高田馬場・秋葉原へコメントを挿入しない／両店の body を変えない**
    （baseline `c35ac89ea13c` を削除・上書きしない）
18. **第1段階の記録（WordPress未挿入・`wp_client.py` diff 0）を削除・書き換えしない**
19. **依頼なしに実WordPress送信（下書き作成・media upload）をしない**
20. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】渋谷新館 記事コメント：第1段階＋第2段階＋実WordPress検証完了（2026-09-09）

**正式記録。巻き戻し禁止。**対象は**【渋谷新館】の記事用ページの📝記事コメントだけ**。
本節は**記録のみで、コード変更を伴わない**（`streamlit_app.py` / `wp_client.py` /
`convert_narabi_pil.py` / `shimazu_renderer.py` はいっさい変更していない）。

**既存3節は削除・圧縮・書き換えしない**：

| 既存節 | commit |
|---|---|
| 記事コメント自動生成 第1段階（2026-09-08） | `31b9014` / 記録 `bb56b94` |
| D⑤オススメ機種も実データから3候補生成へ（2026-09-08） | `b427efe` / `52be5eb` / 記録 `6ef029e` |
| 第2段階：人間が確定した最終文だけをWordPress本文へ挿入（2026-09-08） | `2e3a694` / 記録 `3333795` |

本節は上記を**supersede する最新の正式状態**である。特に第1段階節の
「WordPress本文へ挿入しない」「`wp_client.py` diff 0」は**当時の正式仕様として正しい記録**であり、
**第2段階（`2e3a694`）とここでの実WordPress検証によって上書きされた**という履歴として残す。

### 1. 対象

```python
_ART_COMMENT_STORES = frozenset({"渋谷新館"})
```

**渋谷新館のみ。高田馬場・秋葉原には適用しない。**

### 2. 対象セクション

**A 全台系 ／ B 高配分 ／ C 並び・列 ／ D ⑤オススメ機種 ／ E その他単品優秀台 ／ F まとめ**

### 3. 第1段階（候補生成〜人間確定）

```
実データ → facts → 候補①②③ → ★おすすめ表示 → 人間が明示選択
        → final text へコピー → 人間が編集可能 → article_page_inputs.json へ日付単位保存
```

- **候補生成に random / LLM / 外部API を使わない。候補は決定論的**（同じ facts なら常に同じ文）。
- **★おすすめは表示のみ。自動選択しない。WordPressへ直接使用しない。**

### 4. 保存

- **pick 6キー ＋ final 6キー ＝ 12キー**（`art_comment_pick_{A〜F}_{store}` /
  `art_comment_{A〜F}_{store}`）。
- **新しいJSONを作らない。**既存 `article_page_inputs.json` の日付（Excel名）スコープを使う。
- 保存は既存 `_save_article_inputs(store, True)`＝**`skip_kojin=True` 必須**。
- **別日への混入禁止**（display key は `_artw_{excel_stem}_{logical}`、
  `expected_excel` / `_art_restored_excel` ガードを維持）。

### 5. D⑤の正式仕様（旧固定文方式を supersede）

- **D も現在は3候補**。旧固定文（`_ART_CMT_D_TEXT` / `使用する（固定文）`）へ戻さない
  （定数の定義自体は履歴として残置）。
- **Dの母集団は `_art_osusume_block_images()` が実際に⑤画像へ掲載した `bans` のみ。別抽出禁止。**
- ブロック↔ファイル名の対応は **`_art_osusume_fn(n)`**。
- 差枚は**既存の補正済み `df["差枚"]` をそのまま使用**。**D側で再補正・二重補正禁止。**
- facts に **勝率なし・平均差枚なし**。`n10k` 等も**⑤掲載母集団内だけ**。
- 候補の役割：**①＝`by_machine_max` の上位別機種中心 ／ ②＝各⑤ブロック代表機種中心 ／
  ③＝上位2機種＋既存 outro**。
- **★おすすめ判定も決定論的。**

### 6. WordPress掲載条件

**WordPressへ掲載するのは保存済み final text だけ。**

| 条件 | 掲載 |
|---|---|
| pick が候補①②③のいずれか **かつ** final text 非空 | **する** |
| 未選択 | しない |
| コメントを使用しない | しない |
| final text 空欄 | しない |

- **★おすすめからの補完禁止。候補元文章の直接使用禁止。**
- **候補選択後に人間が final を編集した場合は、編集後 final を掲載する。**

### 7. 「コメントを使用しない」の実UI仕様（2026-09-09 実UI確認で正式確認）

- 「コメントを使用しない」は**正常に選択可能**。
- 選択すると **pick = `コメントを使用しない` ／ final = `""`** になる。
  つまり**「final を内部に残したまま非掲載」ではなく、現在の正式実装では
  final text 自体を空文字へクリアする**（`_map[_ART_CMT_PICK_NONE] = ""`）。
  **これはバグではなく、確認済みの実挙動として記録する。**
- 掲載予定表示は **`掲載しない（「コメントを使用しない」を選択中）`**。
- **rerun 後も維持。日付切替→復帰でも復元。別日混入なし。**

### 8. WordPress本文挿入

- app 側で**送信直前**に現在Excelのコメント状態を取得し、logical comments を payload へ渡す。
- `wp_client.plan_blocks()` が**各論理セクション末尾に既存 para block を追加**する。
- **文章専用の独自HTMLを作らない。**経路は
  **`{"type":"para","text":…}` → `_split_para()` → `blk_para()` → `esc()`** を使う。

### 9. 挿入位置

| | 位置 |
|---|---|
| A | 全台系の**最後の画像の後に1回** |
| B | 高配分の**最後の画像の後に1回** |
| C | 並び・列の**最後の画像の後に1回** |
| D | **⑤全ブロックの最後に1回** |
| E | その他単品優秀台の **WordPress split 全 piece の最後に1回**（**piece 間には入れない**） |
| F | `ランキング → 全台データ conditional → 既存空段落 → 島図 → **Fコメント** → 店舗情報ボタン` |

- **F用の新しいH2を作らない。**
- **セクション自体が存在しない場合は、保存コメントだけを孤立掲載しない。**

### 10. E split との関係

`その他の優秀台ピックアップ.jpg` は **ローカル/preview は one-piece ／ WordPress は split 例外**。
**コメントロジックを split 層へ入れない。**logical image の後へ para を置くことで、
実HTMLでは**全 split piece 展開後に E コメントが1回だけ**出る。

### 11. 既存画像仕様の非回帰

コメント追加によって次を変更しない：
**fullwidth A-2a ／ nosplit ／ その他単品 split 例外 ／ Luminous ／ Gutenberg block markup ／
⑤画像 ／ ランキング ／ 全台データ ／ 島図。**

### 12. 高田馬場・秋葉原の非回帰

- **高田馬場はコメント機能の対象外。既存 body 完全一致。baseline `c35ac89ea13c` を維持。**
- **秋葉原は `_ART_COMMENT_STORES` 外。コメント非適用。**

### 13. 第2段階の pure / local test（実WordPress送信前）

```
test_wp2.py  202 PASS / 0 FAIL
test_d.py     98 PASS / 0 FAIL
test_cmt.py  173 PASS / 0 FAIL
```

- **コメントなし body は第1段階HEADと完全一致。**
- A〜F 全部掲載で**各1回**。
- **D は複数⑤ブロックでも最後に1回。**
- **E は 4 split piece の最後に1回。**
- **F は全台データ成立／不成立の両方で島図の後。**

### 14. 2026-09-09 実UI確認

対象：**渋谷新館 / 2026-09-05 / C 並び・列**。

```
候補① → final 手修正 → コメントを使用しない → rerun → 日付切替 → 復帰
```

**すべて PASS。**テスト用変更は終了後、**実UIから元の `選択してください` へ復元**した
（JSON直接編集なし）。**`[C-EDIT]` 等のテスト文字列の残存は0。**

### 15. 実WordPress下書きテスト

| 項目 | 値 |
|---|---|
| 実施日 | **2026-09-09** |
| 記事データ対象日 | **2026-09-06** |
| WordPress | **新規 draft 1件のみ** |
| post ID | **62525** |
| title | `9月6日(日)│エスパス渋谷新館│` |
| status | **draft** |
| category | **19** |
| author | **2**（m.takahashi） |

**draft 62525 は検証後も削除・編集していない。**

### 16. 実WordPress検証結果（GET `context=edit` で再取得して確認）

- **A〜F の 6/6 掲載。すべて保存済み final text と完全一致。各コメント1回だけ。**
- 挿入位置：**A＝全台系画像4枚後 ／ B＝高配分画像15枚後 ／ C＝並び画像14枚後 ／
  D＝⑤ブロック1・4・5の3枚すべての後 ／ E＝その他単品4分割の4枚目後（piece間コメント0） ／
  F＝ランキング→全台データ→空段落→島図→F→店舗情報ボタン。**
- **候補元文への巻き戻りなし。★おすすめ補完なし。**

### 17. WordPress画像／本文の非回帰（実draft 再取得で確認）

- **画像43ブロック。**
- **fullwidth A-2a：43枚すべて `"width":"100%"` ＋ `wp-block-image size-full is-resized` ＋
  `style="width:100%;height:auto"`。NG 0。**
- **Luminous：`linkDestination":"none"` ／ 画像の `<a href>` ラップ 0。**
- **その他単品：4分割正常。**
- H2順：**日曜日 → ななこ → 全台系 → 高配分 → 並び・列 → ⑤オススメ → その他単品 →
  差枚数ランキング&島図。**
- **店舗情報ボタンは本文最終ブロック。**
- **X埋め込み2件。`twitter.com` 正規化。`x.com` 0。**

### 18. 実プレビュー目視

| 項目 | 結果 |
|---|---|
| PC表示 | **確認済み** |
| コメント改行（1行＝1段落） | **確認済み** |
| 段落間隔 | **確認済み**（正常） |
| 画像→コメント間隔 | **確認済み**（正常） |
| コメント→次H2間隔 | **確認済み**（正常） |
| E位置 | **確認済み**（正常） |
| F位置 | **確認済み**（正常） |
| **Gutenberg編集画面での invalid block 目視** | **未確認** |
| **スマホ実表示** | **未確認** |

**上記2件を「正常」と推測して記録しないこと。**
ただし **Gutenberg markup は機械確認済み**（block属性・figure class・img style の正規形）。

### 19. ⑧正式経路

実テストは**記事用⑧を正式経路で実行**した。

- 2026/09/06 **確定データ433台** ／ 送信対象 **40枚 / 60.72 MB**
- ⑧末尾の **`_git_auto_push("画像生成")` も正式動作**
- 自動commit：**`988ea7b auto: 画像生成後の設定を保存`**
- **commit対象は `article_page_inputs.json` の1ファイルのみ。**
  **`wrt_machines.json` と未追跡ファイルは巻き込まれていない。**
- **この自動commitは正式⑧経路による正常動作**であり、事故ではない。

### 20. WordPress通信

実地テストで許可した書き込みは **新規 draft 62525 ＋ 必要な media upload のみ**。

- 既存公開記事の変更 **0**
- 既存記事の PUT / PATCH **0**
- 公開 **0** ／ 予約投稿 **0** ／ 記事削除 **0**
- **draft 62525 は現在も残している。**

### 21. 今後の禁止事項

1. **既存3節（第1段階・D⑤3候補・第2段階）を削除・圧縮・書き換えない**
2. **D を固定文方式へ戻さない／Dの母集団を⑤画像掲載 bans 以外から取らない**
3. **候補生成に random / LLM / 外部API を使わない**
4. **★おすすめを自動選択・既定値にしない／WordPressへ直接使わない**
5. **未選択／「コメントを使用しない」／final空 を掲載しない**
6. **「コメントを使用しない」で final がクリアされる実挙動を、今回を理由に仕様変更しない**
7. **候補元文章をWordPressへ直接使わない／編集後 final を候補本文へ戻さない**
8. **保存を12キー・日付スコープ以外へ変えない／新しいJSONを作らない／`skip_kojin=True` を外さない**
9. **文章専用の独自HTMLを作らない**（`para` → `_split_para` → `blk_para` → `esc` を維持）
10. **各H3ごとにコメントを入れない／Dをブロックごと・Eを piece ごとに入れない**
11. **Fを島図より前へ入れない／F用の新しいH2を作らない／空段落の位置・個数を変えない**
12. **セクション不在の日に孤立コメントを出さない**
13. **fullwidth A-2a / nosplit / split例外 / Luminous / Gutenberg markup / ⑤画像 /
    ランキング / 全台データ / 島図 を変更しない**
14. **高田馬場・秋葉原へコメントを適用しない／高田馬場の baseline `c35ac89ea13c` を壊さない**
15. **draft 62525 を削除・編集・公開しない**
16. **「スマホ実表示」「Gutenberg編集画面の目視」を確認済みと誤記しない**
17. **無関係なリファクタ・未使用コード整理をしない**

## 渋谷新館 記事用：⑥「全台データ」画像を見本デザインへ変更＋HQ化（2026-09-09・`205ce21`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】記事用⑥の `全台データ.jpg` の描画仕様だけ**。
正式コード commit は **`205ce21`**（`fix: 渋谷新館の全台データ画像を見本デザインへ変更しHQ化`・
**`streamlit_app.py` の1ファイルのみ**・+54／−23）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**

既存節「渋谷新館 記事用：⑥「全台データ」画像（2026-09-08）」および
「⑥「全台データ」画像の数値は結果テキストと共通処理（2026-09-08 追記）」は
**削除・書き換えしない**。本節は**描画仕様だけを supersede** し、**数値・生成条件は無変更**。

### ① 基準は `見本.png`（374×149）の実測値

デザインの正は**ユーザー提供の見本画像の実測ピクセル値**であり、旧デザイン
（濃紫帯＋白文字＋濃紺の数値＋2px 濃紫枠）は**採用しない**。

| 項目 | 値 |
|---|---|
| 論理キャンバス | **374 × 149**（H/W = 0.398） |
| 見出し帯 | y=1..36（36px）・**`(220,185,255)` 薄ラベンダー** |
| 見出し文字 | **`(112,48,160)` 紫**・**20pt** |
| 見出し下の罫線 | **y=37 に 1px `(128,128,128)`** |
| 本文背景 | **`(255,242,204)`** |
| ラベル／値の色 | **どちらも `(90,0,180)` 紫（色分けしない）** |
| ラベル | **20pt**・**X=5** |
| 値 | **22pt**・**X=88（全行固定）** |
| 本文行 | 上端 44 / 81 / 118（**ピッチ37**）・本文開始 y=38・行高37 |
| 外枠 | **1px `(128,128,128)` グレー** |
| フォント | **既存 `load_font()`＝`fonts/MochiyPopOne-Regular.ttf`**（見本と一致・外部フォント導入なし） |

**旧値（帯44 / 見出し30pt / ラベル28pt / 値32pt / PAD14 / GAP22 / 行高46 / 2px枠）へ戻さない。**

### ② HQ化（全要素を同じ倍率でスケール）

```python
_ART_ZENDAI_HQ = 2.0     # 既定。保存画像は 748 × 298
```

- **`_art_zendai_image(diff_raw, hq_scale=_ART_ZENDAI_HQ)` の既定値で倍率を与える。**
  ⑦プレビュー・⑧本番は**どちらも引数を渡さない**ので、**構造的に必ず同じ倍率**になる
  （片方だけ旧デザイン／別解像度になる余地がない）。
- 関数内の **`_sc(v) = max(1, round(v * _hq))`** で
  **フォント・座標・余白・行高・帯高・罫線・外枠のすべてを同じ倍率**にする。
  **キャンバスだけ2倍にしてフォント・座標を1倍のままにするのは禁止。**
- **完成画像を後から `resize` して拡大しない。**
- 目的は WordPress の fullwidth（本文幅約752px）で**拡大されないこと**。
  **`wp_client.py` の fullwidth A-2a / nosplit / Luminous は変更しない。**

### ③ 幅は「見本と同じ最小幅＋必要時のみ拡張」（案A-2）

```python
_val_x = max(_sc(_ART_ZENDAI_VAL_X), PAD + _lab_w + GAP)
_w = max(_sc(_ART_ZENDAI_MIN_W), _val_x + _val_w + PAD,
         PAD + _text_w(_d0, _ART_ZENDAI_TITLE, FN_TITLE) + PAD)
```

- **通常ケースは見本と同じ幅**（論理374／HQ748）＝**右側に余裕のある見た目を再現**。
- **374px を絶対固定幅にして長い値を切る実装にしない。**内容が長い場合だけ必要分だけ広げる。
- 値のXは**見本どおり固定**（論理88）。ラベルが長い場合だけ右へずらしてラベルとの重なりを防ぐ。
- **長い値のためにフォントを縮小する処理は導入しない**（`_build_machine_img` の縮小ループは使わない）。

### ④ 数値ロジックは完全に無変更

**`_zendai_diff_list()` / `_zendai_total_stat()` / `_art_zendai_stat()` /
`generate_report_text()` / `_pipeline_calc_d()` / `_stat_from_diff()` /
`_ART_ZENDAI_MIN_AVG = 50` / `_ART_ZENDAI_STORES` / `_ART_ZENDAI_FN` / `_ART_ZENDAI_TITLE`
はバイト一致で無変更。**

**本体が変わった関数は `_art_zendai_image()` の1つだけ**（新規は関数内ヘルパー `_sc` のみ・消失0）。
勝率・総差枚・平均・母数・補正処理・+50判定・生成条件は**一切変更していない**。

### ⑤ 実測比較（見本 / 修正後 論理1.0倍 / 修正後 HQ2.0倍）

| 項目 | 見本 | 修正後 論理1x | 修正後 HQ2x |
|---|---|---|---|
| サイズ | 374×149 | **374×149** | **748×298** |
| 帯下端 / 罫線 | 36 / y=37 | 36 / y=37 | 73 / y=74-75 |
| 見出し文字 | x5-102 y8-27 | x6-102 y9-28 | x10-205 y18-56 |
| 行 上端 | 44 / 81 / 118 | **46 / 82 / 119** | 90 / 164 / 239 |
| 行ピッチ | 37 / 37 | 36 / 37 | 74 / 75 |
| 右余白 | 55 | **54** | 113 |
| 下余白 | 10 | **9** | 17 |
| 枠色 / 帯色 / 本文背景 | (128,128,128) / (220,185,255) / (255,242,204) | **同一** | **同一** |

**差は最大2px。**（変更前は 468×196・帯44・見出し文字高29・行ピッチ46・左余白14・値X121・
下余白22・帯 `(147,39,143)`＋白文字・値 `(26,26,92)`・枠2px。）

### ⑥ 長い数値のテスト（48通り・全PASS）

勝率 `46.2% (200/433台)` / `9.9% (1/10台)` / `100.0% (433/433台)` ×
総差枚 `+5,000枚` / `+82,900枚` / `+123,450枚` / `-10,000枚` ×
平均 `+50枚` / `+191枚` / `+1,000枚` / `-100枚` の**全48組み合わせ**で：

**文字切れ0 ／ 右端はみ出し0 ／ ラベルと値の重なり0 ／ 全ケース 748×298**（見本と同じ幅）。
右の余り（論理換算）は 39.5〜124px で、最も長い `100.0% (433/433台)` でも余裕がある。

### ⑦ 実UI確認（2026-09-09・ローカル・正式HEAD `205ce21`・⑦プレビュー）

| 日付 | 表示値 | 画像 |
|---|---|---|
| **2026/09/06** | 勝率 43.2% (187/433台) ／ 総差枚 **+51,400枚** ／ 平均 **+119枚** | **748×298** |
| **2026/09/05** | 勝率 46.2% (200/433台) ／ 総差枚 **+82,950枚** ／ 平均 **+192枚** | **748×298** |

**どちらも従来の記録値と完全一致**（9/6 は記事コメントFの「総差枚+51,400枚、平均差枚+119枚」と一致）。
見本準拠の配色・文字サイズ・文字位置・余白・右余白・罫線を目視確認済み。
**⑧本番は実行していない**（`_git_auto_push` による `article_page_inputs.json` の自動commitを避けるため）。
**WordPress 通信は0件。draft 62525 は未参照・未変更。**

### ⑧ 影響範囲

**渋谷新館 記事用⑥の `全台データ.jpg` だけ。**
高田馬場・秋葉原（`_ART_ZENDAI_STORES` 外で画像自体を生成しない）／通常ページ／ローテ／
結果テキスト／⑤オススメ／差枚数ランキング／島図／その他単品／WordPress本文構成は**すべて無変更**。
色定数 `_ART_ZENDAI_*` は**この関数だけが参照**しており、他店舗・他画像へ波及しない。

### ⑨ 今後の禁止事項

1. **旧デザイン（濃紫帯＋白文字＋濃紺の数値＋2px 濃紫枠）へ戻さない**
2. **ラベルと値を色分けしない**（どちらも `(90,0,180)`）
3. **見出し下の 1px グレー罫線を消さない**
4. **論理レイアウト（374×149 / 帯36 / 罫線1 / 行高37 / ラベルX5 / 値X88 / PAD5 / GAP23 /
   20・20・22pt）を理由なく変更しない**
5. **`_ART_ZENDAI_HQ = 2.0` を 1.0 へ戻さない／キャンバスだけ2倍にしない／後から resize しない**
6. **`hq_scale` を⑦と⑧で別々に渡さない**（既定値で共有し、必ず同じ倍率にする）
7. **374px を絶対固定幅にして長い値を切らない／長い値でフォントを縮めない**
8. **値のX固定（論理88）とラベル長時のずらしを外さない**
9. **`_zendai_diff_list` / `_zendai_total_stat` / `_art_zendai_stat` / `generate_report_text` /
   `_pipeline_calc_d` / `_ART_ZENDAI_MIN_AVG` / 生成条件 を変更しない**
10. **`wp_client.py` の fullwidth A-2a / nosplit / Luminous を変更しない**
11. **他店舗・他画像へこの配色や定数を流用しない**
12. **外部フォントを導入しない**（`load_font()`＝MochiyPopOne で見本を再現できる）
13. **無関係なリファクタ・未使用コード整理をしない**

## Streamlit Cloud 起動障害：`packages.txt` 削除で復旧（2026-09-09・`625d29b`）

**正式記録。巻き戻し禁止。**対象は**Streamlit Cloud の起動（APT依存処理）だけ**。
正式コード commit は **`625d29b`**（`fix: 不要なAPT依存を削除してCloud起動エラーを回避`・
**`packages.txt` の削除のみ**・15行削除／追加0）。
**`streamlit_app.py` / `requirements.txt` / `runtime.txt` / その他コードは今回いっさい変更していない。**

### ① 障害内容

2026-09-09、Streamlit Cloud でアプリが起動しなくなった。
**`streamlit_app.py` の実行前**、**APT依存関係のインストール段階**で停止していた。

```
Processing dependencies...
Apt dependencies were installed from /mount/src/guild-image-app/packages.txt using apt-get.
E: Release file for http://deb.debian.org/debian-security/dists/bullseye-security/InRelease
   is expired (invalid since 1d ...)
   Updates for this repository will not be applied.
installer returned a non-zero exit code
Error during processing dependencies!
```

`apt-get install` ではなく **`apt-get update` の段階**で失敗している。
`bullseye-security` は **Debian 11 のセキュリティリポジトリ**で、Debian 11 の EOL に伴い
**Release ファイルの有効期限（Valid-Until）が切れた**ことによる。
ログには `Debian trixie`（Debian 13）・`bullseye-security`（Debian 11）・
`packages.microsoft.com/debian/11/prod` が同時に見えるが、これらは
**Streamlit Cloud のベースイメージ側が持つリポジトリ定義**であり、**当リポジトリの
`packages.txt` の内容（パッケージ名）が原因ではない**。
ただし **`packages.txt` が存在すると Cloud が APT 処理（update → install）を実行する**ため、
**ファイルの存在自体がトリガー**になっていた。

### ② `packages.txt` は旧 Playwright/Chromium 用で現在不要

削除した15項目は**すべて Playwright/Chromium のシステム依存ライブラリ**だった。

```
libnss3 / libnspr4 / libatk1.0-0 / libatk-bridge2.0-0 / libcups2 / libdrm2 /
libxkbcommon0 / libxcomposite1 / libxdamage1 / libxfixes3 / libxrandr2 /
libgbm1 / libasound2 / libpango-1.0-0 / libcairo2
```

**現在の Cloud 実行経路では1つも必要ないことを削除前に確認した。**

| 確認項目 | 結果 |
|---|---|
| `requirements.txt` の playwright / selenium / chromium / imgkit / dataframe_image / weasyprint / cairosvg / pyppeteer / kaleido | **0件**（Cloud にインストールされない） |
| Cloud実行経路（`streamlit_app.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` / `wp_client.py`）のトップレベル import | **0件** |
| 実 import が残るファイル | `convert_20260408.py` / `convert_narabi_稲毛_20260415.py` / `fix_title_spaces.py` ＝ **旧スクリプトで Cloud では起動されない** |
| 並び・列画像 | **全13店舗が `convert_narabi_pil.py`**（`_NARABI_GENERIC`）。import は pandas / os / io / collections / PIL のみ＝**ブラウザ不使用** |
| `streamlit_app.py` の imgkit パッチ | `try: import imgkit, dataframe_image / except: pass` の**文字列**。未インストールなので常に握り潰され無効 |
| `_draw_weekly_table_image` の「Playwright実装に委譲」コメント | **記述が古いだけ**。委譲先 `_weekly_table_html_image()` は docstring どおり **PIL 実装（Playwright不使用・Cloud/ローカル共通版）** |
| フォント | `fonts/MochiyPopOne-Regular.ttf` / `NotoSansJP-Regular.ttf` を**リポジトリ同梱**で使用（APTのフォントパッケージに依存しない） |

`packages.txt` の最終変更は **`e34562e`（2026-06-04）**で、直前の
`205ce21` / `1b43288` / `f0762e7` / `988ea7b` は**いずれも Cloud 起動関連ファイルを触っていない**。
＝**「今日から急に起動しなくなった」のは外部要因（Debian 11 security の期限切れ）のタイミング。**

### ③ 対処＝`packages.txt` を削除して APT 処理自体を発生させない

- **`packages.txt` を削除**すると Cloud は APT 段階を実行しないため、この経路の失敗を回避できる。
- **`streamlit_app.py` をこの起動障害のために変更しない**（実際に変更していない）。
- **APT の workaround（sources.list 書き換え・`--allow-releaseinfo-change` 等）は追加しない。**
- ローカル起動は `packages.txt` を参照しないため**影響なし**。

### ④ 確認できた事実（誤記しないこと）

- **`packages.txt` 削除後、ユーザーが Streamlit Cloud のアプリを実際に開き、
  正常起動・アプリ画面の表示を確認した。これが正式に確認できた事実である。**
- **★Cloud ログ上で「APT処理が消えたこと」自体は Claude 側では直接確認していない。**
  リポジトリに Cloud アプリの URL が記録されておらず、`share.streamlit.io` は
  アカウント設定フォームを表示したため（アカウント作成・フォーム送信は行わない方針）
  コンソール・ログへ到達できなかった。
  **「Cloudログで APT 処理の消滅を確認済み」とは書かない。**

### ⑤ 今後の禁止事項

1. **`packages.txt` を理由なく復活させない**（存在するだけで Cloud の APT 処理が走る）
2. **APT の workaround を勝手に追加しない**
3. **この起動障害を理由に `streamlit_app.py` / `requirements.txt` / `runtime.txt` を変更しない**
4. **並び・列画像を browser 方式（Playwright / selenium / imgkit / dataframe_image）へ戻さない**
   （現在は `convert_narabi_pil.py` の PIL 実装）
5. **将来 Playwright/Chromium 等のブラウザ系処理を Cloud へ再導入する場合は、
   `requirements.txt` への追加と APT システム依存（`packages.txt`）を改めてセットで設計する。**
   その際は Cloud ベースイメージの Debian バージョンに合うパッケージ名かを必ず確認する
   （過去に `chromium-browser` / `wkhtmltopdf` が Debian trixie に存在せず失敗した事例あり＝`e34562e`）
6. **ログに `bullseye-security` / `packages.microsoft.com/debian/11/prod` が出ても、
   当リポジトリのファイルが原因と即断しない**（Cloud ベースイメージ側の定義）

## 渋谷新館 WordPress：全台データ33%幅・左詰め＋まとめコメントFを島図の前へ（2026-09-09・`0583161` / `38a1b61`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】の記事用WordPress本文だけ**。
正式コード commit は **`0583161`**（`fix: 全台データを1/3幅にしまとめコメントFを島図の前へ移動`）＋
**`38a1b61`**（`fix: 全台データ画像をWordPressで左詰め表示`）。
**どちらも `wp_client.py` の1ファイルのみ。`streamlit_app.py` は無変更。**

### ① 全台データだけ本文幅の約1/3・左詰め

```python
FN_ZENDAI            = "全台データ.jpg"
WP_THIRD_WIDTH       = "33%"
WP_THIRD_WIDTH_FILES = frozenset({FN_ZENDAI})
WP_LEFT_ALIGN_CLASS  = "has-text-align-left"
def img_width_css(fn): return WP_THIRD_WIDTH if fn in WP_THIRD_WIDTH_FILES else "100%"
```

- **`全台データ.jpg` だけ**が 33%。他（全台系・高配分・並び・列・⑤オススメ・その他単品・
  ランキング・島図）は**従来どおり fullwidth 100%**。
- **`_ART_WP_FULLWIDTH_STORES = {"渋谷新館"}` は変更しない。**例外は**ファイル名1件だけ**の狭いスコープ。
- **px 固定ではなく `%`**：本文幅が変わっても常に約1/3で、スマホでも親の33%に収まる。
- **元画像 748×298（HQ2.0・論理374×149）は変更しない。**
  `_art_zendai_image()` / ⑦プレビュー / ZIP も無変更。**WordPress の表示幅だけの仕様。**

### ② 左詰めは `className:"has-text-align-left"` で行う（実測で確定）

**初回実装（`0583161`）では中央寄せになった。**原因は SWELL テーマの
```css
/* main.css?ver=2.12.0 */
.wp-block-image { text-align: center; }      /* 特異度 0,1,0 */
```
で、**align クラスの無い画像ブロックはテーマが中央寄せする**（実測 left_offset 268px）。
WordPress コアは中央寄せしないため「align 無し＝左詰め」という想定が**このテーマでは成立しない**。

**`"align":"left"` は採用しない。**実測では
```
+ alignleft → float:left になるが textAlign は center のまま → left_offset 267px（左詰めにならない）
```
＝**目的を達成せず float の副作用だけ増える**。**この事実を忘れて再導入しない。**

正式解は WordPress コアのグローバルスタイル
```css
:root .has-text-align-left { text-align: left; }   /* 特異度 0,2,0 → SWELL に勝つ */
```
を **`className`（core/image の customClassName サポート＝正式なブロック属性）**で付ける方法。
**float は発生しない。**

- **figure への直接 `style` / img への `margin-right:auto` は使わない**
  （ブロック属性から再生成されない形＝A-1 と同種の invalid block リスク）。
- **テーマCSSの変更・画像への余白追加・空段落による clear もしない。**
- className は**既存トークンを消さずに合成**する（分割画像の `SPLIT_JOIN_CLASS` と併用可）。
  `join=True` かつ 100% のときの出力は**旧実装とバイト一致**。

正式な出力形（A-2a の3点セットは維持し、**値だけ 100% → 33%**）:

```html
<!-- wp:image {"id":N,"width":"33%","sizeSlug":"full","linkDestination":"none","className":"has-text-align-left"} -->
<figure class="wp-block-image size-full is-resized has-text-align-left"><img src="…" alt="" class="wp-image-N" style="width:33%;height:auto"/></figure>
<!-- /wp:image -->
```

### ③ 最終H2の正式順序（旧 blank×5 は廃止）

```
H2 差枚数ランキング&島図
  → 差枚数ランキング
  → 全台データ（条件成立時）
  → まとめコメントF
  → 島図
→ 店舗情報ボタン
```

- **`RANK_SHIMAZU_GAP_PARAS = 5` の空段落は完全に廃止した。**
  あれは将来ここへFを入れるための場所取りで、Fを入れた時点で役割が終わった。
  **復活させない。**定数定義だけ履歴として残置（未使用）。
- 全台データ↔F、F↔島図の間に**意図的な空段落を入れない**。
- **Fは島図の下に残さない。** F用の新しいH2も作らない。
- Fが無い日（未選択／「コメントを使用しない」／final空）は
  `ランキング →（全台データ）→ 島図` と自然に詰まる（孤立ブロックなし）。
- 全台データが無い日（平均+50枚未満）は `ランキング →（F）→ 島図`。
- **コメントA〜Eの位置・内容・条件、および候補生成・選択・保存・日付スコープの
  ロジックは変更していない**（`_comment_paras` はバイト一致）。変えたのは**Fの挿入位置だけ**。

### ④ 実WordPress検証（2026-09-09・draft 62659）

| 項目 | 値 |
|---|---|
| post ID | **62659** ／ status `draft` ／ category `[19]` ／ author `2`（m.takahashi） |
| タイトル | `9月6日(日)│エスパス渋谷新館│`（2026/09/06・433台） |
| 送信 | 40枚 / 60.75 MB → media 43枚 |

**PC実表示（SWELL適用後DOM）**

```
本文カラム 784px ／ 全台データ 248×99px ＝ 31.7%
left_offset 16px（＝コメントFの左端と完全一致）
figure textAlign: left ／ float: none ／ img float: none
naturalWidth/Height = 748×298（縮小保存されていない）
縦横比OK ／ はみ出しなし ／ F回り込みなし ／ 島図回り込みなし
```

**スマホ実表示**（同一オリジンの414px iframe に実ページを読み込み、実CSS適用下で測定）

```
viewport 410px ／ 本文カラム 354px ／ 全台データ 117×47px ＝ 33.0%
left_offset 0px（＝本文左端）／ textAlign: left ／ float: none
縦横比OK ／ はみ出しなし ／ 横スクロールなし ／ F・島図とも回り込みなし
```

**本文HTML（GET `context=edit` 実測）**

```
画像43ブロック ／ 33%:1 ／ 100%:42
has-text-align-left の出現 2回（ブロック属性＋figure のみ＝正）
align系クラス 0 ／ A-2a 3点セットNG 0
linkDestination:"none" 43件 ／ 画像の <a href> ラップ 0（Luminous維持・data-luminous あり）
SPLIT_JOIN_CLASS 6件（その他優秀台の分割・非回帰）
空段落 0
最終H2以降: H2 → IMG(100%) → IMG(33%) → P → P → IMG(100%) → BTN
```

**Fコメント**：保存済み final の各行の出現回数は **1 / 1**。
**`P → P` は final 内の改行による2段落で、重複挿入ではない。**

**Gutenberg編集画面**（実際に開いて確認）

```
総ブロック 114 ／ core/image 43 ／ invalid ブロック 0
「想定されていないか無効なコンテンツ」「ブロックの復旧を試行」等の警告文言 0
全台データブロック: name=core/image / isValid=true / width="33%"
                    className="has-text-align-left" / sizeSlug="full"
                    linkDestination="none" / align=undefined
前後: core/image → core/image → core/paragraph(F) → core/paragraph(F) → core/image(島図)
```

**高田馬場**：`plan_blocks` / `build_content` とも旧実装と**完全一致**（`width` / `is-resized` /
`style="width` の混入 0）。秋葉原も `_ART_WP_FULLWIDTH_STORES` 外で不変。

**既存 draft 62525 / 62615 は未編集・未削除・未公開。**（62615 は調査時にブラウザDOM上で
クラスを一時付与して計測したが、WordPress のデータは変更していない。）

### ⑤ 今後の禁止事項

1. **`"align":"left"` / `alignleft` を使わない**（実測で左詰めにならず float の害だけ）
2. **`has-text-align-left` を外さない**（外すと SWELL の `.wp-block-image{text-align:center}` で中央寄せへ戻る）
3. **figure への直接 `style` / img への `margin-right:auto` を使わない**（invalid block リスク）
4. **テーマCSSを変更しない／画像へ余白を足さない／空段落で clear しない**
5. **A-2a の3点セット（属性 width・figure `is-resized`・img `style`）を崩さない／値を食い違わせない**
6. **`className` の既存トークン（`SPLIT_JOIN_CLASS`）を上書き・消失させない**
7. **33% を他の画像へ広げない**／`_ART_WP_FULLWIDTH_STORES` を変更しない
8. **元画像 748×298 / HQ2.0 / 論理374×149 / `_art_zendai_image()` / ⑦プレビュー / ZIP を変更しない**
9. **Fの位置（全台データの直後・島図の前）を戻さない／島図の下へ置かない**
10. **旧 blank×5（`RANK_SHIMAZU_GAP_PARAS`）を復活させない**
11. **コメントA〜Fの生成・選択・保存・日付スコープのロジックを変更しない**
12. **高田馬場・秋葉原へ 33% や `has-text-align-left` を混入させない**
13. **draft 62525 / 62615 / 62659 を公開・編集・削除しない**
14. **無関係なリファクタ・未使用コード整理をしない**

## 新小岩スランプ付き：結果テキストの⑤4カテゴリ優先表示（2026-09-09・`252a39b`）

**正式仕様。巻き戻し禁止。**対象は**【新小岩】スランプ付き結果ポスト用の⑧本番で出力する
結果テキストだけ**。正式コード commit は **`252a39b`**
（`feat: 新小岩の結果テキストで⑤4カテゴリ所属機種のサマリーをカテゴリ内へ表示`・
**`streamlit_app.py` の1ファイルのみ**）。
**`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は diff 0。**
既存節は削除・圧縮・統合・並べ替えしない。

### ① 正式仕様

⑤オススメ機種ピックアップの **B1〜B4** に登録された機種が
**全台系**または**高配分**にも該当した場合、そのサマリーは下部の
`🍀全台系濃厚機種` / `🍀高配分機種` ではなく、**所属するカテゴリ内**に表示する。

| ブロック | `store_settings/新小岩.json` の title |
|---|---|
| B1 | その他の毎日オススメ機種の優秀台 |
| B2 | その他の主役機種の優秀台 |
| B3 | その他のジャグラーシリーズの優秀台 |
| B4 | その他の沖スロ系の機種の優秀台 |

### ② ★変更したのは「判定」ではなく「表示場所」だけ（最重要）

- **全台系・高配分の判定ロジックは一切変更していない。**
  `run_auto_pipeline` / `run_step1_main` / `run_step2_juggler` / `run_step3_other` /
  `filter_recommended_machines` / `_kojin_yushu_filter` は**ASTバイト一致**。
  全台系⇔高配分の既存相互排他（`run_step3_other` の `all_plus` 分岐）も不変。
- **`zen_dai_list` / `high_ratio_list` / `excellent_list` を加工・削除しない。**
  カテゴリへ移した機種も**リスト本体には残したまま**。
- 下部セクションの重複表示は、`generate_report_text()` に追加した
  **`hide_summary_names`（表示抑止専用の引数）**で `zen_dai_section()` /
  `high_ratio_section()` の**描画ループだけ**を skip して行う。
- **`hide_summary_names` を `_demoted_names` / `_zen_dai_names` / `high_ratio_names` /
  `excellent_section()` などの判定へ流用してはならない。**

### ③ カテゴリ内の正式構成

対象サマリーがあるカテゴリ：

```
🍀カテゴリ見出し
全台系/高配分サマリー
（空行）
🎁カテゴリの優秀台
従来の優秀台一覧
```

**対象サマリーが0件のカテゴリは、従来出力を1文字も変更しない**
（`🎁` 見出しも出さない）。

### ④ 優秀台一覧は残す（二段構成が正式）

カテゴリ上部へサマリーを移した機種も、**`🎁カテゴリの優秀台` 以下の台番一覧には
従来どおり残す**。

```
🎖️北斗転生2(5/10台)→平均+930枚      ← カテゴリ上部サマリー
🌋+5,650枚、+3,500枚、+1,100枚

🎁その他の毎日オススメ機種の優秀台
🎖️北斗転生2                          ← 同じ機種の台番一覧も残す
【2220番台】+3,500枚
【2224番台】+5,650枚
【2227番台】+1,100枚
```

**排除するのは「カテゴリ内サマリー ＋ 下部の全台系/高配分」の二重掲載だけ。**
**「カテゴリ内サマリー ＋ 同カテゴリ内の優秀台一覧」は意図した正式仕様なので排除しない。**

### ⑤ その他の優秀台への漏れ出し防止

`excellent_section()` は `high_ratio_names`（＝`high_ratio_list` の name − demoted）で
除外しているため、**`high_ratio_list` から機種を削ると `🍀その他の優秀台` へ漏れ出す**。
今回は**リストを加工せず表示だけ抑止**しているので、この経路は構造的に発生しない。

**2026/09/08 実データで、`🍀その他の優秀台` の13行が修正前後で文字列完全一致**することを確認済み
（移動5機種の台の漏れ出し0）。

### ⑥ 共通サマリーフォーマッタ（新しい書式を作らない）

```python
def _result_summary_lines(item, avg, avg_show_thr=0) -> list[str]
```

- **従来の全台系 / 従来の高配分 / カテゴリへ移動するサマリー の3者が共用**する。
- `🎖️{機種名}({count}/{total}台)` ／ `→平均±○枚`（平均>0 または `always_show_avg` のときだけ）／
  `🌋`（最大 >= 4,000枚）or `💎` ／ `_format_diffs()` の `×N` 圧縮・4件折り返し
  — **すべて既存書式のまま。**
- `_high_avg_of()` … 既存 `high_ratio_section` と同じ平均の取り方の切り出し。
- `_demoted_high_names(store, high_ratio_list)` … 既存の(1/2台)降格判定の切り出し
  （**条件は不変**・稲毛は空を返す）。
- **いずれも判定条件の変更ではない。新しい独自書式を作らない。**

### ⑦ カテゴリへの振り分け

```python
def _rec_category_summaries(recommended_blocks, zen_dai_list, high_ratio_list,
                            demoted_names=None) -> (dict[int, list[str]], set[str])
```

- **新しい全台系/高配分判定は一切しない。**既存 `zen_dai_list` / `high_ratio_list` の項目を
  **既存の並び順**（全台系→高配分の順、各 `all_avg_diff` 降順）のまま振り分けるだけ。
- 照合は **`機種名変換.xlsx` 適用後の正式名同士の完全一致**。
  **`startswith` / `contains` / 部分一致 / 新規別名辞書は禁止。**
  `STORE_REC_CONFIG["新小岩"]["block_header_names"]`（スマスロ北斗・ヴヴヴ2 等）は
  **見出しカッコ内の表示専用**で照合に使わない。
- 第2戻り値が `hide_summary_names` へ渡す「表示抑止する機種名」。

### ⑧ カテゴリ重複の正式扱い（排他化しない）

- B1〜B4へ同一機種を複数登録することを**コード上は禁止していない**。
- **`B1 > B2 > B3 > B4` / 最小index優先 のような新しい排他的優先順位は追加していない。**
- 同一機種が複数ブロックに登録されている場合は、**該当するすべてのブロックへ
  サマリーを表示する**（既存⑤表示の挙動と整合）。
  **今回の変更を理由に既存⑤表示を勝手に排他化しない。**
- 人工テストで「2ブロック登録 → 両方に表示」を確認済み。
- 2026/09/08 の実設定は **26機種すべてユニーク・重複0件**。

### ⑨ 2026/09/08 実データの正式結果

| ブロック | 移動したサマリー |
|---|---|
| **B1 毎日オススメ** | `🎖️北斗転生2(5/10台)→平均+930枚` ／ `🌋+5,650枚、+3,500枚、+1,100枚` |
| **B2 主役** | `🎖️真打吉宗(6/10台)→平均+420枚` ／ `🌋+4,500枚、+2,000枚×2、+1,700枚` |
| **B3 ジャグラー** | `🎖️ネオアイム(14/38台)` ／ `💎+1,900枚、+1,700枚、+1,200枚×2、+1,100枚` |
| **B4 沖スロ** | `🎖️チバリヨ2(2/3台)→平均+1,100枚` ／ `💎+2,450枚、+1,200枚`<br>`🎖️沖ドキゴージャス30(6/10台)→平均+445枚` ／ `💎+3,000枚、+1,800枚、+1,500枚×2` |

**上記5機種は下部の高配分から表示抑止。**

```
🍀全台系濃厚機種
（なし）

🍀高配分機種
新ハナビ / 戦コレ6 / L攻殻機動隊 / やじきた / 戦国乙女5   ← この5機種のみ
```

B4 の順序（チバリヨ2 → 沖ドキゴージャス30）は**既存の平均差枚降順**のまま。

### ⑩ スコープ

**新小岩 ＋ スランプ付き結果ポスト用 ＋ ⑧本番の結果テキスト だけ。**
適用条件は **`_rec_ban_level`（＝`with_slump and store == "新小岩"`）かつ
`recommended_blocks` あり**の経路。呼び出しは `show_auto_page()` の⑧本番**1か所だけ**。

**非対象**：📝記入部分のみ（`generate_report_text` の別呼び出し）／記事用／他店舗／
**西武新宿**／WordPress／画像生成／スランプ／パネル／液晶／ZIP／②個別画像／⑤画像／末尾。

### ⑪ 変更範囲

| 区分 | 関数 |
|---|---|
| 新規4 | `_demoted_high_names` / `_result_summary_lines` / `_high_avg_of` / `_rec_category_summaries` |
| 変更 | `generate_report_text`（内部 `zen_dai_section` / `high_ratio_section` 含む）／`generate_recommended_result_text`／`show_auto_page` |
| 消失 | **0** |

追加引数は **`generate_report_text(..., hide_summary_names=None)`** と
**`generate_recommended_result_text(..., block_summaries=None)`** の2つだけで、
**既定値では従来と完全に同一の出力**になる。

### ⑫ テスト結果（66 PASS / 0 FAIL）

保存済みの 2026/09/08 実出力（`0908_結果.txt`）から実データを再構成して検証。

新引数未指定で HEAD版(`eb68c1a`)と**最終テキスト完全一致** ／ 9/8移動5機種 ／
下部高配分の残存5機種 ／ 全台系（なし）／ カテゴリ内優秀台一覧の維持 ／
**その他の優秀台13行の完全一致** ／ `high_ratio_list` / `zen_dai_list` / `excellent_list` 非改変 ／
カテゴリ0件時の従来出力一致 ／ **複数カテゴリ登録時は両方表示** ／
全台系対象・高配分対象の人工ケース ／ 西武新宿・稲毛・渋谷新館・高田馬場の非回帰 ／
📝・記事用・画像生成系のASTバイト一致 ／ `import streamlit_app` returncode 0。

**HEAD版との比較は必ずプロジェクトと同一ディレクトリへ一時コピーして行い、比較後に削除する**
（`BASE_DIR` がずれると `store_settings` / `機種名変換.xlsx` を読めず誤検知する）。

### ⑬ 実機⑧は実行していない（誤記しないこと）

**⑧「自動処理を開始」は実行していない。**保存済み9/8実データの再現テストで足りたため、
`_git_auto_push()` による自動commitを発生させていない。
**「⑧本番の実出力で確認した」とは書かない。**

### ⑭ 今後の禁止事項

1. **`zen_dai_list` / `high_ratio_list` / `excellent_list` を加工・削除しない**
   （`high_ratio_names` が変わり `🍀その他の優秀台` へ漏れ出す）
2. **`hide_summary_names` を表示以外の判定へ流用しない**
3. **全台系・高配分の判定条件／相互排他／pipeline を変更しない**
4. **カテゴリ内サマリーと同カテゴリ内の優秀台一覧を「重複」として片方消さない**
5. **`🎁{title}` の二段構成を崩さない／サマリー0件ブロックの従来出力を変えない**
6. **`B1 > B2 > B3 > B4` などの新しい排他的優先順位を追加しない**
   （複数登録時は該当全ブロックへ表示する）
7. **照合を部分一致・別名辞書へ変えない**（正式名の完全一致のみ）
8. **`_result_summary_lines()` と別に独自のサマリー書式を作らない**
9. **`block_header_names` を照合に使わない**（表示専用）
10. **新引数の既定値を変えない**（他経路の非回帰が壊れる）
11. **📝・記事用・他店舗・西武新宿・WordPress・画像生成系へ波及させない**
12. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】非記事用・全店舗の表画像デザイン（2026-09-10・`a05cb00`）

**正式仕様。巻き戻し禁止。**対象は**記事用（`auto_article`）以外の表画像を生成する全店舗・全ページ**。
稲毛で実装・実画面確認したうえで全店舗へ横展開し、**横展開後もユーザーが実画面を確認して
「問題ないです」と最終承認済み**。以後これを現行の正式デザインとして扱う。

### ⓪ 確定までのcommit履歴

| commit | 内容 |
|---|---|
| **`2a0ab80`** | `feat: 稲毛の結果ポスト系表画像を新デザインへ`（タイトル #8100FF・見出し #290068＋白文字・サマリー #FF6FA5） |
| **`2a31721`** | `fix: 稲毛のタイトルバーを #8100FF から #7000E0 へ`（明るすぎたため濃くした） |
| **`121f1f7`** | `feat: 稲毛の表画像から赤ラインを削除し通常文字を #4B0082 へ` |
| **`a05cb00`** | `feat: 新デザインの表画像を記事用以外の全店舗へ横展開`（**今回の正式基準HEAD**） |

**`7497c43`（`auto: 画像生成後の設定を保存`）は `auto_page_inputs.json` を94行追加しただけの
アプリ自動commit**であり、**表画像デザインの実装commitではない**。履歴を混同しないこと。

### ① 正式配色

| 要素 | 値 |
|---|---|
| **タイトルバー背景** | **#7000E0** RGB(112, 0, 224) |
| **タイトルバー文字** | **#FFFFFF** |
| **タイトルバー直下** | **赤線なし。赤線用の6px余白も残さない** |
| **列見出しバー背景** | **#290068** RGB(41, 0, 104) |
| **列見出しバー文字** | **#FFFFFF** |
| **白地データ行の通常文字** | **#4B0082** RGB(75, 0, 130) |
| **差枚数** | **既存の条件付き色を維持**（プラス `C_PLUS`=#0000CC 青／マイナス `C_MINUS`=#CC0000 赤／±0 `C_ZERO` 黒） |
| **下段サマリーバー背景** | **#FF6FA5** RGB(255, 111, 165) |
| **下段サマリーバー文字** | **黒 RGB(0,0,0)** |

通常文字の対象は **台番・機種名・ゲーム数・BIG・REG・AT・合算確率**など、
`draw_table_image()` のデータ行ループで通常色として描かれる全セル。
**列ごとのハードコードはしない**（ループ直前で `_data_fg` を1回解決するだけ）。

### ② ★通常文字色と条件付き色は必ず分離する

**通常文字を #4B0082 にするために `C_ZERO` そのものを変更してはならない。**
`C_ZERO` は差枚±0の条件色としても使われるため、変更すると既存の条件付き色ロジックが壊れる。

```python
C_NEW_DATA_FG = "#4B0082"     # 通常セル専用（新設）
...
_data_fg = C_NEW_DATA_FG if _table_theme_new() else C_ZERO   # データ行ループの直前で1回
...
if diff_col_idx is not None and ci == diff_col_idx:
    color = C_PLUS if v > 0 else (C_MINUS if v < 0 else C_ZERO)   # ← 差枚列は無変更
else:
    draw.text((tx, ty_c), cell, fill=_data_fg, font=fn_data)      # ← 通常セルのみ
```

**既存の `C_TITLE_BG` / `C_MACH_HEADER_BG` / `C_MACH_HEADER_FG` / `C_HEADER_BG` /
`C_SUMMARY_BG_RGBA` / `C_REDLINE` / `REDLINE_H` は1つも書き換えない**
（記事用・⑥個別生成ページが従来色のままである根拠）。

### ③ 対象ページ

```python
_TABLE_THEME_PAGES: frozenset[str] = frozenset({"auto", "auto_slump", "work"})
```

| page | 内容 | 判定 |
|---|---|---|
| **`auto`** | 結果ポスト用 | **対象** |
| **`auto_slump`** | スランプ付き結果ポスト用（新宿歌舞伎町かぶぱ・秋葉原を含む） | **対象** |
| **`work`** | ⑥「個別に生成する場合は以下から選択」（全台データ画像・高配分データ画像・並び画像・末尾画像・その他の優秀台画像） | **対象** |
| **`auto_article`** | 記事用 | **対象外（従来デザイン）** |
| **`rote`** | ローテ・週間/月間オススメ表 | **対象外**（独自レンダラー・独自配色） |
| `weekly_result_text` / `name_conversion` / `slump_graph` / `machine_image` / `store` / `image_type` | 表画像なし | 対象外 |

### ④ 対象店舗＝`STORES` から自動導出

```python
_TABLE_THEME_STORES: frozenset[str] = frozenset(STORES)
```

**店舗名を個別ハードコードしない。**`STORES`（現在13店舗）から導出することで、
**今後 `STORES` へ店舗を追加しても「非記事用ページ＝新デザイン／記事用＝従来デザイン」**
という構造が自動的に維持され、**横展開漏れが起きない**。

現在の店舗×ページ対応（`show_image_type_page()` から確定）:

| 店舗 | auto | auto_slump | auto_article | rote |
|---|---|---|---|---|
| 高田馬場 | ○ | — | ○ | ○ |
| 上野本館 | ○ | ○ | — | ○ |
| 新宿歌舞伎町 | — | ○（かぶぱ） | — | ○ |
| 溝の口本館 / 溝の口新館 / 西武新宿 / 新大久保 | ○ | — | — | ○ |
| 渋谷新館 | ○ | — | ○ | ○ |
| 稲毛 / 上野新館 / 新小岩 | ○ | ○ | — | — |
| 秋葉原 | — | ○ | ○ | — |
| 赤坂見附 | ○ | — | — | — |

### ⑤ ★記事用の除外は「店舗名」ではなく「page 単位」

**「高田馬場・渋谷新館・秋葉原だから除外」ではない。`auto_article` というページ自体を
新テーマ対象外にしているのが正式仕様。**
**将来 記事用の店舗が追加されても、`auto_article` である限り新デザインを適用してはならない。**

記事用店舗であっても `auto` / `auto_slump` を開いていれば新デザインになる
（＝店舗名で除外していないことの裏返し）。

### ⑥ テーマ判定は page と store から毎回導出する

```python
def _table_theme_new() -> bool:
    try:
        return (st.session_state.get("page") in _TABLE_THEME_PAGES
                and st.session_state.get("selected_store") in _TABLE_THEME_STORES)
    except Exception:
        return False
```

**session_state へ新しい sticky フラグを保存する方式にしてはならない。**採用理由:

- ページ遷移時の状態残留を防止できる
- rerun 時のフラグ立て忘れ・消し忘れが起きない
- 記事用を page 単位で安全に除外できる
- **約70か所ある `_build_machine_img()` 呼び出しへ theme 引数を足す必要がない**
- Streamlit 外（純粋テスト・subprocess）では `except` で False＝従来デザインへ落ちる

**この設計を今後も維持すること。**

### ⑦ ⑦プレビューと⑧本番は必ず同じデザイン

| 経路 | 実装 |
|---|---|
| ⑦プレビュー | `streamlit_app.py` の `_build_machine_img()` / `draw_table_image()` |
| ⑧本番の並び・列 | `convert_narabi_pil.py`（subprocess） |

`show_auto_page` の ⑧ 呼び出しが **`theme_new=_table_theme_new()`** を渡し、
`_patch_and_run_narabi()` が `NO_BAR` と同じ regex 方式で **`THEME_NEW`** を書き換える。
`convert_narabi_pil.py` 側は `THEME_NEW` により `HEADER_BG` / `HEADER_FG` / `DATA_FG` /
`line_h` / 青バー色 / `SUMMARY_BG` を切り替える。**既定は必ず `False`＝従来デザイン。**

**「⑦だけ新デザイン・⑧だけ旧デザイン」という状態は禁止。**
記事用は `no_bar=True` で呼ばれ `theme_new` を渡さないため、従来デザインのまま。

### ⑧ 店舗固有対応①：秋葉原 `_build_slump_title_img()`

秋葉原のスランプ付き結果ポストは**表なし・タイトルバー＋スランプグラフだけ**の画像を
`_build_slump_title_img()` で作っており、**独自に青バー `(38,76,161)` と `LINE_H = 6` の
赤線を持っていた**。新テーマ時は次のとおり対応済み。

```python
LINE_H = 0 if _table_theme_new() else 6            # 赤線なし・余白も残さない
bar = Image.new("RGBA", (total_w, BAR_H),
                C_NEW_TITLE_BG_RGBA if _table_theme_new() else (38, 76, 161, 255))
if LINE_H:
    canvas.paste(Image.new("RGB", (total_w, LINE_H), (204, 0, 0)), (0, BAR_H))
```

**従来テーマ（記事用等）へは影響させない。**グラフ領域は画素完全一致・幅不変・高さのみ −6px。

### ⑨ 店舗固有対応②：新宿歌舞伎町（かぶぱ）の `_bar_crop_h()`

かぶぱのパネル合成は**「青バー＋赤線6px」を前提に上部を crop** していた。

```
_insert_panel_into_machine_img()   … split = round(w*73/950) + 6
_apply_panel_to_table_img()        … _bar_h = round(img.width*73/950) + 6
_composite_slump_onto_images()     … _bar_h0 = round(_img.width*73/950) + 6
```

**新デザインでは赤線6pxが無いため、固定 +6 のままだと表の先頭行が6px欠ける。**
そこで新設した `_bar_crop_h()` を3か所すべてで使う。

```python
def _bar_crop_h(width: int) -> int:
    return round(width * 73 / 950) + (0 if _table_theme_new() else 6)
```

| テーマ | 戻り値 |
|---|---|
| **新デザイン** | **BAR_H のみ（赤線6pxを含めない）** |
| 従来デザイン | **BAR_H + 6（従来どおり）** |

実測で **新=76 / 旧=82**、**crop後の最上行が列見出し（新 `#290068` / 旧 `#F3E6C8`）**、
**crop後の高さが表本体と一致（6px余分に切っていない）**ことを確認済み。

### ⑩ スランプ合成ロジックは変更していない

**`_attach_slump_to_table()` / `_attach_slump_to_table_side()` は本体無変更。**
赤線6pxを削除した結果、**新デザインの表画像は旧デザインより6px低くなる。これは正式仕様。**

| レイアウト | 挙動 |
|---|---|
| 縦3列 | 幅不変・高さは表の赤線分（−6px）だけ小さい・**グラフ領域は従来と画素完全一致**・表の下端（ピンクバー）が残り切れない |
| 横4列 | 高さは `max(表の高さ, グラフ域の高さ)`。**グラフ域が高い＝実運用の16台以上では高さ不変**。**グラフ領域は従来と画素完全一致**・表とグラフの間の白い SIDE_GAP により重ならない |

**店舗固有のスランプ配置条件は維持する**（例：稲毛＝表下3列／横版4列／16台以上で横版）。

### ⑪ ★スランプグラフ本体のデザインは今回の対象外

今回正式記録したのは **「表画像のデザイン」だけ**である。
**スランプグラフ自体の黒背景・グラフ線・目盛・文字・機種名表示・その他の配色は
今回の正式仕様変更に含めない。**`draw_slump_graph()` は無変更。
スランプグラフの背景色等は**次の別案件**として検討する。

### ⑫ 変更範囲（`a05cb00` 時点）

| ファイル | 変更 |
|---|---|
| `streamlit_app.py` | 定数 `_TABLE_THEME_STORES` / `_TABLE_THEME_PAGES` / `C_NEW_TITLE_BG_RGBA` / `C_NEW_HEADER_BG` / `C_NEW_HEADER_FG` / `C_NEW_DATA_FG` / `C_NEW_SUMMARY_BG_RGBA`、関数 `_table_theme_new()` / `_bar_crop_h()`、`draw_table_image()` / `_build_machine_img()` / `_patch_and_run_narabi()` / `show_auto_page()` / `_insert_panel_into_machine_img()` / `_apply_panel_to_table_img()` / `_composite_slump_onto_images()` / `_build_slump_title_img()` |
| `convert_narabi_pil.py` | `THEME_NEW` / `HEADER_BG` / `HEADER_FG` / `DATA_FG` / `line_h` / 青バー色 / 赤線paste / `SUMMARY_BG` |
| **`wp_client.py` / `shimazu_renderer.py`** | **無変更** |

`run_auto_pipeline` / `run_step1〜3` / `_build_sue_images` / `_build_col_items` /
`_build_machine_img_no_bar` / `_build_article_machine_img` / `_art_high_title_bar` /
`_art_ranking_image` / `_art_zendai_image` / `_attach_slump_to_table(_side)` /
`generate_report_text` / `_save_jpeg` / `draw_slump_graph` / `show_auto_article_page` /
`show_work_page` / `show_rote_page` ほかは**ASTバイト一致（無変更）**。

### ⑬ 確認結果（横展開時・178 PASS / 0 FAIL）

- **ゲート網羅**：全13店舗 × auto/auto_slump/work＝**39通りすべて ON**。
  記事用・ローテ・その他ページは**全店舗で OFF**。未知の店舗名・page未設定・Streamlit外も OFF。
- **稲毛**：横展開前と**画素完全一致**（ピンクあり/なし/no_bar/no_bar+ピンク/hq2.0）。
- **他店舗**：pipeline を7店舗（西武新宿・新小岩・上野本館・赤坂見附・新宿歌舞伎町・秋葉原・稲毛）
  で実行し、各5画像すべてで紫バー・赤線なし・濃紫見出し・白見出し文字・紫の通常文字（黒0px）・
  濃ピンクサマリー・黒サマリー文字を確認。**差枚列は従来デザインと画素完全一致**。
- **⑦⑧一致**：並び・列でタイトル・見出し・赤線なし・通常文字がすべて一致（⑧はJPEG圧縮±数階調）。
- **記事用**：`_build_machine_img_no_bar` / `_build_article_machine_img` / `_art_high_title_bar` /
  `_art_ranking_image` / `_art_zendai_image` / `draw_table_image`(テーマOFF) が**画素完全一致**、
  ⑧記事用相当（`no_bar=True`）は **JPEG SHA256 完全一致**。
- **抽出・結果テキスト**：7店舗すべてで `zen_dai_list` / `high_ratio_list` / `excellent_list` と
  生成ファイル名が**不変**。
- **WordPress 実通信0件**（GET/POST/PUT/DELETE すべてなし）。⑧ボタンも未実行。

### ⑭ 今後の禁止事項

1. **`C_ZERO` を #4B0082 へ変更しない**（通常文字色と条件付き色を必ず分離する）
2. **差枚列の `C_PLUS` / `C_MINUS` / `C_ZERO` の色分岐を変更しない**
3. **既存の `C_TITLE_BG` / `C_MACH_HEADER_BG` / `C_MACH_HEADER_FG` / `C_HEADER_BG` /
   `C_SUMMARY_BG_RGBA` / `C_REDLINE` / `REDLINE_H` を書き換えない・削除しない**
   （`draw_table_image()` 内の `title` 引数用デッド経路も整理・削除しない）
4. **`_TABLE_THEME_STORES` を店舗名の個別ハードコードへ戻さない**（`frozenset(STORES)` を維持）
5. **`_TABLE_THEME_PAGES` へ `auto_article` を追加しない**
6. **記事用の除外を「店舗名リスト」で行わない**（page 単位を維持）
7. **`rote` を対象へ加えない**（独自レンダラー・独自配色）
8. **`_table_theme_new()` を session_state の sticky フラグ方式へ戻さない**
9. **`_build_machine_img()` 等の呼び出し側へ theme 引数を追加しない**
10. **⑦だけ／⑧だけ直さない**（`theme_new` → `THEME_NEW` の配線を維持。既定は必ず `False`）
11. **`_bar_crop_h()` を固定 `+6` へ戻さない**（新宿歌舞伎町の表の先頭行が6px欠ける）
12. **秋葉原 `_build_slump_title_img()` の紫バー・赤線なしを巻き戻さない**
13. **`_attach_slump_to_table()` / `_attach_slump_to_table_side()` を色変更のために改造しない**
14. **表画像が6px低くなることを不具合として扱わない**（正式仕様）
15. **店舗固有のスランプ配置条件（稲毛の3列／横版4列／16台以上 等）を変更しない**
16. **スランプグラフ本体（`draw_slump_graph()` の黒背景・線・目盛・文字）を今回を理由に変更しない**
17. **記事用・WordPress・抽出条件・判定・ファイル名・並び順・液晶・パネル・ban_map・
    結果テキストを色変更を理由に変更しない**
18. **無関係なリファクタ・未使用コード整理をしない**
