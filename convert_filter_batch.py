import pandas as pd
import dataframe_image as dfi
import os, io, tempfile
from PIL import Image, ImageDraw, ImageFont

# =====================================================================
# --- 設定 ---
# =====================================================================
INPUT     = r"C:\Users\23-3\Desktop\画像作成\20260411_エスパス稲毛_20S.xlsx"
SPLIT_DIR = r"C:\Users\23-3\Desktop\画像作成\20260411_エスパス稲毛"

# 機種名・合算確率閾値・差枚ボーナス閾値
JOBS = [
    ("マイジャグV",       136, 1000),
    ("ファンキー2",       141, 1000),
    ("ゴージャグ3",       131, 1000),
    ("アイム",            143, 1000),
    ("ネオアイム",        143, 1000),
    ("ハピジャグV",       138, 1000),
    ("ウルトラミラジャグ", 139, 1000),
    ("ジャグラーガールズ", 133, 1000),
    ("ミスジャグ",        135, 1000),
]

JUGGLER_OUTPUT   = os.path.join(SPLIT_DIR, "ジャグラーシリーズ優秀台.jpg")
JUGGLER_TITLE    = "その他のジャグラーシリーズの優秀台"
JUGGLER_OVERFLOW = os.path.join(SPLIT_DIR, "_juggler_overflow.pkl")

# 高配分個別画像を作らず+1000枚台をその他の優秀台へ回す機種（毎回必要に応じて設定）
MANUAL_EXCLUDE = set()

# 並び画像で使った台番（ジャグラーの優秀台から除外される）
NARABI_BANS = {449, 450, 451}

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
               ("border", "1px solid #AAAAAA"),
               ("background-color", "white")]},
    {"selector": "table",
     "props": [("border-collapse", "collapse")]},
]

def row_bg(row):
    return [f"background-color: {EVEN_BG if row.name % 2 == 0 else ODD_BG}"] * len(row)

def make_title_bar(w, text, sub=None):
    """青バー＋赤ライン画像を返す。subあり=2パーツ、なし=センタリング1パーツ"""
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

    if sub:
        gap = -22
        b1 = bar_draw.textbbox((0, 0), text, font=bar_font)
        b2 = bar_draw.textbbox((0, 0), sub,  font=bar_font)
        w1, w2 = b1[2]-b1[0], b2[2]-b2[0]
        total_w = w1 + gap + w2
        x1 = (w - total_w) // 2 - b1[0]
        x2 = x1 + w1 + gap - b2[0]
        ty = (bar_h - (b1[3]-b1[1])) // 2 - b1[1]
        bar_draw.text((x1, ty), text, fill=(255,255,255,255), font=bar_font)
        bar_draw.text((x2, ty), sub,  fill=(255,255,255,255), font=bar_font)
    else:
        bbox = bar_draw.textbbox((0, 0), text, font=bar_font)
        tx = (w - (bbox[2]-bbox[0])) // 2 - bbox[0]
        ty = (bar_h - (bbox[3]-bbox[1])) // 2 - bbox[1]
        bar_draw.text((tx, ty), text, fill=(255,255,255,255), font=bar_font)

    return blue_bar, red_line, bar_h, line_h

def attach_title(table_img, text, sub=None):
    """テーブル画像の上にタイトルバーを合成して返す"""
    w = table_img.width
    blue_bar, red_line, bar_h, line_h = make_title_bar(w, text, sub)
    total_h = bar_h + line_h + table_img.height
    canvas = Image.new("RGBA", (w, total_h), (255,255,255,255))
    canvas.paste(blue_bar, (0, 0))
    canvas.paste(red_line, (0, bar_h))
    canvas.paste(table_img, (0, bar_h + line_h))
    # 最下段の罫線
    d = ImageDraw.Draw(canvas)
    d.line([(0, total_h-1), (w-1, total_h-1)], fill=(170,170,170,255), width=1)
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

DISPLAY_COLS = ["台番", "機種名", "ゲーム数", "BIG", "REG", "AT", "合算確率", "差枚数"]

_all_rows     = []
_all_diff_raw = []

# =====================================================================
# --- 機種別ループ ---
# =====================================================================
JUGGLER_G_MIN = 2000  # ジャグラーシリーズは2000G以上の台のみ対象

