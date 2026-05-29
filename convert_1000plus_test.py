import pandas as pd
import dataframe_image as dfi
import os, io, tempfile
from PIL import Image, ImageDraw, ImageFont

# --- 設定 ---
INPUT     = r"C:\Users\23-3\Desktop\画像作成\20260411_エスパス稲毛_20S.xlsx"
SPLIT_DIR = r"C:\Users\23-3\Desktop\画像作成\20260411_エスパス稲毛"
OUTPUT_SUFFIX = "_高配分"

DPI             = 150   # 全画像共通の解像度
OTHER_TARGET_KB = 800   # その他の優秀台ピックアップの目標ファイルサイズ（KB）、個別画像は250KB

# ジャグラーシリーズ（convert_filter_batch.py で別途処理するため除外）
JUGGLER_SERIES = {
    "マイジャグV", "ファンキー2", "ゴージャグ3", "ネオアイム", "ハピジャグV",
    "ウルトラミラジャグ", "ジャグラーガールズ", "ミスジャグ", "アイム",
}

# 全台系・高配分の個別画像を作らず+1000枚台のみその他の優秀台へ回す機種
MANUAL_EXCLUDE = {"いざ!番長", "カバネリ"}

# 並び画像で使った台番（優秀台から除外される）
NARABI_BANS = {449, 450, 451}

# RB >= RB_MIN かつ差枚 >= 0 で優秀台に入れる機種
RB_THRESHOLD_MACHINES = {
    "スマスロ北斗の拳", "東京リベンジャーズ", "炎炎ノ消防隊2", "北斗転生2",
    "モンキーターンV", "モンハンライズ", "防振り", "カバネリ海門決戦",
}
RB_MIN    = 15
DIFF_BONUS = 1000

# --- 機種名変換 ---
conv = pd.read_excel(r"C:\Users\23-3\Desktop\画像作成\機種名変換.xlsx", header=1)
name_map = dict(zip(conv.iloc[:, 1], conv.iloc[:, 2]))
name_map_nospace = {str(k).replace(" ", "").replace("\u3000", ""): v
                    for k, v in name_map.items()}

def convert_name(name):
    if name in name_map: return name_map[name]
    key = str(name).replace(" ", "").replace("\u3000", "")
    if key in name_map_nospace: return name_map_nospace[key]
    return name

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

def make_safe(name):
    return name.replace("/", "／").replace("\\", "＼").replace(":", "：") \
               .replace("*", "＊").replace("?", "？").replace('"', '\u201d') \
               .replace("<", "＜").replace(">", "＞").replace("|", "｜")

# --- 読み込み ---
df = pd.read_excel(INPUT)
df = df[["台番", "機種名（データサイト表記）", "G数", "BB", "RB", "ART", "差枚"]].copy()
df.columns = ["台番", "機種名", "ゲーム数_raw", "BIG", "REG", "AT", "差枚数"]
df["機種名"] = df["機種名"].apply(convert_name)
diff_raw = df["差枚数"].copy()
df["ゲーム数_rounded"] = df["ゲーム数_raw"].apply(round_games)
df["合算確率"] = df.apply(lambda r: fmt_prob(r["BIG"], r["REG"], r["ゲーム数_rounded"]), axis=1)
df["ゲーム数"] = df["ゲーム数_rounded"].apply(fmt_games)
df["差枚数"]   = df["差枚数"].apply(fmt_diff)

# --- スタイル定数 ---
EVEN_BG     = "white"
ODD_BG      = "white"
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
               ("border", "1px solid #AAAAAA"),
               ("background-color", "white")]},
    {"selector": "table",
     "props": [("border-collapse", "collapse")]},
]

def row_bg(row):
    return [f"background-color: {EVEN_BG if row.name % 2 == 0 else ODD_BG}"] * len(row)

os.makedirs(SPLIT_DIR, exist_ok=True)
generated = 0

# その他の優秀台 収集用
other_rows     = []
other_diff_raw = []

