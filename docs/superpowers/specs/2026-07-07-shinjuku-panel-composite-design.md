# 新宿歌舞伎町「かぶぱポストの結果」パネル画像合成

## 目的
新宿歌舞伎町のスランプ付き結果ポスト（かぶぱポストの結果）で生成される「青タイトルバー＋表＋スランプグラフ」画像に、機種のパネル画像を差し込む。参照レイアウト＝デスクトップ 111.jpg。

## レイアウト
- 基本：青タイトルバー → **パネル** → 表 → スランプグラフ（3列）
- 優秀台16台以上（_side.jpg）：左に 青バー → **パネル** → 表、右にスランプグラフ4列

## 実装
### 1. `_insert_panel_into_machine_img(img, machine_name) -> (Image, bool)`
- `w = img.width`、差し込み位置 `split = round(w*73/950) + 6`（`_build_machine_img` の BAR_H + LINE_H と同一計算）
- `get_machine_images(machine_name)["panel"]` を取得。無ければ `(img, False)` を返す
- パネルを幅 `w` にリサイズ（縦横比維持）し、青バー＋赤ラインと表の間に差し込んだ新画像を返す `(new_img, True)`
- パネルのパスは `os.path.join(BASE_DIR, panel_rel)`

### 2. `_composite_slump_onto_images` に新宿歌舞伎町分岐
- 単一機種画像のみ（`_show_mn`＝その他/末尾/バラエティ以外）に適用
- 機種名抽出：`re.sub(r"(_高配分)?\.jpg$", "", _bare)`
- `_img` にパネル差し込み → 既存の `_attach_slump_to_table`／`_attach_slump_to_table_side` にそのまま渡す（縦・side 両方にパネルが乗る）
- パネル未登録の機種名を集約し、ループ後に `st.warning` で通知

## 非対象・不変
- 他店舗、秋葉原分岐、複数機種画像（その他の優秀台ピックアップ・ジャグラーシリーズ優秀台統合・末尾・バラエティ）はパネルなしのまま
- パネル未登録でも画像生成は継続（警告のみ）

## 関連
- 参照: `_build_machine_img`(青バー)・`_attach_slump_to_table`(縦)・`_attach_slump_to_table_side`(side)・`get_machine_images`(パネル取得)
