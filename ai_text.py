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
    "short": {"label": "短文", "guide": "全角200〜320字程度",
              "focus": "✅は3行、📊全体の結果は1〜2文、🏅好成績機種ピックアップは2機種を各1〜2文、💎単品の優秀台は1文、仕掛けは該当時に1文だけ"},
    "standard": {"label": "標準", "guide": "全角320〜500字程度",
                 "focus": "✅は3行、📊全体の結果は2〜3文、🏅好成績機種ピックアップは2〜3機種（個別台の好成績にも触れる）、💎単品の優秀台は1〜2文、仕掛けは該当時に要点だけ"},
    "detail": {"label": "詳細", "guide": "全角600〜1,200字程度（データに見どころが多ければ超えてよい）",
               "focus": "✅は3行、📊全体の結果を詳しく（設置台数別・ジャグラー全体・バラエティのプラスの実績も使ってよい）、🏅好成績機種ピックアップは2〜3機種を勝率・平均差枚・総差枚・個別台まで紹介、💎単品の優秀台は1〜3台、仕掛けは該当時に判定結果の数値を使って紹介する"},
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
                  excel_name: str, jug_series=(), source: str = "Pision",
                  ref_total: "int | None" = None, ref_note: str = "") -> AIContext:
    """⑧で使った df（補正後差枚・機種名変換済み）と結果テキストから AI 用データを作る。
    df の列：台番・機種名・差枚（必須）、ゲーム数・BB・RB・AT（あれば使う）。
    対象店舗・日付の取り違えを、Excel名・結果テキストの1行目・df と突き合わせて止める。
    ref_total：照合元の総差枚（呼び出し側が、アップロードされた Excel/CSV を df とは別に読み直して補正した差枚の合計）。
    df の総差枚と一致しなければ作らない。None（照合元を取得できない）なら未検証のまま作らない（ref_note は理由）。"""
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
    # 総差枚の照合（表示用の結果テキストの「総差枚：」の有無に依存しない）
    if ref_total is None:
        return AIContext(ok=False, error=("総差枚を照合できないため作りません（照合元："
                                          + (ref_note or "Excelを読み直した総差枚を取得できません") + "）。"))
    if int(ref_total) != total:
        return AIContext(ok=False, error=(f"台別データの総差枚（{fmt_signed(total)}）と、Excelを読み直した総差枚"
                                          f"（{fmt_signed(int(ref_total))}）が一致しないため作りません。"))
    checks.append(("総差枚（台別データ＝Excelを読み直した補正後差枚）", "OK", fmt_signed(total)))
    # 結果テキストに「総差枚：」がある日（平均+100枚以上）は、従来どおりその値とも照合する
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

    _sk = shikake_lines(report_text)
    shikake = (["【仕掛けの判定結果（既存処理の判定・これ以外を仕掛けとして扱わない）】"]
               + (_sk if _sk else ["該当なし"]) + [""])
    points = _points_lines(d, report_text, rows, total=total, avg=avg, win=win, n_units=n_units)
    tail = points + shikake + ["【既存の集計結果（結果テキスト・全台系／ハーフ系／並び／末尾／単品優秀台など）】", report_text.strip()]
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


POINT_TOTAL_MIN_AVG = 100     # 平均差枚がこれ以上なら全体の総差枚・平均差枚を書く（未満は書かない）
POINT_MACHINE_MIN_AVG = 1000  # 全台系・ハーフ系以外の好成績機種の候補：平均差枚の下限（2台以上・勝率50%以上）
POINT_MACHINES_MAX = 5        # 好成績機種の候補の最大数（文章で紹介するのは2〜3機種）
POINT_SINGLES_MAX = 3         # 💎単品の優秀台の候補（🏆その他の単品優秀台の差枚上位）


def _win_phrase(win: int, n: int) -> str:
    """「5台中4台がプラス、勝率80.0%」（勝率は Python で小数1桁に丸める）。"""
    return f"{n}台中{win}台がプラス、勝率{(win / n * 100) if n else 0.0:.1f}%"


