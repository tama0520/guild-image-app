import pandas as pd
import dataframe_image as dfi
import os, io, tempfile
from PIL import Image, ImageDraw, ImageFont

# =====================================================================
# --- 設定 ---
# =====================================================================
INPUT     = r"C:\Users\23-3\Desktop\画像作成\20260414_エスパス上野新館_20S.xlsx"
SPLIT_DIR = r"C:\Users\23-3\Desktop\画像作成\20260414_エスパス上野新館"

TAIL_DIGIT = 5  # 末尾番号（0〜9）

# ジャグラーシリーズ：合算確率閾値付きフィルター
JUGGLER_THRESHOLDS = {
    "マイジャグV":        136,
    "ファンキー2":        141,
    "ゴージャグ3":        131,
    "アイム":             143,
    "ネオアイム":         143,
    "ハピジャグV":        138,
    "ウルトラミラジャグ":  139,
    "ジャグラーガールズ":  133,
    "ミスジャグ":         135,
}
DIFF_BONUS = 1000  # 差枚がこれ以上なら確率に関係なく含める

# RB>=15 かつ差枚>=0 で優秀台に入れる機種
RB_THRESHOLD_MACHINES = {
    "スマスロ北斗の拳",
    "東京リベンジャーズ",
    "炎炎ノ消防隊2",
    "北斗転生2",
    "モンキーターンV",
    "モンハンライズ",
    "防振り",
    "カバネリ海門決戦",
}
RB_MIN = 15  # RB下限

# =====================================================================
# --- 共通関数・定数 ---
# =====================================================================
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

def save_jpeg(pil_img, path, target_kb=250):
    TARGET_BYTES = target_kb * 1024
    lo, hi, best_q, best_d = 1, 95, 85, float("inf")
    for _ in range(15):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        pil_img.save(buf, format="JPEG", quality=mid, subsampling=0)
        size = buf.tell()
        d = abs(size - TARGET_BYTES)
        if d < best_d: best_d, best_q = d, mid
        if d / TARGET_BYTES <= 0.02: break
        if size < TARGET_BYTES: lo = mid + 1
        else:                   hi = mid - 1
    pil_img.save(path, format="JPEG", quality=best_q, subsampling=0)
    return best_q

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
               ("border", "1px solid #AAAAAA")]},
    {"selector": "table",
     "props": [("border-collapse", "collapse")]},
]

def row_bg(row):
    return [f"background-color: {EVEN_BG if row.name % 2 == 0 else ODD_BG}"] * len(row)

FONT_PATH = r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf"

# 丸付き数字マップ（0〜9）
CIRCLED_DIGITS = {
    0: "⓪", 1: "①", 2: "②", 3: "③", 4: "④",
    5: "⑤", 6: "⑥", 7: "⑦", 8: "⑧", 9: "⑨",
}

