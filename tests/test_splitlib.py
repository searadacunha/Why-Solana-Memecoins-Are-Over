"""splitlib.find_splits: the amount-quasi-equality + time-window grouping that
detects a single sum split through a swap service into several fresh wallets."""
import splitlib


def test_detects_a_three_wallet_split():
    funding = {
        "w1": [(2.976815600, 100)],
        "w2": [(2.976815600, 250)],
        "w3": [(2.976815600, 400)],
        "loner": [(5.0, 100)],
    }
    clusters = splitlib.find_splits(funding)
    assert len(clusters) == 1
    c = clusters[0]
    assert c["n_wallets"] == 3
    assert c["amount_sol"] == 2.976815600
    assert c["span_seconds"] == 300
    assert "first_ts" in c and "date" in c   # both historical fields present


def test_min_cluster_not_met():
    funding = {"w1": [(2.0, 100)], "w2": [(2.0, 150)]}   # only 2 wallets
    assert splitlib.find_splits(funding) == []


def test_amount_outside_tolerance_is_not_grouped():
    # 2.0 vs 2.5 differ by far more than rel_tol (1e-4) -> never one split.
    funding = {"a": [(2.0, 100)], "b": [(2.0, 110)],
               "c": [(2.5, 120)], "d": [(2.5, 130)], "e": [(2.5, 140)]}
    clusters = splitlib.find_splits(funding)
    assert all(c["amount_sol"] != 2.0 for c in clusters)  # the 2.0 pair never clusters
    assert any(c["amount_sol"] == 2.5 and c["n_wallets"] == 3 for c in clusters)


def test_time_window_excludes_far_apart_transfers():
    funding = {"a": [(3.0, 0)], "b": [(3.0, 100)],
               "c": [(3.0, 999999)]}   # c is hours away
    clusters = splitlib.find_splits(funding, window_s=3600)
    assert clusters == []              # only 2 within the window -> below min_cluster


# --- a1_null_model.detect must agree with find_splits on criterion B -----------------
# The null model keeps its own copy of the grouping so it stays runnable from
# published data alone. A copy is only a copy if it behaves identically: these
# tests pin detect()'s B to "find_splits returns at least one cluster".

import random

import a1_null_model


def _as_group(funding):
    """funding dict -> the wallet-group structure a1_null_model.detect eats,
    preserving insertion order so both sides sort the same event list."""
    return [{"wallet": w, "events": [(amt, ts, None, None) for amt, ts in lst]}
            for w, lst in funding.items()]


def test_a1_detect_B_matches_find_splits_on_failed_seed_shadow():
    # Regression for the earlier a1 semantics, which marked events 'used' even
    # when the seed's cluster failed: the failed seed w1 absorbs w2's event,
    # and the real cluster {w2, w3, w4} only exists if w2 may still seed it.
    funding = {
        "w1": [(1.0, 0)],
        "w2": [(1.00002, 3500)],   # within w1's window -> absorbed by the failed seed
        "w3": [(1.00004, 5000)],   # outside w1's window, inside w2's
        "w4": [(1.00006, 5500)],
    }
    assert len(splitlib.find_splits(funding)) == 1          # {w2, w3, w4}
    _, B, _ = a1_null_model.detect(_as_group(funding))
    assert B is True


def test_a1_detect_B_matches_find_splits_fuzzed():
    rng = random.Random(20260810)
    for _ in range(300):
        funding = {}
        for wi in range(rng.randint(2, 8)):
            base = rng.choice([1.0, 2.5, 2.976815600])
            funding[f"w{wi}"] = [
                (base * (1 + rng.uniform(-3e-4, 3e-4)), rng.randint(0, 8000))
                for _ in range(rng.randint(1, 3))
            ]
        expected = len(splitlib.find_splits(funding)) >= 1
        _, B, _ = a1_null_model.detect(_as_group(funding))
        assert B is expected, f"divergence on {funding}"
