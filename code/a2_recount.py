#!/usr/bin/env python3
"""Re-count every measured token under the criteria that survive the null model.

a1_null_model.py showed that criterion C (a shared private funder) fires on 89 % of randomly
drawn 40-wallet groups, and on 99.5 % of groups restricted to wallets whose genesis was reached.
A criterion that fires almost always on unrelated wallets carries no information, and any verdict
resting on it alone is a false positive. Criteria A (same funding transaction) and B (same amount
inside one hour, >= 3 distinct wallets) fired 0 times in 5 000 draws.

This script therefore recomputes every verdict using A and B only, side by side with the original
A-or-B-or-C verdict, and runs Fisher's exact test on the corrected counts.

Usage:
    python3 code/a2_recount.py
Reads only files already published under ./data/. No network access, no key.
"""
from __future__ import annotations
import glob, json, math, os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

GROUPS = OrderedDict([
    ("temoin_mort", [os.path.join(DATA, "trace_temoins", "e3_splits_*.json")]),
    ("temoin_gradue", [os.path.join(DATA, "trace_gradues", "e3_splits_*.json")]),
    ("cible", [os.path.join(DATA, "trace_optimus", "e3_splits_*.json"),
               os.path.join(DATA, "trace_h2w6", "e3_splits_*.json"),
               os.path.join(DATA, "trace_polmrkt", "e3_splits_*.json"),
               os.path.join(DATA, "trace_cohorte", "e3_splits_*.json")]),
])
# Files that live in a target directory but are in fact controls already counted once.
TEMOINS_DANS_CIBLES = {"Calm", "faith", "DOGEFORMULA"}


def fisher_exact_greater(a, b, c, d):
    """One-sided p for the 2x2 table [[a,b],[c,d]]: P(X >= a) under the hypergeometric null."""
    n = a + b + c + d
    r1, c1 = a + b, a + c

    def logC(n, k):
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)

    p = 0.0
    for x in range(max(0, r1 + c1 - n), min(r1, c1) + 1):
        if x < a:
            continue
        p += math.exp(logC(c1, x) + logC(n - c1, r1 - x) - logC(n, r1))
    return min(1.0, p)


rows = []
seen = set()
for role, patterns in GROUPS.items():
    for pat in patterns:
        for path in sorted(glob.glob(pat)):
            d = json.load(open(path))
            lab = d.get("label") or os.path.basename(path)[10:-5]
            key = (role, lab)
            if lab in seen:
                continue
            if role == "cible" and lab in TEMOINS_DANS_CIBLES:
                continue
            seen.add(lab)
            A = d.get("A_meme_transaction") or []
            B = d.get("B_meme_montant_meme_moment") or []
            C = d.get("C_bailleurs_communs_PRIVES") or []
            rows.append({
                "role": role, "label": lab, "mint": d.get("mint"),
                "n_wallets": len(d.get("wallets") or d.get("portefeuilles") or []) or None,
                "n_A": len(A), "n_B": len(B), "n_C": len(C),
                "max_wallets_A": max([x.get("n_wallets", 0) for x in A], default=0),
                "max_wallets_B": max([x.get("n_wallets", 0) for x in B], default=0),
                "verdict_origine": d.get("verdict", ""),
                "positif_ABC": bool(A or B or C),
                "positif_AB": bool(A or B),
                "positif_A": bool(A),
                "fichier": os.path.relpath(path, ROOT),
            })

rows.sort(key=lambda r: (r["role"], r["label"]))

# The reference case is the observation the hypothesis was built from. Leaving it in the test set
# would score the hypothesis on the sample that suggested it. It is reported on its own, and
# excluded from every p-value below.
DECOUVERTE = {"ODIN_POSITIF"}
for r in rows:
    r["role_test"] = "cas_de_decouverte" if r["label"] in DECOUVERTE else r["role"]

cib = [r for r in rows if r["role_test"] == "cible"]
mort = [r for r in rows if r["role_test"] == "temoin_mort"]
grad = [r for r in rows if r["role_test"] == "temoin_gradue"]
dec = [r for r in rows if r["role_test"] == "cas_de_decouverte"]

print(f"{'groupe':<18} {'token':<14} {'A':>3} {'B':>3} {'C':>3}  ABC  AB")
for r in rows:
    print(f"{r['role_test']:<18} {r['label']:<14} {r['n_A']:>3} {r['n_B']:>3} {r['n_C']:>3}   "
          f"{'+' if r['positif_ABC'] else '-'}    {'+' if r['positif_AB'] else '-'}")

