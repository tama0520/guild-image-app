# かぶぱページ スマホ時の「自動処理を開始」ボタン制御 — 設計書

作成日: 2026-07-10
対象: `streamlit_app.py`

## 目的

【新宿歌舞伎町】かぶぱポストの結果ページをスマホで使う際、プレビュー前に赤い
「▶▶ 自動処理を開始」ボタンを誤って押してしまう事故を防ぐ。スマホ表示のときだけ
レイアウト/見た目を変え、PC表示や他店舗には一切影響を与えない。

## 適用範囲

- **店舗**: `store == "新宿歌舞伎町"`（かぶぱ）のみ。
- **端末**: スマホ幅（`@media (max-width: 640px)`）のときのみ。PC幅は完全に従来通り。
- 他店舗・PC は変更なし。

## 挙動

| 状態 | PC | スマホ（≤640px） |
|---|---|---|
| プレビュー前（`_auto_previews is None`）・かぶぱ | 従来通り（赤・表示） | 「自動処理を開始」を**非表示**（`display:none`） |
| プレビュー後・かぶぱ | 従来通り（赤 primary） | 表示するが**グレーで控えめ**（primary赤を上書き） |
| 他店舗・全状態 | 変更なし | 変更なし |

## 実装方針

「▶▶ 自動処理を開始」ボタン（`streamlit_app.py:8238` 付近、`key="auto_run"`、
`type="primary"`）の描画直前に、かぶぱのときだけ状態に応じた `<style>` を
`st.markdown(..., unsafe_allow_html=True)` で注入する。

- ボタンを一意に狙うため、ボタンを `st.container()` で囲み、直前に不可視のマーカー
  （例 `<span class="kabupa-run-marker"></span>`）を置き、`.st-key-auto_run` または
  マーカー隣接セレクタで対象ボタンを特定する。Streamlit は `st.button(key=...)` に
  対して `st-key-<key>` クラスを付与するため、`.st-key-auto_run button` で特定可能。
- CSS はメディアクエリで囲むため PC 幅では無効：
  - プレビュー前:
    ```css
    @media (max-width: 640px) {
      .st-key-auto_run { display: none !important; }
    }
    ```
  - プレビュー後:
    ```css
    @media (max-width: 640px) {
      .st-key-auto_run button {
        background: #6c757d !important;   /* グレー */
        border-color: #6c757d !important;
        color: #fff !important;
      }
    }
    ```
- `_auto_previews`（= `st.session_state.get(_aprev_key)`）が None かどうかで
  プレビュー前/後を分岐し、注入する CSS を切り替える。
- `store != "新宿歌舞伎町"` のときは一切注入しない（従来通り）。

## テスト観点

- 構文チェック（`ast.parse`）が通る。
- スマホ幅（DevTools で幅640px以下）でかぶぱを開く:
  - プレビュー前: 「自動処理を開始」が表示されない。
  - プレビュー生成後: 「自動処理を開始」がグレーで表示される。
- PC幅: プレビュー前後とも赤で表示（従来通り）。
- 他店舗: スマホ/PCとも従来通り。
- `.st-key-auto_run` セレクタが実際に対象ボタンに当たること（Streamlitバージョン依存の
  ため実機で確認。当たらない場合はマーカー隣接セレクタにフォールバック）。
