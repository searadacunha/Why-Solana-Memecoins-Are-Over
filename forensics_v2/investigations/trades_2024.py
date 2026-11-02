"""The author's own 2024 trades: every trip rebuilt by this engine from the cached raw transactions.

Private by construction: every output goes to forensics_v2/private_trades/, which git ignores. Inputs are read only from the
frozen historical_edge_2024 study, whose ledger gives the wallet perimeter and whose figures are what gets checked. A disagreement
is reported and never adjusted away.

    python -m forensics_v2.investigations.trades_2024 reconcile   # against the frozen table, prints only aggregates
    python -m forensics_v2.investigations.trades_2024 build       # the private deliverables, no network
    python -m forensics_v2.investigations.trades_2024 coverage <credits>  # inflows the owner's signatures miss
    python -m forensics_v2.investigations.trades_2024 expand <credits>    # wallets outside the perimeter
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Optional

from .. import decode as D
from ..rpc import SigWalk
from ..trace import History, Trip, load_services, sol_flows, trips

STUDY = Path.home() / "Documents/Crypto/WSMO-historical-edge-2024/historical_edge_2024"
CACHE = STUDY / "data/cache/getTransaction"
POSTHOC = STUDY / "posthoc_divergence"
SOL_USD = Path.home() / "Documents/Crypto/Why-Solana-Memecoins-Are-Over/data/cache/expl_solusdt_1d_1727740800_1738454400.json"
PRIVATE = Path(__file__).resolve().parents[1] / "private_trades"
DEPOSIT = "6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU"
HOT = "FWznbcNXWQuHTawe9RxvQ2LdCENssh12dsznf4RiouN5"
G2Y = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"
OCT1, JAN1, FEB3 = 1727740800, 1735689600, 1738540800  # 2024-10-01, 2025-01-01, 2025-02-03 UTC
SUPPLY_PUMP = 10**15


def utc(t: Optional[int]) -> Optional[str]:
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if t else None


def ledger() -> dict[str, Any]:
    return json.loads((STUDY / "derived/q1_ledger.json").read_text())


def _decode_wallet(job: tuple[str, list[str]]) -> tuple[str, list[D.Decoded]]:
    w, sigs = job
    out = []
    for s in sigs:
        with open(CACHE / (s + ".json")) as f:
            out.append(D.decode(json.load(f)["result"]))
    return w, out


def load_all() -> dict[str, list[D.Decoded]]:
    jobs = [(w, [r["sig"] for r in rows]) for w, rows in ledger()["ledger"].items()]
    with ProcessPoolExecutor(os.cpu_count() or 4) as ex:
        return dict(ex.map(_decode_wallet, jobs))


def frozen_trips() -> list[dict[str, str]]:
    with open(STUDY / "tables/q1_trips.csv") as f:
        return list(csv.DictReader(f))


def reconcile(all_txs: dict[str, list[D.Decoded]], built: list[Trip]) -> dict[str, Any]:
    """This engine's trips against the frozen study's table, by (wallet, mint, open time)."""
    old = {(r["wallet"], r["mint"], int(r["t_open"])): r for r in frozen_trips()}
    new = {(t.wallet, t.mint, t.t_open): t for t in built}
    in_window = {k: t for k, t in new.items() if OCT1 <= k[2] < JAN1}
    old_window = {k: r for k, r in old.items() if OCT1 <= k[2] < JAN1}
    diffs = []
    for k in set(in_window) & set(old_window):
        t, r = in_window[k], old_window[k]
        d_sol = t.realised - round(float(r["realised_sol"]) * 1e9)
        if abs(d_sol) > 2 or t.closed != (r["closed"] == "True"):
            diffs.append({"key": list(k), "new_lamports": t.realised, "old_sol": r["realised_sol"],
                          "new_closed": t.closed, "old_closed": r["closed"]})
    closed = [t for t in in_window.values() if t.closed]
    return {
        "transactions_decoded": sum(len(v) for v in all_txs.values()),
        "conservation_failures": sum(1 for v in all_txs.values() for d in v if not d.conserved),
        "trips_new_oct_dec": len(in_window), "trips_old_oct_dec": len(old_window),
        "only_new": len(set(in_window) - set(old_window)), "only_old": len(set(old_window) - set(in_window)),
        "closed_new": len(closed), "closed_old": sum(1 for r in old_window.values() if r["closed"] == "True"),
        "realised_lamports_new": sum(t.realised for t in closed),
        "realised_sol_old": sum(float(r["realised_sol"]) for r in old_window.values() if r["closed"] == "True"),
        "rows_differing_over_2_lamports": len(diffs), "diff_sample": diffs[:5],
    }


def write_private(name: str, content: str) -> Path:
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    p = PRIVATE / name
    p.write_text(content)
    os.chmod(p, 0o600)
    return p


def _flows_of(all_txs: dict[str, list[D.Decoded]]) -> dict[str, list[Any]]:
    out = {}
    for w, txs in all_txs.items():
        h = History(w, SigWalk(w, [], True, "window", 0), txs)
        out[w] = sol_flows(h)[0]
    return out


def attribution(all_txs: dict[str, list[D.Decoded]], flows: dict[str, list[Any]], built: list[Trip]) -> dict[str, Any]:
    """One class per wallet, by a rule written here, from evidence on chain and on the author's own cards.

    CONFIRMED_PERSONAL   sends to his declared deposit address, and one of his PnL cards matches a trip of this wallet
    STRONGLY_LINKED      sends to that address, and also receives from the exchange hot wallet or from a linked wallet
    CANDIDATE            sends to that address, nothing else
    THIRD_PARTY_INFRASTRUCTURE  over 60,000 signatures: exchange-like, classed so by the frozen study
    A deposit address only proves where money went. None of this is an identity proof beyond his own statement that the
    deposit address and the cards are his.
    """
    led = ledger()
    cands, infra = set(led["candidates"]), set(led["infra"])
    receipts = json.loads((STUDY / "tables/q1_receipts_trips.json").read_text())["receipts"]
    cards: dict[str, list[str]] = defaultdict(list)
    for r in receipts:
        if r.get("confidence") in ("high", "medium") and r.get("match"):
            cards[r["match"]["wallet"]].append(r["card"])
    n_trips = Counter(t.wallet for t in built)
    rows = []
    for w in sorted(cands):
        fl = flows[w]
        dep = [f for f in fl if f.src == w and f.dst == DEPOSIT]
        back = [f for f in fl if f.dst == w and f.src == HOT]
        inter = sorted({(f.src if f.dst == w else f.dst) for f in fl if (f.src if f.dst == w else f.dst) in cands - {w}})
        txs = all_txs[w]
        if dep and cards[w]:
            klass = "CONFIRMED_PERSONAL"
        elif dep and (back or inter):
            klass = "STRONGLY_LINKED"
        elif dep:
            klass = "CANDIDATE"
        else:
            klass = "UNDETERMINED"
        rows.append({"wallet": w, "class": klass, "deposits": len(dep), "deposit_lamports": sum(f.lamports for f in dep),
                     "first_deposit_sig": dep[0].signature if dep else None,
                     "returns_from_hot_wallet": len(back), "return_lamports": sum(f.lamports for f in back),
                     "cards": cards[w], "linked_wallets": inter, "trips": n_trips[w], "transactions": len(txs),
                     "first_utc": utc(txs[0].block_time) if txs else None, "last_utc": utc(txs[-1].block_time) if txs else None})
    rows += [{"wallet": w, "class": "THIRD_PARTY_INFRASTRUCTURE", "note": "over 60,000 signatures, frozen study's rule"}
             for w in sorted(infra)]
    return {"rule": attribution.__doc__, "counts": dict(Counter(r["class"] for r in rows)), "wallets": rows}


def funding_paths(flows: dict[str, list[Any]], all_txs: dict[str, list[D.Decoded]]) -> dict[str, Any]:
    cands = set(flows)
    services = load_services()
    out = {}
    for w, fl in flows.items():
        inflow = [f for f in fl if f.dst == w and f.lamports >= 10_000_000]
        rows = [{"src": f.src, "lamports": f.lamports, "utc": utc(f.ts), "sig": f.signature, "instruction": f.path,
                 "evidence": f.evidence, "src_class": "own_perimeter" if f.src in cands else
                 services[f.src]["name"] if f.src in services else "unknown"} for f in inflow]
        first = rows[0] if rows else None
        out[w] = {"read_from": utc(all_txs[w][0].block_time) if all_txs[w] else None,
                  "note": "window from 2024-09-01: an earlier source is not visible here", "first_inflow_in_window": first,
                  "n_inflows": len(rows),
                  "by_class_lamports": {c: sum(r["lamports"] for r in rows if r["src_class"] == c)
                                        for c in {r["src_class"] for r in rows}},
                  "direct_from_gateway": sum(1 for r in rows if r["src"] == G2Y), "inflows": rows}
    return out


def rotation(attr: dict[str, Any], flows: dict[str, list[Any]]) -> dict[str, Any]:
    """Wallets in order of first activity: was each one started by money from the previous ones or from the exchange?"""
    rows = [r for r in attr["wallets"] if r.get("first_utc")]
    rows.sort(key=lambda r: r["first_utc"])
    cands = {r["wallet"] for r in rows}
    seq = []
    for r in rows:
        fl = [f for f in flows[r["wallet"]] if f.dst == r["wallet"] and f.lamports >= 10_000_000]
        first = fl[0] if fl else None
        seq.append({"wallet": r["wallet"], "first": r["first_utc"], "last": r["last_utc"], "trips": r["trips"],
                    "funded_first_by": ("exchange_hot_wallet" if first.src == HOT else "own_perimeter" if first.src in cands
                                        else "gateway" if first.src == G2Y else "other") if first else None})
    return {"sequence": seq, "funded_first_by": dict(Counter(s["funded_first_by"] for s in seq))}


def trip_rows(all_txs: dict[str, list[D.Decoded]], flows: dict[str, list[Any]],
              built: list[Trip]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Per trip and per leg. Only exact chain values, plus derived prices. USD stays a separate column."""
    frozen = json.loads((POSTHOC / "derived/trips.json").read_text())
    feats = {(r["wallet"], r["mint"], r["t_open"]): r for r in frozen}
    classes = {}
    for r, k in zip(json.loads((POSTHOC / "derived/classes.json").read_text()), frozen):
        assert r["wallet"] == k["wallet"] and r["mint"] == k["mint"]
        classes[(k["wallet"], k["mint"], k["t_open"])] = r
    usd = {k: float(v) for k, v in json.loads(SOL_USD.read_text()).items()} if SOL_USD.exists() else {}
    by_sig = {w: {d.signature: d for d in v} for w, v in all_txs.items()}
    rows, legs = [], []
    for t in sorted(built, key=lambda x: x.t_open):
        if not OCT1 <= t.t_open < FEB3:
            continue
        ds = [by_sig[t.wallet][s] for s in t.sigs]
        buys, sells = [], []
        fees = 0
        for d in ds:
            tok = D.traded_mints(d, t.wallet).get(t.mint, 0)
            sol = d.lamport_delta.get(t.wallet, 0)
            fees += d.fee if d.fee_payer == t.wallet else 0
            side = "buy" if tok > 0 and sol < 0 else "sell" if tok < 0 and sol > 0 else "other"
            legs.append({"wallet": t.wallet, "mint": t.mint, "t_open": t.t_open, "side": side, "sig": d.signature, "slot": d.slot,
                         "utc": utc(d.block_time), "token_delta_raw": tok, "wallet_lamport_delta": sol, "fee": d.fee,
                         "fee_payer_is_wallet": d.fee_payer == t.wallet, "venues": d.venues, "signers": d.signers,
                         "evidence": D.ONCHAIN_VERIFIED,
                         "other_mints_in_tx": len(D.traded_mints(d, t.wallet)) - 1})
            (buys if side == "buy" else sells if side == "sell" else []).append((d, tok, sol))
        fin = [f for f in flows[t.wallet] if f.dst == t.wallet and (f.ts or 0) <= t.t_open and f.lamports >= 10_000_000]
        last_in = fin[-1] if fin else None
        dep = [f for f in flows[t.wallet] if f.src == t.wallet and f.dst == DEPOSIT and t.t_close and (f.ts or 0) >= t.t_close]
        k = (t.wallet, t.mint, t.t_open)
        f = feats.get(k, {})
        c = classes.get(k, {})
        first_tok = buys[0][1] if buys else 0
        is_pump = "pump" in (buys[0][0].venues if buys else [])
        day_open, day_close = utc(t.t_open)[:10], utc(t.t_close)[:10] if t.t_close else None
        rows.append({
            "wallet": t.wallet, "mint": t.mint, "card": c.get("card"), "class_frozen": c.get("class"),
            "t_open_utc": utc(t.t_open), "t_close_utc": utc(t.t_close), "hold_s": (t.t_close - t.t_open) if t.t_close else None,
            "first_buy_sig": t.sig_open, "last_sig": t.sigs[-1], "n_buys": t.n_buys, "n_sells": t.n_sells, "closed": t.closed,
            "sol_out_lamports": t.sol_out, "sol_in_lamports": t.sol_in, "realised_lamports": t.realised,
            "roi": round(t.realised / t.sol_out, 6) if t.sol_out else None, "fees_lamports": fees,
            "tokens_bought_raw": t.bought, "tokens_sold_raw": t.sold, "first_buy_tokens_raw": first_tok,
            "pct_supply_first_buy": round(first_tok * 100 / SUPPLY_PUMP, 4) if is_pump else None,
            "pct_supply_basis": "pump.fun 1e9 tokens, 6 decimals" if is_pump else "not established",
            "entry_lamports_per_token_raw": round(t.sol_out / t.bought, 12) if t.bought else None,
            "exit_lamports_per_token_raw": round(t.sol_in / t.sold, 12) if t.sold else None,
            "entry_venue": f.get("entry_venue"), "exit_venue": f.get("exit_venue"), "venues": ",".join(sorted(t.venues)),
            "entry_curve_real_sol": f.get("entry_curve_real_sol"), "entry_mcap_sol": f.get("entry_mcap_sol"),
            "signal_before_entry_frozen": f.get("sig_main20_before"), "signal_lead_s_frozen": f.get("sig_main20_lead_s"),
            "funded_last_src": last_in.src if last_in else None, "funded_last_lamports": last_in.lamports if last_in else None,
            "funded_last_sig": last_in.signature if last_in else None,
            "funded_age_s": (t.t_open - (last_in.ts or 0)) if last_in else None,
            "next_deposit_lamports": dep[0].lamports if dep else None, "next_deposit_sig": dep[0].signature if dep else None,
            "next_deposit_delay_s": ((dep[0].ts or 0) - t.t_close) if dep and t.t_close else None,
            "realised_usd_at_close_day": round(t.realised / 1e9 * usd[day_close], 2) if day_close in usd and t.closed else None,
            "sol_usd_open_day": usd.get(day_open),
        })
    return rows, legs