def _report_blocks(report_text: str) -> dict:
    """結果テキストを「🏆見出し」ごとの行リストに分ける（（なし）は除く）。"""
    out, cur = {}, None
    for ln in (report_text or "").splitlines():
        t = ln.strip()
        if t.startswith("🏆") or t.startswith(APPEND_STOP):
            cur = t
            out[cur] = []
            continue
        if cur and t and t not in ("（なし）", "(なし)"):
            out[cur].append(t)
    return out


_GROUP_LINE_RE = re.compile(r"^[📌💎]?(.+?)\((\d+)/(\d+)台\)")
_SINGLE_LINE_RE = re.compile(r"^・?(.+)\((\d+)番台\)→([+\-][\d,]+枚)$")


def single_candidates(report_text: str, limit: int = POINT_SINGLES_MAX) -> "list[tuple[int, str, str]]":
    """結果テキストの「🏆その他の単品優秀台」から上位 limit 台（台番, 機種名, 差枚の表記）。差枚の高い順は結果テキストのまま。"""
    out = []
    for key, ls in _report_blocks(report_text).items():
        if key.startswith("🏆その他の単品優秀台"):
            for ln in ls:
                m = _SINGLE_LINE_RE.match(ln)
                if m:
                    out.append((int(m.group(2)), m.group(1), m.group(3)))
    return out[:limit]


def single_sentence(singles: "list[tuple[int, str, str]]") -> str:
    """💎単品の優秀台の1文（台番なし・機種名と差枚は候補の表記のまま・同じ機種は差枚を「・」でつなぐ）。"""
    groups: dict = {}
    for _b, name, diff in singles:
        groups.setdefault(name, []).append(diff)
    parts = [f"{n}が{'・'.join(ds)}" for n, ds in groups.items()]
    if not parts:
        return ""
    if len(singles) >= 3:
        return "、".join(parts) + "と単品からも爆発台が多数🌋"
    if len(singles) == 2:
        return "、".join(parts) + "と単品からも爆発台が登場🌋"
    return f"単品では{parts[0]}を記録🌋"


def _points_lines(d, report_text: str, rows: list, *, total: int, avg: int, win: int, n_units: int) -> list:
    """AI文章用の要点（Python で計算・判定済み）。プラスの実績だけを並べ、書く／書かないの判定も渡す。"""
    heads = [ln.strip() for ln in (report_text or "").splitlines() if ln.strip()][:2]
    blocks = _report_blocks(report_text)
    P = ["【AI文章用の要点（Python で計算・判定済み・この範囲で書く）】"]
    if len(heads) == 2:
        P += [f"日付行：{heads[0]}", f"店名行：{heads[1]}"]
    if avg >= POINT_TOTAL_MIN_AVG:
        P.append(f"全体の総差枚・平均差枚：書く（総差枚 {fmt_signed(total)}／平均差枚 {fmt_signed(avg)}）")
    else:
        P.append(f"全体の総差枚・平均差枚：書かない（平均差枚が+{POINT_TOTAL_MIN_AVG}枚未満のため・数値に触れない）")
    P.append("プラス台の実績：" + "／".join(f"+{t:,}枚以上 {int((d['差枚'] >= t).sum())}台"
                                       for t in (10000, 5000, 3000, 1000)))
    if n_units and win * 2 >= n_units:
        P.append(f"勝率：書いてよい（{_win_phrase(win, n_units)}）")
    else:
        P.append("勝率：書かない（50%未満のため）")
    by = {r["name"]: r for r in rows}
    cands, seen = [], set()

    def _add(name, kind):
        r = by.get(name)
        if r is None or name in seen or r["avg"] <= 0 or len(cands) >= POINT_MACHINES_MAX:
            return
        seen.add(name)
        cands.append((r, kind))

    for key, kind in (("🏆全台", "全台系"), ("🏆ハーフ系", "ハーフ系")):
        for ln in blocks.get(key, []):
            m = _GROUP_LINE_RE.match(ln)
            if m:
                _add(m.group(1), kind)
    for r in sorted([r for r in rows if r["n"] >= 2], key=lambda r: (-r["avg"], r["name"])):
        if r["avg"] >= POINT_MACHINE_MIN_AVG and r["win"] * 2 >= r["n"]:
            _add(r["name"], "2台以上")
    P.append("好成績機種の候補（全台系→ハーフ系→2台以上で平均差枚+1,000枚以上・勝率50%以上の順・最大5機種）：")
    if cands:
        for r, kind in cands:
            P.append(f"- {r['name']}｜{kind}｜{_win_phrase(r['win'], r['n'])}｜平均差枚 {fmt_signed(r['avg'])}｜"
                     f"総差枚 {fmt_signed(r['total'])}｜最高 {r['best_ban']}番台 {fmt_signed(r['best'])}")
    else:
        P.append("- （なし）")
    singles = []
    for key, ls in blocks.items():
        if key.startswith("🏆その他の単品優秀台"):
            for ln in ls:
                m = _SINGLE_LINE_RE.match(ln)
                if m:
                    singles.append((int(m.group(2)), m.group(1), m.group(3)))
    P.append(f"💎単品の優秀台の候補（🏆その他の単品優秀台の差枚上位{POINT_SINGLES_MAX}台・+10,000枚以上が先頭）：")
    if singles:
        P += [f"- {b}番台｜{n}｜{df_}" for b, n, df_ in singles[:POINT_SINGLES_MAX]]
    else:
        P.append("- （なし）")
    return P + [""]


