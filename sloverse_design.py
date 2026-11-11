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
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

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
ALIGN = {"台番": "ban", "機種名": "center", "ゲーム数": "center", "BIG": "center",
         "REG": "center", "AT": "center", "合算確率": "center", "差枚数": "right"}
RIGHT_PAD = {"ゲーム数": 26, "差枚数": 22}   # ゲーム数は中央揃え（2026-11-11）だが、列幅（need）と文字縮小の判定に使うため値は残す

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


def _draw_dash_joined(canvas, box, text, font, fill):
    """「――」を _draw_text（中央揃え）と同じ位置・長さ・太さで、2本の間の切れ目だけ埋めて1本の線にする。
    NotoSansJP-Black の「―」は字の左右に余白があり、2文字並べると中央が数px切れて見えるため
    （他店舗の MochiyPopOne はつながっている）。切れ目の列は、線の中ほどの列と同じ縦の濃淡で埋める。"""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(canvas)
    bb = d.textbbox((0, 0), text, font=font)
    tx = round(x0 + (x1 - x0 - (bb[2] - bb[0])) / 2 - bb[0])
    ty = round(y0 + (y1 - y0 - (bb[3] - bb[1])) / 2 - bb[1])
    m = Image.new("L", (x1 - x0, y1 - y0), 0)
    ImageDraw.Draw(m).text((tx - x0, ty - y0), text, font=font, fill=255)
    ink = m.getbbox()
    if ink:
        px = m.load()
        cols = [max(px[x, y] for y in range(ink[1], ink[3])) for x in range(ink[0], ink[2])]
        top = max(cols)
        full = [ink[0] + i for i, v in enumerate(cols) if v >= top * 0.9]
        if full:
            ref = full[len(full) // 4]                       # 1本目の線の中ほどの列
            prof = [px[ref, y] for y in range(m.height)]
            for x in range(full[0], full[-1] + 1):           # 両端の外側（字の端のぼかし）はそのまま
                for y in range(m.height):
                    if px[x, y] < prof[y]:
                        px[x, y] = prof[y]
    canvas.paste(Image.new("RGB", m.size, fill), (x0, y0), m)


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
                 diff_signs: list[int] | None = None, summary: dict | None = None) -> Image.Image:
    """水色デザインの表画像を返す。

    headers : 表示列名（例 ["台番","機種名","ゲーム数","BIG","REG","合算確率","差枚数"]）
    rows    : 表示用文字列の行（既存 _format_display_cols と同じ書式を想定）
    diff_signs : 差枚の符号（+1/0/-1）。差枚列の色分けに使う。
    summary : 集計バーの表示文字列（render_summary_band 参照）。None なら従来どおりバーなし。
              バーは表の最終行の直下（下の枠の手前）に入り、画像の高さだけが SV_BAR_BAND_H 増える。
    """
    n = len(rows)
    if n == 0:
        raise ValueError("出力するデータが 0 件です。")
    table_y1 = HEADER_Y1 + round(n * ROW_PITCH)          # 表の下端（見本の 764 に相当）
    band_h = SV_BAR_BAND_H if summary else 0              # 集計バーの帯（表の下端〜下の枠）
    bottom = Image.open(os.path.join(ASSET_DIR, "frame_bottom.png")).convert("RGB")
    bottom_y = table_y1 + band_h - BOTTOM_OVERLAP
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
    # 1行で 30px まで縮小、それでも入らなければ2行（台座の高さ 72px に収める）。
    # 「その他のジャグラーシリーズの優秀台」程度の長さは1行のまま収める（語の途中で改行しない）。
    t_lines, tf = _layout_fit(d, title, TITLE_MAX_W, 72, SZ_TITLE, 30, 30, 18)
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
            if h == "合算確率" and txt == "――":
                # 表示不能の合算確率（BB+RB=0 または G数=0）は切れ目のない1本の線（位置・長さ・太さは文字のまま）
                f = _fit_font(d, txt, SZ_DATA, (cx1 - cx0) - RIGHT_PAD.get(h, 24) - 16)
                _draw_dash_joined(canvas, (cx0, y0, cx1, y1), txt, f, C_TEXT)
                d = ImageDraw.Draw(canvas)
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
    if summary:
        canvas.paste(render_summary_band(summary, TABLE_X1 - TABLE_X0), (TABLE_X0, table_y1))
    return canvas