def pnl_markdown(rows: list[dict[str, Any]], attr: dict[str, Any], rec: dict[str, Any], rot: dict[str, Any]) -> str:
    def s(x: float) -> str:
        return "%+.4f" % (x / 1e9)
    closed = [r for r in rows if r["closed"]]
    q4 = [r for r in closed if r["t_open_utc"] < "2025-01-01"]
    jan = [r for r in closed if r["t_open_utc"] >= "2025-01-01"]
    by_month: dict[str, int] = defaultdict(int)
    for r in closed:
        by_month[r["t_open_utc"][:7]] += r["realised_lamports"]
    by_class: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in q4:
        by_class[r["class_frozen"] or "?"][0] += 1
        by_class[r["class_frozen"] or "?"][1] += r["realised_lamports"]
    top = sorted(closed, key=lambda r: -r["realised_lamports"])[:10]
    lines = ["# PnL reconstruction, private", "",
             "Three different things, never added together: trading profit, cash moved, and USD at a date.", "",
             "## 1. Trading profit (closed round trips, SOL, all costs inside each leg)", "",
             "| period | closed trips | realised |", "|---|---:|---:|",
             "| 2024-10-01 to 2024-12-31 | %d | %s |" % (len(q4), s(sum(r["realised_lamports"] for r in q4))),
             "| 2025-01-01 to 2025-02-02 | %d | %s |" % (len(jan), s(sum(r["realised_lamports"] for r in jan))), ""]
    lines += ["Same figure as the frozen study, by a separate implementation over the same raw transactions: %d trips, "
              "%d closed, %d lamports, %d rows differing. Same convention, same data: this validates the code, not the "
              "trades, and adds no evidence "
              "about the trades." % (rec["trips_new_oct_dec"], rec["closed_new"], rec["realised_lamports_new"],
                                     rec["rows_differing_over_2_lamports"]), "",
              "By month: " + ", ".join("%s %s" % (k, s(v)) for k, v in sorted(by_month.items())), "",
              "Open positions are not valued. Residual tokens count for nothing here.", "",
              "## 2. Cash moved (not profit)", "",
              "Deposits, returns from the exchange and trading cash flow are in the frozen study, "
              "`posthoc_divergence/README.md` section 1, unchanged. The published USD figure is the gross inflow of those "
              "deposits. A transfer between own wallets is never profit.",
              "",
              "## 3. USD", "",
              "`realised_usd_at_close_day` values each closed trip at that day's SOL close: a valuation, not money received.", "",
              "## 4. The largest trips", "", "| card | mint | opened | hold | in | realised | ROI | entry | exit | class |",
              "|---|---|---|---:|---:|---:|---:|---|---|---|"]
    for r in top:
        lines.append("| %s | `%s…` | %s | %s | %.3f | %s | %.0f %% | %s | %s | %s |" % (
            r["card"] or "", r["mint"][:10], r["t_open_utc"], r["hold_s"], r["sol_out_lamports"] / 1e9, s(r["realised_lamports"]),
            (r["roi"] or 0) * 100, r["entry_venue"], r["exit_venue"], r["class_frozen"]))
    lines += ["", "## 5. Pattern class of the trips (frozen criteria)", "",
              "| class | trips | realised, closed only |", "|---|---:|---:|"]
    for k, v in sorted(by_class.items()):
        lines.append("| %s | %d | %s |" % (k, v[0], s(v[1])))
    lines += ["", "## 6. Wallets", "", json.dumps(attr["counts"]), "", "First funding of each wallet, in the window read: " +
              json.dumps(rot["funded_first_by"]), ""]
    return "\n".join(lines) + "\n"


