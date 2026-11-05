"""スロバース用：水色の近未来デザインの機種別表画像。

streamlit_app.py の _build_machine_img() が、スロバース店舗 × 結果ポスト用／スランプ付き結果
（_sloverse_theme()）のときだけ _build_sloverse_machine_img() 経由で render_table() を呼ぶ。
他店舗・他ページからは呼ばれない。素材の作り直しは build_assets()（実行時は使わない）。

構成（見本 1536×884「ネオアイム(優秀台)」を唯一の基準にする）
  - フレーム（上段・下段・左右の帯）とタイトル台座、見出しバーの光沢の縦プロファイルは
    見本から切り出した画像素材（assets/sloverse/*.png）を使う。
  - タイトル文字・列見出しの文字・罫線・セル・三角形・台番・機種名・数値は Python で描く。
  - 幅は見本と同じ 1536px 固定。行数に応じて高さだけを変える
    （上段素材と下段素材の間を、左右の帯素材を縦に伸ばしてつなぐ）。
"""
from __future__ import annotations

import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(_HERE, "assets", "sloverse")
FONT_PATH = os.path.join(_HERE, "fonts", "NotoSansJP-Black.otf")

# ── 見本から実測した寸法（px・見本 1536×884 基準）───────────────────────────
W = 1536
TABLE_X0, TABLE_X1 = 46, 1490          # 表の内側（左右の青い外枠線の内側）
HEADER_Y0, HEADER_Y1 = 136, 208        # 列見出しバー
ROW_PITCH = 69.5                       # データ行の間隔（見本 208→764 を 8 行）
TOP_BAND_H = 300                       # 上段素材（見本 0〜300 行目）
BOTTOM_SRC_Y0 = 690                    # 下段素材の切り出し開始（見本の表下端 764 の 74px 上）
BOTTOM_OVERLAP = 764 - BOTTOM_SRC_Y0   # 下段素材の先頭から表下端までの距離
MID_SRC = (300, 600)                   # 左右の帯（縦に伸ばす部分）
TITLE_CY = 60                          # タイトル文字の縦中心（見本 29〜90）
TITLE_MAX_W = 600                      # 台座内に収める最大文字幅
TITLE_ERASE = (452, 22, 1084, 99)      # 見本のタイトル文字を消す範囲（台座の内側）

# 見本の列幅（台番〜差枚数）。AT 列があるときは同じ考え方で比率配分する。
BASE_COL_W = {"台番": 169, "機種名": 326, "ゲーム数": 208, "BIG": 124, "REG": 127,
              "AT": 124, "合算確率": 240, "差枚数": 250}
ALIGN = {"台番": "ban", "機種名": "center", "ゲーム数": "right", "BIG": "center",
         "REG": "center", "AT": "center", "合算確率": "center", "差枚数": "right"}
RIGHT_PAD = {"ゲーム数": 26, "差枚数": 22}

# ── 見本から採った色 ─────────────────────────────────────────────────────
C_ROW_BG      = (238, 247, 254)        # 白〜薄水色のセル
C_ROW_BG_TOP  = (243, 251, 255)        # セル上端（わずかに明るい）
C_HLINE_A     = (101, 138, 162)        # 横罫線 1px 目
C_HLINE_B     = (153, 188, 213)        # 横罫線 2px 目
C_VLINE_A     = (129, 151, 169)        # 縦罫線 1px 目
C_VLINE_B     = (104, 125, 147)        # 縦罫線 2px 目
C_HDR_SEP     = (58, 206, 238)         # 見出しバー内の区切り（シアン）
C_TEXT        = (10, 17, 48)           # 濃紺の文字
C_HDR_TEXT    = (255, 255, 255)
C_PLUS        = (16, 32, 222)          # 差枚プラス：鮮やかな青
C_MINUS       = (204, 0, 0)            # 差枚マイナス：既存の結果ポストと同じ赤
C_TRI         = (4, 243, 5)            # 台番左の緑三角
C_TITLE       = (6, 18, 82)            # タイトル文字

# ── 文字サイズ（見本の文字高さから逆算）───────────────────────────────────
SZ_DATA = 42
SZ_HEADER = 34
SZ_TITLE = 64
SZ_MIN = 22


def _font(sz: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_PATH, sz)


