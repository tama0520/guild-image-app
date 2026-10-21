# Cloud・GitHub同期・運用

対象：Cloud↔GitHub同期・store_settings運用・機種画像/機種名変換の同期・packages.txt・未知pageの無限rerun

> このファイルは旧 `CLAUDE.md`（blob `fde5030`・commit `bfb9ad5`）から機械的に切り出した正式仕様の原文です。
> `VERBATIM-BEGIN` 〜 `VERBATIM-END` の間は1文字も変更しないこと（要約・統合・削除も禁止）。
> 新しい正式仕様は、このファイルの末尾（マーカーの外）へ追記してください。
> 完全一致の確認：`py -3.14 tools/verify_claude_split.py`

<!-- VERBATIM-BEGIN id=S00353 src=CLAUDE.md@fde5030 lines=353-390 sha256=483c1d8f6a195fe897a5de35897546dc9abe6a1a0ada2244771ee6e33de8854b -->
## Cloud ↔ GitHub 同期の正式仕様（2026-08-05 確定・`f3ff59c`）

`weekly_items.json` / `rote_machines.json` の Cloud 側同期は以下を**正式仕様**とする。
**巻き戻し禁止。**関連コミット: `f3ff59c`（復旧は `5d16a90`）

### 守るべき5点

1. **Cloud 起動時は GitHub 上の最新 JSON を取得してから動作する**
   （`_github_sync_on_start()`・セッション1回のみ・対象は `_GH_SYNC_FILES`）
2. **保存前に読み込み時 SHA と現在の SHA を比較し、不一致なら絶対に PUT しない**
   （`_github_push_file(..., base_sha=)`）
3. **競合時は最新を取得して保存を中止する。自動マージは禁止**
   メッセージは `他の環境で更新されたため保存を中止しました。最新データを読み込みました。`
4. **409 発生時も古い内容を再送しない**（旧リトライループは廃止済み。再導入禁止）
5. **ローカル（Windows）の既存保存フローは変更しない**
   （`_git_auto_pull()` / `_git_auto_push()` は無変更。分岐は `_IS_CLOUD` のみ）

### なぜ

`_IS_CLOUD = platform.system() != "Windows"`。Cloud 側にはローカルの起動時 `git pull` が無く、
コンテナ内 JSON は**デプロイ時スナップショット**のまま古くなる。旧実装は SHA を競合検出にしか
使わず**全文 PUT** していたため、古い session_state がリモートの新しい内容を丸ごと消した。
2026-08-05 12:15 の `805d63d` が 00:57 の `579fd65`（渋谷新館 8/4 分のチェック）を完全に
巻き戻した事故がこれにあたる。旧 409 リトライは**新しい SHA で古い内容を再送**するため、
競合時にむしろ確実に上書きしていた。

### 実装上の注意

- PUT 成功時は応答の `content.sha` を `_gh_sha_key(repo_path)` へ記録し、次回保存の基準にする
- 取得内容が JSON として壊れている場合は書き戻さない（コンテナ内ファイルを守る）
- `base_sha` が未設定（起動時同期に失敗した等）のときは従来どおり保存する
- 競合で中止した場合、そのセッションの未保存編集は入れ直しが必要。**黙ってマージしない**

### 運用

- 「ローカルで入力 → その後 Cloud のセッションが動く」が事故条件だった。修正後は構造的に発生しない
- Cloud への反映には **Reboot／再デプロイが必要**

<!-- VERBATIM-END id=S00353 -->

<!-- VERBATIM-BEGIN id=S00864 src=CLAUDE.md@fde5030 lines=864-928 sha256=8ef9b02b7f65d7d4f72f332e319136dddbe3e54f4651c325163c4a6eb5dd46b4 -->
## store_settings の正データ源と Cloud 運用ルール（2026-08-10 確定・調査のみ／コード変更なし）

**正式運用ルール。巻き戻し禁止。**⑤オススメ機種ピックアップと高田馬場の記事用⑤バラエティが
保存される `store_settings/{store}.json` の扱いを定める。**今回は同期機能を実装していない。**

### 現状の構造（コードで確認済みの事実）

- **`store_settings` には Cloud → GitHub の同期経路が1本も無い。**
  - `_GH_SYNC_FILES`（2512行）は **`weekly_items.json` / `rote_machines.json` のみ**。
    `store_settings` は含まれない。
  - `save_store_settings()`（4898行）は**ファイル書き込みだけ**で、
    `_github_push_file()` も `_git_auto_push()` も呼ばない。
  - `_git_auto_push()`（2672行）の `targets` には `"store_settings"` が入っているが、
    呼び出し4か所（10793 / 12313 / 14851 / 17153行）はすべて **`if not _IS_CLOUD:`**。
  - `_github_push_file()` の呼び出しは2か所だけ（15179＝ローテ／15376＝週間）。
