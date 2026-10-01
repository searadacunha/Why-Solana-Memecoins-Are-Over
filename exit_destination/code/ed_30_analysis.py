#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sections B to J of analysis_plan.md on the frozen study table (derived/ed_table.json.gz): token exit paths, sale
proceeds, capital return H1-H6, recurrence, recycling, deployer linkage, hypotheses, nulls and robustness,
fingerprints. No price is read (an audit hook refuses any price file).

Writes tables/B_tokens.md, C_proceeds.md, D_return.md, E_recurrence.md, F_recycling.md, G_deployer.md,
H_hypotheses.md, I_robustness.md, J_fingerprint.md and derived/ED_results.json.
"""

from __future__ import annotations

import bisect
import datetime as dt
import gzip
import hashlib
import json
import os
import random
import statistics
import sys
from collections import Counter, defaultdict
from typing import Any, Callable, Optional


def _no_price(event: str, args: tuple[Any, ...]) -> None:
    if event == "open" and args and isinstance(args[0], str) and "em_price" in args[0]:
        raise RuntimeError("a price file was opened: %s" % args[0])


sys.addaudithook(_no_price)

import ed_lib as L  # noqa: E402
import ed_trace as T  # noqa: E402
import em_lib as E  # noqa: E402

TABLE = os.path.join(L.DERIVED, "ed_table.json.gz")
FREEZE = os.path.join(L.DERIVED, "ED_FREEZE.json")
OBSERVED = ("complete", "window end", "cap")
CATS = ("H1", "H2", "H3", "H4", "H5", "H6")
CAT_NAME = {
    "H1": "H1 launch funder",
    "H2": "H2 same cluster",
    "H3": "H3 deployer network",
    "H4": "H4 known wallet, other cluster",
    "H5": "H5 hub",
    "H6": "H6 unresolved",
}
N_MIN = 20


# ------------------------------------------------------------------ loading --- #
def load() -> dict[str, Any]:
    fz = json.load(open(FREEZE))
    if hashlib.sha256(open(TABLE, "rb").read()).hexdigest() != fz["sha256_table"]:
        sys.exit("the study table differs from the frozen one")
    return json.load(gzip.open(TABLE))


def week(bt: float) -> str:
    y, w, _ = dt.datetime.fromtimestamp(bt, dt.timezone.utc).isocalendar()
    return "%d-W%02d" % (y, w)


class Data:
    def __init__(self) -> None:
        self.rows = sorted(E.load(), key=lambda z: z["t"])
        self.byrow = {r["mint"]: r for r in self.rows}
        self.R = T.Roles(self.rows)
        self.tab = load()
        sel = json.load(open(L.SELECTION))
        self.sel = sel
        self.meta = {(e["wallet"], e["mint"]): e for e in sel["events"]}
        self.corpus_events = Counter(e["wallet"] for e in sel["events"])
        br: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for b in self.tab["branches"]:
            b["hop"] = len(b["path"]) - 1
            b["sol"] = b["path"][1]["sol"]
            b["bt"] = b["path"][1]["bt"]
            br[(b["wallet"], b["mint"])].append(b)
        self.events: list[dict[str, Any]] = []
        for w in self.tab["wallets"]:
            for tr in w["events"]:
                self.events.append(self.event(tr, br.get((tr["wallet"], tr["mint"]), [])))
        self.obs = [e for e in self.events if e["observed"]]
        self.funding = self._funding_index()
        self.funding_t = {w: [x[0] for x in v] for w, v in self.funding.items()}

    def depnet(self, mint: str) -> set[str]:
        cr = self.byrow[mint]["creator"]
        out = {cr.get("wallet")}
        for k in ("gen_funder", "last_funder"):
            if cr.get(k) and cr.get(k + "_hub") is not True:
                out.add(cr[k])
        return out - {None}

    def event(self, tr: dict[str, Any], branches: list[dict[str, Any]]) -> dict[str, Any]:
        m = self.meta[(tr["wallet"], tr["mint"])]
        e: dict[str, Any] = {
            k: m[k]
            for k in (
                "wallet",
                "mint",
                "split",
                "cluster",
                "em_cluster",
                "t",
                "receipt",
                "snipers",
                "funders",
                "tokens",
            )
        }
        e["status"] = str(tr.get("status"))
        e["observed"] = e["status"] in OBSERVED
        e["week"] = week(m["receipt"]["bt"])
        reads = [f for f in tr.get("reads", []) if not f["err"]]
        e["reads"] = reads
        mint = e["mint"]
        sold = transferred = other = 0.0
        rec: list[tuple[str, float]] = []
        first_act = first_sale = None
        proceeds = 0.0
        outs = []
        sale_seen = False
        for f in reads:
            d = f["dtok"].get(mint, 0.0)
            if d < 0:
                first_act = first_act if first_act is not None else f["bt"] - m["receipt"]["bt"]
                if T.is_sale(f, mint):
                    sold += -d
                    proceeds += max(0.0, f["dsol"] + f["dws"] + sum(v for _, v in f["out"]))
                    first_sale = first_sale if first_sale is not None else f["bt"] - m["receipt"]["bt"]
                    sale_seen = True
                elif f["tok_to"].get(mint):
                    transferred += -d
                    rec += list(f["tok_to"][mint].items())
                else:
                    other += -d
            for dst, v in f["out"]:
                if v >= L.MIN_SOL:
                    outs.append(
                        {
                            "to": dst,
                            "sol": v,
                            "bt": f["bt"],
                            "after_sale": sale_seen,
                            "pooled": f["pooled"],
                            "signer_is_wallet": f["signer"] == e["wallet"],
                            "signers": f.get("signers"),
                        }
                    )
        held = max(0.0, tr.get("held_end", 0.0) or 0.0)
        base = sold + transferred + other + held
        e.update(
            {
                "sold": sold,
                "transferred": transferred,
                "other": other,
                "held": held,
                "base": base,
                "first_action_s": first_act,
                "first_sale_s": first_sale,
                "proceeds": proceeds,
                "outs": outs,
                "tok_recipients": rec,
            }
        )
        if not e["observed"]:
            disp = "untraceable (not read: %s)" % e["status"].split(":")[0]
        elif base <= 0:
            disp = "untraceable (no balance seen)"
        elif sold / base >= 0.99:
            disp = "sold"
        elif transferred / base >= 0.99:
            disp = "transferred"
        elif other / base >= 0.99:
            disp = "other contract"
        elif held / base >= 0.99:
            disp = "untraceable (cap reached, tokens left)" if e["status"] == "cap" else "held at window end"
        else:
            disp = "mixed"
        e["disposal"] = disp
        e["branches"] = branches
        main = max(branches, key=lambda b: (b["sol"], -b["bt"]), default=None)
        e["main"] = main
        e["any"] = {b["terminal"] for b in branches}
        e["first_dest"] = main["path"][1]["wallet"] if main else None
        e["terminal_wallet"] = main["path"][-1]["wallet"] if main and main["terminal"] != "H6" else None
        e["return_cat"] = main["terminal"] if main else ("A stays" if e["observed"] and e["status"] != "cap" else None)
        return e

    def _funding_index(self) -> dict[str, list[tuple[float, str, str]]]:
        idx: dict[str, list[tuple[float, str, str]]] = defaultdict(list)
        for r in self.rows:
            for s in r["snipers"]:
                if s.get("last_funder") and s.get("last_bt"):
                    idx[s["last_funder"]].append((s["last_bt"], r["mint"], "sniper"))
            cr = r["creator"]
            if cr.get("last_funder") and cr.get("last_bt"):
                idx[cr["last_funder"]].append((cr["last_bt"], r["mint"], "deployer"))
        for v in idx.values():
            v.sort()
        return idx


# ------------------------------------------------------------------ helpers --- #
def pct(a: float, b: float) -> str:
    return "%.0f %%" % (100 * a / b) if b else "n/a"


def fmt(d: dict[str, Any]) -> str:
    if not d:
        return "n/a"
    return "%.3g | %.3g [%.3g, %.3g] | %.0f %% | %.4f | %s" % (
        d["obs"],
        d["null_mean"],
        d["ci"][0],
        d["ci"][1],
        100 * d["pct"],
        d["p"],
        "n/a" if d["effect"] is None else "x%.2f" % d["effect"],
    )


def null_test(obs_fn: Callable[[random.Random | None], float], n: int = L.N_PERM) -> dict[str, Any]:
    rng = random.Random(L.SEED)
    return E.perm_test(obs_fn(None), [obs_fn(rng) for _ in range(n)])


def write(name: str, lines: list[str]) -> None:
    os.makedirs(L.TABLES, exist_ok=True)
    with open(os.path.join(L.TABLES, name), "w", encoding="utf8") as fh:
        fh.write("\n".join(lines) + "\n")


def dist(v: list[float], f: str = "%.3g") -> str:
    return E.dist(v, f)


# --------------------------------------------------------------- statistics --- #
def same_share(
    events: list[dict[str, Any]],
    attr: Callable[[dict[str, Any]], Any],
    rng: Optional[random.Random],
    setlike: bool = False,
) -> float:
    """Share of exit wallets (2+ events with the attribute) whose events all share it; with rng, the attribute
    values permuted among those events (each wallet keeps its number of events)."""
    vals = [(e["wallet"], attr(e)) for e in events]
    vals = [(w, v) for w, v in vals if v]
    if rng is not None:
        perm = E.shuffled(rng, [v for _, v in vals])
        vals = [(w, p) for (w, _), p in zip(vals, perm)]
    by: dict[str, list[Any]] = defaultdict(list)
    for w, v in vals:
        by[w].append(v)
    m = [v for v in by.values() if len(v) >= 2]
    if not m:
        return 0.0
    if setlike:
        return sum(1 for v in m if set.intersection(*[set(x) for x in v])) / len(m)
    return sum(1 for v in m if len(set(v)) == 1) / len(m)


def h1_any(events: list[dict[str, Any]], rng: Optional[random.Random]) -> float:
    """Share of events with a branch whose path reaches a funder of the launch; with rng, the launch funders are
    permuted among the events (null 2)."""
    ev = [e for e in events if e["branches"]]
    if not ev:
        return 0.0
    fs = [set(e["funders"]) for e in ev]
    if rng is not None:
        fs = E.shuffled(rng, fs)
    n = 0
    for e, f in zip(ev, fs):
        n += any(p["wallet"] in f for b in e["branches"] for p in b["path"][1:])
    return n / len(ev)


def first_dest_repeat(events: list[dict[str, Any]], rng: Optional[random.Random]) -> float:
    """Null 1: share of exit wallets (2+ events with a first destination) with a destination repeated."""
    vals = [(e["wallet"], e["first_dest"]) for e in events if e["first_dest"]]
    if rng is not None:
        perm = E.shuffled(rng, [v for _, v in vals])
        vals = [(w, p) for (w, _), p in zip(vals, perm)]
    by: dict[str, list[str]] = defaultdict(list)
    for w, v in vals:
        by[w].append(v)
    m = [v for v in by.values() if len(v) >= 2]
    return sum(1 for v in m if max(Counter(v).values()) >= 2) / len(m) if m else 0.0


def terminal_rate(D: Data, events: list[dict[str, Any]], cat: str, rng: Optional[random.Random]) -> float:
    """Null 4: share of branches ending in `cat`; with rng, the last wallet of each branch is exchanged among
    branches of the same hop depth and classified again (amounts and depths kept)."""
    br = [b for e in events for b in e["branches"]]
    if not br:
        return 0.0
    if rng is None:
        return sum(1 for b in br if b["terminal"] == cat) / len(br)
    evk = {(e["wallet"], e["mint"]): e for e in events}
    by: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for b in br:
        by[b["hop"]].append(b)
    n = 0
    for bs in by.values():
        lasts = E.shuffled(rng, [b["path"][-1]["wallet"] for b in bs])
        for b, w in zip(bs, lasts):
            c = D.R.classify(w, b["path"][-1]["bt"] or 0, evk[(b["wallet"], b["mint"])]) or "H6"
            n += c == cat
    return n / len(br)


def deployer_link(D: Data, events: list[dict[str, Any]], rng: Optional[random.Random]) -> float:
    """Share of events with a branch whose path touches the deployer network of its cluster (non-hub wallets,
    visible by then); with rng, the network of another multi-launch cluster drawn at random."""
    ev = [e for e in events if e["branches"]]
    if not ev:
        return 0.0
    multi = sorted(c for c, net in D.R.dep_net.items() if len(net) >= 2)
    n = 0
    for e in ev:
        c = e["em_cluster"]
        if rng is not None:
            others = [x for x in multi if x != c]
            c = others[rng.randrange(len(others))]
        net = D.R.dep_net[c]
        n += any(
            net.get(p["wallet"], 1e18) <= (p["bt"] or 0) and not D.R.hub.get(p["wallet"])
            for b in e["branches"]
            for p in b["path"][1:]
        )
    return n / len(ev)


def recycling(
    D: Data, e: dict[str, Any], b: dict[str, Any], wallets: Optional[list[str]] = None, light: bool = False
) -> Optional[dict[str, Any]]:
    """The first later launch B funded (sniper or deployer) by a wallet of the branch's path after the flow."""
    best = None
    path = b["path"][1:]
    ws = wallets if wallets is not None else [p["wallet"] for p in path]
    for p, w in zip(path, ws):
        v = D.funding.get(w)
        if not v:
            continue
        k = bisect.bisect_right(D.funding_t[w], p["bt"] or 0)
        for t, mint, role in v[k:]:
            if mint == e["mint"] or D.byrow[mint]["t_create"] <= e["t"]:
                continue
            if best is None or t < best["t_fund"]:
                best = {"wallet": w, "t_fund": t, "mint": mint, "role": role}
            break
    if best is None or light:
        return best
    rb = D.byrow[best["mint"]]
    sn_b = {s["wallet"] for s in rb["snipers"]}
    rec_b = {o for s in rb["snipers"] for x in s["exits_full"] if x["kind"] == "transfer" for o in x["recipients"]}
    best.update(
        {
            "dt_s": rb["t"] - e["t"],
            "sol": b["sol"],
            "same_funder": bool({E.fkey(s) for s in rb["snipers"]} & set(e["funders"])),
            "same_snipers": bool(sn_b & set(e["snipers"])),
            "same_exit_wallet": e["wallet"] in rec_b,
            "same_cluster": D.R.cl[best["mint"]] == e["em_cluster"],
            "same_deployer_network": bool(D.depnet(best["mint"]) & D.depnet(e["mint"])),
        }
    )
    return best


