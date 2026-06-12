import pandas as pd
import dataframe_image as dfi
import os
import io
import tempfile
from PIL import Image, ImageDraw, ImageFont
from collections import Counter

INPUT     = r"C:\Users\23-3\Desktop\画像作成\20260415_エスパス稲毛_20S.xlsx"
SPLIT_DIR = r"C:\Users\23-3\Desktop\画像作成\20260415_エスパス稲毛\並び画像"
os.makedirs(SPLIT_DIR, exist_ok=True)

# ── 台番範囲を直接指定（空リストなら自動検出） ────────────────
# 例: RANGES = [(409, 413), (315, 317)]
RANGES = [
    (409, 413),
    (315, 317),
]

# --- 機種名変換 ---
conv = pd.read_excel(r"C:\Users\23-3\Desktop\画像作成\機種名変換.xlsx", header=1)
name_map = dict(zip(conv.iloc[:, 1], conv.iloc[:, 2]))
name_map_nospace = {str(k).replace(" ", "").replace("\u3000", ""): v
                    for k, v in name_map.items()}

def convert_name(name):
    if name in name_map:
        return name_map[name]
    key = str(name).replace(" ", "").replace("\u3000", "")
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
    if total == 0: return "───"
    return f"1/{g_rounded / total:.1f}"

diff_raw = df["差枚数"].copy()
df["ゲーム数_rounded"] = df["ゲーム数_raw"].apply(round_games)
df["合算確率"] = df.apply(
    lambda r: fmt_prob(r["BIG"], r["REG"], r["ゲーム数_rounded"]), axis=1)
df["ゲーム数"] = df["ゲーム数_rounded"].apply(fmt_games)
df["差枚数_disp"] = diff_raw.apply(fmt_diff)

# --- runs の構築（RANGES指定 or 自動検出） ---
ban_to_idx = {int(row["台番"]): i for i, row in df.iterrows()}

if RANGES:
    runs = []
    for item in RANGES:
        indices = []
        # 旧形式 (start, end) タプル → 連番展開、新形式 [ban1, ban2, ...] → そのまま使用
        bans = range(item[0], item[1] + 1) if (isinstance(item, tuple) and len(item) == 2) else item
        for ban in bans:
            if ban in ban_to_idx:
                indices.append(ban_to_idx[ban])
            else:
                print(f"  [警告] 台番 {ban} がExcelに見つかりません")
        if indices:
            runs.append(indices)
    print(f"指定並び: {len(runs)}件")
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
def make_title(run_indices):
    machines_ordered = list(dict.fromkeys(df.iloc[i]["機種名"] for i in run_indices))
    N = len(run_indices)
    unique = [m.strip() for m in machines_ordered]
    unique_dedup = list(dict.fromkeys(unique))
    if len(unique_dedup) == 1:
        return f"{unique_dedup[0]}({N}台並び)"
    elif len(unique_dedup) == 2:
        return f"{unique_dedup[0]}+{unique_dedup[1]}({N}台並び)"
    else:
        return f"{unique_dedup[0]}～{unique_dedup[-1]}({N}台並び)"

def make_safe(name):
    return name.replace("/", "／").replace("\\", "＼").replace(":", "：") \
               .replace("*", "＊").replace("?", "？").replace('"', '\u201d') \
               .replace("<", "＜").replace(">", "＞").replace("|", "｜")

# 同タイトルが複数出る場合を事前に検出
title_counts = Counter(make_title(r) for r in runs)
dup_titles = {t for t, c in title_counts.items() if c > 1}

# --- スタイル定数 ---
PLUS_COLOR  = "#0000CC"
MINUS_COLOR = "#CC0000"
ZERO_COLOR  = "#000000"
MACHINE_HEADER_BG = "#f3e6c8"
MACHINE_HEADER_FG = "#4B0082"

