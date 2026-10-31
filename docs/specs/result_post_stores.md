# 結果ポスト系：店舗別

対象：新宿歌舞伎町3系統・新小岩⑤ジャグラー・稲毛/新小岩/3店舗のslotterguild取得・gap猫撤去・マイジャグVI・ジャグラー閾値記憶

> このファイルは旧 `CLAUDE.md`（blob `fde5030`・commit `bfb9ad5`）から機械的に切り出した正式仕様の原文です。
> `VERBATIM-BEGIN` 〜 `VERBATIM-END` の間は1文字も変更しないこと（要約・統合・削除も禁止）。
> 新しい正式仕様は、このファイルの末尾（マーカーの外）へ追記してください。
> 完全一致の確認：`py -3.14 tools/verify_claude_split.py`

<!-- VERBATIM-BEGIN id=S05737 src=CLAUDE.md@fde5030 lines=5737-6025 sha256=7a0fad1b346429320ba24d3754e30eb1c8b19078aa9f0fc2be9de02e6c37eb55 -->
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

<!-- VERBATIM-END id=S05737 -->

<!-- VERBATIM-BEGIN id=S14387 src=CLAUDE.md@fde5030 lines=14387-14681 sha256=338db5a4e3211f9b1ece3e79d8ccebcfe2dc6eb96d238bde93fd3a9d5f4ccd76 -->
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

<!-- VERBATIM-END id=S14387 -->

<!-- VERBATIM-BEGIN id=S18625 src=CLAUDE.md@fde5030 lines=18625-18903 sha256=934e7dcf0e9b337563396b9276dbd2b82bf6e60273bfafea44d3cf689ccd15da -->
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

<!-- VERBATIM-END id=S18625 -->

<!-- VERBATIM-BEGIN id=S18904 src=CLAUDE.md@fde5030 lines=18904-19078 sha256=cb2b282bd9a4fe09c98537fa43f72d5f2a792d3a70f9ae7970cf75206ccb12c2 -->
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

<!-- VERBATIM-END id=S18904 -->

<!-- VERBATIM-BEGIN id=S19079 src=CLAUDE.md@fde5030 lines=19079-19413 sha256=cb7068e9d63828e32ec912e4e2bef45f8ce8813b2903da0e1287ab3a12e16c06 -->
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

<!-- VERBATIM-END id=S19079 -->

<!-- VERBATIM-BEGIN id=S21835 src=CLAUDE.md@fde5030 lines=21835-21905 sha256=73839a8ece3a3ad4f91a65b6a08d1c2a299ac28ed9839b1133e94648e8ab223f -->
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

<!-- VERBATIM-END id=S21835 -->

<!-- VERBATIM-BEGIN id=S24100 src=CLAUDE.md@fde5030 lines=24100-24181 sha256=4431ddf5bbcc19621017fd83be9db915d9591cd47f28be324a00c0419898d49c -->
## 【正式仕様】新宿歌舞伎町 📈スランプ付き結果ポスト：🔄その他を更新でのジャグラー優秀台の再振り分け（2026-10-01・`a5a799d`）

**正式仕様。巻き戻し禁止。**対象は
**【新宿歌舞伎町】→ 📈スランプ付き結果ポスト（`auto_slump2`）→ ⑦プレビュー後の `🔄その他を更新`**。
**Cloud 実機で「ネオアイムOFF → 🔄その他を更新」を確認済み（ユーザー確認）。**既存節は削除・書き換えしない。

### A. 正式commit

| commit | 内容 |
|---|---|
| **`a5a799d`** | `fix: 新宿歌舞伎町スランプ付き結果の🔄でOFFにしたジャグラー機種の優秀台をジャグラー統合画像へ移す`（`streamlit_app.py` のみ・+91 / −6） |

`a5a799d` は現HEADの祖先であることを確認済み。**`a5a799d` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 対象範囲

- ジャグラー機種の個別画像（`{機種名}_高配分.jpg` 等）のチェックをOFFにしたときの、
  **「その他の優秀台」と「その他のジャグラーの優秀台」（`ジャグラーシリーズ優秀台.jpg`）の再振り分けだけ**。
- ゲートは **`_JUG_OV_MOVE_PAGES = frozenset({"auto_slump2"})` × `_JUG_OV_MOVE_STORES = frozenset({"新宿歌舞伎町"})`**
  の AND を返す **`_jug_ov_move_on(store)`**（保存フラグなし・Streamlit外は False）。
  全7ページ×14店舗で ON は `auto_slump2 × 新宿歌舞伎町` の1通りだけ。
- **対象外**：かぶぱ（`auto_slump`）、記事用、通常の結果ポスト、他店舗。

### C. 仕様

- チェックOFFにしたジャグラー機種は、**その他の優秀台の抽出条件（+1,000枚以上）を満たす台**を「その他のジャグラーの優秀台」へ移す。
- **同じ台を「その他の優秀台」に残さない。**ジャグラー該当台は2画像の**どちらか片方だけ**に入り、**重複・取りこぼしを出さない。**
- **ジャグラー以外のその他の優秀台は従来どおり維持**する。
- **チェックOFFにしていないジャグラー機種で、自前画像を持つ機種の掲載台は勝手に移動させない。**
- **該当台が0台、または統合条件（6台以上）を満たさない場合は、ジャグラー画像を作らない既存挙動**（5台以下はその他へ）を維持する。
- **新宿歌舞伎町の📈スランプ付き結果ポストはパネルなし**の正式仕様（`7308977`）を維持する。

### D. 根本原因

1. 旧処理は「移さない機種」を**高配分リストの全機種**（`set(_pv_hr.values())`）にしていた。
   リストには**自前画像を持たない機種（`has_image=False`・例：ジャグラーガールズ）**も含まれるため、
   その機種の overflow 台が除外されて**その他の優秀台に残っていた**。
2. チェックOFF機種の台を**ジャグラーの合算確率条件**で拾っていたため、
   **+1,000枚未満の台までジャグラー画像へ入る**不整合があった。

### E. 実装

- **🔄**：既存の再振り分け経路のまま、「移さない機種」を**⑦で保存した自前画像のある機種だけ**
  （`st.session_state[_aprev_hr_img_key]`＝`auto_preview_hr_img_{store}`）に絞る
  （`_jug_ov_used_bans` と `_jug_hr_names_pv` の2か所）。チェックOFF機種は **+1,000枚以上**で拾う
  （既存 `else` 分岐へ通す）。ジャグラー画像のスランプ台番は、実際に載せた台番（`_jug_comb_bans_upd`）に揃える。
