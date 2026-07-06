# 個別機種の優秀台ピックアップ Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ②個別画像に「個別機種の優秀台ピックアップ」欄（タイトル＋台番、3枠）を追加し、指定台番の機種の自動高配分生成を抑制しつつ、貼った台番だけの画像を生成する（通常ページ＋記事用ページ）。

**Architecture:** 単一ファイル `streamlit_app.py` の Streamlit アプリ。共通ヘルパーを追加し、通常ページ（`show_auto_page`）と記事用ページ（`show_auto_article_page`）の UI・プレビュー・実行・永続化の各所へ最小フックを入れる。抑制はパイプライン呼び出しの `recommended_machines` / `sonota_exclude` に逆引き機種を合流させることで実現（既存の個別画像抑制と同じ仕組み）。

**Tech Stack:** Python 3.14, Streamlit, PIL, pandas。テストフレームワークは無い。検証は AST 構文チェックと Streamlit 起動（CLAUDE.md 準拠）。

## Global Constraints

- 編集後は必ず構文チェック: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
- Windows 環境。コマンドは PowerShell ツールで実行（Bash 不可）。
- 日本語を含む厳密一致が取れない場合は `py -3.14 - << 'PYEOF'` 形式の Python スクリプトで書き換える。
- 枠数は 3（i = 0..2）。タイトル欄＋台番テキスト欄の2欄。機種名欄は無し。
- 画像はピンクバー無し。通常ページ=`_build_machine_img(df, title, None)`、記事用=`_build_machine_img_no_bar(df)`。
- 台番抽出は `expand_machine_numbers(text)`。台番→機種の逆引きで抑制対象機種を決定。
- 既存パターンに合わせる（`sonota_extra` の各所の実装をミラー）。DRY・YAGNI・頻繁なコミット。

---

### Task 1: 共通ヘルパー関数と永続化キーの追加

**Files:**
- Modify: `streamlit_app.py`（ヘルパーは `expand_machine_numbers` 定義の近く④データユーティリティ内、または `_auto_input_keys` の直前に追加）
- Modify: `streamlit_app.py:4339-4344`（`_auto_input_keys`）
- Modify: `streamlit_app.py:4405-4408`（`_article_input_keys`）

**Interfaces:**
- Produces:
  - `_collect_kojin_pick(store: str, prefix: str = "") -> list[tuple[str, set[int]]]` — 非空の (タイトル, 台番set) を最大3件返す。
  - `_kojin_pick_suppressed_machines(uploaded, store: str, prefix: str = "") -> set[str]` — 全ピックアップ台番から Excel を逆引きした機種名 set。
  - `_kojin_pick_machines_from_df(picks, df) -> set[str]` — df から台番逆引きで機種 set（プレビュー/実行で df 既取得時に使う）。

- [ ] **Step 1: ヘルパー関数を追加**

`_auto_input_keys` 定義（4327行）の直前に追加する:

```python
_KOJIN_PICK_COUNT = 3

def _collect_kojin_pick(store: str, prefix: str = "") -> list[tuple[str, set[int]]]:
    """個別機種の優秀台ピックアップの (タイトル, 台番set) を返す（台番非空のみ）。"""
    out: list[tuple[str, set[int]]] = []
    for i in range(_KOJIN_PICK_COUNT):
        title = str(st.session_state.get(f"{prefix}kojin_pick_title_{i}_{store}", "")).strip()
        bans_text = str(st.session_state.get(f"{prefix}kojin_pick_bans_{i}_{store}", "")).strip()
        if not bans_text:
            continue
        bans = set(expand_machine_numbers(bans_text))
        if not bans:
            continue
        out.append((title or "個別機種の優秀台ピックアップ", bans))
    return out

def _kojin_pick_machines_from_df(picks: list[tuple[str, set[int]]], df) -> set[str]:
    """ピックアップ台番から df で機種を逆引きした集合。"""
    all_bans: set[int] = set()
    for _t, b in picks:
        all_bans |= b
    if not all_bans or df is None or df.empty:
        return set()
    _rows = df[df["台番"].apply(lambda b: int(b) in all_bans)]
    return {str(m).strip() for m in _rows["機種名"] if str(m).strip()}

def _kojin_pick_suppressed_machines(uploaded, store: str, prefix: str = "") -> set[str]:
    """アップロード Excel を読み、ピックアップ台番の機種名 set を返す（パイプライン前の抑制用）。"""
    picks = _collect_kojin_pick(store, prefix)
    if not picks:
        return set()
    try:
        _raw = _read_uploaded_df(uploaded)
        _df0, _ = normalize_df(_raw)
        _df0 = apply_name_conversion(_df0)
    except Exception:
        return set()
    finally:
        try:
            uploaded.seek(0)
        except Exception:
            pass
    return _kojin_pick_machines_from_df(picks, _df0)
```

