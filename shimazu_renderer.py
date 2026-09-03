# -*- coding: utf-8 -*-
"""島図（フロアマップ）レンダラー — 渋谷新館 記事用⑥ 専用

責務:
    「台番→差枚→色」「台番→機種名→表示」を、店舗ごとの座標マスタに従って
    1枚のPNGへ描画するだけ。データ取得・機種名変換は **呼び出し側の責務**。

    * Pision へはアクセスしない（呼び出し側が取得済みの DataFrame を渡す）
    * 機種名変換もしない（呼び出し側が apply_name_conversion() 済みの名前を渡す）
    * xlsm を実行時に読まない（座標は masters/shimazu_{store}.json、
      設備画像は assets/shimazu/{store}/ から読む。Cloud でも動く）

streamlit_app.py へ直接書かず独立モジュールにしている理由:
    島図の描画は自己完結した責務で、既存の画像生成系（draw_table_image /
    _build_machine_img など）と共有する処理が無い。streamlit_app.py は
    既に 2万行超あり、Streamlit に依存しないこのロジックを混ぜると
    テスト・再利用（⑦/⑧へ接続する将来Step）が難しくなる。
    wp_client.py / convert_narabi_pil.py と同じ「ルート直下の独立モジュール」
    という既存の構成に合わせている。
"""
from __future__ import annotations

import io
import json
import os

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_DIR, "fonts", "MochiyPopOne-Regular.ttf")

# 対応店舗（座標マスタと設備アセットが揃っている店舗のみ）
SHIMAZU_STORES: frozenset[str] = frozenset({"渋谷新館"})

# ── 色階級（凡例どおりの >= 判定。旧Excelの境界抜けは再現しない）──────────
#   1,999→+1,000 / 2,999→+2,000 / 4,999→+3,000 / 9,999→+5,000 / 20,000以上→+10,000
_CLASSES: tuple[tuple[int, str], ...] = (
    (10000, "RAINBOW"),
    (5000, "964FFF"),
    (3000, "FF552D"),
    (2000, "00C85A"),
    (1000, "FFFF0D"),
)

_LEGEND_PAD = 18        # 凡例の色枠右端と「+」の間隔（260830実測 7px/色枠50px 換算）
_LINE_SPACING = 2       # 機種名の行間
_MAX_LINES = 2          # 機種名は最大2行
_MIN_NAME_PX = 8        # 自動改行時のフォント下限
_MIN_OVERRIDE_PX = 10   # 指定改行時のフォント下限

# ── 機種名の表示レイアウト用 改行指定（機種名変換ではない）──────────────
#   キーは 機種名変換.xlsx を通した **正式な表示名そのもの**。
#   連結すると必ず正式名称へ戻る（下の _validate_overrides() で検証する）。
#   別名化・省略・replace ではない。ここに無い機種は自動改行を使う。
WRAP_OVERRIDE: dict[str, tuple[str, str]] = {
    # --- 確定済み6機種 ---
    "ヴァルヴレイヴ2": ("ヴァルヴ", "レイヴ2"),
    "ウルトラミラジャグ": ("ウルトラ", "ミラジャグ"),
    "ワールドダイスター": ("ワールド", "ダイスター"),
    "シャーマンキング": ("シャーマン", "キング"),
    "東京リベンジャーズ": ("東京リベン", "ジャーズ"),
    "ULTRAMAN最終決戦": ("ULTRAMAN", "最終決戦"),
    # --- 全機種調査で追加確定した17機種 ---
    "カバネリ海門決戦": ("カバネリ", "海門決戦"),
    "ゴッド神々の軌跡": ("ゴッド", "神々の軌跡"),
    "スマスロ北斗の拳": ("スマスロ", "北斗の拳"),
    "からくりサーカス2": ("からくり", "サーカス2"),
    "モンキーターンV": ("モンキー", "ターンV"),
    "とある禁書目録2": ("とある", "禁書目録2"),
    "ジャグラーガールズ": ("ジャグラー", "ガールズ"),
    "炎炎ノ消防隊2": ("炎炎ノ", "消防隊2"),
    "ヴァルヴレイヴ": ("ヴァルヴ", "レイヴ"),
    "スマスロ化物語": ("スマスロ", "化物語"),
    "モンハンライズ": ("モンハン", "ライズ"),
    "ゴッドイーター": ("ゴッド", "イーター"),
    "南国育ちSPECIAL": ("南国育ち", "SPECIAL"),
    "LBサンダーV": ("LB", "サンダーV"),
    "ケロット5BT": ("ケロット5", "BT"),
    "クレアの秘宝伝": ("クレアの", "秘宝伝"),
    "異世界かるてっと": ("異世界", "かるてっと"),
    # ToLOVEるトランス は自動改行のままで自然なため登録しない
}


