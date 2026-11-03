"""What this branch promises about the rest of the repository and about publication."""
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BASE = "6565245e3f5d48b0e6a987ebe6f2aa5954fb00be"
KEY_SHAPE = re.compile(rb"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")


def _git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def _tracked():
    return [ROOT / p for p in _git("ls-files", "forensics_v2").split("\n") if p]


def test_nothing_outside_forensics_v2_changed():
    """Historical code and data stay as published on the branch base, and the README only gains one sentence."""
    try:
        _git("cat-file", "-e", BASE)
    except subprocess.CalledProcessError:
        pytest.skip("base commit not in this clone")
    changed = [p for p in _git("diff", "--name-only", BASE, "--").split("\n") if p]
    outside = [p for p in changed if p != "README.md" and not p.startswith(("forensics_v2/", ".github/workflows/forensics_v2"))]
    assert outside == []
    # The one correction the author allowed after the reconciliation: a line added, none changed.
    readme = _git("diff", "--numstat", BASE, "--", "README.md").split()
    assert readme[:2] in ([], ["2", "0"]), readme


def test_no_api_key_shape_in_tracked_files():
    for p in _tracked():
        if p.is_file():
            assert not KEY_SHAPE.findall(p.read_bytes()), p


def test_private_outputs_are_ignored():
    for rel in ("forensics_v2/private_trades/TRADES_2024_2025.csv", "forensics_v2/private_trades/WALLET_ATTRIBUTION.json"):
        assert subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0
    assert not [p for p in _tracked() if "private_trades" in str(p)]


def test_no_private_trade_figure_in_tracked_files():
    """His totals are computed from the private files at run time, so this test publishes none of them."""
    trades = Path(__file__).resolve().parents[1] / "private_trades" / "TRADES_2024_2025.csv"
    if not trades.exists():
        pytest.skip("private trades not on this machine")
    import csv
    with open(trades) as f:
        rows = list(csv.DictReader(f))
    q4 = [r for r in rows if r["t_open_utc"] < "2025-01-01"]
    closed = [r for r in q4 if r["closed"] == "True"]
    lamports = sum(int(r["realised_lamports"]) for r in closed)
    figures = {"%.2f" % (lamports / 1e9), "%.3f" % (lamports / 1e9), str(lamports), "{:,}".format(len(q4)),
               "{:,}".format(len(closed))}
    for p in _tracked():
        if not p.is_file() or p.suffix == ".json" or "docs/baseline" in str(p) or "AUDIT" in p.name:
            continue  # raw on-chain numbers in data files can repeat a figure by chance
        text = p.read_text(errors="ignore")
        found = [x for x in figures if x in text]
        assert not found, "%s carries a private total: %s" % (p, len(found))


def test_no_private_wallet_in_tracked_files():
    """Runs only where the private ledger exists: the author's wallets must never reach the public branch."""
    ledger = Path.home() / "Documents/Crypto/WSMO-historical-edge-2024/historical_edge_2024/derived/q1_ledger.json"
    if not ledger.exists():
        pytest.skip("private ledger not on this machine")
    import json
    private = {w for w in json.loads(ledger.read_text())["candidates"]}
    extra = Path(__file__).resolve().parents[1] / "private_trades" / "WALLET_ATTRIBUTION.json"
    if extra.exists():
        private |= {r["wallet"] for r in json.loads(extra.read_text())["wallets"] if r["class"] != "THIRD_PARTY_INFRASTRUCTURE"}
    private -= {"6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU"}
    for p in _tracked():
        if p.is_file():
            text = p.read_text(errors="ignore")
            leaked = [w for w in private if w in text]
            assert not leaked, "%s names %d private wallets" % (p, len(leaked))