- **⑧**：ジャグラー画像の作り直しは元から同じ絞り方（`has_image` のある機種だけ除外）だった。
  **移した台（`_jug_ov_mv_e`）をその他の優秀台から外す処理を補い**、移した結果その他が0台なら
  古い同名画像を `_rm_stale_image()`（完全一致）で削除する。
  チェック中の並び台・末尾該当台の除外（`_jov_drop_e`）も🔄と揃える。スランプ台番も実掲載台に揃える（`_jug_comb_bans_e`）。
- **完成画像の後加工・切り貼りはしない。**

### F. 検証・Cloud確認

- **2026/9/30・749台**（Pision確定データ）：⑦時点はジャグラー統合5台で overflow、その他64台（うちジャグラー5台）。
  **ネオアイムOFF → 🔄** で、ジャグラー側へ **1047・1069・1090・1092・1140・1141・1143・1148 の8台**が入り、
  **その他は64台 → 59台**、**画像間の重複0台・その他に残るジャグラー0台**。
  旧処理では ジャグラーガールズ4台（1140・1141・1143・1148）がその他に残り、ネオアイムの+1,000枚未満の台がジャグラー画像へ入っていた。
- **チェックOFFなしは変更前と一致。**ジャグラー以外（東京喰種）をOFFにしても**ジャグラー側は不変**。
  ジャグラー以外のその他の優秀台も不変。
- **Cloud で「ネオアイムOFF → 🔄その他を更新」を実画面確認し、移動・重複なし・パネルなしを確認済み。**
- 実装検証は **Pision 確定データGETのみ**。**WordPress 通信・Cloud 操作はしていない。**

### G. 変更しない対象

- **記事用📝のジャグラー再振り分け仕様（`cec23c7`）とは別経路**であり、変更していない。
- 表、ピンクバー、スランプ（描画）、台番順、画像名、入力・保存、かぶぱ、他店舗、抽出条件の他カテゴリ。

### H. 禁止事項・保全

1. 「移さない機種」を高配分リストの全機種へ戻さない（`_aprev_hr_img_key` の自前画像ありの機種だけ）
2. チェックOFFのジャグラー機種を合算確率条件で拾う方式へ戻さない（+1,000枚以上）
3. ⑧で移した台をその他から外す処理を外さない／⑦→🔄 と ⑧ の掲載台をズラさない
4. `_jug_ov_move_on()` のゲートを他店舗・他ページへ広げない／保存フラグ方式にしない
5. 統合条件（6台以上）・0台時の画像なしの既存挙動を変えない
6. 新宿歌舞伎町 `auto_slump2` にパネルを付けない
7. 完成画像の後加工・切り貼りで代替しない
8. 記事用📝のジャグラー再振り分け・かぶぱ・他店舗を本仕様を理由に変更しない
9. `wrt_machines.json`・`auto_page_inputs.json` の既存差分、未追跡4件、stash 4件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
10. `a5a799d` へ reset・revert しない

<!-- VERBATIM-END id=S24100 -->

<!-- VERBATIM-BEGIN id=S24182 src=CLAUDE.md@fde5030 lines=24182-24266 sha256=c3e28a68d1c69576ff743023dd4de528b9949cec5cb5633135b526539c6a0642 -->
## 【正式仕様】新宿歌舞伎町 📈スランプ付き結果ポスト：統合ジャグラー画像OFF時のその他の優秀台への戻し（2026-10-01・`fc74518`）

**正式仕様。巻き戻し禁止。**対象は **【新宿歌舞伎町】→ 📈スランプ付き結果ポスト（`auto_slump2`）だけ**。
**Cloud 実機で「ネオアイムOFF → 🔄 → 統合ジャグラー画像OFF → 🔄 → ⑧」を確認済み（ユーザー確認）。**
既存節は削除・書き換えしない。直前の節「🔄その他を更新でのジャグラー優秀台の再振り分け（`a5a799d`）」の**追加仕様**である。

### A. 正式commit

| commit | 内容 |
|---|---|
| `a5a799d` | 個別ジャグラー画像OFF時の、統合ジャグラー画像への再振り分け（先行・正式記録 `3a8ea67`） |
| **`fc74518`** | `fix: 新宿歌舞伎町スランプ付き結果で統合ジャグラー画像OFF時に+1,000枚以上の台をその他の優秀台へ戻す`（`streamlit_app.py` のみ・+77 / −4） |

どちらも現HEADの祖先であることを確認済み。直後のアプリ自動commit `1fa523e`（`auto_page_inputs.json`）は有効な履歴として保全する。
**どのcommitへも reset・revert しない。**

### B. 対象範囲

- ⑦プレビュー後に **「その他のジャグラーの優秀台」（`ジャグラーシリーズ優秀台.jpg`）をチェックOFF** にして `🔄その他を更新` を押す場合。
- **⑧本番でも同じチェック状態を反映する。**
- ゲートは既存の **`_jug_ov_move_on(store)`**（`auto_slump2` × 新宿歌舞伎町の AND）。
- **対象外**：かぶぱ（`auto_slump`）、記事用、通常の結果ポスト、他店舗（従来の統合OFF処理のまま）。

### C. 仕様

- **統合ジャグラー画像がONの間は、従来どおり該当ジャグラー台をその他の優秀台から除外する**（`a5a799d`）。
- **統合ジャグラー画像をOFFにした場合、同画像へ掲載されるはずだった台のうち +1,000枚以上の台だけをその他の優秀台へ戻す。**
- **+1,000枚未満の台はその他の優秀台へ戻さない**（その他にも残さない）。
- **統合ジャグラー画像はOFF時に作り直さず、出力・プレビューから外す**（OFFのまま扱い、⑧で生成・保存しない）。
- **その他の優秀台と統合ジャグラー画像の間で、重複・取りこぼしを出さない。**
- **並び・末尾・ONの個別画像などの既存除外条件は維持する。**
- **新宿歌舞伎町の📈スランプ付き結果ポストはパネルなし**（`7308977`）を維持する。

### D. a5a799d との整合

- 個別ジャグラー画像をOFFにした台は、**まず統合ジャグラー画像の候補になる**（`a5a799d` の既存仕様を維持）。
- さらに統合ジャグラー画像もOFFにした場合、**その候補台のうち +1,000枚以上だけ**をその他の優秀台へ戻す。
- **どの操作順でも各台の所属は一意**で、画像間で重複しない。

### E. 根本原因

