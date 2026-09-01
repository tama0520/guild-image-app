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