def _machine_line(r: dict, has_g: bool) -> str:
    s = f"{r['name']}｜{r['n']}台｜{fmt_signed(r['total'])}｜{fmt_signed(r['avg'])}｜{fmt_rate(r['win'], r['n'])}"
    if has_g:
        s += f"｜{fmt_games(r['g'])}｜{r.get('gassan', '-')}"
    s += f"｜{r['best_ban']}番台 {fmt_signed(r['best'])}"
    return s


# ── プロンプト ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは、パチスロ店の営業結果を X（旧Twitter）へ投稿する紹介文を書く担当です（スロバースの投稿）。
入力の <data> は、店舗の台別データ（取得済みの確定データ）から Python で集計した数値と、既存の集計結果（結果テキスト）です。これを読み、その日のプラスの実績を中心に紹介する投稿文を1つ書いてください。

## 事実の扱い（最優先）
- 台番・機種名・差枚・台数・勝率・割合（%）・平均差枚・G数・合算・総差枚・日付・店名は、<data> に書かれているものだけを使い、数値の表記をそのまま写す（+や,や%の書き方も同じ）。
- 勝率は「4/5台（80.0%）」の形では書かず、【AI文章用の要点】の「5台中4台がプラス、勝率80.0%」の形で書く。機種名の後ろに「(2/3台)」のような短い台数表記を付けるのはよい。
- 括弧は半角の ( ) を使う（店名の【】はそのまま）。
- 数値の「+」の直前に空白を入れない（「平均差枚+8,100枚」「総差枚+24,300枚」「89番台+15,750枚」）。
- 足し算・引き算・割合・平均・順位・機種数や台数の数え上げなど、<data> に無い数値を自分で計算しない。四捨五入や「約」「超え」などの言い換えもしない。
- 割合・台数・差枚を「3割台半ば」「約半数」「大半」「一部」のような曖昧な言葉に言い換えない。
- <data> に無い台番・機種名・数値・出来事（設定・イベント・来店・取材など）は書かない。実績を誇張しない。
- 設定についての推測や示唆（「高設定」「設定6」「全台6」「設定示唆」など）は書かない。
- データで確認できない因果関係（「〜が全体を押し上げた」「〜のおかげで」「〜に引っ張られて」など）や、断定的な予想・推測（「狙い目」「次回も」など）は書かない。

