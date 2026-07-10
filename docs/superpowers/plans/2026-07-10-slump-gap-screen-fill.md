# スランプ空きコマ液晶はめ込み Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** スランプグラフをグリッド配置したときの最終行の空きコマ（2コマ以上）に、機種の液晶画像1枚を中央配置ではめ込む機能を、まず新宿歌舞伎町「かぶぱポストの結果」に実装する。

**Architecture:** 純粋なジオメトリ／機種決定ヘルパーを新設し `py -3.14` の assert スクリプトで単体検証。既存の合成関数 `_attach_slump_to_table` / `_attach_slump_to_table_side` に `gap_screen_img` 引数を追加。プレビュー生成時に既定液晶を自動はめ込み、プレビュー各画像下の expander（サムネ付き `st.radio`）で差し替え可能にする。配線は `store == "新宿歌舞伎町"` に限定。

**Tech Stack:** Python 3.14 / Streamlit / Pillow (PIL)

## Global Constraints

- 実行環境は Windows。コマンドは PowerShell ではなく本計画記載の `py -3.14` で実行。
- ファイル編集後は必ず構文チェック: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
- pytest は未導入。テストは `py -3.14 tests/<file>.py` で実行する assert スクリプトとして書く。
- 既存の合成関数の定数は変更しない: `_attach_slump_to_table` は `COLS=3, PAD=12, GAP=8`、`_attach_slump_to_table_side` は `COLS=4, PAD=12, GAP=8`。
- はめ込み条件は共通で `empty >= 2`（`empty = COLS*rows - n`）。`empty` が 0/1 のときは何もしない。
- `get_machine_images(name)` は `{"screens": list[str], ...} | None` を返す（既存）。液晶未登録・None なら `gap_screen_img=None`＝空きのまま。
- 対象機種: 表が1機種ならその機種、2機種以上なら差枚最大の台の機種。

---

## Task 1: ジオメトリヘルパー `_fit_center_in_box`

box(矩形)内にアスペクト比維持で最大サイズにリサイズし、中央配置のオフセットを返す純粋関数。

**Files:**
- Modify: `streamlit_app.py`（`_attach_slump_to_table` 定義の直前、概ね 16130 行付近に追加）
- Test: `tests/test_gap_fill.py`（新規）

**Interfaces:**
- Produces: `_fit_center_in_box(img: "Image.Image", box_w: int, box_h: int) -> tuple["Image.Image", int, int]`
  戻り値 `(resized_img, offset_x, offset_y)`。`offset_x/y` は box 左上を原点とした box 内オフセット。

- [ ] **Step 1: 失敗するテストを書く**

`tests/test_gap_fill.py` を新規作成:

```python
# tests/test_gap_fill.py  —  py -3.14 tests/test_gap_fill.py で実行
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image
import streamlit_app as app


def test_fit_center_landscape_in_wide_box():
    # 横長200x100 を 300x200 box に入れる → scale=min(1.5,2.0)=1.5 → 300x150
    img = Image.new("RGB", (200, 100), (255, 0, 0))
    resized, ox, oy = app._fit_center_in_box(img, 300, 200)
    assert resized.size == (300, 150), resized.size
    assert ox == 0, ox            # 横は box いっぱい
    assert oy == (200 - 150) // 2 == 25, oy  # 縦は中央


def test_fit_center_tall_in_wide_box():
    # 縦長100x200 を 300x100 box に入れる → scale=min(3.0,0.5)=0.5 → 50x100
    img = Image.new("RGB", (100, 200), (0, 255, 0))
    resized, ox, oy = app._fit_center_in_box(img, 300, 100)
    assert resized.size == (50, 100), resized.size
    assert ox == (300 - 50) // 2 == 125, ox
    assert oy == 0, oy


if __name__ == "__main__":
    test_fit_center_landscape_in_wide_box()
    test_fit_center_tall_in_wide_box()
    print("OK: test_fit_center")
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: FAIL（`AttributeError: module 'streamlit_app' has no attribute '_fit_center_in_box'`）

- [ ] **Step 3: 最小実装を追加**

`streamlit_app.py` の `def _attach_slump_to_table(` の直前に追加:

```python
def _fit_center_in_box(img: "Image.Image", box_w: int, box_h: int) -> tuple["Image.Image", int, int]:
    """box(box_w×box_h)内にアスペクト比維持で最大リサイズし、中央配置のオフセットを返す。"""
    iw, ih = img.size
    if iw <= 0 or ih <= 0 or box_w <= 0 or box_h <= 0:
        return img, 0, 0
    scale = min(box_w / iw, box_h / ih)
    new_w = max(1, int(round(iw * scale)))
    new_h = max(1, int(round(ih * scale)))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    ox = (box_w - new_w) // 2
    oy = (box_h - new_h) // 2
    return resized, ox, oy
```

- [ ] **Step 4: テストが通ることを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: `OK: test_fit_center`

- [ ] **Step 5: 構文チェックしてコミット**

```bash
py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"
git add streamlit_app.py tests/test_gap_fill.py
git commit -m "feat: 液晶はめ込み用ジオメトリ _fit_center_in_box を追加"
```

---

## Task 2: 対象機種決定ヘルパー `_featured_machine_for_bans`

台番リストから、はめ込む液晶の対象機種名を決める純粋関数。

**Files:**
- Modify: `streamlit_app.py`（`_fit_center_in_box` の直後に追加）
- Test: `tests/test_gap_fill.py`（追記）

**Interfaces:**
- Consumes: なし
- Produces: `_featured_machine_for_bans(bans: list, ban2diff: dict, ban2mac: dict) -> str | None`
  台番の機種名（`ban2mac[str(ban)]`）を集計。distinct 機種が1つならそれ。2つ以上なら `ban2diff` が最大の台の機種。判定不能なら None。

- [ ] **Step 1: 失敗するテストを追記**

`tests/test_gap_fill.py` の `if __name__` ブロックの前に追加:

```python
def test_featured_single_machine():
    bans = [657, 658, 659]
    ban2mac = {"657": "ゴッドイーター", "658": "ゴッドイーター", "659": "ゴッドイーター"}
    ban2diff = {"657": 6900, "658": 10000, "659": 3200}
    assert app._featured_machine_for_bans(bans, ban2diff, ban2mac) == "ゴッドイーター"


def test_featured_multi_machine_picks_max_diff():
    bans = [5, 665, 45]
    ban2mac = {"5": "カバネリ", "665": "ゴッドイーター", "45": "北斗転生2"}
    ban2diff = {"5": 200, "665": 14900, "45": 900}
    assert app._featured_machine_for_bans(bans, ban2diff, ban2mac) == "ゴッドイーター"


def test_featured_empty_returns_none():
    assert app._featured_machine_for_bans([], {}, {}) is None
```

同ファイル末尾の `if __name__ == "__main__":` ブロックに呼び出しを追加:

```python
    test_featured_single_machine()
    test_featured_multi_machine_picks_max_diff()
    test_featured_empty_returns_none()
    print("OK: test_featured")
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: FAIL（`AttributeError: ... '_featured_machine_for_bans'`）

- [ ] **Step 3: 最小実装を追加**

`_fit_center_in_box` の直後に追加:

```python
def _featured_machine_for_bans(bans: list, ban2diff: dict, ban2mac: dict) -> "str | None":
    """はめ込む液晶の対象機種名を決める。1機種ならそれ、複数なら差枚最大の台の機種。"""
    macs = []
    for b in bans:
        m = ban2mac.get(str(b))
        if m:
            macs.append((str(b), m))
    if not macs:
        return None
    distinct = {m for _, m in macs}
    if len(distinct) == 1:
        return next(iter(distinct))
    best_ban, best_mac = None, None
    best_diff = None
    for b, m in macs:
        d = ban2diff.get(b)
        if d is None:
            continue
        if best_diff is None or d > best_diff:
            best_diff, best_ban, best_mac = d, b, m
    return best_mac if best_mac is not None else macs[0][1]
```

- [ ] **Step 4: テストが通ることを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: `OK: test_featured`（他のOK行も出る）

- [ ] **Step 5: 構文チェックしてコミット**

```bash
py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"
git add streamlit_app.py tests/test_gap_fill.py
git commit -m "feat: 液晶はめ込み対象機種を決める _featured_machine_for_bans を追加"
```

---

## Task 3: `_attach_slump_to_table` に `gap_screen_img` 追加（3列）

3列縦レイアウトで、最終行の空きが2のときに液晶をはめ込む。

**Files:**
- Modify: `streamlit_app.py`（`_attach_slump_to_table`、概ね 16135-16187 行）
- Test: `tests/test_gap_fill.py`（追記）

**Interfaces:**
- Consumes: `_fit_center_in_box`
- Produces: `_attach_slump_to_table(table_img, graph_imgs, bg_path=None, gap_screen_img=None) -> Image.Image`
  （既存呼び出しは位置引数3つのままで互換）

- [ ] **Step 1: 失敗するテストを追記**

`tests/test_gap_fill.py` に追加（`if __name__` ブロックの前）:

```python
def _dummy_graphs(n, w=300, h=200):
    return [Image.new("RGB", (w, h), (0, 0, 128)) for _ in range(n)]


def test_attach_3col_fills_when_empty2():
    # n=4 → rows=2, empty=2 → はめ込む。液晶(黄)がキャンバス右下に現れる
    table = Image.new("RGB", (960, 400), (255, 255, 255))
    screen = Image.new("RGB", (200, 100), (255, 255, 0))
    out = app._attach_slump_to_table(table, _dummy_graphs(4), None, screen)
    # 右下領域に黄色ピクセルが存在すること（雑なサンプリング）
    px = out.load()
    found = any(px[x, y] == (255, 255, 0)
                for x in range(out.size[0] * 2 // 3, out.size[0])
                for y in range(out.size[1] * 2 // 3, out.size[1], 5))
    assert found, "液晶が右下にはめ込まれていない"


def test_attach_3col_skips_when_empty1():
    # n=5 → rows=2, empty=1 → はめ込まない。黄色は現れない
    table = Image.new("RGB", (960, 400), (255, 255, 255))
    screen = Image.new("RGB", (200, 100), (255, 255, 0))
    out = app._attach_slump_to_table(table, _dummy_graphs(5), None, screen)
    px = out.load()
    found = any(px[x, y] == (255, 255, 0)
                for x in range(out.size[0])
                for y in range(out.size[1]))
    assert not found, "empty=1 なのに液晶がはめ込まれた"


def test_attach_3col_none_screen_no_crash():
    table = Image.new("RGB", (960, 400), (255, 255, 255))
    out = app._attach_slump_to_table(table, _dummy_graphs(4), None, None)
    assert out.size[0] == 960
```

`if __name__` ブロックに追加:

```python
    test_attach_3col_fills_when_empty2()
    test_attach_3col_skips_when_empty1()
    test_attach_3col_none_screen_no_crash()
    print("OK: test_attach_3col")
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: FAIL（`gap_screen_img` 未対応で `test_attach_3col_fills_when_empty2` が assert 失敗、または TypeError）

- [ ] **Step 3: 実装を変更**

`_attach_slump_to_table` のシグネチャを変更:

```python
def _attach_slump_to_table(
    table_img: "Image.Image",
    graph_imgs: "list[Image.Image]",
    bg_path=None,
    gap_screen_img=None,
) -> "Image.Image":
```

関数末尾、`return canvas` の直前（`for i, g in enumerate(scaled):` ループの後）に追加:

```python
    # 最終行の空きコマ（2以上）に液晶をはめ込む
    empty = COLS * rows - n
    if gap_screen_img is not None and empty >= 2:
        last_count = n - (rows - 1) * COLS       # 最終行の埋まっている枚数
        gap_x0 = PAD + last_count * cell_w + last_count * GAP   # 最後のグラフ右端 + GAP
        gap_x1 = tw - PAD
        box_w  = gap_x1 - gap_x0
        gap_y0 = th + PAD + (rows - 1) * (row_h + GAP)
        box_h  = row_h
        if box_w > 0 and box_h > 0:
            fitted, ox, oy = _fit_center_in_box(gap_screen_img, box_w, box_h)
            canvas.paste(fitted, (gap_x0 + ox, gap_y0 + oy))
```

- [ ] **Step 4: テストが通ることを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: `OK: test_attach_3col`

- [ ] **Step 5: 構文チェックしてコミット**

```bash
py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"
git add streamlit_app.py tests/test_gap_fill.py
git commit -m "feat: _attach_slump_to_table に液晶はめ込み(gap_screen_img)を追加"
```

---

## Task 4: `_attach_slump_to_table_side` に `gap_screen_img` 追加（4列）

横4列レイアウトで、最終行の空きが2以上のときに液晶をはめ込む。

**Files:**
- Modify: `streamlit_app.py`（`_attach_slump_to_table_side`、概ね 15974-16034 行）
- Test: `tests/test_gap_fill.py`（追記）

**Interfaces:**
- Consumes: `_fit_center_in_box`
- Produces: `_attach_slump_to_table_side(table_img, graph_imgs, bg_path=None, gap_screen_img=None) -> Image.Image`

- [ ] **Step 1: 失敗するテストを追記**

```python
def test_attach_side_fills_when_empty3():
    # n=5 → COLS=4, rows=2, empty=3 → はめ込む
    table = Image.new("RGB", (1200, 400), (255, 255, 255))
    screen = Image.new("RGB", (200, 100), (255, 255, 0))
    out = app._attach_slump_to_table_side(table, _dummy_graphs(5), None, screen)
    px = out.load()
    found = any(px[x, y] == (255, 255, 0)
                for x in range(out.size[0] // 2, out.size[0])
                for y in range(out.size[1] // 2, out.size[1], 5))
    assert found, "side: 液晶がはめ込まれていない"


def test_attach_side_skips_when_empty1():
    # n=7 → COLS=4, rows=2, empty=1 → はめ込まない
    table = Image.new("RGB", (1200, 400), (255, 255, 255))
    screen = Image.new("RGB", (200, 100), (255, 255, 0))
    out = app._attach_slump_to_table_side(table, _dummy_graphs(7), None, screen)
    px = out.load()
    found = any(px[x, y] == (255, 255, 0)
                for x in range(out.size[0]) for y in range(out.size[1]))
    assert not found, "side: empty=1 なのに液晶がはめ込まれた"
```

`if __name__` ブロックに追加:

```python
    test_attach_side_fills_when_empty3()
    test_attach_side_skips_when_empty1()
    print("OK: test_attach_side")
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: FAIL

- [ ] **Step 3: 実装を変更**

`_attach_slump_to_table_side` のシグネチャに `gap_screen_img=None` を追加。
グラフ配置ループ（`for i, g in enumerate(scaled):` ... `canvas.paste(g, (x, y))`）の後、`return canvas` の直前に追加:

```python
    # 最終行の空きコマ（2以上）に液晶をはめ込む
    empty = COLS * rows - n
    if gap_screen_img is not None and empty >= 2:
        last_count = n - (rows - 1) * COLS
        gap_x0 = graph_x0 + PAD + last_count * cell_w + last_count * GAP
        gap_x1 = graph_x0 + graph_area_w - PAD
        box_w  = gap_x1 - gap_x0
        gap_y0 = PAD + (rows - 1) * (row_h + GAP)
        box_h  = row_h
        if box_w > 0 and box_h > 0:
            fitted, ox, oy = _fit_center_in_box(gap_screen_img, box_w, box_h)
            canvas.paste(fitted, (gap_x0 + ox, gap_y0 + oy))
```

- [ ] **Step 4: テストが通ることを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: `OK: test_attach_side`

- [ ] **Step 5: 構文チェックしてコミット**

```bash
py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"
git add streamlit_app.py tests/test_gap_fill.py
git commit -m "feat: _attach_slump_to_table_side に液晶はめ込みを追加"
```

---

## Task 5: 液晶ロード＆選択解決ヘルパー `_resolve_gap_screen`

対象機種の screens から、session_state の選択（index）を反映して液晶 Image を1枚返す。

**Files:**
- Modify: `streamlit_app.py`（`_featured_machine_for_bans` の直後に追加）
- Test: `tests/test_gap_fill.py`（追記）

**Interfaces:**
- Consumes: `_featured_machine_for_bans`, `get_machine_images`
- Produces:
  `_gap_screen_paths_for_bans(bans, ban2diff, ban2mac) -> tuple[str | None, list[str]]`
  戻り値 `(machine_name, screen_paths)`。対象機種名と液晶パス一覧（未登録なら `[]`）。
  `_resolve_gap_screen(screen_paths: list, sel_idx: int) -> "Image.Image | None"`
  `sel_idx == -1` または範囲外・空なら None、それ以外は該当パスを開いて返す。

- [ ] **Step 1: 失敗するテストを追記**

```python
def test_resolve_gap_screen_minus1_is_none():
    assert app._resolve_gap_screen(["dummy.png"], -1) is None


def test_resolve_gap_screen_empty_is_none():
    assert app._resolve_gap_screen([], 0) is None


def test_resolve_gap_screen_loads(tmp_path=None):
    import tempfile, os as _os
    d = tempfile.mkdtemp()
    p = _os.path.join(d, "s.png")
    Image.new("RGB", (40, 20), (1, 2, 3)).save(p)
    img = app._resolve_gap_screen([p], 0)
    assert img is not None and img.size == (40, 20)
```

`if __name__` ブロックに追加:

```python
    test_resolve_gap_screen_minus1_is_none()
    test_resolve_gap_screen_empty_is_none()
    test_resolve_gap_screen_loads()
    print("OK: test_resolve")
```

- [ ] **Step 2: テストが失敗することを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: FAIL（`_resolve_gap_screen` 未定義）

- [ ] **Step 3: 実装を追加**

`_featured_machine_for_bans` の直後に追加:

```python
def _gap_screen_paths_for_bans(bans: list, ban2diff: dict, ban2mac: dict) -> "tuple[str | None, list[str]]":
    """対象機種名と、その液晶パス一覧を返す。未登録なら ([...] は空)。"""
    mac = _featured_machine_for_bans(bans, ban2diff, ban2mac)
    if not mac:
        return None, []
    info = get_machine_images(mac)
    screens = list(info.get("screens") or []) if info else []
    return mac, screens


def _resolve_gap_screen(screen_paths: list, sel_idx: int) -> "Image.Image | None":
    """選択 index の液晶画像を開いて返す。-1・範囲外・空なら None。"""
    if not screen_paths or sel_idx is None or sel_idx < 0 or sel_idx >= len(screen_paths):
        return None
    try:
        return Image.open(str(screen_paths[sel_idx])).convert("RGB")
    except Exception:
        return None
```

- [ ] **Step 4: テストが通ることを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: `OK: test_resolve`

- [ ] **Step 5: 構文チェックしてコミット**

```bash
py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"
git add streamlit_app.py tests/test_gap_fill.py
git commit -m "feat: 液晶選択解決ヘルパー _gap_screen_paths_for_bans/_resolve_gap_screen を追加"
```

---

## Task 6: プレビュー生成で既定液晶を自動はめ込み＋メタ保存（かぶぱ）

プレビュー合成時、かぶぱ限定で対象機種の液晶（既定 index=0 または session_state の選択）をはめ込み、選択UI用のメタ情報を session_state に保存する。

**Files:**
- Modify: `streamlit_app.py`（プレビュー合成ループ、7260-7314 行付近）

**Interfaces:**
- Consumes: `_gap_screen_paths_for_bans`, `_resolve_gap_screen`, `_attach_slump_to_table`, `_attach_slump_to_table_side`
- Produces: session_state キー
  `st.session_state[f"_gap_meta_{store}"]` = `dict[fn -> {"machine": str|None, "screens": list[str]}]`
  `st.session_state[f"_gap_sel_{store}_{fn}"]` = 選択 index（既定 0、-1=はめ込まない）

- [ ] **Step 1: プレビュー合成ループを変更**

7260 行付近、`_merged_pv: list[...] = []` の直前に、メタ保存用 dict 初期化を追加:

```python
                                    _gap_meta_pv: dict[str, dict] = {}
```

7284 行付近、グラフ生成ループ `for _b_pv in _bans_pv:` の**前**に、対象機種の液晶パスを解決し既定はめ込み画像を用意するコードを追加:

```python
                                        _is_kabupa_pv = (store == "新宿歌舞伎町")
                                        _gap_img_pv = None
                                        if _is_kabupa_pv:
                                            _gmac_pv, _gpaths_pv = _gap_screen_paths_for_bans(
                                                _bans_pv, _ban2diff_pv, _ig_ban2mac_pv)
                                            _gap_meta_pv[_fn_pv] = {"machine": _gmac_pv, "screens": _gpaths_pv}
                                            _gsel_key_pv = f"_gap_sel_{store}_{_fn_pv}"
                                            _gsel_pv = st.session_state.get(_gsel_key_pv, 0)
                                            _gap_img_pv = _resolve_gap_screen(_gpaths_pv, _gsel_pv)
```

7307 行の `_attach_slump_to_table(_img_pv, _g_imgs_pv, _ig_bbb_pv)` を変更:

```python
                                            _merged_pv.append((_fn_pv, _attach_slump_to_table(_img_pv, _g_imgs_pv, _ig_bbb_pv, _gap_img_pv)))
```

7311 行の `_attach_slump_to_table_side(_img_pv, _g_imgs_pv, _ig_bbb_pv)` を変更:

```python
                                                _merged_pv.append((_side_fn_pv, _attach_slump_to_table_side(_img_pv, _g_imgs_pv, _ig_bbb_pv, _gap_img_pv)))
```

7314 行 `_prev_img_list = _merged_pv` の直後に、メタ保存を追加:

```python
                                    st.session_state[f"_gap_meta_{store}"] = _gap_meta_pv
```

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 既存単体テストが壊れていないことを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: 全 `OK:` 行が出る

- [ ] **Step 4: コミット**

```bash
git add streamlit_app.py
git commit -m "feat: かぶぱプレビューで既定液晶を自動はめ込み＋選択メタ保存"
```

---

## Task 7: プレビュー各画像下に液晶セレクタ（サムネ付き radio・かぶぱ）

プレビュー画像描画部で、かぶぱ限定で各画像下に expander を置き、対象機種の液晶をサムネ付き `st.radio` で選ばせる。選択変更で `st.rerun()`。

**Files:**
- Modify: `streamlit_app.py`（プレビュー描画ループ、7605-7617 行付近）

**Interfaces:**
- Consumes: `st.session_state[f"_gap_meta_{store}"]`、`st.session_state[f"_gap_sel_{store}_{fn}"]`
- Produces: 選択変更を `_gap_sel_{store}_{fn}` に反映

- [ ] **Step 1: 描画ループにセレクタを追加**

7617 行 `st.image(_pimg, caption=_ptitle, use_container_width=True)` の直後（`with _sub_img:` ブロック内、同インデント）に追加。
`_auto_previews` の要素は `(title, img)` で、対応するファイル名は `_gap_meta` のキー。タイトルとファイル名の対応が必要なため、メタは fn キー。ここでは `_ptitle`（拡張子なし表示名）ではなく、`_gap_meta` の各 fn を照合する。`_auto_previews` にファイル名が無い場合は `_gap_meta` の順序と一致する前提でタイトル一致（`os.path.splitext(fn)[0]` == 表示タイトル）で引く:

```python
                            if store == "新宿歌舞伎町":
                                _gap_meta = st.session_state.get(f"_gap_meta_{store}", {})
                                _match_fn = None
                                for _mfn in _gap_meta:
                                    if os.path.splitext(re.sub(r"^\d{2}_", "", _mfn))[0] == _ptitle \
                                       or os.path.splitext(_mfn)[0] == _ptitle:
                                        _match_fn = _mfn
                                        break
                                _meta = _gap_meta.get(_match_fn) if _match_fn else None
                                if _meta and _meta.get("screens"):
                                    _scr = _meta["screens"]
                                    _sel_key = f"_gap_sel_{store}_{_match_fn}"
                                    _cur = st.session_state.get(_sel_key, 0)
                                    with st.expander(f"🖼️ 液晶画像を選ぶ（{_meta.get('machine') or ''}）"):
                                        _opts = list(range(len(_scr))) + [-1]
                                        def _fmt(_i):
                                            return "はめ込まない" if _i == -1 else f"液晶{_i + 1}"
                                        _new = st.radio(
                                            "液晶", _opts, index=_opts.index(_cur) if _cur in _opts else 0,
                                            format_func=_fmt, key=f"radio_{_sel_key}",
                                            horizontal=True, label_visibility="collapsed",
                                        )
                                        _thumb_cols = st.columns(max(1, len(_scr)))
                                        for _si, _sp in enumerate(_scr):
                                            with _thumb_cols[_si]:
                                                try:
                                                    st.image(_sp, caption=f"液晶{_si + 1}", width=120)
                                                except Exception:
                                                    st.caption(f"液晶{_si + 1}（読込失敗）")
                                        if _new != _cur:
                                            st.session_state[_sel_key] = _new
                                            st.rerun()
```

- [ ] **Step 2: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 3: 単体テストが壊れていないことを確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: 全 `OK:` 行

- [ ] **Step 4: コミット**

```bash
git add streamlit_app.py
git commit -m "feat: かぶぱプレビューに液晶サムネ選択セレクタを追加"
```

---

## Task 8: 実行（生成）時に選択液晶を反映（かぶぱ）

かぶぱの生成実行パス（`_attach_slump_to_table` を呼ぶ実行側、8100・9926 行付近）でも、プレビューで選んだ液晶を反映する。

**Files:**
- Modify: `streamlit_app.py`（実行合成箇所、8128 行・9926 行付近、およびそれらに対応する `_side` 生成箇所）

**Interfaces:**
- Consumes: `st.session_state[f"_gap_sel_{store}_{fn}"]`、`_gap_screen_paths_for_bans`、`_resolve_gap_screen`

- [ ] **Step 1: 実行側の各合成箇所を特定**

Run: `py -3.14 - << 'PYEOF'
import re
src = open('streamlit_app.py', encoding='utf-8').read().splitlines()
for i, line in enumerate(src, 1):
    if '_attach_slump_to_table(' in line or '_attach_slump_to_table_side(' in line:
        print(i, line.strip())
PYEOF`
Expected: 7307・7311（Task6で変更済み）と、実行側の該当行番号一覧が出る。

- [ ] **Step 2: 実行側の各 `_attach_slump_to_table(...)` 呼び出しを変更**

Task 6 以外の各呼び出し箇所（プレビュー描画以外）について、直前で対象機種の液晶を解決して第4引数に渡す。各箇所は `ban_map`・`ban2diff`・`ban2mac` に相当するローカル変数が既にある（変数名は箇所により `_ig_ban2mac_*` 等）。各箇所で以下パターンを適用（`<bans>`・`<ban2diff>`・`<ban2mac>`・`<fn>` はその箇所のローカル変数に置換）:

```python
                                            if store == "新宿歌舞伎町":
                                                _gm, _gp = _gap_screen_paths_for_bans(<bans>, <ban2diff>, <ban2mac>)
                                                _gsel = st.session_state.get(f"_gap_sel_{store}_{<fn>}", 0)
                                                _gap_img = _resolve_gap_screen(_gp, _gsel)
                                            else:
                                                _gap_img = None
```

その直後の `_attach_slump_to_table(<table>, <graphs>, <bg>)` を `_attach_slump_to_table(<table>, <graphs>, <bg>, _gap_img)` に、`_attach_slump_to_table_side(...)` も同様に第4引数 `_gap_img` を追加する。

> 注: 実装者は Step 1 の出力で行番号を確定し、各箇所の実際の bans/ban2diff/ban2mac/fn 変数名（周辺 5-10 行を Read して確認）に置換すること。かぶぱの実行パスに該当しない箇所（他店舗専用ブロック）は変更不要。

- [ ] **Step 3: 構文チェック**

Run: `py -3.14 -c "import ast; ast.parse(open('streamlit_app.py', encoding='utf-8').read()); print('OK')"`
Expected: `OK`

- [ ] **Step 4: 単体テスト確認**

Run: `py -3.14 tests/test_gap_fill.py`
Expected: 全 `OK:` 行

- [ ] **Step 5: コミット**

```bash
git add streamlit_app.py
git commit -m "feat: かぶぱ生成実行時に選択液晶をはめ込み反映"
```

---

## Task 9: 実機確認（かぶぱ・エンドツーエンド）

**Files:**
- なし（動作確認のみ）

- [ ] **Step 1: アプリ起動**

```bash
py -3.14 -m streamlit run streamlit_app.py
```

- [ ] **Step 2: 新宿歌舞伎町 → かぶぱポストの結果 で確認**

以下を目視確認:
1. スランプグラフが4台・7台など「空き2」の画像で、最終行右に液晶が中央配置ではめ込まれる。
2. 空き1（5台・8台など）の画像では液晶がはめ込まれない。
3. 各画像下の「🖼️ 液晶画像を選ぶ」でサムネが出て、液晶2・液晶3へ切替→プレビューが更新される。
4. 「はめ込まない」選択で空きに戻る。
5. 生成実行後の出力画像にも選択が反映されている。
6. 液晶未登録の機種では例外なく空きのまま。

- [ ] **Step 3: 問題があれば該当 Task に戻って修正、なければ完了**

---

## Self-Review 結果

- **Spec coverage:** 描画コア(Task1,3,4)・機種決定(Task2)・液晶解決(Task5)・既定はめ込み(Task6)・サムネ選択UI(Task7)・実行反映(Task8)・実機確認(Task9) で spec 各項目を網羅。段階展開の第2/第3段階は本plan範囲外（かぶぱ完成後に別plan）。
- **Placeholder scan:** コードステップは実コードを記載。Task8 のみ「箇所ごとの変数名に置換」という手順を残すが、これは既存コードの多数の呼び出し箇所が箇所別ローカル変数を持つための正当な実装指示（Step1で行特定→周辺Readで確定）。
- **Type consistency:** `_fit_center_in_box`→`(img,int,int)`、`_featured_machine_for_bans`→`str|None`、`_gap_screen_paths_for_bans`→`(str|None, list)`、`_resolve_gap_screen`→`Image|None`、合成関数の第4引数 `gap_screen_img` で一貫。
