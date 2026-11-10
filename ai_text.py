"""スロバース用：⑧で完成した結果テキストと、取得済みの台別データ（Pision）から AI で投稿文を作る。

- Streamlit に依存しない処理だけを置く（画面は streamlit_app.py の _slv_ai_section）。
- AI に送るのは、⑧で使った df（Pision 取得データ・補正後差枚）から Python で集計した「AI用データ」と
  結果テキストだけ。集計・割合・順位は Python で計算し、AI には計算させない。Pision へは再取得しない。
- APIキーは呼び出し側が get_secret_value() で取得して渡す。キーの値はこのモジュールで表示・ログ出力しない。
- 既定は実API（ボタンを押したときだけ）。SLV_AI_MODE = "mock" にすると API を呼ばない見本になる。
- 実APIは 1回押す＝1リクエスト：SDKの自動再試行 0回・fallbacks なし・自動再生成なし。
- anthropic は実APIを呼ぶときだけ import する（モックでは不要）。
"""
from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field

# ── 設定（secrets.toml / .env の同名キーで上書きできる）──────────────────
# モデルID・料金は公式 Models overview（2026-11-10 確認）の値。
AI_MODELS: "dict[str, dict]" = {
    "claude-sonnet-5-5": {"label": "Claude Sonnet 5.5（標準）", "in": 2.00, "out": 10.00},
    "claude-opus-5-5":   {"label": "Claude Opus 5.5（高品質・高め）", "in": 4.00, "out": 20.00},
    "claude-haiku-5-5":  {"label": "Claude Haiku 5.5（安価・簡易）", "in": 0.10, "out": 0.50},
}
DEFAULT_MODEL = "claude-sonnet-5-5"

# 文章スタイル（画面で切り替え・既定は短文）。guide は長さの目安（上限ではない）。
STYLES: "dict[str, dict]" = {
    "short": {"label": "短文", "guide": "全角120字程度",
              "focus": "その日のいちばんの特徴を1〜2点に絞って簡潔に紹介する"},
    "standard": {"label": "標準", "guide": "全角250〜350字程度",
                 "focus": "全体の特徴に加え、注目ポイントを3〜4点（機種単位の配分・勝率、高差枚の台、ジャグラー／バラエティ、並び・末尾などから、その日に目立ったもの）を選んで分析する"},
    "detail": {"label": "詳細", "guide": "全角600〜1,200字程度（データに見どころが多ければ超えてよい）",
               "focus": "全体傾向 → 機種別の配分・勝率 → 高差枚の個別台 → ジャグラー・バラエティ → 並び・末尾 → 総合まとめ、の順で、取得データを使って詳しく考察する。短い見出し（絵文字付き）で区切ってよい"},
}
DEFAULT_STYLE = "short"

DEFAULT_MODE = "api"           # "api"＝実API（ボタンを押したときだけ） / "mock"＝APIを呼ばない見本（SLV_AI_MODE=mock）
DEFAULT_MAX_TOKENS = 6000      # 1回の出力上限（思考を含む・詳細も途中で切れない量）
DEFAULT_MAX_CALLS = 10         # 1セッション（ブラウザ1つ）あたりの実API呼び出し上限
DEFAULT_EFFORT = "medium"      # 分析を含むので medium（設定で low/high に変更可）
MAX_INPUT_CHARS = 80000        # 送信テキストの上限（超えたら送らない・切り詰めもしない）
SDK_MAX_RETRIES = 0            # SDKの自動再試行（429/5xx/接続エラーでも再送しない）
REQUEST_TIMEOUT_SEC = 120.0
EFFORTS = ("low", "medium", "high")
# 入力トークンの概算係数（実測：AI用データ＋指示 11,809字 → 11,360トークン＝0.962）。表示用の目安
TOKENS_PER_CHAR = 0.96

SETTING_KEYS = {
    "mode": "SLV_AI_MODE",
    "model": "SLV_AI_MODEL",
    "style": "SLV_AI_STYLE",
    "max_tokens": "SLV_AI_MAX_TOKENS",
    "max_calls": "SLV_AI_MAX_CALLS",
    "effort": "SLV_AI_EFFORT",
}
API_KEY_NAME = "ANTHROPIC_API_KEY"


def load_settings(get_value) -> dict:
    """get_value(key, default) で設定を読む（get_secret_value を渡す）。不正値は既定値へ戻す。"""
    def _int(key, default, lo, hi):
        try:
            v = int(str(get_value(key, default)).strip())
        except Exception:
            return default
        return v if lo <= v <= hi else default

    def _str(key, default):
        return str(get_value(key, default) or default).strip()

    mode = _str(SETTING_KEYS["mode"], DEFAULT_MODE).lower()
    model = _str(SETTING_KEYS["model"], DEFAULT_MODEL)
    style = _str(SETTING_KEYS["style"], DEFAULT_STYLE).lower()
    effort = _str(SETTING_KEYS["effort"], DEFAULT_EFFORT).lower()
    return {
        "mode": mode if mode in ("mock", "api") else DEFAULT_MODE,
        "model": model if model in AI_MODELS else DEFAULT_MODEL,
        "style": style if style in STYLES else DEFAULT_STYLE,
        "max_tokens": _int(SETTING_KEYS["max_tokens"], DEFAULT_MAX_TOKENS, 256, 16000),
        "max_calls": _int(SETTING_KEYS["max_calls"], DEFAULT_MAX_CALLS, 0, 200),
        "effort": effort if effort in EFFORTS else DEFAULT_EFFORT,
    }