# --- 全機種ループ ---
for machine, group_df in df.groupby("機種名", sort=False):
    if machine in JUGGLER_SERIES:
        continue  # ジャグラーシリーズは convert_filter_batch.py で処理

    if NARABI_BANS:
        group_df = group_df[~group_df["台番"].isin(NARABI_BANS)].copy()
        if group_df.empty:
            continue

    diff_raw_m = diff_raw.loc[group_df.index]
    total      = len(group_df)
    all_plus   = bool((diff_raw_m > 0).all())

    # 全台プラス機種の処理
    if all_plus:
        if machine in MANUAL_EXCLUDE:
            # 手動除外機種: +1000枚以上の台のみその他の優秀台へ
            mask_1000 = diff_raw_m >= 1000
            if mask_1000.any():
                other_rows.append(group_df[mask_1000].copy().reset_index(drop=True))
                other_diff_raw.append(diff_raw_m[mask_1000].reset_index(drop=True))
        elif total == 1 and int(diff_raw_m.iloc[0]) >= 1000:
            # 1台のみ かつ +1000枚以上 → その他の優秀台ピックアップへ追加
            other_rows.append(group_df.copy().reset_index(drop=True))
            other_diff_raw.append(diff_raw_m.reset_index(drop=True))
        # 2台以上は全台系として別途生成済み → スキップ
        continue

    # 以下、非all_plus機種
    # 手動除外機種: +1000枚以上の台のみその他の優秀台へ（高配分個別画像はスキップ）
    if machine in MANUAL_EXCLUDE:
        mask_1000 = diff_raw_m >= 1000
        if mask_1000.any():
            other_rows.append(group_df[mask_1000].copy().reset_index(drop=True))
            other_diff_raw.append(diff_raw_m[mask_1000].reset_index(drop=True))
        continue

    # フィルターマスク（機種によって切り替え）
    if machine in RB_THRESHOLD_MACHINES:
        # G数2000G以上 かつ RB15以上 かつ 差枚>=0（差枚1000枚フォールバックなし）
        mask = (group_df["ゲーム数_rounded"] >= 2000) & (group_df["REG"] >= RB_MIN) & (diff_raw_m >= 0)
    else:
        mask = diff_raw_m >= DIFF_BONUS

    filtered   = group_df[mask].copy().reset_index(drop=True)
    diff_raw_f = diff_raw_m[mask].reset_index(drop=True)
    count_f    = len(filtered)

    if count_f == 0:
        continue

    # 条件未満 → その他の優秀台に回す
    if count_f < total / 2:
        other_rows.append(filtered.copy())
        other_diff_raw.append(diff_raw_f.copy())
        continue

    # 1台のみ → 個別画像は作らず その他の優秀台に回す
    if count_f == 1:
        other_rows.append(filtered.copy())
        other_diff_raw.append(diff_raw_f.copy())
        continue

    print(f"{machine}: {count_f}/{total}台 → 生成")

    def diff_color_f(row, _d=diff_raw_f):
        styles = [""] * len(row)
        idx = list(row.index).index("差枚数")
        try:
            n = int(_d.iloc[row.name])
            c = PLUS_COLOR if n > 0 else (MINUS_COLOR if n < 0 else ZERO_COLOR)
        except:
            c = ZERO_COLOR
        styles[idx] = f"color: {c}; text-align: right;"
        return styles

    active_cols = [c for c in ["BIG", "REG", "AT"] if not (filtered[c] == 0).all()]
    disp_cols   = ["台番", "機種名", "ゲーム数"] + active_cols + ["合算確率", "差枚数"]
    group       = filtered[disp_cols]

    styled_s = group.style.hide(axis="index").apply(row_bg, axis=1).apply(diff_color_f, axis=1)
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
    dfi.export(styled_s, tmp_table, dpi=DPI, max_rows=-1,
               table_conversion="playwright", fontsize=14)

    top_img = Image.open(tmp_table).convert("RGBA")
    top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
    w = top_img.width
    os.unlink(tmp_table)

    bar_h  = 62
    line_h = 6
    font_size_bar = round(bar_h * 0.58)
    blue_bar = Image.new("RGBA", (w, bar_h),  (47, 85, 164, 255))
    red_line = Image.new("RGBA", (w, line_h), (204, 0, 0, 255))
    bar_draw = ImageDraw.Draw(blue_bar)

    try:
        bar_font = ImageFont.truetype(
            r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf",
            font_size_bar)
    except Exception:
        bar_font = ImageFont.load_default()

    title_name = machine.replace('\uff65', '\u30fb').strip()
    title_sub  = "（優秀台）"
    gap = -22
    b1 = bar_draw.textbbox((0, 0), title_name, font=bar_font)
    b2 = bar_draw.textbbox((0, 0), title_sub,  font=bar_font)
    w1, w2 = b1[2]-b1[0], b2[2]-b2[0]
    total_w = w1 + gap + w2
    x1 = (w - total_w) // 2 - b1[0]
    x2 = x1 + w1 + gap - b2[0]
    ty = (bar_h - (b1[3]-b1[1])) // 2 - b1[1]
    bar_draw.text((x1, ty), title_name, fill=(255,255,255,255), font=bar_font)
    bar_draw.text((x2, ty), title_sub,  fill=(255,255,255,255), font=bar_font)

    total_h = bar_h + line_h + top_img.height
    canvas = Image.new("RGBA", (w, total_h), (255,255,255,255))
    canvas.paste(blue_bar, (0, 0))
    canvas.paste(red_line, (0, bar_h))
    canvas.paste(top_img,  (0, bar_h + line_h))
    # 最下段の罫線
    ImageDraw.Draw(canvas).line([(0, total_h-1), (w-1, total_h-1)], fill=(170,170,170,255), width=1)
    final_pil = canvas.convert("RGB")

    out_path = os.path.join(SPLIT_DIR, f"{make_safe(machine)}{OUTPUT_SUFFIX}.jpg")
    TARGET_BYTES = 250 * 1024
    lo, hi, best_q, best_d = 1, 95, 85, float("inf")
    for _ in range(15):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        final_pil.save(buf, format="JPEG", quality=mid, subsampling=0)
        size = buf.tell()
        d = abs(size - TARGET_BYTES)
        if d < best_d: best_d, best_q = d, mid
        if d / TARGET_BYTES <= 0.02: break
        if size < TARGET_BYTES: lo = mid + 1
        else:                   hi = mid - 1

    final_pil.save(out_path, format="JPEG", quality=best_q, subsampling=0)
    print(f"  -> {out_path}  (quality={best_q}, {os.path.getsize(out_path)//1024}KB)")
    generated += 1

