"""Second co-signer test, on paying wallets. Plan: docs/PLAN_cosigners_v2.md. Reads the windows already cached, spends no credit.

FORENSICS_DATA_ROOT=<copy of the cache> python -m forensics_v2.investigations.cosigners_v2
"""

from __future__ import annotations

import json
import random
import statistics
from collections import Counter, defaultdict
from math import comb
from pathlib import Path
from typing import Any

from .. import storage
from ..__main__ import client
from ..trace import history
from . import cosigners as C

SEED = 20261103
DRAWS = 10_000
OUT = Path(__file__).resolve().parents[1] / "reports/cosigners_v2"
MEASURES = ("M1", "M2", "M3", "M4", "M5")


def verdict(m: dict[str, float], any_payer: bool) -> str:
    if not any_payer:
        return "no_payer"
    if m["M5"] >= 0.8 or m["M4"] >= 0.5:
        return "private"
    if m["M1"] >= 20 and m["M4"] < 0.1 and m["M5"] < 0.6:
        return "service"
    return "not_separated"


def measures(
    days_by_payer: dict[str, set[int]], sol_by_payer: Counter[str], known: set[str], shared: set[str]
) -> dict[str, float]:
    total = sum(sol_by_payer.values()) or 1
    persistent = {p for p, d in days_by_payer.items() if len(d) >= 2}
    return {
        "M1": float(len(persistent)),
        "M2": sum(sol_by_payer[p] for p in persistent) / total,
        "M3": len(persistent & shared) / len(persistent) if persistent else 0.0,
        "M4": sum(v for p, v in sol_by_payer.items() if p in known) / total,
        "M5": sum(v for _, v in sol_by_payer.most_common(5)) / total,
    }


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    n, r1, k1 = a + b + c + d, a + b, a + c

    def pr(x: int) -> float:
        return comb(r1, x) * comb(n - r1, k1 - x) / comb(n, k1)

    p0 = pr(a)
    return min(1.0, sum(pr(x) for x in range(max(0, k1 - (n - r1)), min(r1, k1) + 1) if pr(x) <= p0 * (1 + 1e-9)))


def main() -> int:
    c = client(0)
    store = storage.data_root() / "intermediate" / "cosigners"
    lst = json.loads((store / "list.json").read_text())
    rows = json.loads((store / "rows.json").read_text())
    known = C.known_operator_wallets()
    payers: dict[str, dict[str, set[int]]] = defaultdict(lambda: defaultdict(set))
    sol: dict[str, Counter[str]] = defaultdict(Counter)
    for w in rows:
        for day, s in enumerate(C.WINDOWS):
            h = history(c, w, t_from=s, t_to=min(s + C.DAY - 1, C.HARD_END - 1), token_accounts="none", max_pages=1)
            for d in h.txs:
                if d.ok:
                    for e in d.edges:
                        if e.dst == w:
                            payers[w][e.src].add(day)
                            sol[w][e.src] += e.lamports
    assert c.net_calls == 0, "this test must not spend credits"
    hubs: Counter[str] = Counter(p for w in payers for p in payers[w])
    shared = {p for p, n in hubs.items() if n >= 2}
    table = {w: measures(payers[w], sol[w], known, shared) for w in rows}
    verdicts = {w: verdict(table[w], bool(sol[w])) for w in rows}
    controls = (
        set(lst["controls"])
        if isinstance(lst, dict) and "controls" in lst
        else set(json.loads((store / "list.json").read_text()).get("controls", []))
    )
    cos = [w for w in rows if w not in controls]
    con = [w for w in rows if w in controls]
    rng = random.Random(SEED)
    tests = {}
    for k in MEASURES:
        vals = [table[w][k] for w in cos + con]
        obs = statistics.median(vals[: len(cos)]) - statistics.median(vals[len(cos) :])
        hit = 0
        for _ in range(DRAWS):
            rng.shuffle(vals)
            hit += abs(statistics.median(vals[: len(cos)]) - statistics.median(vals[len(cos) :])) >= abs(obs)
        tests[k] = {
            "median_cosigners": statistics.median(table[w][k] for w in cos),
            "median_controls": statistics.median(table[w][k] for w in con),
            "p": (hit + 1) / (DRAWS + 1),
            "passes_bonferroni": (hit + 1) / (DRAWS + 1) < 0.05 / len(MEASURES),
        }
    cnt = {"cosigners": Counter(verdicts[w] for w in cos), "controls": Counter(verdicts[w] for w in con)}
    a, b = cnt["cosigners"]["service"], len(cos) - cnt["cosigners"]["service"]
    x, y = cnt["controls"]["service"], len(con) - cnt["controls"]["service"]
    p = fisher_two_sided(a, b, x, y)
    res: dict[str, Any] = {
        "plan": "docs/PLAN_cosigners_v2.md",
        "seed": SEED,
        "n_cosigners": len(cos),
        "n_controls": len(con),
        "credits_spent": c.net_calls,
        "verdicts": {k: dict(v) for k, v in cnt.items()},
        "fisher_service_share_p": p,
        "discriminates": p < 0.05,
        "tests": tests,
        "payers_total": len(hubs),
        "payers_shared": len(shared),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
