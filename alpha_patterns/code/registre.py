#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Registre des tests d'une étude : une ligne par test (ou par balayage) calculé, quel que soit l'agent.

Pourquoi : chaque agent sous-compte ses balayages de bonne foi (113 réels contre ~40 déclarés le
24/08). La correction pour tests multiples se fait sur ce registre, jamais sur les déclarations.

Dans le code de l'étude (copier ce fichier dans code/ avant le gel, il est gelé avec) :

    import os
    from registre import enregistrer
    ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # jamais un chemin en dur
    enregistrer(ETUDE, test="T3_funding_vs_x2", declare=True, n=1015, n_effectif=24,
                agent="analyse-principale", params={"fenetre_min": 15},
                stat=2.31, p=0.0004, n_tirages=500_000, n_hits=199, sortie="tables/T3.json")
    # un balayage de 1 582 590 règles : UNE ligne avec n_comparaisons=1_582_590
    # contrôles positifs sur tables synthétiques : donnees="synthetiques"

Appeler APRÈS avoir écrit la sortie (son empreinte est notée).

En ligne de commande :
    registre.py ajouter  <etude> --test T --declare oui|non --n N --agent A [--n-comparaisons K]
                         [--n-effectif M] [--params JSON] [--stat S] [--p P] [--n-tirages K] [--n-hits H]
                         [--donnees reelles|synthetiques] [--sortie F]
    registre.py compter  <etude> [--alpha 0.05]
    registre.py verifier <etude>
    registre.py exporter-aveugle <etude> <fichier_sortie>   # sans stat, p, hits ni intervalles

Garanties :
- chaque ligne porte l'empreinte de la précédente ; la tête (nombre de lignes, dernière empreinte)
  est aussi recopiée hors du dossier (~/.claude/etudes-gelees/temoins/) : effacer la dernière ligne
  se voit ;
- après le gel, une ligne n'est écrite que si toutes les empreintes de PROTOCOL.lock correspondent ;
- chaque ligne note le script qui l'a produite et s'il fait partie du gel ; un test venu de code
  non gelé est forcé "non déclaré" (exploratoire) ;
- pendant une reproduction (variable ETUDE_REPRO=1, posée par repro.py), rien n'est écrit.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import pwd
import sys
import time
import unicodedata
from collections import Counter

LOCK = "PROTOCOL.lock"
FICHIER = os.path.join("registre", "tests.jsonl")
GENESE = "0" * 64
HOME = os.path.realpath(pwd.getpwuid(os.getuid()).pw_dir)
TEMOINS = os.path.join(os.environ.get("ETUDES_GELEES_DIR") or os.path.join(HOME, ".claude", "etudes-gelees"),
                       "temoins")
_CACHE: dict = {}


class ProtocoleRompu(RuntimeError):
    pass


def _sha_fichier(chemin: str) -> str:
    st = os.stat(chemin)
    cle = (os.path.realpath(chemin), st.st_size, st.st_mtime_ns, st.st_ino)
    if cle in _CACHE:
        return _CACHE[cle]
    h = hashlib.sha256()
    with open(chemin, "rb") as fh:
        for bloc in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloc)
    _CACHE[cle] = h.hexdigest()
    return _CACHE[cle]


def _nfc(p: str) -> str:
    return unicodedata.normalize("NFC", p)


def racine_etude(chemin: str) -> str:
    """Le dossier de l'étude : celui qui porte analysis_plan.md ou PROTOCOL.lock (ou un ancien gel),
    ou son parent quand on passe code/. Ne remonte jamais plus haut (une sous-étude garde son registre)."""
    d = _nfc(os.path.realpath(chemin))
    for cand in (d, os.path.dirname(d)):
        try:
            noms = os.listdir(cand)
        except OSError:
            continue
        if LOCK in noms or "analysis_plan.md" in noms or any(f.startswith(LOCK + ".degele-") for f in noms):
            return cand
    return d


