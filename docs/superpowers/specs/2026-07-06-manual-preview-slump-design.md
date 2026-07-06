# スランプ付きページの「記入部分のみプレビュー＋実行」設計

作成日: 2026-07-06

## 背景・目的

通常の結果ポスト用ページ（`show_auto_page(with_slump=False)`）には「📝 記入部分のみプレビュー作成」機能がある（②個別・③並び・④末尾・⑤オススメだけを素早く生成する仕組み）。これをスランプ付き結果ポスト用ページ（`show_auto_page(with_slump=True)`）にも実装し、記入部分の画像にもスランプグラフを合成して確認・出力できるようにする。

現状のゲート:
- 📝ボタンは `if not with_slump:` の分岐でのみ表示（`streamlit_app.py:6250-6258`）。
- 実行モード `_is_manual_mode` は `(not with_slump) and _manual_preview_mode_{store}`（`streamlit_app.py:7696`）。

## スコープ

- スランプ付きページを持つ**全店舗**（店舗限定なし）。
- **📝プレビューと⑧実行の両方**にスランプグラフ合成を行う（最終出力ファイルもスランプ付き）。
- 記事用ページ（`show_auto_article_page` / `art_` プレフィックス）は対象外。

## 既存のスランプ合成の仕組み（再利用元）

フルスランププレビュー（`with_slump=True` の 🔍 プレビュー）は次を行う（`streamlit_app.py:6715-6867` 付近）:
1. pisionデータ取得: 速報キャッシュ `_auto_tb_rt_items_{store}`（日付一致時）を優先、無ければ `fetch_pision_halls` → `fetch_pision_results` で取得し `_slump_apply_names` 適用。uid→item の辞書を `_slump_by_uid_{store}` にキャッシュ。
2. ban_map（画像ファイル名→台番リスト）を各画像種ごとに構築。
3. 各画像について ban_map の台番から `draw_slump_graph`（`_it["points"]` 使用）を作り、`_attach_slump_to_table`（秋葉原は `_build_slump_title_img`、グラフ16枚以上は `_attach_slump_to_table_side` で `_side.jpg` も追加）で合成。
   - `find_slump_template()` / `_find_slump_bg()` を使用。
   - 全台系マイナス台は `show_diff=False`（既存ルール）。

## 設計

### 1. 📝ボタンの表示（with_slump）

`streamlit_app.py:6250-6258` の分岐を変更し、`with_slump` 側でも「🔍 プレビュー生成」と「📝 記入部分のみプレビュー作成」の2カラムを表示する（現状 `with_slump` は 🔍 のみ・`_manual_prev_btn=False`）。全店舗共通。

### 2. スランプ合成ヘルパーの新設

新関数を追加（重複を避け、新パスの単一の合成口とする。フルプレビューの既存合成ブロックは変更しない）:

```
_composite_slump_onto_images(
    img_list: list[tuple[str, Image]],
    ban_map:  dict[str, list[int]],     # ファイル名(連番プレフィックス無し) → 台番リスト
    store: str,
    df,                                  # 台番→機種名の逆引き用（machine_name表示・show_diff判定）
    diff_map: dict[int, int] | None,     # 台番→差枚（show_diff=Falseの全台系マイナス判定用）
    date_str: str,
) -> list[tuple[str, Image]]
```

処理:
- pisionデータを `_slump_by_uid_{store}` から取得（無ければ速報キャッシュ→`fetch_pision_results` の順で取得しキャッシュ）。取得不可なら **img_list をそのまま返す**（合成なし）。
- `find_slump_template()` / `_find_slump_bg()` を取得。
- 各 `(fn, img)` について、`ban_map[bare(fn)]` の台番から `draw_slump_graph` を作り合成。秋葉原は `_build_slump_title_img`、16枚以上は `_side.jpg` も追加（既存フルプレビューと同じ分岐）。
- 既存フルプレビューの合成ロジック（`show_diff` の全台系マイナス判定、`machine_name` 表示条件、秋葉原分岐、`_side`）を踏襲する。

### 3. 記入部分のみプレビュー生成にスランプ合成を追加

既存の記入部分生成（`streamlit_app.py:6984-7103`）で各画像を作る際、**台番リストも収集**して `_manual_ban_map`（ファイル名→台番）を構築する:
- ②個別(全台): `_mg["台番"]`
- ②個別(優秀台): `_mgp["台番"]`
- ②その他ピックアップ: `_se_df_m["台番"]`
- 個別機種の優秀台ピックアップ（既存機能）: 各 `_pk_df["台番"]`
- ③並び: `_ngrp["台番"]`
- ④末尾: 末尾入力（`suebangai_tail_input_*` / `jug_sue_tail_input_*`）とモードから、フルプレビューの末尾 ban_map 構築（`streamlit_app.py:6820-6832` 付近）と同じ方式で `_df_m` から台番を算出する（`_gen_sue_imgs_on_fly` は変更しない）
- ⑤オススメ: `generate_recommended_block_image` に含まれる台番（既存フルプレビューの `_rec_ban_map` 構築ロジックを参照）

`with_slump` の場合、生成後に `_composite_slump_onto_images(_manual_imgs, _manual_ban_map, store, _df_m, diff_map, date)` を通してから `_aprev_key` に格納する。`with_slump=False` は従来どおり合成なし。

### 4. 記入部分のみ実行（⑧）にスランプ合成を追加

- `_is_manual_mode`（`streamlit_app.py:7696`）の判定から `(not with_slump)` ゲートを外し、`with_slump` でも `_manual_preview_mode_{store}` が立っていれば manual 実行に入るようにする。
- manual 実行で記入部分の各表画像を作った後、`with_slump` なら保存前に `_composite_slump_onto_images` で合成してから `output_dir` に保存する（`_side.jpg` も保存対象に含める）。
- 結果テキスト等の他の出力は manual 実行の既存挙動を踏襲。

### 5. データ未取得・エラー時

- `with_slump` で pision データが取得できない場合は、警告表示のうえ **表だけ（合成なし）で継続**する（フルプレビューと同じ寛容な挙動）。プレビュー自体は出す。

## 日付・pisionキー

- 日付は `auto_tb_date_{store}` / `_prev_result.get("date")` 相当（フルプレビューと同じ導出）。記入部分のみパスは `_prev_result` を持たないため、`_df_m` の日付や `auto_tb_date_{store}` から導出する。

## 非対象（YAGNI）

- フルスランププレビューの既存合成ブロックのリファクタ（触らない）。
- 記事用ページ対応。
- スランプデータの自動再取得ポーリング（既存⓪セクションに委ねる）。
