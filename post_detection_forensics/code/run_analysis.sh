#!/bin/sh
# Runs the steps of analysis_plan.md in order, on the frozen table only.
# ana_00_freeze.py is run once, by hand, before this script, and committed.
set -e
cd "$(dirname "$0")" || exit 1
test -f ../derived/TABLE_FREEZE.json || { echo "freeze the table first: python3 ana_00_freeze.py"; exit 1; }
for s in ana_10_descriptive ana_20_pairs ana_30_actor_premium ana_40_funding ana_50_profiles \
         ana_60_rules ana_70_ml ana_80_robust ana_90_verdict; do
    echo "== $s"
    python3 "$s.py" > "../tables/$s.log" 2>&1 || { echo "$s failed, see tables/$s.log"; exit 1; }
done
tail -3 ../tables/D9_verdict.md