def _etat_gel(etude: str) -> tuple[str, str | None, dict]:
    lock = os.path.join(etude, LOCK)
    if not os.path.isfile(lock):
        degel = any(f.startswith(LOCK + ".degele-") for f in os.listdir(etude))
        return ("apres_degel" if degel else "avant_gel"), None, {}
    with open(lock, encoding="utf-8") as fh:
        doc = json.load(fh)
    rompus = [rel for rel, attendu in (doc.get("fichiers") or {}).items()
              if not os.path.isfile(os.path.join(etude, rel)) or _sha_fichier(os.path.join(etude, rel)) != attendu]
    if rompus:
        raise ProtocoleRompu("calcul refusé, le protocole gelé a bougé : " + ", ".join(sorted(rompus)))
    return "apres_gel", _sha_fichier(lock), doc


def _script_appelant(etude: str, doc: dict) -> tuple[str | None, str | None, bool]:
    chemin = os.path.realpath(sys.argv[0]) if sys.argv and sys.argv[0] not in ("", "-c", "-") else None
    if not chemin or not os.path.isfile(chemin):
        return None, None, False
    rel = os.path.relpath(chemin, etude)
    h = _sha_fichier(chemin)
    # registre.py lancé seul = appel en ligne de commande : provenance du calcul inconnue
    gele = os.path.basename(chemin) != "registre.py" and (doc.get("fichiers") or {}).get(rel) == h
    if "Users/" in rel or rel.count("..") > 3:
        rel = "<hors etude>/" + os.path.basename(chemin)  # jamais de chemin local dans le registre
    return rel, h, gele


def _hits(p: float | None, n_tirages: int | None, n_hits: int | None) -> int | None:
    if n_hits is not None:
        return int(n_hits)
    if p is None or not n_tirages:
        return None
    lectures = []
    plus_un = p * (n_tirages + 1)
    if abs(plus_un - round(plus_un)) < 1e-3 and round(plus_un) >= 1:
        lectures.append(int(round(plus_un)) - 1)  # convention (ge+1)/(n+1)
    simple = p * n_tirages
    if abs(simple - round(simple)) < 1e-3:
        lectures.append(int(round(simple)))
    # ambiguïté (p arrondi) : la lecture la plus prudente, le moins de hits
    return min(lectures) if lectures else int(round(simple))


def _resolution_p(p: float | None, n_tirages: int | None, n_hits: int | None) -> dict:
    """Règle du 24/08 : 200 000 tirages au moins pour un p sous 5e-4, 500 000 sous 1e-4 ; 0 hit = borne."""
    hits = _hits(p, n_tirages, n_hits)
    if hits is None:
        return {}
    out: dict = {"hits": hits}
    if hits == 0:
        out.update(p_borne_sup_95=3.0 / n_tirages, p_ic95=[0.0, 3.0 / n_tirages], p_non_resolu=True,
                   note_p="0 hit : seulement p < 3/n, jamais une estimation")
        return out

    def q(k: float, z: float) -> float:
        return k * (1 - 1 / (9 * k) + z / (3 * math.sqrt(k))) ** 3 if k > 0 else 0.0
    out["p_ic95"] = [max(q(hits, -1.96), 0) / n_tirages, q(hits + 1, 1.96) / n_tirages]
    pv = p if p is not None else hits / n_tirages
    if (pv < 1e-4 and n_tirages < 500_000) or (pv < 5e-4 and n_tirages < 200_000):
        out["p_non_resolu"] = True
        out["note_p"] = "trop peu de tirages pour ce p (200k sous 5e-4, 500k sous 1e-4) : ne pas le citer"
    return out


def _json(o):
    if hasattr(o, "tolist"):
        return o.tolist()
    if hasattr(o, "item"):
        return o.item()
    return str(o)


def _nom_temoin(etude: str) -> str:
    return os.path.join(TEMOINS, hashlib.sha1(_nfc(etude).encode("utf-8")).hexdigest()[:16] + ".json")


def _temoin(etude: str, n: int, tete: str) -> None:
    try:
        os.makedirs(TEMOINS, exist_ok=True)
        tmp = _nom_temoin(etude) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"etude": etude, "n": n, "tete": tete,
                       "t_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())}, fh)
        os.replace(tmp, _nom_temoin(etude))
    except Exception:
        pass


