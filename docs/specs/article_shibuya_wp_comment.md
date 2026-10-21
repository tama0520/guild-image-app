# 記事用：渋谷新館（WordPress・記事コメント）

対象：渋谷新館のWordPress下書き・本文構成・ななこ/ギルドX・投稿者・記事コメント

> このファイルは旧 `CLAUDE.md`（blob `fde5030`・commit `bfb9ad5`）から機械的に切り出した正式仕様の原文です。
> `VERBATIM-BEGIN` 〜 `VERBATIM-END` の間は1文字も変更しないこと（要約・統合・削除も禁止）。
> 新しい正式仕様は、このファイルの末尾（マーカーの外）へ追記してください。
> 完全一致の確認：`py -3.14 tools/verify_claude_split.py`

<!-- VERBATIM-BEGIN id=S07552 src=CLAUDE.md@fde5030 lines=7552-7778 sha256=f2475c5088d96df64645eaa65b0a5426b211284ae70f95c2a6873b7af238861f -->
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

<!-- VERBATIM-END id=S07552 -->

<!-- VERBATIM-BEGIN id=S07779 src=CLAUDE.md@fde5030 lines=7779-8011 sha256=d1de92d7c3e9c185c7996a26cac2a980fb43b69ea0bf02840a4cf86b003d0020 -->
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

<!-- VERBATIM-END id=S07779 -->

<!-- VERBATIM-BEGIN id=S08012 src=CLAUDE.md@fde5030 lines=8012-8218 sha256=e817546487dd8670f44831ff4d52ded288d4eb54f555d60ff489b3753a15a19d -->
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

<!-- VERBATIM-END id=S08012 -->

<!-- VERBATIM-BEGIN id=S08219 src=CLAUDE.md@fde5030 lines=8219-8409 sha256=7f9e279ed049772fdf445e392af910db05ead758981c6fbc3d932ba945983625 -->
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

<!-- VERBATIM-END id=S08219 -->

<!-- VERBATIM-BEGIN id=S08555 src=CLAUDE.md@fde5030 lines=8555-8751 sha256=1c68f24910b40008989203fff35f0a1ad44d96f24b33db82fc0ac65f23fc5b02 -->
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

<!-- VERBATIM-END id=S08555 -->

<!-- VERBATIM-BEGIN id=S08752 src=CLAUDE.md@fde5030 lines=8752-8942 sha256=992aa202f6d1ce200a1bbaa7bf8b9f639a274218f061e0285760ea2de11f54af -->
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

<!-- VERBATIM-END id=S08752 -->

<!-- VERBATIM-BEGIN id=S08943 src=CLAUDE.md@fde5030 lines=8943-9206 sha256=966e0027a43139de7940beb5c5067bce40a5dff18478b6f7788f19d1bcec5c2b -->
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

<!-- VERBATIM-END id=S08943 -->

<!-- VERBATIM-BEGIN id=S09486 src=CLAUDE.md@fde5030 lines=9486-9738 sha256=5fad71e64f871f61d68f8db406f1829e445e498c69a21a63e8efd69e64ae7501 -->
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

<!-- VERBATIM-END id=S09486 -->

<!-- VERBATIM-BEGIN id=S10057 src=CLAUDE.md@fde5030 lines=10057-10248 sha256=5fe1a4ae7aac5bb0a2ccdd444d5bbe9f9d6ef7f0a7f096f421a0c2093fe4dee1 -->
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

<!-- VERBATIM-END id=S10057 -->

<!-- VERBATIM-BEGIN id=S12288 src=CLAUDE.md@fde5030 lines=12288-12524 sha256=8e1f1893570c55ed44dbee798626f4ebbae717a60d385527b4de9075d4d1ecc1 -->
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

<!-- VERBATIM-END id=S12288 -->

<!-- VERBATIM-BEGIN id=S12525 src=CLAUDE.md@fde5030 lines=12525-12794 sha256=84a7e209f0b812aa6c4ac589d1c5032a3144f6573c030f2b5509a3ac22688c03 -->
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

<!-- VERBATIM-END id=S12525 -->

<!-- VERBATIM-BEGIN id=S12795 src=CLAUDE.md@fde5030 lines=12795-13076 sha256=d3b1ede7bc0dce39e8798c07790ea79f9f50646970349d173635efbab5d819f8 -->
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

<!-- VERBATIM-END id=S12795 -->

<!-- VERBATIM-BEGIN id=S13077 src=CLAUDE.md@fde5030 lines=13077-13317 sha256=cbcf1913cb4543929ba618254c9759a0732fd2732742d60ad4b03b351bb7a9d9 -->
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

<!-- VERBATIM-END id=S13077 -->

<!-- VERBATIM-BEGIN id=S13540 src=CLAUDE.md@fde5030 lines=13540-13697 sha256=ec4ce9d6a0949a36f5a59e44d3d80fa78e6d6b89d6f479580e4e47c3b06d0c26 -->
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

<!-- VERBATIM-END id=S13540 -->

