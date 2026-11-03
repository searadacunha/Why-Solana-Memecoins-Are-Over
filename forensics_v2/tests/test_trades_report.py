"""Rules of the private trade report, on invented rows: no private data is needed or read here."""

from forensics_v2.decode import JITO_TIP
from forensics_v2.investigations import trades_report as R
from forensics_v2.investigations.trades_2024 import DEPOSIT, HOT, OCT1

W, W2, OUT = "wallet1", "wallet2", "outsider"
TIP = next(iter(JITO_TIP))


def row(**kw):
    base = {
        "w": W,
        "sig": "s",
        "slot": 1,
        "t": OCT1 + 10,
        "ok": True,
        "fee": 5000,
        "payer": W,
        "signers": [W],
        "native": 0,
        "pre": 0,
        "post": 0,
        "tok": {},
        "moves": [],
        "edges": [],
        "venues": [],
        "programs": [],
    }
    return {**base, **kw}


def test_classes():
    per = {W, W2}
    assert R.classify(row(ok=False), per) == "failed"
    assert R.classify(row(tok={"m": 5}, native=-10), per) == "buy"
    assert R.classify(row(tok={"m": -5}, native=10), per) == "sell"
    assert R.classify(row(tok={"m": -5}, native=-1), per) == "token_other"
    assert R.classify(row(moves=[{"k": "sol_transfer", "src": W, "dst": TIP, "n": 9}], native=-9), per) == "tip"
    assert R.classify(row(edges=[[W, DEPOSIT, 9, "instruction"]], native=-9), per) == "to_deposit"
    assert R.classify(row(edges=[[HOT, W, 9, "instruction"]], native=9), per) == "from_hot"
    assert R.classify(row(edges=[[W, W2, 9, "instruction"]], native=-9), per) == "internal"
    assert R.classify(row(edges=[[OUT, W, 9, "instruction"]], native=9), per) == "external_in"
    assert R.classify(row(native=0), per) == "no_transfer"


def test_capital_closes_and_splits_recipients():
    per = {W, W2}
    rows = [
        row(sig="a", slot=1, native=100, pre=0, post=100, edges=[[HOT, W, 100, "instruction"]]),
        row(sig="b", slot=2, native=-60, pre=100, post=40, tok={"m": 5}),
        row(sig="c", slot=3, native=-30, pre=40, post=10, edges=[[W, W2, 10, "instruction"], [W, OUT, 20, "instruction"]]),
    ]
    c = R.capital(rows, per)["oct_dec"]
    assert c["open"] == 0 and c["close"] == 10
    assert (
        c["flows"]["internal"] == -10
        and c["flows"]["external_out"] == -20
        and c["flows"]["from_hot"] == 100
        and c["flows"]["buy"] == -60
    )


def test_a_missing_transaction_breaks_the_chain():
    ok = [row(sig="a", slot=1, pre=0, post=100), row(sig="b", slot=2, pre=100, post=40)]
    assert R.continuity(ok)["breaks"] == []
    gap = [row(sig="a", slot=1, pre=0, post=100), row(sig="b", slot=2, pre=70, post=40)]
    assert R.continuity(gap)["breaks"][0]["gap_lamports"] == -30


def test_tip_attached_to_the_trade_of_its_slot():
    rows = [
        row(sig="t", slot=7, tok={"m": 5}, native=-50),
        row(sig="tip", slot=7, native=-1005, fee=5, moves=[{"k": "sol_transfer", "src": W, "dst": TIP, "n": 1000}]),
    ]
    for r in rows:
        r["class"] = R.classify(r, {W})
    by_sig, unattached = R.tips_of_legs(rows)
    assert by_sig == {"t": 1000} and unattached == 0


def test_attribution_needs_a_card_and_propagates_by_direct_links_only():
    rows = [
        row(w="a", sig="1", edges=[["a", DEPOSIT, 5, "instruction"]]),
        row(w="b", sig="2", slot=2, edges=[["b", DEPOSIT, 5_000_000, "instruction"], ["b", "a", 20_000_000, "instruction"]]),
        row(w="c", sig="3", slot=3, edges=[["c", DEPOSIT, 5_000_000, "instruction"]]),
        row(w="aXXX", sig="4", slot=4, edges=[["aXXX", DEPOSIT, 1, "instruction"]]),
    ]
    cards = [{"card": "K", "matches": [{"wallet": "a"}]}]
    lv = {x["wallet"]: x for x in R.attribution(rows, cards, {"a", "b", "c", "aXXX"}, set())}
    assert lv["a"]["level"] == "CERTAIN" and lv["b"]["level"] == "PROBABLE" and lv["c"]["level"] == "NOT_ESTABLISHED"


def test_held():
    assert R.held("12d 13h 42m") == 1086120 and R.held("10m 35s") == 635
