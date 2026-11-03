"""The author's trades from the ledger rows: capital statement, costs outside the trips, cards, attribution by written rule.

Private outputs only. Rule: docs/PLAN_attribution_2024.md. Nothing here calls the network.

    python -m forensics_v2.investigations.trades_report
"""

from __future__ import annotations

import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from typing import Any, Optional

from ..decode import JITO_TIP
from .trades_2024 import DEPOSIT, FEB3, G2Y, HOT, JAN1, OCT1, PRIVATE, STUDY, ledger, utc, write_private
from .trades_ledger import DERIVED, ROWS

TOOL_FEE = "9yMwSPk9mrXSN7yDHUuZurAh1sjbJsfpUqjZ7SvVtdco"  # the account receiving the fee of the bot named on the cards
PERIODS = (("before_oct", 0, OCT1), ("oct_dec", OCT1, JAN1), ("jan_feb2", JAN1, FEB3), ("after_feb2", FEB3, 10**12))


def period_of(t: int) -> str:
    return next(p for p, a, b in PERIODS if a <= t < b)


def classify(r: dict[str, Any], perimeter: set[str]) -> str:
    """One class per (wallet, transaction). Same sign rule as the frozen ledger for trades, so that its totals can be rebuilt."""
    if not r["ok"]:
        return "failed"
    if r["tok"]:
        v = next(iter(r["tok"].values()))
        if v > 0 and r["native"] < 0:
            return "buy"
        if v < 0 and r["native"] > 0:
            return "sell"
        return "token_other"
    sol = [m for m in r["moves"] if m["k"] == "sol_transfer"]
    if sol and all(m["dst"] in JITO_TIP for m in sol):
        return "tip"
    w = r["w"]
    others = {e[1] if e[0] == w else e[0] for e in r["edges"]}
    if DEPOSIT in others:
        return "to_deposit"
    if HOT in others:
        return "from_hot"
    if G2Y in others:
        return "from_gateway"
    if others & perimeter:
        return "internal"
    if others:
        return "external_out" if any(e[0] == w for e in r["edges"]) else "external_in"
    return "no_transfer"


def load() -> list[dict[str, Any]]:
    with gzip.open(ROWS, "rt") as f:
        return [json.loads(line) for line in f]


def continuity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Each wallet's balance must chain from one transaction to the next: a break means a transaction is missing."""
    by: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by[r["w"]][r["slot"]].append(r)
    breaks = []
    for w, slots in by.items():
        cur: Optional[int] = None
        for slot in sorted(slots):
            pending = list(slots[slot])
            while pending:
                nxt = next((r for r in pending if cur is None or r["pre"] == cur), None)
                if nxt is None:  # order inside a slot is not in the row: take the one closest, and record the break
                    nxt = min(pending, key=lambda r: abs(r["pre"] - (cur or 0)))
                    breaks.append({"wallet": w, "slot": slot, "sig": nxt["sig"], "gap_lamports": nxt["pre"] - (cur or 0)})
                pending.remove(nxt)
                cur = nxt["post"]
    return {"wallets": len(by), "breaks": breaks, "sum_gap_lamports": sum(b["gap_lamports"] for b in breaks)}


def capital(rows: list[dict[str, Any]], perimeter: set[str]) -> dict[str, Any]:
    """Native lamports by class and period, with the opening and closing balance of every wallet. Must close to the lamport."""
    flows: dict[str, Counter[str]] = defaultdict(Counter)
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    by_wallet: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        k = classify(r, perimeter)
        r["class"] = k
        p = period_of(r["t"])
        counts[p][k] += 1
        by_wallet[r["w"]].append(r)
        if k not in ("to_deposit", "from_hot", "from_gateway", "internal", "external_in", "external_out"):
            flows[p][k] += r["native"]
            continue
        booked = 0
        for src, dst, lam, _ in r["edges"]:  # several recipients in one transaction each get their own class
            other = dst if src == r["w"] else src
            cat = (
                "to_deposit"
                if other == DEPOSIT
                else "from_hot"
                if other == HOT
                else "from_gateway"
                if other == G2Y
                else "internal"
                if other in perimeter
                else "external_out"
                if src == r["w"]
                else "external_in"
            )
            flows[p][cat] += -lam if src == r["w"] else lam
            booked += -lam if src == r["w"] else lam
        flows[p]["capital_tx_fees"] += r["native"] - booked
    open_close: dict[str, dict[str, int]] = defaultdict(lambda: {"open": 0, "close": 0})
    first_pre = 0
    for w, rs in by_wallet.items():
        rs.sort(key=lambda r: r["slot"])
        first_pre += rs[0]["pre"]
        for (
            p,
            a,
            b,
        ) in PERIODS:  # order inside a slot is unknown, so a period's opening is the first balance seen plus everything before it
            opening = rs[0]["pre"] + sum(r["native"] for r in rs if r["t"] < a)
            open_close[p]["open"] += opening
            open_close[p]["close"] += opening + sum(r["native"] for r in rs if a <= r["t"] < b)
    out = {}
    for p, *_ in PERIODS:
        total = sum(flows[p].values())
        oc = open_close[p]
        assert oc["open"] + total == oc["close"], p
        out[p] = {"flows": dict(flows[p]), "counts": dict(counts[p]), "open": oc["open"], "close": oc["close"], "sum": total}
    out["first_balance_seen_all_wallets"] = first_pre
    return out


