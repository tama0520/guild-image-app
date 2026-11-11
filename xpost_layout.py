"""スロバース用：X投稿用の画像結合（最大4枚）。

⑥プレビューの素材画像（表・スランプ付きの表・_side など）を、1枚あたり横1〜4列に
並べて最大4枚の完成画像にする。

★素材は等倍（100%）で並べる。素材ごとの拡大・縮小はしない（列の高さをそろえるための
  サイズ変更もしない）。列の幅は「その列で一番幅の広い素材の幅＋列の余白（pad）」で、
  幅の狭い素材は列の中央に置く。列の高さが違う分は背景色のまま残す（余白として見える）。
★完成画像の長辺が MAX_LONG を超えるときだけ、完成画像全体を同じ倍率で一括縮小する。
  切り抜き・引き伸ばし・重ね合わせはしない。

レイアウトの形（JSON）:
    {"frames": [ {"cols": [ {"items": [素材ID, ...], "pad": 0}, ... ]}, × 4 ]}
    - 素材IDは連番 NN_ を外したファイル名（例「戦国乙女4.jpg」「末尾1番台の優秀台_side.jpg」）
    - pad は列の幅に足す余白（px・0以上）。素材の大きさは変えない
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
import shutil
from datetime import datetime

from PIL import Image

N_FRAMES = 4
MAX_COLS = 4
GAP = 6                      # 素材どうしの隙間（px・完成画像の寸法）
BG = (255, 255, 255)         # （旧）白地。今は make_background() の近未来背景で埋める
# 余白の背景（スロバース画像になじむ近未来の回路基板風・控えめ）。
# 乱数は固定シード（寸法ごとに決まる）なので、同じ寸法なら毎回まったく同じ背景になる。
BG_TOP = (18, 58, 120)       # 上端の地色（青）
BG_BOTTOM = (34, 104, 178)   # 下端の地色（ライトブルー寄り）
BG_GLOW = (88, 160, 226)     # 斜めに差すやわらかい光
CIR_CYAN = (80, 220, 255)    # 回路線：シアン（基本）
CIR_GREEN = (90, 255, 140)   # 回路線：ネオングリーン（基本）
CIR_RED = (255, 80, 96)      # 回路線：レッド（アクセント・少量）
BG_SEED = 20261109
RENDER_VERSION = "bg-future-3"  # 背景の見た目を変えたら更新（画面の完成プレビューの作り直し用）
MAX_LONG = 4096              # 完成画像の長辺の上限（X の画像の上限）
MAX_BYTES = 4_800_000        # JPEG の上限（X は 5MB まで）
JPEG_QUALITIES = (92, 90, 88, 86, 84)
PAD_MAX = 2000               # 列の余白（pad）の上限
WARN_SCALE = 0.5             # これより小さい一括縮小率は「文字が小さい」警告
SEG_MAX = 16                 # 自動配置で1枚に入れる素材数の上限


def bare(fn: str) -> str:
    """連番 NN_ を外した素材ID。"""
    return re.sub(r"^\d{2}_", "", fn)


def empty_layout() -> dict:
    return {"frames": [{"cols": [{"items": [], "pad": 0}]} for _ in range(N_FRAMES)]}


def normalize_layout(layout, ids) -> dict:
    """存在しない素材・重複を外し、4枠・各1〜4列の形にそろえる（並び順は保つ）。"""
    ids = set(ids)
    seen: set = set()
    frames = []
    for fr in list((layout or {}).get("frames") or [])[:N_FRAMES]:
        cols = []
        for c in list((fr or {}).get("cols") or [])[:MAX_COLS]:
            items = []
            for i in (c or {}).get("items") or []:
                if i in ids and i not in seen:
                    items.append(i)
                    seen.add(i)
            # 旧形式の列幅比率（w）は使わない（素材を拡大縮小しない方式へ変えたため）
            pad = (c or {}).get("pad")
            pad = int(min(PAD_MAX, max(0, pad))) if isinstance(pad, (int, float)) and not isinstance(pad, bool) else 0
            cols.append({"items": items, "pad": pad})
        frames.append({"cols": cols or [{"items": [], "pad": 0}]})
    while len(frames) < N_FRAMES:
        frames.append({"cols": [{"items": [], "pad": 0}]})
    return {"frames": frames}


def placed_ids(layout) -> list:
    return [i for fr in layout["frames"] for c in fr["cols"] for i in c["items"]]


def layout_hash(layout, sizes: dict) -> str:
    """配置と、配置した素材の寸法から作る指紋（確定済みかどうかの判定に使う）。"""
    used = placed_ids(layout)
    # 完成画像に影響しない「空の列・空の枠」は指紋に含めない（列数ボタンだけで未確定に戻さない）
    canon = [[{"items": c["items"], "pad": int(c.get("pad") or 0)} for c in fr["cols"] if c["items"]]
             for fr in layout["frames"]]
    canon = [f for f in canon if f]
    src = json.dumps({"layout": canon, "sizes": {i: list(sizes.get(i, (0, 0))) for i in used}},
                     ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(src.encode("utf-8")).hexdigest()[:16]


# ── 1枚分の寸法計算 ─────────────────────────────────────────────
def plan_frame(cols: list, sizes: dict) -> "dict | None":
    """列ごとの素材から完成画像の寸法と各素材の位置（等倍の座標）を求める。空の枠は None。

    - 素材は等倍で、列の中で上から GAP 間隔で積む（幅の狭い素材は列の中央）
    - 列の幅＝その列で一番幅の広い素材の幅＋pad
    - 完成画像の高さ＝一番高い列。ほかの列の下は背景色（余白）
    - 長辺が MAX_LONG を超えるときだけ、完成画像全体を同じ倍率 f で一括縮小
    """
    cols = [c for c in cols if c.get("items")]
    if not cols:
        return None
    k = len(cols)
    colw = [max(sizes[i][0] for i in c["items"]) + int(c.get("pad") or 0) for c in cols]
    place, x, col_h = [], 0, []
    for c, col in enumerate(cols):
        y = 0
        for n, i in enumerate(col["items"]):
            w0, h0 = sizes[i]
            place.append((i, x + (colw[c] - w0) // 2, y, w0, h0))
            y += h0 + (GAP if n < len(col["items"]) - 1 else 0)
        col_h.append(y)
        x += colw[c] + (GAP if c < k - 1 else 0)
    native_w, native_h = x, max(col_h)
    f = min(1.0, MAX_LONG / float(max(native_w, native_h)))
    width = max(1, int(round(native_w * f)))
    height = max(1, int(round(native_h * f)))
    if max(width, height) > MAX_LONG:          # 丸めで1px超えたとき
        f = (MAX_LONG - 0.5) / float(max(native_w, native_h))
        width, height = max(1, int(round(native_w * f))), max(1, int(round(native_h * f)))
    item_area = sum(p[3] * p[4] for p in place)
    blank = max(0.0, 1.0 - item_area / float(native_w * native_h))
    return {"width": width, "height": height, "native_w": native_w, "native_h": native_h,
            "place": place, "scales": {p[0]: f for p in place}, "blank": blank,
            "downscale": f, "col_w": colw, "col_h": col_h}


def _bg_color(rnd) -> tuple:
    v = rnd.random()
    return CIR_CYAN if v < 0.55 else (CIR_GREEN if v < 0.90 else CIR_RED)


def make_background(w: int, h: int, occupied=()) -> Image.Image:
    """結合後キャンバスの地（余白・隙間に見える部分）。素材を貼る前に敷くだけで、素材には重ねない。

    青→ライトブルーの縦グラデーション＋斜めのやわらかい光＋薄い方眼＋
    キャンバス全体に1本ずつ引く回路線（シアン・グリーン中心、レッドは少量）。
    一部の線だけ強く発光させ、光の頭（明るい点）と後ろの残光・前の淡い光で
    「回路を光が流れている」ように見せる（静止画）。タイルの繰り返しは使わない。

    occupied：素材を貼る範囲 [(x0, y0, x1, y1), ...]（この画像の座標）。素材に隠れる所へ線を
    使わず、見える余白（列の下・右下・左下など）へ回路線と発光を集める。余白の広さに比例して
    本数が増え、6pxの隙間のような細い所には詰め込まない。乱数は固定シードなので、
    同じ寸法・同じ配置なら毎回同じ背景になる。"""
    import random
    from PIL import ImageDraw, ImageFilter, ImageChops
    rnd = random.Random(f"{BG_SEED}:{w}x{h}")
    # 1) 地色：縦グラデーション＋斜めの光
    grad = Image.new("RGB", (1, 256))
    for y in range(256):
        t = y / 255.0
        grad.putpixel((0, y), tuple(int(round(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t)) for c in range(3)))
    canvas = grad.resize((w, h), Image.BILINEAR)
    lm = Image.new("L", (64, 64), 0)
    ImageDraw.Draw(lm).polygon([(0, 18), (64, 0), (64, 22), (0, 44)], fill=70)
    lm = lm.filter(ImageFilter.GaussianBlur(9)).resize((w, h), Image.BILINEAR)
    canvas = Image.composite(Image.new("RGB", (w, h), BG_GLOW), canvas, lm)
    # 2) 薄い方眼（全面・ごく薄く）
    lines = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lines)
    step = 36
    for v in range(0, w, step):
        d.line([(v, 0), (v, h)], fill=CIR_CYAN + ((14 if v % (step * 4) == 0 else 7),))
    for v in range(0, h, step):
        d.line([(0, v), (w, v)], fill=CIR_CYAN + ((14 if v % (step * 4) == 0 else 7),))
    # 3) 回路線（方眼に沿って縦横に走る・直角と45度の折れ）
    #    キャンバスを CELL 四方のマスに分け、マスごとに「見えている割合」を測る。
    #    見える余白のマスには1〜2本ずつ必ず線を置き（偏らないよう全マスに配る）、
    #    素材に隠れるマスには少しだけ置く（6pxの隙間から少し見える程度）。
    grid = 18
    CELL = 150
    vis = Image.new("L", (w, h), 255)
    if occupied:
        vd = ImageDraw.Draw(vis)
        for x0, y0, x1, y1 in occupied:
            vd.rectangle([x0, y0, x1 - 1, y1 - 1], fill=0)
    nx, ny = max(1, -(-w // CELL)), max(1, -(-h // CELL))
    vcell = vis.resize((nx, ny), Image.BOX)

    def _free(px, py):
        return 0 <= px < w and 0 <= py < h and vis.getpixel((int(px), int(py))) > 0

    # 色は「袋」から順に取り出して偏りを防ぐ（シアン・グリーン中心、レッドは7本に1本）
    bag: list = []

    def _pick_color():
        if not bag:
            bag.extend([CIR_CYAN, CIR_CYAN, CIR_CYAN, CIR_GREEN, CIR_GREEN, CIR_GREEN, CIR_RED])
            rnd.shuffle(bag)
        return bag.pop()

    def _trace(x, y, short):
        pts = [(x, y)]
        horiz = rnd.random() < 0.5
        for _ in range(rnd.randint(2, 5) if short else rnd.randint(2, 6)):
            L = rnd.randrange(grid * 2, grid * (8 if short else 14), grid)
            sgn = rnd.choice((-1, 1))
            if rnd.random() < 0.25:                      # 45度の面取り
                x += sgn * L // 2; y += rnd.choice((-1, 1)) * L // 2
            elif horiz:
                x += sgn * L
            else:
                y += sgn * L
            horiz = not horiz
            pts.append((x, y))
        return pts

    traces = []
    for cy in range(ny):
        for cx in range(nx):
            v = vcell.getpixel((cx, cy)) / 255.0
            if v >= 0.35:                                 # 見える余白のマス
                n = 1 + (rnd.random() < 0.35 * v)
                focus = True
            else:                                         # 素材に隠れるマス（ごく少なく）
                n = 1 if rnd.random() < 0.10 else 0
                focus = False
            for _ in range(n):
                # マスの中で「見えている点」を始点にする（最大8回探す）
                x = y = None
                for _ in range(8):
                    tx = cx * CELL + rnd.randrange(0, CELL, grid)
                    ty = cy * CELL + rnd.randrange(0, CELL, grid)
                    if not focus or _free(tx, ty):
                        x, y = tx, ty
                        break
                if x is None:
                    continue
                pts = _trace(x, y, short=focus)
                col = _pick_color()
                strong = rnd.random() < (0.30 if focus else 0.10)   # 一部だけ強く発光させる線
                wd = rnd.choice((1, 1, 1, 2, 2, 3)) + (1 if strong else 0)
                al = rnd.randint(80, 125) if strong else rnd.randint(40, 85)
                if col == CIR_RED:                         # 赤は本数が少ない分、少しだけはっきり
                    al = min(255, al + 35)
                traces.append((pts, col, strong, wd, focus))
                d.line(pts, fill=col + (al,), width=wd, joint="curve")
                for px, py in (pts[0], pts[-1]):          # 端子（小さな輪）
                    rr = 2 + wd
                    d.ellipse([px - rr, py - rr, px + rr, py + rr], outline=col + (min(255, al + 30),), width=1)
    canvas = Image.alpha_composite(canvas.convert("RGBA"), lines).convert("RGB")
    # 4) 発光（半分の解像度で描いてぼかし、拡大してスクリーン合成）
    gw, gh = max(1, w // 2), max(1, h // 2)
    glow = Image.new("RGB", (gw, gh), (0, 0, 0))
    core = Image.new("RGB", (gw, gh), (0, 0, 0))
    gd, cd = ImageDraw.Draw(glow), ImageDraw.Draw(core)

    def _dim(c, k):
        return tuple(int(v * k) for v in c)

    for pts, col, strong, wd, focus in traces:
        hp = [(px / 2.0, py / 2.0) for px, py in pts]
        if strong:                                        # 線全体のうっすらした発光
            gd.line(hp, fill=_dim(col, 0.35), width=wd + 3)
        # 発光ポイント（端子や折れ点の一部）。見える余白の線は始点を必ず光らせる
        for k, (px, py) in enumerate(hp):
            if (focus and k == 0 and rnd.random() < 0.5) or rnd.random() < (0.35 if strong else 0.06):
                r = rnd.uniform(2.0, 4.5)
                kr = 0.65 if col == CIR_RED else 1.0       # 赤の光は少し控えめ（アクセント）
                gd.ellipse([px - r * 2, py - r * 2, px + r * 2, py + r * 2], fill=_dim(col, 0.55 * kr))
                cd.ellipse([px - r * 0.6, py - r * 0.6, px + r * 0.6, py + r * 0.6], fill=_dim(col, 0.9 * kr))
        if not strong:
            continue
        # 光の軌跡：線の途中に「光の頭」を置き、後ろへ残光、前へ淡い光
        seg = rnd.randrange(len(hp) - 1)
        (x1, y1), (x2, y2) = hp[seg], hp[seg + 1]
        t = rnd.uniform(0.35, 0.95)
        hx, hy = x1 + (x2 - x1) * t, y1 + (y2 - y1) * t
        n = 18
        for k in range(n):                               # 後ろの残光（だんだん弱く）
            a0, a1 = t * (1 - k / n), t * (1 - (k + 1) / n)
            p0 = (x1 + (x2 - x1) * a0, y1 + (y2 - y1) * a0)
            p1 = (x1 + (x2 - x1) * a1, y1 + (y2 - y1) * a1)
            kk = (1 - k / n) ** 1.6
            gd.line([p0, p1], fill=_dim(col, 0.95 * kk), width=wd + 5)
            cd.line([p0, p1], fill=_dim(col, 0.9 * kk), width=wd)
        ahead = min(1.0, t + 0.12)                        # 前の淡い光
        gd.line([(hx, hy), (x1 + (x2 - x1) * ahead, y1 + (y2 - y1) * ahead)], fill=_dim(col, 0.3), width=wd + 3)
        R = rnd.uniform(4.0, 7.0)                         # 光の頭
        gd.ellipse([hx - R * 2.2, hy - R * 2.2, hx + R * 2.2, hy + R * 2.2], fill=_dim(col, 0.9))
        cd.ellipse([hx - R * 0.55, hy - R * 0.55, hx + R * 0.55, hy + R * 0.55], fill=(235, 255, 255))
    glow = glow.filter(ImageFilter.GaussianBlur(5)).resize((w, h), Image.BILINEAR)
    core = core.filter(ImageFilter.GaussianBlur(1.2)).resize((w, h), Image.BILINEAR)
    canvas = ImageChops.screen(canvas, glow)
    canvas = ImageChops.screen(canvas, core)
    return canvas


def render_frame(geom: dict, images: dict) -> Image.Image:
    """等倍で貼り合わせてから、必要なときだけ完成画像全体を一括縮小する。
    地は make_background()（余白・隙間に見える部分だけ。素材の中身には重ねない）。"""
    # 背景は出力の大きさで描いてから等倍キャンバスへ合わせる（一括縮小後に線の太さ・光が同じ見え方になるように）
    _f = geom["width"] / float(geom["native_w"])
    _occ = [(int(x * _f), int(y * _f), int(round((x + w) * _f)), int(round((y + h) * _f)))
            for _i, x, y, w, h in geom["place"]]
    canvas = make_background(geom["width"], geom["height"], _occ)
    if canvas.size != (geom["native_w"], geom["native_h"]):
        canvas = canvas.resize((geom["native_w"], geom["native_h"]), Image.BICUBIC)
    for i, x, y, w, h in geom["place"]:
        im = images[i]
        if im.mode != "RGB":
            im = im.convert("RGB")
        if im.size != (w, h):           # 寸法が違う素材は使わない（呼び出し側で寸法を確認済み）
            raise ValueError(f"素材の寸法が違います: {i} {im.size} != {(w, h)}")
        canvas.paste(im, (x, y))
    if (geom["width"], geom["height"]) != canvas.size:
        canvas = canvas.resize((geom["width"], geom["height"]), Image.LANCZOS)
    return canvas


def encode_jpeg(img: Image.Image) -> tuple[bytes, int]:
    """X に載せられる大きさまで品質を下げる（下げすぎない）。"""
    data, q = b"", JPEG_QUALITIES[0]
    for q in JPEG_QUALITIES:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=q, optimize=True, subsampling=0)
        data = buf.getvalue()
        if len(data) <= MAX_BYTES:
            break
    return data, q


def frame_summary(geom: dict) -> dict:
    sc = list(geom["scales"].values())
    g = math.gcd(geom["width"], geom["height"]) or 1
    return {"width": geom["width"], "height": geom["height"],
            "native_w": geom["native_w"], "native_h": geom["native_h"],
            "ratio": geom["height"] / float(geom["width"]),
            "min_scale": min(sc), "avg_scale": sum(sc) / len(sc),
            "small": [i for i, s in geom["scales"].items() if s < WARN_SCALE],
            "blank": geom["blank"], "downscale": geom["downscale"]}


# ── 自動配置 ──────────────────────────────────────────────────
def _frame_cost(geom: dict) -> float:
    pen = 0.0
    for s in geom["scales"].values():
        if s < WARN_SCALE:
            pen += 1.5 + (WARN_SCALE - s) * 8
        elif s < 0.75:
            pen += (0.75 - s) * 2
        if s > 1.1:
            pen += (s - 1.1) * 3
        pen += (1.0 - min(s, 1.0)) * 0.6          # 大きく見せられる配置ほど良い
    r = geom["height"] / float(geom["width"])
    if r > 3.2:
        pen += (r - 3.2) * 1.5                      # 極端に縦長
    if r < 0.55:
        pen += (0.55 - r) * 4                       # 極端に横長
    return pen + geom["blank"] * 3 * len(geom["scales"])


def _compositions(m: int, k: int):
    """m 個を順番どおり k 列に分ける（各列1個以上）。"""
    for cuts in __import__("itertools").combinations(range(1, m), k - 1):
        b = (0,) + cuts + (m,)
        yield [(b[j], b[j + 1]) for j in range(k)]


def best_frame(seg: list, sizes: dict) -> tuple[float, list]:
    best = (float("inf"), None)
    m = len(seg)
    for k in range(1, min(MAX_COLS, m) + 1):
        for parts in _compositions(m, k):
            cols = [{"items": seg[a:b], "pad": 0} for a, b in parts]
            g = plan_frame(cols, sizes)
            c = _frame_cost(g)
            if c < best[0]:
                best = (c, cols)
    return best


def auto_layout(order: list, sizes: dict, max_frames: int = N_FRAMES) -> dict:
    """優先順（order）を崩さずに、最大4枚（max_frames 枚）・各1〜4列へ分ける。
    max_frames を減らすと前から max_frames 枚だけを使う（残りの枠は空）。既定は従来どおり 4 枚。

    1枚の中は「左の列の上から順に → 次の列」の順。枚数・列数・列ごとの枚数は
    余白・縮小率・縦横比のコストが最小になる組み合わせを選ぶ（動的計画法）。"""
    n = len(order)
    if n == 0:
        return empty_layout()
    INF = float("inf")
    cache: dict = {}

    def seg_cost(a, b):
        if (a, b) not in cache:
            cache[(a, b)] = best_frame(order[a:b], sizes)
        return cache[(a, b)]

    F = max(1, min(N_FRAMES, int(max_frames)))
    best = [[(INF, None)] * (F + 1) for _ in range(n + 1)]
    best[0][0] = (0.0, None)
    for i in range(1, n + 1):
        for f in range(1, F + 1):
            for a in range(max(0, i - SEG_MAX), i):
                if best[a][f - 1][0] == INF:
                    continue
                c, _ = seg_cost(a, i)
                tot = best[a][f - 1][0] + c
                if tot < best[i][f][0]:
                    best[i][f] = (tot, a)
    f_best = min(range(1, F + 1), key=lambda f: best[n][f][0])
    if best[n][f_best][0] == INF:          # 4枚（F 枚）に入りきらない（素材が多すぎる）
        per = math.ceil(n / F)
        segs = [(s, min(n, s + per)) for s in range(0, n, per)]
    else:
        segs, i, f = [], n, f_best
        while f > 0:
            a = best[i][f][1]
            segs.append((a, i))
            i, f = a, f - 1
        segs.reverse()
    lay = empty_layout()
    for fi, (a, b) in enumerate(segs[:F]):
        if b - a <= SEG_MAX:
            lay["frames"][fi]["cols"] = seg_cost(a, b)[1]
        else:
            lay["frames"][fi]["cols"] = [{"items": order[a:b], "pad": 0}]
    return normalize_layout(lay, order)


# ── サムネイル ────────────────────────────────────────────────
def thumb_data_url(img: Image.Image, max_w: int = 240) -> str:
    im = img.convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, max(1, int(round(im.height * max_w / im.width)))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=72)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# ── 保存（ローカルの内部フォルダ・Git 管理外）────────────────────────
def store_root(base_dir: str) -> str:
    # 「_tmp_*」は .gitignore 済み（自動push・Cloud同期の対象外）
    return os.path.join(base_dir, "_tmp_xpost")


def _layouts_path(base_dir: str) -> str:
    return os.path.join(store_root(base_dir), "layouts.json")


def load_record(base_dir: str, key: str) -> "dict | None":
    try:
        with open(_layouts_path(base_dir), encoding="utf-8") as fh:
            return (json.load(fh) or {}).get(key)
    except Exception:
        return None


def save_record(base_dir: str, key: str, rec: dict) -> None:
    root = store_root(base_dir)
    os.makedirs(root, exist_ok=True)
    path = _layouts_path(base_dir)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh) or {}
    except Exception:
        data = {}
    rec = dict(rec)
    rec["saved"] = datetime.now().isoformat(timespec="seconds")
    data[key] = rec
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def materials_dir(base_dir: str, dir_stem: str, mode_key: str) -> str:
    return os.path.join(store_root(base_dir), "materials", dir_stem, mode_key)