# ── 数値の書式（AI用データ・モック・検証で共通）──────────────────────────
def fmt_signed(n: int) -> str:
    """+1,234枚 / -1,234枚 / ±0枚（結果テキストと同じ書式）"""
    n = int(n)
    return f"+{n:,}枚" if n > 0 else (f"{n:,}枚" if n < 0 else "±0枚")


def fmt_rate(win: int, total: int) -> str:
    """勝率：12/20台（60.0%）。割合は Python で小数1桁に丸める。"""
    pct = (win / total * 100) if total else 0.0
    return f"{win}/{total}台（{pct:.1f}%）"


def fmt_games(g: float) -> str:
    return f"{int(round(g)):,}G"


def fmt_gassan(games: int, bonus: int) -> str:
    return f"1/{games / bonus:.1f}" if bonus > 0 else "-"


_WEEK = "月火水木金土日"


# ── AI用データ（Python で集計して構造化テキストにする）────────────────────
UNITS_TOP = 40        # 差枚上位の台（個別）
UNITS_BOTTOM = 10     # 差枚下位の台（個別）
CONTEXT_SOFT_LIMIT = 60000   # これを超えたら、個別台の一覧から順に縮める（機種別集計は必ず全機種残す）


@dataclass
class AIContext:
    ok: bool
    error: str = ""
    text: str = ""
    checks: list = field(default_factory=list)   # (項目, OK/NG, 内容)
    stats: dict = field(default_factory=dict)
    ban_map: dict = field(default_factory=dict)  # 台番 → 機種名
    machines: list = field(default_factory=list)


def _report_total(report_text: str) -> "int | None":
    m = re.search(r"総差枚：([+\-−]?[\d,]+)枚", report_text or "")
    if not m:
        return None
    return int(m.group(1).replace(",", "").replace("−", "-"))


