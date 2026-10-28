"""Regression checks for missing signatures in the phase-1 null model."""
from pathlib import Path
import runpy

DETECT = runpy.run_path(str(Path(__file__).resolve().parents[1] / "code" / "a1_null_model.py"))["detect"]


def wallet(name, amount, ts, signature):
    return {"wallet": name, "events": [(amount, ts, None, signature)]}


def test_missing_signatures_are_not_shared_transactions():
    # Different timestamps and amounts avoid criterion B; no funder avoids C.
    # Previously None and "" were each grouped as if they were a real tx id.
    for absent in (None, ""):
        group = [wallet("one", 1.0, 100, absent), wallet("two", 4.0, 10000, absent)]
        assert DETECT(group) == (False, False, False)


def test_real_shared_signature_still_triggers_criterion_a():
    group = [wallet("one", 1.0, 100, "valid-shared-transaction"),
             wallet("two", 4.0, 10000, "valid-shared-transaction")]
    assert DETECT(group) == (True, False, False)