- **Cloud 上の編集値は Cloud コンテナ内のファイルにだけ存在する。**
  再デプロイ／Reboot でコンテナが作り直されると消える。
- **GitHub 側で `store_settings` が更新されても Cloud は自動で取り込まない。**
  `_github_sync_on_start()`（2567行）は `_GH_SYNC_FILES` しか pull しないため、
  反映は**再デプロイ時のみ**。
- ローカルは `_git_auto_pull()` / `_git_auto_push()` で双方向に通っている
  （ただし push は**画像生成時のみ**。⑤を編集しただけでは push されない）。

### store_settings に入っているもの（全12店舗・実キー22種）

| カテゴリ | キー |
|---|---|
| ⑤オススメ機種ピックアップ（19種） | `rec_enabled` / `recommended_machines_1〜6` / `recommended_title_1〜6` / `recommended_filter_1〜6` |
| 高田馬場 記事用⑤バラエティ（3種） | `art_variety_range` / `art_variety_enabled` / `art_variety_mode` |

画像・Excel・日付単位の入力は含まれない（それらは `auto_page_inputs.json` 側）。

### 正式運用ルール

1. **`store_settings` の正データ源は GitHub とする。**
2. **⑤の設定変更はローカルで行う。** ローカルで変更 → GitHub へ反映 → Cloud は
   GitHub 上の正式設定を使う。
3. **Streamlit Cloud 上では⑤オススメ機種ピックアップの設定を編集しない。**
   Cloud で編集してもコンテナ内にしか保存されず、GitHub／ローカルへは同期されない。
   再デプロイ等で消えるため**正式設定として扱わない**。
4. **高田馬場の記事用⑤バラエティ（`art_variety_*`）も同様に Cloud 上では編集しない。**
5. **2026-08-10 に Cloud の新小岩⑤ブロック5に現れた
   「虚構推理／BIRDIE WING／戦国乙女4／バイオRE:3／ULTRAMAN最終決戦」は正式設定ではない。**
   リポジトリの全JSONにも git 全履歴（`git log -S --all`）にも存在せず、
   **Cloud で入力された Cloud-only 値**である。
   **GitHub HEAD の `store_settings/新小岩.json` を正とし、B5空欄が正式状態。**
   新小岩⑤の正式値は **B1=5 / B2=4 / B3=8 / B4=9 の合計26機種、B5・B6は空**。
6. **双方向同期は今回は実装しない。**将来必要になった場合の別案件とする。
   実装する場合は **「起動時 GitHub→Cloud pull ＋ SHA確認付き Cloud→GitHub push」を必ずセット**で
   設計する。**push だけを追加する実装は禁止**（Cloud の古いコンテナ値が GitHub の新しい設定を
   上書きする事故が確実に起きる）。
7. **将来実装する場合に必ず回帰確認する項目**：
   日本語ファイル名のURLエンコード（現行 `_github_fetch_file` / `_github_push_file` は
   `urllib.parse.quote` を通していない）／SHA競合／409／同一店舗の同時編集／
   起動時の複数GET（12店舗＝12往復）／高田馬場 `art_variety_*` への影響／
   ⑤の `39f1f1e` 正式仕様／②の `0e7dc4c` 正式仕様。

### なぜ同期を実装しないか

`store_settings` に入るのは⑤と記事用バラエティだけで変更頻度が低く、
「ローカルで整えて push → Cloud は再デプロイで受け取る」で運用が成立する。
12ファイル×双方向の同期を足すと、日本語パス・起動時の往復回数・同一店舗の同時編集など
新しい事故クラスが増える。今回の Cloud-only 値は**同期の欠如ではなく
「Cloud で編集した」ことが原因**なので、運用ルールで断つのが最小リスク。

<!-- VERBATIM-END id=S00864 -->

<!-- VERBATIM-BEGIN id=S04049 src=CLAUDE.md@fde5030 lines=4049-4125 sha256=a5ff1aeda4863ffdf05c04955347f4afca4f9685bf8b63769d078cb37a0ca0c0 -->
## 機種画像紐づけ：Cloud反映時の注意（2026-09-01 確定・調査のみ／コード変更なし）

**正式な運用ルール。**「ローカル／GitHub には機種画像紐づけがあるのに Cloud の
🖼️ 機種画像紐づけ 一覧に出ない」ときの切り分け手順を定める。**今回コードは変更していない。**

### ① 何が起きたか（戦国恋姫の実例）

- 戦国恋姫の紐づけと画像は **`45025c9`（2026-09-01 14:55:47・`update machine_image_master`）で
  commit・push 済み**で、当時の main にも現在の main にも含まれていた。
  同 commit の変更は次の**5ファイルだけ**である。

  ```
  masters/machine_image_master.xlsx
  assets/machine_images/sengokukoihime_panel.png
  assets/machine_images/sengokukoihime_01.png
  assets/machine_images/sengokukoihime_02.png
  assets/machine_images/sengokukoihime_03.png
  ```

