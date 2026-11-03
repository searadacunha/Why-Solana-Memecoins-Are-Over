from forensics_v2.decode import JITO_TIP
from forensics_v2.investigations.same_operator import Reference, events, measure, percentile
from forensics_v2.investigations.trades_report import TOOL_FEE

TIP = next(iter(JITO_TIP))


def row(w, t, slot, sig=1, fee=5000, buy=True, tip=False, ok=True):
    moves = [{"k": "sol_transfer", "src": w, "dst": TIP if tip else TOOL_FEE, "n": 100}]
    return {
        "w": w,
        "t": t,
        "slot": slot,
        "ok": ok,
        "fee": fee,
        "signers": ["s"] * sig,
        "tok": {} if tip else {"m": 5 if buy else -5},
        "moves": moves,
    }


def test_events_attach_the_tip_of_the_same_slot_and_drop_failures():
    ev = events([row("a", 10, 1, fee=7000), row("a", 10, 1, tip=True), row("a", 20, 2, buy=False), row("a", 30, 3, ok=False)])
    assert [(e["side"], e["tip"], e["prio"]) for e in ev] == [("buy", 100, 2000), ("sell", 0, 0)]


def test_measure_compares_with_the_nearest_trade_of_another_wallet_only():
    ref = Reference(events([row("r", 100, 1), row("a", 101, 2, fee=9000)]))
    m = measure(events([row("a", 101, 2, fee=9000)]), ref)
    assert m["comparable"] == 1 and m["M1_prio"] == 0  # the wallet's own trade at 101 is not its own reference
    assert m["M2"] == 1  # 100 and 101 share a 10-minute bin


def test_measure_refuses_a_reference_too_far_away_and_counts_empty_bins():
    ref = Reference(events([row("r", 0, 1)]))
    m = measure(events([row("a", 200_000, 2)]), ref)
    assert m["comparable"] == 0 and m["M1_tip"] is None and m["M2"] == 0


def test_percentile_is_an_order_statistic():
    assert percentile([3.0, 1.0, 2.0, 4.0], 0.05) == 1.0
    assert percentile([3.0, 1.0, 2.0, 4.0], 0.95) == 4.0
