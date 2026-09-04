"""WordPress連携（Phase 2）: エスパス高田馬場の記事用下書きを作成する。

【設計方針】
- streamlit_app.py の既存ロジック（画像生成・抽出・機種名変換・記事用処理）には
  一切触れない。本モジュールは `result` の値を **読むだけ** で本文を組み立てる。
- 画像は ⑧実行後の output_dir にある **最終確定済み実ファイル** をそのまま送る。
  WordPress用に再生成・再圧縮はしない。
  例外は「縦長すぎてWordPress側で幅が潰れる画像」だけで、その場合も
  **原本には触れず、送信専用の一時コピーを分割する**（修正4・C案）。
- ネットワークに触れない純粋関数（`build_payload` / `plan_blocks` / `build_content`
  / `build_title` / `collect_files`）と、送信を行う関数（`upload_media` /
  `create_draft` / `create_takadanobaba_draft`）を明確に分ける。

【正式仕様（2026-08-20 確定）】
- 対象店舗は **高田馬場のみ**。
- status=draft 固定 / categories=[24] / author=14 / tags は送らない /
  featured_media・excerpt・template・meta は設定しない。**publish は絶対にしない。**
- 高配分・ジャグラーの **装飾テキスト一覧（赤文字・青文字）は出力しない**（修正1・3）。
  代わりに記事用ページが生成済みの画像を順番配置する。
- 高配分画像の統合はしない（機種ごとに順番配置）。
- 並びは全て【N台並び】。「列」の自動判定はしない。
- 機種名はアプリが保持している名前をそのまま使う（逆変換しない）。
- All-or-Nothing: 必須ファイルが1つでも欠けたら1枚もアップロードしない。
- 逐次アップロードのみ（並列禁止）。自動リトライはしない。
"""

from __future__ import annotations

import html
import json
import math
import os
import re
import tempfile
import time
from collections import Counter
from urllib.parse import quote, urlsplit, urlunsplit

# ── 投稿設定（正式仕様・変更禁止）──────────────────────────────────
WP_STORE          = "高田馬場"
WP_CATEGORY_ID    = 24                      # エスパス高田馬場
WP_AUTHOR_ID      = 14                      # 58109 と同じ投稿者
WP_STATUS         = "draft"                 # publish は絶対にしない
WP_CATEGORY_SLUG  = "espace-takadanobaba"
WP_UPLOAD_TIMEOUT = 180                     # 実測0.6秒/枚に対し十分な余裕
WP_POST_TIMEOUT   = 60

# ── 店舗別の投稿先カテゴリ ───────────────────────────────────────────
# 接続先（WP_SITE_URL / WP_USER / WP_APP_PASSWORD）は **全店舗共通の1組だけ**で、
# 店舗別の Secrets は無い（同じサイトの別カテゴリへ投稿する）。
# 未登録の店舗は store_category() が None を返し、呼び出し側が送信させない。
# **カテゴリ term_id / slug を推測で入れてはならない**（誤ったカテゴリへ投稿するため）。
# WordPress 管理画面で確認した値だけをここへ追記する。
WP_STORE_CATEGORY: "dict[str, dict]" = {
    "高田馬場": {"id": WP_CATEGORY_ID, "slug": WP_CATEGORY_SLUG},
    # 2026-09-04 に GET /wp-json/wp/v2/categories で実測（参照のみ・変更通信なし）。
    #   id=19 name='エスパス渋谷新館' slug='espace-shibuyashin'
    #   （id=20 は 'エスパス渋谷本館' で別カテゴリ。取り違えないこと）
    "渋谷新館": {"id": 19, "slug": "espace-shibuyashin"},
}


def store_category(store: str) -> "dict | None":
    """店舗の投稿先カテゴリ {"id": int, "slug": str}。未登録なら None。"""
    c = WP_STORE_CATEGORY.get(str(store or ""))
    if not c or not c.get("id") or not c.get("slug"):
        return None
    return c

# ── サイト側の画像縮小仕様（2026-08-20 実測）────────────────────────
# slotterguild3.com は **長辺が 2560px を超える画像を 2560px へ縮小**する。
# 縦横比は保たれるため、保存後の幅 = 2560 * w / h となり、縦長画像ほど幅が潰れる。
#   実測: 6800x6800 → 2560x2560 ／ 1876x5120 → 938x2560
#         1986x11228 → 453x2560 ／ 2160x12091 → 457x2560
# 一方 990x1133 のような通常画像は長辺 < 2560 のため無変換。
# → 各分割片の高さを 2560px 以下に収めれば **縮小されず元の幅が保たれる**。
WP_MAX_SIDE = 2560

# 分割時に1片あたりの高さの上限。WP_MAX_SIDE と同値にすることで縮小を回避する。
WP_SPLIT_MAX_H = WP_MAX_SIDE

# 分割位置を表の行境界へ寄せるときの探索幅（px）と、行境界とみなす色ばらつきの閾値。
_CUT_SEARCH = 200
_UNIFORM_STD = 12

# 分割片のJPEG保存設定（2026-08-20 実測により確定・正式仕様）。
#
# アプリ本体の `_save_jpeg()`（streamlit_app.py）は **subsampling=0（4:4:4）**
# で保存しており、元画像も 4:4:4 である。分割保存で subsampling を省略すると
# PIL 既定の 4:2:0 が適用され、色差信号が縦横1/2に間引かれる。
# これが「台番帯の色が変わる」「画質が荒くなる」の原因だった（実測）。
#
#   現行(4:2:0)        : 平均差 1.449 / 彩度域の平均色差 12.40
#   q95 + subsampling=0: 平均差 0.241 / 彩度域の平均色差  1.66   ← 採用
#   q100 + subsampling=0: 平均差 0.031 / 彩度域の平均色差 0.45（容量が約1.5倍）
#
# リサイズは一切しない（crop のみ）。
_SPLIT_QUALITY = 95
_SPLIT_SUBSAMPLING = 0          # 4:4:4。元画像・_save_jpeg と揃える

# JPEG の DCT ブロックは 8px。切れ目を8の倍数へ合わせると原本と格子が一致し、
# 再エンコード誤差がさらに小さくなる（実測: 平均差 4.556 → 0.540）。
_MCU = 8

# ── 58109 から実測した固定文言・記号（コードポイント確認済み）────────────
H2_ZENDAI   = "全台系濃厚機種が複数"
H2_HIGH     = "1/2系以上の高配分機種が大量"
H2_JUGGLER  = "ジャグからも高配分機種多数！"
H2_SUEBANGAI = "末尾"
H2_NARABI   = "並び・列仕掛けも！"
H2_VARIETY  = "バラエティ"
H2_SONOTA   = "その他単品優秀台も多数"
H2_SHIMAZU  = "シマズをチェック！"

# ── 渋谷新館の記事用にだけ現れるセクション（2026-09-04 追加）──────────────
# 文言は **記事用画面の既存表記をそのまま採用**する（新語を増やさない）:
#   ⑤ オススメ機種の優秀台 ／ ⑥ 差枚数ランキング＆島図（小見出し「差枚数ランキング」「島図」）
# これらは payload に該当キーがある店舗でだけ出る。高田馬場は payload に無いので
# 1ブロックも増えない（本文はバイト単位で従来と一致する）。
H2_OSUSUME  = "オススメ機種の優秀台"
# 差枚数ランキングと島図は **1つのH2へ統合**する（2026-09-04）。
# `&` は raw のままだと Gutenberg のブロック検証で不一致になるため実体参照で持つ
# （表示は「差枚数ランキング&島図」）。
H2_RANK_SHIMAZU = "差枚数ランキング&amp;島図"
# 旧・独立見出し。**本文へは出力しない**が、履歴として定数は残す（`_ARROW_TRI` と同じ扱い）。
H2_RANKING  = "差枚数ランキング"
H2_SHIMAZUZ = "島図"

# ランキング画像と島図画像の間に入れる空段落の数（約5行ぶんの余白）。
# `blk_empty_para()` を使う。**スペーサーブロック・`<br>`連続・`&nbsp;`・CSSは使わない**
# （記事上部のX貼付用空段落と同じ方式に揃える）。
RANK_SHIMAZU_GAP_PARAS = 5

