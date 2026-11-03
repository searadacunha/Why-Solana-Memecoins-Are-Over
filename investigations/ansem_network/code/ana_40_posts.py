"""Exploratory, added after the plan: does what a cited post announces match what the deployer then does?

A post that names a share ("sending 60%", "sending him 5%") is compared with the largest single gift in the launch.
Baseline: same posts against launches shuffled at random, 2,000 times. A match says the launch followed the post. It does
not say who wrote the post: a fast copier would match as well. Written to evidence/post_vs_launch.json.
"""
from __future__ import annotations

import csv
import json
import random
import re
from collections import Counter

from lib import CREATOR, OUT

PCT = re.compile(r"(?:send\w*|giv\w*|airdrop\w*|allocat\w*|to\s+\w+)\D{0,25}?(\d{1,3}(?:\.\d+)?)\s?%|(\d{1,3}(?:\.\d+)?)\s?%\D{0,25}?(?:supply|to\s|for\s|fees)", re.I)


def main() -> None:
    posts = {}
    with open(OUT / "x_posts.jsonl") as f:
        for line in f:
            r = json.loads(line)
            posts[r["id"]] = r
    meta = {}
    with open(OUT / "token_metadata.jsonl") as f:
        for line in f:
            r = json.loads(line)
            m = re.search(r"(?:x|twitter)\.com/([^/]+)/status/(\d{15,25})", r.get("twitter") or "")
            if m:
                meta[r["mint"]] = (m.group(1).lower(), m.group(2))
    rows = {r["mint"]: r for r in csv.DictReader(open(OUT.parent / "TOKENS.csv")) if r["creator_wallet"] == CREATOR}
    from ana_12_gifts import largest_gift_share
    share = largest_gift_share()
    read = Counter()
    gone = Counter()
    pairs = []
    for mint, (acc, pid) in meta.items():
        if mint not in rows:
            continue
        p = posts.get(pid)
        if not p or not p.get("readable"):
            gone[acc] += 1
            continue
        read[acc] += 1
        h = PCT.search(p["text"])
        if h:
            pairs.append((mint, acc, float(h.group(1) or h.group(2)), p["text"][:140], pid))
    def hit(pct: float, m: str) -> bool:
        return abs(share.get(m, 0.0) - pct) <= 3.0

    obs = sum(hit(p[2], p[0]) for p in pairs)
    mints = list(rows)
    rng = random.Random(5)
    ge = 0
    sims = []
    for _ in range(2000):
        c = sum(hit(p[2], rng.choice(mints)) for p in pairs)
        sims.append(c)
        ge += c >= obs
    pids = {pid for acc, pid in meta.values()}
    pid_of = {mint: pid for mint, (acc, pid) in meta.items()}
    cited = {pid_of[m] for m in rows if m in pid_of}
    out = {"launches_citing_a_post": len([m for m in rows if m in meta]), "distinct_posts": len(cited), "distinct_posts_readable": sum(1 for p in cited if posts.get(p, {}).get("readable")),
           "distinct_posts_naming_a_share": len({p[4] for p in pairs}), "accounts_naming_a_share": len({p[1] for p in pairs}),
           "share_posts_by_blknoiz06": sum(p[1] == "blknoiz06" for p in pairs),
           "misses": [{"mint": p[0], "account": p[1], "stated_pct": p[2], "largest_gift_pct": round(share.get(p[0], 0.0), 2)} for p in pairs if not hit(p[2], p[0])],
           "launches_citing_posts_readable": sum(read.values()), "launches_citing_posts_unreadable": sum(gone.values()), "readable_by_account": read.most_common(15), "unreadable_by_account": gone.most_common(15),
           "launch_post_pairs_naming_a_share": len(pairs), "matches_within_3_points": obs, "baseline_mean_matches": sum(sims) / len(sims), "p_shuffled": (ge + 1) / 2001,
           "examples": [{"mint": p[0], "account": p[1], "stated_pct": p[2], "largest_gift_pct": round(share.get(p[0], 0.0), 2), "text": p[3], "post": p[4]} for p in pairs if hit(p[2], p[0])][:25],
           "status": "exploratory, not in PLAN.md"}
    (OUT / "post_vs_launch.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
    print({k: v for k, v in out.items() if k not in ("examples", "misses")})
    print(out["misses"])
    for e in out["examples"][:14]:
        print(e["account"], e["stated_pct"], e["largest_gift_pct"], "|", e["text"][:110].replace("\n", " "))


if __name__ == "__main__":
    main()
