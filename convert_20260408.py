import pandas as pd
import dataframe_image as dfi

# --- 入力・出力 ---
INPUT  = r"C:\Users\23-3\Desktop\画像作成\20260404_エスパス上野新館_20S.xlsx"
OUTPUT = r"C:\Users\23-3\Desktop\画像作成\20260404_エスパス上野新館_20S.png"

# --- 機種名変換テーブル読み込み ---
conv = pd.read_excel(r"C:\Users\23-3\Desktop\画像作成\機種名変換.xlsx", header=1)
# 完全一致マップ
name_map = dict(zip(conv.iloc[:, 1], conv.iloc[:, 2]))
# スペース除去で正規化したマップ（完全一致で見つからない場合のフォールバック）
name_map_nospace = {str(k).replace(" ", "").replace("\u3000", ""): v
                    for k, v in name_map.items()}

# --- 読み込み（列名で参照） ---
df = pd.read_excel(INPUT)
df = df[["台番", "機種名（データサイト表記）", "G数", "BB", "RB", "ART", "差枚"]].copy()
df.columns = ["台番", "機種名", "ゲーム数_raw", "BIG", "REG", "AT", "差枚数"]

def convert_name(name):
    if name in name_map:
        return name_map[name]
    key = str(name).replace(" ", "").replace("\u3000", "")
    if key in name_map_nospace:
        return name_map_nospace[key]
    return name

df["機種名"] = df["機種名"].apply(convert_name)