1. **旧🔄**は統合OFF時に「高配分リストの全機種を除いた残り」から戻す台を選んでいたため、
   **自前画像のないジャグラー機種（ジャグラーガールズ）や個別OFFで移った台（ネオアイム）を取りこぼし**、
   さらに個別OFF分から統合画像を作り直していたため **1047番台が両画像に重複**していた。
2. **旧⑧**は、統合ジャグラー画像をOFFにしても、個別OFF分があると**作り直して保存**していた。

### F. 実装

- チェック状態は既存のプレビュー状態 **`_pv_is_on(store, uploaded.name, "ジャグラーシリーズ優秀台.jpg")`** を使う。
  **統合画像がプレビュー一覧にあり、OFFで、かつ横版（`ジャグラーシリーズ優秀台_side.jpg`）もONでないとき**だけ適用する。
- **統合画像に載る台は、既存の作り直し時と同じ組み立て**で求める：
  jug_pool があればそれ、無ければ jug_overflow のうち**自前画像のない機種**の台（⑦保存の `auto_preview_hr_img_{store}`／⑧は `has_image`）
  ＋ 個別OFF機種の +1,000枚以上の台（`_jug_extra_dfs`／⑧は `_jug_ex_dfs`）。
- 🔄：その台番（`_jug_off_bans`）をその他の基礎集合から外し、うち +1,000枚以上を `_upd_extra_dfs` へ戻す。
  `_jug_extra_dfs` を空にして統合画像を作り直さない。従来の統合OFF分岐はこの店舗では通さない（`and not _jug_ov_move_on(store)`）。
- ⑧：同じ判定（`_jug_off_e`）で +1,000枚以上を `_extra_dfs` へ戻し、その他の基礎集合とスランプ台番から外し、`_jug_ex_dfs` を空にして再生成しない。
- **画像の後加工・切り貼りはしない。**

### G. 検証・Cloud確認

- **2026/9/30・749台**：ネオアイムOFF＋統合ジャグラー画像ONで **その他59台・ジャグラー8台・重複0台**（`a5a799d` と同じ）。
- さらに統合ジャグラー画像をOFF → **+1,000枚以上の7台（1047・1069・1090・1092・1141・1143・1148）がその他へ戻り、
  その他66台・ジャグラー画像なし・重複0台**。**+300枚の1140番台はその他へ戻らない。**
- **⑧も その他66台・統合ジャグラー画像を作り直さない**ことを、追加部分の実行で確認。
- チェック変更なし（64台）・ネオアイムOFFのみ（59台）は変更前と一致。ジャグラー以外のその他の台は全ケースで不変。
- **Cloud で「ネオアイムOFF → 🔄 → 統合ジャグラー画像OFF → 🔄 → ⑧」を実画面確認済み。**
- 実装検証は **Pision 確定データGETのみ**。**WordPress 通信・Cloud 操作・画像保存はしていない。**

### H. 変更しない対象

表、ピンクバー、スランプ（描画）、台番順、画像名、入力・保存、かぶぱ、記事用（記事用📝のジャグラー再振り分け `cec23c7` を含む）、他店舗。

### I. 禁止事項・保全

1. 統合OFF時に「高配分リストの全機種を除いた残り」から戻す方式へ戻さない
2. 統合OFF時に +1,000枚未満の台をその他へ戻さない／その他に残さない
3. OFFの統合ジャグラー画像を🔄・⑧で作り直さない
4. 統合画像に載る台を作り直し時と別の組み立てで求めない（⑦→🔄と⑧をズラさない）
5. 横版がONのとき・統合画像が一覧に無いときに本仕様を適用しない
6. `a5a799d` の個別OFF再振り分けを壊さない／`_jug_ov_move_on()` を他店舗・他ページへ広げない
7. 新宿歌舞伎町 `auto_slump2` にパネルを付けない／完成画像の後加工で代替しない
8. `wrt_machines.json` の既存差分、未追跡4件、stash 4件、アプリ自動commit履歴（`1fa523e` ほか）を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
9. `fc74518` / `a5a799d` へ reset・revert しない

<!-- VERBATIM-END id=S24182 -->

<!-- VERBATIM-BEGIN id=S24356 src=CLAUDE.md@fde5030 lines=24356-24455 sha256=e0a60b2f1fcca89c688460eecf7113c4ec3e5ef4a80b30f3cfcfa7bd6d89e742 -->
## 【正式仕様】新宿歌舞伎町：ジャグラー／その他優秀台の自動抽出閾値をページ別に記憶・復元（2026-10-01・`87b7cc0` / `24417c8` / `a8bb82f`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】の📈スランプ付き結果ポスト（`auto_slump2`）と記事用（`auto_article`）だけ**。
**Cloud 実画面で確認済み（ユーザー確認）。**既存節は削除・書き換えしない。

### A. 正式commit（いずれも現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| `87b7cc0` | ジャグラー自動抽出条件を対象ページ×店舗限定で扱う基盤（この時点は +1,000枚以上の**固定・変更不可**＝中間実装。固定方式は 24417c8 で廃止） |
| **`24417c8`** | ジャグラーシリーズ優秀台の自動抽出閾値を「固定」から「記憶・復元」へ変更。auto_slump2 のジャグラーラジオのUIキーを保存キーの名前空間へ統一。かぶぱ文章の保存を他フィールドを消さないマージに変更 |
| **`a8bb82f`** | その他の優秀台ピックアップの自動抽出閾値を記憶・復元へ変更。auto_slump2 の「その他」ラジオのUIキーと保存キーの不一致を修正 |

**どのcommitへも reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 対象

- 新宿歌舞伎町の **`auto_slump2`（📈スランプ付き結果ポスト）** と **`auto_article`（記事用）** の2ページだけ。
- 対象入力は②「全台系・高配分」内の、📝記入部分のみモードの自動抽出条件ラジオ2種類：
  - **ジャグラーシリーズ優秀台**（選択肢 `なし / 優秀台 / +1,000枚以上 / +2,000枚以上`）
  - **その他の優秀台ピックアップ**（選択肢 `なし / +1,000枚以上 / +2,000枚以上 / +3,000枚以上`）
- その他の優秀台は**台番テキストが空欄で自動抽出を使う場合**の条件。
- **対象外**：かぶぱ（新宿歌舞伎町 `auto_slump`）、通常結果ポスト、ローテ用、他店舗、他ページ（いずれも従来の日付単位保存のまま）。

### C. 正式仕様

