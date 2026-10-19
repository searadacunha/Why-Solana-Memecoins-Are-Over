"""pumplib: the swap filter, the robust price series, the temporal clustering
and the two bootstrap engines that produce the confidence intervals of m2, m5
and m6.

The bootstraps must retain sampling variability, including at sample sizes
where the former LCG suppressed it. Fixed seeds must reproduce without using
the global random state; the cluster-mean variance has an analytical check.
"""
import math
import random
import statistics

import pytest

import pumplib as P


# ------------------------------------------------------------ clean_swaps ---
def _cap(swaps):
    return {"mint": "M", "swaps": swaps}


def test_clean_swaps_drops_the_unusable_and_keeps_the_rest():
    d = _cap([
        {"ts": 3, "side": "buy", "sol": 1.0, "tokens": 100.0},
        {"ts": 1, "side": "sell", "sol": 2.0, "tokens": 50.0},
        {"ts": 2, "side": "buy", "sol": 0.0, "tokens": 10.0},    # sol nul
        {"ts": 2, "side": "buy", "sol": 1.0, "tokens": 0.0},     # tokens nuls
        {"ts": None, "side": "buy", "sol": 1.0, "tokens": 10.0},  # sans horodatage
        {"ts": 4, "side": "transfer", "sol": 1.0, "tokens": 10.0},  # side inconnu
    ])
    out = P.clean_swaps(d)
    assert [s["ts"] for s in out] == [1, 3], "tries par ts, les 4 autres rejetes"


def test_clean_swaps_computes_the_executed_price():
    out = P.clean_swaps(_cap([{"ts": 1, "side": "buy", "sol": 3.0, "tokens": 12.0}]))
    assert out[0]["p"] == 0.25


def test_clean_swaps_on_a_capture_without_swaps():
    assert P.clean_swaps({"mint": "M"}) == []
    assert P.clean_swaps(_cap(None)) == []


# ---------------------------------------------------------- robust_series ---
def test_robust_series_ignores_dust_and_takes_the_bucket_median():
    """The failure this exists to prevent: one 0.002 SOL swap whose implicit
    price is orders of magnitude off must not become the price of its bucket."""
    sw = P.clean_swaps(_cap([
        {"ts": 0, "side": "buy", "sol": 1.0, "tokens": 100.0},     # p = 0.01
        {"ts": 1, "side": "buy", "sol": 2.0, "tokens": 100.0},     # p = 0.02
        {"ts": 2, "side": "buy", "sol": 0.002, "tokens": 1e-9},    # poussiere, p enorme
    ]))
    ser = P.robust_series(sw, bucket=30)
    assert len(ser) == 1
    assert ser[0][1] == 0.015, "mediane de 0.01 et 0.02, la poussiere est hors du calcul"


def test_robust_series_is_empty_when_every_swap_is_dust():
    sw = P.clean_swaps(_cap([{"ts": 0, "side": "buy", "sol": 0.01, "tokens": 1.0}]))
    assert P.robust_series(sw) == []


def test_robust_series_separates_buckets():
    sw = P.clean_swaps(_cap([
        {"ts": 0, "side": "buy", "sol": 1.0, "tokens": 100.0},
        {"ts": 45, "side": "buy", "sol": 1.0, "tokens": 50.0},
    ]))
    assert [t for t, _ in P.robust_series(sw, bucket=30)] == [0, 30]


# --------------------------------------------------------------- clusters ---
def test_clusters_splits_strictly_beyond_the_gap():
    caps = [{"mint": "a", "created": 0}, {"mint": "b", "created": 1800},
            {"mint": "c", "created": 3601}]
    out = P.clusters(caps, gap_s=1800)
    assert out["a"] == out["b"], "un ecart egal au seuil ne coupe pas"
    assert out["c"] != out["b"], "un ecart superieur au seuil coupe"


def test_clusters_is_independent_of_input_order():
    caps = [{"mint": "c", "created": 5000}, {"mint": "a", "created": 0},
            {"mint": "b", "created": 100}]
    assert P.clusters(caps) == P.clusters(list(reversed(caps)))


# ------------------------------------------------- bootstrap_median_ci ------
def test_bootstrap_median_ci_is_deterministic():
    xs = [float(i) for i in range(1, 11)]
    runs = {P.bootstrap_median_ci(xs, n_boot=500, seed=42) for _ in range(3)}
    assert len(runs) == 1


@pytest.mark.parametrize("sample_size", [8, 16, 20])
def test_bootstrap_median_preserves_sampling_variation_at_even_sizes(sample_size):
    """Modulo-LCG draws fixed each quartile's count and froze this median."""
    xs = [float(i % 4) for i in range(sample_size)]
    lo, hi = P.bootstrap_median_ci(xs, n_boot=2000, seed=7)
    assert 0.0 <= lo < statistics.median(xs) < hi <= 3.0


