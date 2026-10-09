# POST HOC (declared after reading the sensitivity): robustness of the tradable hits without the largest
# U group, DISCOVERY vs SELECTION; and the pre-registered rule R3 inside that subpopulation.
import sys, os, json, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import ap_lib as A
import mech_48_absorption as Mx
import mech_47_team_rhythm as R
from collections import Counter
S, F = Mx.load()
series_all = Mx.pde.load_series(); series = {m: series_all.get(m, []) for m in S["mints"]}; del series_all
M = Mx.metrics(S, F, series)
Y, NET, ENTRY, _ = Mx.labels(S, series)
U, blocks = S["U"], S["blocks"]
big = max(Counter(U.tolist()).items(), key=lambda kv: kv[1])[0]
rng = np.random.default_rng(7)
d = json.load(open(A.TABLES + "/team_absorption.json"))
hits = sorted(((v["p"], k) for k, v in d["sensitivity"]["tradable_without_largest_group"].items() if v and v.get("p") is not None and v["p"] <= 0.05))
out = {"hits": {}, "rule_R3_nobig": {}}
ntest = 0
for p, k in hits:
    m, T = k.split("|"); T = int(T); c = Mx.T_DEC[T]
    y = Y["Y2_%d" % T]
    rows = Mx.team_rows(S, y, drop=(U == big))
    rec = {"p_sens": p}
    r = R.within_auc(M[m][c], y, U, rows, 0, rng); rec["auc"] = r["auc"]; rec["n"] = r["n"]; rec["teams"] = r["strata"]
    for b in ("DISC", "SEL"):
        rr = R.within_auc(M[m][c], y, U, rows[blocks[rows] == b], 2000, rng)
        rec["auc_" + b] = rr and rr["auc"]; rec["p_" + b] = rr and rr.get("p"); rec["n_" + b] = rr and rr["n"]; rec["teams_" + b] = rr and rr["strata"]
        ntest += 1
    rec["pooled_auc_nobig"] = R.pooled_auc(M[m][c], y, np.flatnonzero(~np.isnan(y) & (U != big)))
    out["hits"][k] = rec
disc = blocks == "DISC"
for T in (20, 30):
    c = Mx.T_DEC[T]; y = Y["Y2_%d" % T]; net = NET[T]
    thr = float(np.nanquantile(M["M3_ext_buy_sol_last10"][c][disc], 0.8))
    f = M["M3_ext_buy_sol_last10"][c] >= thr
    for pop, mask in (("nobig", U != big), ("big_only", U == big)):
        for b in ("DISC", "SEL"):
            mk = ~np.isnan(y) & f & mask & (blocks == b); el = ~np.isnan(y) & mask & (blocks == b)
            out["rule_R3_nobig"]["T%d_%s_%s" % (T, pop, b)] = {"n": int(mk.sum()), "good": int(np.nansum(y[mk])), "precision": float(np.nanmean(y[mk])) if mk.sum() else None,
                                                             "base": float(np.nanmean(y[el])), "net_500": float(np.nanmean(net[mk])) if (~np.isnan(net[mk])).sum() else None}
            ntest += 1
A.write_json(A.TABLES + "/team_absorption_posthoc_nobig.json", out)
A.registre("team_absorption_posthoc", ntest, "POST HOC: tradable sensitivity hits without the largest U group, by block; R3 inside that subpopulation", {"note": "declared after reading the sensitivity"}, n=0, declare=False, sortie="tables/team_absorption_posthoc_nobig.json")
print(json.dumps(out, indent=1))
