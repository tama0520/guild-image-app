# Pision Cloud実装メモ

> 本ドキュメントは、Pision機種一覧・台別詳細表示の Streamlit Cloud 対応に関する
> 調査・検証結果と実装方針をまとめた設計資料です。将来の実装者・Claude Code 向け。
> 記載内容は **現時点の Streamlit Cloud 環境・本プロジェクト構成で確認した結果** です。

## 背景

- 以前、Streamlit Cloud 本番で `Failed to execute 'removeChild' on 'Node': NotFoundError`
  が断続的に発生し、画面の白化（クラッシュ）を起こしていた。
- この対策として、Pision の機種一覧・台別詳細表を `components.html`（iframe）から
  ネイティブ部品（st.dataframe / st.markdown 等）へ順次置き換えていた経緯がある。
- しかし iframe 版（状態0）の方が見た目・操作性の完成度が高く、これを Cloud でも
  安全に使えるか再検証することになった。

## 今回の調査結果

Git 履歴（removeChild 対策コミット）から、真因は **Pision の iframe 自体ではなかった**
ことが判明した。

- **removeChild の真因は「Streamlit 本体（親）DOM を操作する別系統の components.html」**：
  - `ea24749` — 全ページ共通の**不可視 components.html（popstate / autocomplete 監視）**。
    `MutationObserver` で **Streamlit の DOM ツリーを監視・改変**していた。React の再描画で
    消そうとしたノードを、この注入スクリプトが先に移動/削除していたため、React の
    `removeChild` が対象を見つけられず失敗していた。→ 撤去（autocomplete はローカル限定に）。
  - `a699cef` / `77d1932` — **液晶セレクタが expander/columns 内から `st.rerun()` を直呼び**し、
    ネストしたコンテナ内で component の再マウントを強制 → reconciler 不整合。→ on_change
    コールバック方式・selectbox へ変更で解消。
    - **その後 `c21f20f` で、Cloud でもネイティブのサムネ radio へ戻した**（`_IS_CLOUD` 分岐は撤去）。
      危険だったのは `st.rerun()` 直呼びであって radio 自体ではなかったため。現在は
      **Cloud/ローカル共通で「サムネ radio ＋ `on_change` コールバック」**が正式。
      `st.rerun()` 直呼びを再導入しない限りこの構成で問題は出ていない（2026-07-16 時点）。
  - `394ba73` — Pision 表の iframe → 通常テーブル化。これは上記本命対策と**まとめて予防的に**
    行われたもので、Pision iframe 自体が主犯だったわけではない。
- **Pision iframe（`_build_pision_interactive_html`）の JS は親 DOM を操作していなかった**：
  - 使用しているのは `document.querySelectorAll('.mac-row')` / `classList.add|remove` /
    `panel.innerHTML = ...` のみで、**すべて iframe 自身の文書内で完結**。
  - `window.parent` / `parent.document` へのアクセス、`MutationObserver`、明示的な
    `removeChild` / `replaceChild` / `remove` は**いずれも無し**。
- **危険だったのは「iframe × Streamlit の再マウント」の組み合わせ**：
  - 親 DOM を触る不可視 iframe や、ネストコンテナ内 `st.rerun()` による強制再マウントが
    重なると removeChild が誘発されやすかった。

## 今回のCloud検証

- 検証コミット: **af0fbb5**（`test: pision iframe table on cloud`）
- 実装内容: `_render_pision_summary` 内で、Cloud/ローカル両方で状態0の iframe 版
  （`_build_pision_interactive_html`、`summary=None`）を `components.html` で表示。
  総差枚サマリー枠（`_render_pision_summary_box`）は現状維持。

Cloud で確認した操作:

- 表示（機種一覧・台別詳細・総差枚サマリー枠）
- 機種名クリック
- 同じ機種の再クリック（閉じる）
- 別機種クリックでの詳細切り替え
- 日付変更
- 店舗変更
- データ再取得
- ページ移動（他ページ→結果ポスト用へ戻る）
- 画像生成
- ZIP生成

**今回検証した操作範囲では、以下は再現しなかった**（※「今後も絶対安全」という意味ではない）:

- removeChild なし
- NotFoundError なし
- Segmentation fault なし
- 画面の白化なし

## components.htmlを使ってよい条件

以下を **すべて満たす** 場合に限り、比較的安全に使える:

- 親 DOM を触らない（Streamlit 本体の DOM を監視・改変しない）
- iframe 内だけで処理が完結する
- `window.parent` / `parent.document` を使わない
- `MutationObserver` を使わない
- 可視コンポーネントである（height=0 の不可視注入型にしない）
- DOM ツリー上の位置が安定している
- 頻繁な mount / unmount を避ける（条件付きで出し入れしない）
- `st.rerun()` と組み合わせない（特に expander/columns 等ネストコンテナ内からの直呼び）

