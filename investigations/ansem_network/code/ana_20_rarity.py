"""Rarity test fixed in PLAN.md: do the seed wallets co-occur with a partner more than chance, compared to like wallets?

Launches come from local corpora only. Null: curveball randomisation, each launch keeps its number of wallets and each
wallet its number of launches. Statistic for wallet W: the largest number of launches shared with any one other wallet.
Reads no network. Prints and writes evidence/rarity.json. Positive and negative controls run first and must pass.
"""
from __future__ import annotations

import argparse
import gzip
import json
import random
from collections import Counter
from pathlib import Path

from lib import OUT

REPO = Path(__file__).resolve().parents[3]
SEEDS = ["yHCxHBEaJW5tbndqC8JciSThr7U1cqLpdcsvHcx6PRe", "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq",
         "LfEcaUf77iEhnz6gFpLqYgDb5Uk6Ekc5n69wu7Qa9Uw", "dshAybqFXYVVTd4mzy9Uk6KD7km8wE9iZgPMYZdzEXc",
         "HKCFgNYU", "1mGRiNd5", "7mTX78HL", "Bot5Xi6E", "3ntEpydD", "GV6UUmNxz2RpKxmNAPadYKb7uQpszwqQAu3qLJxVdC52"]


def load() -> dict[str, set[str]]:
    launches: dict[str, set[str]] = {}
    with gzip.open(REPO / "data" / "floor_capture_public.jsonl.gz", "rt") as f:
        for line in f:
            d = json.loads(line)
            if d.get("snipers"):
                launches.setdefault(d["mint"], set()).update(d["snipers"])
    for e in json.load(open(REPO / "data" / "v05_creation_block.json"))["lancements"]:
        launches.setdefault(e["mint"], set()).update(e["wallets_bloc"])
    p = Path.home() / "Documents/Crypto/ansem_enquete/data/snipers90.json"
    for m, e in json.load(open(p)).items():
        launches.setdefault(m, set()).update(e["buyers"])
    return {m: w for m, w in launches.items() if w}


def curveball(sets: list[set], trades: int, rng: random.Random) -> None:
    """In-place trades between two random launches: shuffles who is where, margins unchanged."""
    n = len(sets)
    for _ in range(trades):
        i, j = rng.randrange(n), rng.randrange(n)
        if i == j:
            continue
        a, b = sets[i], sets[j]
        only_a, only_b = list(a - b), list(b - a)
        if not only_a or not only_b:
            continue
        pool = only_a + only_b
        rng.shuffle(pool)
        k = len(only_a)
        a.difference_update(only_a)
        b.difference_update(only_b)
        a.update(pool[:k])
        b.update(pool[k:])


def best_partner(sets: list[set], wallets: list[str]) -> dict[str, int]:
    want = set(wallets)
    tally: dict[str, Counter] = {w: Counter() for w in wallets}
    for s in sets:
        for w in want & s:
            tally[w].update(s - {w})
    return {w: (tally[w].most_common(1)[0][1] if tally[w] else 0) for w in wallets}


def run(sets: list[set], wallets: list[str], draws: int, seed: int) -> dict[str, dict]:
    obs = best_partner(sets, wallets)
    rng = random.Random(seed)
    ge = Counter()
    cur = [set(s) for s in sets]
    curveball(cur, 20 * len(cur), rng)
    for _ in range(draws):
        curveball(cur, 2 * len(cur), rng)
        sim = best_partner(cur, wallets)
        for w in wallets:
            ge[w] += sim[w] >= obs[w]
    return {w: {"observed": obs[w], "p": (ge[w] + 1) / (draws + 1)} for w in wallets}


def controls(sets: list[set], draws: int) -> dict:
    rng = random.Random(7)
    planted = [set(s) for s in sets]
    idx = rng.sample(range(len(planted)), 12)
    for i in idx:
        planted[i].update({"PLANT_A", "PLANT_B"})
    pos = run(planted, ["PLANT_A"], draws, 1)["PLANT_A"]
    shuffled = [set(s) for s in sets]
    curveball(shuffled, 200 * len(shuffled), random.Random(11))
    cnt = Counter(w for s in shuffled for w in s)
    mid = [w for w, c in cnt.items() if 5 <= c <= 15][:40]
    neg = run(shuffled, mid, draws, 2)
    n_low = sum(v["p"] < 0.01 for v in neg.values())
    assert pos["p"] < 0.01, "positive control failed"
    assert n_low <= 2, "negative control flagged %d of %d" % (n_low, len(mid))
    return {"planted_pair_p": pos["p"], "shuffled_wallets": len(mid), "shuffled_flagged_p_lt_0.01": n_low}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", type=int, default=10000)
    a = ap.parse_args()
    launches = load()
    sets = [set(v) for _, v in sorted(launches.items())]
    cnt = Counter(w for s in sets for w in s)
    ctl = controls(sets, min(a.draws, 500))
    print("launches", len(sets), "wallets", len(cnt), "controls", ctl, flush=True)
    full = {s: [w for w in cnt if w.startswith(s)] for s in SEEDS}
    seeds = [w[0] for w in full.values() if w]
    missing = [s for s, w in full.items() if not w]
    common = [w for w, c in cnt.items() if c >= 5]
    res = run(sets, sorted(set(common) | set(seeds)), a.draws, 3)
    out = {"launches": len(sets), "wallets": len(cnt), "wallets_tested": len(res), "draws": a.draws, "controls": ctl,
           "seeds_absent_from_corpus": missing, "seeds": {}, "note": "A low p means the wallet shares launches with one partner "
           "more than chance. It says nothing about ownership: shared bots do this too."}
    for w in seeds:
        k = cnt[w]
        group = [x for x in res if x != w and 0.8 * k <= cnt[x] <= 1.2 * k]
        low = sum(res[x]["p"] <= res[w]["p"] for x in group)
        tally = Counter()
        for s in sets:
            if w in s:
                tally.update(s - {w})
        out["seeds"][w] = {"launches": k, **res[w], "top_partners": tally.most_common(4), "group_size": len(group),
                           "group_at_or_below_same_p": low}
        print(w[:10], out["seeds"][w], flush=True)
    (OUT / "rarity.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
