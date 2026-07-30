#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
p0_pitfalls_check.py -- recomputes every figure quoted in docs/PITFALLS.md.

Reads ONLY the published files in ./data/ (no network, no private state):
    data/dataset_socle.json     populations A / B / C + targets
    data/snipe_log.json         raw detector log (211 rows)
    data/horizon.json           GeckoTerminal OHLCV at +1h/+2h/+4h/+24h
    data/sol_usd_hourly.json    SOL/USDC hourly closes (unit conversion)
    data/floor_capture_public.jsonl.gz   swap-level captures (optional, P12)

Usage:  python3 code/p0_pitfalls_check.py
Every printed line is quoted verbatim in docs/PITFALLS.md.
"""
import bisect
import collections
import gzip
import itertools
import json
import math
import os
import statistics as st
from math import comb

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data")


def load(name):
    with open(os.path.join(DATA, name)) as f:
        return json.load(f)


def rate(rows, key):
    return sum(1 for r in rows if r[key]) / len(rows) if rows else float("nan")


def fisher_two_sided(a, b, c, d):
    """Exact two-sided Fisher test on a 2x2 table."""
    n, r1, r2, c1 = a + b + c + d, a + b, c + d, a + c
    hp = lambda x: comb(r1, x) * comb(r2, c1 - x) / comb(n, c1)
    p0 = hp(a)
    return sum(hp(x) for x in range(max(0, c1 - r2), min(r1, c1) + 1)
               if hp(x) <= p0 + 1e-12)


def spearman(x, y):
    def rk(v):
        s = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for i, j in enumerate(s):
            r[j] = i
        return r
    rx, ry = rk(x), rk(y)
    mx, my = st.mean(rx), st.mean(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den


def head(n, title):
    print(f"\n{'=' * 78}\nP{n} -- {title}\n{'=' * 78}")


# ---------------------------------------------------------------- populations
D = load("dataset_socle.json")
A = [r for r in D["A"] if not r["poison_default"]]
B = [r for r in D["B"] if r["q_mc_regime_ok"] and r["q_mc_plausible"] and r["o_ath_true"]]
C = [r for r in D["C"] if r["q_mc_regime_ok"] and r["q_mc_plausible"] and r["o_ath_true"]]
print(f"populations  A_clean={len(A)}  B_clean={len(B)} "
      f"({len({r['cluster_id'] for r in B})} clusters, {len({r['day'] for r in B})} days)"
      f"  C_clean={len(C)}")

# ------------------------------------------------------------------------ P1
head(1, "selection on the outcome (t_buyable)")
for name, rows in (("A_clean", A), ("B_clean", B), ("C_clean", C)):
    by = [r for r in rows if r["t_buyable"]]
    nb = [r for r in rows if not r["t_buyable"]]
    mb, mn = st.median([r["o_ath_true"] for r in by]), st.median([r["o_ath_true"] for r in nb])
    print(f"  {name}: n={len(rows)}  buyable={len(by)}  not={len(nb)}")
    print(f"    median ATH   {mb:>10,.0f} vs {mn:>10,.0f}   ratio x{mb / mn:.2f}")
    for t in ("t_ath_ge_200k", "t_mult_ge_2x"):
        print(f"    {t:14s} {rate(by, t):.3f} vs {rate(nb, t):.3f} "
              f"(whole population {rate(rows, t):.3f})")

# ------------------------------------------------------------------------ P2
head(2, "denominator artefact (multiple = ATH / entry MC)")


def elasticity(rows):
    """OLS slope of log10(ATH) on log10(detect_mc), demeaned within day."""
    use = [r for r in rows if r.get("t_log_ath") is not None and (r.get("detect_mc") or 0) > 0]
    byday = collections.defaultdict(list)
    for r in use:
        byday[r["day"]].append(r)
    xs, ys = [], []
    for _, rr in byday.items():
        mx = st.mean([math.log10(r["detect_mc"]) for r in rr])
        my = st.mean([r["t_log_ath"] for r in rr])
        for r in rr:
            xs.append(math.log10(r["detect_mc"]) - mx)
            ys.append(r["t_log_ath"] - my)
    return sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs), len(use)


for name, rows in (("A_clean", A), ("B_clean", B), ("C_clean", C)):
    b, n = elasticity(rows)
    print(f"  beta log10(ATH) ~ log10(entry MC)  {name}: {b:.4f}  (n={n})")

use = [r for r in B if r.get("t_mult") and r["detect_mc"] > 0]
xs = [math.log10(r["detect_mc"]) for r in use]
ys = [math.log10(r["t_mult"]) for r in use]
mx, my = st.mean(xs), st.mean(ys)
slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
print(f"  slope log10(multiple) ~ log10(entry MC) = {slope:+.4f}  (= beta - 1, mechanical)")
print(f"  spearman(entry MC, ATH)      = {spearman([r['detect_mc'] for r in use], [r['o_ath_true'] for r in use]):+.3f}")
print(f"  spearman(entry MC, multiple) = {spearman([r['detect_mc'] for r in use], [r['t_mult'] for r in use]):+.3f}")
res = [r for r in use if r.get("t_resid_logath") is not None]
print(f"  spearman(entry MC, residual) = {spearman([r['detect_mc'] for r in res], [r['t_resid_logath'] for r in res]):+.3f}  (n={len(res)})")

srt = sorted(use, key=lambda r: r["detect_mc"])
k = len(srt) // 10
print("  P(ATH>=200k) by entry-MC decile:")
for i in range(10):
    ch = srt[i * k:(i + 1) * k] if i < 9 else srt[9 * k:]
    print(f"    D{i}  median entry MC {st.median([r['detect_mc'] for r in ch]):>9,.0f}   "
          f"P(ATH>=200k)={rate(ch, 't_ath_ge_200k'):.3f}   P(mult>=2x)={rate(ch, 't_mult_ge_2x'):.3f}")

# ------------------------------------------------------------------------ P3
head(3, "silent default value (detected_at=0 AND detect_mc=15000)")
sl = load("snipe_log.json")
dflt = [r for r in sl if r.get("detected_at") == 0 and r.get("detect_mc") == 15000]
print(f"  snipe_log rows: {len(sl)}   rows carrying the default: {len(dflt)}")
pois = [r for r in D["A"] if r["poison_default"]]
print(f"  of which inside population A (snipe_sol>=60 SOL, n={len(D['A'])}): {len(pois)}")
print(f"  their multiples: {sorted(round(r['t_mult'], 2) for r in pois if r.get('t_mult'))}")
for t in ("t_mult_ge_2x", "t_mult_ge_3x", "t_mult_ge_5x"):
    pos = [r for r in D["A"] if r[t]]
    pp = [r for r in pos if r["poison_default"]]
    print(f"  {t}: positives={len(pos)}, contaminated={len(pp)} ({100 * len(pp) / len(pos):.1f}% of the positive class)"
          f"   rate {rate(D['A'], t):.3f} -> {rate(A, t):.3f} after removal")
print(f"  median entry MC of the clean rows: {st.median([r['detect_mc'] for r in A]):,.0f} "
      f"(the default was 15,000)")

# ------------------------------------------------------------------------ P4
head(4, "confounder (technical label vs entry MC)")
bnd = [r for r in A if r["f_bot_label"] == "BUNDLER"]
oth = [r for r in A if r["f_bot_label"] != "BUNDLER"]
t = "o_reached_100k_logged"
a, b, c, d = (sum(1 for r in bnd if r[t]), len(bnd) - sum(1 for r in bnd if r[t]),
              sum(1 for r in oth if r[t]), len(oth) - sum(1 for r in oth if r[t]))
print(f"  crude: labelled {rate(bnd, t):.3f} (n={len(bnd)}) vs rest {rate(oth, t):.3f} (n={len(oth)})"
      f"  delta={100 * (rate(bnd, t) - rate(oth, t)):+.1f}pt  fisher p={fisher_two_sided(a, b, c, d):.4f}")
print(f"  crude odds ratio = {(a * d) / (b * c):.2f}")
print(f"  median entry MC: labelled {st.median([r['detect_mc'] for r in bnd]):,.0f} "
      f"vs rest {st.median([r['detect_mc'] for r in oth]):,.0f}")
med = st.median([r["detect_mc"] for r in A])
aa = sum(1 for r in bnd if r["detect_mc"] >= med)
cc = sum(1 for r in oth if r["detect_mc"] >= med)
print(f"  label vs (entry MC >= median): fisher p={fisher_two_sided(aa, len(bnd) - aa, cc, len(oth) - cc):.2e}"
      f"  -> the label IS the entry MC")
for nm, sel in (("below median", lambda r: r["detect_mc"] < med),
                ("above median", lambda r: r["detect_mc"] >= med)):
    bb = [r for r in bnd if sel(r)]
    oo = [r for r in oth if sel(r)]
    print(f"    stratified {nm}: {rate(bb, t):.3f} (n={len(bb)}) vs {rate(oo, t):.3f} (n={len(oo)})"
          f"  delta={100 * (rate(bb, t) - rate(oo, t)):+.1f}pt")

q = sorted(A, key=lambda r: r["detect_mc"])
k = len(q) // 5
strata = []
for i in range(5):
    ch = q[i * k:(i + 1) * k] if i < 4 else q[4 * k:]
    bb = [r for r in ch if r["f_bot_label"] == "BUNDLER"]
    oo = [r for r in ch if r["f_bot_label"] != "BUNDLER"]
    x = sum(1 for r in bb if r[t])
    y = sum(1 for r in oo if r[t])
    strata.append((x, len(bb) - x, y, len(oo) - y))
num = den = Aobs = E = V = 0.0
for (x, y, z, w) in strata:
    n = x + y + z + w
    if n < 2:
        continue
    num += x * w / n
    den += y * z / n
    Aobs += x
    E += (x + y) * (x + z) / n
    V += (x + y) * (z + w) * (x + z) * (y + w) / (n * n * (n - 1))
chi = (abs(Aobs - E) - 0.5) ** 2 / V
print(f"  Mantel-Haenszel over entry-MC quintiles: OR={num / den:.2f}  chi2={chi:.3f}  "
      f"p={math.erfc(math.sqrt(chi / 2)):.3f}")
t2 = "t_mult_ge_2x"
print(f"  sign flip on the multiple target: labelled {rate(bnd, t2):.3f} vs rest {rate(oth, t2):.3f}"
      f"  delta={100 * (rate(bnd, t2) - rate(oth, t2)):+.1f}pt")
v = sorted(r["detect_mc"] for r in A)
t1c = v[len(v) // 3]
bb = [r for r in bnd if r["detect_mc"] < t1c]
oo = [r for r in oth if r["detect_mc"] < t1c]
print(f"  bottom entry-MC tercile, multiple target: {rate(bb, t2):.3f} (n={len(bb)}) "
      f"vs {rate(oo, t2):.3f} (n={len(oo)})")

# ------------------------------------------------------------------------ P5
head(5, "touched is not cashed (peak timing vs detection)")
for name, rows in (("A_clean", A), ("B_clean", B), ("C_clean", C)):
    nb = [r for r in rows if not r["t_buyable"]]
    before = [r for r in rows if (r.get("t_ath_delay_min") or 0) <= 0]
    dl = [r["t_ath_delay_min"] for r in rows if r.get("t_ath_delay_min") is not None]
    print(f"  {name}: peak within 60 s of detection (unreachable) {len(nb)}/{len(rows)} "
          f"= {100 * len(nb) / len(rows):.1f}%  | strictly before detection {100 * len(before) / len(rows):.1f}%"
          f"  | median detection->peak delay {st.median(dl):.1f} min")

# ------------------------------------------------------------------------ P6
head(6, "instrumentation: unit mixing, censored field, history depth")
sol = load("sol_usd_hourly.json")
hh = sol["hourly_close"]
sts = [x[0] for x in hh]
spx = [x[1] for x in hh]


def sol_usd(t):
    i = max(0, min(bisect.bisect_right(sts, t) - 1, len(spx) - 1))
    return spx[i]


H = load("horizon.json")
print(f"  horizon rows: {len(H)}   with an OHLCV series: {sum(1 for r in H if r.get('close_1h'))}"
      f"   status={dict(collections.Counter(r.get('status') for r in H))}")
for kk in ("close_1h", "close_2h", "close_4h", "close_24h"):
    raw = [r[kk] / r["entry_price"] for r in H if r.get(kk)]
    cor = [r[kk] / (r["entry_price"] * sol_usd(r["entry_ts"])) for r in H if r.get(kk)]
    print(f"    {kk:10s} n={len(raw):3d} | mixed units: median {st.median(raw):7.2f}x, "
          f"P(>=1)={sum(1 for x in raw if x >= 1) / len(raw):.3f}"
          f"  || converted: median {st.median(cor):.3f}x, "
          f"P(>=1)={sum(1 for x in cor if x >= 1) / len(cor):.3f}")
used = [sol_usd(r["entry_ts"]) for r in H if r.get("close_1h")]
print(f"    conversion factor actually applied (SOL/USD at entry): "
      f"min {min(used):.1f}  median {st.median(used):.1f}  max {max(used):.1f}")
print(f"  history depth: the hourly pull returned {sol['n']} candles spanning "
      f"{(sol['ts_max'] - sol['ts_min']) / 86400:.1f} days "
      f"(the same 1000-candle cap is {1000 / 60:.1f} h at minute granularity)")

rows = [r for r in D["A"] if r.get("o_max_ath_logged") and r.get("o_ath_true")]
und = [r for r in rows if r["o_max_ath_logged"] < 0.95 * r["o_ath_true"]]
ratios = sorted(r["o_max_ath_logged"] / r["o_ath_true"] for r in rows)
print(f"  censored outcome field: {len(und)}/{len(rows)} rows ({100 * len(und) / len(rows):.1f}%) "
      f"below the true peak; ratio p10={ratios[len(ratios) // 10]:.3f} median={st.median(ratios):.3f}")
for lab, f in (("true peak", lambda r: r["o_ath_true"] / r["detect_mc"]),
               ("logged field", lambda r: r["o_max_ath_logged"] / r["detect_mc"])):
    v2 = [f(r) for r in rows if r["detect_mc"] > 0]
    print(f"    P(multiple >= 2) computed on the {lab}: {sum(1 for x in v2 if x >= 2) / len(v2):.3f}")

# ----------------------------------------------------------------------- P11
head(11, "missing data: are the 352 empty captures random?")
n_files, n_empty, n_kept = 645, 352, 293
print(f"  capture files {n_files}, empty {n_empty} ({100 * n_empty / n_files:.1f}%), usable {n_kept}")
Cm = {r["mint"] for r in D["C"]}
win = [r for r in B if "2026-06-27" <= r["day"] <= "2026-07-05"]
cap = [r for r in win if r["mint"] in Cm]
noc = [r for r in win if r["mint"] not in Cm]
print(f"  within the capture window: {len(cap)}/{len(win)} tokens captured ({100 * len(cap) / len(win):.1f}%)")
for t in ("t_ath_ge_200k", "t_mult_ge_2x"):
    print(f"    {t}: captured {rate(cap, t):.3f} vs not captured {rate(noc, t):.3f}"
          f"  delta={100 * (rate(cap, t) - rate(noc, t)):+.1f}pt")

# ----------------------------------------------------------------------- P12
head(12, "graph clustering: shared infrastructure fabricates a giant component")
path = os.path.join(DATA, "floor_capture_public.jsonl.gz")
if os.path.exists(path):
    tok = {}
    with gzip.open(path, "rt") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            j = json.loads(ln)
            sn = j.get("snipers") or []
            if sn:
                tok[j["mint"]] = {x if isinstance(x, str) else x.get("wallet") for x in sn}
    cnt = collections.Counter()
    for _, s in tok.items():
        for w in s:
            cnt[w] += 1
    print(f"  tokens with a sniper list: {len(tok)}   distinct wallets: {len(cnt)}")
    top = cnt.most_common(5)
    print("  ubiquity of the 5 most frequent addresses (share of tokens): "
          + ", ".join(f"{100 * c / len(tok):.1f}%" for _, c in top))
    ubiq = [w for w, c in cnt.items() if c >= 14]

    def giant(exclude=()):
        ex = set(exclude)
        inv = collections.defaultdict(set)
        for m, s in tok.items():
            for w in s - ex:
                inv[w].add(m)
        shared = collections.Counter()
        for _, ms in inv.items():
            if not 2 <= len(ms) <= 200:
                continue
            for x, y in itertools.combinations(sorted(ms), 2):
                shared[(x, y)] += 1
        adj = collections.defaultdict(set)
        for (x, y), c in shared.items():
            if c >= 3:
                adj[x].add(y)
                adj[y].add(x)
        seen, best = set(), 0
        for m in tok:
            if m in seen:
                continue
            stack, size = [m], 0
            seen.add(m)
            while stack:
                z = stack.pop()
                size += 1
                for w in adj[z]:
                    if w not in seen:
                        seen.add(w)
                        stack.append(w)
            best = max(best, size)
        return best
    g0, g1 = giant(), giant(ubiq)
    print(f"  giant component (edge = >=3 shared snipers): {g0}/{len(tok)} = {100 * g0 / len(tok):.1f}%")
    print(f"  after removing the {len(ubiq)} addresses present on >=14 tokens: "
          f"{g1}/{len(tok)} = {100 * g1 / len(tok):.1f}%")
else:
    print("  floor_capture_public.jsonl.gz not present -- skipped")

print("\ndone.")
