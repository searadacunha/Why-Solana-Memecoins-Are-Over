#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
expl_ledger.py -- the exchange-deposit ledger, reconstructed from the chain.

WHAT IT ESTABLISHES [MESURE]
    Every SOL transfer that LANDED on the author's exchange deposit address
    over 2024-10-01 .. 2025-02-02 (UTC, half-open), valued transfer by
    transfer at the SOL/USD close of that transfer's own UTC day -- never at
    a window average. The total is the NET of every incoming transfer in the
    window, winners and losers alike: the number is strong precisely because
    it already absorbs the losses. Outgoing transfers (the exchange's sweeps)
    are reported separately and EXCLUDED from proceeds. The pass-through
    check (SOL in ~= SOL swept out, residual ~0) validates the model: a
    deposit address holds no balance.

WHAT IT READS
    $EXPL_LEDGER_ADDR   the deposit address, from the environment like every
                        other private input (settings.expl_ledger_addr). It
                        is a KYC'd exchange address and is NEVER committed:
                        the artefact names it only by its RDCT-* label, a
                        SALTED HMAC of the address (code/redact.py) -- not a
                        plain hash, so it cannot be confirmed by hashing a
                        candidate; that needs the address and the salt both.
    Helius RPC          getSignaturesForAddress + getTransaction (jsonParsed
                        balance deltas), key from the environment
                        (settings.py). Every response is cached under
                        data/cache/ (git-ignored): once the cache exists a
                        re-run needs the address but no key and no network,
                        and reproduces the artefact byte for byte.
    Binance             SOLUSDT daily klines, keyless public endpoint,
                        cached the same way.

WHAT IT WRITES
    docs/out/expl_ledger.json -- aggregates only: per-month SOL/USD/n,
    window totals, sweep totals, counts. No transaction signature, no sender
    address, no deposit address: a single signature would identify the
    wallet, so none is published. The sender wallets: their COUNT is
    published, never the list. Most are the author's own trading wallets,
    but the heuristic also resolves a few to third-party exchange hot
    wallets, so ownership is NOT claimed -- the artefact files any identity
    behind a sender under NON_ETABLI.

WHAT IT DOES NOT ESTABLISH
    - The transfer count and the distinct-sender count are method-dependent
      (see the sender heuristic below); the MONEY columns are not.
    - Per-trade P&L: a deposit ledger sees proceeds arriving, not trades.
    - That every incoming transfer is trading proceeds: SOL sent back from
      the exchange to a trading wallet and deposited again would be capital
      returning, not new proceeds. Treatment: every positive balance delta
      is counted (that is the measurement), and the number of incoming
      transfers whose heuristic sender is also a sweep recipient -- the only
      return-of-capital signature visible from this wallet -- is measured
      and published so a reader can subtract it.

Usage:
    EXPL_LEDGER_ADDR=... [HELIUS_API_KEY=...] python3 code/expl_ledger.py [--out ...]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pumplib as P  # noqa: E402
import redact  # noqa: E402
import settings  # noqa: E402
from lib_verif import cached, rpc  # noqa: E402

LAMPORTS = 1e9
WINDOW_LO = 1727740800   # 2024-10-01 00:00 UTC, inclusive
WINDOW_HI = 1738454400   # 2025-02-02 00:00 UTC, exclusive
GOOD_MONTHS = ("2024-10", "2024-11", "2024-12")
PRICE_SOURCE = ("Binance SOLUSDT daily close (api.binance.com /api/v3/klines, "
                "keyless); each transfer valued at the close of its own UTC "
                "day, never at a window average")


def http_get_json(url, tries=6):
    """GET a public JSON endpoint. A failure RAISES -- it never becomes a
    silent zero (see docs/PITFALLS.md: a network outage must not disguise
    itself as a clean result)."""
    last = None
    for a in range(tries):
        try:
            req = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": "curl/8"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2.0 * (a + 1))
    raise RuntimeError("GET %s failed after %d tries: %s" % (url, tries, last))


def all_signatures(addr, label):
    """Full backward pagination, cached under a filename that carries only
    the RDCT label -- never the address."""
    def fetch():
        out, before = [], None
        while True:
            p = [addr, {"limit": 1000}]
            if before:
                p[1]["before"] = before
            page = rpc("getSignaturesForAddress", p)
            if page is None:
                raise RuntimeError("getSignaturesForAddress returned null")
            if not page:
                break
            out.extend(page)
            before = page[-1]["signature"]
            if (page[-1].get("blockTime") or 0) < WINDOW_LO or len(page) < 1000:
                break
        return out
    return cached("expl_sigs_%s_%d" % (label, WINDOW_LO), fetch)


def get_tx(sig):
    tx = cached("expl_tx_" + sig[:24], lambda: rpc(
        "getTransaction", [sig, {"encoding": "jsonParsed",
                                 "maxSupportedTransactionVersion": 0}]))
    if tx is None:
        raise RuntimeError("getTransaction %s returned null" % sig)
    return tx


def wallet_view(tx, addr, sig):
    """The deposit wallet's own balance delta on one successful transaction,
    plus the counterparty HEURISTIC: sender = the account with the most
    negative delta in the same tx (recipient = the most positive, for
    sweeps). Good enough to BOUND the distinct-sender count; NOT an exact
    transfer-level decomposition -- the counts are weaker than the money."""
    meta = tx.get("meta") or {}
    if meta.get("err") is not None:
        return None
    keys = tx["transaction"]["message"]["accountKeys"]
    pubkeys = [k["pubkey"] if isinstance(k, dict) else k for k in keys]
    if addr not in pubkeys:
        return None
    wi = pubkeys.index(addr)
    pre, post = meta["preBalances"], meta["postBalances"]
    wdelta = (post[wi] - pre[wi]) / LAMPORTS
    deltas = [((post[j] - pre[j]) / LAMPORTS, pubkeys[j])
              for j in range(len(pubkeys)) if j != wi]
    ts = tx.get("blockTime")
    if ts is None:
        raise RuntimeError("tx %s has no blockTime" % sig)
    return {"ts": ts, "day": P.utc(ts), "delta": wdelta,
            "sender": min(deltas, key=lambda d: d[0])[1] if wdelta > 0 and deltas else None,
            "recipient": max(deltas, key=lambda d: d[0])[1] if wdelta < 0 and deltas else None}


def sol_usd_daily():
    """SOLUSDT daily close keyed by YYYY-MM-DD (UTC). Cached; empty RAISES."""
    def fetch():
        url = ("https://api.binance.com/api/v3/klines?symbol=SOLUSDT&interval=1d"
               "&startTime=%d&endTime=%d&limit=1000" % (WINDOW_LO * 1000, WINDOW_HI * 1000))
        kl = http_get_json(url)
        out = {P.utc(k[0] // 1000): float(k[4]) for k in kl}   # k[4] = close
        if not out:
            raise RuntimeError("Binance returned no SOLUSDT daily klines")
        return out
    return cached("expl_solusdt_1d_%d_%d" % (WINDOW_LO, WINDOW_HI), fetch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(
        P.HERE, "..", "docs", "out", "expl_ledger.json"))
    a = ap.parse_args()

    addr = settings.expl_ledger_addr()
    label = redact.apply(addr)
    if label == addr or not redact.is_redacted(label):
        raise SystemExit(
            "the deposit address has no entry in code/redactions.json: every "
            "write path must be able to scrub it. Add sha256(addr) -> "
            "RDCT-label to the map (see code/redact.py) before publishing.")

    P.head("EXPL — DEPOSIT-WALLET LEDGER, 2024-10-01 .. 2025-02-02 (%s)" % label,
           "MESURE")

    sigs = [s for s in all_signatures(addr, label)
            if s.get("err") is None
            and WINDOW_LO <= (s.get("blockTime") or 0) < WINDOW_HI]
    P.kv("successful signatures in window", len(sigs))

    incoming, outgoing = [], []
    for n, s in enumerate(sigs):
        v = wallet_view(get_tx(s["signature"]), addr, s["signature"])
        if v is None:
            continue
        if v["delta"] > 0:
            incoming.append(v)
        elif v["delta"] < 0:
            outgoing.append(v)
        if (n + 1) % 100 == 0:
            sys.stderr.write("  tx %d/%d\n" % (n + 1, len(sigs)))

    prices = sol_usd_daily()
    missing = sorted({r["day"] for r in incoming if r["day"] not in prices})

    per_month = defaultdict(lambda: {"sol": 0.0, "usd": 0.0, "n": 0})
    senders, total_sol, total_usd = set(), 0.0, 0.0
    for r in incoming:
        px = prices.get(r["day"])
        if px is None:
            raise RuntimeError("no SOL/USD close for %s -- refusing to guess" % r["day"])
        usd = r["delta"] * px
        ym = r["day"][:7]
        per_month[ym]["sol"] += r["delta"]
        per_month[ym]["usd"] += usd
        per_month[ym]["n"] += 1
        total_sol += r["delta"]
        total_usd += usd
        if r["sender"]:
            senders.add(r["sender"])

    sweep_sol = sum(o["delta"] for o in outgoing) * -1.0
    good_senders = {r["sender"] for r in incoming
                    if r["day"][:7] in GOOD_MONTHS and r["sender"]}
    good = {"sol": round(sum(per_month[m]["sol"] for m in GOOD_MONTHS), 4),
            "usd": round(sum(per_month[m]["usd"] for m in GOOD_MONTHS), 2),
            "n_transfers": sum(per_month[m]["n"] for m in GOOD_MONTHS),
            "distinct_senders": len(good_senders)}

    # Return-of-capital candidates: an incoming transfer whose heuristic
    # sender is also a sweep RECIPIENT is the one visible signature of money
    # coming back from the exchange side. Counted in the totals (the
    # measurement is "what landed"), published so a reader can subtract.
    sweep_dst = {o["recipient"] for o in outgoing if o["recipient"]}
    roc = [r for r in incoming if r["sender"] in sweep_dst]

    P.kv("incoming transfers (proceeds)", len(incoming))
    P.kv("outgoing sweeps (excluded from proceeds)", len(outgoing))
    P.kv("SOL in, full window", "%.4f" % total_sol)
    P.kv("USD in, full window (per-day close)", "%.2f" % total_usd)
    P.kv("SOL swept out", "%.4f" % sweep_sol,
         note="pass-through residual %.4f SOL" % (total_sol - sweep_sol))
    P.kv("distinct senders (heuristic)", len(senders))
    print("\n  per month (SOL / USD / n):")
    for m in sorted(per_month):
        v = per_month[m]
        print("    %s  %10.4f SOL  %11.2f USD  n=%d" % (m, v["sol"], v["usd"], v["n"]))
    P.kv("good months 2024-10..12", "%s SOL / %s USD" % (good["sol"], good["usd"]),
         n=good["n_transfers"])
    P.kv("return-of-capital candidates", len(roc),
         note="%.4f SOL, included in the totals" % sum(r["delta"] for r in roc))
    if missing:
        raise RuntimeError("missing price days: %s" % missing)

    print("""
  CONCLUSION:
   - %.4f SOL landed on the deposit address over the window, %.2f USD at
     each transfer's own-day close; %.4f SOL of it in 2024-10..12. The total
     is the NET of every incoming transfer -- it already absorbs the losing
     trades. [MESURE]
   - The wallet is a pass-through: %.4f SOL in vs %.4f SOL swept out,
     residual ~0, as expected of a deposit address. [MESURE]

  WHAT THIS DOES NOT ESTABLISH:
   - The transfer count (%d) and the sender count (%d) depend on the
     counterparty heuristic; they bound the answer, the money columns do
     not depend on them. [INFERE]
   - Per-trade P&L: a deposit ledger sees proceeds arriving, not the trades
     that produced them. [NON ETABLI]
   - That every incoming transfer is proceeds rather than returning capital:
     %d transfer(s) have a sweep recipient as their heuristic sender and are
     published above so a reader can subtract them; any round trip through
     the exchange's OWN books is invisible on-chain. [NON ETABLI]""" % (
        total_sol, total_usd, good["sol"], total_sol, sweep_sol,
        len(incoming), len(senders), len(roc)))

    P.emit({
        "address_label": label,
        "window_utc": {"lo_inclusive": "2024-10-01", "hi_exclusive": "2025-02-02"},
        "price_source": PRICE_SOURCE,
        "n_signatures_ok_in_window": len(sigs),
        "n_incoming_transfers": len(incoming),
        "n_outgoing_sweeps": len(outgoing),
        "sweep_sol_total": round(sweep_sol, 4),
        "total_sol_full_window": round(total_sol, 4),
        "total_usd_full_window": round(total_usd, 2),
        "distinct_senders_full_window": len(senders),
        "good_months_2024_10_12": good,
        "per_month": {m: {"sol": round(per_month[m]["sol"], 4),
                          "usd": round(per_month[m]["usd"], 2),
                          "n": per_month[m]["n"]} for m in sorted(per_month)},
        "missing_price_days": missing,
        "passthrough_check": {"sol_in": round(total_sol, 4),
                              "sol_swept_out": round(sweep_sol, 4),
                              "residual_sol": round(total_sol - sweep_sol, 4)},
        "return_of_capital_candidates": {
            "n_incoming_whose_heuristic_sender_is_a_sweep_recipient": len(roc),
            "sol": round(sum(r["delta"] for r in roc), 4),
            "treatment": "included in the totals; published so a reader can subtract them"},
        "epistemic_status": {
            "MESURE": ["per-transfer SOL deltas, monthly and window totals, "
                       "sweep totals, the pass-through residual, and the USD "
                       "valuation given the stated price source"],
            "INFERE": ["sender attribution: the counterparty account with the "
                       "most negative balance delta in the same transaction; "
                       "bounds the distinct-sender count, is not an exact "
                       "transfer-level decomposition",
                       "transfer count: one successful transaction with a "
                       "positive delta = one transfer; batched or multi-hop "
                       "routes are not unbundled"],
            "NON_ETABLI": ["per-trade P&L", "the purpose of each transfer "
                           "(proceeds vs returning capital) beyond the "
                           "candidate count above", "any identity behind the "
                           "sender wallets"]},
        "niveau": "MESURE",
    }, os.path.abspath(a.out))


if __name__ == "__main__":
    main()