def build() -> int:
    all_txs = load_all()
    built = [t for w, v in all_txs.items() for t in trips(v, w)]
    rec = reconcile(all_txs, built)
    if rec["rows_differing_over_2_lamports"] or rec["only_new"] or rec["only_old"]:
        print("reconciliation differs, writing anyway and flagging:", {k: rec[k] for k in ("only_new", "only_old")})
    flows = _flows_of(all_txs)
    attr = attribution(all_txs, flows, built)
    attr["rotation"] = rotation(attr, flows)
    write_private("WALLET_ATTRIBUTION.json", json.dumps(attr, indent=1))
    write_private("FUNDING_PATHS.json", json.dumps(funding_paths(flows, all_txs), indent=1))
    rows, legs = trip_rows(all_txs, flows, built)
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    p = PRIVATE / "TRADES_2024_2025.csv"
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    os.chmod(p, 0o600)
    write_private("TRADE_EVIDENCE.jsonl", "\n".join(json.dumps(x) for x in legs) + "\n")
    write_private("PNL_RECONSTRUCTION.md", pnl_markdown(rows, attr, rec, attr["rotation"]))
    open_trips = [r for r in rows if not r["closed"]]
    print(json.dumps({"reconcile": {k: rec[k] for k in ("trips_new_oct_dec", "closed_new", "realised_lamports_new",
                                                        "rows_differing_over_2_lamports", "only_new", "only_old")},
                      "trips_written": len(rows), "legs": len(legs), "open": len(open_trips), "attribution": attr["counts"],
                      "rotation": attr["rotation"]["funded_first_by"], "jan_feb_closed_sol": sum(
                          r["realised_lamports"] for r in rows if r["closed"] and r["t_open_utc"] >= "2025-01-01") / 1e9},
                     indent=0))
    return 0


