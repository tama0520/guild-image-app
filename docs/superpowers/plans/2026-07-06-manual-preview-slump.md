# スランプ付き「記入部分のみプレビュー＋実行」 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** スランプ付き結果ポスト用ページ（`show_auto_page(with_slump=True)`）に「📝 記入部分のみプレビュー作成」機能を追加し、記入部分（②③④⑤）の画像にもスランプグラフを合成してプレビュー・⑧実行できるようにする。

**Architecture:** 既存のフルスランププレビューの合成ロジックを新ヘルパー `_composite_slump_onto_images()` に切り出し（フルプレビューの既存合成ブロックは触らない）、記入部分プレビュー生成と記入部分⑧実行の両方から呼ぶ。📝ボタンを `with_slump` 側でも表示し、`_is_manual_mode` の `not with_slump` ゲートを外す。

**Tech Stack:** Python 3.14, Streamlit, PIL, pandas。テストフレームワーク無し。検証は AST 構文チェックと Streamlit 起動（CLAUDE.md 準拠）。

## Global Constraints

- 編集後は必ず構文チェック: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
- Windows 環境。コマンドは PowerShell ツールで実行（Bash 不可）。
- 対象はスランプ付き全店舗（店舗限定なし）。記事用ページ（`show_auto_article_page` / `art_`）は対象外。
- フルスランププレビューの既存合成ブロック（`streamlit_app.py:6715-6958` 付近）は変更しない。
- pision データ取得不可時は警告のうえ**表だけ（合成なし）で継続**する。
- 既存パターンに合わせる。DRY・YAGNI・頻繁なコミット。

---

### Task 1: スランプ合成ヘルパー `_composite_slump_onto_images` を追加

**Files:**
- Modify: `streamlit_app.py`（`draw_slump_graph` 定義の直前、`14629` 付近にモジュール関数として追加）

**Interfaces:**
- Produces:
  `_composite_slump_onto_images(img_list, ban_map, store, ban2mac=None, ban2diff=None, date_str="", api_key=None) -> list[tuple[str, "Image.Image"]]`
  - `img_list`: `[(filename, PIL.Image), ...]`（連番プレフィックス無しのファイル名）
  - `ban_map`: `dict[str, list[int]]`（ファイル名 → 台番リスト）
  - `ban2mac`: `dict[str, str] | None`（台番文字列 → 機種名。machine_name 表示用）
  - `ban2diff`: `dict[str, int] | None`（台番文字列 → 差枚。全台系マイナス台の show_diff=False 判定用）
  - 戻り値: 合成済み `[(filename, Image), ...]`。16枚以上の非秋葉原は `_side.jpg` を追加。取得不可時は `img_list` をそのまま返す。

- [ ] **Step 1: ヘルパー関数を追加**

`draw_slump_graph(` 定義（`14629` 付近）の直前に次を挿入する。既存フルプレビュー（`6876-6958`）と同じロジックを関数化したもの:

```python
def _composite_slump_onto_images(
    img_list: list[tuple[str, "Image.Image"]],
    ban_map: dict[str, list[int]],
    store: str,
    ban2mac: dict[str, str] | None = None,
    ban2diff: dict[str, int] | None = None,
    date_str: str = "",
    api_key: str | None = None,
) -> list[tuple[str, "Image.Image"]]:
    """記入部分等の画像リストにスランプグラフを合成して返す。
    pision データは _slump_by_uid_{store} キャッシュ→速報キャッシュ→fetch の順で取得。
    取得不可・テンプレ無しなら img_list をそのまま返す（表のみ）。"""
    ban2mac  = ban2mac or {}
    ban2diff = ban2diff or {}
    # pision uid 辞書を取得（キャッシュ優先）
    _by_uid = st.session_state.get(f"_slump_by_uid_{store}")
    if not _by_uid:
        try:
            _rt_cached = st.session_state.get(f"_auto_tb_rt_items_{store}")
            _rt_date   = st.session_state.get(f"_auto_tb_rt_items_date_{store}", "")
            if _rt_cached and _rt_date == date_str:
                _items = _rt_cached
            else:
                _key = api_key or _get_pision_api_key()
                if not _key:
                    return img_list
                _halls = fetch_pision_halls(_key)
                _hall_id = None
                for _h in _halls:
                    _hn = _h.get("name") or _h.get("displayName") or ""
                    if store in _hn and "エスパス" in _hn:
                        _hall_id = str(_h.get("id") or _h.get("hallId") or "")
                        break
                _items = fetch_pision_results(_key, _hall_id, date_str) if _hall_id else None
                if _items:
                    _slump_apply_names(_items)
            if not _items:
                return img_list
            _by_uid = {str(_it.get("unitId", "")): _it for _it in _items}
            st.session_state[f"_slump_by_uid_{store}"] = _by_uid
        except Exception:
            return img_list
    _tmpl = find_slump_template()
    _bbb  = _find_slump_bg()
    if _tmpl is None:
        return img_list
    _sonota_names = ("ジャグラーシリーズ優秀台.jpg", "その他の優秀台ピックアップ.jpg",
                     "その他の優秀台+1,000枚以上.jpg", "その他の優秀台+2,000枚以上.jpg",
                     "その他の優秀台+3,000枚以上.jpg")
    _merged: list[tuple[str, "Image.Image"]] = []
    for (_fn, _img) in img_list:
        _bare = re.sub(r"^\d{2}_", "", _fn)
        _bans = ban_map.get(_bare, [])
        if not _bans:
            if store != "秋葉原":
                _merged.append((_fn, _img))
            continue
        _show_mn = (_bare in _sonota_names or _bare.startswith("末尾") or _bare.startswith("バラエティ"))
        _is_zentai = (not _bare.endswith("_高配分.jpg") and _bare not in _sonota_names)
        _g_imgs: list["Image.Image"] = []
        for _b in _bans:
            _it = _by_uid.get(str(_b))
            if _it is None or not _it.get("points"):
                continue
            _dn = (_it.get("_convertedName") or _it.get("displayName") or ban2mac.get(str(_b), str(_b)))
            _sd = not (_is_zentai and ban2diff.get(str(_b), 0) < 0)
            try:
                _g_imgs.append(draw_slump_graph(
                    _tmpl, str(_b), _dn, _it["points"], diff=_it.get("diff"),
                    machine_name=_dn if _show_mn else None, show_diff=_sd,
                ))
            except Exception:
                pass
        if store == "秋葉原":
            _title = os.path.splitext(_bare)[0]
            _slp = _build_slump_title_img(_title, _g_imgs, _bbb)
            if _slp is not None:
                _merged.append((_fn, _slp))
        else:
            _merged.append((_fn, _attach_slump_to_table(_img, _g_imgs, _bbb)))
        if len(_g_imgs) >= 16 and store != "秋葉原":
            try:
                _merged.append((os.path.splitext(_fn)[0] + "_side.jpg",
                                _attach_slump_to_table_side(_img, _g_imgs, _bbb)))
            except Exception:
                pass
    return _merged
```

注: 参照する `_get_pision_api_key` / `fetch_pision_halls` / `fetch_pision_results` / `_slump_apply_names` / `find_slump_template` / `_find_slump_bg` / `draw_slump_graph` / `_attach_slump_to_table` / `_attach_slump_to_table_side` / `_build_slump_title_img` が実在することを Grep で確認してから書く。関数はこれらの定義より後（`14629` 直前）に置くので前方参照問題は無い。

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```
git add streamlit_app.py
git commit -m "feat: スランプ合成ヘルパー _composite_slump_onto_images を追加"
```

---

### Task 2: 📝ボタンを with_slump ページにも表示

**Files:**
- Modify: `streamlit_app.py:6250-6258`

**Interfaces:**
- Consumes: 既存 `_full_prev_btn` / `_manual_prev_btn`
- Produces: `with_slump` でも `_manual_prev_btn` が押下可能になる

- [ ] **Step 1: 分岐を変更**

`streamlit_app.py:6250-6258` を Read で確認し、次のように変更する。変更前:

```python
            if not with_slump:
                _mc1, _mc2 = st.columns(2)
                with _mc1:
                    _full_prev_btn = st.button("🔍 プレビュー生成", key="auto_preview_btn", use_container_width=True)
                with _mc2:
                    _manual_prev_btn = st.button("📝 記入部分のみプレビュー作成", key="manual_only_preview_btn", use_container_width=True)
            else:
                _full_prev_btn = st.button("🔍 プレビュー生成", key="auto_preview_btn")
                _manual_prev_btn = False
```

変更後:

```python
            _mc1, _mc2 = st.columns(2)
            with _mc1:
                _full_prev_btn = st.button("🔍 プレビュー生成", key="auto_preview_btn", use_container_width=True)
            with _mc2:
                _manual_prev_btn = st.button("📝 記入部分のみプレビュー作成", key="manual_only_preview_btn", use_container_width=True)
```

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 起動して目視確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`（スランプ付きページで「📝 記入部分のみプレビュー作成」ボタンが出ること）
Expected: 2ボタンが表示される。

- [ ] **Step 4: Commit**

```
git add streamlit_app.py
git commit -m "feat: 📝記入部分のみボタンをスランプ付きページにも表示"
```

---

### Task 3: 記入部分プレビュー生成に ban_map 収集＋スランプ合成を追加

**Files:**
- Modify: `streamlit_app.py:6984-7103`（`if _manual_prev_btn:` ブロック）

**Interfaces:**
- Consumes: `_composite_slump_onto_images`（Task 1）, `_df_m`, `_diff_m`, `with_slump`, `store`
- Produces: `with_slump` 時、`_aprev_key` に合成済み画像を格納

- [ ] **Step 1: ban_map 収集を追加**

`_manual_imgs: list[...] = []`（`6995` 付近）の直後に `_manual_ban_map: dict[str, list[int]] = {}` を追加する。そして各画像を `_manual_imgs.append(...)` している箇所の直後に、同じファイル名キーで台番リストを登録する。具体的に:

- ②全台（`7007`）append 直後:
```python
                                _manual_ban_map[f"{_make_safe_fn(_km)}.jpg"] = [int(b) for b in _mg["台番"].tolist()]
```
- ②優秀台（`7023`）append 直後:
```python
                                _manual_ban_map[f"{_make_safe_fn(_mtit)}.jpg"] = [int(b) for b in _mgp["台番"].tolist()]
```
- ②その他ピックアップ（`7032`）append 直後:
```python
                                        _manual_ban_map[f"{_make_safe_fn(_se_tit_m)}.jpg"] = [int(b) for b in _se_df_m["台番"].tolist()]
```
- ③並び（`7060`）append 直後:
```python
                                _manual_ban_map[f"{_make_safe_fn(_file_tit_m)}.jpg"] = [int(b) for b in _ngrp["台番"].tolist()]
```
- ④末尾（`7066-7072`）: `_gen_sue_imgs_on_fly` の返り値 `(fn, img)` に対応する台番を、末尾条件から `_df_m` で算出して登録する。各 `_item = (fn, img)` の append を次の形に変える（通常末尾）:
```python
                            for _item in _gen_sue_imgs_on_fly(_m_sue_tails, _m_sue_mode, is_juggler=False):
                                _manual_imgs.append(_item)
                                _fn_sue = _item[0]
                                _bare_sue = re.sub(r"^\d{2}_", "", _fn_sue)
                                _tail_digits = re.findall(r"[0-9]", _bare_sue)
                                # 末尾画像は _gen_sue_imgs_on_fly 側でファイル名にモード名を含むため、
                                # 台番は _m_sue_tails 全体から算出（複数末尾でも和集合で可）
                                _sue_bans_all: list[int] = []
                                for _t in _m_sue_tails:
                                    if _t == "ゾロ目":
                                        _sue_bans_all += [int(b) for b in _df_m["台番"]
                                                          if (s := str(int(b))) and len(s) >= 2 and s[-2] == s[-1]]
                                    elif _t.isdigit() and len(_t) in (1, 2):
                                        _sue_bans_all += [int(b) for b in _df_m["台番"]
                                                          if str(int(b))[-len(_t):] == _t]
                                _manual_ban_map[_bare_sue] = sorted(set(_sue_bans_all))
```
  ジャグラー末尾（`7068-7072`）も同様に `is_juggler=True` の append 直後に、ジャグラー系列（`get_store_config(store)["juggler_series"]`）に絞った台番を登録する:
```python
                            _jug_ser_m = set(get_store_config(store)["juggler_series"])
                            for _item in _gen_sue_imgs_on_fly(_m_jug_tails, _m_jug_mode, is_juggler=True):
                                _manual_imgs.append(_item)
                                _bare_jsue = re.sub(r"^\d{2}_", "", _item[0])
                                _jsue_bans: list[int] = []
                                for _t in _m_jug_tails:
                                    if _t == "ゾロ目":
                                        _cand = [int(b) for b in _df_m["台番"]
                                                 if (s := str(int(b))) and len(s) >= 2 and s[-2] == s[-1]]
                                    elif _t.isdigit() and len(_t) in (1, 2):
                                        _cand = [int(b) for b in _df_m["台番"] if str(int(b))[-len(_t):] == _t]
                                    else:
                                        _cand = []
                                    for _b in _cand:
                                        _row = _df_m[_df_m["台番"] == _b]
                                        if not _row.empty and str(_row.iloc[0]["機種名"]) in _jug_ser_m:
                                            _jsue_bans.append(_b)
                                _manual_ban_map[_bare_jsue] = sorted(set(_jsue_bans))