# ═══════════════════════════════════════════════════════════════════════════
# 集計バー（総差枚・平均・勝率）：スロバース専用（2026-11-11 見本「新鬼武者3(優秀台)」）
#   既存の他店舗でピンクサマリーバーが付く画像（summary_stat あり）にだけ、表の最終行の直下へ入れる。
#   値の文字列は呼び出し側（streamlit_app）が既存の集計値・fmt_diff で作ったものをそのまま描く。
# ═══════════════════════════════════════════════════════════════════════════
SV_BAR_BAND_H = 104                       # 帯の高さ（1 倍）。表の下端から下の枠まで
SV_BAR_S = 2                              # 2 倍で描いて縮小（斜めの縁・発光をなめらかに）
SV_BAR_Y0, SV_BAR_Y1 = 20, 86             # 帯の中のバー本体（上下）
SV_BAR_SLANT = 30                         # 左右の斜めカット（上辺が下辺より左右に長い）
SV_BAR_INSET = 34                         # 帯の左右端からバー上辺までの距離（外に緑の斜線を置く）

C_SVB_BAND_T  = (10, 44, 96)              # 帯の地：上（表の下の濃紺）
C_SVB_BAND_B  = (4, 18, 52)               # 帯の地：下
C_SVB_CYAN    = (58, 206, 238)            # シアンの発光線（表・スランプの枠と同じ）
C_SVB_FILL_C  = (84, 8, 50)               # バーの中央：黒〜濃いワイン
C_SVB_FILL_E  = (226, 24, 138)            # バーの上下端：マゼンタ
C_SVB_EDGE    = (255, 64, 178)            # ネオンピンクの縁
C_SVB_GREEN   = (40, 236, 96)             # 両端の斜線：グリーン
C_SVB_ICON    = (176, 238, 248)           # アイコン：白〜シアン
C_SVB_LABEL   = (255, 255, 255)           # 見出し「総差枚：」など
C_SVB_VALUE   = (255, 240, 250)           # 数値：白（ピンクの発光を重ねる）
C_SVB_GLOW    = (255, 40, 170)            # 数値の発光：ピンク
SZ_SVB_LABEL, SZ_SVB_VALUE, SZ_SVB_SUB = 30, 46, 28
SZ_SVB_ICON = 34


