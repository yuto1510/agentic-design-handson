#!/usr/bin/env python3
"""決定的な retrieval workflow。

構造化クエリ(JSON)を stdin で受け取り、以下を **コードで保証** する:
  pagination / author metadata の参照 / country 正規化 / retracted 除外 / 重複排除

    echo '{"keywords":["agent"],"year_min":2024,"countries":["JP"]}' | python3 workflow.py

Claude に残す仕事は「自然言語の要求 -> この JSON」の変換だけ。
"""
import json, pathlib, re, sys

DATA = pathlib.Path(__file__).parent / "data"
load = lambda n: json.loads((DATA / f"{n}.json").read_text())
PAGE_SIZE = 5

# --- country 正規化 -------------------------------------------------------
ALIASES = {"JP": "JP", "JPN": "JP", "JAPAN": "JP", "日本": "JP",
           "US": "US", "USA": "US", "UK": "UK", "GB": "UK", "CN": "CN"}
JP_INSTITUTIONS = ("riken", "university of tokyo", "kyoto university",
                   "osaka university", "tohoku university", "ntt", "aist",
                   "waseda", "keio", "titech", "tokyo institute of technology")


def normalize_country(author):
    code = ALIASES.get((author.get("country") or "").strip().upper())
    if code:
        return code
    aff = (author.get("affiliation") or "").lower()
    if "japan" in aff or any(k in aff for k in JP_INSTITUTIONS):
        return "JP"
    return None  # 判定不能。推測はしない。


# --- 重複排除 -------------------------------------------------------------
norm_title = lambda t: re.sub(r"[^a-z0-9]+", "", t.lower())
# 同一 doi / 同一正規化タイトルは同じ論文とみなし、preprint より査読版を優先する
rank = lambda p: (1 if "arxiv" in p["venue"].lower() or "preprint" in p["venue"].lower() else 0, p["id"])


def dedupe(papers):
    best = {}
    for p in papers:
        for key in (("doi", p["doi"]), ("title", norm_title(p["title"]))):
            cur = best.get(key)
            if cur is None or rank(p) < rank(cur):
                best[key] = p
    kept, seen = [], set()
    for p in papers:
        keys = (("doi", p["doi"]), ("title", norm_title(p["title"])))
        if all(best[k] is p for k in keys) and p["id"] not in seen:
            seen.add(p["id"])
            kept.append(p)
    return kept


# --- pagination -----------------------------------------------------------
def fetch_all(keywords):
    papers, page = [], 1
    while True:
        page_papers = [p for p in load("papers")
                       if any(k.lower() in p["title"].lower() for k in keywords)]
        chunk = page_papers[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]
        papers += chunk
        if page * PAGE_SIZE >= len(page_papers):   # 最終ページまで必ず辿る
            return papers
        page += 1


def run(q):
    keywords = q.get("keywords") or [""]
    year_min = q.get("year_min")
    countries = {c.upper() for c in q.get("countries", [])}
    exclude_retracted = q.get("exclude_retracted", True)

    authors = {a["id"]: a for a in load("authors")}
    retracted = {r["doi"] for r in load("retractions")}

    out = []
    for p in fetch_all(keywords):
        if year_min is not None and p["year"] < year_min:
            continue
        if exclude_retracted and p["doi"] in retracted:
            continue
        matched = [authors[i] for i in p["author_ids"]                       # 全著者を見る
                   if i in authors and normalize_country(authors[i]) in countries]
        if countries and not matched:
            continue
        out.append({**p, "matched_authors": [a["name"] for a in matched]})

    out = dedupe(out)
    return {"query": q, "count": len(out), "papers": out}


json.dump(run(json.load(sys.stdin)), sys.stdout, ensure_ascii=False, indent=2)
print()