- **両ラジオは変更可能。固定・disabled にしない**（`87b7cc0` の固定方式へ戻さない）。
- **保存値がない初回の初期値は「+1,000枚以上」。**
- ユーザーが +2,000枚以上などへ変更したら、その選択値を記憶して復元する。
- **日付変更・データ再取得・ページ再読込・Cloud の Reboot 後も、最後に選んだ値を復元する。**
- **`auto_slump2` と記事用は独立して記憶**する。
- **ジャグラー条件とその他優秀台条件も独立して記憶**し、互いの保存で消去・上書きしない。
- **台番テキストを入力した場合の既存の手入力挙動は変えない。**
- **⑦📝、📝からの🔄、📝の⑧本番では、画面に表示している選択値と同じ条件を使う**
  （ラジオ描画の直後に `jug_extra_auto` / `sonota_extra_auto` / `art_jug_extra_auto` / `art_sonota_extra_auto` を読み、各経路はその変数を使う）。
- **🔍フルプレビューでの統合ジャグラー画像は既存パイプラインの条件で決まるため、この記憶仕様の対象外。**

### D. 保存・キーの扱い

- 日付をまたぐ記憶先は**既存の `article_shared_inputs.json`**（店舗単位・Cloud↔GitHub 同期済み）。**新しい保存ファイルを作らない。**
- フィールドは**ページ別・種類別の4つ**（`article_shared_inputs.json` の `新宿歌舞伎町` 配下）：

  | page | ジャグラー | その他の優秀台 |
  |---|---|---|
  | `auto_slump2` | `jug_extra_auto_slump2` | `sonota_extra_auto_slump2` |
  | `auto_article` | `jug_extra_auto_article` | `sonota_extra_auto_article` |

- 定数・関数：`_JUG_AUTO_MEM_FIELDS` / `_JUG_AUTO_MEM_STORES` / `_jug_auto_mem_field()`、
  `_SONOTA_AUTO_OPTS` / `_SONOTA_AUTO_MEM_FIELDS` / `_SONOTA_AUTO_MEM_STORES` / `_sonota_auto_mem_field()`、
  共用の `_jug_auto_mem_resolve(..., opts=None)` / `_save_jug_auto_mem(..., opts=None, label=...)`
  （**`opts` / `label` を省略したときはジャグラー用の既定動作**）。
- **表示値の優先順は「最後に選んだ記憶値 → その日付の保存値（`なし` 以外）→ +1,000枚以上」。**
  日付の保存値 `なし` は初期値として残っている既存保存値であり、記憶値がない場合の復元候補として使わない。
  （ユーザーがラジオで `なし` を選んだ場合は、それ自体が記憶値として保存・復元される。）
- 記憶値の書き込みはラジオ変更時（on_change）だけ。**値が変わらなければ書かない・pushしない。**
  保存は店舗内の他フィールド（かぶぱ文章・もう一方の条件）を消さないマージ。
  Cloud はかぶぱ文章と同じ SHA 確認付き push（競合時は保存せず最新を取り込む）。
- `auto_slump2` は、ジャグラー・その他優秀台とも**画面キーと日付保存キーを `新宿歌舞伎町(スランプ)`（`_kojin_ns(store)`）に統一**
  （`jug_extra_auto_新宿歌舞伎町(スランプ)` / `sonota_extra_auto_新宿歌舞伎町(スランプ)`）。
  **a8bb82f 以前は「その他」の画面キーが `sonota_extra_auto_新宿歌舞伎町` で保存キーと食い違い、
  選択値はセッション内にしか残らず再読込・Reboot で消えていた**（これが原因）。
- 記事用は日付スコープではない店舗単位の画面キー（`art_jug_extra_auto_mem_{store}` / `art_sonota_extra_auto_mem_{store}`）で描き、
  抽出側が読む logical key（`art_jug_extra_auto_{store}` / `art_sonota_extra_auto_{store}`）へ同じ値を入れる。
- **今回直したのはこの2ラジオだけ。対象外入力のキー不一致（例：auto_slump2 の「その他」タイトル・台番テキスト）は無断で直さない。**

### E. 変更しない対象

統合ジャグラー画像OFF時のその他優秀台への戻し（`fc74518` / `148cc95` / `b9ccc4b`）／
個別ジャグラー画像OFF時の再振り分け（`a5a799d`）／記事用②全台系との重複除外（`cec23c7`）／
パネルなし仕様・表・ピンクバー・スランプ・台番順・画像名・WordPress本文／他店舗・他ページの保存・復元。

### F. 検証・Cloud確認

- 9/29・9/30 の実データで、ジャグラー側の +1,000枚以上抽出を確認した。
- +2,000枚以上を選ぶと、条件未満の台が抽出されないことを確認した。
- a8bb82f の関数単位テスト 22件 PASS（一時フォルダに設定ファイルを複製・ゲート／初回+1,000／UIキー＝保存キー／
  日付変更・再起動相当での復元／+1,000へ戻した記憶／2ページ・2種類の独立／かぶぱ文章の不変）。
- **Cloud で、両ページとも +2,000枚以上を選び、日付変更・再読込・Reboot 後に復元されることを確認済み。**
- **+1,000枚以上へ戻した場合も記憶され、2ページ・2種類のラジオ設定がそれぞれ独立することを Cloud で確認済み。**
- 台番テキストを入れた場合の手入力挙動が維持されること。
- 実装検証は Pision 確定データGETのみで、**WordPress 通信・画像生成はしていない。**

### G. 禁止事項・保全