def held(text: str) -> int:
    return sum(int(n) * {"d": 86400, "h": 3600, "m": 60, "s": 1}[u] for n, u in re.findall(r"(\d+)\s*([dhms])", text))


def match_cards(trips: list[dict[str, str]], meta: dict[str, Any]) -> list[dict[str, Any]]:
    """Every card against every trip of the same token symbol, with the figures of the written rule."""
    cards = json.loads((STUDY / "q1/captures_read.json").read_text())["cards"]
    by_sym: dict[str, list[dict[str, str]]] = defaultdict(list)
    for t in trips:
        by_sym[(meta.get(t["mint"], {}).get("symbol") or "").strip().lower()].append(t)
    out = []
    for c in cards:
        hits = []
        for t in by_sym.get(c["sym"].lower(), []):
            o, i = int(t["sol_out_lamports"]) / 1e9, int(t["sol_in_lamports"]) / 1e9
            hold = int(t["hold_s"]) if t["hold_s"] else None
            ok_hold = hold is not None and abs(hold - held(c["held"])) <= 60
            if c.get("inv_sol"):
                ok = (
                    abs(o - c["inv_sol"]) <= 0.02 * c["inv_sol"]
                    and abs(i - o - c["gain_sol"]) <= 0.02 * abs(c["gain_sol"])
                    and ok_hold
                )
            else:
                ok = o > 0 and abs((i - o) / o * 100 - c["pct"]) <= 0.01 * c["pct"] and ok_hold
            if ok:
                hits.append(
                    {
                        "wallet": t["wallet"],
                        "mint": t["mint"],
                        "t_open_utc": t["t_open_utc"],
                        "hold_s": hold,
                        "sol_out": o,
                        "gain": i - o,
                        "first_buy_sig": t["first_buy_sig"],
                        "last_sig": t["last_sig"],
                    }
                )
        out.append(
            {
                "card": c["sym"],
                "bot": c.get("bot"),
                "inv_sol": c.get("inv_sol"),
                "gain_sol": c.get("gain_sol"),
                "held": c["held"],
                "pct": c["pct"],
                "matches": hits,
                "same_symbol_trips": len(by_sym.get(c["sym"].lower(), [])),
            }
        )
    return out