def _validate_overrides() -> None:
    """指定改行を連結すると必ず正式名称へ戻ることを保証する（省略・別名化の防止）"""
    for _k, _v in WRAP_OVERRIDE.items():
        if "".join(_v) != _k:
            raise ValueError("改行指定が正式名称と不一致: %r -> %r" % (_k, _v))


_validate_overrides()


class ShimazuError(Exception):
    """島図マスタ・アセットの不備"""


def master_path(store: str) -> str:
    return os.path.join(BASE_DIR, "masters", "shimazu_%s.json" % store)


_MASTER_CACHE: dict[str, dict] = {}


def load_master(store: str) -> dict:
    """座標マスタを読み込み、最低限の健全性を検証する（壊れたまま描かない）"""
    if store in _MASTER_CACHE:
        return _MASTER_CACHE[store]
    path = master_path(store)
    if not os.path.exists(path):
        raise ShimazuError("島図の座標マスタがありません: %s" % path)
    with open(path, encoding="utf-8") as f:
        m = json.load(f)

    for key in ("range", "font", "colw", "rowh", "ban", "cells", "texts", "pics",
                "asset_dir", "x_adj", "rainbow"):
        if key not in m:
            raise ShimazuError("島図マスタに %r がありません: %s" % (key, path))

    bans = [b["ban"] for b in m["ban"]]
    if not bans:
        raise ShimazuError("島図マスタに台番がありません: %s" % path)
    if len(bans) != len(set(bans)):
        dup = sorted({b for b in bans if bans.count(b) > 1})
        raise ShimazuError("島図マスタの台番が重複しています: %s" % dup[:10])
    for b in m["ban"]:
        for key in ("ban", "r", "c"):
            if b.get(key) is None:
                raise ShimazuError("島図マスタの台番 %r に %r がありません" % (b.get("ban"), key))

    adir = os.path.join(BASE_DIR, m["asset_dir"].replace("/", os.sep))
    missing = sorted({p["img"] for p in m["pics"]
                      if not os.path.exists(os.path.join(adir, p["img"]))})
    if missing:
        raise ShimazuError("島図の設備画像がありません: %s (%s)" % (missing, adir))
    if not os.path.exists(FONT_PATH):
        raise ShimazuError("フォントがありません: %s" % FONT_PATH)

    _MASTER_CACHE[store] = m
    return m


def master_unit_count(store: str) -> int:
    """マスタが持つ台番数（呼び出し側の突合表示用）"""
    return len(load_master(store)["ban"])