1. 両ラジオを固定・disabled に戻さない（`87b7cc0` の固定方式を復活させない）
2. 初回初期値を +1,000枚以上以外にしない／日付保存値 `なし` を記憶値なし時の復元候補に使わない
3. 新しい保存ファイルを作らない（`article_shared_inputs.json` を使う）
4. 4つの記憶フィールドを統合・共用しない（ページ間・種類間で上書きさせない）
5. `_jug_auto_mem_resolve` / `_save_jug_auto_mem` の `opts` / `label` 既定（ジャグラー用）を変えない
6. 保存をマージ以外（全置換）に戻さない／値不変時に書き込み・pushしない仕様を外さない／Cloud の SHA 確認を外さない
7. auto_slump2 の2ラジオの画面キーを `新宿歌舞伎町` 単独へ戻さない
8. 対象外入力のキー不一致を無断で直さない
9. かぶぱ・通常結果ポスト・ローテ用・他店舗・他ページへ広げない
10. 台番テキスト入力時の手入力挙動・⑦📝／🔄／⑧が読む変数を変えない
11. E の変更しない対象を本仕様を理由に変えない
12. `wrt_machines.json`・`auto_page_inputs.json`・`article_page_inputs.json`・`article_shared_inputs.json` の既存差分、
    未追跡4件、stash 4件、アプリ自動commit履歴を保全する。
    `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
13. `87b7cc0` / `24417c8` / `a8bb82f` へ reset・revert しない

<!-- VERBATIM-END id=S24356 -->

<!-- VERBATIM-BEGIN id=S25360 src=CLAUDE.md@fde5030 lines=25360-25451 sha256=32d81b7e7635affa4cf03fcdbcb13d1e5d51d0a25018514601b06fa14ae065a1 -->
## 【正式仕様】マイジャグVIをジャグラーシリーズとして扱う（2026-10-08・`8d97023` / `ec6a3cf`）

**正式仕様。巻き戻し禁止。**対象は**ジャグラーシリーズの一覧を参照する全ページ**
（結果ポスト用・スランプ付き結果・記事用ほか）。
**Cloud 実画面で確認済み（2026-10-08）。**既存節は削除・圧縮・統合・並べ替え・書き換えしない。

### A. 正式commit（いずれも現HEADの祖先であることを確認済み）

| commit | 内容 |
|---|---|
| **`8d970238efdfc653177d7c5abc8c5ca9df9a7be9`** | `fix: マイジャグVIを「その他のジャグラーの優秀台」の対象に追加`（`streamlit_app.py` のみ・+1行） |
| **`ec6a3cf2a0ac7de1bd12eb8149483b85787bc8f3`** | `fix: 新小岩⑤B3（ジャグラー枠）にマイジャグVIを追加`（`store_settings/新小岩.json` のみ・1行） |

**どのcommitへも reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 不具合（記録）

マイジャグVIが `DEFAULT_STORE_CONFIG["juggler_jobs"]` に無く、普通の機種として扱われていたため、
新宿歌舞伎町の記事用などで**「その他のジャグラーの優秀台」ではなく「その他の優秀台ピックアップ」に入っていた。**

### C. 正式仕様

```python
DEFAULT_STORE_CONFIG["juggler_jobs"] = [
    ("マイジャグV",         140, 1000),
    ("マイジャグVI",        140, 1000),   # マイジャグVと同じ判定条件   ← 追加
    ...
]
```

- **マイジャグVIの優秀台判定はマイジャグVと同一**（合算確率 1/140 以下かつ差枚±0以上、または差枚 +1,000枚以上。
  2,000G以上はジャグラー共通の `juggler_g_min`）。
- **マイジャグVIは「その他のジャグラーの優秀台」（`ジャグラーシリーズ優秀台.jpg`）側として扱い、
  「その他の優秀台ピックアップ」から除外する。**
- `cfg["juggler_series"]` は `juggler_jobs` から導出されるため、この共通一覧を参照する処理すべてに効く：
  統合ジャグラー画像（`run_step2_juggler`）、その他の優秀台（`run_step3_other` はジャグラーを除外）、
  📝記入部分のみの自動抽出（`_manual_juggler_auto_extract` / `_jug_sonota_exc_series`）、
  末尾・ジャグラー末尾、高配分判定、結果テキスト。**店舗・ページ別のリストは追加していない。**
- 実データ表記は Pision の「マイジャグラーVI」→ 既存の機種名変換で **「マイジャグVI」** の1種類のみ
  （10/7・8店舗で確認）。**「マイジャグ6」などの名称ゆれ分岐は作らない。**

### D. 高配分画像の出方（正式仕様として承認済み）

マイジャグVと同じ判定になったため、マイジャグVIの高配分画像の出方が変わる。**これは正式仕様**。

| 店舗（2026/10/7） | 修正前 | 修正後 |
|---|---|---|
| 新宿歌舞伎町 | `マイジャグVI_高配分.jpg`（4/8台） | 個別の高配分画像は作らず、1001・1002・1008番台を統合ジャグラー画像へ |
| 上野本館 | `マイジャグVI_高配分.jpg`（2/4台） | 生成しない（+900枚の2台が 1/144〜1/146 で 1/140 を満たさない） |
| 渋谷新館 | 3台掲載 | 2台掲載（2225番台 +100枚・1/145.8 が外れる） |

### E. 新小岩スランプ付き：⑤B3へマイジャグVIを追加（`ec6a3cf`）

- 新小岩のスランプ付きは、⑤オススメ機種のジャグラー枠 **B3 が正式な掲載先**で、通常のジャグラー統合画像を作らない（`1301431`）。
- `8d97023` だけでは、B3 に無いマイジャグVIの台（10/7 の70番台 +2,000枚）が**どの画像にも載らず、
  結果テキストにだけ載る**食い違いになったため、`store_settings/新小岩.json` の
  **`recommended_machines_3` の空いていた9枠目へ「マイジャグVI」を追加**した。
- **B3 の既存8機種・順序・タイトル・抽出条件、他ブロック、他店舗の⑤設定は変更していない。**
- 結果（10/7）：B3 の掲載台は修正前の37台＋70番台だけ（既存機種は不変）／その他の優秀台からは70番台だけが外れる／
  ⑤結果テキストの B3 の最後に「🤡マイジャグVI【70番台】+2,000枚」が加わる。

### F. 今回変更していないもの（別リスト）

- **`convert_narabi_pil.py` の `THRESHOLDS`**（並び画像を自動検出するときの優秀台判定・独自の閾値）
- **渋谷新館ローテの `_T3_JUGGLER_MACHINES`**（月間表③の選択肢）
- **新小岩B3以外の⑤オススメ機種の登録内容**（上野本館・稲毛・渋谷新館ほか。ユーザー設定値）

**必要になった場合は別案件として調査・承認のうえ対応する。**

### G. 検証・Cloud確認

- 8502複製環境で、10/7確定データ8店舗 × 結果ポスト用・スランプ付き・記事用・新宿歌舞伎町記事用の**28通り**を
  修正前と比較し、チェックはすべて合格（不合格0）。マイジャグVI以外の掲載台・全台系・高配分は不変、
  マイジャグVIが無い稲毛・秋葉原は全画像が修正前と一致。
- **Cloud 実画面（2026-10-08）**：
  - 新宿歌舞伎町・記事用：1001・1002・1008番台が統合ジャグラー画像に入り（マイジャグVIパネル付き）、
    その他の優秀台に1001〜1008番台なし、`マイジャグVI_高配分.jpg` は出ない
  - 新小岩・スランプ付き：⑤B3画像に70番台が入り、その他の優秀台に入らない（8502と同じ画像ハッシュ）
  - 上野新館・結果ポスト用：2020番台が統合ジャグラー画像に入り、その他の優秀台に入らない
- 検証・確認中の WordPress 通信・⑧本番は行っていない（Pision 確定データGETのみ）。

### H. 禁止事項

1. **`juggler_jobs` からマイジャグVIを外さない／判定値（140・1000）をマイジャグVと別にしない**
2. **マイジャグVIを「その他の優秀台」側へ戻さない**
3. **名称ゆれ分岐・店舗別・ページ別のジャグラーリストを新設しない**
4. **新小岩B3からマイジャグVIを外さない／B3の既存8機種・順序を変えない**
5. **F の別リストを本仕様を理由に変更しない**
6. `wrt_machines.json` の既存差分、未追跡ファイル、stash 4件、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止
7. `8d97023` / `ec6a3cf` へ reset・revert しない

<!-- VERBATIM-END id=S25360 -->

<!-- VERBATIM-BEGIN id=S26047 src=CLAUDE.md@fde5030 lines=26047-26147 sha256=6f1b8fcf1bb782abbefccb5ccb028bb6d09709bd7865c61b90db464ba75180d5 -->
## 【正式仕様】新宿歌舞伎町・上野本館・秋葉原 スランプ付き結果ポスト：「🌐 サイトから取得」を追加（2026-10-13・`04a8daa`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】【上野本館】【秋葉原】のスランプ付き結果ポスト用の「📈 日付からデータを自動取得」（確定データ）だけ**。
**Cloud 実機で確認済み（2026-10-13・ユーザー承認）。**既存節は削除・圧縮・統合・書き換えしない。

### A. 正式commit

| 項目 | 内容 |
|---|---|
| 正式commit | **`04a8daa802addf941c0c1a1089c0c3cf6fb5c0d0`**（`feat: 3店舗のスランプ結果にサイト取得を追加`・`streamlit_app.py` のみ・+7 / −3） |
| 変更箇所 | 定数 `_SG_FETCH_STORES` / `_SG_HALL_IDS` と、`show_auto_page()` のボタン表示条件1行だけ。新規・削除関数0 |

**`04a8daa` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

★「稲毛 … 2系統データ取得（`a51e362`）」節・「新小岩 … slotterguild 確定データ取得対応（`a1d47e9`）」節に書かれた
`_SG_FETCH_STORES` / `_SG_HALL_IDS` の値は**それぞれの commit 時点の記録として正しく、削除・書き換えしない**。
**現在の正式な集合は本節の6店舗（＋「その他」配下は設定ファイル）**である。
新小岩節の「新宿歌舞伎町は SG points 採用不可・上野本館／秋葉原は保留」という判断も**当時の正式記録**であり、
**本節が後発仕様として上書き**する（理由は下記 E の運用前提）。

### B. 店舗別の正式仕様

| 店舗 | 表示するページ | 表示しないページ |
|---|---|---|
| **新宿歌舞伎町** | **スランプ付き結果ポスト用（`page=auto_slump2`）**：🔄 Pisionから取得 ／ 🌐 サイトから取得 | **かぶぱ（`page=auto_slump`）・記事用・ローテ用** |
| **上野本館** | **スランプ付き結果ポスト用（`page=auto_slump`）**：Pision ／ サイト | **非表示中の結果ポスト用（`page=auto`）・ローテ用** |
| **秋葉原** | **スランプ付き結果ポスト用（`page=auto_slump`）**：Pision ／ サイト | **記事用** |

- **取得後は既存の表・スランプ・結果テキスト処理へそのまま流す**（Pision 取得と同じ session_state・同じ下流処理）。
- **秋葉原固有のタイトル型スランプ画像（`_build_slump_title_img()`）等は従来どおり。**
- **Pision 取得は従来どおり残す**（ボタン key `auto_tb_refetch_{store}` も不変）。
- 速報モードは変更しない（slotterguild は確定データのみ）。

### C. 実装要点

```python
_SG_FETCH_STORES = frozenset({"稲毛", "上野新館", "新小岩",
                              "新宿歌舞伎町", "上野本館", "秋葉原"})
