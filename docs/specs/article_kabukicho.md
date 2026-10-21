# 記事用：新宿歌舞伎町

対象：新宿歌舞伎町の記事用ページ・画像・WordPress・記事コメント・ポスター

> このファイルは旧 `CLAUDE.md`（blob `fde5030`・commit `bfb9ad5`）から機械的に切り出した正式仕様の原文です。
> `VERBATIM-BEGIN` 〜 `VERBATIM-END` の間は1文字も変更しないこと（要約・統合・削除も禁止）。
> 新しい正式仕様は、このファイルの末尾（マーカーの外）へ追記してください。
> 完全一致の確認：`py -3.14 tools/verify_claude_split.py`

<!-- VERBATIM-BEGIN id=S19414 src=CLAUDE.md@fde5030 lines=19414-19751 sha256=4330548a3746bd5133835f2f1ef7f64f80824f279a17e5ed535fb9abf605c63a -->
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

<!-- VERBATIM-END id=S19414 -->

<!-- VERBATIM-BEGIN id=S19752 src=CLAUDE.md@fde5030 lines=19752-20004 sha256=089ba83065a7f2be83e921bf74d9bce70ef6eebb8dcab6c27001d00f900f802c -->
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


<!-- VERBATIM-END id=S19752 -->

<!-- VERBATIM-BEGIN id=S20005 src=CLAUDE.md@fde5030 lines=20005-20173 sha256=a3480706425a8103c7e6ce8a10e6550bc17e56697d15219449e5922dc1dc2e8f -->
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


<!-- VERBATIM-END id=S20005 -->

<!-- VERBATIM-BEGIN id=S20352 src=CLAUDE.md@fde5030 lines=20352-20624 sha256=df2cafdc064a55a40b617e33b150be7baae0ac91733fb30f366400052859990d -->
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

<!-- VERBATIM-END id=S20352 -->

<!-- VERBATIM-BEGIN id=S20625 src=CLAUDE.md@fde5030 lines=20625-20835 sha256=9d214ec625544c2c775457e91d0242d83b023f992b9a9bbbce568ef7504b9594 -->
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

<!-- VERBATIM-END id=S20625 -->

<!-- VERBATIM-BEGIN id=S20836 src=CLAUDE.md@fde5030 lines=20836-21137 sha256=b579aedf5bca0ab92fc1f7554a621e4a01bf1aea6dd4d95971f8a6a96acbfaf5 -->
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

<!-- VERBATIM-END id=S20836 -->

<!-- VERBATIM-BEGIN id=S21138 src=CLAUDE.md@fde5030 lines=21138-21280 sha256=a766b93c5c6f2178ac57b1f7be060853b2f380b397ff0e40f1fdf67445bf37dd -->
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

<!-- VERBATIM-END id=S21138 -->

<!-- VERBATIM-BEGIN id=S21281 src=CLAUDE.md@fde5030 lines=21281-21393 sha256=d192ed3eb0377b50c13e9aadeafa5e058a3caf821f75d21313b18c559f23ef26 -->
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

<!-- VERBATIM-END id=S21281 -->

<!-- VERBATIM-BEGIN id=S21394 src=CLAUDE.md@fde5030 lines=21394-21580 sha256=66f6bf5cdd91ef6467a6b9d5495f10aea3abffbc16128f7a0d9213ae3426270b -->
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

<!-- VERBATIM-END id=S21394 -->

<!-- VERBATIM-BEGIN id=S22634 src=CLAUDE.md@fde5030 lines=22634-22674 sha256=883823d9e7c92eaaeb1727bf32c6ced8fe595d024dfdb4fe50dbe96eb3e99586 -->
## 【正式仕様】新宿歌舞伎町 記事用①：22択ポスターをアプリ内素材から読む（2026-09-24・`35f16dd`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】記事用①「WordPressメディアから選ぶ」の22択ポスターのみ**。
**Cloud 実機確認済み（ユーザー承認）。**`35f16dd` は現HEADの祖先であることを確認済み。reset・revert しない。
（`92ac8af` / `ee39cd7` の「WordPressメディアをGETして表示」節は当時の正式記録として残し、本節が後発仕様として上書きする。）

### ① 読み込み元
- Cloud で**選択・プレビュー・⑧本番**に使うポスターは、**`assets/posters/kabukicho/` のアプリ内素材**を読む（`_art_poster_local()`）。
- **`manifest.json`** で「ラベル → 素材ファイル（英字名：`day06.jpg` / `tsuku7.jpg` 等・`_ART_POSTER_SLUGS`）」を管理し、
  メディアID・元ファイル名・sha256・同期日を**記録として**保持する。**実行時の読み込みはID・URL・認証情報に依存しない。**

### ② 維持する仕様
- **手動アップロード画像を最優先**（素材も読まない）。手動画像を削除すると選択済み素材へ戻る。
- **22択・最大1件・日付単位保存・⑦／⑧の共通入力（`_art_poster_inputs()`）・⑧の `_wp_poster.jpg` 結合**は維持。

### ③ 通信しない
- Cloud では **WordPress REST API・画像本体へのGETを行わない**＝ConnectTimeout の影響を受けない。
- **素材未同期時は安全な「未同期」エラー**を表示し、CloudからWordPressへ**暗黙フォールバックしない**。
- 旧「🔄 再取得」ボタンは不要となったため**表示しない**。

### ④ 差し替え手順
1. WordPress メディアへ追加（差し替えは `6日2.jpg` のような**末尾連番**）
2. ローカルで **`py -3.14 sync_kabukicho_posters.py`**（`--dry-run` で比較のみ）
3. **素材・manifest の変更だけ**を明示指定で commit・push → **Cloud を Reboot**

同期ツールは **WordPress への GET のみ**。既存の `_art_poster_resolve()` を再利用し、**ラベル名＋末尾連番の最新版**を選び、
**ID 29・44 は除外**する。**1件でも失敗したら素材を部分更新しない**（何も書き込まずに中止）。Cloud では実行できない。

### ⑤ 確認
`1日`（ID21）／`6日`（ID26）／`7のつく日`（ID127・`7のつく日2.jpg`）を **Cloud で選択・即時表示できることを確認済み**。

### ⑥ 変更しないもの
他店舗・他ページ・WordPress投稿／メディア操作・画像生成仕様・Secrets。

### ⑦ 禁止事項
1. ポスター表示で WordPress へ GET する方式へ戻さない／Cloud で暗黙フォールバックしない
2. 実行時の読み込みをメディアID・URLに依存させない（manifest のラベル→ファイルが正）
3. 同期ツールで部分更新しない／29・44 を使わない／POST・PUT・PATCH・DELETE を行わない
4. 手動アップロード優先・22択・最大1件・日付単位保存・⑧結合を変更しない
5. `35f16dd` へ reset・revert しない

<!-- VERBATIM-END id=S22634 -->

<!-- VERBATIM-BEGIN id=S22727 src=CLAUDE.md@fde5030 lines=22727-22759 sha256=0236c50c05c221bb7a24e64f3fb144edd257524a67e20765da2f8eb0a6f44387 -->
## 【正式仕様】新宿歌舞伎町 記事用：自動全台系画像のサマリーを並び画像と同じピンクバーに（2026-09-24・`3aabf82`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】記事用の「自動全台系画像」だけ**。
**Cloud 実機確認済み（ユーザー承認）。**`3aabf82` は現HEADの祖先であることを確認済み。reset・revert しない。

### ① 仕様
- 表の下にあった**王冠付きサマリー（`_build_article_machine_img()`）を廃止**し、**③並び画像と同じ既存のピンクサマリーバー**へ変更した。
  描画は記事用の並びと同じ **`_build_machine_img(grp, title, summary_stat, no_bar=True, hq_scale)`**（中央寄せ・書体は既存の記事用ゲートがそのまま効く）。
- 画像構成は記事用の並びと同様に **「機種パネル → 表 → ピンクバー → スランプ」**。**青いタイトルバーは付けない**（機種名はパネル・表に出る）。
- ピンクバーへ渡す総差枚・平均・勝率・台数は、**従来の王冠付きサマリーと同じ `_stat_from_diff(dr_m)`**（同じ判定・同じ値）。

### ② 実装
- `run_auto_pipeline()` / `run_step1_main()` に **`zen_pink_bar: bool = False`（既定OFF＝従来の王冠付き）**を追加。
- ゲートは **`_ART_ZEN_PINK_STORES = {"新宿歌舞伎町"}`**。**記事用の⑦・⑧の pipeline 呼び出しだけ** `zen_pink_bar=(store in _ART_ZEN_PINK_STORES)` を渡す。
- **⑦プレビュー／🔄その他を更新／⑧本番／WordPressへ送る画像**は、いずれも**同じ抽出処理（pipeline）の出力**を使う。

### ③ 対象外・非変更
- **②個別入力の「全台」画像は対象外**で従来どおり（王冠付き）。
- 表・パネル・スランプ・台番・抽出／全台系判定・結果テキスト・画像名は変更しない。
- 新宿歌舞伎町の記事用以外（既存エスパス店舗の結果ポスト用／スランプ付き結果、かぶぱ、他店舗の記事用、「その他」配下、WordPress本文）は不変。

### ④ 検証
2026/9/23 の実データで**ワールドダイスター・ケロット5BT**を確認。全台系2枚は並び画像の描画と画素一致、数値は王冠版と同一
（例：ワールドダイスター＝総差枚 +24,150枚／平均 +6,038枚／勝率 100.0%(4/4台)）。**全台系以外の画像はファイル単位で完全一致、
全台系・高配分の判定値（台数・平均・台番）も不変**。

### ⑤ 禁止事項
1. `zen_pink_bar` の既定を True にしない／新宿歌舞伎町の記事用⑦⑧以外へ渡さない
2. 独自デザインや生成後の画像貼り替えで代替しない（並び画像と同じ描画関数を使う）
3. 集計値の計算元（`_stat_from_diff(dr_m)`）を変えない
4. ②個別「全台」画像へ広げない（別途指示がない限り）
5. `3aabf82` へ reset・revert しない

<!-- VERBATIM-END id=S22727 -->

<!-- VERBATIM-BEGIN id=S22760 src=CLAUDE.md@fde5030 lines=22760-22792 sha256=63c96f7466ba5bde675cab3fb7d4af7a627c31ae3c6967d271c228dd5e31f02f -->
## 【正式仕様】新宿歌舞伎町 記事用：自動全台系ピンクバーの台数表記を「総台数台中プラス台数台+」に（2026-09-24・`3221897`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】記事用の自動全台系画像、表下のピンクサマリーバーのみ**。
**Cloud 実機確認済み（ユーザー承認）。**`3221897` は現HEADの祖先であることを確認済み。reset・revert しない。
（`3aabf82` のピンクバー化の節の追加仕様。同節は変更しない。）

### ① 仕様
- 勝率の台数表記を、従来の **`（プラス台数/総台数台）`** ではなく **`（総台数台中プラス台数台+）`** とする。
  例：従来の `（4/4台）` → **`（4台中4台+）`**。
- 分子・分母は**従来と同じプラス台数（`win_count`）・総台数（`total_count`）**。`+` はプラス台数の直後に**1つだけ**付ける。
- 総差枚・平均差枚・全台系判定・表・パネル・スランプ・画像名・結果テキストは不変。

### ② 実装
- 表記を作る正規箇所は **`_build_machine_img()` のピンクバー（part2）**。任意キー **`summary_stat["count_style"] == "of_plus"`** のときだけ新表記、
  キーが無ければ従来の `（○/○台）`（＝**既定OFF**・関数の引数は増やしていない）。
- 指定するのは**新宿歌舞伎町の記事用・自動全台系を描く呼び出し（`run_step1_main` の `zen_pink_bar` 分岐）だけ**。
- **⑦プレビュー／🔄その他を更新／⑧本番／WordPress送信画像**は同じ抽出処理（pipeline）の出力を使う。

### ③ 対象外
②個別「全台」・③並び・高配分・ジャグラー・その他優秀台・既存エスパス店舗・かぶぱ・「その他」配下・他店舗の記事用・WordPress本文。

### ④ 検証
2026/9/23 の実データで **ワールドダイスター＝`（4台中4台+）`、ケロット5BT＝`（3台中3台+）`** を確認（Cloud でも確認済み）。
全台系2枚は表部分が画素一致・サイズ同一で、変わったのはピンクバーの文字だけ。**表記指定なしのページ・画像は従来表記のまま変更前と画素一致**
（新宿歌舞伎町記事用の並び相当／高田馬場記事用／新小岩結果ポスト／稲毛スランプ付き／プレサス飯田橋、タイトルバーあり・なし）。

### ⑤ 禁止事項
1. `count_style` を指定なしで新表記にする実装へ変えない（既定は従来表記）
2. 新宿歌舞伎町の記事用・自動全台系以外へ `count_style` を渡さない
3. 全体置換・画像生成後の文字列置換で実現しない
4. 分子・分母の値や `+` の位置・個数を変えない
5. `3221897` へ reset・revert しない

<!-- VERBATIM-END id=S22760 -->

<!-- VERBATIM-BEGIN id=S22793 src=CLAUDE.md@fde5030 lines=22793-22846 sha256=2e7307a1c77d8cdf6da75f7818557036a4d836b5fba1c58276103377cf64bf96 -->
## 【正式仕様】新宿歌舞伎町 記事用：「全台データ」画像の赤見出し・薄紫項目セル／白数値セル・罫線（2026-09-24・`361b912` / `18a9420` / `b7dbba7`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】記事用の「全台データ」画像（`全台データ.jpg`）だけ**。
**Cloud 実機確認済み（ユーザー承認）。**3commitとも現HEADの祖先であることを確認済み。reset・revert しない。
（渋谷新館の全台データ画像の既存節 `205ce21` ほかは当時の正式記録として残す。本節は新宿歌舞伎町の記事用だけの後発仕様。）

### ① commit の構成
| commit | 内容 |
|---|---|
| `361b912` | `_art_zendai_image()` に `red_theme`（既定 False）を追加。見出し `#dd3333`＋白文字・中央寄せ、文字黒、「平均」→「平均差枚」。この時点の本文は全面薄紫 |
| `18a9420` | 本文を**左の項目セル薄紫 `#D8C6E3`／右の数値セル白**に分け、項目名・数値を**各セル矩形の中央**へ配置 |
| `b7dbba7` | 項目セル／数値セルの境界に縦罫線1本、行間に横罫線2本を追加 |

### ② 生成経路とゲート
- 正規の生成箇所は **`_art_zendai_image(diff_raw, hq_scale=_ART_ZENDAI_HQ, red_theme=False)`** のみ。
- **⑦プレビュー・⑧本番はどちらも `red_theme=(store in _ART_ZENDAI_RED_STORES)` で同じ関数を呼ぶ。**WordPress送信画像は⑧の出力ファイル。
- **`_ART_ZENDAI_RED_STORES = frozenset({"新宿歌舞伎町"})`。`red_theme` の既定は False＝従来デザイン。**他店舗・他ページは従来のまま。

### ③ デザイン
| 要素 | 仕様 |
|---|---|
| 見出し「全台データ」 | 背景 **`#dd3333`**（WordPress H2 と同色・`_ART_ZENDAI_RED_TITLE_BG`）・**白文字**・帯全幅で中央寄せ |
| 左の項目セル（勝率／総差枚／平均差枚） | 背景 **`#D8C6E3`**（記事用スランプ背景の `C_ART_SLUMP_AREA_BG` を流用）・**黒文字** |
| 右の数値セル | 背景 **白**・**黒文字** |
| セル範囲 | 項目セル＝外枠の内側 `BD`〜`_val_x`、数値セル＝`_val_x`〜`_w - BD`。`_val_x` は従来の値の開始位置で、**セル幅は不変** |
| 配置 | 項目名・数値とも**それぞれのセル矩形を基準に水平・垂直中央寄せ**（`_put(..., cell_w=...)`）。**固定のずらし量で配置しない** |
| 表記 | 「平均差枚」（行順は 勝率 → 総差枚 → 平均差枚） |
| 罫線 | 外枠と同じ **`_ART_ZENDAI_BORDER`＝灰色 (128,128,128)**・同じ太さ **`BD`**。**`_val_x` の境界に見出し下（`BODY_TOP`）から下端までの縦罫線1本**、**勝率／総差枚・総差枚／平均差枚の間に画像全幅の横罫線2本** |
| サイズ | **748×298（HQ 2.0）で不変** |