print(f"\n個別画像: {generated}機種")

# ジャグラーシリーズ5台以下のオーバーフロー分を取り込む
import pickle
JUGGLER_OVERFLOW = os.path.join(SPLIT_DIR, "_juggler_overflow.pkl")
if os.path.exists(JUGGLER_OVERFLOW):
    with open(JUGGLER_OVERFLOW, "rb") as f:
        jug_df, jug_diff = pickle.load(f)
    other_rows.append(jug_df)
    other_diff_raw.append(jug_diff)
    print(f"ジャグラーオーバーフロー: {len(jug_df)}台をその他の優秀台ピックアップへ追加")

# =====================================================================
# --- その他の優秀台（統合画像）---
# =====================================================================
if not other_rows:
    print("その他の優秀台: 該当台なし")
else:
    OTHER_OUTPUT = os.path.join(SPLIT_DIR, "その他の優秀台ピックアップ.jpg")
    OTHER_TITLE  = "その他の優秀台ピックアップ"

    other_combined  = pd.concat(other_rows,     ignore_index=True)
    other_diff_all  = pd.concat(other_diff_raw, ignore_index=True)

    # 台番順に並び替え
    sort_order      = other_combined["台番"].argsort()
    other_combined  = other_combined.iloc[sort_order].reset_index(drop=True)
    other_diff_all  = other_diff_all.iloc[sort_order].reset_index(drop=True)

    print(f"その他の優秀台: {len(other_combined)}台")

    def diff_color_other(row, _d=other_diff_all):
        styles = [""] * len(row)
        idx = list(row.index).index("差枚数")
        try:
            n = int(_d.iloc[row.name])
            c = PLUS_COLOR if n > 0 else (MINUS_COLOR if n < 0 else ZERO_COLOR)
        except:
            c = ZERO_COLOR
        styles[idx] = f"color: {c}; text-align: right;"
        return styles

    active_cols_o = [c for c in ["BIG", "REG", "AT"] if not (other_combined[c] == 0).all()]
    disp_cols_o   = ["台番", "機種名", "ゲーム数"] + active_cols_o + ["合算確率", "差枚数"]
    group_o       = other_combined[disp_cols_o]

    styled_o = group_o.style.hide(axis="index").apply(row_bg, axis=1).apply(diff_color_other, axis=1)
    styled_o = (
        styled_o
        .set_properties(subset=["台番"],     **{"text-align": "center"})
        .set_properties(subset=["機種名"],   **{"text-align": "center", "width": "170px"})
        .set_properties(subset=["ゲーム数"], **{"text-align": "center"})
        .set_properties(subset=["合算確率"], **{"text-align": "center", "width": "80px"})
        .set_properties(subset=["差枚数"],   **{"width": "90px", "white-space": "nowrap"})
        .set_table_styles(TABLE_STYLES)
    )
    if active_cols_o:
        styled_o = styled_o.set_properties(
            subset=active_cols_o, **{"width": "40px", "text-align": "center"})

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_o = f.name
    dfi.export(styled_o, tmp_o, dpi=DPI, max_rows=-1,
               table_conversion="playwright", fontsize=14)

    top_img = Image.open(tmp_o).convert("RGBA")
    top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
    w = top_img.width
    os.unlink(tmp_o)

    bar_h  = 62
    line_h = 6
    font_size_bar = round(bar_h * 0.58)
    blue_bar = Image.new("RGBA", (w, bar_h),  (47, 85, 164, 255))
    red_line = Image.new("RGBA", (w, line_h), (204, 0, 0, 255))
    bar_draw = ImageDraw.Draw(blue_bar)

    try:
        bar_font = ImageFont.truetype(
            r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf",
            font_size_bar)
    except Exception:
        bar_font = ImageFont.load_default()

    bbox = bar_draw.textbbox((0, 0), OTHER_TITLE, font=bar_font)
    tx = (w - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty = (bar_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    bar_draw.text((tx, ty), OTHER_TITLE, fill=(255, 255, 255, 255), font=bar_font)

    total_h = bar_h + line_h + top_img.height
    canvas = Image.new("RGBA", (w, total_h), (255, 255, 255, 255))
    canvas.paste(blue_bar, (0, 0))
    canvas.paste(red_line, (0, bar_h))
    canvas.paste(top_img,  (0, bar_h + line_h))
    # 最下段の罫線
    ImageDraw.Draw(canvas).line([(0, total_h-1), (w-1, total_h-1)], fill=(170,170,170,255), width=1)
    final_o = canvas.convert("RGB")

    TARGET_BYTES = OTHER_TARGET_KB * 1024
    lo, hi, best_q, best_d = 1, 95, 85, float("inf")
    for _ in range(15):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        final_o.save(buf, format="JPEG", quality=mid, subsampling=0)
        size = buf.tell()
        d = abs(size - TARGET_BYTES)
        if d < best_d: best_d, best_q = d, mid
        if d / TARGET_BYTES <= 0.02: break
        if size < TARGET_BYTES: lo = mid + 1
        else:                   hi = mid - 1

    final_o.save(OTHER_OUTPUT, format="JPEG", quality=best_q, subsampling=0)
    print(f"  -> {OTHER_OUTPUT}  (quality={best_q}, {os.path.getsize(OTHER_OUTPUT)//1024}KB)")
