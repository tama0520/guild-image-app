"""スロバース用：⑧で完成した結果テキスト（report_text）から AI で投稿文を作る。

- Streamlit に依存しない処理だけを置く（画面は streamlit_app.py の _slv_ai_section）。
- 送るのは report_text だけ。APIキーは呼び出し側が get_secret_value() で取得して渡す。
  キーの値はこのモジュールで表示・ログ出力しない（例外メッセージにも含めない）。
- 既定は実API（ボタンを押したときだけ）。SLV_AI_MODE = "mock" にすると API を呼ばない見本になる。
- 実APIは 1回押す＝1リクエスト：SDKの自動再試行 0回・fallbacks なし・自動再生成なし。
- anthropic は実APIを呼ぶときだけ import する（モックでは不要）。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# ── 設定（secrets.toml / .env の同名キーで上書きできる）──────────────────
# モデルID・料金は公式 Models overview（2026-11-10 確認）の値。
AI_MODELS: "dict[str, dict]" = {
    "claude-sonnet-5-5": {"label": "Claude Sonnet 5.5（標準）", "in": 2.00, "out": 10.00},
    "claude-opus-5-5":   {"label": "Claude Opus 5.5（高品質・高め）", "in": 4.00, "out": 20.00},
    "claude-haiku-5-5":  {"label": "Claude Haiku 5.5（安価・簡易）", "in": 0.10, "out": 0.50},
}
DEFAULT_MODEL = "claude-sonnet-5-5"

# 文章スタイル（画面で切り替え・既定は短文）。chars は全角の目安。
STYLES: "dict[str, dict]" = {
    "short":    {"label": "短文", "chars": 120, "picks": "注目は2つまで"},
    "standard": {"label": "標準", "chars": 180, "picks": "注目は3つ程度"},
    "detail":   {"label": "詳細", "chars": 300, "picks": "注目は4〜5つ程度。末尾や全体データにも触れてよい"},
}
DEFAULT_STYLE = "short"

DEFAULT_MODE = "api"           # "api"＝実API（ボタンを押したときだけ） / "mock"＝APIを呼ばない見本（SLV_AI_MODE=mock）
DEFAULT_MAX_TOKENS = 4000      # 1回の出力上限（思考を含む）
DEFAULT_MAX_CALLS = 10         # 1セッション（ブラウザ1つ）あたりの実API呼び出し上限
DEFAULT_EFFORT = "low"         # 文章のまとめ直し程度なので low（必要なら設定で上げる）
MAX_INPUT_CHARS = 30000        # これを超える結果テキストは送らない（切り詰めもしない）
SDK_MAX_RETRIES = 0            # SDKの自動再試行（429/5xx/接続エラーでも再送しない）
REQUEST_TIMEOUT_SEC = 60.0
EFFORTS = ("low", "medium", "high")

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


# ── プロンプト ────────────────────────────────────────────────────────
SYSTEM_PROMPT = """あなたは、パチスロ店の営業結果を X（旧Twitter）へ投稿する文章を書く担当です（スロバースの投稿）。
入力の <result_text> は、店舗のデータから集計済みの「結果テキスト」です。これを読み、投稿文を1つ書いてください。

## 事実の扱い（最優先）
- 台番・機種名・差枚・台数（N/M台）・平均差枚・勝率・総差枚・日付・店名は、<result_text> に書かれているものだけを使う。
- 台数は「(5/5台)」のように、<result_text> の括弧を含めた表記をできるだけそのまま使う。
- 数値は <result_text> の表記をそのまま写す（+や,の付け方も同じ）。足し算・数え上げ（「◯機種」「◯台」）・平均・順位付けなどの再計算、四捨五入、言い換えた数値（「約1万枚」「1万枚超え」など）は書かない。
- <result_text> に無い台番・機種名・数値・出来事（設定・イベント・来店・取材など）は書かない。設定についての推測や示唆（「高設定」「設定6」「全台6」など）もしない。
- 紹介しきれない項目は省いてよい。書く項目は必ず <result_text> と一致させる。

## 構成
1. 1行目：日付と店名（<result_text> の1・2行目の表記どおり。例「11/04(水) 【店名】」）
2. 結果全体の特徴を、数値を使わずに短くひと言で（例：全台系・ハーフ系・単品のどこが目立ったか）。
3. 目立つ機種・優秀台を優先して紹介する（{picks}）。全台系や平均差枚の高い機種、差枚の大きい単品台を優先。
4. （余裕があれば）全体データを1行で。

## 書き方
- 長さ：全角 {chars} 字程度まで（改行・絵文字を含めて、この長さを超えない）。
- 同じ文末（「〜でした」など）を続けない。数値だけを並べた行にしない。自然な文章にする。
- 読みやすく改行し、絵文字は適度に（{chars} 字なら 2〜4 個程度）。
- ハッシュタグ・URL・宣伝文句は付けない。「爆発」「確定」「激アツ」のような過剰な煽りは書かない。