- それにもかかわらず、**Cloud の一覧には当初表示されなかった**。
- **Cloud を Reboot したところ、`🖼️ 機種画像紐づけ` の一覧に戦国恋姫が正常表示された（実機確認済み）**。

  | 簡略名 | 画像グループID | パネル | 液晶 | 状態 |
  |---|---|---|---|---|
  | 戦国恋姫 | `sengokukoihime` | **あり** | **3枚** | **OK** |

- **原因は「未push」ではない。**必要ファイルはすでに push 済みで、
  **Cloud 側が古い状態を保持していたため表示されず、Reboot で最新 main を取り込んで正常反映した**。
  **今後この事象を「未push」と記録しないこと。**

### ② 構造（コードで確認済みの事実）

- 紐づけマスタ：**`masters/machine_image_master.xlsx`**（列 `簡略名` / `画像グループID`）
- 画像：**`assets/machine_images/{画像グループID}_panel.*` / `{画像グループID}_01.*` …**
- 定数：`_MACHINE_IMAGE_MASTER_PATH` / `_MACHINE_IMAGES_DIR`（ともに **`BASE_DIR` 配下＝リポジトリ内**）
- 読み出し：`load_machine_image_master()` → `get_machine_images(簡略名)` →
  `_find_panel_image()` / `_find_screen_images()` → `show_machine_image_page()` が表示
- 外部ストレージ・Secrets・別APIは使わない。**リポジトリ内の実ファイルを直接読む**ため、
  **main へ push したうえで Cloud が新しいコミットを取り込めば反映される**。

### ③ 同じ事象が起きたときの手順（むやみに再登録・再commitしない）

1. **`origin/main` にマスタと画像が存在するか**を先に確認する。
   ```
   git ls-tree -r --name-only origin/main assets/machine_images | Select-String "{画像グループID}"
   git ls-tree -r --name-only origin/main masters
   git log --oneline -- assets/machine_images/{画像グループID}_panel.png
   git merge-base --is-ancestor <その commit> origin/main
   ```
   併せて `git status --porcelain --ignored -- masters assets` が空（未追跡・変更なし）かを見る。
2. **Cloud が最新 main を取り込んでいるか**を確認する。
3. **必要なら Cloud を Reboot する**（Manage app → Reboot）。
   push だけでは反映されないことがある（「⑪ Cloud 実機確認と403の原因」の節と同じ現象）。
4. 1〜3で解決する場合、**画像の再登録・再commit・再pushは不要**。

### ④ ローカルで出ないときは「古いプロセス」を疑う

**`load_machine_image_master()` は `@st.cache_data`（引数なし）**で、
**プロセス生存中はマスタファイルの更新を検知しない**。
そのため、マスタを更新した時刻より**前に起動していた Streamlit セッション**では
新しい紐づけが出ないことがある。
（`append_machine_image_master()` / 紐づけ追加の経路は `load_machine_image_master.clear()` を
呼ぶので、**同じプロセス内で登録した場合は反映される**。）

→ **ローカルで出ないときは、まず Streamlit を再起動して再確認する。**
再登録やマスタの直接編集を先に行わない。

### ⑤ 今回いっさい変更していないもの

`masters/machine_image_master.xlsx` ／ `assets/machine_images/` の画像 ／ `機種名変換.xlsx` ／
`streamlit_app.py` の機種画像関連コード。**戦国恋姫のための追加 commit / push も不要**である
（必要ファイルはすべて `45025c9` で main に入っている）。

なお `機種名変換.xlsx` には**戦国恋姫とは無関係の未コミット差分**（HEAD 1067行 → 現在 1074行・
`Lストファイ6` / `Lリゼロ2` / `L喰霊-零-Re` / `Lうしおととら 白面決戦` / `エウレカ4` 系の**+7行**）が
存在する。**恋姫の行はHEADと現在で同一（3件）**であり、今回の件と混同しないこと。

<!-- VERBATIM-END id=S04049 -->

<!-- VERBATIM-BEGIN id=S04126 src=CLAUDE.md@fde5030 lines=4126-4397 sha256=c7700e6a1a376407e0a0f0c82cff74adddd78aa344c3bba8e1970b4aa86f2db4 -->
## 機種名変換：保存時GitHub自動同期（2026-09-01 確定・`fae637e` / `bde3afb`）

**正式仕様。巻き戻し禁止。**対象は**機種名変換ページの保存経路と `機種名変換.xlsx` の1ファイルだけ**。

| 項目 | 値 |
|---|---|
| **正式基準 HEAD** | **`bde3afb`**（= origin/main） |
| `fae637e` | `update: 機種名変換マスタを更新` — **`機種名変換.xlsx` 1ファイルだけ**をcommit / push。未反映だった9行を main へ正式反映 |
| `bde3afb` | `feat: 機種名変換の保存時にGitHubへ自動同期` — **`streamlit_app.py` のみ** |