## プラスの実績を中心にする
- マイナスの印象を与える文章は書かない。「厳しい」「苦戦」「不調」「マイナスの中で」「振るわない」などの否定的な表現は使わない。
- 「📉厳しかった機種」のような、マイナスの機種・台を紹介する項目は作らない。マイナスの機種・台・差枚には触れない。
- マイナスの総差枚・平均差枚は書かない。マイナスの数値をプラスのように言い換えることもしない。
- 紹介するのは <data> にあるプラスの結果だけにする。

## 構成（この順番・見出しはこの表記のまま）
- 1行目：【AI文章用の要点】の「日付行」をそのまま書く。
- 2行目：【AI文章用の要点】の「店名行」をそのまま書く（日付と店名は必ず別の行にする）。
- 3〜5行目：「✅」の1文字だけの行を3行（✅の後ろに文章・数値・空白を書かない）。
- 空行のあと「📊全体の結果」：
  - 【AI文章用の要点】の「全体の総差枚・平均差枚」が「書く」のときは、総差枚・平均差枚（実数値）を最初に書き、その後に +10,000枚以上・+5,000枚以上などの台数を書く。
  - 「書かない」のときは総差枚・平均差枚に触れず、+10,000枚以上・+5,000枚以上などプラス台の台数を中心に書く。
  - 台数は「プラス台の実績」の値を使い、0台の区分は書かない。勝率は「勝率：書いてよい」のときだけ書く。
  - プラスの実績の紹介で自然に締める。次の見出しへつなぐだけの文（「好成績の機種と台を紹介します👇」「その中から、好成績だった機種を紹介します！」など）は書かない。
- 空行のあと「🏅好成績機種ピックアップ」：
  - 【AI文章用の要点】の「好成績機種の候補」から、実績に応じて2〜3機種を選んで紹介する（候補が1機種なら1機種だけ・候補にない機種は選ばない・無理に3機種にしない）。
  - 機種名・勝率（「N台中M台がプラス、勝率P%」）・平均差枚・総差枚・個別台の好成績（最高の台番と差枚）を自然な文章でつなげる。同じ機種や同じ情報を繰り返さない。
- 空行のあと「💎単品の優秀台」：
  - 【AI文章用の要点】の「💎単品の優秀台の候補」（＝🏆その他の単品優秀台の差枚上位）の機種名と差枚だけを使い、**台番は書かずに**1つの文章にまとめる（箇条書きにしない）。機種名・差枚は候補の表記のまま。
  - 例：「スーパーBJが+8,750枚、ヴァルヴレイヴ2が+8,500枚、無職転生 ~異世界行ったら本気だす~が+7,700枚と単品からも爆発台が多数🌋」。候補が1〜2台ならその台数で自然な文にする。
  - 候補が「（なし）」のときは、この見出しごと書かない。全台系・ハーフ系・並びの台を混ぜない。
- 「🔢並び・末尾などの仕掛け」は、<data> の【仕掛けの判定結果】に該当があるときだけ最後に書く。「該当なし」のときは見出しごと書かない。判定結果にない並び・末尾・列を推測で書かない。
- この文章の後ろには、結果テキストの「🏆全台」〜「🏆その他の単品優秀台」がそのまま付く。その一覧を書き写したり、全機種・全台を並べたりしない。

## 書き方
- 数値の羅列ではなく自然な文章にする。同じ文末を続けない。読みやすく改行する。
- 文末に、内容に合う絵文字を適度に付ける（🎉🔥✨💪 など）。絵文字を連続して並べない・付けすぎない。
- 個別台を並べるとき、G数を書くなら並べる全台に書く。揃えられない場合はG数を書かない。
- ハッシュタグ・URL・宣伝文句は付けない。「激アツ」のような過剰な煽りは書かない（💎単品の優秀台の「爆発台」は可）。
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


# ── 結果テキストの連結部分（🏆全台〜🏆その他の単品優秀台）────────────────
APPEND_START = "🏆全台"
APPEND_STOP = "📝全体データ📝"


