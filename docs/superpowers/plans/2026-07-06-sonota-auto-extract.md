# 📝記入部分のみモード その他自動抽出 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 📝記入部分のみモードで、②その他ピックアップの台番テキストが空欄のとき、ラジオ（+1,000/+2,000/+3,000枚以上）で選んだ閾値の「その他の優秀台ピックアップ」を、記入済みの個別・並び・末尾の台を除外して自動生成する。

**Architecture:** ②その他ピックアップにラジオを追加。除外集合の算出（機種＋台番）と抽出を2つのモジュールヘルパーに切り出し、記入部分プレビュー生成と⑧実行の両方から呼ぶ。台番テキストがあれば従来どおり台番優先。

**Tech Stack:** Python 3.14, Streamlit, PIL, pandas。テストフレームワーク無し。検証は AST 構文チェックと Streamlit 起動（CLAUDE.md 準拠）。

## Global Constraints

- 編集後は必ず構文チェック: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
- Windows 環境。PowerShell ツール使用（Bash 不可）。
- 対象は **📝記入部分のみモードのみ**（プレビュー `if _manual_prev_btn:` と ⑧実行 `if _is_manual_mode:`）。フルフロー・記事用ページは変更しない。
- ラジオ選択肢：`なし`（デフォルト）／`+1,000枚以上`／`+2,000枚以上`／`+3,000枚以上`。閾値 1000/2000/3000。
- 台番テキストに入力があれば台番優先（ラジオ無視）。空欄＋ラジオ≠なしで自動抽出。抽出0台なら生成しない。
- タイトルは `sonota_extra_title.strip() or "その他の優秀台ピックアップ"`、ピンクバーなし（`_build_machine_img(df, title, None)`）。
- 除外：②個別（全台・優秀台）の機種名＋個別機種ピックアップ台番＋並び台番＋末尾台番。ジャグラーは「その他」に含める。

---

### Task 1: ヘルパー2種 ＋ ラジオUI ＋ 永続化キー

**Files:**
- Modify: `streamlit_app.py`（`_auto_input_keys` 定義の直前にヘルパー追加。`_collect_kojin_pick` の近くでも可）
- Modify: `streamlit_app.py:4401`（`_auto_input_keys` の keys）
- Modify: `streamlit_app.py:5602-5622`（②その他ピックアップUI）

**Interfaces:**
- Produces:
  - `_manual_sonota_auto_bans(df, store, kojin_zentai_machines, kojin_yushu_machines, narabi_ranges, kojin_narabi_range_txt, kojin_narabi2_range_txt) -> tuple[set[str], set[int]]`
  - `_manual_sonota_auto_extract(df, diff, thr, exc_mac, exc_ban) -> pd.DataFrame`
  - session_state キー `sonota_extra_auto_{store}`（ラジオ）
  - `_SONOTA_AUTO_THR: dict[str,int]`（ラベル→閾値）

- [ ] **Step 1: ヘルパーと定数を追加**

`_auto_input_keys`（`4400` 付近）の直前に追加する:

```python
_SONOTA_AUTO_THR = {"+1,000枚以上": 1000, "+2,000枚以上": 2000, "+3,000枚以上": 3000}

def _manual_sonota_auto_bans(df, store, kojin_zentai_machines, kojin_yushu_machines,
                             narabi_ranges, kojin_narabi_range_txt, kojin_narabi2_range_txt):
    """記入部分のみモードのその他自動抽出で除外する (機種名集合, 台番集合)。"""
    _exc_mac = {m.strip() for m in (list(kojin_zentai_machines) + list(kojin_yushu_machines)) if m.strip()}
    _exc_ban: set[int] = set()
    for _t, _b in _collect_kojin_pick(store):
        _exc_ban |= set(_b)
    for _bl in (narabi_ranges or []):
        _exc_ban |= {int(b) for b in _bl}
    for _txt in (kojin_narabi_range_txt, kojin_narabi2_range_txt):
        if _txt and _txt.strip():
            try:
                _exc_ban |= ranges_to_bans(parse_ranges(_txt.strip()))
            except Exception:
                pass
    if st.session_state.get("suebangai_enabled", False):
        for _t in [t for _i in range(1, 4) if (t := st.session_state.get(f"suebangai_tail_input_{_i}", "").strip())]:
            if _t == "ゾロ目":
                _exc_ban |= {int(b) for b in df["台番"] if (s := str(int(b))) and len(s) >= 2 and s[-2] == s[-1]}
            elif _t.isdigit() and len(_t) in (1, 2):
                _exc_ban |= {int(b) for b in df["台番"] if str(int(b))[-len(_t):] == _t}
    if st.session_state.get("jug_sue_enabled", False):
        _jser = set(get_store_config(store)["juggler_series"])
        for _t in [t for _i in range(1, 4) if (t := st.session_state.get(f"jug_sue_tail_input_{_i}", "").strip())]:
            if _t == "ゾロ目":
                _cand = [int(b) for b in df["台番"] if (s := str(int(b))) and len(s) >= 2 and s[-2] == s[-1]]
            elif _t.isdigit() and len(_t) in (1, 2):
                _cand = [int(b) for b in df["台番"] if str(int(b))[-len(_t):] == _t]
            else:
                _cand = []
            for _b in _cand:
                _row = df[df["台番"] == _b]
                if not _row.empty and str(_row.iloc[0]["機種名"]) in _jser:
                    _exc_ban.add(_b)
    return _exc_mac, _exc_ban

def _manual_sonota_auto_extract(df, diff, thr, exc_mac, exc_ban):
    """差枚>=thr かつ 機種名∉exc_mac かつ 台番∉exc_ban の台を台番順で返す。"""
    _mask = ((~df["機種名"].isin(exc_mac)) &
             (diff.values >= thr) &
             (~df["台番"].apply(lambda b: int(b) in exc_ban)))
    _r = df[_mask.values].copy()
    if _r.empty:
        return _r
    return _r.iloc[_r["台番"].argsort()].reset_index(drop=True)
```

