"""statlib: the Wilson interval and the None-filtering median/quantile that the
whole dossier's confidence intervals and medians go through."""
import math

import statlib


def test_wilson_n_zero_is_none():
    assert statlib.wilson(0, 0) == (None, None)


def test_wilson_clamped_to_unit_interval():
    lo, hi = statlib.wilson(0, 1)      # p = 0
    assert lo == 0.0
    assert 0.0 <= hi <= 1.0
    lo, hi = statlib.wilson(1, 1)      # p = 1
    assert hi == 1.0
    assert 0.0 <= lo <= 1.0


def test_wilson_known_value():
    # p = 1, n = 1: lower bound = 1 / (1 + z^2), upper = 1 (clamped).
    z = 1.96
    lo, hi = statlib.wilson(1, 1)
    assert hi == 1.0
    assert math.isclose(lo, 1.0 / (1.0 + z * z), rel_tol=1e-9)


def test_wilson_interval_brackets_point_estimate():
    lo, hi = statlib.wilson(58, 70)     # the 82.9 % headline
    assert lo < 58 / 70 < hi
    assert math.isclose(lo, 0.724, abs_tol=0.01)
    assert math.isclose(hi, 0.899, abs_tol=0.01)


def test_median_filters_none_and_handles_empty():
    assert statlib.median([3, 1, 2]) == 2
    assert statlib.median([1, 2, None]) == 1.5     # None dropped -> median(1,2)
    assert statlib.median([]) is None
    assert statlib.median([None, None]) is None


def test_quantile_nearest_rank_and_none_filter():
    assert statlib.quantile([1, 2, 3, 4], 0.0) == 1
    assert statlib.quantile([4, 3, 2, 1], 1.0) == 4      # sorted internally
    assert statlib.quantile([], 0.5) is None
    assert statlib.quantile([5, None, 1, None], 0.0) == 1