## 避けるべき実装（危険パターン）

- 親 DOM を**監視/改変**する**不可視 components.html**（autocomplete の MutationObserver 等）
  - ただし「不可視 components.html」自体が危険なのではなく、**親 DOM の監視/改変**が危険。
    親 DOM に一切触れない popstate 登録は該当しない（「ブラウザ履歴対応（正式仕様）」参照）。
- **expander / columns 等ネストコンテナ内から `st.rerun()`** を直呼びする
- 条件分岐で**頻繁に mount / unmount** される、または**ツリー上の位置が動く** iframe
- **同一画面で複数の iframe が同時に再マウント**される構成
- `window.parent.document` 経由で Streamlit の要素を直接操作する処理

## 今後の実装方針

- Pision の機種一覧・台別詳細は **`_build_pision_interactive_html`（iframe 版）を標準実装**とする。
- ネイティブ版 `_render_pision_machine_table`（st.dataframe 行選択）は**定義を残置**し、
  **Cloud で問題が起きた場合のみネイティブ版へ切り替える**保険とする。
  - 切替方法: `_render_pision_summary` 内の `components.html(...)` 呼び出しを
    `_render_pision_machine_table(title, rows, units_df, single_names)` に戻す。
- **新規に components.html を追加する際は、上記「使ってよい条件」を満たしたうえで、
  Cloud 実機で risk 操作（初回取得・再取得・日付/店舗変更・ページ遷移・画像/ZIP生成）を
  一度検証してから本採用する**（今回のプロセスを標準とする）。

## 最後に

- 本ドキュメントの検証結果は、**現時点の Streamlit Cloud 環境・本プロジェクト構成
  （streamlit==1.56.0 / pandas==3.0.2 / numpy==2.4.4 / pillow==12.2.0 / pyarrow==23.0.1）
  で確認した結果**である。
- Streamlit のバージョン更新や環境変更により挙動が変わる可能性があるため、
  「今回検証した操作範囲では問題は再現しなかった」という事実の記録として扱うこと。
- 関連: pyarrow 固定による Cloud Segmentation fault 解消の経緯も本プロジェクトの
  安定化に寄与している（requirements.txt のコメント参照）。

## Pision結果ポスト表示の確定仕様（2026-07-13）

`_render_pision_summary`（結果ポスト用/データビュー/記事用/スランプ生成の4ページ共通）の
表示は以下で確定。今後の前提とする。

- **表示順**: 注意書き → 日付＋店舗名（見出し）→ 総差枚サマリー枠 → 機種別データ表 → 台別詳細。
- **日付＋店舗名の見出し**: ネイティブ `st.markdown(f"#### <span style='font-weight:700'>{title}</span>", unsafe_allow_html=True)`。
  - 理由: h4 既定(600)だと CJK に 600 の字面が無く日本語(店名)だけ細く見えるため、
    span で **font-weight:700** に統一し日付(ASCII)と店名(CJK)を同一サイズ・同一太さにする。
  - iframe 内の重複見出し `<div class="pis-title">` は**削除済み**（見出しは上側1か所のみ）。
- **総差枚サマリー枠**: ネイティブ `_render_pision_summary_box`（`.pis-sum` 2列縦テーブル）。
  iframe には `summary=None` を渡し二重表示しない。
- **機種一覧＋クリック詳細**: iframe 版 `_build_pision_interactive_html`（標準実装）。
- **文字ウェイト**: 大見出し/小見出し(`.pis-sec`)/表ヘッダー(`.pis-tbl th`)/サマリー項目名=600、
  表本文・数値・案内文(`.hint-txt`)=400。
- **iframe 固定高さ**: `_comp_h = max(200, min(585, len(rows) * 30 + 120))`。
  - `components.html` は自動高さ調整できず固定 px が必要。旧式(480〜820)は実内容より高く、
    機種別データ表と「台別データ」expander の間に大きな空白が出ていた。
  - 上限 585 は `.pis-wrap{max-height:520px}` ＋ 見出し等（実内容≈570px）に対し約15px の余地を持たせ、
    `.pis-wrap` の下端罫線・角丸が iframe 境界で切れないようにするための値。
  - 台数の多い機種クリック時の詳細は `scrolling=True` の内部スクロールで全表示。
  - 空白/罫線の見え方を再調整する場合は **585 の数値だけ**を微調整する。

## ブラウザ履歴対応（正式仕様）（2026-07-15・31c2dcb）

ブラウザの **戻るボタン / 進むボタン / Alt＋← / マウスの戻る・進むボタン** でページ遷移
できることを**正式仕様**とする。この挙動を壊さないこと。