@pytest.mark.parametrize("clustered", [False, True])
def test_bootstraps_do_not_depend_on_or_modify_global_random_state(clustered):
    xs = [float(i) for i in range(1, 11)]
    values = {i: [x] for i, x in enumerate(xs)} if clustered else xs
    bootstrap = P.cluster_bootstrap_mean_ci if clustered else P.bootstrap_median_ci
    saved = random.getstate()
    try:
        random.seed(1)
        before = random.getstate()
        first = bootstrap(values, n_boot=500, seed=42)
        assert random.getstate() == before
        random.seed(999999)
        before = random.getstate()
        assert bootstrap(values, n_boot=500, seed=42) == first
        assert random.getstate() == before
    finally:
        random.setstate(saved)


def test_bootstrap_median_ci_filters_none_and_refuses_a_short_sample():
    assert P.bootstrap_median_ci([1.0, 2.0]) == (None, None)
    assert P.bootstrap_median_ci([1.0, None]) == (None, None), "None ne compte pas"
    with_missing = [1.0, None, 2.0, 3.0, None, 4.0, 5.0]
    complete = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert P.bootstrap_median_ci(with_missing, n_boot=100, seed=1) == P.bootstrap_median_ci(
        complete, n_boot=100, seed=1)


# -------------------------------------------- cluster_bootstrap_mean_ci -----
def test_cluster_bootstrap_mean_ci_brackets_its_own_point_estimate():
    """The interval on this example brackets the mean of the cluster means."""
    by = {"c0": [1.0], "c1": [2.0, 2.5], "c2": [3.0], "c3": [10.0, 11.0, 12.0],
          "c4": [4.0], "c5": [5.5], "c6": [20.0]}
    cmeans = [sum(v) / len(v) for v in by.values()]
    point = sum(cmeans) / len(cmeans)
    lo, hi = P.cluster_bootstrap_mean_ci(by, n_boot=500, seed=7)
    assert lo <= point <= hi
    assert lo < hi, "sept grappes: l'intervalle n'est pas degenere"


def test_cluster_bootstrap_mean_ci_refuses_fewer_than_three_clusters():
    assert P.cluster_bootstrap_mean_ci({"a": [1.0], "b": [2.0]}) == (None, None)


def test_cluster_bootstrap_mean_ci_is_deterministic():
    by = {"c%d" % i: [float(i), float(i) + 1] for i in range(7)}
    runs = {P.cluster_bootstrap_mean_ci(by, n_boot=300, seed=3) for _ in range(3)}
    assert len(runs) == 1


@pytest.mark.parametrize("n_clusters", [8, 16, 20])
def test_cluster_bootstrap_preserves_sampling_variation_at_even_sizes(n_clusters):
    """Twenty clusters also failed: the LCG fixed all four residue counts."""
    by = {i: [float(i % 4)] for i in range(n_clusters)}
    lo, hi = P.cluster_bootstrap_mean_ci(by, n_boot=2000, seed=7)
    assert 0.0 <= lo < 1.5 < hi <= 3.0


def test_cluster_bootstrap_sd_matches_the_independent_draw_formula():
    """For 20 means cycling through 0,1,2,3, Var(mean*) = 1.25 / 20.

    With one replicate both returned quantiles expose that resampled mean.
    Across 4000 fixed seeds its SD must be close to the exact value 0.25;
    the former LCG returns 1.5 for every seed and has zero SD here.
    """
    means = [float(i % 4) for i in range(20)]
    by = {i: [v] for i, v in enumerate(means)}
    sampled_means = [P.cluster_bootstrap_mean_ci(by, n_boot=1, seed=seed)[0]
                     for seed in range(4000)]
    expected_sd = math.sqrt(statistics.pvariance(means) / len(means))
    assert expected_sd == 0.25
    assert statistics.pstdev(sampled_means) == pytest.approx(expected_sd, rel=0.05)


def test_cluster_bootstrap_gives_each_cluster_mean_equal_weight():
    """A large zero-return cluster must not outweigh the seven small ones.

    The median number of zero-cluster draws among eight is one, so the
    central percentiles of the mean of cluster means are (0 + 7*10) / 8.
    Pooling the underlying observations would give a different result.
    """
    by = {0: [0.0] * 100, **{i: [10.0] for i in range(1, 8)}}
    assert P.cluster_bootstrap_mean_ci(by, n_boot=10000, seed=7, alpha=0.99) == (8.75, 8.75)
