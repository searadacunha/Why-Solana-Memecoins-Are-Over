#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""feat_25_derived.py -- a few new decision-time features suggested by the external-repo audit.

Per-sniper conjunctions that launch-level atoms cannot express (a rule ANDs launch aggregates, not
facts about the same wallet), and the burstiness of the pre-alert buys. Sources: sc_table snipers[]
(every field is strictly before the sniper's buy, no hub flag is used) and cd_table early[]
(records with pre_alert and block time <= alert - 1 s only). No outcome is read.

  x_motif_ffs_n / _share   snipers that are at once first-funded (genesis funder = last sender,
                           <= 2 earlier transactions), funded <= 5 min before the buy, and funded by
                           a sender shared with another sniper of the launch     [create -> fund -> buy]
  x_motif_fs60_n           snipers funded <= 60 s before the buy by a shared sender
  x_motif_seasoned_indep_n snipers with >= 50 earlier transactions and a sender nobody else shares
  x_burst_pre              Goh-Barabasi burstiness (sd - mean) / (sd + mean) of the slot gaps between
                           consecutive pre-alert buys after the creation slot (>= 6 buys)
  x_pre_slot_peak_share    largest share of those buys landing in one slot
"""
from __future__ import annotations

import os
from collections import Counter

import numpy as np

import ap_lib as A


def main() -> None:
    base = {b["mint"]: b for b in A.load_base()}
    out = {m: {"mint": m} for m in base}
    for r in A.jl(A.SC_TABLE):
        sn = [s for s in r["snipers"] if s.get("role") == "core"]
        f = out[r["mint"]]
        need = ("last_sender", "last_age_s", "n_prior")
        obs = [s for s in sn if all(s.get(k) is not None for k in need)]
        if not sn or len(obs) < len(sn):      # like sc_table: null unless every sniper is observed
            for k in ("x_motif_ffs_n", "x_motif_ffs_share", "x_motif_fs60_n", "x_motif_seasoned_indep_n"):
                f[k] = None
            continue
        cnt = Counter(s["last_sender"] for s in obs)
        ffs = fs60 = seas = 0
        for s in obs:
            shared = cnt[s["last_sender"]] >= 2
            first = s.get("gen_funder") == s["last_sender"] and s["n_prior"] <= 2
            ffs += bool(first and s["last_age_s"] <= 300 and shared)
            fs60 += bool(s["last_age_s"] <= 60 and shared)
            seas += bool(s["n_prior"] >= 50 and not shared)
        f.update(x_motif_ffs_n=float(ffs), x_motif_ffs_share=ffs / len(obs), x_motif_fs60_n=float(fs60),
                 x_motif_seasoned_indep_n=float(seas))
    for r in A.jl(A.CD_TABLE):
        f = out[r["mint"]]
        t = base[r["mint"]]["t"]
        slots = sorted(x["slot"] for x in r["early"] if x.get("pre_alert") and x["bt"] <= t - 1 and x["slot"] > r["slot0"])
        f["x_burst_pre"] = f["x_pre_slot_peak_share"] = None
        if len(slots) >= 6:
            gaps = np.diff(slots).astype(float)
            mu, sd = gaps.mean(), gaps.std()
            f["x_burst_pre"] = float((sd - mu) / (sd + mu)) if (sd + mu) > 0 else None
            f["x_pre_slot_peak_share"] = max(Counter(slots).values()) / len(slots)
    rows = [out[m] for m in out]
    A.write_jl(os.path.join(A.DERIVED, "feat_derived.jsonl.gz"), rows)
    names = [k for k in rows[0] if k != "mint"]
    for k in names:
        print("%-26s non-null %d" % (k, sum(1 for r in rows if r.get(k) is not None)))


if __name__ == "__main__":
    main()