- **実装コミット**: `31c2dcbedaac7c5ea4aa4f738be95454028825da`（短縮 `31c2dcb`）
- 変更ファイルは `streamlit_app.py` のみ（`main()` 内の既存 components.html 1 箇所）。
  `_navigate()` / `_sync_from_query_params()` / 各ページの遷移処理は**変更していない**。

### 実装方式

`main()` の**既存 components.html 内**で popstate を監視し、URL 変更時に `location.reload()`
を実行、リロード後の再実行で `_sync_from_query_params()` が URL → `session_state` を復元する。

- popstate 処理は**既存 autocomplete 用 components.html に統合**する。
  **新しい components.html は追加しない**（不可視 iframe を増やさない）。
- 既存 autocomplete 側は先頭に `if (p._autocompleteDisabled) return;` の早期 return を持つため、
  **popstate を同一 IIFE に入れてはならない**（2回目以降の注入で popstate 登録がスキップされる）。
  同一 `<script>` 内に**独立した IIFE として並べ**、フラグも
  `_popstateAttached` / `_autocompleteDisabled` に**分離**する。

### popstate 処理で行ってよい処理（これのみ）

- `window.parent` への popstate 登録
- 二重登録防止フラグ
- `location.reload()`

### popstate 処理で行ってはならない処理

- 親 DOM 操作 / `removeChild` / `MutationObserver` / Streamlit 内部 DOM 操作
- iframe 外の DOM 書き換え、クリックイベントの疑似発火、Streamlit 内部 DOM の探索

### 経緯（再撤去しないための記録）

- `ea24749` で Cloud の removeChild 対策として popstate と autocomplete の
  components.html を**まとめて撤去**したが、**真因は autocomplete 側の MutationObserver**
  による親 DOM 監視であり、popstate 側は無関係だった。
- popstate を失った結果、`_navigate()` の `st.query_params` 更新は pushState で URL 履歴を
  積むものの、戻る/進むで URL が変わっても Streamlit が再実行されず `session_state.page` が
  古いまま残り、**画面が切り替わらない**（＝履歴が積まれていないように見える）状態になっていた。
- popstate は `addEventListener` と `reload()` のみで親 DOM に触れないため、安全に復活できる。
  **removeChild 対策を理由に popstate を再撤去しないこと。**

### 検証状況（2026-07-15 時点）

- **ローカル**: 確認済み。ブラウザの戻る/進むでの復元、Alt＋←、多段遷移
  （トップ→店舗→画像種類→work / 結果ポスト用）、リロードループなし、記事用ページの
  F5 後の店舗復元、Console エラー 0 件を確認。**戻るは1回で正常**。
- **Streamlit Cloud**: 確認済み。アプリの正常起動・主要ページの表示・戻る操作の動作、
  白画面 / リロードループ / removeChild / NotFoundError が出ないことを確認。
  **ただし戻る（マウスの戻る含む）は2回押す必要がある**
  （下記「既知の未解決問題：Cloudのみ戻る操作が2回必要」参照）。

### 既知の未解決問題：Cloudのみ戻る操作が2回必要（2026-07-15）

**症状**: Streamlit Cloud でのみ、ブラウザの戻るボタン／マウスの戻るボタンを**2回押さないと**
前ページへ戻らない。1回目は URL は戻るが画面が変わらない。それ以外（起動・主要ページの表示・
進む・白画面 / リロードループ / removeChild / NotFoundError）は正常。

#### 確定事項

- **Cloud では戻る操作が2回必要**（Cloud 実機で確認）。
- **ローカルでは1回で正常**（Windows / py 3.14。`_navigate()` 1回につき pushState 1回、
  reload で history.length は増えないことを実測）。
- **Streamlit Issue #9878 は、同種の Community Cloud 限定事象として `status:confirmed`**。
  https://github.com/streamlit/streamlit/issues/9878
  - **2026-07-15 時点で Open**（`type:bug` / `status:confirmed` / `priority:P3` /
    `feature:query-params`）。2024-11-17 起票、2025-06-12 更新。担当者・修正PRなし。
  - 報告者: "It seems like this only affects community cloud? I was unable to reproduce on a
    local instance of streamlit."（**Cloud のみ発生・ローカルでは再現しない**）
  - メンテナ(sfc-gh-bnisco, 2024-11-19)が原因を `App.tsx` の `handlePageInfoChanged` と特定し、
    **"each re-run of this app will (erroneously) push a new state to the browser history"** と説明。
  - **2026-07-15 時点で、develop ブランチでも URL を比較せず無条件に
    `window.history.pushState` する実装が残っている**ことを確認。