def _lire_temoin(etude: str) -> dict | None:
    try:
        with open(_nom_temoin(etude), encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def enregistrer(etude: str, test: str, declare: bool, n: int, agent: str,
                n_effectif: int | None = None, params: dict | None = None,
                stat: float | None = None, p: float | None = None,
                n_tirages: int | None = None, n_hits: int | None = None,
                n_comparaisons: int = 1, donnees: str = "reelles",
                sortie: str | None = None, note: str | None = None) -> dict:
    repro_dir = os.environ.get("ETUDE_REPRO_DIR")
    if repro_dir and _nfc(os.path.realpath(etude)).startswith(_nfc(os.path.realpath(repro_dir)) + os.sep):
        return {"repro": True, "test": test}  # une reproduction ne compte pas comme un nouveau test
    if donnees not in {"reelles", "synthetiques"}:
        raise ValueError("donnees doit valoir 'reelles' ou 'synthetiques'")
    if p is not None:
        p = float(p)
        if not (math.isfinite(p) and 0.0 <= p <= 1.0):
            raise ValueError(f"p invalide : {p}")
    if n_hits is not None and not (n_tirages and int(n_tirages) >= 1):
        raise ValueError("n_hits demande n_tirages >= 1")
    if n_tirages is not None and int(n_tirages) < 1:
        raise ValueError("n_tirages doit valoir au moins 1")
    if int(n_comparaisons) < 1 or int(n) < 0:
        raise ValueError("n_comparaisons doit valoir au moins 1, n doit être positif")
    params = {str(k): v for k, v in (params or {}).items()}
    etude = racine_etude(etude)
    phase, sha_lock, doc = _etat_gel(etude)
    script, script_sha, code_gele = _script_appelant(etude, doc)
    declare = bool(declare)
    note_decl = None
    if phase == "apres_gel" and declare and not code_gele:
        declare, note_decl = False, "script hors du gel : test forcé exploratoire"
    sortie_abs = os.path.join(etude, sortie) if sortie else None
    ligne = {
        "t_utc": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "phase": phase, "lock_sha": sha_lock, "test": test, "declare_dans_plan": declare,
        "agent": agent, "donnees": donnees, "n": int(n),
        "n_effectif": int(n_effectif) if n_effectif is not None else None,
        "n_comparaisons": int(n_comparaisons), "params": params or {},
        "stat": float(stat) if stat is not None else None, "p": p,
        "n_tirages": int(n_tirages) if n_tirages else None,
        "script": script, "script_sha": script_sha, "code_gele": code_gele,
        "sortie": sortie,
        "sortie_sha": _sha_fichier(sortie_abs) if sortie_abs and os.path.isfile(sortie_abs) else None,
        "note": "; ".join(x for x in (note, note_decl) if x) or None,
    }
    ligne.update(_resolution_p(p, ligne["n_tirages"], n_hits))
    chemin = os.path.join(etude, FICHIER)
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "a+", encoding="utf-8") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        try:
            fh.seek(0)
            prec, nb, contenu = GENESE, 0, fh.read()
            for brute in contenu.splitlines():
                if brute.strip():
                    prec = hashlib.sha256(brute.encode("utf-8")).hexdigest()
                    nb += 1
            t = _lire_temoin(etude)
            if t is not None and (nb < t["n"] or (nb == t["n"] and prec != t["tete"])):
                raise ProtocoleRompu("registre tronqué ou réécrit depuis la dernière écriture (témoin hors "
                                     f"dossier : {t['n']} lignes) ; rien n'est ajouté, lancer registre.py verifier")
            ligne["prec"] = prec
            texte = json.dumps(ligne, ensure_ascii=False, sort_keys=True, default=_json)
            n_apres = nb + 1
            fh.seek(0, os.SEEK_END)
            if contenu and not contenu.endswith("\n"):
                fh.write("\n")
            fh.write(texte + "\n")
            fh.flush()
            os.fsync(fh.fileno())
            _temoin(etude, n_apres, hashlib.sha256(texte.encode("utf-8")).hexdigest())
        finally:
            fcntl.flock(fh, fcntl.LOCK_UN)
    return ligne