### ① 今回の発端（原因を誤認しないこと）

西武新宿の機種名変換で

```
Lバイオハザード ヴィレッジ        → バイオヴィレッジ
スマスロ バイオハザード ヴィレッジ → バイオヴィレッジ
```

をローカルで追加したのに、**Cloud では未登録**だった。
調査の結果、**ローカルの `機種名変換.xlsx` には存在するが `origin/main` には存在しない**状態だった。

未commit差分はバイオヴィレッジ2行だけではなく、**次の9行**だった。

| # | 変換前 | 変換後 |
|---|---|---|
| 1 | `Lストファイ6` | スト6 |
| 2 | `Lリゼロ2` | Re：ゼロ2 |
| 3 | `Lパチスロ 喰霊-零-Re` | 喰霊零Re |
| 4 | `L喰霊-零-Re` | 喰霊零Re |
| 5 | `Lうしおととら 白面決戦` | うしおととら |
| 6 | `スマスロ交響詩篇エウレカセブン4 HI-EVOLUTION` | エウレカ4 |
| 7 | `L交響詩篇エウレカセブン4` | エウレカ4 |
| 8 | `Lバイオハザード ヴィレッジ` | バイオヴィレッジ |
| 9 | `スマスロ バイオハザード ヴィレッジ` | バイオヴィレッジ |

この9行は **`fae637e` で `機種名変換.xlsx` 1ファイルだけをcommit / push**し、`origin/main` へ正式反映済み。

**この事象の原因を「Cloud Reboot不足」と誤認しないこと。**
今回の直接原因は
**「ローカルの `機種名変換.xlsx` だけが更新され、GitHub main へ同期されていなかった」**ことである。

### ② Reboot だけでは直らないケース（戦国恋姫と区別する）

**`origin/main` に変換行自体が存在しない場合、Cloud Reboot だけでは絶対に直らない。**
先に `機種名変換.xlsx` を GitHub main へ反映する必要がある。

| 事象 | 状態 | 対処 |
|---|---|---|
| 戦国恋姫の機種画像紐づけ | 必要ファイルは **push済み**、Cloud が古かった | **Cloud Reboot で解決** |
| **今回の機種名変換** | 必要な変換行が **`origin/main` に存在しなかった** | **Reboot だけでは解決しない**（先に main へ反映） |

### ③ `bde3afb` 以前の保存仕様

機種名変換画面の保存経路は3つあったが、いずれも

```
機種名変換.xlsx をローカル保存 → load_name_map.clear() → st.rerun()
```

**だけ**で、`git add` / `commit` / `push` は**一切行っていなかった**。
そのため「ローカルで保存したが手動pushを忘れる」と **Cloud では未登録のまま**になる構造だった。

### ④ 機種画像紐づけとの違い（誤認しないこと）

既存の **`_sync_machine_image_master()` は機種画像紐づけ専用**である。

- 対象：**`masters/machine_image_master.xlsx`** / **`assets/machine_images`**
- **`機種名変換.xlsx` は対象外**だった。

**「以前同期機能を作ったから機種名変換にも効いている」と誤認しないこと。**

### ⑤ `bde3afb` の正式仕様

機種名変換画面の**保存成功後**に **`_sync_name_map()`** を使い、
**`機種名変換.xlsx` だけ**を GitHub main へ自動同期する。

- **対象ファイルは必ず `機種名変換.xlsx` の1ファイルだけ。**
- **`_git_auto_push()` の targets へは追加していない。**
  **画像生成時に `機種名変換.xlsx` を巻き込む仕様ではない。**

### ⑥ 対象となる3保存経路（一部だけ同期する状態へ戻さない）

| # | タブ | ボタン |
|---|---|---|
| ① | 📋マスタ管理 | `💾 マスタを保存` |
| ② | 🔄変換実行 | `📝 N件をマスタに追加` |
| ③ | 🔍pisionチェック | `📝 N件をマスタに追加` |

**正式順序：保存 → `load_name_map.clear()` → `_sync_name_map_ui(...)` → `st.rerun()`**

### ⑦ ローカル同期の正式判定順（最重要）

```
git fetch origin main
  ↓
behind 判定
  ↓
ahead 判定
  ↓
機種名変換.xlsx の差分判定
  ↓
add（1ファイル）
  ↓
パス限定 commit
  ↓
push
```

**差分判定より先に ahead / behind を確認することが正式仕様。**

### ⑧ `behind > 0`（GitHub側が進んでいる）

自動同期を**停止**する。
**`pull` / `merge` / `rebase` / `reset` / `force push` / `autostash` を自動実行してはならない。**
UI には

```
GitHub側に新しいcommitがあります。自動でmerge/rebaseは行いません。手動で確認してください
```

と分かる形で通知する。

### ⑨ `ahead > 0`（未pushのローカルcommitがある）