def build_context(df, report_text: str, *, store_key: str, store_label: str, date,
                  excel_name: str, jug_series=(), source: str = "Pision") -> AIContext:
    """⑧で使った df（補正後差枚・機種名変換済み）と結果テキストから AI 用データを作る。
    df の列：台番・機種名・差枚（必須）、ゲーム数・BB・RB・AT（あれば使う）。
    対象店舗・日付の取り違えを、Excel名・結果テキストの1行目・df と突き合わせて止める。"""
    checks: list = []
    if df is None or len(df) == 0:
        return AIContext(ok=False, error="台別データがありません（⑧を実行してから使ってください）。")
    for col in ("台番", "機種名", "差枚"):
        if col not in df.columns:
            return AIContext(ok=False, error=f"台別データに「{col}」列がありません。")
    # 日付・店舗の照合（Excel名 YYYYMMDD_店舗_20S.xlsx・結果テキスト1行目 MM/DD）
    if isinstance(date, _dt.datetime):
        date = date.date()
    m = re.match(r"(\d{8})_(.+?)_20S\.(xlsx|xls|csv)$", excel_name or "")
    if not m:
        checks.append(("Excel名", "注意", f"形式が想定と違います：{excel_name}"))
    else:
        ymd, st_ = m.group(1), m.group(2)
        if st_ != store_key:
            return AIContext(ok=False, error=f"Excel名の店舗（{st_}）が対象店舗（{store_key}）と違うため作りません。")
        if date is not None and ymd != date.strftime("%Y%m%d"):
            return AIContext(ok=False, error=f"Excel名の日付（{ymd}）と⑧の日付（{date:%Y%m%d}）が違うため作りません。")
        if date is None:
            date = _dt.date(int(ymd[:4]), int(ymd[4:6]), int(ymd[6:8]))
        checks.append(("Excel名と店舗・日付", "OK", f"{ymd}_{st_}"))
    first = (report_text or "").splitlines()[0].strip() if report_text else ""
    if date is not None:
        want = f"{date.month:02d}/{date.day:02d}"
        if not first.startswith(want):
            return AIContext(ok=False, error=f"結果テキストの日付（{first}）と対象日（{want}）が違うため作りません。")
        checks.append(("結果テキストの日付", "OK", first))

    d = df.copy()
    d["台番"] = d["台番"].astype(int)
    d["差枚"] = d["差枚"].astype(int)
    has_g = "ゲーム数" in d.columns
    has_bb, has_rb, has_at = "BB" in d.columns, "RB" in d.columns, "AT" in d.columns
    if has_g:
        d["ゲーム数"] = d["ゲーム数"].astype(int)
    n_units = len(d)
    total = int(d["差枚"].sum())
    avg = int(round(d["差枚"].mean()))
    win = int((d["差枚"] > 0).sum())
    rep_total = _report_total(report_text)
    if rep_total is not None:
        if rep_total != total:
            return AIContext(ok=False, error=(f"台別データの総差枚（{fmt_signed(total)}）と結果テキストの総差枚"
                                              f"（{fmt_signed(rep_total)}）が一致しないため作りません。"))
        checks.append(("総差枚（台別データ＝結果テキスト）", "OK", fmt_signed(total)))
    ban_map = {int(b): str(n) for b, n in zip(d["台番"], d["機種名"])}
    if len(ban_map) != n_units:
        checks.append(("台番の重複", "注意", f"{n_units - len(ban_map)}件"))

    week = _WEEK[date.weekday()] if date is not None else ""
    L: list[str] = []
    L.append("【基本情報】")
    L.append(f"日付：{date:%Y-%m-%d}（{week}）／店舗：{store_label}／データ：{source}の取得済み確定データ {n_units}台" if date
             else f"店舗：{store_label}／データ：{source} {n_units}台")
    L.append("※差枚は結果テキスト・画像と同じ補正後の値。G数は台ごとの実G数の合計・平均。割合と平均は集計済み（再計算しない）。")
    L.append("")
    L.append("【店舗全体】")
    line = f"総台数 {n_units}台／総差枚 {fmt_signed(total)}／平均差枚 {fmt_signed(avg)}／勝率 {fmt_rate(win, n_units)}"
    if has_g:
        line += f"／平均G数 {fmt_games(d['ゲーム数'].mean())}"
    L.append(line)
    L.append("／".join(f"{fmt_signed(t).replace('枚', '')}枚以上 {int((d['差枚'] >= t).sum())}台"
                       for t in (1000, 3000, 5000, 10000)))
    L.append("")

    # 機種別集計
    g = d.groupby("機種名", sort=False)
    rows = []
    for name, x in g:
        n = len(x)
        r = {"name": str(name), "n": n, "total": int(x["差枚"].sum()), "avg": int(round(x["差枚"].mean())),
             "win": int((x["差枚"] > 0).sum()),
             "best_ban": int(x.loc[x["差枚"].idxmax(), "台番"]), "best": int(x["差枚"].max())}
        if has_g:
            r["g"] = float(x["ゲーム数"].mean())
            if has_bb and has_rb:
                r["gassan"] = fmt_gassan(int(x["ゲーム数"].sum()), int(x["BB"].sum() + x["RB"].sum()))
        r["jug"] = str(name) in set(jug_series or ())
        rows.append(r)
    multi = sorted([r for r in rows if r["n"] >= 2], key=lambda r: (-r["avg"], r["name"]))
    single = sorted([r for r in rows if r["n"] == 1], key=lambda r: (-r["total"], r["name"]))

    def _grp(rs):
        n = sum(r["n"] for r in rs)
        t = sum(r["total"] for r in rs)
        w = sum(r["win"] for r in rs)
        return n, t, w

    n2, t2, w2 = _grp(multi)
    n1, t1, w1 = _grp(single)
    L.append("【設置台数別】")
    if n2:
        L.append(f"2台以上の機種：{len(multi)}機種・{n2}台／総差枚 {fmt_signed(t2)}／平均差枚 {fmt_signed(round(t2 / n2))}／勝率 {fmt_rate(w2, n2)}")
    if n1:
        L.append(f"1台設置の機種（バラエティ）：{len(single)}機種・{n1}台／総差枚 {fmt_signed(t1)}／平均差枚 {fmt_signed(round(t1 / n1))}／勝率 {fmt_rate(w1, n1)}")
    L.append("")

    jug_rows = [r for r in rows if r["jug"]]
    if jug_rows:
        jn, jt, jw = _grp(jug_rows)
        j1000 = int((d[d["機種名"].isin({r["name"] for r in jug_rows})]["差枚"] >= 1000).sum())
        L.append("【ジャグラー全体】")
        L.append(f"{len(jug_rows)}機種・{jn}台／総差枚 {fmt_signed(jt)}／平均差枚 {fmt_signed(round(jt / jn))}／"
                 f"勝率 {fmt_rate(jw, jn)}／+1,000枚以上 {j1000}台")
        for r in sorted(jug_rows, key=lambda r: (-r["avg"], r["name"])):
            L.append(_machine_line(r, has_g))
        L.append("")

    head = "機種名｜台数｜総差枚｜平均差枚｜勝率｜平均G数｜合算｜最高（台番 差枚）" if has_g else "機種名｜台数｜総差枚｜平均差枚｜勝率｜最高（台番 差枚）"
    L.append("【機種別集計（2台以上・平均差枚の高い順・全機種）】")
    L.append(head)
    for r in multi:
        L.append(_machine_line(r, has_g))
    L.append("")

    def _unit_line(row) -> str:
        s = f"{int(row['台番'])}番台｜{row['機種名']}｜{fmt_signed(row['差枚'])}"
        if has_g:
            s += f"｜{int(row['ゲーム数']):,}G"
        parts = []
        if has_bb:
            parts.append(f"BB{int(row['BB'])}")
        if has_rb:
            parts.append(f"RB{int(row['RB'])}")
        if has_at and int(row.get("AT", 0) or 0) > 0:
            parts.append(f"AT{int(row['AT'])}")
        if parts:
            s += "｜" + " ".join(parts)
        return s

    single_lines = ["【1台設置の機種（差枚の高い順・全機種）】", "台番｜機種名｜差枚｜G数｜BB RB AT"]
    for r in single:
        row = d[d["台番"] == r["best_ban"]].iloc[0]
        single_lines.append(_unit_line(row))
    single_lines.append("")

    srt = d.sort_values(["差枚", "台番"], ascending=[False, True])
    top = srt.head(UNITS_TOP)
    bottom = srt.tail(UNITS_BOTTOM).sort_values(["差枚", "台番"])
    unit_lines = [f"【差枚上位{len(top)}台】", "台番｜機種名｜差枚｜G数｜BB RB AT"]
    unit_lines += [_unit_line(r) for _, r in top.iterrows()]
    unit_lines += ["", f"【差枚下位{len(bottom)}台】"] + [_unit_line(r) for _, r in bottom.iterrows()] + [""]

    tail = ["【既存の集計結果（結果テキスト・全台系／ハーフ系／並び／末尾／単品優秀台など）】", report_text.strip()]
    body = "\n".join(L + single_lines + unit_lines + tail)
    notes = []
    if len(body) > CONTEXT_SOFT_LIMIT:
        # 送信量の制御：機種別集計・ジャグラー・既存集計は残し、1台設置の一覧を上位30件に縮める
        keep = single_lines[:2] + single_lines[2:32] + [f"（ほか{max(0, len(single) - 30)}機種は省略。合計は【設置台数別】のとおり）", ""]
        body = "\n".join(L + keep + unit_lines + tail)
        notes.append("1台設置の機種一覧を上位30件に縮めました（合計値は全機種で集計）")
    if len(body) > CONTEXT_SOFT_LIMIT:
        unit_lines = unit_lines[:2 + 20] + ["（差枚上位は20台まで）", ""]
        body = "\n".join(L + keep + unit_lines + tail)
        notes.append("差枚上位の台一覧を20台に縮めました")
    stats = {"units": n_units, "machines": len(rows), "multi": len(multi), "single": len(single),
             "jug_machines": len(jug_rows), "chars": len(body), "total": total, "avg": avg, "win": win,
             "notes": notes, "date": date.isoformat() if date else "", "store": store_key}
    checks.append(("台数（台別データ）", "OK", f"{n_units}台・{len(rows)}機種"))
    return AIContext(ok=True, text=body, checks=checks, stats=stats, ban_map=ban_map,
                     machines=[r["name"] for r in rows])


