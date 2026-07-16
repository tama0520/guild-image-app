# tests/test_gap_sel_key.py  —  py -3.14 tests/test_gap_sel_key.py で実行
# 液晶選択キーの台番ベース化（同一機種の複数画像を個別選択）
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit_app as app


def test_same_bans_same_key():
    """同じ台番集合＝同じキー（順序が違っても一致＝縦版/横版が共有できる）"""
    a = app._gap_sel_key("新小岩", [1001, 1002, 1003], "マイジャグV")
    b = app._gap_sel_key("新小岩", [1003, 1001, 1002], "マイジャグV")
    assert a == b, (a, b)


def test_different_bans_different_key():
    """同一機種でも台番が違えば別キー（今回の並び画像2枚のケース）"""
    a = app._gap_sel_key("新小岩", [1001, 1002, 1003], "マイジャグV")
    b = app._gap_sel_key("新小岩", [1010, 1011, 1012], "マイジャグV")
    assert a != b, (a, b)


def test_different_store_different_key():
    a = app._gap_sel_key("新小岩", [1, 2, 3], "マイジャグV")
    b = app._gap_sel_key("上野新館", [1, 2, 3], "マイジャグV")
    assert a != b


def test_different_machine_different_key():
    a = app._gap_sel_key("新小岩", [1, 2, 3], "マイジャグV")
    b = app._gap_sel_key("新小岩", [1, 2, 3], "ネオアイム")
    assert a != b


def test_stable_across_processes():
    """hash() と違い hashlib なので値が固定（プロセス間で再現できる）"""
    k = app._gap_sel_key("新小岩", [1001, 1002, 1003], "マイジャグV")
    assert k == "_gap_sel_新小岩_b_" + __import__("hashlib").md5(
        "新小岩|マイジャグV|1001,1002,1003".encode("utf-8")).hexdigest()[:12]


def test_str_bans_same_as_int():
    """台番が文字列でも int と同じキー（経路により型が違っても一致させる）"""
    a = app._gap_sel_key("新小岩", ["1001", "1002"], "マイジャグV")
    b = app._gap_sel_key("新小岩", [1001, 1002], "マイジャグV")
    assert a == b


def test_fallback_to_machine_when_no_bans():
    """bans が空/取得不能なら従来の機種名単位キーへフォールバック"""
    assert app._gap_sel_key("新小岩", [], "マイジャグV") == "_gap_sel_新小岩_m_マイジャグV"
    assert app._gap_sel_key("新小岩", None, "マイジャグV") == "_gap_sel_新小岩_m_マイジャグV"
    assert app._gap_sel_key("新小岩", ["x"], "マイジャグV") == "_gap_sel_新小岩_m_マイジャグV"


def test_bans_key_not_machine_key():
    """bans があるときは機種名単位キーへ戻らない"""
    k = app._gap_sel_key("新小岩", [1001], "マイジャグV")
    assert "_b_" in k and "_m_" not in k


if __name__ == "__main__":
    test_same_bans_same_key()
    test_different_bans_different_key()
    test_different_store_different_key()
    test_different_machine_different_key()
    print("OK: key identity")
    test_stable_across_processes()
    test_str_bans_same_as_int()
    print("OK: stability")
    test_fallback_to_machine_when_no_bans()
    test_bans_key_not_machine_key()
    print("OK: fallback")
