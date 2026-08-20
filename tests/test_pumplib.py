"""pumplib: the swap filter, the robust price series, the temporal clustering
and the two bootstrap engines that produce the confidence intervals of m2, m5
and m6.

The bootstraps carry an explicit promise: their generator is written out in the
module so the interval is the same on any machine and any Python version. These
tests are what makes that promise checkable.
"""
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
def test_bootstrap_median_ci_is_pinned_to_an_exact_value():
    """The generator is written out in the module precisely so this value does
    not move between machines or Python versions. If it moves, the published
    intervals of m2 and m6 moved with it."""
    xs = [float(i) for i in range(1, 11)]
    assert P.bootstrap_median_ci(xs, n_boot=200, seed=42) == (3.0, 8.0)
    assert P.bootstrap_median_ci(xs) == (3.0, 8.5)


def test_bootstrap_median_ci_does_not_depend_on_the_global_random_state():
    import random
    xs = [float(i) for i in range(1, 11)]
    random.seed(1)
    first = P.bootstrap_median_ci(xs)
    random.seed(999999)
    assert P.bootstrap_median_ci(xs) == first


def test_bootstrap_median_ci_filters_none_and_refuses_a_short_sample():
    assert P.bootstrap_median_ci([1.0, 2.0]) == (None, None)
    assert P.bootstrap_median_ci([1.0, None]) == (None, None), "None ne compte pas"
    assert P.bootstrap_median_ci([1.0, None, 2.0, 3.0, None, 4.0, 5.0],
                                 n_boot=100, seed=1) == (1.0, 5.0)


# -------------------------------------------- cluster_bootstrap_mean_ci -----
def test_cluster_bootstrap_mean_ci_brackets_its_own_point_estimate():
    """The docstring states the estimator resampled is the mean of the cluster
    means, and that the other candidate (pooling the tokens) would give an
    interval not containing its own point estimate. This checks the first half."""
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


def test_a_power_of_two_number_of_clusters_collapses_the_interval():
    """KNOWN LIMITATION, pinned here so it is never discovered by surprise.

    The generator is `state = (1103515245 * state + 12345) % 2**31` and the draw
    is `state % len(keys)`. The low bits of that recurrence have a period equal
    to their modulus, so when the number of clusters is a power of two the draw
    cycles through every cluster exactly once per resample: each resample is the
    whole set, the resampled mean is always the point estimate, and the interval
    has zero width.

    No published figure is affected: m5 resamples 20 clusters, and no committed
    interval in docs/out/ has zero width. It is the corpus that keeps this off,
    not the code, which is why it is written down.
    """
    eight = {"c%d" % i: [float(i)] for i in range(8)}
    lo, hi = P.cluster_bootstrap_mean_ci(eight, n_boot=500, seed=7)
    assert lo == hi, "huit grappes: intervalle de largeur nulle"

    seven = {"c%d" % i: [float(i)] for i in range(7)}
    lo7, hi7 = P.cluster_bootstrap_mean_ci(seven, n_boot=500, seed=7)
    assert lo7 < hi7, "sept grappes: comportement normal"