def attribution(
    rows: list[dict[str, Any]], cards: list[dict[str, Any]], perimeter: set[str], infra: set[str]
) -> list[dict[str, Any]]:
    """docs/PLAN_attribution_2024.md, applied as written."""
    ev: dict[str, dict[str, Any]] = {
        w: {
            "wallet": w,
            "deposits": 0,
            "deposit_lamports": 0,
            "first_deposit_sig": None,
            "hot_returns": 0,
            "hot_lamports": 0,
            "first_hot_sig": None,
            "token_rows": 0,
            "tool_fee_rows": 0,
            "cards": [],
            "direct": defaultdict(lambda: {"n": 0, "lamports": 0, "sig": None}),
            "first_t": None,
            "last_t": None,
        }
        for w in perimeter
    }
    for r in sorted(rows, key=lambda x: x["slot"]):
        e = ev[r["w"]]
        e["first_t"] = e["first_t"] or r["t"]
        e["last_t"] = r["t"]
        if r["ok"] and r["tok"]:
            e["token_rows"] += 1
            e["tool_fee_rows"] += any(m["k"] == "sol_transfer" and m["dst"] == TOOL_FEE for m in r["moves"])
        for s, d, lam, _ in r["edges"]:
            if s == r["w"] and d == DEPOSIT:
                e["deposits"] += 1
                e["deposit_lamports"] += lam
                e["first_deposit_sig"] = e["first_deposit_sig"] or r["sig"]
            if d == r["w"] and s == HOT:
                e["hot_returns"] += 1
                e["hot_lamports"] += lam
                e["first_hot_sig"] = e["first_hot_sig"] or r["sig"]
            other = d if s == r["w"] else s
            if other in perimeter and lam >= 10_000_000:
                link = e["direct"][other]
                link["n"] += 1
                link["lamports"] += lam
                link["sig"] = link["sig"] or r["sig"]
        for m in r["moves"]:
            if m.get("mint") and m["k"] == "spl" and m["src"] in perimeter and m["dst"] in perimeter and m["src"] != m["dst"]:
                other = m["dst"] if m["src"] == r["w"] else m["src"]
                link = e["direct"][other]
                link["tokens"] = link.get("tokens", 0) + 1
                link["sig"] = link["sig"] or r["sig"]
    for c in cards:
        for m in c["matches"]:
            ev[m["wallet"]]["cards"].append(c["card"])
    level: dict[str, str] = {w: "CERTAIN" for w, e in ev.items() if e["deposits"] and e["cards"]}
    why: dict[str, str] = {w: "deposit address and card(s) " + ", ".join(sorted(set(ev[w]["cards"]))) for w in level}
    changed = True
    while changed:
        changed = False
        for w, e in ev.items():
            if w in level or not e["deposits"]:
                continue
            via = [o for o in e["direct"] if o in level]
            if via:
                level[w] = "PROBABLE"
                why[w] = "deposit address and direct transfer with " + via[0]
                changed = True
            elif e["hot_returns"] >= 2 and e["token_rows"] and e["tool_fee_rows"] * 2 >= e["token_rows"]:
                level[w] = "PROBABLE"
                why[w] = "deposit address, %d returns from the hot wallet, tool fee on %d of %d trades" % (
                    e["hot_returns"],
                    e["tool_fee_rows"],
                    e["token_rows"],
                )
                changed = True
    # First characters of a real wallet, a dust amount, nothing else: an address-poisoning attempt.
    real = {w[:4] for w, e in ev.items() if e["token_rows"]}
    for w, e in ev.items():
        e["lookalike"] = w not in level and not e["token_rows"] and e["deposit_lamports"] < 1_000_000 and w[:4] in real
    out = []
    for w, e in sorted(ev.items()):
        out.append(
            {
                **{k: v for k, v in e.items() if k != "direct"},
                "level": level.get(w, "NOT_ESTABLISHED"),
                "why": why.get(
                    w,
                    "dust from an address copying the first characters of a real wallet"
                    if e["lookalike"]
                    else "only sends to the deposit address"
                    if e["deposits"]
                    else "no transfer to the deposit address in the window",
                ),
                "direct": {o: dict(v) for o, v in e["direct"].items()},
                "first_utc": utc(e["first_t"]),
                "last_utc": utc(e["last_t"]),
            }
        )
    return out + [{"wallet": w, "level": "EXCLUDED_INFRASTRUCTURE", "why": "over 60,000 signatures"} for w in sorted(infra)]


def tips_of_legs(rows: list[dict[str, Any]]) -> tuple[dict[str, int], int]:
    """A tip is its own transaction in the slot of the trade it paid for. Shared equally when a slot holds several trades."""
    trades: dict[tuple[str, int], list[str]] = defaultdict(list)
    for r in rows:
        if r.get("class") in ("buy", "sell", "token_other"):
            trades[(r["w"], r["slot"])].append(r["sig"])
    by_sig: Counter[str] = Counter()
    unattached = 0
    for r in rows:
        if r.get("class") == "tip":
            lam = -r["native"] - (r["fee"] if r["payer"] == r["w"] else 0)
            sigs = trades.get((r["w"], r["slot"]))
            if not sigs:
                unattached += lam
                continue
            for s in sigs:
                by_sig[s] += lam // len(sigs)
    return dict(by_sig), unattached


def _csv(name: str, rows: list[dict[str, Any]]) -> None:
    """Private CSV, mode 600, columns from the first row."""
    p = PRIVATE / name
    with open(p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["empty"])
        w.writeheader()
        w.writerows(rows)
    p.chmod(0o600)