注: `_collect_kojin_pick` / `ranges_to_bans` / `parse_ranges` / `get_store_config` が実在することを Grep で確認（すべて既存）。ヘルパーは `_collect_kojin_pick` 定義より後に置くこと。

- [ ] **Step 2: 永続化キーを追加**

`streamlit_app.py:4401` の `f"sonota_extra_title_{store}", f"sonota_extra_text_{store}",` を含む `keys += [...]` に、同じリスト内へ `f"sonota_extra_auto_{store}",` を追記する。Read で該当行を確認してから編集。

- [ ] **Step 3: ラジオUIを追加**

`streamlit_app.py:5620` の台番テキスト `st.text_area(...)` ブロックの直後（`with _col_seb:` を閉じた後、`sonota_extra_title = ...`（`5621`）の直前）に、`if True:` ブロックのインデントで追加する:

```python
            st.radio(
                "台番テキストが空欄のとき、下記の閾値で「その他の優秀台ピックアップ」を自動抽出（📝記入部分のみモード）",
                options=["なし", "+1,000枚以上", "+2,000枚以上", "+3,000枚以上"],
                key=f"sonota_extra_auto_{store}",
                horizontal=True,
                on_change=_save_auto_inputs, args=(store,),
            )
```

そして `sonota_extra_text = ...`（`5622`）の直後に読み出し変数を追加:

```python
        sonota_extra_auto = st.session_state.get(f"sonota_extra_auto_{store}", "なし")
```

- [ ] **Step 4: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: 起動して目視確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`（②その他ピックアップにラジオが表示され、保存されること）
Expected: ラジオ表示・リロードで値保持。

- [ ] **Step 6: Commit**

```
git add streamlit_app.py
git commit -m "feat: その他自動抽出のヘルパー・ラジオUI・永続化キーを追加"
```

---

### Task 2: 記入部分プレビューに自動抽出分岐を追加

**Files:**
- Modify: `streamlit_app.py:7026-7032` 付近（`if _manual_prev_btn:` 内の「② その他の優秀台ピックアップ」）

**Interfaces:**
- Consumes: `_manual_sonota_auto_bans` / `_manual_sonota_auto_extract` / `_SONOTA_AUTO_THR`（Task 1）、`sonota_extra_auto`, `_df_m`, `_diff_m`, `_manual_imgs`, `_manual_ban_map`
- Produces: 空欄＋ラジオ選択時、`_manual_imgs`/`_manual_ban_map` にその他画像を追加

- [ ] **Step 1: sonota_extra ブロックに elif を追加**

`if _manual_prev_btn:` 内の「② その他の優秀台ピックアップ」処理（`sonota_extra_text.strip()` を判定している箇所）を Read で特定し、その `if sonota_extra_text.strip():` の後ろに次の `elif` を追加する（既存 if 節は変更しない）:

```python
                            elif sonota_extra_auto in _SONOTA_AUTO_THR:
                                _exc_mac_m, _exc_ban_m = _manual_sonota_auto_bans(
                                    _df_m, store, kojin_zentai_machines, kojin_yushu_machines,
                                    narabi_ranges if narabi_ok else [],
                                    st.session_state.get(f"kojin_narabi_range_{store}", ""),
                                    st.session_state.get(f"kojin_narabi2_range_{store}", ""),
                                )
                                _se_auto_m = _manual_sonota_auto_extract(
                                    _df_m, _diff_m, _SONOTA_AUTO_THR[sonota_extra_auto], _exc_mac_m, _exc_ban_m)
                                if not _se_auto_m.empty:
                                    _se_tit_m = sonota_extra_title.strip() or "その他の優秀台ピックアップ"
                                    _manual_imgs.append((f"{_make_safe_fn(_se_tit_m)}.jpg",
                                                         _build_machine_img(_se_auto_m, _se_tit_m, None)))
                                    _manual_ban_map[f"{_make_safe_fn(_se_tit_m)}.jpg"] = [int(b) for b in _se_auto_m["台番"].tolist()]