# hall_id は slotterguild の店舗一覧（halls.php）で確認した値。
_SG_HALL_IDS = {"稲毛": 566, "上野新館": 570, "新小岩": 573,
                "新宿歌舞伎町": 572, "上野本館": 571, "秋葉原": 568}
...
            elif with_slump and _sg_enabled(store) and not _is_kabupa_pg:
                # ★新宿歌舞伎町のかぶぱ（auto_slump）には出さない（auto_slump2 だけ）。
```

- **ボタン表示を実際に決めているのは `_sg_enabled(store)`（＝`_SG_HALL_IDS` に店舗IDがあるか）と `with_slump`。**
  `_SG_FETCH_STORES` は現在どこからも参照されていないが、既存方針に合わせて3店舗を追加した。
- **★`not _is_kabupa_pg` は必須。**新宿歌舞伎町のかぶぱ（`auto_slump`）も `with_slump=True` のため、
  店舗IDを足すだけではかぶぱにもボタンが出てしまう。
- **新しい取得ロジック・関数は作らない。**既存の `_sg_fetch_excel()` / `_sg_fetch_items()` をそのまま流用する。
- slotterguild の店舗ID（572 / 571 / 568）と Pision の hall_id は**別体系**。混同しない。

### D. 8502 での確認（2026-10-13）

- 3店舗とも **閉店後の本データがそろった 10/11** で、Pision 取得と比較：
  **台番・機種名（変換後）・ゲーム数・BB・RB・AT・差枚が全セル一致、総差枚も一致**
  （新宿歌舞伎町 749台 −65,900／上野本館 375台 −12,800／秋葉原 522台 +144,100）。
- 処理後の**画像（ファイル名・バイト列）と結果テキストが、サイト取得版と Pision 版で3店舗とも完全一致**。
- **スランプグラフ終点は全台一致。**点の取り方が違う台があるため画像の画素差は平均0.16〜0.92%（最大4.3%）だが、
  形・終点・表示差枚は同じ（目視でも確認）。
- 既存のサイト取得店舗（新小岩・稲毛・上野新館・プレサス飯田橋）と、結果ポスト用・記事用・ローテ用に非回帰なし。

### E. 運用前提（取得機能は制限しない）

- **slotterguild は営業途中に収集すると途中データが残ることがある**（回転数が Pision 以下になる）。
- **結果用途では、閉店後に本データを再収集済みの slotterguild データを使う。**
- 上野新館 2026/10/10 では、閉店後の再収集で **Pision と 377/377台・全項目一致**したことを確認済み
  （再収集前は310台で回転数が少なく、総差枚は Pision +131,400 に対し slotterguild +13,800 だった）。
- **今回は Pision との自動照合機能は入れていない。**
- slotterguild に未収集の日（例：新宿歌舞伎町 10/12）に押すと「ページ構造が変わった可能性」と表示されるのは**既存挙動**で、今回は変更していない。

### F. Cloud 確認（2026-10-13）

- **Reboot 後に `04a8daa` が反映されたことを確認**（Reboot 前は旧コードのまま「🔄 取得」だけだった）。health は 200 `ok`。
- **新宿歌舞伎町 10/11：749台取得・プレビュー28枚・エラー0**
- **上野本館 10/12：375台取得・プレビュー14枚・エラー0**
- **秋葉原 10/12：522台取得・プレビュー23枚・エラー0**（タイトル型スランプ画像も正常）
- 新宿歌舞伎町のかぶぱ・記事用・ローテ用、上野本館の非表示中の結果ポスト用・ローテ用、秋葉原の記事用には**サイト取得が出ない**。
- **新小岩・稲毛・上野新館・プレサス飯田橋の既存サイト取得表示に非回帰なし**（これらの店舗で取得ボタンを押す確認は Cloud では行っていない）。
- **PC では2ボタン横並び（各812×40px）、390px相当では縦並び（各344×40px）**。横スクロール・文字切れなし。

### G. ★結果テキストの確認範囲（誤記しないこと）

- **結果テキストは Cloud では確認していない。**結果テキストは⑧本番の実行時にしか出ず、⑧は本番処理になるため Cloud では押していない。
- **8502 では3店舗とも、サイト取得版と Pision 版の結果テキストが完全一致することを確認済み。**
- **「Cloud で結果テキスト確認済み」と書かない。**

### H. 禁止事項

1. **新宿歌舞伎町のかぶぱ（`auto_slump`）へサイト取得を出さない**（`not _is_kabupa_pg` を外さない）
2. **記事用・ローテ用・通常の結果ポスト用へ出さない**（`with_slump` の条件を外さない）
3. **店舗IDを推測で追加しない**（slotterguild の店舗一覧で確認した値だけ）／Pision の hall_id と混同しない
4. **新しい取得ロジック・別の保存先を作らない**（既存の取得処理と session_state を流用する）
5. **Pision 取得ボタンを消さない／key を変えない**
6. **秋葉原のタイトル型スランプ・各店舗の既存処理を本仕様を理由に変えない**
7. **途中データの日を結果用途に使わない**（閉店後の本データを再収集してから使う）
8. **結果テキストを Cloud で確認済みと記録しない**
9. `wrt_machines.json` の既存差分、未追跡ファイル、stash、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / 通常merge / revert / force push は禁止

<!-- VERBATIM-END id=S26047 -->

<!-- VERBATIM-BEGIN id=S26220 src=CLAUDE.md@fde5030 lines=26220-26308 sha256=1a55d9070330aae7df6f2c08faeb1680138f6f57feaa9823bacc74d2070d13db -->
## 【正式仕様】新宿歌舞伎町 スランプ付き結果ポスト用：初期チェック状態をCloudとローカルで一致（2026-10-13・`3e8a051`）

**正式仕様。巻き戻し禁止。**対象は**【新宿歌舞伎町】スランプ付き結果ポスト用（`page=auto_slump2`）の初期チェック状態だけ**。
**Cloud 実機で確認済み（2026-10-13・ユーザー承認）。**既存節は削除・圧縮・統合・書き換えしない。

### A. 正式commit

| 項目 | 内容 |
|---|---|
| 正式commit | **`3e8a05110bb1c9c679eda39edf39cb96a765f4cd`**（`fix: 新宿歌舞伎町の初期チェック状態を修正`） |
| 変更 | **保存データ2行だけ**（`article_shared_inputs.json` 1行・`store_settings/新宿歌舞伎町.json` 1行）。**コード変更なし** |

**`3e8a051` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 正しい初期状態

| 項目 | 正しい初期状態 |
|---|---|
| **⑤ オススメ機種ピックアップ** | **OFF** |
| **② 個別画像「下記の条件で『ジャグラーシリーズ優秀台』を自動抽出」** | **`+1,000枚以上`** |

### C. 原因（コード不具合ではない）

Cloud とローカルで参照している**保存ファイルの内容が違っていた**。

| 項目 | ファイル | Cloud／GitHub HEAD版 | ローカル作業ツリー版 |
|---|---|---|---|
| ⑤ | `store_settings/新宿歌舞伎町.json` の `rec_enabled` | **true** | **false** |
| ② | `article_shared_inputs.json` の `jug_extra_auto_slump2` | **"なし"** | **"+1,000枚以上"** |

- `rec_enabled: true` は 10/12 23:28 のローカル自動commit `6e585e5` で GitHub に入り、ローカルは false に戻したまま push されていなかった。
- `"なし"` は 10/11 03:02 の Cloud 自動commit `87f25dc` で GitHub に入り、ローカルは +1,000枚以上 に戻したまま push されていなかった。
- **`auto_page_inputs.json` はこの2項目に関係しない。**

### D. 値の決まり方

**⑤**
- `_init_recommended_settings()` が `store_settings/新宿歌舞伎町.json` の `rec_enabled` を `rec_enabled_{店舗}` の初期値として読む。
- **保存値がある場合、コード上のデフォルト False より保存値が優先される。**
- **データ取得後の処理で⑤を書き換えることはない**（seed は session_state にキーが無いときだけ）。
- `store_settings` には Cloud↔GitHub の同期経路が無いため、Cloud は**最後の Reboot 時点の HEAD 版**を読む。

**②**
- **`_jug_auto_mem_resolve()` が描画のたびに表示値を決める**。
- 優先順は **`article_shared_inputs.json` の記憶値 → 日付保存値（「なし」以外）→ `+1,000枚以上`**。
- **記憶値が `"なし"` の場合も有効値として採用されるため、コード初期値 `+1,000枚以上` には戻らない。**
- `article_shared_inputs.json` は `_GH_SYNC_FILES` の対象で、Cloud はセッション開始時に GitHub の最新を取り込む。

### E. 正式修正（GitHub上の保存データをローカルの正しい状態へ合わせた）

変更は2行だけ：

1. `article_shared_inputs.json`：`jug_extra_auto_slump2` を `"なし"` → **`"+1,000枚以上"`**
2. `store_settings/新宿歌舞伎町.json`：`rec_enabled` を `true` → **`false`**

**★重要**
- ローカル作業ツリーの `store_settings/新宿歌舞伎町.json` には、**東京喰種・マギレコ・モンキーターンV 等の10/12テスト用⑤設定が未コミットで存在する**。
- **そのファイルを丸ごと commit せず、HEAD 版を基準に `rec_enabled` だけを false へ変えた内容を Git へ登録した**
  （作業ツリーのファイルには触れていない）。
- **テスト用⑤設定は正式commitへ含めていない。**

### F. Cloud確認（2026-10-13）

Reboot 後、新宿歌舞伎町・スランプ付き結果ポスト用で **10/12 の Pision 確定データ 749台**を取得。

- **⑤ オススメ機種ピックアップ：OFF**
- ②は「個別画像も生成する」を ON にした際に表示され、**`+1,000枚以上` が選択**されていることを確認。確認後「個別画像も生成する」は OFF へ戻した。
- **再読み込み・新しいセッションでも⑤は OFF。**
- ②は **GitHub 上の `article_shared_inputs.json` の `+1,000枚以上` を毎回読む**ことを確認。

### G. 他店舗への影響

今回の変更は新宿歌舞伎町専用。Cloud で以下も確認し、非回帰なし：

| 店舗 | Cloud の⑤ | 設定（HEAD版） |
|---|---|---|
| 新小岩 | ON | true |
| 上野本館 | ON | true |
| 稲毛 | OFF | false |

### H. 禁止事項・保全

1. ⑤・②の初期状態をコードの変更で合わせようとしない（原因は保存データ）
2. `store_settings/新宿歌舞伎町.json` を丸ごと commit しない／10/12テスト用⑤設定を commit しない
3. Cloud の画面で⑤を切り替えて直そうとしない（`store_settings` はコンテナ内にしか残らず Reboot で消える）
4. `_init_recommended_settings()` / `_jug_auto_mem_resolve()` の優先順を本件を理由に変えない
5. `auto_page_inputs.json`・`store_settings/新宿歌舞伎町.json`（テスト用⑤設定）・`wrt_machines.json` の既存差分、未追跡4件、stash 5件、
   アプリ自動commit履歴を保全する。`git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / merge / revert / force push は禁止