- **現時点でアプリ側の公式回避策は確認できていない**（下記「回避策の状況」参照）。
- **診断コミット `4038d3c` で、ローカル・Cloud 両方の履歴操作が壊れた**。
  **`296a39b` で完全 revert 済み**（`streamlit_app.py` は `31c2dcb` 時点とバイト単位で一致）。

#### 推定（確定していない事項）

- 症状から、**同一URLの履歴エントリが1つ余分に積まれている可能性**がある
  （1回目の戻るがその重複を消費し、画面が変わらないと考えると「ちょうど2回」と整合する）。
  関連として `page_info_changed` は `streamlit/runtime/forward_msg_queue.py` の `clear()` で
  **保持対象（lifecycle msg）**であり、再実行をまたいで再送され得る。
- **今回の症状が Issue #9878 と同一原因である可能性が極めて高い**。症状およびローカル／Cloud の
  差が極めてよく一致しているが、**同バグに起因すると断定はできていない**。
  「なぜ Cloud だけか」の Cloud 側の引き金は**公式にも未特定**。`/~/+/` が履歴を追加している事実や、
  Cloud で `location.reload()` が特殊という情報は**確認できなかった**。
- 診断コード(`4038d3c`)が壊れた原因は、**iframe 再生成後に古いクロージャのラッパーが
  親ウィンドウへ残った可能性**。ガード `p.__histDiagWrapped` は親に立つ一方、退避した `origPush` は
  その時の iframe のクロージャにあり、Streamlit が rerun で components.html の iframe を作り直すと
  参照が失われるため。ローカルで 10/10 PASS でも「rerun で iframe が再生成される条件」を
  突けておらず検証不足だった。

#### 回避策の状況

- 現在の `_navigate()`（`st.query_params.from_dict()`）は公式APIの正しい使い方。複数キーで
  履歴が複数積まれる Issue #8347 は **固定中の 1.56.0 で修正済み**（`update()` に
  "to ensure only one one ForwardMsg is sent" とあり ForwardMsg は1通。ローカル実測とも一致）。
- 現在の **popstate → `location.reload()` 方式は必要**。Issue #13963 に
  "single-page apps don't trigger backend reruns for history navigation at all" とあり、
  `pages/` を持たない本アプリでは reload 以外に URL 変更をバックエンドへ伝える手段が公式にない。
- 修正対象は Streamlit 本体のフロントエンド(TypeScript)で、アプリ側の Python からは変更できない。
  関連 PR #9902 は **closed・未マージ**（2025-03-10 ブランチ削除）。
- **現在固定している Streamlit 1.56.0 では未解決。将来のバージョンで修正される可能性があるため、
  更新時に Issue #9878 と実装状況を再確認する。**

**運用**: Cloud では当面、**戻る操作を2回行う暫定運用**とする。

#### 現在の main へ推測修正を入れないこと（禁止事項）

- `history.pushState` / `replaceState` のラップ
- `history.back()` の自動実行 / `history.go(-2)` / 無条件の連続 back
- Cloud だけを対象にした推測修正
- Streamlit 本体のフロントエンドをアプリ側から上書きする処理
- 新しい診断コードの追加
- 原因未確認のまま正式仕様（`31c2dcb`）を変更すること

再調査する場合は **main を直接変更せず、別ブランチまたはローカルの検証環境**で行う。

#### Streamlit 更新時の再確認

streamlit のバージョンを上げる際は、**Issue #9878 の解決状況を必ず再確認**する
（Closed になっていれば本項の暫定運用を解除できる可能性がある）。あわせて
`frontend/app/src/App.tsx` の `handlePageInfoChanged` に
**URL 比較（同一URLなら push しない）**が入ったかを確認する。

### 今後のルール

ブラウザ履歴やページ遷移（`_navigate()` / `_sync_from_query_params()` / `st.query_params` /
各ページの遷移処理）を変更する場合は、**必ず今回の実装との互換性を確認してから**変更する。

## Cloud変更時のチェックリスト

Pision表示や components.html に関係する変更を行った場合は、
main へ反映する前に以下を確認する。

- [ ] Cloud で初回データ取得
- [ ] 機種クリック
- [ ] 同じ機種の再クリック
- [ ] 日付変更
- [ ] 店舗変更
- [ ] データ再取得
- [ ] ページ切り替え
- [ ] 画像生成
- [ ] ZIP生成
- [ ] ブラウザの戻る/進むでページが復元される（トップ→店舗→結果ポスト用の多段で確認）
- [ ] 戻る/進むを繰り返してもリロードループ・白画面が起きない
- [ ] Console に removeChild / NotFoundError が出ない
- [ ] Manage app ログに Segmentation fault が出ない
- [ ] RSS ログに異常増加がない

**上記をすべて通過した場合のみ正式採用とする。**
