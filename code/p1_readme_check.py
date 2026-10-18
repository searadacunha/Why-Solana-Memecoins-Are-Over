#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""p1_readme_check.py -- recomputes every figure quoted in README.md, as
p0_pitfalls_check.py does for docs/PITFALLS.md. Output is a claim ledger: per
quoted figure, the literal sentence, the artefact behind it, the value that
artefact holds, whether the two agree. Expected values are written out in
CLAIMS below rather than scraped from the prose with a regex, so a claim that
moves or is reworded turns up as ABSENT instead of being skipped. Figures no
artefact backs sit in UNBACKED: counted at every run, never fatal, since
unsourced is a different defect from wrong.

A failing row means the README states a number this code does not produce. Fix
the README, or fix the measurement; never adjust the expected value to match
the prose. Every row reproduces today, so a red row is a real signal.

Only the literal `texte` substrings are matched, so a correct number can sit in
a sentence whose surrounding claim is false and the row still passes on the
digits. A row's `texte` therefore has to span the clause the figure supports,
not just the digits.

Rows may carry a `texte_fr`, checked against _relecture_fr/README.fr.md exactly
as `texte` is against README.md, and a declared French sentence that is not
found fails the run. That file is untracked by design (the repository publishes
in English), so a clone lacks it and the check is then skipped. Coverage is
partial and the count is printed at every run. French results are printed but
never written: a value derived from an untracked file would reproduce on the
author's machine and nowhere else, which is what run_all.py --strict catches.