<!-- VERBATIM-END id=S26220 -->


---

## 【参照】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用は新宿歌舞伎町 auto_slump2 と同じ（2026-10-29・`1526531`）

モグ玄・新宿歌舞伎町の 📈スランプ付き結果ポスト用は、既存新宿歌舞伎町 auto_slump2 の仕様（本ファイルの新宿歌舞伎町各節・slotterguild hall_id 572 を含む）をそのまま使う。
データ取得元だけ `_data_store()` で新宿歌舞伎町を共有し、保存・出力は店舗名で分離。スランプ固有デザインは新宿歌舞伎町仕様のまま（後発指示で変更予定）。
正式仕様の本文は [top_ui_tools.md](top_ui_tools.md) の「トップに「モグ玄・新宿歌舞伎町」を追加」節。

---

## 【参照】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用のスランプは横長カード・1行7台（2026-10-30・`e234268`）

主記録は `result_images.md` の「【正式仕様】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用：横長スランプカード・1行7台・+5,000/-2,000固定レンジ（2026-10-30・`e234268`）」。`page == "auto_slump2"` かつ `store == "モグ玄・新宿歌舞伎町"` のときだけ適用する。新宿歌舞伎町の auto_slump2 は従来の淡紫カードのまま。

---

## 【参照】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用は3列台番一覧＋スランプ一覧へ分離（2026-10-30・`799dc89`／先行 `075746a`）