**数値・集計（`_zendai_total_stat()`）・台数・判定（補正後平均+50枚以上で生成）・画像名は不変。**

### ④ 確認
- 2026/9/23 の実データ（Pision確定・749台）で生成し目視確認：勝率 47.4%（355/749台）／総差枚 +394,650枚／平均差枚 +527枚。
  見出し (221,51,51)・項目セル (216,198,227)・数値セル白、6セルとも左右・上下の余白差 0〜2px、罫線の追加差分は灰色 3,408px のみ。
- **指定なしの全台データ画像は倍率1.0（374×149）・2.0（748×298）とも変更前と画素一致。**
- **Cloud 実機でも表示を確認済み。**WordPress への通信は行っていない。

### ⑤ 対象外（不変）
②個別・③並び・高配分・ジャグラー・その他優秀台・全台系ピンクバー・末尾・結果テキスト・WordPress本文、
**渋谷新館を含む他店舗・他ページの全台データ画像**。

### ⑥ 禁止事項・保全対象
1. `red_theme` の既定を True にしない／`_ART_ZENDAI_RED_STORES` へ他店舗を勝手に追加しない
2. 生成後の貼り替え・後処理で実現しない（`_art_zendai_image()` の正規描画のみ）
3. 項目名・数値を固定のずらし量で配置しない（セル矩形基準の中央寄せを維持）
4. 本文を全面薄紫・全面白へ戻さない／「平均」表記へ戻さない
5. 罫線の色・太さを外枠と別の値にしない／縦1本・横2本の構成を変えない
6. 集計・判定・セル幅・画像サイズ・画像名を今回を理由に変更しない
7. ⑦だけ・⑧だけ別の指定にしない
8. `361b912` / `18a9420` / `b7dbba7` へ reset・revert しない
9. `wrt_machines.json` の既存差分・未追跡ファイル・stash・既存自動commit履歴を保全する


<!-- VERBATIM-END id=S22793 -->

<!-- VERBATIM-BEGIN id=S22847 src=CLAUDE.md@fde5030 lines=22847-22943 sha256=e499e5e3c5dc4be6e8fb6c418a1592b4c6ae092aa244388f7fdd3467f9df778a -->
## 【正式仕様】新宿歌舞伎町 記事用：かぶぱ文章欄のCloud永続保存・本文H2・②予測候補の当日機種絞り込み・②個別「全台」のピンクバー化（2026-09-24・`657ba98` / `722dbc3` / `f50af5f`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】の記事用（`auto_article`）だけ**。
**Cloud 実機確認済み（ユーザー承認）。**3commitとも現HEADの祖先であることを確認済み。reset・revert しない。
途中のアプリ自動commit **`79e95ef`（`auto: 画像生成後の設定を保存`）は有効な履歴として保全**する。

| commit | 内容 |
|---|---|
| `657ba98` | ①かぶぱ文章欄3項目の追加（この時点の保存先は store_settings＝**後で廃止**）／②予測候補を当日設置機種へ絞り込み |
| `722dbc3` | かぶぱ文章欄を `article_shared_inputs.json` で Cloud 永続保存へ変更／本文の固定H2文言を変更 |
| `f50af5f` | ②個別画像「全台」を王冠付きサマリーからピンクサマリーバーへ変更 |

**対象外（不変）**：他店舗の記事用・結果ポスト用・スランプ付き結果・かぶぱページ（`auto_slump`）・`auto_slump2`・「その他」配下・ローテ・他店舗のWordPress本文。

### ① かぶぱポスト・ヒントの文章欄とCloud永続保存

- ①冒頭部分に3項目がある（`_ART_KABUPA_TOP_STORES = frozenset({"新宿歌舞伎町"})`）。
  - **かぶぱポストの見出し**（`art_kabupa_head_{store}`・text_input・「かぶぱポスト」見出しの直前）
  - **見出し下の文章**（`art_kabupa_head_text_{store}`・text_area）
  - **ヒント下の文章**（`art_kabupa_hint_after_{store}`・text_area・ヒント10の直下）
- WordPress本文の出力順（`wp_client.plan_blocks()` の nanako ブロック）：
  **固定H2 → 導入文 → [入力時のみ] H3見出し → 見出し下の文章 → かぶぱポスト（↓前日の夜に… ＋ 埋め込み） → ヒント見出し → ヒント1〜10 → ヒント下の文章 → 締め文**。
  固定H2は置き換えず現在の位置のまま残す。
- 空欄（空白・改行だけを含む）なら該当ブロックを出さない。**空H3・空段落・余計な空行を作らない。**
  3項目が空なら本文は項目追加前と完全一致。キーを渡さない店舗（渋谷新館など）は1ブロックも変わらない。
- 改行を含む文章は既存の記事上部文章欄と同じ **`_split_para()`**（改行で段落・空行は落とす）で処理する。
- 3項目は**日付に依存しない新宿歌舞伎町の記事用共通値**（日付単位の `article_page_inputs.json` には入れない。`_article_input_keys()` 非登録）。
- **`store_settings/新宿歌舞伎町.json` は保存先として使わない**（`657ba98` の旧方式・読み書きとも廃止）。
  過去に入った `art_kabupa_*` の空キーは参照されない残置（削除しない）。
- **正規保存先は `article_shared_inputs.json`**（`{店舗: {head, head_text, hint_after}}`・初期ファイル `{}` はcommit済み）。
  - **Cloud**：`_GH_SYNC_FILES` に追加済みで**起動時に GitHub から復元**。入力確定時（`on_change`）に
    **`_github_push_file(..., base_sha=読み込み時SHA)` で即同期**（rote_machines.json と同じ正規経路）。
  - **ローカル**：ファイルへ即保存し、既存 `_git_auto_push()` の targets（`article_shared_inputs.json` を追加済み）で push。
  - **値が変わらないときは書き込み・pushしない。空欄への変更も空欄として保存する。**
  - **競合（SHA不一致・409）時は自動マージ・古い値の再送をせず、最新値を画面へ戻してトーストで通知**する。
  - widget key は日付スコープにしない（`_artw_*` を使わない）。初期値は `value=保存値` でブラウザへ渡す。
- 関数：`_art_kabupa_top_key()` / `_load_art_shared_inputs()` / `_art_kabupa_top_saved()` / `_art_kabupa_top_current()` / `_save_art_kabupa_top()`。
- ★この節は「## Cloud ↔ GitHub 同期の正式仕様（2026-08-05・`f3ff59c`）」の同期対象（当時は weekly_items / rote_machines のみ）へ
  `article_shared_inputs.json` を**後発で追加**したもの。同節は当時の記録として残す（書き換えない）。
- 確認：ローカルで「初回表示直後の入力→保存→プロセス再起動→再読込→日付変更→ページ再訪問」で3項目とも復元。
  **Cloudで入力→再読込→Reboot→再訪問→日付変更後も復元することを確認済み。**
  （検証途中の「初回入力が保存されない」は、ブラウザ自動操作が入力欄へ文字を入れられていなかった操作側の問題で、アプリの不具合ではなかった。）

### ② WordPress本文の固定H2（新宿歌舞伎町の記事用のみ）

| 旧 | 新（正式） |
|---|---|
| かぶぱポストに仕掛けのヒントを確認！ | **かぶぱポストは毎日チェック！**（`NANAKO_TEXT_BY_STORE["新宿歌舞伎町"]["h2"]`） |
| 全台系濃厚機種が複数 | **全？**（`H2_ZENDAI_ALT`） |
| 高配分機種も複数 | **1/2系以上？**（`H2_HIGH_ALT`） |
| 並び・列仕掛けも！ | **並びも複数！**（`H2_NARABI_ALT`） |

- `h2_alt`（`_ART_WP_TITLE2_STORES`＝新宿歌舞伎町だけが渡す）の分岐と店舗別文言辞書で切り替える。**全体文字列置換・送信直前の後処理は使わない。**
- 旧文言は本文に出さない。**H2の順序・数・HTMLタグ・上記以外の本文は不変。**`H2_ZENDAI` / `H2_NARABI` / 渋谷新館の文言も不変。

### ③ ②全台系・高配分の予測候補を当日設置機種へ絞る

- ②入力欄の予測機種候補は、取得データ表と同じ **`normalize_df` → `apply_name_conversion`** 済みの当日機種名
  （`_art_view_df_{store}` の機種名列・現在のExcelと一致するときだけ）と **`_normalize_key`** で照合した**当日設置機種だけ**を表示する
  （`_ART_KOJIN_CAND_TODAY_STORES` / `_art_today_candidates()`）。
- 店にない機種は候補に出さない。**階別候補（・2F / ・3F）は元機種が当日設置されていれば残す。**
  **変換マスタ未登録の当日機種は候補へ追加する。当日データがない場合は従来どおり全候補。**
- **保存済み入力は削除・書き換えせず、候補表示だけを絞る。**判定・画像・結果テキストは不変。
- 確認：9/23実データ（749台・78機種）で全408候補→82候補（78機種＋階別4）、非設置機種0件・設置機種の取りこぼし0件。

### ④ ②個別画像「全台」のピンクバー化

- 新宿歌舞伎町の記事用の②個別「全台」画像は、自動全台系・③並びと同じ **「機種パネル → 表 → ピンクサマリーバー → スランプ」**。**王冠付きサマリーは出さない。**
- 描画は⑦・⑧共通の **`_art_kojin_zen_img()`**。`_ART_ZEN_PINK_STORES` の店舗は自動全台系（`run_step1_main` の `zen_pink_bar`）と同じ
  **`_build_machine_img(grp, title, {**stat, "count_style": "of_plus"}, no_bar=True, hq_scale=...)`**。他店舗は従来の `_build_article_machine_img()`（王冠付き）。
- 総差枚・平均差枚・勝率は従来と同じ **`_stat_from_diff`** の値。台数表記は **`（総台数台中プラス台数台+）`**（例 `（13台中12台+）`）。
- **②個別「全台」へ入力した機種を自動全台系候補から除外する既存仕様（`7b433da`）は維持。**
- ②個別「優秀台」・自動全台系の判定・台番・表・パネル・スランプ・画像名・結果テキストは不変。
- 経緯：Cloudで王冠付きだった マギレコ／ドラハナ閃光30 は自動全台系ではなく②個別「全台」の画像だった（自動全台系のピンクバー `3aabf82` は正しく動作していた）。
- 確認：9/1実データでマギレコ 総差枚+59,650枚・平均+4,588枚・92.3%（13台中12台+）、ドラハナ閃光30 +39,300枚・+2,807枚・100.0%（14台中14台+）。
  自動全台系はアニスロドッチのみで②入力機種の混入なし。他店舗の②個別「全台」は変更前と画素一致。
  **Cloudで マギレコ／ドラハナ閃光30 の②個別「全台」画像がピンクバーになっていることを確認済み。**

### ⑤ 共通

- ⑦プレビュー・🔄その他を更新・⑧本番・WordPress送信直前payloadで同じ仕様（同じ関数・同じ保存値を通る）。
- 検証中の WordPress 通信は**0件**（POST / PUT / PATCH / DELETE・下書き作成・更新・公開・メディア操作なし）。実データ取得は Pision 確定 GET のみ。
- 実データ検証済み・Cloud 確認済み。

### ⑥ 禁止事項

1. かぶぱ文章3項目を `store_settings` や `article_page_inputs.json`（日付単位）へ保存しない／日付スコープのキーにしない
2. `article_shared_inputs.json` を `_GH_SYNC_FILES` / `_git_auto_push()` の targets から外さない
3. SHA確認なしの push・競合時の自動マージ・古い値の再送をしない／値不変時に書き込み・pushしない
4. 空欄時に空H3・空段落を出さない／固定H2を置き換えない／出力順を変えない
5. 本文H2を旧文言へ戻さない／全体文字列置換・送信直前の後処理で実現しない／他店舗の本文を変えない
6. 予測候補の絞り込みで保存済み入力を削除・書き換えない／判定・画像・結果テキストへ波及させない
7. ②個別「全台」へ王冠付きサマリーを戻さない／②個別「優秀台」・他店舗へ広げない／自動全台系からの除外仕様を外さない
8. 生成後の画像貼り替えで代替しない（`_art_kojin_zen_img()` の正規描画を使う）
9. `657ba98` / `722dbc3` / `f50af5f` / `79e95ef` へ reset・revert しない
10. `wrt_machines.json`・`article_page_inputs.json` 等の既存dirty・未追跡ファイル・stash・自動commit履歴を保全する

<!-- VERBATIM-END id=S22847 -->

<!-- VERBATIM-BEGIN id=S22944 src=CLAUDE.md@fde5030 lines=22944-23080 sha256=e9c9591e3a1e7ed4c929373108d851cde416efc3db774f3243e50f399c38b284 -->
## 【正式仕様】新宿歌舞伎町 記事用WordPress：本文順・全台データ3分岐・かぶぱ7項目・H2/H3・ランキング停止・アイキャッチ（2026-09-25・`0b774f8` / `af9a7f2` / `3519480` / `66ba162` / `154dbd3` / `a2bd02c`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）のWordPress本文・下書き作成だけ**。
2026-09-25 に **Cloud で新宿歌舞伎町の記事用WordPress下書きを作成し、①でポスターを選択した状態でアイキャッチも正常に設定されることを確認済み（ユーザー承認）**。
既存節（`2e3a694` の渋谷新館コメント、`657ba98` / `722dbc3` / `f50af5f` のかぶぱ文章欄ほか）は削除・書き換えしない。
本節と矛盾する既存記述（かぶぱブロックの位置・任意3入力の本文出力・`全？` / `1/2系以上？` / `【全台系】` などの旧文言）は、本節が後発仕様として上書きする。

### A. 正式commit（6件・すべて現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| `0b774f8` | 差枚数ランキング停止・かぶぱブロックを本文最後へ移動 |
| `af9a7f2` | 全台データ画像をWordPress本文へ独立配置 |
| `3519480` | 店舗全体の平均差枚による全台データ画像の3分岐 |
| `66ba162` | かぶぱブロックを7項目へ整理 |
| `154dbd3` | H2/H3文言の変更 |
| `a2bd02c` | ①で実際に使ったポスターをアイキャッチへ設定 |

途中の **`c0b6ea3`（機種名変換マスタ更新）・`8d3faef`（auto: 画像生成後の設定を保存）はアプリの自動commit**。有効な履歴として保全し、reset / revert しない。
**これらの commit へ reset してはならない**（正式仕様の根拠commitであって、HEAD を戻す意味ではない）。

### B. WordPress本文の掲載順

```
冒頭 → 全台データ画像（+150枚以上のとき）→ 全台？ → ニブイチ系も大量！ → 並びも複数！
→ ⑤オススメポスター機種の優秀台 → その他の単品優秀台 → かぶぱ（7項目）
→ 全台データ画像（+50〜+149枚のとき）
```

- **かぶぱブロックは本文末尾**。平均差枚 +50〜+149枚の日だけ、その**完全な後ろ**に全台データ画像を置く。
- 実装は `payload["nanako_last"]`（`_ART_WP_NANAKO_LAST_STORES = {"新宿歌舞伎町"}`）。`wp_client.plan_blocks()` がかぶぱブロックを別リスト `_nk_plan` に組み、キーのある店舗だけ末尾（ボタンの前）へ置く。**既定は従来位置**。
- **HTML生成後の文字列置換ではなく、plan の正規ブロック順で並べる。**
- ⑤オススメは従来どおり並びとその他の間。

### C. 差枚数ランキング（新宿歌舞伎町の記事用は停止）

- **生成・ZIP・payload・最終HTML・WordPress掲載のすべてで0件。**
- 定数 **`_ART_RANK_OFF_STORES = {"新宿歌舞伎町"}`** ＋ **`_art_rank_on(store)`**（`_ART_RANK_STORES` かつ OFF集合外）。⑦・⑧の画像生成はこの判定だけを見る。
- ⑧では前回出力の `差枚数ランキング.jpg` を `_rm_stale_image()`（完全一致）で削除する。
- payload の `ranking` / `zendai_data` は**空リストで渡す**（キーを落とすと「シマズをチェック！」H2が出るため）。
- **`_art_ranking_image()`・集計・順位選択UI・素材は削除しない。**復活は OFF集合から外すだけ。渋谷新館は従来どおり生成・掲載。

