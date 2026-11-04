from collections import Counter

from forensics_v2.investigations import cosigners_v2 as V


def test_verdict_rule_as_written():
    many = {"M1": 25.0, "M2": 0.5, "M3": 0.1, "M4": 0.05, "M5": 0.3}
    assert V.verdict(many, True) == "service"
    assert V.verdict({**many, "M5": 0.85}, True) == "private"
    assert V.verdict({**many, "M4": 0.6}, True) == "private"
    assert V.verdict({**many, "M1": 5.0}, True) == "not_separated"
    assert V.verdict(many, False) == "no_payer"


def test_measures_count_only_persistent_payers():
    m = V.measures({"a": {0, 1}, "b": {0}}, Counter({"a": 75, "b": 25}), {"b"}, {"a"})
    assert m["M1"] == 1 and m["M2"] == 0.75 and m["M3"] == 1.0 and m["M4"] == 0.25 and m["M5"] == 1.0


def test_fisher():
    assert abs(V.fisher_two_sided(3, 1, 1, 3) - 0.4857) < 0.001
