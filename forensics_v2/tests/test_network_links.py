from forensics_v2.investigations.network_links import label_wallet
from forensics_v2.trace import Flow


def flow(src, dst, t, n=1_000_000_000):
    return Flow(src, dst, n, "s%d" % t, 1, t, "x", "instruction", None)


def test_many_senders_in_100_transactions_is_service_like():
    fl = [flow("s%d" % i, "w", 1000 + i) for i in range(18)]
    assert label_wallet(fl, [1000 + i for i in range(100)], "w")["label"] == "service-like"


def test_more_than_200_transactions_in_an_hour_is_service_like():
    assert label_wallet([], list(range(1000, 1201)), "w")["label"] == "service-like"


def test_few_senders_over_a_full_page_is_private_like():
    fl = [flow("a", "w", 1000), flow("b", "w", 1001)]
    r = label_wallet(fl, [1000 + 60 * i for i in range(100)], "w")
    assert r["label"] == "private-like" and r["top5_share_of_sol_received"] == 1.0


def test_a_short_read_stays_undetermined():
    assert label_wallet([flow("a", "w", 1000)], [1000, 1060], "w")["label"] == "undetermined"