- [ ] **Step 2: 通常ページの永続化キーを追加**

`streamlit_app.py:4339` の `keys += [` ブロック（`sonota_extra_*` を含む）に追記する。変更前:

```python
    keys += [
        f"kojin_narabi_range_{store}", f"kojin_narabi_title_{store}",
        f"kojin_narabi2_range_{store}", f"kojin_narabi2_title_{store}",
        f"sonota_extra_title_{store}", f"sonota_extra_text_{store}",
        "variety_enabled", f"variety_range_{store}", "variety_mode",
    ]
```

変更後（`for` を挿入）:

```python
    keys += [
        f"kojin_narabi_range_{store}", f"kojin_narabi_title_{store}",
        f"kojin_narabi2_range_{store}", f"kojin_narabi2_title_{store}",
        f"sonota_extra_title_{store}", f"sonota_extra_text_{store}",
        "variety_enabled", f"variety_range_{store}", "variety_mode",
    ]
    for i in range(_KOJIN_PICK_COUNT):
        keys += [f"kojin_pick_title_{i}_{store}", f"kojin_pick_bans_{i}_{store}"]
```

- [ ] **Step 3: 記事用ページの永続化キーを追加**

`streamlit_app.py:4405` の `keys += [` ブロックに追記する。変更後:

```python
    keys += [
        f"art_kojin_narabi_range_{store}", f"art_kojin_narabi_title_{store}",
        f"art_kojin_narabi2_range_{store}", f"art_kojin_narabi2_title_{store}",
    ]
    for i in range(_KOJIN_PICK_COUNT):
        keys += [f"art_kojin_pick_title_{i}_{store}", f"art_kojin_pick_bans_{i}_{store}"]
```

- [ ] **Step 4: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```
git add streamlit_app.py
git commit -m "feat: 個別機種の優秀台ピックアップ 共通ヘルパーと永続化キー追加"
```

---

### Task 2: 通常ページ（show_auto_page）の UI 追加

**Files:**
- Modify: `streamlit_app.py:5519-5540`（②個別画像「その他の優秀台ピックアップ」の直前に挿入）

**Interfaces:**
- Consumes: `_KOJIN_PICK_COUNT`, `_save_auto_inputs`
- Produces: session_state キー `kojin_pick_title_{i}_{store}` / `kojin_pick_bans_{i}_{store}`

- [ ] **Step 1: UI ブロックを挿入**

`streamlit_app.py:5520` の `if True:  # その他の優秀台ピックアップ（全店舗）` の**直前**に、次を挿入する:

```python
        # 個別機種の優秀台ピックアップ（全店舗・その他の優秀台ピックアップの上）
        st.markdown("**個別機種の優秀台ピックアップ**")
        st.caption("タイトルと台番を指定した機種は、貼った台番だけの画像を作り、自動高配分画像は生成しません。")
        for _pi in range(_KOJIN_PICK_COUNT):
            _col_pt, _col_pb = st.columns([2, 3])
            with _col_pt:
                st.text_input(
                    "タイトル",
                    key=f"kojin_pick_title_{_pi}_{store}",
                    placeholder="例: マイジャグV",
                    on_change=_save_auto_inputs, args=(store,),
                )
            with _col_pb:
                st.text_area(
                    "台番テキスト（台番を含むテキストをそのまま貼り付け）",
                    key=f"kojin_pick_bans_{_pi}_{store}",
                    height=68,
                    on_change=_save_auto_inputs, args=(store,),
                )
```

注: `text_input`/`text_area` は `key` があり session_state に復元済みのため `value=` は付けない（`_restore_auto_inputs` が値を設定する）。

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 起動して UI 目視確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`（ブラウザで店舗→自動処理→②個別画像を開き、「個別機種の優秀台ピックアップ」欄が「その他の優秀台ピックアップ」の上に3枠表示されること、入力が保存されること）
Expected: 欄が表示され、リロード後も値が残る。

- [ ] **Step 4: Commit**

```
git add streamlit_app.py
git commit -m "feat: 通常ページに個別機種の優秀台ピックアップ欄を追加"
```

---

### Task 3: 通常ページ 抑制＋プレビュー画像生成

**Files:**
- Modify: `streamlit_app.py:6199-6220`（`_prev_rec_names` と `run_auto_pipeline` 呼び出しの `sonota_exclude`）
- Modify: `streamlit_app.py:6357-6379` 付近（kojin 並びブロックの直後にプレビュー画像を追加）

**Interfaces:**
- Consumes: `_collect_kojin_pick`, `_kojin_pick_suppressed_machines`, `_pv_df`, `_build_machine_img`, `_prev_img_list`
- Produces: プレビュー一覧 `_prev_img_list` に `(f"{title}.jpg", Image)` を追加

- [ ] **Step 1: 抑制機種をパイプラインに渡す**

`streamlit_app.py:6205-6207` の直後（`_prev_rec_names` 構築後）に追加:

```python
                        _pick_suppress = _kojin_pick_suppressed_machines(uploaded, store)
                        _prev_rec_names |= _pick_suppress
```

そして `run_auto_pipeline`（6214）の `sonota_exclude=` 引数（6220）を次に変更:

変更前:
```python
                            sonota_exclude={m.strip() for block in recommended_blocks for m in block["machines"] if m.strip()},
```
変更後:
```python
                            sonota_exclude={m.strip() for block in recommended_blocks for m in block["machines"] if m.strip()} | _pick_suppress,
```

- [ ] **Step 2: プレビュー画像を追加**

`streamlit_app.py:6379`（kojin narabi2 ブロックの `except Exception: pass` 直後、`# ─ ⑤ バラエティ画像` の直前）に追加:

```python
                            # 個別機種の優秀台ピックアップ（貼った台番のみ・ピンクバーなし）
                            for _pk_tit, _pk_bans in _collect_kojin_pick(store):
                                _pk_df = _pv_df[_pv_df["台番"].apply(lambda b: int(b) in _pk_bans)].copy()
                                if _pk_df.empty:
                                    continue
                                _pk_df = _pk_df.iloc[_pk_df["台番"].argsort()].reset_index(drop=True)
                                _prev_img_list.append((f"{_make_safe_fn(_pk_tit)}.jpg",
                                                       _build_machine_img(_pk_df, _pk_tit, None)))
```

注: このブロックは既存の `if kojin_enabled and _pv_df is not None and _pv_diff is not None:`（6357）の内側インデントに合わせて配置する（`_pv_df` が None でない文脈）。