def lire(etude: str) -> tuple[list[dict], list[str]]:
    etude = racine_etude(etude)
    chemin = os.path.join(etude, FICHIER)
    lignes: list[dict] = []
    erreurs: list[str] = []
    prec = GENESE
    if os.path.isfile(chemin):
        with open(chemin, encoding="utf-8") as fh:
            for i, brute in enumerate(fh, 1):
                brute = brute.rstrip("\n")
                if not brute.strip():
                    continue
                try:
                    d = json.loads(brute)
                except json.JSONDecodeError:
                    erreurs.append(f"ligne {i} : JSON illisible")
                    prec = hashlib.sha256(brute.encode("utf-8")).hexdigest()
                    continue
                if d.get("prec") != prec:
                    erreurs.append(f"ligne {i} : chaîne rompue (ligne précédente effacée ou réécrite)")
                prec = hashlib.sha256(brute.encode("utf-8")).hexdigest()
                lignes.append(d)
    t = _lire_temoin(etude)
    if t is None and lignes:
        erreurs.append("AVERTISSEMENT aucun témoin hors dossier (étude déplacée, renommée ou autre machine) : "
                       "la fin du registre n'est pas vérifiable")
    if t is not None:
        if len(lignes) + sum(1 for e in erreurs if "illisible" in e) < t["n"]:
            erreurs.append(f"le témoin hors dossier compte {t['n']} lignes, le fichier moins : "
                           f"des lignes de fin ont été effacées")
        elif prec != t["tete"] and len(lignes) == t["n"]:
            erreurs.append("la dernière ligne ne correspond plus au témoin hors dossier : réécrite")
    return lignes, erreurs


def _afficher(erreurs: list[str]) -> list[str]:
    graves = [e for e in erreurs if not e.startswith("AVERTISSEMENT")]
    for e in erreurs:
        if e.startswith("AVERTISSEMENT"):
            print(e)
    if graves:
        print("INTÉGRITÉ ROMPUE :")
        for e in graves:
            print("  " + e)
    return graves


def cmd_compter(a: argparse.Namespace) -> None:
    lignes, erreurs = lire(a.etude)
    erreurs = _afficher(erreurs)
    if not lignes:
        print("registre vide")
        sys.exit(1 if erreurs else 0)
    reelles = [x for x in lignes if x.get("donnees", "reelles") == "reelles"]
    synth = len(lignes) - len(reelles)
    comp = sum(int(x.get("n_comparaisons") or 1) for x in reelles)
    par_agent = Counter(x.get("agent") for x in reelles)
    par_phase = Counter(x.get("phase") for x in reelles)
    non_decl = [x for x in reelles if not x.get("declare_dans_plan")]
    hors_gel = [x for x in reelles if x.get("phase") == "apres_gel" and not x.get("code_gele")]
    non_resolus = [x for x in reelles if x.get("p_non_resolu")]
    print(f"lignes sur données réelles : {len(reelles)} (contrôles synthétiques à part : {synth})")
    print("par phase : " + ", ".join(f"{k} {v}" for k, v in par_phase.most_common()))
    print(f"comparaisons réelles au total (balayages compris) : {comp}")
    print("par agent : " + ", ".join(f"{k} {v}" for k, v in par_agent.most_common()))
    print(f"non déclarées dans le plan (exploratoires) : {len(non_decl)}, dont venues de code non gelé : "
          f"{len(hors_gel)}")
    if par_phase.get("avant_gel"):
        print(f"ATTENTION : {par_phase['avant_gel']} test(s) sur données réelles AVANT le gel : "
              f"le plan a été écrit après les avoir vus")
    print(f"p non résolus (ne pas citer) : {len(non_resolus)}")
    if comp:
        print(f"seuil officiel, Bonferroni sur toutes les comparaisons réelles : {a.alpha}/{comp} = "
              f"{a.alpha / comp:.3g}")
    else:
        print("aucune comparaison sur données réelles : pas de seuil à calculer")
    sys.exit(1 if erreurs else 0)