主記録は `result_images.md` の「【正式仕様】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用：3列台番一覧＋優秀機種/高配分スランプ一覧へ分離（2026-10-30・`799dc89`／先行 `075746a`）」。`page == "auto_slump2"` かつ `store == "モグ玄・新宿歌舞伎町"` の通常経路だけに適用する。統合するカテゴリ（優秀機種・高配分・並び・末尾・⑤・単品）の個別同居画像は出さず、ジャグラー等は従来どおり出す。新宿歌舞伎町本体とモグ玄・新大久保は変更しない。

---

## 【参照】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用は紫系表画像を全廃し台番一覧＋スランプ一覧の2枚へ（2026-10-30・`be71e60`／先行 `3d4ad38`）

主記録は `result_images.md` の「【正式仕様】モグ玄・新宿歌舞伎町 スランプ付き結果ポスト用：紫系表画像を全廃し、通常／manualとも台番一覧＋スランプ一覧へ統合（2026-10-30・`be71e60`／先行 `3d4ad38`）」。`page == "auto_slump2"` かつ `store == "モグ玄・新宿歌舞伎町"` のときだけ適用し、🔍・🔄・⑧・📝・⑧📝のすべてで紫系の表画像を作らない。ジャグラーも台番一覧＋スランプ一覧へ統合し、🎯・画像チェックは出さない。結果テキストの内容は変えない。新宿歌舞伎町本体とモグ玄・新大久保は変更しない。

---

## 【参照】モグ玄・新宿歌舞伎町 台番一覧の列仕掛けは1入力＝1かたまりで分断しない（2026-10-30・`5fe0082`）

主記録は `result_images.md` の「【正式仕様・後発訂正】モグ玄・新宿歌舞伎町 台番一覧：列仕掛けは1入力単位のまとまりを維持し、列境界で分断しない（2026-10-30・`5fe0082`）」。be71e60 の記録のうち「列は1台ずつ配置」の部分だけを訂正する。ブロック順と追加ブロック（②範囲・個別ピック等＝1台ずつ）は変わらない。

---

## 【参照】モグ玄・新宿歌舞伎町 台番一覧／スランプ一覧の表示整理（2026-10-30・`d55976d`）

主記録は `result_images.md` の「【正式仕様】モグ玄・新宿歌舞伎町 台番一覧／スランプ一覧：タイトル・分類帯・カード文字・グラフ領域・注記の表示整理（2026-10-30・`d55976d`）」。表示とレイアウトだけの変更で、判定・対象台・集計・結果テキスト・cleanup・ファイル名は変わらない。

---

## 【参照】モグ玄・新大久保／モグ玄・新宿歌舞伎町 台番一覧の文字サイズと機種名～台番の間隔（2026-10-31・`b880b52`／`6e18032`、先行 `3869e29`）

主記録は `result_images.md` の「【正式仕様】モグ玄・新大久保／モグ玄・新宿歌舞伎町 台番一覧：タイトル32px・見出し18px・機種名～台番の間隔58へ調整（2026-10-31・`b880b52`／`6e18032`、先行 `3869e29`）」。台番一覧の見た目だけの変更で、判定・対象台・ブロック順・結果テキスト・cleanup・ファイル名・スランプ一覧は変わらない。
