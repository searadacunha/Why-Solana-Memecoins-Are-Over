#!/usr/bin/env python3
"""A mechanical exit ladder, stated as executable code — and measured.

WHAT THIS FILE IS, AND WHAT IT IS NOT
-------------------------------------
It is not a reconstruction of how the 2024 trades were closed. Those exits were discretionary:
take-profits set by eye, one trade at a time (docs/EXPLOITATION.md section 3). The only automated
part was standing sell orders at x5 and x10 for the hours away from the screen. That automation was
an upside catcher, not a stop: if the price never reached x5, nothing sold. It did nothing whatsoever
for the downside, and an unattended position ran with the stake still in the market. The x2 was used
after a token had graduated off the bonding curve, on large positions. The size sold at any level was
never recorded.

What this file states is a MECHANICAL policy of the kind a reader will naturally propose in place of
judgement: sell fixed fractions at fixed multiples of entry, written out precisely enough to be
applied to real price paths and scored.

    x2   -> sell 50 %
    x5   -> sell 25 %
    x10  -> sell 15 %
    beyond -> never sold by this policy

The 50 / 25 / 15 split is stipulated by this script and sourced nowhere else. Fixing the numbers is
what makes a policy testable; it is not a claim that these were the numbers. Do not quote them as
anyone's configuration.

WHY IT IS STILL WORTH MEASURING
-------------------------------
Because "could a rule have done this?" has an answer, and the answer is the point of the repository.

    2026 corpus, measured in code/t1_base_rate_sorties.py:
        0 of 15 exit policies have a positive mean return
        0 of 15 have a 95 % CI clearing zero

Scope, stated exactly: those fifteen are all single full exits — five timeouts, three trailing stops,
six take-profit / stop-loss variants, and buy-and-hold. A staged ladder like the one above is not
among them, and no backtest of a staged ladder exists in this repository. What the fifteen establish
is broader and more useful: on 2026 launches, no exit rule tested rescues an unfiltered entry. The
exit is not where the problem is. The entry is — the curve is bought out in the creation slot, and
there is nothing left to climb.

The headline numbers below are derived from the committed artefacts at run time, not asserted here.

USAGE
    python3 code/exit_ladder.py                    # the policy under test, and the 2026 verdict
    python3 code/exit_ladder.py --path 1 2.4 7 3   # apply it to a price path (multiples of entry)
"""
from __future__ import annotations
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# A MECHANICAL policy under test: (multiple of entry, share of the ORIGINAL position sold there).
# NOT a record of what was executed. The levels x5 and x10 are the ones that were configured for
# unattended trading in 2024; x2 was used post-graduation, on large positions. The three SHARES have
# no source in this repository, and no tranche size was ever confirmed: they are fixed here only so
# the policy is executable and the simulation reproducible. Do not quote them as tranche sizes that
# were used. See docs/EXPLOITATION.md section 3.
LADDER = [(2.0, 0.50), (5.0, 0.25), (10.0, 0.15)]
NEVER_SOLD = 1.0 - sum(p for _, p in LADDER)  # the 10 % this policy never sells


def simulate(path, ladder=LADDER):
    """Apply the ladder to a price path expressed in multiples of the entry price.

    Returns the realised multiple on the whole position. The unsold remainder is marked to the last
    price in the path — a convention, and stated as one: in reality that tranche is discretionary,
    and 'touched but not sold' is exactly the confusion PITFALLS P5 was written about.
    """
    sold, proceeds, hit = 0.0, 0.0, []
    for mult in path:
        for rung, share in ladder:
            if mult >= rung and rung not in hit:
                hit.append(rung)
                sold += share
                proceeds += share * rung
    rest = 1.0 - sold
    proceeds += rest * path[-1]
    return {"realised_multiple": round(proceeds, 4), "sold_on_ladder": round(sold, 4),
            "remainder_at_last_price": round(rest, 4), "rungs_hit": hit}