ローカル HEAD に**未pushのcommitが1件でも存在する場合は自動同期を停止**する。
**そのcommitが機種名変換由来か別案件由来かは問わない。自動push禁止。**

理由：**`git push origin main` はブランチ単位**であり、**別件の未pushcommitまで一緒に反映する危険**があるため。
**「機種名変換のcommitだから自動pushしてよい」という判定は禁止。**
このとき**新しいcommitも作らない**（未pushcommitの積み上がりも防ぐ）。

### ⑩ 正常状態（`ahead == 0` かつ `behind == 0`）

このときだけ `機種名変換.xlsx` の差分を確認する。

| 差分 | 挙動 |
|---|---|
| なし | **`変更なし（同期不要）`**。**commitなし・pushなし** |
| あり | `機種名変換.xlsx` だけを stage → `機種名変換.xlsx` だけを commit → push |

### ⑪ stage / commit の安全条件

自動同期で使用してよいのは **`git add -- 機種名変換.xlsx`** だけ。

- **禁止：`git add .` / `git add -A` / `git commit -a`**
- **commit も pathspec 限定**（`git commit -m ... -- 機種名変換.xlsx`）
- **すでに別ファイルが stage されていても、機種名変換の commit へ含めない。**
- **既存 stage を勝手に解除することも禁止。**

### ⑫ push 拒否時

- **ローカル保存と commit は残す。**
- **rollback しない / reset しない / force push しない。**
- UI には
  **「ローカル保存とcommitは完了したが、GitHubへのpushは未完了」**と明確に表示する。

### ⑬ push拒否後の重要な欠陥と修正（順序を巻き戻さない）

`bde3afb` 実装途中に発見して修正した欠陥。

**旧案の問題**

```
push拒否 → ローカルcommitだけ残る → ワークツリーはclean
        → 次回同期で「変更なし（同期不要）」と誤判定
```

さらにその後保存すると、**未pushcommitが 1件 → 2件 と積み上がる**問題もあった。

**正式修正**：差分確認より**先**に

```
ahead = git rev-list --count origin/main..HEAD
```

を確認し、**`ahead > 0` なら即停止**する。
そのため push 拒否後の次回同期は

```
未pushcommitがあります。安全のため自動同期を停止します
```

となり、**`変更なし（同期不要）` とは絶対に表示しない。**
**この判定順を巻き戻してはならない。**

### ⑭ 分岐状態（`ahead > 0` かつ `behind > 0`）

**自動解決禁止。**分岐状態として停止する。**merge / rebase 等を勝手に行わない。**

### ⑮ Cloud 側

Cloud では **Git コマンドを使用せず、GitHub Contents API 経路**を使う。安全条件：

- **`GITHUB_TOKEN` 必須**
- **現在 SHA を取得**
- **読み込み時 SHA と現在 SHA が不一致なら PUT しない**
- **409 は再送しない**
- **競合は自動解決しない**

**既存の安全仕様（`f3ff59c` の思想）を弱めないこと。**

### ⑯ Cloud Reboot

**GitHub main への自動同期成功と、Streamlit Cloud のコンテナ反映は別問題である。**
**自動同期処理から Cloud Reboot は実行しない。**
同期成功後に Cloud で変換が見えない場合は Reboot を確認する。

### ⑰ 実機確認結果（2026-09-01・ローカル・正式HEAD `bde3afb`）

**西武新宿 / 2026/08/31 確定データ**

```
登録済み: 75 件 ／ 未登録: 0 件
Lバイオハザード ヴィレッジ → バイオヴィレッジ   ← 画面で確認
```

`load_name_map()` でも次の3表記すべてが **`バイオヴィレッジ`** へ変換されることを確認済み。

```
Lバイオハザード ヴィレッジ
スマスロ バイオハザード ヴィレッジ
バイオハザード ヴィレッジ
```

### ⑱ 差分なし同期の実測（本番リポジトリ）

差分なし状態で `_sync_name_map()` を実行した実測結果：

```
戻り値: (True, "変更なし（同期不要）")
HEAD 不変 / origin/main 不変 / git status 不変 / 機種名変換.xlsx 不変
stage 空 / 新commitなし / pushなし
```

**不要な commit を生成しない**ことを確認済み。

### ⑲ 安全性テスト結果（一時リポジトリ・全PASS）

| ケース | 結果 |
|---|---|
| ahead0 / behind0 / 差分なし | **変更なし**（commit・pushなし） |
| ahead0 / behind0 / 差分あり | **Excelだけcommit / push成功** |
| ahead1 | **自動pushしない** |
| behind1 | **自動同期停止** |
| ahead1 / behind1 | **自動解決しない** |
| push拒否 | **local commit残存**（rollbackしない） |
| push拒否後の再同期 | **ahead1で停止／「変更なし」と誤認しない** |
| 他ファイルの未commit差分 | **巻き込まない** |
| 他ファイルstage済み | **機種名変換commitへ含めない／stage状態は保持** |
| 正常push後の再同期 | **変更なし** |

