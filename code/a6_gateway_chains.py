#!/usr/bin/env python3
"""Dated funding chains: swap gateway -> distributor -> fresh wallets -> first buys.

The entry rule for this cohort was a narrow one: at least one early buyer of the token traces
back to one specific swap gateway, the address called G2Y throughout this repository. This
script tests that rule token by token and, where it holds, rebuilds the chain with a timestamp
on every link.

Two levels are tested. At hop 0 the gateway paid an early buyer directly. At hop 1 it paid an
address that then funded an early buyer, which is how the reference case works: the gateway
never touches the buying wallets, it pays a distributor that fans the money out. Testing hop 0
alone found 4 tokens, far fewer than the two levels together.

Every link is checked against the token's creation time. A gateway payment dated after the
token was created cannot have funded a launch that already happened, so those links are dropped
and counted separately. Two tokens that "have G2Y" fail that check and are not counted as
confirmations.

Coverage is partial and is printed per token. A wallet whose history could not be paged back to
genesis has an unknown funding origin, so a negative on it is a measurement failure rather than
an observation: a token reported without a chain may simply be one whose buyers were out of
reach. Absence here is not evidence of absence.

Usage:
    python3 code/a6_gateway_chains.py
Reads only committed files under ./data/. No network, no key.
"""
from __future__ import annotations
import glob, json, os, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

GATEWAY = "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t"

FUNDING = [os.path.join(DATA, "trace_cohorte", "e2_funding_*.json"),
           os.path.join(DATA, "trace_optimus", "e2_funding_OPTIMUS.json"),
           os.path.join(DATA, "trace_optimus", "e2_funding_ODIN_POSITIF.json"),
           os.path.join(DATA, "trace_h2w6", "e2_funding_h2w6gm6jz.json"),
           os.path.join(DATA, "trace_polmrkt", "e2_funding_POLMRKTBOT.json")]


def utc(ts):
    return dt.datetime.fromtimestamp(ts, dt.UTC).strftime("%Y-%m-%d %H:%M") if ts else None


def creation_dates():
    """Token creation time, the cut-off every link is checked against."""
    out = {}
    for path, key in ((os.path.join(DATA, "trace_cohorte", "t0_cohorte.json"), "temoins"),
                      (os.path.join(DATA, "cibles", "cibles.json"), "cibles")):
        if not os.path.exists(path):
            continue
        for t in json.load(open(path)).get(key, []):
            d = t.get("date_creation_utc")
            if d:
                out[t["label"] if "label" in t else t.get("symbole")] = d
    return out


hop1_path = os.path.join(DATA, "split", "g2y_hop1.json")
hop1 = json.load(open(hop1_path)) if os.path.exists(hop1_path) else {"resultats": {}}
gw_paid = {a: r["g2y_hits"] for a, r in hop1.get("resultats", {}).items() if r.get("g2y_hits")}
incomplete = {a for a, r in hop1.get("resultats", {}).items() if not r.get("histoire_complete")}

