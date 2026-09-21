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

## 【正式仕様】スランプグラフ新デザイン（2026-09-10・`0e49bd9` / `5711df4`）

**正式仕様。巻き戻し禁止。**対象は**スランプ付き結果ポスト用（`auto_slump`）のスランプカードだけ**。
2026-09-10 に対象6店舗を **Cloud 実機でユーザーが確認し「問題なかったです」と最終承認**した。

**過去のスランプ背景に関する記述（`82efd8c` / `060519a` / `95bde1d` 時点の途中版）と競合する場合は、
本節（2026-09-10）が最新の正式仕様として優先する。**既存記録は履歴として削除・圧縮しない。

### ① 対象ページは `auto_slump` のみ

```python
_SLUMP_THEME_PAGES: frozenset[str] = frozenset({"auto_slump"})
```

**次はすべて対象外で、従来デザイン（黒地テンプレート）を維持する正式仕様である。**

`auto_article` ／ `auto` ／ `work` ／ `rote` ／ `slump_graph` ／ その他単独スランプページ

**特に記事用 `auto_article` へ新スランプデザインを適用してはならない。**

### ② 対象店舗は auto_slump を持つ6店舗（明示列挙）

```python
_SLUMP_THEME_STORES: frozenset[str] = frozenset({
    "稲毛",
    "新小岩",
    "上野新館",
    "上野本館",
    "秋葉原",
    "新宿歌舞伎町",
})
```

**対象外の7店舗**（`auto_slump` のボタン自体を持たない）：
高田馬場 ／ 西武新宿 ／ 新大久保 ／ 渋谷新館 ／ 赤坂見附 ／ 溝の口本館 ／ 溝の口新館

**`frozenset(STORES)` にはしない。対象6店舗を明示列挙することが正式仕様である。**
**今後 `STORES` へ店舗が追加されても自動的に新スランプテーマの対象にはしない**
（対象＝スランプ付き結果ポストを実際に使う店舗、という意図を集合から読み取れる状態を保つ）。

### ③ テーマ判定は page × store の AND

```python
def _slump_theme_new() -> bool:
    return (st.session_state.get("page") in _SLUMP_THEME_PAGES
            and st.session_state.get("selected_store") in _SLUMP_THEME_STORES)
```

**店舗名だけで新テーマONにしてはならない。**保存フラグを持たず毎回 page と store から導出するため、
ページ遷移・rerun・on_change の順序に依存しない。Streamlit 外では False（従来デザイン）。

**同じ対象店舗でも `auto_article` / `auto` / `work` / `rote` / `slump_graph` では新テーマOFF。**

### ④ カード生成は全店舗で1本道

```
draw_slump_graph()
  → _sl_new = _slump_theme_new()
       ON : _slump_template_image()          ← 新デザイン＋猫
       OFF: Image.open(template).convert()   ← 従来テンプレートPNGをそのまま
```

- **基本サイズ 388×472**（全店舗共通）。
- `draw_slump_graph` / `_slump_template_image` / `_slump_neko_alpha` / `find_slump_template` に
  **店舗依存の分岐は1つも無い**。
- **対象6店舗の `auto_slump` は、同一入力データならカードが完全同一**になる。

### ⑤ 正式デザイン

**白を基調にした淡い紫のグラデーション／ファセット表現。**

**ヘッダー2セル（機種名・台番）**
- 白主体
- 左右端から淡紫が自然に減衰する濃淡（指数減衰）
- **少数の広い斜めバンド**のみ
- **細い斜めストライプ（`/////` のような繰り返し模様）は使用しない**
- 中央部は白に近く保つ

**グラフ本体**
- 白主体
- 四隅に淡紫、**右下を最も強く**する
- 広い斜めレイヤーを使用
- **赤いグラフ線を横切るような白い斜め光沢線は入れない**

**淡紫の最濃色**：**`#C7B4DD`**（`C_SL_PURPLE`）

### ⑥ 正式カラー

| 対象 | 色 |
|---|---|
| 機種名 / 台番 / 差枚 / 軸 / 0ライン / 目盛文字 | **`#4B0082`** |
| 補助線 | **`#CFBDE5`** |
| 外枠・区切り | **`#D8C6E3`** |
| スランプグラフ線 | **`#FF0000`** |
| 淡紫の最濃色 | **`#C7B4DD`** |
| 背景 | **白主体** |

**既存座標・グラフ計算は変更しない。**

### ⑦ 猫の正式仕様

右下へ猫を薄く配置する。

| 項目 | 値 |
|---|---|
| 正式アセット | **`assets/slump/neko_5000_1.bmp`**（読み取り専用） |
| 合成強度 | **`_SL_NEKO_K = 0.198`**（ユーザーが最終承認した濃さ） |

- **対象6店舗で同一アセットを共通使用する。店舗ごとに複製しない。**
- **右下配置／同じ位置／同じサイズ／同じ透明度／同じマスク／同じ合成強度**。
- **店舗ごとの個別調整はしない。**

### ⑧ 猫マスクと不要線の除去（`_slump_neko_alpha()`）

猫の元画像に焼き込まれていた
**点線・破線・水平線・罫線・枠線・そのアンチエイリアス**を
スランプカードへ**一切持ち込まない**のが正式仕様。

判定は濃さ **`d = 255 - min(R, G, B)`**。

```python
_SL_NEKO_BASE = 26    # これ以下は完全透明（地色のゆらぎ）
_SL_NEKO_CAT  = 74    # 猫の濃さの上限（alpha=255）
_SL_NEKO_LINE = 90    # これ以上は破線・罫線・枠 → 線として除外
```

- 線と判定した画素は**1px膨張**してアンチエイリアス残りも除去する。
- **★不要線を `#FFFFFF` や背景色で塗りつぶす方式は禁止。**
  猫の外側は **`alpha = 0` の完全透明**として扱い、下の白＋淡紫グラデーションが
  途切れずそのまま見える状態にする。
- **★線を除いた「穴」は、上下の猫アルファから縦方向に補間して埋める。**
  単に alpha=0 にすると猫の中で線の跡が抜け、合成後に**白い点線**として見えてしまう。
- 正式確認では**猫由来の点線・破線・水平線は0**。

### ⑨ 四隅の濃紫点対策

途中版で四隅に `#4B0082` の濃紫点が出ていた問題は正式版で解消済み。

**外枠判定は `< / >` ではなく `<= / >=` を使い、枠線そのものを外枠として扱う**のが正式仕様。
これを `< / >` に戻すと、枠の角の濃い画素がグラフ側の色で再配色され、四隅に濃紫の点が復活する。

- **外枠の外側余白は白のまま維持する。**
- 正式確認：**四隅24×24走査で濃紫点0**。
- **四隅の淡紫グラデーション自体は残す**（消さない）。

### ⑩ 座標・サイズは従来維持

```python
X_START = 24
X_END   = 364
Y_ZERO  = 290
PX_1000 = 47
DARK_Y1 = 462
```

**388×472 とあわせて変更しない。**
**新デザインはグラフの座標計算・差枚計算を変更するものではない。**

### ⑪ 店舗固有のコンテナ処理は従来どおり（変更しない）

新テーマが変えるのは **388×472 カードの内部デザインだけ**。カード生成後の合成は従来仕様を維持する。

| 店舗 | 維持する既存仕様 |
|---|---|
| **稲毛** | 表下3列／16台以上で横4列（`_attach_slump_to_table` / `_attach_slump_to_table_side`） |
| **新小岩 / 上野新館 / 上野本館** | 上記＋`_GAP_FILL_STORES` の液晶はめ込み |
| **新宿歌舞伎町** | `_PANEL_STORES` のパネル処理／**`_bar_crop_h()`**／10日区切り／その他既存仕様 |
| **秋葉原** | **`_build_slump_title_img()`（表なしタイトル型）**／**横版 `_side.jpg` を作らない**／その他既存仕様 |

**新スランプテーマのためにこれらのコンテナ処理を変更してはならない。**

### ⑫ ⑦プレビュー・🔄その他更新・⑧本番は同一経路

`auto_slump` の **⑦プレビュー / 🔄その他を更新 / ⑧本番生成**は、いずれも
`show_auto_page` 内から同じ **`draw_slump_graph()` → `_slump_template_image()`** を通る。

**⑦と⑧でスランプデザインを分けてはならない。**

### ⑬ 実装履歴

| commit | 内容 |
|---|---|
| `82efd8c` | feat: 稲毛のスランプグラフを淡紫デザインへ（初回・稲毛限定） |
| `060519a` | fix: 稲毛のスランプ背景を白基調グラデーションへ |
| `95bde1d` | fix: 稲毛スランプのセル別グラデーションを見本へ寄せる |
| **`0e49bd9753a8c4b57ac5b1199aeb2045caee86ca`** | **feat: 稲毛スランプへ承認済み背景デザインを反映**（ユーザー承認済みサンプルのロジックを正式実装。この時点で稲毛 `auto_slump` を Cloud 実機確認しユーザーOK） |
| **`5711df42d5aee74f925aa06a96c19f17c07cfc10`** | **feat: スランプ新デザインを全対象店舗へ横展開**（`streamlit_app.py` の `_SLUMP_THEME_STORES` のみ変更・**変更関数0**） |

その後、**ユーザーが Cloud 実機で対象6店舗を確認し「問題なかったです」と最終承認**。
**2026-09-10 をもって正式仕様確定とする。**

### ⑭ テスト・回帰確認結果（横展開時・全PASS / FAIL 0）

**対象6店舗**
- 同一入力でカードが**完全一致**（ハッシュ一致）
- **388×472**／猫あり／**猫由来の点線・破線・水平線0**／**四隅の濃紫点0**
- 軸 `#4B0082`／補助線 `#CFBDE5`／グラフ線 `#FF0000`
- **稲毛は横展開前（`0e49bd9`）と pixel-identical**

**テーマOFF回帰**
- `auto_article`（高田馬場・渋谷新館・秋葉原・稲毛・新小岩・新宿歌舞伎町）／`slump_graph`／
  `auto`（8店舗）／`work` を含む**18経路すべてで変更前と pixel-identical**

**ゲート網羅**
- **13店舗 × 11ページ ＝ 143通り**を確認し、**ONは「対象6店舗 × auto_slump」の6通りのみ**

**店舗固有処理の不変**
- `_attach_slump_to_table` / `_attach_slump_to_table_side` / `_build_slump_title_img` /
  `_bar_crop_h` / `_slump_theme_new` / `_slump_template_image` / `_slump_neko_alpha` /
  `draw_slump_graph` / `find_slump_template` / `_find_slump_bg` /
  `_composite_slump_onto_images` の**11関数すべてASTバイト一致**
- `_PANEL_STORES` / `_GAP_FILL_STORES` / `_bar_crop_h()` の戻り値も不変

### ⑮ 今後の禁止事項

1. **`_SLUMP_THEME_PAGES` へ `auto_article` などを追加しない**
2. **`auto_article` へ新スランプデザインを適用しない**（記事用は旧デザインを完全維持）
3. **`_SLUMP_THEME_STORES` を `frozenset(STORES)` にしない／対象外7店舗を追加しない**
4. **`STORES` への店舗追加を理由に自動で新テーマ対象へ加えない**
5. **店舗名だけで新テーマONにする判定を作らない**（page × store の AND を維持）
6. **`_slump_theme_new()` を保存フラグ方式へ戻さない**
7. **`C_SL_PURPLE = #C7B4DD` / `#4B0082` / `#CFBDE5` / `#D8C6E3` / `#FF0000` を変更しない**
8. **ヘッダーへ細い斜めストライプを戻さない／グラフ本体へ白い斜め光沢線を入れない**
9. **`_SL_NEKO_K = 0.198` を変更しない／店舗ごとに猫を調整・複製しない**
10. **`assets/slump/neko_5000_1.bmp` を変更・削除しない**
11. **猫の不要線を白や背景色で塗りつぶさない**（`alpha = 0` の完全透明を維持）
12. **線を除いた穴の縦補間を外さない**（外すと白い点線が復活する）
13. **`_SL_NEKO_BASE = 26` / `_SL_NEKO_CAT = 74` / `_SL_NEKO_LINE = 90` を理由なく変更しない**
14. **外枠判定を `< / >` へ戻さない**（四隅の濃紫点が復活する）
15. **四隅の淡紫グラデーションを消さない**
16. **`X_START` / `X_END` / `Y_ZERO` / `PX_1000` / `DARK_Y1` / 388×472 を変更しない**
17. **店舗固有のコンテナ処理（稲毛の3列・横4列／液晶／新宿歌舞伎町のパネル・`_bar_crop_h`・10日区切り／
    秋葉原のタイトル型・横版なし）を新テーマのために変更しない**
18. **⑦と⑧でスランプデザインを分けない**
19. **表画像のテーマ（`_TABLE_THEME_*` / `_table_theme_new`）と混ぜない・統合しない**
20. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町・3系統分離（2026-09-10・`0e79a80` / `394f309`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】のトップ画面と結果系ページだけ**。
2026-09-10 に **Cloud 実機でユーザーが確認し「問題なかったです」と最終承認**した。

**本節が新宿歌舞伎町の結果系に関する最新の正式仕様であり、該当する旧記述を上書きする。**
既存の記録（表画像新デザイン・スランプグラフ新デザイン・かぶぱ関連・ローテ関連）は
**削除・圧縮・書き換えしない**。矛盾する箇所は本節を優先する。

### ① トップ画面は3系統

新宿歌舞伎町の結果系機能は**3つの別系統**として扱う。

| # | ボタン | page | 中身 |
|---|---|---|---|
| **①** | **📊 かぶぱポストの結果** | **`auto_slump`** | 従来の新宿歌舞伎町専用システム |
| **②** | **📈 スランプ付き結果** | **`auto_slump2`** | 上野新館型をベースにした新設システム |
| **③** | **📋 ローテ用** | **`rote`** | 従来のローテシステム（完全不変） |

**★「かぶぱポストの結果」と「スランプ付き結果」は同じ機能ではない。**
配置は上段2カラム（①②）＋下段全幅（③）。
button key は **`auto_slump_btn` / `auto_slump2_btn` / `rote_mode_btn`**（①③は既存キー据え置き）。
**「⚡ 結果ポスト用」(auto) は従来どおり非表示。**

### ② page 設計

- **`page` を正式な識別子として使う。sticky flag 方式は禁止。**
- `_navigate()` の **store 保持ページのタプルへ `"auto_slump2"` を追加済み**
  （URL に `store` が乗り、F5・ブラウザ戻る/進むで復元される）。
- **`_sync_from_query_params()` は無変更**（既存の仕組みをそのまま利用）。
- `main()` のルーティングとパンくずへ `auto_slump2` を追加。
- **`show_auto_page(with_slump=True)` を①②で共用する。ページ関数を複製しない。**

### ③ ①かぶぱポストの結果（`auto_slump`）

**7c700fe 以前の新宿歌舞伎町専用仕様。**

| 項目 | 値 |
|---|---|
| ②全台枠数 | **3枠** |
| ②優秀台枠数 | **6枠** |
| ②の左右配置 | **優秀台＝左 / 全台＝右** |
| `kojin_y_*` | **毎回空欄**（保存値・永続値を無視） |
| 個別機種の優秀台ピックアップ | **非表示** |
| その他の優秀台ピックアップ | **非表示** |
| 通常末尾モード | **3択**（全台／優秀台(ピンクバー付き)／優秀台(ピンクバーなし)） |
| ジャグラー末尾モード | **3択** |
| ⑤オススメ機種ピックアップ | **非表示** |
| ⑥結果テキスト素材メモ | **非表示** |
| バラエティ | **あり** |
| 🎯掲載台を選ぶ | **あり** |
| 🔍プレビュー生成 | **なし** |
| 📝記入部分のみプレビュー | **あり** |
| 🔄その他を更新 | **なし** |
| パネル / `_bar_crop_h()` / 液晶 / 階別バリアント | **あり** |
| 結果テキスト | **`_build_kabupa_result_text()`** |
| スマホUI制御 | **維持** |
| ⑧実行 / ZIP | あり |
| スランプカード | **正式新デザイン（白＋淡紫＋猫・388×472）** |

### ④ ②スランプ付き結果（`auto_slump2`・新設）

**上野新館型をベースにした新宿歌舞伎町版。**

| 項目 | 値 |
|---|---|
| ②全台枠数 | **12枠** |
| ②優秀台枠数 | **12枠 →「▼ ページを広げる」で最大48枠** |
| ②個別入力の保存 | **日付（Excel）単位**（未保存日は空欄／同日は復元／別日混入なし） |
| 個別機種の優秀台ピックアップ | **あり** |
| その他の優秀台ピックアップ | **あり（上野新館同様の①②分割）** |
| ⑤オススメ機種ピックアップ | **あり** |
| ⑥結果テキスト素材メモ | **あり** |
| 通常末尾モード | **5択** |
| ジャグラー末尾モード | **5択** |
| 🔍プレビュー生成 | **あり** |
| 📝記入部分のみプレビュー | **あり** |
| 🔄その他を更新 | **あり** |
| バラエティ | **なし** |
| かぶぱ専用「🎯掲載台を選ぶ」 | **なし** |
| パネル / `_bar_crop_h()` / 液晶 / 階別バリアント | **あり** |
| 結果テキスト | **`generate_report_text()`** |
| 縦版 / 16台以上の横版 `_side.jpg` / ZIP | **あり** |
| スランプカード | **正式新デザイン（白＋淡紫＋猫・388×472）** |

### ⑤ ③ローテ用（`rote`）は完全不変

**★10日区切り（1〜10 / 11〜20 / 21〜月末）と「○日目結果」は
`_generate_rote_result_text()` / `show_rote_page()` の *ローテ専用仕様* である。**

**`auto_slump` / `auto_slump2` の仕様ではない。**
過去のスランプデザイン正式記録などに、新宿歌舞伎町の「10日区切り」「○日目結果」を
**auto_slump 側の店舗固有仕様のように読める記述があるが、本節で訂正する**
（過去の文章自体は削除しない）。今回 rote は1文字も変更していない。

### ⑥ かぶぱ判定 `_is_kabupa_page()`

```python
def _is_kabupa_page() -> bool:
    return (st.session_state.get("selected_store") == _KABUPA_STORE
            and st.session_state.get("page") == "auto_slump")
```

**`store == "新宿歌舞伎町"` だけで①固有UIを判定してはならない。**
①と②は store が同じなので、**必ず page を含めた AND で判定する**。
保存フラグを持たず毎回導出するので、URL・F5・戻る/進むと常に一致する
（`_slump_theme_new()` と同じ流儀）。②`auto_slump2` では False になり、
上野新館型の共通経路へ落ちる。他店舗では常に False。

### ⑦ 保存名前空間 `_kojin_ns()`

①と②の②個別入力を**物理的に分離**する。

```python
_KABUPA_STORE     = "新宿歌舞伎町"
_KABUPA_SLUMP2_NS = "新宿歌舞伎町(スランプ)"

def _kojin_ns(store: str) -> str:
    if store == _KABUPA_STORE and st.session_state.get("page") == "auto_slump2":
        return _KABUPA_SLUMP2_NS
    return store
```

| | 保存キー例 |
|---|---|
| ① | `kojin_y_0_新宿歌舞伎町` |
| ② | `kojin_y_0_新宿歌舞伎町(スランプ)` |

適用は **`_auto_input_keys` / `_persistent_keys` / `_kojin_keys` / `_kojin_scope_key` の
先頭1行**と、`_merge_auto_entry` / `_restore_auto_inputs` の集合判定だけ。

**★論理名前空間は入力値の保存のためだけに使う。**
**Pision取得・`store_config`・画像生成・店舗表示・出力ファイル名・パネル・液晶へは渡さない。**
**実店舗名は常に「新宿歌舞伎町」。**

### ⑧ ①の後方互換

①かぶぱの `auto_page_inputs.json` の保存キーは**従来の `_新宿歌舞伎町` suffix のまま**。
既存①データはそのまま①で読める。②は新しい名前空間を使うため、
**①の既存保存データを②へ流用しない**（②は空から始まる）。

なお `_restore_auto_inputs()` は保存エントリの**全キー**を session_state へ入れる既存仕様のため、
①でも②の名前空間キーが session_state に載る。ただし①のUIは `_新宿歌舞伎町` キーしか読まず、
`_merge_auto_entry()` も `_auto_input_keys(store)` のキーしか書かないので、
**表示にも保存にも混ざらない。**

### ⑨ ②の日付単位保存

**②`auto_slump2` だけ**が②の日付（Excel）単位保存の対象
（`_KOJIN_DATE_SCOPED_STORES` へ `_KABUPA_SLUMP2_NS` を入れる。**`"新宿歌舞伎町"` は入れない**）。
既存の scope guard（`_kojin_scope_excel_{ns}`）と②60キー完全性チェックをそのまま利用する。

- 未保存日 → **②空欄**
- 同日 → **復元**（hidden枠＝13枠目以降を含む）
- 別日 → **値混入なし**
- 日付切替直後の rerun（scope 不一致）→ **旧日付値を新日付へ保存しない**
- ②60キーが不完全（widget GC）→ **部分保存しない**

**①`auto_slump` は日付単位保存の対象ではなく、従来どおり `kojin_y_*` を毎回空欄にする。**

### ⑩ 共有キーは変更しない

`kojin_enabled` / `suebangai_enabled` / `suebangai_mode` / `jug_sue_*` /
`variety_enabled` / `variety_mode` / `narabi_*` / `retsu_*` などの
**店舗suffixを持たない既存共有キーの構造は変更していない**（①②で共有されたまま）。
**①②の分離のために全店舗の保存キー体系を変更してはならない。**
今回物理分離したのは②個別入力の名前空間だけである。

### ⑪〜⑬ パネル・液晶・階別バリアント

①②とも store は「新宿歌舞伎町」なので、**既存の store 判定をそのまま使う**。

- パネル：**`_PANEL_STORES`**（①②ともあり）／**`_bar_crop_h()` も既存仕様を維持**
- 液晶：**`_GAP_FILL_STORES`**（①②ともあり）／**`_gap_sel_key(store, bans, machine)`**
  の掲載台番集合単位の選択保持・縦横共有・空き2コマ以上判定も既存どおり
- 階別バリアント：**`_FLOOR_SPLIT_MACHINES`**（①②とも使用可）

**今回の3系統分離のために、これらの関数本体は1つも変更していない。**

### ⑭ スランプカード

①`auto_slump`・②`auto_slump2` とも、2026-09-10 正式採用済みの
**白＋淡紫＋猫の新スランプカード（388×472）** を使う。

```python
_SLUMP_THEME_PAGES = frozenset({"auto_slump", "auto_slump2"})
```

**`_SLUMP_THEME_STORES` の既存6店舗集合は変更しない。**
**★①かぶぱは今回の分離より前から正式新デザインの対象である。旧黒背景へ戻さない。**

### ⑮ 表画像テーマ

```python
_TABLE_THEME_PAGES = frozenset({"auto", "auto_slump", "auto_slump2", "work"})
```

②でも正式採用済みの新しい表デザインを使う。
**記事用(`auto_article`)などの既存除外仕様は維持する。**

### ⑯ 結果テキストは3系統で別物

| 系統 | 関数 |
|---|---|
| ① かぶぱポストの結果 | **`_build_kabupa_result_text()`** |
| ② スランプ付き結果 | **`generate_report_text()`** |
| ③ ローテ用 | **`_generate_rote_result_text()`** |

**3つの用途を混同しない。特に「10日区切り」「○日目結果」は③ローテだけ。**

### ⑰ ①かぶぱ専用（②へ適用しない）

バラエティ ／ 🎯掲載台を選ぶ ／ かぶぱ専用結果テキスト ／ ②全台3枠・優秀台6枠 ／
末尾3択 ／ 🔍プレビュー生成なし ／ ⑤⑥非表示

### ⑱ ②上野新館型（①へ適用しない）

②全台12枠・優秀台48枠 ／ 日付単位保存 ／ 個別機種の優秀台ピックアップ ／
その他の優秀台ピックアップ（①②分割）／ ⑤ ／ ⑥ ／ 末尾5択 ／
🔍 ／ 📝 ／ 🔄 ／ `generate_report_text()`

### ⑲ ボタン色（Cloud確認後に追加した正式UI仕様）

| ボタン | 通常背景 | 通常ボーダー | 文字 | hover背景 | hoverボーダー |
|---|---|---|---|---|---|
| **① 📊 かぶぱポストの結果** | **`#7000E0`** | **`#5A00B8`** | **白** | **`#5A00B8`** | **`#5A00B8`** |
| ② 📈 スランプ付き結果 | `#00ACC1`（既存） | `#00838F` | 白 | `#00838F` | `#00838F` |
| ③ 📋 ローテ用 | `#1976D2`（既存） | `#1565C0` | 白 | `#1565C0` | `#1565C0` |

**この色分けは新宿歌舞伎町トップ専用**（CSSは `elif store == "新宿歌舞伎町":` の内側で
のみ描画される）。**他店舗へ波及させない。共通CSS全体の紫化も禁止。**

### ⑳ 実装 commit 履歴

| commit | 内容 |
|---|---|
| `7c700fee6e522d82563577ceacc60e12e0d0c794` | 上野新館型機能の横展開。**ただし既存かぶぱ `auto_slump` 自体へ適用してしまい、ユーザー意図と異なる状態だった。最終仕様ではない（途中経過）** |
| **`0e79a80354286cbf921bf7b7df7cac95304e4c72`** | **正式な3系統分離。**①`auto_slump`／②`auto_slump2`／③`rote` を分離し、①の従来かぶぱ仕様を復元、②を上野新館型として新設、保存名前空間を分離 |
| **`394f309570b3e39fae8972d11cb65e5a4181e234`** | **①「📊 かぶぱポストの結果」ボタンのみ紫へ変更** |

**ユーザー Cloud 実機確認：2026-09-10「問題なかったです」。**
したがって **`0e79a80` + `394f309` の状態を正式採用**する。
**`7c700fe` へ戻してはならない。**

### ㉑ テスト・回帰記録

**3系統分離（`0e79a80`）：PASS 247 / FAIL 0**

途中で**実装不具合を1件検出**した。
`_restore_auto_inputs()` の scope 記録が名前空間を通っておらず（`store` のまま判定していた）、
**②の日付単位保存が効かなかった**。`_kojin_ns(store)` を通すよう修正して PASS。
その他の途中 FAIL はテスト期待値側の問題で、実コードの不具合ではないことを確認済み。

**ボタン紫化（`394f309`）：PASS 11 / FAIL 0**

**回帰（すべて確認済み）**

- `rote` 不変 ／ `auto_article` 不変（AST バイト一致）
- `_build_kabupa_result_text()` 本体不変
- パネル関数本体不変（`_apply_panel_to_table_img` / `_build_panel_row` /
  `_insert_panel_into_machine_img` / `_bar_crop_h`）
- 液晶関数本体不変（`_gap_sel_key` / `_gap_fillable` / `_resolve_gap_screen` /
  `_on_gap_screen_change`）
- 階別バリアント（`_FLOOR_SPLIT_MACHINES`）不変
- 既存スランプ関連関数不変（`draw_slump_graph` / `find_slump_template` /
  `_slump_theme_new` / `_slump_template_image` / `_slump_neko_alpha`）
- **上野新館・上野本館・新小岩・稲毛・秋葉原の既存 `auto_slump` は非回帰**
  （ゲート値・カードとも変更前と一致）
- **①のスランプカードは分離前と pixel-identical**

### ㉒ 今後の禁止事項

1. **①`auto_slump` と②`auto_slump2` を同じものとして扱わない**
2. **`store == "新宿歌舞伎町"` だけで①固有UIを判定しない**（`_is_kabupa_page()` を使う）
3. **sticky flag 方式へ戻さない**（page を正式な識別子として使う）
4. **`_navigate` の store 保持タプルから `auto_slump2` を外さない**
5. **`show_auto_page` を①②で複製しない**
6. **①へ②の機能（12/48枠・日付保存・⑤⑥・末尾5択・🔍・🔄・その他優秀台）を適用しない**
7. **②へ①の機能（3/6枠・毎回空欄・末尾3択・バラエティ・🎯・かぶぱ結果テキスト）を適用しない**
8. **論理名前空間を Pision・store_config・画像生成・ファイル名・パネル・液晶へ渡さない**
9. **①の既存 `_新宿歌舞伎町` 保存キーを変更しない**（後方互換）
10. **`_KOJIN_DATE_SCOPED_STORES` へ `"新宿歌舞伎町"` を入れない**（②の名前空間だけ）
11. **scope guard・②60キー完全性チェックを外さない／部分保存を許さない**
12. **共有キー（`kojin_enabled` / `suebangai_mode` 等）を①②分離のために作り替えない**
13. **パネル・液晶・階別バリアントの関数本体を変更しない**
14. **`_SLUMP_THEME_PAGES` / `_TABLE_THEME_PAGES` から `auto_slump2` を外さない／
    `_SLUMP_THEME_STORES` の6店舗集合を変更しない**
15. **①のスランプカードを旧黒背景へ戻さない**
16. **「10日区切り」「○日目結果」を `auto_slump` / `auto_slump2` の仕様として扱わない**（③rote 専用）
17. **結果テキスト3系統（`_build_kabupa_result_text` / `generate_report_text` /
    `_generate_rote_result_text`）を混同しない**
18. **①のボタン色 `#7000E0` / hover `#5A00B8` を他店舗・他ボタンへ波及させない**
19. **`7c700fe` の状態へ戻さない**
20. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】結果テキストの記号・表記（2026-09-11・`1146b10` / `1c036e7` / `20bb9ea` / `9f274e8`）

**正式仕様。巻き戻し禁止。**対象は**アプリ内で生成される「結果テキスト」全般**（画像・WordPress本文は対象外）。
2026-09-11 に **ユーザーが Cloud 実機で確認し「確認して問題なかったです」と承認**した。

**本セクションが結果テキストの記号・表記に関する最新の正式仕様であり、
過去セクションの記述と競合する場合は 2026-09-11 の本セクションを優先する。**
既存セクションは**削除・圧縮・統合・並べ替え・書き換えしない**（当時の正式仕様の履歴として残す）。

### ⓪ 正式コミット（4件・この順で1つの仕様を構成）

| # | commit | 内容 |
|---|---|---|
| ① | **`1146b10443917151e68c91f96671d593c9291291`** | `fix: 渋谷新館のポスター機種結果テキストを更新` |
| ② | **`1c036e76518f3235bcc1a9b750a350bbbfb9e370`** | `fix: 結果テキストの記号表記を統一` |
| ③ | **`20bb9ea7d2d70d23010208cc42d559fcfb90b3d0`** | `fix: 結果テキストの箇条書き記号を統一` |
| ④ | **`9f274e8b4bf455ddc75ab2818bd78d20400bc8aa`** | `fix: 新小岩の特定機種結果を🏅表記へ調整` |

いずれも **`streamlit_app.py` の1ファイルのみ**の変更。**新規関数・削除関数は0件。**

---

## A. 全結果テキスト共通の箇条書き記号は「・」

機種結果・台結果などを列挙する**文頭記号は「・」**とする。

```
・戦国乙女5(11/16台)→平均+2,675枚
```

**従来の `🎖️` / `🚩` は結果テキストの通常の文頭記号として使用しない。**
唯一の正式な例外は**下記 E の「新小岩⑤カテゴリ内の全台系／高配分サマリー」＝`🏅`** だけ。

実装（`1c036e7` / `20bb9ea`）:

| 生成箇所 | 変更 |
|---|---|
| `_result_summary_lines()` | 見出し行 `🎖️` → **`・`**（既定） |
| `_build_kabupa_result_text()`（4か所） | 機種結果行 `🎖️` → **`・`** |
| `generate_recommended_result_text()` | `block_emojis` の値を生成時に `.replace("🎖️", "・")` |
| `excellent_section()`（👑その他の優秀台） | `item_emoji` を生成時に `.replace("🚩", "・")` |
| `suebangai_section()`（👑優秀末尾／👑ジャグラーの優秀末尾） | 同上 |
| `variety_section()`（👑バラエティの優秀台） | 同上 |

**★`STORE_REC_CONFIG` の定義そのものは変更していない。**
`"block_emojis": ["🎖️", "💥", "🤡", "🌺", "🎖️", "🎖️"]` / `"item_emoji": "🚩"` は**定義のまま残し、
生成時に該当絵文字だけを置換する**方式。したがって

- **`💥` `🤡` `🌺` `🍀` `⚡️` `⭐` `🎯` は据え置き**（新小岩⑤の B2=💥 / B3=🤡 / B4=🌺 はそのまま）
- **西武新宿の `item_emoji = "📍"` は据え置き**（末尾・バラエティ・その他の優秀台で 📍 のまま。・へ変えない）

**この「定義は残し生成時に置換」方式を、設定定義の直接書き換えへ変更してはならない。**

---

## B. 差枚一覧の文頭 `🌋` / `💎` は出さない

機種結果の直下に出る差枚一覧は**絵文字を付けず `+○,○○○枚` から直接始める**。

```
・戦国乙女5(11/16台)→平均+2,675枚
+14,500枚、+10,250枚、+7,100枚、
+5,500枚、+5,150枚、+4,900枚、
+4,000枚、+2,450枚、+1,100枚
```

**改行位置（4件折り返し）／並び順／`×N` 表記／3桁区切り／「枚」／読点「、」は既存 `_format_diffs()` のまま維持。**
変えたのは**先頭絵文字を出さないことだけ**。

### ★`🌋` / `💎` を全廃したわけではない（最重要・誤記しないこと）

削除したのは **「機種名の下にある差枚一覧の文頭」としての `🌋` / `💎` だけ**。
次は**正式に維持**しており、復活させたり削除したりしてはならない。

| 維持するもの | 場所 |
|---|---|
| `🌋万枚オーバーが{N}台！` | `summary_section()`（`📈{M/D}の結果📈`） |
| `💥+5,000枚オーバーが{N}台！` / `💥+3,000枚オーバーが{N}台！` | 同上 |
| `💎{N}台が+1,000枚オーバー！` | `summary_section()` / `juggler_summary_section()` |
| `_diff_emoji()`（現在未使用の既存ヘルパー） | 定義を残す |
| `💎{台番}番台`（上野本館ローテの月間オススメ表結果.txt） | ローテ専用・対象外 |

UI・見出し・画像内文字の同絵文字も**今回の対象外**。

---

## C. 並び／列：`🍡` 削除・`(N台並び)` → `(N台)`

- **見出し `👑並び仕掛け` / `👑列仕掛け` は維持**（`👑` を消さない）。
- 配下の機種名行・対象行に付いていた **`🍡` は出さない**（別絵文字へ置換しない）。
- 台数表記は **`(N台並び)` を廃止し `(N台)` へ統一**。

```
旧: 🍡2013-2015番台(3台並び)→平均+3,400枚
新: 2013-2015番台(3台)→平均+3,400枚
```

実装は **`_nami_like_section()`（並び・列で共通）と、渋谷新館ポスター用 `_detail_lines()`** の2か所だけ。

**開始台番・終了台番・台数・平均差枚・抽出条件・並び順・`ban_range` の算出ロジックは変更していない。**

### ★「台並び」は結果テキストの中だけを変えた

`streamlit_app.py` 内の他17件の「台並び」は**すべて対象外で未変更**：

画像タイトル・画像ファイル名（`{機種名}(N台並び).jpg`）／`_ART_NARABI_FN_RE`／
`_art_is_narabi_fn()`／パネル判定（`"台並び" in bare_fn`）／`_narabi_panel_names` 経路／
記事コメントの自然文（`3台並びが2箇所` 等）。

**ファイル名・パネル判定の「台並び」を `(N台)` へ変えてはならない**（画像名とパネル分岐が壊れる）。

---

## D. その他の優秀台／末尾／バラエティの個別台は「・」

```
👑その他の優秀台
・【5001番台】ネオアイム→+3,000枚

👑優秀末尾
🎁末尾③番台(5/9台)→平均+1,200枚
・【4001番台】戦国乙女5→+14,500枚

👑ジャグラーの優秀末尾
🎁末尾ゾロ目番台(2/4台)→平均+800枚
・【3001番台】マイジャグV→+2,500枚

👑バラエティの優秀台
・【5001番台】ネオアイム→+3,000枚
```

**サマリー行の `🎁` は変更していない。**`👑` 見出し・末尾の丸囲み数字・台数・平均差枚も不変。
抽出条件・対象末尾・対象台・並び順も不変。

---

## E. 【新小岩だけの例外】⑤カテゴリ内の全台系／高配分サマリーは `🏅`

新小岩の**⑤オススメ機種系結果テキスト**（`generate_recommended_result_text()`）では、
下記4カテゴリ内で **「全台系」または「高配分」として表示される機種単位サマリー行の文頭だけ**
`・` ではなく **`🏅`** を使う。

### 🏅対象の4カテゴリ

| # | カテゴリ見出し | 表示上の対象（`block_header_names` の略称） |
|---|---|---|
| ① | `🍀その他の毎日オススメ機種` | スマスロ北斗 / 北斗転生2 / 東京喰種 / ヴヴヴ2 / かぐや様 |
| ② | `🍀その他の主役機種` | カバネリ海門 / モンキーV / 炎炎2 / 真打吉宗 |
| ③ | `🍀その他のジャグラーシリーズの優秀台` | （`block_header_names` 未登録＝`{title}` 形式） |
| ④ | `🍀その他の沖スロ系の機種の優秀台` | （同上） |

### 正式な出力形

```
🍀その他の毎日オススメ機種(スマスロ北斗・北斗転生2・東京喰種・ヴヴヴ2・かぐや様)
🏅東京喰種(2/3台)→平均+2,800枚
+4,000枚、+3,500枚
🏅スマスロ北斗の拳(3/4台)→平均+3,125枚
+5,000枚、+4,500枚、+3,200枚

🎁その他の毎日オススメ機種の優秀台
・スマスロ北斗の拳
【2201番台】+5,000枚
【2202番台】+4,500枚
```

### ★🏅にするのはサマリーだけ（他はすべて「・」のまま）

`🏅` の対象は **`_rec_category_summaries()` が生成する全台系／高配分の機種単位サマリー行**だけ。

| 対象外（従来どおり） | 記号 |
|---|---|
| ⑤カテゴリ内の**個別台**（`🎁{title}` 以下の `【○番台】+○枚`） | 形式不変（🏅なし） |
| ⑤カテゴリ内の**機種見出し**（`🎁` 以下） | `block_emojis`（B1=・ / B2=💥 / B3=🤡 / B4=🌺） |
| 末尾 ／ ジャグラー末尾 ／ バラエティ ／ その他の優秀台 | **`・`** |
| 並び ／ 列 | **🏅なし**・`(N台)` 表記 |
| 通常セクションの `🍀全台系濃厚機種` / `🍀高配分機種` | **`・`** |
| 差枚一覧 | `+○,○○○枚` から開始（🏅も🌋💎も付けない） |

**`generate_report_text()` の出力に `🏅` は1件も出ない**（🏅は⑤テキストのカテゴリ内サマリーだけ）。

### 実装構造（`9f274e8`）

```python
_REC_CATEGORY_SUMMARY_HEAD = "🏅"      # 新小岩⑤カテゴリ内サマリー専用

def _result_summary_lines(item, avg, avg_show_thr=0, head="・") -> list[str]   # 既定は「・」
def _rec_category_summaries(..., demoted_names=None, head="・")                # head を透過
```

呼び出しは **`show_auto_page()` の⑧本番1か所だけ**で、
既存の店舗ゲート **`_rec_ban_level = with_slump and store == "新小岩"`**（かつ
`store in EXTENDED_FEATURE_STORES`）の内側から **`head=_REC_CATEGORY_SUMMARY_HEAD`** を渡す。

- **共通既定値 = `・` ／ 新小岩⑤の指定4カテゴリのサマリー = `🏅`** という構造。
- **既定 `head="・"` を変更してはならない**（`zen_dai_section` / `high_ratio_section` と
  他店舗・他ページが即座に壊れる）。
- **新しい全台系／高配分判定は作っていない。**既存 `zen_dai_list` / `high_ratio_list` と
  既存のカテゴリ振り分け結果（`252a39b` の正式仕様）をそのまま使う。
- `hide_summary_names`（下部セクションの表示抑止）は不変。

### 新小岩カテゴリのソース構造（2026-09-11 調査で確定）

**カテゴリ見出しの表示と、実際の抽出対象は別ソースである。**

| 用途 | ソース |
|---|---|
| **見出しカッコ内の表示** | `STORE_REC_CONFIG["新小岩"]["block_header_names"]`（コード内の**略称の固定文字列**） |
| **サマリー／台番一覧の抽出対象** | `store_settings/新小岩.json` の `recommended_machines_N`（UIで編集） |

`_rec_category_summaries()` は **`block["machines"]`（＝`recommended_machines_N`）から機種名集合を作り、
完全一致（`in names`）でサマリー対象を判定**する。**`block_header_names` は抽出判定に使わない。**
部分一致・`startswith`・`contains` は使っていないため、**未登録機種の混入経路はない。**

2026-09-11 時点の実設定は見出しの略称と整合済み：

```
recommended_machines_1 = スマスロ北斗の拳 / 北斗転生2 / 東京喰種 / ヴァルヴレイヴ2 / かぐや様
recommended_machines_2 = カバネリ海門決戦 / モンキーターンV / 炎炎ノ消防隊2 / 真打吉宗
recommended_machines_3 = マイジャグV / ネオアイム / ファンキー2 / ゴージャグ3 /
                         ジャグラーガールズ / ミスジャグ / ハピジャグV / ウルトラミラジャグ
recommended_machines_4 = 沖ドキBLACK / 沖ドキGOLD30 / 沖ドキゴージャス30 / スマートキンハナV /
                         キンハナ30 / ドラハナ閃光30 / チバリヨ2 / ヤバチバ / ダークハイビ
（B5・B6 は空 ／ rec_enabled = True ／ 合計26機種・重複0件）
```

**2系統は自動同期していない。**`block_header_names` を触るときは
`recommended_machines_N` との整合を人が確認すること（自動チェックは未実装）。

### ★誤解防止：「戦コレ6」が②主役機種に出た件（実装の不具合ではない）

2026-09-11 の作業中、テスト報告の代表出力で `🍀その他の主役機種` に **戦コレ6** が
表示された例があったが、**実コード・実設定の不具合ではない。**

- 原因は **`scratchpad/test_medal.py` の合成テストデータ**で、B2 の `machines` に
  `戦コレ6` を入れていたため（完全一致して正しくヒットしただけ）。
- **実設定 `recommended_machines_2` に戦コレ6は含まれない。**
  実設定を使った再検証では **B2 に戦コレ6は混入しない**ことを実測で確認済み。
- **`9f274e8` による機種振り分けの変更はない。**`🏅→・` へ戻すと `9f19e0f`（変更前）と
  バイト完全一致することを実測済み。

**scratchpad のテストデータ自体は正式仕様ではない。**上記は誤解防止のための履歴。

### 重複登録は既存仕様のまま

**同一機種を複数の recommended block へ登録した場合は、該当するすべてのブロックへ表示する。**
**新しい排他ルール（B1優先・最小index優先など）を作らない**（`252a39b` の正式仕様を維持）。
2026-09-11 時点の新小岩実設定は26機種すべてユニークで**重複0件**。

---

## F. 【渋谷新館】結果ポスト用「📈オススメポスター機種の仕掛け📈」（`1146b10`）

対象は**渋谷新館の結果ポスト用（`auto`）結果テキスト内の
`📈オススメポスター機種の仕掛け📈` 配下**。生成は `generate_report_text()` 内の
入れ子関数 **`shibuyashinkan_poster_section()`**（呼び出しは `if store_name == "渋谷新館":` の1か所）。

### 正式なカテゴリ順（固定）

```
📈オススメポスター機種の仕掛け📈

【東京喰種】
【カバネリ海門決戦】
【ジャグラーシリーズ】
【北斗シリーズ】
【3F週間オススメポスター】   ← 既存見出し（今回変更していない）
```

**旧順（スマスロ北斗の拳 → 北斗転生2 → ジャグラーシリーズ → 東京喰種）へ戻さない。**
カテゴリ間は空行1つで統一。**見出しは既存どおり常時表示**（空でも見出しは残す）。

### ① 東京喰種

- チェック連動は **`_checked_pins(2)`（t2＝月間オススメ表①・`date_checks` 日付キー方式）**。
- 項目の文頭 **`📌` → `📍`** ／ 詳細行の文頭 **`🎖️` → `・`**（並び詳細行も `・` を付ける）。
- **チェック条件・抽出条件・台数計算・平均差枚計算・対象機種判定は変更していない。**

### ② カバネリ海門決戦（新規カテゴリ）

- **既存の `weekly_items.json` の `t4`（月間オススメ表②・`machine_name = カバネリ海門決戦`）を利用**。
  **新しいチェック項目は作っていない。**判定は **`_checked_pins(4)`**。
- 既存5項目のうち**チェックが入った項目だけ**を `📍` で表示する（5項目固定表示ではない）。

```
📍オールスター(全台系!?)
📍来栖2分割(高配分◎!?)
📍来栖3分割(高配分〇!?)
📍甲鉄城(列!?)
📍ボーイミーツガール(並び!?)
```

- 項目の種別に応じて**既存データを再利用**して詳細を `・` で出す。**新しい判定計算は追加していない。**

| 項目キーワード | データ元 | 出力形 |
|---|---|---|
| `全台系` | **`zen_dai_list`** | `・カバネリ海門決戦(○/○台)→平均+○,○○○枚` |
| `高配分` | **`high_ratio_list`**（`find_high`） | `・カバネリ海門決戦(○/○台)` |
| `並び` | **`nami_list`** | `・2013-2015番台(3台)→平均+3,400枚` |
| `列` | **`retsu_list`**（`_build_retsu_report_items()`） | `・2065-2068番台(4台)→平均+2,300枚` |

- **項目名・機種名をハードコードしない**（項目文字列はローテ画面の入力値なのでキーワード判定）。
- 内部機種名は **`カバネリ海門決戦`**（`rb_threshold_machines` / `min7_machines` /
  `weekly_items.json t4` の実値と一致）。
- 並び／列の台数表記は上記 C により **`(N台)`**。

### ③ ジャグラーシリーズ

- チェック連動は **`_checked_pins(3)`（t3＝`cell_date_machines` の選択有無で活性判定）**。
- **`📌` → `📍`** ／ **`🎖️` → `・`** ／ **`🍡` → `・`**（機種名行）＋詳細行も `・`。
- **抽出条件・対象機種条件（`juggler_series`）・並び順は変更していない。**

### ④ 北斗シリーズ（新規カテゴリ）

```
【北斗シリーズ】
📍スマスロ北斗の拳
・【2039番台】+4,700枚
・【2037番台】+3,600枚

📍北斗転生2
・【2250番台】+5,500枚
・【2045番台】+3,400枚
```

- 対象は **`スマスロ北斗の拳` と `北斗転生2` の2機種**。
- 抽出は **既存 `extract_bans_1k()`**（`df["機種名"]` × `diff_raw >= 1000`）。
  **+1,000枚以上の台だけ**を出す（+999枚以下は除外・+1,000枚ちょうどは含める）。
- 並び順は **差枚降順 → 同差枚は台番昇順**（`sorted(rows, key=lambda t: (-t[1], t[0]))` で決定論化）。
- 台表示は **`・【○○番台】+○,○○○枚`**（3桁区切り・`+` 付き）。
- **対象台が0台の機種は `📍機種名` を出さない**。2機種とも0台でも**カテゴリ見出しは残す**
  （既存ポスターカテゴリの常時表示に合わせる）。
- **t1（週間オススメ表①＝スマスロ北斗の拳）のチェック項目・高配分・並び詳細は
  北斗シリーズへ出さない**（ユーザー承認済みの決定）。
  **新しいチェック項目は作っていない。**

### ⑤ 渋谷新館 `auto_article` への波及（承認済み）

**`generate_report_text()` を共有しているため、渋谷新館の記事用（`auto_article`）の
結果テキストにも同じ新フォーマットが適用される。**
2026-09-11 の Cloud 確認でユーザーが全体を確認したうえで承認した正式状態。

**ただしこれは「結果テキスト生成経路の共有」によるものであり、
記事用の画像生成・WordPress 本文生成が同じ意味で変更されたわけではない。**

---

## G. 対象となる結果テキスト生成経路（調査済み）

| 生成関数 | 対象ページ |
|---|---|
| **`generate_report_text()`** | `auto`（結果ポスト用）／`auto_slump`／`auto_slump2`／📝記入部分のみ／`auto_article` |
| **`_build_kabupa_result_text()`** | 新宿歌舞伎町 かぶぱ（`auto_slump`） |
| **`generate_recommended_result_text()`** | ⑤オススメ機種（結果ポスト用／スランプ付き） |
| `_generate_rote_result_text()` / `_generate_shibuyashinkan_result_texts()` / `_generate_weekly_result_text()` | ローテ用・週間結果テキスト |

**ローテ／週間系には今回の対象記号（`🎖️` / `🚩` / `🍡` / 差枚行の `🌋` `💎` / `(N台並び)`）が
1件も存在しなかったため、これらの関数は変更していない。**

### ★既存の別用途 `🏅`（混同しない）

週間結果テキスト側の **`_wrt_build_machine_block(df, m, machine_prefix="🏅")`** は
**今回の新小岩⑤の🏅とは別仕様**であり、**変更していない**。

### 変更対象外だった `🎖️` / `🚩`（設定定義・コメント）

| 箇所 | 理由 |
|---|---|
| `STORE_REC_CONFIG["新小岩"]["block_emojis"]` の `🎖️` | **設定定義**。生成時に置換済みで出力0件 |
| `STORE_REC_CONFIG["新小岩"]["item_emoji"]` の `🚩` | 同上 |
| 各所のコメント文 | コメント |
| **`generate_results.py` の `🎖️` 3件** | **git untracked** の別アプリ（`image_generator_app.py` 専用）。`streamlit_app.py` からの参照0件＝現アプリの結果テキスト経路外のため**未変更** |

---

## H. 今回いっさい変更していないもの

抽出条件 ／ 全台系判定 ／ 高配分判定 ／ 並び判定 ／ 列判定 ／ 対象機種 ／ 対象台 ／ 対象末尾 ／
バラエティ判定 ／ 差枚条件 ／ 差枚値 ／ 平均差枚 ／ 台数 ／ 台番 ／ 並び順 ／ チェック状態 ／
保存値（`weekly_items.json` / `store_settings` / `auto_page_inputs.json` ほか）／ Pision取得 ／
機種名変換 ／ 画像生成ロジック ／ スランプ画像 ／ 表画像 ／ パネル ／ 液晶 ／ ZIP ／
WordPress（`wp_client.py`）／ 店舗設定UI ／ `convert_narabi_pil.py` ／ `shimazu_renderer.py`。

**変えたのは結果テキストの表示記号・台数表記・渋谷新館ポスターのカテゴリ構成だけ。**

`run_auto_pipeline` / `run_step1〜3` / `_kojin_yushu_filter` / `filter_recommended_machines` /
`_format_diffs` / `_fmt_diff` / `extract_bans_1k` の判定部 / `_build_retsu_report_items` /
`_save_*` / `_restore_*` は**本体無変更**。

---

## I. テスト・回帰確認結果（2026-09-11）

| commit | 結果 |
|---|---|
| `1c036e7` | **34 PASS / 0 FAIL** |
| `20bb9ea` | **43 PASS / 0 FAIL** |
| `9f274e8` | `test_medal.py` **34 PASS / 0 FAIL** ／ `test_symbols.py` **43 PASS / 0 FAIL** |

- **全13店舗で数値・判定・台番・台数・平均差枚・抽出件数の非回帰を確認**
  （HEAD版の出力へ許可した記号変換だけを適用した結果と新出力が完全一致）。
- **新小岩以外の12店舗は `🏅` 追加による変更なし**（`generate_report_text` が HEAD とバイト一致）。
- **渋谷新館 `1146b10` 仕様維持**（カテゴリ順・チェック連動・カバネリ詳細・北斗+1,000枚・差枚降順・📍）。
- **新宿歌舞伎町3系統（`0e79a80` / `394f309`）維持**（かぶぱ結果テキストも HEAD 一致）。
- **二重記号「・・」の意図しない発生0件。**
- HEAD版との比較は**必ずプロジェクトと同一ディレクトリへ一時配置**して行い、比較後に削除する
  （`BASE_DIR` がずれると `store_settings` / `機種名変換.xlsx` を読めず誤検知する）。

### ★`scratchpad/test_poster.py` の旧期待値（コード回帰ではない）

1タスク目に作った `test_poster.py` は **`(3台並び)` を期待している**ため、
現在仕様 **`(3台)`** に対して **5件 FAIL** する。

**これは今回のコード回帰ではなく、`1c036e7` で正式に変更した表記に古いテスト期待値が
追従していないだけ**である。現行の正式スイートは **`test_symbols.py` / `test_medal.py`**。
**ユーザー承認なしに `test_poster.py` を修正しない。**

---

## J. Cloud 承認

**2026-09-11：ユーザーが Streamlit Cloud の実機で確認し「確認して問題なかったです」と承認。**
よって `1146b10` / `1c036e7` / `20bb9ea` / `9f274e8` の4実装を正式仕様とする。

---

## K. 今後の禁止事項

1. **結果テキストの文頭記号を `🎖️` / `🚩` へ戻さない**
2. **差枚一覧の文頭へ `🌋` / `💎` を戻さない**
3. **`summary_section()` / `juggler_summary_section()` の `🌋万枚オーバー` / `💥+5,000枚` /
   `💎N台が+1,000枚オーバー！` を削除しない**（`🌋`/`💎` の全廃ではない）
4. **`_diff_emoji()` の定義を削除しない**
5. **並び／列へ `🍡` を戻さない／別絵文字へ置換しない／`👑` 見出しを消さない**
6. **`(N台)` を `(N台並び)` へ戻さない**
7. **画像タイトル・ファイル名・パネル判定・記事コメント文の「台並び」を変更しない**
8. **`STORE_REC_CONFIG` の `block_emojis` / `item_emoji` の定義を直接書き換えない**
   （生成時 `.replace()` 方式を維持）
9. **`💥` `🤡` `🌺` `🍀` `⚡️` `⭐` `🎯` や西武新宿の `📍` を「・」へ変えない**
10. **`🎁`（末尾サマリー／⑤の優秀台見出し）を変更しない**
11. **`_result_summary_lines()` / `_rec_category_summaries()` の既定 `head="・"` を変更しない**
12. **`🏅` を新小岩⑤の指定4カテゴリのサマリー以外へ広げない**
    （個別台・末尾・バラエティ・その他の優秀台・並び・列・`🍀全台系濃厚機種`・`🍀高配分機種`・
    `generate_report_text()` 全体には出さない）
13. **`🏅` を他店舗へ広げない**／`_rec_ban_level` の店舗ゲートを外さない
14. **週間結果テキストの `machine_prefix="🏅"`（別仕様）と混同しない・変更しない**
15. **新しい全台系／高配分判定を作らない**（既存 `zen_dai_list` / `high_ratio_list` を使う）
16. **`block_header_names` を抽出判定へ使わない**／`recommended_machines_N` との整合は人が確認する
17. **重複登録時の「該当する全ブロックへ表示」（`252a39b`）を排他化しない**
18. **「戦コレ6が②主役機種に出た」件を実装の不具合として扱わない**（合成テストデータ由来）
19. **渋谷新館ポスターのカテゴリ順（東京喰種→カバネリ→ジャグラー→北斗）を変えない**
20. **カバネリ用に新しいチェック項目を作らない**（`weekly_items.json` の t4 を使う）
21. **北斗シリーズへ t1 のチェック項目・高配分・並び詳細を足さない**
22. **北斗の `+1,000枚以上・差枚降順・同差枚は台番昇順` を変えない**
23. **渋谷新館 `auto_article` の結果テキストだけ旧形式へ分岐させない**（共有経路を維持）
24. **ローテ／週間系の結果テキストへ今回の記号変更を波及させない**
25. **`generate_results.py`（untracked の別アプリ）を勝手に変更しない**
26. **`test_poster.py` をユーザー承認なしに修正しない**
27. **抽出条件・判定・数値・保存値・画像生成・WordPress を今回の記号仕様を理由に変更しない**
28. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】スランプ付き結果ポストの液晶挿入停止（2026-09-11・`ebe881e` / `6fd3991`）

**正式仕様。巻き戻し禁止。**対象は**スランプ付き結果ポスト用（`auto_slump` / `auto_slump2`）の
液晶（空きコマはめ込み）機能だけ**。2026-09-11 に **ユーザーが Streamlit Cloud 実機で確認し
「問題なかったです」と承認**した。

**本セクションは「スランプ付き結果ポスト用途における液晶の使用有無」についての最新正式仕様であり、
過去の液晶セクション（とくに「## スランプ空きコマの液晶はめ込み — 選択キー」2026-07-16・`4695044`）の
うち *結果ポスト用途で液晶を挿入する* という部分を上書きする。**
ただし**過去セクションは削除・圧縮・書き換えしない**。`_gap_sel_key()` の選択キー仕様など、
そこに書かれた**液晶そのものの正式仕様は記事用で今後も使うため引き続き有効**である。

### A. 対象commit

| # | commit | 内容 |
|---|---|---|
| ① | **`ebe881e2b64c578599b538f8a5dd3d63d9e387c3`** | `fix: 新小岩スランプ付き結果の液晶挿入を停止`（新小岩で実験） |
| ② | **`6fd3991d9a63bc235aba73328c004dc741cc7d74`** | `fix: スランプ付き結果の液晶挿入を全対象店舗で停止`（全対象へ展開） |

いずれも **`streamlit_app.py` の1ファイルのみ**。②は **`_GAP_FILL_OFF_SLUMP_STORES` への
4店舗追記だけ（+7/−1 の1ハンク）**で、`_gap_fill_on()` 本体も含めロジックは①のまま。

### B. 変更理由と正式動作

従来はスランプグラフ付き画像で**最終行の空きが2コマ以上**あると
「液晶画像を自動挿入」「`🖼️ 液晶画像を選ぶ` UIを表示」「選択変更で再合成」していた。

**2026-09-11 以降、結果ポスト用途では液晶を使わない。**

| 空きコマ | 正式動作 |
|---|---|
| 0コマ | **液晶なし** |
| 1コマ | **液晶なし** |
| **2コマ** | **液晶なし**（旧仕様では挿入していた） |
| **3コマ以上** | **液晶なし**（同） |

**空き部分は詰めずそのまま空けておく。**
「2コマ以上なら液晶を挿入」という旧仕様は**結果ポスト用途では廃止**。
**ただし `_gap_fillable()` 自体は記事用で必要なので残す。**

### C. 対象店舗・ページ（液晶OFF）

| 店舗 | ページ |
|---|---|
| **新小岩** | `auto_slump` |
| **上野新館** | `auto_slump` |
| **上野本館** | `auto_slump` |
| **秋葉原** | `auto_slump` |
| **新宿歌舞伎町** | **`auto_slump`（📊 かぶぱポストの結果）** と **`auto_slump2`（📈 スランプ付き結果）の両方** |

以上5店舗・6ページ。

### D. 稲毛は「今回OFFにした店舗」ではない

**稲毛 `auto_slump` を `_GAP_FILL_OFF_SLUMP_STORES` へ入れていない。**
稲毛は今回の改修前から **`_GAP_FILL_STORES` に未登録**で、**もともと液晶自動挿入の対象外**だった。

**稲毛は「もともと液晶なしの店舗」として扱う。**「今回OFFにした店舗」と誤記しないこと。
（**稲毛に `auto_article` は存在しない**ことも実測済み。記事用ページを持つのは
高田馬場 / 渋谷新館 / 秋葉原の3店舗だけ。）

### E. `_GAP_FILL_OFF_SLUMP_STORES`（正式）

```python
_GAP_FILL_OFF_SLUMP_STORES: "frozenset[str]" = frozenset({
    "新小岩",
    "上野新館",
    "上野本館",
    "秋葉原",        # auto_slump はOFF。auto_article は _GAP_FILL_STORES 経由で液晶を維持する
    "新宿歌舞伎町",  # auto_slump（かぶぱ）/ auto_slump2 の両方がOFFになる
})
```

**店舗ごとにコードを複製しない。**対象を増やす／戻すときは**この集合の編集だけ**で行う。

### F. `_gap_fill_on()`（結果ポスト経路専用の判定）

```python
def _gap_fill_on(store: str) -> bool:
    """結果ポスト用の液晶はめ込み／液晶選択UIを使うか。
    _GAP_FILL_OFF_SLUMP_STORES の店舗は False（液晶なし・セレクタも出さない）。
    液晶を抜くだけで、表・スランプのレイアウト・サイズは一切変えない。"""
    if store in _GAP_FILL_OFF_SLUMP_STORES:
        return False
    return store in _GAP_FILL_STORES
```

**結果ポスト経路のゲートは `store in _GAP_FILL_STORES` ではなく `_gap_fill_on(store)` を使う。**
呼び出しは **計11箇所**：

| 関数 | 箇所 | 内容 |
|---|---|---|
| `show_auto_page` | **7** | ⑦プレビュー合成 `_is_gap_pv` ／ ⑦液晶セレクタUI ／ 🔄その他を更新（3） ／ ⑧本番（秋葉原タイトル型・通常の2） |
| `_composite_slump_onto_images` | **4** | 秋葉原タイトル型 ／ 通常（表下3列） ／ 横版 `_side` ／ `_gap_meta_`・`_gap_base_` の保存 |

`_composite_slump_onto_images()` は **`show_auto_page` からのみ呼ばれる結果ポスト専用**
（📝記入部分のみ・⑧の2経路）。**記事用からは呼ばれない。**

### G. ★`_GAP_FILL_STORES` を直接変更しない（最重要）

```python
_GAP_FILL_STORES = {"新宿歌舞伎町", "上野新館", "上野本館", "新小岩", "秋葉原"}   # 変更しない
```

**この集合を空にしたり、対象店舗を直接削除したりしてはならない。**

理由：**記事用 `show_auto_article_page` の2ゲートが
`store in _GAP_FILL_STORES or store in _ARTICLE_GAP_FILL_STORES` を見ている**ため、
`_GAP_FILL_STORES` から店舗を外すと**記事用の液晶まで消える**。

とくに **秋葉原**は次が正式仕様で、`_GAP_FILL_STORES` を直接触ると壊れる。

| 秋葉原 | 液晶 |
|---|---|
| `auto_slump` | **OFF（今回）** |
| **`auto_article`** | **ON（従来どおり維持）** |

したがって正式方式は **「結果ポスト側専用の `_gap_fill_on()` でOFFにする」**である。

### H. 記事用（`auto_article`）は液晶機能を維持

**今回の廃止対象ではない。**記事用では今後も
**空き判定・液晶選択・液晶合成・液晶変更・再合成**をすべて使う。

| | 結果ポスト側 | 記事用側 |
|---|---|---|
| ゲート | **`_gap_fill_on(store)`** | `store in _GAP_FILL_STORES or store in _ARTICLE_GAP_FILL_STORES`（19115行は `store == "新宿歌舞伎町" or store in _ARTICLE_GAP_FILL_STORES`） |
| session_state | `_gap_meta_{store}` / `_gap_base_{store}` | **`_art_gap_meta_{store}` / `_art_gap_base_{store}`** |
| セレクタUI | 12733行（今回OFF） | **17815行（維持）** |

**記事用の液晶ゲート（6行）へ `_gap_fill_on()` を使ってはならない。**
`_ARTICLE_GAP_FILL_STORES = {"高田馬場", "渋谷新館"}` も変更しない。

### I. 液晶機能そのものは残す（削除禁止）

**「液晶システム廃止」ではなく「スランプ付き結果ポスト用途では現在使用しない」である。**
次はすべて**残す正式方針**。削除・改造しない。

`_gap_sel_key()` ／ `_gap_fillable()` ／ `_gap_screen_paths_for_bans()` ／
`_resolve_gap_screen()` ／ `_on_gap_screen_change()` ／ `_fit_center_in_box()` ／
`assets/machine_images/` の液晶画像 ／ `masters/machine_image_master.xlsx` ／
液晶選択 session_state ／ **保存済みの液晶選択値** ／ 記事用液晶UI ／ 記事用液晶合成。

**対象店舗で `_gap_meta_{store}` / `_gap_base_{store}` を新規生成・更新しないだけで、
既存値を削除・初期化する仕様ではない。**

### J. 将来スランプ付き結果へ液晶を戻すときの方針

**現在の記事用液晶システムを流用する。**
結果ポスト側に独自の液晶実装を作り直さない。
戻すときは **`_GAP_FILL_OFF_SLUMP_STORES` から店舗を外す**か、必要なら記事用と同じ
`_art_gap_*` 相当の経路を参考にする。

### K. 液晶選択キーの既存正式仕様（維持・削除禁止）

**`_gap_sel_key(store, bans, machine)` は変更していない。**
掲載台番集合単位で保持し、**異なる台番集合は個別選択／同じ台番集合の縦横は選択共有**という
`4695044` の正式仕様もそのまま。**記事用で今後も使うため、過去仕様を削除・上書きしない。**

### L. 結果ポスト側で液晶が止まる範囲

対象店舗では次の**すべて**で液晶OFF。

**⑦プレビュー ／ ⑧本番画像 ／ ZIP ／ 🔄その他を更新 ／ 共通スランプ合成経路
（`_composite_slump_onto_images`）／ 縦版 ／ 横版（`_side.jpg`）**

- **`🖼️ 液晶画像を選ぶ` も表示しない。**
- **CSSで隠しているのではない。** `_gap_fill_on(store) == False` により
  結果ポスト側の液晶ロジック自体へ入らない方式。
- ⑦・🔄・⑧・共通合成が**同一ゲート**なので「⑦だけ消えて⑧では入る」状態は構造的に起こらない。
- ZIP は⑧の出力フォルダを固めるため、⑧が液晶なしなら自動的に液晶なし。

### M. 店舗固有仕様はすべて維持（変えたのは液晶の使用有無だけ）

| 店舗 | 維持するもの |
|---|---|
| 新小岩 / 上野新館 / 上野本館 | 表下スランプ3列 ／ **16台以上の横版4列（`_side.jpg`）** ／ 結果ポスト構成 |
| **秋葉原** | **表なしタイトル型（`_build_slump_title_img()`）／ 横版なし ／ その他の優秀台の可変列（列数 = `ceil(台数/10)`）／ 実列数ベースの空き判定構造** |
| **新宿歌舞伎町** | **パネル合成（`_apply_panel_to_table_img()`）／ `_bar_crop_h()` ／ かぶぱ専用機能** |

**液晶がなくなった空き領域を詰める・列数を変える・表やスランプのサイズを変えるといった
レイアウト変更は行っていない。**

### N. 新宿歌舞伎町3系統との関係（`0e79a80` / `394f309` を維持）

| # | ページ | 今回 |
|---|---|---|
| ① | `auto_slump`（📊 かぶぱポストの結果） | **液晶OFF** |
| ② | `auto_slump2`（📈 スランプ付き結果） | **液晶OFF** |
| ③ | `rote`（📋 ローテ用） | **今回無関係・無変更** |

2026-09-10 の**3系統分離の正式仕様はすべて維持**する。
**10日区切り・「○日目結果」が `rote` 専用**という既存正式仕様も変更しない。

### O. スランプカードデザイン非変更（`0e49bd9` / `5711df4` を維持）

**白基調・淡紫グラデーション・猫・濃紫文字・赤グラフ**の 388×472 カードは完全維持。
`draw_slump_graph()` ／ `_slump_template_image()` ／ `_slump_neko_alpha()` ／
`_attach_slump_to_table()` ／ `_attach_slump_to_table_side()` ／ `_build_slump_title_img()`
は**本体無変更**（HEADとバイト一致を機械確認）。

### P. 表画像デザイン非変更（`a05cb00` を維持）

タイトル **#7000E0** ／ 通常文字 **#4B0082** ／ 列見出し #290068 ／ サマリー #FF6FA5 などの
非記事用表デザインは不変。`draw_table_image()` ／ `_table_theme_new()` ／ `_bar_crop_h()` ／
`_apply_panel_to_table_img()` ／ `_build_panel_row()` も**本体無変更**。

### Q. 結果テキスト非変更（2026-09-11 の記号仕様を維持）

通常の文頭 **`・`** ／ 差枚一覧の行頭 **🌋/💎 なし** ／ 並び・列 **`(N台)`** ／
新小岩⑤の指定4カテゴリの全台系・高配分だけ **🏅** ／ 渋谷新館のポスター機種4カテゴリ ──
**すべて維持**。`generate_report_text()` は**本体無変更**。**今回の液晶停止とは無関係。**

### R. テスト・検証結果

| 段階 | 結果 |
|---|---|
| ① 新小岩実験（`ebe881e`） | **65 PASS / 0 FAIL** → Cloud でユーザー確認「問題なかった」 |
| ② 全対象展開（`6fd3991`） | **160 PASS / 0 FAIL** |

検証は **HEAD版を同一ディレクトリへ一時配置**し、`_composite_slump_onto_images()` の
**実画像を md5 で比較**（液晶3枚が登録済みの機種「北斗」を使用）して行った。

- **新小岩 / 上野新館 / 上野本館 / 秋葉原 / 新宿歌舞伎町 `auto_slump` ／
  新宿歌舞伎町 `auto_slump2`** ── 空き0/1/2/3+ のすべてで**液晶なし**、
  `_gap_meta_` / `_gap_base_` を**書かない**（＝セレクタ非表示）。
  空き2以上では **HEADが液晶を合成していたことも同時に確認**（比較の妥当性）。
- **画像サイズは全ケースでHEADと同一**＝レイアウト不変。
- **縦版＋横版**：新小岩・上野新館・上野本館・新宿歌舞伎町で17台投入し
  縦版＋`_side.jpg` の2枚・**両方とも液晶なし・サイズHEAD同一**。
  **秋葉原は `_side.jpg` を作らない既存仕様**も維持。
- **秋葉原のタイトル型・可変列**：`その他の優秀台ピックアップ.jpg` を12台（実列2）／
  25台（実列3）で検証し**サイズがHEADと完全同一**。
- **新宿歌舞伎町のパネル**：4台・7台で**パネル込みサイズがHEADと同一**（`_bar_crop_h()` 維持）。
- **稲毛**：1/3/4/7/17台すべて**HEADと画像・meta・base が完全一致**（もともと液晶なし）。
- **非対象7店舗**（西武新宿・新大久保・赤坂見附・溝の口本館・溝の口新館・高田馬場・渋谷新館）も
  **HEADと完全一致**。
- **記事用**：秋葉原・高田馬場・渋谷新館の**記事用ゲートが True のまま**（HEADと同値）。
  `show_auto_article_page` の**液晶ゲート6行がHEADとバイト完全一致**、
  `_art_gap_meta_` / `_art_gap_base_` / セレクタの出現数もHEADと同数。
  **記事用への `_gap_fill_on()` 混入0件。**
- `assets` / `masters` に変更0件。`_gap_sel_` の出現数もHEADと同数で、
  **液晶選択 session_state を削除するコードは追加していない。**

### S. Cloud 承認

**2026-09-11：全対象店舗へ展開後、ユーザーが Streamlit Cloud 実機で確認し
「問題なかったです」と承認。**よって `ebe881e` / `6fd3991` を正式仕様とする。

### T. 今後の禁止事項

1. **結果ポスト用途で液晶の自動挿入を復活させない**（`_GAP_FILL_OFF_SLUMP_STORES` から
   対象店舗を勝手に外さない）
2. **`_GAP_FILL_STORES` を空にしない／対象店舗を直接削除しない**（記事用が壊れる）
3. **`_ARTICLE_GAP_FILL_STORES` を変更しない**
4. **記事用の液晶ゲート（6行）へ `_gap_fill_on()` を使わない**
5. **秋葉原の `auto_article` の液晶を消さない**（`auto_slump` だけOFF）
6. **`_gap_fill_on()` を記事用・ローテ用など結果ポスト以外へ広げない**
7. **`_gap_sel_key()` / `_gap_fillable()` / `_gap_screen_paths_for_bans()` /
   `_resolve_gap_screen()` / `_on_gap_screen_change()` / `_fit_center_in_box()` を削除・改造しない**
8. **液晶画像 assets・機種画像マスタ・保存済み液晶選択値・session_state を削除・初期化しない**
9. **`_gap_fillable()` を「もう使わないから」と削除しない**（記事用で必要）
10. **稲毛を「今回OFFにした店舗」と記録しない**（もともと液晶なし）／
    稲毛を `_GAP_FILL_OFF_SLUMP_STORES` へ追加しない
11. **液晶がなくなった空き領域を詰めない**（表・タイトル・スランプ・列数・サイズ・余白・
    パネル・縦版・横版を変更しない）
12. **秋葉原のタイトル型・横版なし・可変列（`ceil(台数/10)`）を変更しない**
13. **新宿歌舞伎町のパネル合成・`_bar_crop_h()`・かぶぱ専用機能・3系統分離を変更しない**
14. **`rote` を今回の対象に含めない**
15. **スランプカードデザイン（`0e49bd9` / `5711df4`）・表デザイン（`a05cb00`）・
    結果テキスト（2026-09-11）を今回を理由に変更しない**
16. **⑦だけ／⑧だけOFFにしない**（同一ゲートを維持）／CSSで隠す方式へ変えない
17. **過去の液晶正式仕様セクション（`4695044` ほか）を削除・書き換えない**
18. **将来復活させるときは記事用システムを流用する**（結果ポスト専用の液晶実装を新造しない）
19. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】ローテ画像の外背景・差枚凡例削除（2026-09-11・`6b87aa4`）

**正式仕様。巻き戻し禁止。**対象は**ローテ用ページ（`page == "rote"`）で生成される画像だけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で全8店舗を確認し「Cloud確認で問題なし」と承認**した。

**本セクションはローテ用画像の外周デザイン（外背景・差枚凡例）についての最新正式仕様である。**
既存のローテ関連セクション（`c59dd90` / `f23e0e4` / `a011c33` ほか）は**削除・圧縮・書き換えしない**。
それらの「`generate_rote_image()` 本体は変更しない」「`_add_margin()` は無変更」という記述は
**当時の正式仕様として正しく**、本セクションでは
**`generate_rote_image()` へ既定 `True` の `with_legend` 引数を1つ追加**し、
**`_add_margin()` は本体を変更せず呼び出しだけをやめた**という関係になる
（既定値のままなら従来と完全に同一出力）。

### A. 実装commit（1本だけ）

| commit | 内容 |
|---|---|
| **`6b87aa4f1beb577e5249d679d7f01ff8f70494df`** | `fix: ローテ画像の外背景と凡例削除を全店舗へ展開` |

**`streamlit_app.py` の1ファイルのみ・+66/−25。**

### ★O. 新宿歌舞伎町の先行実装は別commitではない（誤記しないこと）

新宿歌舞伎町では全店舗展開の前に**ローカル画像で先行確認**したが、
**その時点では commit / push していない**。実装は**未コミットの `streamlit_app.py`** として
作業ツリーに保持されていた（`git log -S"_ROTE_PLAIN_STORES" --all` の結果は **`6b87aa4` の1件だけ**）。

その後、**残り7店舗への展開とまとめて `6b87aa4` として commit / push** された。

### ★P. したがって `6b87aa4` が唯一の正式実装commit

**「新宿歌舞伎町の先行実装commit＋全展開commit」という2commit構成ではない。**
**この経緯を「先行commitが存在する」と記録してはならない。**
**`6b87aa4` 以前へ reset して先行実装を分離し直すことも禁止。**

### B. Cloud 承認

**2026-09-11：`6b87aa4` push 後、ユーザーが Cloud で全8店舗のローテ画像を確認し
「Cloud確認で問題なし」と承認。**

### C. 対象店舗（rote 入口を持つ8店舗すべて）

| # | 店舗 |
|---|---|
| 1 | 新宿歌舞伎町 |
| 2 | 高田馬場 |
| 3 | 上野本館 |
| 4 | 渋谷新館 |
| 5 | 西武新宿 |
| 6 | 新大久保 |
| 7 | 溝の口本館 |
| 8 | 溝の口新館 |

**全8店舗で同一方針。**（rote 入口を持たない 稲毛・新小岩・上野新館・秋葉原・赤坂見附は
そもそもこの経路を通らないため対象外。）

### D. 差枚数画像（`generate_rote_image()`）の新仕様

```
【旧】 凡例4行（1,000枚～／3,000枚～／5,000枚～／万枚オーバー）
       ↓ #CFEEEE の帯
       列ヘッダー（台番／日付）
       機種名の黒帯 ＋ 台番・差枚の行 …
       ↑ この全体を #CFEEEE の台紙（外周40px）が囲む

【新】 列ヘッダー（台番／日付）      ← 画像の上端
       機種名の黒帯 ＋ 台番・差枚の行 …
       最終機種の最終台番行          ← 画像の下端
       （外側の地・台紙・padding なし）
```

- **表の最背面にあった薄い地（#CFEEEE の台紙）を削除**
- **上部の凡例4行を削除**（`1,000枚～` / `3,000枚～` / `5,000枚～` / `万枚オーバー`）
- **凡例直下の薄い帯（#CFEEEE）も削除**
- **凡例を削除した跡の空白は残さない**
- **上端＝「台番／日付」の列ヘッダー行（日付セル）**
- **下端＝指定機種の最終台番を含む最終行**
- **左右も表本体の端**
- 表外の不要な padding／台紙／地は付けない

**残すもの**：日付セル ／ 台番 ／ 機種名（黒帯）／ 差枚数 ／ セル背景 ／ 条件別配色
（黄 `#FFFF00`・橙 `#FFC000`・赤 `#FF4343`・万枚のレインボー）／ 罫線 ／ 文字 ／
既存の表示順 ／ 既存の数値。

### E. 仕掛け表（週間／月間オススメ表）の新仕様

- **表の外側にあった薄い地／台紙（`_add_margin` の外周40px）を削除し、表本体だけを画像化**
- **内部タイトル・日付ヘッダー・項目・○セル・罫線・文字・セル背景・配色・行列構成は
  すべて維持**（HEADと画素完全一致）
- **`_draw_weekly_table_image()` / `_weekly_table_html_image()` の描画ロジック本体は変更していない。**
  変えたのは**完成した表画像へ `_add_margin()` を付けないこと**だけ。
  表は外周に黒罫線を持つため、**表の端が画像の端**になる。

### F. `_ROTE_PLAIN_STORES`（正式）

```python
_ROTE_PLAIN_STORES: "frozenset[str]" = frozenset({
    "新宿歌舞伎町",
    "高田馬場",
    "上野本館",
    "渋谷新館",
    "西武新宿",
    "新大久保",
    "溝の口本館",
    "溝の口新館",
})
```

**店舗ごとにコードを複製しない。**対象を変えるときは**この集合の編集だけ**で行う。

### G. `_rote_plain(store)`

```python
def _rote_plain(store: str) -> bool:
    """ローテ用画像を表本体だけ（地・凡例なし）にする店舗か。"""
    return store in _ROTE_PLAIN_STORES
```

### H. `_rote_margin(store, img)`

```python
def _rote_margin(store: str, img: "Image.Image") -> "Image.Image":
    """ローテ用画像の外枠マージン。_rote_plain() の店舗は付けずに表本体を返す。"""
    return img if _rote_plain(store) else _add_margin(img)
```

**ローテ対象店舗では `_add_margin()` を付けず、表本体をそのまま返す。**
`show_rote_page()` / `show_weekly_table_section()` の**旧 `_add_margin(...)` 呼び出し6箇所は
すべて `_rote_margin(store, ...)` へ差し替え済み**で、
**この2関数の中に `_add_margin(` の直接呼び出しは1件も残っていない。**

### I. `generate_rote_image(..., with_legend: bool = True)`

```python
def generate_rote_image(df, machine_names, date_label="", store="",
                        with_legend: bool = True) -> Image.Image:
```

- ローテ8店舗では **`with_legend=not _rote_plain(store)` → `False`** で呼ぶ（呼び出し2箇所）。
- **既定は `True`**。引数を渡さない呼び出しは**従来と画素完全一致**。

### J. 凡例 228px の扱い（★文字だけ消すのではない）

```
LEG_H = 26 * SC = 52px  × 4行 = 208px
GAP_H = 10 * SC = 20px（#CFEEEE の帯）
                 合計 228px
```

**この228pxは「文字を描かない」だけでなく、`generate_rote_image()` の高さ計算そのものから除外する。**

```python
_head_h = (LEG_H * 4 + GAP_H) if with_legend else 0
total_h = _head_h + COL_HDR_H + Σ(MAC_H + ROW_H × 台数)
```

**したがって凡例跡の空白は残らない。**
**「文字を非表示にして228pxの領域を残す」実装にしてはならない。**

### K. ★`_add_margin()` は削除しない

従来の薄い地は `_add_margin()` が
`Image.new("RGB", (w + 40, h + 40), "#CFEEEE")` の新規canvasを作り、
表画像を中央へ `paste` することで作っていた（背景画像でも透明合成でもない **padding付き台紙**）。

**ローテ8店舗ではこの外背景を使用しないが、`_add_margin()` そのものは削除していない。**
将来別用途で使う可能性があるため**既存関数は残す**。
呼び出しが残っているのは **`_rote_margin()` の中（非対象店舗向けの else 側）だけ**。

### L. ★固定cropではない

**完成後に固定座標で crop する方式ではない。**

- 差枚数画像：**`generate_rote_image()` の高さ計算から凡例部分を除外**
- 外周：**`_add_margin()` を付けない**

したがって **台数・機種数・行数が変化しても自動追従**する。
**固定cropで代替してはならない。**

### M. ランキング画像は対象外

**`generate_ranking_image()` は今回いっさい変更していない。**
もともと `_add_margin()` を通らず、凡例も持たず、外側の薄い地もなかった。
**全8店舗で修正前HEADと画素一致を確認済み。**

### N. 店舗別セル配色は維持

差枚数画像の台番列などの店舗別配色（`ROTE_BAN_COLOR_CONFIG`）はそのまま。
検証で確認した実値：

| 店舗 | 台番列の色 |
|---|---|
| 新宿歌舞伎町 | `#FFF2CD` |
| 高田馬場 | `#EA5A96` |
| 上野本館 | `#EA5A96` |
| 渋谷新館 | `#F7EBCB` |
| 新大久保 | `#AED6F1` |
| その他（西武新宿・溝の口本館・溝の口新館） | 既定 `#00FFCC` |

**今回変更したのは外背景と凡例だけで、セル内部の配色は変更していない。**

### Q. 新宿歌舞伎町3系統との関係

| # | ページ | 今回 |
|---|---|---|
| ① | `auto_slump`（📊 かぶぱポストの結果） | **対象外・無変更** |
| ② | `auto_slump2`（📈 スランプ付き結果） | **対象外・無変更** |
| ③ | **`rote`（📋 ローテ用）** | **今回の変更対象** |

`0e79a80` / `394f309` の3系統分離の正式仕様はすべて維持する。

新宿歌舞伎町のローテ固有正式仕様（**1〜10日 / 11〜20日 / 21〜30日 /
31日がある月は21〜31日 / 「○日目結果」**）も**今回変更していない**。
`_generate_rote_result_text()` も**本体無変更**。

### R. ローテ判定・結果テキストは非変更

**今回の変更は画像デザイン（外背景と凡例）だけ。**
ローテ判定 ／ 対象機種 ／ 台番 ／ 差枚数 ／ 表示順 ／ 日付処理 ／ 結果テキスト ／
店舗設定 ／ 仕掛け内容 は**すべて維持**。

### S. 非ローテページは非変更

`auto` ／ `auto_slump` ／ `auto_slump2` ／ `auto_article` は**今回対象外**。
次の既存正式仕様も維持：
スランプカード新デザイン（`0e49bd9` / `5711df4`）／ 非記事用表デザイン（`a05cb00`）／
結果テキスト 2026-09-11 仕様 ／ 新小岩⑤の🏅 ／ 渋谷新館のポスター機種結果テキスト ／
スランプ付き結果ポストの液晶停止（`6fd3991`）／ 記事用液晶維持 ／ 液晶選択キー ／
パネル合成 ／ Pision ／ WordPress。

### T. プレビュー／本番／ZIP は同一画像を共有

- 差枚数画像は **`_rote_imgs` という同一画像リスト**を
  **プレビュー（`st.image`）・ダウンロードボタン・本番保存（`.save`）・ZIP（`_make_zip_bytes`）**で共有する。
- 仕掛け表も **`_wt_img` の同一画像オブジェクト**を保存に使う。

**したがって「プレビューだけ新仕様・本番だけ旧背景あり」という分岐は構造的に存在しない。**

### U. 可変台数テスト

**8店舗 × 4ケース＝32通り**で確認：**3台 ／ 10台 ／ 30台 ／ 2機種（6台+6台）**。

差枚数画像：凡例なし ／ 凡例跡の空白なし（高さ減が**全ケース228pxちょうど**）／
上端＝日付セル（`#606060`）／ 下端＝最終台番行 ／ 外側 `#CFEEEE` **0px** ／ padding なし ／
**表本体の内容がHEADの凡例より下と画素完全一致**（台番・差枚・機種名・行順・セル配色も同一）。

仕掛け表：外側の地なし ／ padding なし（HEAD−40px）／
**内部タイトル・日付ヘッダー・項目・○セル・罫線・配色・内容がHEADと画素完全一致**
（4項目×7日／2項目×3日の可変列でも確認）。

**最終台番行が欠けず、最終行の下に余白も残らない。**

### ★新宿歌舞伎町の非回帰（全店舗展開で承認済みデザインが変化していないこと）

`_ROTE_PLAIN_STORES` を **`{"新宿歌舞伎町"}` だけに戻した状態**と **8店舗版**を同一データで比較し、
**新宿歌舞伎町の差枚数画像・仕掛け表がともに画素完全一致**（4ケースすべて）。
**全店舗展開によって新宿歌舞伎町の承認済みデザインは変化していない。**

### V. テスト結果

**383 PASS / 0 FAIL。**

次の関数の**本体が修正前HEADとバイト一致**であることも機械確認済み：

`generate_ranking_image` ／ `_generate_rote_result_text` ／ `show_auto_page` ／
`show_auto_article_page` ／ `_composite_slump_onto_images` ／ `draw_table_image` ／
`draw_slump_graph` ／ `generate_report_text` ／ `_draw_weekly_table_image` ／
`_weekly_table_html_image` ／ `_weekly_table_data` ／ `_slump_template_image` ／
`_attach_slump_to_table` ／ `_gap_fill_on` ／ `_build_slump_title_img` ／ `_add_margin`。

**新規関数は `_rote_plain` / `_rote_margin` の2つだけ・削除関数0。**

### W. Cloud 承認（再掲）

**2026-09-11：`6b87aa4` push 後に Cloud で全8店舗を確認し、ユーザーが
「Cloud確認で問題なし」と承認。**よって `6b87aa4` を正式仕様とする。

### X. 今後の禁止事項

1. **ローテ差枚画像へ `1,000枚～` / `3,000枚～` / `5,000枚～` / `万枚オーバー` の凡例を
   勝手に戻さない**
2. **凡例を消したまま228pxの空白だけ戻さない**（高さ計算からの除外を維持する）
3. **ローテ画像へ `#CFEEEE` の外背景（台紙・padding）を勝手に戻さない**
4. **`_add_margin()` 自体は削除しない**（`_rote_margin()` の else 側で使用中・将来用に残す）
5. **固定cropで代替しない**（高さ計算からの除外＋マージン非付与の方式を維持）
6. **表内部のセル背景・店舗別色（`ROTE_BAN_COLOR_CONFIG`）を消さない**
7. **仕掛け表内部のタイトル・日付ヘッダー・○セル・罫線・配色を削らない**
   （`_draw_weekly_table_image()` / `_weekly_table_html_image()` の本体を変更しない）
8. **`generate_ranking_image()` を巻き込まない**（もともと地なし・凡例なし）
9. **ローテ判定・差枚抽出・対象機種・台番・表示順・日付処理・結果テキスト・店舗設定を変更しない**
10. **`auto` / `auto_slump` / `auto_slump2` / `auto_article` へ適用しない**
11. **新宿歌舞伎町の10日区切り（1〜10／11〜20／21〜30／31日がある月は21〜31）や
    「○日目結果」を変更しない**
12. **`6b87aa4` 以前へ reset して先行実装を分離し直さない**／
    **「新宿歌舞伎町の先行実装commitが存在する」と記録しない**
13. **`generate_rote_image()` の `with_legend` 既定値 `True` を変更しない**
    （引数を渡さない他経路の非回帰が壊れる）
14. **`_ROTE_PLAIN_STORES` を店舗名の個別ハードコードへ展開しない**（集合の編集だけで行う）
15. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】スランプ付き結果・グラフエリア背景 #FFFFCB（2026-09-11・`3432a97`）

**正式仕様。巻き戻し禁止。**対象は**スランプ付き結果（`auto_slump` / `auto_slump2`）で
スランプカードを並べる「グラフエリアの外側の地」だけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で確認し「問題なかった」と承認**した。

既存のスランプ関連セクション（`0e49bd9` / `5711df4` の白＋淡紫カード、
`ebe881e` / `6fd3991` の液晶停止、`a05cb00` の表デザイン、`6b87aa4` のローテ画像など）は
**削除・圧縮・統合・書き換え・並べ替えしない**。本節は**カード外側の地についてだけ**の追記である。

### A. 実装commit（1本だけ）

| commit | 内容 |
|---|---|
| **`3432a97b37a08555d61d0b3f3394837da727714e`** | `fix: スランプ付き結果のグラフエリア背景を#FFFFCBの単色へ` |

**`streamlit_app.py` の1ファイルのみ・+31/−18。**
**この commit が今回の正式実装commitである。**
**なお `3432a97` は「正式仕様の根拠となる実装commit」であって、
HEAD をここへ戻すという意味ではない。`3432a97` へ reset してはならない。**

### B. Cloud 承認

**2026-09-11：`3432a97` push 後、ユーザーが Cloud の「スランプ付き結果」を実機確認し
「問題なかった」と承認。**

### C. ★レインボー背景の正体は `bbb.jpg` だった

調査の結果、レインボーは **`draw_slump_graph()` や `_slump_template_image()` が
生成しているカード内部の背景ではなかった。**

正体は **`画像作成/bbb.jpg`**（**2512 × 8813** のパステル系レインボー画像）で、
これを**グラフエリアへ resize して貼り付けていた**。

実測色の例：

```
(166, 251, 230)   (251, 241, 156)
(182, 179, 246)   (245, 166, 198)
```

### D. ★カード内部ではなく「カード外側のグラフエリア」だった

| | 内容 | 今回 |
|---|---|---|
| **カード内部** | `draw_slump_graph()` / `_slump_template_image()` が作る **388×472** のスランプカード（白＋淡紫デザイン・機種名・台番・軸・グリッド・0ライン・赤いスランプ線・猫・フレーム） | **変更していない** |
| **カード外部** | 複数の388×472カードを 表の下／横／タイトル型 で並べるときの **「カードを並べるグラフエリアの地」** | **今回の変更対象** |

**この2つを今後も混同してはならない。**
レインボーはカードの外側に見えていた地であり、カード内部の淡紫デザインとは別物である。

### E. 正式色

| | 値 |
|---|---|
| HEX | **`#FFFFCB`** |
| RGB | **(255, 255, 203)** |

**かなり薄い黄色。近似色ではない。今後もこの値を正式値として扱う。**

### F. 単色でありグラデーションではない

変更後は **`#FFFFCB` 一色の単色背景**である。**黄色系グラデーションではない。**
次は使用しない：**レインボー ／ 色相変化 ／ 複数色グラデーション ／ `bbb.jpg` の色**。

### G. 対象店舗（正式スランプテーマ6店舗）

**稲毛 ／ 新小岩 ／ 上野新館 ／ 上野本館 ／ 秋葉原 ／ 新宿歌舞伎町**

（`_SLUMP_THEME_STORES` の既存6店舗集合。**この集合は変更していない。**）

### H. 対象ページ

**`auto_slump` ／ `auto_slump2`**
＝**正式な新スランプテーマが ON になるページ**（`_SLUMP_THEME_PAGES`）。

### I. ★`auto_article` は非対象

**記事用は今回変更していない。**
今回変更した3つの合成関数は `auto_article` 側でも共有されているが、
**`_slump_theme_new()` のゲートが False になるため、記事用では従来どおり `bbb.jpg` を維持する。**

```
スランプ付き結果 → #FFFFCB
記事用           → 従来仕様（bbb.jpg）
```

**今後「共通関数だから」という理由で `auto_article` まで `#FFFFCB` へ変更してはならない。**

### J. ★`rote` は完全非対象

**ローテ用は今回いっさい変更していない。**
直前に正式化した **実装 `6b87aa4f1beb577e5249d679d7f01ff8f70494df` ／
正式記録 `061e42f3bf4ddf95451448a9d6a686c62a6d5990`** の仕様
（**外地削除 ／ 差枚凡例削除 ／ 上端＝日付セル・下端＝最終台番行 ／ 仕掛け表の外地削除**）は
**すべて維持**する。10日区切り・「○日目結果」・ローテ画像仕様にも変更はない。

### K. `C_SLUMP_AREA_BG`

```python
C_SLUMP_AREA_BG = (255, 255, 203)   # #FFFFCB
```

**`#FFFFCB` の定義はこの共通定数の1箇所だけ。**各所へ数値を散らさない。

### L. `_paste_slump_area_bg()`（共通ヘルパー）

```python
def _paste_slump_area_bg(canvas, bg_path, x0, y0, w, h) -> None:
    if w <= 0 or h <= 0:
        return
    if _slump_theme_new():
        canvas.paste(Image.new("RGB", (w, h), C_SLUMP_AREA_BG), (x0, y0))
        return
    if bg_path is None:
        return
    try:
        canvas.paste(Image.open(str(bg_path)).convert("RGB").resize((w, h), Image.LANCZOS),
                     (x0, y0))
    except Exception:
        pass
```

**背景だけを塗る関数で、カード・液晶・表・座標には触れない。**
`Image.open(str(bg_path))` の出現は**このヘルパー内の1箇所だけ**＝
`bbb.jpg` を貼る処理は完全に集約済み。

### M. `_slump_theme_new()` のゲート

| 判定 | 背景 |
|---|---|
| **True**（対象6店舗 × `auto_slump` / `auto_slump2`） | **`#FFFFCB` の単色** |
| **False**（記事用など） | **従来どおり `_find_slump_bg()` → `bbb.jpg`** |

**`_slump_theme_new()` 本体は変更していない**（page × store の AND・保存フラグなし・
Streamlit 外では False という既存正式仕様のまま）。

### N〜P. 変更した3つの合成経路

`bbb.jpg` を貼っていた箇所は調査の結果**3箇所**だった。
いずれも従来の `Image.open(bg_path).resize(...)` + `canvas.paste(...)` を
**共通 `_paste_slump_area_bg()` へ置き換えた**。

| # | 関数 | レイアウト | 変更する領域 |
|---|---|---|---|
| **N** | **`_attach_slump_to_table()`** | 表下3列 | 表の下のスランプカード配置エリアの地 |
| **O** | **`_attach_slump_to_table_side()`** | 横版4列 | 横側のスランプカード配置エリアの地 |
| **P** | **`_build_slump_title_img()`** | 秋葉原タイトル型 | タイトル画像内のスランプカード配置エリアの地 |

**いずれもカードそのものではなく、カードの外側に見える背景領域**を `#FFFFCB` にする。

### Q. スランプカード内部は非変更

次はすべて**変更禁止**（今回、修正前HEADと**画素md5一致**を確認済み）：

`draw_slump_graph()` ／ `_slump_template_image()` ／ `_slump_neko_alpha()` ／
**388×472 サイズ** ／ 白＋淡紫カードデザイン ／ 機種名 ／ 台番 ／ 文字色 ／ フォント ／
赤いスランプ線 ／ 軸 ／ 目盛り ／ グリッド ／ 0ライン ／ 猫 ／ 猫の濃さ ／ 猫の位置 ／
猫のサイズ ／ フレーム ／ グラフ座標 ／ スランプデータ。

### R. 猫は非変更

**2026-09-10 に正式化したスランプカードの猫仕様（`assets/slump/neko_5000_1.bmp` ／
`_SL_NEKO_K = 0.198` ／ mask ／ alpha ／ 位置 ／ サイズ）は完全維持。**
今回それらに一切触れていない。

**`#FFFFCB` にしたのは猫が存在する388×472カードの内部ではなく、カードの外側の地である。**
**今後も混同しないこと。**

### S. ★`bbb.jpg` は削除しない

**`bbb.jpg` そのものは削除していない。**
`_slump_theme_new()` が False になる従来系の経路（**とくに `auto_article`**）で
**引き続き使用するため**である。

**「スランプ付き結果では使わなくなった」＝「`bbb.jpg` を削除してよい」ではない。**
`bbb.jpg` は維持する（`git ls-files` で追跡済みであることを確認済み）。

### T. ★`_find_slump_bg()` は削除しない

**`_find_slump_bg()` も削除禁止。**
新スランプテーマ OFF 時に従来背景を取得するために必要である。
（`show_auto_page` / `show_auto_article_page` / `_composite_slump_onto_images` ほか
計7箇所から呼ばれている。）

### U. ⑦プレビュー／⑧本番／ZIP は共通経路

**⑦プレビュー ／ 🔄その他を更新 ／ ⑧本番生成 ／ 液晶再合成経路 ／ ZIP** は
いずれも最終的に今回変更した**3つの合成関数**を使用する。
`bbb.jpg` を直接貼る処理は共通ヘルパーへ集約済みなので、

**「プレビューだけ `#FFFFCB` で本番はレインボー」という分岐は構造的に存在しない。**

### V. 画像サイズは非変更

**3レイアウトとも完成画像サイズが修正前HEADと完全一致。**
背景変更によって **幅 ／ 高さ ／ カード配置 ／ 余白 ／ 座標**は変更していない。

### W. 新テーマOFF時はHEADと画素一致

`_slump_theme_new() == False` の経路では、**合成後画像そのものが修正前HEADと
画素md5完全一致**。＝記事用等の旧背景経路には変更が出ていない。

### X. テスト結果

**49 PASS / 0 FAIL**（`import streamlit_app` 成功 ／ `ast.parse` OK）。

新テーマONで**対象領域が `(255,255,203)`**・**`bbb.jpg` 由来のレインボー／緑系画素0**、
新テーマOFFで**合成後画像がHEADと画素md5一致**、
**3レイアウト × ON/OFF すべてでカード本体の画素md5一致**、
**画像サイズがHEADと同一**を確認。

次の17関数がソース一致（本体無変更）であることも機械確認済み：

`draw_slump_graph` ／ `_slump_template_image` ／ `_slump_neko_alpha` ／
`draw_table_image` ／ `_build_machine_img` ／ `generate_rote_image` ／ `_rote_margin` ／
`_rote_plain` ／ `show_rote_page` ／ `show_auto_article_page` ／ `_gap_fill_on` ／
`_gap_sel_key` ／ `_gap_fillable` ／ `_composite_slump_onto_images` ／
`generate_report_text` ／ `_find_slump_bg` ／ `find_slump_template`。

**HEAD版との比較は必ずプロジェクトと同一ディレクトリへ一時配置して行う**
（`BASE_DIR` がずれると `store_settings` / `機種名変換.xlsx` / 猫アセットを読めず誤検知する。
今回この誤検知が実際に発生し、同一ディレクトリ配置で解消した）。

### Y. その他の既存正式仕様も維持

非記事用表画像の新デザイン（`a05cb00`）／ 白＋淡紫スランプカード（`0e49bd9` / `5711df4`）／
猫 ／ 結果テキスト2026-09-11仕様 ／ 新小岩⑤の🏅 ／ 渋谷新館ポスター機種結果テキスト ／
スランプ付き結果ポストの液晶停止（`ebe881e` / `6fd3991`）／ 記事用液晶維持 ／ 液晶選択キー ／
パネル合成 ／ Pision ／ WordPress ── **すべて非変更**。

### Z. 今後の禁止事項

1. **対象のスランプ付き結果でグラフエリア背景を `bbb.jpg` のレインボーへ勝手に戻さない**
2. **`#FFFFCB` を近似色へ変更しない**
3. **`#FFFFCB` を黄色系グラデーションへ変更しない**
4. **カード内部まで `#FFFFCB` にしない**
5. **白＋淡紫の388×472スランプカードを変更しない**
6. **猫の濃さ・位置・サイズ・mask を変更しない**
7. **赤線・軸・グリッド・0ラインを変更しない**
8. **`bbb.jpg` 自体を削除しない**
9. **`_find_slump_bg()` を削除しない**
10. **`auto_article` へ `#FFFFCB` を勝手に展開しない**
11. **`rote` へ今回の仕様を適用しない**
12. **店舗別に同じ背景処理を複製しない**（共通 `_paste_slump_area_bg()` を維持）
13. **固定crop や画像サイズ変更で実現しない**
14. **カード配置座標や表との結合位置を変更しない**
15. **スランプデータや結果テキストを巻き込まない**
16. **`C_SLUMP_AREA_BG` 以外へ `#FFFFCB` の数値を散らさない**
17. **`_slump_theme_new()` のゲート（page × store の AND）を変更しない**
18. **⑦だけ／⑧だけ変更しない**（3関数の共通経路を維持）
19. **`3432a97` へ reset しない**
20. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町ローテ・ランキング画像生成停止（2026-09-11・`7a47c12`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】のローテ用（`page == "rote"`）で生成される
`ranking_*.png` だけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で「📋 ローテ用」を確認し「問題なし」と承認**した。

既存のローテ関連セクション（`c59dd90` / `f23e0e4` / `a011c33` / `6b87aa4`＋記録 `061e42f` ほか）は
**削除・圧縮・統合・書き換え・並べ替えしない**。本節は**ランキング画像の生成有無だけ**の追記である。

### A. 実装commit（1本だけ）

| commit | 内容 |
|---|---|
| **`7a47c1220b0e4983d58818144f05f409ebf7fcd5`** | `fix: 新宿歌舞伎町ローテのランキング画像生成を停止` |

**`streamlit_app.py` の1ファイルのみ・+23/−6・変更関数は `show_rote_page()` のみ・
新規関数は `_rote_ranking_on()` のみ・削除関数0。**

**この commit は「正式仕様の根拠となる実装commit」であって、
HEAD をここへ戻すという意味ではない。`7a47c12` へ reset してはならない。**

### B. Cloud 承認

**2026-09-11：`7a47c12` push 後、ユーザーが Cloud で
【新宿歌舞伎町】→【📋 ローテ用】を実機確認し「問題なし」と承認。**

### C. 対象

**【新宿歌舞伎町】の `page == "rote"` だけ。**

### D. `ranking_*.png` を今後生成しない

例：**`ranking_炎炎ノ消防隊2ローテ.png`**

2026-09-11 以降、**新宿歌舞伎町のローテ用ではこの種類の画像は不要**であり生成しない。

### E. ★「非表示」ではなく「生成しない」

**ランキング画像を作ったうえで画面から隠す仕様ではない。**

新宿歌舞伎町 rote では次のすべてを満たす。

- **`generate_ranking_image()` を呼ばない**
- **ランキング画像を生成しない**
- **プレビュー用にも生成しない**
- **保存しない**
- **ZIP へ新規格納しない**
- **0byte ファイルも作らない**
- **空画像も作らない**

＝**最初からランキング画像の生成経路へ入らない**ことが正式仕様である。

### F. `generate_ranking_image()` の実呼び出しは元々1箇所だけ

調査の結果、**`generate_ranking_image()` の実コード上の呼び出しは1箇所だけ**だった
（コメント行の言及は除く）。

### G. その呼び出しは `_rote_single` の内側だった

その1箇所は **`if _rote_single:` の内側**にあり、
**`_ROTE_SINGLE_STORES` の対象は「新宿歌舞伎町」**である。

したがって**実際に `ranking_*.png` を生成していたのは新宿歌舞伎町だけ**だった。

### H. ★他7店舗は元からランキング画像を生成していなかった（誤認禁止）

rote 入口がある他7店舗

**高田馬場 ／ 上野本館 ／ 渋谷新館 ／ 西武新宿 ／ 新大久保 ／ 溝の口本館 ／ 溝の口新館**

について、**「今回の変更後もランキング画像を生成し続ける」という意味ではない。**

調査の結果、**これら7店舗は変更前からランキング画像を生成していなかった。**
開始時点から **`_rank_imgs = [None] * len(_rote_imgs)`** となる経路で、
**`generate_ranking_image()` を呼んでいない。**

正式な理解：

| 店舗 | 変更前 | 変更後 |
|---|---|---|
| **新宿歌舞伎町** | **従来はランキング画像を生成していた** | **`7a47c12` 以降は生成しない** |
| **他7店舗** | **もともと生成していない** | **今回もそのまま** |

**今後「他7店舗ではランキング画像を生成している」と誤って記録・実装してはならない。**

### I. 最終的な rote 8店舗の状態

結果として現在、**rote 入口が存在する8店舗すべてで `ranking_*.png` は生成されない。**

ただし**実装上の経緯は異なる**。

| 店舗 | 経緯 |
|---|---|
| **新宿歌舞伎町** | **今回 `7a47c12` で OFF** |
| **他7店舗** | **以前から生成経路に入っていない** |

**この違いを混同しないこと。**

### J. `_ROTE_RANKING_OFF_STORES`

```python
_ROTE_RANKING_OFF_STORES: "frozenset[str]" = frozenset({
    "新宿歌舞伎町",
})
```

**店舗ごとにコードを複製しない。**対象を増やす／戻すときは**この集合の編集だけ**で行う。
`_ROTE_SINGLE_STORES` の直後に新設してある。

### K. `_rote_ranking_on(store)`

```python
def _rote_ranking_on(store: str) -> bool:
    """ローテ用でランキング画像を生成するか（OFF店舗は生成・保存・ZIPとも0件）。"""
    return store not in _ROTE_RANKING_OFF_STORES
```

**小さな述語関数でランキング画像を生成するかを判定する。**

### L. `show_rote_page()` のゲート

```python
if _rote_ranking_on(store):
    _rank_imgs = [
        generate_ranking_image(df, _ci, date_label=_rote_date_label, store=store)
        if _cn else None
        for _ci, _cn in zip(_cat_inputs, _cat_names)
    ]
else:
    _rank_imgs = [None] * len(_rote_imgs)
```

**`_rote_ranking_on(store)` が True のときだけ `generate_ranking_image()` へ入る構造。**
新宿歌舞伎町では False になるため **`_rank_imgs` は `None` の配列**となり、
ランキング画像生成を行わない。

### M. ★`generate_ranking_image()` は削除しない

**`generate_ranking_image()` 本体は今回削除していない。変更もしていない**
（修正前HEADとバイト一致を機械確認済み）。

**ランキング画像が現在不要だからといって、関数・定数・描画ロジックを削除してはならない。**
将来の再利用や過去仕様確認の可能性がある。

**今回の正式仕様は「関数削除」ではなく「新宿歌舞伎町 rote から生成経路へ入らない」である。**

### N. ★既存 `ranking_*.png` を削除しない

今回の変更は **「今後生成しない」**である。
**過去に作成済みの `ranking_*.png` を検索・削除する仕様ではない。**

次を勝手に削除してはならない：
**ローカルの過去成果物 ／ Git管理ファイル ／ Cloud上の既存成果物 ／ ZIP等に残っている過去ファイル。**

**削除処理（cleanup）を新設しないこと。**

### O. プレビュー経路には元からランキングが無い

調査の結果、**`_rank_imgs` はプレビュー経路
（`_pv_items` / `img1` / `img2` / `img3` / `st.image` 等）に入っていなかった。**

つまり、ランキング専用の
**プレビュー ／ 見出し ／ 空白枠 ／ 空画像 ／ エラー表示は、もともと存在しない。**

**今回、ランキング画像停止に伴う追加UI削除は不要だった。**

### P. 保存経路（None ガードで保存されない）

既存の保存処理は **`if _crank:`** でガードされている。
新宿歌舞伎町ではランキング画像が `None` になるため **`.save()` へ入らない**。

したがって **ranking ファイル保存なし ／ 0byte ファイルなし ／ 空画像なし ／
ファイル名だけ作ることもなし。**

### Q. ZIP 経路

ZIP は **`_make_zip_bytes(_rote_out_dir)`** で出力フォルダをまとめる構造。
新宿歌舞伎町では ranking 画像を新規保存しないため、
**今回生成する成果物として `ranking_*.png` は ZIP へ入らない。**
差枚数画像など必要な既存成果物は従来どおり。

### R. ★過去ファイルの扱い（自動削除しない）

ZIP がフォルダ単位で作られる構造であるため、
**過去の `ranking_*.png` が同じ出力フォルダへ物理的に残っているケース**については、
**今回の実装が既存ファイルを削除するものではない**ことを明確にする。

正式仕様は **「今回の生成処理では ranking 画像を新規生成・保存しない」**である。
**過去成果物を自動削除する仕様へ勝手に拡張してはならない。**

### S. 差枚数画像は維持

新宿歌舞伎町 rote の**差枚数画像は従来どおり生成する。**

```
スマスロ北斗の拳ローテ.png
炎炎ノ消防隊2ローテ.png
```

**今回停止したのは `ranking_*.png` だけ。**

### T. 仕掛け表も維持

仕掛け表も従来どおり生成する。
直前に正式化したローテ画像仕様
（**実装 `6b87aa4f1beb577e5249d679d7f01ff8f70494df` ／
正式記録 `061e42f3bf4ddf95451448a9d6a686c62a6d5990`**）の

**外背景なし ／ 差枚凡例なし ／ 画像上端＝日付セル ／ 画像下端＝最終台番行 ／
仕掛け表の外地なし ／ 表内部デザイン維持**

を**完全維持**する。

### U. ローテ結果テキスト維持

**`_generate_rote_result_text()` は変更していない。**結果テキストも従来どおり。

### V. 新宿歌舞伎町ローテ固有仕様も維持（10日区切り）

以下は**非変更**：

**1〜10日 ／ 11〜20日 ／ 21〜30日 ／ 31日がある月は21〜31日 ／ 「○日目結果」 ／
ローテ判定 ／ 対象機種 ／ 台番 ／ 差枚数 ／ 表示順 ／ 日付処理 ／
`_generate_rote_result_text()` ／ 結果テキスト。**

**ランキング画像停止によってローテ判定そのものを変えてはならない。**

### W. 新宿歌舞伎町3系統と他ページは非変更

| # | ページ | 今回 |
|---|---|---|
| ① | `auto_slump`（📊 かぶぱポストの結果） | **完全非対象・無変更** |
| ② | `auto_slump2`（📈 スランプ付き結果） | **完全非対象・無変更** |
| ③ | **`rote`（📋 ローテ用）** | **今回の変更対象** |

`auto` ／ `auto_slump` ／ `auto_slump2` ／ `auto_article` はいずれも**非変更**。
**今回のランキング停止を他ページへ展開してはならない。**

また、直近の
**実装 `3432a97b37a08555d61d0b3f3394837da727714e` ／
正式記録 `6366b3ed8d0993cc613e3c175b281ca3542f7b98`** の
**スランプ付き結果・グラフエリア背景 `#FFFFCB`** も**完全非変更**。
今回の ranking 停止とは無関係である。

### X. テスト結果

**100 PASS / 0 FAIL**（`ast.parse` OK ／ `import streamlit_app` OK）。

**新宿歌舞伎町**：`generate_ranking_image()` 呼び出し0 ／ `ranking_*.png` 新規生成0 ／
`ranking_炎炎ノ消防隊2ローテ.png` 新規生成なし ／ ランキング preview なし ／
空白枠なし ／ 空画像なし ／ エラーなし ／ 不要見出しなし ／ 0byte なし ／
差枚数画像は従来どおり ／ 仕掛け表は従来どおり ／ ZIP の今回生成成果物に ranking なし。

**他7店舗**：従来からランキング生成なし ／ 修正前HEADと呼び出し回数一致 ／
保存件数一致 ／ 出力ファイル集合一致。

**`generate_ranking_image()` 本体は修正前HEADとバイト一致。**
**ローテ8店舗の差枚数画像は修正前HEADと画素一致。**
**仕掛け表も修正前HEADと画素一致。**

**HEAD版との比較は必ずプロジェクトと同一ディレクトリへ一時配置して行う**
（`BASE_DIR` がずれると `store_settings` / `機種名変換.xlsx` を読めず誤検知する）。

### Y. Cloud 承認（再掲）

**2026-09-11：`7a47c12` push 後に Cloud で【新宿歌舞伎町】→【📋 ローテ用】を確認し、
ユーザーが「問題なし」と承認。**よって `7a47c12` を正式仕様とする。

### Z. 今後の禁止事項

1. **新宿歌舞伎町 rote で `ranking_*.png` を勝手に再生成しない**
2. **ランキング画像を非表示にするだけの方式へ戻さない**（生成経路へ入らない状態を維持）
3. **`generate_ranking_image()` 自体を削除しない**
4. **ランキング描画用の共通定数・ロジックを「不要だから」という理由だけで削除しない**
5. **既存の過去 ranking 画像を勝手に削除しない**
6. **過去 ranking 画像を削除する cleanup 処理を勝手に追加しない**
7. **他7店舗について「現在 ranking を生成している」と誤認しない**
   （他7店舗は今回以前から生成していない）
8. **差枚数画像を止めない**
9. **仕掛け表を止めない**
10. **`6b87aa4` / `061e42f` のローテ画像デザインを巻き戻さない**
11. **10日区切り・「○日目結果」を変更しない**
12. **`_generate_rote_result_text()` を変更しない**
13. **`auto` / `auto_slump` / `auto_slump2` / `auto_article` へ今回のゲートを広げない**
14. **`3432a97` / `6366b3e` の `#FFFFCB` スランプ背景仕様を巻き込まない**
15. **過去commitへ reset して実装をやり直さない**

## 2026-09-11 ローテ画像 紫系配色 全8店舗正式採用

**正式仕様。巻き戻し禁止。**対象は**ローテ用ページ（`page == "rote"`）で生成される
差枚ローテ画像 `{機種名}ローテ.png` の配色だけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で全8店舗を確認し「問題なし」と正式承認**した。

既存のローテ関連セクション（`c59dd90` / `f23e0e4` / `a011c33` / `6b87aa4`＋記録 `061e42f` /
`7a47c12`＋記録 `a17ea22` ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。
本節は**差枚ローテ画像の配色だけ**を追加する仕様である。

### A. 正式実装commit（2本）

| # | commit | 内容 |
|---|---|---|
| ① 先行 | **`a2bd8f74557e17afd5c47d8e433e9f11ddca18e0`** | `feat: 新宿歌舞伎町ローテ画像を紫系配色へ変更` |
| ② 全展開 | **`9084f935ad5e0bd04339c71c6b2aa096515f5b66`** | `feat: ローテ画像の紫系配色を全店舗へ展開` |

`a2bd8f7` で**新宿歌舞伎町のみ先行実装 → ローカル確認 → Cloud確認で承認**を得たのち、
`9084f93` で**`_ROTE_NEW_THEME_STORES` へ7店舗を追記するだけ**（`streamlit_app.py` のみ・
**+13 / −3・1ハンク**・新規関数0・削除関数0・本体が変わった関数0）で全8店舗へ展開した。

**`9084f93` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。
`a2bd8f7` / `9084f93` へ reset してはならない。**

### B. Cloud 承認

**2026-09-11：`9084f93` push 後、ユーザーが Cloud で【全8店舗】の「📋 ローテ用」を
実機確認し「問題なし」と正式承認。**

### C. 対象ページ・対象店舗

**対象は `page == "rote"` だけ。**
ローテ入口を持つ**全8店舗**が対象である。

```python
_ROTE_NEW_THEME_STORES: "frozenset[str]" = frozenset({
    "高田馬場",
    "上野本館",
    "新宿歌舞伎町",
    "溝の口本館",
    "溝の口新館",
    "西武新宿",
    "渋谷新館",
    "新大久保",
})
```

| # | 店舗 | `_rote_new_theme()` |
|---|---|---|
| 1 | 高田馬場 | **True** |
| 2 | 上野本館 | **True** |
| 3 | 新宿歌舞伎町 | **True** |
| 4 | 溝の口本館 | **True** |
| 5 | 溝の口新館 | **True** |
| 6 | 西武新宿 | **True** |
| 7 | 渋谷新館 | **True** |
| 8 | 新大久保 | **True** |

**ローテ入口を持たない店舗（稲毛・新小岩・上野新館・秋葉原・赤坂見附）および未知店舗・
空文字は False**（実測確認済み）。**これらを集合へ追加しない。**

### D. 正式な4色（`generate_rote_image()` の `{機種名}ローテ.png`）

| # | 対象 | 旧 | **正式（新）** |
|---|---|---|---|
| ① | **台番・日付ヘッダー背景** | `#606060` | **`#7000E0` RGB(112, 0, 224)** |
| ② | **機種名背景** | `#000000` | **`#290068` RGB(41, 0, 104)** |
| ③ | **台番セル背景** | 店舗別（`#FFF2CD` / `#EA5A96` / `#F7EBCB` / `#AED6F1` / `#00FFCC`） | **`#C7B4DD` RGB(199, 180, 221)** |
| ④ | **台番数字の文字** | `#000000`（`"black"`） | **`#4B0082` RGB(75, 0, 130)** |

- **ヘッダー文字＝白（`#FFFFFF`）／機種名文字＝白（`#FFFFFF`）を維持する。**
  今回文字色を変えたのは**④台番数字だけ**である。
- **差枚数の文字色・セル条件配色（黄 `#FFFF00` / 橙 `#FFC000` / 赤 `#FF4343` /
  万枚のレインボー）・罫線 `#000000` / 空セル `#FFFFFF` は変更していない。**

### E. 色の由来（新色を考案していない）

| 色 | 由来 |
|---|---|
| **① `#7000E0`** | 既存の**非記事用高配分画像の紫タイトルバー正式色**（`C_NEW_TITLE_BG_RGBA`） |
| **② `#290068`** | 既存の**非記事用高配分画像の機種名／ヘッダー系背景の正式な濃紺紫**（`C_NEW_HEADER_BG`） |
| **④ `#4B0082`** | 既存の**非記事用表画像のデータ文字色（濃い紫）**（`C_NEW_DATA_FG`） |
| **③ `#C7B4DD`** | **ローテ用台番セル背景として正式採用した薄紫**（ユーザー選択値） |

**①②④は既存定数をそのまま参照している。新しい色定数を作っていない。**

### F. ★`C_ROTE_NEW_BAN_BG` は用途分離（`C_SL_PURPLE` と統合しない）

```python
C_ROTE_NEW_BAN_BG = "#C7B4DD"   # RGB(199, 180, 221)
```

**値はスランプカードの `C_SL_PURPLE`（`#C7B4DD`）と同値だが、
ローテ側の変更でスランプ・高配分の定数へ影響を出さないため、
ローテ専用定数として用途を分けて管理する。**

**`C_SL_PURPLE` / `C_NEW_TITLE_BG_RGBA` / `C_NEW_HEADER_BG` / `C_NEW_DATA_FG` /
`ROTE_BAN_COLOR_CONFIG` は変更していない。**
**同値だからといって定数を統合・共用してはならない。**

### G. 正式実装構造（ゲート1本・描画側へ店舗別ifを増やさない）

```python
def _rote_new_theme(store: str) -> bool:
    """ローテ用画像を紫系配色にする店舗か（未登録店舗は従来配色のまま）。"""
    return store in _ROTE_NEW_THEME_STORES
```

`generate_rote_image()` 内で**1回だけ**解決し、4色を切り替える。

```python
_rote_new = _rote_new_theme(store)
C_BAN_BG  = (C_ROTE_NEW_BAN_BG if _rote_new
             else ROTE_BAN_COLOR_CONFIG.get(store, "#00FFCC"))   # ③台番列
C_HDR_BG  = (C_NEW_TITLE_BG_RGBA[:3] if _rote_new else "#606060")  # ①ヘッダー
C_HDR_FG  = "#FFFFFF"
C_BORDER  = "#000000"
C_EMPTY   = "#FFFFFF"
C_MAC_BG  = C_NEW_HEADER_BG if _rote_new else "#000000"            # ②機種名
C_MAC_FG  = "#FFFFFF"
C_BAN_FG  = C_NEW_DATA_FG if _rote_new else "black"                # ④台番文字
```

- **`_ROTE_NEW_THEME_STORES` の参照は `generate_rote_image()` の1箇所だけ。**
- `show_rote_page()` の `generate_rote_image()` 呼び出し2箇所は**ともに `store=store` を渡す**ため、
  **集合の拡張だけで全8店舗へ効く**。
- **新しい店舗別 if 文を各描画処理へ分散させない。**
- **将来対象店舗を変更する場合は `_ROTE_NEW_THEME_STORES` の編集だけで行う。**
  店舗名を個別ハードコードへ展開しない。

### H. ★仕掛け表は今回の対象外（従来デザイン維持）

**Cloud承認済みの正式仕様は
【差枚ローテ画像のみ紫系新テーマ】／【仕掛け表は従来デザイン維持】である。**

調査結果（実コードで確認）：

| 4項目 | 仕掛け表での該当 |
|---|---|
| 台番セル背景 | **該当する構造が存在しない**（台番セルがない） |
| 機種名背景帯 | **存在しない**（機種名は黄色セル内の小さなテキスト） |
| 日付ヘッダー | **独自配色 `#D0D0D0` ＋黒文字**（ローテの濃グレー＋白文字とは別デザイン） |
| タイトルバー | 黒だが**表タイトル**であり「機種名背景」とは意味が異なる |

したがってユーザー指示「**4項目と対応しない独自配色がある場合はそこは変更しない**」に従い、
**`_draw_weekly_table_image()` / `_weekly_table_html_image()` などの仕掛け表描画は
今回いっさい変更していない**（修正前HEADと **md5 完全一致**・新4色の混入 **0px**）。

**差枚ローテ画像の色を機械的に仕掛け表の無関係セルへ塗ってはならない。**

### I. 既存ローテ画像デザインとの組み合わせ

次の既存正式仕様は**引き続き有効**である。

| | commit |
|---|---|
| 実装 | **`6b87aa4f1beb577e5249d679d7f01ff8f70494df`** |
| 正式記録 | **`061e42f3bf4ddf95451448a9d6a686c62a6d5990`** |

内容：**外背景なし ／ 差枚凡例なし ／ 画像上端＝日付セル ／ 画像下端＝最終台番行 ／
仕掛け表の外地なし。**

**今回の紫系配色はこの正式デザインの上に追加された新仕様である。**
つまり**現在の正式ローテ画像は**

```
【外背景なし】＋【差枚凡例なし】＋【紫系4色テーマ】
```

**の組み合わせ**である。

**`#CFEEEE` の外背景や `1,000枚～` / `3,000枚～` / `5,000枚～` / `万枚オーバー` の凡例を
復活させてはならない**（実測で外背景 0px・凡例ON/OFF差 228px を確認済み）。

### J. ranking 仕様は独立して維持（今回書き換えない）

新宿歌舞伎町の **ranking 画像生成停止仕様**は今回と独立した既存正式仕様として維持する。

| | commit |
|---|---|
| 実装 | **`7a47c1220b0e4983d58818144f05f409ebf7fcd5`** |
| 正式記録 | **`a17ea22643ab05530fe10afad1610174b77ece02`** |

- **新宿歌舞伎町 rote から `generate_ranking_image()` を呼ばない。**
- **`_ROTE_RANKING_OFF_STORES` / `_rote_ranking_on()` は今回変更していない**
  （新宿歌舞伎町 False ／ 他7店舗 True を実測確認）。
- **他7店舗へ新たな ranking 生成処理を追加していない。**
- **今回の配色記録で ranking 仕様を書き換えたり統合削除したりしてはならない。**

### K. 新宿歌舞伎町のローテ固有仕様は維持

**1〜10日 ／ 11〜20日 ／ 21〜30日 ／ 31日がある月は21〜31日 ／ 「○日目結果」 ／
`_generate_rote_result_text()`** はすべて**非変更**。

**今回の正式配色変更は見た目（4色）だけであり、
ローテ判定・期間処理・対象機種・表示順・日付処理・結果テキスト・台番処理には影響しない。**

### L. 他ページは非対象

**今回の正式仕様の対象は `rote` だけ。**

**非対象**：`auto` ／ `auto_slump` ／ `auto_slump2` ／ `auto_article` ／ `work`
（いずれもAST一致で非変更を確認済み）。

**高配分画像は色の参照元だが、高配分画像そのものの仕様変更ではない。**
非記事用表画像の既存定数・描画も変更していない。

### M. スランプ仕様とも独立

次は**今回と独立した既存正式仕様**として維持する（すべて非変更）：

**388×472 スランプカード ／ `C_SL_PURPLE` ／ 猫画像 ／ グリッド ／ 軸色 ／
`#FFFFCB` のグラフエリア背景 ／ `_SLUMP_THEME_STORES` ／ `_paste_slump_area_bg()`。**

**`#C7B4DD` が `C_SL_PURPLE` と同値でも、ローテ用の正式色は
`C_ROTE_NEW_BAN_BG` として用途を分離して扱う。**

### N. 正式確認結果

- **全8店舗で4色を実測**（① `#7000E0` ② `#290068` ③ `#C7B4DD` ④ `#4B0082`）。
  旧 `#606060` と旧台番色は **0px**。ヘッダー・機種名の白文字あり。
- **新宿歌舞伎町は先行承認commit `a2bd8f7` と md5 完全一致**
  （4ケース × 凡例ON/OFF ＝ 8通り）＝**承認済みデザインは全店舗展開後も変化していない**。
- **残り7店舗は対象領域だけ配色変更**（領域ベース比較）：
  差枚列（データ行）md5 一致 ／ 差分画素はヘッダー行・機種名帯・台番列に限定（想定外差分0）／
  allowed 領域の白文字画素一致 ／ **台番インクの差分はインク境界1px以内のみ**（孤立差分0）／
  インク質量差1%以内＝文字の追加・欠落・移動なし。
- **画像サイズ不変 ／ 列幅不変 ／ 行高不変 ／ セル位置不変 ／ 罫線不変 ／ 余白不変 ／
  フォント不変 ／ 文字位置不変 ／ 文字内容不変 ／ 差枚データ不変 ／ ファイル名不変。**
- **外背景なし維持 ／ 差枚凡例なし維持。**
- **仕掛け表 md5 一致（従来デザイン維持）。**
- **ranking 仕様維持 ／ 他ページ非回帰（AST一致）／ 既存色定数非変更。**
- **プレビュー・本番保存・ZIP は同一 `_rote_imgs` を共有**
  ＝「プレビューだけ新配色」という状態は構造的に発生しない。
- **Cloud で全8店舗を承認済み（2026-09-11）。**

### O. 今後の禁止事項

1. **ローテ差枚画像の4色を旧配色（`#606060` / `#000000` / 店舗別台番色 / 黒文字）へ戻さない**
2. **①②④に新しい色を考案しない**（既存 `C_NEW_TITLE_BG_RGBA` / `C_NEW_HEADER_BG` /
   `C_NEW_DATA_FG` を参照する）
3. **`C_ROTE_NEW_BAN_BG` を `C_SL_PURPLE` と統合・共用しない**
4. **`C_SL_PURPLE` / `C_NEW_*` / `ROTE_BAN_COLOR_CONFIG` を変更しない**
5. **ヘッダー文字・機種名文字の白を変更しない**
6. **差枚数の文字色・セル条件配色（黄・橙・赤・レインボー）・罫線・空セルを変更しない**
7. **`_ROTE_NEW_THEME_STORES` を店舗名の個別ハードコードへ展開しない**
8. **描画処理へ店舗別 if 文を分散させない**
9. **ローテ入口を持たない店舗（稲毛・新小岩・上野新館・秋葉原・赤坂見附）を集合へ追加しない**
10. **仕掛け表へ紫系4色を塗らない**（`_draw_weekly_table_image()` /
    `_weekly_table_html_image()` を変更しない）
11. **`#CFEEEE` の外背景・差枚凡例を復活させない**（`6b87aa4` / `061e42f` を維持）
12. **ranking 仕様（`7a47c12` / `a17ea22` / `_ROTE_RANKING_OFF_STORES` /
    `_rote_ranking_on()`）を書き換え・統合削除しない**
13. **新宿歌舞伎町の10日区切り・「○日目結果」・`_generate_rote_result_text()` を変更しない**
14. **ローテ判定・期間処理・対象機種・表示順・台番処理・ファイル名を変更しない**
15. **`auto` / `auto_slump` / `auto_slump2` / `auto_article` / `work` へ適用しない**
16. **高配分画像そのもの・非記事用表画像の定数と描画を変更しない**
17. **スランプ関連（388×472・`C_SL_PURPLE`・猫・グリッド・軸・`#FFFFCB`・
    `_SLUMP_THEME_STORES`・`_paste_slump_area_bg()`）を変更しない**
18. **`a2bd8f7` / `9084f93` へ reset して実装をやり直さない**
19. **プレビューと本番で異なる配色にしない**（同一 `_rote_imgs` 共有を維持）
20. **無関係なリファクタ・未使用コード整理をしない**

## 2026-09-11 上野本館・渋谷新館 ローテ表画像 紫系配色正式採用

**正式仕様。巻き戻し禁止。**対象は**ローテ用ページ（`page == "rote"`）で
【上野本館】【渋谷新館】が生成する週間／月間オススメ表 `{機種名}表.png` の配色だけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で両店舗の「📋 ローテ用」→「表.png」を確認し
「問題なし」と正式承認**した。

既存のローテ関連セクション（`c59dd90` / `f23e0e4` / `a011c33` / `6b87aa4`＋記録 `061e42f` /
`7a47c12`＋記録 `a17ea22` / **`a2bd8f7`・`9084f93`＋記録 `4914bed`** ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。

### A. 正式実装commit

| # | commit | 扱い |
|---|---|---|
| ① | **`fdcf3496ea9590cf3c40bebe926318434153b109`**（`feat: ローテ表画像を紫系配色へ変更`） | **未承認版。Cloud確認でイメージと違ったため正式採用しない**（履歴としてのみ残る） |
| ② | **`8a85e34ded29cd93791e52c014343a482690dfdc`**（`fix: ローテ表画像の紫系配色を再調整`） | **正式版（Cloud承認済み）** |

`fdcf349` は構造（ゲート・両renderer対応・`theme_new` 引数）を導入した commit であり、
**構造はそのまま `8a85e34` へ引き継がれている**。
`8a85e34` は **`streamlit_app.py` のみ・+26/−19** で**色の割り当てと項目文字色だけ**を修正した。

**`fdcf349` / `8a85e34` へ reset してはならない**（正式仕様の根拠commitであって、
HEAD をそこへ戻すという意味ではない）。

### B. ★`fdcf349` の配色は正式仕様ではない（誤記しないこと）

`fdcf349` 時点の配色（**未承認**）:

| 対象 | `fdcf349`（未承認） |
|---|---|
| タイトルバー | `#290068` |
| 日付セル | `#7000E0` |
| 項目セル | `#4B0082` ＋ **白文字** |
| チェック済みセル | `#C7B4DD` |

**この配色へ戻してはならない。**現在の正式配色は下記 D のとおり。

### C. Cloud 承認

**2026-09-11：`8a85e34` push 後、ユーザーが Cloud で【上野本館】【渋谷新館】の
「📋 ローテ用」→「表.png」を実機確認し「問題なし」と正式承認。**

### D. 正式配色（`{機種名}表.png`）

| 対象 | 背景 | 文字 |
|---|---|---|
| **タイトルバー** | **`#4B0082` RGB(75, 0, 130)** | **白** |
| **日付セル** | **`#7000E0` RGB(112, 0, 224)** | **白** |
| **項目セル** | **`#C7B4DD` RGB(199, 180, 221)** | **黒** |
| **チェック済みセル** | **`#FFFFCB` RGB(255, 255, 203)** | **黒**（`○`・機種名とも） |
| **チェック前セル** | **白（従来どおり）** | 従来どおり |

色の流れ（`fdcf349` → `8a85e34`）:

```
タイトルバー     #290068 → #4B0082
項目セル         #4B0082 → #C7B4DD（白文字 → 黒文字）
チェック済みセル #C7B4DD → #FFFFCB
日付セル         #7000E0 → 変更なし
チェック前セル   白      → 変更なし
```

**罫線 `#000000` ／ 白セル `#FFFFFF` は変更していない。**

### E. ★項目セルの文字色は黒（白へ戻さない）

`fdcf349` では項目セルが `#4B0082`（濃紫）だったため白文字にしていたが、
正式版では背景が **`#C7B4DD`（淡紫）**になったので**黒文字**とする。
完成画像を目視して黒文字の方が明確に可読と確認した。

実装上は `fdcf349` で白へ変えた2行（PIL の `_draw_mixed(..., C_BK)` ／
html の `fill=(0, 0, 0)`）を**元の記述へ復元**しており、
`_item_centered` も `fdcf349` より前と同一形に戻っている。

**`#C7B4DD` の項目セルに白文字を入れてはならない。**

### F. 対象ページ・対象店舗

**対象は `page == "rote"` の【上野本館】【渋谷新館】だけ。**

```python
_ROTE_WEEKLY_NEW_THEME_STORES: "frozenset[str]" = frozenset({
    "上野本館",
    "渋谷新館",
})


def _rote_weekly_new_theme(store: str) -> bool:
    """ローテ用「表.png」を紫系配色にする店舗か（未登録店舗は従来配色のまま）。"""
    return store in _ROTE_WEEKLY_NEW_THEME_STORES
```

**ローテ入口を持つ他6店舗（高田馬場・新宿歌舞伎町・溝の口本館・溝の口新館・西武新宿・
新大久保）および稲毛・新小岩・上野新館・秋葉原・赤坂見附・未知店舗・空文字は False**
（実測確認済み）。**表を作らない店舗を集合へ追加しない。**

### G. ★`_ROTE_NEW_THEME_STORES` と混同しない（統合禁止）

| 定数 | 対象画像 | 店舗数 |
|---|---|---|
| **`_ROTE_NEW_THEME_STORES`** | **`{機種名}ローテ.png`（差枚ローテ画像）** | **全8店舗** |
| **`_ROTE_WEEKLY_NEW_THEME_STORES`** | **`{機種名}表.png`（週間／月間オススメ表）** | **上野本館・渋谷新館の2店舗** |

**意味が違うので統合・流用してはならない**（流用すると表を作らない6店舗まで表テーマONになる）。
対象店舗の変更は**該当する集合の編集だけ**で行う。

### H. renderer は2系統・同じ配色を出す

| 店舗 | 使用renderer |
|---|---|
| **上野本館** | **`_draw_weekly_table_image()`（PIL・checksモード／t2・t4・t5）** |
| **渋谷新館** | **`_draw_weekly_table_image()`（t2・t4）** ＋ **`_weekly_table_html_image()`（t3・`cell_machines` モード）** |

**両renderer で同じ正式配色を出力する。片方だけ変更してはならない。**
実画像で両系統とも ① `#4B0082` ② `#7000E0` ③ `#C7B4DD` ④ `#FFFFCB` を確認済み。

### I. `theme_new: bool = False` の既定値を変更しない

両renendrer は **`theme_new: bool = False`** を持ち、
**既定（引数省略）では従来配色を維持**する。
`_draw_weekly_table_image()` は `cell_machines` モードのとき
`_weekly_table_html_image(..., theme_new=theme_new)` へ透過する。

呼び出しは **`show_rote_page()` の保存2箇所 ＋ `show_weekly_table_section()` の
UIプレビュー2箇所＝計4箇所**で、いずれも **`theme_new=_rote_weekly_new_theme(store)`** を渡す。

**既定 `False` を変更してはならない**（他経路の非回帰が壊れる）。
`theme_new=False` の出力は HEAD コードと **md5 完全一致**（checks／cells 両モード）を確認済み。

### J. ★`#FFFFCB` は同色だが用途分離（スランプ側へ依存させない）

```python
C_ROTE_WEEKLY_CK_BG = "#FFFFCB"   # RGB(255, 255, 203)  ← 表専用
C_SLUMP_AREA_BG     = (255, 255, 203)   # #FFFFCB       ← スランプ専用（変更しない）
```

**HEX は同じだが、同じ用途・同じ定数ではない。**
表テーマのチェック済みセルは **表専用定数 `C_ROTE_WEEKLY_CK_BG`** を使い、
**スランプ側の `C_SLUMP_AREA_BG` / `_paste_slump_area_bg()` へ直接依存させない**
（`C_ROTE_NEW_BAN_BG` と `C_SL_PURPLE` を分けているのと同じ用途分離）。

**同値だからといって定数を統合・共用してはならない。**

スランプ側の正式仕様（実装 `3432a97b37a08555d61d0b3f3394837da727714e` ／
記録 `6366b3ed8d0993cc613e3c175b281ca3542f7b98`）は**完全に維持**する
（`C_SLUMP_AREA_BG` / `_paste_slump_area_bg()` / `_attach_slump_to_table(_side)` /
`_build_slump_title_img()` / `_slump_theme_new()` / 388×472カード / `C_SL_PURPLE` /
猫 / グリッド / 軸 — すべて非変更。スランプカードは HEAD と md5 完全一致を確認済み）。

### K. ★`4914bed` の「仕掛け表は従来デザイン維持」を後発仕様で上書き（過去記録は残す）

既存記録 **`4914bed727508bb2f6c95caea82f7792c5a57d87`（`docs: ローテ画像の紫系配色を正式仕様化`）**
の節「## 2026-09-11 ローテ画像 紫系配色 全8店舗正式採用」には、
**H.「仕掛け表は今回の対象外（従来デザイン維持）」／
【差枚ローテ画像のみ紫系新テーマ】【仕掛け表は従来デザイン維持】** と記録されている。

**この記述は `4914bed` 時点の正式仕様として正しく、削除・修正・書き換えしない。**

履歴関係は次のとおり：

```
4914bed 時点   : 表.png は従来配色（黒タイトル／#D0D0D0 日付／#F7EBCB 項目／#FFFF00 チェック）
    ↓
2026-09-11 後発: 上野本館・渋谷新館の 表.png のみ 新配色へ正式変更（本節・8a85e34）
```

**つまり本節は `4914bed` の「仕掛け表は従来デザイン維持」を
【上野本館・渋谷新館の `表.png` に限って】後発仕様で上書きするものである。**

**上書きされるのはこの2店舗の `表.png` だけ**で、
`4914bed` のそれ以外（差枚ローテ画像の4色・外背景なし・凡例なし・ranking 仕様・
他ページ非対象・スランプ独立）は**すべてそのまま有効**である。

### L. `{機種名}ローテ.png` は今回いっさい変更していない

全8店舗の差枚ローテ画像は**引き続き正式仕様**（実装 `a2bd8f7` / `9084f93` ／ 記録 `4914bed`）。

| 対象 | 正式色 |
|---|---|
| 台番・日付ヘッダー背景 | **`#7000E0`** |
| 機種名背景 | **`#290068`** |
| 台番セル背景 | **`#C7B4DD`** |
| 台番数字の文字 | **`#4B0082`** |

**今回の表.png変更によってこの正式仕様は1つも変わらない**
（全8店舗で HEAD と **md5 完全一致**・`generate_rote_image()` は AST 一致）。

**★特に `#290068` は表.png のタイトルバーでは使わなくなったが、
`{機種名}ローテ.png` の機種名背景では引き続き正式色である。**
**`#290068` をアプリから削除してはならない。**

### M. 既存ローテ正式仕様も維持

**外背景なし ／ 差枚凡例なし ／ 上端＝日付セル ／ 下端＝最終台番行 ／ 仕掛け表の外地なし**
（実装 `6b87aa4f1beb577e5249d679d7f01ff8f70494df` ／
記録 `061e42f3bf4ddf95451448a9d6a686c62a6d5990`）は**引き続き有効**
（`#CFEEEE` 0px・凡例なしを実測確認）。

**新宿歌舞伎町の ranking 画像生成停止**（実装 `7a47c1220b0e4983d58818144f05f409ebf7fcd5` ／
記録 `a17ea22643ab05530fe10afad1610174b77ece02`）も**今回と独立して維持**する
（`_ROTE_RANKING_OFF_STORES` / `_rote_ranking_on()` は非変更）。
**今回の表.png記録で ranking 仕様を書き換え・統合削除してはならない。**

### N. ロジック・保存復元・他ページは非変更

**今回変えたのは色（と項目文字色）だけ。**次はすべて**非変更**：

チェック判定 ／ `weekly_ck_*` ／ session_state ／ `blank_date_checks` ／
`cell_date_machines` ／ `weekly_items.json` ／ 保存 ／ 復元 ／
`_wt_tn_list` ／ `_wt_save_list` ／ 対象日付 ／ 対象機種 ／ 項目名 ／ 並び順 ／
結果テキスト ／ ZIP構造 ／ ファイル名。

**他ページは完全非対象**：`auto` ／ `auto_slump` ／ `auto_slump2` ／ `auto_article` ／ `work`
（AST 一致で非変更を確認）。高配分画像・非記事用表画像の定数と描画も非変更。

**新規関数0・削除関数0**（`fdcf349` で新設した `_rote_weekly_new_theme()` /
`_wt_hex_rgb()` を流用）。`8a85e34` で本体が変わったのは
`_draw_weekly_table_image` / `_weekly_table_html_image` / `_item_centered` の3つだけ。

### O. 正式確認結果

- **両renderer・両店舗・チェック前後の実画像で4色を実測**
  （① `#4B0082` ② `#7000E0` ③ `#C7B4DD` ④ `#FFFFCB`）。
  **`#290068` は表から 0px**、レガシー `#D0D0D0` / `#F7EBCB` / `#FFFF00` も **0px**。
- **チェック前は白維持**（`#FFFFCB` 混入 0px）／**チェック後だけ `#FFFFCB`**。
- **レイアウト不変**：`fdcf349` 版との厳密マッピング（`#290068`→`#4B0082`、
  `#4B0082`→`#C7B4DD`、`#C7B4DD`→`#FFFFCB`）で**孤立不一致0**、
  **日付セル `#7000E0` は全画素完全一致**、**項目列の外で 白→他 0px・黒→他 0px**。
  画像サイズ・列幅・行高・セル位置・罫線・余白・フォント・文字位置・データ・ファイル名は一致。
- **`theme_new=False` は HEAD コードと md5 完全一致**（checks／cells）。
- **対象外店舗（稲毛・高田馬場）の表画像は md5 完全一致**（テーマ色の混入0）。
- **全8店舗の `{機種名}ローテ.png` は HEAD と md5 完全一致。**
- **スランプカード（4店舗・388×472）は HEAD と md5 完全一致。**
- テスト **231 PASS / 0 FAIL**。
- **Cloud で上野本館・渋谷新館を承認済み（2026-09-11）。**

### P. 今後の禁止事項

1. **`fdcf349` の配色（タイトル `#290068` ／ 項目 `#4B0082`＋白文字 ／
   チェック済み `#C7B4DD`）へ戻さない**
2. **項目セル `#C7B4DD` に白文字を入れない**（黒文字が正式）
3. **タイトルバー・日付セルの白文字を変更しない**
4. **チェック済みセルの `○`・機種名の黒文字を変更しない**
5. **チェック前セルを白以外にしない／チェック前から `#FFFFCB` にしない**
6. **チェック判定・`weekly_ck_*`・session_state・保存復元・`_wt_tn_list` /
   `_wt_save_list` を変更しない**
7. **`_ROTE_WEEKLY_NEW_THEME_STORES` と `_ROTE_NEW_THEME_STORES` を統合・流用しない**
8. **表を作らない店舗を `_ROTE_WEEKLY_NEW_THEME_STORES` へ追加しない**
9. **片方の renderer だけ変更しない**（PIL / html で同じ配色を保つ）
10. **`theme_new` の既定 `False` を変更しない**
11. **`C_ROTE_WEEKLY_CK_BG` を `C_SLUMP_AREA_BG` と統合・共用しない**
12. **`C_SLUMP_AREA_BG` / `_paste_slump_area_bg()` / スランプ関連を変更しない**
13. **`4914bed` の節（「仕掛け表は従来デザイン維持」を含む）を削除・修正・書き換えしない**
    （本節が後発仕様として2店舗の `表.png` のみ上書きした履歴を残す）
14. **`{機種名}ローテ.png` の4色を変更しない／`#290068` をアプリから削除しない**
15. **外背景なし・差枚凡例なし（`6b87aa4` / `061e42f`）を巻き戻さない**
16. **ranking 停止仕様（`7a47c12` / `a17ea22`）を書き換え・統合削除しない**
17. **`auto` / `auto_slump` / `auto_slump2` / `auto_article` / `work` へ適用しない**
18. **`fdcf349` / `8a85e34` へ reset して実装をやり直さない**
19. **無関係なリファクタ・未使用コード整理をしない**

## 2026-09-11 新宿歌舞伎町 ローテ機種別データ絞り込み正式修正

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】のローテ用（`page == "rote"`）で
速報データ取得後に表示される「機種別データ」の絞り込みだけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で確認し「問題なし」と正式承認**した。

既存のローテ関連セクション（とくに **`c59dd90`**「新宿歌舞伎町ローテ：①〜⑥各1機種＝1枚」／
`6b87aa4`＋記録 `061e42f` ／ `7a47c12`＋記録 `a17ea22` ／ `a2bd8f7`・`9084f93`＋記録 `4914bed` ／
`8a85e34`＋記録 `378291b` ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。

### A. 正式実装commit

| | commit |
|---|---|
| **正式** | **`94f8e7b7bfe85a6dde4af8dd309618f5c3cb446c`**（`fix: 新宿歌舞伎町ローテの機種別データ絞り込みを修正`） |

**`streamlit_app.py` のみ・+8 / −1・1ハンク・変更関数は `show_rote_page()` だけ・
新規関数0・削除関数0。**
**`94f8e7b` へ reset してはならない**（正式仕様の根拠commitであって、HEAD を戻す意味ではない）。

### B. Cloud 承認

**2026-09-11：`94f8e7b` push 後、ユーザーが Cloud で【新宿歌舞伎町】→「📋 ローテ用」→
速報データ取得 →「機種別データ」を実機確認し「問題なし」と正式承認。**

確認内容：

```
現在の入力  ① 東京喰種 ／ ② カバネリ海門決戦 ／ ③〜⑥ 空
機種別データ 東京喰種 ／ カバネリ海門決戦 の2機種だけ
旧hidden値  set2[1] = 炎炎ノ消防隊2 は保持したまま、機種別データには表示されない
```

### C. 発生していた事象

新宿歌舞伎町のローテ用で**2機種だけ入力**して「速報データを取得」したのに、
**「機種別データ」に `炎炎ノ消防隊2` まで出て3機種**表示されていた。

### D. ★根本原因（filter の index 範囲）

`rote_machines.json` の新宿歌舞伎町には旧仕様由来の

```
set1 = ['東京喰種',         '', '', '', '', '']
set2 = ['カバネリ海門決戦', '炎炎ノ消防隊2', '', '', '', '']   ← index 1 に旧機種
set3〜set6 = ['']
```

が保持されている。復元処理（`show_rote_page()` 冒頭）は
**`_rote_init_{store}_{set}_{index}` を index 0〜5 まで作る**。

一方、新宿歌舞伎町は **`_ROTE_SINGLE_STORES`** 対象で
**UI・画像生成・結果テキストは各 set の index 0 しか使わない**
（widget は `rote1_mname_0`〜`rote6_mname_0` のみ）。

にもかかわらず、**機種別データの `_rv_filter` 構築だけが `for _rfi in range(6):` で
index 0〜5 を全走査**しており、widget が存在しない index 1 では
`or st.session_state.get(f"_rote_init_{store}_{_rset}_{_rfi}", "")` のフォールバックが
**必ず `_rote_init_新宿歌舞伎町_2_1 = 炎炎ノ消防隊2` を採用**していた。

```
画面入力         2件（① 東京喰種 ／ ② カバネリ海門決戦）
画像/ZIP/結果    2件（machine_inputs_all＝widget index0 のみ）
_rv_filter      3件（+ 炎炎ノ消防隊2）★ ここだけ食い違っていた
```

**`preserve_tail=True` の `_merge_set()` が index 1 以降を恒久保持する仕様のため、
この旧値は UI からは消せない。** つまり原因は「今回2機種へ減らした操作」ではなく
**filter の index 範囲**である。

### E. 正式実装（既存ゲートを再利用・新定数を作らない）

```python
# ①〜⑥各1機種方式の店舗は各 set の index 0 しか UI・画像生成・
# 結果テキストで使わないため、絞り込みも index 0 だけを見る。
# （_save_rote_machines(preserve_tail=True) が index 1 以降を
#   恒久保持する仕様のため、index を全部見ると
#   「新UIでは使用しない」旧機種まで機種別データへ混入する。
#   c59dd90 の「JSON上は保持／新UIでは使用しない」を絞り込みへ反映）
_rv_idxs = (0,) if store in _ROTE_SINGLE_STORES else range(6)
for _rfi in _rv_idxs:
    for _rset in _rv_sets:
        _rv_m = (st.session_state.get(f"rote{_rset}_mname_{_rfi}", "")
                 or st.session_state.get(f"_rote_init_{store}_{_rset}_{_rfi}", "")).strip()
        if _rv_m:
            _rv_filter.add(_rv_m)
```

| 店舗 | 機種別データ filter が見る index |
|---|---|
| **新宿歌舞伎町（`_ROTE_SINGLE_STORES`）** | **index 0 のみ** |
| **それ以外のローテ店舗** | **index 0〜5（従来どおり）** |

- **既存 `_ROTE_SINGLE_STORES` をそのまま再利用**する（`_ROTE_SINGLE_STORES` の参照が1箇所増えただけ）。
- **新しい店舗別 if 文・新しい専用定数・新しい helper を作らない。**
- `_rv_sets`（単一機種店舗は `("1"..."6")`／他店舗は `("1","2")`）は**変更していない**。

### F. ★「2機種固定」ではない（誤記しないこと）

正式仕様は **「①〜⑥の各 set の index 0 に現在入力されている機種だけを表示する」**である。

| 入力 | 機種別データ |
|---|---|
| ①② に2機種 | **2機種** |
| **①〜⑥ に6機種** | **6機種** |

**`set1`〜`set6` の index 0 はすべて対象。**新宿歌舞伎町で無視するのは **index 1〜5 だけ**。
**「2機種だけ表示する」という仕様に読み替えてはならない。**

### G. ★`c59dd90` との関係（既存仕様は変更していない）

既存正式仕様 **`c59dd90`**（「新宿歌舞伎町ローテ：①〜⑥各1機種＝1枚」節 ③）では
`set2[1] = "炎炎ノ消防隊2"` について

- **JSON上で保持する**
- **新UIでは使用しない**
- **③へ自動移動しない**
- **削除しない**

と記録されている。**この既存仕様は今回いっさい変更していない。**

**今回の修正は、その「新UIでは使用しない」という正式仕様を
機種別データ filter 側にも正しく反映したもの**である。

したがって次はすべて**非変更**：

**`rote_machines.json`（無変更・`git status` に出ない）／ `set2[1] = 炎炎ノ消防隊2`（保持）／
`preserve_tail=True` ／ `_merge_set()` ／ `_save_rote_machines()` ／ `_load_rote_machines()` ／
`_on_rote_name_change()` ／ 復元方式 ／ session_state ／ widget 構造 ／ UI。**

**`rote_machines.json` の `set2[1]` を削除してはならない。**

### H. 他店舗は従来どおり（誤適用しない）

**`_ROTE_SINGLE_STORES` 以外のローテ店舗は index 0〜5 のまま。**

**高田馬場 ／ 上野本館 ／ 溝の口本館 ／ 溝の口新館 ／ 西武新宿 ／ 渋谷新館 ／ 新大久保**
は**非変更**（実データで修正前後の `_rv_filter` 一致を確認）。
**今回の index 0 限定を他店舗へ誤適用してはならない。**

### I. 影響範囲は「機種別データの filter」だけ

**今回の問題は表示用 filter だけで、画像生成・ZIP・結果テキストには元々影響していなかった**
（これらは `machine_inputs_all`＝widget index 0 のみを読むため）。

次はすべて**非変更**：

`machine_inputs_all` ／ `{機種名}ローテ.png` ／ ZIP ／ 結果テキスト ／
`_cat_inputs` ／ `_cat_names` ／ 10日区切り ／ 「○日目結果」 ／ ranking 生成停止 ／
ローテ画像配色 ／ 上野本館・渋谷新館の `表.png` 配色 ／ 速報取得そのもの ／
Pision 取得処理 ／ `normalize_df()` ／ `apply_name_conversion()` ／ `_render_pision_summary()`。

### J. 回帰確認結果（テスト **103 PASS / 0 FAIL**）

**新宿歌舞伎町（実 `rote_machines.json` を読み取りのみで検証）**
- 実データ（`set1[0]=東京喰種` / `set2[0]=カバネリ海門決戦` / `set2[1]=炎炎ノ消防隊2`）で
  **`_rv_filter` = {東京喰種, カバネリ海門決戦} の2機種**
- **`炎炎ノ消防隊2` 除外を確認**（修正前は3機種だったことも同一データで再現）
- 機種別データの表示機種数 **2**
- **①〜⑥へ6機種入力時は `_rv_filter` 6機種**（`set1`〜`set6` の index 0 を全採用）
- **hidden index 1〜5 に旧値30件を仕込んでも filter は2機種のまま**（全部無視）

**他店舗の非回帰（修正前後で `_rv_filter` 完全一致）**
高田馬場2件 ／ 上野本館1件 ／ 溝の口本館4件 ／ 溝の口新館1件 ／ 西武新宿5件 ／
渋谷新館2件 ／ 新大久保5件。渋谷新館の `_rote_init_渋谷新館_2_1` に旧値を仕込むと
**従来どおり拾う**ことも確認（index 0〜5 維持）。

**保存**：`rote_machines.json` 無変更 ／ `set2[1]` 保持 ／
`preserve_tail` / `_merge_set` / `_save_rote_machines` / `_load_rote_machines` /
`_on_rote_name_change` / `_rote_init_` / `machine_inputs_all` / `_cat_inputs` / `_cat_names` の
**コード上の出現数が HEAD と一致**。

**出力**：`{機種名}ローテ.png` が **HEAD と md5 完全一致**（3ケース）／ ZIP 非回帰 ／
結果テキスト非回帰（`_generate_rote_result_text` AST 一致）／
**ranking 停止維持**（`_rote_ranking_on("新宿歌舞伎町") == False`・他7店舗 True・
`_ROTE_RANKING_OFF_STORES` 不変）／ **10日区切り・「○日目結果」維持** ／
**ローテ配色維持**（`#7000E0` / `#290068` / `#C7B4DD` / `#4B0082`・外背景 `#CFEEEE` 0px）／
**上野本館・渋谷新館の `表.png` は md5 一致・4色（`#4B0082` / `#7000E0` / `#C7B4DD` / `#FFFFCB`）維持**。

**AST**：**変更関数は `show_rote_page()` の1つだけ**。
`generate_rote_image` / `generate_ranking_image` / `_rote_margin` / `_rote_plain` /
`_rote_new_theme` / `_rote_ranking_on` / `_rote_weekly_new_theme` /
`_generate_rote_result_text` / `_load_rote_machines` / `_save_rote_machines` /
`_draw_weekly_table_image` / `_weekly_table_html_image` / `_weekly_table_data` /
`normalize_df` / `apply_name_conversion` / `_render_pision_summary` / `show_auto_page` /
`show_auto_article_page` / `show_weekly_table_section` / `_add_margin` /
`draw_table_image` / `draw_slump_graph` — **すべて一致**。

### K. ★副案は今回実装していない

調査時に出た副案
**「widget key が存在する場合は `_rote_init_` へフォールバックしない」**は
**今回の正式仕様に含めない（未実装）**。

理由：**Streamlit のページ離脱→復帰時の widget GC との関係**があり、
別途の影響調査が必要なため（`_rote_init_*` は「widget キーが消えた run で古い値へ戻るのを防ぐ」
ための非widgetキーとして機能している）。

**今後必要になった場合は、別途調査・ユーザー承認のうえ実装する。**
なお「カテゴリをクリアした直後に `_rote_init_*` が非空だと復活しうる」という潜在挙動は
**調査時に確認済みの別論点**であり、今回の正式仕様の対象外である。

### L. 今後の禁止事項

1. **`for _rfi in range(6):` の無条件全走査へ戻さない**
2. **`_rv_idxs` の判定を `_ROTE_SINGLE_STORES` 以外の新しい店舗別 if・新定数へ置き換えない**
3. **新宿歌舞伎町の index 0 限定を他店舗へ適用しない**（他店舗は `range(6)` 維持）
4. **「2機種固定」と解釈しない**（①〜⑥の各 index 0 に入力されている機種を表示する）
5. **`set1`〜`set6` のいずれかを filter 対象から外さない**（`_rv_sets` は変更しない）
6. **`rote_machines.json` の `set2[1] = 炎炎ノ消防隊2` を削除・移動しない**（`c59dd90` を維持）
7. **`preserve_tail=True` / `_merge_set()` / `_save_rote_machines()` / `_load_rote_machines()` /
   `_on_rote_name_change()` / 復元方式 / widget 構造 / UI を変更しない**
8. **`machine_inputs_all` / `_cat_inputs` / `_cat_names` / `{機種名}ローテ.png` / ZIP /
   結果テキストを今回を理由に変更しない**
9. **ranking 停止（`7a47c12` / `a17ea22`）・10日区切り・「○日目結果」・
   `_generate_rote_result_text()` を変更しない**
10. **ローテ画像配色（`4914bed`）・上野本館/渋谷新館の `表.png` 配色（`378291b`）を変更しない**
11. **速報取得・Pision 取得処理・`normalize_df()` / `apply_name_conversion()` /
    `_render_pision_summary()` を変更しない**
12. **副案（widget キー存在時のフォールバック抑止）を承認なしに実装しない**
13. **`94f8e7b` へ reset して実装をやり直さない**
14. **無関係なリファクタ・未使用コード整理をしない**

## 2026-09-11 新宿歌舞伎町 ローテ結果テキスト新デザイン正式採用

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】のローテ用（`page == "rote"`）で
生成される結果テキストの表示デザインだけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で確認し「問題なし」と正式承認**した。

既存のローテ関連セクション（`c59dd90` ／ `6b87aa4`＋記録 `061e42f` ／
`7a47c12`＋記録 `a17ea22` ／ `a2bd8f7`・`9084f93`＋記録 `4914bed` ／
`8a85e34`＋記録 `378291b` ／ **`94f8e7b`＋記録 `4b32b54`** ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。

### A. 正式実装commit

| | commit |
|---|---|
| **正式** | **`370d5f0d2ea11319fea78668fabfd861f39c7418`**（`fix: 新宿歌舞伎町ローテの結果テキストを新デザインへ変更`） |

**`streamlit_app.py` のみ・+18 / −6・2ハンク・変更関数は `_generate_rote_result_text()` だけ。**
**新規helper 0 ／ 新規定数 0 ／ 新規関数 0 ／ 削除関数 0。**
**`370d5f0` へ reset してはならない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

生成関数は **`_generate_rote_result_text()`**、呼び出し元は **`show_rote_page()` の1箇所だけ**。

### B. Cloud 承認

**Cloud承認日：2026-09-11。**
【新宿歌舞伎町】→「📋 ローテ用」→ 結果テキストを実機確認し、
**`📝結果📝` ／ `○日目` ／ `💎10,000枚超` `💎5,000枚超` `💎3,000枚超` `💎1,000枚超` ／
`・○番台`** のすべてを問題なしとして正式承認。

### C. 正式な完成形

```
9/1(火)📝結果📝
エスパス 新宿 歌舞伎 町

🏆9月1日～9月10日🏆
🏆炎炎ノ消防隊2×スマスロ北斗の拳ポスター🏆
1日目

【炎炎ノ消防隊2】
💎5,000枚超
・25番台
・17番台

💎3,000枚超
・31番台

💎1,000枚超
・126番台
```

実際の台番号・機種名・日数は**その日のデータと既存ロジック**に従う。

### D. 正式変更① 結果見出し

| | |
|---|---|
| 旧 | `👨‍💻結果👨‍💻` |
| **新** | **`📝結果📝`** |

**日付プレフィックスは従来どおり維持**（例：`9/1(火)📝結果📝`）。
店舗名行（`エスパス 新宿 歌舞伎 町`）・`🏆{週間表記}🏆`・`🏆{機種}ポスター🏆` は**不変**。

### E. 正式変更② 「○日目結果」の表記

| | |
|---|---|
| 旧 | `＼＼1日目結果／／` |
| **新** | **`1日目`** |

**★日数計算ロジックは変更していない。**正式ロジックは従来どおり：

```python
if d <= 10:
    period_start, period_end, day_num = 1, 10, d
elif d <= 20:
    period_start, period_end, day_num = 11, 20, d - 10
else:
    period_start, period_end, day_num = 21, last_day, d - 20   # last_day = calendar.monthrange
```

| 日付 | 表示 |
|---|---|
| 9/1 | **1日目** |
| 9/2 | **2日目** |
| 9/10 | **10日目** |
| 9/11 | **1日目** |
| 9/20 | **10日目** |
| 9/21 | **1日目** |
| 9/30 | **10日目** |
| **8/31** | **11日目**（31日がある月の 21〜31区切り） |
| **1/31** | **11日目** |

**★「1日目」を固定値にしているのではない。**
変更したのは **`f"＼＼{day_num}日目結果／／"` → `f"{day_num}日目"`** だけで、
`day_num` は既存ロジックの算出結果をそのまま使う。
**`period_end` / `calendar.monthrange` / 10日区切りは非変更。**

### F. 正式変更③ 差枚帯見出し

| 旧 | **新** |
|---|---|
| `🔥10,000枚超🔥` | **`💎10,000枚超`** |
| `🔥5,000枚超🔥` | **`💎5,000枚超`** |
| `🔥3,000枚超🔥` | **`💎3,000枚超`** |
| `🔥1,000枚超🔥` | **`💎1,000枚超`** |

- 先頭 **`🔥` → `💎`**
- **末尾の絵文字は削除**（`💎5,000枚超💎` のようにしない）
- **差枚帯の判定条件は一切変更していない**：
  閾値 `(10000, None)` / `(5000, 10000)` / `(3000, 5000)` / `(1000, 3000)` と
  **`差枚 >= 1000` の抽出条件**を維持。

### G. 正式変更④ 台番号記号

| | |
|---|---|
| 旧 | `💫25番台` |
| **新** | **`・25番台`** |

**台番号そのもの・抽出条件・並び順・所属差枚帯は変更していない。**
並び順は既存の

```python
sort_values(["差枚", "台番"], ascending=[False, True])
```

を維持（差枚降順 → 同差枚は台番昇順）。

### H. 空カテゴリの扱い（既存挙動を維持）

- **対象台が0件の差枚帯は見出しを出さない。**
- **全帯0件なら `💎` 見出し自体を出さない。**

今回の変更で**空カテゴリ処理は変えていない**。

### I. 改行構造（維持）

**改行数・空行構造は旧出力と同一。**今回の変更は**文字・記号の置換だけ**。
検証では、新表記を旧表記へ逆変換すると **HEAD 出力とバイト一致**することを
10日付すべてで確認済み（改行数も一致）。**余計な空行の追加・削除はしていない。**

### J. ★新宿歌舞伎町限定（他7店舗へ誤適用しない）

**今回の正式仕様は新宿歌舞伎町だけ。**

**高田馬場 ／ 上野本館 ／ 溝の口本館 ／ 溝の口新館 ／ 西武新宿 ／ 渋谷新館 ／ 新大久保**
は**今回まだ旧デザインのまま**で、結果テキストは**修正前後で完全一致**
（各10日付 ＋ md5 一致。`📝結果📝` / `💎` / `・○番台` の混入0。
`👨‍💻結果👨‍💻` と `＼＼○日目結果／／`、`ROTE_EMOJI_CONFIG` / `ROTE_BAN_EMOJI_CONFIG` の
店舗別絵文字＝西武新宿 `💥5,000枚超💥` ／ 新大久保 `✨25番台` などをそのまま維持）。

**この正式記録を他店舗へ誤適用してはならない。**
他店舗展開は**別途の調査・実装・Cloud承認**を経て行う。

### K. 実装構造

- **見出し・日数表記**：`_generate_rote_result_text()` 内の**既存 `if store == "新宿歌舞伎町":`
  ブロック内**で変更（新しいゲートは不要）。
- **差枚帯・台番号記号**：`_te` / `_be` 解決直後に**店舗限定分岐を1つだけ**追加。

```python
_re, _te = ROTE_EMOJI_CONFIG.get(store, ("🌌", "🔥"))
_be = ROTE_BAN_EMOJI_CONFIG.get(store, "💫")
if store == "新宿歌舞伎町":
    _tp, _ts, _be = "💎", "", "・"
else:
    _tp, _ts = _te, _te
tiers = [
    (10000, None,  f"{_tp}10,000枚超{_ts}"),
    (5000,  10000, f"{_tp}5,000枚超{_ts}"),
    (3000,  5000,  f"{_tp}3,000枚超{_ts}"),
    (1000,  3000,  f"{_tp}1,000枚超{_ts}"),
]
```

- **新規helper・新規定数・新規関数・削除関数はいずれも0。**
  同関数内に既存の `store == "新宿歌舞伎町"` 判定が複数あり、それと整合する最小分岐。
- **他店舗へ展開するときは、この店舗条件の扱いを別途検討・承認すること**
  （frozenset ゲート化するかどうかを含め、その時点で判断する）。

### L. 今回変更していないもの（正式に非変更）

10日区切りロジック ／ 日数算出ロジック ／ `period_end` ／ `calendar.monthrange` ／
差枚帯判定条件 ／ 台番号抽出条件 ／ 台番号順 ／ 空カテゴリ判定 ／
速報データ取得 ／ 機種別データ ／ Pision処理 ／ ローテ対象機種 ／
`machine_inputs_all` ／ `_cat_inputs` ／ `_cat_names` ／
`{機種名}ローテ.png` ／ ZIP ／ ranking ／ 保存JSON ／ session_state ／ widget ／
保存・復元 ／ ローテ画像配色 ／ 上野本館・渋谷新館の `表.png` 配色。

### M. 直前正式仕様との整合（`94f8e7b` を維持）

直前に正式採用した **`94f8e7b7bfe85a6dde4af8dd309618f5c3cb446c`**
（新宿歌舞伎町ローテの機種別データ絞り込み修正）は**維持**している。

**`_ROTE_SINGLE_STORES` では機種別データ filter が各 set の index 0 のみを見る仕様**
（`_rv_idxs = (0,) if store in _ROTE_SINGLE_STORES else range(6)`）はそのまま。
**今回の結果テキスト変更とは別件**であり、相互に影響しない。

### N. 回帰確認結果

**日数**：9/1→1日目 ／ 9/2→2日目 ／ 9/10→10日目 ／ 9/11→1日目 ／ 9/20→10日目 ／
9/21→1日目 ／ 9/30→10日目 ／ **8/31→11日目** ／ **1/31→11日目**。
旧出力の `＼＼{N}日目結果／／` の N と新出力の `{N}日目` の N が**10ケースすべて一致**。

**差枚帯**：10,000 / 5,000 / 3,000 / 1,000 の判定条件**非変更**。
**台番**：記号を除いた帯ごとの台番リストが **before/after で完全一致**（抽出条件・順序非変更）。
**空カテゴリ**：該当0件の帯は見出しなし ／ 全帯0件なら `💎` なし（従来挙動維持）。
**改行**：改行数一致・逆変換で HEAD とバイト一致。

**他7店舗**：結果テキスト **before/after 完全一致**（md5 一致）。
**画像**：`{機種名}ローテ.png` が**8店舗すべて md5 一致**。
**表.png**：上野本館・渋谷新館とも **md5 一致**。
**ranking**：新宿歌舞伎町は**生成停止維持**（`_rote_ranking_on("新宿歌舞伎町") == False`）。
**JSON**：`rote_machines.json` **無変更**。
**機種別データ**：`94f8e7b` の filter 修正**維持**。

**AST**：**変更関数は `_generate_rote_result_text` の1つだけ**。
`show_rote_page` / `generate_rote_image` / `generate_ranking_image` / `_rote_margin` /
`_rote_plain` / `_rote_new_theme` / `_rote_ranking_on` / `_rote_weekly_new_theme` /
`_load_rote_machines` / `_save_rote_machines` / `_draw_weekly_table_image` /
`_weekly_table_html_image` / `normalize_df` / `apply_name_conversion` / `show_auto_page` /
`show_auto_article_page` / `generate_report_text` — **すべて一致**。
`ROTE_EMOJI_CONFIG` / `ROTE_BAN_EMOJI_CONFIG` / `_ROTE_SINGLE_STORES` /
`_ROTE_RANKING_OFF_STORES` / `preserve_tail` / `machine_inputs_all` /
`_cat_inputs` / `_cat_names` のコード上の出現数も HEAD と一致。

**テスト：264 PASS / 0 FAIL。**

### O. 今後の禁止事項

1. **`👨‍💻結果👨‍💻` へ戻さない**（新宿歌舞伎町は `📝結果📝`）
2. **`＼＼{N}日目結果／／` へ戻さない**
3. **日数を固定値にしない**（`day_num` は既存ロジックの算出結果を使う）
4. **10日区切り・`period_end`・`calendar.monthrange`・31日月の 21〜31区切りを変更しない**
5. **差枚帯の絵文字を `🔥○○枚超🔥` へ戻さない／末尾絵文字を復活させない**
6. **差枚帯の閾値（10,000 / 5,000 / 3,000 / 1,000）と `差枚 >= 1000` を変更しない**
7. **台番記号を `💫` へ戻さない**
8. **台番の抽出条件・`sort_values(["差枚","台番"], ascending=[False,True])` を変更しない**
9. **空カテゴリ挙動（0件の帯は見出しなし／全帯0件なら `💎` なし）を変更しない**
10. **改行数・空行構造を変更しない**
11. **他7店舗へ新デザインを勝手に適用しない**（展開は別途調査・実装・Cloud承認）
12. **`ROTE_EMOJI_CONFIG` / `ROTE_BAN_EMOJI_CONFIG` を今回を理由に変更しない**
13. **`94f8e7b` の機種別データ filter（index 0 限定）を壊さない**
14. **`{機種名}ローテ.png` / ZIP / ranking 停止 / ローテ配色 / `表.png` 配色 /
    `rote_machines.json` / session_state / widget / 保存復元を変更しない**
15. **`370d5f0` へ reset して実装をやり直さない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 2026-09-11 全店舗ローテ結果テキスト新デザイン＋渋谷新館見出し正式採用

**正式仕様。巻き戻し禁止。**対象は**ローテ用ページ（`page == "rote"`）で生成される
結果テキストの表示デザイン／見出しだけ**。
2026-09-11 に **ユーザーが Streamlit Cloud 実機で確認し「問題なし」と正式承認**した。

既存のローテ関連セクション（`c59dd90` ／ `6b87aa4`＋記録 `061e42f` ／
`7a47c12`＋記録 `a17ea22` ／ `a2bd8f7`・`9084f93`＋記録 `4914bed` ／
`8a85e34`＋記録 `378291b` ／ `94f8e7b`＋記録 `4b32b54` ／
**`370d5f0`＋記録 `b36b524`** ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。

### A. 正式実装commit（3本）

| # | commit | 内容 |
|---|---|---|
| ① | **`fc589ce534d79fe46967334f068a5ea850012a6e`** | `fix: ローテ結果テキストの新デザインを全店舗へ展開`（`streamlit_app.py` のみ・**+46 / −15**） |
| ② | **`97b17fa5dfffa7d4dd9e1eb73bbd551c3d46f7d7`** | `fix: 渋谷新館ローテ結果テキストの見出しを調整`（`streamlit_app.py` のみ・**+8 / −6**） |
| ③ | **`6b4c0b348979bf788d9fa3b53dd8dfd80046cfcb`** | `fix: 渋谷新館ローテのジャグラー見出しを統一`（`streamlit_app.py` のみ・**+1 / −1**） |

**3本とも `streamlit_app.py` の1ファイルのみ。**
**`fc589ce` / `97b17fa` / `6b4c0b3` へ reset してはならない**
（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. Cloud 承認

**Cloud承認日：2026-09-11。**
全8店舗のローテ結果テキストと、渋谷新館の見出しを実機確認し「問題なし」と正式承認。

### C. 対象

**page：`rote`。ローテ対象8店舗すべて。**

```
新宿歌舞伎町 ／ 高田馬場 ／ 上野本館 ／ 溝の口本館 ／
溝の口新館 ／ 西武新宿 ／ 渋谷新館 ／ 新大久保
```

### D. 正式仕様① 結果見出し（全8店舗共通）

| | |
|---|---|
| **正式** | **`📝結果📝`** |
| 旧 | `👨‍💻結果👨‍💻`（使用しない） |

**日付プレフィックスは既存仕様を維持**する。例：

```
9/11(金)📝結果📝
```

### E. 正式仕様② 差枚帯見出し（全8店舗共通）

```
💎10,000枚超
💎5,000枚超
💎3,000枚超
💎1,000枚超
```

- **末尾に `💎` を付けない**（`💎5,000枚超💎` のようにしない）。
- 旧の店舗別表現 **`🔥…🔥` / `👑…👑` / `🚨…🚨` / `💥…💥` / `🐝…🐝` / `📌…📌`** などは
  **差枚帯表示では使用しない**。

### F. 正式仕様③ 台番号（全8店舗共通）

```
・25番台
・17番台
```

**形式は `・○番台`。**
旧の **`💫○番台` / `✨○番台` / `💎○番台`** などは**結果テキストでは使用しない**。

### G. ★`ROTE_EMOJI_CONFIG` / `ROTE_BAN_EMOJI_CONFIG` は変更していない

**両 config の定義そのものは1文字も変更していない。**

理由：**機種見出しなど別用途の既存値を保持するため**。
`ROTE_EMOJI_CONFIG` は `(機種見出し用 `_re`, 差枚帯用 `_te`)` の**1タプルを共有**しており、
config を書き換えると機種見出しまで壊れる。

**正式方式は「結果テキスト生成時だけ表示記号をローカル差し替えする」**である。

```python
_re, _te = ROTE_EMOJI_CONFIG.get(store, ("🌌", "🔥"))
_be = ROTE_BAN_EMOJI_CONFIG.get(store, "💫")
_new_text = store in _ROTE_NEW_TEXT_STORES
if _new_text:
    _tp, _ts, _be = "💎", "", "・"
else:
    _tp, _ts = _te, _te
```

**特に新大久保の `ROTE_BAN_EMOJI_CONFIG` の `✨` は config 上そのまま保持**している
（結果テキストでは使わないだけ）。**config を直接書き換えてはならない。**

### H. 正式仕様④ 日数（★店舗ごとに違う。混同しないこと）

#### H-1. 新宿歌舞伎町＝10日区切り

**既存の10日区切りを維持**する（1〜10日 ／ 11〜20日 ／ 21〜月末）。

表示は **`○日目`**。

| 日付 | 表示 |
|---|---|
| 9/1 | **1日目** |
| 9/10 | **10日目** |
| 9/11 | **1日目** |
| 9/20 | **10日目** |
| 9/21 | **1日目** |
| 9/30 | **10日目** |
| **8/31** | **11日目** |
| **1/31** | **11日目** |

**10日区切りロジック（`period_start` / `period_end` / `day_num` / `calendar.monthrange`）は
一切変更していない。**

#### H-2. 曜日ベース5店舗

**対象：高田馬場 ／ 溝の口本館 ／ 溝の口新館 ／ 西武新宿 ／ 新大久保**

**既存の `weekday + 1` を維持**する。

| 曜日 | 表示 |
|---|---|
| 月 | 1日目 |
| 火 | 2日目 |
| 水 | 3日目 |
| 木 | 4日目 |
| 金 | 5日目 |
| 土 | 6日目 |
| 日 | 7日目 |

| | |
|---|---|
| 旧 | `＼＼5日目結果／／` |
| **新** | **`5日目`** |

**日数計算は一切変更せず、装飾（`＼＼` / `結果／／`）だけを除去した。**

#### H-3. 日数なし2店舗

**対象：上野本館 ／ 渋谷新館**

**この2店舗には日数ロジック自体が存在しない。**

**正式仕様：日数行なし。**

**新デザイン展開に伴って `1日目` / `2日目` などを新設していない。**
**今後も、別途仕様変更の承認がない限り日数行を追加してはならない。**

### I. 正式仕様⑤ 機種見出しは原則として店舗固有（全店舗共通化していない）

**結果見出し・差枚帯・台番号は全8店舗で統一したが、機種見出しまで共通化していない。**

既存の店舗固有表現を維持する。例：

```
🌌機種名🌌 ／ 🌠機種名🌠 ／ 👑機種名👑 ／ 🍯機種名🍯 ／ 🤡機種名🤡 など
```

**新宿歌舞伎町は `【機種名】`。**
**渋谷新館は今回追加で正式採用した個別仕様があるため次節（J）に明記する。**

### J. 正式仕様⑥ 渋谷新館の見出し（`97b17fa` / `6b4c0b3`）

渋谷新館は専用関数 **`_generate_shibuyashinkan_result_texts()`** で生成する。
**5テキスト構成を維持**し、**`text2` は廃止状態で空のまま**、**日数行なし**。

共通部分は全8店舗と同じく **`📝結果📝` ／ `💎○○枚超` ／ `・○番台`**。

そのうえで次の見出しを正式採用する。

#### J-1. 北斗

```
🏆北斗シリーズ🏆
🏆週間オススメポスター🏆

【スマスロ北斗の拳】
【北斗転生2】
```

**旧 `🔥北斗シリーズ🔥` / `🔥週間オススメポスター🔥` /
`👊スマスロ北斗の拳👊` / `👊北斗転生2👊` は使用しない。**

#### J-2. カバネリ海門決戦

```
🏆カバネリ海門決戦🏆
🏆月間オススメポスター🏆
```

**旧 `🚂カバネリ海門決戦🚂` / `🚂月間オススメポスター🚂` は使用しない。**

#### J-3. ジャグラー（★最終正式値は 🏆）

```
🏆ジャグラーシリーズ🏆
🏆月間オススメポスター🏆
```

**★重要（誤記しないこと）：**

| 時点 | 値 |
|---|---|
| **`97b17fa` の時点** | **実コードの既存値 `🤡ジャグラーシリーズ🤡` / `🚨月間オススメポスター🚨` を一旦維持していた**（ユーザー指示「ジャグラーは触らない」に従ったため） |
| **`6b4c0b3`（Cloud承認前）** | **`🏆ジャグラーシリーズ🏆` / `🏆月間オススメポスター🏆` へ変更** |

**したがって最終正式仕様は `🏆`。**
**中間状態の `🤡` / `🚨` を正式仕様として誤記してはならない。**

#### J-4. 東京喰種

```
🏆東京喰種🏆
🏆月間オススメポスター🏆
```

**旧 `🗼東京喰種🗼` / `🗼月間オススメポスター🗼` は使用しない。**

### K. 正式仕様⑦ 渋谷新館で維持している既存仕様

次はすべて**非変更**：

**5テキスト構成 ／ `text2` 空 ／ 当日データ0台の機種はセクションごと省略 ／
差枚帯判定 ／ 台番抽出 ／ 台番順 ／ 空カテゴリ挙動 ／ 日数行なし ／
その他の独自文言 ／ `📍` 項目 ／ `✅毎日何かしらの仕掛けアリ!?`。**

**今回変更したのは結果テキストの表示デザイン／見出しだけ。**

### L. 正式仕様⑧ 上野本館

上野本館は **`_generate_rote_result_text()` を通らない。**
**`show_rote_page()` 内のインライン `_uo_monthly_text()`** による専用生成である。

正式表示：

```
📝結果📝
💎○○枚超
・○番台
```

**日数行：なし。**

次は維持：**月間表①②③ ／ 表ごとのポスター名 ／ 独自機種見出し ／
`✅毎日何かしらの仕掛けアリ!?` ／ `📍` 項目。**

### M. 正式仕様⑨ 結果テキスト生成は3経路（すべてへ新デザイン適用済み）

| # | 経路 | 対象店舗 |
|---|---|---|
| ① | **`_generate_shibuyashinkan_result_texts()`** | **渋谷新館** |
| ② | **`show_rote_page()` → インライン `_uo_monthly_text()`** | **上野本館** |
| ③ | **`_generate_rote_result_text()`** | **新宿歌舞伎町 ／ 高田馬場 ／ 溝の口本館 ／ 溝の口新館 ／ 西武新宿 ／ 新大久保** |

**この3経路すべてに新デザインを適用済み。**
**1経路だけ直す／1経路だけ戻すことを禁止する。**

### N. 正式仕様⑩ 実装構造（`_ROTE_NEW_TEXT_STORES`）

`fc589ce` で新設：

```python
_ROTE_NEW_TEXT_STORES: "frozenset[str]" = frozenset({
    "新宿歌舞伎町", "高田馬場", "溝の口本館", "溝の口新館", "西武新宿", "新大久保",
})
```

- これは **`_generate_rote_result_text()` を通る新テキスト対象店舗用**のゲートである。
- **上野本館・渋谷新館は別生成経路なので、この set に含めない。**
- 既存の **`_ROTE_SINGLE_STORES` / `_ROTE_PLAIN_STORES` / `_ROTE_NEW_THEME_STORES` /
  `_ROTE_WEEKLY_NEW_THEME_STORES`** とは**意味が違うため流用していない。統合禁止。**
- **新規helper 0。**

### O. 正式仕様⑪ 判定・抽出ロジックは非変更

```
差枚帯: (10000, None) / (5000, 10000) / (3000, 5000) / (1000, 3000)
抽出  : 差枚 >= 1000
台番順: sort_values(["差枚", "台番"], ascending=[False, True])
空帯  : 0件なら帯を表示しない
```

**これらは一切変更していない。**

### P. 正式仕様⑫ 既存の機種別データ filter を維持

新宿歌舞伎町の正式修正
**`94f8e7b7bfe85a6dde4af8dd309618f5c3cb446c`**
（`_ROTE_SINGLE_STORES` では機種別データ filter が各 set の index 0 のみを見る）は**維持**。

**今回の結果テキスト変更とは独立した別件**であり、相互に影響しない。

### Q. 正式仕様⑬ 非対象（今回いっさい変更していない）

`{機種名}ローテ.png` ／ `表.png` ／ ranking ／ ZIP ／
ローテ画像の紫系配色 ／ 外背景なし ／ 凡例削除 ／
上野本館・渋谷新館の `表.png` 配色 ／
`generate_rote_image()` ／ `generate_ranking_image()` ／
`_draw_weekly_table_image()` ／ `_weekly_table_html_image()` ／
`rote_machines.json` ／ `wrt_machines.json` ／ `auto_page_inputs.json` ／
session_state ／ widget ／ 保存処理 ／ 復元処理 ／ `preserve_tail`。

### R. 検証実績

| commit | テスト |
|---|---|
| `fc589ce` | **435 PASS / 0 FAIL** |
| `97b17fa` | **178 PASS / 0 FAIL** |
| `6b4c0b3` | **157 PASS / 0 FAIL** |

確認済み項目：

全8店舗の結果テキスト ／ 曜日ベース5店舗の7曜日 ／ 新宿歌舞伎町の10日区切り ／
31日月の11日目 ／ 上野本館の日数行なし ／ 渋谷新館の日数行なし ／
渋谷新館の5テキスト構成 ／ `text2` 空 ／ 0台省略 ／ 差枚帯 ／ 台番順 ／ 空カテゴリ ／
他店舗の非回帰 ／ ローテ画像 md5 ／ `表.png` md5 ／ JSON 非変更。

**Cloud：2026-09-11 最終確認問題なし。**

### S. 既存正式記録との関係（履歴を消さない）

新宿歌舞伎町単独の正式記録
**`b36b524cbe24680d6a4c0a13019f5b2440b5b1e4`**
（「2026-09-11 新宿歌舞伎町 ローテ結果テキスト新デザイン正式採用」節）は
**履歴としてそのまま残す。削除・書き換えしない。**

**本節はその新デザインを他7店舗へ展開し、
さらに渋谷新館の店舗固有見出しを確定した後続正式仕様**である。

とくに `b36b524` 節の「他7店舗は旧デザインのまま／誤適用禁止／展開は別途承認」という記述は
**`b36b524` 時点の正式仕様として正しく**、
**本節（`fc589ce` / `97b17fa` / `6b4c0b3`・Cloud承認）で正式に展開された**という履歴として扱う。

### T. 今後の禁止事項

1. **`👨‍💻結果👨‍💻` へ戻さない**（全8店舗 `📝結果📝`）
2. **差枚帯を `🔥…🔥` / `👑…👑` / `🚨…🚨` / `💥…💥` / `🐝…🐝` / `📌…📌` へ戻さない／
   末尾絵文字を復活させない**
3. **台番記号を `💫` / `✨` / `💎` へ戻さない**
4. **`ROTE_EMOJI_CONFIG` / `ROTE_BAN_EMOJI_CONFIG` を直接書き換えない**
   （生成時のローカル差し替え方式を維持。新大久保の `✨` も config 上は保持）
5. **新宿歌舞伎町の10日区切り（`period_start` / `period_end` / `day_num` /
   `calendar.monthrange` / 31日月の 21〜31）を変更しない**
6. **曜日ベース5店舗の `weekday + 1` を変更しない／`＼＼N日目結果／／` へ戻さない**
7. **上野本館・渋谷新館へ日数行を追加しない**（承認なしの新設禁止）
8. **3つの日数仕様（10日区切り／曜日ベース／日数なし）を混同しない**
9. **機種見出しを全店舗共通化しない**（店舗固有表現を維持）
10. **渋谷新館の `🏆` 見出し（北斗シリーズ／週間オススメポスター／カバネリ海門決戦／
    ジャグラーシリーズ／月間オススメポスター／東京喰種）を旧値へ戻さない**
11. **渋谷新館の北斗2機種を `【機種名】` から `👊…👊` へ戻さない**
12. **ジャグラーの最終正式値を `🤡` / `🚨` と誤記しない**（`6b4c0b3` で `🏆` が最終）
13. **渋谷新館の5テキスト構成・`text2` 空・0台省略・日数行なし・`📍` 項目・
    `✅毎日何かしらの仕掛けアリ!?` を変更しない**
14. **上野本館のインライン `_uo_monthly_text()` 経路・月間表①②③・ポスター名・
    独自機種見出しを変更しない**
15. **3生成経路のうち一部だけ変更しない**
16. **`_ROTE_NEW_TEXT_STORES` へ上野本館・渋谷新館を追加しない／
    既存の `_ROTE_SINGLE_STORES` / `_ROTE_PLAIN_STORES` / `_ROTE_NEW_THEME_STORES` /
    `_ROTE_WEEKLY_NEW_THEME_STORES` と統合・流用しない**
17. **差枚帯閾値・`差枚 >= 1000`・`sort_values(["差枚","台番"], ascending=[False,True])`・
    空カテゴリ挙動を変更しない**
18. **`94f8e7b` の機種別データ filter（index 0 限定）を壊さない**
19. **画像・ranking・ZIP・配色・JSON・session_state・widget・保存復元を今回を理由に変更しない**
20. **`b36b524` の節を削除・書き換えない**（supersede は追記で記録する）
21. **`fc589ce` / `97b17fa` / `6b4c0b3` へ reset して実装をやり直さない**
22. **無関係なリファクタ・未使用コード整理をしない**

## 2026-09-12 スランプ付き結果 side画像 24px余白削除正式採用

**正式仕様。巻き戻し禁止。**対象は**スランプ付き結果の side画像（`_side.jpg`）の
表とスランプグラフエリアの横方向レイアウトだけ**。
2026-09-12 に **ユーザーが Streamlit Cloud 実機で確認し「問題なし」と正式承認**した。

既存のスランプ／表デザイン関連セクション（`0e49bd9` / `5711df4` の白＋淡紫カード、
`3432a97` の `#FFFFCB` グラフエリア背景、`a05cb00` の非記事用表デザイン、
`ebe881e` / `6fd3991` の液晶停止、`0e79a80` / `394f309` の新宿歌舞伎町3系統など）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**side画像の横方向レイアウトだけ**の追記である。

### A. 関連commitの履歴（3つの区別を誤らないこと）

| # | commit | 位置づけ |
|---|---|---|
| ① | **`d3ef85898b6606e2fe32f9a7da7d01b92f12e14b`**（`fix: side画像の表とスランプ間の白帯を背景色で埋める`） | **中間実装。最終仕様ではない。** `SIDE_GAP = 24` を残したまま、その24pxを `#FFFFCB` で塗っただけ。総画像幅・`graph_x0`・カード位置は不変。Cloud確認の結果「白帯は消えたが24pxの空間自体が残り、表とグラフの間が広く見える」ため採用しない |
| ② | **`b9dbe4e9cc72fc8d67a8ae8b9cf2949b22279127`**（`auto: 画像生成後の設定を保存`） | **アプリの `_git_auto_push()` による自動commit**（`auto_page_inputs.json` のみ）。**side レイアウト仕様とは無関係**。reset / revert せず履歴として維持する |
| ③ | **`1f29b4b6ad841ecdbff9e5b189ce48b46322daef`**（`fix: side画像の表とグラフ間の24px余白を削除`） | **最終実装＝現在の正式仕様。** 24pxそのものをレイアウトから削除した |

**★`d3ef858` は履歴としてそのまま残す。reset / revert しない。
ただし「24pxを `#FFFFCB` で塗る」は最終仕様ではなく、`1f29b4b` が上書きしている。
`d3ef858` の状態へ戻してはならない。**

**Cloud承認日：2026-09-12（`1f29b4b`）。**

### B. 対象

**スランプ付き結果の side画像**（`auto_slump` / `auto_slump2`）。
対象関数は **`_attach_slump_to_table_side()`** で、**カテゴリ共通のhelper**である。

したがって次のすべてが対象（**カテゴリ固有分岐は追加しない**）：

その他の優秀台 ／ 高配分 ／ 個別機種（優秀台）／ ジャグラー ／
その他 **16台以上**で side 化されるカテゴリ全般。

**非対象**：
**秋葉原**（横版 side を作らない既存仕様のため実質対象外）／
**記事用 `auto_article`**（`_attach_slump_to_table_side()` を呼ばない）／
**ローテ `rote`**。

### C. 正式仕様：24pxの余白そのものを削除する

```
旧: 表 ｜ 24px(SIDE_GAP) ｜ スランプグラフエリア
新: 表 ｜ スランプグラフエリア
```

**表の右端の直後からスランプグラフエリアが始まる。**
**24pxを背景色で塗るのではなく、24pxそのものをレイアウトから削除する。**

### D. 正式仕様：`SIDE_GAP` の削除

`_attach_slump_to_table_side()` 内にあった **`SIDE_GAP = 24` は削除**した。

再調査の結果、**`SIDE_GAP` はこの関数内だけの局所定数**であり、
**他関数・他ファイル（`convert_narabi_pil.py` / `wp_client.py` / `shimazu_renderer.py`）からの
参照は0件**、**他用途なし**であることを確認済み。

### E. 正式仕様：`total_w`

```python
旧: total_w = new_tw + SIDE_GAP + graph_area_w
新: total_w = new_tw + graph_area_w
```

**side画像の総横幅は旧仕様より 24px 縮小する。高さは不変。**

### F. 正式仕様：`graph_x0`

```python
旧: graph_x0 = new_tw + SIDE_GAP
新: graph_x0 = new_tw
```

**グラフエリア全体が旧仕様より 24px 左へ移動する。**

### G. 正式仕様：スランプ背景の塗り範囲

```python
_paste_slump_area_bg(canvas, bg_path, graph_x0, 0, graph_area_w, total_h)
```

開始位置 **`graph_x0`（＝`new_tw`）**、幅 **`graph_area_w`**。

**`d3ef858` 時点の「`new_tw` から `SIDE_GAP + graph_area_w` まで塗る」実装は最終仕様ではない。
その形へ戻さない。**

### H. 正式仕様：`#FFFFCB` は維持（今回変えたのは背景色ではない）

スランプグラフ外側エリアの背景は既存正式仕様の **`#FFFFCB`** を維持する。

```python
C_SLUMP_AREA_BG = (255, 255, 203)   # 変更しない
```

関連する既存正式実装：**`3432a97b37a08555d61d0b3f3394837da727714e`**。

**今回変更したのは背景色ではなく、表とグラフの横方向レイアウトである。**
結果として **表の右端の直後から `#FFFFCB` が始まる**。

### I. 正式仕様：スランプカード配置は不変

**カード自体の仕様は一切変更しない**：
**388×472** ／ `PAD = 12` ／ `GAP = 8` ／ カードサイズ ／ カード間隔 ／
カード内部デザイン ／ 猫 ／ グラフ線 ／ 軸 ／ 背景 ／ 文字。

**グラフ側全体が24px左へ平行移動するだけで、カードのグラフエリア内での相対位置は不変。**

### J. 正式仕様：液晶も相対位置不変

液晶はめ込み仕様は変更しない。液晶が表示される場合は
**サイズ不変 ／ Y座標不変 ／ カードとの相対位置不変**のまま、
グラフ側に追従して **絶対X座標だけ 24px 左へ移動**する。

**液晶選択キー（`_gap_sel_key`）・空き判定（`_gap_fillable`）・
`_resolve_gap_screen()` などの既存仕様は変更していない。**

### K. 正式仕様：左側の表は完全維持

**表の位置 ／ 幅 ／ 高さ ／ 列幅 ／ 行高 ／ 罫線 ／ タイトルバー ／ 配色 ／ 文字 ／ 差枚色**
はすべて不変。**表領域は旧版と画素完全一致**である。

### L. 正式仕様：縦版は完全非対象

**`_attach_slump_to_table()`（縦版）は変更していない。**
検証でも **1082×2697 の出力が旧版と画素完全一致**。

**今後も今回の side 余白仕様を縦版へ適用しない。**

### M. 画像寸法（検証実測）

全 side ケースで **`new_width = old_width - 24` ／ 高さ完全一致**。

| ケース | 旧 | 新 |
|---|---|---|
| その他の優秀台 相当（20枚・液晶あり） | 2937 × 1626 | **2913 × 1626** |
| 別カテゴリ：個別機種（優秀台）相当（17枚・液晶あり） | 3061 × 1626 | **3037 × 1626** |
| 液晶なし（16枚） | 2534 × 1208 | **2510 × 1208** |

### N. 画素比較（同一入力でHEAD版と比較・FAIL 0）

- **表領域 `x < new_tw`：バイト完全一致**
- **`graph_area_w`：不変**（`= tw`）
- **グラフ側を24pxオフセット比較（`old[x ≥ old_gx0]` vs `new[x ≥ new_gx0]`）：バイト完全一致**
  ＝**グラフ側全体が24px左へ平行移動しただけ**
- カード：相対位置不変（カード左端＝`graph_x0 + PAD(12)`）
- カード間隔：不変
- 液晶：bbox `(2388,1308,2916,1604)` → `(2364,1308,2892,1604)`
  ＝**サイズ・Y不変、Xのみ −24px**
- **白帯：0** ／ **余計な `#FFFFCB` 帯：0**（表右端から `#FFFFCB` は `PAD` 分だけ）
- **縦版：画素完全一致**

AST比較でも**本体が変わった関数は `_attach_slump_to_table_side()` の1つだけ**
（新規関数0・消失関数0）。`_attach_slump_to_table` / `_paste_slump_area_bg` /
`_slump_theme_new` / `_build_slump_title_img` / `draw_slump_graph` / `draw_table_image` /
`_build_machine_img` / `show_auto_page` / `show_auto_article_page` / `show_rote_page` /
`generate_rote_image` / `generate_report_text` / `_composite_slump_onto_images` /
`_on_gap_screen_change` / `_gap_sel_key` / `_gap_fillable` / `_fit_center_in_box` /
`_save_auto_inputs` / `_restore_auto_inputs` / `_generate_rote_result_text` /
`_draw_weekly_table_image` は**すべて一致**。
定数 `C_SLUMP_AREA_BG` / `_GAP_SCREEN_SHRINK` / `_SLUMP_THEME_STORES` / `_GAP_FILL_STORES` も不変。

### O. 実機確認

**ローカル⑦プレビュー（2026-09-12）**

| 店舗 / 日付 | 画像 |
|---|---|
| 上野新館 / 2026-09-11 確定（377台） | `その他の優秀台+1,000枚以上_side.jpg` |
| 新小岩 / 2026-09-11 確定 | **`マイジャグV_高配分_side.jpg`（別カテゴリ）** ／ `その他の優秀台+1,000枚以上_side.jpg` |

確認結果：**24px余白なし ／ 表の直後から `#FFFFCB` ／ グラフが左へ寄った ／
カード間隔正常 ／ 表正常 ／ 余計な黄色帯なし ／ 白帯なし。**

プレビューは幅1460へ正規化表示されるため、**横幅24px縮小は表示高さの増加として現れる**
（上野新館 1460×808 → **1460×815**、新小岩 1460×716 → **1460×724** / 1460×832 → **1460×839**。
いずれも元幅が24px縮んだ場合の理論値と一致）。

**Cloud：2026-09-12 問題なし・正式採用。**

### P. 今回変更していないもの

縦版 ／ 記事用 ／ ローテ ／ 結果テキスト ／ 抽出条件 ／ 台番 ／ 並び順 ／ 表デザイン ／
スランプカード内部 ／ 液晶選択仕様 ／ JSON構造 ／ session_state ／ 保存 ／ 復元 ／ Pision取得。

### Q. 今後の禁止事項

1. **`SIDE_GAP = 24` を復活させない**
2. **`total_w = new_tw + SIDE_GAP + graph_area_w` へ戻さない**
3. **`graph_x0 = new_tw + SIDE_GAP` へ戻さない**
4. **`_paste_slump_area_bg()` を「`new_tw` 起点・`SIDE_GAP + graph_area_w` 幅」へ戻さない**
   （`d3ef858` の中間実装）
5. **`d3ef858` を最終仕様として扱わない／その表示状態へ戻さない**
6. **`d3ef858` / `b9dbe4e` を reset・revert しない**（履歴として維持する）
7. **`#FFFFCB`（`C_SLUMP_AREA_BG`）を変更しない**
8. **`graph_area_w`（`= tw`）を変更しない**
9. **カードサイズ・カード間隔・`PAD` ・388×472・猫・グラフ線・軸を変更しない**
10. **液晶のサイズ・Y座標・相対位置・選択キー仕様を変更しない**
11. **表（位置・幅・高さ・列幅・行高・罫線・タイトルバー・配色・文字・差枚色）を変更しない**
12. **縦版 `_attach_slump_to_table()` へ今回の仕様を適用しない**
13. **カテゴリ固有分岐を追加しない**（共通helperのまま）
14. **記事用 `auto_article` ／ ローテ `rote` へ適用しない**
15. **秋葉原へ横版 side を新設しない**
16. **抽出条件・台番・並び順・結果テキスト・JSON・session_state・保存復元・Pision取得を
    今回を理由に変更しない**
17. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】渋谷新館ローテ 出力ファイル名・並び順（2026-09-14・`7e30920`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】のローテ用（`page == "rote"`）で出力される
ファイル名と、完成フォルダ／ZIP内の並び順だけ**。
2026-09-14 に **ユーザーが Streamlit Cloud で Reboot 後に実生成し「Cloud最終確認OK」と承認**した。

既存のローテ関連セクション（`c59dd90` / `f23e0e4` / `a011c33` / `6b87aa4`＋記録 `061e42f` /
`7a47c12`＋記録 `a17ea22` / `a2bd8f7`・`9084f93`＋記録 `4914bed` / `8a85e34`＋記録 `378291b` /
`94f8e7b`＋記録 `4b32b54` / `370d5f0`＋記録 `b36b524` / `fc589ce`・`97b17fa`・`6b4c0b3` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**ファイル名と並び順だけ**を追加する仕様である。

### A. 正式実装commit

| | commit |
|---|---|
| **正式** | **`7e30920c096132d621dacf2106efa27f95943266`**（`fix: 渋谷新館ローテの出力順と北斗結果名を変更`） |

**`streamlit_app.py` の1ファイルのみ・+64 / −7・4ハンク。**
**変更関数は `show_rote_page()` の1つだけ／新規helperは `_shibuya_rote_fn()` の1つだけ／削除関数0。**
**`7e30920` は正式仕様の根拠commitであって、HEAD をここへ戻すという意味ではない。reset禁止。**

### B. 完成フォルダの正式な並び（Explorer「名前」昇順）

```
01_ジャグラー系結果.txt
02_ジャグラー系表.png
03_東京喰種結果.txt
04_東京喰種ローテ.png
05_東京喰種表.png
06_カバネリ海門決戦結果.txt
07_カバネリ海門決戦ローテ.png
08_カバネリ海門決戦表.png
09_北斗シリーズ結果.txt
10_スマスロ北斗の拳ローテ.png
11_北斗転生2ローテ.png
```

**11件ちょうど。過不足なし。**

### C. ★番号プレフィックス `01_`〜`11_` は正式仕様（暫定回避策ではない）

希望する並びは **Windows エクスプローラーの「名前」昇順では実現不可能**である。
実際に Explorer と同じ比較関数 **`StrCmpLogicalW`（shlwapi.dll）** で実測した結果、
番号なしでは次のようになり、希望順にならない。

```
カバネリ海門決戦ローテ.png / カバネリ海門決戦結果.txt / カバネリ海門決戦表.png
ジャグラー系結果.txt / ジャグラー系表.png / スマスロ北斗の拳ローテ.png
東京喰種ローテ.png / 東京喰種結果.txt / 東京喰種表.png
北斗シリーズ結果.txt / 北斗転生2ローテ.png
```

理由は2つ。
1. **カタカナ3語は必ず カ < ジ < ス の順**になるため、ジャグラーを先頭・カバネリを6番目にできない。
   漢字グループ（東京喰種・北斗）とカタカナグループを希望どおり交互配置することも不可能。
2. グループ内も `結果.txt → ローテ.png → 表.png` にならない（カタカナ「ロ」が漢字より前に来る）。

したがって **番号プレフィックスを正式採用する。**
**「番号は暫定だから外す」という判断をしてはならない。**

### D. ★並びは生成順・保存順ではなくファイル名で実現する

**内部の生成順・保存順は今回1行も変更していない。**
`{YYYYMMDD}_渋谷新館` フォルダの表示順は **Explorer が名前で再ソートした結果**であり、
Python 側の生成順・保存順とは無関係。したがって
**「保存順を並べ替えれば Explorer の表示順が変わる」という前提で実装してはならない。**

### E. ZIP（Cloud）

**`_make_zip_bytes()` は変更していない**（`for fname in sorted(files)` のまま）。
番号プレフィックスにより **ZIP内も自然に `01_`〜`11_` の順**になる。
**ZIP専用のソートロジックを追加しない。**

### F. ★北斗結果テキストのファイル名

| | |
|---|---|
| 旧 | **`北斗転生2結果.txt`（廃止）** |
| 論理名 | **`北斗シリーズ結果.txt`** |
| 最終保存名 | **`09_北斗シリーズ結果.txt`** |

- 論理名は既存定数 **`_SHIBUYA_WEEKLY_SERIES`（`"北斗シリーズ"`）を流用**して生成する。
  **機種名（`_r1_mac`）には依存させない。**
- **`北斗転生2結果.txt` へ戻さない。**

### G. ★結果テキストの本文は変更していない

**`_generate_shibuyashinkan_result_texts()` は1文字も変更していない**（AST完全一致を機械確認済み）。
書き出す変数も従来どおり `_rote_result`。
**`09_北斗シリーズ結果.txt` は旧 `北斗転生2結果.txt` と本文が完全に同一**で、
**変わったのはファイル名だけ**である。

Cloud／ローカル実機で維持を確認した本文仕様：

```
9/13(日)📝結果📝
エスパス渋谷新館

🏆北斗シリーズ🏆
🏆週間オススメポスター🏆

【スマスロ北斗の拳】
💎5,000枚超 → ・2252番台 …
【北斗転生2】
💎5,000枚超 → ・2044番台 …
```

`💎10,000枚超` / `💎5,000枚超` / `💎3,000枚超` / `💎1,000枚超` ／ `・N番台` ／
5テキスト構造 ／ text2空 ／ 0台機種セクション省略 ／ `🏆カバネリ海門決戦🏆` ／
`🏆ジャグラーシリーズ🏆` ／ `🏆東京喰種🏆` ／ `📍`項目 ／ `✅毎日何かしらの仕掛けアリ!?`
── **すべて従来どおり。今回の仕様を理由に本文を変更しない。**

### H. 画像は描画仕様を変更していない

変更したのは**最終保存ファイル名だけ**。
`generate_rote_image()` / `_draw_weekly_table_image()` / `_weekly_table_html_image()` /
`_rote_margin()` / `_rote_plain()` / `_rote_new_theme()` / `_rote_weekly_new_theme()` /
`_rote_ranking_on()` / `generate_ranking_image()` は**すべてAST一致（無変更）**。

紫系配色（ヘッダー `#7000E0` ／ 機種名帯 `#290068` ／ 台番セル `#C7B4DD` ／
台番文字 `#4B0082` ／ 表タイトル `#4B0082` ／ 日付セル `#7000E0` ／ 項目 `#C7B4DD` ／
チェック済み `#FFFFCB`）／**外背景なし**／**差枚凡例なし**／差枚の条件色（黄・橙・赤・レインボー）／
サイズ／余白／台番／日付／機種名／チェック状態 ── **すべて維持**。

### I. 実装構造（役割ベースの1箇所管理）

```python
_SHIBUYA_ROTE_ORDER: "dict[str, int]" = {
    "t3_txt": 1, "t3_tbl": 2,          # ジャグラー系（月間オススメ表③）
    "m3_txt": 3, "m3_rote": 4, "t2_tbl": 5,   # 東京喰種（月間オススメ表①）
    "m4_txt": 6, "m4_rote": 7, "t4_tbl": 8,   # カバネリ海門決戦（月間オススメ表②）
    "hokuto_txt": 9,                   # 北斗シリーズ結果
    "wk_rote": 10,                     # 週間オススメのローテ画像（入力順に連番）
}
_SHIBUYA_ROTE_TBL_ROLE: "dict[int, str]" = {2: "t2_tbl", 3: "t3_tbl", 4: "t4_tbl"}

def _shibuya_rote_fn(fname: str, no: "int | None") -> str:
    return f"{int(no):02d}_{fname}" if no else fname
```

- **機種名はユーザー入力で変わるため、ファイル名リテラルではなく
  「どのカテゴリのどの種類か」という役割で番号を決める。**
- **`no` が `None` / 0 のときは原名をそのまま返す**ため、**他店舗は番号が付かない**。
- **店舗別 if を各保存箇所へ散らさない。**採番を変えるときは**このマップ1箇所**を編集する。
- **勝手に採番し直さない。**

### J. stale 旧ファイル削除（完全一致のみ）

出力フォルダは日をまたいで再利用されるため、**番号なしの旧ファイルだけ**を削除する。

```
ジャグラー系結果.txt / ジャグラー系表.png
東京喰種結果.txt / 東京喰種ローテ.png / 東京喰種表.png
カバネリ海門決戦結果.txt / カバネリ海門決戦ローテ.png / カバネリ海門決戦表.png
北斗転生2結果.txt / 北斗シリーズ結果.txt
スマスロ北斗の拳ローテ.png / 北斗転生2ローテ.png
```

- 削除は **`store == "渋谷新館"` の既存 `_stale_fns` ループ内・完全一致のみ**。
- **glob・前方一致・部分一致・拡張子一括・フォルダ丸ごと削除は禁止。**
- 新しい `01_`〜`11_` は **`_kept_fns` で保護**され、削除対象にならない。
- 実機検証：**旧12件 → 全削除 ／ 無関係6件（`ranking_東京喰種ローテ.png` /
  `メモ.txt` / `12_東京喰種ローテ.png` / `東京喰種ローテ(1).png` / `ジャグラー系表.jpg` /
  `結果テキスト.txt`）→ 全保全（中身も無傷）**。

### K. 対象と非対象

**対象は渋谷新館の `rote` だけ。**

**非対象（今回いっさい変更していない）**：
高田馬場 ／ 上野本館 ／ 新宿歌舞伎町 ／ 溝の口本館 ／ 溝の口新館 ／ 西武新宿 ／ 新大久保 ／
`auto` ／ `auto_slump` ／ `auto_slump2` ／ `auto_article` ／ `work`。

他7店舗はファイル名・件数・生成順・保存順・結果テキスト本文・画像がHEAD相当と完全一致し、
**番号プレフィックスは付かない**ことを機械確認済み。

### L. 検証実績

**静的テスト 61 PASS / 0 FAIL ＋ 実測テスト 19 PASS / 0 FAIL。**
`_generate_shibuyashinkan_result_texts()` の5テキストが**バイト一致**、
ローテ画像・表画像が**md5一致**、`show_auto_page` / `show_auto_article_page` /
`generate_report_text` / `draw_table_image` / `draw_slump_graph` / `_attach_slump_to_table(_side)` /
`_make_zip_bytes` 等が**AST一致**。

**ローカル実機**（本体の dirty / stash を保全するため、一時clone＋ローカルdummy origin で実施。
GitHub通信0）：Pision **2026-09-13 渋谷新館 確定データ 433台**取得 → ローテ生成 →
`C:\Users\23-3\Desktop\20260913_渋谷新館` に **11件ちょうど**・
**`StrCmpLogicalW` で希望順と完全一致**・旧12件残留0・無関係6件保全・本文維持・画像7枚正常。
`_git_auto_push("ローテ画像生成")` は **「変更なし（push不要）」** で commit/push なし。

**Cloud**：push 後の初回生成では**旧仕様のZIP**が出たため **Streamlit Cloud を Reboot**。
Reboot 後に同じ 2026-09-13 渋谷新館ローテを再生成し、**ZIP内の11件が正式順**であることを確認。
**Cloud最終確認OK（2026-09-14）。**

**★Cloud はコードを push しただけでは反映されないことがある。
出力が旧仕様のままなら Manage app → Reboot を実行してから再確認する。**

### M. 今後の禁止事項

1. **番号プレフィックス `01_`〜`11_` を外さない**（暫定回避策ではなく正式仕様）
2. **勝手に採番し直さない**（変更は `_SHIBUYA_ROTE_ORDER` 1箇所で行う）
3. **ファイル名リテラルで番号を決めない**（役割ベースを維持・機種名は可変）
4. **`_shibuya_rote_fn()` の「`no` が None/0 なら原名」を変えない**（他店舗へ番号が漏れる）
5. **保存箇所ごとに店舗別 if を散らさない**
6. **並び順を生成順・保存順の変更で実現しようとしない**
7. **`_make_zip_bytes()` を変更しない／ZIP専用ソートを追加しない**
8. **`北斗転生2結果.txt` へ戻さない**／論理名の生成を `_SHIBUYA_WEEKLY_SERIES` 以外にしない
9. **結果テキスト本文・`_generate_shibuyashinkan_result_texts()` を変更しない**
   （本文デザイン変更は別仕様）
10. **画像描画仕様（紫テーマ・外背景なし・凡例なし・サイズ・配色）を変更しない**
    （画像仕様変更は別仕様）
11. **stale 削除を glob・前方一致・部分一致・フォルダ丸ごとへ広げない**
12. **新しい `01_`〜`11_` を stale 対象へ入れない**（`_kept_fns` の保護を外さない）
13. **他店舗ローテ・他ページへ横展開しない**
14. **`7e30920` へ reset して実装をやり直さない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】渋谷新館ローテ 月間オススメ表③のデータ欠落防止（2026-09-14・`9e137d5`）

**正式仕様。巻き戻し禁止。**対象は**【渋谷新館】ローテ用の
📅 月間オススメ表③（t3）の保存・復元だけ**。
正式実装 commit は **`9e137d504692c0b855f2b51014a290c04c4975b9`**
（`fix: 渋谷新館ローテの月間表③データ欠落を防止`・**`streamlit_app.py` の1ファイルのみ**・+31／−7）。

既存のローテ関連セクション（`c59dd90` / `509ec07` / `475a6c2` / `f23e0e4` / `6b87aa4` /
`7a47c12` / `a2bd8f7`・`9084f93` / `8a85e34` / `94f8e7b` / `370d5f0` /
`fc589ce`・`97b17fa`・`6b4c0b3` / `7e30920` / `e507b0d` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**t3 の保存・復元だけ**を追加する仕様である。

### A. 発生事象

`weekly_items.json` の

```
渋谷新館 / t3 / cell_date_machines / 2026-09-13 / item index 5（バーベルとらっぴ(前日より上げ!?)）
  = ["対象台が4/8でプラス差枚"]
```

が**ユーザー操作なしに消失**した（同じ日付の item 1・2 は残存）。
値は HEAD に残っていたため、**UI から同じ `4/8` を選び直して復元**した
（JSON直接編集・Git復元は使っていない）。

### B. 原因：位置キー widget × 日付キー保存

| | キー |
|---|---|
| **widget（session_state）** | **`t3_ms_{store}_{item_index}_{列index}`＝「位置」キー（日付を含まない）** |
| **正規保存先** | **`weekly_items.json → {store}.t3.cell_date_machines`＝「日付」キー** |

**表示期間が変わると同じ列 index が別の日付を指す。**
旧期間由来の session_state 値（とくに**空値**）が残ったまま新期間の日付へ対応すると、
旧実装の `_on_ms_save()` はそれを**「ユーザーが明示的に解除した空」**と誤認し、
**新しい日付の既存値を削除**できた。

旧実装は防御が **`_weekly_prev_start_{store}_t3` による開始日比較 → `t3_ms_*` 一括削除 → 再seed**
の1点しかなく、**この検知が発火しない run が1回でもあれば即座に欠落**した。

**再現**：シミュレーションのシナリオ **G（別期間でseed → 期間検知なし → 9/13を含む期間でsave）**
および **H（legacy期間でseed → 検知なし → Excel期間でsave）** で、
**`2026-09-13 / item 5` だけが消える実データと同一の欠落**を再現した。

### C. 正式仕様：主防御（B案・保存側）

**`_on_ms_save()` は「既存の `cell_date_machines` を起点」にし、
「そのrunで実際に描画された t3 セル」だけを更新する。**

```python
_drawn3: set = set()          # そのrunで描画した (item_index, 列index)

_row = dict(_cdm_new.get(_diso, {}))        # ★既存の保存値を起点にする
_touched = False
for _ci2 in range(_WEEKLY_N_ITEMS):
    if (_ci2, _cj2) not in _drawn3:  continue   # 未描画／別期間由来 → 既存値を保持
    _msk2 = f"t3_ms_{store}_{_ci2}_{_cj2}"
    if _msk2 not in st.session_state: continue
    _touched = True
    _sel = st.session_state.get(_msk2, [])
    if _sel: _row[str(_ci2)] = list(_sel)       # A: 値あり → 更新
    else:    _row.pop(str(_ci2), None)          # B: 明示解除 → そのセルだけ削除
if _row:          _cdm_new[_diso] = _row
elif _touched:    _cdm_new.pop(_diso, None)
```

| 状態 | 動作 |
|---|---|
| **描画中・値あり** | **更新** |
| **描画中・空（＝ユーザーの明示解除）** | **そのセルだけ削除** |
| **未描画** | **既存JSON値を保持** |
| **別期間由来** | **既存JSON値を保持**（現在日付の削除材料にしない） |

**旧実装の `_cm_dict3` フォールバック（未描画セルを復元値で書き直す経路）は廃止した。
未描画セルは「触らない」のが正式。**

### D. 正式仕様：日付単位 pop の条件

`cell_date_machines[date]` を**日付ごと削除してよいのは**、

1. 既存値＋今回の正規更新を反映した結果、その日付の `_row` が**本当に空**であり、
2. **かつ `_touched`＝その列で描画済みセルを1つ以上処理した**

の**両方**を満たす場合だけ。
**未描画セルに残存値があれば `_row` は非空になるため pop されない。**
**列ごと未描画なら `_touched=False` で pop しない。**

### E. 正式仕様：補助防御（A案・scope 再seed）

**t3 widget 群が「いまどの表示期間に対応しているか」を session_state で管理する。**

```python
_t3_scope_key = f"_t3_ms_scope_{store}"                      # ★新規キー（1つだけ）
_t3_scope_cur = ("E" if _use_excel_date else "L") + "|" + ",".join(
    _d0.isoformat() for _d0 in _dates)                       # E=Excel日付 / L=legacy日付
_t3_scope_changed = st.session_state.get(_t3_scope_key) != _t3_scope_cur
...
if _ms_key not in st.session_state or _t3_scope_changed:     # ★期間が変わった時だけ再seed
    st.session_state[_ms_key] = _saved_sel3
...
st.session_state[_t3_scope_key] = _t3_scope_cur              # 描画完了後に記録
```

- **期間が変わった run だけ**、その期間の保存値で再seedする（旧期間の値・空値を持ち越さない）。
- **期間が同じ通常の rerun では再seedしない**（ユーザーの現在選択値を勝手に上書きしない）。
- **`if _ms_key not in st.session_state` を無条件上書きへ変えてはならない。**

### F. 既存 `_weekly_prev_start_` との関係

**今回の防御は `_weekly_prev_start_{store}_t3` だけに依存しない。**
既存の開始日比較による検知が発火しない run があっても、
**保存側（C）と scope 再seed（E）の二重防御でデータ欠落を防ぐ。**
既存キー自体は**変更していない**（削除・意味変更もしない）。

### G. 明示解除は正式に維持する

**「保存済み値を消せなくなる」仕様にしてはならない。**
ユーザーが**現在正しく描画されている t3 widget** で値を解除した場合は、
**その日付・その行の値だけ**を正常に削除する。**他日付・他行は維持**する。

### H. テスト結果（**31 PASS / 0 FAIL**・本番JSONはコピーで検証）

| | シナリオ | 修正前 | 修正後 |
|---|---|---|---|
| A〜F・I | 通常／期間往復／legacy→Excel／未mount／キー消失／行5未描画 | OK | **PASS** |
| **G** | 別期間seed → 期間検知なし → 9/13期間save | **LOST** | **PASS** |
| **H** | legacy seed → 期間検知なし → Excel期間save | **LOST** | **PASS** |
| **J** | 9/13 / item5 / 4/8 を**明示解除** | — | **PASS（正常削除・他日付/他行は維持）** |
| **K** | 解除 → 4/8 を再選択 | — | **PASS（復活）** |
| **L** | 4/8 → 15/15 へ変更 | — | **PASS（15/15だけ保存）** |
| **M** | 期間往復 → 正しい値を再seed | — | **PASS**（`4/8` → `[]` → `4/8`） |
| **N** | widget未mount → save | — | **PASS（既存値維持）** |
| **O** | item5未描画＋他セル操作 | — | **PASS（item5維持・操作セルは反映）** |
| **P** | 通常rerun | — | **PASS（現在選択値を上書きしない）** |

**実機確認**：legacy期間（8/31〜9/6）→ 9/13の確定データ取得 → Excel期間（9/7〜9/13）へ切替
（＝以前は危険だった遷移）で、**バーベルとらっぴ行の 9/13 に `4/8` が正しく復元**。
この間 **`weekly_items.json` は HEAD と完全一致のまま**だった。

### I. 120候補（`e507b0d`）との関係

直前の正式実装 **`e507b0d4d142ec608c5cd8eca4484154e978296f`
（`fix: 渋谷新館ローテのジャグラー対象台選択肢を拡張`）はそのまま維持**する。

- `_T3_SPECIAL_OPTS` ＝ **1/1〜15/15 の全120候補**（分母15→1・各分母内は分子 分母→1）
- 先頭 `15/15` `14/15` `13/15` ／ 末尾 `2/2` `1/2` `1/1` ／ **件数120・重複0**
- **`9e137d5` では `_T3_SPECIAL_OPTS` を変更していない。**

既存保存値 **`2/2` / `2/5` / `3/3` / `8/9` / `4/8`** はすべて正常復元を確認済み。
**session_state キー形式 `t3_ms_{store}_{item}_{列}` は変更していない。**

### J. 変更範囲

| 項目 | 内容 |
|---|---|
| 変更ファイル | **`streamlit_app.py` のみ** |
| 変更関数 | **`show_weekly_table_section()` と その内部 `_on_ms_save()` の2つだけ** |
| 新規関数 / 削除関数 | **0 / 0** |
| 新規 session_state キー | **`_t3_ms_scope_{store}` の1つだけ** |

`_save_weekly_items()` ／ `_load_t3_cell_date_machines()` ／ `_load_t3_cell_machines()` ／
`_weekly_table_data()` ／ `_draw_weekly_table_image()` ／ `_weekly_table_html_image()` ／
`_load_weekly_date_checks()` ／ `show_rote_page()` ／ `generate_rote_image()` ／ `_rote_margin()`
は**すべてAST一致（無変更）**。`weekly_ck_` / `date_checks` / `cell_machines` の出現数も HEAD と同数。

### K. 非対象（今回いっさい変更・横展開していない）

t2（月間オススメ表①）／ t4（月間オススメ表②）／ 上野本館 ／ 他店舗ローテ ／
`auto` / `auto_slump` / `auto_slump2` / `auto_article` / `work` ／ 画像描画 ／ 画像デザイン ／
結果テキスト ／ JSON構造 ／ 既存JSONキー名 ／ `cell_date_machines` 優先仕様 ／
legacy `cell_machines` フォールバック。

### L. ★未横展開事項（別案件）

**t2 / t4、および上野本館の一部月間表にも「位置キー widget × 日付キー保存」に似た構造が残る。**
ただし **`9e137d5` では調査・実装・横展開していない。**
これらは**今回の正式仕様とは別案件**であり、**今回の正式化作業で勝手に触らないこと。**
対応が必要になった場合は、**調査 → 原因報告 → 最小修正案 → ユーザー承認 → 実装**の順で行う。

### M. 今後の判断基準（t3 を修正するとき）

1. **未描画 widget を「空欄」として保存しない**
2. **古い表示期間の session_state 値を新しい日付へ書かない**
3. **明示解除だけは正常に削除する**（消せなくしない）
4. **`cell_date_machines` は既存値を起点に更新する**
5. **scope 変更時だけ再seedする**
6. **通常 rerun では現在選択値を再seedで潰さない**
7. **日付 pop は「本当にその日付が空」かつ「描画済みセル処理あり」のときだけ**
8. **`_t3_ms_scope_{store}` を不用意に削除・意味変更しない**
9. **`t3_ms_{store}_{item}_{列}` の形式を変える場合は、位置/日付ズレ問題を再評価する**
10. **t2 / t4・上野本館へ機械的に横展開しない**
11. **120候補仕様（`e507b0d`）を壊さない**
12. **正式実装は `9e137d5` を基準にする**（このhashへ reset する意味ではない）

## 【正式仕様】ローテ月間表の日付切替によるチェック消失防止（2026-09-14・`0de5080`）

**正式仕様。巻き戻し禁止。**対象は**ローテ用の月間オススメ表のうち、
チェックボックス経路（`weekly_ck_*` × `date_checks`）を使う表の保存・復元だけ**。
正式実装 commit は **`0de5080c5ad429e1bdcce3432b3a0aeb66179675`**
（`fix: ローテ月間表の日付切替によるチェック消失を防止`・**`streamlit_app.py` の1ファイルのみ**・+37／−9・4ハンク）。
**ローカル実画面でユーザー確認済み・問題なし。**

直前の t3 正式仕様（実装 `9e137d504692c0b855f2b51014a290c04c4975b9` ／
記録 `8ac2a0e9f3861729c52488d02a85a39697b428e2`）と**同じ原因の別経路**への対応であり、
**t3 側は一切変更していない**。既存のローテ関連セクションは**削除・圧縮・統合・並べ替え・書き換えしない**。

### A. 対象

| 店舗 | 表 | 状態 |
|---|---|---|
| **渋谷新館** | **t2（月間オススメ表①）** | **LOST再現あり → 修正対象** |
| **渋谷新館** | **t4（月間オススメ表②）** | **LOST再現あり → 修正対象** |
| **上野本館** | **t2** | **LOST再現あり → 修正対象** |
| 上野本館 | t4 / t5 | **現在は項目未入力で休眠中**（`if not _active: return` で描画・保存とも走らない）。共通経路のため**将来項目が入れば同じ防御が働く** |
| 渋谷新館 | **t1（週間）** | **非対象**（後述） |

### B. 発生事象と原因

| | キー |
|---|---|
| **widget（session_state）** | **`weekly_ck_{store}_t{tn}_{item}_{列}`＝位置キー（日付を含まない）** |
| **保存先** | **`date_checks`＝日付キー `{日付: [bool × 項目数]}`** |

表示期間が変わると**同じ列 index が別の日付**を指す。
旧実装の防御は **`_weekly_prev_start_{store}_t{tn}` の比較1点のみ**で、
さらに保存が **`st.session_state.get(key, False)`** による一括生成（**フォールバックなし**）だったため、

- **未描画**
- **widget キー消失（GC）**
- **古い表示期間由来の False**

がすべて**「ユーザーが明示的にOFFにした False」と同じ**に扱われ、
**既存の True が False で上書きされて消えた**。

**★t3 旧実装より危険だった点**：t3 には `_cm_dict3` フォールバックがあったが、
チェックボックス経路には**フォールバックが一切なく、未描画＝False で確定保存**された。

### C. 修正前に LOST を再現したシナリオ（渋谷新館 t2 / t4・上野本館 t2 の3表とも）

| | シナリオ | 修正前 |
|---|---|---|
| C | 別期間seed → 期間変更検知なし → 新期間save | **LOST** |
| D | legacy seed → Excel期間 → 検知なし → save | **LOST** |
| E | widget未mount → save | **LOST** |
| F | widget key消失 → save | **LOST** |
| G | 保存済みTrue ＋ 古い期間由来False → 新日付save | **LOST** |
| I | 対象行未描画 ＋ 他セル操作 | **LOST** |
| **H** | **表示中の明示OFF** | **修正前から正常** |

消え方は**日付単位（その日付の行が全 False になり日付ごと消失）**と
**1セル単位（未描画の1行だけ消失）**の両方が起きた。

### D. 正式仕様：主防御（案1）

`_on_ck_change()` の `_use_excel_date` 分岐は、
**既存 `date_checks` の当日行を起点**にし、**そのrunで実際に描画したセルだけ**を更新する。

```python
_drawn_ck: set = set()          # そのrunで描画した (item index, 列index)

_dc_base = _load_weekly_date_checks(store, _tn)
_dc = {}
for _cj2 in range(len(_dates)):
    _diso2 = _dates[_cj2].isoformat()
    _prev_row = list(_dc_base.get(_diso2, []))
    _row2 = [(_prev_row[_ci2] if _ci2 < len(_prev_row) else False)
             for _ci2 in range(_WEEKLY_N_ITEMS)]
    for _ci2 in range(_WEEKLY_N_ITEMS):
        if (_ci2, _cj2) not in _drawn_ck:  continue   # 未描画／古いscope → 既存値を保持
        _ck2 = f"weekly_ck_{store}_t{_tn}_{_ci2}_{_cj2}"
        if _ck2 not in st.session_state:   continue
        _row2[_ci2] = bool(st.session_state.get(_ck2, False))   # 描画中＝ユーザーの意思
    _dc[_diso2] = _row2
```

**旧 `st.session_state.get(key, False)` による一括生成へ戻してはならない。**

### E. 正式仕様：True / False / 未描画の区別

| 状態 | 動作 |
|---|---|
| 現在scopeで描画中 ＋ **True** | **ON として保存** |
| 現在scopeで描画中 ＋ **False** | **ユーザーの明示OFF として保存** |
| **未描画** | **既存値を維持** |
| **widget key 消失 ＋ 未描画** | **既存値を維持** |
| **古い期間由来の False** | **新日付の False として保存しない** |

### F. 正式仕様：scope 防御（案2）

```python
_ck_scope_key = f"_weekly_ck_scope_{store}_t{_tn}"     # ★新規 session_state キー
_ck_scope_cur = ("E" if _use_excel_date else "L") + "|" + ",".join(
    _d1.isoformat() for _d1 in _dates)                 # 例: E|2026-09-07,...,2026-09-13
_ck_scope_changed = _use_excel_date and st.session_state.get(_ck_scope_key) != _ck_scope_cur
...
if _ck_key not in st.session_state or _ck_scope_changed:   # ★期間が変わった時だけ再seed
    ...
if _bk_key not in st.session_state or _ck_scope_changed:   # weekly_blank_* も同条件で再seed
    ...
if _use_excel_date:
    st.session_state[_ck_scope_key] = _ck_scope_cur        # 描画完了後に記録
```

- **scope が変わった run だけ**、その期間の `date_checks` から再seed。
  **古い期間の True / False を新しい期間へ持ち越さない。**
- **`weekly_blank_*`（空欄にする行）も同じ条件で再seed**する。
- **scope が同じ通常 rerun では再seedしない**（ユーザーの現在の入力を上書きしない）。

### G. `_weekly_prev_start_` との関係

既存の `_weekly_prev_start_{store}_t{tn}` による処理は**互換のためそのまま残している**。
ただし**今回の防御はこれに依存しない。**
**旧検知が発火しない run でも、主防御（D）＋ scope 防御（F）で LOST しない。**

### H. 適用条件は `_use_excel_date`（店舗名のベタ書きをしない）

今回の防御は **`_use_excel_date`（＝日付キー保存 `date_checks` を使う表）** にだけ作用する。
そのため **渋谷新館 t2 / t4 ／ 上野本館 t2 / t4 / t5** へ共通で効き、
**店舗名や table_num のベタ書きによる限定はしない。**

### I. 渋谷新館 t1 は非対象

t1 は **`checks` ＋ `start_date` という位置キーJSONで完結**しており、
**位置キーwidget × 日付キー保存のズレが発生しない**。
**今回の scope 防御を t1 へ機械的に適用しない。**
（テストで、t1 の legacy 保存が `checks` / `start_date` のままで `date_checks` を作らないことを確認済み。）

### J. 上野本館 t4 / t5

**現在は項目未入力で休眠中**（描画も保存も走らない）。
今回 **項目追加・有効化・本番データ変更はしていない。**
scratch 上で「項目あり」を模擬し、**共通経路の防御が働くことを確認済み**。
将来項目が入った場合も同じ防御が自然に作用する。

### K. テスト結果（**56 PASS / 0 FAIL**・本番JSONはコピーで検証）

**渋谷新館 t2 / 渋谷新館 t4 / 上野本館 t2 の3表すべてで：**

| | シナリオ | 修正前 | 修正後 |
|---|---|---|---|
| A | 通常表示 → save（全日付不変） | PASS | **PASS** |
| B | 期間移動 | 窓外削除 | **窓外削除のまま（既存仕様維持）**※判定枠外 |
| **C** | 別期間seed → 検知なし → 新期間save | **LOST** | **PASS** |
| **D** | legacy seed → 検知なし → Excel期間save | **LOST** | **PASS** |
| **E** | widget未mount → save | **LOST** | **PASS** |
| **F** | widget key消失 → save | **LOST** | **PASS** |
| **G** | 古い期間由来False → 新日付save | **LOST** | **PASS** |
| **H** | **表示中の明示OFF** | PASS | **PASS（正常に削除できる）** |
| **I** | 対象行未描画 ＋ 他セル操作 | **LOST** | **PASS** |
| **J** | 複数Trueの片方だけ明示OFF → 他方維持 | — | **PASS** |
| **K** | 未描画行のTrue維持 ＋ 他セル操作 | — | **PASS** |
| **L** | 旧 `_weekly_prev_start_` が効かない条件でも scope で再seed | — | **PASS** |
| **M** | 期間A → 期間B → 期間A で各期間の値を再seed | — | **PASS**（True/False/True） |
| **N** | 通常rerun で現在値を潰さない | — | **PASS** |
| **O** | widget key GC ＋ 未描画 ＋ 他セルsave → 既存True維持 | — | **PASS** |

加えて **上野本館 t4 / t5**（scratchで項目ありを模擬）も **C相当が PASS**。

### L. ★案3（窓外日付の保持）は非採用

今回 **「窓外日付を保持する」案3は実装していない。**

- `date_checks` は**従来どおり表示期間分で全置換**する。
- **窓外の日付が消える既存仕様を維持**する。
- **保持日数の延長はしない。**

**今回の修正は保存期間の仕様変更ではなく、
「現在扱っている表示期間内での誤削除防止」だけ**である。

**★将来「窓外日付も保持したい」となった場合は、今回の修正とは別案件として扱う。
今回の防御と混ぜてはならない。**

### M. t3 正式仕様・120候補との関係

**渋谷新館 t3 の正式実装 `9e137d5` は変更していない**（`_on_ms_save` は AST 一致）。
**`_drawn3` ／ `_t3_ms_scope_{store}` ／ `cell_date_machines` 防御はすべて維持。**
**`e507b0d` の 1/1〜15/15 全120候補（`_T3_SPECIAL_OPTS`）も変更していない。**

### N. 変更範囲

| 項目 | 内容 |
|---|---|
| 変更ファイル | **`streamlit_app.py` のみ** |
| 変更関数 | **`show_weekly_table_section()` と その内部 `_on_ck_change()` の2つだけ** |
| 新規関数 / 削除関数 | **0 / 0** |
| 新規 session_state キー | **`_weekly_ck_scope_{store}_t{tn}` の1つだけ** |
| diff | **+37 / −9（4ハンク）** |

### O. 非対象（今回いっさい変更していない）

渋谷新館 t1 ／ 渋谷新館 t3 ／ 120候補 ／ 画像描画 ／ 画像デザイン ／ 結果テキスト ／
`_save_weekly_items()` ／ `_load_weekly_date_checks()` ／ `_load_t3_cell_date_machines()` ／
`_load_t3_cell_machines()` ／ `_weekly_table_data()` ／ `_draw_weekly_table_image()` ／
`_weekly_table_html_image()` ／ `show_rote_page()`（すべて AST 一致）。

### P. 実画面承認

**ローカル実画面でユーザーが確認し「問題なし」と承認済み（2026-09-14）。**

### Q. 今後の判断基準（この経路を修正するとき）

1. **`weekly_ck_*` は位置キーであることを忘れない**
2. **`date_checks` は日付キー保存**
3. **未描画 checkbox を False として保存しない**
4. **widget key 消失を明示OFFと扱わない**
5. **明示OFFだけは正常に False 保存する**（消せなくしない）
6. **既存 `date_checks` 行を起点に、描画済み index だけ更新する**
7. **`_weekly_ck_scope_{store}_t{tn}` を不用意に削除・意味変更しない**
8. **scope 変更時だけ再seedする**
9. **通常 rerun ではユーザー値を潰さない**
10. **`_weekly_prev_start_` だけに依存しない**
11. **`_use_excel_date` 対象だけに適用する**（店舗名をベタ書きしない）
12. **渋谷新館 t1 へ機械的に横展開しない**
13. **渋谷新館 t3 の `9e137d5` 防御を壊さない**
14. **`e507b0d` の120候補を壊さない**
15. **窓外日付を保持する仕様へ勝手に変更しない**
16. **窓外保持は別案件**
17. **上野本館 t4 / t5 は現在休眠中だが、将来有効化時も同防御が働くことを前提とする**
18. **正式実装基準は `0de5080`**（このhashへ reset する意味ではない）

## 【正式仕様】新大久保ローテ 結果テキストの機種名囲み（2026-09-14・`bbd869a`）

**正式仕様。巻き戻し禁止。**対象は**【新大久保】のローテ用 結果テキストで、
機種名を囲む記号だけ**。
正式実装 commit は **`bbd869afffae14363bfd9637f05bb4fad550dbb3`**
（`fix: 新大久保ローテ結果の機種名囲みを統一`・**`streamlit_app.py` の1ファイルのみ**・+9／−1・2ハンク）。
**ローカル実画面でユーザー確認済み・問題なし。**

既存のローテ関連セクション（`fc589ce`・`97b17fa`・`6b4c0b3` の結果テキスト新デザインほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**機種名の囲み記号だけ**を追加する仕様である。

### A. 対象と変更内容

| | |
|---|---|
| 変更前 | **`🍯機種名🍯`** |
| 変更後 | **`【機種名】`** |

```
9/13(日)📝結果📝
エスパス新大久保

🏆9月7日～9月13日オススメポスター🏆
7日目

【スマスロ北斗の拳】     ← 旧: 🍯スマスロ北斗の拳🍯
💎10,000枚超
・1001番台
```

### B. 原因

新大久保の結果テキストは `_generate_rote_result_text()` 内で
**`ROTE_EMOJI_CONFIG[store][0]`（機種名囲み絵文字）**を機種名の前後に付けていた。

```python
ROTE_EMOJI_CONFIG["新大久保"] = ("🍯", "🐝")   # 第1要素が機種名囲み
...
if store == "新宿歌舞伎町":          # ← 新宿歌舞伎町だけ【】をハードコードしていた
    lines.append(f"【{machine_name}】")
else:
    lines.append(f"{_re}{machine_name}{_re}")
```

**新大久保専用の分岐ではなく、共通関数内の「新宿歌舞伎町だけ特別扱い」が原因。**

### C. 正式な修正方法

**`ROTE_EMOJI_CONFIG` 自体は変更せず、結果テキストの表示側だけで切り替える。**

```python
# ローテ結果テキストで機種名を「【機種名】」で囲む店舗。
# 未登録店舗は ROTE_EMOJI_CONFIG の囲み絵文字（例 🌠機種名🌠）のまま。
# ROTE_EMOJI_CONFIG 自体は画像・他用途でも使うため変更しない（表示側だけで切り替える）。
_ROTE_BRACKET_NAME_STORES: "frozenset[str]" = frozenset({
    "新宿歌舞伎町",
    "新大久保",
})
...
if store in _ROTE_BRACKET_NAME_STORES:
    lines.append(f"【{machine_name}】")
else:
    lines.append(f"{_re}{machine_name}{_re}")
```

**店舗追加はこの集合への追記だけで行う。店舗名を各所へベタ書きしない。**

### D. ★共通絵文字設定は変更しない

**`ROTE_EMOJI_CONFIG` ／ `ROTE_BAN_EMOJI_CONFIG` ／ `STORE_EMOJI_CONFIG` は1文字も変更していない。**
**`ROTE_EMOJI_CONFIG["新大久保"] = ("🍯", "🐝")` は定義のまま残す。**

理由：これらは結果テキスト以外・画像・別用途でも利用される可能性があるため、
**新大久保の結果テキスト修正のために共通設定を書き換えないこと**を正式仕様とする。

### E. 正式な対象範囲

| 店舗 | 機種名の囲み |
|---|---|
| **新大久保** | **`【機種名】`（今回変更）** |
| **新宿歌舞伎町** | **`【機種名】`（従来どおり）** |
| その他店舗 | **各店舗の `ROTE_EMOJI_CONFIG` 由来の囲み（従来どおり）** |

### F. 他7店舗は不変（バイト一致で確認）

高田馬場 ／ 上野本館 ／ 新宿歌舞伎町 ／ 溝の口本館 ／ 溝の口新館 ／ 西武新宿 ／ 渋谷新館 の
結果テキストは**修正前後でバイト一致**。

- 新宿歌舞伎町 → **`【機種名】` のまま**
- 溝の口新館 → **`🌠機種名🌠` を維持**
- 上野本館 → **`🗼機種名🗼` を維持**
- 西武新宿 → **`👑機種名👑` を維持**

※ 上野本館の月間表結果テキスト（`show_rote_page` 内インライン `_uo_monthly_text` の `_re` 使用箇所）は
**別経路で今回未変更**。

### G. 変更していないもの

機種名文字列そのもの ／ 台番 ／ 差枚帯（`💎10,000枚超` ほか）／ 台番行 `・N番台` ／
日目表示 ／ 曜日判定 ／ ヘッダー ／ 改行 ／ 空行 ／ 結果テキスト全体構成 ／ 抽出条件 ／
画像生成 ／ ローテ画像 ／ ランキング画像 ／ 月間表 ／ 週次表 ／ 保存処理 ／
t3の120候補（`_T3_SPECIAL_OPTS`）／ `_t3_ms_scope_` ／ `_weekly_ck_scope_`。

### H. テスト結果（**45 PASS / 0 FAIL**）

| | 内容 | 結果 |
|---|---|---|
| **A** | 新大久保の結果テキストに `🍯機種名🍯` が **0件**（修正前は4件） | **PASS** |
| **B** | `【機種名】` へ変更（`【】` の数が機種数と一致） | **PASS** |
| **C** | 機種名文字列そのものは不変 | **PASS** |
| **D** | 台番・差枚帯・日目・ヘッダー・改行・行数が不変（🍯→【】の置換だけで**修正前とバイト一致**・行数25→25・台番絵文字 `✨` も出ない） | **PASS** |
| **E** | 他7店舗の結果テキストが**修正前後でバイト一致** | **PASS** |
| **F** | 画像系関数が **AST一致**（`generate_rote_image` / `generate_ranking_image` / `_rote_margin` / `_rote_plain` / `_rote_new_theme` / `_rote_weekly_new_theme` / `_rote_ranking_on` / `_draw_weekly_table_image` / `_weekly_table_html_image` / `show_rote_page` / `_on_ck_change` / `_on_ms_save` / `_save_weekly_items` / `generate_report_text`） | **PASS** |
| **G** | 共通設定（`ROTE_EMOJI_CONFIG` / `ROTE_BAN_EMOJI_CONFIG` / `STORE_EMOJI_CONFIG` / `_ROTE_NEW_TEXT_STORES`）が**すべて不変** | **PASS** |

### I. 変更範囲

| 項目 | 内容 |
|---|---|
| 変更ファイル | **`streamlit_app.py` のみ** |
| 変更関数 | **`_generate_rote_result_text()` の1つだけ** |
| 新規関数 / 削除関数 | **0 / 0** |
| 新規定数 | **`_ROTE_BRACKET_NAME_STORES` の1つだけ** |
| diff | **+9 / −1（2ハンク）** |

### J. 実画面承認

**ローカル実画面でユーザーが確認し「問題なし」と承認済み（2026-09-14）。**

### K. 作業開始時のGit経緯（誤認しないこと）

前回の正式記録 `5eda14585f0a644c69af46b3e460f85f898d8ef4` のあと、
**アプリの `_git_auto_push()` による自動commit `796c610`（`rote_machines.json` のみ）**が作成されていた。
**`5eda145` は祖先で、`streamlit_app.py` / `CLAUDE.md` は不変**であることを確認し、
**その現HEADを基準に実装した**（reset・rebase はしていない）。

### L. 今後の判断基準

1. **新大久保ローテ結果テキストの機種名は `【機種名】` が正式仕様**
2. **`🍯機種名🍯` へ戻さない**
3. **`ROTE_EMOJI_CONFIG["新大久保"] = ("🍯", "🐝")` を今回のために変更しない**
4. **結果テキストの表示側だけで対応する**
5. **`_ROTE_BRACKET_NAME_STORES` を不用意に削除・意味変更しない**
6. **正式対象は 新宿歌舞伎町 と 新大久保 の2店舗**
7. **他店舗へ `【】` を機械的に横展開しない**
8. **画像用途の絵文字設定と結果テキストの表示仕様を混同しない**
9. **`_generate_rote_result_text()` 周辺を変更するときは新大久保の `【】` を回帰確認する**
10. **他7店舗の囲み表示を維持する**
11. **実画面確認済み**
12. **正式実装基準は `bbd869a`**（このhashへ reset する意味ではない）

## 【正式仕様】稲毛 スランプ付き結果ポスト：Pision / slotterguild 2系統データ取得（2026-09-15・`a51e362`）

**正式仕様。巻き戻し禁止。**対象は**【稲毛】スランプ付き結果ポスト用ページの
「📈 日付からデータを自動取得」の確定データモードだけ**。
正式実装 commit は **`a51e3628f147ccfccfba9f0ce387cfe7c2b9363f`**
（`feat: 稲毛にslotterguildデータ取得を追加`・**`streamlit_app.py` の1ファイルのみ**・**+180 / −1**・8ハンク）。
**ローカル実機確認 → push → ユーザーによる Cloud 実機確認まで完了し「問題なし」と承認済み。**

既存の CLAUDE.md 各節は**削除・圧縮・統合・並べ替え・書き換えしない**。
本節は**2026-09-15 の正式仕様として追加**するものである。

### ① 対象と目的

| 項目 | 値 |
|---|---|
| 店舗 | **稲毛のみ** |
| ページ | **スランプ付き結果ポスト用**（`show_auto_page(with_slump=True)`） |
| 対象モード | **確定データのみ** |
| 目的 | **「取得元を選べるようにする」こと** |

**★「Pision 完全非依存化」ではない。**下記⑫のとおりスランプ合成側には Pision 前提の既存ゲートが
残っており、それは今回**意図的に変更していない**。Pision 完全非依存化は**別案件**である。

### ② UI 正式仕様

```
### 📈 日付からデータを自動取得（稲毛）
データ種別: (●) 確定データ  ( ) 速報データ（当日・営業中）   ← 既存のまま
日付を選択: [2026/09/14]                                    ← 既存widget 1つを共用
┌──────────────────────┬──────────────────────┐
│ 🔄 Pisionから取得    │ 🌐 サイトから取得    │   ← 確定データ時のみ横2列
└──────────────────────┴──────────────────────┘
✅ 2026-09-14 の確定データ（196台）を取得し、①にセットしました。／ 取得元: slotterguild.com
```

- **日付widgetは既存の1つだけ。左右それぞれに日付widgetを作らない。**
- 左の Pision ボタンは **既存 key `auto_tb_refetch_{store}` を維持**する（新keyへ変えない）。
- 右は新 key **`auto_tb_sg_{store}`**。
- 分岐は **`elif store in _SG_FETCH_STORES and _sg_hall_id(store) is not None:`** の1箇所のみ。

### ③ 速報モードは変更しない

**slotterguild.com は確定データのみ。速報モードへは一切手を入れない。**

- 速報時は従来どおり **`⚡ 速報を取得` / `📂 既存のデータを取得`**（`elif _tb_is_rt and _tb_rt_ok:` 経路）
- 収集中は従来どおり **`⏳ 収集中...` / `🔍 今すぐ確認`**
- 手動確認・自動ポーリング（30秒）・既存データ取得の3処理ブロックも不変

正式確認時に、**速報ボタンブロックと収集中ボタンブロックが修正前と
バイト完全一致（586B一致）**であることを機械確認済み。

### ④ 稲毛限定ゲート（他店舗へ横展開しない）

```python
_SG_BASE_URL = "https://slotterguild.com/hall_data_db/halldata"
_SG_FETCH_STORES: "frozenset[str]" = frozenset({"稲毛"})
_SG_HALL_IDS: "dict[str, int]" = {"稲毛": 566}
_SG_TIMEOUT = 20
```

**非対象12店舗には「🌐 サイトから取得」を出さない。**従来どおり
`_tb_refetch = st.button("🔄 取得", key=f"auto_tb_refetch_{store}")` の単一ボタンのまま。

### ⑤ ★hall_id は Pision と別体系（混同禁止）

| 系統 | 稲毛の hall_id |
|---|---|
| **slotterguild** | **566** |
| **Pision** | **4031** |

**この2つを混同しない。**slotterguild 側は `_SG_HALL_IDS` の固定値、
Pision 側は従来どおり `fetch_pision_halls()` の結果から
「store名 と エスパス を両方含むホール」を検索して解決する（ハードコードしない）。

### ⑥ 取得元エンドポイント（GET のみ・認証不要）

| 用途 | エンドポイント |
|---|---|
| **表データ** | `halldata_api.php?download_dedama_s_excel&hall_id=566&date_at=YYYY-MM-DD&name_col=name_1` |
| **スランプpoints** | `hall_all.php?hall_id=566&date_at=YYYY-MM-DD` |

**`new.php` からは台データを取らない**（新着一覧ページであり台別データを含まない）。
**書き込み系API（`set_schedule_onetime` 等）は使わない。GET のみ。**

### ⑦ 表データは既存共通パイプラインへ無加工で流す

slotterguild の xlsx 列は

```
台番 / 機種名（データサイト表記） / 機種名（name_1） / 差枚 / BB / RB / ART / G数
```

で、**既存 `COLUMN_ALIASES` がすべて解決できる**（`機種名（データサイト表記）` / `ART` / `G数`
はいずれも既存 alias に含まれる）。実測で **`normalize_df()` の missing は `[]`**。

- **専用 normalize 層を新設しない。**
- **`COLUMN_ALIASES` / `normalize_df()` / `apply_name_conversion()` / `_read_uploaded_df()` を変更しない。**
- **★CSV経路は使わない。** slotterguild の CSV は **UTF-8 BOM** だが既存
  `_read_csv_raw()` は **`encoding="cp932"` 固定**のため `UnicodeDecodeError` になる。
  **xlsx を使えば既存コード変更が不要**なので xlsx を正式とする。

### ⑧ 既存 session_state へ流す（新しい保存システムを作らない）

取得成功時は **Pision 確定取得と同じ既存キー**へ入れる。

```python
st.session_state[_tb_bytes_key]         # = _auto_tb_file_bytes_fix_{store}
st.session_state[_tb_name_key]          # = "{YYYYMMDD}_{store}_20S.xlsx" 例: 20260914_稲毛_20S.xlsx
st.session_state[_tb_count_key]
st.session_state[_tb_fetched_key]
st.session_state[_tb_rt_items_key]      # = _auto_tb_rt_items_{store}
st.session_state[_tb_rt_items_date_key] # = _auto_tb_rt_items_date_{store}
st.session_state[_tb_src_key]           # = _auto_tb_src_{store}（取得元表示・JSON保存しない）
```

その後 `st.rerun()` し、**既存の `_tb_uploaded` → 手動アップロードと同じ入口**へ乗る。
以降の **全台系 / 高配分 / 並び / ジャグラー優秀台 / その他優秀台 / 結果テキスト / 画像生成**は
すべて既存経路を共通利用する。

### ⑨ スランプ points は既存キャッシュへ注入（専用実装を作らない）

`hall_all.php` の各行に埋まっている

```html
<tr data-dai="355" data-coin="6500" data-machine="...">
  ... <script>drawMiniGraph('mg-355',[{"x":0,"y":0},...,{"x":3543,"y":6500}],3556);</script>
```

を解析し、**Pision の details と同形**の items を作る。

```
{unitId, displayName, modelName, points, diff, games, bb, rb, art}
points = [{"x": int, "y": int}, ...]
```

- **`_slump_apply_names(items)` を再利用**する（機種名変換の適用）。
- `displayName` には **xlsx の「機種名（データサイト表記）」を台番で突き合わせて上書き**する。
  `hall_all` の `data-machine` は name_1 表記で未登録が出るため。これにより
  **`_convertedName` が Pision と完全一致**する。
- **⑦プレビュー・⑧本番は既存の cache-first 経路をそのまま使う**
  （`_auto_tb_rt_items_{store}` を見る3箇所）。
  **slotterguild 専用のスランプ生成処理を別実装しない。**

### ⑩ 取得元表示

| session_state | 値 |
|---|---|
| **`_auto_tb_src_{store}`** | **`"Pision"` または `"slotterguild.com"`** |

**JSON へは保存しない**（session_state のみ）。成功メッセージ末尾に `／ 取得元: {値}` を表示する。
Pision 側は確定取得と速報取得（`_save_rt_items_to_session`）の**2箇所**で `"Pision"` を設定する。

### ⑪ エラー処理正式仕様（例外を握り潰さない）

`_sg_get()` が次をすべて **`_SGError`（ユーザー向け文面）** にして送出する。

| 事象 | 表示 |
|---|---|
| **HTTP 403** | `❌ slotterguild.com へのアクセスが拒否されました（HTTP 403）。` |
| HTTP 404 | `❌ slotterguild.com にページが見つかりません（HTTP 404）。` |
| HTTP 5xx | `❌ slotterguild.com がエラーを返しました（HTTP {code}）。` |
| その他非200 | `❌ slotterguild.com が予期しない応答を返しました（HTTP {code}）。` |
| **timeout** | `❌ サイトへの接続がタイムアウトしました（20秒）。時間をおいて再試行するか、Pisionから取得してください。` |
| 接続失敗 | `❌ サイトへの接続に失敗しました: {e}` |
| Content-Type不正 | `❌ サイトが想定外の形式を返しました（Content-Type: {ct}）。` |
| 非xlsx（PKシグネチャ無し） | `❌ サイトから正しい Excel ファイルを取得できませんでした。` |
| HTML構造変化 | `❌ サイトのページ構造が変わった可能性があります（台データが見つかりません）。` |
| **0台** | `❌ サイトに {日付} のデータがありません（未収集 / 店休日の可能性があります）。` |

**`requests.get` には必ず有限 timeout（`_SG_TIMEOUT = 20`）を指定する。**
**失敗時に既存の Pision データ・手動アップロードデータ・既存 session_state を上書きしない。**

### ⑫ ★半端更新禁止（最重要）

slotterguild 取得は **2リクエスト（xlsx と hall_all）**になるため、
**次の全検証を通過したときだけ** session_state を更新する。

```
1. xlsx 取得
2. xlsx 行数 > 0
3. items 取得
4. items 件数 > 0
5. xlsx の台番集合 == items の unitId 集合
   ↓ すべて成功
   _sg_ok = True → ここで初めて7キーを更新 → st.rerun()
```

- **`try` ブロック内に `st.session_state[...]` の書き込みを置かない**（構造テストで0件を機械確認）。
- **`st.rerun()` も成功時の1回のみ。**
- **表だけ使うフォールバックは作らない**（表＋points が両方揃ったときだけ成功扱い）。

### ⑬ 正式確認結果（2026-09-14・稲毛）

| 項目 | 結果 |
|---|---|
| slotterguild 台数 | **196台** |
| Pision 台数 | **196台** |
| 台番集合 | **完全一致** |
| 差枚 / G数 / BB / RB / ART | **すべて不一致0件** |
| **normalize後 DataFrame** | **完全一致（`a.equals(b) == True`・7列×196行）** |
| 機種名（変換後） | **196/196 一致** |
| 未登録機種 | **0件** |
| スランプ points | **196/196台 取得（欠損0）** |
| **points y系列** | **196/196 完全一致** |
| ①表 | 総差枚 **-11,500** / 平均差枚 **-59** / 平均G数 **2,205** / 勝率 **75/196**（両経路一致） |

純粋テストは **合計75件 PASS / 0 FAIL**（取得36 ＋ 非回帰18 ＋ 等価性21）。

### ⑭ x スケール差は実用上問題なし

| | x の最大値 |
|---|---|
| slotterguild | 実G数寄り（0〜3,556） |
| Pision | 間引き値（0〜809） |

**`draw_slump_graph()` が `max_x = max(p["x"])` で自前正規化する**ため絶対スケールは不問。
正規化後の相対xズレは最大7.4%・平均1.9%だが、**y系列・点数・終点がすべて同一**で、
実際に両ソースを `draw_slump_graph()` で描画して比較した結果、
**山谷の形・到達点・表示差枚は同等**（画素差は横1〜2pxのズレによる0.85〜5.73%のみ）。

### ⑮ 確認状況

| 項目 | 結果 |
|---|---|
| ローカル Pision 取得 | **正常** |
| ローカル slotterguild 取得 | **正常** |
| ①表 | **一致** |
| normalize後 DataFrame | **完全一致** |
| ⑦プレビュー（slotterguild経路） | **6枚正常生成・各台にスランプ合成を目視確認** |
| **Cloud 実機**（稲毛 → スランプ付き結果ポスト用 → 確定データ → サイトから取得） | **ユーザー確認済み・問題なし → Cloud 利用も正式採用** |

### ⑯ 正式記録する実装要素

| 区分 | 内容 |
|---|---|
| **定数** | `_SG_BASE_URL` / `_SG_FETCH_STORES` / `_SG_HALL_IDS` / `_SG_TIMEOUT` ／ 正規表現4種（`_SG_ROW_RE` / `_SG_TD_RE` / `_SG_GRAPH_RE` / `_SG_TAG_RE`）／ 例外 `_SGError` |
| **新規helper（5つ）** | `_sg_hall_id()` / `_sg_get()` / `_sg_fetch_excel()` / `_sg_cell_int()` / `_sg_fetch_items()` |
| **変更関数（2つだけ）** | `show_auto_page()` ／ その内部 `_save_rt_items_to_session()`（取得元1行の追加のみ） |
| **消失関数** | **0** |

### ⑰ 非変更（今回いっさい触れていない）

`COLUMN_ALIASES` ／ `normalize_df` ／ `_read_uploaded_df` ／ `_read_csv_raw` ／
`_slump_apply_names` ／ `draw_slump_graph` ／ Pision API関数群（`fetch_pision_halls` /
`fetch_pision_results` / `fetch_pision_realtime` / `_parse_pision_rt_detail` / `_pision_request` /
`_get_pision_api_key`）／ `run_auto_pipeline` ／ `_save_auto_inputs` ／ `_restore_auto_inputs` ／
`_merge_auto_entry` ／ `_build_sue_images` ／ `show_auto_article_page` ／ `show_rote_page` ／
`generate_report_text` ／ `wp_client.py` ／ `requirements.txt` ／ Secrets ／ 各種JSON schema ／
`機種名変換.xlsx`。

**いずれも AST バイト一致を機械確認済み。**

### ⑱ 今回の正式仕様に含めないもの（別案件）

**Pision 完全非依存化** ／ **他店舗への slotterguild 展開** ／ **slotterguild 速報取得** ／
**`schedule_onetime` の自動実行** ／ **書き込みAPIの利用** ／ **CSV経路** ／
**Secrets 変更** ／ **WordPress 連携変更**。

### ⑲ 今後の禁止事項

1. **速報モードの UI・処理を変更しない**（slotterguild は確定データのみ）
2. **日付widget を左右で分けない**（既存1つを共用する）
3. **Pision ボタンの key `auto_tb_refetch_{store}` を変えない**
4. **`_SG_FETCH_STORES` / `_SG_HALL_IDS` を承認なしに他店舗へ広げない**
5. **slotterguild の 566 と Pision の 4031 を混同しない**
6. **専用 normalize 層を新設しない**／`COLUMN_ALIASES` を変更しない
7. **CSV経路を使わない**（`_read_csv_raw` は cp932 固定）
8. **新しい保存キー・新しいJSONを作らない**（既存 `_auto_tb_file_bytes_fix_*` 系を流用）
9. **slotterguild 専用のスランプ生成処理を別実装しない**（既存 cache-first 経路を使う）
10. **`_auto_tb_src_{store}` を JSON へ保存しない**
11. **例外を握り潰さない**／`requests.get` の timeout を外さない
12. **半端更新をしない**（全検証成功後にのみ session_state を更新する）
13. **表だけ使うフォールバックを作らない**
14. **失敗時に既存 Pision データ・手動アップロードデータを上書きしない**
15. **`new.php` から台データを取らない**／**書き込みAPIを使わない**
16. **⑰の非変更リストを今回を理由に変更しない**
17. **本節を「Pision 完全非依存化」と誤記しない**
18. **正式実装基準は `a51e362`**（この hash へ reset する意味ではない）

## 【正式仕様】稲毛 スランプ付き結果ポスト：空き枠のgap猫撤去・空白維持（2026-09-15・`51008ee`）

**正式仕様。巻き戻し禁止。**対象は**【稲毛】スランプ付き結果ポスト用ページの
スランプグラフ最終行の空きコマだけ**。
正式実装 commit は **`51008eeb7314c29dca9fa4f705ca3702a0ba84d8`**
（`fix: 稲毛スランプ空き枠の猫表示を撤去`・**`streamlit_app.py` の1ファイルのみ**・**+18 / −116**）。
**ローカル実画面でユーザーが確認し「問題なし」と承認済み。**

既存の CLAUDE.md 各節は**削除・圧縮・統合・並べ替え・書き換えしない**。
本節は**2026-09-15 の正式仕様として追加**するものである。

### ① 正式仕様

稲毛のスランプ付き結果ポスト用で、**最終行に空きコマが発生しても
gap猫を表示しない。液晶も表示しない。空き部分はそのまま空白にする。**

```
猫なし ／ 液晶なし ／ 空きはそのまま
```

| 空きコマ数 | 表示 |
|---|---|
| **0コマ** | 何も入れない |
| **1コマ** | 何も入れない |
| **2コマ** | **何も入れない**（従来は猫が入っていた） |
| **3コマ** | **何も入れない**（従来は猫が入っていた） |

**縦版（`_attach_slump_to_table`・COLS=3）・side版（`_attach_slump_to_table_side`・COLS=4）
とも同じ。**

空き部分は既存のスランプ結果背景 **`#FFFFCB`（`C_SLUMP_AREA_BG`）のクリーム背景のまま**で、
**何も追加表示しない。**

### ② ★液晶は復活させない（2026-09-11 正式仕様を維持）

**本節は「液晶システムの削除」でも「液晶の復活」でもない。**

既存正式仕様
**「【正式仕様】スランプ付き結果ポストの液晶挿入停止（2026-09-11・`ebe881e` / `6fd3991`）」は
そのまま有効**であり、結果ポスト用途では既存OFFゲートにより液晶が入らない状態を維持する。

**今回いっさい変更していない（AST不変を機械確認済み）:**

`_GAP_FILL_STORES` ／ `_GAP_FILL_OFF_SLUMP_STORES` ／ `_gap_fill_on()` ／
`_gap_fillable()` ／ `_gap_sel_key()` ／ `_gap_screen_paths_for_bans()` ／
`_featured_machine_for_bans()` ／ `_resolve_gap_screen()` ／ `_on_gap_screen_change()` ／
`_fit_center_in_box()` ／ `_GAP_SCREEN_SHRINK`（0.95）／ `_ARTICLE_GAP_FILL_STORES`。

**既存の液晶コードは残す。**`_gap_fill_on()` は**全13店舗で `False`**（結果ポスト経路の液晶は無効）で、
この値は修正前後で**全店舗一致**することを実行確認済み。

合成部は**猫導入前（`79b3126^`）の形へ復帰**した（AST完全一致）:

```python
# 最終行の空きコマ（2以上）に液晶をはめ込む
empty = COLS * rows - n
if gap_screen_img is not None and empty >= 2:
    ...
    fitted, ox, oy = _fit_center_in_box(gap_screen_img, _sw, _sh)
    canvas.paste(fitted, (...))
```

結果ポスト用途では `gap_screen_img` が常に `None` になるため、**最終的な稲毛の表示は空白**になる。

### ③ 撤去した gap猫実装（`51008ee`）

| 区分 | 内容 |
|---|---|
| **定数（8つ）** | `_GAP_NEKO_SLUMP_STORES` / `_GAP_NEKO_PATH` / `_GAP_NEKO_CACHE` / `_GAP_NEKO_FEATHER` / `_GAP_NEKO_BASE` / `_GAP_NEKO_CAT` / `_GAP_NEKO_K` / `_GAP_NEKO_SHRINK` |
| **helper（2つ）** | `_gap_neko_soften()` / `_gap_neko_img()` |
| **引数（2つ）** | `_attach_slump_to_table(..., gap_neko_img=None)` / `_attach_slump_to_table_side(..., gap_neko_img=None)` |
| **分岐** | `_fill = gap_screen_img if gap_screen_img is not None else gap_neko_img` の**フォールバック**と RGBAマスク貼り |
| **呼び出し（8箇所）** | `gap_neko_img=_gap_neko_img(store)`（`show_auto_page` 6箇所 ／ `_composite_slump_onto_images` 2箇所） |

**残存参照は `gap_neko` 0件 ／ `_GAP_NEKO` 0件**（撤去前はそれぞれ21件・22件）。

### ④ アセットは残置（削除しない）

**`assets/slump/neko_gap_1.png` は削除していない。**
コードからは参照しなくなるが、**ファイル自体は残置する。**

### ⑤ ★右下猫は別仕様（絶対に触らない）

**スランプカード内部右下の猫は、今回撤去した gap猫とは完全に別物**である。
以下は**正式仕様として維持**し、**消さない**：

```
assets/slump/neko_5000_1.bmp
_SL_NEKO_K = 0.198
_slump_neko_alpha()
_SL_NEKO_PATH / _SL_NEKO_BOX / _SL_NEKO_REF / _SL_NEKO_BASE / _SL_NEKO_CAT / _SL_NEKO_LINE
```

`draw_slump_graph()` の出力が**画素完全一致（388×472）**であることを確認済み。

> 補足：`neko_5000_1.bmp` の文字列出現数は 5 → 3 になったが、**減った2件は撤去した
> gap猫ブロック内のコメント**（「右下猫とは別物」と説明していた行）であり、
> **右下猫の実体は無傷**。猫導入前と**同数の3件**に一致することを確認済み。

### ⑥ 実画面確認（2026-09-15・ローカル・正式HEAD `51008ee`）

**稲毛 → スランプ付き結果ポスト用 → 確定データ → 2026-09-14**

- slotterguild.com から **196台**を取得（`／ 取得元: slotterguild.com`）
- **⑦プレビュー 6枚生成**
- **`その他の優秀台ピックアップ.jpg`（19台・COLS=3 → rows=7 → 空き2コマ）の最終行が完全に空白**
- 拡大確認：**`#FFFFCB` のクリーム背景のみ・gap猫なし・液晶なし・残像なし**
- **スランプカード内部の右下猫は従来どおり残存**（各カードに薄く表示）
- 2台構成の画像（かのかり / ヴァルヴレイヴ2 / 真打吉宗_高配分）は空き1コマで従来どおり空白

### ⑦ テスト結果（静的58 ＋ 実画像40 ＝ 98件・実質 FAIL 0）

| ケース | 結果 |
|---|---|
| 縦版 空き2コマ（n=4 / n=7） | **猫なし**（旧と差分119,753px＝猫が消えた・**サイズ不変**） |
| side版 空き2コマ（n=18） | **猫なし**（差分66,351px・サイズ不変 6618×1806） |
| side版 空き3コマ（n=17） | **猫なし**（差分66,351px・サイズ不変） |
| 空き0/1コマ（縦 n=6/n=5・side n=16/n=19） | **旧と画素完全一致（差分0px）** |
| 液晶画像を渡した場合（縦版・side版） | **旧と完全一致**＝液晶経路は壊れていない |
| 合成2関数の AST | **猫導入前（`79b3126^`）と完全一致** |

### ⑧ 非回帰（すべて確認済み）

| 対象 | 結果 |
|---|---|
| **他店舗** | 新小岩 / 上野新館 / 上野本館 / 秋葉原 / 新宿歌舞伎町 / 西武新宿 / 高田馬場 / 渋谷新館 の8店舗で**画素完全一致**（元々猫なし）。秋葉原タイトル型 `_build_slump_title_img`（n=4/7/17）も**完全一致** |
| **記事用** | `show_auto_article_page` **AST一致**。`hq_scale=1.0 / 2.0` の両経路で**画素完全一致**。`_ARTICLE_GAP_FILL_STORES` 不変。**記事用液晶仕様は別仕様として維持** |
| ローテ / 結果テキスト / 表デザイン / スランプカード本体デザイン / 保存復元 / JSON / Pision取得 / slotterguild取得 / WordPress / side画像24px余白仕様 | **すべて非変更**（`show_rote_page` / `generate_report_text` / `draw_table_image` / `_paste_slump_area_bg` / `run_auto_pipeline` / `_save_auto_inputs` / `_restore_auto_inputs` / `_sg_fetch_excel` / `_sg_fetch_items` / `fetch_pision_results` / `fetch_pision_realtime` / `normalize_df` / `apply_name_conversion` / `_build_sue_images` / `_apply_panel_to_table_img` が AST 一致） |

**変更関数は `_attach_slump_to_table` / `_attach_slump_to_table_side` / `show_auto_page` /
`_composite_slump_onto_images` の4つだけ。新規関数0・消失関数は gap猫の2つだけ。**

### ⑨ 過去の gap猫 commit（履歴として残す）

gap猫は以下で段階的に追加されていた。**過去履歴は削除・書き換えしない。**

| commit | 内容 |
|---|---|
| `79b3126` | feat: 稲毛スランプ空き枠に透過猫画像を追加 |
| `e5ed040` | fix: 稲毛の空き枠猫をクリーム背景へなじませる |
| `cb27bc7` | fix: 稲毛の空き枠猫を背景減光方式へ変更 |
| `8d03d24` | fix: 稲毛の空き枠猫の表示サイズを縮小 |
| **`51008ee`** | **fix: 稲毛スランプ空き枠の猫表示を撤去（今回）** |

### ⑩ ★これは既存正式仕様の巻き戻しではない

調査の結果、**gap猫は CLAUDE.md にも MEMORY にも正式仕様化されていなかった**
（実測：CLAUDE.md 0件 / MEMORY 0件）。
そのため今回の撤去は**既存正式仕様の巻き戻しに該当しない**。

**今回初めて**「稲毛のスランプ付き結果ポストの空き部分は
**猫なし・液晶なし・空白**」を**正式仕様として記録**する。

### ⑪ 今後の禁止事項

1. **稲毛のスランプ空き枠へ gap猫を再導入しない**
2. **空き2コマ・3コマへ何かを自動で入れる実装を復活させない**（猫・別画像を問わず）
3. **`_GAP_NEKO_*` 定数・`_gap_neko_soften()` / `_gap_neko_img()` を復活させない**
4. **`gap_neko_img` 引数・`gap_screen_img` が None のときのフォールバック分岐を復活させない**
5. **`assets/slump/neko_gap_1.png` を削除しない**（参照0でも残置）
6. **右下猫（`neko_5000_1.bmp` / `_SL_NEKO_K = 0.198` / `_slump_neko_alpha()` / `_SL_NEKO_*`）を
   今回を理由に変更・削除しない**
7. **液晶を結果ポスト用途で復活させない**
   （2026-09-11 の `ebe881e` / `6fd3991` 正式仕様を維持）
8. **`_GAP_FILL_STORES` / `_GAP_FILL_OFF_SLUMP_STORES` / `_gap_fill_on()` を変更しない**
9. **液晶システム（`_gap_fillable` / `_gap_sel_key` / `_gap_screen_paths_for_bans` /
   `_featured_machine_for_bans` / `_resolve_gap_screen` / `_on_gap_screen_change` /
   `_fit_center_in_box` / `_GAP_SCREEN_SHRINK`）を削除しない**
10. **記事用（`show_auto_article_page` / `_ARTICLE_GAP_FILL_STORES`）を変更しない**
11. **空き部分の背景 `#FFFFCB` を変更しない／空きを詰めない**
12. **他店舗へ横展開しない**（今回の見た目変更対象は稲毛の gap猫のみ）
13. **過去の gap猫 commit（`79b3126` / `e5ed040` / `cb27bc7` / `8d03d24`）を reset・revert しない**
14. **正式実装基準は `51008ee`**（この hash へ reset する意味ではない）
15. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新小岩 スランプ付き結果ポスト：slotterguild 確定データ取得対応（2026-09-15・`a1d47e9`）

**正式仕様。巻き戻し禁止。**対象は**【新小岩】スランプ付き結果ポスト用ページの
「📈 日付からデータを自動取得」の確定データモードだけ**。
正式実装 commit は **`a1d47e9c0b0ffdaca14b4fcc361d6d7f761408ea`**
（`feat: 新小岩にslotterguild取得を追加`・**`streamlit_app.py` の1ファイルのみ**・**+2 / −2**・1ハンク）。
**ローカル実機確認 → push → ユーザーによる Cloud 実機確認まで完了し「問題なし」と承認済み。**

既存の CLAUDE.md 各節は**削除・圧縮・統合・並べ替え・書き換えしない**。
本節は**2026-09-15 の正式仕様として末尾へ追加**するものである。

### ① SG対象店舗は現在3店舗

| 店舗 | 実装 commit | CLAUDE.md 記録 |
|---|---|---|
| **稲毛** | **`a51e3628f147ccfccfba9f0ce387cfe7c2b9363f`**（`feat: 稲毛にslotterguildデータ取得を追加`） | 「## 【正式仕様】稲毛 スランプ付き結果ポスト：Pision / slotterguild 2系統データ取得（2026-09-15・`a51e362`）」 |
| **上野新館** | **`76c34b0`**（`feat: 上野新館にslotterguild取得を追加`） | **★未記録**（下記④参照） |
| **新小岩** | **`a1d47e9`**（本節） | **本節** |

```python
_SG_FETCH_STORES: "frozenset[str]" = frozenset({"稲毛", "上野新館", "新小岩"})
_SG_HALL_IDS: "dict[str, int]" = {"稲毛": 566, "上野新館": 570, "新小岩": 573}
```

### ② ★稲毛節に書かれた集合は「その commit 時点の状態」（誤読しないこと）

稲毛節（`a51e362`）には

```python
_SG_FETCH_STORES = frozenset({"稲毛"})
_SG_HALL_IDS = {"稲毛": 566}
```

と記録されているが、これは **`a51e362` 時点の正式な状態**である。
その後 **`76c34b0`（上野新館）→ `a1d47e9`（新小岩）** により集合が拡張された。

**稲毛節の当該記述は当時の記録として正しいので、削除・書き換えしない。**
**現在の正式な集合は本節①の3店舗である。**

### ③ 実装は定数2行のみ（helper・UI・処理は新規追加なし）

`a1d47e9` の差分は **`_SG_FETCH_STORES` と `_SG_HALL_IDS` の2行だけ**。

- **新規helper 0 / 新規関数 0 / 消失関数 0。**
- **`_sg_hall_id()` / `_sg_get()` / `_sg_fetch_excel()` / `_sg_cell_int()` / `_sg_fetch_items()`
  は本体 AST 完全一致で再利用**（`show_auto_page` / `show_auto_article_page` / `show_rote_page` /
  `normalize_df` / `apply_name_conversion` / Pision API 関数群 / `draw_slump_graph` /
  `_slump_apply_names` / `run_auto_pipeline` / `generate_report_text` /
  `_composite_slump_onto_images` / `_attach_slump_to_table(_side)` / `_save_auto_inputs` /
  `_restore_auto_inputs` / `_merge_auto_entry` / `draw_table_image` / `_build_sue_images`
  ほか計26関数も AST 一致を機械確認済み）。
- **`_SG_BASE_URL` / `_SG_TIMEOUT = 20` / `_SGError` / 正規表現4種も不変。**

**店舗追加は「この2定数への追記だけ」で行う。店舗別のコード分岐を新設しない。**

### ④ ★上野新館（`76c34b0`）は CLAUDE.md に未記録（事実として記録する）

調査の結果、**上野新館の slotterguild 対応は CLAUDE.md に節が存在しない**
（slotterguild × 上野新館 の検索ヒット0件）。

**本節はその事実を記録するだけで、上野新館の節を代筆・捏造しない。**
上野新館の正式仕様化が必要であれば、**別途ユーザーの指示で行う**。
なお **`_SG_FETCH_STORES` / `_SG_HALL_IDS` に上野新館（570）が入っていること自体は
現行コードの事実**であり、本節①の表がその現状である。

### ⑤ 対象とモード

| 項目 | 値 |
|---|---|
| 店舗 | **新小岩のみ**（本節の対象） |
| ページ | **スランプ付き結果ポスト用**（`show_auto_page(with_slump=True)`） |
| モード | **確定データのみ** |

### ⑥ UI（確定データ時だけ横2列）

```
### 📈 日付からデータを自動取得（新小岩）
データ種別: (●) 確定データ  ( ) 速報データ（当日・営業中）   ← 既存のまま
日付を選択: [2026/09/14]                                    ← 既存widget 1つを共用
┌──────────────────────┬──────────────────────┐
│ 🔄 Pisionから取得    │ 🌐 サイトから取得    │
└──────────────────────┴──────────────────────┘
✅ 2026-09-14 の確定データ（484台）を取得し、①にセットしました。／ 取得元: slotterguild.com
```

- **日付widgetは既存の1つだけ。左右それぞれに日付widgetを作らない。**
- 左の Pision ボタンは **既存 key `auto_tb_refetch_{store}` を維持**する。
- 右は **`auto_tb_sg_{store}`**。

### ⑦ ★通常結果ポスト用には出さない（正式仕様）

**新小岩の「⚡ 結果ポスト用」（`with_slump=False`）には
「🌐 サイトから取得」を表示しない。**従来どおり単一の「🔄 取得」のまま。

### ⑧ ゲート（店舗名だけで出さない）

既存の正式ゲートをそのまま使用する。**変更しない。**

```python
elif (with_slump and store in _SG_FETCH_STORES
      and _sg_hall_id(store) is not None):
```

### ⑨ 速報モードは変更しない

**slotterguild は確定データのみ。速報モードへは一切手を入れていない。**
`⚡ 速報を取得` / `📂 既存のデータを取得` / 収集中UI（`⏳ 収集中...` / `🔍 今すぐ確認`）/
30秒ポーリング / 既存データ取得の各ブロックは**修正前とバイト一致**を機械確認済み。

### ⑩ ★SG hall_id と Pision hall_id は別体系（混同禁止）

| 系統 | 新小岩の hall_id |
|---|---|
| **slotterguild** | **573** |
| **Pision** | **2** |

（参考：稲毛 SG=566 / Pision=4031 ／ 上野新館 SG=570 / Pision=201）

slotterguild 側は **`_SG_HALL_IDS` の固定値**、Pision 側は従来どおり
`fetch_pision_halls()` の結果から「store名 と エスパス を両方含むホール」を検索して解決する
（**ハードコードしない**）。

### ⑪ 取得先（GETのみ・認証不要）

| 用途 | エンドポイント |
|---|---|
| **表データ** | `halldata_api.php?download_dedama_s_excel&hall_id=573&date_at=YYYY-MM-DD&name_col=name_1` |
| **スランプpoints** | `hall_all.php?hall_id=573&date_at=YYYY-MM-DD` |

Base は **`https://slotterguild.com/hall_data_db/halldata`**。
**`new.php` からは台データを取らない。書き込みAPI（`set_schedule_onetime` 等）は使わない。**

### ⑫ 既存パイプラインへ流す（専用 normalize を作らない）

- xlsx bytes は **`_auto_tb_file_bytes_fix_{store}` 系の既存 session_state** へ。
  ファイル名は **`{YYYYMMDD}_{store}_20S.xlsx`**（例 `20260914_新小岩_20S.xlsx`）。
- その後は **`_read_uploaded_df()` → `normalize_df()` → `apply_name_conversion()`** の既存処理。
  **専用 normalize 層を新設しない。`COLUMN_ALIASES` を変更しない。**
- **CSV経路は使わない**（slotterguild は UTF-8 BOM ／ 既存 `_read_csv_raw` は cp932 固定）。

### ⑬ スランプ items は既存キャッシュへ注入

`hall_all.php` から得た items を
**`_auto_tb_rt_items_{store}` / `_auto_tb_rt_items_date_{store}`** へ保存し、
**既存のスランプ描画経路（cache-first）をそのまま使用**する。
**slotterguild 専用のスランプ生成処理を別実装しない。**

### ⑭ 取得元表示

| session_state | 値 |
|---|---|
| **`_auto_tb_src_{store}`** | **`"Pision"` または `"slotterguild.com"`** |

**session_state のみ。JSON へ永続化しない。**

### ⑮ エラー処理（稲毛・上野新館と同一仕様を維持）

**0台 / HTTP 403 / 404 / 5xx / 非200 / timeout（20秒）/ 接続失敗 /
Content-Type不正 / 非xlsx（PKシグネチャなし）/ HTML構造変化** を
すべて `_SGError`（ユーザー向け文面）にして送出する。**例外を握り潰さない。**

**失敗時に既存の Pision データ・手動アップロードデータ・既存 session_state を上書きしない。**

### ⑯ ★半端更新禁止（既存仕様を維持）

```
xlsx取得 → 行数>0 → items取得 → 件数>0 → 台番集合一致
  ↓ すべて成功したときだけ
session_state を更新 → st.rerun()
```

**`try` ブロック内に `st.session_state[...]` の書き込みを置かない。**
**表だけ使うフォールバックを作らない。**

### ⑰ 2026-09-14 新小岩の実測（正式確認値）

| 項目 | 値 |
|---|---|
| SG hall_id | **573** |
| 取得台数 | **484台** |
| xlsx行数 | **484** |
| hall_all 台数 | **484** |
| items件数 | **484** |
| points | **484 / 484** |
| points欠損 | **0** |
| 台番集合 | **完全一致** |
| normalize missing | **`[]`** |

### ⑱ Pision比較（2026-09-14）

| 項目 | 結果 |
|---|---|
| Pision台数 / SG台数 | **484 / 484** |
| 台番集合 | **完全一致** |
| 差枚 / G数 / BB / RB / ART・AT | **すべて不一致 0** |
| 機種名変換後 | **不一致 0** |

**表データは Pision と完全一致。**

### ⑲ SG内部不整合（Δ = SG表差枚 − SG points終点y）

| 指標 | 値 |
|---|---|
| 総台数 | 484 |
| 一致 | 476 |
| **不一致** | **8台** |
| **不一致率** | **1.65%** |
| 差 | **8台すべて +100枚** |
| **最大絶対差** | **100枚** |
| **絶対差 500枚超** | **0台** |
| **絶対差 1000枚超** | **0台** |

**この程度は画像用途として許容し、正式採用する。**

不整合8台（参考記録）：

```
台  216 この素晴らしい世界に祝福   Δ +100
台  269 沖ドキ!BLACK            Δ +100
台  285 沖ドキ!ゴージャス-30      Δ +100
台  295 沖ドキ!BLACK            Δ +100
台  297 沖ドキ!BLACK            Δ +100
台  299 沖ドキ!BLACK            Δ +100
台 2227 L北斗 転生の章2          Δ +100
台 2288 L東京喰種               Δ +100
```

**★表示される差枚は「表の値」（＝Pisionと一致する正しい値）であり、
points終点の値ではない。**したがって Δ=100 は表示数値に影響しない
（例：台2288 は表 +9,400枚／points終点 +9,300枚 → スランプカードの表示は **+9,400枚**）。

### ⑳ ローカル実機確認（2026-09-15）

新小岩 → スランプ付き結果ポスト用 → 確定データ → 2026-09-14 → 🌐 サイトから取得

- **484台取得** ／ 表示 **`取得元: slotterguild.com`**
- **⑦プレビュー 14枚 正常生成**
- 表（紫テーマ）正常 ／ スランプ（白＋淡紫＋猫・388×472）正常
- **不整合8台（269 / 295 / 297 等）も 異常線・極端な終点ズレ・描画崩れなし**

テストは **合計 90件 PASS / 0 FAIL**
（ゲート66件＝指定9テスト＋全13店舗×2ページ網羅＋helper 26関数AST＋diff検証＋速報非回帰／
データ・描画24件）。

### ㉑ Cloud実機確認

**ユーザーが Cloud で確認済み・「問題なし」。これをもって正式採用条件成立とする。**

### ㉒ UI確認結果（実ブラウザ・2026-09-15）

| 店舗 | `auto_slump` | `auto`（通常） |
|---|---|---|
| **稲毛** | **🌐 サイトから取得 あり** | **なし** |
| **上野新館** | **あり** | **なし** |
| **新小岩** | **あり** | **なし** |
| 新宿歌舞伎町 | **なし**（`auto_slump` / `auto_slump2` とも） | なし |
| 上野本館 | **なし** | なし |
| 秋葉原 | **なし** | なし |

### ㉓ 非対象店舗（今回 `_SG_FETCH_STORES` に追加しない）

**新宿歌舞伎町 ／ 上野本館 ／ 秋葉原。**

2026-09-14 の SG内部不整合 実測（参考）：

| 店舗 | 不一致 | 最大絶対差 | 500枚超 | 1000枚超 | 判断 |
|---|---|---|---|---|---|
| **新宿歌舞伎町** | **662 / 749台（88.38%）** | **5,700枚** | **312台** | **143台** | **SG points 採用不可** |
| 上野本館 | 95 / 375台（25.33%） | 400枚 | 0 | 0 | **保留** |
| 秋葉原 | 145 / 522台（27.78%） | 500枚 | 0 | 0 | **保留** |

**新宿歌舞伎町は現状 SG points の採用不可。**上野本館・秋葉原は**現時点では保留**とし、
今回の正式対象に含めない。

**参考（2026-09-14 の追加検証）**：Pision 側は全5店舗・全2,507台で
**「points終点 == 表差枚」が100%成立**しており、乖離しているのは **SG 側の points** である。
SG の `hall_all.php` ミニグラフは最終x が G数と一致せず（新宿歌舞伎町では一致2/749）、
**途中打ち切り／別スケールの系列**と判断できる。

### ㉔ 機種名変換

**新小岩 2026-09-14 では機種名変換後の Pision との差 0件。**
したがって **今回の新小岩追加に伴う `機種名変換.xlsx` の変更はなし。**

### ㉕ 非変更（今回いっさい触れていない）

稲毛SG取得 ／ 上野新館SG取得 ／ 速報取得 ／ 通常結果ポスト用 ／ 記事用 ／ ローテ ／
結果テキスト ／ 表デザイン ／ スランプグラフデザイン ／ 液晶 ／ gap猫 ／ 保存復元 ／
JSON構造 ／ WordPress ／ `requirements.txt` ／ Secrets ／ `機種名変換.xlsx`。

`_SLUMP_THEME_STORES` / `_GAP_FILL_OFF_SLUMP_STORES` / `_gap_fill_on("新小岩") == False` /
`_KOJIN_DATE_SCOPED_STORES` も不変。

### ㉖ Git履歴の注意（誤認しないこと）

```
c61149c  auto: 画像生成後の設定を保存        ← アプリの _git_auto_push() による自動commit
a1d47e9  feat: 新小岩にslotterguild取得を追加  ← ★本節の正式実装commit
fe5ac39  update: 機種名変換マスタを更新        ← 機種名変換の自動同期による自動commit
76c34b0  feat: 上野新館にslotterguild取得を追加
```

- **`fe5ac39` / `c61149c` はアプリ由来の自動commit**であり、手作業のコード変更ではない。
  **いずれも有効な履歴として扱う。reset / revert しない。**
- **`c61149c` は `auto_page_inputs.json` のみの変更**で、
  **`streamlit_app.py` は `a1d47e9` から不変**（`git diff --quiet a1d47e9 HEAD -- streamlit_app.py` で確認）。
- **正式実装基準は `a1d47e9`**（この hash へ reset する意味ではない）。

### ㉗ 今後の禁止事項

1. **新小岩の通常結果ポスト用（`with_slump=False`）へ「🌐 サイトから取得」を出さない**
2. **ゲートを店舗名だけの判定に変えない**
   （`with_slump and store in _SG_FETCH_STORES and _sg_hall_id(store) is not None` を維持）
3. **速報モードの UI・処理を変更しない**（slotterguild は確定データのみ）
4. **日付widget を左右で分けない**（既存1つを共用する）
5. **Pision ボタンの key `auto_tb_refetch_{store}` を変えない**
6. **`_SG_FETCH_STORES` / `_SG_HALL_IDS` を承認なしに他店舗へ広げない**
   （とくに**新宿歌舞伎町は追加しない**）
7. **SG hall_id 573 と Pision hall_id 2 を混同しない**
8. **稲毛節の `frozenset({"稲毛"})` を「現在の集合」と誤読しない**（本節①が現行）
9. **上野新館の節を代筆・捏造しない**（未記録であることが事実）
10. **専用 normalize 層を新設しない／`COLUMN_ALIASES` を変更しない**
11. **CSV経路を使わない**（`_read_csv_raw` は cp932 固定）
12. **新しい保存キー・新しいJSONを作らない**（既存 `_auto_tb_file_bytes_fix_*` 系を流用）
13. **slotterguild 専用のスランプ生成処理を別実装しない**（既存 cache-first 経路を使う）
14. **`_auto_tb_src_{store}` を JSON へ保存しない**
15. **例外を握り潰さない**／`requests.get` の timeout を外さない
16. **半端更新をしない**（全検証成功後にのみ session_state を更新する）
17. **表だけ使うフォールバックを作らない**
18. **失敗時に既存 Pision データ・手動アップロードデータを上書きしない**
19. **`new.php` から台データを取らない／書き込みAPIを使わない**
20. **㉕の非変更リストを今回を理由に変更しない**
21. **本節を「Pision 完全非依存化」と誤記しない**（取得元を選べるようにしただけ）
22. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：並び・列のban_map再計算とWordPress狭幅画像の分割（2026-09-16・`77e140d`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】の記事用ページ（`auto_article`）だけ**。
2026-09-16 に **ユーザーが Streamlit Cloud 実機で確認し「問題ありませんでした」と正式承認**した。

既存の記事用・WordPress関連セクション（`73db0ba` / `d121e54` / `148d672` / `bd9fa40` /
`3432a97` / `c31b860`（渋谷新館 全画像nosplit）/ 2026-09-05 の fullwidth A-2a /
2026-09-09 の 33%幅・左詰め ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。
本節は**2026-09-16 の正式仕様として末尾へ追加**するものである。

### A. 正式実装commit

| | commit |
|---|---|
| **正式** | **`77e140ddde83822f0fe54510dd8684a7bc9b86c0`**（`fix: 新宿歌舞伎町の記事用画像出力を修正`） |

**`streamlit_app.py` と `wp_client.py` の2ファイルのみ・+108 / −31。**
**変更関数は `show_auto_article_page()` と `wp_client.plan_split()` の2つだけ。**
**新規関数は `_art_narabi_items()` と `wp_client.wp_saved_width()` の2つだけ・消失関数0。**

**`77e140d` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。
`77e140d` へ reset してはならない。**

なお `77e140d` の直後の **`e1ad706`（`auto: 画像生成後の設定を保存`）は
`article_page_inputs.json` だけのアプリ自動commit**であり、コード変更ではない。
**有効履歴として維持し、reset / revert しない**（`streamlit_app.py` / `wp_client.py` は
`77e140d` から差分0）。

---

## 不具合1：⑧本番の並び・列画像にパネル・スランプが付かない

### B. 原因（⑦プレビューの session_state スナップショット依存）

**⑧本番の並び・列画像だけ**が、ban_map を
**`art_preview_narabi_{store}` / `art_preview_col_{store}`**
（＝⑦プレビューが残した session_state のスナップショット）から作っていた。

他カテゴリ（全台系・高配分・②個別・⑤オススメ・ジャグラー統合・その他優秀台・
④末尾・バラエティ）は**すべて⑧内で ban_map を再計算**しており、
**並び・列だけが⑦依存**という非対称だった。

そのため次のいずれかで ban_map が空になり、⑧の合成ループが
`if not _bans_sl: continue` でスキップ → **並び・列画像が「表のみ」のまま保存**されていた。

```
・⑦を一度も押さずに⑧を実行
・⑦の後に並び台番範囲を変更して⑧を実行
・「🔄 プレビューをクリア」後に⑧を実行
・Excel（日付）を切り替えて⑧を実行
・Cloud再起動・ブラウザ再接続などでセッションが変わった後に⑧を実行
```

**WordPress 側の不具合ではない。**完成データ（ローカル出力）の時点で既にパネル・スランプが
無く、WordPress はその正しくない完成画像をそのままアップロードしていただけである。
**この切り分けを今後も誤認しない。**

### C. 正式ゲート `_ART_NARABI_BANMAP_STORES`

```python
# 記事用⑧で並び・列の ban_map を⑦プレビューの session_state スナップショットに
# 頼らず、現在の入力値から再計算する店舗。
_ART_NARABI_BANMAP_STORES: "frozenset[str]" = frozenset({
    "新宿歌舞伎町",
})
```

**対象は新宿歌舞伎町だけ。**
**高田馬場・渋谷新館・秋葉原は従来経路のままで対象外**（同じ潜在バグがあっても今回は修正しない）。
店舗を増やす／戻すときは**この集合の編集だけ**で行う。

### D. 共通helper `_art_narabi_items(df, ranges)`

```python
def _art_narabi_items(df, ranges) -> list[tuple]:
    """記事用の並び画像の生成対象を
    (DataFrame, 機種名リスト, タイトル, ファイル名, 掲載台番リスト) で返す。"""
```

- **副作用なし**（`df` / `ranges` を変更しない・session_state を触らない）。
- **抽出条件 ／ 台番順 ／ 同名タイトル時の `（開始～終了）` 表記**は従来の⑦と同一規則。
- **⑦プレビューと⑧本番がこの1本を共用する**ので、ファイル名と掲載台番が構造的にズレない。
- 列は既存 **`_build_col_items(df, ranges)`** をそのまま再利用する（**列専用helperを新設しない**）。

**★helper化によって⑦の出力を変えてはならない。**
同じ入力なら **⑦のファイル名・タイトル・機種名リスト・サマリー（総差枚/平均/勝率/台数）・
DataFrame の内容が修正前と完全一致**すること（純粋テストで機械確認済み）。

### E. ⑦プレビュー

インラインの `_anbm` / `_antit` / `_anbinfos` / 重複タイトル判定を廃止し、
**`_art_narabi_items()` の戻り値を回すだけ**にした。
**サマリー計算・`_build_machine_img(..., no_bar=True, hq_scale=_art_narabi_hq(store))` の
呼び出しは不変。**

### F. ⑧本番（正式）

```python
if store in _ART_NARABI_BANMAP_STORES:
    _art_df_nb_sl = result.get("df")
    if narabi_ok and narabi_ranges and _art_df_nb_sl is not None:
        for _nbi_sl in _art_narabi_items(_art_df_nb_sl, narabi_ranges):
            _art_bm_sl[_nbi_sl[3]] = _nbi_sl[4]
    # 列画像（列仕掛け）
    if retsu_ok and retsu_ranges and _art_df_nb_sl is not None:
        for _cbi_sl in _build_col_items(_art_df_nb_sl, retsu_ranges):
            _art_bm_sl[_cbi_sl[2]] = _cbi_sl[3]
else:
    （従来の art_preview_narabi_{store} / art_preview_col_{store} 経路）
```

- 参照するのは **⑧実行時の現在入力値（`narabi_ranges` / `retsu_ranges`）と `result["df"]`** だけ。
  **`result["df"]` は `_pipeline_calc_d` 適用後の補正済み差枚**なので、⑦の `_apdf` と同じ基準。
  **差枚を再補正しない（二重補正の禁止）。**
- これにより **⑦を押さずに⑧だけ実行しても**、並び・列画像へ正しい掲載台番が渡り、
  **完成画像・WordPress掲載画像でもプレビューと同じパネル・スランプ合成**が行われる。

### G. ★`art_preview_narabi_{store}` の別参照は据え置き（誤解しないこと）

`show_auto_article_page()` には、上記の else 分岐とは**別に**
`_arnbm = st.session_state.get(f"art_preview_narabi_{store}", {})` を読む箇所がある。

これは **「⑦でチェックを外した並び画像の +1,000枚台を『その他の優秀台』へ再振り分けする」
別機能**であり、**ban_map とは無関係**。今回は最小修正のため**意図的に据え置いた**。
**この箇所を「修正漏れ」と誤認して勝手に書き換えてはならない。**

### H. パネル・スランプ処理は既存のまま

並び・列画像のパネルは**他の記事用画像と同じ既存処理**を使う。
**並び・列専用のパネル処理・スランプ処理を新設していない。**

`_apply_panel_to_table_img()`（`narabi_like=_art_is_narabi_fn(bare)` /
`max_panels=_art_panel_max(store, bare)`）／`_build_panel_row()` ／
`_narabi_panel_names()` ／`draw_slump_graph()` ／`_attach_slump_to_table()` は
**いずれも本体無変更（AST一致）**。

---

## 不具合2：WordPress上のマイジャグV画像だけ粗い

### I. 原因（縦長かつ狭幅の画像が1枚で保存され、記事表示幅で拡大された）

ローカルの `マイジャグV_高配分.jpg` は **1982 × 11480px**（縦横比 5.79・記事内で最大）で
**画質に問題はなかった**（HQ 2倍・q95・5.24MB）。

新宿歌舞伎町は **`_ART_WP_NOSPLIT_STORES` 対象**のため1枚のまま送信され、
WordPress が**長辺2560px**へ縮小する際に**幅が442pxまで巻き添えで潰れた**。

```
1982 × 11480  →（長辺2560へ縮小）→  442 × 2560 で保存
→ fullwidth（本文カラム内幅 752px）で 1.70倍に「拡大」表示 → 荒く見える
```

**画像生成側・JPEG品質・リサイズ処理・srcset・別経路の縮小はいずれも原因ではない。**
**ローカル保存時点では粗くなく、WordPressアップロード後に粗くなる**という切り分けを維持する。

### J. 正式ゲートと定数

```python
_ART_WP_SPLIT_NARROW_STORES: "frozenset[str]" = frozenset({"新宿歌舞伎町"})
# SWELL 本文カラム内幅（2026-09-05 実測 752px）
_ART_WP_MIN_KEEP_W = 752


def wp_saved_width(w: int, h: int, max_side: int = WP_MAX_SIDE) -> int:
    """WordPress が長辺 max_side へ縮小して保存したあとの想定幅を返す（副作用なし）。"""
```

**対象は新宿歌舞伎町だけ。他店舗へ追加しない。**
**★`_ART_WP_NOSPLIT_STORES`（店舗単位で分割しない）／`WP_NOSPLIT_FILES`（島図を全店舗で1枚絵）／
`_ART_WP_SPLIT_ALLOW_FILES`（ファイル名単位の例外）とは**すべて別仕様**。統合しない。**

### K. `plan_split()` の正式仕様（判定順に意味がある）

**nosplit 判定より前に実画像サイズを確認する。**

```python
_nosplit_store = store in _ART_WP_NOSPLIT_STORES
_narrow_store = store in _ART_WP_SPLIT_NARROW_STORES
for f in found:
    if f["file"] in WP_NOSPLIT_FILES:      # 島図など：needs_split すら呼ばない
        continue
    try:
        with Image.open(f["path"]) as im:  # ★ nosplit 判定より前にサイズを見る
            w, h = im.size
    except Exception:
        continue
    if not needs_split(w, h):              # 既存条件を必ず満たすことが前提
        continue
    if (_nosplit_store
            and f["file"] not in _ART_WP_SPLIT_ALLOW_FILES
            and not (_narrow_store
                     and wp_saved_width(w, h) < _ART_WP_MIN_KEEP_W)):
        continue
    parts = split_image_for_wp(f["path"], tmp_dir)
```

判定は **`needs_split(w, h)` を満たし、かつ `wp_saved_width(w, h) < 752`** のときだけ、
**nosplit 対象でも分割を許可**する。

**★機種名・ファイル名による特例にしない。**掲載機種は日によって変わるため、
**サイズだけで判定する**。`_ART_WP_SPLIT_ALLOW_FILES` へ機種名を足す方式は採らない。

**★この判定順（サイズ確認 → `needs_split` → nosplit 判定）を入れ替えない。**
元の順序（nosplit で先に `continue`）に戻すと幅を判定できず、この仕様が成立しない。
なお `Image.open` / `needs_split()` は副作用のない読み取りなので、
**対象外店舗の `plan_split()` 結果は順序変更後も完全に同一**である。

### L. 実データでの結果（2026-09-15 新宿歌舞伎町・749台）

| 画像 | 元サイズ | 旧WP保存 | 新WP保存 | 判定 |
|---|---|---|---|---|
| **マイジャグV_高配分.jpg** | **1982×11480** | **442×2560（1枚・1.70倍拡大）** | **1982×2256 / 2296 / 2336 / 2296 / 2296（5分割）** | **★分割対象になる** |
| ファンキー2_高配分.jpg | — | 826×2560 | 826×2560 | 現状維持（分割しない） |
| ゴージャグ3_高配分.jpg | — | 838×2560 | 838×2560 | 現状維持 |
| ジャグラーシリーズ優秀台.jpg | — | — | 1760×2560 | 現状維持 |
| 差枚数ランキング.jpg | — | 1204×2560 | 1204×2560 | 現状維持 |
| 全台データ.jpg | 748×298 | 748×298 | 748×298 | 現状維持（`needs_split=False`・752px枠で1.005倍＝実質等倍） |
| その他の優秀台ピックアップ.jpg | — | 10片 | 10片 | **既存例外分割（`_ART_WP_SPLIT_ALLOW_FILES`）を維持** |

**挙動が変わるのは `マイジャグV_高配分.jpg` の1枚だけ。**
5分割後は**各片の幅1982pxを維持**し、752px枠では**0.38倍の縮小表示**になるため粗さが解消する。
分割片の高さ合計は元画像の高さと一致（リサイズなし・crop のみ）。

### M. 既存WP仕様は維持

**`needs_split()` / `split_count()` / `split_image_for_wp()` / `WP_MAX_SIDE`(2560) /
`WP_SPLIT_MAX_H` / `_ART_WP_NOSPLIT_STORES` / `_ART_WP_FULLWIDTH_STORES` /
`_ART_WP_SPLIT_ALLOW_FILES` / `WP_NOSPLIT_FILES` / `WP_THIRD_WIDTH_FILES`（全台データの33%幅）/
`build_content()` / `collect_files()` / `blk_image()` / `build_payload()` / `plan_blocks()` は
いずれも本体無変更（AST一致）。**

fullwidth A-2a（`"width":"100%"` ＋ `wp-block-image size-full is-resized` ＋
`style="width:100%;height:auto"`）／`linkDestination":"none"`（Luminous）／
全台データの33%幅・左詰め（`has-text-align-left`）も**分割片を含めて維持**される。

### N. 他店舗の非回帰（実測）

| 店舗 | 結果 |
|---|---|
| **高田馬場** | `plan_blocks` **完全一致** ／ 本文HTML **完全一致** ／ `plan_split` 13件一致 |
| **渋谷新館** | `plan_blocks` **完全一致** ／ 本文HTML **完全一致** ／ `plan_split` 1件一致 |
| **秋葉原** | `plan_split` 13件一致（**今回対象外**） |
| **稲毛** | `plan_split` 13件一致 |
| **`store=""`（既定）** | `plan_split` 13件一致 |

---

## O. 検証結果

**純粋テスト 146 PASS / 0 FAIL。**

⑦のファイル名・台番・タイトル・機種名リスト・サマリー・DataFrame が**修正前と完全一致** ／
⑦ファイル名＝⑧実ファイル7件と完全一致 ／ **session_state が空でも並び7件の ban_map を再計算** ／
列も現在入力から生成可 ／ 再現条件5種すべてで ban_map 生成 ／ 並び7枚のパネル＋スランプ合成 ／
`wp_saved_width(1982, 11480) == 441` ／ **新たに分割対象になったのは1件だけ**（マイジャグV）／
既存分割が消えない ／ 5分割・各片幅1982px・高さ合計一致 ／ 非対象5画像の現状維持 ／
他店舗5パターンの `plan_split` 一致 ／ 高田馬場・渋谷新館の `plan_blocks` と本文HTML md5 一致 ／
AST 非回帰（変更関数2・新規関数2・消失0）。

**非回帰（すべてPASS）**：かぶぱ（`_is_kabupa_page` / `_build_kabupa_result_text`）／
`auto_slump2`（`_kojin_ns`）／ローテ（`show_rote_page` / `generate_rote_image`）／
Pision（`fetch_pision_results`）／slotterguild（`_sg_fetch_excel` / `_sg_fetch_items`）／
記事用液晶（`_art_gap_fill_on`：新宿歌舞伎町=False・高田馬場/渋谷新館=True）／
島図なし（`_ARTICLE_SHIMAZU_STORES` 不変）／10日区切り（9/15 → `🏆9月11日～9月20日🏆` ＋ `5日目`）／
記事用パネル（`_ARTICLE_PANEL_STORES` 不変）。

### P. ローカル実機確認（2026-09-15 データ・749台）

`55e7752` の必須手順どおり **アプリ停止 → コードのみ commit → 再起動 → 実機確認**で実施。

**⑦「🔍 プレビュー生成」を一度も押さず、⑧「▶▶ 自動処理を開始」だけを実行**
（実行前のUIに⑦ボタンが表示されている＝プレビュー未生成状態を確認済み）。

| 並び画像 | 修正前 | 修正後 |
|---|---|---|
| SAOII(4台並び).jpg | 1889×**534** | 1889×**2795** |
| カバネリ海門決戦(3台並び).jpg | 2062×**442** | 2062×**2080** |
| ゴージャグ3(4台並び).jpg | 2062×**534** | 2062×**3000** |
| ハピジャグV(3台並び).jpg | 2062×**442** | 2062×**2086** |
| モンキーターンV(3台並び).jpg | 2062×**442** | 2062×**2080** |
| 東京喰種(3台並び)（805～807）.jpg | 2062×**442** | 2062×**2086** |
| 東京喰種(3台並び)（855～857）.jpg | 2062×**442** | 2062×**2086** |

**7/7 でパネル＋スランプ合成済み**（画像を開いて「パネル→表→スランプ」の構成も目視確認）。
`_git_auto_push()` は「変更なし（push不要）」で自動commitなし。

### Q. WordPress下書きでの確認（62868）

| 項目 | 値 |
|---|---|
| post ID | **62868** |
| status / category / author | **`draft` / 7 / 2（m.takahashi）** |
| title | `9月15日(火)│エスパス新宿歌舞伎町│` |
| media | **40枚**（送信対象27枚 → 分割で40） |

- **並び7件すべてがパネル・スランプ付きで掲載**（2062×2080 / 2062×2086 / 1730×2560 / 1760×2560）
- **マイジャグVは5分割・各片幅1982px**（旧下書き62827では 442×2560 の1枚）→ **粗さが解消**
- 62827 との比較：共通media 35件中**差分は並び7枚だけ**、他28件は寸法完全一致
- 752px枠で1.10倍を超えて拡大される media は**0件**
- media URL のリンク切れ **0件**
- fullwidth 3点セット・`linkDestination":"none"`・画像用 `<a href>` 0件を維持
- 10日区切り（`9月11日～9月20日` / `5日目`）・島図なし・差枚数ランキングも維持

**既存下書き 62752 / 62789 / 62827 は未変更**（`created == modified` で一度も更新されていない）。
**PUT / PATCH / DELETE / publish はすべて0件。新規作成は 62868 の1件のみ。公開していない。**

### R. Cloud 承認

**2026-09-16：ユーザーが Streamlit Cloud 実機で確認し「問題ありませんでした」と正式承認。**
よって `77e140d` を正式仕様とする。

### S. 今後の禁止事項

1. **⑧の並び・列 ban_map を `art_preview_narabi_{store}` / `art_preview_col_{store}` 依存へ戻さない**
2. **`_ART_NARABI_BANMAP_STORES` へ高田馬場・渋谷新館・秋葉原を追加しない**（同じ潜在バグがあっても今回は対象外）
3. **`_art_narabi_items()` を⑦／⑧で別実装に分けない**（1本を共用する）
4. **helper化を理由に⑦のファイル名・抽出条件・台番順・`（開始～終了）` 表記・画像内容を変えない**
5. **列専用のhelperを新設しない**（`_build_col_items()` を再利用する）
6. **`result["df"]` の差枚を再補正しない**（`_pipeline_calc_d` の二重適用禁止）
7. **「その他へ再振り分けする別機能」の `_arnbm` 参照を修正漏れと誤認して書き換えない**
8. **並び・列専用のパネル処理・スランプ処理を新設しない**（既存処理を使う）
9. **不具合2の原因を「画像生成側の画質」「WordPressの再圧縮」と誤認しない**（長辺2560px縮小による幅潰れ）
10. **`_ART_WP_SPLIT_NARROW_STORES` を他店舗へ広げない**
11. **`_ART_WP_MIN_KEEP_W = 752` を理由なく変更しない**（SWELL 本文カラム内幅の実測値）
12. **機種名・ファイル名による特例にしない**（`_ART_WP_SPLIT_ALLOW_FILES` へ機種名を足さない）
13. **`plan_split()` の判定順（サイズ確認 → `needs_split` → nosplit 判定）を入れ替えない**
14. **`needs_split()` / `split_count()` / `split_image_for_wp()` / `WP_MAX_SIDE` を変更しない**
15. **`_ART_WP_NOSPLIT_STORES` / `WP_NOSPLIT_FILES` / `_ART_WP_SPLIT_ALLOW_FILES` /
    `_ART_WP_FULLWIDTH_STORES` / `WP_THIRD_WIDTH_FILES` と統合・整理しない**
16. **fullwidth A-2a・Luminous・33%幅左詰め・島図1枚絵などの既存WP仕様を変更しない**
17. **高田馬場・渋谷新館・秋葉原・稲毛・`store=""` の `plan_split()` 結果を変えない**
18. **記事用液晶（新宿歌舞伎町OFF）・島図なし・10日区切り・記事用パネルの既存仕様を変更しない**
19. **かぶぱ（`auto_slump`）／`auto_slump2`／ローテ／Pision／slotterguild へ波及させない**
20. **`77e140d` / `e1ad706` へ reset・revert しない**
21. **既存下書き 62752 / 62789 / 62827 / 62868 を公開・編集・削除しない**
22. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用の書体を Noto Sans JP Black へ統一（2026-09-16・`31f7346`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用画像だけ**。
2026-09-16 に **ユーザーが ローカル・Streamlit Cloud の両方で実機確認し「問題なく Noto Sans JP Black で
生成される」と正式承認**した。

既存の記事用・フォント関連セクション（`47e0372` / `77e140d` / `517535b` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**2026-09-16 の正式仕様として末尾へ追加**する。

### A. 正式実装commit

| | commit | 扱い |
|---|---|---|
| ① | **`137592c`**（`feat: 新宿歌舞伎町記事用の書体を変更`） | **ローカルWindowsのみ HGS創英角ゴシックUB／Cloud は MochiyPopOne という中間実装。有効履歴として維持し reset / revert しない。ただし現在の正式な生成書体ではない** |
| ② | **`31f734608490044a8f7441bca4dbe6a30b767774`**（`feat: 新宿歌舞伎町記事用のCloud書体を統一`） | **正式。ローカル・Cloud 共通の Noto Sans JP Black へ置き換えた** |

`31f7346` の変更は **`streamlit_app.py` / `convert_narabi_pil.py` / `fonts/NotoSansJP-Black.otf` /
`fonts/OFL.txt` の4ファイル**（+115 / −35）。
**変更関数は `load_font()` / `_patch_and_run_narabi()` / `show_auto_article_page()` /
`convert_narabi_pil._load_font()` だけ。新規関数0・消失関数0。**

**`31f7346` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。
`137592c` / `31f7346` へ reset してはならない。**

### B. 正式な書体

**新宿歌舞伎町かつ `page=auto_article` の記事用画像で、アプリが PIL で描画する文字・数字の
正式書体は `Noto Sans JP Black`。**

| 項目 | 値 |
|---|---|
| 同梱ファイル | **`fonts/NotoSansJP-Black.otf`**（4,855,212 bytes） |
| 配布元 | **`github.com/notofonts/noto-cjk`（Noto CJK 公式）の `Sans/SubsetOTF/JP/NotoSansJP-Black.otf`** — 日本語サブセットの**静的OTF** |
| ライセンス | **SIL Open Font License 1.1（再配布可）**。本文は **`fonts/OFL.txt`**（上流 `Sans/LICENSE` の内容をそのまま・OFL標準の慣例名で配置） |
| フォント内部 | Family `Noto Sans JP Black` ／ PostScript `NotoSansJP-Black` ／ weightClass **900** ／ sfntVersion `OTTO` ／ name(13) に OFL 1.1、name(14) に `http://scripts.sil.org/OFL` |
| 収録 | 16,732 コードポイント |

**★太字指定は不要**（Black＝weight 900 でフォント自体が太い）。PIL に合成ボールドは無い。

### C. ★HGS創英角ゴシックUB は使わない（ライセンス上の確定事項）

**HGS創英角ゴシックUB（`HGRSGU.TTC` の index=2 ＝ `HGSSoeiKakugothicUB`）は
Windows/MS Office 同梱の商用フォントで、再配布が許諾されていない。**
本リポジトリは **public**（`github.com/tama0520/guild-image-app`）であり、
**public リポジトリへのフォント追加は配布行為にあたる**ため、Cloud との書体統一には使用しない。

**次をリポジトリへ含めてはならない：`HGRSGU.TTC` ／ HGS関連ファイル ／ Windows固有パス。**
実装からも完全に撤去済みで、`HGRSGU` / `HGS` / `_ART_FONT_HGS` / `FONT_INDEX` / `font_index` の
**残存は `streamlit_app.py` / `convert_narabi_pil.py` とも0件**（死コードを残していない）。

なお環境内に「HGS創英角ゴシック**B**」は存在せず、実在するのは **UB（Ultra Bold）** だけである
（`137592c` 時点の調査で確定）。この事実は記録として残す。

### D. `_ART_FONT_PATH`（OS依存パスを使わない）

```python
_ART_FONT_PATH = os.path.join(_FONTS_DIR, "NotoSansJP-Black.otf")
```

**`BASE_DIR` 相対のリポジトリ内パス**なので、**ローカルWindowsでも Streamlit Cloud でも
同じ commit の同じファイル**を読む。**`C:\Windows\Fonts` のような OS依存パスを書かない。**

### E. `_art_font_new()`（ページ×店舗ゲート）

```python
_ART_FONT_PAGES:  "frozenset[str]" = frozenset({"auto_article"})
_ART_FONT_STORES: "frozenset[str]" = frozenset({"新宿歌舞伎町"})


def _art_font_new() -> bool:
    try:
        return (st.session_state.get("page") in _ART_FONT_PAGES
                and st.session_state.get("selected_store") in _ART_FONT_STORES)
    except Exception:
        return False
```

- **`page × store` の AND で毎回導出**する（`_table_theme_new()` / `_slump_theme_new()` /
  `_is_kabupa_page()` と同じ確立済みの流儀）。**保存フラグを持たない**のでページ遷移・rerun に影響されない。
- **Streamlit 外（純粋テスト・subprocess）では `False`＝従来書体。**
- 網羅テストで、**10ページ × 13店舗＝130通りのうち ON は
  `auto_article × 新宿歌舞伎町` の1通りだけ**であることを確認済み。

### F. ★`load_font()` のキャッシュキーは書体識別子を含む

```python
_font_cache: dict[tuple[int, str], ImageFont.ImageFont] = {}
...
    _art = _art_font_new()
    _ck = (size, "art" if _art else "std")
```

**キーを「サイズのみ」へ戻してはならない。**戻すと、同じサイズで先に読まれた書体が
**他店舗・他ページへ混入する**（例：記事用で読んだ Black が通常ページの表にも出る）。

候補の並びは次のとおりで、**述語がTrueのときだけ先頭に同梱フォントを挿す**。
呼び出し側30箇所は**1行も変更していない**（`load_font()` の1箇所で
表・タイトルバー・サマリー・差枚数ランキング・全台データ・スランプへ一括適用される）。

```
（記事用・新宿歌舞伎町のみ）fonts/NotoSansJP-Black.otf
 → fonts/MochiyPopOne-Regular.ttf → fonts/NotoSansJP-Regular.ttf
 → Windows フォント（ローカル実行時フォールバック）
```

### G. ★⑦プレビューと⑧本番で同じ同梱フォントを参照する

**⑧本番の並び・列は `convert_narabi_pil.py` を subprocess 実行するため
`load_font()` を通らない。必ず両方へ同じフォントを渡すこと。**

| 経路 | フォント取得 |
|---|---|
| ⑦プレビュー（および⑧の非並び画像） | `load_font()` → `_ART_FONT_PATH` |
| ⑧本番の並び・列（subprocess） | `_patch_and_run_narabi(font_path=_ART_FONT_PATH)` → `FONT_OVERRIDE` |

```python
# 記事用⑧の呼び出し（1箇所だけ）
font_path=(_ART_FONT_PATH if _art_font_new() else None),
```

**`_patch_and_run_narabi()` の `font_path` 既定は `None`＝従来書体**。
`font_index` は OTF に TTC index が不要なため**撤去済み**（死コードを残さない）。

### H. `convert_narabi_pil.py` の既定は従来書体

```python
FONT_OVERRIDE = ""          # 既定＝従来どおり FONT_PATH（MochiyPopOne）


def _load_font(size):
    try:
        if FONT_OVERRIDE and os.path.exists(FONT_OVERRIDE):
            return ImageFont.truetype(FONT_OVERRIDE, size)
    except Exception:
        pass
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()
```

**既定値 `""` を変更しない。**他店舗・他ページの⑧は従来書体のまま。
**新宿歌舞伎町の記事用⑧だけ**が `_patch_and_run_narabi()` の regex 書き換えで
`FONT_OVERRIDE` を受け取り、Noto Sans JP Black を使う。

### I. 対象（この書体になるもの）

**全台系 ／ 高配分 ／ ②個別 ／ ④末尾 ／ ⑤オススメ ／ ジャグラーシリーズ優秀台 ／
その他優秀台 ／ 並び ／ 列 ／ 差枚数ランキング ／ 全台データ、
および画像へ合成される スランプカード内の機種名・台番・差枚。**

### J. 対象外（従来仕様を維持する）

他店舗の記事用（高田馬場・渋谷新館・秋葉原）／通常結果ポスト（`auto`）／
かぶぱポスト（`auto_slump`）／スランプ付き結果（`auto_slump2`）／ローテ用（`rote`）／
作業用ページ（`work`）／**WordPress本文・投稿タイトル・Streamlit UI**／
**パネル画像・液晶画像・ポスターなど素材へ焼き込まれた文字**（アプリから書体変更不可）／
**WordPressの分割・画質・fullwidth・nosplit 処理**／
記事用パネルあり・記事用液晶なし・島図なし・10日区切り。

同一コンテキストで「述語を常に False＝従来挙動」と比較し、次の10通りが
**画素・サイズ完全一致**であることを確認済み。

```
auto_article×高田馬場 / auto_article×渋谷新館 / auto_article×秋葉原 /
auto×新宿歌舞伎町 / auto_slump×新宿歌舞伎町 / auto_slump2×新宿歌舞伎町 /
rote×新宿歌舞伎町 / work×新宿歌舞伎町 / auto×稲毛 / auto×高田馬場
```

**`wp_client.py` は無変更**なので、fullwidth A-2a ／ Luminous ／ nosplit ／
`_ART_WP_SPLIT_NARROW_STORES` ／ `_ART_WP_MIN_KEEP_W = 752` も不変。

### K. `77e140d` の仕様を維持

- **⑦プレビューを押さず⑧だけ実行しても、並び画像へパネル・スランプが付く**
  （`_ART_NARABI_BANMAP_STORES` ／ `_art_narabi_items()`）。
- **WordPress用のマイジャグV分割仕様（5分割・各片幅1982px）**
  （`_ART_WP_SPLIT_NARROW_STORES` ／ `wp_saved_width()` ／ `_ART_WP_MIN_KEEP_W`）。

どちらも本節の書体変更では変えていない。

### L. フォントが読めない環境でのフォールバック

**`fonts/NotoSansJP-Black.otf` が万一読めない環境では、例外を出さず
従来の MochiyPopOne へフォールバックする。**
`os.path.exists` で候補をスキップするだけなので、**`st.error` / `st.stop()` も発生しない**
（`os.path.exists` を差し替えて「フォント無し」を再現したテストで確認済み）。
⑧の subprocess 側も `FONT_OVERRIDE` の実在チェックで `FONT_PATH` へ落ちる。

### M. レイアウトは調整していない

**文字サイズ係数・`GAP_TITLE`・レイアウトは今回いっさい変更していない。**

Noto Sans JP Black の metrics は **`(ascent 47, descent 12)`** で
**MochiyPopOne と完全に同一**のため、既存の指定サイズのままで
行高・バー高・列幅が自然に収まり、破綻が出ない
（`137592c` の HGS は `(35, 6)` で約30%小さく見えていた）。

### N. 確認結果

**純粋テスト 86 PASS / 0 FAIL。**
ゲート網羅（130通りでONは1通り）／キャッシュ混入なし／グリフ収録／
`convert_narabi_pil` の既定維持と差し替え／regexパッチ／AST非回帰。

**ローカル実機（2026-09-15 データ・749台／⑦を押さず⑧だけ実行）**

| 項目 | 結果 |
|---|---|
| 並び7件のパネル・スランプ | **7/7**（1889×2795 ／ 2062×2080 ／ 2062×3000 ／ 2062×2086 ×3 ／ 2062×2080） |
| ⑧並び（subprocess）の書体 | 記事用書体版と画素差分 **0.0001**／従来版とは **0.1044** → 一致 |
| ⑦（in-app `load_font`） | `Noto Sans JP Black` → **⑦と⑧で一致** |
| 差枚数ランキング.jpg（2181×4638） | 記事用書体差分 **0.000024** ／ 従来差分 0.0850 |
| 全台データ.jpg（748×298） | 記事用書体差分 **0.0003** ／ 従来差分 0.1065 |
| スランプカード内の機種名・台番・差枚 | **目視で変更確認** |

**文字の健全性**：`（805～807）`（全角括弧・波ダッシュ U+301C／U+FF5E）／`（優秀台）`（重なりなし）／
`+1,300枚` 相当／`1/220.5` 相当／漢字・かな・カナ・英字・全角/半角数字・
記号（`+ - % ( ) , . : /` と全角版）・丸数字・全角スペース ── **欠落0・豆腐0・はみ出し0**。

**Cloud 実機**：2026-09-16 にユーザーが確認し、**ローカルと同じ Noto Sans JP Black で
問題なく生成される**ことを承認済み。

### O. Cloud で同じ書体になる根拠

1. **書体ファイルがリポジトリ内にある**（`_ART_FONT_PATH` は `BASE_DIR` 相対）。
   ローカルでも Cloud でも**同じ commit の同じファイル**を読む。
2. **⑧の subprocess にも同じパスを渡す**ので、⑦と⑧が同一ファイルを参照する。
3. **OS依存の分岐が残っていない**（`HGRSGU` / `HGS` / `C:\Windows\Fonts` への参照は0件）。
4. **SIL OFL 1.1 で再配布可能**なので public リポジトリへ同梱できる。

### P. 今後の禁止事項

1. **`fonts/NotoSansJP-Black.otf` / `fonts/OFL.txt` を削除しない**
2. **`HGRSGU.TTC` / HGS関連ファイル / Windowsフォントをリポジトリへ追加しない**
3. **`_ART_FONT_PATH` に OS依存パス（`C:\Windows\Fonts` 等）を書かない**
4. **`_art_font_new()` のページ×店舗ゲートを外さない／他店舗・他ページへ広げない**
5. **`_font_cache` のキーをサイズのみへ戻さない**（書体混入が起きる）
6. **⑦だけ／⑧だけ直さない**（`load_font()` と `_patch_and_run_narabi(font_path=…)` は必ずセット）
7. **`convert_narabi_pil.FONT_OVERRIDE` の既定 `""` を変更しない**
8. **`_patch_and_run_narabi()` の `font_path` 既定 `None` を変更しない**
9. **`font_index` / `FONT_INDEX` を復活させない**（OTF に TTC index は不要）
10. **`load_font()` の呼び出し側30箇所へ引数を足さない**（1箇所での一括適用を維持）
11. **文字サイズ係数・`GAP_TITLE`・レイアウトを本節を理由に変更しない**
12. **フォント未存在時のフォールバックを外さない**（例外・`st.error` を出さない）
13. **`137592c` を「現在の正式な生成書体」と誤記しない**（`31f7346` が正式）／
    **`137592c` / `31f7346` へ reset・revert しない**
14. **`77e140d` の並び ban_map 再計算とマイジャグV分割仕様を壊さない**
15. **`wp_client.py`・WordPress本文・分割・fullwidth・nosplit・パネル・液晶・島図・
    10日区切りを本節を理由に変更しない**
16. **他店舗の記事用・通常結果ポスト・かぶぱ・`auto_slump2`・ローテ用・作業用へ波及させない**
17. **無関係なリファクタ・未使用コード整理をしない**


## 【正式仕様】新宿歌舞伎町 記事用：スランプ外側背景を薄紫 #D8C6E3 へ統一（2026-09-16・`61851ca`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用だけ**。
2026-09-16 に **ユーザーが Streamlit Cloud 実機で確認し「問題なし」と正式承認**した。

| 項目 | 値 |
|---|---|
| **正式実装 commit** | **`61851ca9fac84f98f894c308842a8e335ff6de85`** |
| commit message | **`feat: 新宿歌舞伎町記事用のスランプ背景を統一`** |
| 変更ファイル | **`streamlit_app.py` の1ファイルのみ**（+15 / −17） |
| 前提 commit | **`e53a116`**（`feat: 新宿歌舞伎町高配分画像の表示を調整`） |

**`61851ca` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。
`e53a116` / `61851ca` へ reset してはならない。**

既存の記事用・スランプ関連セクション（`77e140d` / `31f7346` / `5c5c1f2` / `3432a97` /
`0e49bd9` / `5711df4` ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。

### ① 正式な背景色

**新宿歌舞伎町の記事用で `_attach_slump_to_table()` によりスランプを合成する全カテゴリで、
スランプカード外側の背景を薄紫 `#D8C6E3` ＝ RGB `(216, 198, 227)` に統一する。**

**カテゴリ・ファイル名では判定しない（店舗だけで決める）。**

### ② 対象カテゴリ（ban_map があって実際にスランプを合成する画像）

全台系 ／ 高配分（**自動 `{機種名}_高配分.jpg` と手動 `{機種名}（優秀台）.jpg` の両方**）／
②個別の優秀台 ／ ジャグラーシリーズ優秀台 ／ その他優秀台 ／ 並び ／ 列 ／ ④末尾 ／
バラエティ ／ ⑤オススメ。

### ③ ★②個別「全台」へスランプ合成を追加しない

**⑧本番では従来から②個別「全台」が ban_map 未登録**（⑦のみ登録）であり、
**今回もスランプ合成を追加していない。勝手に ban_map 登録を足さないこと。**

### ④ 対象外（スランプを合成しない画像）

**差枚数ランキング ／ 全台データ ／ 島図 ／ ポスター**は ban_map 未登録のため
合成ループに入らず、今回も対象外。

### ⑤ 正式な定数・helper

```python
# 記事用（auto_article）でスランプを合成する **全カテゴリ共通**の「カード外側」背景色。
C_ART_SLUMP_AREA_BG: "tuple[int, int, int]" = (216, 198, 227)   # #D8C6E3
_ART_SLUMP_BG_STORES: "frozenset[str]" = frozenset({"新宿歌舞伎町"})


def _art_slump_bg(store: str):
    """記事用スランプの「カード外側」背景色（対象外は None＝従来の bbb.jpg 経路）。"""
    return C_ART_SLUMP_AREA_BG if store in _ART_SLUMP_BG_STORES else None
```

- **`_art_slump_bg(store)` は新宿歌舞伎町だけ薄紫を返し、他店舗は `None` を返す。**
- **引数は `store` だけ。カテゴリ名・ファイル名に依存させない。**
- 旧名 `C_ART_HIGH_SLUMP_BG` / `_ART_HIGH_SLUMP_BG_STORES` / `_art_high_slump_bg()` は
  **この commit で廃止**（`e53a116` 時点の高配分限定版）。**復活させない。**
- ★既存の `C_SL_PURPLE`（スランプカード内部の淡紫）/ `C_SLUMP_AREA_BG`（スランプ付き結果の
  `#FFFFCB`）/ `bbb.jpg` とは**別用途の専用定数**。値が近くても統合・流用しない。

### ⑥ ⑦・🔄・⑧で同じ判定を使う

**⑦プレビュー ／ 🔄その他を更新 ／ ⑧本番の3経路すべて**で、
`_attach_slump_to_table()` の **`bg_color` に同じ `_art_slump_bg(store)`** を渡す。

**⑦だけ・⑧だけ・🔄だけ異なる背景にしてはならない。**
店舗のみの判定なので、ファイル名の綴り違い・連番プレフィックス（`NN_`）の有無による
不一致が構造的に発生しない。

### ⑦ 既定値は維持（他店舗・他ページを変えない）

**`_paste_slump_area_bg(..., bg_color=None)` と `_attach_slump_to_table(..., bg_color=None)` の
既定 `None` は維持する。**`bg_color is None` のときは従来どおり
「`_slump_theme_new()` なら `C_SLUMP_AREA_BG`（#FFFFCB）／それ以外は `bbb.jpg`」になる。

**`_find_slump_bg()` ／ `bbb.jpg` ／ `base_3000_bk.png` ／ `_slump_theme_new()` ／
`C_SLUMP_AREA_BG` は変更しない。**

### ⑧ 水色バー削除（`e53a116`）は別系統として維持

**高配分画像の水色バー「優秀台ピックアップ」を削除する `e53a116` の正式仕様を維持する。**

| 用途 | ゲート |
|---|---|
| **水色バー削除** | **`_ART_HIGH_NO_BAR_STORES = frozenset({"新宿歌舞伎町"})`**（pipeline 2か所＋手動⑦⑧ 2か所） |
| **スランプ背景** | **`_ART_SLUMP_BG_STORES`**（記事用の attach 3か所） |

**この2つを混同・統合しない。**
`run_step2_juggler()` / `run_step3_other()` の **`high_bar: bool = True`（既定＝従来動作）**、
`run_auto_pipeline()` からの `high_bar=(store not in _ART_HIGH_NO_BAR_STORES)`、
`_art_high_title_bar()` 本体・既定テキスト・既定色も**変更しない**。

### ⑨ `_art_is_high_fn()` は削除しない

背景判定からは外れたが、**既存 helper として残す**
（`_高配分.jpg` / `（優秀台）.jpg` を判別する。将来の高配分限定処理で使う）。
**`_ARROW_TRI` / `_ART_CMT_D_TEXT` と同じ「未使用でも残す」扱い。**

### ⑩ 維持する既存正式仕様

記事用パネルあり（`_ARTICLE_PANEL_STORES`）／ **液晶なし**（`_ART_GAP_FILL_OFF_STORES`）／
**島図なし**（`_ARTICLE_SHIMAZU_STORES = {"渋谷新館"}`）／
**Noto Sans JP Black**（`31f7346` / `5c5c1f2`・`_ART_FONT_STORES`）／
**`77e140d` の並び・列 ban_map 再計算＋パネル・スランプ**（`_ART_NARABI_BANMAP_STORES`）／
**初代ヴァルヴレイヴの `vvv` 紐づけ・ヴァルヴレイヴ2の `vvv2` 紐づけ**／
**マイジャグVの WordPress 5分割**（`_ART_WP_SPLIT_NARROW_STORES` / `_ART_WP_MIN_KEEP_W = 752`）。

### ⑪ 対象外（従来仕様を維持）

**他店舗の記事用（高田馬場・渋谷新館・秋葉原）／ 通常結果ポスト ／ かぶぱ（`auto_slump`）／
`auto_slump2` ／ ローテ用 ／ 作業用 ／ WordPress 本文・UI・画像分割・fullwidth・nosplit。**

`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` / 機種画像マスタ /
パネル素材 / フォント / `機種名変換.xlsx` は**いずれも無変更（diff 0）**。

### ⑫ 変更範囲（機械確認）

- **新規関数は `_art_slump_bg` の1つだけ／削除は `_art_high_slump_bg` の1つだけ**
- **本体が変わった関数は `show_auto_article_page` のみ**
- `_paste_slump_area_bg` / `_attach_slump_to_table` / `_art_is_high_fn` /
  `_art_high_title_bar` / `run_step2_juggler` / `run_step3_other` / `run_auto_pipeline` /
  `_apply_panel_to_table_img` / `draw_slump_graph` / `_build_machine_img_no_bar` /
  `show_auto_page` / `show_rote_page` ほかは**すべて AST 一致**
- `bg_color=_art_slump_bg(store)` の3行はいずれも `show_auto_article_page` の行範囲内

### ⑬ 確認結果

**純粋テスト 164 PASS / 0 FAIL。**
新宿歌舞伎町のみ薄紫・他12店舗＋空文字は `None` ／ `_art_slump_bg()` の本体が
「`store in _ART_SLUMP_BG_STORES` の判定だけ」（AST 検証）／ 11カテゴリ相当のファイル名で
**同一画像**（色は薄紫＋カード黒の2色のみ）／ 他店舗は **`colors=5071` のレインボー維持・
薄紫混入0** ／ `bg_color` 省略時は **HEAD版と画素完全一致** ／ 画像サイズ・表領域・
カード本体の画素一致 ／ **マイジャグV 5分割維持**。

**ローカル実機（⑦プレビュー・2026/09/15 確定749台・28枚生成）**

スランプ合成のある **26枚すべてで左端が `(217,198,226)`（JPEG誤差±1）**、
**bbb.jpg 由来のレインボー画素は0件**。内訳は 全台系2（かのかり／ミスジャグ）・
高配分13・並び6・ジャグラーシリーズ優秀台1・その他優秀台1・⑤オススメ2、
外側は `差枚数ランキング.jpg`（白）と `全台データ.jpg` が**スランプなしで従来どおり**。
**水色バー `#0080FF` は26枚すべて0px**（青ブタの231pxはパネル画像内の青でバーではない）。
**ヴァルヴレイヴは `vvv_panel.png` が付き、構成は `[パネル][表][スランプ]`。**
黒いスランプカード本体・赤線・軸・機種名・台番・差枚・表・パネルは従来どおり。

**Cloud 実機：2026-09-16 にユーザーが確認し「問題なし」と正式承認。**

### ⑭ 今後の禁止事項

1. **背景判定をカテゴリ・ファイル名依存へ戻さない**（`_art_slump_bg(store)` は store のみ）
2. **`C_ART_HIGH_SLUMP_BG` / `_ART_HIGH_SLUMP_BG_STORES` / `_art_high_slump_bg()` を復活させない**
3. **`C_ART_SLUMP_AREA_BG` を `C_SL_PURPLE` / `C_SLUMP_AREA_BG` と統合・流用しない**
4. **`_ART_SLUMP_BG_STORES` へ他店舗を勝手に追加しない**
5. **⑦だけ・⑧だけ・🔄だけ変更しない**（3経路で同じ式）
6. **`bg_color` の既定 `None` を変更しない**（他店舗・他ページの背景が壊れる）
7. **`_find_slump_bg()` / `bbb.jpg` / `base_3000_bk.png` / `_slump_theme_new()` /
   `C_SLUMP_AREA_BG` を変更しない**
8. **水色バー削除（`_ART_HIGH_NO_BAR_STORES` / `high_bar` 既定 True）を巻き戻さない・
   スランプ背景判定と統合しない**
9. **`_art_is_high_fn()` を削除しない**
10. **②個別「全台」へ ban_map 登録・スランプ合成を追加しない**
11. **差枚数ランキング・全台データ・島図・ポスターへスランプ背景を適用しない**
12. **パネル・表・タイトル・文字・スランプカード本体・画像サイズ・合成順を変更しない**
13. **他店舗記事用・通常結果ポスト・かぶぱ・`auto_slump2`・ローテ用・作業用へ波及させない**
14. **WordPress 本文・UI・分割・fullwidth・nosplit・マイジャグV5分割を変更しない**
15. **`e53a116` / `61851ca` へ reset して実装をやり直さない**
16. **無関係なリファクタ・未使用コード整理をしない**


## 【正式仕様】新小岩 結果ポスト用テキスト：⑤オススメ機種の機種名先頭を「・」へ統一（2026-09-16・`4b72428`）

**正式仕様。巻き戻し禁止。**対象は**【新小岩】の結果ポスト用テキストだけ**。
2026-09-16 に **ユーザーが Streamlit Cloud 実機で確認し「問題なし」と正式承認**した。

| 項目 | 値 |
|---|---|
| **正式実装 commit** | **`4b724280eb68a00ee41c86c3d092bffba6fd6ce6`** |
| commit message | **`fix: 新小岩結果ポストの機種名記号を統一`** |
| 変更ファイル | **`streamlit_app.py` の1ファイルのみ**（+17 / −3） |

**`4b72428` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。**
直前の **`69db84f`（`auto: 画像生成後の設定を保存`）はアプリの `_git_auto_push()` による
有効な自動commit**（`auto_page_inputs.json` / `store_settings/新小岩.json`）であり、
**reset・revert・再commitしない。**

既存の結果テキスト関連セクション（2026-09-11 の `1c036e7` / `20bb9ea` / `9f274e8`、
`252a39b`、`1301431` ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。

### ① 対象ページ（両方）

| page | ボタン | `with_slump` |
|---|---|---|
| **`auto`** | **⚡ 結果ポスト用** | **False** |
| **`auto_slump`** | **📊 スランプ付き結果ポスト** | **True** |

**新小岩の両ページへ適用する。`with_slump` を条件に含めない。**

**★`auto_slump2` は新宿歌舞伎町専用で、新小岩には存在しない。**
新小岩のスランプ付きは **`auto_slump`** である（ボタンは「📊 スランプ付き結果ポスト」）。
**この2つを混同しない。**

### ② 「・」へ統一する対象

新小岩の **⑤オススメ機種**（`generate_recommended_result_text()`）で、

1. **B1〜B6 の機種名の行頭に付くブロック絵文字**（新小岩は `💥` / `🤡` / `🌺`。
   B1・B5・B6 の `🎖️` は既に「・」へ変換済み）
2. **⑤カテゴリ内の全台系／高配分サマリーの行頭 `🏅`**（`_rec_category_summaries()` の `head`）

を**すべて中黒「・」**にする。

```
💥カバネリ海門決戦 → ・カバネリ海門決戦
🏅ゴージャグ3      → ・ゴージャグ3
🤡マイジャグV      → ・マイジャグV
🌺沖ドキBLACK      → ・沖ドキBLACK
```

- **すでに「・」の箇所はそのまま維持する。**
- **「・・」の二重中黒を作らない。**

### ③ 対象外（従来どおり）

**⑤カテゴリ見出しの `🍀`** ／ **優秀台一覧見出しの `🎁`** ／ **台番行 `【N番台】+X,XXX枚`** ／
**差枚行 `+3,000枚、…`** ／ **末尾テキスト** ／ **+1,000枚以上台の羅列** ／ **画像内の文字**。

`✨` `📈` `🏆` `🌋` `💥`（`💥+5,000枚オーバー…`）`💎` `🤡`（`🤡本日のジャグラー全体…`）など、
**機種名の行頭ではない見出し・文言の絵文字も対象外。**

### ④ ★定義そのものは変更しない（生成時だけ差し替える）

**`STORE_REC_CONFIG["新小岩"]` の `block_emojis`（`["🎖️","💥","🤡","🌺","🎖️","🎖️"]`）・
`item_emoji`（`"🚩"`）・`section_emoji`（`"🍀"`）の定義、および
`_REC_CATEGORY_SUMMARY_HEAD = "🏅"` の定数定義は変更しない。**

2026-09-11（`1c036e7` / `20bb9ea`）で確立した
**「設定定義は残し、生成時に置換する」方式**をそのまま踏襲する。

### ⑤ 正式な店舗ゲートと引数

```python
# _REC_CATEGORY_SUMMARY_HEAD の直後
_REC_PLAIN_HEAD_STORES: "frozenset[str]" = frozenset({"新小岩"})


def generate_recommended_result_text(..., plain_head: bool = False) -> str:
    ...
    emoji = ("・" if plain_head
             else (_blk_emojis[i] if i < len(_blk_emojis) else "🎯").replace("🎖️", "・"))
```

- **`plain_head` の既定は必ず `False`＝従来動作。**
- 呼び出し（`show_auto_page` の⑧・1か所だけ）は
  **`plain_head=(store in _REC_PLAIN_HEAD_STORES)`**。
  **`with_slump` を条件に含めない**ので、新小岩の `auto` / `auto_slump` の両方で `True` になる。
- ⑤カテゴリ内サマリーは
  **`head=("・" if store in _REC_PLAIN_HEAD_STORES else _REC_CATEGORY_SUMMARY_HEAD)`**。
- **新小岩以外は `plain_head=False` のまま**（西武新宿の `🍀⚡️⭐🎯` / `📍` も不変）。

### ⑥ 「その他の主役機種」見出しの正式表記

```
🍀その他の主役機種(カバネリ海門・ゴッド神々・モンキーV・真打吉宗)
```

- **`STORE_REC_CONFIG["新小岩"]["block_header_names"][1]` を
  `["カバネリ海門", "ゴッド神々", "モンキーV", "真打吉宗"]` とする。**
- **「炎炎2」は表示から外す。**「ゴッド神々」を追加。
- **中黒は1つ。空要素を入れて `・・` にしない。**
- `block_header_names[0]`（B1）は**不変**。

### ⑦ ★`block_header_names` は見出し表示専用

**抽出判定・対象機種・並び順には一切使わない。**
⑤の抽出対象は `store_settings/新小岩.json` の `recommended_machines_N`（UIで編集）であり、
`_rec_category_summaries()` はそこから作った機種名集合と**完全一致**で判定する。

2026-09-16 時点の B2 実設定は
**カバネリ海門決戦 / ゴッド神々の軌跡 / モンキーターンV / 真打吉宗**（炎炎ノ消防隊2 は含まない）で、
今回の見出し変更は**この実設定へ表示を合わせたもの**である。
**2系統は自動同期しないので、`block_header_names` を触るときは
`recommended_machines_N` との整合を人が確認する。**

### ⑧ 変更しないもの

**`generate_report_text()`**（AST 一致・無変更）／ 末尾仕様 ／ +1,000枚以上台の羅列 ／
⑤の**抽出条件・対象機種・閾値・並び順** ／ **画像生成**（`generate_recommended_block_image()` ほか）／
`_rec_category_summaries()` 本体 ／ `_result_summary_lines()` ／
`filter_recommended_machines()` ／ `_kojin_yushu_filter()` ／ `run_auto_pipeline` ／
`run_step1〜3` ／ `_build_kabupa_result_text()` ／ `_generate_rote_result_text()` ／
`show_auto_article_page()`。

### ⑨ 対象外（従来仕様を維持）

**新小岩以外の全店舗** ／ **新宿歌舞伎町の `auto_slump2`** ／ **記事用** ／
**かぶぱ（`auto_slump`）** ／ **ローテ用** ／ **WordPress** ／ **Pision 表示**。

`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` / 機種画像マスタ /
`機種名変換.xlsx` / `store_settings/` はいずれも**無変更（diff 0）**。

### ⑩ 変更範囲（機械確認）

- **新規関数0 ／ 削除関数0**
- **本体が変わった関数は `generate_recommended_result_text` と `show_auto_page` の2つだけ**
- `generate_report_text` / `_rec_category_summaries` / `_result_summary_lines` /
  `filter_recommended_machines` / `_kojin_yushu_filter` /
  `generate_recommended_block_image` / `run_auto_pipeline` / `run_step1_main` /
  `run_step2_juggler` / `run_step3_other` / `_build_kabupa_result_text` /
  `_generate_rote_result_text` / `show_auto_article_page` / `show_rote_page` /
  `_attach_slump_to_table` / `_art_slump_bg` ほかは**すべて AST 一致**

### ⑪ 確認結果

**純粋テスト 78 PASS / 0 FAIL**（実 `store_settings/新小岩.json` の26機種で検証）。

新小岩の **`auto` / `auto_slump` の両方**で:
**行頭の `💥` / `🤡` / `🌺` / `🏅` が0件** ／ **`・` が30行＝機種名26＋サマリー4** ／
**`・・` の二重0件** ／ 見出しが
**`🍀その他の主役機種(カバネリ海門・ゴッド神々・モンキーV・真打吉宗)` と完全一致** ／
`🍀` `🎁` 見出し維持 ／ 台番行26行で不変 ／
**記号以外の内容（機種・台番・並び順・差枚行）は `plain_head=False` の出力と完全一致**。

**他店舗12店すべてで ⑤テキストが HEAD 版と出力完全一致**（西武新宿の `🍀⚡️⭐🎯`・`📍` も維持）。

**ローカル実機**：`auto` / `auto_slump` の両ページが例外なく表示（Traceback 0件）。
**Cloud 実機：2026-09-16 にユーザーが両ページを確認し「問題なし」と正式承認。**

### ⑫ 今後の禁止事項

1. **新小岩の⑤で `💥` / `🤡` / `🌺` / `🏅` を機種名・サマリーの行頭へ戻さない**
2. **`_REC_PLAIN_HEAD_STORES` へ他店舗を勝手に追加しない**
3. **`plain_head` の既定 `False` を変更しない**（他店舗の従来動作が壊れる）
4. **呼び出しへ `with_slump` を条件として足さない**（`auto` 側が元へ戻る）
5. **`STORE_REC_CONFIG` の `block_emojis` / `item_emoji` / `section_emoji` の定義を書き換えない**
6. **`_REC_CATEGORY_SUMMARY_HEAD = "🏅"` の定数定義を削除・変更しない**
7. **`🍀` カテゴリ見出し・`🎁` 優秀台一覧見出しを「・」にしない**
8. **台番行・差枚行・末尾テキスト・+1,000枚以上の羅列・画像内文字を変更しない**
9. **見出しへ「炎炎2」を戻さない／`・・` の二重中黒にしない／空要素を入れない**
10. **`block_header_names` を抽出判定へ使わない**（`recommended_machines_N` との整合は人が確認）
11. **`generate_report_text()` を変更しない**
12. **⑤の抽出条件・対象機種・閾値・並び順・画像生成を変更しない**
13. **新小岩以外・新宿歌舞伎町の `auto_slump2`・記事用・かぶぱ・ローテ・WordPress・Pision へ
    波及させない**
14. **`auto_slump2` を新小岩のページとして扱わない**
15. **`4b72428` / `69db84f` へ reset・revert しない**
16. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：白地スランプカード・右下青差枚・細い最外周罫線・表見出し黒地・カード内機種名なし（2026-09-17・`c1c3bdd` / `56844fe` / `cc695d4`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用だけ**。
2026-09-17 に **ユーザーが Streamlit Cloud 実機で確認し「すべて問題なく表示される」と正式承認**した。

既存の記事用・スランプ関連セクション（`77e140d` / `31f7346` / `5c5c1f2` / `61851ca` / `e53a116` /
`0e49bd9` / `5711df4` / `3432a97` / `a05cb00` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**2026-09-17 の正式仕様として末尾へ追加**する。

### A. 正式実装commit（3本でひとつの仕様を構成）

| # | commit | 内容 |
|---|---|---|
| ① | **`c1c3bdd90753ec815b994c59da8aa59d7785eda5`** | `feat: 新宿歌舞伎町記事用のスランプを白地化`（`streamlit_app.py` のみ） |
| ② | **`56844fe88539d4f3bcf8effb2216658b85842bba`** | `feat: 新宿歌舞伎町記事用のスランプ表示を調整`（`streamlit_app.py` / `convert_narabi_pil.py` の2ファイル） |
| ③ | **`cc695d449e46e8993e8b5d2ac72f4a5eb51eb620`** | `feat: 新宿歌舞伎町記事用スランプの機種名を削除`（`streamlit_app.py` のみ・+13 / −3） |

**いずれも「正式仕様の根拠となる実装commit」であって、HEAD をここへ戻すという意味ではない。
`c1c3bdd` / `56844fe` / `cc695d4` へ reset してはならない。**

**★`56844fe` は commit メッセージの先頭に `@` が混入している**（Bash に PowerShell の
here-string 記法を渡したミス）。**push 済みのため force push による書き換えはしていない。
コード差分は正常で、この `@` を理由に履歴を書き換えてはならない。**

### B. 対象範囲

**対象は `auto_article × 新宿歌舞伎町` の1通りだけ。**
その記事用で**スランプを合成する全カテゴリ**に適用する。

全台系 ／ 高配分（**自動 `{機種名}_高配分.jpg` と手動 `{機種名}（優秀台）.jpg` の両方**）／
②個別の優秀台 ／ ジャグラーシリーズ優秀台 ／ その他の優秀台ピックアップ ／ 並び ／ 列 ／
④末尾 ／ バラエティ ／ ⑤オススメ。

### C. ★②個別「全台」へスランプ合成を追加しない／スランプなし画像は対象外

- **⑧本番では従来から②個別「全台」が ban_map 未登録**（⑦のみ登録）であり、
  **今回もスランプ合成を追加していない。勝手に ban_map 登録を足さないこと。**
- **差枚数ランキング ／ 全台データ ／ 島図 ／ ポスター**は ban_map 未登録で
  スランプ合成ループに入らないため**対象外**。

### D. スランプカード本体の配色

| 対象 | 色 |
|---|---|
| **カード地** | **白 `#FFFFFF`**（`C_ART_SL_CARD_BG = (255, 255, 255)`） |
| **外枠 ／ 区切り線 ／ ヘッダー帯 ／ 縦軸 ／ 0ライン ／ 補助線 ／ 目盛文字** | **黒 `#000000`**（`C_ART_SL_CARD_LINE`） |
| **カード外側の背景** | **薄紫 `#D8C6E3` RGB `(216, 198, 227)`**（既存正式仕様 `61851ca` の `C_ART_SLUMP_AREA_BG` を維持） |
| **スランプ折れ線** | **赤 `#FF0000`（維持）** |

### E. 最外周罫線だけ細くする（内部線は太さを維持）

```python
_ART_SL_OUTER_RATIO = 0.4
_keep = max(1, round(_SL_FRAME_PAD * _ART_SL_OUTER_RATIO))   # = 4px（黒として残す内側）
_cut  = max(0, _SL_FRAME_PAD - _keep)                        # = 6px（薄紫で塗る外側）
```

- 元テンプレの外枠は上下左右とも**厳密に10pxのベタ白帯**で、再配色でそのまま10pxの黒帯になる。
  その**外側6pxをカード外側と同じ `C_ART_SLUMP_AREA_BG` で塗り、内側4pxだけを黒として残す**
  ＝**見た目4px相当の細い罫線**。
- **塗る色は `C_ART_SLUMP_AREA_BG` を関数内でそのまま参照する**（別定数にすると値がズレて境目が見える）。
- **カード内部の区切り線・グラフ枠・縦軸・0ライン・補助線・目盛線は細くしない**（太さも色も不変）。
- **`base_3000_bk.png` は読み取るだけで変更しない**（メモリ上の再配色のみ）。

### F. カード内の差枚数は右下・青・85%

| 項目 | 値 |
|---|---|
| 位置 | **グラフ囲みの右下へ右寄せ** |
| 色 | **`C_ART_SL_CARD_DIFF = C_PLUS = "#0000CC"`**（表内のプラス差枚色と同じ青を**参照**する） |
| サイズ | **既存サイズの85%**（`_ART_SL_DIFF_FONT_RATIO = 0.85`） |
| 安全余白 | **`_ART_SL_DIFF_PAD = 8`**。`_SL_FRAME_PAD(10) + 8 = 18` なので**下端位置は従来と1pxも変わらない**（横位置だけ中央寄せ→右寄せ） |
| 可読性 | **8方向の白縁取り**（`C_ART_SL_CARD_EDGE`）を先に描いてから青文字を重ねる |

- 右端は `388 - 10 - 8 = 370` で、**0ライン・補助線の右端(377)より内側**に収まる。
  目盛文字は左端にあるので当たらない。
- **右下は折れ線の終点が来る場所でもある**（終端が概ね **−2,800枚以下**だと赤線がテキスト帯を通る）。
  白縁取りは**可読性のためだけ**で、**色（`C_PLUS`）・サイズ（85%）・位置（右下）は変えない。
  赤い折れ線自体も消さない。**
- **新しい青定数を作らず `C_PLUS` を参照する**（表の差枚色と値がズレないため）。

### G. ★カード内に機種名を一切表示しない（`cc695d4`）

**新宿歌舞伎町の記事用では、スランプカード内の機種名を上部・下部とも一切描画しない。**

| 区分 | 従来 | 正式 |
|---|---|---|
| **カード上部の機種名**（`display_name`・ヘッダー1帯 `_SL_HDR1 = (10, 50)`） | 無条件で描画 | **描画しない**（`_center_xy()` の**文字位置計算にも入らない**） |
| **カード下部の複数機種用の機種名**（`machine_name`・差枚数の直上） | `if machine_name:` で描画 | **描画しない**（**フォント計算・白の縁取り・本描画のいずれにも入らない**） |

**カード内に残すもの：台番 ／ 目盛 ／ 赤い折れ線 ／ 右下の青い差枚数。**

### H. 機種名を消してもレイアウトは変えない（案A）

- **上部ヘッダー帯は空白のまま残す。**帯・区切り線（`_SL_SEP1` / `_SL_SEP2`）は従来どおり描かれる。
- **台番は従来どおりヘッダー2帯（`_SL_HDR2 = (57, 97)`）へ残す。**
- **カードサイズ 388×472 ／ グラフ座標（`X_START=24` / `X_END=364` / `Y_ZERO=290` /
  `PX_1000=47` / `DARK_Y1=462`）／ 表との合成位置は一切変更しない。**
- **カードを詰めない ／ 台番を上へ移動しない ／ テンプレ素材・座標定数を変更しない。**

### I. ★実装は `draw_slump_graph()` 内の `_sl_art` 1本（呼び出し側へ分岐を足さない）

```python
_sl_new = _slump_theme_new()
_sl_art = (not _sl_new) and _art_slump_card_new()
if _sl_new:      base = _slump_template_image(template_path)     # auto_slump系の淡紫
elif _sl_art:    base = _art_slump_card_image(template_path)     # 記事用の白カード
else:            base = Image.open(str(template_path)).convert("RGBA")   # 従来の黒テンプレ
```

機種名の抑止も**この関数内の `_sl_art` 2箇所のガードだけ**で行う。

- **⑦プレビュー・🔄その他を更新・⑧本番の呼び出し側（`show_auto_article_page` 内の3箇所）へ
  個別分岐を追加しない。**同じ関数を通るので**3経路が構造的に一致**する。
- **`_show_mn_pv2` / `_show_mn_u` / `_show_mn_sl` / `_osu_multi_pv2` / `_osu_multi_sl` と、
  呼び出し側で渡す `display_name` / `machine_name` の条件式を変更しない**
  （他店舗の記事用と共有しているため）。
- **`show_auto_article_page` に `_sl_art` を持ち込まない。**

### J. ゲートは page × store の AND（保存フラグを持たない）

```python
_ART_SL_CARD_PAGES:  "frozenset[str]" = frozenset({"auto_article"})
_ART_SL_CARD_STORES: "frozenset[str]" = frozenset({"新宿歌舞伎町"})


def _art_slump_card_new() -> bool:
    try:
        return (st.session_state.get("page") in _ART_SL_CARD_PAGES
                and st.session_state.get("selected_store") in _ART_SL_CARD_STORES)
    except Exception:
        return False
```

- **True になるのは `auto_article × 新宿歌舞伎町` の1通りだけ**（13店舗 × 12ページ＝156通りで確認）。
- **Streamlit 外（純粋テスト・subprocess）では `False`＝従来の黒テンプレ。**
- `_art_font_new()` / `_slump_theme_new()` / `_table_theme_new()` と同じ確立済みの流儀。
  **保存フラグ方式へ戻さない。**
- **専用キャッシュ `_ART_SL_TMPL_CACHE` を持つ**（`_SL_TMPL_CACHE` と共有すると
  淡紫版と白版が同じキーで衝突する）。**キャッシュを統合しない。**

### K. 表の最上段見出しを黒地・白文字・薄灰色罫線

| 対象 | 値 |
|---|---|
| **見出しセル背景** | **黒 `#000000`**（`C_ART_TBL_HEADER_BG`） |
| **見出しセル文字** | **白 `#FFFFFF`**（`C_ART_TBL_HEADER_FG`） |
| **見出しセル間の罫線** | **薄いグレー `#DDDDDD`**（`C_ART_TBL_HEADER_LINE`）。**白にしない** |

対象は最上段の **「台番」「機種名」「ゲーム数」「REG」「AT」「合算確率」「差枚数」**。

**本文セルの背景・本文文字・本文罫線（`C_BORDER`）・差枚数の値の色（`C_PLUS` / `C_MINUS` /
`C_ZERO`）・列幅・行高・表高さ・タイトルバー・サマリー・スランプ合成順は変更しない。**

判定は **`_art_table_header_new()`**（`_ART_TBL_HEADER_PAGES` × `_ART_TBL_HEADER_STORES`）。
**既存の結果ポスト系テーマ（`_table_theme_new()` / `C_NEW_HEADER_*` / `_TABLE_THEME_*`）とは
別仕様**で、ページが排他（`auto` 系 / `auto_article`）なので同時に成立しない。**統合しない。**

### L. ★⑦・🔄・⑧で表見出しを一致させる（並び・列は subprocess）

⑧本番の並び・列は **`convert_narabi_pil.py` を subprocess 実行**するため `draw_table_image()` を
通らない。**必ず両経路へ同じ設定を渡すこと。**

| 経路 | 実装 |
|---|---|
| ⑦プレビュー（および⑧の非並び画像） | `draw_table_image()` が `_art_table_header_new()` で切替 |
| ⑧本番の並び・列（subprocess） | **`_patch_and_run_narabi(..., art_header=_art_table_header_new())`** → `convert_narabi_pil.py` の **`ART_HEADER`** を regex で書き換え |

```python
# convert_narabi_pil.py（既定は必ず False＝従来のクリーム見出し）
ART_HEADER = False
HEADER_BG  = ((0, 0, 0) if ART_HEADER else ((41, 0, 104) if THEME_NEW else (243, 230, 200)))
HEADER_FG  = ((255, 255, 255) if ART_HEADER else ((255, 255, 255) if THEME_NEW else (75, 0, 130)))
HEADER_LINE_C = (221, 221, 221) if ART_HEADER else BORDER_C
```

- **`THEME_NEW` は流用しない**（本文文字色・行高・タイトルバー・サマリーまで変わるため）。
- 見出し行は `draw.rectangle([(0, 0), (img_w - 1, row_y(1) - 2)], fill=HEADER_LINE_C)` で
  先に帯を塗ってからセルを描くので、**見出し／本文の境界線は `BORDER_C` のまま**。
- **`ART_HEADER` の既定 `False` を変更しない**（通常ページ・他店舗・ローテ・かぶぱが壊れる）。
- **⑦だけ／⑧だけ直さない。**

### M. 素材・他ファイルは変更しない

**`base_3000_bk.png` ／ `bbb.jpg` ／ `_slump_template_image()` ／ 機種画像マスタ ／
パネル素材 ／ フォント素材はいっさい変更しない。**

**`base_3000_bk.png` の sha256 は
`bbc09ea8a3b24ec880606f36ac89054e38276a78217402834e0a7d3e2bd73618`（不変）。**

`wp_client.py` / `shimazu_renderer.py` / `masters/machine_image_master.xlsx` / `機種名変換.xlsx` も
**`git diff` 0**（`convert_narabi_pil.py` は `56844fe` の `ART_HEADER` 追加のみ）。

### N. 維持する既存正式仕様（新宿歌舞伎町の記事用）

**記事用パネルあり**（`_ARTICLE_PANEL_STORES`）／ **液晶なし**（`_art_gap_fill_on("新宿歌舞伎町") == False`）／
**島図なし**（`_ARTICLE_SHIMAZU_STORES` は渋谷新館のみ）／ **Noto Sans JP Black**
（`_ART_FONT_STORES` / `31f7346` / `5c5c1f2`）／ **高配分の水色バー削除**（`_ART_HIGH_NO_BAR_STORES` / `e53a116`）／
**薄紫のカード外側背景**（`_ART_SLUMP_BG_STORES` / `61851ca`）／
**`77e140d` の並び・列 ban_map 再計算＋パネル・スランプ**（`_ART_NARABI_BANMAP_STORES`）／
**初代ヴァルヴレイヴの `vvv` 紐づけ・ヴァルヴレイヴ2の `vvv2` 紐づけ**／
**マイジャグVの WordPress 5分割**（`_ART_WP_SPLIT_NARROW_STORES` / `_ART_WP_MIN_KEEP_W = 752`）。

### O. 対象外（従来仕様を維持）

**他店舗の記事用（高田馬場・渋谷新館・秋葉原）／ 新宿歌舞伎町の通常ページ（`auto`）／
かぶぱ（`auto_slump`）／ `auto_slump2` ／ ローテ（`rote`）／ 単体スランプページ
（`show_slump_graph_page`）／ 📝記入部分のみ（`_composite_slump_onto_images` 経由）。**

**WordPress 本文・画像分割・fullwidth・nosplit ／ 抽出条件 ／ 台番 ／ ファイル名 ／ ban_map ／
結果テキスト ／ 表の機種名 ／ パネル画像内の機種名 ／ 記事見出しの機種名**も**対象外で削除しない**。

### P. 確認結果

**純粋テスト**：`c1c3bdd` 時点 ／ `56844fe` **614 PASS / 0 FAIL** ／ `cc695d4` **394 PASS / 0 FAIL**。

- **ゲート網羅**：13店舗 × 12ページ＝156通りで ON は1通りだけ。
- **全11カテゴリ**で上部の文字画素0、かつ **HEAD版の「名前を渡さない」基準と画素完全一致**、
  同時に **HEAD版とは差が出る**（＝元は名前が出ていた）ことも確認。
- **`machine_name` の有無で結果が変わらない**（下部も消えている）。
- 台番・縦軸・目盛文字・補助線・赤い折れ線・右下の青い差枚数・区切り線が**残存**。
- **カードサイズ 388×472 不変**、`out_scale=2.0` でも 776×944、
  帯・外枠の座標定数（`_SL_HDR1` / `_SL_HDR2` / `_SL_SEP1` / `_SL_SEP2` / `_SL_FRAME_PAD`）が不変。
- **`show_diff=False`**（全台系のマイナス台）でも上部だけ消え、台番・サイズは従来どおり。
- **最外周は内側4pxが黒・外側6pxが薄紫**、内部罫線は従来どおり。
- **⑦・🔄・⑧の一致**：3経路は同一関数・同一ゲート。呼び出し数と条件式は HEAD と同数。
- **対象外の非回帰**：他店舗の記事用・`auto`・`auto_slump`・`auto_slump2`・`rote`・`slump_graph`・
  `work` などで、`machine_name` の有無 × `show_diff` の4組合せ ＋ `out_scale=2.0` が
  **HEAD と画素完全一致**。`_attach_slump_to_table(_side)` / `_apply_panel_to_table_img` /
  `draw_table_image` / `_art_high_title_bar` / `_build_col_items` / `_art_narabi_items` /
  `_composite_slump_onto_images` / `show_auto_page` / `show_rote_page` /
  `show_slump_graph_page` ほか **49関数が AST 一致**。
- **`cc695d4` で本体が変わった関数は `draw_slump_graph` だけ**（新規・消失関数0・
  `show_auto_article_page` も不変）。

**実機**：ローカル ⑦プレビューで確認後、**2026-09-17 にユーザーが Streamlit Cloud 実機で
「新宿歌舞伎町の記事用のスランプカード・表見出しの見た目変更がすべて問題なく表示される」と
正式承認**。白地・黒罫線・細い最外周線・右下の青い差枚数・カード内機種名なし・
表見出しの黒地／白文字が**新宿歌舞伎町の記事用だけで正常表示**されることを確認済み。

### Q. 今後の禁止事項

1. **記事用のスランプカードを黒地へ戻さない**（`_ART_SL_CARD_PAGES` / `_ART_SL_CARD_STORES` を外さない）
2. **カード内へ機種名（上部・下部）を復活させない**
3. **機種名を消したことを理由にカードを詰めない／台番を上へ移動しない／
   ヘッダー1帯・区切り線を消さない／カードサイズ 388×472・グラフ座標・合成位置を変更しない**
4. **差枚数を中央寄せ・黄色・100%サイズへ戻さない／`C_PLUS` 以外の新しい青定数を作らない**
5. **差枚数の白縁取りを外さない**（終端 −2,800枚以下で赤線と重なる）／**赤い折れ線を消さない**
6. **`_ART_SL_DIFF_PAD = 8` を変更しない**（下端位置が従来からずれる）
7. **最外周の細線化（`_ART_SL_OUTER_RATIO = 0.4`）を巻き戻さない／
   カード内部の区切り線・グラフ枠・軸・0ライン・補助線・目盛線を細くしない**
8. **外側6pxを `C_ART_SLUMP_AREA_BG` 以外の色で塗らない／別定数へコピーしない**
9. **`_ART_SL_TMPL_CACHE` を `_SL_TMPL_CACHE` と統合しない**
10. **`_art_slump_card_new()` を保存フラグ方式へ戻さない／店舗名だけの判定にしない**
11. **呼び出し側（⑦ / 🔄 / ⑧）へ `_sl_art` 分岐を追加しない／
    `_show_mn_*` / `_osu_multi_*` / `display_name` / `machine_name` の条件式を変更しない**
12. **②個別「全台」へ ban_map 登録・スランプ合成を追加しない／
    差枚数ランキング・全台データ・島図・ポスターへスランプを付けない**
13. **表見出しの罫線を白にしない／本文セル・差枚色・列幅・表高さ・タイトルバー・サマリーを変更しない**
14. **`convert_narabi_pil.py` の `ART_HEADER` 既定 `False` を変更しない／`THEME_NEW` を流用しない／
    ⑦だけ・⑧だけ直さない**
15. **`base_3000_bk.png` / `bbb.jpg` / `_slump_template_image()` / 機種画像マスタ /
    パネル素材 / フォント素材を変更しない**
16. **N の既存正式仕様（パネルあり・液晶なし・島図なし・Noto Sans JP Black・
    高配分の水色バー削除・薄紫背景・`77e140d`・`vvv` 紐づけ・マイジャグV5分割）を壊さない**
17. **他店舗の記事用・`auto`・`auto_slump`・`auto_slump2`・ローテ・単体スランプ・
    📝記入部分のみへ波及させない**
18. **WordPress 本文・画像分割・fullwidth・nosplit・抽出条件・台番・ファイル名・ban_map・
    結果テキスト・表の機種名・パネル内の機種名・記事見出しの機種名を変更しない**
19. **`c1c3bdd` / `56844fe` / `cc695d4` へ reset・revert しない／
    `56844fe` の commit メッセージ先頭の `@` を理由に履歴を書き換えない**
20. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：⑤「10日間オススメポスター」最優先・その他との重複排除・結果テキストの同一見出し統合（2026-09-17・`51dde3a` / `b5d0f73` / `eacc532`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用⑤だけ**。
2026-09-17 に **ユーザーがローカルおよび Streamlit Cloud の実機で確認し承認**した。

既存の記事用・⑤オススメ・結果テキスト関連セクション（`d121e54` / `77e140d` / `31f7346` /
`61851ca` / `e53a116` / `c1c3bdd` / `56844fe` / `cc695d4` / `252a39b` / `4b72428` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**2026-09-17 の正式仕様として末尾へ追加**する。

### A. 正式実装commit（3本でひとつの仕様を構成）

| # | commit | 内容 |
|---|---|---|
| ① | **`51dde3ab30c01d809b76dae81bc1853f0c94cf38`** | `feat: 新宿歌舞伎町記事用で⑤オススメ機種を最優先にする` |
| ② | **`b5d0f736bce8a466395856a250062a5d5b6f916d`** | `fix: 新宿歌舞伎町記事用の⑤重複を解消し結果テキストへ追加` |
| ③ | **`eacc532d69bf65be8f0412be19fc8fe216b40f35`** | `fix: 新宿歌舞伎町記事用の⑤結果テキスト見出しを1回にまとめる` |

**3本とも変更ファイルは `streamlit_app.py` の1ファイルだけ。**
**いずれも「正式仕様の根拠となる実装commit」であって、HEAD をここへ戻すという意味ではない。
`51dde3a` / `b5d0f73` / `eacc532` へ reset・revert してはならない。**

なお ① と ② の間にある **`db659aa`（`auto: 画像生成後の設定を保存`）はアプリの `_git_auto_push()` による
有効な自動commit**（`article_page_inputs.json`）であり、**reset・revert・再commitしない。**

### B. 対象範囲

**新宿歌舞伎町 × `page=auto_article` の⑤「オススメ機種の優秀台」だけ。**
⑤ブロックタイトルが **「10日間オススメポスター」** の場合を含む。

**対象外**：他店舗の記事用（高田馬場・渋谷新館・秋葉原）／ 通常結果ポスト（`auto`）／
かぶぱ（`auto_slump`）／ `auto_slump2` ／ ローテ（`rote`）／ 作業用（`work`）。

### C. ⑤優先（`51dde3a`）

- 新宿歌舞伎町の記事用では、**⑤へ入力した機種を最優先**にする。
- **⑤入力機種は、記事用の自動全台系・自動高配分より⑤へ掲載する。**
- **高配分・全台系と⑤への二重掲載をしない。**
- **⑤入力機種をハードコードしない。**既存の⑤入力値（`store_settings/{store}.json` の
  `art_osusume_machines`）を正とし、**将来機種を追加しても同じ扱い**になる。
- 2026-09-16 の代表例：**東京喰種とカバネリ海門決戦を⑤へ掲載し、
  カバネリ海門決戦の高配分画像は出さない。**
- **⑤の抽出条件（例：+1,000枚以上）と、⑤画像が実際に採用した掲載台番を正**とする。

### D. ★`_art_prec` だけでは全台系を抑制できない（実装上の要点）

`recommended_machines`（＝`_art_prec`）は自動高配分・ジャグラー統合・その他へは効くが、
**`run_step1_main()`（自動全台系）は `recommended_machines` を受け取らない**。

そのため⑤優先機種は **`recommended_machines` と `kojin_zentai_machines` の両方へ union** する。

```python
_ART_OSU_PRIORITY_STORES: "frozenset[str]" = frozenset({"新宿歌舞伎町"})

def _art_osu_priority_machines(store: str, machines) -> set[str]:
    """⑤を最優先にする店舗の「⑤へ入力済みの機種名」集合（対象外の店舗は空集合）。"""
    if store not in _ART_OSU_PRIORITY_STORES:
        return set()
    return {str(m).strip() for m in (machines or []) if str(m or "").strip()}
```

```python
_art_osu_prio = _art_osu_priority_machines(store, art_osusume_machines)
_art_prec |= _art_osu_prio                     # 自動高配分・ジャグラー統合・その他を抑制
...
kojin_zentai_machines=(... | _art_osu_prio),   # 自動全台系（Step1）を候補段階から除外
```

**⑦フルプレビュー／📝記入部分のみ／⑧本番の3経路すべてで同じ集合を渡す。
片側だけの変更にしてはならない。**
**生成後の画像削除・機種名の再変換・新しい抽出ロジックは作らない**（既存の②個別優先と同じ抑制機構を再利用）。

### E. その他の優秀台との重複排除（`b5d0f73`）

- **⑤入力機種は「その他の優秀台ピックアップ」から機種単位で除外する。**
- **台番単位にしない。**理由：**⑤とその他の閾値が将来異なっても、⑦／📝／🔄／⑧の結果を一致させるため。**
- **⑤以外の機種・台番はその他の優秀台へ従来どおり掲載する。**
- **⑦フルプレビュー／📝記入部分のみ／🔄その他を更新／⑧本番のすべてで⑤機種はその他に出さない。**

実装は⑦／📝の自動抽出で使う既存の機種単位除外集合へ union するだけ。

```python
_exc_mac_a = {m.strip() for m in (kojin_zentai_machines + kojin_yushu_machines) if m.strip()}
_exc_mac_a |= _art_osu_prio
```

**★原因の切り分け（誤認しないこと）**：⑧・🔄は pipeline が `recommended_machines` で
既に除外済みで**重複していなかった**。重複していたのは **⑦／📝だけ**で、
`art_sonota_extra_auto='+1,000枚以上'` により `_manual_sonota_auto_extract()` が
pipeline 版のその他を差し替えており、その `_exc_mac_a` に⑤機種が入っていなかったことが原因。

**代表実測（2026-09-16・749台）**：⑤へ **東京喰種13台・カバネリ海門決戦9台**を掲載。
⑦／📝のその他は **94台 → 77台**（減17台＝すべて⑤機種／**増0台**）、
**⑤ ∩ その他 = 0台**、⑤以外の台は修正前と完全一致。

### F. 結果テキストへ⑤を追加（`b5d0f73`）

- 新宿歌舞伎町の記事用⑧の結果テキストへ**⑤の優秀台を追加する。**
- 挿入位置は **`👑その他の優秀台` の直前**（既存 `insert_formatted_result_before_other_picks()` を使用）。
- **台番・差枚数は⑤画像が実際に掲載した台番集合（`_art_osu_bans_e`）を正**とし、**画像と完全一致**させる。
  ブロックの抽出条件が変わっても画像とズレない。
- 表記は**既存の新小岩スランプ付き結果ポストの流儀をそのまま再利用**する
  （`generate_recommended_result_text()`。**新しい独自書式を作らない**）。

| 項目 | 正式 |
|---|---|
| 機種名の先頭 | **`・`** |
| 台行 | **`【○○番台】+○,○○○枚`** |
| 並び | **台番昇順** |
| 機種間 | **空行1つ** |

- **空ブロック（掲載0台を含む）は見出し・機種名・空行のいずれも出さない。**
- **⑤優先機種は全台系・高配分・その他の結果テキストへ重複表示しない。**

呼び出しは⑧本番の1か所だけで、`_art_osu_prio_e and _art_osu_bans_e` のゲート内側に置く。

### G. 同一タイトルの統合は結果テキストだけ（`eacc532`）

- **結果テキストだけ、同じ⑤ブロックタイトルは見出しを1回にまとめる。**
- 例：ブロック1・2がともに「10日間オススメポスター」のとき、
  **`👑10日間オススメポスターの優秀台` は1回だけ**表示し、その下へ
  **ブロック順で 東京喰種 → カバネリ海門決戦** を並べる。

実装は `generate_recommended_result_text()` へ任意引数
**`merge_same_title: bool = False`（既定＝従来動作）** を追加し、
`_merged_idx: dict[str, int]` で**同じ見出し行の2ブロック目以降は見出しを繰り返さず、
既存セクションの末尾へ機種ブロックだけを追記**する。

```python
_body = header_line + "\n" + "\n\n".join(machine_parts)
if merge_same_title and header_line in _merged_idx:
    sections[_merged_idx[header_line]] += "\n\n" + "\n\n".join(machine_parts)
else:
    if merge_same_title:
        _merged_idx[header_line] = len(sections)
    sections.append(_body)
```

- **`merge_same_title=True` を渡すのは新宿歌舞伎町記事用の⑤呼び出し1か所だけ。**
  **新小岩を含む既存呼び出しは引数省略のままで出力完全一致。**
- **★タイトル文字列の全体置換・後処理での見出し削除は禁止。**

### H. ★WordPress本文のH3は各ブロックのまま（統合しない）

**今回まとめるのは結果テキストだけ。**WordPress 本文は従来どおり：

| | 個数 |
|---|---|
| **H2「オススメ機種の優秀台」** | **1つ** |
| **H3「10日間オススメポスター」** | **ブロック1・2で2つ** |
| ⑤画像ブロック | 2つ |

**`wp_client.py` は今回いっさい変更していない（diff 0）。**
**WordPress本文のH3を今回の理由で1つに統合してはならない。**

### I. 実装上の維持事項

- ⑤優先対象は **既存 `_art_osu_priority_machines()` と⑤入力値**を使う。
- ⑦／📝のその他自動抽出は **既存 `_exc_mac_a` へ⑤優先機種集合を加える**だけ。
- **結果テキスト生成の既定動作は従来どおり**で、**新宿歌舞伎町記事用の⑤呼び出しだけ**が
  同一タイトル統合を使う。
- **`generate_report_text()` の既存書式・一般ロジックは変更しない。**
- 次はすべて**維持**する：
  **高配分判定条件 ／ 全台系判定条件 ／ 並び ／ 列 ／ 末尾 ／ バラエティ ／
  ジャグラーシリーズ優秀台 ／ WordPress送信先・カテゴリ28・投稿者2択（`i.sasaki` / `m.takahashi`）／
  実在画像だけ本文へ載せる仕様 ／ 分割・nosplit・fullwidth ／ マイジャグV5分割。**

### J. 確認済み内容

- **ローカル実機確認済み**（2026-09-16 の確定データ 749台で⑧を実行）。
- **Cloud 実機確認済み**（2026-09-17・ユーザー承認）。
- 確認できた内容：**⑤画像（東京喰種13台・カバネリ海門決戦9台）／ その他との重複0台 ／
  結果テキストの台番・差枚数が⑤画像と完全一致 ／ `👑10日間オススメポスターの優秀台` が1回だけ ／
  `👑その他の優秀台` の直前に挿入 ／ `👑その他の優秀台` に⑤機種0件。**
- **WordPress本文のH3構成は不変**（H2=1 / H3=2 / ⑤画像2）。

**★WordPress通信について（推測で書かないこと）**：
この3commitの実装・検証中に行った WordPress 関連の処理は
**`wp_client.plan_blocks()` のローカル呼び出しだけ**であり、
**HTTP通信（GET / POST / PUT / PATCH / DELETE）・メディアアップロード・下書き作成・公開は
いずれも0件**である。**「送信済み」「下書きを作成した」等と記録してはならない。**

### K. 変更範囲（機械確認）

- **3commit とも `streamlit_app.py` のみ。**
- **新規関数は `_art_osu_priority_machines()` の1つだけ・消失関数0。**
- `eacc532` 時点で本体が変わった関数は
  **`generate_recommended_result_text()` と `show_auto_article_page()` の2つだけ**。
- `generate_report_text` / `run_auto_pipeline` / `run_step1_main` / `run_step2_juggler` /
  `run_step3_other` / `filter_recommended_machines` / `_art_osusume_block_images` /
  `_manual_sonota_auto_extract` / `insert_formatted_result_before_other_picks` /
  `_build_kabupa_result_text` / `show_auto_page` / `show_rote_page` ほかは**すべて AST 一致**。
- **`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` は無変更。**

### L. 今後の禁止事項

1. **⑤入力機種をハードコードしない**（`store_settings` の⑤入力値を正とする）
2. **⑤機種を高配分・全台系・その他へ二重掲載しない**
3. **`_art_prec` だけにして `kojin_zentai_machines` への union を外さない**（自動全台系が復活する）
4. **⑦／📝／⑧のいずれか1経路だけ変更しない**
5. **その他からの除外を台番単位へ変えない**（機種単位を維持）
6. **結果テキストの見出しを文字列の後処理で削除しない**
7. **`merge_same_title` の既定 `False` を変更しない**（新小岩ほか既存呼び出しが壊れる）
8. **WordPress本文のH3を今回の理由で1つに統合しない／`wp_client.py` を変更しない**
9. **結果テキストの台番・差枚を⑤画像以外から作らない**（`bans_by_block` を外さない）
10. **空ブロックで見出し・機種名・空行を出さない**
11. **新小岩・渋谷新館・高田馬場など他店舗の結果テキストや⑤仕様を変更しない**
12. **既存画像仕様・WordPress仕様・保存キーを変更しない**
13. **`generate_report_text()` の既存書式・一般ロジックを変更しない**
14. **`51dde3a` / `b5d0f73` / `eacc532` / `db659aa` へ reset・revert しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：①冒頭のギルドポストXリンク削除・ピンクバー内文字の中央寄せ（2026-09-18・`9f0f363`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用だけ**。
2026-09-18 に **ユーザーが Streamlit Cloud 実機で確認し承認**した。

既存の記事用・ピンクバー関連セクション（`77e140d` / `31f7346` / `5c5c1f2` / `e53a116` /
`61851ca` / `c1c3bdd` / `56844fe` / `cc695d4` / `51dde3a` / `b5d0f73` / `eacc532` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**2026-09-18 の正式仕様として末尾へ追加**する。

### A. 正式実装commit

| | commit |
|---|---|
| **正式** | **`9f0f363c532e7cc25adcca7c81b80d979853a0fc`**（`fix: 新宿歌舞伎町記事用のギルドX削除とピンクバー中央寄せ`） |

**変更ファイルは `streamlit_app.py`（+90/−7）と `convert_narabi_pil.py`（+22/−2）の2つだけ。**
**`wp_client.py` は diff 0。**
**`9f0f363` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。
`9f0f363` へ reset・revert してはならない。**

### B. 対象範囲

**`auto_article × 新宿歌舞伎町` の1通りだけ。**

**対象外（従来仕様を維持）**：他店舗の記事用（高田馬場・渋谷新館・秋葉原）／
通常結果ポスト（`auto`）／かぶぱ（`auto_slump`）／`auto_slump2` ／ローテ（`rote`）／
作業用（`work`）。

判定は **`_ART_NO_TOP_X_STORES`（①冒頭）**と
**`_ART_SUM_CENTER_PAGES` × `_ART_SUM_CENTER_STORES`（ピンクバー）**の2ゲート。
`_art_summary_center()` は `_art_font_new()` / `_art_slump_card_new()` /
`_art_table_header_new()` と同じ **page × store の AND** で毎回導出し、保存フラグを持たない。
**Streamlit 外（純粋テスト・subprocess）では False＝従来の左寄せ。**
**12ページ × 13店舗＝156通りで ON は1通りだけ**であることを機械確認済み。

---

## 1. ①冒頭のギルドポストXリンク削除

### C. 削除するもの

新宿歌舞伎町の記事用①冒頭から、次の2項目を**表示・新規保存・WordPress本文出力のいずれもしない**。

- **ギルドポスト Xリンク（空欄・不正URLなら埋め込みません）**
- **Xリンク下の文章（改行で段落／空欄なら出力しません）**

あわせて、この分岐の caption（「自動で埋め込まれます」「空段落3行へ手で貼り付け」）も出さない。

### D. 維持するもの

**その日の見出し ／ ポスター画像 ／ ポスター下の文章 ／
かぶぱポストのXリンク・ヒント1〜10 ／ WordPress投稿者UI（2択）。**

### E. ★`_ART_GUILD_X_STORES` から新宿歌舞伎町を外してはならない（最重要）

`wp_client.plan_blocks()` は

```python
_has_guild_key = "guild_x" in payload
...
if _has_guild_key:
    if _guild_x: plan.append({"type": "embed_x", "url": _guild_x})
else:
    for _ in range(X_EMPTY_PARAS):      # ← キーが無い店舗は手貼り用の空段落×3
        plan.append({"type": "empty_para"})
```

という既存仕様なので、**payload から `guild_x` キー自体を落とすと空段落3行が復活する。**

**正しくは「キーは残したまま値を `""` 固定」**し、
「キーあり・空欄＝何も出さない」既存経路を使う。**`wp_client.py` は変更しない。**

```python
_ART_GUILD_X_STORES  = frozenset({"渋谷新館", "新宿歌舞伎町"})   # 変更しない
_ART_NO_TOP_X_STORES = frozenset({"新宿歌舞伎町"})               # 今回追加
```

### F. payload の固定（出力抑止の正）

```python
_art_wp_pl["top_text_x"] = ("" if store in _ART_NO_TOP_X_STORES
                            else st.session_state.get(f"art_wp_top_text_x_{store}", ""))
if store in _ART_GUILD_X_STORES:
    _art_wp_pl["guild_x"] = ("" if store in _ART_NO_TOP_X_STORES
                             else st.session_state.get(f"art_guild_x_url_{store}", ""))
```

- **`top_text_x` も `""` 固定**する。
- **★`_restore_article_inputs()` は `saved.items()` の全キーを session_state へ戻す**
  （`_article_input_keys()` の外のキーも入る）。したがって
  **`_article_input_keys()` から外すだけでは過去の保存値が payload へ拾われ得る。
  出力抑止の正は payload 側の `""` 固定である。**
- これにより、過去の `article_page_inputs.json` に旧保存値が残っていて session_state へ
  復元されても、**WordPress本文へ出ない。**

### G. 既存JSONは削除・一括変更しない

`_article_input_keys()` は対象店舗でのみ該当2キーを**新規保存の対象から外す**だけ。

```python
if store in _ART_NO_TOP_X_STORES:
    _no_x = {f"art_wp_top_text_x_{store}", f"art_guild_x_url_{store}"}
    keys = [k for k in keys if k not in _no_x]
```

- `_save_article_inputs()` は**マージ保存**なので、**既存JSONの値は削除も変更もされない**。
- **非対象店舗の keys は順序まで従来と完全に同一**（12店舗で機械確認済み）。
- **`article_page_inputs.json` を編集・一括変更しない。**

### H. 他店舗の非回帰（実UI＋純粋テストで確認済み）

| 店舗 | ①冒頭 |
|---|---|
| **渋谷新館** | **ギルドX入力・Xリンク下文章・「自動で埋め込まれます」caption すべてあり**。payload・本文計画が HEAD と完全一致、`embed_x` 1件・Xリンク下文章の para あり |
| **高田馬場** | 2カラムUI・Xリンク下文章あり・**空段落3行 caption あり**、本文の `empty_para` **3件で不変** |
| **秋葉原** | 同上（`empty_para` 3件・HEAD一致） |

**`X_EMPTY_PARAS = 3` は変更しない。**

---

## 2. 表画像 最下段ピンクバー内文字の中央寄せ

### I. 正式仕様

新宿歌舞伎町の記事用だけ、**表画像最下段のピンクバー内の文字をバー幅の中央へ配置する。**

### J. 対象（実際にピンクバーを持つものだけ）

- **並び**
- **列（列仕掛け）**
- **②個別の並び台番範囲①（ピンクバーあり）など、既存 `_build_machine_img()` が
  `summary_stat` を受け取ってピンクバーを描く画像**

### K. 対象外（ピンクバーが無い画像へ新規追加しない）

**全台系（白サマリー）／ 高配分 ／ ②全台・②優秀台・②個別ピック ／
ジャグラーシリーズ優秀台 ／ その他の優秀台 ／ 末尾 ／ ⑤オススメ ／
差枚数ランキング ／ 全台データ ／ 島図。**

述語ONでもこれらは **HEAD と画素完全一致・ピンクバーの新規追加0** であることを機械確認済み。

### L. 変更してよいのは開始X座標だけ

**ピンクバーの色 ／ 高さ ／ 枠線 ／ 文字内容 ／ 文字サイズ ／ 書体 ／
既存 `GAP_SUM` のカーニング ／ 表本体 ／ パネル ／ スランプ ／ 白地カード ／
表見出しの黒地・白文字 は一切変更しない。**

左寄せから中央寄せへ変わるのは **対象ピンクバー内の文字の開始X座標だけ**。
**左端余白 8px（×hq）を最低値として維持する**（長文で右へはみ出さない）。

```python
_pad_sum = round(8 * _hq)
if _art_summary_center():
    _bb2c = pd_.textbbox((0, 0), part2, font=font_sum)
    _tw_sum = ((bb1[2]-bb1[0]) + round(GAP_SUM * _hq) + (_bb2c[2]-_bb2c[0]))
    _pad_sum = max(_pad_sum, (w - _tw_sum) // 2)
```

下流の `x2 = _pad_sum + (bb1[2]-bb1[0]) + round(GAP_SUM * _hq)` が追従するので、
**part1 と part2 の相対位置（文字間隔）は変わらない。**

**実測**：文字ビットマップは OFF と完全一致し、**開始Xだけが平行移動**する
（並び 16→281px ／ 列 16→263px ／ ②台番範囲① 8→157px）。

### M. 実インクの左右差について（誤記しないこと）

中央計算は **`textbbox` の span（part1 ＋ GAP_SUM ＋ part2）** で行う。
PIL の `textbbox` は末尾グリフの advance を含むため、
**末尾「）」の右サイドベアリングぶん（バー幅の1〜2%程度）だけ右に余りが出る。**
これは HEAD の左寄せ実装と同じ計測値を使っていることの帰結で、**⑦と⑧で同一**。
**「ピクセル単位で完全対称」ではないことを不具合として扱わない。**

---

## 3. ⑦プレビューと⑧本番の一致

### N. 2経路

| 経路 | 描画 |
|---|---|
| **⑦プレビュー（および②台番範囲①は⑧も）** | アプリ内 `_build_machine_img()` → `_art_summary_center()` |
| **⑧本番の並び・列** | **`convert_narabi_pil.py` の subprocess** → `ART_SUM_CENTER` |

**⑦だけ・⑧だけ直してはならない。**

### O. `convert_narabi_pil.py`

```python
ART_SUM_CENTER = False   # 既定＝従来の左寄せ
...
sum_x0 = 8
if ART_SUM_CENTER:
    _bb2c = _textbbox(draw_pink, sum_part2, font_sum)
    _tw_sum = (bb1[2] - bb1[0]) + GAP_SUM + (_bb2c[2] - _bb2c[0])
    sum_x0 = max(8, (w - _tw_sum) // 2)
draw_pink.text((sum_x0, y_text), sum_part1, ...)
x2  = sum_x0 + (bb1[2] - bb1[0]) + GAP_SUM
```

- **既定 `False` を変更しない**（通常ページ・他店舗・ローテ・かぶぱが壊れる）。
- `SUMMARY_BG` / `row_h_sum` / `font_sum` / `GAP_SUM` / `pink_rgba` は**再定義しない**。
- **関数本体の変更は0**（ピンクバーはトップレベルの生成ループ内）。

### P. `_patch_and_run_narabi()`

`ART_HEADER` / `FONT_OVERRIDE` / `NO_BAR` / `HQ_SCALE` と**同じ regex パッチ方式**で
`art_sum_center: bool = False` を追加し、**記事用⑧の呼び出し1箇所だけ**へ
`art_sum_center=_art_summary_center()` を渡す。

**通常ページ（`show_auto_page` の呼び出し）・他店舗・ローテは引数を渡さず既定 False のまま。**
**実測：`art_sum_center=False` でも、引数を渡さない既定呼び出しでも、
生成JPEGが HEAD と SHA256 完全一致。**

### Q. ⑦⑧一致の実測

同一データで **⑦の文字中心 0.4914 ／ ⑧の文字中心 0.4930（幅比・差0.16%）**。
ピンクバーより上（表・見出し・パネル）は⑦⑧とも **OFF と画素完全一致**、画像サイズも不変。

---

## 4. 維持する既存仕様（今回いっさい変更していない）

**新宿歌舞伎町 記事用**：パネルあり ／ **液晶なし** ／ **島図なし** ／
**Noto Sans JP Black**（`_ART_FONT_STORES`）。

**スランプカード**：白地カード ／ **上部の機種名あり** ／ **下部の機種名なし** ／
**右下の青い差枚数** ／ **薄紫のカード外側背景**（`C_ART_SLUMP_AREA_BG`）。

**表・画像**：**高配分の水色バーなし**（`_ART_HIGH_NO_BAR_STORES`）／
**その他の優秀台の濃紺タイトルバーなし**（`_art_sonota_no_bar`）／
表見出しの黒地・白文字（`_art_table_header_new()` / `ART_HEADER`）。

**本文**：**かぶぱポスト表記**（`nanako_texts()`）／
**⑤最優先・その他との重複排除・結果テキストの⑤見出し統合**
（`_art_osu_priority_machines` / `merge_same_title`）。

**WordPress**：**新サイト送信先** ／ **カテゴリ28** ／ **投稿者2択（`i.sasaki` / `m.takahashi`）** ／
**実在画像だけ本文へ載せる** ／ **分割・nosplit・fullwidth・マイジャグV5分割**
（`_ART_WP_NOSPLIT_STORES` / `_ART_WP_FULLWIDTH_STORES` / `_ART_WP_SPLIT_NARROW_STORES` /
`_ART_WP_MIN_KEEP_W = 752`）。

**`77e140d` の並び・列 ban_map 再計算（⑦未実行でも⑧でパネル・スランプが付く）** も維持。

---

## 5. 検証結果

**純粋テスト 168 PASS / 0 FAIL**（ギルドX削除・ゲート網羅・keys・payload・本文計画・
ピンクバー画素・subprocess・静的確認）。

- **変更関数は `_article_input_keys` / `_build_machine_img` / `_patch_and_run_narabi` /
  `show_auto_article_page` の4つだけ。新規関数は `_art_summary_center` の1つだけ。消失0。**
- `draw_table_image` / `_build_article_machine_img` / `_build_machine_img_no_bar` /
  `_art_high_title_bar` / `_attach_slump_to_table(_side)` / `_build_sue_images` /
  `_art_osusume_block_images` / `_art_ranking_image` / `_art_zendai_image` /
  `show_auto_page` / `show_rote_page` / `show_work_page` / `_save_article_inputs` /
  `_restore_article_inputs` / `_art_widget_key` / `generate_report_text` /
  `run_step1_main` / `run_step2_juggler` / `run_step3_other` / `run_auto_pipeline` /
  `generate_rote_image` / `_art_narabi_items` / `_build_col_items` /
  `_apply_panel_to_table_img` / `draw_slump_graph` / `_paste_slump_area_bg` /
  `_art_slump_bg` ── **すべて AST 一致**
- **`wp_client.py` / `shimazu_renderer.py` の差分0**、`article_page_inputs.json` の差分0
- `git diff --check` クリーン

### R. Cloud 確認済み（2026-09-18・ユーザー承認）

- 新宿歌舞伎町の①冒頭で**ギルドポスト Xリンク・Xリンク下の文章が出ない**
- **ポスター下の文章・かぶぱポスト・ヒント・投稿者2択が残る**
- **並び・列・②台番範囲①のピンクバー文字が中央寄せ**
- **⑦と⑧が同じ見た目**
- **対象外の既存仕様（渋谷新館のギルドX、高田馬場・秋葉原の空段落3行、
  パネル・液晶なし・島図なし・フォント・白地カード・水色バーなし・WordPress仕様）が維持**

---

## 6. 今後の禁止事項

1. **`_ART_GUILD_X_STORES` から新宿歌舞伎町を外さない**（空段落3行が復活する）
2. **payload から `guild_x` キーを落とさない**（値の `""` 固定で抑止する）
3. **`top_text_x` の `""` 固定を外さない**
4. **`_article_input_keys()` から外すだけで済ませない**（payload 固定が出力抑止の正）
5. **`article_page_inputs.json` の既存値を削除・一括変更しない**
6. **`wp_client.py` を変更しない／`X_EMPTY_PARAS = 3` を変えない**
7. **渋谷新館のギルドX・Xリンク下文章、高田馬場・秋葉原の空段落3行を変えない**
8. **新宿歌舞伎町の①冒頭から「ポスター下の文章」「その日の見出し」
   「かぶぱポストのXリンク・ヒント1〜10」「WordPress投稿者UI」を消さない**
9. **ピンクバーが無い画像へピンクバーを新規追加しない**
10. **ピンクバーの色・高さ・枠線・文字内容・文字サイズ・書体・`GAP_SUM`・表本体・
    パネル・スランプ・白地カード・表見出しを変更しない**（変えるのは開始Xだけ）
11. **左端余白 8px（×hq）の最低値を外さない**
12. **実インクの左右差（末尾「）」の右サイドベアリング由来）を不具合として扱わない**
13. **⑦だけ・⑧だけ直さない**（`_art_summary_center()` と `ART_SUM_CENTER` はセット）
14. **`convert_narabi_pil.py` の `ART_SUM_CENTER` 既定 `False` を変更しない**
15. **`_patch_and_run_narabi()` の `art_sum_center` 既定 `False` を変更しない／
    記事用⑧以外の呼び出しへ渡さない**
16. **`_art_summary_center()` を保存フラグ方式へ戻さない／店舗名だけの判定にしない**
17. **他店舗の記事用・通常ページ・かぶぱ・`auto_slump2`・ローテ・作業用へ波及させない**
18. **「4. 維持する既存仕様」を今回を理由に変更しない**
19. **`9f0f363` へ reset・revert しない**
20. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：①ポスターをWordPressメディア22択から選ぶ（2026-09-18・`92ac8af` / `ee39cd7`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用①「新しいポスターを追加」だけ**。
2026-09-18 に **Cloud 実機で「7のつく日」を含む画像の取得・プレビュー成功を確認済み**。

既存の記事用セクション（`77e140d` / `31f7346` / `5c5c1f2` / `e53a116` / `61851ca` /
`c1c3bdd` / `56844fe` / `cc695d4` / `51dde3a` / `b5d0f73` / `eacc532` / `9f0f363` ほか）は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節は**2026-09-18 の正式仕様として末尾へ追加**する。

### A. 正式実装commit（2本でひとつの仕様を構成）

| # | commit | 内容 |
|---|---|---|
| ① | **`92ac8af4383906cc1d99c6fc624cb4adcc8498f9`** | `feat: 新宿歌舞伎町記事用のポスターをWordPressメディア22択から選べるようにする` |
| ② | **`ee39cd71f826dc320557b93b246e08cce2338349`** | `fix: 新宿歌舞伎町記事用ポスター取得の失敗キャッシュを解消`（失敗を非キャッシュ化・安全な失敗表示・Secrets状態表示・選択中IDだけの「🔄 再取得」） |

**どちらも「正式仕様の根拠となる実装commit」であって、HEAD をここへ戻すという意味ではない。
`92ac8af` / `ee39cd7` へ reset・revert してはならない。**

### B. 対象範囲

**`auto_article × 新宿歌舞伎町` の1通りだけ。**
判定は **`_ART_POSTER_PICK_PAGES`（`auto_article`）× `_ART_POSTER_PICK_STORES`（新宿歌舞伎町）** の AND。

**対象外（従来どおり手動アップロードUIとポスター処理を完全維持）**：
他店舗の記事用（高田馬場・渋谷新館・秋葉原）／ 通常結果ポスト（`auto`）／
かぶぱ（`auto_slump`）／ `auto_slump2` ／ ローテ（`rote`）／ 作業用（`work`）。

### C. 正式な22択（表示名 → WordPressメディアID）

**`_ART_POSTER_LIBRARY` の対応表をそのまま使う。実行時に名前・ファイル名で検索しない。IDを推測しない。**

| 表示名 | ID | 表示名 | ID |
|---|---|---|---|
| 1日 | **21** | 4のつく日 | **23** |
| 2日 | **22** | 5のつく日 | **24** |
| **6日** | **26** | 6のつく日 | **25** |
| 12日 | **30** | 7のつく日 | **27** |
| 21日 | **31** | 8のつく日 | **28** |
| 23日 | **32** | 0のつく日 | **20** |
| 24日 | **33** | 39の日 | **35** |
| 29日 | **34** | ゾロ目の日 | **37** |
| 強ゾロの日 | **39** | 月末 | **40** |
| 土曜日 | **41** | 日曜日 | **42** |
| キングぱないなー | **36** | **はぐれキングぱないなー** | **38** |

**★重要**

- **「6日」は ID26。ID44（`6日-1.jpg`）は使わない**（メディア側に重複2件あり）。
- **「はぐれキングぱないなー」は ID38。**
  メディア側タイトルは「はぐれキングぱないな」（末尾の長音なし）だが、
  **UI表示はユーザー指定どおり長音付き**とする。
- **ID29（10日間ポスター）は選択肢に含めない。**

### D. 選択は最大1件・日付単位保存

- **選択は最大1件。別項目を選ぶと既存の選択を自動で外す。**
- 保存するのは**表示名の文字列だけ**で、**既存 `article_page_inputs.json` へ日付（Excel）単位**で保存する。
  **新しいJSON・新しい保存システムを作らない。**
- **別日へ混入させない。**

### E. ★手動アップロードが最優先（最重要）

**手動アップロード画像が1枚でもある間は、手動画像だけを使う。**

その間は次をすべて行わない。

- WordPressメディア選択のプレビュー表示
- ⑦プレビュー・⑧本番・本文用ポスター生成への受け渡し
- **WordPressメディアのGET通信そのもの**

**保存済みのメディア選択が残っていても読み込まない。**
**2種類を1枚のポスターへ結合しない。**
**手動画像を全削除したら、保存済みのメディア選択が再び有効になる。**

手動画像が無い場合だけ、**選択中のメディア画像をGETして既存のポスター生成経路へ渡す。**

### F. ⑦と⑧は同じ経路

**⑦プレビュー・⑧本番はともに `_art_poster_inputs(store, excel)` を通る。**
**⑦だけ・⑧だけ別経路にしてはならない。**

取得に失敗した場合は、**選択を保持したままプレビュー不可を表示**し、
**⑧では欠けたまま `build_poster()` へ渡さず、古いポスターも使わせない。**

### G. 失敗はキャッシュしない（`ee39cd7`）

- **取得成功だけをキャッシュする。失敗はキャッシュしない。**
  失敗は **`_ArtPosterFetchError`** として送出する（`st.cache_data` は例外をキャッシュしないため、
  **次回 rerun で即時に再試行できる**）。
- **「🔄 再取得」は選択中メディアIDのキャッシュ1件だけを破棄する。
  全キャッシュを `clear()` しない。**

### H. ★安全な失敗表示（機密を出さない）

表示してよいのは次だけ。

- **段階**（`secrets` / `rest` / `src` / `img`）
- **HTTPステータス**
- **例外クラス名**
- **WordPress の安全な code / message**
- **未設定 Secrets のキー名**

**Secrets値 ／ パスワード ／ Authorization ／ 完全URL ／ クエリは、表示もログ出力もしない。**

**Secrets状態表示はキー名のみ**とし、**Kabukicho用3キーが揃わず共通キーへフォールバックしている場合も
安全に判別できる**ようにする。

### I. WordPress通信はGETのみ

この機能が行う WordPress 通信は **新サイトのメディア情報・画像本体の GET だけ**。

**POST / PUT / PATCH / DELETE ／ メディアアップロード ／ 下書きの作成・更新・公開は行わない。**

### J. 維持する既存仕様

新宿歌舞伎町 記事用の既存正式仕様（①冒頭のギルドX削除・ピンクバー中央寄せ（`9f0f363`）／
かぶぱポストのXリンクとヒント1〜10 ／ その日の見出し ／ ポスター下の文章 ／
WordPress投稿者2択 ／ パネルあり・液晶なし・島図なし ／ Noto Sans JP Black ／
白地スランプカード ／ 高配分の水色バーなし ／ ⑤最優先と重複排除 ／
`_ART_WP_NOSPLIT_STORES` / `_ART_WP_FULLWIDTH_STORES` / `_ART_WP_SPLIT_NARROW_STORES` /
`_ART_WP_MIN_KEEP_W = 752`）は**すべて維持**する。

**`build_poster()` / `wp_client.py` の本文生成・分割・fullwidth・nosplit は変更していない。**

### K. 今後の禁止事項

1. **手動アップロード最優先を崩さない**（手動があるときはGET・プレビュー・受け渡しをしない）
2. **手動画像とメディア画像を1枚へ結合しない**
3. **メディアIDを推測しない／実行時に名前・ファイル名で検索しない**
4. **「6日」を ID44 へ変えない／「はぐれキングぱないなー」を ID38 以外にしない／
   ID29（10日間ポスター）を選択肢へ入れない**
5. **選択を複数件にしない／日付単位保存を外さない／別日へ混入させない**
6. **失敗をキャッシュしない**（`_ArtPosterFetchError` の送出を維持）
7. **「🔄 再取得」で全キャッシュを `clear()` しない**
8. **Secrets値・パスワード・Authorization・完全URL・クエリを表示・ログ出力しない**
9. **GET以外のWordPress通信（POST/PUT/PATCH/DELETE・アップロード・下書き作成/更新/公開）を追加しない**
10. **⑦だけ・⑧だけ別経路にしない**（`_art_poster_inputs()` を共用する）
11. **他店舗の記事用・通常ページ・かぶぱ・`auto_slump2`・ローテ・作業用へ波及させない**
12. **「J. 維持する既存仕様」を今回を理由に変更しない**
13. **`92ac8af` / `ee39cd7` へ reset・revert しない**
14. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：①「かぶぱポスト」見出しのXプロフィール案内リンク（2026-09-18・`b6e403c`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の
①冒頭部分「かぶぱポスト」入力欄の案内表示だけ**。
2026-09-18 に **Cloud 実機でリンクが別タブで開くことを確認済み**。

既存の記事用セクション（`77e140d` / `31f7346` / `5c5c1f2` / `e53a116` / `61851ca` /
`c1c3bdd` / `56844fe` / `cc695d4` / `51dde3a` / `b5d0f73` / `eacc532` / `9f0f363` /
`92ac8af` / `ee39cd7` ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。
本節は**2026-09-18 の正式仕様として末尾へ追加**する。

### A. 正式実装commit

| | commit |
|---|---|
| **正式** | **`b6e403cb609fed81624065770b07143430fb0f10`**（`fix: 新宿歌舞伎町記事用のかぶぱポスト見出しにXのリンクを表示する`） |

**変更ファイルは `streamlit_app.py` の1ファイルだけ（+20 / −1）。**
**`wp_client.py` は無変更（`kabupa777` の出現0件）。**
**`b6e403c` は正式仕様の根拠となる実装commitであって、HEAD をここへ戻すという意味ではない。
`b6e403c` へ reset・revert してはならない。**

### B. 対象範囲

**`auto_article × 新宿歌舞伎町` の1通りだけ。**

**対象外（従来どおり）**：渋谷新館の「ななこポスト」／ 他店舗の記事用 ／ 通常結果ポスト（`auto`）／
かぶぱポストの結果（`auto_slump`）／ `auto_slump2` ／ ローテ（`rote`）／ 作業用（`work`）。

### C. 正式な案内表示

①冒頭の「かぶぱポスト」入力欄の見出しを次のとおりにする。

```
かぶぱポスト（https://x.com/kabupa777）
```

- **`https://x.com/kabupa777` はクリックできるリンク**にする。
- **別タブで開く**（`target="_blank"` ／ `rel="noopener noreferrer"`）。
- 用途は「別タブでXのかぶぱアカウントを開き、そこで**該当ポスト**を開いて
  URLをコピーし、下の入力欄へ貼り付ける」ための**案内表示**。

旧表示 `かぶぱポスト（WordPress冒頭・「全台系」の直前に入ります）` へは戻さない。

### D. ★固定URLは案内表示専用（最重要）

**`https://x.com/kabupa777` を次のいずれにも使ってはならない。**

- **保存値**（`article_page_inputs.json` ほか）
- **X埋め込みURL**
- **WordPress本文**

**WordPress本文へ入るのは、従来どおり入力欄に貼り付けた「該当ポストのURL」だけ。**
挿入位置も従来どおり **WordPress冒頭・「全台系」の直前**。

なお **`wp_client.normalize_x_url()` が `/status/` を要求する**ため、
仮にプロフィールURLが入力欄へ入っても **`""` を返して埋め込まれない**
（実測：`https://x.com/kabupa777` → `""` ／
`https://x.com/kabupa777/status/1234567890` → そのまま採用）。
**この `/status/` 必須の判定を緩めてはならない。**

### E. 実装（定数1つ＋見出し1箇所の分岐だけ）

```python
# ①冒頭の「かぶぱポスト」見出しに出す**案内用のプロフィールURL**（新宿歌舞伎町のみ）。
# ★このURLを **WordPress本文・X埋め込みURL・保存値として使ってはならない**。
_ART_NANAKO_PROFILE_URLS: "dict[str, str]" = {
    "新宿歌舞伎町": "https://x.com/kabupa777",
}
```

- **参照は `_ART_NANAKO_PROFILE_URLS.get(store, "")` の1箇所だけ**（見出し描画）。
  **payload・保存・X埋め込みへは流さない。**
- **未登録の店舗（渋谷新館など）は従来の文言のまま**
  （`**ななこポスト**（WordPress冒頭・「全台系」の直前に入ります）`）。
- 店舗を増やす／戻すときは**この辞書の編集だけ**で行う。**見出し側へ店舗別 if を増やさない。**

### F. 維持する既存仕様

**入力欄キー `art_nanako_url_{store}` ／ ヒント `art_nanako_hint_{i}_{store}`（`_ART_NANAKO_HINTS = 10`）／
日付（Excel）単位の保存・復元（`_art_txt()` ／ `skip_kojin=True`）／
`wp_client.nanako_texts(store)` 由来の「かぶぱポスト」表記／
WordPress本文の挿入位置（全台系の直前）／ 固定の見出し・導入文・締め文／
ヒント先頭の「■」自動付与・空欄ヒントは出力しない** ── **すべて不変**。

`9f0f363`（①冒頭のギルドX削除・ピンクバー中央寄せ）／`92ac8af` / `ee39cd7`
（ポスターのWordPressメディア22択）など、新宿歌舞伎町 記事用の既存正式仕様も**すべて維持**する。

### G. 確認結果

- **定数**：`{'新宿歌舞伎町': 'https://x.com/kabupa777'}` ／ ヒント数10で不変
- **新宿歌舞伎町の見出し**：`target="_blank"` ／ `rel="noopener noreferrer"` あり
- **渋谷新館の見出し**：**従来と完全に同一の文言**
- **固定URLの混入なし**：`wp_client.py` に `kabupa777` **0件**、
  `streamlit_app.py` も**定数定義の1件のみ**
- **`normalize_x_url()`**：プロフィールURLは `""`／個別ポストURLはそのまま採用
- **Cloud 実機でリンクが別タブで開くことを確認済み（2026-09-18）**
- **WordPress通信は0件**（GET / POST / PUT / PATCH / DELETE・下書き作成/更新/公開なし）

### H. 今後の禁止事項

1. **旧文言 `かぶぱポスト（WordPress冒頭・「全台系」の直前に入ります）` へ戻さない**
2. **リンクを同一タブ表示にしない**（`target="_blank"` / `rel="noopener noreferrer"` を外さない）
3. **`https://x.com/kabupa777` を保存値・X埋め込みURL・WordPress本文へ使わない**
4. **`_ART_NANAKO_PROFILE_URLS` の参照を見出し描画以外へ広げない**
5. **`normalize_x_url()` の `/status/` 必須判定を緩めない**
6. **渋谷新館ほか未登録店舗の見出し文言を変えない／プロフィールURLを勝手に追加しない**
7. **入力欄キー・ヒント・保存復元・挿入位置（全台系の直前）・かぶぱポスト表記を変更しない**
8. **見出し側へ店舗別 if を増やさない**（辞書の編集だけで対応する）
9. **`wp_client.py` を今回の理由で変更しない**
10. **`b6e403c` へ reset・revert しない**
11. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新宿歌舞伎町 記事用：📝⑧の一致・スランプ横4列・WordPress表記・⑤H3平均（2026-09-18）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】かつ `page=auto_article` の記事用だけ**。
本節の各commitは**すべて現HEAD（`6829353`）の祖先であることを確認済み**。

既存の記事用セクション（`77e140d` / `31f7346` / `5c5c1f2` / `e53a116` / `61851ca` /
`c1c3bdd` / `56844fe` / `cc695d4` / `51dde3a` / `b5d0f73` / `eacc532` / `9f0f363` /
`92ac8af` / `ee39cd7` / `b6e403c` ほか）は**削除・圧縮・統合・並べ替え・書き換えしない**。

### A. 正式実装commit（7本でひとつの仕様を構成）

| # | commit | 内容 |
|---|---|---|
| ① | **`c060590`** | `fix: 記入部分のみプレビュー後の本番で自動カテゴリを生成しない` |
| ② | **`86f583f`** | `fix: 記入部分のみの本番でその他優秀台・ジャグラー統合を保存する` |
| ③ | **`0cf25ec`** | `fix: 記入部分のみ本番のその他・ジャグラー画像にパネルとスランプを付ける` |
| ④ | **`bc61f1b`** | `feat: 記事用スランプを19件以上で横4列にする` |
| ⑤ | **`71e120f`** | `feat: 新宿歌舞伎町の記事用WordPress表記を変更` |
| ⑥ | **`e201c7d` → `e422ff5`** | ⑤H3の平均差枚（`e201c7d` は反映されず、`e422ff5` の `meta_only_list` が正式） |
| ⑦ | **`6829353`** | `fix: 新宿歌舞伎町記事用の📝⑧でも⑤H3の平均差枚を出す`（本日の最終確定） |

**いずれも「正式仕様の根拠となる実装commit」であって、HEAD をここへ戻す意味ではない。
これらの commit へ reset・revert してはならない。**

### B. 📝「記入部分のみ」→⑧は⑦📝と完全に一致させる（`c060590`）

**📝プレビュー由来の⑧（`_art_exec_manual=True` → `run_auto_pipeline(manual_mode=True)`）では、
⑦📝が描かない自動カテゴリを「生成してから削除」するのではなく、生成・保存の前に除外する。**

対象：**自動全台系 ／ 自動高配分 ／ pipeline版ジャグラー統合 ／ pipeline版その他の優秀台**。

揃える対象は **出力フォルダ ／ ZIP ／ WordPress payload ／ 結果テキスト**。
`df` / `diff_raw` / `nami_list` / `date` など**記入由来の画像に必要な計算は従来どおり行う**。

**既定 `manual_mode=False`＝従来動作**。🔍フルプレビュー後の⑧・他店舗・他ページは完全に不変。

### C. 📝⑧でも「その他の優秀台」「ジャグラーシリーズ優秀台」を保存する（`86f583f` / `0cf25ec`）

- 📝で `その他の優秀台ピックアップ.jpg` / `ジャグラーシリーズ優秀台.jpg` が出る場合、
  **⑧でも同名画像を同じファイル名で保存する**（⑦にあるのに⑧で消える状態にしない）。
- **パネル・表・スランプの合成まで⑦と同じ見た目**にする。ban_map へも登録する。
- ⑦📝で出ないもの（Bの自動カテゴリ）は⑧でも出さない。**この2つを混同しない。**

### D. 記事用スランプは19件以上で横4列（`bc61f1b`）

| スランプカード枚数 | レイアウト |
|---|---|
| **19件以上** | **横4列** |
| **18件以下** | **従来どおり横3列** |

**閾値・列数を変更しない。** 通常ページ・他店舗・かぶぱ・ローテは**対象外**。

### E. WordPress投稿タイトル（`71e120f`）

```
○月○日(曜)の結果
```

`title_simple` キーで切り替える（**キーを渡さない店舗＝高田馬場・渋谷新館は従来どおり**）。

### F. WordPress本文の表記（`71e120f`）

| 対象 | 正式 |
|---|---|
| 全台系H3の接頭辞 | **`【全台系】`**（`h3_zendai_alt`） |
| 台数表記 | **`(総台数中プラス台数+)`** 例 `(44台中22台+)` |
| H2 高配分 | **`高配分機種も複数`**（`h2_alt`） |
| H2 ⑤オススメ | **`オススメポスター機種の優秀台`** |
| H2 その他 | **`その他の単品優秀台`** |
| 末尾の案内ボタン | **出さない**（`no_button`） |
| 10日間ポスターの期間（`🏆9月11日～9月20日🏆`）・「○日目」 | **出さない** |

**10日区切りの画像生成・⑤の機種選択・結果テキストは従来どおり**（WordPress本文だけ出さない）。
**`h3_zendai_alt` / `h2_alt` / `no_button` / `title_simple` はキーを渡した店舗だけに効く。
高田馬場・渋谷新館の本文を変えてはならない。**

### G. ⑤のH3は「入力した機種名」（`71e120f` / `e422ff5` / `6829353`）

- ⑤H3はブロックタイトル（例「10日間オススメポスター」）ではなく、
  **⑤へ記入した実際の機種名**を使う。同一ブロックに複数記入したときは **`・` 区切り**。
- **全台系／高配分にも該当する⑤機種だけ**、機種名の後ろへ **`　平均+〇枚`** を足す。
  該当しない機種には出さない。書式は `wp_client.fmt_signed` と同じ（`+1,200` / `-800`）。
- 平均は **pipeline 結果の `all_avg_diff` をそのまま使い、WordPress用に再計算しない。**

#### ★⑤最優先で抑制した機種の平均は `meta_only_list`（⑤H3専用）から引く

⑤最優先（`_art_osu_priority_machines`）の機種は `recommended_machines` /
`kojin_zentai_machines` へ入るため **`zen_dai_list` / `high_ratio_list` に載らない**。
そこで **判定が成立したことと平均差枚だけ**を専用キー **`meta_only_list`** へ控える。

**`meta_only_list` は⑤H3の平均表示専用。`zen_dai_list` / `high_ratio_list` / 画像 /
ZIP / 結果テキスト / 通常の全台系・高配分H3 へは一切混ぜてはならない。**

#### ★📝⑧では⑤機種だけの meta 専用パスで採る（`6829353`）

`run_auto_pipeline()` の `if manual_mode:` 分岐は Step1/2/3 を呼ばないため、
`e422ff5` だけでは📝⑧で `meta_only_list` が常に空になり平均が出なかった（本日の不具合）。

正式仕様：**`manual_mode=True` でも `meta_only_machines` が非空のときだけ**、
**⑤機種だけへ絞った `df`** を **一時ディレクトリ**へ通して
`run_step1_main` / `run_step2_juggler` / `run_step3_other` の**既存判定をそのまま再利用**し、
**`_meta_only_list` だけ**を受け取る。

- **新しい抽出・判定ロジックを作らない**（Step の条件式を複製しない）。
- ⑤機種は `meta_only_machines` ＝ `recommended_machines` に入っているため、
  Step1 は meta 追記後に `continue`、Step2/3 も `machine not in recommended_machines` が偽で
  画像も `high_ratio_list` も触らない＝**画像0件・出力フォルダ不変**。
- 戻り値は `_meta_only_list` 以外すべて破棄する。**`output_dir` へは絶対に書かない。**
- 例外時は `_meta_only_list = []` に倒し、📝の生成物へ影響させない。
- **`meta_only_machines` が空（他店舗・他ページ・通常ページ）なら1行も実行しない＝従来動作。**

### H. 実データ検証（2026-09-17・新宿歌舞伎町・749台・📝⑧と同じ入力/kwargs）

```
meta_only_list : カバネリ海門決戦 1116 / 東京喰種 662

送信直前payload osusume:
  '東京喰種　平均+662枚'           ['オススメ優秀台_ブロック1.jpg']
  'カバネリ海門決戦　平均+1,116枚'  ['オススメ優秀台_ブロック2.jpg']

最終HTML:
  <h3 class="wp-block-heading">東京喰種　平均+662枚</h3>
  <h3 class="wp-block-heading">カバネリ海門決戦　平均+1,116枚</h3>
```

⑤H3付与は **`streamlit_app.py` の該当ソース行をそのまま exec** し、
`wp_client.build_payload()` → `plan_blocks()` → `build_content()` を通して確認した。

**非回帰（HEAD版を同一ディレクトリへ置いて直接比較・比較後に削除）**

| 比較 | 📝(manual=True) | 🔍(manual=False) |
|---|---|---|
| 現行（meta空） vs 変更前 | **完全一致** | **完全一致** |
| meta あり vs meta 空：戻り値（`meta_only_list` 除く） | **一致** | **一致** |
| 同：出力フォルダのファイル | **一致（📝は0件）** | **一致（15件）** |
| 同：`result["files"]` | **一致** | **一致** |

**WordPress通信は0件**（GET含め一切なし。下書き作成・更新・削除・公開・メディア操作なし）。

### I. 対象外（従来仕様を維持）

**他店舗の記事用（高田馬場・渋谷新館・秋葉原）／ 通常結果ポスト（`auto`）／
かぶぱ（`auto_slump`）／ `auto_slump2` ／ ローテ（`rote`）／ 作業用（`work`）。**

**画像生成 ／ 抽出条件 ／ 台番 ／ ファイル名 ／ ban_map ／ 結果テキスト ／
⑤の入力・順序・優先・重複排除 ／ ②個別画像 ／ 並び・列 ／ 末尾 ／ バラエティ ／
差枚数ランキング ／ 全台データ ／ パネル ／ 液晶（新宿歌舞伎町はなし）／ 島図（なし）／
Noto Sans JP Black ／ 白地スランプカード ／ 高配分の水色バーなし ／
`_ART_WP_NOSPLIT_STORES` / `_ART_WP_FULLWIDTH_STORES` / `_ART_WP_SPLIT_NARROW_STORES` /
`_ART_WP_MIN_KEEP_W = 752` ／ マイジャグV5分割** ── **すべて不変**。

### J. ★今後の改修（未実装・正式仕様として完了扱いにしない）

**⑤の全台系／高配分該当機種のH3を、通常の高配分H3と同じ形式へ揃える。**

| | 表記 |
|---|---|
| **現在（実装済み・平均だけ）** | `東京喰種　平均+662枚` ／ `カバネリ海門決戦　平均+1,116枚` |
| **将来（未実装）** | `【高配分】東京喰種(44台中22台+)→平均+662枚` ／ `【高配分】カバネリ海門決戦(31台中18台+)→平均+1,116枚` |

- **この改修は後日別途実装する。2026-09-18 時点ではコード変更していない。**
- `meta_only_list` には既に `kind`（`zen` / `high`）・`count`・`total`・`all_avg_diff` を
  控えてあるため、**追加の抽出・判定は不要**（表記の組み立てだけで実現できる）。
- 実装時も **`meta_only_list` は⑤H3専用**を維持し、`zen_dai_list` / `high_ratio_list` /
  画像 / 結果テキスト / 通常の全台系・高配分H3 へ混ぜてはならない。
- **この項目を「完了」「正式仕様」として書き換えないこと。**

### K. 今後の禁止事項

1. **📝⑧で自動全台系・自動高配分などを「生成してから削除」する方式へ戻さない**
2. **📝⑦に出る「その他の優秀台」「ジャグラーシリーズ優秀台」を⑧で保存しない状態へ戻さない／
   パネル・表・スランプ合成を外さない**
3. **記事用スランプの「19件以上で横4列／18件以下は横3列」を変更しない**
4. **WordPress投稿タイトル `○月○日(曜)の結果` を変更しない**
5. **`【全台系】` / `(総台数中プラス台数+)` / `高配分機種も複数` /
   `オススメポスター機種の優秀台` / `その他の単品優秀台` を変更しない**
6. **末尾の案内ボタン・10日間ポスターの期間／○日目テキストを本文へ復活させない**
7. **⑤H3をブロックタイトルへ戻さない／該当しない機種へ平均を出さない／平均を再計算しない**
8. **`meta_only_list` を⑤H3以外（画像・ZIP・結果テキスト・通常H3・既存リスト）へ混ぜない**
9. **📝の meta 専用パスを `output_dir` へ書く実装にしない／新しい判定ロジックを複製しない**
10. **`meta_only_machines` が空のときに何か実行する実装にしない（既定＝従来動作を保つ）**
11. **`title_simple` / `h3_zendai_alt` / `h2_alt` / `no_button` を他店舗へ広げない**
12. **I の対象外リストを本節を理由に変更しない**
13. **Jの未実装項目を完了扱いにしない**
14. **A の各commitへ reset・revert しない**
15. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】「その他」配下のスランプ付き結果（2026-09-19・`53a4890` / `1b80b4b` / `f436054`）

**正式仕様。巻き戻し禁止。**対象は**「その他」配下（エスパス以外）のスランプ付き結果だけ**。
2026-09-19 に **ユーザーが Streamlit Cloud 実機で確認し「問題なかった」と承認**した。

| commit | 内容 |
|---|---|
| **`53a4890`** | `feat: 「その他」配下のスランプ付き結果を追加`（`streamlit_app.py` ／ `store_settings/_other_stores.json` 新規） |
| **`1b80b4b`** | `fix: 「その他」店舗選択で検索後も旧選択が残る問題を修正` |
| **`f436054`** | `fix: 「その他」配下のジャグラー統合画像のタイトルとパネル枚数` |

**3commitとも現HEADの祖先であることを確認済み。いずれへも reset・revert しない。**

### ① 導線

```
TOP（既存13店舗 ＋ 末尾に「その他」ボタン1つ）
 → page="other"        … show_other_store_page()（検索テキスト ＋ 店舗selectbox）
 → page="other_slump"  … show_auto_page(with_slump=True)
```

- **既存の `auto` / `auto_slump` / `auto_slump2` / `auto_article` とは別 page**。既存店舗の導線・
  機能ボタン・WordPress導線は**1ビットも変更しない**。
- `_navigate()` の store 保持タプル・パンくず・`main()` ルーティングへ `other_slump` を追加。
- **店舗選択の selectbox に固定 key を付けない**（`1b80b4b`）。固定 key だと検索で options を
  絞り込んでも直前の選択値が widget 状態として残り、候補外の店舗が選ばれたまま表示される
  （実機で確認）。key なしなら options が変わった時点で widget が作り直される。

### ② 対象店舗と設定ファイル

| 店舗 | Pision hall_id |
|---|---|
| プレサス飯田橋 | **306** |
| BEAM新井薬師 | **171** |
| ラ・カータ鶴ヶ島 | **3709** |

- 管理は **`store_settings/_other_stores.json`** の1枚だけ。**店舗追加はこのJSONへ1ブロック
  足すだけ**（コード変更不要）。
- **`STORES` へは追加しない**（TOPの店舗一覧・⑥個別生成ページは従来どおり13店舗のまま）。
- 設定キー：`display_name` / `pision_hall_id` / `slotterguild` / `realtime` / `panel` / `side` /
  `image_types`。
- 判定ヘルパー：`_load_other_stores()` / `_other_store_cfg()` / `_is_other_store()` /
  `_other_hall_id()` / `_other_panel_on()` / `_image_types_of()` / `_other_display_name()`。
  **既存13店舗ではすべて False / None を返す**（`_is_other_store` は `store not in STORES` が前提）。
- **`store_settings` は Cloud→GitHub の同期経路が無い**（2026-08-10 正式運用ルール）。
  編集はローカルで行い、push → **Cloud Reboot** で反映する。

### ③ データ取得

- **Pision 確定データは設定の `pision_hall_id` を直接使う。**
  **既存エスパス店舗の hall 解決（ホール名に店舗名と「エスパス」を含む）は変更しない**
  ── ⓪取得・⑦・⑧・📝合成の4経路とも、既存ループの**前に**「その他」分岐を置くだけ。
- **速報（realtime）・slotterguild は現時点で対象外**。⓪では
  **確定データのみ**（速報ラジオ・「🌐 サイトから取得」を表示しない・`🔄 取得` の1ボタン）。
- **xlsx / csv の手動アップロードは既存仕様のまま利用可能**（`_read_uploaded_df` /
  `normalize_df` / `apply_name_conversion` は店舗非依存・無変更）。
- 結果テキストの店名は **`display_name` をそのまま使う**（**「エスパス」を勝手に付けない**）。
  既存店舗は従来の `エスパス{store}` 経路のまま。

### ④ 画像構成

**`タイトルバー + 機種パネル + 表 + スランプ`** を正式とする。

- 新helper **`_insert_panel_under_bar()`**：`_bar_crop_h()` でバーを分離し、**タイトルバーを
  残したまま**その下へパネルを挿入する。
  **★既存 `_insert_panel_into_machine_img()` は青バーを crop してパネルへ置換する
  「かぶぱ」仕様なので流用しない**（バーが消える）。
- パネル選定は既存 **`_apply_panel_to_table_img(crop_bar=False)`** をそのまま再利用
  （単一機種／2×2グリッド／並び・列）。**新しいパネル選定ロジックは作らない。**
- **パネル未登録機種は例外にせず、その機種だけパネルなしで元画像を返す。**
- 適用は共通 **`_other_apply_panel()`** 1本で、**⑦プレビュー・🔄その他を更新・⑧本番の
  3経路すべて**から呼ぶ（経路ごとに構成がズレないようにするため）。
- **16台以上は既存どおり `{元ファイル名}_side.jpg`**（左＝バー＋パネル＋表／右＝スランプ4列）、
  **16台未満は既存の表下スランプ（3列）**。`_attach_slump_to_table(_side)` は**無変更**。
- 表テーマ・スランプカードは既存の新デザインを使う
  （`_TABLE_THEME_PAGES` / `_SLUMP_THEME_PAGES` へ `other_slump` を追加し、
  `_table_theme_new()` / `_slump_theme_new()` の店舗判定へ `_is_other_store()` を OR）。

### ⑤ ジャグラー統合画像のタイトル（`f436054`）

| ジャグラーシリーズに**自前の画像**（全台系・高配分）が | タイトル |
|---|---|
| **ない** | **`ジャグラーシリーズの優秀台`** |
| **ある** | **`その他のジャグラーシリーズの優秀台`** |

**★原因**：`run_step2_juggler` の `high_ratio_list` には**統合画像へ入った機種も
`has_image=False` で追加される**ため、`bool(high_ratio_list)` だと自前画像が1枚も無くても
「その他の…」になっていた（BEAM新井薬師 9/16 で発生）。

- 実装は **`run_step2_juggler(..., jug_title_by_image: bool = False)`**。
  True のときだけ **`any(h.get("has_image") for h in high_ratio_list)`** で判定する。
  **既定 False ＝ 従来動作**なので既存店舗は不変。
- `run_auto_pipeline` から **`jug_title_by_image=_is_other_store(store)`** を渡す。
- **⑧の再生成経路（`_jug_has_other`）も「その他」のときだけ同じ判定へ揃える**
  （`has_image=True` かつジャグラー機種のみ）。既存店舗は従来の `bool(high_ratio_list)` のまま。
- 🔄の判定（`_still_jug_other`）は元からジャグラー限定で正しいため**無変更**。
- `zen_dai_juggler_machines` / `has_narabi_jug` / `juggler_recommended` の各条件は**変更しない**。

### ⑥ ジャグラー統合画像のパネル枚数（`f436054`）

| パネル登録のある掲載機種数 | パネル |
|---|---|
| 1〜2機種 | **従来どおり**（最大4の既存ルール） |
| **ちょうど3機種** | **最高差枚順の上位2機種のみ（1行2枚）** |
| 4機種以上 | **従来どおり 2×2（4枚）** |

- **右下が空欄の 2×2 を作らない**（`_build_variety_panel_grid` は2枚ずつ折り返すため、
  3枚だと `[2枚][1枚]` になり右下が白く空く）。
- 実装は **`_other_panel_max(bare_fn, bans, ban2mac)`**。
  **対象は `ジャグラーシリーズ優秀台.jpg` だけ**で、その他の優秀台・全台系・高配分・並びへは
  広げない。**パネル未登録機種は機種数に数えない。**
- **選定順位（機種ごとの最高差枚降順）・未登録機種の繰り上げ・表示順は既存のまま。**
  `_build_variety_panel_grid` 本体・`_art_panel_max` は**無変更**。

### ⑦ 対象外（今回いっさい変更していない）

**既存エスパス13店舗 ／ 記事用（`auto_article`）／ 新宿歌舞伎町（かぶぱ・`auto_slump2`）／
通常結果ポスト（`auto`）／ ローテ（`rote`）／ WordPress（`wp_client.py`）／
`masters/machine_image_master.xlsx` ／ パネル素材 ／ フォント ／ `機種名変換.xlsx`。**

`_build_variety_panel_grid` / `_apply_panel_to_table_img` / `_insert_panel_into_machine_img` /
`_art_panel_max` / `_attach_slump_to_table(_side)` / `draw_slump_graph` / `run_step1_main` /
`run_step3_other` / `_manual_jug_title` / `show_auto_article_page` / `normalize_df` /
`_read_uploaded_df` / `apply_name_conversion` / `fetch_pision_*` / `_sg_*` は**AST一致（無変更）**。
`_SG_FETCH_STORES` / `_PANEL_STORES` / `_ART_JUG_PANEL2_STORES` / `STORE_NARABI_SCRIPT` も不変。

### ⑧ 検証

- 構造・非回帰 **96 PASS**／画像構成 **26 PASS**／実データ **28 PASS**／
  修正2件 **44 PASS**（いずれも FAIL 0）。
- 実データ（Pision確定 GET のみ）：プレサス飯田橋 204台 ／ BEAM新井薬師 192台 ／
  ラ・カータ鶴ヶ島 258台。**`normalize_df` の欠損列なし**、pipeline・パネル・スランプ正常。
  **BEAM の points なし40台は全て `games=0`** で既存どおり安全に除外。
- **side は プレサス飯田橋（その他の優秀台35台）で `_side.jpg` の生成を実機確認。**
- **ローカル実機**：BEAM新井薬師 9/16 で
  **タイトル「ジャグラーシリーズの優秀台」・パネル2枚横並び（右下空欄なし）**を目視確認。
- **Cloud 実機確認済み（2026-09-19・ユーザー承認）。**

### ⑨ 今後の禁止事項

1. **`STORES` へ「その他」店舗を追加しない**
2. **`store_settings/_other_stores.json` 以外の場所へ店舗定義を書かない**
3. **既存エスパス店舗の hall 解決（名前一致）を変更しない**
4. **「その他」配下へ速報・slotterguild の導線を勝手に出さない**
5. **結果テキストの店名へ「エスパス」を付けない**
6. **`_insert_panel_into_machine_img()`（バー置換）を「その他」のパネルへ流用しない**
7. **パネル未登録機種を例外にしない**（その機種だけパネルなしで継続）
8. **⑦／🔄／⑧のいずれか1経路だけ変更しない**（`_other_apply_panel` 経由を維持）
9. **side の条件（16台以上）・ファイル名 `_side.jpg`・4列/3列レイアウトを変更しない**
10. **`jug_title_by_image` の既定 `False` を変更しない**（既存店舗の挙動が変わる）
11. **`bool(high_ratio_list)` だけでタイトルを決める実装へ戻さない**
12. **`_other_panel_max` の対象を `ジャグラーシリーズ優秀台.jpg` 以外へ広げない**
13. **パネル選定順位（機種ごとの最高差枚降順）を変更しない／1〜2機種・4機種以上のルールを変えない**
14. **`_build_variety_panel_grid` / `_apply_panel_to_table_img` / `_art_panel_max` を変更しない**
15. **記事用・かぶぱ・通常結果・ローテ・WordPress・機種画像マスタ・パネル素材へ波及させない**
16. **`53a4890` / `1b80b4b` / `f436054` へ reset・revert しない**
17. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】「その他」配下：③並び・列画像と⑤オススメ機種ピックアップ（2026-09-19・`6feaa25`）

**正式仕様。巻き戻し禁止。**対象は**「その他」配下（エスパス以外）のスランプ付き結果
（`page="other_slump"`）だけ**。
2026-09-19 に **ユーザーが Streamlit Cloud 実機で確認し承認**した。

| | commit |
|---|---|
| **正式実装** | **`6feaa25`**（`feat: 「その他」配下へ③並び・列画像と⑤オススメ機種ピックアップを追加`・**`streamlit_app.py` の1ファイルのみ**・+26 / −6） |

**`6feaa25` が現HEADの祖先であることを確認済み。reset・revert してはならない。**
直前の正式記録（`53a4890` / `1b80b4b` / `f436054` ＋ 記録 `83961d7`）の節は
**削除・圧縮・統合・並べ替え・書き換えしない**。本節はそこへ**機能を追加した記録**である。

### ① 追加した機能

「その他」配下の3店舗（**プレサス飯田橋 ／ BEAM新井薬師 ／ ラ・カータ鶴ヶ島**）でも
次を利用できる。

- **③ 並び画像（並び仕掛け・列仕掛け）**
- **⑤ オススメ機種ピックアップ**

### ② ★並び指定は汎用ルール（`STORE_NARABI_SCRIPT` は不変）

「その他」配下は **汎用の並び指定ルール**を使う。

**既存13店舗の `STORE_NARABI_SCRIPT` は1件も変更・追加しない。**
「その他」店舗を `STORE_NARABI_SCRIPT` へ登録する実装にしてはならない。

### ③ ⑤は既存仕様をそのまま継承

⑤オススメ機種ピックアップは、**既存の仕様をそのまま継承**する。

- **抽出条件**
- **優先順位**
- **全台系・高配分などとの重複排除**
- **結果テキストの書式**

**「その他」専用の抽出ロジック・優先ルール・重複排除・結果テキスト書式を新設しない。**

### ④ 画像構成は「その他」配下の既存正式仕様と同じ

③・⑤の画像も **`タイトルバー + 機種パネル + 表 + スランプ`** で生成する。

| 掲載台数 | レイアウト |
|---|---|
| **16台以上** | **`{元ファイル名}_side.jpg`**（左＝バー＋パネル＋表／右＝スランプ4列） |
| **16台未満** | **表下スランプ（3列）** |

`_insert_panel_under_bar()`（タイトルバーを残したままパネルを挿入）・
`_other_apply_panel()`・`_attach_slump_to_table(_side)` など、
**既存の「その他」画像構成の仕組みをそのまま使う。新しいパネル・スランプ処理を作らない。**

### ⑤ ⑦・🔄・⑧で一致させる

**⑦プレビュー ／ 🔄その他を更新 ／ ⑧本番**の3経路で、
**同じ入力・同じ生成内容**になること。

**⑦だけ・⑧だけ生成される／構成が違う状態にしてはならない。**

### ⑥ 保存は既存方式

保存は**既存の日付（Excel）単位・店舗単位の方式**をそのまま使う。

**新しいJSON・新しい保存キー体系・新しい保存関数を作らない。**

### ⑦ 対象外（今回いっさい変更していない）

**記事用（`auto_article`）／ WordPress（`wp_client.py`）／ 既存エスパス13店舗 ／
`機種名変換.xlsx` ／ 機種画像マスタ・パネル素材 ／ Pision 取得仕様 ／ slotterguild 取得仕様。**

「その他」配下の既存正式仕様（`store_settings/_other_stores.json` による店舗管理 ／
`STORES` へ追加しない ／ Pision 確定データのみ（速報・slotterguild は対象外）／
結果テキストの店名は `display_name` をそのまま使い「エスパス」を付けない ／
ジャグラー統合画像のタイトル判定 `jug_title_by_image` ／
ちょうど3機種のときのパネル2枚（`_other_panel_max`））も**すべて維持**する。

### ⑧ Cloud 確認

**2026-09-19：ユーザーが Streamlit Cloud 実機で確認し承認済み。**

### ⑨ 今後の禁止事項

1. **「その他」店舗を `STORE_NARABI_SCRIPT` へ登録しない／既存13店舗の定義を変更しない**
2. **「その他」専用の並び・列の抽出ロジックを新設しない**（汎用ルールを使う）
3. **⑤の抽出条件・優先順位・重複排除・結果テキスト書式を「その他」だけ変えない**
4. **③・⑤の画像構成（バー＋パネル＋表＋スランプ）を崩さない／
   16台以上の `_side.jpg`・16台未満の表下3列を変更しない**
5. **⑦／🔄／⑧のいずれか1経路だけ変更しない**
6. **新しいJSON・新しい保存キー体系・新しい保存関数を作らない**
7. **記事用・WordPress・既存エスパス13店舗・機種名変換マスタ・パネル素材・
   Pision／slotterguild 取得仕様へ波及させない**
8. **「その他」配下の既存正式仕様（`53a4890` / `1b80b4b` / `f436054`）を壊さない**
9. **`6feaa25` へ reset・revert しない**
10. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】新小岩 スランプ付き結果ポスト：🔄その他を更新での⑤オススメ画像のスランプ合成（2026-09-20・`c62846d`）

**正式仕様。巻き戻し禁止。**対象は**【新小岩】スランプ付き結果ポスト用のみ**。
正式実装 commit は **`c62846d`**（`streamlit_app.py` の1ファイルのみ・+37行）。
**Cloud 実機確認済み（2026-09-20・ユーザー承認）。**
**`c62846d` へ reset・revert してはならない。**

### ① 事象と原因

⑦プレビューで自動生成画像（例: 高配分）をチェックOFFし 🔄その他を更新すると、
その機種が⑤オススメ機種ピックアップへ登録済みなら優秀台が⑤画像へ移る。
このとき **表はあるのにスランプグラフが消えていた。**

原因は 🔄 のスランプ合成ブロックで、動的 ban_map（`_upd_dyn_ban_map`）へ
「ジャグラーシリーズ優秀台」「その他の優秀台」しか登録していなかったこと。
直前の⑤再生成で差し替えた `オススメ_*.jpg` は ban_map に入らず、
合成ループの `if _ufn not in _upd_dyn_ban_map: continue` でスキップされ**素の表のまま残っていた**。
（⑦は `_pv_ban_map.update(_rec_ban_map)`、⑧は `_ig_bm_u.update(_exec_rec_ban_map)` で登録済み。）

### ② 正式仕様

- **⑤画像に掲載された全台番は、タイトルバー＋表＋スランプの合成対象でなければならない。**
- **🔄でも⑤再生成画像の掲載台番を動的 ban_map へ登録し、合成漏れを防ぐ。**
- **⑦プレビュー／🔄その他を更新／⑧本番で、⑤画像の掲載台・スランプ・見た目を一致させる。**

### ③ 実装

- 共通ヘルパー **`_rec_block_bans()`** を新設。抽出条件は
  **`generate_recommended_block_image` と完全に同一**（⑦/⑧のインライン実装とも同結果）。
- 🔄の⑤再生成ループで掲載台番を集めて **`_upd_rec_bans`** に控える
  （`_upd_rec_bans` は `if _rec_unchecked_machines ...` の**外**で初期化する）。
- 合成ブロック冒頭で **`_upd_dyn_ban_map.update(_upd_rec_bans)`**。
- **掲載0台（`if _rb_r:`）なら ban_map へ入れない**＝画像を作らない既存仕様を維持。
- ⑤が再生成されない場合 `_upd_rec_bans` は空なので、**`.update({})` の no-op** となり従来動作と同一。

### ④ 変更しないもの

⑤の優先・重複排除・チェックOFF後の移動先・画像名・台番順・結果テキスト・
掲載0台時は画像を作らない既存仕様 ／ `generate_recommended_block_image` ／
`run_auto_pipeline` ／ `filter_recommended_machines` ／ `_collect_published_bans` ／
`_attach_slump_to_table(_side)` ／ `draw_slump_graph` ／ `generate_report_text` ／
⑦の `_rec_ban_map` ／ ⑧の `_exec_rec_ban_map`。

### ⑤ 対象外

**新小岩以外 ／ 記事用（`auto_article`）／「その他」配下3店舗 ／ WordPress ／
機種名変換マスタ ／ パネル素材。**
`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` / `機種名変換.xlsx` は無変更。

### ⑥ 検証

9/19 新小岩の確定データ（484台）で再現・修正を確認。
モンキーターンVをOFF → 🔄 で `オススメ_その他の主役機種の優秀台_2000枚以上.jpg` が
**5台→6台**（台番2115 追加）になり、**表397px → 合成後1273px** でスランプ6枚が付くこと、
レイアウト（タイトルバー＋表＋スランプ3列）が維持されることを実画像で確認。
ヘルパー＝⑦インライン＝⑧インライン＝画像の実掲載行の一致、
変化しない⑤画像の⑦と🔄でのバイト一致、AST差分（変更関数は `show_auto_page` のみ／
新規は `_rec_block_bans` のみ／削除0）も確認済み。

### ⑦ 今後の禁止事項

1. **🔄の `_upd_dyn_ban_map` から⑤画像（`_upd_rec_bans`）のマージを外さない**
2. **`_upd_rec_bans` の初期化を `if _rec_unchecked_machines ...` の内側へ移さない**
3. **`_rec_block_bans()` の抽出条件を `generate_recommended_block_image` とズラさない**
4. **`if _rb_r:` を外さない**（掲載0台で画像を作らない仕様が壊れる）
5. **⑦の `_rec_ban_map` / ⑧の `_exec_rec_ban_map` を変更しない**
6. **⑤の優先・重複排除・移動先・画像名・台番順・結果テキストを変更しない**
7. **新小岩以外・記事用・「その他」配下・WordPress へ波及させない**
8. **`c62846d` へ reset・revert しない**
9. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】既存エスパス店舗の結果テキスト表記統一（2026-09-21・`07ac10b` / `be24e7e`）

**正式仕様。巻き戻し禁止。**対象は**既存エスパス13店舗の結果テキスト（`*_結果.txt`）だけ**。
2026-09-21 に **ユーザーが Streamlit Cloud 実機で確認し「問題なかった」と承認**した。

| commit | 内容 |
|---|---|
| **`07ac10b`** | `fix: 既存エスパス店舗の結果テキスト表記を変更`（見出し／優秀機種の空行／並びの「・」） |
| **`be24e7e`** | `fix: 結果テキストの高配分機種も機種ごとに空行で区切る` |

**2件とも現HEADの祖先であることを確認済み。reset・revert してはならない。**

### ① 対象と対象外

- 対象は **既存エスパス13店舗**（`STORES`）の結果テキストのみ。
- **「その他」配下（プレサス飯田橋／BEAM新井薬師／ラ・カータ鶴ヶ島）は対象外**で、
  **結果テキストを従来どおり維持**する（HEAD版と完全一致）。
- ゲートは `generate_report_text()` 内の **`_espa_txt = not _is_other_store(store_name)`** 1本。
  **店舗名のハードコードや新しいゲートを作らない。**

### ② 見出し

**`👑全台系濃厚機種` ではなく `👑優秀機種`**（`{e2}` は店舗別絵文字）。

### ③ 機種ブロック間の空行

**`👑優秀機種` と `👑高配分機種` は、各機種ブロックの間を空行1行で区切る。**

```
・からくりサーカス2(4/5台)→平均+2,440枚
+9,000枚、+1,900枚

・ワールドダイスター(2/3台)→平均+1,983枚
+10,150枚、+1,600枚

・東京喰種(9/23台)→平均+763枚
+5,800枚、+5,400枚、+5,350枚、
+4,900枚、+4,350枚、+3,950枚、
+3,750枚
```

- **同一機種内の差枚折返し行の途中には空行を入れない**（1機種＝1ブロック）。
- **機種が1件だけのときは余分な空行を入れない。**
- **掲載0件時の `（なし）` など既存表記は維持する。**

### ④ 並び仕掛けの機種名先頭「・」

**`👑並び仕掛け` の各機種名の先頭へ `・` を付ける。**

```
👑並び仕掛け
・SAOII
2123-2125番台(3台)→平均+3,067枚
・カバネリ海門決戦
2103-2105番台(3台)→平均+2,600枚
2107-2109番台(3台)→平均+2,667枚
・モンキーターンV
2092-2094番台(3台)→平均+3,233枚
```

- **同一機種に複数の並びがある場合は最初の機種名行だけ**に付ける。
- **後続の台番範囲行には付けない。**
- **`👑列仕掛け` には付けない**（`_nami_like_section(items, name_head="")` の既定は `""` で、
  `nami_section()` だけが `"・"` を渡す。`retsu_section()` は従来どおり）。
- **すでに「・」がある経路で二重にしない。**

### ⑤ 変更しないもの

**抽出条件 ／ 機種順 ／ 差枚順 ／ 平均値 ／ 画像 ／ WordPress本文 ／ 保存データ**は変更しない。
`run_auto_pipeline` / `run_step1〜3` / `_result_summary_lines` / `_format_diffs` /
`_build_kabupa_result_text` / `_generate_rote_result_text` / 画像生成系は**AST一致（無変更）**。
`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` も無変更。

### ⑥ 見出し変更に追従させた2箇所（外すと壊れる）

| 箇所 | 正式 |
|---|---|
| **赤坂見附の後処理** `STORE_RESULT_TRANSFORMS` | **`("👑優秀機種", "👑優秀機種👑")`**。装飾（`👑高配分以上機種👑` / `👑並び👑` / `➡`）は従来どおり |
| **新小岩⑤の挿入位置** `insert_formatted_result_before_other_picks()` | **`marker = f"{e2}優秀機種"`**。⑤ブロックは**`👑優秀機種` の直前**へ挿入する（末尾追記にしない） |

### ⑦ 検証

純粋関数テスト **206 PASS / 0 FAIL**（`07ac10b`）＋ **100 PASS / 0 FAIL**（`be24e7e`）。
HEAD版は**同一ディレクトリへ一時配置**して比較した（`BASE_DIR` がずれると
`store_settings` / `機種名変換.xlsx` を読めず誤検知するため。比較後に削除）。

新小岩9/19相当（優秀機種・高配分機種とも複数機種＋差枚折返し・同機種の複数並び）で
期待例と**文字列完全一致**。並びなし／優秀機種なし／高配分1件・0件・`(1/2台)` 降格
（稲毛のみ非降格）も確認。**その他3店舗は5ケースすべて HEAD と完全一致。**
**Cloud 実機確認済み（2026-09-21・ユーザー承認）。**

### ⑧ 今後の禁止事項

1. **`👑全台系濃厚機種` へ戻さない**
2. **`👑優秀機種` / `👑高配分機種` の機種ブロック間の空行を外さない**
3. **差枚の折返し行の途中へ空行を入れない**
4. **1機種だけのときに余分な空行を入れない／0件時の `（なし）` を変えない**
5. **並び仕掛けの機種名「・」を外さない／台番範囲行や列仕掛けへ付けない／二重に付けない**
6. **「その他」配下3店舗へ今回の表記を適用しない**（`_espa_txt` ゲートを外さない）
7. **抽出条件・機種順・差枚順・平均値・画像・WordPress本文・保存データを変更しない**
8. **赤坂見附の後処理キー（`👑優秀機種`）と新小岩⑤の挿入マーカーを見出しとズラさない**
9. **`07ac10b` / `be24e7e` へ reset・revert しない**
10. **無関係なリファクタ・未使用コード整理をしない**

## 【正式仕様】「その他」配下のスランプ付き結果：取得元拡張・表示・パネル・結果テキスト（2026-09-21・`81d58e4` / `87ecc62` / `cfebeec` / `98b00b3`）

**正式仕様。巻き戻し禁止。**対象は**「その他」配下（エスパス以外）のスランプ付き結果**。
現行対象店舗は **プレサス飯田橋 ／ BEAM新井薬師 ／ ラ・カータ鶴ヶ島**。
2026-09-21 に **ユーザーが Streamlit Cloud 実機で確認し「問題なかった」と承認**した。

| commit | 内容 |
|---|---|
| **`81d58e4`** | `feat: プレサス飯田橋の速報とslotterguild取得に対応` |
| **`87ecc62`** | `fix: 「その他」配下の機種別データタイトルからエスパスを外す` |
| **`cfebeec`** | `fix: 「その他」配下の並び・列画像のパネル選定を修正` |
| **`98b00b3`** | `feat: 「その他」配下の結果テキストにも機種ブロック空行と並びの「・」を適用` |

**4件とも現HEADの祖先であることを確認済み。reset・revert してはならない。**

### ① 取得元（プレサス飯田橋のみ3系統）

**プレサス飯田橋は Pision確定 ／ Pision速報 ／ slotterguild.com の3取得元に対応する。**

| 取得元 | ID | 確認方法 |
|---|---|---|
| Pision確定 | `pision_hall_id = "306"` | 設定値 |
| **Pision速報** | **`/realtime/create` の店舗 select から解決**（設定値を持たない） | select に「プレサス飯田橋」が存在することを実データで確認 |
| **slotterguild** | **`slotterguild = 136`** | サイト自身の店舗一覧 `halls.php` で確認（既知の稲毛566／上野新館570／新小岩573 とも一致） |

- **確認済みの設定値・select 実値だけを使う。確定用 306 を速報やSGへ流用しない。ID総当たり禁止。**
- **取得元は画面で明示する**：データ種別 radio（確定／速報）＋ `🔄 Pisionから取得` / `🌐 サイトから取得`、
  取得後も `…の{確定|速報}データ（N台）を取得し、①にセットしました。／ 取得元: Pision | slotterguild.com`。
- **混在・暗黙フォールバックをしない**（xlsx＋points＋台番集合一致が揃ったときだけ session_state を更新）。

### ② BEAM新井薬師 ／ ラ・カータ鶴ヶ島

**未確認の速報・slotterguild を有効化しない**（`store_settings/_other_stores.json` で
`realtime: false` / `slotterguild: false` のまま＝UIに出さない・確定データのみ）。

### ③ 機種別データのタイトル・店舗名に「エスパス」を付けない

**「その他」配下は設定の `display_name` をそのまま使う。**

```
2026/9/20 ラ・カータ鶴ヶ島      ← ○
2026/9/20 エスパスラ・カータ鶴ヶ島 ← ×
```

- 実装は `show_auto_page` の `_title` 組立で **`_other_display_name(store) or f"エスパス{store}"`**。
- **既存エスパス13店舗と未登録店舗は従来どおり「エスパス{store}」**（`_other_display_name()` が None）。
- 結果テキストの店舗名行は元から `_other_display_name()` 経由（無変更）。
- **記事用・ローテ・週間の「エスパス{…}」組立は変更しない。**

### ④ ③並び・列画像のパネル選定（その他配下のみ）

| パネル**登録済み**機種数 | パネル |
|---|---|
| 1機種 | 1枚（全幅・従来どおり） |
| 2機種 | 横並び2枚（従来どおり） |
| **3機種** | **差枚上位2機種を横並び**（**空欄付き2×2にしない**） |
| 4機種以上 | **既存の最大4枚・2×2グリッド** |

- **パネル未登録機種は繰り上げて選び、画像生成を止めない**（全機種未登録なら素通し）。
- 選定順位（機種ごとの最高差枚降順）・表示順（台番昇順）は **既存 `_build_variety_panel_grid()`** のまま。
- 実装は `_other_apply_panel()` の振り分け＋新設 `_other_panel_macs()`。
  `_apply_panel_to_table_img` / `_insert_panel_under_bar` の `panel_names`（既定 None＝従来動作）。
- **★`narabi_like` は True のまま渡す。**False にすると列画像が単一機種分岐へ落ち、
  ファイル名から機種名を復元できずパネルが消える。
- **原因（記録）**：並び・列は `_narabi_panel_names()` の「3機種以上→差枚最大の1機種」で選定され、
  `_other_panel_max()`（ジャグラー統合限定）は並び分岐で参照されないため1枚になっていた。
- **⑦プレビュー／🔄その他を更新／⑧本番は同じ `_other_apply_panel()` を通す**（`show_mn` の違いでも出力同一）。

### ⑤ 結果テキストの見出し

**「その他」配下は従来どおり `{e2}全台系濃厚機種`**（`👑優秀機種` にしない）。
`_espa_txt = not _is_other_store(store_name)` は**この見出しの出し分けだけ**に使う。

### ⑥ 機種ブロック間の空行（全店舗共通）

**全台系・高配分など「機種名＋平均差枚＋差枚一覧」を出すセクションは、
1機種分の内容の後に空行を1行入れる。**

```
・南国育ちSPECIAL(2/2台)→平均+6,525枚
+12,250枚

・戦コレ6(2/4台)→平均+2,650枚
+9,950枚、+2,500枚
```

- **同一機種の差枚折返し行の途中には空行を入れない**（1機種＝1ブロック）。
- **機種1件だけなら余分な空行を入れない。0件時の `（なし）` も維持。**

### ⑦ 並び仕掛けの機種名先頭「・」（全店舗共通）

```
👑並び仕掛け
・南国育ちSPECIAL～バーニングEXP.
541-543番台(3台)→平均+4,806枚
・ミスジャグ+ファンキー2
554-557番台(4台)→平均-300枚
560-562番台(3台)→平均+200枚
```

- **同一機種に複数の並びがあるときは最初の機種名行だけ。台番範囲行には付けない。二重に付けない。**
- **`👑列仕掛け` は対象外**（`_nami_like_section` の既定 `name_head=""`・`retsu_section()` は引数を渡さない）。

### ⑧ ⑥⑦は全店舗共通・既存エスパスの表記は維持

⑥⑦は **無条件適用**なので、**今後追加する「その他」店舗にも自動で効く**。
同時に **既存エスパス13店舗の `👑優秀機種` などの既存表記は維持**する
（エスパス13店舗の出力は `98b00b3` 直前HEADと完全一致を確認済み）。

### ⑨ 変更していないもの

**画像（生成ロジック・サイズ・配色）／ 抽出条件・機種順・差枚順・平均値 ／ WordPress ／
保存データ（JSON schema・キー）／ `masters/machine_image_master.xlsx` ／ パネル素材 ／
`機種名変換.xlsx` ／ 既存エスパス13店舗 ／ 記事用 ／ かぶぱ ／ ローテ ／ 週間。**

`wp_client.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` はいずれも無変更。

### ⑩ 検証

`81d58e4`：109 PASS ／ `87ecc62`：106 PASS ／ `cfebeec`：62 PASS ／ `98b00b3`：144 PASS（いずれも FAIL 0）。
HEAD版は**同一ディレクトリへ一時配置**して比較した（`BASE_DIR` がずれると
`store_settings` / `機種名変換.xlsx` を読めず誤検知するため。比較後に削除）。
実機ではプレサス飯田橋で3取得元の取得と⑦プレビュー（表・パネル・スランプ）、
ラ・カータ鶴ヶ島 9/20 の3機種並び（535-537）でパネル2枚横並び・🔄後も同一を確認。
**Cloud 実機確認済み（2026-09-21・ユーザー承認）。**

### ⑪ 今後の禁止事項

1. **未確認の取得元を有効化しない**（BEAM新井薬師／ラ・カータ鶴ヶ島の `realtime` / `slotterguild` を false のまま）
2. **確定用 hall_id を速報・slotterguild へ流用しない／IDを推測・総当たりしない**
3. **取得元を混在させない／失敗時に確定データへ暗黙フォールバックしない**
4. **その他店舗のタイトル・店舗名へ「エスパス」を付けない／既存エスパス店舗から外さない**
5. **並び・列で3機種のとき1枚へ戻さない／空欄付き2×2にしない／`narabi_like` を False にしない**
6. **パネル未登録機種で画像生成を止めない／選定順位・表示順を変えない**
7. **その他店舗の見出しを `👑優秀機種` にしない**
8. **機種ブロック間の空行を外さない／差枚折返しの途中へ入れない／1件・0件の挙動を変えない**
9. **並びの「・」を外さない／台番範囲行・列仕掛けへ付けない／二重に付けない**
10. **⑥⑦を店舗ゲート付きへ戻さない**（全店舗共通・今後追加分へ自動適用）
11. **既存エスパス13店舗の結果テキスト表記を変えない**
12. **画像・抽出条件・WordPress・保存データ・機種名変換マスタ・パネル素材を変更しない**
13. **`81d58e4` / `87ecc62` / `cfebeec` / `98b00b3` へ reset・revert しない**
14. **無関係なリファクタ・未使用コード整理をしない**