def _artefact(*parts):
    p = os.path.join(DATA, *parts)
    if not os.path.exists(p):
        raise SystemExit(f"missing artefact: {p} — run the script that produces it first")
    return json.load(open(p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", nargs="*", type=float,
                    help="price path in multiples of entry, e.g. 1 2.4 7 3")
    a = ap.parse_args()

    print("MECHANICAL LADDER UNDER TEST (stipulated here, not an execution record)")
    cum = 0.0
    for rung, share in LADDER:
        cum += share
        print(f"  x{rung:<5g} sell {share:.0%}   (cumulative {cum:.0%})")
    print(f"  beyond   {NEVER_SOLD:.0%} remainder, never sold by this policy")
    print("\n  The 2024 exits were discretionary: take-profits set by eye, one trade at a time.")
    print("  The only automated part was standing sell orders at x5 and x10 for the hours away")
    print("  from the screen — an upside catcher, not a stop: if the price never reached x5,")
    print("  nothing sold, and an unattended position ran with the stake still in the market.")
    print("  The x2 was used after a token had left the bonding curve, on large positions. No")
    print("  tranche size was ever recorded: the 50/25/15 above are this script's hypothesis,")
    print("  fixed so the policy can be measured, and are nobody's configuration. See")
    print("  docs/EXPLOITATION.md section 3.")

    if a.path:
        r = simulate(a.path)
        print(f"\nPATH {a.path}")
        print(f"  rungs hit                : {r['rungs_hit'] or 'none'}")
        print(f"  sold on the ladder       : {r['sold_on_ladder']:.0%}")
        print(f"  remainder at last price  : {r['remainder_at_last_price']:.0%}")
        print(f"  REALISED MULTIPLE        : {r['realised_multiple']:.3f}x")

    # --- what the repository measures on current launches -------------------------------------
    # All figures below are read from the committed artefacts, never asserted here.
    d = _artefact("cout_acheteur", "t1_base_rate_sorties.json")
    pol = d.get("politiques") or d.get("policies")
    if isinstance(pol, dict):
        pol = [{"nom": k, **v} for k, v in pol.items()]
    if not isinstance(pol, list) or not pol:
        raise SystemExit(f"'politiques' unusable in t1_base_rate_sorties.json: {type(pol).__name__}")
    n_pos = sum(1 for x in pol if x["moyenne_pct"] > 0)
    n_ci = sum(1 for x in pol if x["moyenne_ic95_cluster_pct"][0] > 0)

    t5 = _artefact("cout_acheteur", "t5_horizon_1h_24h.json")["horizons"]
    ath = _artefact("t3_ath_avant_detection.json")["bandes"]["_toutes_bandes"]

    print("\nWHAT THE MEASUREMENTS SAY OF ANY MECHANICAL POLICY ON 2026 LAUNCHES")
    print(f"  exit policies tested (single full exits)     : {len(pol)}")
    print(f"  of which positive mean return                : {n_pos}")
    print(f"  of which 95 % CI of the mean clears zero     : {n_ci}")
    print(f"  entering after the snipe, +1 h               : "
          f"{t5['1']['mult_median']:.2f}x  (median, docs/tables/T5)")
    print(f"  entering after the snipe, +24 h              : "
          f"{t5['24']['mult_median']:.2f}x")
    print(f"  tokens that peaked before becoming visible   : "
          f"{ath['ath_avant_detection_pct']:.1f} %")
    print("\n  Those policies are all single full exits: the staged ladder above is not among")
    print("  them and is not backtested anywhere in this repository.")
    print("\n  It is not an exit policy that degraded, it is the market. On current launches the")
    print("  curve is bought out in the creation slot (42/42 verified): by the time a launch is")
    print("  visible, the position is no longer being accumulated, it is being distributed.")
    print("  There is no rung to climb — for any policy, not just this one.")
    print("\n  See docs/RESULTATS.md and docs/EXPLOITATION.md section 6.")


if __name__ == "__main__":
    main()