# ═══════════════════════════════════════════════════════════════════════════
# 素材の切り出し（見本 → assets/sloverse/）
# ═══════════════════════════════════════════════════════════════════════════
def build_assets(sample_path: str, out_dir: str = ASSET_DIR) -> dict:
    """見本画像からフレーム素材を切り出す（タイトル文字は台座の色で塗りつぶす）。"""
    os.makedirs(out_dir, exist_ok=True)
    im = Image.open(sample_path).convert("RGB")
    assert im.size == (1536, 884), im.size

    top = im.crop((0, 0, W, TOP_BAND_H))
    # タイトル文字を消す：台座内の左右の列（文字の外側）を行ごとに線形補間する
    x0, y0, x1, y1 = TITLE_ERASE
    px = top.load()
    for y in range(y0, y1):
        a, b = px[x0, y], px[x1, y]
        for x in range(x0 + 1, x1):
            t = (x - x0) / (x1 - x0)
            px[x, y] = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    top.save(os.path.join(out_dir, "frame_top.png"))
    im.crop((0, MID_SRC[0], W, MID_SRC[1])).save(os.path.join(out_dir, "frame_mid.png"))
    im.crop((0, BOTTOM_SRC_Y0, W, im.height)).save(os.path.join(out_dir, "frame_bottom.png"))
    # 見出しバーの光沢：文字の無い列（機種名ラベルと区切りの間 x=500）の縦プロファイル
    im.crop((500, HEADER_Y0, 501, HEADER_Y1)).save(os.path.join(out_dir, "header_profile.png"))
    return {"top": top.size, "mid": MID_SRC, "bottom": (W, im.height - BOTTOM_SRC_Y0)}


# ═══════════════════════════════════════════════════════════════════════════
# 描画
# ═══════════════════════════════════════════════════════════════════════════
def _col_widths(cols: list[str], need: list[int] | None = None) -> list[int]:
    """見本の列幅比で内幅を配分し、文字が収まらない列（need）は余裕のある列から幅を借りる。"""
    base = [BASE_COL_W.get(c, 150) for c in cols]
    inner = TABLE_X1 - TABLE_X0
    s = sum(base)
    ws = [round(b * inner / s) for b in base]
    ws[-1] += inner - sum(ws)
    if need:
        for i, nd in enumerate(need):
            short = nd - ws[i]
            while short > 0:
                j = max((k for k in range(len(ws)) if k != i), key=lambda k: ws[k] - need[k])
                spare = ws[j] - need[j]
                if spare <= 0:
                    break
                take = min(spare, short)
                ws[j] -= take; ws[i] += take; short -= take
    return ws


def _fit_font(draw: ImageDraw.ImageDraw, text: str, size: int, max_w: int) -> ImageFont.FreeTypeFont:
    f = _font(size)
    while size > SZ_MIN and draw.textlength(text, font=f) > max_w:
        size -= 1
        f = _font(size)
    return f


def _draw_text(draw, box, text, font, fill, align, right_pad=24, left_x=None):
    """box=(x0,y0,x1,y1)。上下は文字の実描画範囲で中央。"""
    x0, y0, x1, y1 = box
    bb = draw.textbbox((0, 0), text, font=font)
    tw = bb[2] - bb[0]
    # 数字を含む文字列は「0」の高さで上下中央（カンマ・スラッシュ・G の下端に引っぱられない）
    vb = draw.textbbox((0, 0), "0", font=font) if any(c.isdigit() for c in text) else bb
    ty = y0 + (y1 - y0 - (vb[3] - vb[1])) / 2 - vb[1]
    if align == "right":
        tx = x1 - right_pad - tw - bb[0]
    elif align == "left":
        tx = left_x - bb[0]
    else:
        tx = x0 + (x1 - x0 - tw) / 2 - bb[0]
    draw.text((round(tx), round(ty)), text, font=font, fill=fill)


def _split2(text: str) -> tuple[str, str]:
    """2行に分ける位置：中央に最も近い「・」「空白」「(」の直前／直後。無ければ中央。"""
    mid = len(text) / 2
    cands = [i + 1 for i, c in enumerate(text) if c in "・ 　"] + [i for i, c in enumerate(text) if c in "(（"]
    cands = [i for i in cands if 0 < i < len(text)]
    i = min(cands, key=lambda k: abs(k - mid)) if cands else round(mid)
    return text[:i].rstrip(" 　"), text[i:].lstrip(" 　")