def enrich_trips(
    trips: list[dict[str, str]],
    meta: dict[str, Any],
    levels: dict[str, str],
    tip_sig: dict[str, int],
    cards: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Trip table with symbol, attribution level, Jito tips of its legs, matched card, and what was read about the launch."""
    tips: Counter[tuple[str, str, int]] = Counter()
    with open(PRIVATE / "TRADE_EVIDENCE.jsonl") as f:
        for line in f:
            e = json.loads(line)
            tips[(e["wallet"], e["mint"], e["t_open"])] += tip_sig.get(e["sig"], 0)
    t_open = {
        (e["wallet"], e["mint"], e["utc"]): e["t_open"]
        for e in map(json.loads, open(PRIVATE / "TRADE_EVIDENCE.jsonl"))
        if e["side"] == "buy"
    }
    pm = {}
    for name in ("PATTERN_MATCHES.json", "PATTERN_PRIORITY.json"):
        if (PRIVATE / name).exists():
            pm.update({(t["wallet"], t["mint"], t["t_open"]): t for t in json.loads((PRIVATE / name).read_text())["trips"]})
    card_of = {(m["wallet"], m["first_buy_sig"]): c["card"] for c in cards for m in c["matches"]}
    out = []
    for t in trips:
        key_t = t_open.get((t["wallet"], t["mint"], t["t_open_utc"]))
        p = pm.get((t["wallet"], t["mint"], key_t))
        if p:
            tier = (
                "launch_read_S1"
                if p["S1"]
                else "launch_read_S2_only"
                if p["S2"]
                else "launch_read_no_signal"
                if p.get("window_covers_entry")
                else "launch_read_window_short"
            )
        else:
            tier = {"P": "frozen_P_not_reread", "H": "not_a_pump_token"}.get(t["class_frozen"], "launch_not_read")
        lam = tips[(t["wallet"], t["mint"], key_t)]
        m = meta.get(t["mint"], {})
        out.append(
            {
                "level": levels.get(t["wallet"], "OUTSIDE"),
                "wallet": t["wallet"],
                "symbol": m.get("symbol"),
                "name": m.get("name"),
                "mint": t["mint"],
                "card_v2": card_of.get((t["wallet"], t["first_buy_sig"]), ""),
                "pattern": tier,
                "t_open_utc": t["t_open_utc"],
                "t_close_utc": t["t_close_utc"],
                "hold_s": t["hold_s"],
                "closed": t["closed"],
                "n_buys": t["n_buys"],
                "n_sells": t["n_sells"],
                "sol_in_lamports_bought_with": t["sol_out_lamports"],
                "sol_got_back_lamports": t["sol_in_lamports"],
                "realised_lamports": t["realised_lamports"],
                "jito_tips_lamports": lam,
                "realised_after_tips_lamports": int(t["realised_lamports"]) - lam,
                "entry_venue": t["entry_venue"],
                "exit_venue": t["exit_venue"],
                "class_frozen": t["class_frozen"],
                "first_buy_sig": t["first_buy_sig"],
                "last_sig": t["last_sig"],
                "S0": p and p["S0"],
                "S1": p and p["S1"],
                "S2": p and p["S2"],
                "delay_after_S1_s": p and p.get("delay_after_S1_s"),
                "first_buy_pct_supply": t["pct_supply_first_buy"],
            }
        )
    return out


def token_table(
    rows: list[dict[str, Any]], meta: dict[str, Any], levels: dict[str, str], tip_sig: dict[str, int]
) -> list[dict[str, Any]]:
    """Every token over all wallets, no trip cutting, 2024-10-01 to 2025-02-02: the cash really spent and received on it."""
    acc: dict[str, dict[str, Any]] = {}
    for r in sorted(rows, key=lambda x: x["slot"]):
        if not r["ok"] or not r["tok"] or not OCT1 <= r["t"] < FEB3:
            continue
        for mint, dt in r["tok"].items():
            a = acc.setdefault(
                mint,
                {
                    "mint": mint,
                    "symbol": meta.get(mint, {}).get("symbol"),
                    "wallets": set(),
                    "levels": set(),
                    "buys": 0,
                    "sells": 0,
                    "other_legs": 0,
                    "spent": 0,
                    "received": 0,
                    "other_sol": 0,
                    "tips": 0,
                    "bought_raw": 0,
                    "sold_raw": 0,
                    "moved_in_raw": 0,
                    "moved_out_raw": 0,
                    "first_utc": utc(r["t"]),
                    "last_utc": None,
                    "first_sig": r["sig"],
                    "last_sig": None,
                },
            )
            a["wallets"].add(r["w"])
            a["levels"].add(levels.get(r["w"], "OUTSIDE"))
            a["last_utc"], a["last_sig"] = utc(r["t"]), r["sig"]
            a["tips"] += tip_sig.get(r["sig"], 0)
            if r["class"] == "buy":
                a["buys"] += 1
                a["spent"] -= r["native"]
                a["bought_raw"] += dt
            elif r["class"] == "sell":
                a["sells"] += 1
                a["received"] += r["native"]
                a["sold_raw"] -= dt
            else:
                a["other_legs"] += 1
                a["other_sol"] += r["native"]
                a["moved_in_raw" if dt > 0 else "moved_out_raw"] += abs(dt)
    out = []
    for a in acc.values():
        held_raw = a["bought_raw"] + a["moved_in_raw"] - a["sold_raw"] - a["moved_out_raw"]
        out.append(
            {
                **a,
                "wallets": len(a["wallets"]),
                "levels": "+".join(sorted(a["levels"])),
                "residual_raw": held_raw,
                "open": a["bought_raw"] > 0 and held_raw * 1000 > a["bought_raw"],
                "net_before_tips": a["received"] - a["spent"] + a["other_sol"],
                "net_after_tips": a["received"] - a["spent"] + a["other_sol"] - a["tips"],
            }
        )
    return sorted(out, key=lambda x: -x["net_after_tips"])


def transfers(rows: list[dict[str, Any]], perimeter: set[str], levels: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    """Every SOL movement of the perimeter that is not a trade, by counterpart, and every token moved to another wallet."""
    out: dict[str, list[dict[str, Any]]] = {
        "DEPOSITS": [],
        "EXCHANGE_RETURNS": [],
        "INTERNAL": [],
        "EXTERNAL": [],
        "TOKEN_MOVES": [],
    }
    for r in sorted(rows, key=lambda x: x["slot"]):
        if not r["ok"]:
            continue
        for src, dst, lam, basis in r["edges"]:
            if r["tok"] or (src != r["w"] and dst != r["w"]):
                continue
            other = dst if src == r["w"] else src
            row = {
                "utc": utc(r["t"]),
                "slot": r["slot"],
                "sig": r["sig"],
                "from": src,
                "to": dst,
                "lamports": lam,
                "wallet_level": levels.get(r["w"]),
                "basis": basis,
            }
            if other == DEPOSIT:
                out["DEPOSITS"].append(row)
            elif other == HOT:
                out["EXCHANGE_RETURNS"].append(row)
            elif other in perimeter:
                if src == r["w"]:  # both ends are in the ledger: one row, kept on the sender's side
                    out["INTERNAL"].append(row)
            elif lam >= 1_000_000:
                out["EXTERNAL"].append(row)
        for m in r["moves"]:
            if (
                m.get("mint")
                and m["k"] == "spl"
                and not r["venues"]
                and r["w"] in (m["src"], m["dst"])
                and m["src"] != m["dst"]
                and "program" not in m
            ):
                out["TOKEN_MOVES"].append(
                    {
                        "utc": utc(r["t"]),
                        "slot": r["slot"],
                        "sig": r["sig"],
                        "mint": m["mint"],
                        "from": m["src"],
                        "to": m["dst"],
                        "raw": m["n"],
                        "seen_on": r["w"],
                        "other_in_perimeter": (m["dst"] if m["src"] == r["w"] else m["src"]) in perimeter,
                        "wallet_native_lamports": r["native"],
                    }
                )
    return out


def capital_path(rows: list[dict[str, Any]], perimeter: set[str]) -> dict[str, Any]:
    """Money entering and leaving the perimeter in order: the largest amount actually at work, against the gross turnover."""
    ev = []
    for r in rows:
        if not r["ok"] or r["tok"]:
            continue
        for src, dst, lam, _ in r["edges"]:
            other = dst if src == r["w"] else src
            if other not in perimeter:
                ev.append((r["slot"], lam if dst == r["w"] else -lam, r["t"]))
    ev.sort()
    cur = peak = 0
    trough = 0
    t_peak = t_trough = None
    for _, d, t in ev:
        cur += d
        if cur > peak:
            peak, t_peak = cur, t
        if cur < trough:
            trough, t_trough = cur, t
    return {
        "net_in_end": cur,
        "peak_net_in": peak,
        "peak_utc": utc(t_peak),
        "most_negative": trough,
        "most_negative_utc": utc(t_trough),
    }


def usd(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Each flow at the daily close of its own day: a valuation, not money received."""
    from .trades_2024 import SOL_USD

    px = {k: float(v) for k, v in json.loads(SOL_USD.read_text()).items()}
    tot: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    missing = 0
    for r in rows:
        day = utc(r["t"])[:10]
        if day not in px:
            missing += 1
            continue
        p = period_of(r["t"])
        k = r["class"]
        if k in ("buy", "sell", "token_other", "failed", "tip"):
            tot[p]["trading_after_tips"] += r["native"] / 1e9 * px[day]
        if k == "to_deposit":
            tot[p]["sent_to_deposit"] += r["native"] / 1e9 * px[day]
        if k == "from_hot":
            tot[p]["back_from_hot"] += r["native"] / 1e9 * px[day]
    return {"by_period": {p: dict(v) for p, v in tot.items()}, "rows_without_price": missing}


def main() -> int:
    led = ledger()
    perimeter, infra = set(led["candidates"]), set(led["infra"])
    rows = load()
    meta = json.loads((DERIVED / "token_meta.json").read_text())
    with open(PRIVATE / "TRADES_2024_2025.csv") as f:
        trips = list(csv.DictReader(f))
    cont = continuity(rows)
    cap = capital(rows, perimeter)
    cards = match_cards(trips, meta)
    attr = attribution(rows, cards, perimeter, infra)
    tip_sig, unattached = tips_of_legs(rows)
    levels = {a["wallet"]: a["level"] for a in attr}
    table = enrich_trips(trips, meta, levels, tip_sig, cards)
    _csv("TRADES_V2.csv", table)
    tokens = token_table(rows, meta, levels, tip_sig)
    _csv("TOKENS_V2.csv", tokens)
    trip_sum: dict[str, Counter[str]] = defaultdict(Counter)
    for t in table:
        c = trip_sum[t["wallet"]]
        c["trips"] += 1
        c["closed"] += t["closed"] == "True"
        c["realised_closed"] += int(t["realised_lamports"]) if t["closed"] == "True" else 0
        c["tips"] += t["jito_tips_lamports"]
    _csv(
        "WALLETS_V2.csv",
        [
            {
                "level": a["level"],
                "wallet": a["wallet"],
                "why": a["why"],
                "lookalike": a.get("lookalike", False),
                "cards": ",".join(sorted(set(a.get("cards", [])))),
                "deposits": a.get("deposits"),
                "deposit_lamports": a.get("deposit_lamports"),
                "first_deposit_sig": a.get("first_deposit_sig"),
                "hot_returns": a.get("hot_returns"),
                "hot_lamports": a.get("hot_lamports"),
                "first_hot_sig": a.get("first_hot_sig"),
                "token_rows": a.get("token_rows"),
                "tool_fee_rows": a.get("tool_fee_rows"),
                "direct_links": ";".join("%s:%s" % (o, v.get("sig")) for o, v in a.get("direct", {}).items()),
                "first_utc": a.get("first_utc"),
                "last_utc": a.get("last_utc"),
                **trip_sum[a["wallet"]],
            }
            for a in attr
        ],
    )
    for name, rs in transfers(rows, perimeter, levels).items():
        _csv("%s.csv" % name, rs)
    by_level: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        lv = levels[r["w"]]
        by_level[lv][period_of(r["t"]) + ":" + r["class"]] += r["native"]
    report = {
        "continuity": {**cont, "breaks": cont["breaks"][:50], "n_breaks": len(cont["breaks"])},
        "capital": cap,
        "tips_unattached_lamports": unattached,
        "by_level": {k: dict(v) for k, v in by_level.items()},
        "capital_path": capital_path(rows, perimeter),
        "usd": usd(rows),
    }
    write_private("derived/report_core.json", json.dumps(report, indent=1))
    write_private("derived/cards_v2.json", json.dumps(cards, indent=1))
    write_private("derived/attribution_v2.json", json.dumps(attr, indent=1))
    write_private("derived/tips_by_sig.json", json.dumps(tip_sig))
    print(
        "rows",
        len(rows),
        "continuity breaks",
        len(cont["breaks"]),
        "gap SOL",
        cont["sum_gap_lamports"] / 1e9,
        "tips unattached",
        unattached / 1e9,
    )
    print(Counter(a["level"] for a in attr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