def recycle_rate(D: Data, events: list[dict[str, Any]], rng: Optional[random.Random]) -> float:
    ev = [e for e in events if e["branches"]]
    if not ev:
        return 0.0
    if rng is None:
        return sum(1 for e in ev if any(recycling(D, e, b, light=True) for b in e["branches"])) / len(ev)
    br = [(e, b) for e in ev for b in e["branches"]]
    by: dict[int, list[int]] = defaultdict(list)
    for i, (_, b) in enumerate(br):
        by[b["hop"]].append(i)
    paths: dict[int, list[str]] = {}
    for idx in by.values():
        perm = E.shuffled(rng, idx)
        for i, j in zip(idx, perm):
            paths[i] = [p["wallet"] for p in br[j][1]["path"][1:]]
    hit: set[tuple[str, str]] = set()
    for i, (e, b) in enumerate(br):
        if recycling(D, e, b, paths[i], light=True):
            hit.add((e["wallet"], e["mint"]))
    return len(hit) / len(ev)


def exit_pairs(D: Data, wallets: set[str], rng: Optional[random.Random]) -> float:
    """Null 3: share of the exit wallets always fed by the same sniper, all their corpus events (frozen)."""
    ev = [(e["wallet"], s) for e in D.sel["events"] if e["wallet"] in wallets for s in e["snipers"]]
    if rng is not None:
        sn = E.shuffled(rng, [s for _, s in ev])
        ev = [(w, s) for (w, _), s in zip(ev, sn)]
    by: dict[str, set[str]] = defaultdict(set)
    for w, s in ev:
        by[w].add(s)
    return sum(1 for v in by.values() if len(v) == 1) / len(by) if by else 0.0