def _hx(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _class_of(diff) -> str | None:
    if diff is None or (isinstance(diff, float) and pd.isna(diff)):
        return None
    try:
        d = int(diff)
    except (TypeError, ValueError):
        return None
    for th, col in _CLASSES:
        if d >= th:
            return col
    return None


def class_counts(units: dict[int, tuple[str, object]], store: str) -> dict[str, int]:
    """島図に載る台の色階級別台数（呼び出し側の検証表示用）"""
    m = load_master(store)
    out: dict[str, int] = {}
    for e in m["ban"]:
        col = _class_of(units.get(e["ban"], (None, None))[1])
        key = col or "なし"
        out[key] = out.get(key, 0) + 1
    return out


def _units_from_df(df: pd.DataFrame) -> dict[int, tuple[str, object]]:
    """DataFrame(台番/機種名/差枚) -> {台番: (機種名, 差枚)}。突合キーは台番のみ。"""
    if df is None or df.empty:
        return {}
    need = {"台番", "差枚"}
    if not need <= set(df.columns):
        raise ShimazuError("島図に必要な列がありません: %s" % sorted(need - set(df.columns)))
    has_name = "機種名" in df.columns
    out: dict[int, tuple[str, object]] = {}
    for _, row in df.iterrows():
        try:
            ban = int(str(row["台番"]).strip())
        except (TypeError, ValueError):
            continue
        name = str(row["機種名"]).strip() if has_name and pd.notna(row["機種名"]) else ""
        diff = row["差枚"] if pd.notna(row["差枚"]) else None
        out[ban] = (name, diff)
    return out


def render(df: pd.DataFrame, store: str = "渋谷新館") -> Image.Image:
    """島図を描画して PIL.Image を返す。

    df: 台番 / 機種名 / 差枚 を持つ DataFrame。
        機種名は **呼び出し側で apply_name_conversion() 済み**であること。
    """
    if store not in SHIMAZU_STORES:
        raise ShimazuError("島図に未対応の店舗です: %s" % store)
    m = load_master(store)
    units = _units_from_df(df)

    x_adj = float(m["x_adj"])
    c0, c1 = m["range"]["c0"], m["range"]["c1"]
    r0, r1 = m["range"]["r0"], m["range"]["r1"]
    colw, rowh = m["colw"], m["rowh"]

    # ── 座標系（列幅は既に <col min max> を個別展開したものがマスタに入っている）
    colx, x = {}, 0
    for c in range(1, 301):
        colx[c] = x
        w = colw.get(str(c), 9.0)
        x += 0 if w <= 0 else round((w * 7 + 5) * x_adj)
    rowy, y = {}, 0
    for r in range(1, 201):
        rowy[r] = y
        h = rowh.get(str(r), 44.1)
        y += 0 if h <= 0 else round(h * 96 / 72)
    ox, oy = colx[c0], rowy[r0]
    W, H = colx[c1 + 1] - ox, rowy[r1 + 1] - oy

    img = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(img)

    def box(r, c):
        return colx[c] - ox, rowy[r] - oy, colx[c + 1] - ox, rowy[r + 1] - oy

    fcache: dict[int, ImageFont.FreeTypeFont] = {}

    def fnt(px):
        if px not in fcache:
            fcache[px] = ImageFont.truetype(FONT_PATH, px)
        return fcache[px]

    # ── 1) 固定塗り ─────────────────────────────────────────────
    for cell in m["cells"]:
        r, c = cell["r"], cell["c"]
        if not (r0 <= r <= r1 and c0 <= c <= c1) or not cell["fill"]:
            continue
        x0, y0, x1, y1 = box(r, c)
        if x1 > x0 and y1 > y0:
            dr.rectangle([x0, y0, x1 - 1, y1 - 1], fill=_hx(cell["fill"]))

    # ── 2) 設備画像（座標変換は共通。設備ごとの個別倍率は使わない）───────
    adir = os.path.join(BASE_DIR, m["asset_dir"].replace("/", os.sep))
    EMU = 914400 / 96.0
    for p in m["pics"]:
        try:
            src = Image.open(os.path.join(adir, p["img"])).convert("RGBA")
        except Exception:
            continue
        # xdr:col / xdr:row は 0 始まりの絶対インデックス。X方向のオフセットにも同じ補正
        X0 = colx[p["fc"] + 1] - ox + p["fco"] / EMU * x_adj
        Y0 = rowy[p["fr"] + 1] - oy + p["fro"] / EMU
        X1 = colx[p["tc"] + 1] - ox + p["tco"] / EMU * x_adj
        Y1 = rowy[p["tr"] + 1] - oy + p["tro"] / EMU
        w, h = max(1, int(X1 - X0)), max(1, int(Y1 - Y0))
        rs = src.resize((w, h), Image.LANCZOS)
        img.paste(rs, (int(X0), int(Y0)), rs)

    # ── 3) 罫線 ─────────────────────────────────────────────────
    for cell in m["cells"]:
        r, c = cell["r"], cell["c"]
        if not (r0 <= r <= r1 and c0 <= c <= c1):
            continue
        x0, y0, x1, y1 = box(r, c)
        if x1 <= x0 or y1 <= y0:
            continue
        L, R, T, B = cell["bd"]
        if L:
            dr.line([x0, y0, x0, y1 - 1], fill=(0, 0, 0), width=1)
        if R:
            dr.line([x1 - 1, y0, x1 - 1, y1 - 1], fill=(0, 0, 0), width=1)
        if T:
            dr.line([x0, y0, x1 - 1, y0], fill=(0, 0, 0), width=1)
        if B:
            dr.line([x0, y1 - 1, x1 - 1, y1 - 1], fill=(0, 0, 0), width=1)

    # ── 4) セル塗り（中心白→外周色 / +10,000はレインボー）──────────────
    rainbow = [tuple(v) for v in m["rainbow"]]

    def paint(x0, y0, x1, y1, col):
        w, h = x1 - x0, y1 - y0
        if w <= 0 or h <= 0:
            return
        cell = Image.new("RGB", (w, h), "white")
        px = cell.load()
        if col == "RAINBOW":
            n = len(rainbow) - 1
            for i in range(w):
                t = i / max(1, w - 1) * n
                k = min(n - 1, int(t))
                f = t - k
                cc = tuple(round(rainbow[k][j] + (rainbow[k + 1][j] - rainbow[k][j]) * f)
                           for j in range(3))
                for j in range(h):
                    px[i, j] = cc
        else:
            oc = _hx(col)
            cx, cy = (w - 1) / 2, (h - 1) / 2
            for i in range(w):
                for j in range(h):
                    t = min(1.0, max(abs(i - cx) / max(cx, 1e-6),
                                     abs(j - cy) / max(cy, 1e-6)))
                    px[i, j] = tuple(round(255 + (oc[k] - 255) * t) for k in range(3))
        img.paste(cell, (x0, y0))

    # ── 5) 文字（最終座標系へ直接描画。画像を後から横へ伸ばさない）─────────
    PT = 96 / 72
    ban_px = round(float(m["font"]["ban_sz"]) * PT)
    name_px = round(float(m["font"]["nm_sz"]) * PT)

    def draw_block(lines, x0, y0, x1, y1, font, halign="center", pad=0):
        """複数行を1つのテキストブロックとして扱い、インクbboxの中心をセル中心へ。
           1行でも2行でも同じ経路（機種ごとの個別補正はしない）。"""
        txt = "\n".join(lines)
        bb = dr.multiline_textbbox((0, 0), txt, font=font,
                                   spacing=_LINE_SPACING, align="center")
        px_ = (x0 + pad - bb[0]) if halign == "left" else \
              ((x0 + x1) / 2 - (bb[0] + bb[2]) / 2)
        py_ = (y0 + y1) / 2 - (bb[1] + bb[3]) / 2
        dr.multiline_text((px_, py_), txt, font=font,
                          spacing=_LINE_SPACING, align="center", fill=(0, 0, 0))

    def auto_wrap(txt, font, maxw, maxline):
        lines, cur = [], ""
        for ch in txt:
            if dr.textlength(cur + ch, font=font) <= maxw or not cur:
                cur += ch
            else:
                lines.append(cur)
                cur = ch
                if len(lines) > maxline:
                    return None
        if cur:
            lines.append(cur)
        return lines if len(lines) <= maxline else None

    used_px: dict[str, int] = {}
    used_lines: dict[str, list[str]] = {}
    missing: list[int] = []
    counts: dict[str, int] = {}

    for e in m["ban"]:
        ban, r, c = e["ban"], e["r"], e["c"]
        x0, y0, x1, y1 = box(r, c)
        name, diff = units.get(ban, ("", None))
        col = _class_of(diff)
        counts[col or "なし"] = counts.get(col or "なし", 0) + 1
        if ban not in units:
            missing.append(ban)
        if col:
            paint(x0, y0, x1 - 1, y1 - 1, col)
        dr.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(0, 0, 0), width=1)
        draw_block([str(ban)], x0, y0, x1, y1, fnt(ban_px))

        if not e.get("nr") or not name:
            continue
        nx0, ny0, nx1, ny1 = box(e["nr"], e["nc"])
        dr.rectangle([nx0, ny0, nx1 - 1, ny1 - 1], fill=_hx("B9FFE8"), outline=(0, 0, 0))
        mw, mh = nx1 - nx0 - 6, ny1 - ny0 - 4
        sz = name_px
        ov = WRAP_OVERRIDE.get(name)
        if ov:
            # 指定改行を最優先。14ptで収まらない場合だけ必要最小限まで縮小する
            lines = list(ov)
            while sz > _MIN_OVERRIDE_PX and (
                    max(dr.textlength(l, font=fnt(sz)) for l in lines) > mw
                    or (sz + _LINE_SPACING) * len(lines) > mh):
                sz -= 1
        else:
            lines = auto_wrap(name, fnt(sz), mw, _MAX_LINES)
            while (lines is None
                   or (sz + _LINE_SPACING) * len(lines) > mh) and sz > _MIN_NAME_PX:
                sz -= 1
                lines = auto_wrap(name, fnt(sz), mw, _MAX_LINES)
            if lines is None:
                lines = [name]
        used_px[name] = sz
        used_lines[name] = lines
        draw_block(lines, nx0, ny0, nx1, ny1, fnt(sz))

    # ── 6) 凡例のレインボー枠（Excel は VBA 塗りで solid fill を持たない）───
    for t in m["texts"]:
        if str(t["t"]).startswith("+10,000"):
            lx0, ly0, lx1, ly1 = box(t["r"], t["c"] - 1)
            if lx1 > lx0:
                paint(lx0, ly0, lx1 - 1, ly1 - 1, "RAINBOW")
                dr.rectangle([lx0, ly0, lx1 - 1, ly1 - 1], outline=(0, 0, 0), width=1)

    # ── 7) 固定文字 ──────────────────────────────────────────────
    # 「2F」の枠は AZ8+BA8、凡例文字の枠は BA6+BB6 のように、同じ塗りの複数セルで
    # 1つの視覚ブロックを作っている（外周だけ罫線）。文字は先頭セルにしか無いので、
    # 単セル中央に描くと左寄りに見える。連結範囲を求めてその中央へ置く。
    cellmap = {(cc["r"], cc["c"]): cc for cc in m["cells"]}

    def visual_block(r, c):
        base = cellmap.get((r, c))
        if not base or not base["fill"]:
            return c, c
        lo = hi = c
        while True:
            cur = cellmap.get((r, lo))
            if not cur or cur["bd"][0]:
                break
            nxt = cellmap.get((r, lo - 1))
            if not nxt or nxt["fill"] != base["fill"] or nxt["bd"][1]:
                break
            lo -= 1
        while True:
            cur = cellmap.get((r, hi))
            if not cur or cur["bd"][1]:
                break
            nxt = cellmap.get((r, hi + 1))
            if not nxt or nxt["fill"] != base["fill"] or nxt["bd"][0]:
                break
            hi += 1
        return lo, hi

    for t in m["texts"]:
        lo, hi = visual_block(t["r"], t["c"])
        x0, y0, _, y1 = box(t["r"], lo)
        _, _, x1, _ = box(t["r"], hi)
        f = fnt(round(float(t["sz"]) * PT))
        if t.get("h") == "left":
            draw_block([t["t"]], x0, y0, x1, y1, f, halign="left", pad=_LEGEND_PAD)
        else:
            draw_block([t["t"]], x0, y0, x1, y1, f)

    img.info["shimazu_counts"] = counts
    img.info["shimazu_missing"] = missing
    img.info["shimazu_used_px"] = used_px
    img.info["shimazu_used_lines"] = used_lines
    return img


def render_png(df: pd.DataFrame, store: str = "渋谷新館") -> bytes:
    """島図を PNG バイト列で返す（⑦/⑧へ接続する将来Stepでもこれを呼べばよい）"""
    img = render(df, store)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
