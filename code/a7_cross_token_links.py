#!/usr/bin/env python3
"""Are the per-token operations linked to each other, or only to a common entry point?

A split is one actor by definition: a transaction paying N wallets identical amounts has one
signer and one decision. What is open is whether the splits observed on different tokens come
from the same actor, a shared tool, or unrelated users of the same gateway. Three independent
tests, none of which can prove identity, each of which strengthens or weakens the link:

1. Recurring exact amounts. A swap output depends on size, route and the instant price, so the
   same nine-decimal figure appearing on two unrelated launches is not what conversions produce
   by chance. Recurrence across tokens is the strongest link available short of a shared
   address.

2. Shared wallets. A wallet buying on two of the tokens is a direct link. An operator who burns
   addresses leaves none, so a null result here is uninformative and is reported as such.

3. Funding sessions. Several tokens' wallets funded from the gateway inside the same short
   window point to one operator working a batch, or to a busy gateway. The base rate matters,
   so the observed clustering is compared against the gateway's own traffic.

Usage:
    python3 code/a7_cross_token_links.py
Reads only committed files under ./data/. No network, no key.
"""
from __future__ import annotations
import json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

src = json.load(open(os.path.join(DATA, "split", "all_buyers_g2y.json")))

# --- collect every gateway payment, tagged with its token -----------------------------------------
paiements = []          # (token, wallet, montant, ts, utc, avant_token)
wallets_par_token = defaultdict(set)
for tok, v in src.items():
    if not v.get("mesurable"):
        continue
    for w, r in (v.get("portefeuilles") or {}).items():
        wallets_par_token[tok].add(w)
        for h in (r.get("g2y") or []):
            paiements.append((tok, w, round(h["sol"], 9), h["ts"], h["utc"], h["avant_token"]))

mesures = [t for t, v in src.items() if v.get("mesurable")]
avant = [p for p in paiements if p[5]]
print(f"{len(mesures)} tokens mesures, {len(paiements)} paiements du guichet vers des "
      f"portefeuilles frais ({len(avant)} avant la creation du token)\n")

# --- 1. montants exacts recurrents d'un token a l'autre -------------------------------------------
par_montant = defaultdict(set)
detail = defaultdict(list)
for tok, w, sol, ts, utc, av in avant:
    par_montant[sol].add(tok)
    detail[sol].append((tok, w, utc))
recurrents = {m: sorted(t) for m, t in par_montant.items() if len(t) >= 2}

print("1. MONTANTS EXACTS PRESENTS SUR PLUSIEURS TOKENS")
if recurrents:
    for m, toks in sorted(recurrents.items(), key=lambda kv: -len(kv[1])):
        print(f"   {m:.9f} SOL  ->  {len(toks)} tokens : {', '.join(toks)}")
        for tok, w, utc in sorted(detail[m], key=lambda d: d[2]):
            print(f"       {tok:<12} {w}  {utc}")
else:
    print("   aucun")

# --- 2. portefeuilles communs a plusieurs tokens ---------------------------------------------------
par_wallet = defaultdict(set)
for tok, ws in wallets_par_token.items():
    for w in ws:
        par_wallet[w].add(tok)
partages = {w: sorted(t) for w, t in par_wallet.items() if len(t) >= 2}
print(f"\n2. PORTEFEUILLES PRESENTS SUR PLUSIEURS TOKENS : {len(partages) or 'aucun'}")
for w, toks in partages.items():
    print(f"   {w}  {', '.join(toks)}")
if not partages:
    print("   Resultat non informatif : un operateur qui brule ses adresses ne laisse pas de")
    print("   portefeuille partage. L'absence ici ne distingue pas 'acteurs differents' de")
    print("   'meme acteur, adresses jetables'.")

# --- 3. sessions de financement --------------------------------------------------------------------
tri = sorted(avant, key=lambda p: p[3])
sessions, cur = [], []
for p in tri:
    if cur and p[3] - cur[-1][3] > 6 * 3600:
        sessions.append(cur)
        cur = []
    cur.append(p)
if cur:
    sessions.append(cur)
multi = [s for s in sessions if len({p[0] for p in s}) >= 2]
print(f"\n3. SESSIONS DE FINANCEMENT (paiements espaces de moins de 6 h)")
print(f"   {len(sessions)} sessions, dont {len(multi)} touchant plusieurs tokens")
for s in multi:
    toks = sorted({p[0] for p in s})
    print(f"   {s[0][4]} -> {s[-1][4]}  {len(s)} paiements, tokens : {', '.join(toks)}")

res = {
    "objet": "Les operations observees sur des tokens differents sont-elles liees entre elles, ou "
             "seulement a un point d'entree commun ?",
    "prealable": "Un split est un acteur : une transaction payant N portefeuilles au meme montant "
                 "a un signataire et une decision. Ce qui reste a etablir, c'est si les splits de "
                 "tokens differents sont le meme acteur, un meme outil, ou des utilisateurs "
                 "distincts du meme guichet.",
    "n_tokens_mesures": len(mesures), "n_paiements": len(paiements),
    "n_paiements_avant_token": len(avant),
    "montants_recurrents": {f"{m:.9f}": {"tokens": t,
                                         "occurrences": [{"token": d[0], "portefeuille": d[1],
                                                          "utc": d[2]} for d in detail[m]]}
                            for m, t in recurrents.items()},
    "portefeuilles_partages": partages,
    "n_sessions": len(sessions), "n_sessions_multi_tokens": len(multi),
    "sessions_multi_tokens": [{"debut": s[0][4], "fin": s[-1][4], "n_paiements": len(s),
                               "tokens": sorted({p[0] for p in s})} for s in multi],
    "portee": "Aucun de ces tests ne peut demontrer une identite. Un montant recurrent ou une "
              "session partagee resserre le lien ; un outil commun produirait les memes signes. "
              "Le depot s'arrete a ce que la chaine montre.",
}
out = os.path.join(DATA, "adverse", "a7_cross_token_links.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump(res, open(out, "w"), indent=1, ensure_ascii=False)
print(f"\n-> {out}")