### D. 全台データ画像の平均差枚3分岐

判定値は **`_art_zendai_stat(diff_raw)["avg_diff"]`**（画像に表示する平均差枚・既存の+50判定と同じ整数）。**表示文字列で比較しない。**

| 平均差枚 | 画像 | 掲載位置 | payload |
|---|---|---|---|
| **+150枚以上** | 生成 | **冒頭の直後に1枚** | `zendai_top` |
| **+50〜+149枚** | 生成 | **かぶぱブロック全体の後ろ・本文最後に1枚** | `zendai_bottom` |
| **+49枚以下** | **生成しない** | 載せない | どちらのキーも入れない |

- しきい値は `_ART_ZENDAI_TOP_MIN_AVG = 150` と既存 `_ART_ZENDAI_MIN_AVG = 50`。
- +49枚以下は⑧が前回の `全台データ.jpg` を `_rm_stale_image()` で削除するため、**出力フォルダ・ZIP・payload・HTML・送信対象へ混入しない**。
- **H2は付けない**（旧「差枚数ランキング」H2ブロックは出さない）。
- **赤見出し・薄紫項目セル／白数値セル・罫線・中央寄せ・サイズ・集計（`_art_zendai_image()` / `_zendai_total_stat()`）は不変。**

### E. かぶぱブロック（7項目だけ）

1. H2 `かぶぱポストは毎日チェック！`
2. 固定導入文「前日の夜に配信されるかぶぱのポストには仕掛けのヒントが隠されていることが多め。今回もヒントがあった？」
3. `↓前日の夜に配信されたポストがコチラ`
4. Xのかぶぱポスト埋め込み
5. 固定文章「今回の結果から考えると下記のキーワードがヒントになっていたのかも？」
6. ヒント1〜10（入力済みのものだけ）
7. 固定締め文「かぶぱのポストは毎日チェックしましょう！」

- 文言は **`wp_client.NANAKO_TEXT_BY_STORE["新宿歌舞伎町"]`** の `lead` / `hint_lead` / `outro`。`nanako_texts()` の既定 `hint_lead` は従来の `NANAKO_HINT_LEAD`（**渋谷新館は不変**）。
- URLが空なら3・4を出さない、ヒント0件なら5〜7を出さない（従来どおり）。
- **旧H3・見出し下文章・ヒント下文章・重複導入文・旧締め文（「これらがヒントに…」「このように、かぶぱポストからは連日…」）は出力しない。**
- 任意3入力（見出し／見出し下の文章／ヒント下の文章）は **`_ART_KABUPA_TOP_OFF_STORES = {"新宿歌舞伎町"}` × `_art_kabupa_top_on()`** で画面表示も payload 受け渡しもしない。
  **`article_shared_inputs.json` の保存値・キー、`_ART_KABUPA_TOP_STORES`、Cloud同期経路（`_GH_SYNC_FILES` / `_git_auto_push` targets / SHA確認）は削除せず保持**する（復活は OFF集合から外すだけ）。

### F. H2/H3文言（`h2_alt` / `h3_zendai_alt` の店舗だけ）

| 種類 | 定数 | 正式文言 |
|---|---|---|
| H2 全台系 | `H2_ZENDAI_ALT` | **全台？** |
| H2 高配分 | `H2_HIGH_ALT` | **ニブイチ系も大量！** |
| H2 並び | `H2_NARABI_ALT` | **並びも複数！** |
| H3 全台系 | `H3_PREFIX_ZENDAI_ALT` | **【全台？】** |
| H3 高配分 | `H3_PREFIX_HIGH_ALT`（新設） | **【ニブイチ系】** |

- 共通の `H3_PREFIX_HIGH = "【高配分】"` / `H3_PREFIX_ZENDAI` / `H2_ZENDAI` / `H2_HIGH` は変更しない（他店舗が使用）。
- **画像名・画像内の文字・結果テキストの見出し（`👑優秀機種` / `👑高配分機種` 等）は変更しない。**

### G. アイキャッチ（`featured_media`）

⑧でポスターを作った時点で、①で**実際に採用した**ポスターから `payload["featured"]` を決める（`streamlit_app._art_wp_featured_for()`・`_ART_WP_FEATURED_STORES = {"新宿歌舞伎町"}`）。手動優先の判定は `_art_poster_inputs()` と同じ。

| ①の状態 | アイキャッチ |
|---|---|
| **22択ポスター** | `assets/posters/kabukicho/manifest.json` の元WordPressメディアID（**1日=21／6日=26／7のつく日=127**）。**除外ID 29・44 は使わない** |
| **手動アップロード** | 本文用にアップロードした **同じ `_wp_poster.jpg` のメディアID**。**二重アップロードしない** |
| **未選択・未アップロード** | 投稿payloadへ `featured_media` を**入れない**（従来どおりアイキャッチなし） |

- 送信時に `wp_client.resolve_featured()` がIDを確定し、`create_draft(featured_media=…)` へ渡す。**正の整数のときだけ**キーを追加（0・None・不正値は送らない）。
- manifest のIDが欠損・不正・除外IDなら、**代替画像を使わず**アイキャッチなしで下書き作成を続け、画面と結果に理由を表示する。
- 手動ポスターのアップロード失敗は既存の本文画像アップロード失敗として停止（投稿を作らない）。
- 22択のIDは **新宿歌舞伎町専用接続（`WP_SECRET_KEYS_BY_STORE`）で送るときだけ使う**。共通接続へフォールバックした場合はアイキャッチなし＋理由表示。
- **①のポスター選択状態が⑧実行時に残っていることが必須。日付だけで自動選択はしない。**
- **Cloud実行時、22択は manifest のIDを使うため WordPress メディアの GET は不要。**手動はアップロード結果のIDを使う。
- **Cloudで、選択済みポスターのアイキャッチ設定を確認済み。**
- 新宿歌舞伎町以外・他ページの投稿payloadに `featured_media` を追加しない。
- 調査記録：アプリは `17b17be` 以降一度も `featured_media` を送っていなかった。過去投稿（387 / 120 / 51 / 49 / 43 / 16）のアイキャッチは管理画面での手動設定だった。本仕様は復旧ではなく**新仕様**。

### H. 共通・検証

- ⑦プレビュー・🔄その他を更新・⑧本番・送信直前payload・最終HTMLの整合を維持する。
- 実装・検証中の WordPress 書き込みは0件（HTTPモック・Pision確定GETのみ）。**Cloud確認として、選択済みポスターで実際に下書きを作成しアイキャッチ設定を確認済み。**
- 検証：9/23 実データ（749台）で本文順・ランキング0件・全台データ3分岐（+527 / +150 / +149 / +100 / +50 / +49 / 0）・かぶぱ7項目・H2/H3・アイキャッチ（22択3種／手動／未選択／manifest不正4種／アップロード失敗）を確認。渋谷新館・高田馬場の plan / HTML / 投稿payload は変更前と一致。

### I. 対象外（変更しない）

他店舗の記事用（高田馬場・渋谷新館・秋葉原）／結果ポスト用／スランプ付き結果／かぶぱページ（`auto_slump`）／`auto_slump2`／「その他」配下／ローテ／他店舗のWordPress本文。
全台・高配分・並び・⑤・その他優秀台・全台データ画像の**画像内容・判定・結果テキスト・台番・スランプ・パネル・画像名**、WordPressタイトル・カテゴリ・著者・ステータス、ポスターのローカル素材化・22択・手動優先・専用Secrets。

### J. 禁止事項

1. かぶぱブロックを旧位置（冒頭直後）へ戻さない／`nanako_last` の既定を True にしない
2. 並び替え・非出力を HTML の後処理・全体文字列置換で実現しない
3. 新宿歌舞伎町の記事用で差枚数ランキングを復活させない／ランキングの機能・素材・集計を削除しない
4. `ranking` / `zendai_data` キーを payload から落とさない（空リストで渡す）
5. 全台データの判定を表示文字列にしない／しきい値150・50を変えない／+49枚以下で掲載しない
6. 全台データ画像のデザイン・集計・サイズを変更しない
7. かぶぱの旧H3・見出し下文章・ヒント下文章・旧導入文・旧締め文を本文へ戻さない
8. `article_shared_inputs.json` の任意3入力の値・キー・同期経路を削除・初期化しない
9. 共通の見出し定数（`H3_PREFIX_HIGH` 等）を書き換えて他店舗へ波及させない／画像名・結果テキストの見出しを変えない
10. アイキャッチに代替画像・先頭画像を使わない／`featured_media=0` を送らない／アイキャッチ用の二重アップロードをしない
11. 22択のアイキャッチで WordPress メディアを GET・再検索しない／ID 29・44 を使わない
12. 他店舗・他ページの投稿payloadへ `featured_media` を足さない
13. 6件の正式commit・途中の自動commit（`c0b6ea3` / `8d3faef`）へ reset・revert しない

### K. 保全対象

`wrt_machines.json`・`article_shared_inputs.json`・`auto_page_inputs.json`・`article_page_inputs.json` の既存差分、未追跡ファイル、stash 4件、既存の自動commit履歴。

<!-- VERBATIM-END id=S22944 -->

<!-- VERBATIM-BEGIN id=S23081 src=CLAUDE.md@fde5030 lines=23081-23146 sha256=3fa3c02cf16e3bba924a03a0dae6672da4d50c6655d2ff92a4dbfdadd7495f11 -->
## 【正式仕様】新宿歌舞伎町 記事用：末尾画像のサマリーを③並びと同じピンクバーに（2026-09-25・`9fa7eee`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）で生成する末尾画像だけ**。
**通常末尾・ジャグラー末尾の両方**が対象。2026-09-25 に **Cloud で王冠なし・ピンクバー表示・記事用の中央寄せと書体を確認済み（ユーザー承認）**。
既存節（`6fdf731` の末尾モード表示名、`3aabf82` / `3221897` / `f50af5f` の全台系・②個別「全台」ピンクバー ほか）は削除・書き換えしない。

### A. 正式commit

| commit | 内容 |
|---|---|
| **`9fa7eee`** | `feat: 新宿歌舞伎町記事用の末尾画像のサマリーを並びと同じピンクバーに`（`streamlit_app.py` のみ） |

`9fa7eee` は現HEADの祖先であることを確認済み。直前の **`175745e`（アプリの自動commit）** は有効な履歴として保全する。
**`9fa7eee` へ reset してはならない**（正式仕様の根拠commitであって、HEAD を戻す意味ではない）。

### B. 仕様

- **集計を表示する末尾画像**（「全台」／プラス台・優秀台の「平均差枚付き」）は、**王冠付きサマリーを出さず**、表の下に **③並び画像と同じ既存のピンクサマリーバー**を表示する。
- 構成は **既存の表（必要なら既存パネル等）→ ピンクバー → スランプ**。王冠付きサマリーは出さない。
- **集計を表示しない「平均差枚なし」モードは従来どおり表だけ**で、ピンクバーを追加しない。
- ピンクバーは **既存の `_build_machine_img(..., no_bar=True)` の正規描画を流用**する。新デザイン・生成後の貼り替えは作らない。
- 総差枚・平均差枚・勝率・台数は、**従来の王冠付きサマリーと同じ既存集計値（`_stat_of`）**をそのまま渡す。末尾用の別計算をしない。
- 台数表記は③並びと同じ既存ルール **`（x/y台）`**（`count_style` は渡さない）。
- 中央寄せ・書体は既存の記事用ゲート（`_art_summary_center()` / `_art_font_new()`）がそのまま効く。

### C. 実装

- 共通の **`_build_sue_images()` に `sue_pink_bar: bool = False`** を追加。`article_mode` かつ集計ありのときだけピンクバーで描く。
- 店舗ゲートは **`_ART_SUE_PINK_STORES = frozenset({"新宿歌舞伎町"})`**。
- **ONにするのは記事用⑦プレビュー・⑧本番の2呼び出しだけ**（`sue_pink_bar=(store in _ART_SUE_PINK_STORES)`）。
- **既定 False** のため、通常ページの `_gen_sue_imgs_on_fly` ・他店舗の記事用は従来の王冠付きサマリー（または従来表示）を維持する。
- 🔄その他を更新は⑦で作った末尾画像をそのまま使うため、**⑦・🔄・⑧・WordPress送信画像で同じ見た目**になる。

### D. 不変

末尾抽出条件／末尾番号・ゾロ目判定／台番／表／パネル／スランプ／画像名／画像順／結果テキスト。

### E. 対象外

新宿歌舞伎町の記事用の全台系・②個別「全台」・高配分・並び・全台データ画像・かぶぱ・WordPress本文。
新宿歌舞伎町以外の店舗・他ページ（結果ポスト用・スランプ付き結果・かぶぱページ・「その他」配下）の末尾画像。

### F. 検証

- 9/23実データ（Pision確定）で**通常末尾（7・8・ゾロ目）とジャグラー末尾（7・ゾロ目）**を4モードすべて生成。集計付きは全画像ピンクバーあり・王冠0件、画像名・掲載台番・枚数は変更前と同一。
- 目視：末尾7番台で王冠版「勝率40.5%(30/74台)・総差枚-2,950枚・平均-40枚」とピンクバーの数値が一致。
- **Cloudでも王冠なし・ピンクバー・記事用の中央寄せと書体を確認済み。**
- 非回帰：**指定なし（既定False）・平均差枚なし・高田馬場・新小岩の末尾画像が変更前と画素一致**。
- WordPress通信0件（Pision確定GETのみ）。

### G. 禁止事項

1. 新宿歌舞伎町の記事用末尾画像へ王冠付きサマリーを戻さない
2. 「平均差枚なし」モードへピンクバーを追加しない
3. 独自のピンクバー描画・生成後の貼り替えを作らない（`_build_machine_img(no_bar=True)` を使う）
4. 末尾用に集計を別計算しない／台数表記を `（x/y台）` 以外にしない（`of_plus` を渡さない）
5. `sue_pink_bar` の既定を True にしない／`_ART_SUE_PINK_STORES` へ他店舗を勝手に追加しない
6. 通常ページ（`_gen_sue_imgs_on_fly`）へ `sue_pink_bar` を渡さない
7. ⑦だけ・⑧だけONにしない
8. 末尾抽出・ゾロ目判定・台番・表・パネル・スランプ・画像名・画像順・結果テキストを本仕様を理由に変更しない
9. `9fa7eee` / `175745e` へ reset・revert しない

### H. 保全対象

`wrt_machines.json`・`article_shared_inputs.json`・`auto_page_inputs.json`・`article_page_inputs.json` の既存差分、未追跡ファイル、stash 4件、既存の自動commit履歴。

<!-- VERBATIM-END id=S23081 -->

<!-- VERBATIM-BEGIN id=S23147 src=CLAUDE.md@fde5030 lines=23147-23215 sha256=f7ad41e51c0db4402d271e551b7565431a6c5d56db8fea400fa032636d017987 -->
## 【正式仕様】新宿歌舞伎町 記事用📝：末尾画像の掲載台を「その他の優秀台」から除外（2026-09-29・`6acfc8f` / `287883a`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）→ 📝記入部分のみ の「その他の優秀台」だけ**。
**Cloud 実画面で重複0台を確認済み（ユーザー確認）。**既存節は削除・書き換えしない。

### A. 正式commit（2件・いずれも現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| **`6acfc8f`** | `fix: 新宿歌舞伎町記事用📝で末尾画像の台をその他の優秀台へ重複させない` |
| **`287883a`** | `fix: 記事用⑧の末尾画像先行生成を新宿歌舞伎町×📝だけに限定` |

間の **`b102051`（`auto: 画像生成後の設定を保存`）はアプリの自動commit**。有効な履歴として保全する。
**どのcommitへも reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 仕様

- 末尾画像（通常末尾・ゾロ目・ジャグラー末尾を含む）に**実際に掲載された台番**は、
  +1,000枚以上などの条件で作る**「その他の優秀台」から除外**する。
- 除外に使うのは、末尾画像を作る既存関数 **`_build_sue_images()` の戻り値 `ban_out`（実掲載台番）**。
  **末尾条件に一致する全台を除外する仕様ではない**（画像に載らなかった台・別末尾・別機種は除外しない）。