def cmd_verifier(a: argparse.Namespace) -> None:
    lignes, erreurs = lire(a.etude)
    graves = _afficher(erreurs)
    if graves:
        sys.exit(1)
    temoin = "sans témoin hors dossier" if erreurs else "conforme au témoin hors dossier"
    print(f"registre intact : {len(lignes)} lignes, chaîne continue, {temoin}")
    sys.exit(0)


def cmd_exporter(a: argparse.Namespace) -> None:
    lignes, erreurs = lire(a.etude)
    caches = {"stat", "p", "hits", "p_ic95", "p_borne_sup_95", "sortie_sha", "note_p", "prec", "p_non_resolu",
              "note", "params"}
    dest = os.path.realpath(a.sortie)
    if dest.startswith(racine_etude(a.etude) + os.sep):
        sys.exit("l'export aveugle va hors du dossier de l'étude (par exemple dans mktemp -d)")
    with open(dest, "w", encoding="utf-8") as fh:
        for ligne in lignes:
            fh.write(json.dumps({k: v for k, v in ligne.items() if k not in caches}, ensure_ascii=False) + "\n")
    suite = " (registre rompu, voir verifier)" if erreurs else ""
    print(f"export aveugle : {len(lignes)} lignes dans {dest}{suite}")


def _bool_oui_non(v: str) -> bool:
    v = v.strip().lower()
    if v in {"oui", "o", "yes", "y", "true", "1"}:
        return True
    if v in {"non", "n", "no", "false", "0"}:
        return False
    raise argparse.ArgumentTypeError("--declare attend oui ou non")


def cmd_ajouter(a: argparse.Namespace) -> None:
    try:
        d = enregistrer(a.etude, a.test, a.declare, a.n, a.agent, n_effectif=a.n_effectif,
                        params=json.loads(a.params) if a.params else None, stat=a.stat, p=a.p,
                        n_tirages=a.n_tirages, n_hits=a.n_hits, n_comparaisons=a.n_comparaisons,
                        donnees=a.donnees, sortie=a.sortie, note=a.note)
    except (ProtocoleRompu, ValueError) as e:
        sys.exit(str(e))
    print(json.dumps(d, ensure_ascii=False, default=_json))


def main() -> None:
    p = argparse.ArgumentParser(description="Registre des tests d'une étude")
    sp = p.add_subparsers(dest="cmd", required=True)
    g = sp.add_parser("ajouter")
    g.add_argument("etude")
    g.add_argument("--test", required=True)
    g.add_argument("--declare", required=True, type=_bool_oui_non)
    g.add_argument("--n", type=int, required=True)
    g.add_argument("--n-effectif", dest="n_effectif", type=int)
    g.add_argument("--n-comparaisons", dest="n_comparaisons", type=int, default=1)
    g.add_argument("--agent", required=True)
    g.add_argument("--params")
    g.add_argument("--stat", type=float)
    g.add_argument("--p", type=float)
    g.add_argument("--n-tirages", dest="n_tirages", type=int)
    g.add_argument("--n-hits", dest="n_hits", type=int)
    g.add_argument("--donnees", choices=["reelles", "synthetiques"], default="reelles")
    g.add_argument("--sortie")
    g.add_argument("--note")
    c = sp.add_parser("compter")
    c.add_argument("etude")
    c.add_argument("--alpha", type=float, default=0.05)
    sp.add_parser("verifier").add_argument("etude")
    x = sp.add_parser("exporter-aveugle")
    x.add_argument("etude")
    x.add_argument("sortie")
    a = p.parse_args()
    {"ajouter": cmd_ajouter, "compter": cmd_compter, "verifier": cmd_verifier,
     "exporter-aveugle": cmd_exporter}[a.cmd](a)


if __name__ == "__main__":
    main()
