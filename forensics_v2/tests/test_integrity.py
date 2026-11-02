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
    """Historical code, data and the README stay as published on the branch base."""
    try:
        _git("cat-file", "-e", BASE)
    except subprocess.CalledProcessError:
        pytest.skip("base commit not in this clone")
    changed = [p for p in _git("diff", "--name-only", BASE, "--").split("\n") if p]
    assert [p for p in changed if not p.startswith(("forensics_v2/", ".github/workflows/forensics_v2"))] == []


def test_no_api_key_shape_in_tracked_files():
    for p in _tracked():
        if p.is_file():
            assert not KEY_SHAPE.findall(p.read_bytes()), p


def test_private_outputs_are_ignored():
    for rel in ("forensics_v2/private_trades/TRADES_2024_2025.csv", "forensics_v2/private_trades/WALLET_ATTRIBUTION.json"):
        assert subprocess.run(["git", "check-ignore", "-q", rel], cwd=ROOT).returncode == 0
    assert not [p for p in _tracked() if "private_trades" in str(p)]


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
