# 液晶はめ込みの他店舗展開（上野新館・上野本館・新小岩）— 設計書

作成日: 2026-07-10
対象: `streamlit_app.py`
前提: 新宿歌舞伎町かぶぱで実装済みの液晶はめ込み機能（[[project_slump_gap_screen_fill]]）を横展開する。

## 目的

スランプグラフ最終行の空きコマ（2以上）への液晶はめ込み＋⑥プレビューの液晶セレクタ
（サムネ選択・即時反映）を、**上野新館・上野本館・新小岩**のスランプ付き結果ポストにも
効かせる。秋葉原はレイアウトが異なる（`_build_slump_title_img`）ため今回は対象外。

## 方針

液晶はめ込み関連のガードだけを対象店舗に広げる。kabupa専用の別機能（パネル挿入・
青タイトルバー除去・結果テキスト・②優秀台空欄・スマホボタンUI・`_panel_report`）は
一切変更しない。

### 店舗セットの新設

```python
_GAP_FILL_STORES = {"新宿歌舞伎町", "上野新館", "上野本館", "新小岩"}  # 秋葉原は後日
```
（`_composite_slump_onto_images` や show_auto_page から参照できるモジュールレベル定数）

### 差し替え対象（液晶ガードのみ `store == "新宿歌舞伎町"` → `store in _GAP_FILL_STORES`）

判別ルール：その `if store == "新宿歌舞伎町":` ブロックの本体が
`_gap_screen_paths_for_bans` / `_resolve_gap_screen` / `_gap_meta` / `_gap_base` /
液晶セレクタ(expander) を参照している箇所のみ。パネル系シンボルを参照する箇所は対象外。

対象サイト（概略・実装時に行番号を再確認）:
1. `_composite_slump_onto_images` 内
   - 液晶メタ/ベース構築＋`_gap_screen_paths_for_bans`＋`_resolve_gap_screen`（本体）
   - `_side.jpg` 用の同処理
   - 末尾の `_gap_meta_{store}` / `_gap_base_{store}` の session_state 保存
     （※ここは `_panel_report` 保存と同じ `if store == "新宿歌舞伎町":` に同居して
     いるため**ブロックを分割**：`_panel_report` は kabupa のまま、gap_meta/gap_base
     保存だけを `store in _GAP_FILL_STORES` に広げる）
2. pisionマージ・プレビュー経路の `_is_kabupa_pv`（→ `_gap_fill_pv` として membership 判定に）
3. 「🔄その他を更新」更新経路（`_gap_screen_paths_for_bans(_bans_u2, …)` の前後）
4. ⑧実行経路（`_gap_screen_paths_for_bans(_bans_exec, …)` の前後）
5. 記事用ページ経路（プレビュー更新／実行の2箇所）
6. ⑥プレビュー表示の液晶セレクタUI＋即時反映＋診断キャプション（現在 `store == "新宿歌舞伎町"`）

### 変更しない（kabupa専用のまま）

- `_insert_panel_into_machine_img`・青タイトルバー除去（table-only/panel）
- `_panel_report` 保存、かぶぱ結果テキスト（`_build_kabupa_result_text`）
- ②優秀台を毎回空欄、スマホボタンUI（`.st-key-auto_run` 等）
- `store != "秋葉原"` の条件（そのまま）

## 期待挙動（3店舗）

- スランプ付き結果ポストのプレビュー/実行で、空き2コマ以上に差枚最大機種（1機種なら
  その機種）の液晶を中央配置ではめ込む。0.95縮小。液晶未登録なら空きのまま。
- ⑥プレビュー各画像下に「🖼️ 液晶画像を選ぶ（機種名）」が出て、サムネ選択→即時反映。
- ⑧実行の出力にも選択が反映。
- kabupa の見た目・挙動は不変。他店舗（対象外）・PC も不変。

## 検証観点

- 構文チェック（ast.parse）通過、`tests/test_gap_fill.py` 全通過。
- 上野新館・上野本館・新小岩それぞれで実機確認：
  - プレビューで空き2以上の画像に液晶＋セレクタが出る。
  - 液晶を選び直すと即時反映、⑧出力にも反映。
  - 液晶未登録機種は空きのまま＋「液晶が未登録です」キャプション。
- 新宿歌舞伎町（かぶぱ）が従来通り（パネル・結果テキスト・スマホUIに影響なし）。
- 対象外店舗・秋葉原が従来通り（液晶なし）。