```
- ⑤オススメ（`7097`）append 直後: 掲載機種の台番を登録する。フルプレビューの `_rec_ban_map` 構築（`streamlit_app.py:6640-6713` 付近）を参照し、`_mbm` の各機種の台番（narabi 除外なし・`min_diff` 条件でのマスク）を集める:
```python
                                    _rec_bans_m: list[int] = []
                                    for _rvm in _mbm:
                                        _rg = _df_m[_df_m["機種名"] == _rvm].copy()
                                        if _rg.empty:
                                            continue
                                        _rd = _diff_m.loc[_rg.index]
                                        if _rvm in _mj_cfg.get("series", set()):
                                            _jc = next((c for c in ["ゲーム数_rounded", "ゲーム数"] if c in _rg.columns), None)
                                            if _jc:
                                                _jm = _rg[_jc] >= _mj_cfg.get("g_min", 2000)
                                                _rg = _rg[_jm]; _rd = _rd[_jm]
                                            _jt = _mj_cfg["jobs_map"].get(_rvm)
                                            if _jt is not None and "合算確率_num" in _rg.columns:
                                                _rmk = ((_rg["合算確率_num"] <= _jt) & (_rd >= 0)) | (_rd >= _mj_cfg.get("diff_bonus", 1000))
                                            else:
                                                _rmk = _rd >= 0
                                        else:
                                            _rmk = _rd >= _mthr
                                        _rec_bans_m += [int(b) for b in _rg[_rmk]["台番"].dropna()]
                                    if _rec_bans_m:
                                        _manual_ban_map[f"オススメ_{_make_safe_fn(_mbt)}_{_ms_sfxv}.jpg"] = sorted(set(_rec_bans_m))
```

注: 挿入位置・インデントは Read で厳密に確認する。`re` は既に import 済み。

- [ ] **Step 2: with_slump のときスランプ合成を通す**

`if _manual_imgs:`（`7099` 付近）の中を次のように変更する。変更前:

```python
                        if _manual_imgs:
                            st.session_state[_aprev_key] = _manual_imgs
                            st.session_state[f"_manual_preview_mode_{store}"] = True
```

変更後:

```python
                        if _manual_imgs:
                            if with_slump:
                                _m_ban2mac = {str(int(b)): str(m) for b, m in zip(_df_m["台番"], _df_m["機種名"])
                                              if str(b).split(".")[0].lstrip("-").isdigit()}
                                _m_ban2diff = {str(int(b)): int(d) for b, d in zip(_df_m["台番"], _diff_m)
                                               if str(b).split(".")[0].lstrip("-").isdigit()}
                                _m_date = st.session_state.get(f"auto_tb_date_{store}")
                                _m_date_str = _m_date.strftime("%Y-%m-%d") if hasattr(_m_date, "strftime") else str(_m_date or "")
                                _manual_imgs = _composite_slump_onto_images(
                                    _manual_imgs, _manual_ban_map, store,
                                    ban2mac=_m_ban2mac, ban2diff=_m_ban2diff, date_str=_m_date_str,
                                )
                            st.session_state[_aprev_key] = _manual_imgs
                            st.session_state[f"_manual_preview_mode_{store}"] = True
```

- [ ] **Step 3: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: 起動して動作確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`
手順: スランプ付き店舗で⓪でデータ取得 → ②等に記入 → 📝記入部分のみプレビュー作成。
Expected: 記入部分の画像にスランプグラフが合成されて表示される。データ未取得なら表だけで出る。

- [ ] **Step 5: Commit**

```
git add streamlit_app.py
git commit -m "feat: 記入部分のみプレビューにスランプ合成を追加"
```

---

### Task 4: 記入部分のみ実行（⑧）を with_slump 対応＋スランプ合成

**Files:**
- Modify: `streamlit_app.py:7696`（`_is_manual_mode` の判定）
- Modify: `streamlit_app.py:7697-7900` 付近（manual 実行の画像保存箇所）

