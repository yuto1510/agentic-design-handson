#!/usr/bin/env python3
"""低レベルツール群（agentic ブランチ）。

ここには「答えを出す処理」は入っていない。
pagination / 所属の名寄せ / retracted 除外 / 重複排除 はすべて呼び出し側の責任。

    python3 tools.py search --query agent --page 1   # 1ページ5件しか返らない
    python3 tools.py author --id a1                  # 著者を1件だけ返す
    python3 tools.py retraction --doi 10.1000/agent-f
"""
import argparse, json, pathlib, sys

DATA = pathlib.Path(__file__).parent / "data"
load = lambda n: json.loads((DATA / f"{n}.json").read_text())
PAGE_SIZE = 5


def search(args):
    q = args.query.lower()
    hits = [p for p in load("papers") if q in p["title"].lower()]
    start = (args.page - 1) * PAGE_SIZE
    return {
        "page": args.page,
        "page_size": PAGE_SIZE,
        "total_pages": max(1, -(-len(hits) // PAGE_SIZE)),
        "total_hits": len(hits),
        "results": hits[start:start + PAGE_SIZE],
    }


def author(args):
    return next((a for a in load("authors") if a["id"] == args.id), None)


def retraction(args):
    rec = next((r for r in load("retractions") if r["doi"] == args.doi), None)
    return {"doi": args.doi, "retracted": rec is not None, "record": rec}


p = argparse.ArgumentParser(description=__doc__)
sub = p.add_subparsers(dest="cmd", required=True)

s = sub.add_parser("search", help="タイトル部分一致で論文を検索する（1ページ5件）")
s.add_argument("--query", required=True)
s.add_argument("--page", type=int, default=1)
s.set_defaults(fn=search)

s = sub.add_parser("author", help="著者 ID から著者レコードを1件返す")
s.add_argument("--id", required=True)
s.set_defaults(fn=author)

s = sub.add_parser("retraction", help="DOI が撤回されているか調べる")
s.add_argument("--doi", required=True)
s.set_defaults(fn=retraction)

a = p.parse_args()
json.dump(a.fn(a), sys.stdout, ensure_ascii=False, indent=2)
print()