### ⑳ 無変更の既存機能

**`_sync_machine_image_master()` / `_git_auto_push()` / `load_name_map()` / `_save_master_df()` /
`run_auto_pipeline` / `generate_report_text` / 画像生成系 / WordPress系 / 機種画像紐づけ /
ban_map系** はいっさい変更していない。

**特に `_git_auto_push()` の targets へ `機種名変換.xlsx` を追加してはならない。**

### ㉑ 非回帰で守ること（機種名変換周りを変更するとき）

- **3保存経路すべてで同期する**
- **差分判定より前に ahead / behind を判定する**
- **未pushcommitがあれば停止する**
- **GitHub側が進んでいれば停止する**
- **push拒否で rollback しない**
- **次回の ahead 判定で停止する（「変更なし」と誤認しない）**
- **他ファイルの差分・stage を巻き込まない**
- **差分なしなら commit を作らない**
- **Cloud の競合を自動解決しない**

<!-- VERBATIM-END id=S04126 -->

<!-- VERBATIM-BEGIN id=S13451 src=CLAUDE.md@fde5030 lines=13451-13539 sha256=b66566e3990b7fd1d526005e9fc20533279da1144267661d40b1616fa1973234 -->
## Streamlit Cloud 起動障害：`packages.txt` 削除で復旧（2026-09-09・`625d29b`）

**正式記録。巻き戻し禁止。**対象は**Streamlit Cloud の起動（APT依存処理）だけ**。
正式コード commit は **`625d29b`**（`fix: 不要なAPT依存を削除してCloud起動エラーを回避`・
**`packages.txt` の削除のみ**・15行削除／追加0）。
**`streamlit_app.py` / `requirements.txt` / `runtime.txt` / その他コードは今回いっさい変更していない。**

### ① 障害内容

2026-09-09、Streamlit Cloud でアプリが起動しなくなった。
**`streamlit_app.py` の実行前**、**APT依存関係のインストール段階**で停止していた。

```
Processing dependencies...
Apt dependencies were installed from /mount/src/guild-image-app/packages.txt using apt-get.
E: Release file for http://deb.debian.org/debian-security/dists/bullseye-security/InRelease
   is expired (invalid since 1d ...)
   Updates for this repository will not be applied.
installer returned a non-zero exit code
Error during processing dependencies!
```

`apt-get install` ではなく **`apt-get update` の段階**で失敗している。
`bullseye-security` は **Debian 11 のセキュリティリポジトリ**で、Debian 11 の EOL に伴い
**Release ファイルの有効期限（Valid-Until）が切れた**ことによる。
ログには `Debian trixie`（Debian 13）・`bullseye-security`（Debian 11）・
`packages.microsoft.com/debian/11/prod` が同時に見えるが、これらは
**Streamlit Cloud のベースイメージ側が持つリポジトリ定義**であり、**当リポジトリの
`packages.txt` の内容（パッケージ名）が原因ではない**。
ただし **`packages.txt` が存在すると Cloud が APT 処理（update → install）を実行する**ため、
**ファイルの存在自体がトリガー**になっていた。

### ② `packages.txt` は旧 Playwright/Chromium 用で現在不要

削除した15項目は**すべて Playwright/Chromium のシステム依存ライブラリ**だった。

```
libnss3 / libnspr4 / libatk1.0-0 / libatk-bridge2.0-0 / libcups2 / libdrm2 /
libxkbcommon0 / libxcomposite1 / libxdamage1 / libxfixes3 / libxrandr2 /
libgbm1 / libasound2 / libpango-1.0-0 / libcairo2
```

**現在の Cloud 実行経路では1つも必要ないことを削除前に確認した。**

| 確認項目 | 結果 |
|---|---|
| `requirements.txt` の playwright / selenium / chromium / imgkit / dataframe_image / weasyprint / cairosvg / pyppeteer / kaleido | **0件**（Cloud にインストールされない） |
| Cloud実行経路（`streamlit_app.py` / `convert_narabi_pil.py` / `shimazu_renderer.py` / `wp_client.py`）のトップレベル import | **0件** |
| 実 import が残るファイル | `convert_20260408.py` / `convert_narabi_稲毛_20260415.py` / `fix_title_spaces.py` ＝ **旧スクリプトで Cloud では起動されない** |
| 並び・列画像 | **全13店舗が `convert_narabi_pil.py`**（`_NARABI_GENERIC`）。import は pandas / os / io / collections / PIL のみ＝**ブラウザ不使用** |
| `streamlit_app.py` の imgkit パッチ | `try: import imgkit, dataframe_image / except: pass` の**文字列**。未インストールなので常に握り潰され無効 |
| `_draw_weekly_table_image` の「Playwright実装に委譲」コメント | **記述が古いだけ**。委譲先 `_weekly_table_html_image()` は docstring どおり **PIL 実装（Playwright不使用・Cloud/ローカル共通版）** |
| フォント | `fonts/MochiyPopOne-Regular.ttf` / `NotoSansJP-Regular.ttf` を**リポジトリ同梱**で使用（APTのフォントパッケージに依存しない） |