def _layout_fit(draw, text: str, max_w: int, max_h: int, sz1: int, sz1_min: int,
                sz2: int, sz2_min: int = 16):
    """1行で sz1→sz1_min まで縮めて入ればそれ、入らなければ2行（sz2→sz2_min）。
    戻り値: (行のリスト, フォント)。文字は省略しない。"""
    for sz in range(sz1, sz1_min - 1, -1):
        f = _font(sz)
        if draw.textlength(text, font=f) <= max_w:
            return [text], f
    a, b = _split2(text)
    for sz in range(sz2, sz2_min - 1, -1):
        f = _font(sz)
        lh = draw.textbbox((0, 0), "国", font=f)
        if (max(draw.textlength(a, font=f), draw.textlength(b, font=f)) <= max_w
                and (lh[3] - lh[1]) * 2 + sz * 0.25 <= max_h):
            return [a, b], f
    return [a, b], _font(sz2_min)


def _draw_lines(draw, cx: float, cy: float, lines: list[str], font, fill):
    """複数行を (cx, cy) を中心に描く（行間は文字サイズの 0.25）。"""
    ref = draw.textbbox((0, 0), "国", font=font)
    lh = ref[3] - ref[1]
    gap = round(font.size * 0.25)
    total = lh * len(lines) + gap * (len(lines) - 1)
    y = cy - total / 2
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        draw.text((round(cx - (bb[2] - bb[0]) / 2 - bb[0]), round(y - ref[1])), ln, font=font, fill=fill)
        y += lh + gap


