from forensics_v2.investigations import signal_matched as M


def test_bands_follow_the_plan():
    assert M.curve_band(None) is None
    assert (
        M.curve_band(4_999_999_999) == "under_5"
        and M.curve_band(5_000_000_000) == "5_to_20"
        and M.curve_band(20_000_000_000) == "20_to_85"
    )
    assert M.curve_band(85_000_000_000) is None
    assert M.age_band(59) == "a_1m" and M.age_band(60) == "b_10m" and M.age_band(3600) == "d_1d" and M.age_band(86400) == "e_more"
    assert M.age_band(-1) is None and M.age_band(None) is None


def test_exact_mcnemar_and_holm():
    assert M.mcnemar_exact(0, 0) == 1.0
    assert abs(M.mcnemar_exact(0, 5) - 0.0625) < 1e-12
    assert abs(M.mcnemar_exact(8, 2) - 0.109375) < 1e-12
    assert M.holm([0.01, 0.04]) == [0.02, 0.04]
    assert M.holm([0.04, 0.03]) == [0.06, 0.06]


def test_paired_counts_each_side():
    trip = {"S1": True}
    pairs = [
        {"trip": trip, "control": {"S1": False}},
        {"trip": trip, "control": {"S1": True}},
        {"trip": {"S1": False}, "control": {"S1": False}},
    ]
    r = M.paired(pairs, "S1")
    assert (r["author"], r["control"], r["only_author"], r["only_control"]) == (2, 1, 1, 0)