`packages.txt` の最終変更は **`e34562e`（2026-06-04）**で、直前の
`205ce21` / `1b43288` / `f0762e7` / `988ea7b` は**いずれも Cloud 起動関連ファイルを触っていない**。
＝**「今日から急に起動しなくなった」のは外部要因（Debian 11 security の期限切れ）のタイミング。**

### ③ 対処＝`packages.txt` を削除して APT 処理自体を発生させない

- **`packages.txt` を削除**すると Cloud は APT 段階を実行しないため、この経路の失敗を回避できる。
- **`streamlit_app.py` をこの起動障害のために変更しない**（実際に変更していない）。
- **APT の workaround（sources.list 書き換え・`--allow-releaseinfo-change` 等）は追加しない。**
- ローカル起動は `packages.txt` を参照しないため**影響なし**。

### ④ 確認できた事実（誤記しないこと）

- **`packages.txt` 削除後、ユーザーが Streamlit Cloud のアプリを実際に開き、
  正常起動・アプリ画面の表示を確認した。これが正式に確認できた事実である。**
- **★Cloud ログ上で「APT処理が消えたこと」自体は Claude 側では直接確認していない。**
  リポジトリに Cloud アプリの URL が記録されておらず、`share.streamlit.io` は
  アカウント設定フォームを表示したため（アカウント作成・フォーム送信は行わない方針）
  コンソール・ログへ到達できなかった。
  **「Cloudログで APT 処理の消滅を確認済み」とは書かない。**

### ⑤ 今後の禁止事項

1. **`packages.txt` を理由なく復活させない**（存在するだけで Cloud の APT 処理が走る）
2. **APT の workaround を勝手に追加しない**
3. **この起動障害を理由に `streamlit_app.py` / `requirements.txt` / `runtime.txt` を変更しない**
4. **並び・列画像を browser 方式（Playwright / selenium / imgkit / dataframe_image）へ戻さない**
   （現在は `convert_narabi_pil.py` の PIL 実装）
5. **将来 Playwright/Chromium 等のブラウザ系処理を Cloud へ再導入する場合は、
   `requirements.txt` への追加と APT システム依存（`packages.txt`）を改めてセットで設計する。**
   その際は Cloud ベースイメージの Debian バージョンに合うパッケージ名かを必ず確認する
   （過去に `chromium-browser` / `wkhtmltopdf` が Debian trixie に存在せず失敗した事例あり＝`e34562e`）
6. **ログに `bullseye-security` / `packages.microsoft.com/debian/11/prod` が出ても、
   当リポジトリのファイルが原因と即断しない**（Cloud ベースイメージ側の定義）

<!-- VERBATIM-END id=S13451 -->

<!-- VERBATIM-BEGIN id=S25957 src=CLAUDE.md@fde5030 lines=25957-26046 sha256=47a80c64684fbc67f7db56343153d50106de9e5ef29a0a421a66b5547fb363c0 -->
## 【正式仕様】不正・未知の `page=` によるCloud無限rerunの防止（2026-10-12・`5c429cc`）

**正式仕様。巻き戻し禁止。**対象は**`main()` 最後の、どのページにも当てはまらない状態を処理する `else` だけ**（全ページ・全店舗共通）。
**8502と Streamlit Cloud 実機で確認済み（2026-10-12）。**既存節は削除・圧縮・統合・書き換えしない。

### A. 正式commit

| 項目 | 内容 |
|---|---|
| 正式commit | **`5c429cc96fa9fdadc7478da39ee36af1037252aa`**（`fix: 不正pageでの無限rerunを防止`・`streamlit_app.py` のみ・+4 / −3） |
| 変更箇所 | `main()` 最後の `else` だけ。新規・削除関数0 |

`5c429cc` の後の Cloud 自動commit **`0117d9f` / `2276df4`**（`work_progress.json` のみ）は有効な履歴として保全し、`git merge --ff-only origin/main` で取り込み済み。
**`5c429cc` へ reset・revert しない**（正式仕様の根拠commitであって HEAD を戻す意味ではない）。

### B. 症状

- Streamlit Cloud で `[RSS] main() 起動直後` が**1秒に数回**の頻度で出続け、アプリが動かないように見える。
- **SyntaxError / ImportError / ModuleNotFoundError / OOM / Segmentation fault / Secrets / GitHub API / Pision・Streamlit の例外は1件もない。**
- Manage app のログ画面に約1万行が溜まって重くなり、「起動していない」ように見える。新しいタブで開くと正常に表示される。
- 2026-10-12 は、修正を push した直後の反映待ちの間にも Cloud 上で連続rerunが再発しており、
  **11:05:02〜11:08:02 UTC の約3分間に約888回**（1秒に約5回）出ていた。

