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


if __name__ == "__main__":
    test_fit_center_landscape_in_wide_box()
    test_fit_center_tall_in_wide_box()
    print("OK: test_fit_center")
    test_featured_single_machine()
    test_featured_multi_machine_picks_max_diff()
    test_featured_empty_returns_none()
    print("OK: test_featured")
    test_attach_3col_fills_when_empty2()
    test_attach_3col_skips_when_empty1()
    test_attach_3col_none_screen_no_crash()
    print("OK: test_attach_3col")
    test_attach_side_fills_when_empty3()
    test_attach_side_skips_when_empty1()
    print("OK: test_attach_side")
    test_resolve_gap_screen_minus1_is_none()
    test_resolve_gap_screen_empty_is_none()
    test_resolve_gap_screen_loads()
    print("OK: test_resolve")