def extract_append(report_text: str) -> "tuple[str, str]":
    """結果テキストから「🏆全台」の行〜「📝全体データ📝」の直前（＝🏆その他の単品優秀台の最後の行）を
    そのまま取り出す（行の内容・順番・表記は変えない。前後の空行だけ除く）。
    戻り値：(連結する文字列, エラー文)。見つからなければ ("", 理由)。"""
    lines = (report_text or "").replace("\r\n", "\n").split("\n")
    try:
        i0 = next(i for i, l in enumerate(lines) if l.strip() == APPEND_START)
    except StopIteration:
        return "", "結果テキストに「🏆全台」がありません。"
    i1 = next((i for i, l in enumerate(lines) if i > i0 and l.strip().startswith(APPEND_STOP)), len(lines))
    part = lines[i0:i1]
    while part and not part[-1].strip():
        part.pop()
    return "\n".join(part), ""


def shikake_lines(report_text: str) -> "list[str]":
    """結果テキストの並び・列・末尾・ジャグラー末尾の見出しと中身（既存処理の判定結果）。（なし）の項目は含めない。"""
    lines = (report_text or "").splitlines()
    out: list[str] = []
    cur = None
    buf: list[str] = []
    keys = ("🏆並び", "🏆列", "🏆末尾", "🏆ジャグラーの優秀末尾")

    def _flush():
        if cur and buf and not all(b.strip() in ("（なし）", "(なし)") for b in buf):
            out.append(cur)
            out.extend(buf)

    for l in lines:
        t = l.strip()
        if t.startswith("🏆") or t.startswith(APPEND_STOP):
            _flush()
            cur = t if t.startswith(keys) else None
            buf = []
            continue
        if cur and t:
            buf.append(t)
    _flush()
    return out


_HEADING_RENAME = {"🎯目立った機種": "🏅好成績機種ピックアップ", "🎰目立った機種": "🏅好成績機種ピックアップ",
                   "📊全体の結果・考察": "📊全体の結果"}
_HEADING_MARKS = ("📊", "🏅", "💎", "🔢", "🎯", "🎰", "📉", "✅")
_DATE_LINE_RE = re.compile(r"^\d{1,2}/\d{1,2}\(.\)")


# つなぎ文：文の頭（行頭、または直前の文末記号とその後ろの絵文字は残す）から「〜紹介します」などまで
_BRIDGE_RE = re.compile(
    r"((?:^|[。！!？?])[\U0001F300-\U0001FAFF☀-➿️]*)[^。！!？?\n]*?(?:紹介します|紹介していきます|紹介しましょう|"
    r"ピックアップします|見ていきましょう|見ていきます|チェックしていきましょう|チェックしましょう)[。！!]*\s*"
    r"[👇⬇️⤵️🔽✨🎉🔥💪]*")
_PLUS_SPACE_RE = re.compile(r"[ 　]+(?=[+＋][\d０-９])")


def _ai_sections(lines: "list[str]") -> list:
    """本文を [見出し or None, [行…]] の並びに分ける（見出しは 📊🏅💎🔢 などで始まる行）。"""
    secs = [[None, []]]
    for ln in lines:
        t = ln.strip()
        if t.startswith(_HEADING_MARKS) and not t.startswith("✅"):
            secs.append([t, []])
        else:
            secs[-1][1].append(ln)
    return secs


