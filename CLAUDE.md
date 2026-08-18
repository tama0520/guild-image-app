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

## 機種名変換

`機種名変換.xlsx`（2行目をヘッダーとして読み込む、B列=変換前, C列=変換後）を `load_name_map()` でキャッシュ。完全一致 → 正規化一致（スペース・全角除去）の順で変換。`@st.cache_data` でセッション中は再読み込みしない。