```

注: インデントは既存 `if sonota_extra_text.strip():` に合わせる。この節が `if kojin_enabled:` の内側にあるか Read で確認し、もし内側なら `kojin_enabled` が False のときは自動抽出も出ないことになる（既存の台番テキスト処理と同じ挙動なので許容）。

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 起動して動作確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`
手順: 台番テキスト空欄・ラジオ「+1,000枚以上」→📝記入部分のみプレビュー。
Expected: 記入済み機種／並び／末尾を除いた +1,000枚以上の「その他の優秀台ピックアップ」が出る。台番テキストに入力すると従来どおりその台のみ。

- [ ] **Step 4: Commit**

```
git add streamlit_app.py
git commit -m "feat: 記入部分プレビューにその他自動抽出を追加"
```

---

### Task 3: 記入部分⑧実行に自動抽出分岐を追加

**Files:**
- Modify: `streamlit_app.py:7836-7847` 付近（`if _is_manual_mode:` 内の「② その他の優秀台ピックアップ」）

**Interfaces:**
- Consumes: `_manual_sonota_auto_bans` / `_manual_sonota_auto_extract` / `_SONOTA_AUTO_THR`、`sonota_extra_auto`, `_df_exec_m`, `_diff_exec_m`, `_exec_order`, `_m_exec_ban_map_e`, `_unique_fn_e`
- Produces: 空欄＋ラジオ選択時、その他画像を `output_dir` に保存し `_exec_order`・`_m_exec_ban_map_e` に登録

- [ ] **Step 1: sonota_extra 実行ブロックに elif を追加**

`if _is_manual_mode:` 内の「② その他の優秀台ピックアップ」実行処理（`if sonota_extra_text.strip():` で `_se_df_e`/`_unique_fn_e`/`_exec_order` を使う箇所）を Read で特定し、その `if` の後ろに次の `elif` を追加する:

```python
                        elif sonota_extra_auto in _SONOTA_AUTO_THR:
                            _exc_mac_e, _exc_ban_e = _manual_sonota_auto_bans(
                                _df_exec_m, store, kojin_zentai_machines, kojin_yushu_machines,
                                narabi_ranges if narabi_ok else [],
                                st.session_state.get(f"kojin_narabi_range_{store}", ""),
                                st.session_state.get(f"kojin_narabi2_range_{store}", ""),
                            )
                            _se_auto_e = _manual_sonota_auto_extract(
                                _df_exec_m, _diff_exec_m, _SONOTA_AUTO_THR[sonota_extra_auto], _exc_mac_e, _exc_ban_e)
                            if not _se_auto_e.empty:
                                _se_tit_e = sonota_extra_title.strip() or "その他の優秀台ピックアップ"
                                _sefn_e = _unique_fn_e(f"{_make_safe_fn(_se_tit_e)}.jpg")
                                _se_out_e = os.path.join(output_dir, _sefn_e)
                                _save_jpeg(_build_machine_img(_se_auto_e, _se_tit_e, None), _se_out_e)
                                _exec_order.append(_sefn_e)
                                _m_exec_ban_map_e[_sefn_e] = [int(b) for b in _se_auto_e["台番"].tolist()]
                                _m_log(f"  ✅ その他の優秀台ピックアップ（自動抽出 {sonota_extra_auto}）({len(_se_auto_e)}台)")
```

注: インデントは既存 `if sonota_extra_text.strip():` に合わせる。`_m_exec_ban_map_e` は既存（Task4で追加済み）なので登録すればスランプ合成対象になる。

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 起動して⑧実行確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`
手順: 台番テキスト空欄・ラジオ選択 → 📝プレビュー → ⑧実行 → デスクトップ出力確認。
Expected: 「その他の優秀台ピックアップ.jpg」が自動抽出内容で出力される（スランプ付きページならグラフ合成込み）。台番テキスト入力時は従来どおり。

- [ ] **Step 4: Commit**

```
git add streamlit_app.py
git commit -m "feat: 記入部分⑧実行にその他自動抽出を追加"
```

---

## Self-Review メモ

- **Spec coverage:** ラジオUI＋永続化＝Task1 / 除外・抽出ヘルパー＝Task1 / プレビュー分岐＝Task2 / ⑧実行分岐＝Task3 / スランプ合成は既存 `_composite_slump_onto_images` が `_manual_ban_map`/`_m_exec_ban_map_e` を見るため自動対応。全網羅。
- **エッジ:** 台番テキスト優先は `if sonota_extra_text.strip(): ... elif sonota_extra_auto in _SONOTA_AUTO_THR:` の順で担保。抽出0台は `if not _se_auto.empty:` でスキップ。
- **型整合:** `_manual_sonota_auto_bans`/`_manual_sonota_auto_extract`/`_SONOTA_AUTO_THR` の名前・引数は Task2/3 の呼び出しと一致。
- **要実機確認:** Task2/3 の sonota_extra ブロックが `if kojin_enabled:` の内側かどうかを Read で確認（内側なら kojin 無効時に自動抽出も出ない＝既存台番テキストと同挙動で許容）。