for machine, PROB_THRESHOLD, DIFF_BONUS in JOBS:
    all_for_machine = df[df["機種名"] == machine]
    if NARABI_BANS:
        all_for_machine = all_for_machine[~all_for_machine["台番"].isin(NARABI_BANS)]
    total_all = len(all_for_machine)  # NARABI_BANS除外後・2000Gフィルター前の全台数
    mdf = all_for_machine[all_for_machine["ゲーム数_rounded"] >= JUGGLER_G_MIN]
    if mdf.empty:
        print(f"[スキップ] '{machine}' はこのExcelにありません")
        continue

    diff_raw_m = diff_raw.loc[mdf.index]

    # 全台プラス → メインスクリプトで全台系画像生成済みのため高配分はスキップ
    if bool((diff_raw_m > 0).all()):
        print(f"  -> {machine} 全台プラスのため高配分スキップ（全台系画像あり）")
        continue

    mask = ((mdf["合算確率_num"] <= PROB_THRESHOLD) & (diff_raw_m >= 0)) | (diff_raw_m >= DIFF_BONUS)
    filtered   = mdf[mask].copy().reset_index(drop=True)
    diff_raw_f = diff_raw_m[mask].reset_index(drop=True)

    print(f"{machine} 全台数: {total_all}　フィルター後: {len(filtered)}台")
    if filtered.empty:
        print(f"  -> 該当台なし。スキップ")
        continue

    # 手動除外機種: +1000枚以上の台のみoverflowへ → その他の優秀台ピックアップに追加される
    if machine in MANUAL_EXCLUDE:
        mask_1000 = diff_raw_m >= 1000
        if mask_1000.any():
            _all_rows.append(mdf[mask_1000].copy().reset_index(drop=True))
            _all_diff_raw.append(diff_raw_m[mask_1000].reset_index(drop=True))
            print(f"  -> 手動除外: +1000枚台 {mask_1000.sum()}台をoverflowへ")
        else:
            print(f"  -> 手動除外: +1000枚台なし、スキップ")
        continue

    # 1台のみ、または「半数未満かつ10台未満」→ 個別画像は作らず統合画像へ
    # ※半数判定は2000Gフィルター前の全台数(total_all)に対して行う
    if len(filtered) == 1 or (len(filtered) < total_all / 2 and len(filtered) < 10):
        print(f"  -> {len(filtered)}/{total_all}台（個別画像スキップ）")
        _all_rows.append(filtered.copy())
        _all_diff_raw.append(diff_raw_f.copy())
        continue

    # 半数以上、または10台以上 → 個別画像生成（統合画像には含めない）

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
    dfi.export(styled_s, tmp_table, dpi=150, max_rows=-1,
               table_conversion="playwright", fontsize=14)

    top_img = Image.open(tmp_table).convert("RGBA")
    top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
    os.unlink(tmp_table)

    final_img = attach_title(top_img, machine.replace('\uff65', '\u30fb'), "（優秀台）")
    final_pil = final_img.convert("RGB")

    out_path = os.path.join(SPLIT_DIR, f"{make_safe(machine)}_高配分.jpg")
    q = save_jpeg(final_pil, out_path)
    print(f"  -> {out_path}  (quality={q}, {os.path.getsize(out_path)//1024}KB)")

# =====================================================================
# --- 統合画像：ジャグラーシリーズの優秀台 ---
# =====================================================================
if not _all_rows:
    print("\n統合画像: 該当台なし。スキップ")
    if os.path.exists(JUGGLER_OVERFLOW):
        os.remove(JUGGLER_OVERFLOW)
else:
    combined     = pd.concat(_all_rows,     ignore_index=True)
    diff_raw_all = pd.concat(_all_diff_raw, ignore_index=True)

    sort_order   = combined["台番"].argsort()
    combined     = combined.iloc[sort_order].reset_index(drop=True)
    diff_raw_all = diff_raw_all.iloc[sort_order].reset_index(drop=True)

    print(f"\n統合画像: {len(combined)}台")

    # 5台以下 → ジャグラーシリーズ優秀台は作らず全台をその他へ渡す
    if len(combined) <= 5:
        import pickle
        overflow_df   = combined.reset_index(drop=True)
        overflow_diff = diff_raw_all.reset_index(drop=True)
        if os.path.exists(JUGGLER_OUTPUT):
            os.remove(JUGGLER_OUTPUT)
        if not overflow_df.empty:
            with open(JUGGLER_OVERFLOW, "wb") as f:
                pickle.dump((overflow_df, overflow_diff), f)
            print(f"  -> 5台以下のためジャグラーシリーズ優秀台スキップ。{len(overflow_df)}台をその他の優秀台ピックアップへ")
        else:
            if os.path.exists(JUGGLER_OVERFLOW):
                os.remove(JUGGLER_OVERFLOW)
            print("  -> 5台以下かつ該当台なし。スキップ")
    else:
        if os.path.exists(JUGGLER_OVERFLOW):
            os.remove(JUGGLER_OVERFLOW)

        def diff_color_all(row, _d=diff_raw_all):
            styles = [""] * len(row)
            idx = list(row.index).index("差枚数")
            try:
                n = int(_d.iloc[row.name])
                c = PLUS_COLOR if n > 0 else (MINUS_COLOR if n < 0 else ZERO_COLOR)
            except:
                c = ZERO_COLOR
            styles[idx] = f"color: {c}; text-align: right;"
            return styles

        active_cols_all = [c for c in ["BIG", "REG", "AT"] if not (combined[c] == 0).all()]
        disp_cols_all   = ["台番", "機種名", "ゲーム数"] + active_cols_all + ["合算確率", "差枚数"]
        group_all       = combined[disp_cols_all]

        styled_all = group_all.style.hide(axis="index").apply(row_bg, axis=1).apply(diff_color_all, axis=1)
        styled_all = (
            styled_all
            .set_properties(subset=["台番"],     **{"text-align": "center"})
            .set_properties(subset=["機種名"],   **{"text-align": "center", "width": "170px"})
            .set_properties(subset=["ゲーム数"], **{"text-align": "center"})
            .set_properties(subset=["合算確率"], **{"text-align": "center", "width": "80px"})
            .set_properties(subset=["差枚数"],   **{"width": "90px", "white-space": "nowrap"})
            .set_table_styles(TABLE_STYLES)
        )
        if active_cols_all:
            styled_all = styled_all.set_properties(
                subset=active_cols_all, **{"width": "40px", "text-align": "center"})

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            tmp_all = f.name
        dfi.export(styled_all, tmp_all, dpi=150, max_rows=-1,
                   table_conversion="playwright", fontsize=14)

        top_img = Image.open(tmp_all).convert("RGBA")
        top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
        os.unlink(tmp_all)

        final_all = attach_title(top_img, JUGGLER_TITLE).convert("RGB")
        q = save_jpeg(final_all, JUGGLER_OUTPUT)
        print(f"  -> {JUGGLER_OUTPUT}  (quality={q}, {os.path.getsize(JUGGLER_OUTPUT)//1024}KB)")