- 除外は `_manual_sonota_auto_extract()` へ渡す除外台番へ足すだけ。新しい後処理・画像削除は作らない。
- 店舗ゲートは **`_ART_MANUAL_SUE_EXC_STORES = frozenset({"新宿歌舞伎町"})`**。

### C. ⑦・🔄・⑧

- **⑦プレビューと⑧本番で同じ末尾掲載台番（`_art_sue_ban` / `_art_sue_ban_e`）を除外に使う。**
  ⑦は `_art_manual and store in _ART_MANUAL_SUE_EXC_STORES` のときだけ除外を足す。
- **🔄その他を更新の既存仕様は変更しない**（元から末尾該当台を除外済み）。
- **⑧で末尾画像を「その他の優秀台」より先に生成するのは、新宿歌舞伎町×📝だけ**
  （`_art_sue_early = _art_exec_manual and store in _ART_MANUAL_SUE_EXC_STORES`）。
  末尾生成は `_art_gen_sue_e()` にまとめ、対象時はその他の前、それ以外は**従来位置（その他の後）**で1回だけ呼ぶ。
- **他店舗の記事用・新宿歌舞伎町の通常（🔍）経路では、従来の画像保存順・ログ順・ファイル追加順を維持する**
  （`6acfc8f` では全店舗で順序が変わっていたが `287883a` で対象限定へ戻した）。

### D. 変更しないもの

末尾画像の抽出条件・掲載台・集計値・ピンクバー・画像名、通常末尾／ジャグラー末尾それぞれの既存仕様、
その他の優秀台の既存抽出条件（+1,000枚以上等）・台番順・表・パネル・スランプ・画像名・結果テキスト、
ジャグラー統合の除外。

### E. 検証

- **9/16実データ（749台・Pision確定GETのみ）、末尾6番台＋「その他の優秀台：+1,000枚以上」で重複が 26台 → 0台**
  （その他 122 → 96台）。**末尾以外の対象台はその他に残る**（減ったのは重複台だけ・増0）。
  ゾロ目は 11台 → 0台、通常3＋ジャグラー0 は 14台 → 0台、ジャグラー末尾7・末尾なしは変化なし。
- 変更前（`6acfc8f~1`）と今回版の⑧ブロックを同一データで実行比較し、
  **新宿歌舞伎町の通常経路と高田馬場・渋谷新館・秋葉原の📝／通常経路（末尾6・ゾロ目・末尾なし）で
  呼び出し順・保存ファイル名と順序・画像内容・ログ順・ファイル一覧・結果テキスト用データが完全一致**（24ケースPASS）。
- **Cloud 実画面でも重複0台を確認済み。**
- **WordPress 通信・公開・下書き作成は行っていない。**

### F. 対象外

結果ポスト用（`auto`）／スランプ付き結果（`auto_slump` / `auto_slump2`）／かぶぱ／「その他」配下（`other_slump`）／
ローテ（`rote`）／他店舗の記事用。

### G. 禁止事項・保全

1. 除外を「末尾条件に一致する全台」へ広げない（`ban_out` の実掲載台番を使う）
2. ⑧の末尾先行生成を全店舗共通へ戻さない／`_art_sue_early` の条件を広げない
3. ⑦だけ・⑧だけ除外する状態にしない／🔄の既存仕様を変えない
4. `_ART_MANUAL_SUE_EXC_STORES` へ他店舗を勝手に追加しない
5. 末尾画像・その他の優秀台の既存仕様を本仕様を理由に変更しない
6. WordPress への POST / PUT / PATCH / DELETE・下書き作成・公開を行わない
7. `wrt_machines.json` の既存差分、未追跡ファイル、stash、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / revert / force push は禁止
8. `6acfc8f` / `287883a` / `b102051` へ reset・revert しない

<!-- VERBATIM-END id=S23147 -->

<!-- VERBATIM-BEGIN id=S23216 src=CLAUDE.md@fde5030 lines=23216-23303 sha256=89b09d775e658456a24c6176adc16f7eb7728403acca1040a39273f0bea800ca -->
## 【正式仕様】新宿歌舞伎町 記事用WordPress：長尺画像を分割せず原寸1枚で掲載（2026-09-29・`716d377`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）→ ⑧「WordPress下書きを作成」で送る本文画像だけ**。
**Cloud で実際に下書きを作成し、長尺画像が1枚として掲載・保存されることを確認済み（ユーザー確認）。**
既存節は削除・書き換えしない。2026-09-16「新宿歌舞伎町 記事用：並び・列のban_map再計算とWordPress狭幅画像の分割（`77e140d`）」の
**「マイジャグVを5分割」など新宿歌舞伎町の記事用での分割部分は、本節が後発仕様として上書きする**（同節は当時の記録として残す）。

### A. 正式commit

| commit | 内容 |
|---|---|
| **`716d377`** | `feat: 新宿歌舞伎町記事用のWordPress画像を分割せず原寸1枚で送る`（`streamlit_app.py` / `wp_client.py` のみ・+18 / −2） |

直後の **`85a7d19`（`auto: 画像生成後の設定を保存`）はアプリの自動commit**。有効な履歴として保全する。
**`716d377` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 仕様

- 縦長の「その他の優秀台」「末尾」「高配分」「②個別画像」などを、**分割片ではなく⑧で完成した元画像1ファイルのまま**アップロードし、
  **本文の img 要素も1件だけ**にする。
- **⑦プレビュー・ローカル出力・ZIP・画像生成・画像の解像度・画素・ファイル名は変更しない。**
  画像の再圧縮・再保存・結合・CSSでの見かけの1枚化はしない。

### C. 実装（既定OFFのフラグ）

- `streamlit_app.py`：**`_ART_WP_ONE_PIECE_STORES = frozenset({"新宿歌舞伎町"})`**。
  `show_auto_article_page()` の「WordPress下書きを作成」処理で、この店舗のときだけ **`_wp_pl["wp_one_piece"] = True`**。
  他店舗はキー自体を渡さない。
- `wp_client.py`：**`plan_split(..., one_piece: bool = False)`**。`one_piece=True` なら分割計画を作らず空を返す
  （`split_image_for_wp()` を呼ばない）。`create_takadanobaba_draft()` が `payload.get("wp_one_piece")` を渡す。
- 送信関数は記事用ページのこのボタンからしか呼ばれない＝**新宿歌舞伎町の結果ポスト用・スランプ付き・かぶぱは経路上対象外**。
- **`_ART_WP_SPLIT_ALLOW_FILES` / `_ART_WP_SPLIT_NARROW_STORES` / `needs_split()` / `split_image_for_wp()` の既存一般仕様は変更していない。**
- 変更関数は `show_auto_article_page` / `plan_split` / `create_takadanobaba_draft` の3つだけ（新規・削除関数0）。

### D. 対象外（従来の分割仕様のまま）

新宿歌舞伎町の結果ポスト用・スランプ付き・かぶぱ ／ 他店舗の記事用（高田馬場・渋谷新館・秋葉原）／
結果ポスト用 ／ スランプ付き結果 ／ ローテ。

### E. WordPress側の前提設定（新宿歌舞伎町サイト espacekabuki-blog.com だけで実施済み）

- **EWWW Image Optimizer → 必須 →「最大画像サイズ」を 幅2560・高さ2560 → 幅0・高さ0 へ変更。**
  （原因特定：EWWW がアップロード時に長辺2560pxへ縮小し、「オリジナルを保持」オフのため元画像を残していなかった）
- **SWELL CHILD の `functions.php` 末尾へ `add_filter('big_image_size_threshold', '__return_false');` を追加**
  （WordPress標準の2560px縮小も無効化。親テーマは未編集。保存後 542バイト＝元483＋追加分）。
- EWWW の「オリジナルを保持」「既存の画像をリサイズ」「JPG最適化レベル（ピクセルパーフェクト）」は**変更していない**。
- **この設定は新宿歌舞伎町サイト全体の今後の画像アップロードへ効き、閲覧者の通信量・表示速度へ影響する可能性がある。**
- EWWW はアプリ画像を**除外パスに入れて未最適化のまま残す**状態（除外パス955行・最適化済みはサイト全体で30枚）だが、
  **原寸・画素は変更しない**（実測）。仮に最適化されても jpegtran の可逆方式。**既存の縮小済み画像は復元しない。**

### F. 検証

- **管理画面アップロード ID 1040** と、**アプリと同じ `wp_client.upload_media()` の REST アップロード ID 1104**（HTTP 201）で、
  2121×20354・5,715,501バイトの画像が **原寸・画素一致（バイト列も一致）・`-scaled` なし・source_url は原寸ファイル** で保存されることを確認済み。
  いずれも EWWW 処理後は「未最適化」で、ファイルは書き換えられない。
- 実装検証（HTTPモック・WordPress通信なし）：9/16・9/15 の実出力フォルダの長尺画像で、
  **その他の優秀台 9/16（2121×20354）8分割 ／ 末尾6番台の優秀台（2121×13568）6分割 ／ その他の優秀台 9/15（2121×15521）7分割 ／
  マイジャグV_高配分（1946×8132）4分割 → いずれも送信1ファイル・本文img1件**。送信ファイルは元ファイルそのもので、
  **バイト列・画素とも一致**。送信枚数は 9/16 が19→7枚、9/15 が19→10枚。
- 画像以外の本文（見出し・かぶぱブロックの位置・文言）、画像の並び順、タイトル・カテゴリ28・投稿者2、
  アイキャッチ（本文用ポスターと同じメディアID）、ランキング停止は変更前と同じ。
- 高田馬場・渋谷新館・フラグなしの新宿歌舞伎町は、分割計画・送信ファイル（バイト列）・本文HTMLが変更前と完全一致。
  `plan_split()` の既定呼び出しも全店舗で変更前と一致。
- **Cloud で実際に下書きを作成し、長尺画像が1枚として掲載・保存されることを確認済み。**

### G. 影響しないもの

アイキャッチ ／ ①ポスター ／ 本文順 ／ 全台データ画像 ／ ランキング停止 ／ かぶぱブロック ／ ⑦プレビュー ／ ZIP。

### H. WordPressへの書き込み記録

- アプリ実装・検証では WordPress へ書き込んでいない（HTTPモックのみ）。書き込みは上記の設定変更（EWWW・functions.php）、
  テストメディア2件（ID 1040・1104）、ID 1040 の手動最適化の実行、Cloud確認での下書き作成だけ。
- **テストメディア ID 1040 / 1104 は削除していない**（削除判断はユーザー）。

### I. 禁止事項・保全

1. 新宿歌舞伎町の記事用で分割送信へ戻さない（`wp_one_piece` を外さない）
2. `one_piece` の既定 False を変えない／他店舗・他ページへ `wp_one_piece` を渡さない
3. `_ART_WP_SPLIT_ALLOW_FILES` / `_ART_WP_SPLIT_NARROW_STORES` / `needs_split()` / `split_image_for_wp()` を本仕様を理由に変更・削除しない
4. 画像の再圧縮・再保存・結合・CSSでの擬似1枚化をしない／⑦・ZIP・画像生成を変えない
5. 新宿歌舞伎町サイトの EWWW「最大画像サイズ」を2560へ戻さない／functions.php の1行を消さない（戻すと長辺2560へ縮小され1枚掲載が破綻する）
6. EWWW の除外リスト・最適化設定を本仕様を理由に編集しない
7. テストメディア ID 1040 / 1104 を勝手に削除しない
8. `wrt_machines.json` の既存差分・未追跡ファイル・stash・アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / revert / force push は禁止
9. `716d377` / `85a7d19` へ reset・revert しない

<!-- VERBATIM-END id=S23216 -->

<!-- VERBATIM-BEGIN id=S23304 src=CLAUDE.md@fde5030 lines=23304-23378 sha256=1ca50dfa74b3168cecd096d0bf8806b949738fc9d048ce6afbdf5cc42c7d5f23 -->
## 【正式仕様】新宿歌舞伎町 記事用：②個別機種の優秀台ピックアップを「4分割パネル → 表 → スランプ」に（2026-09-29・`131cb0c` / `5f1cb2b` / `39007e8`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）→ ②「個別機種の優秀台ピックアップ」だけ**。
**Cloud で⑦・⑧とも同じ構成で、ピンクバーがないことを確認済み（ユーザー確認）。**
既存節は削除・書き換えしない。

### A. 正式commit（3件・いずれも現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| **`131cb0c`** | 表だけだった②個別「優秀台ピックアップ」へ、パネル・スランプ合成を追加 |
| **`5f1cb2b`** | パネルを「その他の優秀台」と同じ4分割パネルへ統一 |
| **`39007e8`** | 表とスランプの間のピンクサマリーバーを削除 |

3件とも `streamlit_app.py` のみ。**いずれも正式仕様の根拠commitであって、HEAD をここへ戻す意味ではない。reset・revert しない。**

### B. 完成画像の構成

```
「その他の優秀台」と同じ4分割の機種パネル → 表 → 実際の掲載台だけのスランプ
```

- **表とスランプの間にピンクサマリーバーは付けない。**
  描画は `_build_machine_img(df, タイトル, None, no_bar=True, hq_scale=…)`（**`summary_stat=None` でピンクバーを生成しない**）。
  **画像完成後にピンク部分を切り取る方式にしない。**
- 店舗ゲートは **`_ART_PICK_FULL_STORES = frozenset({"新宿歌舞伎町"})`**。他店舗は従来の表のみ（`_build_machine_img_no_bar`）。

### C. パネル

- **既存 `_build_variety_panel_grid` をそのまま使う**（合成ループで `is_multi=True` 扱い・`narabi_like` は立てない）。
- **最大4機種**（`_art_panel_max()` の既定4）。機種の並びは**掲載台番の小さい順**（記事用は `order_by_min_ban=True`）。
- **5機種以上のときは既存の上位4機種ルール**（機種ごとの最高差枚降順で選定）を維持する。
- **パネル未登録機種はエラーにせず既存どおりスキップ**。全機種が未登録ならパネルなしで「表 → スランプ」になる。
- **独自レイアウト・後処理での切り貼り・素材複製・機種名変換の追加はしない。**

### D. 表とスランプ

- 表は**入力台番のうち当日データに実在する台だけを台番昇順**で載せる（実在0台なら画像を作らない既存動作）。
- 掲載台番を ban_map（⑦ `_art_pick_bans` → `_pv_bm_sl`、⑧ `_art_pick_bans_e` → `_art_bm_sl`）へ登録し、
  **スランプもその掲載台だけ**を既存の合成ループで付ける。

### E. 変えないもの

**タイトル／台番テキスト／画像名（`{タイトル}.jpg`）／②入力・保存／自動高配分を抑制する既存仕様／
WordPress本文へ送らない既存仕様。**
**⑦プレビュー・🔄その他を更新・⑧本番で同じ完成画像を使う**（🔄は⑦の完成画像をそのまま使い、🎯変更時の再生成も同じ⑦経路）。

### F. 対象外

②個別「全台」／自動全台系／自動高配分／並び／末尾／⑤オススメ／その他の優秀台／全台データ画像／
①ポスター／アイキャッチ／ランキング停止／かぶぱブロック／他店舗・他ページ（結果ポスト用・スランプ付き・かぶぱ・「その他」配下・ローテ）。

### G. 検証

- 4機種（北斗・カバネリ・SAO・L攻殻機動隊）×2台＝8台のケースで、完成画像が **「4分割パネル → 表 → スランプ」** になった。
- **ピンクバー色（`#FFB6C1` / `#FF6FA5`）の画素は0件**（変更前は存在）。
- **パネル・表・スランプの各領域は変更前と画素一致**し、**高さだけ52px（ピンクバー分）減少**した。
- ⑧相当（同じ呼び出し＋`_save_jpeg`）も⑦と同じ寸法・構成・ピンクなし。
- AST比較で変更関数は `show_auto_article_page` のみ（新規・削除関数0）。
- **Cloud で⑦・⑧とも同じ構成・ピンクバーなしを確認済み。**
- **実装検証で WordPress・Pision への通信、下書き作成・更新・公開は行っていない。**

### H. 禁止事項・保全