def coverage(credits: int) -> int:
    """Inflows that signatures of the owner cannot show: ask for every balance change of each wallet."""
    from ..__main__ import client
    c = client(credits)
    LO, HI = 1725148800, 1740787200
    led = ledger()["ledger"]
    out = {}
    for w, rows in led.items():
        known = {r["sig"] for r in rows}
        raw, walk = c.history_txs(w, LO, HI - 1, "balanceChanged", max_pages=60)
        extra = [t for t in raw if t["transaction"]["signatures"][0] not in known]
        moved = []
        for t in extra:
            d = D.decode(t)
            n = d.owners.get(w)
            if d.ok and n and (n.tokens or n.sol):
                moved.append({"sig": d.signature, "utc": utc(d.block_time), "tokens": n.tokens, "sol": n.sol,
                              "fee_payer": d.fee_payer})
        out[w] = {"read": len(raw), "ledger": len(rows), "complete": walk.complete, "extra": len(extra), "extra_moving": moved}
        print(w[:6], len(raw), len(rows), len(extra), len(moved), "net", c.net_calls, flush=True)
        write_private("COVERAGE_TOKEN_ACCOUNTS.json", json.dumps(out, indent=1))
    print({"wallets": len(out), "extra_tx": sum(v["extra"] for v in out.values()),
           "extra_moving": sum(len(v["extra_moving"]) for v in out.values()),
           "all_complete": all(v["complete"] for v in out.values())})
    return 0