## 出力
- 投稿本文だけを出力する。前置き・説明・見出し・コードブロックは付けない。"""

USER_TEMPLATE = "<result_text>\n{report_text}\n</result_text>"


def build_system_prompt(style: str) -> str:
    st_ = STYLES.get(style, STYLES[DEFAULT_STYLE])
    return SYSTEM_PROMPT.replace("{chars}", str(st_["chars"])).replace("{picks}", st_["picks"])


def build_request(report_text: str, settings: dict) -> dict:
    """messages.create に渡す引数（APIキーを含まない・fallbacks/betas なし）。"""
    return {
        "model": settings["model"],
        "max_tokens": int(settings["max_tokens"]),
        "system": build_system_prompt(settings["style"]),
        "messages": [{"role": "user", "content": USER_TEMPLATE.format(report_text=report_text)}],
        "output_config": {"effort": settings["effort"]},
    }


# ── X の文字数（twitter-text v3 の重み付け）──────────────────────────
# 重み1：U+0000–10FF・U+2000–200D・U+2010–201F・U+2032–2037。それ以外（全角・記号・矢印など）は重み2。
# 絵文字（ZWJ・異体字セレクタ・肌色・キーキャップの組み合わせを1つ）は重み2。URLは23。上限は280。
X_MAX_WEIGHT = 280
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
    """X の投稿文字数（重み付き）。日本語1字＝2、半角英数＝1、絵文字＝2、URL＝23。上限280。"""
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
    """文字数の表示用。chars＝見た目の字数、weight＝Xの重み付き数、zen＝全角換算（weight/2）。"""
    w = x_weighted_length(text)
    return {"chars": len(text or ""), "weight": w, "zen": w / 2, "max": X_MAX_WEIGHT, "over": w > X_MAX_WEIGHT}


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


def check_input(report_text: str) -> str:
    """送信前チェック。問題があれば日本語のエラー文、なければ ""。"""
    if not (report_text or "").strip():
        return "結果テキストが空のため生成できません。⑧を実行してから押してください。"
    if len(report_text) > MAX_INPUT_CHARS:
        return (f"結果テキストが長すぎます（{len(report_text):,}字・上限{MAX_INPUT_CHARS:,}字）。"
                "切り詰めずに送らないため、生成を中止しました。")
    return ""


# ── モック（APIを呼ばない）───────────────────────────────────────────
_MOCK_OPENERS = ("📣結果まとめ", "📊本日の注目", "🔥ピックアップ", "✨結果ハイライト")
_MOCK_PICKS = {"short": 2, "standard": 3, "detail": 5}


def mock_generate(report_text: str, variant: int = 0, model: str = DEFAULT_MODEL,
                  style: str = DEFAULT_STYLE) -> AIResult:
    """結果テキストから行を拾って並べるだけの決定的なモック。数値は入力の行をそのまま使う。
    スタイルで拾う行数を変える（短文2・標準3・詳細5＋全体データ）。"""
    err = check_input(report_text)
    if err:
        return AIResult(ok=False, error=err, model=model, mock=True)
    style = style if style in STYLES else DEFAULT_STYLE
    lines = [ln.rstrip() for ln in report_text.splitlines()]
    head = " ".join([ln for ln in lines[:3] if ln.strip()][:2])
    picks: list[str] = []
    cur = ""
    total = []
    for idx, ln in enumerate(lines):
        s = ln.strip()
        if s.startswith("📝"):
            total = [x.strip() for x in lines[idx + 1:idx + 3] if x.strip()]
            break
        if s.startswith("🏆"):
            cur = s.replace("🏆", "")
            continue
        if cur and s and s not in ("（なし）", "(なし)"):
            picks.append(f"・{cur}：{s.lstrip('💎')}")
    n = len(picks)
    k = min(_MOCK_PICKS[style], n)
    start = (variant * k) % n if n else 0
    chosen = [picks[(start + i) % n] for i in range(k)]
    body = [head, f"【モック#{variant + 1}・{STYLES[style]['label']}】{_MOCK_OPENERS[variant % len(_MOCK_OPENERS)]}"] + chosen
    if style == "detail" and total:
        body.append("📝" + "／".join(total))
    return AIResult(ok=True, text="\n".join(body).strip(), model=model, mock=True, stop_reason="mock")


# ── 実API ────────────────────────────────────────────────────────────
def make_client(api_key: str):
    """自動再試行なしのクライアント（1回押す＝1リクエスト）。"""
    import anthropic
    return anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SEC, max_retries=SDK_MAX_RETRIES)


def api_generate(report_text: str, settings: dict, api_key: "str | None", client=None) -> AIResult:
    """Claude API で1回だけ生成する。client を渡すとそれを使う（テスト用・通信なし）。"""
    model = settings["model"]
    err = check_input(report_text)
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

    req = build_request(report_text, settings)
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


# ── 捏造チェック（AIの文章にだけ現れる台番・数値を洗い出す）─────────────
_TRANS = str.maketrans({"＋": "+", "－": "-", "−": "-", "，": ",", "（": "(", "）": ")", "／": "/"})
_PATTERNS = (
    re.compile(r"\d{2,5}番台"),
    re.compile(r"[+\-]\d[\d,]*"),
    re.compile(r"\(\d+/\d+台\)"),
    re.compile(r"\d[\d,]*枚"),
    re.compile(r"\d+機種"),
    re.compile(r"\d+台"),
)


def _norm(s: str) -> str:
    return (s or "").translate(_TRANS)


def unverified_tokens(ai_text: str, report_text: str) -> list[str]:
    """AI文章の台番・差枚・台数のうち、結果テキストに同じ表記が無いもの（重複なし・出現順）。"""
    src = _norm(report_text)
    src_nc = src.replace(",", "")
    out: list[str] = []
    for pat in _PATTERNS:
        for m in pat.finditer(_norm(ai_text)):
            tok = m.group(0)
            if tok in src or tok.replace(",", "") in src_nc:
                continue
            if tok not in out:
                out.append(tok)
    return out