**Interfaces:**
- Consumes: `_composite_slump_onto_images`（Task 1）, `_df_exec_m`, `_diff_exec_m`, `output_dir`, `_exec_order`, `_save_jpeg`
- Produces: `with_slump` 時、manual 実行の出力ファイルがスランプ合成済みになる

- [ ] **Step 1: ゲートを外す**

`streamlit_app.py:7696` を Read で確認し変更する。変更前:

```python
        _is_manual_mode = (not with_slump) and st.session_state.get(f"_manual_preview_mode_{store}", False)
```
変更後:
```python
        _is_manual_mode = bool(st.session_state.get(f"_manual_preview_mode_{store}", False))
```

- [ ] **Step 2: manual 実行の画像を収集し、保存前に合成**

manual 実行ブロック（`_is_manual_mode` の中、`7697` 以降）は各表画像を作って `output_dir` に `_save_jpeg` し `_exec_order` に追加する。これを「(fn, img) をリストに集め → with_slump なら `_composite_slump_onto_images` → まとめて保存」に変更する。

実装方針（Read で実際の生成箇所を確認して適用）:
1. manual 実行の先頭付近で `_m_slump_pairs: list[tuple[str, "Image.Image"]] = []` と `_m_ban_map_e: dict[str, list[int]] = {}` を用意。
2. 各画像生成箇所で、`_save_jpeg(...)` の代わりに `_m_slump_pairs.append((_fn, _img))` し、対応する台番を `_m_ban_map_e[_fn] = [int(b) ...]` に登録（Task 3 と同じ台番算出）。
3. manual 実行の末尾（`return`/`status` 完了前）で:
```python
                        if with_slump and _m_slump_pairs:
                            _me_ban2mac = {str(int(b)): str(m) for b, m in zip(_df_exec_m["台番"], _df_exec_m["機種名"])
                                           if str(b).split(".")[0].lstrip("-").isdigit()}
                            _me_ban2diff = {str(int(b)): int(d) for b, d in zip(_df_exec_m["台番"], _diff_exec_m)
                                            if str(b).split(".")[0].lstrip("-").isdigit()}
                            _me_date = st.session_state.get(f"auto_tb_date_{store}")
                            _me_date_str = _me_date.strftime("%Y-%m-%d") if hasattr(_me_date, "strftime") else str(_me_date or "")
                            _m_slump_pairs = _composite_slump_onto_images(
                                _m_slump_pairs, _m_ban_map_e, store,
                                ban2mac=_me_ban2mac, ban2diff=_me_ban2diff, date_str=_me_date_str,
                            )
                        for _fn_s, _img_s in _m_slump_pairs:
                            _out_s = os.path.join(output_dir, _fn_s)
                            _save_jpeg(_img_s, _out_s)
                            if _fn_s not in _exec_order:
                                _exec_order.append(_fn_s)
```

注: manual 実行の既存の生成／保存箇所の実変数名（`_df_exec_m`, `_diff_exec_m`, `_exec_order`, `_unique_fn_e` 等）と構造は着手時に Read で確認し、上記の「集めて→合成→保存」に確実に置き換える。合成なし（`with_slump=False`）のときは従来どおり保存されること（`_m_slump_pairs` をそのまま保存）を保証する。

- [ ] **Step 3: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: 起動して⑧実行確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`
手順: スランプ付き店舗で📝プレビュー → ⑧実行 → デスクトップ出力を確認。
Expected: 記入部分の出力ファイルにスランプグラフが合成されている（16台以上は `_side.jpg` も）。`with_slump=False`（通常ページ）の manual 実行は従来どおり表のみで出力される。

- [ ] **Step 5: Commit**

```
git add streamlit_app.py
git commit -m "feat: 記入部分のみ実行をスランプ合成対応"
```

---

## Self-Review メモ

- **Spec coverage:** 📝ボタン=Task2 / 合成ヘルパー=Task1 / プレビュー合成=Task3 / ⑧実行合成＋ゲート解除=Task4 / データ未取得は表のみ=Task1のヘルパー内。全網羅。
- **要実機確認:** Task4 の manual 実行ブロックの生成／保存構造は行がずれやすく分岐も多いため、着手時に Read で実変数名・保存箇所を確定してから「集めて→合成→保存」に置換する。`with_slump=False` の回帰（従来どおり表のみ保存）を必ず確認する。
- **型整合:** `_composite_slump_onto_images` の引数名・戻り値は Task3/4 の呼び出しと一致。