def tidy_ai_part(text: str, head_lines: "list[str]", singles: "list | None" = None) -> str:
    """生成直後（AI・モック共通）に1回だけ整える（再生成はしない）。手動編集後の文章・⑦では使わない。
    - 冒頭の日付と店名を、結果テキストの1・2行目（head_lines）に置き換えて必ず別の行にし、その下を「✅」だけの3行にする
    - 全角の括弧（）を半角 () に（店名の【】はそのまま）・数値の「+」の直前の空白を詰める
    - 旧見出し（🎯目立った機種・📊全体の結果・考察）を新しい見出しへ、「📉…」の項目（マイナスの紹介）は丸ごと除く
    - 📊全体の結果から、次の見出しへつなぐだけの文（「〜を紹介します👇」など）を除く
    - singles（🏆その他の単品優秀台の上位・single_candidates）を渡すと、💎単品の優秀台を実データから
      台番なしの1文で作り直す（候補が無ければ見出しごと除く・AIが書いていなければ🏅の後ろに入れる）"""
    lines = (text or "").replace("\r\n", "\n").replace("（", "(").replace("）", ")").split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and _DATE_LINE_RE.match(lines[0].strip()):
        first = lines.pop(0)
        if "【" not in first and lines and lines[0].strip().startswith("【") and lines[0].strip().endswith("】"):
            lines.pop(0)
    elif lines and lines[0].strip().startswith("【") and lines[0].strip().endswith("】"):
        lines.pop(0)
    # 冒頭の✅の行（文章付きでも）と間の空行を除く（あとで「✅」だけの3行を入れる）
    while lines and (not lines[0].strip() or lines[0].strip().startswith("✅")):
        lines.pop(0)
    out, skip = [], False
    for ln in lines:
        t = ln.strip()
        if t.startswith(_HEADING_MARKS) and not t.startswith("✅"):
            skip = t.startswith("📉")
            for old, new in _HEADING_RENAME.items():
                if t.startswith(old):
                    ln = new
        if skip:
            continue
        out.append(ln)
    out = [_PLUS_SPACE_RE.sub("", ln) for ln in out]
    secs = _ai_sections(out)
    for sec in secs:
        if sec[0] and sec[0].startswith("📊"):
            kept = []
            for ln in sec[1]:
                t = _BRIDGE_RE.sub(r"\1", ln).rstrip()
                if t.strip() or not ln.strip():
                    kept.append(t)
            sec[1] = kept
    if singles is not None:
        sent = single_sentence(singles)
        idx = next((i for i, s_ in enumerate(secs) if s_[0] and s_[0].startswith("💎")), None)
        if not sent:
            if idx is not None:
                secs.pop(idx)
        elif idx is not None:
            secs[idx] = ["💎単品の優秀台", [sent]]
        else:
            pos = next((i + 1 for i, s_ in enumerate(secs) if s_[0] and s_[0].startswith("🏅")), None)
            if pos is None:
                pos = next((i + 1 for i, s_ in enumerate(secs) if s_[0] and s_[0].startswith("📊")), len(secs))
            secs.insert(pos, ["💎単品の優秀台", [sent]])
    blocks = []
    for h, ls in secs:
        b = "\n".join(([h] if h else []) + ls).strip()
        if b:
            blocks.append(b)
    body = re.sub(r"\n{3,}", "\n\n", "\n\n".join(blocks)).strip()
    head = [h for h in (head_lines or []) if h.strip()][:2]
    return "\n".join(head + ["✅", "✅", "✅"] + (["", body] if body else []))


NEGATIVE_WORDS = ("厳しい", "厳しかった", "厳しめ", "苦戦", "不調", "マイナスの中", "振るわ", "低調", "凹み", "📉")
_NEG_NUM_RE = re.compile(r"[\-−－][\d,]+枚")


def negative_notes(ai_part: str) -> "list[str]":
    """プラス中心の方針に合わない表現（否定的な語・マイナスの差枚）。注意表示だけ（文章は書き換えない）。"""
    out = []
    for w in NEGATIVE_WORDS:
        if w in (ai_part or ""):
            out.append(f"「{w}」")
    for m in _NEG_NUM_RE.finditer(ai_part or ""):
        if f"「{m.group(0)}」" not in out:
            out.append(f"「{m.group(0)}」")
    return out


def compose_full(ai_part: str, append: str) -> str:
    """AI文章の後ろに空行1行を空けて結果テキストの連結部分を付ける。"""
    a = (ai_part or "").rstrip()
    return (a + "\n\n" + append) if append else a


# ── モック（APIを呼ばない）───────────────────────────────────────────
_MOCK_OPENERS = ("📊結果分析", "🔍本日の傾向", "📝データまとめ", "✨ハイライト")