def cross_launch(D: Data, wallets: set[str]) -> dict[str, Any]:
    """Null 5: exit-wallet pairs together in two launches or more, against degree-preserving rewiring."""
    g: dict[str, list[str]] = defaultdict(list)
    for e in D.sel["events"]:
        if e["wallet"] in wallets:
            g[e["mint"]].append(e["wallet"])
    return E.null_pairs([sorted(v) for v in g.values()], L.N_PERM)


# --------------------------------------------------------------- subsets ------ #
def subsets(D: Data) -> list[tuple[str, list[dict[str, Any]]]]:
    obs = D.obs
    top_op = Counter(e["cluster"] for e in obs).most_common(1)[0][0]
    top10 = {w for w, _ in sorted(D.corpus_events.items(), key=lambda x: (-x[1], x[0]))[:10]}

    def strip(events: list[dict[str, Any]], keep: Callable[[dict[str, Any]], bool]) -> list[dict[str, Any]]:
        return [{**e, "branches": [b for b in e["branches"] if keep(b)]} for e in events]

    def through_hub(b: dict[str, Any]) -> bool:
        return b["terminal"] == "H5" or any(m.get("hub") for m in b["measured"].values())

    def strict_ok(b: dict[str, Any]) -> bool:
        if through_hub(b):
            return False
        last = b["path"][-1]["wallet"]
        if b["terminal"] in ("H1", "H2", "H3", "H4") and D.R.hub.get(last) is not False:
            return False
        return all(m.get("status") == "read" for m in b["measured"].values())

    out = [
        ("full", obs),
        ("without the dominant operator", [e for e in obs if e["cluster"] != top_op]),
        ("without the 10 most frequent exit wallets", [e for e in obs if e["wallet"] not in top10]),
        ("known non-hub", strip(obs, lambda b: not through_hub(b))),
        ("strict non-hub", strip(obs, strict_ok)),
        ("TRAIN", [e for e in obs if e["split"] == "train"]),
        ("VALIDATION", [e for e in obs if e["split"] == "val"]),
    ]
    ops = Counter(e["cluster"] for e in obs)
    for op, n in sorted(ops.items(), key=lambda x: (-x[1], x[0])):
        if n >= 30:
            out.append(("operator %s (%d events)" % (op[:14], n), [e for e in obs if e["cluster"] == op]))
    return out