created = creation_dates()
rows = []
for pat in FUNDING:
    for path in sorted(glob.glob(pat)):
        d = json.load(open(path))
        lab = d["label"]
        t_creation = created.get(lab)
        cut = (dt.datetime.strptime(t_creation[:19], "%Y-%m-%dT%H:%M:%S")
               .replace(tzinfo=dt.UTC).timestamp()) if t_creation else None

        chains, tardifs = [], []
        for w in d["wallets"]:
            for inf in w.get("inflows", []):
                if inf.get("nature") != "financement":
                    continue
                src = inf.get("source")
                if not src:
                    continue

                # hop 0: the gateway itself paid this buyer.
                if src == GATEWAY:
                    lien = {"niveau": 0, "portefeuille": w["wallet"],
                            "recu_sol": inf["amount_sol"], "quand": inf.get("utc"),
                            "ts": inf["ts"], "via": None, "via_recu": None}
                # hop 1: the gateway paid whoever paid this buyer.
                elif src in gw_paid:
                    g = min(gw_paid[src], key=lambda h: h["ts"])
                    lien = {"niveau": 1, "portefeuille": w["wallet"],
                            "recu_sol": inf["amount_sol"], "quand": inf.get("utc"),
                            "ts": inf["ts"], "via": src,
                            "via_recu": {"sol": round(g["sol"], 6), "quand": g["utc"],
                                         "ts": g["ts"],
                                         "n_versements": len(gw_paid[src])}}
                else:
                    continue

                # Two temporal rules. Both remove cases, neither adds any.
                #
                # 1. Inside the chain: the gateway must pay the distributor before the distributor
                #    pays the buyer. A funder that paid a wallet in 2022 and only received from the
                #    gateway in 2024 is no link, the money cannot have flowed that way. The script
                #    reported such a chain before this check existed.
                if lien["via_recu"] and lien["via_recu"]["ts"] > lien["ts"]:
                    lien["motif_rejet"] = "guichet paie le distributeur apres que celui-ci ait " \
                                          "paye le portefeuille : ordre impossible"
                    tardifs.append(lien)
                    continue
                # 2. Against the token: a payment landing after the launch cannot have funded it.
                ref = lien["via_recu"]["ts"] if lien["via_recu"] else lien["ts"]
                if cut and ref > cut:
                    lien["motif_rejet"] = "versement posterieur a la creation du token"
                    tardifs.append(lien)
                else:
                    chains.append(lien)

        chains.sort(key=lambda c: (c["niveau"], c["ts"]))
        n_gen = d.get("n_genesis_reached") or 0
        rows.append({
            "token": lab, "mint": d.get("mint"), "creation": t_creation,
            "n_premiers_acheteurs": d["n_wallets"], "n_genese_atteinte": n_gen,
            "couverture": round(n_gen / d["n_wallets"], 3) if d["n_wallets"] else None,
            "n_liens_hop0": sum(1 for c in chains if c["niveau"] == 0),
            "n_liens_hop1": sum(1 for c in chains if c["niveau"] == 1),
            "n_liens_ecartes": len(tardifs),
            "n_hop0_valides": sum(1 for c in chains if c["niveau"] == 0),
            "guichet_en_amont": bool(chains),
            "chaines": chains[:12],
            "ecartes": tardifs[:4],
        })

rows.sort(key=lambda r: (not r["guichet_en_amont"], r["token"]))
conf = [r for r in rows if r["guichet_en_amont"]]

print(f"GUICHET EN AMONT : {len(conf)}/{len(rows)} tokens tradés\n")
print(f"{'token':<13} {'couv.':>6} {'hop0':>5} {'hop1':>5} {'écartés':>8}  premier lien daté")
for r in rows:
    prem = r["chaines"][0]["quand"] if r["chaines"] else ""
    print(f"{r['token']:<13} {r['couverture']:>6.0%} {r['n_liens_hop0']:>5} "
          f"{r['n_liens_hop1']:>5} {r['n_liens_ecartes']:>8}  {prem}")

print("\nCHAINES DATEES")
for r in conf:
    print(f"\n{r['token']}  (token créé {r['creation'][:16] if r['creation'] else '?'})")
    for c in r["chaines"][:4]:
        if c["niveau"] == 0:
            print(f"   guichet ──({c['quand']})──► {c['portefeuille'][:14]}…  "
                  f"{c['recu_sol']:.6f} SOL")
        else:
            v = c["via_recu"]
            print(f"   guichet ──({v['quand']})──► {c['via'][:14]}… ──({c['quand']})──► "
                  f"{c['portefeuille'][:14]}…  {c['recu_sol']:.6f} SOL")

out = os.path.join(DATA, "adverse", "a6_gateway_chains.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
json.dump({
    "objet": "Chaines datees guichet de swap -> distributeur -> portefeuilles frais -> premiers "
             "achats, sur les tokens tradés.",
    "guichet": GATEWAY,
    "regle_temporelle": "Tout lien posterieur a la creation du token est ecarte et compte a part : "
                        "un versement qui arrive apres le lancement ne peut pas l'avoir finance.",
    "portee": "Presence, pas prevalence. La couverture est partielle et rapportee par token : "
              "un portefeuille dont l'historique n'a pas ete remonte jusqu'a la genese a une "
              "origine inconnue, et un negatif ne vaut rien pour lui.",
    "n_tokens": len(rows), "n_guichet_en_amont": len(conf),
    "n_adresses_amont_a_historique_incomplet": len(incomplete),
    "tokens": rows,
}, open(out, "w"), indent=1, ensure_ascii=False)
print(f"\n-> {out}")