# Two comparisons. Against dead tokens, targets differ by outcome as much as by the exposure
# under test; against graduated tokens of the same window the outcome is held fixed and only the
# exposure varies, so that second comparison carries the information.
tests = {}
for tem, tem_name in ((mort, "temoins_morts"), (grad, "temoins_gradues")):
    if not tem:
        continue
    for crit, crit_name in (("positif_ABC", "A_ou_B_ou_C_verdict_dorigine"),
                            ("positif_AB", "A_ou_B_apres_retrait_de_C"),
                            ("positif_A", "A_seul_le_critere_le_plus_specifique")):
        a = sum(1 for r in cib if r[crit])
        b = len(cib) - a
        c = sum(1 for r in tem if r[crit])
        d = len(tem) - c
        p = fisher_exact_greater(a, b, c, d)
        tests[f"{crit_name}__contre_{tem_name}"] = {
            "cibles_positives": a, "cibles_total": len(cib),
            "temoins_positifs": c, "temoins_total": len(tem),
            "p_unilateral_fisher": round(p, 6)}
        print(f"\n{crit_name} vs {tem_name}: cibles {a}/{len(cib)}  vs  temoins {c}/{len(tem)}"
              f"   Fisher unilateral p = {p:.4f}")

# --- markdown table, injected into docs/SPLIT_PHASE1.md at the RESULTS-TABLE marker -------------
LIB = {"cible": "target", "temoin_mort": "control, dead", "temoin_gradue": "control, graduated",
       "cas_de_decouverte": "**discovery case** (excluded from every p below)"}
TEST_LIB = {
    "A_ou_B_ou_C_verdict_dorigine__contre_temoins_morts":
        "original verdict (A or B or **C**) vs dead controls",
    "A_ou_B_apres_retrait_de_C__contre_temoins_morts":
        "**A or B only** vs dead controls",
    "A_ou_B_ou_C_verdict_dorigine__contre_temoins_gradues":
        "original verdict (A or B or **C**) vs graduated controls",
    "A_ou_B_apres_retrait_de_C__contre_temoins_gradues":
        "**A or B only** vs graduated controls",
    "A_seul_le_critere_le_plus_specifique__contre_temoins_morts":
        "A alone (zero false positives in the null) vs dead controls",
    "A_seul_le_critere_le_plus_specifique__contre_temoins_gradues":
        "A alone (zero false positives in the null) vs graduated controls",
}
md = ["| group | token | A | B | C | verdict A-or-B-or-C | verdict A-or-B |",
      "|---|---|---:|---:|---:|:-:|:-:|"]
for r in rows:
    md.append(f"| {LIB[r['role_test']]} | `{r['label']}` | {r['n_A']} | {r['n_B']} | {r['n_C']} | "
              f"{'+' if r['positif_ABC'] else '–'} | {'**+**' if r['positif_AB'] else '–'} |")
md.append("")
md.append("| comparison | targets | controls | Fisher one-sided *p* |")
md.append("|---|---|---|---|")
for k, v in tests.items():
    md.append(f"| {TEST_LIB.get(k, k.replace('_', ' '))} | "
              f"{v['cibles_positives']}/{v['cibles_total']} | "
              f"{v['temoins_positifs']}/{v['temoins_total']} | {v['p_unilateral_fisher']:.4f} |")
table_md = "\n".join(md)

doc = os.path.join(ROOT, "docs", "SPLIT_PHASE1.md")
if os.path.exists(doc):
    txt = open(doc).read()
    start = "<!-- RESULTS-TABLE -->"
    end = "<!-- /RESULTS-TABLE -->"
    block = f"{start}\n\n{table_md}\n\n{end}"
    if start in txt:
        head = txt.split(start)[0]
        tail = txt.split(end)[1] if end in txt else txt.split(start)[1].split("\n", 1)[1]
        open(doc, "w").write(head + block + tail)
        print(f"\ntable injectee dans docs/SPLIT_PHASE1.md")

out = os.path.join(DATA, "adverse", "a2_recount.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump({
    "objet": "Recomptage de tous les tokens mesures sous les seuls criteres qui survivent au "
             "modele nul (A et B), a cote du verdict d'origine (A ou B ou C).",
    "motif": "a1_null_model.py : le critere C se declenche sur 89 % des groupes de 40 "
             "portefeuilles tires au hasard (99,5 % a genese atteinte). Il ne distingue rien. "
             "A et B se declenchent 0 fois sur 5 000 tirages.",
    "cas_de_decouverte_exclu_des_tests": sorted(DECOUVERTE),
    "motif_exclusion": "Le cas de reference est l'observation qui a fait naitre l'hypothese. "
                       "Le garder dans l'echantillon de test reviendrait a noter l'hypothese sur "
                       "les donnees qui l'ont suggeree. Il est rapporte a part.",
    "tokens": rows, "tests": tests,
    "limite": "Le test de Fisher suppose que cibles et temoins ne different que par l'exposition "
              "testee. Ce n'est pas le cas ici : les cibles sont toutes graduees et choisies par "
              "l'auteur parmi ses trades gagnants, les temoins sont des tokens morts apparies sur "
              "le seul slot de creation. Le p rapporte est donc un majorant optimiste ; voir "
              "docs/PITFALLS.md.",
}, open(out, "w"), indent=1, ensure_ascii=False)
print(f"\n-> {out}")