# ジャグラー統合画像の直前へ入れるH3（渋谷新館の記事用のみ）。
# payload["juggler_comb_h3"] が真のときだけ、**統合画像が実在する場合に限り**出す。
# 高田馬場はこのキーを持たないので1ブロックも増えない。
H3_JUGGLER_COMB = "その他のジャグラーシリーズの優秀台"

# ── ななこポスト（渋谷新館の記事用のみ・2026-09-04 追加）────────────────
# 記事上部（Xリンク下文章）の直後・「全台系濃厚機種が複数」H2 の直前に入る。
# 固定文はここで管理し、**ユーザー入力欄にはしない**。
# 可変なのは「前日のななこポストURL」と「ヒント1〜6」だけ。
NANAKO_H2       = "ななこポストに仕掛けのヒントを確認！"
NANAKO_LEAD     = ("前日の夜に配信される渋谷ななこのポストには仕掛けのヒントが"
                   "隠されていることが多く、今回もポストから仕掛けのヒントと"
                   "思しき箇所を複数確認！")
NANAKO_URL_LEAD = "↓前日の夜に配信されたポストがコチラ"
NANAKO_HINT_LEAD = "今回の結果から考えると下記のヒントを確認することができました！"
NANAKO_OUTRO    = ("このように、ななこポストからは連日仕掛けのヒントを確認できているため、"
                   "打ちに行く際は必ずチェックしておきましょう！")
NANAKO_HINT_MARK = "■"          # ヒント行の先頭記号。**この記号だけ赤＋太字**にする
NANAKO_MARK_COLOR = "#e60012"   # ■ の色（インラインstyle。テーマCSSは変更しない）
NANAKO_HINT_COUNT = 6           # ヒント入力欄の数（固定）
BUTTON_TEXT = "店舗情報・過去の結果はコチラ"

# 機種H3の接頭辞（2026-08-25 追加）。**全台系と高配分だけ**に付ける。
# `h3_zendai()` は全台系・高配分・ジャグラー個別高配分の3箇所で共用しているため、
# **関数本体へ足さず呼び出し側で連結する**（ジャグラーへ波及させないため）。
# 括弧は全角隅付き（U+3010 / U+3011）。**機種名との間にスペースを入れない。**
H3_PREFIX_ZENDAI = "【全台系濃厚】"
H3_PREFIX_HIGH   = "【高配分】"

# 58963 実データで確認した「画像を隙間なく縦連結する」SWELLユーティリティクラス。
# 連続画像群のうち **最後の1枚を除く全て** に付与する。
SPLIT_JOIN_CLASS = "u-mb-ctrl u-mb-0"

_ARROW_R    = "&#x27a1;"   # ➡ U+27A1（raw ではHTML実体で保存されている）
_ARROW_R2   = "&#x2192;"   # → U+2192（機種H3・並びH3で共用。_ARROW_R とは別定数）
_ARROW_TRI  = "&#x25b6;"   # ▶ U+25B6（旧・並びH3用。2026-08-24 で未使用。定数は残す）
_SEP_TITLE  = "│"     # │ BOX DRAWINGS LIGHT VERTICAL（U+2502）
_WAVE_BAN   = "〜"     # 〜 WAVE DASH（台番範囲の連結）
_TILDE_FW   = "～"     # ～ FULLWIDTH TILDE（並び画像の重複サフィックス）
_PAREN_L    = "（"     # （
_PAREN_R    = "）"     # ）

_WEEKDAY_JP = ("月", "火", "水", "木", "金", "土", "日")

# 固定ファイル名（記事用⑧が書き出す名前）
FN_JUGGLER = "ジャグラーシリーズ優秀台.jpg"
FN_SONOTA  = "その他の優秀台ピックアップ.jpg"

# ── その日のポスター（記事上部）────────────────────────────────────
# ⑧実行時に output_dir へ書き出す結合済みポスター1枚のファイル名。
# 複数枚アップロードされても **横結合して常に1枚** にする。
# 本文では optional 扱いで、無ければブロックごと出さない（送信は中止しない）。
POSTER_FN = "_wp_poster.jpg"
# 保存設定は分割片と同じ q95 / 4:4:4。**_SPLIT_QUALITY 等とは別定数**（用途が違う）。
POSTER_QUALITY = 95
POSTER_SUBSAMPLING = 0

# X (旧Twitter) の URL を後から手で貼るための空段落の数。
X_EMPTY_PARAS = 3

_CIRCLE_TO_ASCII = {
    "⓪": "0", "①": "1", "②": "2", "③": "3", "④": "4", "⑤": "5",
    "⑥": "6", "⑦": "7", "⑧": "8", "⑨": "9", "⑩": "10", "⑪": "11",
    "⑫": "12", "⑬": "13", "⑭": "14", "⑮": "15", "⑯": "16", "⑰": "17",
    "⑱": "18", "⑲": "19", "⑳": "20",
}


# ══════════════════════════════════════════════════════════════════
# ファイル名規則（既存コードと完全一致させること）
# ══════════════════════════════════════════════════════════════════

def app_safe_fn(name: str) -> str:
    """streamlit_app.py の `_make_safe_fn()` と同一。

    全台系 `{機種名}.jpg` / 自動高配分 `{機種名}_高配分.jpg` /
    ②個別優秀台 `{機種名}（優秀台）.jpg` に使う。禁止文字はアンダースコアへ置換。
    """
    s = str(name)
    for _c, _d in _CIRCLE_TO_ASCII.items():
        s = s.replace(_c, _d)
    return re.sub(r'[\\/:*?"<>|]', "_", s)


def narabi_safe_fn(name: str) -> str:
    """convert_narabi_pil.py の `make_safe()` と同一。

    並び画像だけ規則が異なり、禁止文字を **全角へ置換** する。
    app_safe_fn（アンダースコア置換）と混同しないこと。
    """
    return (str(name).replace("/", "／").replace("\\", "＼").replace(":", "：")
            .replace("*", "＊").replace("?", "？").replace('"', "”")
            .replace("<", "＜").replace(">", "＞").replace("|", "｜"))


def narabi_file_name(item: dict, dup_titles: set[str]) -> str:
    """nami_list の1件から並び画像のファイル名を再現する。

    convert_narabi_pil.py:393 と streamlit_app.py:13405-13410 の規則:
      同じタイトルが複数ある場合のみ `（{先頭台番}～{末尾台番}）` を付ける。
    """
    title = item["title"]
    if title in dup_titles:
        bans = item.get("bans") or []
        if bans:
            title = f"{title}{_PAREN_L}{bans[0]}{_TILDE_FW}{bans[-1]}{_PAREN_R}"
    return narabi_safe_fn(title) + ".jpg"


def high_file_name(item: dict) -> "str | None":
    """高配分エントリ → 画像ファイル名。**生成経路で判別する**（修正2）。

    high_ratio_list へは2つの経路から積まれ、ファイル名が異なる:

      - 自動高配分（run_step3_other:3546/3565）
          `has_image` キーを **持つ**（True/False）。
          画像名は `{機種名}_高配分.jpg`。has_image=False は画像なし。
      - 手動高配分＝②個別「優秀台」（show_auto_article_page:14321）
          `has_image` キーを **持たない**。
          画像名は `{機種名}（優秀台）.jpg`。

    ファイルの存在だけで推測せず、この経路差で判別する。
    戻り値 None は「画像を出さない」。
    """
    name = item.get("name", "")
    if not name:
        return None
    if "has_image" in item:                      # 自動高配分
        if not item.get("has_image"):
            return None                          # 全台除外などで画像なし
        return f"{app_safe_fn(name)}_高配分.jpg"
    return f"{app_safe_fn(name)}{_PAREN_L}優秀台{_PAREN_R}.jpg"   # 手動高配分


def is_manual_high(item: dict) -> bool:
    """②個別「優秀台」由来（手動高配分）なら True。"""
    return "has_image" not in item


# ══════════════════════════════════════════════════════════════════
# 数値・文字列フォーマット（58109 の書式を実測どおり再現）
# ══════════════════════════════════════════════════════════════════

def fmt_signed(n) -> str:
    """+5,317 / -820 形式。"""
    n = int(n)
    return f"{'+' if n >= 0 else '-'}{abs(n):,}"


