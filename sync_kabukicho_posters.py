"""新宿歌舞伎町 記事用①の22択ポスター素材を WordPress メディアライブラリから同期する（ローカル専用）。

使い方（Windows のローカル環境だけで実行する）:
    py -3.14 sync_kabukicho_posters.py            # 取得して素材と manifest.json を更新
    py -3.14 sync_kabukicho_posters.py --dry-run  # 取得・比較だけ（書き込まない）

・WordPress へは **GET だけ**（メディア一覧・メディア情報・画像本体）。
  投稿・メディアの作成／編集／削除／公開は一切しない。
・どの画像を使うかはアプリと同じ規則（streamlit_app._art_poster_resolve）で決める。
  ＝ラベル名／末尾連番の最新版を選び、除外ID（29・44）は使わない。
・1件でも取得に失敗したら **何も書き込まずに中止**する（中途半端な素材を残さない）。
・Secrets値・URL・クエリ・認証情報は表示しない。
・同期後は assets/posters/kabukicho/ 配下だけを明示指定で commit・push し、Cloud を Reboot する。
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys

STORE = "新宿歌舞伎町"


def main() -> int:
    dry = "--dry-run" in sys.argv[1:]
    root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root)
    sys.path.insert(0, root)
    try:
        from dotenv import load_dotenv
        load_dotenv(os.path.join(root, ".env"))
    except Exception:
        pass
    import streamlit_app as sa

    if sa._IS_CLOUD:
        print("❌ このツールはローカル（Windows）環境専用です。Cloud では実行しません。")
        return 2
    out_dir = sa._ART_POSTER_ASSET_DIRS[STORE]
    man_path = os.path.join(out_dir, sa._ART_POSTER_MANIFEST_FN)
    old = sa._art_poster_manifest(STORE)

    sa._art_poster_media_index.clear()
    sa._art_poster_media_fetch.clear()
    fetched: list[tuple[str, int, dict]] = []
    errors: list[str] = []
    for label, _fixed in sa._ART_POSTER_LIBRARY:
        mid, rerr = sa._art_poster_resolve(STORE, label)
        if rerr:
            errors.append(f"{label}: 一覧の取得に失敗 [{rerr}]")
            continue
        got, err = sa._art_poster_media_try(STORE, int(mid))
        if not got:
            errors.append(f"{label}（ID {mid}）: 画像の取得に失敗 [{err}]")
            continue
        fetched.append((label, int(mid), got))
    if errors:
        print("❌ 取得に失敗したため、何も書き込まずに中止しました。")
        for e in errors:
            print("   -", e)
        return 1

    new_man: dict = {}
    changed = 0
    for label, mid, got in fetched:
        ext = os.path.splitext(got["name"])[1].lower() or ".jpg"
        fn = sa._ART_POSTER_SLUGS[label] + ext
        sha = hashlib.sha256(got["data"]).hexdigest()
        prev = old.get(label) or {}
        same = (prev.get("file") == fn and prev.get("sha256") == sha
                and os.path.isfile(os.path.join(out_dir, fn)))
        new_man[label] = {
            "file": fn, "media_id": mid, "source_name": got["name"], "sha256": sha,
            "synced_at": (prev.get("synced_at") if same
                          else datetime.date.today().isoformat()),
        }
        mark = "＝変更なし" if same else "★更新"
        print(f"{mark} {label:14s} ID {mid:>4} {got['name']} → {fn} ({len(got['data']):,} bytes)")
        if not same:
            changed += 1
            if not dry:
                os.makedirs(out_dir, exist_ok=True)
                with open(os.path.join(out_dir, fn), "wb") as f:
                    f.write(got["data"])
    if dry:
        print(f"（dry-run）更新対象 {changed} 件。書き込みはしていません。")
        return 0
    if changed or new_man != old:
        os.makedirs(out_dir, exist_ok=True)
        with open(man_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(new_man, f, ensure_ascii=False, indent=2)
            f.write("\n")
    print(f"✅ 完了：{len(new_man)} 件（更新 {changed} 件）。")
    print("   次に assets/posters/kabukicho/ の変更ファイルだけを明示指定で commit・push し、Cloud を Reboot してください。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