1. ピンクサマリーバーを戻さない／生成後の切り取り・貼り替えで実現しない
2. 並び用のパネル選定（`narabi_like`・差枚最大1機種）へ戻さない／独自レイアウト・素材複製を作らない
3. `_build_variety_panel_grid` / `_apply_panel_to_table_img` / `_art_panel_max` を本仕様を理由に変更しない
4. パネル未登録機種でエラーにしない
5. `_ART_PICK_FULL_STORES` へ他店舗を勝手に追加しない／⑦だけ・⑧だけ変更しない
6. タイトル・画像名・②入力保存・自動高配分抑制・WordPress非送信を変えない
7. F の対象外へ波及させない
8. `wrt_machines.json`・`article_page_inputs.json`・`store_settings/新宿歌舞伎町.json` の既存差分、未追跡ファイル、stash 4件、
   アプリ自動commit履歴を保全する。`git add .` / `-A` / reset / restore / clean / stash操作 / revert / force push は禁止
9. `131cb0c` / `5f1cb2b` / `39007e8` へ reset・revert しない

<!-- VERBATIM-END id=S23304 -->

<!-- VERBATIM-BEGIN id=S23379 src=CLAUDE.md@fde5030 lines=23379-23457 sha256=dfa89ef67092081bcca45ad267b71e440f9cfdee182142a9b795b3beffea945a -->
## 【正式仕様】新宿歌舞伎町 記事用：表罫線を描画倍率に連動させ本文幅でも消えないようにする（2026-09-29・`c031ac5`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）で作成し WordPress 本文へ掲載する、表を含む画像全体**。
**Cloud の PC 表示で確認済み（ユーザー確認）。**既存節は削除・書き換えしない。

### A. 正式commit

| commit | 内容 |
|---|---|
| **`c031ac5`** | `fix: 新宿歌舞伎町記事用の表罫線を高解像度倍率に連動させ本文幅でも消えないようにする`（`streamlit_app.py` / `convert_narabi_pil.py`） |

`c031ac5` は現HEADの祖先であることを確認済み。直前のアプリ自動commit **`6583d46` / `19c7a8a` / `614580c`
（`auto: 画像生成後の設定を保存`・設定JSONのみ）** は有効な履歴として保全する。
**どのcommitへも reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 対象画像

全台系 ／ 高配分 ／ ②個別（全台／優秀台／優秀台ピックアップ）／ 並び ／ 列 ／ 末尾 ／ その他の優秀台 ／
ジャグラー ／ ⑤オススメ など、**2倍描画の表を含む画像**（いずれも `draw_table_image()`、⑧の並び・列は
`convert_narabi_pil.py` の `build_table_pil()` で表を描く）。

### C. 原因（確定）

- 表の罫線が**描画倍率に関係なく固定**（`draw_table_image` はセル境目2px・外枠1px、`convert_narabi_pil.py` は1px）だった。
- 幅約2100pxの2倍描画画像を **PC本文幅約752px（約1/2.8）** へ縮小表示すると、罫線が **1px未満相当**になり、
  縦線・横線・外枠が**薄く溶ける／縮小の位相によっては線ごと抜ける**ことがあった
  （スクショでは「ゲーム数｜BIG」間の縦線だけ消えていた）。
- 元画像の罫線は正常。JPEG圧縮・画像変換・描画処理の不具合ではない。
  1倍描画（幅約1000px・約1/1.3）は1px以上残るため消えなかった。

### D. 正式仕様

- 対象ページだけ、**表描画時点で罫線幅を描画倍率に連動**させる。**2倍描画ではセル境目・外枠とも4px**。
  - `streamlit_app.py`：判定 **`_art_table_line_new()`**（**`_ART_TBL_LINE_PAGES={"auto_article"}` × `_ART_TBL_LINE_STORES={"新宿歌舞伎町"}`** の AND・保存フラグなし・Streamlit外は False）。
    ON のとき `draw_table_image()` のセル枠線を `round(倍率)`px にし（セル境目は2セル分で 2×）、外枠も 2×round(倍率)px にそろえる。
  - `convert_narabi_pil.py`：**`ART_LINE = False`（既定）**。ON のとき罫線を 2×round(倍率)px にする（セル塗りを内側へ寄せ、外枠も同じ太さ）。
- **線はセルの内側へ太らせる**ので、**列幅・行高・画像サイズ・文字位置・表の数値は変えない**。
- **画像完成後の線の重ね描き・切り貼り・画像縮小・再圧縮・WordPress側の設定変更は行わない。**
- 記事用⑧の並び・列は別プロセスのため、**`_patch_and_run_narabi(art_line=_art_table_line_new())` で
  同じ指定を `convert_narabi_pil.py` へ渡して同じ太さにする**（`art_line` 既定 False）。
- **⑦・⑧・WordPress送信画像で同じ罫線仕様**になる（送信画像は⑧の出力ファイルそのもの）。

### E. 対象外（従来の画素を維持）

新宿歌舞伎町以外の記事用 ／ `auto` ／ `auto_slump` ／ `auto_slump2` ／ ローテ ／ 作業用 ／ ⑥個別生成 ／
結果ポスト ／ スランプ付き結果 ／「その他」配下。

表の内容 ／ パネル ／ スランプ ／ 画像名 ／ ピンクバー有無 ／ 判定・集計 ／ アイキャッチ ／ ①ポスター ／
本文順 ／ かぶぱ ／ ランキング停止 は変えない。

### F. 検証

- 完成画像を **PC本文幅752px相当へ4種類の方式（NEAREST / BILINEAR / BOX / LANCZOS）で縮小**し、
  すべての縦線・横線・外枠を全長にわたって測定。線の太さ方向の濃さ合計（1.0＝1px分）の最小値は
  **修正前 0〜0.33px分 → 修正後 約1.0〜1.45px分**（⑧並びのJPEGは NEAREST 0.99＝JPEG誤差）。
- ON/OFFで変化した画素はすべて罫線色。**パネル・スランプ領域は修正前と画素完全一致**、画像サイズ不変。
- **対象外は修正前と画素一致**（⑧並びの既定・通常ページ設定は生成JPEGがバイト一致）。
- 変更関数は `draw_table_image` / `_patch_and_run_narabi` / `show_auto_article_page`（新規 `_art_table_line_new`）と、
  `convert_narabi_pil.py` の `_draw_cell` / `build_table_pil` だけ。
- **111 PASS / 0 FAIL。Cloud の PC 表示で確認済み。**
- **実装検証で WordPress・Pision への通信は行っていない。**

### G. 保証範囲の注意

**スマホ本文幅約354px（約1/6）では、4pxの罫線でも1px未満になる可能性がある。今回の保証範囲は PC 本文幅（752px）。**

### H. 禁止事項・保全

1. 罫線幅を倍率非連動の固定値へ戻さない／`_art_table_line_new()` のゲートを外さない・他店舗や他ページへ広げない
2. `ART_LINE` / `art_line` の既定 False を変えない／⑦だけ・⑧だけ変更しない
3. 線を完成画像へ重ね描き・切り貼りしない／画像縮小・再圧縮・WordPress設定・テーマ・CSSで代替しない
4. 列幅・行高・画像サイズ・文字位置・数値を罫線のために変えない
5. E の対象外・変えないものへ波及させない
6. `wrt_machines.json` の既存差分、未追跡ファイル、stash 4件、アプリ自動commit履歴を保全する。
   `git add .` / `-A` / reset / restore / clean / stash操作 / revert / force push は禁止
7. **アプリ起動中に未commitのコードを残したまま検証しない**（自動 stash で作業ツリーが HEAD へ戻る・`55e7752`）
8. `c031ac5` / `6583d46` / `19c7a8a` / `614580c` へ reset・revert しない


<!-- VERBATIM-END id=S23379 -->

<!-- VERBATIM-BEGIN id=S23677 src=CLAUDE.md@fde5030 lines=23677-23748 sha256=30cbf23ba58675f85b5bcbba96407d293fa568af1f908e04f1609b3fec47bd3b -->
## 【正式仕様】新宿歌舞伎町 記事用📝：ジャグラーシリーズ優秀台のパネル・スランプ付与と②全台系掲載台の除外（2026-10-01・`cec23c7`）

**正式仕様。巻き戻し禁止。**対象は
**【新宿歌舞伎町】→ 記事用（`auto_article`）→ 📝記入部分のみ で「ジャグラーシリーズ優秀台」を自動抽出した場合だけ**。
**Cloud 実機で確認済み（ユーザー確認）。**既存節は削除・書き換えしない。

### A. 正式commit

| commit | 内容 |
|---|---|
| **`cec23c7`** | `fix: 新宿歌舞伎町記事用📝のジャグラーシリーズ優秀台にパネル・スランプを付け②全台台を除外`（`streamlit_app.py` のみ・+27行） |

`cec23c7` は現HEADの祖先であることを確認済み。前後のアプリ自動commit（`b7280bd` / `bb2dded` / `d7a559f` / `6c49725` ほか）は有効な履歴として保全する。
**`cec23c7` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 原因

1. **表だけになる**：⑧📝は自動抽出の掲載台番を ban_map（`_art_bm_sl` ← `_man_jug_bans_e`・`0cf25ec`）へ登録していたが、
   **⑦📝は台番（`_art_jg_bans`）を計算するだけで `_pv_bm_sl` へ登録していなかった**。⑦の登録元は通常経路の
   `jug_pool_df` だけで、📝（`manual_mode=True`）では作られないため、合成ループで素通し＝表のみになっていた。
2. **ゴージャグ3の重複**：📝のジャグラー自動抽出の除外集合（`_art_jg_exc` / `_jg_exc_m`）は
   ②個別ピック・並び・台番範囲・列・②優秀台の掲載台を含むが、**②個別「全台」画像の掲載台を含んでいなかった**。
   （🔍フル経路では②全台の機種は `recommended_machines` 経由で元からジャグラー集計に入らない。）

### C. 仕様

- ゲートは **`_ART_MANUAL_JUG_FIX_STORES = frozenset({"新宿歌舞伎町"})`**。他店舗は従来どおり。
- **⑦📝**：表に実際に掲載した台番（`_art_jg_bans`）を既存 **`_pv_bm_sl["ジャグラーシリーズ優秀台.jpg"]`** へ登録し、
  既存の合成経路で **「機種パネル → 表 → スランプ」** にする。
  **新しいパネル素材・独自レイアウト・画像完成後の貼り付けは作らない。**
- パネルは **ジャグラーシリーズ優秀台の既存最大2機種ルール**（`_ART_JUG_PANEL2_STORES` / `_art_panel_max()`）、
  スランプは **表に掲載した台だけ**。
- **②「全台系」に実際に掲載した台番を、ジャグラーシリーズ優秀台の自動抽出から除外する。**
  台番は表と同じ既存 **`_resolve_kojin_name()`** で求め（⑦ `_art_kz_bans` ／ ⑧ `_art_kz_bans_e`）、
  除外集合へ加える。**機種名文字列の単純置換では行わない。**
- ②全台系に `ゴージャグ3` がある場合はジャグラーシリーズ優秀台から **0台**、外すと**既存条件を満たすゴージャグ3だけが復帰**する。
- **⑦📝と⑧📝で同じ除外対象・掲載台・パネル／スランプ構成**になる。
  **🔄その他を更新は、完成済み⑦画像を引き継ぐ既存仕様を維持**する。
- 変えないもの：既存の抽出条件（例 +1,000枚以上）、表、台番順、画像名、既存サマリー有無（ジャグラーはサマリーなし）、入力・保存。

### D. ★明示的な対象外（未対応の特殊🔄操作）

📝で②優秀台のジャグラー機種をチェックOFFし、🔄その他を更新で**通常経路のジャグラー集計（`_apjp` / `_apje` ＋ `_ajdfs`）で
再振り分けが走る**特殊操作は、**今回変更していない**。この操作ではジャグラー画像が作り直されるため、
📝自動抽出分が置き換わる可能性がある。**この操作で📝自動抽出分を維持する仕様は、必要になった場合に別途判断する。**

### E. 対象外（変更しない）

自動全台系、高配分、②個別（全台・優秀台）、並び、末尾、⑤、その他の優秀台、WordPress本文、①ポスター、アイキャッチ、
ランキング停止、かぶぱ、他店舗・他ページ。AST上の変更関数は `show_auto_article_page` のみ（新規・削除関数0）。

### F. 検証・確認

- **2026/9/27・新宿歌舞伎町749台**：②全台にゴージャグ3ありの場合、ジャグラー**66台中ゴージャグ3は0台**。
  外した場合は72台に戻り、**+1,000枚以上のゴージャグ3 6台（1055 / 1103 / 1109 / 1112 / 1115 / 1117）だけが復帰**（他の増減0）。
- **表とスランプの台番が66台で完全一致**し、完成画像が「パネル（2枚）→ 表 → スランプ」になったことを目視確認。
- **Cloud で、ゴージャグ3の除外・復帰、パネル・表・スランプの構成、⑧本番の同一性を確認済み。**
- 実装検証では **WordPress 通信を行っていない**。Pision は確定データGETのみ。

### G. 禁止事項・保全

1. ⑦📝の `_pv_bm_sl` 登録を外さない／⑦だけ・⑧だけの除外にしない
2. ②全台の除外を機種名の文字列置換・別名辞書で行わない（`_resolve_kojin_name()` の実台番を使う）
3. 独自のパネル・スランプ描画・後処理合成を作らない／パネル最大2機種ルールを変えない
4. `_ART_MANUAL_JUG_FIX_STORES` へ他店舗を勝手に追加しない
5. 抽出条件・表・台番順・画像名・サマリー有無・入力保存を本仕様を理由に変えない
6. D の特殊🔄操作を承認なしに変更しない
7. WordPress への POST / PUT / PATCH / DELETE・メディアアップロード・下書き作成／更新／公開を行わない
8. `wrt_machines.json`・`auto_page_inputs.json`・`article_page_inputs.json` の既存差分、未追跡4件、stash 4件、
   アプリ自動commit履歴を保全する。`git add .` / `git add -A` / reset / restore / clean / stash操作 / revert / force push は禁止
9. `cec23c7` へ reset・revert しない

<!-- VERBATIM-END id=S23677 -->

<!-- VERBATIM-BEGIN id=S23749 src=CLAUDE.md@fde5030 lines=23749-23860 sha256=2213b22f3e7b96875712a62bb05bb219b0eb9219b0d07fe0f3c92c0d8b067fe5 -->
## 【正式仕様】新宿歌舞伎町 記事用WordPress：「その他のジャグラーの優秀台」ブロック追加と③の列→並び掲載順（2026-10-01・`414e627` / `80eae5c`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）の WordPress 本文だけ**。
**Cloud 実機（下書き）で確認済み（ユーザー確認）。**既存節は削除・書き換えしない。

### A. 正式commit（いずれも現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| **`414e627`** | `feat: 新宿歌舞伎町記事用WordPressに「その他のジャグラーの優秀台」ブロックを追加`（`streamlit_app.py` / `wp_client.py`） |
| **`80eae5c`** | `feat: 新宿歌舞伎町記事用WordPressの③で列画像を並び画像より先に掲載`（`streamlit_app.py` / `wp_client.py`） |

前後のアプリ自動commit（`6c49725` / `fd28600` ほか）は有効な履歴として保全する。
**どのcommitへも reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

---

## 1. ジャグラーシリーズ優秀台の WordPress 掲載（`414e627`）

### B. 原因（記録）

⑧では `ジャグラーシリーズ優秀台.jpg` が正常に生成・`result["files"]` へ登録されていたが、新宿歌舞伎町は
**`_ART_WP_NO_JUG_SECTION_STORES`（独立ジャグラーセクションを作らない店舗）**に入っているため
`payload["juggler_section"] = False` となり、`plan_blocks()` が統合画像の実在確認すらせず
**本文計画・アップロード対象から漏れていた**。

### C. 仕様

- 本文順（新宿歌舞伎町の記事用）：

  ```
  … ニブイチ系も大量！ …
  → H2「その他のジャグラーの優秀台」（H2_JUG_TAIL）
  → ジャグラーシリーズ優秀台.jpg（1件）
  → その日のジャグラー全体結果の1文
  → H2「その他の単品優秀台」 …
  ```

- **新ブロックは必ず「その他の単品優秀台」H2より前**（`plan_blocks()` の `tenday` / その他単品H2の直前）。
  H2・画像・段落は既存の `blk_h2` / `blk_image` / `blk_para`（`esc()` 済み）を使い、独自HTML・CSSは作らない。