def ban_range_str(bans) -> str:
    """台番リスト → `2078〜2080+2187番台`（2026-08-24 正式仕様）。

    連続する区間は `_WAVE_BAN`（〜 U+301C）でまとめ、**飛び地は半角 `+` で連結**する。
    **「番台」は各区間へ付けず、括弧内の最後に1回だけ付ける**。
    単独1台のみのときは `2187番台`。
    旧表記 `2078番台〜2080番台・2187番台` へは戻さない（`・` を使わない）。
    呼び出しは `h3_narabi()` の1箇所のみ。
    """
    bs = sorted(int(b) for b in bans)
    if not bs:
        return ""
    runs, cur = [], [bs[0]]
    for b in bs[1:]:
        if b == cur[-1] + 1:
            cur.append(b)
        else:
            runs.append(cur)
            cur = [b]
    runs.append(cur)
    parts = []
    for r in runs:
        if len(r) >= 2:
            parts.append(f"{r[0]}{_WAVE_BAN}{r[-1]}")
        else:
            parts.append(f"{r[0]}")
    return "+".join(parts) + "番台"


def h3_zendai(item: dict) -> str:
    """`戦国乙女4(3/3台+)→平均+5,317枚`。

    **全台系・高配分・ジャグラーで共通に使う**。zen_dai_list と high_ratio_list は
    name / count / total / all_avg_diff を同じ意味で持つため、そのまま渡せる
    （自動 Step1:3165・手動②全台:14297・自動 Step3:3565・手動②優秀台:14322 で確認済み）。
    高配分用に別書式を作らないこと。

    書式は 2026-08-24 に旧`戦国乙女4 (3/3台+） ➡平均 +5,317枚`から変更した（正式仕様）。
    記事内で書式を混在させないため、**ジャグラーの個別高配分H3も同じ新表記**とする。
    括弧は左右とも半角・スペースなし・矢印は `_ARROW_R2`（→ U+2192）。

    **平均差枚がマイナスのときは `→平均…枚` を丸ごと出さない**（2026-08-24 正式仕様）。
    0 は `→平均+0枚` と表示する（0以上は従来どおり）。これは**表示だけ**の仕様で、
    plan_blocks() の降順ソートは実際の all_avg_diff を使い続ける
    （マイナス機種を除外したり 0 として扱ったりしない）。
    `int()` は fmt_signed() と同じ丸めにして、表示と分岐の判定をずらさないために掛ける。
    """
    avg = int(item['all_avg_diff'])
    base = f"{item['name']}({item['count']}/{item['total']}台+)"
    if avg < 0:
        return base
    return f"{base}{_ARROW_R2}平均{fmt_signed(avg)}枚"


def line_high(item: dict) -> str:
    """`Lモンハンライズ(4/6台+）➡平均+1,850枚`。

    ※ 修正1・3 により本文へは出力しない（装飾テキスト一覧を作らない）。
       書式は将来の参照用に残す。
    """
    return (f"{item['name']}({item['count']}/{item['total']}台+{_PAREN_R}"
            f"{_ARROW_R}平均{fmt_signed(item['all_avg_diff'])}枚")


def h3_narabi(item: dict) -> str:
    """`【3台並び】かぐや様(2025〜2027番台)→平均+7,533枚`（2026-08-24 正式仕様）。

    「列」の自動判定はしない（正式仕様）。常に【N台並び】。
    機種名はアプリ保持のものをそのまま使う（逆変換しない）。
    複数機種にまたがる並びの `machine`（`A+B` / `A～Z`）も**そのまま**置く。

    書式は旧`【3台並び】2025番台〜2027番台 かぐや様▶平均+7,533枚`から変更した。
    機種名を台番より前へ出し、台番は半角括弧で囲む。機種名と `(` の間・
    `)` の直後・`→平均` の前後にスペースを入れない。矢印は `_ARROW_R2`（→ U+2192）。
    **`_ARROW_TRI`（▶）はこの関数でのみ使っていたが未使用になった。定数は残す。**

    **平均差枚がマイナスでも `→平均-○枚` を表示する。**
    `h3_zendai()` のマイナス非表示仕様（`9c83eef`）は**並びへ適用しない**。
    """
    return (f"【{item['count']}台並び】{item['machine']}"
            f"({ban_range_str(item.get('bans') or [])})"
            f"{_ARROW_R2}平均{fmt_signed(item['avg_diff'])}枚")


def h3_retsu(item: dict) -> str:
    """列画像のH3。`h3_narabi()` と同じ体裁だが先頭を【列仕掛け】にする。

    並びは `【N台並び】…` だが、列は台数表記をしない（画像タイトルと同じ流儀・`42ea146`）。
    **`h3_narabi()` 本体は変更しない**（並びの表記を巻き込まないため）。
    """
    return (f"【列仕掛け】{item['machine']}"
            f"({ban_range_str(item.get('bans') or [])})"
            f"{_ARROW_R2}平均{fmt_signed(item['avg_diff'])}枚")


def build_title(date_obj, store: str = WP_STORE) -> str:
    """`8月8日(土)│エスパス高田馬場│`。後半は人間が編集画面で追記する。"""
    if date_obj is None:
        return f"エスパス{store}{_SEP_TITLE}"
    wd = _WEEKDAY_JP[date_obj.weekday()]
    return (f"{date_obj.month}月{date_obj.day}日({wd}){_SEP_TITLE}"
            f"エスパス{store}{_SEP_TITLE}")


# ══════════════════════════════════════════════════════════════════
# 縦長画像の分割（修正4・C案）— 原本には触れない
# ══════════════════════════════════════════════════════════════════

# 縦長でも **分割せず1枚のまま送る**ファイル名（2026-09-04 追加）。
# 島図は分割すると WordPress 上で3つの別メディアになり、クリック拡大したときに
# 「2Fの片だけ」が開いてしまう。記事では 2F+3F を含む島図全体を1枚絵として
# 拡大できることを優先するため、島図だけ分割対象から外す。
# **`needs_split()` 本体は変更しない**（高田馬場を含む既存の長画像分割は正式仕様のまま）。
# トレードオフ: 1枚で送るとサイト側の長辺2560px縮小により約1361×2560になる。
WP_NOSPLIT_FILES: "frozenset[str]" = frozenset({"島図.jpg"})


def needs_split(w: int, h: int, max_h: int = WP_SPLIT_MAX_H) -> bool:
    """WordPress側の長辺縮小で幅が潰れるか。高さが上限超なら分割対象。"""
    return h > max_h


def split_count(h: int, max_h: int = WP_SPLIT_MAX_H) -> int:
    """必要な分割枚数。各片が max_h 以下に収まる最小枚数。"""
    return max(1, math.ceil(h / max_h))