Reads (all committed, no network, no private state)
    README.md                              the claims themselves
    _relecture_fr/README.fr.md             optional and untracked: the French
                                           edition, for the rows declaring a
                                           `texte_fr`; feeds stdout only
    docs/out/a9_g2y_prelaunch.json         act I burst
    docs/out/expl_ledger.json              the 2024 deposit ledger, rebuilt on
                                           chain; since 2026-08 it carries the
                                           deposit address in the clear
                                           (published: README.md, "Author")
    docs/out/m2_entry_price.json           entry multiple
    data/v05_creation_block.json           creation-slot buy
    data/v06_curve_ladder.json             curve captured
    data/v07_exit.json                     exit delay
    data/v09_signature_gros_tokens.json    frozen 70-token sample
    data/screens/trades/index.json         the 19 screenshotted executions
    post_detection_edge/data/SNAPSHOT.json the live detector's snapshot (act IV)
    alpha_patterns/tables/*.json           the October 2026 search (act IV):
                                           discovery_summary, operator_forensics,
                                           team_rhythm, team_absorption,
                                           x2_timing_summary

Writes
    docs/out/p1_readme_check.json          the ledger (byte-compared by --strict:
                                           no timestamp, no run id, rows sorted)

Usage :  python3 code/p1_readme_check.py [--out ...]
Sortie :  docs/out/p1_readme_check.json
Exit code : 1 if any row is MISMATCH or ABSENT, or if README.fr.md is present
            and a declared `texte_fr` is not found in it; 0 otherwise. The mere
            absence of README.fr.md never fails the run.
"""
import argparse
import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import settings
import pumplib as P

# Number words, so a derived value can be compared to prose that spells its
# figures out ("three seconds", "at least six wallets"). Presentation only.
MOTS = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five",
        6: "six", 7: "seven", 8: "eight", 9: "nine", 10: "ten",
        11: "eleven", 12: "twelve"}


class Absent(Exception):
    """An artefact, or a key inside it, is not there. An expected outcome
    rather than a crash: it is reported as a row status and it fails the run."""


# --------------------------------------------------------------------- load
_CACHE = {}


def _consts_py(path):
    """Module-level literal assignments of a .py file, without importing it.

    A file such as exit_ladder.py runs work at import or under __main__. The
    values wanted here are constants, and ast.literal_eval reads them without
    executing a line of the file."""
    out = {}
    tree = ast.parse(open(path, encoding="utf-8").read())
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        tgt = node.targets[0]
        if not isinstance(tgt, ast.Name):
            continue
        try:
            out[tgt.id] = ast.literal_eval(node.value)
        except ValueError:
            continue          # not a literal; not a constant we can check
    return out


def source(rel):
    """Load a source by repo-relative path. .json -> object, .md -> text,
    .py -> {NAME: literal}. Raises Absent if the file is not there."""
    if rel in _CACHE:
        return _CACHE[rel]
    path = os.path.join(settings.ROOT, rel)
    if not os.path.exists(path):
        raise Absent("artefact absent: %s" % rel)
    if rel.endswith(".json"):
        with open(path, encoding="utf-8") as f:
            obj = json.load(f)
    elif rel.endswith(".py"):
        obj = _consts_py(path)
    else:
        obj = open(path, encoding="utf-8").read()
    _CACHE[rel] = obj
    return obj


def walk(obj, chemin, rel):
    """Follow a list of keys / indices into a loaded artefact."""
    cur = obj
    for step in chemin:
        try:
            cur = cur[step]
        except (KeyError, IndexError, TypeError):
            raise Absent("missing key: %s -> %s" % (rel, "/".join(map(str, chemin))))
    return cur


# -------------------------------------------------------------------- derives
# Each derive rebuilds, from one artefact, the exact form the README quotes.
# They are the audit trail: the transformation is code rather than a claim
# about code.

def d_v05_42_42(a):
    g = a["agregats"]
    return "%d/%d" % (g["n_zero_petit_acheteur_avant"], g["n_lancements"])


def d_v06_42_of_42(a):
    g = a["agregats"]
    return "%d out of %d" % (g["n_zero_achat_courbe_avant_bloc"], g["n_lancements"])


def d_v09_signature(a):
    toks = a["tokens"]
    if len(toks) != a["n"]:
        raise Absent("v09: n=%d but %d tokens listed" % (a["n"], len(toks)))
    k = sum(1 for t in toks if t["full_snipe"])
    return "%d (%.1f%%)" % (k, 100.0 * k / a["n"])


def d_trades_plage(a):
    g = [t["gain_pct"] for t in a["trades"]]
    if len(g) != a["n"]:
        raise Absent("index.json: n=%d but %d trades listed" % (a["n"], len(g)))
    # Truncated, not rounded: the README writes +100 % for 100.06 and
    # +28 465 % for 28465.63.
    return "%d (+%d%% to +%s%%)" % (a["n"], int(min(g)), format(int(max(g)), ","))


BONS_MOIS = ("2024-10", "2024-11", "2024-12")


def _expl_bons_mois(a, cle):
    """One good-months total of expl_ledger.json, checked against its own
    per-month breakdown before it is returned.

    The artefact publishes both, so the addition is done here rather than
    assumed: a good-months total that does not equal the sum of the three
    months it names is an arithmetic defect inside the artefact."""
    g = a["good_months_2024_10_12"]
    somme = round(sum(a["per_month"][m][cle] for m in BONS_MOIS), 4)
    if somme != round(g[cle], 4):
        raise Absent("expl_ledger: good_months %s = %r but the three months sum "
                     "to %r" % (cle, g[cle], somme))
    return g[cle]


def d_expl_sol_bons_mois(a):
    return format(_expl_bons_mois(a, "sol"), ",.4f")


def d_expl_usd_bons_mois(a):
    return format(_expl_bons_mois(a, "usd"), ",.2f")


def d_expl_usd_fenetre(a):
    """The full-window USD total, with the window bound the README names.

    The README says "to 2 Feb 2025"; the artefact carries the bound it actually
    used. If the two part company the row goes red rather than the prose
    relabelling a different window."""
    hi = a["window_utc"]["hi_exclusive"]
    if hi != "2025-02-02":
        raise Absent("expl_ledger: window hi_exclusive is %r, the README says "
                     "2 Feb 2025" % hi)
    return format(a["total_usd_full_window"], ",.2f")


def d_expl_passthrough(a):
    """In against out, the check that makes the totals readable.

    A deposit address is a pass-through: everything that lands is swept to the
    exchange. The two figures matching to a hundredth of a SOL is the evidence
    that the balance-delta reconstruction caught the transfers rather than some
    subset of them, so the residual is recomputed here from the two sides
    instead of being taken from the artefact's own field.

    The tolerance is one unit of the last published place, which is arithmetic
    rather than slack. expl_ledger publishes sol_in, sol_swept_out and
    residual_sol each rounded to 4 decimals but computes the residual from the
    unrounded sides: here in - out = 0.0097 while residual_sol is 0.0098,
    because the two roundings go opposite ways. 1e-4 is the exact resolution of
    the figures the artefact hands over, so a stricter equality would fail on a
    correct artefact."""
    p = a["passthrough_check"]
    if round(p["sol_in"], 4) != round(a["total_sol_full_window"], 4):
        raise Absent("expl_ledger: passthrough sol_in %r != total_sol_full_window "
                     "%r" % (p["sol_in"], a["total_sol_full_window"]))
    ecart = abs((p["sol_in"] - p["sol_swept_out"]) - p["residual_sol"])
    if ecart > 1.0e-4:
        raise Absent("expl_ledger: residual_sol %r but in - out = %r (off by "
                     "%.2e, more than the published 4-decimal resolution)"
                     % (p["residual_sol"], p["sol_in"] - p["sol_swept_out"], ecart))
    return ("**%s SOL** arrived over the full window against **%s SOL** swept out"
            % (format(p["sol_in"], ",.4f"), format(p["sol_swept_out"], ",.4f")))


def d_trades_n(a):
    """The count of screenshotted trades. The README used to quote the range of
    their gains too; since 2026-09 it quotes the count alone."""
    if len(a["trades"]) != a["n"]:
        raise Absent("index.json: n=%d but %d trades listed" % (a["n"], len(a["trades"])))
    return int(a["n"])


# --- act IV: alpha_patterns/tables/*.json ------------------------------------
def d_ap_good_rate(a):
    p = a["population"]["Y2"]
    if p["eligible"] == 0 or round(p["good"] / p["eligible"], 12) != round(p["rate"], 12):
        raise Absent("team_absorption: good / eligible does not reproduce the stored rate")
    return "%d (%.1f %%)" % (p["good"], 100.0 * p["rate"])


def d_ap_corroboration(a):
    """How much the link types confirm each other: for a pair of launches linked
    one way (shared wallet L1, shared funder L3, two shared wallets L4, same
    ticket configuration L5), the share also linked another way, divided by the
    same share among pairs of the same week. Two ratios are left out: the ones
    with a zero baseline (undefined) and L4 -> L1, which is 1.0 by construction
    (two shared wallets imply one) and measures nothing."""
    c = a["groupings"]["corroboration"]
    kinds = ("L1", "L3", "L4", "L5")
    ratios = []
    for k in kinds:
        for other in kinds:
            if other == k or (k, other) == ("L4", "L1"):
                continue
            base = c[k]["sameweek_baseline_" + other]
            if base > 0:
                ratios.append(c[k]["also_" + other] / base)
    if not ratios:
        raise Absent("operator_forensics: no corroboration ratio with a non-zero baseline")
    return "%d to %d" % (round(min(ratios)), round(max(ratios)))


def d_ap_rate_range(a):
    rates = [g["rate_x2"] for g in a["groups"]["U"] if g["eligible"] >= 10]
    if len(rates) != a["groupings"]["stats"]["U"]["groups_ge"]["10"]:
        raise Absent("operator_forensics: groups listed with >= 10 outcomes differ from the count")
    return "%d %% to %d %%" % (round(100.0 * min(rates)), round(100.0 * max(rates)))


def d_ap_teams_mixed(a):
    p = a["population"]
    return "%d of the %d" % (p["within_teams_mixed"], p["within_teams"])


def d_ap_hc1(a):
    h = a["history_prediction"]["U"]["ALL"]["Y2_HC1"]
    if round(h["successes"] / h["n"], 12) != round(h["rate"], 12):
        raise Absent("operator_forensics: HC1 successes / n does not reproduce the stored rate")
    return "%d times in %d, against %.1f %%" % (h["successes"], h["n"], 100.0 * h["rest_rate"])


def d_ap_rhythm_tests(a):
    rows = [v for v in list(a["rhythm_vs_outcome"].values()) + list(a["sequences"].values())
            if isinstance(v, dict) and v.get("q_bh_sections_2_3") is not None]
    if len(rows) != a["family_23_tests"]:
        raise Absent("team_rhythm: %d tests with a q against family_23_tests=%d"
                     % (len(rows), a["family_23_tests"]))
    return "%d, %s" % (len(rows), "none passes" if not any(v.get("passes") for v in rows) else "some pass")


def d_ap_within_team(a):
    rows = a["within_team"]
    return "%d, %s" % (len(rows), "none passes" if not any(v.get("passes") for v in rows.values()) else "some pass")


def d_ap_demand_share_27(a):
    m = a["mechanism"]["timeline_medians"]["27"]["M7_demand_over_inventory"]
    return "%.1f %% / %.1f %%" % (100.0 * m["good_median"], 100.0 * m["bad_median"])


def d_ap_alert_age(a):
    d = a["mechanism"]["descriptive"]["age_alert"]
    return "%.1f s / %.1f s" % (d["good_median"], d["bad_median"])


def d_ap_sold_c40(a):
    d = a["mechanism"]["descriptive"]["team_sold_share_c40"]
    return "%.1f %% / %.1f %%" % (100.0 * d["good_median"], 100.0 * d["bad_median"])


def d_ap_price_paths(a):
    p = a["mechanism"]["price_after_entry"]
    return "%.2f / %.2f ; %.2f / %.2f" % (p["at_30"]["good_median"], p["at_300"]["good_median"],
                                          p["at_30"]["bad_median"], p["at_300"]["bad_median"])


def d_ap_tradable(a):
    rows = a["tradable"]
    return "%d, %s" % (len(rows), "none passes" if not any(v.get("passes") for v in rows.values()) else "some pass")


def _m4_ubiquite(prefixe, infra_attendue):
    """The two ANSEM slot-0 wallets, looked up in the ubiquity table of
    m4_infra.json. The wallets' presence across the 282-token corpus is the
    only part of the ANSEM block any artefact of this repository covers; the
    slot-0 SOL amounts are not measured here and are declared UNBACKED."""
    def f(a):
        hit = [e for e in a["top_ubiquite"] if e["adresse"].startswith(prefixe)]
        if not hit:
            raise Absent("m4_infra: no ubiquity row starting with %s" % prefixe)
        e = hit[0]
        return "%d of %d, infra=%s" % (e["tokens"], a["n_tokens"],
                                       "yes" if e["classee_infra"] else "no")
    return f


DERIVES = {
    "v05_42_42": d_v05_42_42,
    "v06_42_of_42": d_v06_42_of_42,
    "v09_signature": d_v09_signature,
    "trades_plage": d_trades_plage,
    "trades_n": d_trades_n,
    "ap_good_rate": d_ap_good_rate,
    "ap_corroboration": d_ap_corroboration,
    "ap_rate_range": d_ap_rate_range,
    "ap_teams_mixed": d_ap_teams_mixed,
    "ap_hc1": d_ap_hc1,
    "ap_rhythm_tests": d_ap_rhythm_tests,
    "ap_within_team": d_ap_within_team,
    "ap_sold_c40": d_ap_sold_c40,
    "ap_demand_share_27": d_ap_demand_share_27,
    "ap_alert_age": d_ap_alert_age,
    "ap_price_paths": d_ap_price_paths,
    "ap_tradable": d_ap_tradable,
    "expl_sol_bons_mois": d_expl_sol_bons_mois,
    "expl_usd_bons_mois": d_expl_usd_bons_mois,
    "expl_usd_fenetre": d_expl_usd_fenetre,
    "expl_passthrough": d_expl_passthrough,
    "m4_op1": _m4_ubiquite("yHCxHBEa", False),
    "m4_sniper": _m4_ubiquite("9ryBR3Sn", True),
}


# ---------------------------------------------------------------------- rules
# How the artefact's value is turned into the form the README quotes. One
# function per rule, so the transformation applied to each row is explicit.
def _echelon(v):
    """A rung of exit_ladder.LADDER -> the README's own wording."""
    seuil, part = v
    return "sell %g%% at %g×" % (part * 100.0, seuil)


REGLES = {
    "exact": lambda v: v,
    "round0": lambda v: round(v),
    "round1": lambda v: round(v, 1),
    "round4": lambda v: round(v, 4),
    "round1_pct": lambda v: round(100.0 * v, 1),
    "round0_pct": lambda v: round(100.0 * v),
    "dec9": lambda v: "%.9f" % v,
    "pct_pm": lambda v: "±%g%%" % (100.0 * v),
    "echelon": _echelon,
}


# ----------------------------------------------------------------------- table
# One row per figure quoted in README.md that has a committed artefact behind it.
# 'texte' is the literal substring as it appears in README.md: if the sentence
# is reworded the row goes ABSENT rather than passing unnoticed.
CLAIMS = [
    # ---------------------------------------------------------------- act I --
    {"section": "1 Act I", "texte": "* **9 wallets**",
     "source": "docs/out/a9_g2y_prelaunch.json",
     "chemin": ["cas_reference", "n_portefeuilles"], "regle": "exact",
     "attendu": 9, "niveau": "MESURE"},
    {"section": "1 Act I", "texte": "all funded with exactly **2.976815600 SOL**",
     "source": "docs/out/a9_g2y_prelaunch.json",
     "chemin": ["cas_reference", "montant_sol"], "regle": "dec9",
     "attendu": "2.976815600", "niveau": "MESURE"},
    {"section": "1 Act I", "texte": "all funded within **343 seconds**",
     "source": "docs/out/a9_g2y_prelaunch.json",
     "chemin": ["cas_reference", "etendue_s"], "regle": "exact",
     "attendu": 343, "niveau": "MESURE"},
    {"section": "1 Act I", "texte": "token launched **7.6 hours later**",
     "source": "docs/out/a9_g2y_prelaunch.json",
     "chemin": ["cas_reference", "delai_creation_h_depuis_dernier_credit"],
     "regle": "round1", "attendu": 7.6, "niveau": "MESURE",
     "note": "delay from the LAST credit; from the first one a9 measures 7.7 h"},

    # ------------------------------------------------- exploiting the pattern -
    # The three exit rungs used to be checked here, against LADDER in
    # code/exit_ladder.py. p1 cannot settle them: that constant is an assertion
    # rather than a record, and the tranche sizes were never written down. They
    # are listed in UNBACKED below instead.
    # The 2024 table. Its money and its counts are now read on chain by
    # code/expl_ledger.py. The SOL total used to be checked by adding up a table
    # inside docs/EXPLOITATION.md, which established only that the README agreed
    # with another document of this repository; do not restore it beside the
    # on-chain rows. Every row carries its French sentence, spanning the whole
    # table row rather than the digits alone -- the FR edition writes these
    # figures with a decimal comma and a space for thousands, so a bare number
    # would also have to be transcribed and could not be shared with the
    # English form.
    {"section": "0 Front page",
     "texte": "I withdrew **$237,137.87** trading memecoins",
     "texte_fr": "j'ai retiré **237 137,87 $**",
     "source": "docs/out/expl_ledger.json", "derive": "expl_usd_bons_mois",
     "regle": "exact", "attendu": "237,137.87", "niveau": "MESURE",
     "note": "the headline occurrence of the same figure as the table row "
             "below; it gets its own row because a substring check cannot see "
             "a second occurrence, and the front page is what most people read"},
    {"section": "2 Exploiting the pattern",
     "texte": '| Withdrawn, Oct–Dec 2024                    | **1,190.6957 SOL** |',
     "texte_fr": "| Retiré, oct.–déc. 2024 | **1 190,6957 SOL** |",
     "source": "docs/out/expl_ledger.json", "derive": "expl_sol_bons_mois",
     "regle": "exact", "attendu": "1,190.6957", "niveau": "MESURE",
     "note": "sum of the deposit address's own positive balance deltas on "
             "successful transactions, the three 2024 months; sweeps out to "
             "the exchange are reported separately and excluded. Replaces the "
             "1 200.12 asserted before, which no on-chain read produced"},
    {"section": "2 Exploiting the pattern",
     "texte": "| USD value at each transfer's own day price |    **$237,137.87** |",
     "texte_fr": "| USD au prix du jour propre à chaque transfert | "
                 "**237 137,87 $** |",
     "source": "docs/out/expl_ledger.json", "derive": "expl_usd_bons_mois",
     "regle": "exact", "attendu": "237,137.87", "niveau": "MESURE",
     "note": "each transfer valued at the Binance SOLUSDT close of its own UTC "
             "day, never at a window average; expl_ledger publishes "
             "missing_price_days and raises rather than skipping a day"},
    {"section": "2 Exploiting the pattern",
     "texte": '| Incoming transfers, Oct–Dec 2024           |            **245** |',
     "texte_fr": "| Transferts entrants, oct.–déc. 2024 | **245** |",
     "source": "docs/out/expl_ledger.json",
     "chemin": ["good_months_2024_10_12", "n_transfers"], "regle": "exact",
     "attendu": 245, "niveau": "INFERE",
     "note": "one successful transaction with a positive delta = one transfer. "
             "Batched or multi-hop routes are not unbundled, so this is weaker "
             "than the SOL it sums to -- the money does not depend on how the "
             "transfers are counted"},
    {"section": "2 Exploiting the pattern",
     "texte": '| Distinct sending wallets                   |             **74** |',
     "texte_fr": "| Portefeuilles expéditeurs distincts, oct.–déc. 2024 | "
                 "**74** |",
     "source": "docs/out/expl_ledger.json",
     "chemin": ["good_months_2024_10_12", "distinct_senders"], "regle": "exact",
     "attendu": 74, "niveau": "INFERE",
     "note": "sender = the counterparty with the most negative delta in the "
             "same transaction. A heuristic, and named as one in the artefact's "
             "INFERE block: it bounds the number of senders, it is not an exact "
             "transfer-level decomposition. The addresses are published as a "
             "count, never as a list; ownership is not claimed, since the same "
             "heuristic resolves four of the 74 to third-party exchange hot "
             "wallets this repository labels elsewhere"},
    {"section": "2 Exploiting the pattern",
     "texte": '| Full window through 2 Feb 2025             |    **$244,315.58** |',
     "texte_fr": "| Fenêtre complète jusqu'au 2 février 2025 | "
                 "**244 315,58 $** |",
     "source": "docs/out/expl_ledger.json", "derive": "expl_usd_fenetre",
     "regle": "exact", "attendu": "244,315.58", "niveau": "MESURE",
     "note": "2024-10-01 to 2025-02-02 exclusive, the bound checked by the "
             "derive against the artefact's own window_utc. Replaces the "
             "246 945.59 asserted before"},
    {"section": "2 Exploiting the pattern",
     "texte": "**1,226.4663 SOL** arrived over the full window against "
              "**1,226.4566 SOL** swept out",
     "texte_fr": "**1 226,4663 SOL** sont arrivés sur la fenêtre complète "
                 "contre **1 226,4566 SOL** balayés",
     "source": "docs/out/expl_ledger.json", "derive": "expl_passthrough",
     "regle": "exact",
     "attendu": "**1,226.4663 SOL** arrived over the full window against "
                "**1,226.4566 SOL** swept out",
     "niveau": "MESURE",
     "note": "the consistency check that makes the totals readable: a deposit "
             "address holds nothing, so in and out must meet. They do, to "
             "0.0098 SOL. The derive recomputes that residual from the two "
             "sides rather than trusting the artefact's own field"},
    {"section": "2 Exploiting the pattern",
     "texte": '| Example trades in documented sample        |             **19** |',
     "texte_fr": "| Trades d'exemple (un échantillon ; la fenêtre en compte "
                 "des centaines) | **19 (de +100 % à +28 465 %)** |",
     "source": "data/screens/trades/index.json", "derive": "trades_n",
     "regle": "exact", "attendu": 19,
     "niveau": "MESURE (on the screenshot sample, not on the book)"},

    # -------------------------------------------------------------- act III --
    {"section": "3 Act III",
     "texte": "across **42/42 manually verified launches**, with each transaction checked individually",
     "source": "data/v05_creation_block.json", "derive": "v05_42_42",
     "regle": "exact", "attendu": "42/42", "niveau": "MESURE",
     "note": "launches with zero small buyer before the block / total"},
    {"section": "3 Act III", "texte": "* approximately **85 SOL**",
     "source": "data/v05_creation_block.json",
     "chemin": ["agregats", "sol_bloc_med"], "regle": "round0",
     "attendu": 85, "niveau": "MESURE"},
    {"section": "3 Act III", "texte": "* approximately **79% of supply**",
     "source": "data/v05_creation_block.json",
     "chemin": ["agregats", "part_supply_med"], "regle": "round0_pct",
     "attendu": 79, "niveau": "MESURE"},
    {"section": "3 Act III",
     "texte": "of 70 tokens reaching at least $500k market cap",
     "source": "data/v09_signature_gros_tokens.json", "chemin": ["n"],
     "regle": "exact", "attendu": 70, "niveau": "MESURE"},
    {"section": "3 Act III", "texte": "**58 of 70 (82.9%)** exhibited the same signature",
     "source": "data/v09_signature_gros_tokens.json", "derive": "v09_signature",
     "regle": "exact", "attendu": "58 (82.9%)", "niveau": "MESURE"},

    # ------------------------------------------------- act III, ANSEM block --
    # The two rows the ANSEM section CAN back. Restored with the mint and the
    # creation slot so the rest of the block is falsifiable rather than merely
    # unsourced; the slot-0 amounts remain in UNBACKED below.

    # ---------------------------------------------------------- conclusion ---
    {"section": "6 Why Solana memecoins are over",
     "texte": "on **42/42** manually verified launches and **58 of 70 (82.9%)** of an independent frozen sample",
     "source": "data/v06_curve_ladder.json", "derive": "v06_42_of_42",
     "regle": "exact", "attendu": "42 out of 42", "niveau": "MESURE",
     "note": "launches with zero curve purchase before the block / total"},

    {"section": "6 Why Solana memecoins are over",
     "texte": "**58 of 70 (82.9%)** of an independent frozen sample",
     "source": "data/v09_signature_gros_tokens.json", "derive": "v09_signature",
     "regle": "exact", "attendu": "58 (82.9%)", "niveau": "MESURE",
     "note": "second occurrence of the frozen-sample figure, in the closing list"},
    {"section": "6 Why Solana memecoins are over",
     "texte": "approximately **79% of supply** on the 42 verified launches",
     "source": "data/v05_creation_block.json",
     "chemin": ["agregats", "part_supply_med"], "regle": "round0_pct",
     "attendu": 79, "niveau": "MESURE"},

    # ---------------------------------------------------------------- act IV --
    # The exploratory search of October 2026 (alpha_patterns/) and the detector
    # snapshot it ran on. Every row reads a committed JSON; the French reports
    # beside them quote the same figures and are not read here.
    {"section": "5 Act IV", "texte": "alerted on **1,657 launches**",
     "source": "post_detection_edge/data/SNAPSHOT.json", "chemin": ["n_alerts"],
     "regle": "exact", "attendu": 1657, "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "over 415 features",
     "source": "alpha_patterns/tables/discovery_summary.json",
     "chemin": ["atoms", "n_features"], "regle": "exact", "attendu": 415,
     "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "On the **1,015 launches** before 15 September 2026",
     "source": "alpha_patterns/tables/team_absorption.json",
     "chemin": ["population", "alerts"], "regle": "exact", "attendu": 1015,
     "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "**612** had an observable one-hour outcome",
     "source": "alpha_patterns/tables/team_absorption.json",
     "chemin": ["population", "Y2", "eligible"], "regle": "exact", "attendu": 612,
     "niveau": "MESURE"},
    {"section": "5 Act IV",
     "texte": "**168 (27.5 %)** doubled from the entry price read 5 to 15 s after the alert",
     "source": "alpha_patterns/tables/team_absorption.json", "derive": "ap_good_rate",
     "regle": "exact", "attendu": "168 (27.5 %)", "niveau": "MESURE",
     "note": "GOOD = two consecutive reads at or above 2x the entry price within 1 h"},
    {"section": "5 Act IV", "texte": "confirm each other **47 to 212 times** above chance",
     "source": "alpha_patterns/tables/operator_forensics.json", "derive": "ap_corroboration",
     "regle": "exact", "attendu": "47 to 212", "niveau": "MESURE",
     "note": "share of launch pairs linked one way that are also linked another way, "
             "over the same share among pairs of the same week; the two ratios with a "
             "zero baseline are left out"},
    {"section": "5 Act IV", "texte": "**33 teams** have five or more observable launches",
     "source": "alpha_patterns/tables/operator_forensics.json",
     "chemin": ["groupings", "stats", "U", "groups_ge", "5"], "regle": "exact",
     "attendu": 33, "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "**19** have ten or more",
     "source": "alpha_patterns/tables/operator_forensics.json",
     "chemin": ["groupings", "stats", "U", "groups_ge", "10"], "regle": "exact",
     "attendu": 19, "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "from **0 % to 58 %**",
     "source": "alpha_patterns/tables/operator_forensics.json", "derive": "ap_rate_range",
     "regle": "exact", "attendu": "0 % to 58 %", "niveau": "MESURE",
     "note": "x2 rates of the union-identity groups with ten or more observable launches"},
    {"section": "5 Act IV", "texte": "(p = 0.0017 within the day)",
     "source": "alpha_patterns/tables/operator_forensics.json",
     "chemin": ["heterogeneity", "U", "Y2", "10", "p_within_day"], "regle": "round4",
     "attendu": 0.0017, "niveau": "MESURE",
     "note": "10,000 reshufflings of the outcomes inside each calendar day"},
    {"section": "5 Act IV", "texte": "**28 of the 33 teams** have both",
     "source": "alpha_patterns/tables/team_rhythm.json", "derive": "ap_teams_mixed",
     "regle": "exact", "attendu": "28 of the 33", "niveau": "MESURE"},
    {"section": "5 Act IV",
     "texte": "is right **3 times in 29**, against **44.1 %** for the launches it leaves aside",
     "source": "alpha_patterns/tables/operator_forensics.json", "derive": "ap_hc1",
     "regle": "exact", "attendu": "3 times in 29, against 44.1 %", "niveau": "MESURE",
     "note": "HC1: ten or more resolved antecedents and a 90 % Wilson lower bound of "
             "the group's rate above the market's; chronological identity"},
    {"section": "5 Act IV", "texte": "one launch every **20.6 minutes** in the median inside a session",
     "source": "alpha_patterns/tables/team_rhythm.json",
     "chemin": ["rhythm_descriptive", "gap_in_session_quantiles_min", "50"],
     "regle": "round1", "attendu": 20.6, "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "17 pre-registered tests, none passes",
     "source": "alpha_patterns/tables/team_rhythm.json", "derive": "ap_rhythm_tests",
     "regle": "exact", "attendu": "17, none passes", "niveau": "MESURE"},
    {"section": "5 Act IV",
     "texte": "**32 variables** measured before the alert",
     "source": "alpha_patterns/tables/team_rhythm.json", "derive": "ap_within_team",
     "regle": "exact", "attendu": "32, none passes", "niveau": "MESURE",
     "note": "the README's 'none passes the correction' is checked by the same derive"},
    {"section": "5 Act IV",
     "texte": "has sold **4.6 %** of what it holds on a GOOD launch and **4.5 %** on a BAD one",
     "source": "alpha_patterns/tables/team_absorption.json", "derive": "ap_sold_c40",
     "regle": "exact", "attendu": "4.6 % / 4.5 %", "niveau": "MESURE",
     "note": "medians at creation + 40 s, the launches whose window reaches it"},
    {"section": "5 Act IV",
     "texte": "**×1.09** thirty seconds after the entry and **×1.55** after five minutes; "
              "a BAD one at **×1.01** and **×0.64**",
     "source": "alpha_patterns/tables/team_absorption.json", "derive": "ap_price_paths",
     "regle": "exact", "attendu": "1.09 / 1.55 ; 1.01 / 0.64", "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "a **median 375 s** after the entry",
     "source": "alpha_patterns/tables/x2_timing_summary.json",
     "chemin": ["t_hit_2x_s", "p50"], "regle": "round0", "attendu": 375,
     "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "**1.2 %** of the GOOD launches confirm it within 30 s",
     "source": "alpha_patterns/tables/x2_timing_summary.json",
     "chemin": ["share_of_good_confirmed_within_s", "30"], "regle": "round1_pct",
     "attendu": 1.2, "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "Forty tests of demand at the moment of decision: none passes",
     "source": "alpha_patterns/tables/team_absorption.json", "derive": "ap_tradable",
     "regle": "exact", "attendu": "40, none passes", "niveau": "MESURE"},
    {"section": "5 Act IV",
     "texte": "**11.0 %** on the GOOD launches and **9.9 %** on the BAD, 27 s after the alert",
     "source": "alpha_patterns/tables/team_absorption.json", "derive": "ap_demand_share_27",
     "regle": "exact", "attendu": "11.0 % / 9.9 %", "niveau": "MESURE",
     "note": "external SOL paid over the value of the team's inventory at the alert price, "
             "medians at alert + 27 s, the last cut before the end of the transaction window"},
    {"section": "5 Act IV",
     "texte": "the detector alerts a median **12.6 s / 12.3 s** after the creation (GOOD / BAD launches)",
     "source": "alpha_patterns/tables/team_absorption.json", "derive": "ap_alert_age",
     "regle": "exact", "attendu": "12.6 s / 12.3 s", "niveau": "MESURE"},
    {"section": "5 Act IV", "texte": "the signal came **7.6 hours** before the launch",
     "source": "docs/out/a9_g2y_prelaunch.json",
     "chemin": ["cas_reference", "delai_creation_h_depuis_dernier_credit"],
     "regle": "round1", "attendu": 7.6, "niveau": "MESURE",
     "note": "second occurrence of the act I delay, in act IV"},
]

# Figures quoted in README.md that no committed artefact backs. They never fail
# the run: "unsourced" is a different defect from "wrong". They are printed and
# counted at every run so the number stays a visible, falling quantity.
UNBACKED = [
    # Four entries used to sit here: 238 989.57 $, 246 945.59 $, 312 withdrawals
    # and 97 trading wallets. They are gone from this list because they were
    # measured, not because they were deleted: code/expl_ledger.py reconstructs
    # the deposit ledger on chain and the README now prints what it produced --
    # 237 137.87 $, 244 315.58 $, 245 transfers, 74 senders. The four figures
    # they replaced were assertions whose cents appeared in no file, no script
    # and no data source. This list may only shrink this way, or by a figure
    # leaving the README; never by dropping a row that is still asserted.
    {"section": "1 Act I",
     "texte": "roughly **2% of supply** — around 20 million tokens",
     "raison": "data/ holds no purchased-token quantity for the phase-1 tokens; "
               "a9 lists this under non_etabli"},
    {"section": "4 Real-world example",
     "texte": "**84.74 SOL** purchased by a single wallet",
     "raison": "the ANSEM launch has no committed artefact; the 84.74 in "
               "data/v09 belongs to a different mint, with 8 buyers"},
    {"section": "4 Real-world example",
     "texte": "**85.007 SOL**",
     "raison": "the ANSEM launch has no committed artefact; data/v05 covers a "
               "different, frozen set of 42 mints"},
    {"section": "4 Real-world example",
     "texte": "`9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump`",
     "raison": "the mint is published so the block is falsifiable, but no "
               "script here measures it; re-running the frozen v05/v06 chain "
               "on it needs $HELIUS_API_KEYS and is the declared remedy"},
    {"section": "4 Real-world example", "texte": "**426930467**",
     "raison": "the ANSEM launch has no committed artefact"},
    {"section": "4 Real-world example", "texte": "only **two buyers**",
     "raison": "the ANSEM launch has no committed artefact"},
    {"section": "4 Real-world example", "texte": "sixteen signatures",
     "raison": "the ANSEM launch has no committed artefact"},
    {"section": "4 Real-world example", "texte": "**2026-06-16 21:05:48 UTC**",
     "raison": "the ANSEM launch has no committed artefact"},
    {"section": "2 Exploiting the pattern",
     "texte": "ChangeNOW-funded wallet buying at least **2% of supply**",
     "raison": "second occurrence of the entry rule, in the Exploiting the "
               "Pattern section; same gap as the Act I wording -- data/ holds "
               "no purchased-token quantity for the phase-1 tokens"},
    {"section": "2 Exploiting the pattern",
     "texte": "1% of supply at most",
     "raison": "the operator's own position size, stated as personal prose. No "
               "artefact of this repository measures the size of my own buys; "
               "the deposit ledger measures only the net that reached the "
               "exchange. Kept as prose, never a measured row"},
    # Starting capital is the author's firsthand trading account. Keep its
    # wording tracked separately from the withdrawal measurements: the exchange
    # ledger records funds received, not the initial fiat funding.
    {"section": "0 Trading record",
     "texte": "I started with **€400**.",
     "raison": "starting capital confirmed directly by Benjamin Da Cunha in "
               "his firsthand trading account. The automated ledger check "
               "reconstructs withdrawals reaching the exchange; it does not "
               "reconstruct the initial fiat funding"},
    # Act IV quotes three results of the nine pre-registered studies in prose.
    # Their results.md tables carry them; no JSON of those studies is read here.
    {"section": "5 Act IV", "texte": "78 % of the supply, exit wallets",
     "raison": "economic_mechanics/results.md, the share of the supply the "
               "coordinated snipers hold after the creation slot (TRAIN and "
               "VALIDATION medians); stated in its results tables, not in a JSON "
               "this ledger reads. The same quantity on the alpha_patterns launches "
               "is the 77.7 % / 77.8 % row of alpha_patterns/tables/team_absorption.json"},
    {"section": "5 Act IV", "texte": "four snipers",
     "raison": "economic_mechanics/results.md, the typical coordinated launch (four sniper "
               "wallets, about 25 SOL each); results tables, no JSON read here"},
    {"section": "5 Act IV",
     "texte": "the same snipers funded again a median 21 minutes later (18 in the validation weeks)",
     "raison": "economic_mechanics/results.md, median gap between two launches of "
               "the same snipers (21 min TRAIN, 18 min VALIDATION); results table, "
               "no JSON read here"},
    {"section": "5 Act IV", "texte": "Yes, in about four launches out of five",
     "raison": "coordination_detection/README.md: the rate of launches with a "
               "coordinated funding and buying structure, TRAIN and VALIDATION; "
               "results table, no JSON read here"},
]


# The French edition. It carries the same figures, transcribed by hand, and
# until now no code compared the two. Relative to settings.ROOT so nothing here
# depends on the machine.
README_FR = os.path.join("_relecture_fr", "README.fr.md")


# ------------------------------------------------------------------ evaluation
def evaluer_fr(row, texte_fr_source):
    """-> statut of one row's French sentence.

    "-" when the row declares none, which is still most of them, or when the
    French edition is not in this checkout: it is untracked by design, so a
    clone has nothing to compare against. "OK" when the declared sentence is
    present verbatim. "ABSENT" when the file is there and the sentence is not,
    which fails the run like an English claim text that moved: declaring a
    French sentence promises it exists wherever the file does.
    """
    if not row.get("texte_fr") or texte_fr_source is None:
        return "-"
    return "OK" if row["texte_fr"] in texte_fr_source else "ABSENT"


def evaluer(row, readme):
    """-> (statut, valeur_rendue) for one claim row."""
    if row["texte"] not in readme:
        return "ABSENT", "claim text not found in README.md"
    try:
        art = source(row["source"])
        if row.get("derive"):
            brut = DERIVES[row["derive"]](art)
        else:
            brut = walk(art, row["chemin"], row["source"])
        val = REGLES[row["regle"]](brut)
    except (Absent, KeyError, IndexError, TypeError, ValueError,
            ZeroDivisionError) as exc:
        return "ABSENT", str(exc)
    return ("OK" if val == row["attendu"] else "MISMATCH"), val


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(P.HERE, "..", "docs", "out",
                                                  "p1_readme_check.json"))
    a = ap.parse_args()

    readme_path = os.path.join(settings.ROOT, "README.md")
    if not os.path.exists(readme_path):
        raise SystemExit("README.md not found at the repository root: %s ; run this "
                         "script from a checkout that still has it"
                         % os.path.relpath(readme_path, settings.ROOT))
    readme = open(readme_path, encoding="utf-8").read()

    # The French edition is optional as a file (a checkout may not carry the
    # relecture directory) but not as a check: if it is there, every row that
    # declares a French sentence must find it.
    fr_path = os.path.join(settings.ROOT, README_FR)
    fr_texte = (open(fr_path, encoding="utf-8").read()
                if os.path.exists(fr_path) else None)

    P.head("P1 : README CLAIM LEDGER", "MESURE")
    print("  Every figure quoted in README.md, the artefact behind it, and whether")
    print("  the two agree. A red row means the README states a number this code")
    print("  does not produce: fix the README, or fix the measurement.\n")

    lignes = []
    for row in CLAIMS:
        statut, val = evaluer(row, readme)
        lignes.append({
            "attendu": row["attendu"],
            "chemin": ("/".join(map(str, row["chemin"])) if row.get("chemin")
                       else "derive:" + row["derive"]),
            "niveau": row["niveau"],
            "note": row.get("note", ""),
            "section": row["section"],
            "source": row["source"],
            "statut": statut,
            "statut_fr": evaluer_fr(row, fr_texte),
            "texte": row["texte"],
            "texte_fr": row.get("texte_fr", ""),
            "valeur_artefact": val,
        })
    lignes.sort(key=lambda d: (d["section"], d["texte"]))

    hdr = "  %-8s  %-40s  %-34s  %-26s  %s"
    print(hdr % ("STATUT", "CLAIM (README.md)", "SOURCE", "ARTEFACT SAYS", "README SAYS"))
    print("  " + "-" * 144)
    sec = None
    for r in lignes:
        if r["section"] != sec:
            sec = r["section"]
            print("  [%s]" % sec)
        print(hdr % (r["statut"], _cut(r["texte"], 40), _cut(r["source"], 34),
                     _cut(r["valeur_artefact"], 26), _cut(r["attendu"], 30)))
    print()
    for r in lignes:
        if r["statut"] != "OK":
            print("  %-8s %s" % (r["statut"], r["texte"]))
            print("           artefact : %s = %s" % (r["source"], r["valeur_artefact"]))
            print("           README   : %s" % (r["attendu"],))
            if r["note"]:
                print("           note     : %s" % r["note"])

    # ------------------------------------------------------------- unbacked --
    non_source = []
    for row in UNBACKED:
        present = row["texte"] in readme
        non_source.append({"present_dans_readme": present, "raison": row["raison"],
                           "section": row["section"], "texte": row["texte"]})
    non_source.sort(key=lambda d: (d["section"], d["texte"]))

    n_present = sum(1 for r in non_source if r["present_dans_readme"])
    print("\n  UNSOURCED FIGURES STILL IN README.md: %d" % n_present)
    print("  (counted, never fatal: 'unsourced' is not the same defect as 'wrong')")
    for r in non_source:
        if r["present_dans_readme"]:
            print("    - %s" % r["texte"])
            print("      %s" % r["raison"])
        else:
            print("    - REMOVED from README.md: %s" % r["texte"])

    # ---------------------------------------------------------- french ------
    n_fr = sum(1 for r in lignes if r["statut_fr"] != "-")
    n_fr_ab = sum(1 for r in lignes if r["statut_fr"] == "ABSENT")
    print("\n  FRENCH EDITION (%s): %d of %d claim(s) declare a sentence there"
          % (README_FR, n_fr, len(lignes)))
    if fr_texte is None:
        print("    file not in this checkout -- untracked by design, so this is"
              " the normal state of a clone.")
        print("    The check is skipped, it never fails the run, and nothing"
              " from it reaches the artefact.")
    for r in lignes:
        if r["statut_fr"] == "ABSENT":
            print("    ABSENT  %s" % r["texte_fr"])
    print("    (the other %d rows are transcribed by hand and checked by "
          "nothing; that count is the gap, and it is meant to fall)"
          % (len(lignes) - n_fr))

    n_ok = sum(1 for r in lignes if r["statut"] == "OK")
    n_mm = sum(1 for r in lignes if r["statut"] == "MISMATCH")
    n_ab = sum(1 for r in lignes if r["statut"] == "ABSENT")

    P.kv("claims with a committed artefact", len(lignes))
    P.kv("  reproduced exactly", n_ok)
    P.kv("  MISMATCH (README != artefact)", n_mm)
    P.kv("  ABSENT (artefact, key, or claim text gone)", n_ab)
    P.kv("figures with no artefact at all", n_present,
         note="listed above, not fatal")
    P.kv("claims also checked in README.fr.md", n_fr,
         note="%d of them not found there" % n_fr_ab)

    # The French columns are stripped here, and the French counts are absent
    # below: _relecture_fr/README.fr.md is untracked by design, so any value
    # derived from it would reproduce on the author's machine and nowhere else.
    # Keeping them printed but unwritten is what makes this artefact regenerate
    # byte-for-byte from a clean clone. (See the module docstring.)
    claims_publies = [{k: v for k, v in r.items()
                       if k not in ("statut_fr", "texte_fr")}
                      for r in lignes]

    obj = {
        "claims": claims_publies,
        "n_absent": n_ab,
        "n_claims": len(lignes),
        "n_mismatch": n_mm,
        "n_non_source_present": n_present,
        "n_non_source_retire": len(non_source) - n_present,
        "n_ok": n_ok,
        "niveau": "MESURE",
        "non_source": non_source,
        "objet": "Every figure quoted in README.md, the artefact that produces it, "
                 "the value that artefact holds, and whether the two agree.",
        "regle": "A red row means the README states a number this code does not "
                 "produce. Fix the README, or fix the measurement. Never adjust "
                 "the expected value to match the prose.",
    }
    P.emit(obj, os.path.abspath(a.out))

    print("""
=> What is established: for every figure listed, the value the committed
   artefact holds and whether it agrees with the README's prose. [MESURE]
=> What is not established here: that the artefacts are themselves right. p1
   compares prose to artefacts; the artefacts are established by the scripts
   that produce them. [MESURE for the agreement, NON ETABLI for the substance]
=> Also not established: that the README is complete. A figure added without a
   row in CLAIMS or UNBACKED is invisible to this script. [NON ETABLI]
=> A red run is not a regression in p1. Fix the README, or fix the measurement;
   never adjust the expected value to match the prose. [MESURE]
=> Also not established: that README.fr.md is right. Only the rows declaring a
   `texte_fr` are compared to it; the rest of the French prose is transcribed
   by hand and checked by nothing. [NON ETABLI for the remainder]""")

    if n_mm or n_ab or n_fr_ab:
        sys.stdout.flush()
        sys.stderr.write(
            "p1: %d claim(s) of %d do not match the artefacts "
            "(%d MISMATCH, %d ABSENT), %d declared French sentence(s) not "
            "found in %s -- see docs/out/p1_readme_check.json\n"
            % (n_mm + n_ab, len(lignes), n_mm, n_ab, n_fr_ab, README_FR))
        raise SystemExit(1)


def _cut(x, n):
    s = str(x)
    return s if len(s) <= n else s[:n - 1] + "…"


if __name__ == "__main__":
    main()
