"""Checks on this investigation. Offline. Run: python -m pytest investigations/ansem_network/tests -q"""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(ROOT.parents[1]))

B58 = re.compile(r"[1-9A-HJ-NP-Za-km-z]{32,44}")


def tracked_text():
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".csv", ".json", ".jsonl", ".html", ".py"}:
            yield p, p.read_text(errors="ignore")


def test_ledger_is_true_on_raw_data():
    import check_ledger
    assert check_ledger.main() == 0


def test_fee_share_decoder_on_the_creation_setting():
    import ana_10_deployer
    ana_10_deployer.test()


def test_snowflake_time_matches_the_endpoint():
    from col_10_x_posts import snowflake_ts
    from lib import utc
    assert utc(snowflake_ts("2066989048497905753")) == "2026-06-16 20:59:26"
    assert utc(snowflake_ts("2070870549492883555")) == "2026-06-27 14:03:08"


def test_curveball_keeps_margins_and_controls_pass():
    import random
    from collections import Counter
    from ana_20_rarity import curveball
    sets = [{"a", "b", "c"}, {"a", "d"}, {"b", "e", "f"}, {"c", "e"}]
    before = (sorted(len(s) for s in sets), Counter(w for s in sets for w in s))
    curveball(sets, 500, random.Random(1))
    assert (sorted(len(s) for s in sets), Counter(w for s in sets for w in s)) == before
    assert json.load(open(ROOT / "evidence" / "rarity.json"))["controls"]["planted_pair_p"] < 0.01


def test_tables_agree_on_the_launch():
    row = next(r for r in csv.DictReader(open(ROOT / "TOKENS.csv")) if r["mint"].startswith("9cRCn9"))
    assert float(row["gift_to_ansem_wallet"]) == 650_000_000
    assert abs(float(row["dev_buy_sol"]) - 86.06810776) < 1e-6
    n = json.load(open(ROOT / "evidence" / "numbers.json"))
    assert n["deployer"]["launches"] == sum(1 for r in csv.DictReader(open(ROOT / "TOKENS.csv")) if r["creator_wallet"].startswith("yHCxHBEa"))


def test_no_cross_sol_edge_between_the_two_sides():
    d = json.load(open(ROOT / "evidence" / "link_tests_extended.json"))
    assert d["direct_sol_between_sides"] == []


def test_every_address_named_in_the_report_exists_in_the_data():
    """An address completed by hand would appear nowhere else."""
    text = (ROOT / "REPORT.md").read_text()
    corpus = "".join(t for p, t in tracked_text() if p.name not in {"REPORT.md", "TOP10.md", "README.md", "PROVENANCE.md"})
    for a in set(B58.findall(text)):
        assert a in corpus, a


def test_no_private_wallet_of_the_author():
    ledger = Path.home() / "Documents/Crypto/WSMO-historical-edge-2024/historical_edge_2024/derived/q1_ledger.json"
    extra = Path.home() / "Documents/Crypto/WSMO-forensics-v2/forensics_v2/private_trades/WALLET_ATTRIBUTION.json"
    if not ledger.exists():
        pytest.skip("private ledger not on this machine")
    private = set(json.loads(ledger.read_text())["candidates"])
    if extra.exists():  # the file also lists third-party hot wallets, which are not his
        private |= {w["wallet"] for w in json.loads(extra.read_text())["wallets"] if w.get("class") != "THIRD_PARTY_INFRASTRUCTURE"}
    hits = [p.name for p, t in tracked_text() if private & set(B58.findall(t))]
    assert not hits, "%d files hold a private wallet" % len(hits)


def test_plain_writing_in_the_deliverables():
    for name in ("REPORT.md", "TOP10.md", "README.md", "PROVENANCE.md", "TIMELINE.md"):
        assert "—" not in (ROOT / name).read_text(), name
