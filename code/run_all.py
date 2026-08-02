#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py -- re-run the dossier and report what reproduces.

    python3 code/run_all.py            # offline measurements (no key, ~2 min)
    python3 code/run_all.py --list     # what each script does, and what it needs
    python3 code/run_all.py --deps     # confirm stdlib-only
    python3 code/run_all.py --strict   # additionally fail if any committed
                                       # table/JSON changed (byte comparison)

--strict is the interesting mode. It snapshots every generated artefact, runs
everything, and diffs. A green run means the numbers in docs/ are exactly what
this code produces from this data -- not what they produced on some earlier
state of either.

Scripts needing the network or the unpublished corpus are listed but skipped;
their committed outputs are what the offline scripts consume.
"""
import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings  # noqa: E402

# (script, needs, one-line description)
#   needs: "" offline | "net" Helius key | "priv" unpublished corpus
PLAN = [
    ("p0_pitfalls_check.py", "", "recompute every figure quoted in docs/PITFALLS.md"),
    ("m1_corpus.py", "", "corpus perimeter: what is in it, what was dropped and why"),
    ("m2_entry_price.py", "", "entry price actually paid, vs the pool price"),
    ("m3_operators.py", "", "operator clusters by shared wallets, with the 3 attacks on the result"),
    ("m4_infra_ubiquity.py", "", "shared infrastructure: how much of the graph it fabricates"),
    ("m5_roundtrip.py", "", "round trip under 10 exit policies"),
    ("m6_horizon.py", "", "price at +1 h / +2 h / +4 h / +24 h"),
    ("t1_base_rate_sorties.py", "", "T1 base rate, 15 exit policies, cluster bootstrap"),
    ("t2_x2_par_prix_entree.py", "", "T2 doubling rate by entry price + denominator artefact"),
    ("t3_ath_avant_detection.py", "", "T3 share of tokens whose peak precedes first visibility"),
    ("t4_entree_post_snipe_20min.py", "", "T4 post-snipe entry, incl. the 'without the best token' column"),
    ("t5_horizon_1h_24h.py", "", "T5 horizon extension with the unit cross-check"),
    ("a1_null_model.py", "", "null distribution of the split detector's own criteria (P13)"),
    ("a2_recount.py", "", "every token recounted under the criteria that survive that null"),
    ("a3_hub_origin.py", "", "phase-1 hub: genesis, fan-out shape, upstream reached and not"),
    ("a4_selection_bias.py", "", "distance between the phase-1 cohort and a random sample"),
    ("a5_author_pattern.py", "", "presence test of the funding-dispatch pattern, token by token"),
    ("a6_gateway_chains.py", "", "dated chains: swap gateway -> distributor -> fresh wallets"),
    ("a7_cross_token_links.py", "", "are the per-token operations linked to each other?"),
    ("exit_ladder.py", "", "the exit ladder actually used, stated as executable policy"),
    ("a8_wallet_horde.py", "net", "what the funded wallets do AFTER the trade: die, or spawn"),
    ("v05_creation_block.py", "net", "creation-slot buy block, non-circular (needs the RPC cache)"),
    ("v06_curve_ladder.py", "net", "curve ladder: SOL spent, share of supply"),
    ("fetch_sol_usd.py", "net", "SOL/USDC hourly series (no key, GeckoTerminal)"),
    ("fetch_gt_ohlcv.py", "net", "per-token OHLCV (no key, GeckoTerminal)"),
    ("v01_corpus.py", "priv", "corpus reconciliation against the raw capture files"),
    ("v02_fleets.py", "priv", "wallet fleets in the creation window"),
    ("v03_onchain_slot.py", "priv", "on-chain re-read of the creation slot"),
    ("v04_slot_order.py", "priv", "intra-slot ordering, AMM opening price"),
    ("v07_exit.py", "net", "bag transfer and liquidation in tranches"),
    ("v08_ages.py", "net", "wallet birth dates and batch creation"),
    ("v1_probe_addresses.py", "net", "existence and activity of the quoted infrastructure addresses"),
    ("v2_dispatcher_burst.py", "net", "geometry of a funding burst"),
    ("r1_dust_vs_funding.py", "net", "dust vs funding: kills 'N wallets funded in T seconds'"),
    ("r1_burst_window.py", "net", "burst geometry over an explicit time window"),
    ("09_bundle_snipe.py", "net", "creation-slot buyback rate, and whether it depends on the date"),
    ("f_figures_resultats.py", "fig", "redraw figures/*.png (matplotlib)"),
    ("f_signature_gros_tokens.py", "fig", "redraw the creation-signature figure (matplotlib)"),
]

ARTEFACT_DIRS = [settings.TABLES, settings.OUT,
                 os.path.join(settings.DATA, "cout_acheteur")]


def snapshot(dst):
    for d in ARTEFACT_DIRS:
        if os.path.isdir(d):
            shutil.copytree(d, os.path.join(dst, os.path.basename(d)),
                            dirs_exist_ok=True)


def compare(snap):
    changed = []
    for d in ARTEFACT_DIRS:
        base = os.path.join(snap, os.path.basename(d))
        if not os.path.isdir(base):
            continue
        for n in sorted(os.listdir(base)):
            a, b = os.path.join(base, n), os.path.join(d, n)
            if not os.path.exists(b) or not filecmp.cmp(a, b, shallow=False):
                changed.append(os.path.relpath(b, settings.ROOT))
    return changed


# Third-party imports that are allowed, with the reason. Anything outside this
# set makes --deps fail: "stdlib only" is a claim the repository has to keep.
OPTIONAL = {"matplotlib": "figures only (code/f_*.py); no measurement uses it"}


def deps():
    """Confirm no unexpected third-party import anywhere in code/."""
    import ast
    local = {os.path.splitext(f)[0] for f in os.listdir(settings.CODE)
             if f.endswith(".py")}
    stdlib = set(getattr(sys, "stdlib_module_names", ())) or set()
    third = {}
    for f in sorted(os.listdir(settings.CODE)):
        if not f.endswith(".py"):
            continue
        tree = ast.parse(open(os.path.join(settings.CODE, f)).read())
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                names = [node.module.split(".")[0]]
            for n in names:
                if n not in local and (stdlib and n not in stdlib):
                    third.setdefault(n, []).append(f)
    unexpected = {k: v for k, v in third.items() if k not in OPTIONAL}
    for k in sorted(set(third) & set(OPTIONAL)):
        print("  optional  %-14s %-28s (%s)"
              % (k, ", ".join(sorted(set(third[k]))), OPTIONAL[k]))
    if unexpected:
        print("UNDECLARED third-party imports:")
        for k, v in sorted(unexpected.items()):
            print("  %-20s %s" % (k, ", ".join(sorted(set(v)))))
        return 1
    print("  %d modules under code/, 0 undeclared third-party import "
          "(every measurement is stdlib-only)" % len(local))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--deps", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--with-net", action="store_true",
                    help="also run the scripts that hit the RPC / the caches")
    ap.add_argument("--with-figures", action="store_true",
                    help="also redraw figures/ (requires matplotlib)")
    a = ap.parse_args()

    if a.deps:
        sys.exit(deps())

    if a.list:
        for name, need, desc in PLAN:
            tag = {"": "offline", "net": "network", "priv": "raw corpus",
                   "fig": "figures"}[need]
            print("  %-32s [%-10s] %s" % (name, tag, desc))
        print("\n  offline = data/ only, no key, no network.")
        return

    has_key = bool(settings.helius_keys())
    has_priv = bool(settings.private_root())

    snap = tempfile.mkdtemp(prefix="runall_") if a.strict else None
    if snap:
        snapshot(snap)

    ran, skipped, failed = [], [], []
    for name, need, _desc in PLAN:
        if need == "priv" and not has_priv:
            skipped.append((name, "needs $PUMP_PRIVATE_ROOT"))
            continue
        if need == "fig" and not a.with_figures:
            skipped.append((name, "needs --with-figures (matplotlib)"))
            continue
        if need == "net" and not (a.with_net or has_key):
            skipped.append((name, "needs $HELIUS_API_KEYS or --with-net"))
            continue
        t0 = time.time()
        p = subprocess.run([sys.executable, os.path.join(settings.CODE, name)],
                           capture_output=True, text=True)
        dt = time.time() - t0
        if p.returncode == 0:
            ran.append((name, dt))
            print("  ok    %-32s %5.1f s" % (name, dt))
        else:
            failed.append((name, (p.stderr or "").strip().splitlines()[-1:] or [""]))
            print("  FAIL  %-32s %5.1f s" % (name, dt))

    print("\n%d ran, %d skipped, %d failed" % (len(ran), len(skipped), len(failed)))
    for name, why in skipped:
        print("  skipped %-30s %s" % (name, why))
    for name, err in failed:
        print("  failed  %-30s %s" % (name, err[0][:120]))

    rc = 1 if failed else 0
    if snap:
        changed = compare(snap)
        if changed:
            print("\n%d committed artefact(s) changed on re-run:" % len(changed))
            for c in changed:
                print("   ", c)
            rc = 1
        else:
            print("\nevery committed table and JSON reproduced byte for byte")
        shutil.rmtree(snap, ignore_errors=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