TABLE_STYLES = [
    {"selector": "thead th",
     "props": [("background-color", MACHINE_HEADER_BG),
               ("color", MACHINE_HEADER_FG),
               ("font-weight", "500"),
               ("text-align", "center"),
               ("font-family", "'Mochiy Pop One', sans-serif"),
               ("font-size", "14px"),
               ("padding", "4px 8px"),
               ("border", "1px solid #AAAAAA")]},
    {"selector": "td",
     "props": [("font-family", "'Mochiy Pop One', sans-serif"),
               ("font-size", "14px"),
               ("padding", "4px 8px"),
               ("border", "1px solid #AAAAAA")]},
    {"selector": "table",
     "props": [("border-collapse", "collapse")]},
]

EVEN_BG = "white"
ODD_BG  = "white"
FONT_PATH = r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf"

# --- 各並びの画像生成 ---
for run_idx, run in enumerate(runs):
    run_df_full = df.iloc[run].copy().reset_index(drop=True)
    diff_raw_s  = diff_raw.iloc[run].reset_index(drop=True)

    title = make_title(run)
    print(f"\n[{run_idx+1}/{len(runs)}] {title}")

    DISPLAY_COLS = ["台番", "機種名", "ゲーム数", "BIG", "REG", "AT", "合算確率", "差枚数_disp"]
    group = run_df_full[DISPLAY_COLS].copy()
    group = group.rename(columns={"差枚数_disp": "差枚数"})

    active_cols = [c for c in ["BIG", "REG", "AT"] if not (group[c] == 0).all()]
    disp_cols   = ["台番", "機種名", "ゲーム数"] + active_cols + ["合算確率", "差枚数"]
    group       = group[disp_cols]

    def row_bg(row):
        bg = EVEN_BG if row.name % 2 == 0 else ODD_BG
        return [f"background-color: {bg}"] * len(row)

    def diff_color_s(row, _dr=diff_raw_s):
        styles = [""] * len(row)
        idx = list(row.index).index("差枚数")
        try:
            n = int(_dr.iloc[row.name])
            c = PLUS_COLOR if n > 0 else (MINUS_COLOR if n < 0 else ZERO_COLOR)
        except:
            c = ZERO_COLOR
        styles[idx] = f"color: {c}; text-align: right;"
        return styles

    styled_s = group.style.hide(axis="index").apply(row_bg, axis=1).apply(diff_color_s, axis=1)
    styled_s = (
        styled_s
        .set_properties(subset=["機種名"],   **{"text-align": "center", "width": "170px"})
        .set_properties(subset=["ゲーム数"], **{"text-align": "center"})
        .set_properties(subset=["合算確率"], **{"text-align": "center", "width": "80px"})
        .set_properties(subset=["差枚数"],   **{"width": "90px", "white-space": "nowrap"})
        .set_table_styles(TABLE_STYLES)
    )
    if active_cols:
        styled_s = styled_s.set_properties(
            subset=active_cols, **{"width": "40px", "text-align": "center"})

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_table = f.name
    dfi.export(styled_s, tmp_table, dpi=150, max_rows=-1,
               table_conversion="playwright", fontsize=14)

    top_img = Image.open(tmp_table).convert("RGBA")
    top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
    w = top_img.width

    # --- タイトルバー（青バー＋赤ライン） ---
    bar_h  = 62
    line_h = 6
    font_size_bar = round(bar_h * 0.58)

    blue_bar = Image.new("RGBA", (w, bar_h),  (47, 85, 164, 255))
    red_line = Image.new("RGBA", (w, line_h), (204, 0, 0, 255))
    bar_draw = ImageDraw.Draw(blue_bar)

    try:
        bar_font = ImageFont.truetype(FONT_PATH, font_size_bar)
    except Exception:
        bar_font = ImageFont.load_default()

    title_text = title.strip().replace('\uff65', '\u30fb')

    bbox = bar_draw.textbbox((0, 0), title_text, font=bar_font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    if text_w > w - 20:
        reduced_size = font_size_bar
        while text_w > w - 20 and reduced_size > 12:
            reduced_size -= 2
            try:
                bar_font = ImageFont.truetype(FONT_PATH, reduced_size)
            except:
                break
            bbox = bar_draw.textbbox((0, 0), title_text, font=bar_font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]

    tx = (w - text_w) // 2 - bbox[0]
    ty = (bar_h - text_h) // 2 - bbox[1]
    bar_draw.text((tx, ty), title_text, fill=(255, 255, 255, 255), font=bar_font)

    total_h = bar_h + line_h + top_img.height
    canvas = Image.new("RGBA", (w, total_h), (255, 255, 255, 255))
    canvas.paste(blue_bar, (0, 0))
    canvas.paste(red_line, (0, bar_h))
    canvas.paste(top_img,  (0, bar_h + line_h))
    os.unlink(tmp_table)

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
    GAP_SUM = -8

    table_only_h = canvas.height - bar_h - line_h
    base_row_h = max(30, table_only_h // (len(group) + 2))
    row_h = int(base_row_h * 1.2)

    SUMMARY_BG = "#FFB6C1"
    pink_rgba = tuple(int(SUMMARY_BG.lstrip("#")[i:i+2], 16) for i in (0, 2, 4)) + (255,)
    bar_pink = Image.new("RGBA", (w, row_h), pink_rgba)
    draw_pink = ImageDraw.Draw(bar_pink)

    font_size_sum = round(14 * 150 / 96)
    try:
        font_sum = ImageFont.truetype(FONT_PATH, font_size_sum)
    except Exception:
        font_sum = ImageFont.load_default()

    bb1 = draw_pink.textbbox((0, 0), sum_part1, font=font_sum)
    y_text = (row_h - (bb1[3] - bb1[1])) // 2 - bb1[1]
    draw_pink.text((8, y_text), sum_part1, fill=(0, 0, 0, 255), font=font_sum)
    x2 = 8 + (bb1[2] - bb1[0]) + GAP_SUM
    bb2 = draw_pink.textbbox((0, 0), sum_part2, font=font_sum)
    draw_pink.text((x2 - bb2[0], y_text), sum_part2, fill=(0, 0, 0, 255), font=font_sum)

    bc = (170, 170, 170, 255)
    draw_pink.line([(0, 0),       (w-1, 0)],       fill=bc, width=1)
    draw_pink.line([(0, 0),       (0, row_h-1)],   fill=bc, width=1)
    draw_pink.line([(w-1, 0),     (w-1, row_h-1)], fill=bc, width=1)
    draw_pink.line([(0, row_h-1), (w-1, row_h-1)], fill=bc, width=1)

    combined = Image.new("RGBA", (w, canvas.height + row_h), (255, 255, 255, 255))
    combined.paste(canvas,   (0, 0))
    combined.paste(bar_pink, (0, canvas.height))
    final_pil = combined.convert("RGB")

    # ファイル名（同タイトルが複数あれば台番範囲を付与）
    ban_start = df.iloc[run[0]]["台番"]
    ban_end   = df.iloc[run[-1]]["台番"]
    if title in dup_titles:
        file_title = f"{title}（{ban_start}～{ban_end}）"
    else:
        file_title = title
    safe_title = make_safe(file_title)
    out_path = os.path.join(SPLIT_DIR, f"{safe_title}.jpg")

    TARGET_BYTES = 250 * 1024
    lo, hi = 1, 95
    best_quality = 85
    best_diff = float("inf")
    for _ in range(15):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        final_pil.save(buf, format="JPEG", quality=mid, subsampling=0)
        size = buf.tell()
        diff_sz = abs(size - TARGET_BYTES)
        if diff_sz < best_diff:
            best_diff = diff_sz
            best_quality = mid
        if diff_sz / TARGET_BYTES <= 0.02:
            break
        if size < TARGET_BYTES:
            lo = mid + 1
        else:
            hi = mid - 1

    final_pil.save(out_path, format="JPEG", quality=best_quality, subsampling=0)
    print(f"  -> {out_path}")
    print(f"     quality={best_quality}, {os.path.getsize(out_path)//1024}KB")

print("\n完了！")
