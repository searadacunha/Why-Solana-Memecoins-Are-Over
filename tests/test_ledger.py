"""expl_ledger.wallet_view: the balance-delta reading that turns one
transaction into (direction, amount, counterparty) for the deposit ledger.
No network -- it operates on a decoded transaction dict."""
import expl_ledger


def _tx(pre, post, keys, err=None, blocktime=1_727_800_000):
    return {"meta": {"err": err, "preBalances": pre, "postBalances": post},
            "transaction": {"message": {"accountKeys": keys}},
            "blockTime": blocktime}


def test_incoming_transfer_and_sender_heuristic():
    # ADDR gains 10 lamports; OTHER loses 10 -> incoming, sender = OTHER.
    tx = _tx([100, 50], [110, 40], ["ADDR", "OTHER"])
    v = expl_ledger.wallet_view(tx, "ADDR", "sig")
    assert v is not None
    assert v["delta"] > 0
    assert v["sender"] == "OTHER"
    assert v["recipient"] is None          # only set for outgoing


def test_outgoing_sweep_sets_recipient_not_sender():
    tx = _tx([100, 50], [40, 110], ["ADDR", "DEST"])
    v = expl_ledger.wallet_view(tx, "ADDR", "sig")
    assert v["delta"] < 0
    assert v["recipient"] == "DEST"
    assert v["sender"] is None


def test_failed_transaction_is_ignored():
    tx = _tx([100, 50], [110, 40], ["ADDR", "OTHER"], err={"InstructionError": []})
    assert expl_ledger.wallet_view(tx, "ADDR", "sig") is None


def test_address_absent_from_tx_returns_none():
    tx = _tx([100, 50], [110, 40], ["X", "Y"])
    assert expl_ledger.wallet_view(tx, "ADDR", "sig") is None


def test_jsonparsed_account_keys_as_dicts():
    # accountKeys can be {"pubkey": ...} objects; wallet_view must handle both.
    tx = _tx([100, 50], [110, 40], [{"pubkey": "ADDR"}, {"pubkey": "OTHER"}])
    v = expl_ledger.wallet_view(tx, "ADDR", "sig")
    assert v is not None and v["delta"] > 0