def mock_generate(data_text: str, variant: int = 0, model: str = DEFAULT_MODEL,
                  style: str = DEFAULT_STYLE) -> AIResult:
    """AI用データの【AI文章用の要点】の行だけを使って、新しい構成の文章を決定的に作るモック（数値は入力の表記のまま）。"""
    err = check_input(data_text)
    if err:
        return AIResult(ok=False, error=err, model=model, mock=True)
    style = style if style in STYLES else DEFAULT_STYLE
    sec = _sections(data_text)
    kv, cands, singles, mode = {}, [], [], None
    for ln in sec.get("AI文章用の要点", []):
        if ln.startswith("好成績機種の候補"):
            mode = "c"
            continue
        if ln.startswith("💎単品の優秀台の候補"):
            mode = "s"
            continue
        if mode and ln.startswith("- "):
            if ln[2:] != "（なし）":
                (cands if mode == "c" else singles).append(ln[2:].split("｜"))
            continue
        if "：" in ln:
            k, v = ln.split("：", 1)
            kv[k] = v
    emo = ("🎉", "🔥", "✨", "💪")
    e = lambda i: emo[(variant + i) % len(emo)]
    cnt = {int(a.replace(",", "")): int(b) for a, b in re.findall(r"\+([\d,]+)枚以上 (\d+)台", kv.get("プラス台の実績", ""))}
    mt = re.search(r"総差枚 ([+\-][\d,]+枚)／平均差枚 ([+\-][\d,]+枚)", kv.get("全体の総差枚・平均差枚", ""))
    show_total = kv.get("全体の総差枚・平均差枚", "").startswith("書く") and mt
    mw = re.search(r"（(.+)）", kv.get("勝率", ""))
    show_win = kv.get("勝率", "").startswith("書いてよい") and mw
    big = [(t, cnt.get(t, 0)) for t in (10000, 5000) if cnt.get(t, 0)] or \
          [(t, cnt.get(t, 0)) for t in (3000, 1000) if cnt.get(t, 0)][:1]
    body = [kv.get("日付行", ""), kv.get("店名行", ""), "✅", "✅", "✅", "", "📊全体の結果"]
    s1 = ""
    if show_total:
        s1 += f"総差枚{mt.group(1)}・平均差枚{mt.group(2)}を記録しました{e(0)}"
    if big:
        s1 += "、".join(f"+{t:,}枚以上が{c}台" for t, c in big) + "と、プラス台が多数出ています！" + ("" if show_total else e(0))
    if show_win:
        s1 += f"{mw.group(1)}でした。"
    body += [s1 or "プラスの台が出ています！"]
    k = 2 if style == "short" else 3
    if cands:
        body += ["", "🏅好成績機種ピックアップ"]
        for i, c in enumerate(cands[:k]):
            name, kind, wtxt, avg_t, tot_t, best = c[:6]
            mb = re.match(r"最高 (\d+番台) ([+\-][\d,]+枚)", best)
            pre = "全台系の" if kind == "全台系" else ""
            tail = f"で、{mb.group(1)}が{mb.group(2)}を記録しました！{e(i + 1)}" if mb else f"でした！{e(i + 1)}"
            body.append(f"{pre}{name}は{wtxt}。{avg_t.replace(' ', '')}・{tot_t.replace(' ', '')}{tail}")
    if singles:
        body += ["", "💎単品の優秀台", single_sentence([(0, b[1], b[2]) for b in singles])]
    shk = [ln for ln in sec.get("仕掛けの判定結果", []) if ln != "該当なし"]
    if shk:
        body += ["", "🔢並び・末尾などの仕掛け"] + [f"・{ln}" for ln in shk[:{"short": 2, "standard": 4, "detail": 8}[style]]]
    return AIResult(ok=True, text="\n".join(body).strip(), model=model, mock=True, stop_reason="mock")


_SECTION_KEYS = ("基本情報", "店舗全体", "設置台数別", "ジャグラー全体", "機種別集計", "1台設置",
                 "差枚上位", "差枚下位", "AI文章用の要点", "仕掛けの判定結果", "既存の集計結果")


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