def make_tail_title_bar(w, tail_digit):
    """
    末尾番台タイトルバーを生成。
    タイトル: 「末尾⑤番台の優秀台」（丸付き数字Unicode・センタリング）
    """
    bar_h     = 62   # 30pt @ 150dpi
    line_h    = 6    # 3pt  @ 150dpi
    font_size = round(bar_h * 0.58)   # ≈ 36px

    blue_bar = Image.new("RGBA", (w, bar_h),  (47, 85, 164, 255))
    red_line = Image.new("RGBA", (w, line_h), (204, 0, 0, 255))
    d        = ImageDraw.Draw(blue_bar)

    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()

    circled  = CIRCLED_DIGITS.get(tail_digit % 10, str(tail_digit))
    title    = f"末尾{circled}番台の優秀台"

    bbox = d.textbbox((0, 0), title, font=font)
    tx   = (w - (bbox[2] - bbox[0])) // 2 - bbox[0]
    ty   = (bar_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
    d.text((tx, ty), title, fill=(255, 255, 255, 255), font=font)

    return blue_bar, red_line, bar_h, line_h

def attach_tail_title(table_img, tail_digit):
    """テーブル画像の上に末尾番台タイトルバーを合成して返す"""
    w = table_img.width
    blue_bar, red_line, bar_h, line_h = make_tail_title_bar(w, tail_digit)
    total_h = bar_h + line_h + table_img.height
    canvas  = Image.new("RGBA", (w, total_h), (255, 255, 255, 255))
    canvas.paste(blue_bar,   (0, 0))
    canvas.paste(red_line,   (0, bar_h))
    canvas.paste(table_img,  (0, bar_h + line_h))
    return canvas

# =====================================================================
# --- Excel 読み込み ---
# =====================================================================
os.makedirs(SPLIT_DIR, exist_ok=True)

df = pd.read_excel(INPUT)
df = df[["台番", "機種名（データサイト表記）", "G数", "BB", "RB", "ART", "差枚"]].copy()
df.columns = ["台番", "機種名", "ゲーム数_raw", "BIG", "REG", "AT", "差枚数"]
df["機種名"] = df["機種名"].apply(convert_name)
diff_raw = df["差枚数"].copy()
df["ゲーム数_rounded"] = df["ゲーム数_raw"].apply(round_games)
df["合算確率_num"] = df.apply(
    lambda r: r["ゲーム数_rounded"] / (r["BIG"] + r["REG"])
              if (r["BIG"] + r["REG"]) > 0 else float("inf"), axis=1)
df["合算確率"] = df.apply(
    lambda r: fmt_prob(r["BIG"], r["REG"], r["ゲーム数_rounded"]), axis=1)
df["ゲーム数"] = df["ゲーム数_rounded"].apply(fmt_games)
df["差枚数"]   = df["差枚数"].apply(fmt_diff)

# =====================================================================
# --- 末尾フィルター ---
# =====================================================================
# 台番の末尾が TAIL_DIGIT の台だけ抽出
tail_mask = df["台番"].apply(lambda x: int(x) % 10 == TAIL_DIGIT)
df_tail      = df[tail_mask].copy()
diff_tail    = diff_raw[tail_mask].copy()

# 各行にフィルター条件を適用
keep_idx = []
for idx, row in df_tail.iterrows():
    d       = int(diff_tail.loc[idx])
    machine = row["機種名"]
    if machine in JUGGLER_THRESHOLDS:
        # ジャグラー：確率フィルター（差枚>=0）OR +DIFF_BONUS以上
        thr  = JUGGLER_THRESHOLDS[machine]
        prob = row["合算確率_num"]
        if (prob <= thr and d >= 0) or d >= DIFF_BONUS:
            keep_idx.append(idx)
    elif machine in RB_THRESHOLD_MACHINES:
        # RB閾値機種：RB>=RB_MIN かつ差枚>=0、OR +DIFF_BONUS以上
        rb = int(row["REG"])
        if (rb >= RB_MIN and d >= 0) or d >= DIFF_BONUS:
            keep_idx.append(idx)
    else:
        # その他：+DIFF_BONUS以上のみ
        if d >= DIFF_BONUS:
            keep_idx.append(idx)

filtered     = df_tail.loc[keep_idx].copy().reset_index(drop=True)
diff_filt    = diff_tail.loc[keep_idx].reset_index(drop=True)

print(f"末尾{TAIL_DIGIT}番台 全台数: {len(df_tail)}台 → 優秀台フィルター後: {len(filtered)}台")

if filtered.empty:
    print("該当台なし。画像は生成しません。")
else:
    # 台番昇順でソート
    sort_order  = filtered["台番"].argsort()
    filtered    = filtered.iloc[sort_order].reset_index(drop=True)
    diff_filt   = diff_filt.iloc[sort_order].reset_index(drop=True)

    # BIG/REG/AT で全行0の列を除外
    active_cols = [c for c in ["BIG", "REG", "AT"] if not (filtered[c] == 0).all()]
    disp_cols   = ["台番", "機種名", "ゲーム数"] + active_cols + ["合算確率", "差枚数"]
    group       = filtered[disp_cols]

    def diff_color_f(row, _d=diff_filt):
        styles = [""] * len(row)
        idx = list(row.index).index("差枚数")
        try:
            n = int(_d.iloc[row.name])
            c = PLUS_COLOR if n > 0 else (MINUS_COLOR if n < 0 else ZERO_COLOR)
        except:
            c = ZERO_COLOR
        styles[idx] = f"color: {c}; text-align: right;"
        return styles

    styled_f = group.style.hide(axis="index").apply(row_bg, axis=1).apply(diff_color_f, axis=1)
    styled_f = (
        styled_f
        .set_properties(subset=["台番"],     **{"text-align": "center"})
        .set_properties(subset=["機種名"],   **{"text-align": "center", "width": "170px"})
        .set_properties(subset=["ゲーム数"], **{"text-align": "center"})
        .set_properties(subset=["合算確率"], **{"text-align": "center", "width": "80px"})
        .set_properties(subset=["差枚数"],   **{"width": "90px", "white-space": "nowrap"})
        .set_table_styles(TABLE_STYLES)
    )
    if active_cols:
        styled_f = styled_f.set_properties(
            subset=active_cols, **{"width": "40px", "text-align": "center"})

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        tmp_table = f.name
    dfi.export(styled_f, tmp_table, dpi=150, max_rows=-1,
               table_conversion="playwright", fontsize=14)

    top_img = Image.open(tmp_table).convert("RGBA")
    top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
    os.unlink(tmp_table)

    final_img = attach_tail_title(top_img, TAIL_DIGIT).convert("RGB")

    out_path = os.path.join(SPLIT_DIR, f"末尾{TAIL_DIGIT}番台の優秀台.jpg")
    q = save_jpeg(final_img, out_path)
    print(f"-> {out_path}  (quality={q}, {os.path.getsize(out_path)//1024}KB)")