### C. 再現できた原因経路

URLの `page=` に**現在存在しない値**が入ると：

1. `_sync_from_query_params()` が未知の page を `st.session_state.page` へ入れる
2. `main()` 最後の `else` が **session_state だけ**を `store` に戻して `st.rerun()`
3. **URL側の未知の `page=` は残っている**ため、次の実行で 1 に戻って再び読み込まれる
4. 「戻す → 未知値を読み直す」を**待ち時間なしで繰り返す**

修正前の再現（`?page=__unknown_page__`）：**40秒で2,635回以上実行され停止しない**（AppTest）。
正常なページ（`?page=store`）では `main()` は1回で完了する。

### D. 正式修正

```python
    else:
        # 不正な状態はトップに戻す。URL の page も store に直さないと、
        # 次の実行で _sync_from_query_params() が未知の page を再び読み込み、
        # 「戻す→読み直す」の無限再実行になる（Cloud で main() が連続再実行した件）。
        _navigate("store")
```

- 旧：`st.session_state.page = "store"` ＋ `st.rerun()`
- 新：**`_navigate("store")`**（既存関数をそのまま使う）
- **session_state と URL の `page` を同時に `store` へ直す**ので、次の実行で `_sync_from_query_params()` が未知値を読み直さず、**2回で収束**する。
- `_navigate()` / `_sync_from_query_params()` の中身、正常ページのルーティング、戻る・進む（popstate）の仕組みは変更していない。

### E. 確認結果

**8502（`.git` なしの複製）**
- 未知の page は **`main()` 2回で停止**、URLは **`page=store`** に直る。
- 40秒観察して**2回のまま増加なし**。
- 日本語・空白を含む値、存在しない page 名（`work_progress` / `auto_mode`）、大文字の `STORE`、空白だけ、
  店舗付き（`store=新宿歌舞伎町`）・種類付き（`store=稲毛&type=foo`）の未知 page も**すべて2回で収束**。
- 正常17ページ（store / image_type / auto / auto_slump / auto_slump2 / かぶぱ auto_slump / rote / auto_article ×2 /
  other / other_slump / osusume_top / weekly_result_text / work / name_conversion / slump_graph / machine_image）は
  **修正前と同じく `main()` 1回・例外なし・URL変更なし**。
- 戻る・進む（トップ → 高田馬場 → ローテ用）正常。「戻る」で履歴の中の未知URLに入っても2回で収束。

**Cloud**
- 新コードへの更新前（11:05〜11:08 UTC）は連続rerunが実際に再発していた。
- **`Updated app!`（11:08:02 UTC）の後に連続rerunが停止**（その後は2回・1回だけ）。
- `?page=__unknown_page__` → **トップへ戻り、URLも `page=store`**。
- その後 **40秒超の観察でログの増加なし**（41秒間0行）。
- 通常ページ遷移（トップ → 高田馬場 → ローテ用）正常・エラー表示なし。
- **health 200 `ok`・約0.2秒**。8501 もHTTP 200。

### F. 発生源についての扱い（断定しない）

- **今回発生したタブの元URLそのものはログに残っていないため、発生源までは断定しない。**
- ただし、**同じ症状を確実に起こす無限rerun経路を再現・修正し、修正版の反映時点で Cloud 上の連続rerunが止まった**ことは記録する。
- 2026-10-08 の未解決事象（約55分間 `[RSS]` 約3,600回）は症状が同じで、**この経路が強く関連した可能性はあるが、
  10/8 の事象まで遡って原因確定とはしない。**
- 再発した場合は、開いていた全タブのURL（特に `?page=…`）・直前の操作・連続が始まる直前のログを控えてから調べる。

### G. 禁止事項・保全

1. `main()` 最後の `else` を、session_state だけを書き換えて `st.rerun()` する形へ戻さない
2. URLの `page` を残したまま再実行する処理を、ページ判定の外側に新しく作らない
3. `_navigate()` / `_sync_from_query_params()` を本仕様を理由に変更しない
4. 正常ページのルーティング・戻る／進む・popstate の仕組みを本仕様を理由に変えない
5. 発生源を断定した記録へ書き換えない
6. `auto_page_inputs.json`・`store_settings/新宿歌舞伎町.json`・`wrt_machines.json` の既存差分、未追跡4件、stash 5件、
   `C:\Program Files\Git\tmp_chk.json`、アプリ自動commit履歴を保全する。
   `git add .` / `git add -A` / reset / restore / clean / stash操作 / rebase / 通常merge / revert / force push / 削除操作は禁止
7. `5c429cc` へ reset・revert しない

<!-- VERBATIM-END id=S25957 -->