- ゲートは **`_ART_WP_JUG_TAIL_STORES = frozenset({"新宿歌舞伎町"})`** → `payload["jug_tail"] = {"text": …}`。
  **キーを渡さない店舗は1ブロックも増えない。**
- **画像は⑧が実際に生成・保存した `ジャグラーシリーズ優秀台.jpg` だけ**：
  payload を渡す条件は「`output_dir` に実ファイルがある **かつ** `result["files"]` に今回のパスがある」。
  `plan_blocks()` でも実在確認する。**二重生成・二重アップロードはしない**（独立ジャグラーセクションは出ないので画像は本文に1回だけ）。
- **画像がない日・0台の日・⑦で画像チェックOFFの日（⑧が削除）は、H2・画像・文章をまとめて出さない。前回の古い画像は拾わない。**
- 文章は結果テキスト「🤡本日のジャグラー全体の結果は」と**同じジャグラー全台集計・同じ書式**：
  - 集計は共通関数 **`_juggler_total_stat(df, jug_series)`**（`juggler_series` 全台の総差枚・平均差枚・+1,000枚台数）、
    書式は **`_jug_signed()`**（`+12,345枚`）。結果テキストの `juggler_summary_section()` もこの2関数を呼ぶ形に置換した
    （出力は変更前とバイト一致）。
  - 本文用は **`_jug_total_wp_text(df, store)`** で
    `本日のジャグラー全体の結果は総差枚{±X枚}、平均差枚{±Y枚}！` の**総差枚・平均差枚だけ**。
  - **「+1,000枚オーバー」などの台数表記、画像掲載台だけの集計、別カテゴリの数値は出さない。**
  - 入力は⑧の `result["df"]`（結果テキストと同じ・補正後の差枚。再補正しない）。
- **`_ART_WP_NO_JUG_SECTION_STORES` の設定は維持**（`juggler_series=set()` で高配分へ統合する仕様も不変）。
  独立ジャグラーセクションは出さず、この本文ブロックだけを追加した。
- 変えないもの：ジャグラー自動抽出・パネル・表・スランプ・②全台系との重複除外（`cec23c7`）・結果テキストそのもの・
  高田馬場・渋谷新館など他店舗の本文。

---

## 2. ③画像の WordPress 掲載順（`80eae5c`）

### D. 仕様

- 対象は新宿歌舞伎町の記事用 WordPress 本文の③「並びも複数！」セクションだけ。
- 本文では **「列画像すべて → 並び画像すべて」**。
  実装は `plan_blocks()` で並び用・列用の H3＋画像ブロックを別々に組み立て、
  **`payload["retsu_first"]`（`_ART_WP_RETSU_FIRST_STORES = frozenset({"新宿歌舞伎町"})`）**のときだけ列を先に連結する。
  **既定（キーなし）は従来どおり 並び → 列。**
- **同種内の順序・画像名・画像内容・掲載台・画像チェック状態・見出し文言（H2/H3）は変えない。**
  Cコメントは従来どおりセクション末尾に1回。
- **⑦プレビューは元から列→並びの順**（`_art_pil` へ列を先に追加）であり変更しない。
- **⑧の画像一覧・ZIPは出力フォルダ全体のファイル名順**（`sorted(os.listdir(output_dir))` / `_make_zip_bytes`）で、
  カテゴリ順を持たない既存仕様のため**今回の並び替え対象外**（ファイル名を変えないため）。
- 結果テキストの「並び仕掛け」「列仕掛け」の順は画像順と独立したデータ（`nami_list` / `retsu_list`）で、従来どおり維持する。
- 他店舗の記事用、結果ポスト、スランプ付き結果、ローテの本文・画像順は変更しない。

---

### E. 検証・確認

- **2026/9/27 実データ（新宿歌舞伎町749台）**：ジャグラー新ブロックが
  「H2 → 画像1件 → 総差枚・平均差枚文1件 → その他の単品優秀台」の順。
  文章は `本日のジャグラー全体の結果は総差枚+66,550枚、平均差枚+269枚！` で、
  結果テキスト `🤡本日のジャグラー全体の結果は 総差枚+66,550枚、平均差枚+269枚！` と一致。新ブロックに台数表記なし。
- 画像なし（実ファイルなし）では新ブロック全体が出ない。画像OFFは⑧が実ファイルを削除するため同じく出ない。
- 新ブロックを除いた本文計画・最終HTMLは変更前と完全一致（画像ブロック増加は1件のみ）。
- ③：列2枚（ゴージャグ3・ジャグラーガールズ）／並び3枚（ゴージャグ3・ファンキー2・マイジャグV）で、
  **列画像すべてが並び画像より前**にあることを**送信前本文計画・最終HTMLで確認**し、**Cloud下書きでも確認済み**。
  同種内順序・ブロック集合は変更前と一致。
- 結果テキストは新宿歌舞伎町・高田馬場・渋谷新館・新小岩で変更前と完全一致。高田馬場・渋谷新館の本文計画は変更前と一致。
- 実装検証では **WordPress 通信を行っていない**（HTTPモック・本文計画/HTMLのローカル生成のみ。Pision は確定データGETのみ）。
  **Cloud確認時の下書き作成以外の書き込みはしていない。**

### F. 禁止事項・保全

1. 新ブロックを「その他の単品優秀台」H2より後ろへ移さない／独自HTML・CSSを作らない
2. ⑧が今回保存していない画像（前回の残り）を本文へ載せない（実在＋`result["files"]` の二重確認を外さない）
3. 新ブロック用に画像を二重生成・二重アップロードしない
4. 文章へ台数表記・画像掲載台だけの集計・別カテゴリの数値を足さない／`_juggler_total_stat` / `_jug_signed` 以外で再計算しない
5. 結果テキスト `juggler_summary_section()` の出力を変えない
6. `_ART_WP_NO_JUG_SECTION_STORES` から新宿歌舞伎町を外さない（高配分統合仕様が変わる）
7. `_ART_WP_JUG_TAIL_STORES` / `_ART_WP_RETSU_FIRST_STORES` へ他店舗を勝手に追加しない／`retsu_first` の既定を真にしない
8. 列→並びを画像の移動・ファイル名変更・HTML文字列置換で実現しない（`plan_blocks()` の正規組立順で行う）
9. ⑧の画像一覧・ZIPの順を変えるためにファイル名を変えない
10. 結果テキストの並び／列の順・自動抽出・パネル・表・スランプ・②全台除外を本仕様を理由に変えない
11. WordPress への POST / PUT / PATCH / DELETE・メディアアップロード・下書き作成／更新／公開を検証で行わない
12. `wrt_machines.json`・`article_page_inputs.json`・`auto_page_inputs.json` の既存差分、未追跡4件、stash 4件、
    アプリ自動commit履歴を保全する。`git add .` / `git add -A` / reset / restore / clean / stash操作 / revert / force push は禁止
13. `414e627` / `80eae5c` へ reset・revert しない

<!-- VERBATIM-END id=S23749 -->

<!-- VERBATIM-BEGIN id=S24545 src=CLAUDE.md@fde5030 lines=24545-24623 sha256=8e26ff3600ed16c0df3f8540f6961d6637bb8f771f912d06b334fa5280feac7f -->
## 【正式仕様】新宿歌舞伎町 記事用：🔄で作り直す「その他のジャグラーの優秀台」を青バーなし・4分割パネルにする（2026-10-05・`729d306`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）だけ**。
**Cloud 実機で⑦プレビュー・🔄その他を更新・⑧本番が同じ見た目になることを確認済み（ユーザー確認）。**
既存節は削除・書き換えしない。

### A. 正式commit

| commit | 内容 |
|---|---|
| **`729d306`** | `fix: 新宿歌舞伎町記事用の🔄で作り直すジャグラー統合画像を青バーなし・4分割パネルにする`（`streamlit_app.py` のみ・+59 / −4） |

`729d306` は現HEAD（＝origin/main）の祖先であることを確認済み。直前のアプリ自動commit（`3b3e861` / `889c620` ほか）は有効な履歴として保全する。
**`729d306` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 対象範囲

- **②の自動生成されたジャグラー高配分画像（`{機種名}_高配分.jpg` 等）を複数チェックOFFにして `🔄その他を更新` を押した後に作り直される「その他のジャグラーの優秀台」画像（`ジャグラーシリーズ優秀台.jpg`）だけ。**
- **⑦プレビュー・🔄その他を更新・⑧本番で同じ完成形にする。**
- **対象外**：📝記入部分のみの経路（`_art_prev_manual_{store}` / `_art_exec_manual`）、
  **チェックOFFがない最初の自動生成画像**、他店舗・他ページ。
  **最初の自動生成画像の既存「最大2枚パネル」仕様（`_ART_JUG_PANEL2_STORES` / `_art_panel_max()`）は変えない。**

### C. 原因（記録）

1. **青タイトルバー**：初回の自動抽出（`run_step2_juggler` の `article_mode`）は `_build_machine_img_no_bar(hq_scale)` で青バーなし・2倍で描くが、
   🔄と⑧の作り直しだけ `_build_machine_img(df, タイトル, None)`（青バー付き・1倍）を呼んでいた。スランプは2倍で合成されるため大きさも食い違っていた。
2. **2分割パネル**：記事用ページ追加時（`47e0372`）から、新宿歌舞伎町の `ジャグラーシリーズ優秀台.jpg` はパネル上限2（`_ART_JUG_PANEL2_STORES`）。
   作り直し後に4機種以上が載っても2枚しか出なかった。
3. **⑧のずれ**：⑧の作り直しは掲載元を `jug_excellent_list` だけから取り、末尾台・🎯OFF台を除外せず、
   スランプも初回の `jug_pool_df` の台番のままで、表とスランプがずれ得た。

### D. 正式仕様

- **作り直した画像は、最初の自動抽出と同じく青タイトルバーなし・2倍解像度で描画する**
  （`_art_jug_regen_img()` ＝ `_build_machine_img_no_bar(df, hq_scale=_art_hq_scale_for("ジャグラーシリーズ優秀台.jpg", store, 台数))`）。
  **完成後に青バーを切り取る方式にはしない。**⑧は高解像度時 `_ART_HQ_TARGET_KB` で保存する。
- **作り直した画像だけ**、既存「その他の優秀台」と同じ4分割パネル処理（`_apply_panel_to_table_img` → `_build_variety_panel_grid`・`max_panels=4`）を使い、**最大4機種**を表示する。
  **5機種以上の既存の選び方（機種ごとの最高差枚順）・並べ方（掲載台の最小台番昇順）を変えない。**
  **独自の素材・レイアウト・機種名変換は追加しない。**
- 完成形は **「最大4分割パネル → 表 → 掲載台だけのスランプ」**。**青タイトルバーは付けない。**
- **⑧本番も🔄と同じ掲載台から表・スランプを作る**：統合プール（`jug_pool_df`、無ければ `jug_excellent_list`）＋OFF機種の+1,000枚以上の台を基に、
  **末尾画像の掲載台（`_art_tail_bans` × 通常末尾・ジャグラー末尾）と🎯掲載台選択で外した台（`art_juggler`）を除外**し、
  ⑧の ban_map を作り直した表の台番（`_arj_regen_bans_e`）で上書きして**表の台番とスランプの台番を一致させる**。

### E. 実装

- 定数・関数：**`_ART_JUG_REGEN_STORES = frozenset({"新宿歌舞伎町"})`** ／ `_ART_JUG_FN` ／ **`_art_jug_regen_on(store)`** ／ **`_art_jug_regen_img(store, df)`**。
- 🔄：作り直し時に `_aj_regen_new = True` とし、🔄の合成ループだけ該当画像の `max_panels` を4にする（📝記入部分のみのプレビュー由来は対象外）。
- ⑧：`_arj_new = _art_jug_regen_on(store) and not _art_exec_manual` のときだけ新しい組み立て・描画・ban_map上書き・`max_panels=4`。
- 変更関数は `show_auto_article_page` のみ、新規関数は上記2つ、削除関数0。

### F. 変えないもの

表、ピンクバーの有無、画像名、入力・保存、**WordPress本文の組み立て、`wp_client.py`**、パネル以外の既存仕様、
初回自動生成画像（上限2枚）、⑦初回プレビューの合成、他店舗・他ページ（従来の `_build_machine_img(..., タイトル, None)` 経路のまま）。

### G. 検証・Cloud確認

- **2026/10/4・749台の確定データ**で、ジャグラー高配分5機種（マイジャグV／ファンキー2／ゴージャグ3／ネオアイム／ミスジャグ）をすべてOFFにした場合に、
  **56台・8機種**となり、**青バーが0px**（修正前 63,278px）、**2×2の4分割パネル**（同じ台で作った「その他の優秀台」パネルと画素一致）、
  **表とスランプの台番一致**を確認した。作り直した表は初回の描画方法と画素一致。
- **Cloud で⑦・🔄・⑧が同じ見た目になることを確認済み。**
- 実装検証では **Pision 確定データ取得のみ**で、**WordPress 通信・Cloud 操作・本番画像保存はしていない。**

### H. 禁止事項・保全

1. 作り直したジャグラー画像を青バー付き・1倍描画へ戻さない／青バーを完成後に切り取らない
2. 最初の自動生成画像の上限2枚パネルを変えない（4枚にするのは作り直した画像だけ）
3. 独自のパネル素材・レイアウト・機種名変換・選定順を作らない（既存 `_build_variety_panel_grid` を使う）
4. ⑦・🔄・⑧のどれかだけ別の構成にしない／⑧の掲載台を🔄と別の組み立てにしない
5. 表とスランプの台番をずらさない（`_arj_regen_bans_e` の ban_map 上書きを外さない）
6. `_ART_JUG_REGEN_STORES` へ他店舗を勝手に追加しない／📝記入部分のみ経路へ広げない
7. 表・ピンクバー・画像名・入力保存・WordPress本文・`wp_client.py` を本仕様を理由に変えない
8. WordPress への POST / PUT / PATCH / DELETE・メディアアップロード・下書き作成／更新／公開を行わない
9. `wrt_machines.json`・`article_page_inputs.json` の既存差分、未追跡ファイル、stash 4件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
10. `729d306` へ reset・revert しない

<!-- VERBATIM-END id=S24545 -->

<!-- VERBATIM-BEGIN id=S24664 src=CLAUDE.md@fde5030 lines=24664-24740 sha256=ead91800fc5200697e1b419f0caea34a020798d138496a4393b692cd37708630 -->
## 【正式仕様】新宿歌舞伎町 記事用：📝記事コメントを候補の複数チェック方式へ（全台系・ニブイチ系・末尾・オススメ機種）（2026-10-05・`80925a7` / `2ba0d2a` / `529d9ed` / `06360c3`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）の⑦プレビュー後に出る「📝 記事コメント」と、WordPress本文へ渡す文章だけ**。
**Cloud で候補表示・選択・保存復元・WordPress本文への反映を確認済み（ユーザー確認）。**
既存節は削除・書き換えしない。渋谷新館の記事コメント節（`31b9014` / `b427efe` / `52be5eb` / `2e3a694`）の
「単一選択（候補①②③から1つ）」は**渋谷新館の正式仕様として引き続き有効**であり、本節は新宿歌舞伎町だけの後発仕様である。

### A. 正式commit（4件・いずれも現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| **`80925a7`** | `feat: 新宿歌舞伎町記事用のWordPress文章を候補の複数チェック方式にする`（`streamlit_app.py`） |
| **`2ba0d2a`** | `fix: 新宿歌舞伎町記事用の全台系・ニブイチ系候補①②を平均プラスの上位3機種に絞る`（`streamlit_app.py`） |
| **`529d9ed`** | `feat: 新宿歌舞伎町記事用のWordPress文章に末尾の候補を追加`（`streamlit_app.py` / `wp_client.py`） |
| **`06360c3`** | `feat: 新宿歌舞伎町記事用のオススメ機種コメントを2候補のチェック式にする`（`streamlit_app.py`） |

間のアプリ自動commit **`57108c4`（`auto: 画像生成後の設定を保存`）** は有効な履歴として保全する。
**どのcommitへも reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 共通仕様