def _held(text: str) -> int:
    import re
    return sum(int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for n, u in re.findall(r"(\d+)\s*([dhms])", text))


def expand(credits: int, top: int = 150) -> int:
    """Wallets outside the perimeter that exchanged SOL with it. Do they trade like the cards nothing else explains?

    A transfer from one of his wallets does not make a wallet his. A candidate here is that plus a trade matching a card's
    invested amount, gain and holding time, the three figures that can only coincide by chance. Everything stays a candidate.
    """
    from ..__main__ import client
    from ..trace import history
    all_txs = load_all()
    flows = _flows_of(all_txs)
    perimeter = set(flows)
    infra = set(ledger()["infra"])
    services = set(load_services()) | {DEPOSIT, HOT, G2Y} | infra
    links: dict[str, list[Any]] = defaultdict(list)
    for w, fl in flows.items():
        for f in fl:
            other = f.dst if f.src == w else f.src
            if other not in perimeter and other not in services and f.lamports >= 100_000_000 and other not in D.JITO_TIP:
                links[other].append(f)
    ranked = sorted(links, key=lambda a: -sum(f.lamports for f in links[a]))
    receipts = json.loads((STUDY / "tables/q1_receipts_trips.json").read_text())["receipts"]
    open_cards = {r["card"] for r in receipts if r.get("confidence") not in ("high", "medium")}
    cards = [c for c in json.loads((STUDY / "q1/captures_read.json").read_text())["cards"]
             if c["sym"] in open_cards and c["inv_sol"] and c["gain_sol"]]
    c = client(credits)
    out = []
    stopped = None
    for a in ranked[:top]:
        try:
            h = history(c, a, 1725148800, 1740787199, token_accounts="none", max_pages=3)
        except RuntimeError as e:
            stopped = str(e)[:120]
            break
        ts = trips(h.txs, a)
        hits = []
        for t in ts:
            if not t.closed or not t.t_close:
                continue
            for k in cards:
                inv, gain, held = k["inv_sol"], k["gain_sol"], _held(k["held"])
                ok_i = abs(t.sol_out / 1e9 - inv) <= max(0.03 * inv, 0.02)
                ok_g = abs(t.realised / 1e9 - gain) <= 0.05 * abs(gain)
                ok_h = abs((t.t_close - t.t_open) - held) <= max(0.10 * held, 120)
                if ok_i + ok_g + ok_h >= 2:
                    hits.append({"card": k["sym"], "mint": t.mint, "first_sig": t.sig_open, "invested": ok_i, "gain": ok_g,
                                 "held": ok_h, "sol_out": t.sol_out / 1e9, "realised": t.realised / 1e9,
                                 "dur_s": t.t_close - t.t_open})
        fl = links[a]
        out.append({"wallet": a, "linked_from": sorted({f.src if f.dst == a else f.dst for f in fl}),
                    "transfers": len(fl), "lamports": sum(f.lamports for f in fl),
                    "to_it": sum(f.lamports for f in fl if f.dst == a), "from_it": sum(f.lamports for f in fl if f.src == a),
                    "link_sigs": [f.signature for f in fl][:5], "tx_read": len(h.txs), "history_capped": not h.walk.complete,
                    "trips": len(ts), "realised_lamports_closed": sum(t.realised for t in ts if t.closed),
                    "deposits_to_his_address": sum(1 for f in sol_flows(h)[0] if f.dst == DEPOSIT),
                    "exchange_returns": sum(1 for f in sol_flows(h)[0] if f.src == HOT), "card_hits": hits,
                    "class": "CANDIDATE" if any(x["invested"] and x["gain"] and x["held"] for x in hits) else "UNDETERMINED"})
        write_private("WALLET_CANDIDATES_EXPANDED.json",
                      json.dumps({"rule": expand.__doc__, "stopped": stopped, "rows": out}, indent=1))
    full = [r for r in out if r["class"] == "CANDIDATE"]
    print({"external_counterparties": len(ranked), "read": len(out), "stopped": stopped, "net": c.net_calls,
           "with_trips": sum(1 for r in out if r["trips"]), "capped": sum(1 for r in out if r["history_capped"]),
           "with_deposits": sum(1 for r in out if r["deposits_to_his_address"]),
           "with_exchange_returns": sum(1 for r in out if r["exchange_returns"]),
           "two_of_three_hits": sum(1 for r in out if r["card_hits"]), "three_of_three": len(full),
           "cards_matched": sorted({x["card"] for r in full for x in r["card_hits"]})})
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    cmd = args[0] if args else "reconcile"
    if cmd == "coverage":
        return coverage(int(args[1]))
    if cmd == "expand":
        return expand(int(args[1]))
    if cmd == "build":
        return build()
    all_txs = load_all()
    built = [t for w, v in all_txs.items() for t in trips(v, w)]
    print(json.dumps(reconcile(all_txs, built), indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