- [ ] **Step 3: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: 起動して動作確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`
手順: 稲毛 Excel をアップ→②で「個別機種の優秀台ピックアップ」にタイトル「マイジャグV」＋マイジャグVの台番を貼る→⑦プレビュー生成。
Expected:
- プレビューに「マイジャグV.jpg」（貼った台のみ）が出る。
- 「マイジャグV_高配分.jpg」が**出ない**（自動高配分が抑制されている）。
- 自動「その他の優秀台ピックアップ.jpg」にマイジャグVが含まれない。

- [ ] **Step 5: Commit**

```
git add streamlit_app.py
git commit -m "feat: 通常プレビューで個別機種ピックアップ生成と自動高配分抑制"
```

---

### Task 4: 通常ページ 実行（⑧）抑制＋画像出力

**Files:**
- Modify: `streamlit_app.py:7925-7930`（実行時の `run_auto_pipeline` の `recommended_machines` / `sonota_exclude`）
- Modify: `streamlit_app.py:7672` の直前（`② その他の優秀台ピックアップ` 生成の前にピックアップ画像を出力）

**Interfaces:**
- Consumes: `_collect_kojin_pick`, `_kojin_pick_suppressed_machines`, `_df_exec_m`, `_diff_exec_m`(不要), `_unique_fn_e`, `_save_jpeg`, `_exec_order`, `output_dir`, `_build_machine_img`
- Produces: `output_dir` に `{title}.jpg` を保存し `_exec_order` に追加

- [ ] **Step 1: 抑制機種を実行パイプラインに渡す**

`streamlit_app.py:7925` の `result = run_auto_pipeline(` 呼び出し直前で `_rec_names` を組み立てている箇所を確認し、その直後に次を追加する（`_rec_names` 構築後・`run_auto_pipeline` 呼び出し前）:

```python
                _pick_suppress_e = _kojin_pick_suppressed_machines(uploaded, store)
                _rec_names |= _pick_suppress_e
```

`run_auto_pipeline`（7925）の `sonota_exclude=`（7930）を変更:

変更前:
```python
                sonota_exclude={m.strip() for block in recommended_blocks for m in block["machines"] if m.strip()},
```
変更後:
```python
                sonota_exclude={m.strip() for block in recommended_blocks for m in block["machines"] if m.strip()} | _pick_suppress_e,
```

注: `_rec_names` の実変数名は 7928 の `recommended_machines=_rec_names` で確認する。異なる場合はその変数に `|= _pick_suppress_e` する。

- [ ] **Step 2: 実行時にピックアップ画像を出力**

`streamlit_app.py:7672`（`# ② その他の優秀台ピックアップ`）の直前に追加する（同じ `_unique_fn_e`/`_df_exec_m` 文脈内、インデントを 7673 に合わせる）:

```python
                        # 個別機種の優秀台ピックアップ（貼った台番のみ・ピンクバーなし）
                        for _pk_tit_e, _pk_bans_e in _collect_kojin_pick(store):
                            _pk_df_e = _df_exec_m[_df_exec_m["台番"].apply(lambda b: int(b) in _pk_bans_e)].copy()
                            if _pk_df_e.empty:
                                continue
                            _pk_df_e = _pk_df_e.iloc[_pk_df_e["台番"].argsort()].reset_index(drop=True)
                            _pkfn_e = _unique_fn_e(f"{_make_safe_fn(_pk_tit_e)}.jpg")
                            _pk_out_e = os.path.join(output_dir, _pkfn_e)
                            _save_jpeg(_build_machine_img(_pk_df_e, _pk_tit_e, None), _pk_out_e)
                            _exec_order.append(_pkfn_e)
                            _m_log(f"  ✅ 個別機種の優秀台ピックアップ「{_pk_tit_e}」({len(_pk_df_e)}台)")
```

- [ ] **Step 3: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: 起動して⑧実行確認**

Run: `py -3.14 -m streamlit run streamlit_app.py`
手順: Task 3 と同じ入力で⑧実行→ZIP を確認。
Expected: ZIP に「マイジャグV.jpg」が含まれ、「マイジャグV_高配分.jpg」が含まれず、ジャグラーシリーズ優秀台.jpg にマイジャグVが入っていない。

- [ ] **Step 5: Commit**

```
git add streamlit_app.py
git commit -m "feat: 通常⑧実行で個別機種ピックアップ出力と自動高配分抑制"
```

---

### Task 5: 記事用ページ（show_auto_article_page）UI 追加

**Files:**
- Modify: `streamlit_app.py:9744-9745`（②個別画像の並びタイトル取得の直後、③並び画像の直前に挿入）

**Interfaces:**
- Consumes: `_KOJIN_PICK_COUNT`, `_save_article_inputs`
- Produces: session_state キー `art_kojin_pick_title_{i}_{store}` / `art_kojin_pick_bans_{i}_{store}`

- [ ] **Step 1: UI ブロックを挿入**

`streamlit_app.py:9744`（`kojin_narabi2_title = ...` の行）の直後、`# ── ③ 並び画像オプション`（9746）の直前に、`if kojin_enabled:` ブロック内インデントで挿入する:

```python
        st.markdown("**個別機種の優秀台ピックアップ**")
        st.caption("タイトルと台番を指定した機種は、貼った台番だけの画像を作り、自動高配分画像は生成しません。")
        for _pi in range(_KOJIN_PICK_COUNT):
            _col_apt, _col_apb = st.columns([2, 3])
            with _col_apt:
                st.text_input(
                    "タイトル",
                    key=f"art_kojin_pick_title_{_pi}_{store}",
                    placeholder="例: マイジャグV",
                    on_change=_save_article_inputs, args=(store,),
                )
            with _col_apb:
                st.text_area(
                    "台番テキスト（台番を含むテキストをそのまま貼り付け）",
                    key=f"art_kojin_pick_bans_{_pi}_{store}",
                    height=68,
                    on_change=_save_article_inputs, args=(store,),
                )
```

注: 挿入位置が `if kojin_enabled:`（9686）ブロックの内側インデント（8スペース）であることを確認する。9744 が同ブロック内であることを Read で確認してから挿入。

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 起動して UI 目視確認（高田馬場・記事用）**

Run: `py -3.14 -m streamlit run streamlit_app.py`
Expected: 高田馬場の記事用ページ ②個別画像 の並び欄の下に3枠が表示され、値が保存される。

- [ ] **Step 4: Commit**

```
git add streamlit_app.py
git commit -m "feat: 記事用ページに個別機種の優秀台ピックアップ欄を追加"
```

---

### Task 6: 記事用ページ 抑制＋プレビュー＋実行画像出力

**Files:**
- Modify: `streamlit_app.py:9983-9987`（記事用プレビューの `run_auto_pipeline` / `recommended_machines`）
- Modify: 記事用プレビュー画像構築ブロック（10225 付近〜、kojin 画像を append している箇所）
- Modify: `streamlit_app.py:10519-10522`（記事用実行の `run_auto_pipeline` / `recommended_machines`）＋実行画像出力箇所

**Interfaces:**
- Consumes: `_collect_kojin_pick(store, prefix="art_")`, `_kojin_pick_suppressed_machines(uploaded, store, prefix="art_")`, `_build_machine_img_no_bar`
- Produces: 記事用プレビュー一覧・記事用 ZIP に `{title}.jpg`

- [ ] **Step 1: 記事用プレビューの抑制**

`streamlit_app.py:9983` の `_art_pr = run_auto_pipeline(` 呼び出しの直前で `_art_prec`（9987 の `recommended_machines=_art_prec`）を構築している箇所を Read で確認し、その直後に追加:

```python
                        _art_pick_suppress = _kojin_pick_suppressed_machines(uploaded, store, prefix="art_")
                        _art_prec |= _art_pick_suppress
```

`run_auto_pipeline` の `sonota_exclude=` 引数がある場合は同様に `| _art_pick_suppress` を付ける（引数が無ければ追加しない）。

- [ ] **Step 2: 記事用プレビュー画像を追加**

10225 付近の記事用プレビュー画像リスト（kojin 個別画像を append しているブロック）の末尾に、記事用の帯なし画像を追加する。プレビュー DataFrame 変数（記事用の `_pv_df` 相当。Read で実変数名を確認、多くは `_art_pv_df` 等）を用いて:

```python
                            for _pk_tit, _pk_bans in _collect_kojin_pick(store, prefix="art_"):
                                _pk_df = _ART_PV_DF[_ART_PV_DF["台番"].apply(lambda b: int(b) in _pk_bans)].copy()
                                if _pk_df.empty:
                                    continue
                                _pk_df = _pk_df.iloc[_pk_df["台番"].argsort()].reset_index(drop=True)
                                _ART_PREV_LIST.append((f"{_make_safe_fn(_pk_tit)}.jpg",
                                                       _build_machine_img_no_bar(_pk_df)))
```

`_ART_PV_DF` / `_ART_PREV_LIST` は Read で確認した実際のプレビュー DataFrame 変数・プレビュー一覧変数に置き換える。

- [ ] **Step 3: 記事用実行の抑制と画像出力**

`streamlit_app.py:10519` の実行 `run_auto_pipeline`（`recommended_machines=_kojin_names`、10522）の直前で:

```python
            _art_pick_suppress_e = _kojin_pick_suppressed_machines(uploaded, store, prefix="art_")
            _kojin_names |= _art_pick_suppress_e
```

記事用実行の画像出力ループ（`_df_exec_m` 相当を使って画像を `output_dir` に保存している箇所。Read で確認）に、帯なし版のピックアップ出力を追加する:

```python
                        for _pk_tit_e, _pk_bans_e in _collect_kojin_pick(store, prefix="art_"):
                            _pk_df_e = _df_exec_m[_df_exec_m["台番"].apply(lambda b: int(b) in _pk_bans_e)].copy()
                            if _pk_df_e.empty:
                                continue
                            _pk_df_e = _pk_df_e.iloc[_pk_df_e["台番"].argsort()].reset_index(drop=True)
                            _pkfn_e = _unique_fn_e(f"{_make_safe_fn(_pk_tit_e)}.jpg")
                            _save_jpeg(_build_machine_img_no_bar(_pk_df_e), os.path.join(output_dir, _pkfn_e))
                            _exec_order.append(_pkfn_e)
```

`_unique_fn_e` / `_exec_order` / `_df_exec_m` は記事用実行ブロックでの実変数名を Read で確認して合わせる。存在しない場合は保存＋ファイルリスト追加の既存パターン（記事用の他画像出力）に合わせる。

- [ ] **Step 4: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 5: 起動して記事用の動作確認（高田馬場）**

Run: `py -3.14 -m streamlit run streamlit_app.py`
Expected: 記事用プレビュー・実行で帯なしのピックアップ画像が出力され、対象機種の自動高配分が抑制される。

- [ ] **Step 6: Commit**

```
git add streamlit_app.py
git commit -m "feat: 記事用ページで個別機種ピックアップ生成と自動高配分抑制"
```

---

## Self-Review メモ

- **Spec coverage:** UI(通常/記事)=Task2,5 / 抑制(通常/記事)=Task3,4,6 / 画像生成(通常プレビュー・実行/記事プレビュー・実行)=Task3,4,6 / 永続化(通常/記事)=Task1 / ピンクバー無し・帯なし=各Task。すべて網羅。
- **要実機確認:** Task4/6 の実行ブロックの実変数名（`_rec_names`, `_art_prec`, `_kojin_names`, `_df_exec_m`, `_unique_fn_e`, `_exec_order`, 記事用プレビュー DataFrame/一覧変数）は行番号が実装で前後するため、着手時に Read で確定してから編集する。プレースホルダは大文字（`_ART_PV_DF` 等）で明示。
- **重複除去:** 新欄と既存その他欄の台番重複は非要件（ユーザー確認済み）。