- 従来の単一選択（selectbox）ではなく、**各セクションの候補をすべて表示し、チェックした候補だけを採用する。複数選択可。**
- ゲートは **`_ART_CMT_CK_STORES = frozenset({"新宿歌舞伎町"})`**。
  セクションは **`_ART_CMT_CK_SECTIONS`**＝ A 全台系 ／ B ニブイチ系 ／ **S 末尾** ／ C 並び ／ D オススメ機種 ／ E その他の単品優秀台、
  ラベルは **`_ART_CMT_CK_LABELS`**。
- **`📝まとめ`（F）は表示・本文出力しない。**
- **データがない候補は「対象データなし」と表示し、選択不可**にする。
- **選択状態は既存 `article_page_inputs.json` へ日付（Excel）ごとに保存・復元する。**
  キーは **`art_comment_ck_{sec}_{idx}_{store}`**。**新規JSON・新しい保存方式は作らない。**
- **対象外**：渋谷新館（単一選択のまま）、他店舗、結果ポスト、スランプ付き結果、かぶぱ、ローテ。

### C. 全台系・ニブイチ系（`80925a7` / `2ba0d2a`）

- 候補①②は、**判定対象の全機種数を `○機種` として残す**。
- **文中に出す機種は平均差枚がプラスの機種だけ。平均差枚の大きい順に最大3機種。**
- **4機種以上、またはマイナス／0枚の機種を省略した場合は `など○機種`。**全機種を表示できる1〜3機種なら「など」は付けない。
- **プラス機種が0なら候補①②は「対象データなし」。**
- **候補③と多台数／少台数判定は変更しない。**

### D. 末尾（`529d9ed`）

- UIは**全台系・ニブイチ系の後、並びの前**に「📝 末尾」（セクション `S`）。
- 候補①：`末尾○番台は平均差枚+○○枚で○台中○台がプラス！`
- 候補②：`末尾○番台は平均差枚+○○枚で○台がプラス！○番台の機種名は+○○枚！`
- **通常末尾・ジャグラー末尾とも対象。**複数あるときは **末尾① → 末尾② → ジャグラー末尾** の順に、**末尾ごとに1文**。
- 数字は**末尾画像のピンクバーと同じ実掲載台・補正後差枚**を使う。**ジャグラー末尾は結果テキストではなく画像集計を優先**する。
- 候補②の最優秀台は、**末尾画像に実際に載った台の最大差枚**。
- WordPress本文では**末尾見出し・末尾画像の直後**に、チェック済み候補を **①→②順** で置き、**並び見出しより前**に出す
  （`wp_client.plan_blocks()` の末尾ブロック直後へ既存 `para` 経路で配置）。

### E. オススメ機種（`06360c3`）

- 候補①は**常時ON固定（`_ART_CMT_CK_FIXED`）を廃止**し、通常のチェック式・**初期OFF**とした（`_ART_CMT_CK_FIXED = frozenset()`）。
- 候補①は、**⑤オススメ機種画像に実際に載った台**から、**プラスの機種だけ最大3機種**の No.1 差枚を出す（上限 `_ART_CMT_CK_OSU_MAX = 3`）。
- 候補②：`オススメ機種は機種名と機種名がニブイチ系！機種名の単品からも+○○枚の爆発台が出現！`
  - **前半**は⑤入力機種のうち**既存判定でニブイチ系となった機種だけ**（平均差枚の高い順。**全台系は含めない**）。
  - **後半**は**非ニブイチ系の⑤入力機種**から、**画像に実際に載った台の最大差枚が最も大きい1機種・1台**。**プラスの場合だけ。**
  - **前半・後半の両条件がそろう場合だけ候補②を有効**にする（そろわなければ「対象データなし」）。

### F. 変更しないもの

画像生成、抽出、🎯掲載台選択、末尾重複除外、結果テキスト、WordPress画像配置、
⑤の入力・優先・重複排除、ニブイチ系／全台系の判定、渋谷新館の記事コメント（単一選択・F まとめ・保存キー）。

### G. 禁止事項・保全

1. 新宿歌舞伎町の記事コメントを単一選択へ戻さない／渋谷新館を複数チェック式へ変えない
2. `📝まとめ` を新宿歌舞伎町で表示・本文出力しない
3. 対象データなしの候補を選択可能にしない／新規JSON・別の保存キー体系を作らない
4. 全台系・ニブイチ系の候補①②でマイナス／0枚の機種を文中に出さない／最大3機種・「など○機種」の規則を変えない／候補③と多台数・少台数判定を変えない
5. 末尾の数字を結果テキストや未掲載台から作らない（画像の実掲載台・補正後差枚を使う）／末尾①→末尾②→ジャグラー末尾の順と本文配置（末尾画像の直後・並びより前）を変えない
6. オススメ機種候補①を常時ON固定へ戻さない／候補②の前半に全台系を含めない／両条件がそろわないのに候補②を有効にしない
7. F の変更しないものを本仕様を理由に変えない
8. `wrt_machines.json`・`article_page_inputs.json` の既存差分、未追跡ファイル、stash 4件、アプリ自動commit履歴（`57108c4` ほか）を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
9. `80925a7` / `2ba0d2a` / `529d9ed` / `06360c3` へ reset・revert しない

<!-- VERBATIM-END id=S24664 -->

<!-- VERBATIM-BEGIN id=S27664 src=CLAUDE.md@fde5030 lines=27664-27758 sha256=0522226382bbaec74a464c2af4d92fb4c4114a7dfe3e23f481e1b288fd0891d8 -->
## 【正式仕様】新宿歌舞伎町 記事用：ジャグラー統合画像を最大4パネルへ戻す（2026-10-18・`afb3988`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】× 記事用（`page=auto_article`）の `ジャグラーシリーズ優秀台.jpg` のパネル枚数だけ**。
**Cloud 実機で確認済み（2026-10-18）。**既存節は削除・圧縮・統合・書き換えしない。

### A. 正式commit

| 項目 | 内容 |
|---|---|
| 正式commit | **`afb3988`**（`fix: 新宿歌舞伎町のジャグラー統合画像を最大4パネルに修正`・`streamlit_app.py` のみ・1行） |

**`afb3988` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 原因（記録）

- 9/16 の **`47e0372`**（新宿歌舞伎町に記事用ページを追加）で、渋谷新館型のゲートを一括流用した際
  （commit メッセージ「渋谷新館型ゲートへ 新宿歌舞伎町 を追加（…最大2パネル…）」）、
  新宿歌舞伎町まで **`_ART_JUG_PANEL2_STORES`（最大2パネル）** に入った。
- **「新宿歌舞伎町は最大2枚でよい」というユーザーの明示指示は、Git履歴にも CLAUDE.md にも存在しない。**
  最大2枚の明示指示があるのは渋谷新館だけ（`5f51fc7`・2026-09-05）。
- 正とするのは **2026/8/4 の4分割仕様（`0df63dd`）**：
  `ジャグラーシリーズ優秀台.jpg` / `その他の優秀台ピックアップ.jpg` を末尾画像と同じ4分割パネルにし、
  採用は差枚上位・表示順は代表台番昇順。

### C. ★過去記録の上書き（誤読しないこと）

次の過去節にある「**新宿歌舞伎町の記事用ジャグラー統合画像は初回・📝とも最大2**」という記述は、
`47e0372` 時点のコードを書き写したもので、ユーザー指示の根拠はない。

- 「新宿歌舞伎町 記事用📝：ジャグラーシリーズ優秀台のパネル・スランプ付与と②全台系掲載台の除外（`cec23c7`）」節
  （「パネルは ジャグラーシリーズ優秀台の既存最大2機種ルール」）
- 「新宿歌舞伎町 記事用：🔄で作り直す「その他のジャグラーの優秀台」を青バーなし・4分割パネルにする（`729d306`）」節
  （「最初の自動生成画像の既存「最大2枚パネル」仕様は変えない」「4枚にするのは作り直した画像だけ」）

**これらの節は当時の記録として削除・書き換えしない。ただしこの部分は本節（`afb3988`）で上書きされ、
現在の正式仕様は「初回・📝・🔄・⑧とも最大4」である。**
（`729d306` の「青バーなし・2倍描画」「⑧の掲載台を🔄と揃える」「表とスランプの台番一致」はそのまま有効。）

### D. 正式仕様

新宿歌舞伎町の記事用 `ジャグラーシリーズ優秀台.jpg` は：

| 掲載機種数（パネル登録あり） | パネル |
|---|---|
| 1機種 | 1パネル |
| 2機種 | 2パネル |
| 3機種 | 3パネル（2列並べのため右下が1枠空く。高田馬場と同じ既存の並べ方） |
| 4機種以上 | **最大4パネル** |

- 対象経路：**初回プレビュー（🔍）／📝記入部分のみ／🔄その他を更新／⑧本番／ZIP**（すべて同じ）
- 採用：既存どおり**機種ごとの最高差枚が大きい順**（パネル未登録機種は繰り上げ）
- 表示順：既存正式仕様どおり**代表台番（掲載台の最小台番）昇順**（記事用は `order_by_min_ban=True`）

### E. 実装（1行だけ）

```python
# 修正前
_ART_JUG_PANEL2_STORES: "frozenset[str]" = frozenset({"渋谷新館", "新宿歌舞伎町"})
# 修正後
_ART_JUG_PANEL2_STORES: "frozenset[str]" = frozenset({"渋谷新館"})
```

- **新しいロジックは追加していない。**4経路とも既存の `_art_panel_max()` → `_build_variety_panel_grid()` を通る。
- `_art_panel_max("新宿歌舞伎町", "ジャグラーシリーズ優秀台.jpg")` は **4**、渋谷新館は **2** のまま。
- 🔄・⑧の `4 if (作り直し) else _art_panel_max(...)` の分岐はそのまま（どちらも4になる）。

### F. 変更していないもの

**渋谷新館の最大2（`_ART_JUG_PANEL2_STORES = {"渋谷新館"}`）／高田馬場等の既存4パネル仕様／
⑤オススメの2枚上限（`_ART_OSU_PANEL2_STORES`）／その他の優秀台ピックアップ／抽出条件・表・スランプ・
画像名・結果テキスト・WordPress。**

### G. 確認結果

**8502（`.git` なしの複製・出力先は一時フォルダ）・2026/10/17・749台（対象ジャグラー9機種）**
- 初回・📝・🔄（マイジャグV_高配分OFF）・⑧とも4パネル。⑧は🔄と同じ4機種・同じ並び。
- 1/2/3/4機種で 1/2/3/4 パネル（実データの機種を絞って計算）。修正前は3機種以上でも2枚。

**Cloud（2026/10/17・749台）**
- 初回・📝・🔄 の `ジャグラーシリーズ優秀台.jpg` は **8502確認済み画像とハッシュ一致**（4パネル）。
- ⑧本番：ZIP内の同画像は 1946×9992 で8502の⑧と同寸、パネル2段目の存在を確認＝最大4パネル。
- OFFにした `マイジャグV_高配分.jpg` は⑧で生成されずZIPにも無い（OFF反映）。例外0。
- ★1/2/3機種・渋谷新館（2枚のまま）は Cloud 画面では確認していない（8502計算と本体コードの値で確認）。

### H. 禁止事項・保全

1. **新宿歌舞伎町を `_ART_JUG_PANEL2_STORES` へ戻さない**
2. **渋谷新館を `_ART_JUG_PANEL2_STORES` から外さない**（渋谷新館の2枚は明示指示による正式仕様）
3. **`cec23c7` / `729d306` 節の「最大2」を現在の仕様として扱わない**（本節が上書き）
4. **新しいパネル選定ロジック・独自レイアウトを作らない**（既存 `_build_variety_panel_grid()` を使う）
5. **⑤オススメ・その他の優秀台・他店舗の上限を本仕様を理由に変えない**
6. `wrt_machines.json`・`article_page_inputs.json`・`auto_page_inputs.json` の既存差分、未追跡4件、stash 5件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
7. `afb3988` へ reset・revert しない

<!-- VERBATIM-END id=S27664 -->

<!-- VERBATIM-BEGIN id=S27942 src=CLAUDE.md@fde5030 lines=27942-28010 sha256=c1c59131afcc811b27bd8e1bf879f0c7c01c88a5cb62283488bc0502d9be07d4 -->
## 【正式仕様】新宿歌舞伎町 記事用：記事コメント「ニブイチ系」に②個別「優秀台」の機種を含める（2026-10-19・`ca5970e`）

**正式仕様。巻き戻し禁止。**対象は**記事コメントを使う店舗（`_ART_COMMENT_STORES`）の記事用ページで、🔍プレビュー時に作る記事コメントの元データ `_art_cmt_src_{store}` の `high_names` だけ**。
発見・確認は**新宿歌舞伎町 2026/10/18**。**8502確認後に本体へ反映し、Streamlit Cloud 実機で確認済み（ユーザー承認）。**既存節（「記事用：「🔄 その他を更新」後に記事コメントを掲載状態へ同期（`f2ee0a7`）」ほか）は削除・圧縮・統合・書き換えしない。

### A. 正式commit

| 項目 | 内容 |
|---|---|
| 正式commit | **`ca5970e`**（`fix: 記事コメントに個別優秀台の機種を反映`・`streamlit_app.py` のみ・+7 / −2） |
| 変更箇所 | `show_auto_article_page()` 内、🔍プレビュー時の `high_names` の1か所だけ。新規・削除関数0 |

**`ca5970e` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 原因

- 🔍プレビュー時の `high_names` は**自動高配分で画像がある機種**（`high_ratio_list` の `has_image`）だけだった。
- ②個別「優秀台」へ入力した機種は自動高配分を作らない決まり（`recommended_machines`）のため、`high_ratio_list` には最初から入らない。
- 実際に描画した②優秀台の機種一覧 **`_art_cmt_high_manual`** は🔍でも作られていたが、📝記入部分のみのときしか使われていなかった。
- `f2ee0a7` の🔄同期処理は元の一覧から**外すことしかできない**ため、元の一覧に無い②優秀台の機種は戻せなかった。
- 結果、10/18では最終プレビューに残っているニブイチ系10機種に対し、コメントは**7機種**だった（差分＝真打吉宗・かぐや様・邪神ちゃん）。

### C. 正式仕様

```python
"high_names": (list(_art_cmt_high_manual) if _art_manual else
               list(dict.fromkeys(
                   [h["name"] for h in _art_pr.get("high_ratio_list", [])
                    if h.get("has_image")]
                   + list(_art_cmt_high_manual)))),
```

- 🔍プレビュー時の `high_names` は **「自動高配分で画像がある機種」＋「実際に描画された②個別優秀台の機種 `_art_cmt_high_manual`」を重複なしで結合**する。
- **コメントは最終プレビューでONになっている対象機種に追従する**（OFFは既存の `_art_cmt_src_after_update()` が `（優秀台）.jpg` の持ち主として外し、ONへ戻せば復活する）。
- **新しい集計は作らない。コメント生成関数（`_art_cmt_facts_*` / `_art_cmt_cands_*`）は変更しない。**
- 📝記入部分のみは従来どおり `_art_cmt_high_manual` だけ（元から正しい）。
- ②入力機種は自動高配分を作らないため、結合しても重複しない。②優秀台を入れない日は修正前と同じ結果。

### D. Cloud確認（新宿歌舞伎町 2026/10/18・749台）

| 操作 | ニブイチ系の機種数 |
|---|---|
| 🔍プレビュー直後 | **16**（自動13＋②優秀台3。旧コードなら13） |
| 自動高配分6枚OFF →「その他を更新」 | **10**（旧コードなら7） |
| かぐや様（優秀台）OFF →「その他を更新」 | **9** |
| かぐや様をONへ戻す →「その他を更新」 | **10** |

- **候補①②③すべて同じ機種数**。
- **最終プレビューのON対象数（自動高配分7枚＋②優秀台3枚＝10、OFF時は9）と一致**。
- **⑧実行後も10機種のまま**（コメント元は⑧で作り直さない）。**ZIP・`1018_結果.txt` は正常生成**。WordPress下書きボタンは押していない。
- **アプリの Traceback 0件。**`removeChild` が1件表示されたが、Chrome自動翻訳で翻訳済みのまま残った画面要素（①「WordPressメディアから選ぶ」付近）で起きた**既知のブラウザ側現象で、コード不具合ではない**。
- 8502（`.git` なしの複製）でも同じ結果（16→10→9→10、📝記入部分のみは3機種）を確認済み。

### E. 変えていないもの