# --- 書式 ---
def round_games(v):
    n = int(v); r = n % 100
    if r <= 24:   return (n // 100) * 100
    elif r <= 74: return (n // 100) * 100 + 50
    else:         return (n // 100 + 1) * 100

def fmt_games(v):
    try:
        return f"{int(v):,}G"
    except:
        return str(v)

def fmt_diff(v):
    try:
        n = int(v)
        if n > 0:
            return f"+{n:,}枚"
        elif n < 0:
            return f"{n:,}枚"
        else:
            return "±0枚"
    except:
        return str(v)

def fmt_prob(bb, rb, g_rounded):
    total = bb + rb
    if total == 0: return "───"
    return f"1/{g_rounded / total:.1f}"

diff_raw = df["差枚数"].copy()
df["ゲーム数_rounded"] = df["ゲーム数_raw"].apply(round_games)
df["合算確率"] = df.apply(
    lambda r: fmt_prob(r["BIG"], r["REG"], r["ゲーム数_rounded"]), axis=1)
df["ゲーム数"] = df["ゲーム数_rounded"].apply(fmt_games)
df["差枚数"]  = df["差枚数"].apply(fmt_diff)

# --- スタイル関数 ---
HEADER_BG   = "#4472C4"
EVEN_BG     = "white"
ODD_BG      = "white"
SUMMARY_BG  = "#DDDDDD"
PLUS_COLOR  = "#0000CC"
MINUS_COLOR = "#CC0000"
ZERO_COLOR  = "#000000"

def row_bg(row):
    bg = EVEN_BG if row.name % 2 == 0 else ODD_BG
    return [f"background-color: {bg}"] * len(row)

def diff_color(row):
    styles = [""] * len(row)
    idx = list(row.index).index("差枚数")
    try:
        n = int(diff_raw.iloc[row.name])
        if n > 0:
            c = PLUS_COLOR
        elif n < 0:
            c = MINUS_COLOR
        else:
            c = ZERO_COLOR
    except:
        c = ZERO_COLOR
    styles[idx] = f"color: {c}; text-align: right;"
    return styles

DISPLAY_COLS = ["台番", "機種名", "ゲーム数", "BIG", "REG", "AT", "合算確率", "差枚数"]

styled = (
    df[DISPLAY_COLS].style
    .hide(axis="index")
    .apply(row_bg, axis=1)
    .apply(diff_color, axis=1)
    .set_properties(subset=["機種名"], **{"text-align": "center", "width": "170px"})
    .set_properties(subset=["ゲーム数"], **{"text-align": "center"})
    .set_properties(subset=["合算確率"], **{"text-align": "center", "width": "80px"})
    .set_properties(subset=["BIG", "REG", "AT"],
                    **{"width": "40px", "text-align": "center"})
    .set_properties(subset=["差枚数"], **{"width": "90px", "white-space": "nowrap"})
    .set_table_styles([
        {"selector": "thead th",
         "props": [("background-color", HEADER_BG),
                   ("color", "white"),
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
    ])
)

# --- 出力 ---
dfi.export(
    styled,
    OUTPUT,
    dpi=150,
    max_rows=-1,
    table_conversion="playwright",
    fontsize=14,
)

print("Done:", OUTPUT)

# --- 機種別個別画像出力 ---
SPLIT_DIR  = r"C:\Users\23-3\Desktop\画像作成\機種別"
SUMMARY_BG = "#FFB6C1"
import os
os.makedirs(SPLIT_DIR, exist_ok=True)

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

def make_safe(name):
    return name.replace("/", "／").replace("\\", "＼").replace(":", "：") \
               .replace("*", "＊").replace("?", "？").replace('"', '\u201d') \
               .replace("<", "＜").replace(">", "＞").replace("|", "｜")


for machine, group in df.groupby("機種名", sort=False):

    diff_raw_s = diff_raw.loc[group.index].reset_index(drop=True)
    group = group[DISPLAY_COLS].reset_index(drop=True)

    # 集計値
    total_diff  = int(round(diff_raw_s.sum()))
    avg_diff    = int(round(diff_raw_s.mean()))
    win_count   = int((diff_raw_s > 0).sum())
    total_count = len(diff_raw_s)
    win_rate    = win_count / total_count * 100
    all_plus    = bool((diff_raw_s > 0).all())
    summary_text = (
        f"総差枚：{fmt_diff(total_diff)}　"
        f"平均：{fmt_diff(avg_diff)}　"
        f"勝率：{win_rate:.1f}%（{win_count}/{total_count}台）"
    )

    def diff_color_s(row, _diff_raw=diff_raw_s):
        styles = [""] * len(row)
        idx = list(row.index).index("差枚数")
        try:
            n = int(_diff_raw.iloc[row.name])
            c = PLUS_COLOR if n > 0 else (MINUS_COLOR if n < 0 else ZERO_COLOR)
        except:
            c = ZERO_COLOR
        styles[idx] = f"color: {c}; text-align: right;"
        return styles

    # BIG/REG/AT で全行0の列を除外
    active_cols = [c for c in ["BIG", "REG", "AT"] if not (group[c] == 0).all()]
    disp_cols   = ["台番", "機種名", "ゲーム数"] + active_cols + ["合算確率", "差枚数"]
    group       = group[disp_cols]

    # テーブル画像（一時ファイル）
    import tempfile
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

    # 結合：テーブル画像を読み込んでサマリーバーをPILで直接描画
    from PIL import Image, ImageDraw, ImageFont
    top_img = Image.open(tmp_table).convert("RGBA")

    # テーブル下端の罫線をトリム
    top_img = top_img.crop((0, 0, top_img.width, top_img.height - 2))
    w = top_img.width

    # --- タイトルバー（青バー＋赤ライン）---
    bar_h  = 62   # 30pt @ 150dpi
    line_h = 6    # 3pt  @ 150dpi
    font_size_bar = round(bar_h * 0.58)   # ≈ 36px

    blue_bar  = Image.new("RGBA", (w, bar_h),  (47, 85, 164, 255))
    red_line  = Image.new("RGBA", (w, line_h), (204, 0, 0, 255))
    bar_draw  = ImageDraw.Draw(blue_bar)

    try:
        bar_font = ImageFont.truetype(
            r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf",
            font_size_bar)
    except Exception:
        bar_font = ImageFont.load_default()

    # 文字化け対策（半角中点→全角中点）
    title_name = machine.replace('\uff65', '\u30fb')
    if all_plus:
        title_text = title_name
        # センタリング（1パーツ）
        bbox = bar_draw.textbbox((0, 0), title_text, font=bar_font)
        tx = (w - (bbox[2] - bbox[0])) // 2 - bbox[0]
        ty = (bar_h - (bbox[3] - bbox[1])) // 2 - bbox[1]
        bar_draw.text((tx, ty), title_text, fill=(255, 255, 255, 255), font=bar_font)
    else:
        # 2パーツ描画（機種名＋「（優秀台）」、gap=-22px）
        part1 = title_name
        part2 = "（優秀台）"
        gap   = -22
        b1 = bar_draw.textbbox((0, 0), part1, font=bar_font)
        b2 = bar_draw.textbbox((0, 0), part2, font=bar_font)
        w1 = b1[2] - b1[0]
        w2 = b2[2] - b2[0]
        total_w = w1 + gap + w2
        x1 = (w - total_w) // 2 - b1[0]
        x2 = x1 + w1 + gap - b2[0]
        ty = (bar_h - (b1[3] - b1[1])) // 2 - b1[1]
        bar_draw.text((x1, ty), part1, fill=(255, 255, 255, 255), font=bar_font)
        bar_draw.text((x2, ty), part2, fill=(255, 255, 255, 255), font=bar_font)

    # 合成：青バー → 赤ライン → テーブル
    total_h = bar_h + line_h + top_img.height
    canvas = Image.new("RGBA", (w, total_h), (255, 255, 255, 255))
    canvas.paste(blue_bar, (0, 0))
    canvas.paste(red_line, (0, bar_h))
    canvas.paste(top_img,  (0, bar_h + line_h))
    top_img = canvas

    out_path = os.path.join(SPLIT_DIR, f"{make_safe(machine)}.jpg")
    # 旧PNGが残っていれば削除
    old_png = os.path.join(SPLIT_DIR, f"{make_safe(machine)}.png")
    if os.path.exists(old_png):
        os.remove(old_png)

    # (優秀台)タイトル（全台プラスでない）はピンクバーを付けない
    if not all_plus:
        final_pil = top_img.convert("RGB")
    else:
        # サマリーバーの高さ＝データ行1行分の高さ × 1.2（タイトルバー分を除く）
        table_only_h = top_img.height - bar_h - line_h
        base_row_h = max(30, table_only_h // (len(group) + 2))
        row_h = int(base_row_h * 1.2)

        # ピンクの帯を作成
        pink_rgba = tuple(int(SUMMARY_BG.lstrip("#")[i:i+2], 16) for i in (0,2,4)) + (255,)
        bar = Image.new("RGBA", (w, row_h), pink_rgba)
        draw = ImageDraw.Draw(bar)

        # フォントサイズ＝テーブルの14px CSS を dpi=150 で換算
        font_size = round(14 * 150 / 96)  # ≈ 22
        try:
            font = ImageFont.truetype(
                r"C:/Users/23-3/AppData/Local/Microsoft/Windows/Fonts/MochiyPopOne-Regular.ttf",
                font_size)
        except Exception:
            font = ImageFont.load_default()

        # テキストを左寄せ・天地センタリングで描画
        bbox = draw.textbbox((0, 0), summary_text, font=font)
        text_h = bbox[3] - bbox[1]
        y_text = (row_h - text_h) // 2 - bbox[1]
        draw.text((8, y_text), summary_text, fill=(0, 0, 0, 255), font=font)

        # 外枠（上・左・右・下）
        bc = (170, 170, 170, 255)
        draw.line([(0, 0),     (w-1, 0)],     fill=bc, width=1)  # 上
        draw.line([(0, 0),     (0,   row_h-1)], fill=bc, width=1)  # 左
        draw.line([(w-1, 0),   (w-1, row_h-1)], fill=bc, width=1)  # 右
        draw.line([(0, row_h-1), (w-1, row_h-1)], fill=bc, width=1)  # 下

        # 結合
        combined = Image.new("RGBA", (w, top_img.height + row_h), (255,255,255,255))
        combined.paste(top_img, (0, 0))
        combined.paste(bar, (0, top_img.height))
        final_pil = combined.convert("RGB")
    os.unlink(tmp_table)

    # JPEG品質バイナリサーチで250KBに近づける
    import io
    TARGET_BYTES = 250 * 1024
    lo, hi = 1, 95
    best_quality = 85
    best_diff = float("inf")
    for _ in range(15):
        mid = (lo + hi) // 2
        buf = io.BytesIO()
        final_pil.save(buf, format="JPEG", quality=mid, subsampling=0)
        size = buf.tell()
        diff = abs(size - TARGET_BYTES)
        if diff < best_diff:
            best_diff = diff
            best_quality = mid
        if diff / TARGET_BYTES <= 0.02:
            break
        if size < TARGET_BYTES:
            lo = mid + 1
        else:
            hi = mid - 1

    final_pil.save(out_path, format="JPEG", quality=best_quality, subsampling=0)
    final_size = os.path.getsize(out_path)
    print(f"  -> {out_path}  (quality={best_quality}, {final_size//1024}KB)")
