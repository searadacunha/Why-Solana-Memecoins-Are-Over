"""Very active wallets that co-sign for several operators, per docs/PLAN_cosigners.md.

    python -m forensics_v2.investigations.cosigners list              # co-signers and controls, from the frozen tables
    python -m forensics_v2.investigations.cosigners collect <credits> # the eight windows of each wallet
    python -m forensics_v2.investigations.cosigners analyse           # measures and the hypotheses

Wallet-level rows stay on the data volume. The public report only gives counts and addresses already public.
"""
from __future__ import annotations

import gzip
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Optional

from .. import decode as D
from ..__main__ import client
from .. import storage
from ..trace import history
from .gateway_bursts import wilson  # noqa: F401  (kept next to the other interval users)

REPO = Path(__file__).resolve().parents[2]
SEED = 20261102
DAY = 86400
T0, T1 = 1787270400, 1789948800  # 2026-08-21 00:00 and 2026-09-21 00:00 UTC
HARD_END = 1790035200            # 2026-09-22 00:00 UTC: nothing at or after this is read
WINDOWS = [T0 + i * (T1 - T0) // 7 for i in range(8)]
OUT = Path(__file__).resolve().parents[1] / "reports" / "cosigners"
FN_TX_CACHE = Path.home() / "Documents/Crypto/Why-Solana-Memecoins-Are-Over/funder_network/data/cache/tx"


def _tables() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    fn = json.loads(gzip.open(REPO / "funder_network/derived/fn_table.json.gz").read())
    ed = json.loads(gzip.open(REPO / "exit_destination/derived/ed_table.json.gz").read())
    post = json.loads((REPO / "funder_network/derived/FN_posthoc.json").read_text())
    return fn, ed, post


def _signers(sig: str, fn: dict[str, Any], c: Any) -> list[str]:
    for rows in fn["reads"].values():
        for r in rows:
            if r.get("sig") == sig and r.get("signers") is not None:
                return r["signers"]
    p = FN_TX_CACHE / sig[:2] / (sig + ".json")
    if p.exists():
        keys = json.loads(p.read_text())["transaction"]["message"]["accountKeys"]
        return [k["pubkey"] for k in keys if k.get("signer")]
    return D.decode(c.tx(sig)).signers


def build_list(c: Any) -> dict[str, Any]:
    fn, _, post = _tables()
    hubs = post["hubs"]
    co: dict[str, set[str]] = {}
    for x in fn["downs"]:
        step = x["path"][1]
        a = step["wallet"]
        if a in hubs and a in _signers(step["sig"], fn, c):
            co.setdefault(a, set()).update(fn["primary"].get(x["primary"], {}).get("operators", []))
    others = sorted(set(hubs) - set(co))
    ctrl = random.Random(SEED).sample(others, min(len(co), len(others)))
    return {"cosigners": {a: sorted(v) for a, v in sorted(co.items())}, "controls": sorted(ctrl), "n_hubs": len(hubs)}


def known_operator_wallets() -> set[str]:
    """Wallets of the frozen tables tied to an operator: primaries, exit wallets, snipers' sweeps, chain members."""
    fn, ed, _ = _tables()
    out = set(fn["primary"])
    for x in fn["downs"] + fn["ups"]:
        out.update(s["wallet"] for s in x["path"])
    for b in ed["branches"]:
        out.update(s["wallet"] for s in b["path"])
    return out


def _measures(txs: list[D.Decoded], w: str, known: set[str]) -> dict[str, Any]:
    other: Counter[str] = Counter()
    signer_counts: Counter[int] = Counter()
    programs: Counter[str] = Counter()
    dest: Counter[str] = Counter()
    signed = template = 0
    for d in txs:
        signer_counts[len(d.signers)] += 1
        signed += w in d.signers
        other.update(s for s in d.signers if s != w)
        programs[",".join(p[:6] for p in d.programs)] += 1
        closes = any(t.kind == "close_refund" and t.mint == D.WSOL for t in d.transfers)
        template += len(d.signers) == 4 and closes
        if d.ok:
            for e in d.edges:
                if e.src == w:
                    dest[e.dst] += e.lamports
    n = len(txs)
    top10 = sum(v for _, v in other.most_common(10))
    return {
        "n_tx": n, "share_signed": signed / n if n else None, "signer_counts": dict(signer_counts),
        "distinct_other_signers": len(other), "top10_share_of_other_signers": top10 / sum(other.values()) if other else None,
        "known_operator_share_of_other_signers": sum(1 for s in other if s in known) / len(other) if other else None,
        "n_known_operator_signers": sum(1 for s in other if s in known),
        "distinct_program_sets": len(programs), "top_program_set_share": programs.most_common(1)[0][1] / n if n else None,
        "four_signer_sweep_share": template / n if n else None, "distinct_destinations": len(dest),
        "top_destination_share": dest.most_common(1)[0][1] / sum(dest.values()) if dest else None,
        "out_lamports": sum(dest.values()), "other_signers": sorted(other),
    }


def collect(credits: int) -> int:
    c = client(credits)
    lst = build_list(c)
    store = storage.data_root() / "intermediate" / "cosigners"
    store.mkdir(parents=True, exist_ok=True)
    (store / "list.json").write_text(json.dumps(lst, indent=1))
    print("cosigners", len(lst["cosigners"]), "controls", len(lst["controls"]), "net", c.net_calls, flush=True)
    known = known_operator_wallets()
    rows = {}
    stopped: Optional[str] = None
    wallets = [(w, "cosigner") for w in lst["cosigners"]] + [(w, "control") for w in lst["controls"]]
    for i, (w, group) in enumerate(wallets):
        txs: list[D.Decoded] = []
        windows = 0
        try:
            for start in WINDOWS:
                end = min(start + DAY - 1, HARD_END - 1)
                txs += history(c, w, t_from=start, t_to=end, token_accounts="none", max_pages=1).txs
                windows += 1
        except RuntimeError as e:
            stopped = str(e)[:120]
            break
        assert all((d.block_time or 0) < HARD_END for d in txs)
        rows[w] = {"group": group, "windows": windows, **_measures(txs, w, known)}
        if i % 10 == 0:
            print(i, "net", c.net_calls, flush=True)
            (store / "rows.json").write_text(json.dumps(rows))
    (store / "rows.json").write_text(json.dumps(rows))
    print({"wallets_read": len(rows), "stopped": stopped, "net": c.net_calls})
    return 0


def verdict(r: dict[str, Any]) -> str:
    if not r["n_tx"]:
        return "no activity in the windows"
    n, share = r["distinct_other_signers"], r["known_operator_share_of_other_signers"]
    if share is not None and share >= 0.5:
        return "private to the operators"
    if n >= 100 and share is not None and share < 0.05 and (r["top_program_set_share"] or 0) >= 0.5:
        return "shared execution service"
    return "not separated"


MEASURES = ("share_signed", "distinct_other_signers", "top10_share_of_other_signers",
            "known_operator_share_of_other_signers", "distinct_program_sets", "top_program_set_share",
            "four_signer_sweep_share", "distinct_destinations", "top_destination_share")


def median(v: list[float]) -> Optional[float]:
    v = sorted(v)
    return (v[(len(v) - 1) // 2] + v[len(v) // 2]) / 2 if v else None


def analyse() -> int:
    store = storage.data_root() / "intermediate" / "cosigners"
    lst = json.loads((store / "list.json").read_text())
    rows = json.loads((store / "rows.json").read_text())
    co = [r for w, r in rows.items() if r["group"] == "cosigner"]
    ctl = [r for w, r in rows.items() if r["group"] == "control"]
    multi = [rows[w] for w, ops in lst["cosigners"].items() if len(ops) >= 2 and w in rows]
    rng = random.Random(SEED)
    tests: dict[str, Any] = {}
    alpha = 0.05 / len(MEASURES)
    for m in MEASURES:
        pairs = [(r["group"] == "cosigner", r[m]) for r in rows.values() if r.get(m) is not None]
        a = [v for g, v in pairs if g]
        b = [v for g, v in pairs if not g]
        obs = (median(a) or 0) - (median(b) or 0) if a and b else None
        p = None
        if obs is not None:
            vals = [v for _, v in pairs]
            hits = 0
            for _ in range(10000):
                rng.shuffle(vals)
                if abs((median(vals[:len(a)]) or 0) - (median(vals[len(a):]) or 0)) >= abs(obs):
                    hits += 1
            p = (1 + hits) / 10001
        tests[m] = {"median_cosigner": median(a), "median_control": median(b), "p_two_sided": p,
                    "below_bonferroni": p is not None and p < alpha}
    # do the signers of one co-signer also appear on another? a shared client base points to one platform
    counts: Counter[str] = Counter()
    for r in co:
        counts.update(r["other_signers"])
    res = {
        "n_cosigners_listed": len(lst["cosigners"]), "n_controls_listed": len(lst["controls"]), "wallets_read": len(rows),
        "n_multi_operator_cosigners_read": len(multi), "alpha_bonferroni": alpha, "measures": tests,
        "verdicts_all_cosigners": dict(Counter(verdict(r) for r in co)),
        "verdicts_multi_operator": dict(Counter(verdict(r) for r in multi)),
        "verdicts_controls": dict(Counter(verdict(r) for r in ctl)),
        "multi_operator_medians": {m: median([r[m] for r in multi if r.get(m) is not None]) for m in MEASURES},
        "other_signers_seen_with_two_or_more_cosigners": sum(1 for v in counts.values() if v >= 2),
        "other_signers_total": len(counts),
        "known_operator_signers_found": sum(r["n_known_operator_signers"] for r in co),
        "windows": WINDOWS, "tx_read": sum(r["n_tx"] for r in rows.values()),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=0))
    return 0


def main() -> int:
    cmd = sys.argv[1]
    if cmd == "list":
        c = client(500)
        lst = build_list(c)
        print({"cosigners": len(lst["cosigners"]), "multi_operator": sum(1 for v in lst["cosigners"].values() if len(v) >= 2),
               "controls": len(lst["controls"]), "hubs": lst["n_hubs"], "net": c.net_calls})
        return 0
    if cmd == "collect":
        return collect(int(sys.argv[2]))
    return analyse()


if __name__ == "__main__":
    sys.exit(main())