def _machine_line(r: dict, has_g: bool) -> str:
    s = f"{r['name']}｜{r['n']}台｜{fmt_signed(r['total'])}｜{fmt_signed(r['avg'])}｜{fmt_rate(r['win'], r['n'])}"
    if has_g:
        s += f"｜{fmt_games(r['g'])}｜{r.get('gassan', '-')}"
    s += f"｜{r['best_ban']}番台 {fmt_signed(r['best'])}"
    return s


# ── プロンプト ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは、パチスロ店の営業結果を X（旧Twitter）へ投稿する分析記事を書く担当です（スロバースの投稿）。
入力の <data> は、店舗の台別データ（取得済みの確定データ）から Python で集計した数値と、既存の集計結果（結果テキスト）です。これを読み、その日の結果を分析・考察した投稿文を1つ書いてください。

## 事実の扱い（最優先）
- 台番・機種名・差枚・台数・勝率・割合（%）・平均差枚・G数・合算・総差枚・日付・店名は、<data> に書かれているものだけを使い、表記をそのまま写す（+や,や%の書き方も同じ）。
- 台数は「(5/5台)」「12/20台（60.0%）」のように <data> の括弧を含めた表記をできるだけそのまま使う。
- 足し算・引き算・割合・平均・順位・機種数や台数の数え上げなど、<data> に無い数値を自分で計算しない。四捨五入や「約」「超え」などの言い換えもしない。
- 割合・台数・差枚を「3割台半ば」「約半数」「大半」「一部」のような曖昧な言葉に言い換えない。触れるときは <data> の数値をそのまま書く。
- <data> に無い台番・機種名・数値・出来事（設定・イベント・来店・取材など）は書かない。
- 設定についての推測や示唆（「高設定」「設定6」「全台6」「設定示唆」など）は書かない。
- データで確認できない因果関係（「〜が全体を押し上げた」「〜のおかげで」「〜に引っ張られて」など）は書かない。全体への影響を書くのは、その機種の総差枚と店舗全体の総差枚のように、<data> の数値を並べて示せるときだけにする。
- 機種同士を比べるときは、比べる両方の機種名と根拠の数値を書く。「同系統」「同シリーズ」などの括りも、両方の機種名と数値を挙げられるときだけ使う。
- 実績（<data> の数値）と考察を書き分ける。考察は、直前に書いた数値を根拠にした短い文にし、断定的な予想や推測（「狙い目」「次回も」など）は書かない。