def _row_boundaries(img) -> list[int]:
    """表の行境界（横方向に色が一様な帯）の中心yを返す。

    行の途中で切らないための候補点。numpy が使えない場合は空を返し、
    呼び出し側は等分割へフォールバックする。
    """
    try:
        import numpy as np
    except Exception:
        return []
    a = np.asarray(img.convert("RGB"))
    std = a.std(axis=(1, 2))
    uni = np.where(std < _UNIFORM_STD)[0]
    if len(uni) == 0:
        return []
    centers, start, prev = [], int(uni[0]), int(uni[0])
    for y in uni[1:]:
        y = int(y)
        if y != prev + 1:
            centers.append((start + prev) // 2)
            start = y
        prev = y
    centers.append((start + prev) // 2)
    return centers


def _snap_cut(target: int, boundaries: list[int], lo: int, hi: int) -> int:
    """切れ目を決める。行境界を最優先し、そのうえで可能なら8px境界へ合わせる。

    優先順位（正式仕様）:
      1. target 付近の行境界（表の行を途中で切らないことが最優先）
      2. その行境界の許容幅内で 8 の倍数（JPEGのDCT格子と一致させ誤差を減らす）
      3. どちらも取れなければ target を8の倍数へ丸める
    """
    cands = [b for b in boundaries if lo < b < hi and abs(b - target) <= _CUT_SEARCH]
    if cands:
        base = min(cands, key=lambda b: abs(b - target))
        # 行境界は「一様な帯」の中心なので、帯の中で8の倍数へずらしても
        # 行を切らない。帯の厚み相当（±_MCU*3）だけ許容して探す。
        for d in range(0, _MCU * 3 + 1):
            for cand in (base - d, base + d):
                if cand % _MCU == 0 and lo < cand < hi:
                    return cand
        return base
    aligned = (target // _MCU) * _MCU
    return aligned if lo < aligned < hi else target


def split_image_for_wp(path: str, out_dir: str,
                       max_h: int = WP_SPLIT_MAX_H) -> list[dict]:
    """縦長画像を送信用に分割する。**原本は読み取るだけで変更しない。**

    戻り値: [{"path","file","w","h","bytes"}, …]（上から順）
    分割不要なら空リストを返す（呼び出し側は原本をそのまま使う）。
    """
    from PIL import Image
    with Image.open(path) as im:
        im.load()
        w, h = im.size
        if not needs_split(w, h, max_h):
            return []
        n = split_count(h, max_h)
        bounds = _row_boundaries(im)
        # 等分割の目標位置を、行境界へ寄せて確定する
        cuts = [0]
        for i in range(1, n):
            target = round(h * i / n)
            prev = cuts[-1]
            y = _snap_cut(target, bounds, prev + 1, h - 1)
            # 単調増加を保証（寄せ先が前の切れ目を追い越さないように）
            cuts.append(max(y, prev + 1))
        cuts.append(h)

        stem = os.path.splitext(os.path.basename(path))[0]
        os.makedirs(out_dir, exist_ok=True)
        parts: list[dict] = []
        for i in range(n):
            top, bot = cuts[i], cuts[i + 1]
            if bot <= top:
                continue
            piece = im.crop((0, top, w, bot))
            fn = f"{stem}_wp_{i + 1:02d}.jpg"
            fp = os.path.join(out_dir, fn)
            # リサイズせず crop のみ。4:4:4 を維持して色を保つ。
            piece.save(fp, "JPEG", quality=_SPLIT_QUALITY,
                       subsampling=_SPLIT_SUBSAMPLING)
            parts.append({"path": fp, "file": fn, "w": w, "h": bot - top,
                          "bytes": os.path.getsize(fp), "top": top, "bottom": bot})
        return parts


def build_poster(paths: "list[str]", out_dir: str,
                 max_side: int = WP_MAX_SIDE) -> "dict | None":
    """その日のポスターを **常に1枚** の JPEG (`POSTER_FN`) として書き出す。

    - 1枚 … リサイズせずそのまま JPEG 化する。
    - 2枚以上 … **最も小さい高さへ全画像を縮小**（アスペクト比維持・クロップなし・
      余白なし・`Image.LANCZOS`）して **横一列に結合**する。
    - 結合後の幅が `max_side` を超えるときだけ、全体をアスペクト比維持で縮める。
      **`WP_MAX_SIDE` の値そのものは変更しない**（参照するだけ）。
    - PNG などの透過は **白背景へ合成**してから JPEG 化する。
    - 保存は `POSTER_QUALITY`(95) / `POSTER_SUBSAMPLING`(0 = 4:4:4)。

    既存の長尺画像分割（`split_image_for_wp`）とは**別用途で、互いに無関係**。
    戻り値: {"path","file","w","h","bytes","count"} ／ 入力が空なら None。
    """
    from PIL import Image

    paths = [p for p in (paths or []) if p and os.path.isfile(p)]
    if not paths:
        return None

    def _flat(im):
        """透過を白背景へ合成して RGB にする。"""
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            base = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            base.paste(rgba, mask=rgba.split()[-1])
            return base
        return im.convert("RGB")

    imgs = []
    try:
        for fp in paths:
            with Image.open(fp) as im:
                im.load()
                imgs.append(_flat(im))

        if len(imgs) == 1:
            canvas = imgs[0]
        else:
            # 最も小さい高さへ統一（拡大はしない＝画質劣化を避ける）
            th = min(im.height for im in imgs)
            resized = []
            for im in imgs:
                if im.height == th:
                    resized.append(im)
                else:
                    nw = max(1, int(round(im.width * th / im.height)))
                    resized.append(im.resize((nw, th), Image.LANCZOS))
            total_w = sum(im.width for im in resized)
            canvas = Image.new("RGB", (total_w, th), (255, 255, 255))
            x = 0
            for im in resized:      # 余白なしで横一列に連結
                canvas.paste(im, (x, 0))
                x += im.width

        # サイト側の縮小（長辺 > max_side）を避けるため、自前で高品質に縮める
        if max(canvas.size) > max_side:
            sc = max_side / float(max(canvas.size))
            canvas = canvas.resize((max(1, int(canvas.width * sc)),
                                    max(1, int(canvas.height * sc))), Image.LANCZOS)

        os.makedirs(out_dir, exist_ok=True)
        out = os.path.join(out_dir, POSTER_FN)
        canvas.save(out, "JPEG", quality=POSTER_QUALITY,
                    subsampling=POSTER_SUBSAMPLING)
        return {"path": out, "file": POSTER_FN, "w": canvas.width,
                "h": canvas.height, "bytes": os.path.getsize(out),
                "count": len(paths)}
    finally:
        for im in imgs:
            try:
                im.close()
            except Exception:
                pass


def wp_stored_width(w: int, h: int, max_side: int = WP_MAX_SIDE) -> int:
    """WordPress保存後の推定幅（長辺 max_side への縮小を再現）。"""
    longest = max(w, h)
    if longest <= max_side:
        return w
    return int(round(w * max_side / longest))


# ══════════════════════════════════════════════════════════════════
# Gutenberg ブロック生成
# ══════════════════════════════════════════════════════════════════

def blk_h2(text: str) -> str:
    return ('<!-- wp:heading -->\n'
            f'<h2 class="wp-block-heading">{text}</h2>\n'
            '<!-- /wp:heading -->')


def blk_h3(text: str) -> str:
    return ('<!-- wp:heading {"level":3} -->\n'
            f'<h3 class="wp-block-heading">{text}</h3>\n'
            '<!-- /wp:heading -->')


def blk_image(media_id: int, src: str, join: bool = False) -> str:
    """58109 の画像ブロックと同一属性。

    join=True で 58963 と同じ連結クラスを付ける（分割片の最後以外）。
    """
    if join:
        return (f'<!-- wp:image {{"id":{media_id},"sizeSlug":"full",'
                f'"linkDestination":"none","className":"{SPLIT_JOIN_CLASS}"}} -->\n'
                f'<figure class="wp-block-image size-full {SPLIT_JOIN_CLASS}">'
                f'<img src="{src}" alt="" class="wp-image-{media_id}"/></figure>\n'
                '<!-- /wp:image -->')
    return (f'<!-- wp:image {{"id":{media_id},"sizeSlug":"full","linkDestination":"none"}} -->\n'
            f'<figure class="wp-block-image size-full">'
            f'<img src="{src}" alt="" class="wp-image-{media_id}"/></figure>\n'
            '<!-- /wp:image -->')


def _split_para(text) -> "list[str]":
    """記事上部の入力テキストを段落リストへ分解する。

    空行は段落の区切りとして捨て、各行を1段落にする。
    未入力・空白のみなら空リスト（＝ブロックを出力しない）。
    """
    if not text:
        return []
    return [ln.strip() for ln in str(text).replace("\r\n", "\n").split("\n")
            if ln.strip()]


def blk_para(text: str) -> str:
    """通常の段落ブロック（記事上部の文章用）。装飾は付けない。"""
    return ('<!-- wp:paragraph -->\n'
            f'<p class="wp-block-paragraph">{text}</p>\n'
            '<!-- /wp:paragraph -->')


def esc(text) -> str:
    """ユーザー入力をHTMLへ入れる前のエスケープ（& < > " ' ）。

    本文へそのまま連結するとブロック検証が壊れる・リンクが崩れるため、
    **ユーザー入力を出す新しいブロックは必ずここを通す**。
    """
    return html.escape(str(text if text is not None else ""), quote=True)


def blk_para_bold(text: str) -> str:
    """段落まるごと太字（ななこポストの「↓前日の夜に…」用）。"""
    return ('<!-- wp:paragraph -->\n'
            f'<p class="wp-block-paragraph"><strong>{text}</strong></p>\n'
            '<!-- /wp:paragraph -->')


# X（旧Twitter）投稿の埋め込み。**推測ではなく、同じサイトの既存投稿（ID 60367）の
# content.raw を GET で読んで確認した実物の markup** に合わせている（2026-09-04）。
#
#   <!-- wp:embed {"url":"…","type":"rich","providerNameSlug":"x","responsive":true} -->
#   <figure class="wp-block-embed is-type-rich is-provider-x wp-block-embed-x">
#   <div class="wp-block-embed__wrapper">
#   URL
#   </div></figure>
#   <!-- /wp:embed -->
#
# サイトの oEmbed プロキシは x.com / twitter.com の**どちらでも 200 を返す**ことを実測
# 済みなので、入力されたドメインは書き換えない。
_X_STATUS_RE = re.compile(
    r"^https://(?:x\.com|twitter\.com)/[A-Za-z0-9_]{1,15}/status/\d+/?$", re.I)


def normalize_x_url(url) -> str:
    """X投稿URLとして安全なものだけを返す。該当しなければ空文字。

    * `?s=20` のようなクエリ・フラグメントは落としてから判定する
      （HTML内の `&` によるブロック検証ずれを避けるため）。
    * `javascript:` `data:` など https 以外は**すべて弾く**。
    * 独自のURLパーサーは作らず urllib.parse と1本の正規表現だけで判定する。
    """
    u = str(url or "").strip()
    if not u:
        return ""
    try:
        p = urlsplit(u)
    except Exception:
        return ""
    if p.scheme.lower() != "https" or not p.netloc:
        return ""
    base = urlunsplit((p.scheme, p.netloc, p.path, "", ""))
    return base if _X_STATUS_RE.match(base) else ""


def blk_embed_x(url: str) -> str:
    """X投稿の埋め込みブロック（Gutenberg標準の wp:embed）。

    ブロック属性は JSON なので json.dumps で、figure 内のURLテキストは esc() で出す。
    **生の文字列連結はしない。**
    """
    u = normalize_x_url(url)
    if not u:
        return ""
    attrs = json.dumps({"url": u, "type": "rich",
                        "providerNameSlug": "x", "responsive": True},
                       ensure_ascii=False, separators=(",", ":"))
    return (f'<!-- wp:embed {attrs} -->\n'
            '<figure class="wp-block-embed is-type-rich is-provider-x wp-block-embed-x">'
            '<div class="wp-block-embed__wrapper">\n'
            f'{esc(u)}\n'
            '</div></figure>\n'
            '<!-- /wp:embed -->')


def blk_para_hint(text: str) -> str:
    """ヒント1行。**先頭の「■」だけ赤＋太字**で、後ろの本文は通常表示。

    span のインラインstyleだけで表現する（テーマCSSは変更しない）。
    段落全体を赤・太字にしない。
    """
    return ('<!-- wp:paragraph -->\n'
            f'<p class="wp-block-paragraph">'
            f'<strong style="color:{NANAKO_MARK_COLOR}">{NANAKO_HINT_MARK}</strong>'
            f'{esc(text)}</p>\n'
            '<!-- /wp:paragraph -->')


def blk_empty_para() -> str:
    """空の段落ブロック。

    Gutenberg 上で **クリックしてカーソルを置ける空行** になる。
    ここへ X (旧Twitter) の URL を手で貼ると自動で埋め込みへ変換される。
    `<br>` 連続・スペーサーブロック・`&nbsp;` は
    「後から URL を貼る」用途に向かないため使わない（正式仕様）。
    """
    return ('<!-- wp:paragraph -->\n'
            '<p class="wp-block-paragraph"></p>\n'
            '<!-- /wp:paragraph -->')


def blk_para_high(lines: list[str]) -> str:
    """高配分の装飾段落。**修正1により本文へは出力しない**（定義のみ残置）。"""
    body = "<br>".join(lines)
    return ('<!-- wp:paragraph -->\n'
            '<p><strong><span class="swl-fz u-fz-l">'
            '<span class="swl-inline-color has-swl-deep-01-color">'
            f'{body}</span></span></strong></p>\n'
            '<!-- /wp:paragraph -->')


def blk_para_juggler(lines: list[str]) -> str:
    """ジャグラーの装飾段落。**修正3により本文へは出力しない**（定義のみ残置）。"""
    body = "<br>".join(lines)
    return ('<!-- wp:paragraph -->\n'
            '<p><strong><span class="swl-inline-color has-swl-deep-02-color">'
            '<span class="swl-fz u-fz-l">'
            f'{body}</span></span></strong></p>\n'
            '<!-- /wp:paragraph -->')


def blk_button(slug: str = WP_CATEGORY_SLUG, site: str = "") -> str:
    url = f"{site.rstrip('/')}/category/{slug}" if site else f"/category/{slug}"
    return (f'<!-- wp:loos/button {{"hrefUrl":"{url}","className":"is-style-btn_normal"}} -->\n'
            f'<div class="swell-block-button is-style-btn_normal">'
            f'<a href="{url}" class="swell-block-button__link">'
            f'<span>{BUTTON_TEXT}</span></a></div>\n'
            '<!-- /wp:loos/button -->')


# ══════════════════════════════════════════════════════════════════
# payload / plan
# ══════════════════════════════════════════════════════════════════

def build_payload(*, store: str, output_dir: str, dir_stem: str, result: dict,
                  juggler_series) -> dict:
    """⑧の `result` から WordPress 用の投影 dict を作る（読み取り専用）。

    `result` は書き換えない。必要な値だけを浅くコピーする。
    """
    js = set(juggler_series or ())
    hr = list(result.get("high_ratio_list") or [])
    return {
        "store":      store,
        "output_dir": output_dir,
        "dir_stem":   dir_stem,
        "date":       result.get("date"),
        "zen_dai":    [dict(x) for x in (result.get("zen_dai_list") or [])],
        "high":       [dict(x) for x in hr if x.get("name") not in js],
        "juggler":    [dict(x) for x in hr if x.get("name") in js],
        "nami":       [dict(x) for x in (result.get("nami_list") or [])],
    }


def _existing_files(files, output_dir: str) -> list[str]:
    """ファイル名リストのうち **output_dir に実在するものだけ** を順序を保って返す。

    末尾・バラエティのセクション判定に使う（2026-08-25 追加）。
    payload が無い / None / 空でも例外を出さず [] を返す（旧 payload 互換）。
    実ファイルが1枚も無ければ呼び出し側が H2 ごと出さないため、
    「見出しだけ残る」状態にならない。**新しいソートは掛けない**（生成順を維持）。
    """
    out: list[str] = []
    seen: set[str] = set()
    for fn in (files or []):
        fn = str(fn or "").strip()
        if not fn or fn in seen:
            continue
        if output_dir and os.path.isfile(os.path.join(output_dir, fn)):
            seen.add(fn)
            out.append(fn)
    return out


def _resolve_high_images(entries: list[dict], output_dir: str) -> list[dict]:
    """高配分エントリ列 → 実在する画像の並び（機種単位で重複除去）。

    同一機種に自動と手動の両方が存在した場合:
      位置＝最初の出現位置 / 内容＝後勝ち（②個別「優秀台」を優先）。
      これは既存 `_dedup_previews()` の正式仕様と同じ考え方。
    """
    order: list[str] = []
    chosen: dict[str, dict] = {}
    for it in entries:
        name = it.get("name", "")
        fn = high_file_name(it)
        if not name or not fn:
            continue
        if not os.path.isfile(os.path.join(output_dir, fn)):
            continue
        if name not in chosen:
            order.append(name)
            chosen[name] = {"file": fn, "manual": is_manual_high(it),
                            "name": name, "entry": it}
        else:
            # 後勝ち。ただし自動が手動を上書きしないようにする
            if is_manual_high(it):
                chosen[name] = {"file": fn, "manual": True,
                                "name": name, "entry": it}
    return [chosen[n] for n in order]


def plan_blocks(payload: dict) -> list[dict]:
    """本文の構成計画（見出し・画像の並び）を作る。

    画像項目は {"type":"image","file":…,"label":…} を持ち、
    実ファイルの解決とアップロードは呼び出し側が行う。
    """
    out_dir = payload.get("output_dir", "")
    plan: list[dict] = []

    # ── 記事上部（2026-08-22 追加）──────────────────────────────────
    # ①その日の見出し ②ポスター ③ポスター下文章 ④X貼付用の空段落×3 ⑤Xリンク下文章
    # **すべて任意**。空欄・ポスター未アップロードならブロックごと出力しない。
    # ★4項目（見出し／ポスター／ポスター下文章／Xリンク下文章）が **すべて空なら、
    #   空段落×3 も含めて上部を1ブロックも出力しない**。この場合の本文は
    #   記事上部の追加前とバイト単位で完全一致する（正式仕様）。
    # ここより下（全台系以降）の構成は一切変更しない。
    _top_h = str(payload.get("top_heading") or "").strip()
    _top_p = _split_para(payload.get("top_text_poster"))
    _top_x = _split_para(payload.get("top_text_x"))
    _has_poster = bool(out_dir) and os.path.isfile(os.path.join(out_dir, POSTER_FN))
    if _top_h or _has_poster or _top_p or _top_x:
        if _top_h:
            plan.append({"type": "h2", "text": _top_h})
        if _has_poster:
            plan.append({"type": "image", "file": POSTER_FN,
                         "label": "その日のポスター", "optional": True})
        for _ln in _top_p:
            plan.append({"type": "para", "text": _ln})
        # X (旧Twitter) の URL を後から手で貼るための空段落
        for _ in range(X_EMPTY_PARAS):
            plan.append({"type": "empty_para"})
        for _ln in _top_x:
            plan.append({"type": "para", "text": _ln})

    # ── ななこポスト（渋谷新館の記事用のみ・2026-09-04 追加）──────────────
    #    位置は **記事上部（Xリンク下文章）の直後・全台系H2の直前**で固定。
    #    payload["nanako"] を持つ店舗だけ出る（高田馬場はキーを持たないので1ブロックも
    #    増えない）。固定文は定数、可変は URL とヒント1〜6 だけ。
    #    * URL が空 → 「↓前日の夜に…」とURLの **2つをセットで出さない**
    #    * ヒントが0件 → 「今回の結果から…」・ヒント一覧・締め文章を **まとめて出さない**
    #    * 空のヒント欄は詰めて出す（空の「■」を作らない）
    _nanako = payload.get("nanako")
    if _nanako is not None:
        _nk_url   = normalize_x_url((_nanako or {}).get("url"))
        _nk_hints = [str(h or "").strip() for h in ((_nanako or {}).get("hints") or [])]
        _nk_hints = [h for h in _nk_hints if h]
        plan.append({"type": "h2", "text": NANAKO_H2})
        plan.append({"type": "para", "text": NANAKO_LEAD})
        if _nk_url:
            plan.append({"type": "para_bold", "text": NANAKO_URL_LEAD})
            plan.append({"type": "embed_x", "url": _nk_url})
        if _nk_hints:
            plan.append({"type": "para", "text": NANAKO_HINT_LEAD})
            for _h in _nk_hints:
                plan.append({"type": "para_hint", "text": _h})
            plan.append({"type": "para", "text": NANAKO_OUTRO})

    # ── 全台系: H2 →（H3 + 画像）× 機種数 ──
    zen = sorted(payload["zen_dai"], key=lambda x: -int(x.get("all_avg_diff", 0)))
    if zen:
        plan.append({"type": "h2", "text": H2_ZENDAI})
        for it in zen:
            # 接頭辞のみ付ける。h3_zendai() 本体は変更しない
            # （マイナス平均の非表示・0の +0枚・_ARROW_R2・fmt_signed をそのまま維持）。
            plan.append({"type": "h3", "text": H3_PREFIX_ZENDAI + h3_zendai(it)})
            plan.append({"type": "image",
                         "file": f"{app_safe_fn(it['name'])}.jpg",
                         "label": f"全台系 {it['name']}"})

    # ── 高配分: H2 → 画像を機種ごとに順番配置 ──
    #    修正1: 赤文字テキスト一覧は出力しない。
    #    修正2: 自動 `_高配分.jpg` と 手動 `（優秀台）.jpg` を生成経路で判別。
    high_imgs = _resolve_high_images(payload["high"], out_dir)
    #    修正4(2026-08-24): 画像セット確定後に平均差枚の降順へ並べ替える。
    #    H3と画像は同じ dict（entry/file）なので **セット単位**で動き、ズレは起きない。
    #    手動/自動による優先順位は付けない（純粋に all_avg_diff のみ）。
    #    Python の sorted() は安定ソートなので同値は現在の相対順を維持する。
    #    キーの取り方は全台系（zen）と同じ .get("all_avg_diff", 0)。
    #    _resolve_high_images() の解決ロジック・手動/自動判定には触れない。
    high_imgs = sorted(high_imgs,
                       key=lambda h: -int(h["entry"].get("all_avg_diff", 0)))
    if high_imgs:
        plan.append({"type": "h2", "text": H2_HIGH})
        for h in high_imgs:
            # 全台系とまったく同じ h3_zendai() を流用する（新書式は作らない）。
            # 自動・手動どちらも high_ratio_list の name/count/total/all_avg_diff を使う。
            # 接頭辞のみ付ける（ジャグラー個別高配分には付けない）。
            plan.append({"type": "h3", "text": H3_PREFIX_HIGH + h3_zendai(h["entry"])})
            plan.append({"type": "image", "file": h["file"],
                         "label": ("手動高配分 " if h["manual"] else "自動高配分 ") + h["name"]})

    # ── 末尾: H2 → 画像 × 枚数（2026-08-25 追加）──
    #    掲載順は **⑧の生成順そのまま**（通常末尾①②③ → ジャグラー末尾①②③）。
    #    payload["suebangai"] は ⑧が実際に保存したファイル名のリストで、
    #    ここで**新しいソートを掛けない**。ジャグラー末尾も同じ「末尾」へまとめる。
    #    ★実ファイルが1枚も無ければ **H2ごと出さない**（見出しだけ残る状態を作らない）。
    #      そのため optional は使わず、先に実在確認してから H2＋画像を足す。
    sue_files = _existing_files(payload.get("suebangai"), out_dir)
    if sue_files:
        plan.append({"type": "h2", "text": H2_SUEBANGAI})
        for fn in sue_files:
            plan.append({"type": "image", "file": fn, "label": f"末尾 {fn}"})

    # ── 並び・列: H2 →（H3 + 画像）× 並び数 →（H3 + 画像）× 列数 ──
    #    列は渋谷新館の記事用にだけある。payload["retsu"] が無い店舗（高田馬場）は
    #    従来どおり並びだけで、ブロックは1つも増えない。
    #    列のファイル名は **⑧が使うのと同じ `_build_col_items()` の結果**を
    #    呼び出し側から受け取る（ここで再生成・再推測しない）。
    #    H2 は既存の「並び・列仕掛けも！」をそのまま使う（元から列を含む文言）。
    nami = payload["nami"]
    retsu = [r for r in (payload.get("retsu") or [])
             if str(r.get("file") or "")
             and out_dir and os.path.isfile(os.path.join(out_dir, str(r["file"])))]
    if nami or retsu:
        dup = {t for t, c in Counter(x["title"] for x in nami).items() if c > 1}
        plan.append({"type": "h2", "text": H2_NARABI})
        for it in nami:
            plan.append({"type": "h3", "text": h3_narabi(it)})
            plan.append({"type": "image",
                         "file": narabi_file_name(it, dup),
                         "label": f"並び {it['title']}"})
        for it in retsu:
            plan.append({"type": "h3", "text": h3_retsu(it)})
            plan.append({"type": "image", "file": it["file"],
                         "label": f"列 {it.get('machine', it['file'])}"})

    # ── バラエティ: H2 → 画像（2026-08-25 追加）──
    #    ⑧は最大1枚（`バラエティ.jpg` / `バラエティの優秀台.jpg`）。
    #    末尾と同じく **実ファイルが無ければ H2ごと出さない**。
    var_files = _existing_files(payload.get("variety"), out_dir)
    if var_files:
        plan.append({"type": "h2", "text": H2_VARIETY})
        for fn in var_files:
            plan.append({"type": "image", "file": fn, "label": f"バラエティ {fn}"})

    # ── ジャグラー: H2 → 個別高配分画像（あれば）→ 統合画像 ──
    #    修正3: 青文字テキスト一覧は出力しない。
    jug_imgs = _resolve_high_images(payload["juggler"], out_dir)
    jug_comb = os.path.isfile(os.path.join(out_dir, FN_JUGGLER)) if out_dir else False
    if jug_imgs or jug_comb or payload["juggler"]:
        plan.append({"type": "h2", "text": H2_JUGGLER})
        for h in jug_imgs:
            plan.append({"type": "h3", "text": h3_zendai(h["entry"])})
            plan.append({"type": "image", "file": h["file"],
                         "label": ("手動高配分(ジャグ) " if h["manual"]
                                   else "自動高配分(ジャグ) ") + h["name"]})
        # 統合画像が実在する店舗（渋谷新館）だけ、その直前へH3を入れる。
        # **画像が無いときにH3だけ残らない**よう jug_comb を条件にする。
        if jug_comb and payload.get("juggler_comb_h3"):
            plan.append({"type": "h3", "text": H3_JUGGLER_COMB})
        plan.append({"type": "image", "file": FN_JUGGLER,
                     "label": "ジャグラーシリーズ優秀台", "optional": True})

    # ── その他単品: H2 → 画像1枚 ──
    plan.append({"type": "h2", "text": H2_SONOTA})
    plan.append({"type": "image", "file": FN_SONOTA,
                 "label": "その他の優秀台ピックアップ", "optional": True})

    # ── ⑤オススメ機種の優秀台: H2 →（H3=ブロックタイトル + 画像）× ブロック数 ──
    #    渋谷新館の記事用のみ。payload["osusume"] は
    #    [{"title": ブロックタイトル, "images": [ファイル名, …]}, …]（⑧の生成順）。
    #    ブロックタイトルは**画像には描かれない**（記事の小見出し用・`d121e54`）。
    #    実ファイルが1枚も無いブロックは出さず、全ブロック空なら H2 ごと省略する。
    osu_blocks = []
    for _b in (payload.get("osusume") or []):
        _files = _existing_files((_b or {}).get("images"), out_dir)
        if _files:
            osu_blocks.append((str((_b or {}).get("title") or "").strip(), _files))
    if osu_blocks:
        plan.append({"type": "h2", "text": H2_OSUSUME})
        for _t, _files in osu_blocks:
            if _t:
                plan.append({"type": "h3", "text": _t})
            for fn in _files:
                plan.append({"type": "image", "file": fn, "label": f"オススメ {fn}"})

    # ── 差枚数ランキング&島図: 1つのH2へ統合（渋谷新館の記事用のみ）──
    #    ランキング画像 →（5行ぶんの空段落）→ 島図画像 の順。
    #    **独立した「差枚数ランキング」「島図」のH2は出さない。**
    #    どちらか片方だけでもH2を出し、両方無ければH2ごと省略する。
    #    空段落は **両方そろっているときだけ** 入れる（片方だけなら余白が浮かない）。
    #    島図画像が無い店舗（高田馬場）は従来どおり「シマズをチェック！」の見出しのみ
    #    （画像は人間が挿入する）。**高田馬場のブロックは1つも変わらない。**
    rank_files    = _existing_files(payload.get("ranking"), out_dir)
    shimazu_files = _existing_files(payload.get("shimazu"), out_dir)
    if rank_files or shimazu_files:
        plan.append({"type": "h2", "text": H2_RANK_SHIMAZU})
        for fn in rank_files:
            plan.append({"type": "image", "file": fn, "label": f"差枚数ランキング {fn}"})
        if rank_files and shimazu_files:
            for _ in range(RANK_SHIMAZU_GAP_PARAS):
                plan.append({"type": "empty_para"})
        for fn in shimazu_files:
            plan.append({"type": "image", "file": fn, "label": f"島図 {fn}"})
    elif "ranking" not in payload and "shimazu" not in payload:
        # ランキング/島図の**キー自体を持たない店舗**（高田馬場）だけ、
        # 従来どおり「シマズをチェック！」の見出しを出す。
        # 渋谷新館はキーを必ず渡すので、両方0枚なら **H2ごと出さない**。
        plan.append({"type": "h2", "text": H2_SHIMAZU})

    # ── 店舗情報ボタン ──
    plan.append({"type": "button"})
    return plan


def collect_files(plan: list[dict], output_dir: str) -> tuple[list[dict], list[dict], list[dict]]:
    """画像項目の実ファイルを解決する。

    戻り値: (found, missing_required, missing_optional)
      found            … {"file","path","label","bytes"} のリスト（本文の登場順）
      missing_required … 欠けている必須ファイル → 1つでもあれば送信を中止する
      missing_optional … 欠けていてよいファイル（ジャグラー統合・その他）
    """
    found, miss_req, miss_opt = [], [], []
    seen: set[str] = set()
    for item in plan:
        if item.get("type") != "image":
            continue
        fn = item["file"]
        path = os.path.join(output_dir, fn)
        if os.path.isfile(path):
            if fn in seen:          # 同名は1回だけ送る
                continue
            seen.add(fn)
            found.append({"file": fn, "path": path, "label": item.get("label", ""),
                          "bytes": os.path.getsize(path)})
        elif item.get("optional"):
            miss_opt.append({"file": fn, "label": item.get("label", "")})
        else:
            miss_req.append({"file": fn, "label": item.get("label", "")})
    return found, miss_req, miss_opt


def plan_split(found: list[dict], tmp_dir: str) -> dict:
    """送信対象のうち縦長すぎる画像を、送信用の一時コピーへ分割する。

    戻り値: {元ファイル名: [{"path","file","w","h","bytes"}, …]}
    分割対象でなければキーを作らない。**原本は読み取るだけ。**
    """
    from PIL import Image
    result: dict[str, list[dict]] = {}
    for f in found:
        # 島図など「1枚絵のまま送る」ファイルは分割しない（needs_split は呼ばない）
        if f["file"] in WP_NOSPLIT_FILES:
            continue
        try:
            with Image.open(f["path"]) as im:
                w, h = im.size
        except Exception:
            continue
        if not needs_split(w, h):
            continue
        parts = split_image_for_wp(f["path"], tmp_dir)
        if parts:
            result[f["file"]] = parts
    return result


def build_content(plan: list[dict], media_map: dict, site: str = "",
                  split_map: "dict | None" = None,
                  category_slug: str = WP_CATEGORY_SLUG) -> str:
    """plan と {ファイル名: {"id":…, "src":…}} から content.raw を組み立てる。

    split_map があるファイルは、その分割片を順に並べ、
    **最後の1枚以外へ連結クラスを付ける**（58963 と同じ構造）。
    media_map に無い画像はブロックごと出力しない（見出しは残す）。
    """
    split_map = split_map or {}
    out: list[str] = []
    for item in plan:
        t = item["type"]
        if t == "h2":
            out.append(blk_h2(item["text"]))
        elif t == "h3":
            out.append(blk_h3(item["text"]))
        elif t == "para":
            out.append(blk_para(item["text"]))
        elif t == "empty_para":
            out.append(blk_empty_para())
        elif t == "para_bold":
            out.append(blk_para_bold(item["text"]))
        elif t == "embed_x":
            out.append(blk_embed_x(item["url"]))
        elif t == "para_hint":
            out.append(blk_para_hint(item["text"]))
        elif t == "para_high":
            out.append(blk_para_high(item["lines"]))
        elif t == "para_juggler":
            out.append(blk_para_juggler(item["lines"]))
        elif t == "image":
            fn = item["file"]
            parts = split_map.get(fn)
            if parts:
                blocks = []
                for p in parts:
                    m = media_map.get(p["file"])
                    if m:
                        blocks.append(m)
                for i, m in enumerate(blocks):
                    out.append(blk_image(m["id"], m["src"],
                                         join=(i < len(blocks) - 1)))
            else:
                m = media_map.get(fn)
                if m:
                    out.append(blk_image(m["id"], m["src"]))
        elif t == "button":
            out.append(blk_button(slug=category_slug, site=site))
    return "\n\n".join(out)


# ══════════════════════════════════════════════════════════════════
# WordPress 送信（ここから先だけがネットワークに触れる）
# ══════════════════════════════════════════════════════════════════

def _secret(name: str) -> str:
    """st.secrets → os.getenv の優先順で1件取得する。値はログへ出さない。

    Cloud には .env が無いため st.secrets を先に見る。streamlit は関数内で
    try import し、Streamlit 外の通常 Python 実行でも壊れないようにする
    （requests / PIL と同じ流儀）。
    """
    try:
        import streamlit as st
        if name in st.secrets:
            return str(st.secrets[name] or "")
    except Exception:
        pass
    return os.getenv(name, "") or ""


def _conf() -> tuple[str, tuple[str, str]]:
    """st.secrets（Cloud）/ .env・環境変数（ローカル）から接続情報を取得する。
    値はログへ出さない。"""
    site = _secret("WP_SITE_URL").rstrip("/")
    return site, (_secret("WP_USER"), _secret("WP_APP_PASSWORD"))


def config_ready() -> tuple[bool, str]:
    site, (user, pw) = _conf()
    missing = [k for k, v in (("WP_SITE_URL", site), ("WP_USER", user),
                              ("WP_APP_PASSWORD", pw)) if not v]
    if missing:
        return False, "未設定: " + ", ".join(missing)
    return True, site


def _err_text(resp) -> str:
    """秘密情報を含まない範囲のエラー文字列。"""
    try:
        j = resp.json()
        return f"code={j.get('code')} message={j.get('message')}"
    except Exception:
        return f"(非JSON応答 {len(resp.content)}バイト)"


def upload_media(path: str, *, timeout: int = WP_UPLOAD_TIMEOUT) -> dict:
    """POST /wp/v2/media を1件。日本語ファイル名は Phase 1 で実証した方式で送る。

    WordPress は Content-Disposition の `filename=` しか読まない（RFC 5987 の
    `filename*` は解釈しない）ため、`filename=` に UTF-8 の生バイトを載せる。
    """
    import requests
    site, auth = _conf()
    fn = os.path.basename(path)
    disp = ('attachment; filename="' + fn + '"; filename*=UTF-8\'\'' + quote(fn, safe=""))
    headers = {"Content-Disposition": disp.encode("utf-8"), "Content-Type": "image/jpeg"}
    with open(path, "rb") as f:
        data = f.read()
    t0 = time.perf_counter()
    try:
        r = requests.post(f"{site}/wp-json/wp/v2/media", headers=headers, data=data,
                          auth=auth, timeout=timeout)
    except Exception as e:
        return {"ok": False, "status": "EXC", "error": f"{type(e).__name__}: {e}",
                "sec": time.perf_counter() - t0, "file": fn}
    sec = time.perf_counter() - t0
    if r.status_code in (200, 201):
        j = r.json()
        return {"ok": True, "status": r.status_code, "id": j.get("id"),
                "src": j.get("source_url"), "sec": sec, "file": fn,
                "wp_file": (j.get("media_details") or {}).get("file")}
    # 429 は検知するが自動リトライはしない（正式仕様）
    return {"ok": False, "status": r.status_code, "error": _err_text(r),
            "retry_after": r.headers.get("Retry-After"), "sec": sec, "file": fn}


def create_draft(title: str, content: str,
                 category_id: int = WP_CATEGORY_ID) -> dict:
    """POST /wp/v2/posts。status=draft 固定・publish しない。

    既存投稿の更新（PUT/PATCH）は実装しない。常に新規 draft のみ。
    category_id の既定は高田馬場（24）＝従来動作。
    """
    import requests
    site, auth = _conf()
    payload = {
        "title":      title,
        "content":    content,
        "status":     WP_STATUS,       # "draft" 固定
        "categories": [int(category_id)],
        "author":     WP_AUTHOR_ID,
        # tags / featured_media / excerpt / template / meta は送らない
    }
    try:
        r = requests.post(f"{site}/wp-json/wp/v2/posts", json=payload,
                          auth=auth, timeout=WP_POST_TIMEOUT)
    except Exception as e:
        return {"ok": False, "status": "EXC", "error": f"{type(e).__name__}: {e}"}
    if r.status_code in (200, 201):
        j = r.json()
        pid = j.get("id")
        return {"ok": True, "status": r.status_code, "id": pid,
                "post_status": j.get("status"),
                "edit_url": f"{site}/wp-admin/post.php?post={pid}&action=edit"}
    return {"ok": False, "status": r.status_code, "error": _err_text(r)}


def create_takadanobaba_draft(payload: dict, progress=None) -> dict:
    """画像を逐次アップロードし、成功したら下書きを1件作成する。

    All-or-Nothing:
      - 送信前に必須ファイルを検証し、欠けていれば1枚も送らずに中止
      - 途中で失敗したらその場で中断し、**投稿は作成しない**
      - アップロード済みメディアの自動削除はしない

    縦長画像は送信用の一時コピーへ分割する（原本は変更しない）。
    一時ファイルは **成功・失敗とも自動削除しない**（失敗時の再調査のため）。
    """
    ok, site_or_msg = config_ready()
    if not ok:
        return {"ok": False, "stage": "config", "error": site_or_msg}
    site = site_or_msg

    # 投稿先カテゴリは店舗別。未登録の店舗は**1枚も送らずに中止**する
    # （推測したカテゴリへ投稿しないため）。既定は高田馬場＝従来動作。
    _store = payload.get("store", WP_STORE)
    _cat = store_category(_store)
    if _cat is None:
        return {"ok": False, "stage": "config", "uploaded": [],
                "error": f"{_store} の WordPress カテゴリが未登録です"
                         "（wp_client.WP_STORE_CATEGORY へ term_id / slug を登録してください）"}

    plan = plan_blocks(payload)
    found, miss_req, miss_opt = collect_files(plan, payload["output_dir"])

    if not os.path.isdir(payload["output_dir"]):
        return {"ok": False, "stage": "precheck",
                "error": f"出力フォルダが見つかりません: {payload['output_dir']}",
                "missing": [], "uploaded": []}
    if miss_req:
        return {"ok": False, "stage": "precheck",
                "error": f"必須画像が {len(miss_req)} 件不足しているため中止しました"
                         "（1枚もアップロードしていません）",
                "missing": miss_req, "missing_optional": miss_opt, "uploaded": []}
    if not found:
        return {"ok": False, "stage": "precheck",
                "error": "送信対象の画像が1枚もありません", "missing": [], "uploaded": []}

    # ── 縦長画像を送信用に分割（原本は読み取るだけ）──
    tmp_dir = tempfile.mkdtemp(prefix="wp_split_")
    try:
        split_map = plan_split(found, tmp_dir)
    except Exception as e:
        return {"ok": False, "stage": "split", "tmp_dir": tmp_dir,
                "error": f"送信用画像の分割に失敗: {type(e).__name__}: {e}",
                "uploaded": []}

    # 実際に送るファイルの並び（分割対象は片に置き換える）
    send: list[dict] = []
    for f in found:
        parts = split_map.get(f["file"])
        if parts:
            for p in parts:
                send.append({"file": p["file"], "path": p["path"],
                             "bytes": p["bytes"],
                             "label": f["label"] + f"（分割 {p['file']}）"})
        else:
            send.append(f)

    media_map: dict[str, dict] = {}
    uploaded: list[dict] = []
    total = len(send)
    for i, f in enumerate(send, 1):
        if progress:
            progress(i, total, f["file"])
        r = upload_media(f["path"])
        if not r["ok"]:
            return {"ok": False, "stage": "upload", "failed": r,
                    "uploaded": uploaded, "missing_optional": miss_opt,
                    "tmp_dir": tmp_dir,
                    "error": f"{f['file']} のアップロードに失敗（status={r['status']}）"
                             f" / {r.get('error', '')}"
                             + (f" / Retry-After={r['retry_after']}"
                                if r.get("retry_after") else "")}
        media_map[f["file"]] = {"id": r["id"], "src": r["src"]}
        uploaded.append({"file": f["file"], "id": r["id"], "src": r["src"],
                         "sec": r["sec"], "bytes": f["bytes"]})

    title   = build_title(payload.get("date"), _store)
    content = build_content(plan, media_map, site=site, split_map=split_map,
                            category_slug=_cat["slug"])
    res = create_draft(title, content, category_id=_cat["id"])
    if not res["ok"]:
        return {"ok": False, "stage": "post", "uploaded": uploaded,
                "missing_optional": miss_opt, "tmp_dir": tmp_dir,
                "error": f"下書き作成に失敗（status={res['status']}）/ {res.get('error', '')}"}

    return {"ok": True, "id": res["id"], "post_status": res["post_status"],
            "edit_url": res["edit_url"], "title": title,
            "uploaded": uploaded, "missing_optional": miss_opt,
            "image_count": total, "split_map": split_map, "tmp_dir": tmp_dir,
            "total_bytes": sum(u["bytes"] for u in uploaded)}
