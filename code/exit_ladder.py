#!/usr/bin/env python3
"""A mechanical exit ladder, written as code so it can be run against price paths and scored.

    x2   -> sell 50 %
    x5   -> sell 25 %
    x10  -> sell 15 %
    beyond -> never sold by this policy

Not a record of how the 2024 trades were closed. Those exits were discretionary, take-profits set
by eye one trade at a time; the only automation was standing sell orders at x5 and x10 for the
hours away from the screen, an upside catcher rather than a stop, since nothing sold if the price
never reached x5 and the unattended position kept its stake in the market. The x2 was used after a
token had graduated off the bonding curve, on large positions, and the size sold at any level was
never recorded. The 50 / 25 / 15 split is stipulated by this script and sourced nowhere else:
fixed numbers make the policy testable, they are nobody's configuration and must not be quoted as
one. See docs/EXPLOITATION.md section 3.

On the 2026 corpus, code/t1_base_rate_sorties.py finds 0 of 15 exit policies with a positive mean
return and 0 of 15 whose 95 % CI clears zero. All fifteen are single full exits (five timeouts,
three trailing stops, six take-profit / stop-loss variants, buy-and-hold), so the staged ladder
above is not among them and is backtested nowhere in this repository. On 2026 launches no exit
rule tested rescues an unfiltered entry: the curve is bought out in the creation slot, so there is
nothing left to climb. The figures printed below are read from the committed artefacts at run time.

Usage:
    python3 code/exit_ladder.py                    # the policy under test, and the 2026 verdict
    python3 code/exit_ladder.py --path 1 2.4 7 3   # apply it to a price path (multiples of entry)
"""
from __future__ import annotations
import argparse, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")

# The policy under test: (multiple of entry, share of the original position sold there). This is
# a hypothesis, not a record of what was executed. The x5 and x10 levels are the ones configured
# for unattended trading in 2024; x2 was used post-graduation, on large positions. The three shares
# have no source in this repository, and no tranche size was ever confirmed: they are fixed here so
# the policy is executable and the simulation reproducible. Do not quote them as tranche sizes that
# were used. See docs/EXPLOITATION.md section 3.
LADDER = [(2.0, 0.50), (5.0, 0.25), (10.0, 0.15)]
NEVER_SOLD = 1.0 - sum(p for _, p in LADDER)  # the 10 % this policy never sells


def simulate(path, ladder=LADDER):
    """Apply the ladder to a price path expressed in multiples of the entry price.

    Returns the realised multiple on the whole position. Marking the unsold remainder to the last
    price in the path is a convention: in reality that tranche is discretionary, and 'touched but
    not sold' is the confusion PITFALLS P5 was written about.
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
        raise SystemExit(f"missing artefact: {p}, run the script that produces it first")
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
    print("  from the screen, an upside catcher rather than a stop: if the price never reached")
    print("  x5, nothing sold, and an unattended position ran with the stake still in the market.")
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
    print("\n  What degraded is the market, not the exit policy. On current launches the curve is")
    print("  bought out in the creation slot (42/42 verified): by the time a launch is visible,")
    print("  the position is no longer being accumulated, it is being distributed. There is no")
    print("  rung left to climb, for any policy, not just this one.")
    print("\n  See docs/RESULTATS.md and docs/EXPLOITATION.md section 6.")


if __name__ == "__main__":
    main()
