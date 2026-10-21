"""CLAUDE.md 分割（docs/specs/）の完全一致を検証する。

使い方:
  py -3.14 tools/verify_claude_split.py               作業ツリーの CLAUDE.md・docs/specs を検証
  py -3.14 tools/verify_claude_split.py --rev <rev>   指定 commit の状態を検証
  py -3.14 tools/verify_claude_split.py --docs-only   docs と復元だけ検証（CLAUDE.md の保持部分は見ない）

検証内容:
  1. 区切りの網羅：保持範囲＋移した各節が旧 CLAUDE.md の全行を漏れ0・重複0で覆う
  2. docs の各 VERBATIM ブロックが manifest の sha256 と一致し、割当ファイルに過不足がない
  3. 保持部分＋各節を元の行番号順につなぐと旧 CLAUDE.md とバイト単位で一致（最終改行なしも含む）
  4. 新 CLAUDE.md の保持部分が、承認済みの文言変更を戻すと旧 1〜191 行目とバイト一致
  5. 見出し総数・全行の多重集合が一致／README に全節の索引がある
旧 CLAUDE.md は manifest の blob を `git cat-file` で読む（作業ツリーには依存しない）。
"""
import collections, hashlib, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = sys.argv[sys.argv.index("--rev") + 1] if "--rev" in sys.argv else None
DOCS_ONLY = "--docs-only" in sys.argv
fails = []


def git(*a):
    return subprocess.run(["git", *a], capture_output=True, cwd=ROOT, check=True).stdout


def read(path):
    if REV:
        return git("show", f"{REV}:{path}").decode("utf-8")
    with open(os.path.join(ROOT, path), "rb") as fh:
        # core.autocrlf=true の環境では作業ツリーが CRLF になり得るため LF へ戻して比較する
        # （commit 済みの blob は LF。厳密な確認は --rev で行う）
        return fh.read().decode("utf-8").replace("\r\n", "\n")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        fails.append(msg)


M = json.loads(read("docs/specs/_split_manifest.json"))
src = M["source"]
RAW = git("cat-file", "blob", src["blob"])
OLD = RAW.decode("utf-8")
L = OLD.split("\n")
N = len(L)
check(sha(OLD) == src["sha256"] and len(RAW) == src["bytes"] and N == src["lines"],
      f"旧CLAUDE.md blob {src['blob'][:7]} の sha256・バイト数・行数が manifest と一致")
check(OLD.endswith("\n") == src["ends_with_newline"] == False, "旧CLAUDE.md は最終改行なし")

seg = lambda s, e: "\n".join(L[s - 1:e])
keep = M["keep"]
secs = M["sections"]

# 1. 区切りの網羅
cover = collections.Counter(range(keep["start"], keep["end"] + 1))
for x in secs:
    cover.update(range(x["start"], x["end"] + 1))
missing = [i for i in range(1, N + 1) if cover[i] == 0]
dup = [i for i, c in cover.items() if c > 1]
outside = [i for i in cover if not 1 <= i <= N]
check(not missing and not dup and not outside,
      f"区切りの網羅：欠落{len(missing)}行・重複{len(dup)}行・範囲外{len(outside)}行")
check(all(L[x["start"] - 1] == x["heading"] for x in secs), "各節の先頭行が manifest の見出しと一致")
check(len({x["id"] for x in secs}) == len(secs), f"節IDの重複なし（{len(secs)}節）")

# 2. docs の VERBATIM ブロック
pat = re.compile(r"<!-- VERBATIM-BEGIN id=(S\d+) [^\n]*-->\n")
SEC = {x["id"]: x for x in secs}
seen = collections.Counter()
for f in M["files"]:
    text = read(f"{M['docs_dir']}/{f['file']}")
    ids = []
    for m in pat.finditer(text):
        sid = m.group(1)
        endtag = f"\n<!-- VERBATIM-END id={sid} -->"
        e = text.find(endtag, m.end())
        if e < 0:
            fails.append(f"{f['file']} {sid} END なし")
            continue
        body = text[m.end():e]
        ids.append(sid)
        seen[sid] += 1
        x = SEC.get(sid)
        ok = x is not None and sha(body) == x["sha256"] and body == seg(x["start"], x["end"])
        if not ok:
            fails.append(f"{f['file']} {sid} 本文不一致")
    check(ids == f["sections"], f"{f['file']}：{len(ids)}節・割当順どおり・本文 sha256 一致")
check(set(seen) == set(SEC) and all(c == 1 for c in seen.values()),
      f"docs 全体で各節がちょうど1回（{sum(seen.values())}/{len(SEC)}）")
check(all(x["file"] == f["file"] for f in M["files"] for sid in f["sections"] for x in [SEC[sid]]),
      "manifest のファイル割当が一致")

# 3. 復元（バイト単位）
parts = [(keep["start"], seg(keep["start"], keep["end"]))]
for f in M["files"]:
    text = read(f"{M['docs_dir']}/{f['file']}")
    for sid in f["sections"]:
        b = text.index(f"<!-- VERBATIM-BEGIN id={sid} ")
        b = text.index("-->\n", b) + 4
        e = text.index(f"\n<!-- VERBATIM-END id={sid} -->", b)
        parts.append((SEC[sid]["start"], text[b:e]))
REBUILT = "\n".join(p for _, p in sorted(parts))
check(REBUILT.encode("utf-8") == RAW and sha(REBUILT) == src["sha256"],
      f"復元が旧CLAUDE.mdとバイト単位で一致（sha256 {sha(REBUILT)[:16]}…・最終改行なし）")
check(not REBUILT.endswith("\n"), "復元結果も最終改行なし")

# 4. 新 CLAUDE.md の保持部分
if not DOCS_ONLY:
    new = read("CLAUDE.md")
    mk = "\n" + keep["marker"] + "\n"
    if mk not in new:
        check(False, "新CLAUDE.md に保持部分の終端マーカーがある")
    else:
        head = new[:new.index(mk)].split("\n")
        for e in keep["edits"]:
            if head[e["line"] - 1] == e["new"]:
                head[e["line"] - 1] = e["old"]
            else:
                fails.append(f"承認済み変更 {e['line']}行目 が見つからない")
        check("\n".join(head) == seg(keep["start"], keep["end"]),
              f"新CLAUDE.md の保持部分＝旧{keep['start']}〜{keep['end']}行目（承認済み変更{len(keep['edits'])}行を除きバイト一致）")
        check(new.count(keep["marker"]) == 1, "保持部分の終端マーカーは1つ")

# 5. 補助チェック
heads = [l for l in REBUILT.split("\n") if l.startswith("## ")]
check(len(heads) == src["headings_total"], f"見出し総数 {len(heads)}／{src['headings_total']}")
check(collections.Counter(REBUILT.split("\n")) == collections.Counter(L), "全行の多重集合が一致")
readme = read(f"{M['docs_dir']}/README.md")
check(all(f"`{x['id']}`" in readme for x in secs), "README に全節の索引がある")

print("\n結果:", "全項目合格" if not fails else f"不合格 {len(fails)}件")
for f in fails[:20]:
    print("  -", f)
sys.exit(1 if fails else 0)
