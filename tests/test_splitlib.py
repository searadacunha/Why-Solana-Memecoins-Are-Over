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