def render_table(title: str, headers: list[str], rows: list[list[str]],
                 diff_signs: list[int] | None = None) -> Image.Image:
    """水色デザインの表画像を返す。

    headers : 表示列名（例 ["台番","機種名","ゲーム数","BIG","REG","合算確率","差枚数"]）
    rows    : 表示用文字列の行（既存 _format_display_cols と同じ書式を想定）
    diff_signs : 差枚の符号（+1/0/-1）。差枚列の色分けに使う。
    """
    n = len(rows)
    if n == 0:
        raise ValueError("出力するデータが 0 件です。")
    table_y1 = HEADER_Y1 + round(n * ROW_PITCH)          # 表の下端（見本の 764 に相当）
    bottom = Image.open(os.path.join(ASSET_DIR, "frame_bottom.png")).convert("RGB")
    bottom_y = table_y1 - BOTTOM_OVERLAP
    H = bottom_y + bottom.height

    canvas = Image.new("RGB", (W, H), (12, 61, 111))
    top = Image.open(os.path.join(ASSET_DIR, "frame_top.png")).convert("RGB")
    mid = Image.open(os.path.join(ASSET_DIR, "frame_mid.png")).convert("RGB")
    # 上段 → 左右の帯（必要な高さだけ縦に伸ばす）→ 下段
    canvas.paste(top.crop((0, 0, W, min(TOP_BAND_H, H))), (0, 0))
    gap = bottom_y - TOP_BAND_H
    if gap > 0:
        canvas.paste(mid.resize((W, gap), Image.BICUBIC), (0, TOP_BAND_H))
    canvas.paste(bottom, (0, bottom_y))

    d = ImageDraw.Draw(canvas)

    # ── タイトル（台座の中央・長いときだけ縮小）──
    # 1行で 44px まで縮小、それでも入らなければ2行（台座の高さ 72px に収める）
    t_lines, tf = _layout_fit(d, title, TITLE_MAX_W, 72, SZ_TITLE, 44, 32, 18)
    glow = Image.new("L", canvas.size, 0)
    _draw_lines(ImageDraw.Draw(glow), W / 2, TITLE_CY, t_lines, tf, 255)
    glow = glow.filter(ImageFilter.GaussianBlur(6))
    canvas.paste(Image.new("RGB", canvas.size, (255, 255, 255)), (0, 0),
                 glow.point(lambda v: int(v * 0.55)))
    d = ImageDraw.Draw(canvas)
    _draw_lines(d, W / 2, TITLE_CY, t_lines, tf, C_TITLE)

    # ── 列見出しバー（光沢は見本の縦プロファイルを横に伸ばす）──
    prof = Image.open(os.path.join(ASSET_DIR, "header_profile.png")).convert("RGB")
    canvas.paste(prof.resize((TABLE_X1 - TABLE_X0, HEADER_Y1 - HEADER_Y0)), (TABLE_X0, HEADER_Y0))
    _df = _font(SZ_DATA)
    need = []
    for i, h in enumerate(headers):
        tw = max(d.textlength(str(r[i]), font=_df) for r in rows)
        need.append(round(tw + (66 + 10 if ALIGN.get(h) == "ban" else RIGHT_PAD.get(h, 24) + 16)))
    if "機種名" in headers:
        _ni = headers.index("機種名")
        need[_ni] = min(need[_ni], (TABLE_X1 - TABLE_X0) - sum(v for k, v in enumerate(need) if k != _ni))
    ws = _col_widths(headers, need)
    xs = [TABLE_X0]
    for w_ in ws:
        xs.append(xs[-1] + w_)
    hf = _font(SZ_HEADER)
    for i, h in enumerate(headers):
        if i > 0:
            d.line([(xs[i], HEADER_Y0 + 2), (xs[i], HEADER_Y1 - 2)], fill=C_HDR_SEP, width=1)
            d.line([(xs[i] + 1, HEADER_Y0 + 2), (xs[i] + 1, HEADER_Y1 - 2)], fill=(16, 90, 140), width=1)
        _draw_text(d, (xs[i], HEADER_Y0, xs[i + 1], HEADER_Y1), h, hf, C_HDR_TEXT, "center")

    # ── データ行 ──
    for r, row in enumerate(rows):
        y0 = HEADER_Y1 + round(r * ROW_PITCH)
        y1 = HEADER_Y1 + round((r + 1) * ROW_PITCH)
        d.rectangle([(TABLE_X0, y0), (TABLE_X1 - 1, y1 - 1)], fill=C_ROW_BG)
        d.line([(TABLE_X0, y0), (TABLE_X1 - 1, y0)], fill=C_ROW_BG_TOP, width=3)
        for i, h in enumerate(headers):
            txt = str(row[i])
            cx0, cx1 = xs[i], xs[i + 1]
            if ALIGN.get(h) == "ban":
                # 緑の直角三角形（見本 33px・左上直角）＋台番
                t0x, t0y = cx0 + 13, y0 + 18
                d.polygon([(t0x, t0y), (t0x + 33, t0y), (t0x, t0y + 33)], fill=C_TRI)
                f = _fit_font(d, txt, SZ_DATA, (cx1 - cx0) - 66 - 8)
                _draw_text(d, (cx0, y0, cx1, y1), txt, f, C_TEXT, "left", left_x=cx0 + 66)
                continue
            if h == "機種名":
                # 1行で 30px まで縮小、入らなければ2行（行の高さに収める）。省略しない。
                n_lines, nf = _layout_fit(d, txt, (cx1 - cx0) - 20, (y1 - y0) - 8, SZ_DATA, 30, 28, 16)
                _draw_lines(d, (cx0 + cx1) / 2, (y0 + y1) / 2, n_lines, nf, C_TEXT)
                continue
            fill = C_TEXT
            if h == "差枚数" and diff_signs is not None:
                fill = C_PLUS if diff_signs[r] > 0 else (C_MINUS if diff_signs[r] < 0 else C_TEXT)
            pad = RIGHT_PAD.get(h, 24)
            f = _fit_font(d, txt, SZ_DATA, (cx1 - cx0) - pad - 16)
            _draw_text(d, (cx0, y0, cx1, y1), txt, f, fill, ALIGN.get(h, "center"), right_pad=pad)
        # 行下の横罫線（2px）
        d.line([(TABLE_X0, y1 - 2), (TABLE_X1 - 1, y1 - 2)], fill=C_HLINE_A, width=1)
        d.line([(TABLE_X0, y1 - 1), (TABLE_X1 - 1, y1 - 1)], fill=C_HLINE_B, width=1)
    # 縦罫線（データ行の範囲）
    for i in range(1, len(headers)):
        d.line([(xs[i], HEADER_Y1), (xs[i], table_y1 - 1)], fill=C_VLINE_A, width=1)
        d.line([(xs[i] + 1, HEADER_Y1), (xs[i] + 1, table_y1 - 1)], fill=C_VLINE_B, width=1)
    return canvas