## 書き方
- 1行目に日付と店名（結果テキストの1・2行目の表記どおり。例「11/04(水) 【店名】」）。
- 結果テキストの言い換えや数値の羅列ではなく、データからその日の特徴を読み取って自然な文章で伝える。全項目を並べず、その日に重要なものを選ぶ。
- 機種別の紹介は注目機種を優先して絞り、数値を並べるだけでなく、何が目立ったのかを説明する。
- 個別台を並べるとき、G数を書くなら並べる全台に書く。揃えられない場合はG数を書かない。
- 同じ文末を続けない。読みやすく改行し、絵文字は適度に使う。
- ハッシュタグ・URL・宣伝文句は付けない。「爆発」「確定」「激アツ」のような過剰な煽りは書かない。
- 長さの目安：{guide}。
- 内容：{focus}。

## 出力
- 投稿本文だけを出力する。前置き・説明・コードブロックは付けない。"""

USER_TEMPLATE = "<data>\n{data}\n</data>"


def build_system_prompt(style: str) -> str:
    st_ = STYLES.get(style, STYLES[DEFAULT_STYLE])
    return SYSTEM_PROMPT.replace("{guide}", st_["guide"]).replace("{focus}", st_["focus"])


def build_request(data_text: str, settings: dict) -> dict:
    """messages.create に渡す引数（APIキーを含まない・fallbacks/betas なし）。"""
    return {
        "model": settings["model"],
        "max_tokens": int(settings["max_tokens"]),
        "system": build_system_prompt(settings["style"]),
        "messages": [{"role": "user", "content": USER_TEMPLATE.format(data=data_text)}],
        "output_config": {"effort": settings["effort"]},
    }


def estimate_request(data_text: str, settings: dict) -> dict:
    """送信量と入力料金の概算（API を呼ばない・係数は実測からの目安）。"""
    req = build_request(data_text, settings)
    chars = len(req["system"]) + len(req["messages"][0]["content"])
    tok = int(chars * TOKENS_PER_CHAR)
    p = AI_MODELS.get(settings["model"], AI_MODELS[DEFAULT_MODEL])
    out_guess = {"short": 300, "standard": 700, "detail": 2000}.get(settings["style"], 500)
    return {"chars": chars, "tokens": tok, "in_usd": tok / 1e6 * p["in"],
            "out_tokens_guess": out_guess, "total_usd": tok / 1e6 * p["in"] + out_guess / 1e6 * p["out"]}


# ── X の文字数（twitter-text v3 の重み付け・表示のみ）────────────────────
_X_LIGHT = ((0x0000, 0x10FF), (0x2000, 0x200D), (0x2010, 0x201F), (0x2032, 0x2037))
_URL_RE = re.compile(r"https?://\S+")
_EMOJI_BASE = re.compile(
    "[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿〰〽㊗㊙©®‼⁉™ℹ↔-↪]")
_EMOJI_SEQ = re.compile(
    "(?:[0-9#*]️?⃣)"
    "|(?:[\U0001F1E6-\U0001F1FF]{2})"
    "|(?:" + _EMOJI_BASE.pattern + "[︎️]?[\U0001F3FB-\U0001F3FF]?"
    "(?:‍" + _EMOJI_BASE.pattern + "[︎️]?[\U0001F3FB-\U0001F3FF]?)*)")


def _x_char_weight(ch: str) -> int:
    cp = ord(ch)
    return 1 if any(a <= cp <= b for a, b in _X_LIGHT) else 2


def x_weighted_length(text: str) -> int:
    """X の重み付き文字数（日本語1字＝2、半角英数＝1、絵文字＝2、URL＝23）。表示用。"""
    s = unicodedata.normalize("NFC", text or "")
    total, i = 0, 0
    for m in _URL_RE.finditer(s):
        total += _x_seg(s[i:m.start()]) + 23
        i = m.end()
    total += _x_seg(s[i:])
    return total


def _x_seg(s: str) -> int:
    total, i = 0, 0
    while i < len(s):
        m = _EMOJI_SEQ.match(s, i)
        if m and m.end() > i:
            total += 2
            i = m.end()
            continue
        total += _x_char_weight(s[i])
        i += 1
    return total


def x_check(text: str) -> dict:
    """文字数の表示用（上限の判定はしない）。chars＝見た目の字数、weight＝Xの重み付き数、zen＝全角換算。"""
    w = x_weighted_length(text)
    return {"chars": len(text or ""), "weight": w, "zen": w / 2}


# ── 結果 ─────────────────────────────────────────────────────────────
@dataclass
class AIResult:
    ok: bool
    text: str = ""
    error: str = ""
    warning: str = ""
    model: str = ""
    mock: bool = False
    input_tokens: int = 0
    output_tokens: int = 0
    stop_reason: str = ""
    request_id: str = ""

    @property
    def cost_usd(self) -> float:
        p = AI_MODELS.get(self.model)
        if not p or self.mock:
            return 0.0
        return self.input_tokens / 1e6 * p["in"] + self.output_tokens / 1e6 * p["out"]


def check_input(data_text: str) -> str:
    """送信前チェック。問題があれば日本語のエラー文、なければ ""。"""
    if not (data_text or "").strip():
        return "AI用データが空のため生成できません。⑧を実行してから押してください。"
    if len(data_text) > MAX_INPUT_CHARS:
        return (f"AI用データが長すぎます（{len(data_text):,}字・上限{MAX_INPUT_CHARS:,}字）。"
                "切り詰めずに送らないため、生成を中止しました。")
    return ""


# ── モック（APIを呼ばない）───────────────────────────────────────────
_MOCK_OPENERS = ("📊結果分析", "🔍本日の傾向", "📝データまとめ", "✨ハイライト")


def mock_generate(data_text: str, variant: int = 0, model: str = DEFAULT_MODEL,
                  style: str = DEFAULT_STYLE) -> AIResult:
    """AI用データの行をそのまま拾って並べるだけの決定的なモック（数値は入力の表記のまま）。"""
    err = check_input(data_text)
    if err:
        return AIResult(ok=False, error=err, model=model, mock=True)
    style = style if style in STYLES else DEFAULT_STYLE
    sec = _sections(data_text)
    rep = sec.get("既存の集計結果", [])
    head = " ".join([ln for ln in rep[:3] if ln.strip()][:2])
    whole = (sec.get("店舗全体") or [""])[0]
    mach = [ln for ln in sec.get("機種別集計", [])[1:] if "｜" in ln]
    units = [ln for ln in sec.get("差枚上位", [])[1:] if "｜" in ln]
    jug = (sec.get("ジャグラー全体") or [""])[0]
    var = [ln for ln in sec.get("設置台数別", []) if "バラエティ" in ln]
    n = {"short": 1, "standard": 3, "detail": 6}[style]
    k = variant % max(1, len(mach))
    body = [head, f"【モック#{variant + 1}・{STYLES[style]['label']}】{_MOCK_OPENERS[variant % 4]}",
            f"・全体：{whole}"]
    body += [f"・機種：{ln}" for ln in (mach[k:] + mach[:k])[:n]]
    body += [f"・台：{ln}" for ln in (units[k:] + units[:k])[:n]]
    if style != "short" and jug:
        body.append(f"・ジャグラー：{jug}")
    if style == "detail" and var:
        body.append(f"・{var[0]}")
    return AIResult(ok=True, text="\n".join(body).strip(), model=model, mock=True, stop_reason="mock")


_SECTION_KEYS = ("基本情報", "店舗全体", "設置台数別", "ジャグラー全体", "機種別集計", "1台設置",
                 "差枚上位", "差枚下位", "既存の集計結果")


def _sections(text: str) -> dict:
    """AI用データを見出し（【基本情報】など・既知の名前だけ）ごとの行リストに分ける。
    結果テキスト内の【店名】は見出しとして扱わない。"""
    out, cur = {}, None
    for ln in text.splitlines():
        s = ln.strip()
        key = None
        if s.startswith("【") and s.endswith("】"):
            inner = s[1:-1]
            key = next((k for k in _SECTION_KEYS if inner.startswith(k)), None)
        if key:
            cur = key
            out[cur] = []
            continue
        if cur is not None and s:
            out[cur].append(s)
    return out


# ── 実API ────────────────────────────────────────────────────────────
def make_client(api_key: str):
    """自動再試行なしのクライアント（1回押す＝1リクエスト）。"""
    import anthropic
    return anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SEC, max_retries=SDK_MAX_RETRIES)


def api_generate(data_text: str, settings: dict, api_key: "str | None", client=None) -> AIResult:
    """Claude API で1回だけ生成する。client を渡すとそれを使う（テスト用・通信なし）。"""
    model = settings["model"]
    err = check_input(data_text)
    if err:
        return AIResult(ok=False, error=err, model=model)
    if client is None:
        if not api_key:
            return AIResult(ok=False, model=model, error=(
                f"APIキー（{API_KEY_NAME}）が設定されていません。ローカルは .streamlit/secrets.toml、"
                "Cloud は Streamlit Cloud の Secrets に登録してください。"))
        try:
            client = make_client(api_key)
        except ImportError:
            return AIResult(ok=False, model=model, error=(
                "anthropic ライブラリが入っていません。ローカルは `py -3.14 -m pip install anthropic`、"
                "Cloud は requirements_streamlit.txt に anthropic を追加してください。"))

    req = build_request(data_text, settings)
    try:
        resp = client.messages.create(**req)
    except Exception as e:  # 例外の種類だけを日本語にする（本文やキーは出さない）・再送しない
        return AIResult(ok=False, model=model, error=_error_message(e))

    texts = [getattr(b, "text", "") for b in (getattr(resp, "content", None) or [])
             if getattr(b, "type", "") == "text"]
    text = "\n".join(t for t in texts if t).strip()
    usage = getattr(resp, "usage", None)
    res = AIResult(
        ok=True, text=text, model=str(getattr(resp, "model", model) or model),
        input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
        output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
        stop_reason=str(getattr(resp, "stop_reason", "") or ""),
        request_id=str(getattr(resp, "_request_id", "") or ""),
    )
    if res.stop_reason == "refusal":
        res.ok = False
        res.error = "AIが生成を断りました（安全上の判断）。結果テキストを確認してください（自動では再生成しません）。"
    elif res.stop_reason == "max_tokens":
        res.warning = "出力上限に達したため、文章が途中で切れている可能性があります（設定の出力上限を上げてください）。"
    if res.ok and not res.text:
        res.ok = False
        res.error = "AIの応答に本文がありませんでした（自動では再生成しません）。"
    return res


def _error_message(e: Exception) -> str:
    name = type(e).__name__
    status = getattr(e, "status_code", None)
    table = {
        "AuthenticationError": "APIキーが無効です（401）。キーを確認してください。",
        "PermissionDeniedError": "このAPIキーでは利用できません（403）。",
        "NotFoundError": "モデルが見つかりません（404）。設定のモデルIDを確認してください。",
        "RateLimitError": "利用上限に達しました（429）。時間をおいて、必要なら手動でもう一度押してください。",
        "BadRequestError": "リクエストが不正です（400）。設定（モデル・出力上限など）を確認してください。",
        "APITimeoutError": "タイムアウトしました。時間をおいて、必要なら手動でもう一度押してください。",
        "APIConnectionError": "Claude API に接続できませんでした。ネットワークを確認してください。",
    }
    if name in table:
        return table[name]
    if status and int(status) >= 500:
        return f"Claude API 側のエラーです（{status}）。時間をおいて、必要なら手動でもう一度押してください。"
    return f"生成に失敗しました（{name}）。"


# ── 整合性チェック（AI文章 ↔ AI用データ・台別データ）─────────────────────
_TRANS = str.maketrans({"＋": "+", "－": "-", "−": "-", "，": ",", "（": "(", "）": ")", "／": "/", "％": "%"})
_PATTERNS = (
    re.compile(r"\d{2,5}番台"),
    re.compile(r"[+\-]\d[\d,]*"),
    re.compile(r"\d[\d,]*枚"),
    re.compile(r"\d+/\d+台"),
    re.compile(r"\d+(?:\.\d+)?%"),
    re.compile(r"\d[\d,]*G"),
    re.compile(r"1/\d+(?:\.\d+)?"),
    re.compile(r"\d+機種"),
    re.compile(r"\d+台"),
)


def _norm(s: str) -> str:
    return (s or "").translate(_TRANS)


_ONE_COUNT = {"1機種", "1台"}   # 「1機種の存在感」「1台設置」などの言い回し。数え上げとして機械的に警告しない


def unverified_tokens(ai_text: str, source_text: str) -> list[str]:
    """AI文章の台番・差枚・台数・割合・G数などのうち、送ったデータに同じ表記が無いもの（重複なし・出現順）。
    「1機種」「1台」だけの言い回しは対象外（「11台」「1/4台」などは従来どおり照合する）。"""
    src = _norm(source_text)
    src_nc = src.replace(",", "")
    out: list[str] = []
    txt = _norm(ai_text)
    for pat in _PATTERNS:
        for m in pat.finditer(txt):
            tok = m.group(0)
            prev = txt[m.start() - 1] if m.start() > 0 else ""
            if tok[:1].isdigit() and prev and (prev.isdigit() or prev in ",./"):
                continue                      # 大きな数値・日付・割合の途中から始まる断片（全体は別のパターンで照合）
            if tok in _ONE_COUNT:
                continue
            if _in_source(tok, src) or _in_source(tok.replace(",", ""), src_nc):
                continue
            if tok not in out:
                out.append(tok)
    return out


def _in_source(tok: str, src: str) -> bool:
    """tok が src に「前後に数字が続かない形」で含まれるか（「11台」が「711台」の一部として一致しないように）。"""
    pre = r"(?<![\d,.])" if tok[:1].isdigit() else ""
    post = r"(?![\d])" if tok[-1:].isdigit() else ""
    return re.search(pre + re.escape(tok) + post, src) is not None


# 数値をぼかす表現（注意表示のみ。文章は書き換えない）
_VAGUE_PATTERNS = (
    (re.compile(r"\d割(台|強|弱|近く|程度|前後)?"), "割合を「N割」でぼかしています"),
    (re.compile(r"[一二三四五六七八九]割(台|強|弱|近く|程度|前後)?"), "割合を「N割」でぼかしています"),
    (re.compile(r"半数"), "「半数」は数値で書けます"),
    (re.compile(r"大半"), "「大半」は数値で書けます"),
    (re.compile(r"一部"), "「一部」は数値で書けます"),
    (re.compile(r"約(?=[\d０-９一二三四五六七八九十百千万半+\-])"), "「約」は丸めた数値です"),
)
_MANMAI_RE = re.compile(r"万枚(?:超え|オーバー|以上)(?:の台|台)?(?:が|は|も)?\s*(\d+)?\s*台?")
_TYPO_PATTERNS = (
    (re.compile(r"勝(?=\s*\d)"), "「勝率」の「率」が抜けている可能性"),
    (re.compile(r"枚枚|台台|番台台"), "単位が重なっている可能性"),
    (re.compile(r"\(\s*\)|（\s*）"), "空の括弧"),
)


def vague_and_typo_notes(ai_text: str, source_text: str) -> "tuple[list[str], list[str]]":
    """(数値をぼかす表現の注意, 表記ミスの疑い)。文章は書き換えない。
    「万枚超え」は、送ったデータの「+10,000枚以上 N台」が1台以上で、台数を書くならその N と一致するときだけ許容する。"""
    txt = ai_text or ""
    vague: list[str] = []
    for pat, why in _VAGUE_PATTERNS:
        for m in pat.finditer(txt):
            s = f"「{m.group(0)}」…{why}"
            if s not in vague:
                vague.append(s)
    src = _norm(source_text)
    mm = re.search(r"\+10,000枚以上\s*(\d+)台", src)
    n_src = int(mm.group(1)) if mm else 0
    for m in _MANMAI_RE.finditer(txt):
        n_txt = m.group(1)
        if n_src == 0:
            vague.append(f"「{m.group(0).strip()}」…送ったデータに +10,000枚以上の台がありません")
        elif n_txt is not None and int(n_txt) != n_src:
            vague.append(f"「{m.group(0).strip()}」…+10,000枚以上は {n_src}台です")
    typo: list[str] = []
    for pat, why in _TYPO_PATTERNS:
        for m in pat.finditer(txt):
            ctx_ = txt[max(0, m.start() - 6):m.end() + 6].replace("\n", " ")
            s = f"「…{ctx_}…」…{why}"
            if s not in typo:
                typo.append(s)
    return vague, typo


_AFTER_SKIP = " 　の：:は)）｜・"
_BEFORE_SKIP = " 　のはがで"


def _longest_prefix(s: str, names: "list[str]") -> "str | None":
    return next((n for n in names if s.startswith(n)), None)       # names は長い順


def _longest_suffix(s: str, names: "list[str]") -> "str | None":
    return next((n for n in names if s.endswith(n)), None)


def ban_machine_mismatches(ai_text: str, ban_map: dict, machines: "list[str]") -> list[str]:
    """台番と機種名の組が台別データと違うもの、台別データに無い台番を返す。
    - 判定は台番と「同じ行で隣り合う」機種名だけ。別の行・離れた位置の機種名は使わない
    - 「機種名(NNNN番台)」→ 括弧の直前の機種名、「NNNN番台 機種名」「NNNN番台の機種名」→ 直後の機種名、
      「機種名のNNNN番台」「機種名はNNNN番台」→ 直前の機種名（直後に機種名があればそちらを優先）
    - 隣に機種名が無い台番は組を判定しない（断定しない）。台番そのものが無い場合だけ指摘する"""
    out: list[str] = []
    names = sorted({m for m in machines if m}, key=len, reverse=True)
    for line in _norm(ai_text).splitlines():
        for m in re.finditer(r"(\d{2,5})番台", line):
            ban = int(m.group(1))
            if ban not in ban_map:
                msg = f"{ban}番台（台別データに無い台番）"
                if msg not in out:
                    out.append(msg)
                continue
            before = line[:m.start()]
            after = line[m.end():]
            if before.endswith("("):
                near = _longest_suffix(before[:-1].rstrip(), names)
            else:
                near = _longest_prefix(after.lstrip(_AFTER_SKIP), names)
                if near is None:
                    near = _longest_suffix(before.rstrip(_BEFORE_SKIP), names)
            if near is None:
                continue                      # 隣に機種名が無い → 判定しない
            if near != ban_map[ban]:
                msg = f"{ban}番台＝{ban_map[ban]}（文章では「{near}」と組になっています）"
                if msg not in out:
                    out.append(msg)
    return out


SETTING_WORDS = ("高設定", "低設定", "設定6", "設定5", "設定4", "設定示唆", "全6", "据え置き", "濃厚", "確定", "設定")
# 解釈・見立て・因果の表現（「傾向」「配分」だけでは警告しない）
INTERPRETIVE_WORDS = ("狙い目", "次回", "期待", "可能性", "かもしれ", "思われ", "推測", "予想", "示唆", "うかがえ",
                      "と言え", "印象", "意図", "力を入れ", "押し上げ", "引っ張", "牽引", "おかげ", "支え")


def _is_heading(line: str) -> bool:
    """見出し行（句点などで終わらない20字以下の行）。解釈表現の判定から外す。"""
    s = line.strip()
    return bool(s) and len(s) <= 20 and not re.search(r"[。！!？?]", s)


def speculative_notes(ai_text: str) -> "tuple[list[str], list[str]]":
    """(設定に関わる語を含む文, 解釈・見立て・因果を含む文)。数値では検証できない表現の注意表示用。
    設定に関わる語は見出し行も含めて調べる。解釈表現は見出し行を対象外にする。"""
    sents, heads = [], set()
    for line in (ai_text or "").splitlines():
        parts = [s.strip() for s in re.split(r"(?<=[。！!？?])", line) if s.strip()]
        if _is_heading(line):
            heads.update(parts)
        sents += parts
    setting = [s for s in sents if any(w in s for w in SETTING_WORDS)]
    interp = [s for s in sents if s not in setting and s not in heads
              and any(w in s for w in INTERPRETIVE_WORDS)]
    return setting, interp