高配分判定 ／ ②優秀台の抽出・描画 ／ 全台系 ／ 並び ／ その他 ／ オススメ ／ ジャグラー ／ 📝記入部分のみ ／ ⑧画像生成ロジック ／ `_art_cmt_src_after_update()` ／ コメント生成関数。

### F. 未対応・別件

②全台に「・2F／・3F」付きの機種名を入れた場合、🔍の `kojin_zen` は入力名そのまま（例「ファンキー2・2F」）で集計されるため、**全台系コメントの機種数がずれる可能性がある**。10/18は該当なし。**今回は修正していない（別件として扱う）。**

### G. 禁止事項・保全

1. 🔍の `high_names` を自動高配分だけへ戻さない（②優秀台が消える）
2. ②優秀台を入力値から直接足さない（実際に描いた `_art_cmt_high_manual` を使う）
3. コメント生成関数・`_art_cmt_src_after_update()` を本仕様を理由に変えない
4. F の「・2F／・3F」問題を本仕様の記録を理由に勝手に直さない（別件）
5. `wrt_machines.json` の既存差分、未追跡4件、stash 5件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
<!-- VERBATIM-END id=S27942 -->

<!-- VERBATIM-BEGIN id=S28011 src=CLAUDE.md@fde5030 lines=28011-28047 sha256=beff830654f38372b5b28f931988349e1b77f01f0906c9d8aabdd5f7150b4a08 -->
## 【正式仕様】新宿歌舞伎町 記事用WordPress：「その他のジャグラーの優秀台」の文章へ+1,000枚超台数を追加（2026-10-19・`986b56c`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）→ WordPress本文の「その他のジャグラーの優秀台」ブロックの文章だけ**。
「新宿歌舞伎町 記事用WordPress：「その他のジャグラーの優秀台」ブロック追加と③の列→並び掲載順（`414e627` / `80eae5c`）」節の
「文章に台数表記を足さない」は当時の正式記録として残し、**本節が後発仕様として上書き**する。既存節は削除・書き換えしない。

| 項目 | 内容 |
|---|---|
| 正式commit | **`986b56c`**（`fix: WordPress記事にジャグラー1000枚超台数を追加`・`streamlit_app.py` のみ・+6 / −2） |
| 変更関数 | **`_jug_total_wp_text()` のみ**。新規・削除関数0 |

**`986b56c` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### A. 正式仕様

- 台数は**既存 `_juggler_total_stat()` の +1,000枚以上台数を再利用**する（新しい集計を作らない）。
- 既存の `本日のジャグラー全体の結果は総差枚{±X枚}、平均差枚{±Y枚}！` の**後ろに `○台が+1,000枚オーバー！` を追加**する。
- **0台のときはこの文を出さない。**
- 掲載順は従来どおり **見出し → 画像 → 文章**。
- **他店舗、結果テキスト（`juggler_summary_section()`）、画像生成、`wp_client.py` は変更なし。**

### B. 確認

- 2026/10/18：**総差枚 +22,200枚・平均差枚 +90枚・57台**。
- **結果テキストと記事用の台数が一致**。
- 見出し → 画像 → 文章の順。
- **Cloud で⑧完走・Traceback 0。**
- **WordPress下書きは未作成**（WordPress通信なし）。

### C. 禁止事項・保全

1. 台数を `_juggler_total_stat()` 以外で再計算しない
2. 0台で文を出さない／総差枚・平均差枚の文を変えない
3. 結果テキスト・画像生成・`wp_client.py`・他店舗を本仕様を理由に変えない
4. `wrt_machines.json` の既存差分、未追跡4件、stash 5件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止

<!-- VERBATIM-END id=S28011 -->

<!-- VERBATIM-BEGIN id=S28048 src=CLAUDE.md@fde5030 lines=28048-28100 sha256=062f18bd468a562cc19603c232038512957f1c070d248889a1bb9ddd433693a8 -->
## 【正式仕様】新宿歌舞伎町 記事用：ジャグラー高配分画像は優秀台が総台数の50%以上のときだけ（2026-10-19・`ae00fd7`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`auto_article`）のジャグラー高配分画像（`{機種名}_高配分.jpg`・`run_step2_juggler()`）の生成条件だけ**。
**8502確認後に本体へ反映し、Streamlit Cloud 実機で確認済み（ユーザー承認）。**既存節は削除・圧縮・統合・書き換えしない。

| 項目 | 内容 |
|---|---|
| 正式commit | **`ae00fd7`**（`fix: 新宿記事用ジャグラー高配分を50%以上に限定`・`streamlit_app.py` のみ・+13 / −3） |
| 新規定数 | **`_ART_JUG_HALF_STORES = frozenset({"新宿歌舞伎町"})`** |
| 引数 | **`run_step2_juggler(..., jug_high_half: bool = False)`**（既定 False＝従来動作） |
| 呼び出し | `run_auto_pipeline()` の Step2 呼び出し2か所（通常／📝の⑤平均用）で **`jug_high_half=(article_mode and store in _ART_JUG_HALF_STORES)`** |

**`ae00fd7` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### A. 原因（記録）

従来の判定は「優秀台2台以上 かつ（総台数の半分以上 **または 10台以上**）」または少数機種ルールで、
台数の多い機種（マイジャグV 100台中30台 など）は「10台以上」だけで高配分画像になっていた。

### B. 正式仕様

- 分母＝**その機種の当日総台数**（`total_all`）、分子＝**既存ロジックの優秀台数**（`filtered`）。
- **優秀台2台以上 かつ 優秀台数÷総台数が50%以上**（`len(filtered) >= 2 and len(filtered) * 2 >= total_all`）のときだけ高配分画像を作る。**ちょうど50%は作る。**
- この店舗・ページでは「10台以上」と少数機種ルール（`small_machine_rule`）は使わない。
- **50%未満は高配分画像を作らず、既存の else 分岐で統合プール（その他のジャグラーの優秀台）へ流す。**新しい流し先の処理は作っていない（台番重複なし・台番順は既存処理）。
- **1台設置1台優秀は従来どおり作らない**（「優秀台2台以上」を残す）。
- **流した結果、統合対象が5台以下なら既存仕様どおり「その他の優秀台」へ回る。**
- 優秀台そのものの判定基準・差枚計算は変更していない。⑤最優先機種の平均表示判定（`_meets_jug_meta`）も同じ条件になる。
- **結果ポスト用・通常ページ・他店舗は変更なし**（`jug_high_half` 既定 False で従来式と同じ）。

### C. 確認

**8502（10/18・749台）**：マイジャグV 100/30・マイジャグVI 11/2・ファンキー2 38/11・ゴージャグ3 29/9・ネオアイム 37/14・ジャグラーガールズ 14/4 は作らない、ハピジャグV 7/4・ウルトラミラジャグ 5/4 は作る。
境界（20台中10台・6台中3台・40台中20台は作る／20台中9台・40台中19台は作らない）・統合の重複なし・台番順・通常ページの出力が修正前と一致を確認。

**Cloud（新宿歌舞伎町・10/18）**
- マイジャグV／ネオアイム／ファンキー2：高配分画像なし
- ハピジャグV：高配分画像あり
- その他ジャグラー 63台
- ハピジャグVをOFF →🔄その他を更新で統合画像へ反映
- ⑧完走・ZIP／`1018_結果.txt` 生成
- 例外0

### D. 禁止事項・保全

1. 新宿歌舞伎町の記事用で「10台以上」・少数機種ルールによる高配分生成へ戻さない
2. 「優秀台2台以上」条件を外さない／50%判定を表示文字列や別集計で行わない
3. `jug_high_half` の既定 False を変えない／`_ART_JUG_HALF_STORES` へ承認なしに他店舗を追加しない
4. 50%未満の機種用に新しい流し先・統合処理を作らない（既存の統合プール・5台以下 overflow を使う）
5. 結果ポスト用・他店舗・優秀台判定・差枚計算を本仕様を理由に変えない
6. `wrt_machines.json` の既存差分、未追跡4件、stash 5件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止

<!-- VERBATIM-END id=S28048 -->

<!-- VERBATIM-BEGIN id=S28209 src=CLAUDE.md@fde5030 lines=28209-28266 sha256=85080bea95dfca2b2bee4870a75c1fafce8f1e92bd112bd91d80e0628da15406 -->
## 【正式仕様】新宿歌舞伎町 記事用：🔄その他を更新／⑧でON画像の掲載台を「その他の優秀台」へ重複させない（2026-10-20・`e9dc51e`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`page=auto_article`）の「🔄 その他を更新」と⑧本番で作り直す「その他の優秀台ピックアップ」だけ**。
**8502確認後に本体へ反映し、Streamlit Cloud 実機（10/19・749台）で確認済み。**既存節は削除・圧縮・統合・書き換えしない。

| 項目 | 内容 |
|---|---|
| 正式commit | **`e9dc51e`**（`fix: 新宿記事用のその他更新で掲載台重複を防止`・`streamlit_app.py` のみ・+78 / −2） |
| 新規 | 定数 **`_ART_SON_ON_EXC_STORES = frozenset({"新宿歌舞伎町"})`**／関数 **`_art_on_img_bans()`** |
| 変更関数 | `show_auto_article_page()` のみ |

**`e9dc51e` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### A. 不具合（記録）

10/19 の📝記入部分のみで、②優秀台に東京喰種を入れたまま東京喰種の並び画像3枚をOFFにして🔄を押すと、
**801・802・803・832・833・840・841番台**が「その他の優秀台」へ入った（いずれも東京喰種（優秀台）画像に掲載中の台）。
原因は、🔄・⑧がOFF画像の +1,000枚以上の台をその他へ戻すとき、**まだONの画像に載っている台を確認していなかった**こと。
⑦の画像ごとの掲載台番（`_pv_bm_sl`）は保存されておらず、🔄・⑧から参照できなかった。記事用の共通処理なので機種を問わず起き得る。

### B. 正式仕様

1. **⑦で画像ごとの実掲載台番を保持**する（`art_preview_bm_{store}`。🔄でその他を作り直したらその台番で更新）。
2. **🔄・⑧で、ONの画像に載っている台は「その他の優秀台」へ流入させない**（`_art_on_img_bans()` で現在ONの画像の掲載台を集めて除外。その他画像自身は対象外）。
   機種名による固定除外はしない。
3. **📝→🔄のその他は、全自動版ではなく⑦📝で実際に載せたその他の台を土台にする**（`art_preview_son_base_{store}`。📝以外は従来どおり）。
   従来は全自動版を土台にしていたため、158番台（からくりサーカス2）・1449番台（スタハナ30）が落ちていた。
4. **⑧📝のその他画像は📝で抽出した台を土台に作り直し、スランプの台番も作り直した表と同じにする**
   （従来は表が1行になり、スランプとずれていた）。
5. **その他の台番は重複を除く。**

ゲートは `_ART_SON_ON_EXC_STORES` だけで、**他店舗の記事用・通常ページは従来どおり**。

### C. Cloud確認（新宿歌舞伎町・10/19・📝記入部分のみ）

| 操作 | その他の優秀台 |
|---|---|
| 並び5枚OFF（東京喰種3・青ブタ・獣王93-95）＋東京喰種（優秀台）ON | **57台・東京喰種0・重複0**（158 / 1449 / 95番台あり） |
| ＋東京喰種（優秀台）もOFF | **74台・東京喰種17台流入**（839は末尾39側） |
| 東京喰種（優秀台）をONへ戻す | **57台・画像ハッシュ一致** |
| ⑧本番 | **🔄と一致**（8502の⑧と同寸） |

例外0。WordPress通信なし。

### D. 別件として未対応（今回触っていない）

- 結果テキスト「👑並び仕掛け」に、OFFにした並びが残る
- 結果テキスト「👑その他の優秀台」が（なし）になる（📝の⑧）
- 📝でジャグラー統合が5台以下になりその他へ回す経路（⑧で同じ土台の問題が残る）

### E. 禁止事項・保全

1. ON画像の掲載台をその他へ戻す方式に戻さない／機種名で固定除外しない
2. `art_preview_bm_{store}` / `art_preview_son_base_{store}` の保存を外さない
3. `_ART_SON_ON_EXC_STORES` へ承認なしに他店舗を追加しない
4. D の未対応3件を本仕様の記録を理由に直さない（別件）
5. `article_page_inputs.json`・`wrt_machines.json` の既存差分、未追跡4件、stash 5件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
<!-- VERBATIM-END id=S28209 -->

<!-- VERBATIM-BEGIN id=S28267 src=CLAUDE.md@fde5030 lines=28267-28317 sha256=6c4aa1f7ec503f67d4299c225014f968761b0492e85335d0a179fb2f64ce098b -->
## 【正式仕様】新宿歌舞伎町 記事用：🔄その他を更新後、記事コメントの並び／列を最終ON画像に追従（2026-10-20・`2a65f16`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】→ 記事用（`page=auto_article`）の📝記事コメント「並び」（並び・列）だけ**。
**8502確認後に本体へ反映し、Streamlit Cloud を Reboot して実機確認済み（10/19・749台）。**既存節は削除・圧縮・統合・書き換えしない。
「記事用：「🔄 その他を更新」後に記事コメントを掲載状態へ同期（`f2ee0a7`）」節の追加仕様である（同節はそのまま有効）。

| 項目 | 内容 |
|---|---|
| 正式commit | **`2a65f16`**（`fix: 新宿記事コメントの並び件数をON画像に追従`・`streamlit_app.py` のみ・+37 / −3） |
| 新規定数 | **`_ART_CMT_NB_SYNC_STORES = frozenset({"新宿歌舞伎町"})`** |
| 変更 | `_art_cmt_src_after_update(..., nb_fn_bans=None, col_fn_bans=None)`（既定 None＝並び・列は触らない）／`show_auto_article_page()` |

**`2a65f16` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### A. 不具合（記録）

📝記入部分のみで並び画像のチェックをOFFにして🔄を押しても、記事コメントの並びが「20か所」のままだった。
`_art_cmt_src_{store}` の `nami`（③に入力した並び範囲20件）と `retsu` はプレビュー生成時の値のままで、
`f2ee0a7` の🔄同期は全台系・高配分・その他しか作り直していなかった。⑧も同じコメント元を使うため20か所になっていた。

### B. 正式仕様

- **📝記事コメントの並び／列は、最終プレビューでONの画像だけを反映する。**
- **OFF画像と同じ掲載台番の並び／列をコメント元から除外する**（ONへ戻せば復活する）。
- 照合には**⑦が保存済みの 画像名→掲載台番**（`art_preview_narabi_{store}` / `art_preview_col_{store}`）を再利用する。新しい集計は作らない。
- コメント元の並び1件ごとに照合用の `bans` を持たせる（新宿歌舞伎町のみ・コメント文には使わない）。
- **固定件数にしない。**最終ON状態に追従する。
- **全台系・高配分・その他など他コメントは変更しない。**
- **渋谷新館は従来仕様のまま**（`_ART_CMT_NB_SYNC_STORES` に含めない）。

### C. Cloud確認（新宿歌舞伎町・10/19・📝記入部分のみ）

| 操作 | コメント | ONの並び画像 |
|---|---|---|
| 📝プレビュー直後 | 20か所 | 20枚 |
| 並び5枚OFF →🔄 | **15か所** | 15枚 |
| さらに1枚OFF →🔄 | **14か所** | 14枚 |
| ONへ戻す →🔄 | **15か所** | 15枚 |
| ⑧本番 | **15か所** | 出力並び画像15枚 |

例外0。**渋谷新館**は並び3枚から1枚OFF→🔄後も従来どおり「計3箇所」のまま（非影響）。
※ 2a65f16 は push 直後の Cloud に反映されず、Reboot 後に確認した。

### D. 禁止事項・保全

1. 記事コメントの並び／列をプレビュー生成時の固定値へ戻さない／件数を固定で書き換えない
2. ⑦保存の画像名→掲載台番以外で並びを数え直さない（新しい集計を作らない）
3. `nb_fn_bans` / `col_fn_bans` の既定 None を変えない／`_ART_CMT_NB_SYNC_STORES` へ承認なしに他店舗（渋谷新館を含む）を追加しない
4. 全台系・高配分・その他のコメント同期（`f2ee0a7`）を本仕様を理由に変えない
5. `wrt_machines.json` の既存差分、未追跡4件、stash 5件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
<!-- VERBATIM-END id=S28267 -->