def core_tests(D: Data, ev: list[dict[str, Any]], n_perm: int = L.N_PERM) -> dict[str, dict[str, Any]]:
    wallets = {e["wallet"] for e in ev}

    def t(fn: Callable[[Optional[random.Random]], float]) -> dict[str, Any]:
        return null_test(fn, n_perm)

    res = {
        "capital reaches the launch funder (events)": t(lambda r: h1_any(ev, r)),
        "same first SOL destination repeated (exit wallets)": t(lambda r: first_dest_repeat(ev, r)),
        "same terminal wallet in all events (exit wallets)": t(
            lambda r: same_share(ev, lambda e: e["terminal_wallet"], r)
        ),
        "same return category in all events (exit wallets)": t(lambda r: same_share(ev, lambda e: e["return_cat"], r)),
        "same funder in all events (exit wallets)": t(
            lambda r: same_share(ev, lambda e: tuple(e["funders"]), r, setlike=True)
        ),
        "same cluster in all events (exit wallets)": t(lambda r: same_share(ev, lambda e: e["em_cluster"], r)),
        "capital reaches the cluster's deployer network (events)": t(lambda r: deployer_link(D, ev, r)),
        "capital funds a later launch (events)": t(lambda r: recycle_rate(D, ev, r)),
        "fixed sniper-to-exit-wallet pairs (exit wallets, corpus)": t(lambda r: exit_pairs(D, wallets, r)),
    }
    for c in ("H1", "H2", "H3"):
        res["branches ending in %s" % c] = t(lambda r, c=c: terminal_rate(D, ev, c, r))
    res["n_events"] = {"obs": len(ev), "with_branch": sum(1 for e in ev if e["branches"])}
    return res


