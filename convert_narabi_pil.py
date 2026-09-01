#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
convert_narabi_pil.py
並び画像生成スクリプト（PIL ImageDraw版 / Cloud・ローカル共通）
dataframe_image / ブラウザ不使用
"""
import pandas as pd
import os
import io
from collections import Counter
from PIL import Image, ImageDraw, ImageFont

INPUT     = r"C:\Users\23-3\Desktop\画像作成\20260414_エスパス上野新館_20S.xlsx"
SPLIT_DIR = r"C:\Users\23-3\Desktop\画像作成\20260414_エスパス上野新館\並び画像"
os.makedirs(SPLIT_DIR, exist_ok=True)

# 台番範囲を直接指定（空リストなら自動検出）
RANGES = []

# 青タイトルバー＋赤ラインを描かない（記事用ページのみ True へ書き換えて実行する）。
# 既定 False＝通常ページの並び画像は従来どおり青バー付き。
NO_BAR = False

# 高解像度描画の倍率（記事用ページのみ 2.0 へ書き換えて実行する）。
# 掲載台が HQ_MIN_ROWS 台以上の並び画像だけ、最初からこの倍率で描画する。
# 既定 1.0＝通常ページの並び画像は従来どおり。
HQ_SCALE = 1.0
HQ_MIN_ROWS = 10

# 列画像（列仕掛け）用の台番範囲。既定は空リスト＝従来の並び画像だけを生成する。
# Streamlit 側の ③「列画像を作成する」がONのときだけ書き換えて実行される。
# 列画像は並び画像とまったく同じ描画・後処理で作り、タイトルだけ
# 「機種名（列仕掛け）」（台数表記なし）にする。
COL_RANGES = []
COL_SUFFIX = "（列仕掛け）"

# ── フォントパス（cwd = BASE_DIR で subprocess 実行される）──────────
_BASE = os.getcwd()
FONT_PATH = os.path.join(_BASE, "fonts", "MochiyPopOne-Regular.ttf")
if not os.path.exists(FONT_PATH):
    FONT_PATH = r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf"

# --- 機種名変換 ---
conv = pd.read_excel(r"C:\Users\23-3\Desktop\画像作成\機種名変換.xlsx", header=1)
name_map = dict(zip(conv.iloc[:, 1], conv.iloc[:, 2]))
name_map_nospace = {str(k).replace(" ", "").replace("　", ""): v
                    for k, v in name_map.items()}

def convert_name(name):
    if name in name_map:
        return name_map[name]
    key = str(name).replace(" ", "").replace("　", "")
    if key in name_map_nospace:
        return name_map_nospace[key]
    return name

# --- データ読み込み ---
df = pd.read_excel(INPUT)
_machine_col = next(
    (c for c in ["機種名", "機種名（正式名）", "機種名（データサイト表記）", "機種名（表記）", "機種"] if c in df.columns),
    "機種名（データサイト表記）",
)
_games_col = next((c for c in ["G数", "G数(G)", "ゲーム数", "総ゲーム数", "G", "回転数", "スピン数"] if c in df.columns), "G数")
_diff_col  = next((c for c in ["差枚", "差枚数", "差玉", "差枚(枚)", "差"] if c in df.columns), "差枚")
_dai_col   = next((c for c in ["台番", "台No", "台no", "台NO", "号機", "番台", "台番号"] if c in df.columns), "台番")
_bb_col    = next((c for c in ["BB", "bb", "BIG", "big", "BIG回数", "BB回数"] if c in df.columns), "BB")
_rb_col    = next((c for c in ["RB", "rb", "REG", "reg", "REG回数", "RB回数"] if c in df.columns), "RB")
_at_col    = next((c for c in ["ART", "art", "AT", "at", "ART回数", "AT回数"] if c in df.columns), None)
if _at_col is None:
    df["__AT__"] = 0
    _at_col = "__AT__"
df = df[[_dai_col, _machine_col, _games_col, _bb_col, _rb_col, _at_col, _diff_col]].copy()
df.columns = ["台番", "機種名", "ゲーム数_raw", "BIG", "REG", "AT", "差枚数"]
df["台番"] = df["台番"].astype(int)
df["機種名"] = df["機種名"].apply(convert_name)

# --- 書式関数 ---
def round_games(v):
    n = int(v); r = n % 100
    if r <= 24:   return (n // 100) * 100
    elif r <= 74: return (n // 100) * 100 + 50
    else:         return (n // 100 + 1) * 100

def fmt_games(v):
    try:    return f"{int(v):,}G"
    except: return str(v)

def fmt_diff(v):
    try:
        n = int(v)
        if n > 0:   return f"+{n:,}枚"
        elif n < 0: return f"{n:,}枚"
        else:       return "±0枚"
    except: return str(v)

def fmt_prob(bb, rb, g_rounded):
    total = bb + rb
    if total == 0: return "――"
    return f"1/{g_rounded / total:.1f}"

diff_raw = df["差枚数"].copy()
df["ゲーム数_rounded"] = df["ゲーム数_raw"].apply(round_games)
df["合算確率"] = df.apply(
    lambda r: fmt_prob(r["BIG"], r["REG"], r["ゲーム数_rounded"]), axis=1)
df["ゲーム数"] = df["ゲーム数_rounded"].apply(fmt_games)
df["差枚数_disp"] = diff_raw.apply(fmt_diff)

# --- 優秀台判定 ---
THRESHOLDS = {
    "マイジャグV": 136, "ファンキー2": 141, "ゴージャグ3": 131, "アイム": 143,
    "ネオアイム": 143, "ハピジャグV": 138, "ウルトラミラジャグ": 139,
    "ジャグラーガールズ": 133, "ミスジャグ": 135,
}

def is_yushu(i):
    row = df.iloc[i]
    d = diff_raw.iloc[i]
    if d >= 1000: return True
    if d < 0:     return False
    m = row["機種名"]
    if m in THRESHOLDS:
        total = row["BIG"] + row["REG"]
        if total == 0: return False
        return row["ゲーム数_rounded"] / total <= THRESHOLDS[m]
    return d >= 0

df["優秀台"] = [is_yushu(i) for i in range(len(df))]

# --- runs の構築（RANGES指定 or 自動検出） ---
ban_to_idx = {int(row["台番"]): i for i, row in df.iterrows()}

if RANGES:
    runs = []
    for item in RANGES:
        indices = []
        bans = range(item[0], item[1] + 1) if (isinstance(item, tuple) and len(item) == 2) else item
        for ban in bans:
            if ban in ban_to_idx:
                indices.append(ban_to_idx[ban])
            else:
                print(f"  [警告] 台番 {ban} がExcelに見つかりません")
        if indices:
            runs.append(indices)
    print(f"指定並び: {len(runs)}件")
elif COL_RANGES:
    # 列画像だけを生成する指定（並びはOFF）。自動検出へ落とさない。
    runs = []
    print("並び指定なし（列画像のみ）")
else:
    runs = []
    current_run = []
    for i in range(len(df)):
        row = df.iloc[i]
        if row["優秀台"]:
            if current_run:
                prev = df.iloc[i - 1]
                if row["台番"] - prev["台番"] == 1:
                    current_run.append(i)
                else:
                    if len(current_run) >= 3:
                        runs.append(current_run.copy())
                    current_run = [i]
            else:
                current_run = [i]
        else:
            if len(current_run) >= 3:
                runs.append(current_run.copy())
            current_run = []
    if len(current_run) >= 3:
        runs.append(current_run.copy())
    print(f"3台以上の並び（自動検出）: {len(runs)}件")

# --- タイトル生成 ---
def machine_label(run_indices):
    """並び・列で共通の機種名ラベル（1機種／2機種／3機種以上）。"""
    machines_ordered = list(dict.fromkeys(df.iloc[i]["機種名"] for i in run_indices))
    unique_dedup = list(dict.fromkeys(m.strip() for m in machines_ordered))
    if len(unique_dedup) == 1:
        return f"{unique_dedup[0]}"
    elif len(unique_dedup) == 2:
        return f"{unique_dedup[0]}+{unique_dedup[1]}"
    else:
        return f"{unique_dedup[0]}～{unique_dedup[-1]}"

def make_title(run_indices):
    return f"{machine_label(run_indices)}({len(run_indices)}台並び)"

def make_col_title(run_indices):
    """列画像のタイトル。台数表記は付けず「機種名（列仕掛け）」とする。"""
    return f"{machine_label(run_indices)}{COL_SUFFIX}"

def make_safe(name):
    return name.replace("/", "／").replace("\\", "＼").replace(":", "：") \
               .replace("*", "＊").replace("?", "？").replace('"', '”') \
               .replace("<", "＜").replace(">", "＞").replace("|", "｜")

title_counts = Counter(make_title(r) for r in runs)
dup_titles = {t for t, c in title_counts.items() if c > 1}

# --- 列画像 runs（COL_RANGES 指定時のみ。既定は空リスト＝従来と完全に同一）---
col_runs = []
for item in (COL_RANGES or []):
    indices = []
    bans = range(item[0], item[1] + 1) if (isinstance(item, tuple) and len(item) == 2) else item
    for ban in bans:
        if ban in ban_to_idx:
            indices.append(ban_to_idx[ban])
        else:
            print(f"  [警告] 台番 {ban} がExcelに見つかりません（列）")
    if indices:
        col_runs.append(indices)
if col_runs:
    print(f"指定列: {len(col_runs)}件")
col_dup_titles = {t for t, c in Counter(make_col_title(r) for r in col_runs).items() if c > 1}

# 並び → 列 の順に (台番indices, タイトル, 同名タイトル集合) を並べる。
# COL_RANGES が空なら並びだけ＝従来の runs ループと同一。
_JOBS = ([(r, make_title(r), dup_titles) for r in runs]
         + [(r, make_col_title(r), col_dup_titles) for r in col_runs])

# ── PIL 描画定数（dfi.export DPI=150 相当に寄せる）─────────────────
SCALE         = 150 / 96            # ≈ 1.5625
FONT_SIZE_TBL = round(14 * SCALE)   # 22px  表本体
PAD_X         = round(8  * SCALE)   # 13px  左右パディング
# 他画像（全台系・高配分・ジャグラー優秀台）の ROW_H=28 CSS px と統一
ROW_H_TBL     = round(28 * SCALE)   # 44px  行高（28 CSS px × 1.5625）
PAD_Y         = (ROW_H_TBL - FONT_SIZE_TBL) // 2  # 11px  上下パディング

HEADER_BG  = (243, 230, 200)   # #f3e6c8
HEADER_FG  = (75,  0,   130)   # #4B0082
CELL_BG    = (255, 255, 255)   # white
BORDER_C   = (170, 170, 170)   # #AAAAAA
PLUS_C     = (0,   0,   204)   # #0000CC
MINUS_C    = (204, 0,   0  )   # #CC0000
ZERO_C     = (0,   0,   0  )

# 列コンテンツ幅（CSS px × SCALE 済みの実ピクセル）
COL_CONTENT_W = {
    "台番":     round(55  * SCALE),   # ~86
    "機種名":   round(170 * SCALE),   # 266
    "ゲーム数": round(75  * SCALE),   # ~117
    "BIG":      round(40  * SCALE),   # ~63
    "REG":      round(40  * SCALE),   # ~63
    "AT":       round(40  * SCALE),   # ~63
    "合算確率": round(80  * SCALE),   # 125
    "差枚数":   round(90  * SCALE),   # 141
}

def _load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def _textbbox(draw, text, font):
    try:
        bb = draw.textbbox((0, 0), text, font=font)
    except Exception:
        sz = getattr(font, "size", 10)
        bb = (0, 0, len(text) * sz // 2 + 4, sz)
    return bb

def _draw_cell(draw, x, y, cw, ch, text, bg, fg, font, align="center"):
    draw.rectangle([x, y, x + cw - 1, y + ch - 1], fill=bg)
    bb = _textbbox(draw, text, font)
    tw = bb[2] - bb[0]
    th = bb[3] - bb[1]
    if align == "center":
        tx = x + (cw - tw) // 2 - bb[0]
    elif align == "right":
        tx = x + cw - PAD_X - tw - bb[0]
    else:
        tx = x + PAD_X - bb[0]
    ty = y + (ch - th) // 2 - bb[1]
    draw.text((tx, ty), text, fill=fg, font=font)

def build_table_pil(group, diff_raw_s, hq=1.0):
    """PIL ImageDraw でテーブル部分を描画して RGBA Image を返す。
    hq>1 なら文字・行高・列幅・パディングを hq 倍にして**最初から**高解像度で描く
    （出来上がりを resize で拡大しない）。hq=1.0 は従来と完全に同一。"""
    _hq       = hq if hq and hq > 0 else 1.0
    _font_sz  = round(FONT_SIZE_TBL * _hq)
    _pad_x    = round(PAD_X * _hq)
    _row_h    = round(ROW_H_TBL * _hq)
    font = _load_font(_font_sz)
    cols = list(group.columns)
    # セル外幅 = コンテンツ幅 + 2×PAD_X
    cell_ow = [round(COL_CONTENT_W.get(c, round(70 * SCALE)) * _hq) + 2 * _pad_x for c in cols]
    n_rows  = len(group) + 1  # ヘッダー + データ行

    # border-collapse モデル: 全体を BORDER_C で塗り、セルを1px内側に描画
    img_w = 1 + sum(ow + 1 for ow in cell_ow)   # 左端1px + セル + 右境界
    img_h = 1 + n_rows * (_row_h + 1)           # 上端1px + 行 + 下境界

    img  = Image.new("RGBA", (img_w, img_h), BORDER_C + (255,))
    draw = ImageDraw.Draw(img)

    def col_x(ci):
        return 1 + sum(cell_ow[k] + 1 for k in range(ci))

    def row_y(ri):
        return 1 + ri * (_row_h + 1)

    # ヘッダー行
    for ci, col in enumerate(cols):
        _draw_cell(draw, col_x(ci), row_y(0), cell_ow[ci], _row_h,
                   col, HEADER_BG, HEADER_FG, font, "center")

    # データ行
    for ri, (_, row) in enumerate(group.iterrows()):
        y = row_y(ri + 1)
        for ci, col in enumerate(cols):
            val = str(row[col]) if pd.notna(row[col]) else ""
            if col == "差枚数":
                try:
                    n  = int(diff_raw_s.iloc[ri])
                    fg = PLUS_C if n > 0 else (MINUS_C if n < 0 else ZERO_C)
                except Exception:
                    fg = ZERO_C
                align = "right"
            else:
                fg, align = ZERO_C, "center"
            _draw_cell(draw, col_x(ci), y, cell_ow[ci], _row_h,
                       val, CELL_BG, fg, font, align)
    return img

# ── 各並びの画像生成 ─────────────────────────────────────────────
for run_idx, (run, title, _dup_set) in enumerate(_JOBS):
    run_df_full = df.iloc[run].copy().reset_index(drop=True)
    diff_raw_s  = diff_raw.iloc[run].reset_index(drop=True)

    print(f"\n[{run_idx+1}/{len(_JOBS)}] {title}")

    DISPLAY_COLS = ["台番", "機種名", "ゲーム数", "BIG", "REG", "AT", "合算確率", "差枚数_disp"]
    group = run_df_full[DISPLAY_COLS].copy().rename(columns={"差枚数_disp": "差枚数"})
    active_cols = [c for c in ["BIG", "REG", "AT"] if not (group[c] == 0).all()]
    disp_cols   = ["台番", "機種名", "ゲーム数"] + active_cols + ["合算確率", "差枚数"]
    group       = group[disp_cols]

    # ── PIL テーブル描画 ──────────────────────────────────────────
    # 掲載台が HQ_MIN_ROWS 台以上なら記事用の高解像度で描画（通常ページは HQ_SCALE=1.0）
    _hq_run = HQ_SCALE if (HQ_SCALE > 1.0 and len(group) >= HQ_MIN_ROWS) else 1.0
    top_img = build_table_pil(group, diff_raw_s, hq=_hq_run)
    w = top_img.width

    # --- タイトルバー（青バー＋赤ライン） ---
    bar_h  = round(w * 73 / 950)   # 標準幅950pxのとき73px（_build_machine_imgと統一）
    line_h = 6
    font_size_bar = round(bar_h * 40 / 73)

    blue_bar = Image.new("RGBA", (w, bar_h),  (38, 76, 161, 255))
    red_line = Image.new("RGBA", (w, line_h), (204, 0, 0, 255))
    bar_draw = ImageDraw.Draw(blue_bar)
    bar_font = _load_font(font_size_bar)

    title_text = title.strip().replace('･', '・')
    # 列画像は「機種名（列仕掛け）」を2パーツで描いて余白を詰める（GAP_TITLE=-22）。
    # MochiyPopOne の全角括弧は1em幅で左に約半角の空きがあり、一括描画だと
    # 機種名との間に隙間が見える（streamlit_app._build_machine_img と同じ補正）。
    # 並び画像のタイトルは COL_SUFFIX で終わらないので従来どおり一括描画。
    GAP_TITLE = -22
    _sub  = COL_SUFFIX if (COL_SUFFIX and title_text.endswith(COL_SUFFIX)) else None
    _main = title_text[:-len(_sub)] if _sub else title_text

    def _title_w(_font):
        if _sub:
            _b1 = _textbbox(bar_draw, _main, _font)
            _b2 = _textbbox(bar_draw, _sub,  _font)
            return (_b1[2] - _b1[0]) + GAP_TITLE + (_b2[2] - _b2[0])
        _b = _textbbox(bar_draw, title_text, _font)
        return _b[2] - _b[0]

    bbox = _textbbox(bar_draw, title_text, bar_font)
    text_w = _title_w(bar_font)
    text_h = bbox[3] - bbox[1]

    # タイトルが広すぎる場合はフォントを縮小
    reduced_size = font_size_bar
    while text_w > w - 20 and reduced_size > 12:
        reduced_size -= 2
        bar_font = _load_font(reduced_size)
        bbox   = _textbbox(bar_draw, title_text, bar_font)
        text_w = _title_w(bar_font)
        text_h = bbox[3] - bbox[1]

    if _sub:
        b1 = _textbbox(bar_draw, _main, bar_font)
        b2 = _textbbox(bar_draw, _sub,  bar_font)
        w1, w2 = b1[2] - b1[0], b2[2] - b2[0]
        x1 = (w - (w1 + GAP_TITLE + w2)) // 2 - b1[0]
        x2 = x1 + w1 + GAP_TITLE - b2[0]
        ty = (bar_h - (b1[3] - b1[1])) // 2 - b1[1]
        bar_draw.text((x1, ty), _main, fill=(255, 255, 255, 255), font=bar_font)
        bar_draw.text((x2, ty), _sub,  fill=(255, 255, 255, 255), font=bar_font)
    else:
        tx = (w - text_w) // 2 - bbox[0]
        ty = (bar_h - text_h) // 2 - bbox[1]
        bar_draw.text((tx, ty), title_text, fill=(255, 255, 255, 255), font=bar_font)

    # 合成：青バー → 赤ライン → テーブル（NO_BAR=True の記事用はテーブルのみ）
    _top_h  = 0 if NO_BAR else bar_h + line_h
    total_h = _top_h + top_img.height
    canvas  = Image.new("RGBA", (w, total_h), (255, 255, 255, 255))
    if not NO_BAR:
        canvas.paste(blue_bar, (0, 0))
        canvas.paste(red_line, (0, bar_h))
    canvas.paste(top_img,  (0, _top_h))

    # --- ピンクのサマリーバー ---
    total_diff  = int(round(diff_raw_s.sum()))
    avg_diff    = int(round(diff_raw_s.mean()))
    win_count   = int((diff_raw_s > 0).sum())
    total_count = len(diff_raw_s)
    win_rate    = win_count / total_count * 100

    sum_part1 = (
        f"総差枚：{fmt_diff(total_diff)}　"
        f"平均：{fmt_diff(avg_diff)}　"
        f"勝率：{win_rate:.1f}%"
    )
    sum_part2 = f"（{win_count}/{total_count}台）"
    GAP_SUM   = -8

    table_only_h = canvas.height - _top_h   # ピンクバー高さの算出はテーブル部分のみ基準（従来と同値）
    row_h_sum    = int(max(30, table_only_h // (len(group) + 2)) * 1.2)

    SUMMARY_BG = "#FFB6C1"
    pink_rgba  = tuple(int(SUMMARY_BG.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    bar_pink   = Image.new("RGBA", (w, row_h_sum), pink_rgba)
    draw_pink  = ImageDraw.Draw(bar_pink)

    font_sum = _load_font(round(14 * 150 / 96 * _hq_run))  # ≈ 22px（hq倍）

    bb1    = _textbbox(draw_pink, sum_part1, font_sum)
    y_text = (row_h_sum - (bb1[3] - bb1[1])) // 2 - bb1[1]
    draw_pink.text((8, y_text), sum_part1, fill=(0, 0, 0, 255), font=font_sum)
    x2  = 8 + (bb1[2] - bb1[0]) + GAP_SUM
    bb2 = _textbbox(draw_pink, sum_part2, font_sum)
    draw_pink.text((x2 - bb2[0], y_text), sum_part2, fill=(0, 0, 0, 255), font=font_sum)

    bc = (170, 170, 170, 255)
    draw_pink.line([(0, 0),          (w-1, 0)],           fill=bc, width=1)
    draw_pink.line([(0, 0),          (0, row_h_sum-1)],   fill=bc, width=1)
    draw_pink.line([(w-1, 0),        (w-1, row_h_sum-1)], fill=bc, width=1)
    draw_pink.line([(0, row_h_sum-1),(w-1, row_h_sum-1)], fill=bc, width=1)

    combined = Image.new("RGBA", (w, canvas.height + row_h_sum), (255, 255, 255, 255))
    combined.paste(canvas,   (0, 0))
    combined.paste(bar_pink, (0, canvas.height))
    final_pil = combined.convert("RGB")

    # ファイル名（同タイトルが複数あれば台番範囲を付与して区別）
    ban_start = df.iloc[run[0]]["台番"]
    ban_end   = df.iloc[run[-1]]["台番"]
    file_title = f"{title}（{ban_start}～{ban_end}）" if title in _dup_set else title
    safe_title = make_safe(file_title)
    out_path   = os.path.join(SPLIT_DIR, f"{safe_title}.jpg")

    # JPEG品質バイナリサーチで目標サイズに近づける（高解像度時は1200KB）
    TARGET_BYTES = (1200 if _hq_run > 1.0 else 250) * 1024
    lo, hi = 1, 95
    best_quality = 85
    best_diff_sz = float("inf")
    for _ in range(15):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        final_pil.save(buf, format="JPEG", quality=mid, subsampling=0)
        size = buf.tell()
        diff_sz = abs(size - TARGET_BYTES)
        if diff_sz < best_diff_sz:
            best_diff_sz = diff_sz
            best_quality = mid
        if diff_sz / TARGET_BYTES <= 0.02:
            break
        if size < TARGET_BYTES:
            lo = mid + 1
        else:
            hi = mid - 1

    final_pil.save(out_path, format="JPEG", quality=best_quality, subsampling=0)
    print(f"  -> {out_path}  quality={best_quality}, {os.path.getsize(out_path)//1024}KB")

print("\n完了！")