def _svb_lerp(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _svb_icon(d, kind: str, x: float, cy: float, sz: float, col):
    """白〜シアンの簡易アイコン（棒グラフ・人＋棒・ターゲット）。左端 x・縦中心 cy・一辺 sz。"""
    top, bot = cy - sz / 2, cy + sz / 2
    if kind == "bars":
        bw, gp = sz * 0.19, sz * 0.08
        for k, hr in enumerate((0.32, 0.5, 0.74, 1.0)):
            x0 = x + k * (bw + gp)
            d.rectangle([x0, bot - sz * hr, x0 + bw, bot], fill=col)
    elif kind == "avg":
        r = sz * 0.13
        d.ellipse([x + sz * 0.05, top + sz * 0.02, x + sz * 0.05 + 2 * r, top + sz * 0.02 + 2 * r], fill=col)
        d.rounded_rectangle([x, top + sz * 0.34, x + sz * 0.36, bot], radius=sz * 0.1, fill=col)
        bw, gp = sz * 0.17, sz * 0.07
        for k, hr in enumerate((0.55, 0.85)):
            x0 = x + sz * 0.44 + k * (bw + gp)
            d.rectangle([x0, bot - sz * hr, x0 + bw, bot], fill=col)
    else:  # target
        cx = x + sz / 2
        w_ = max(2, round(sz * 0.09))
        for rr in (0.5, 0.31):
            d.ellipse([cx - sz * rr, cy - sz * rr, cx + sz * rr, cy + sz * rr], outline=col, width=w_)
        d.ellipse([cx - sz * 0.11, cy - sz * 0.11, cx + sz * 0.11, cy + sz * 0.11], fill=col)
        d.line([(cx, cy), (cx + sz * 0.5, cy - sz * 0.5)], fill=col, width=w_)
        d.polygon([(cx + sz * 0.5, cy - sz * 0.5), (cx + sz * 0.26, cy - sz * 0.5), (cx + sz * 0.5, cy - sz * 0.26)], fill=col)
    return sz


def render_summary_band(summary: dict, width: int) -> Image.Image:
    """集計バーの帯（幅 width・高さ SV_BAR_BAND_H）を返す。

    summary = {"total": "+22,050枚", "avg": "+7,350枚", "rate": "100.0%", "count": "(3/3台)"}
    文字は省略・改行せず、収まらないときだけ全体を同じ比率で縮小する（装飾より数値の読みやすさを優先）。"""
    S = SV_BAR_S
    Wd, Hd = width * S, SV_BAR_BAND_H * S
    band = Image.new("RGB", (Wd, Hd), C_SVB_BAND_B)
    d = ImageDraw.Draw(band)
    for y in range(Hd):
        d.line([(0, y), (Wd, y)], fill=_svb_lerp(C_SVB_BAND_T, C_SVB_BAND_B, y / max(1, Hd - 1)))

    def _glow(draw_fn, color, radius, strength):
        """draw_fn(ImageDraw) で描いた形をぼかして color で重ねる（発光）。"""
        m = Image.new("L", (Wd, Hd), 0)
        draw_fn(ImageDraw.Draw(m))
        m = m.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: min(255, int(v * strength)))
        band.paste(Image.new("RGB", (Wd, Hd), color), (0, 0), m)

    # 上下のシアン発光線（表の下・スランプ領域の上と同じ色）
    _glow(lambda g: (g.line([(0, 2 * S), (Wd, 2 * S)], fill=255, width=4 * S),
                     g.line([(60 * S, Hd - 7 * S), (Wd - 60 * S, Hd - 7 * S)], fill=255, width=3 * S)),
          C_SVB_CYAN, 4 * S, 1.3)
    d = ImageDraw.Draw(band)
    d.line([(0, 1 * S), (Wd, 1 * S)], fill=C_SVB_CYAN, width=3 * S)
    d.line([(90 * S, Hd - 7 * S), (Wd - 90 * S, Hd - 7 * S)], fill=(150, 236, 250), width=1 * S)

    y0, y1 = SV_BAR_Y0 * S, SV_BAR_Y1 * S
    xl, xr = SV_BAR_INSET * S, Wd - SV_BAR_INSET * S
    sl = SV_BAR_SLANT * S
    poly = [(xl, y0), (xr, y0), (xr - sl, y1), (xl + sl, y1)]

    # 両端の外側：緑〜シアンの斜線 3 本（見本の左下・右下）
    for k in range(3):
        for side in (-1, 1):
            off = (k * 15 + 8) * S
            if side < 0:
                bx = xl + sl * 0.15 - off
                pts = [(bx - 9 * S, y0 + 22 * S), (bx, y0 + 22 * S), (bx + 26 * S, y1 + 8 * S), (bx + 17 * S, y1 + 8 * S)]
            else:
                bx = xr - sl * 0.15 + off
                pts = [(bx + 9 * S, y0 + 22 * S), (bx, y0 + 22 * S), (bx - 26 * S, y1 + 8 * S), (bx - 17 * S, y1 + 8 * S)]
            col = _svb_lerp(C_SVB_GREEN, C_SVB_CYAN, k / 2)
            _glow(lambda g, pts=pts: g.polygon(pts, fill=255), col, 3 * S, 0.9)
            ImageDraw.Draw(band).polygon(pts, fill=col)

    # バー本体：上下端マゼンタ → 中央の黒〜ワインのグラデーション
    fill = Image.new("RGB", (Wd, Hd))
    fd = ImageDraw.Draw(fill)
    for y in range(y0, y1 + 1):
        t = abs((y - y0) / max(1, y1 - y0) * 2 - 1)          # 中央 0 → 上下端 1
        fd.line([(0, y), (Wd, y)], fill=_svb_lerp(C_SVB_FILL_C, C_SVB_FILL_E, t ** 1.8))
    m = Image.new("L", (Wd, Hd), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    _glow(lambda g: g.polygon(poly, outline=255, width=5 * S), C_SVB_EDGE, 7 * S, 1.2)   # 外側の発光
    band.paste(fill, (0, 0), m)
    d = ImageDraw.Draw(band)
    d.polygon(poly, outline=C_SVB_EDGE, width=2 * S)
    # 左上・右上の小さなピンクの切り欠き装飾
    d.polygon([(xl - 6 * S, y0 - 7 * S), (xl + 46 * S, y0 - 7 * S), (xl + 40 * S, y0 - 2 * S), (xl - 1 * S, y0 - 2 * S)], fill=C_SVB_EDGE)
    d.polygon([(xr + 6 * S, y0 - 7 * S), (xr - 46 * S, y0 - 7 * S), (xr - 40 * S, y0 - 2 * S), (xr + 1 * S, y0 - 2 * S)], fill=C_SVB_EDGE)

    # ── 3 区画の文字（アイコン＋見出し＋数値）──
    secs = [("bars", "総差枚：", str(summary.get("total", "")), ""),
            ("avg", "平均：", str(summary.get("avg", "")), ""),
            ("target", "勝率：", str(summary.get("rate", "")), str(summary.get("count", "")))]
    in_x0, in_x1 = xl + sl + 14 * S, xr - sl - 14 * S        # 斜めカットの内側
    sep_w = 40 * S                                            # 区切り（斜線）に最低限とる幅

    def _measure(k):
        lf, vf, sf = _font(round(SZ_SVB_LABEL * S * k)), _font(round(SZ_SVB_VALUE * S * k)), _font(round(SZ_SVB_SUB * S * k))
        isz, igap = SZ_SVB_ICON * S * k, 10 * S * k
        ws = []
        for _ic, lab, val, sub in secs:
            w_ = isz + igap + d.textlength(lab, font=lf) + d.textlength(val, font=vf)
            if sub:
                w_ += 8 * S * k + d.textlength(sub, font=sf)
            ws.append(w_)
        return lf, vf, sf, isz, igap, ws

    k = 1.0
    lf, vf, sf, isz, igap, ws = _measure(k)
    while sum(ws) + sep_w * 2 > (in_x1 - in_x0) and k > 0.5:
        k -= 0.02
        lf, vf, sf, isz, igap, ws = _measure(k)
    free = (in_x1 - in_x0) - sum(ws)
    gap = free / 3                                           # 両端に gap/2・区画の間に gap
    cy = (y0 + y1) / 2
    vb = d.textbbox((0, 0), "0", font=vf)                    # 数字の高さで上下中央
    x = in_x0 + gap / 2
    text_layer = []
    for i, ((ic, lab, val, sub), w_) in enumerate(zip(secs, ws)):
        _svb_icon(d, ic, x, cy, isz, C_SVB_ICON)
        tx = x + isz + igap
        lb = d.textbbox((0, 0), "0", font=lf)
        d.text((tx, cy - (lb[1] + lb[3]) / 2), lab, font=lf, fill=C_SVB_LABEL)
        tx += d.textlength(lab, font=lf)
        text_layer.append((tx, cy - (vb[1] + vb[3]) / 2, val))
        tx += d.textlength(val, font=vf)
        if sub:
            sb = d.textbbox((0, 0), "0", font=sf)
            d.text((tx + 8 * S * k, cy - (sb[1] + sb[3]) / 2), sub, font=sf, fill=C_SVB_LABEL)
        x += w_
        if i < 2:                                           # 区切り：ピンクの細い斜線
            sx = x + gap / 2
            seg = [(sx + 12 * S, y0 + 10 * S), (sx - 12 * S, y1 - 10 * S)]
            _glow(lambda g, seg=seg: g.line(seg, fill=255, width=4 * S), C_SVB_EDGE, 3 * S, 1.0)
            d = ImageDraw.Draw(band)
            d.line(seg, fill=(255, 120, 200), width=1 * S + 1)
            x += gap
    # 数値：ピンクの発光 → 白文字
    _glow(lambda g: [g.text((tx_, ty_), v_, font=vf, fill=255) for tx_, ty_, v_ in text_layer], C_SVB_GLOW, 5 * S, 1.6)
    d = ImageDraw.Draw(band)
    for tx_, ty_, v_ in text_layer:
        d.text((tx_, ty_), v_, font=vf, fill=C_SVB_VALUE)
    return band.resize((width, SV_BAR_BAND_H), Image.LANCZOS)


# ═══════════════════════════════════════════════════════════════════════════
# スランプグラフ（スロバース用 × スランプ付き結果 other_slump だけ・2026-11-06 試作）
#   streamlit_app.py の draw_slump_graph() / _attach_slump_to_table() /
#   _attach_slump_to_table_side() が _sloverse_slump_on() のときだけ呼ぶ。
#   カードの中身は「機種名・台番・差枚・スランプグラフ」の4要素だけ（G数は入れない）。
# ═══════════════════════════════════════════════════════════════════════════
SL_S = 2                                  # カードは 2 倍解像度で描き、並べるときに縮小する
SL_CARD_W, SL_CARD_H = 466, 330           # 1 倍換算のカード寸法（3 列で表の内幅に収まる）
SL_NAME_H = 52                            # 機種名の帯
SL_INFO_H = 50                            # 台番・差枚の行
SL_RADIUS = 10
SL_GAP = 22                               # カードの間隔・表との間隔
SL_TAIL_H = 120                           # render_table の下端から下の枠（frame_bottom の表下端以降）
# 縦軸は固定目盛り（2026-11-11）：+5,000〜-1,000 を 1,000 枚ごとに 7 本。表記は +5,000 と 0 だけ・0 だけ実線。
# 台ごとの自動拡大はしない（他店舗のスランプと同じく 1,000 枚あたりの高さは固定）。
SL_Y_TOP, SL_Y_BOT, SL_Y_STEP = 5000, -1000, 1000
SL_Y_LABELS = {5000: "+5,000", 0: "0"}
SL_GRID_PAD_T = 44                        # 台番行の下端〜+5,000 の線（上へはみ出す線の余白・1 倍）
SL_GRID_PAD_B = 30                        # -1,000 の線〜カード下端（下へはみ出す線の余白・1 倍）
SL_DASH = (7, 5)                          # 点線：線・すき間（1 倍）

C_SL_FRAME    = (58, 206, 238)            # カード外枠：シアン（見出しバーの区切りと同じ）
C_SL_NAME_T   = (22, 104, 176)            # 機種名の帯：上
C_SL_NAME_B   = (6, 38, 92)               # 機種名の帯：下
C_SL_GRAPH_BG = (6, 22, 56)               # グラフ地：ネイビー
C_SL_GRID     = (34, 78, 128)             # 補助線
C_SL_ZERO     = (120, 205, 245)           # 0 ライン
C_SL_LABEL    = (150, 200, 232)           # 目盛文字
C_SL_LINE     = (57, 255, 20)             # 折れ線：蛍光グリーン
C_SL_AREA_BG  = (226, 241, 252)           # カードを並べる領域の地（表のセルより少し濃い水色）


def _sl_dash(d, x0: float, x1: float, y: float, fill, width: int, dash: int, gap: int) -> None:
    """横の点線（x0→x1）。"""
    x = x0
    while x < x1:
        d.line([(x, y), (min(x + dash, x1), y)], fill=fill, width=width)
        x += dash + gap


def render_slump_card(unit_id: str, machine_name: str, points: list,
                      diff_text: str | None, diff_sign: int = 0) -> Image.Image:
    """スランプカード1枚（2 倍解像度 932×660）。

    diff_text が None のときは差枚を出さない（既存の show_diff=False と同じ扱い）。
    縦軸は固定目盛り：+5,000〜-1,000 を 1,000 枚ごとに 7 本（表記は +5,000 と 0 だけ・0 だけ実線・他は点線）。
    台ごとに目盛りを広げず、+5,000 を超える／-1,000 を下回る線はグラフ地（台番行の下〜カード下端）の中で
    目盛りの外へはみ出して描く（他店舗のスランプと同じ考え方）。"""
    S = SL_S
    W_, H_ = SL_CARD_W * S, SL_CARD_H * S
    card = Image.new("RGB", (W_, H_), C_SL_AREA_BG)
    mask = Image.new("L", (W_, H_), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W_ - 1, H_ - 1], radius=SL_RADIUS * S, fill=255)
    body = Image.new("RGB", (W_, H_), C_SL_GRAPH_BG)
    d = ImageDraw.Draw(body)

    # ── 機種名の帯（上→下のグラデーション・白文字）──
    nh, ih = SL_NAME_H * S, SL_INFO_H * S
    for y in range(nh):
        t = y / max(1, nh - 1)
        d.line([(0, y), (W_, y)], fill=tuple(round(C_SL_NAME_T[i] + (C_SL_NAME_B[i] - C_SL_NAME_T[i]) * t) for i in range(3)))
    n_lines, nf = _layout_fit(d, str(machine_name), W_ - 28 * S, nh - 6 * S, 30 * S, 20 * S, 20 * S, 14 * S)
    _draw_lines(d, W_ / 2, nh / 2, n_lines, nf, (255, 255, 255))

    # ── 台番・差枚の行（表のセルと同じ地・緑三角＋台番／右に差枚）──
    y0, y1 = nh, nh + ih
    d.rectangle([(0, y0), (W_, y1 - 1)], fill=C_ROW_BG)
    d.line([(0, y0), (W_, y0)], fill=C_SL_FRAME, width=2 * S)
    d.line([(0, y1 - 2 * S), (W_, y1 - 2 * S)], fill=C_SL_FRAME, width=2 * S)
    tri = 26 * S
    tx, ty = 14 * S, y0 + (ih - tri) // 2
    d.polygon([(tx, ty), (tx + tri, ty), (tx, ty + tri)], fill=C_TRI)
    bf = _font(32 * S)
    _draw_text(d, (0, y0, W_, y1), f"{unit_id}番台", bf, C_TEXT, "left", left_x=tx + tri + 12 * S)
    if diff_text:
        df_ = _fit_font(d, diff_text, 34 * S, W_ // 2)
        fill = C_PLUS if diff_sign > 0 else (C_MINUS if diff_sign < 0 else C_TEXT)
        _draw_text(d, (0, y0, W_, y1), diff_text, df_, fill, "right", right_pad=16 * S)

    # ── グラフ（ネイビー地・固定目盛り 7 本・0 ラインだけ実線・蛍光グリーンの折れ線）──
    gx0, gx1 = 82 * S, W_ - 18 * S
    gy0, gy1 = y1 + SL_GRID_PAD_T * S, H_ - SL_GRID_PAD_B * S     # +5,000 の線 / -1,000 の線
    lf = _font(16 * S)
    def _y(v: float) -> float:
        return gy0 + (SL_Y_TOP - v) / (SL_Y_TOP - SL_Y_BOT) * (gy1 - gy0)
    for v in range(SL_Y_TOP, SL_Y_BOT - 1, -SL_Y_STEP):
        yy = _y(v)
        if v == 0:
            d.line([(gx0, yy), (gx1, yy)], fill=C_SL_ZERO, width=2 * S)
        else:
            _sl_dash(d, gx0, gx1, yy, C_SL_GRID, 2 * S, SL_DASH[0] * S, SL_DASH[1] * S)
        lab = SL_Y_LABELS.get(v)
        if lab:
            bb = d.textbbox((0, 0), lab, font=lf)
            d.text((gx0 - 8 * S - bb[2], round(yy - (bb[1] + bb[3]) / 2)), lab, font=lf, fill=C_SL_LABEL)
    d.line([(gx0, gy0), (gx0, gy1)], fill=C_SL_GRID, width=1 * S)

    pts = points or []
    if len(pts) >= 2:
        max_x = max(float(p.get("x", 0)) for p in pts)
        if max_x > 0:
            xy = [(gx0 + float(p["x"]) / max_x * (gx1 - gx0), _y(float(p["y"]))) for p in pts]
            # 目盛りの外へはみ出した線もグラフ地（台番行の下端〜カード下端）の中は描く。台番・差枚の行には重ねない
            area = Image.new("L", (W_, H_), 0)
            ImageDraw.Draw(area).rectangle([0, y1, W_, H_], fill=255)
            glow = Image.new("L", (W_, H_), 0)
            ImageDraw.Draw(glow).line(xy, fill=255, width=10 * S, joint="curve")
            glow = glow.filter(ImageFilter.GaussianBlur(5 * S))
            glow = ImageChops.multiply(glow.point(lambda a: int(a * 0.45)), area)
            body.paste(Image.new("RGB", (W_, H_), C_SL_LINE), (0, 0), glow)
            lm = Image.new("L", (W_, H_), 0)
            ImageDraw.Draw(lm).line(xy, fill=255, width=4 * S, joint="curve")
            body.paste(Image.new("RGB", (W_, H_), C_SL_LINE), (0, 0), ImageChops.multiply(lm, area))
            d = ImageDraw.Draw(body)

    card.paste(body, (0, 0), mask)
    ImageDraw.Draw(card).rounded_rectangle([1, 1, W_ - 2, H_ - 2], radius=SL_RADIUS * S,
                                           outline=C_SL_FRAME, width=3 * S)
    return card


def _sl_grid(cards: list, cols: int, area_w: int) -> tuple[Image.Image, int]:
    """カードを cols 列・左詰めで並べた領域（地は C_SL_AREA_BG）。戻り値: (画像, 高さ)。"""
    cell_w = (area_w - SL_GAP * (cols - 1)) // cols
    sc = [c.resize((cell_w, max(1, round(c.height * cell_w / c.width))), Image.LANCZOS) for c in cards]
    row_h = max(c.height for c in sc)
    rows = -(-len(sc) // cols)
    h = SL_GAP + rows * row_h + (rows - 1) * SL_GAP + SL_GAP
    area = Image.new("RGB", (area_w, h), C_SL_AREA_BG)
    x_off = (area_w - (cell_w * cols + SL_GAP * (cols - 1))) // 2
    for i, c in enumerate(sc):
        r, k = divmod(i, cols)                           # 左→右、次の行も左→右（Z 型）・最後の行は左詰め
        area.paste(c, (x_off + k * (cell_w + SL_GAP), SL_GAP + r * (row_h + SL_GAP)))
    return area, h


def _sl_frame_panel(area: Image.Image, top_cap: Image.Image, tail: Image.Image) -> Image.Image:
    """area を水色の枠（左右の帯＋上下の枠）で囲んだパネル。幅は W 固定。"""
    mid = Image.open(os.path.join(ASSET_DIR, "frame_mid.png")).convert("RGB")
    h = top_cap.height + area.height + tail.height
    out = Image.new("RGB", (W, h), (12, 61, 111))
    out.paste(top_cap, (0, 0))
    out.paste(mid.resize((W, area.height), Image.BICUBIC), (0, top_cap.height))
    out.paste(area, (TABLE_X0, top_cap.height))
    out.paste(tail, (0, top_cap.height + area.height))
    return out


def attach_slumps(table_img: Image.Image, cards: list, cols: int = 3) -> Image.Image:
    """表画像（render_table の出力）の下へ、同じ枠の中でスランプを cols 列に並べる。

    表の下端（下の枠の直前）で切り、左右の帯を伸ばした中にカードを置いて、下の枠を付け直す。
    幅が W でない画像（スロバース表ではない画像）は、表の下へ同じデザインのパネルを足す。"""
    if not cards:
        return table_img.copy()
    tw, th = table_img.size
    area, ah = _sl_grid(cards, cols, TABLE_X1 - TABLE_X0)
    if tw == W and th > SL_TAIL_H:
        head = table_img.crop((0, 0, W, th - SL_TAIL_H))
        tail = table_img.crop((0, th - SL_TAIL_H, W, th))
        mid = Image.open(os.path.join(ASSET_DIR, "frame_mid.png")).convert("RGB")
        out = Image.new("RGB", (W, head.height + ah + SL_TAIL_H), (12, 61, 111))
        out.paste(head, (0, 0))
        out.paste(mid.resize((W, ah), Image.BICUBIC), (0, head.height))
        out.paste(area, (TABLE_X0, head.height))
        ImageDraw.Draw(out).line([(TABLE_X0, head.height), (TABLE_X1 - 1, head.height)], fill=C_SL_FRAME, width=3)
        out.paste(tail, (0, head.height + ah))
        return out
    bottom = Image.open(os.path.join(ASSET_DIR, "frame_bottom.png")).convert("RGB")
    tail = bottom.crop((0, BOTTOM_OVERLAP, W, bottom.height))
    panel = _sl_frame_panel(area, tail.transpose(Image.FLIP_TOP_BOTTOM), tail)
    panel = panel.resize((tw, max(1, round(panel.height * tw / W))), Image.LANCZOS)
    out = Image.new("RGB", (tw, th + panel.height), (255, 255, 255))
    out.paste(table_img, (0, 0))
    out.paste(panel, (0, th))
    return out


def attach_slumps_side(table_img: Image.Image, cards: list, cols: int = 4) -> Image.Image:
    """16 台以上の横版：左に表、右に同じ枠のスランプパネル（cols 列）。高さは高いほうに合わせる。"""
    if not cards:
        return table_img.copy()
    tw, th = table_img.size
    bottom = Image.open(os.path.join(ASSET_DIR, "frame_bottom.png")).convert("RGB")
    tail = bottom.crop((0, BOTTOM_OVERLAP, W, bottom.height))
    cap = tail.transpose(Image.FLIP_TOP_BOTTOM)
    area, ah = _sl_grid(cards, cols, TABLE_X1 - TABLE_X0)
    panel_h = cap.height + ah + tail.height
    total_h = max(th, panel_h)
    if total_h > ah + cap.height + tail.height:                   # 表のほうが高い：地を伸ばして上下中央
        pad = total_h - panel_h
        big = Image.new("RGB", (TABLE_X1 - TABLE_X0, ah + pad), C_SL_AREA_BG)
        big.paste(area, (0, pad // 2))
        area = big
    panel = _sl_frame_panel(area, cap, tail)
    if th < total_h:                                               # パネルのほうが高い：表を縦横比維持で拡大
        table_img = table_img.resize((max(1, round(tw * total_h / th)), total_h), Image.LANCZOS)
    out = Image.new("RGB", (table_img.width + W, total_h), (12, 61, 111))
    out.paste(table_img, (0, 0))
    out.paste(panel, (table_img.width, 0))
    return out


SL_SPLIT_COLS = 8                         # 40台以上の分割画像：下部の共通スランプ領域の列数
SL_SPLIT_TGAP = 24                        # 分割画像：左右の表の間隔（2倍キャンバス上の px）


def attach_slumps_split(table_img: Image.Image, cards: list, row_bans: list, cols: int = SL_SPLIT_COLS):
    """40台以上の「その他の優秀台ピックアップ」：3段構成の1枚（幅 W）。

      上段：共通のタイトルバー（画像全体の中央に1つ）
      中段：表を前半・後半に分けて左右に並べる（右の表にも同じ列見出しバー）
      下段：全台のスランプを1つの共通領域に cols 列（左→右、次の行も左→右・最後の行は左詰め）

    幅 2W のキャンバスで組み、最後に W へ縮小する。外枠（上の枠・左右の帯・下の枠）は
    表画像と同じ素材を 2 倍にして使うので、縮小後は通常のスロバース画像と同じ太さになる。
    スランプの並びは表と同じ順（row_bans の順＝台番の若い順）。前半は ceil(行数/2) 行。
    行数と row_bans の数が合わない・台番の無いカード・表に無い台のカードがあるときは None
    （呼び出し側で従来の1ブロック）。"""
    tw, th = table_img.size
    if tw != W or th <= SL_TAIL_H or not cards:
        return None
    table_y1 = th - SL_TAIL_H
    n = round((table_y1 - HEADER_Y1) / ROW_PITCH)
    if n != len(row_bans) or HEADER_Y1 + round(n * ROW_PITCH) != table_y1:
        return None
    order = {str(b): i for i, b in enumerate(row_bans)}
    units = [c.info.get("sv_unit") for c in cards]
    if any(u is None or str(u) not in order for u in units):
        return None
    cards = [c for _, c in sorted(zip(units, cards), key=lambda t: order[str(t[0])])]
    k = -(-n // 2)
    y_k = HEADER_Y1 + round(k * ROW_PITCH)

    S2 = 2
    WW = W * S2
    fx0, fx1 = TABLE_X0 * S2, WW - (W - TABLE_X1) * S2           # 2倍キャンバスでの内側の左右端
    inner_w = fx1 - fx0
    # 上段：表画像の上端〜見出しバーの直前（タイトル台座と上の枠）を 2 倍に
    top = table_img.crop((0, 0, W, HEADER_Y0)).resize((WW, HEADER_Y0 * S2), Image.LANCZOS)
    tail = table_img.crop((0, table_y1, W, th)).resize((WW, SL_TAIL_H * S2), Image.LANCZOS)
    # 中段：左＝見出し＋前半の行、右＝同じ見出し＋後半の行（左右の帯は除いた内側だけ）
    hdr = table_img.crop((TABLE_X0, HEADER_Y0, TABLE_X1, HEADER_Y1))
    l_rows = table_img.crop((TABLE_X0, HEADER_Y1, TABLE_X1, y_k))
    r_rows = table_img.crop((TABLE_X0, y_k, TABLE_X1, table_y1))
    def _stack(a, b):
        im = Image.new("RGB", (a.width, a.height + b.height), C_SL_AREA_BG)
        im.paste(a, (0, 0)); im.paste(b, (0, a.height))
        return im
    t_w = (inner_w - SL_SPLIT_TGAP) // 2
    l_tbl = _stack(hdr, l_rows); r_tbl = _stack(hdr, r_rows)
    l_tbl = l_tbl.resize((t_w, max(1, round(l_tbl.height * t_w / l_tbl.width))), Image.LANCZOS)
    r_tbl = r_tbl.resize((t_w, max(1, round(r_tbl.height * t_w / r_tbl.width))), Image.LANCZOS)
    tables_h = max(l_tbl.height, r_tbl.height)
    # 下段：全台のスランプを cols 列で
    area, ah = _sl_grid(cards, cols, inner_w)

    body_h = tables_h + ah
    H2 = top.height + body_h + tail.height
    mid = Image.open(os.path.join(ASSET_DIR, "frame_mid.png")).convert("RGB")
    out = Image.new("RGB", (WW, H2), (12, 61, 111))
    out.paste(top, (0, 0))
    out.paste(mid.resize((WW, body_h), Image.BICUBIC), (0, top.height))
    out.paste(Image.new("RGB", (inner_w, body_h), C_SL_AREA_BG), (fx0, top.height))
    out.paste(l_tbl, (fx0, top.height))
    out.paste(r_tbl, (fx1 - t_w, top.height))
    y_area = top.height + tables_h
    out.paste(area, (fx0, y_area))
    ImageDraw.Draw(out).line([(fx0, y_area), (fx1 - 1, y_area)], fill=C_SL_FRAME, width=3 * S2)
    out.paste(tail, (0, top.height + body_h))
    return out.resize((W, max(1, round(H2 * W / WW))), Image.LANCZOS)