# --------------------------------------------------------------- sections ----- #
def section_b(D: Data) -> dict[str, Any]:
    ev = D.events
    lines = [
        "# B. Token exit paths: sniper -> exit wallet -> token",
        "",
        "Sampled events %d; read %d (complete %d, window end %d, cap %d); not read %d."
        % (
            len(ev),
            len(D.obs),
            sum(e["status"] == "complete" for e in ev),
            sum(e["status"] == "window end" for e in ev),
            sum(e["status"] == "cap" for e in ev),
            len(ev) - len(D.obs),
        ),
        "",
        "| disposal of the token by the exit wallet | TRAIN | VALIDATION | all | launches | exit wallets |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    c = Counter(e["disposal"] for e in ev)
    out: dict[str, Any] = {"disposal": {}}
    for k, n in c.most_common():
        sub = [e for e in ev if e["disposal"] == k]
        tr = sum(e["split"] == "train" for e in sub)
        va = len(sub) - tr
        lines.append(
            "| %s | %d | %d | %d (%s) | %d | %d |"
            % (k, tr, va, n, pct(n, len(ev)), len({e["mint"] for e in sub}), len({e["wallet"] for e in sub}))
        )
        out["disposal"][k] = n
    obs = [e for e in D.obs if e["base"] > 0]
    tot = {k: sum(e[k] for e in obs) for k in ("sold", "transferred", "other", "held")}
    base = sum(tot.values())
    lines += [
        "",
        "Token amounts over the read events: sold %s, transferred %s, other contracts %s, left at the end "
        "of the reading %s." % tuple(pct(tot[k], base) for k in ("sold", "transferred", "other", "held")),
        "",
    ]
    fa = [e["first_action_s"] for e in D.obs if e["first_action_s"] is not None]
    fs = [e["first_sale_s"] for e in D.obs if e["first_sale_s"] is not None]
    lines += [
        "Delay from the sniper's transfer to the exit wallet's first move of the token (s), median / p25 / p75 / "
        "p90 / min / max: %s" % dist(fa),
        "",
        "Delay to the first sale (s): %s" % dist(fs),
        "",
    ]
    multi = [e for e in D.obs if len(e["snipers"]) >= 2]
    lines.append(
        "Events where two snipers or more sent the same token to the same exit wallet: %d of %d (%s)."
        % (len(multi), len(D.obs), pct(len(multi), len(D.obs)))
    )
    rc = Counter()
    for e in D.obs:
        for o, _ in e["tok_recipients"]:
            rc[D.R.proceeds_cat(o, e["receipt"]["bt"] + 1, e).replace("H unknown", "unknown wallet")] += 1
    lines += [
        "",
        "Recipients of tokens transferred onward by the exit wallet (transfers): "
        + (", ".join("%s %d" % kv for kv in rc.most_common()) or "none"),
        "",
    ]
    sig_w = Counter(o["signer_is_wallet"] for e in D.obs for o in e["outs"])
    lines.append(
        "Outgoing SOL transfers of 0.1 SOL or more signed (fee paid) by the exit wallet itself: %d of %d."
        % (sig_w[True], sum(sig_w.values()))
    )
    payers = Counter(o["signers"][0] for e in D.obs for o in e["outs"] if not o["signer_is_wallet"] and o["signers"])
    lines.append(
        "Distinct fee payers of the others: %d; the largest pays for %s transfers."
        % (len(payers), payers.most_common(1)[0][1] if payers else 0)
    )
    write("B_tokens.md", lines)
    out.update(
        {
            "amount_shares": {k: tot[k] / base for k in tot} if base else {},
            "first_action_s_median": statistics.median(fa) if fa else None,
            "first_sale_s_median": statistics.median(fs) if fs else None,
            "multi_sniper_events": len(multi),
            "own_signed_transfers": sig_w[True],
            "transfers": sum(sig_w.values()),
            "fee_payers": len(payers),
            "top_fee_payer_share": (payers.most_common(1)[0][1] / sum(payers.values())) if payers else None,
        }
    )
    return out


def proceeds_category(D: Data, e: dict[str, Any]) -> Optional[tuple[str, float]]:
    if not e["proceeds"] or e["first_sale_s"] is None:
        return None
    outs = [o for o in e["outs"] if o["after_sale"]]
    if not outs:
        return ("H untraceable (cap)" if e["status"] == "cap" else "A remains on the exit wallet"), e["proceeds"]
    cats = {D.R.proceeds_cat(o["to"], o["bt"], e) for o in outs}
    sol = sum(o["sol"] for o in outs)
    if len(cats) >= 2:
        return "G split", sol
    c = cats.pop()
    return ("H unknown recipient (followed in D)" if c.startswith("H") else c), sol


def section_c(D: Data) -> dict[str, Any]:
    rows = [(e, proceeds_category(D, e)) for e in D.obs]
    rows = [(e, c) for e, c in rows if c]
    lines = [
        "# C. Sale proceeds: exit wallet -> SOL destination (direct, after its first sale)",
        "",
        "Events with a sale by the exit wallet: %d of %d read." % (len(rows), len(D.obs)),
        "",
        "| category | count | % | SOL | TRAIN | VALIDATION | launches | exit wallets |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    c = Counter(cat for _, (cat, _) in rows)
    out = {}
    for k in sorted(c):
        sub = [(e, s) for e, (cat, s) in rows if cat == k]
        lines.append(
            "| %s | %d | %s | %.1f | %d | %d | %d | %d |"
            % (
                k,
                len(sub),
                pct(len(sub), len(rows)),
                sum(s for _, s in sub),
                sum(e["split"] == "train" for e, _ in sub),
                sum(e["split"] == "val" for e, _ in sub),
                len({e["mint"] for e, _ in sub}),
                len({e["wallet"] for e, _ in sub}),
            )
        )
        out[k] = {"n": len(sub), "sol": sum(s for _, s in sub)}
    pooled = sum(1 for e in D.obs for o in e["outs"] if o["pooled"])
    lines += [
        "",
        "Proceeds of the sales (SOL received by the exit wallet): %s." % dist([e["proceeds"] for e, _ in rows]),
        "Outgoing transfers made after the wallet's next receipt (proceeds of two launches possibly mixed, "
        "flagged pooled): %d." % pooled,
    ]
    write("C_proceeds.md", lines)
    return {"n_sale_events": len(rows), "categories": out, "pooled_transfers": pooled}


def section_d(D: Data) -> dict[str, Any]:
    br = [b for e in D.obs for b in e["branches"]]
    tot_sol = sum(b["sol"] for b in br)
    lines = [
        "# D. Capital return: every outgoing SOL transfer (0.1 SOL or more) of the exit wallet, followed",
        "",
        "Read events %d; with at least one outgoing transfer %d; branches %d carrying %.1f SOL."
        % (len(D.obs), sum(1 for e in D.obs if e["branches"]), len(br), tot_sol),
        "",
        "| first terminal | branches | % | SOL | % SOL | direct (hop 1) | multi-hop | events with one | "
        "launches | exit wallets |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    out: dict[str, Any] = {"branches": len(br), "sol": tot_sol, "cats": {}}
    for c in CATS:
        sub = [b for b in br if b["terminal"] == c]
        evs = [e for e in D.obs if c in e["any"]]
        sol = sum(b["sol"] for b in sub)
        lines.append(
            "| %s | %d | %s | %.1f | %s | %d | %d | %d (%s) | %d | %d |"
            % (
                CAT_NAME[c],
                len(sub),
                pct(len(sub), len(br)),
                sol,
                pct(sol, tot_sol),
                sum(1 for b in sub if b["hop"] == 1),
                sum(1 for b in sub if b["hop"] >= 2),
                len(evs),
                pct(len(evs), sum(1 for e in D.obs if e["branches"])),
                len({e["mint"] for e in evs}),
                len({e["wallet"] for e in evs}),
            )
        )
        out["cats"][c] = {
            "branches": len(sub),
            "sol": sol,
            "direct": sum(1 for b in sub if b["hop"] == 1),
            "multi": sum(1 for b in sub if b["hop"] >= 2),
            "events": len(evs),
        }
    stays = [e for e in D.obs if not e["branches"]]
    lines += [
        "",
        "Read events with no outgoing transfer of 0.1 SOL or more in the window (capital stays on the exit "
        "wallet, or left before the reading stopped): %d." % len(stays),
        "",
        "Unresolved branches by reason: "
        + ", ".join("%s %d" % kv for kv in Counter(b["reason"] for b in br if b["terminal"] == "H6").most_common()),
        "",
        "Hops to the first terminal: "
        + ", ".join("%d: %d" % kv for kv in sorted(Counter(b["hop"] for b in br).items())),
        "",
    ]
    for sp, name in (("train", "TRAIN"), ("val", "VALIDATION")):
        sb = [b for e in D.obs if e["split"] == sp for b in e["branches"]]
        lines.append(
            "%s: " % name
            + ", ".join("%s %s" % (c, pct(sum(1 for b in sb if b["terminal"] == c), len(sb))) for c in CATS)
        )
    after = [b for b in br if b["after_sale"]]
    lines += [
        "",
        "Branches leaving after the exit wallet's first sale: %d; their terminals: %s."
        % (
            len(after),
            ", ".join("%s %s" % (c, pct(sum(1 for b in after if b["terminal"] == c), len(after))) for c in CATS),
        ),
    ]
    sides = Counter(s["class"] or "unknown" for b in br for s in b["side"])
    lines.append(
        "Smaller outgoing transfers of intermediate wallets (recorded, not followed): "
        + (", ".join("%s %d" % kv for kv in sides.most_common()) or "none")
    )
    write("D_return.md", lines)
    out["stays"] = len(stays)
    out["reasons_h6"] = dict(Counter(b["reason"] for b in br if b["terminal"] == "H6"))
    return out


def section_e(D: Data) -> dict[str, Any]:
    ev = D.obs
    rel: list[tuple[str, Callable[[Optional[random.Random]], float]]] = [
        (
            "sniper -> same exit wallet (always the same sniper, corpus)",
            lambda r: exit_pairs(D, {e["wallet"] for e in ev}, r),
        ),
        ("exit -> same funder", lambda r: same_share(ev, lambda e: tuple(e["funders"]), r, setlike=True)),
        ("exit -> same cluster", lambda r: same_share(ev, lambda e: e["em_cluster"], r)),
        (
            "exit -> same deployer network",
            lambda r: same_share(ev, lambda e: tuple(sorted(D.depnet(e["mint"]))), r, setlike=True),
        ),
        ("exit -> same first SOL destination", lambda r: same_share(ev, lambda e: e["first_dest"], r)),
        ("exit -> same collection (terminal) wallet", lambda r: same_share(ev, lambda e: e["terminal_wallet"], r)),
        (
            "exit -> same hub",
            lambda r: same_share(ev, lambda e: e["terminal_wallet"] if e["return_cat"] == "H5" else None, r),
        ),
        (
            "exit -> same destination architecture (return category)",
            lambda r: same_share(ev, lambda e: e["return_cat"], r),
        ),
    ]
    lines = [
        "# E. Exit-wallet recurrence (exit wallets with two read events or more)",
        "",
        "Share of exit wallets whose events all share the relation (sets: a common element). Null: the "
        "relation's values permuted among events, each wallet keeping its number of events (null 1 for "
        "destinations, 2 for funders, 3 for sniper pairs); %d permutations." % L.N_PERM,
        "",
        "| relationship | observed | null mean [95 %] | percentile | p | ratio |",
        "|---|---:|---|---:|---:|---:|",
    ]
    out = {}
    for name, fn in rel:
        t = null_test(fn)
        out[name] = t
        lines.append(
            "| %s | %.3f | %.3f [%.3f, %.3f] | %.0f %% | %.4f | %s |"
            % (
                name,
                t["obs"],
                t["null_mean"],
                t["ci"][0],
                t["ci"][1],
                100 * t["pct"],
                t["p"],
                "x%.2f" % t["effect"] if t["effect"] else "n/a",
            )
        )
    t5 = cross_launch(D, {e["wallet"] for e in ev})
    out["cross-launch co-occurrence (null 5)"] = t5
    lines += [
        "",
        "Null 5, exit-wallet pairs together in two launches or more (corpus events of the sample, "
        "degree-preserving rewiring): %s" % fmt(t5),
        "",
        "Same first destination repeated at least once (null 1): %s"
        % fmt(null_test(lambda r: first_dest_repeat(ev, r))),
    ]
    write("E_recurrence.md", lines)
    return out


def section_f(D: Data) -> dict[str, Any]:
    links = []
    for e in D.obs:
        best = None
        for b in e["branches"]:
            r = recycling(D, e, b)
            if r and (best is None or r["t_fund"] < best["t_fund"]):
                best = r
        if best:
            links.append((e, best))
    ev_b = [e for e in D.obs if e["branches"]]
    lines = [
        "# F. Capital recycling: launch A -> exit wallet -> path -> funding -> launch B",
        "",
        "Events whose outgoing capital reaches a wallet that later funds a sniper or the deployer of another "
        "launch: %d of %d events with a branch (%s)." % (len(links), len(ev_b), pct(len(links), len(ev_b))),
        "",
    ]
    if links:
        lines += [
            "Time from launch A to launch B (min): %s" % dist([r["dt_s"] / 60 for _, r in links]),
            "SOL on the branch: %s" % dist([r["sol"] for _, r in links]),
            "Funding role in B: " + ", ".join("%s %d" % kv for kv in Counter(r["role"] for _, r in links).items()),
            "",
        ]
        for k in ("same_funder", "same_snipers", "same_exit_wallet", "same_cluster", "same_deployer_network"):
            lines.append(
                "- B has the %s: %d (%s)"
                % (
                    k.replace("same_", "same ").replace("_", " "),
                    sum(r[k] for _, r in links),
                    pct(sum(r[k] for _, r in links), len(links)),
                )
            )
    g: dict[str, str] = {}
    for e, r in links:
        g[e["mint"]] = r["mint"]
    chains = []
    starts = set(g) - set(g.values())
    for s in sorted(starts):
        n, cur, seen = 1, s, {s}
        while cur in g and g[cur] not in seen:
            cur = g[cur]
            seen.add(cur)
            n += 1
        chains.append(n)
    lines += [
        "",
        "Longitudinal chains among the sampled launches (A -> B -> C ...), launches per chain: %s"
        % (", ".join("%d: %d" % kv for kv in sorted(Counter(chains).items())) or "none"),
    ]
    tt = null_test(lambda r: recycle_rate(D, D.obs, r))
    lines += ["", "Null 4 (path wallets exchanged among branches of the same depth): %s" % fmt(tt)]
    ex = sorted(links, key=lambda x: (x[0]["t"], x[0]["wallet"]))[:5]
    lines += ["", "Examples (first five in time):", ""]
    for e, r in ex:
        lines.append(
            "- %s launch %s -> exit wallet %s -> %s (%s in B) -> launch %s, %.0f min later; same funder %s, "
            "same cluster %s"
            % (
                e["split"].upper(),
                e["mint"][:8],
                e["wallet"][:8],
                r["wallet"][:8],
                r["role"],
                r["mint"][:8],
                r["dt_s"] / 60,
                r["same_funder"],
                r["same_cluster"],
            )
        )
    write("F_recycling.md", lines)
    return {
        "links": len(links),
        "events_with_branch": len(ev_b),
        "null": tt,
        "chains": dict(Counter(chains)),
        "same": {
            k: sum(r[k] for _, r in links)
            for k in ("same_funder", "same_snipers", "same_exit_wallet", "same_cluster", "same_deployer_network")
        },
        "dt_min_median": statistics.median([r["dt_s"] / 60 for _, r in links]) if links else None,
    }


def section_g(D: Data) -> dict[str, Any]:
    ev_b = [e for e in D.obs if e["branches"]]
    h3 = [b for e in ev_b for b in e["branches"] if b["terminal"] == "H3"]
    strict = [b for b in h3 if D.R.hub.get(b["path"][-1]["wallet"]) is False]
    lines = [
        "# G. Deployer linkage (strict non-hub)",
        "",
        "| | branches | events |",
        "|---|---:|---:|",
        "| direct (hop 1) to the deployer network | %d | %d |"
        % (sum(1 for b in h3 if b["hop"] == 1), len({(b["wallet"], b["mint"]) for b in h3 if b["hop"] == 1})),
        "| indirect (hops 2-5) | %d | %d |"
        % (sum(1 for b in h3 if b["hop"] >= 2), len({(b["wallet"], b["mint"]) for b in h3 if b["hop"] >= 2})),
        "| of which the terminal wallet has a measured non-hub status | %d | %d |"
        % (len(strict), len({(b["wallet"], b["mint"]) for b in strict})),
        "| unresolved branches (H6) | %d | %d |"
        % (
            sum(1 for e in ev_b for b in e["branches"] if b["terminal"] == "H6"),
            sum(1 for e in ev_b if e["any"] == {"H6"}),
        ),
        "",
    ]
    tests = {}
    for name, sub in (
        ("all", ev_b),
        ("TRAIN", [e for e in ev_b if e["split"] == "train"]),
        ("VALIDATION", [e for e in ev_b if e["split"] == "val"]),
    ):
        tests[name] = null_test(lambda r, sub=sub: deployer_link(D, sub, r))
        lines.append(
            "Path touches the cluster's deployer network, %s (null: another multi-launch cluster's "
            "network): %s" % (name, fmt(tests[name]))
        )
    roles = Counter()
    for b in h3:
        w = b["path"][-1]["wallet"]
        roles["deployer" if w in D.R.deployers else "deployer funder"] += 1
    lines += ["", "Terminal wallets of H3: " + (", ".join("%s %d" % kv for kv in roles.items()) or "none")]
    write("G_deployer.md", lines)
    return {"h3_branches": len(h3), "strict": len(strict), "tests": tests, "roles": dict(roles)}


def classify_mech(res: dict[str, dict[str, dict[str, Any]]], name: str) -> str:
    def p(sub: str) -> Optional[float]:
        t = res.get(sub, {}).get(name)
        return t["p"] if t and "p" in t else None

    tr, va = p("TRAIN"), p("VALIDATION")
    n_tr = res.get("TRAIN", {}).get("n_events", {}).get("with_branch", 0)
    n_va = res.get("VALIDATION", {}).get("n_events", {}).get("with_branch", 0)
    if tr is None or va is None or min(n_tr, n_va) < N_MIN:
        return "INSUFFICIENT DATA"
    if tr < 0.01 and va < 0.01:
        rob = [p("without the dominant operator"), p("without the 10 most frequent exit wallets")]
        if all(x is not None and x < 0.01 for x in rob):
            return "ROBUST STRUCTURAL EVIDENCE"
        return "PROBABLE STRUCTURAL EVIDENCE"
    if tr < 0.05 and va < 0.05:
        return "PROBABLE STRUCTURAL EVIDENCE"
    return "NULL-COMPATIBLE"


def section_i(D: Data) -> dict[str, Any]:
    res = {}
    for name, ev in subsets(D):
        res[name] = core_tests(D, ev)
    names = [k for k in res["full"] if k != "n_events"]
    lines = [
        "# I. Robustness and nulls (%d permutations)" % L.N_PERM,
        "",
        "Each cell: observed | null mean [95 %] | percentile | p | effect.",
        "",
    ]
    for name in names:
        lines += ["## %s" % name, "", "| subset | events (with a branch) | test |", "|---|---:|---|"]
        for sub, r in res.items():
            lines.append(
                "| %s | %d (%d) | %s |" % (sub, r["n_events"]["obs"], r["n_events"]["with_branch"], fmt(r[name]))
            )
        lines += ["", "Classification: **%s**" % classify_mech(res, name), ""]
    wk = sorted({e["week"] for e in D.obs})
    lines += [
        "## Time (ISO weeks of the receipt)",
        "",
        "| week | events | with a branch | reaches the funder | same cluster or funder (H1+H2 branches) | "
        "deployer network | funds a later launch |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for w in wk:
        ev = [e for e in D.obs if e["week"] == w]
        eb = [e for e in ev if e["branches"]]
        br = [b for e in eb for b in e["branches"]]
        lines.append(
            "| %s | %d | %d | %s | %s | %s | %s |"
            % (
                w,
                len(ev),
                len(eb),
                pct(h1_any(eb, None) * len(eb), len(eb)),
                pct(sum(1 for b in br if b["terminal"] in ("H1", "H2")), len(br)),
                pct(deployer_link(D, eb, None) * len(eb), len(eb)),
                pct(recycle_rate(D, eb, None) * len(eb), len(eb)),
            )
        )
    write("I_robustness.md", lines)
    return {"tests": res, "classes": {n: classify_mech(res, n) for n in names}}


def section_j(D: Data) -> list[dict[str, Any]]:
    by: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for e in D.obs:
        by[e["em_cluster"]].append(e)
    lines = [
        "# J. Behavioural fingerprints (economic-mechanics clusters with 10 read events or more)",
        "",
        "No intent is attached to a fingerprint.",
        "",
    ]
    out = []
    for c, ev in sorted(by.items(), key=lambda x: (-len(x[1]), x[0])):
        if len(ev) < 10:
            continue
        mints = sorted({e["mint"] for e in ev}, key=lambda m: D.byrow[m]["t"])
        rr = [D.byrow[m] for m in mints]
        sn = [s for r in rr for s in r["snipers"]]
        amts = [s["last_amount"] for s in sn if s.get("last_amount")]
        lead = [r["t_create"] - s["last_bt"] for r in rr for s in r["snipers"] if s.get("last_bt")]
        gaps = [(rr[i + 1]["t"] - rr[i]["t"]) / 60 for i in range(len(rr) - 1)]
        br = [b for e in ev for b in e["branches"]]
        disp = Counter(e["disposal"] for e in ev)
        fp = {
            "cluster": c,
            "read events": len(ev),
            "launches": len(mints),
            "funding pattern": "%.1f SOL per sniper (median), funded %.0f s before creation (median)"
            % (statistics.median(amts) if amts else float("nan"), statistics.median(lead) if lead else float("nan")),
            "sniper set": "%d distinct snipers, %.1f per launch" % (len({s["wallet"] for s in sn}), len(sn) / len(rr)),
            "exit-wallet pattern": "%d exit wallets; same sniper always %s"
            % (len({e["wallet"] for e in ev}), pct(exit_pairs(D, {e["wallet"] for e in ev}, None) * 100, 100)),
            "token routing": ", ".join("%s %d" % kv for kv in disp.most_common(3)),
            "SOL routing": ", ".join(
                "%s %s" % (k, pct(sum(1 for b in br if b["terminal"] == k), len(br)))
                for k in CATS
                if any(b["terminal"] == k for b in br)
            )
            or "no outgoing transfer",
            "funder recurrence": pct(same_share(ev, lambda e: tuple(e["funders"]), None, setlike=True) * 100, 100),
            "deployer relationships": "path reaches the deployer network in %s of events with a branch"
            % pct(deployer_link(D, ev, None) * 100, 100),
            "recycling frequency": "%s of events with a branch fund a later launch"
            % pct(recycle_rate(D, ev, None) * 100, 100),
            "temporal cadence": "median gap between its sampled launches %.0f min"
            % (statistics.median(gaps) if gaps else float("nan")),
        }
        out.append(fp)
        lines += ["## %s" % c[:20], ""] + ["- %s: %s" % (k, v) for k, v in fp.items() if k != "cluster"] + [""]
    write("J_fingerprint.md", lines)
    return out


def section_h(D: Data, s: dict[str, Any]) -> None:
    i = s["I"]["tests"]["full"]
    d = s["D"]["cats"]
    br = s["D"]["branches"] or 1
    lines = [
        "# H. Hypotheses: one economic unit, a common execution service, independent traders",
        "",
        "| observation | value | A one unit | B execution service | C independent traders |",
        "|---|---|---|---|---|",
        "| sniper always sends to the same exit wallet | %.0f %% (null %.0f %%) | expected | expected | not expected |"
        % (
            100 * i["fixed sniper-to-exit-wallet pairs (exit wallets, corpus)"]["obs"],
            100 * i["fixed sniper-to-exit-wallet pairs (exit wallets, corpus)"]["null_mean"],
        ),
        "| exit wallet keeps the same funder | %.0f %% (null %.0f %%) | expected | expected (service funder) | weak |"
        % (
            100 * i["same funder in all events (exit wallets)"]["obs"],
            100 * i["same funder in all events (exit wallets)"]["null_mean"],
        ),
        "| capital reaches the launch funder | %.0f %% of events (null %.0f %%) | expected | expected if the "
        "funder is the service's wallet | weak |"
        % (
            100 * i["capital reaches the launch funder (events)"]["obs"],
            100 * i["capital reaches the launch funder (events)"]["null_mean"],
        ),
        "| same terminal wallet across events | %.0f %% (null %.0f %%) | expected | per client | weak |"
        % (
            100 * i["same terminal wallet in all events (exit wallets)"]["obs"],
            100 * i["same terminal wallet in all events (exit wallets)"]["null_mean"],
        ),
        "| capital reaches a hub | %.0f %% of branches | possible | possible (client withdrawals) | possible |"
        % (100 * d["H5"]["branches"] / br),
        "| capital reaches the deployer network | %.0f %% of events (null %.0f %%) | expected if the deployer is "
        "part of the unit | separate deployer networks | not expected |"
        % (
            100 * i["capital reaches the cluster's deployer network (events)"]["obs"],
            100 * i["capital reaches the cluster's deployer network (events)"]["null_mean"],
        ),
        "| capital funds a later launch | %.0f %% of events (null %.0f %%) | expected | expected (the service "
        "re-funds) | weak |"
        % (
            100 * i["capital funds a later launch (events)"]["obs"],
            100 * i["capital funds a later launch (events)"]["null_mean"],
        ),
        "",
        "What would separate A from B is where the capital goes after the funder: to one owner (A) or to "
        "several clients (B). The funder's own outflows are not collected in this study.",
    ]
    write("H_hypotheses.md", lines)


def main() -> None:
    D = Data()
    s: dict[str, Any] = {}
    s["coverage"] = {
        "events": len(D.events),
        "read": len(D.obs),
        "status": dict(Counter(e["status"].split(":")[0] for e in D.events)),
        "calls": D.tab.get("calls"),
        "stopped": D.tab.get("stopped"),
    }
    print(json.dumps(s["coverage"], indent=1))
    s["B"] = section_b(D)
    s["C"] = section_c(D)
    s["D"] = section_d(D)
    s["E"] = section_e(D)
    s["F"] = section_f(D)
    s["G"] = section_g(D)
    s["I"] = section_i(D)
    s["J"] = section_j(D)
    section_h(D, s)
    with open(os.path.join(L.DERIVED, "ED_results.json"), "w") as fh:
        json.dump(s, fh, indent=1, sort_keys=True, default=str)
    for k in ("B", "C", "D", "F", "G"):
        print(k, json.dumps(s[k], default=str)[:1500])
    print(json.dumps(s["I"]["classes"], indent=1))


if __name__ == "__main__":
    main()
