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


if __name__ == "__main__":
    test_fit_center_landscape_in_wide_box()
    test_fit_center_tall_in_wide_box()
    print("OK: test_fit_center")
    test_featured_single_machine()
    test_featured_multi_machine_picks_max_diff()
    test_featured_empty_returns_none()
    print("OK: test_featured")
