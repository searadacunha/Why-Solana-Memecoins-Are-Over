"""Decoder on hand-built transactions: each case is a way money movement gets misread."""
import json
import struct
from pathlib import Path

from forensics_v2 import decode as D
from forensics_v2.trace import History, sol_flows
from forensics_v2.rpc import SigWalk

FIX = Path(__file__).with_name("fixtures")
SYS, TOK = D.SYSTEM, D.TOKEN
A, B, C, E, X = "A" * 32, "B" * 32, "C" * 32, "E" * 32, "X" * 32
MINT = "M" * 32
WS = D.WSOL


def ix(keys, prog, accounts, data=b""):
    return {"programIdIndex": keys.index(prog), "accounts": [keys.index(a) for a in accounts], "data": D.b58encode(data)}


def sys_transfer(keys, src, dst, lamports):
    return ix(keys, SYS, [src, dst], struct.pack("<IQ", 2, lamports))


def spl_transfer(keys, src, dst, auth, amount):
    return ix(keys, TOK, [src, dst, auth], bytes([3]) + struct.pack("<Q", amount))


def tb(keys, acct, mint, owner, amount):
    return {"accountIndex": keys.index(acct), "mint": mint, "owner": owner, "programId": TOK,
            "uiTokenAmount": {"amount": str(amount), "decimals": 6}}


def mk(keys, pre, post, instructions, inner=None, pre_tok=None, post_tok=None, fee=5000, err=None, signers=1, loaded=None):
    return {"slot": 100, "blockTime": 1700000000,
            "transaction": {"signatures": ["SIG"], "message": {
                "accountKeys": keys[:len(keys) - sum(len(v) for v in (loaded or {}).values())],
                "instructions": instructions, "header": {"numRequiredSignatures": signers}}},
            "meta": {"err": err, "fee": fee, "preBalances": pre, "postBalances": post, "preTokenBalances": pre_tok or [],
                     "postTokenBalances": post_tok or [], "logMessages": [], "loadedAddresses": loaded or {},
                     "innerInstructions": [{"index": i, "instructions": v} for i, v in (inner or {}).items()]}}


def test_base58_round_trip():
    for raw in (b"", b"\0\0abc", bytes(range(32))):
        assert D.b58decode(D.b58encode(raw)) == raw
    assert D.b58encode(bytes(32)) == SYS


def test_plain_transfer_is_verified_and_fee_is_not_a_payment():
    k = [A, B, SYS]
    d = D.decode(mk(k, [100_000, 0, 1], [100_000 - 5000 - 700, 700, 1], [sys_transfer(k, A, B, 700)]))
    assert d.conserved and not d.residual
    assert [(e.src, e.dst, e.lamports, e.evidence, e.path) for e in d.edges] == [(A, B, 700, D.ONCHAIN_VERIFIED, "0")]
    assert d.owners[A].sol == -5700 and not d.unresolved_sol


def test_fee_payer_other_than_sender():
    k = [C, A, B, SYS]
    d = D.decode(mk(k, [10_000, 900, 0, 1], [5000, 200, 700, 1], [sys_transfer(k, A, B, 700)], signers=2))
    assert [(e.src, e.dst, e.lamports) for e in d.edges] == [(A, B, 700)]
    assert d.signers == [C, A] and d.fee_payer == C


def test_failed_transaction_moves_only_its_fee():
    k = [A, B, SYS]
    d = D.decode(mk(k, [100_000, 0, 1], [95_000, 0, 1], [sys_transfer(k, A, B, 700)], err={"InstructionError": [0, "x"]}))
    assert not d.ok and d.transfers == [] and d.edges == [] and not d.residual and d.conserved


def test_sweep_through_disposable_address_names_the_real_receiver():
    # A -> X (disposable), X wraps into a WSOL account W, W pays C's WSOL account Y, Y closes to C.
    W, Y, RENT = "W" * 32, "Y" * 32, 2000
    k = [A, X, W, Y, C, SYS, TOK, WS]
    amount = 1_000_000
    instrs = [
        sys_transfer(k, A, X, amount + RENT),
        ix(k, SYS, [X, W], struct.pack("<IQQ", 0, amount + RENT, 165) + bytes(32)),
        ix(k, TOK, [W, WS, X, X], bytes([1])),
        spl_transfer(k, W, Y, X, amount),
        ix(k, TOK, [W, X, X], bytes([9])),
        ix(k, SYS, [X, A], struct.pack("<IQ", 2, RENT)),
        ix(k, TOK, [Y, C, C], bytes([9])),
    ]
    pre = [10_000_000, 0, 0, RENT, 0, 1, 1, 1]
    post = [10_000_000 - amount - 5000, 0, 0, 0, amount + RENT, 1, 1, 1]
    d = D.decode(mk(k, pre, post, instrs, pre_tok=[tb(k, Y, WS, C, 0)]))
    assert d.conserved and not d.residual, d.residual
    assert not d.unresolved_sol
    total = {(e.src, e.dst): e.lamports for e in d.edges}
    assert total == {(A, C): amount}, total
    assert all(e.dst != X for e in d.edges)  # the disposable address received nothing in the end
    # C's closed WSOL account gave its rent back: native gains it, rent loses it, the net is the amount.
    assert d.owners[C].sol == amount and d.owners[C].rent == -RENT and d.owners[C].native == amount + RENT


def test_ata_close_refunds_rent_to_its_owner_and_books_the_tokens():
    T = "T" * 32
    k = [A, T, SYS, TOK]
    d = D.decode(mk(k, [100_000, 2000, 1, 1], [97_000, 0, 1, 1], [ix(k, TOK, [T, A, A], bytes([9]))],
                    pre_tok=[tb(k, T, MINT, A, 0)]))
    close = [t for t in d.transfers if t.kind == "close_refund"]
    assert close[0].amount == 2000 and close[0].dst == A and d.conserved and not d.residual
    # Rent moved from A's token account to A itself: only the fee leaves A.
    assert d.owners[A].native == -3000 and d.owners[A].rent == -2000 and d.owners[A].sol == -5000


def test_many_to_many_without_instructions_stays_unresolved():
    # A program moves lamports it owns: two payers, two receivers, no instruction names the pairs.
    P = "P" * 32
    k = [A, B, C, E, X, P]
    pre, post = [1000_000, 1000, 1000, 1000, 1000, 1], [1000_000 - 5000, 600, 1300, 900, 1200, 1]
    d = D.decode(mk(k, pre, post, [ix(k, P, [A])]))
    assert sum(d.residual.values()) == 0 and d.residual
    assert d.edges == [], d.edges  # nobody is named as anybody's payer
    assert d.unresolved_sol == {B: -400, C: 300, E: -100, X: 200}


def test_program_direct_payout_with_one_payer_is_inference_not_verified():
    CURVE = "Q" * 32
    P = "P" * 32
    k = [A, CURVE, P]
    d = D.decode(mk(k, [100_000, 9000, 1], [100_000 - 5000 + 700, 8300, 1], [ix(k, P, [A, CURVE])]))
    assert [(e.src, e.dst, e.lamports, e.evidence) for e in d.edges] == [(CURVE, A, 700, D.STRONG_TECHNICAL_INFERENCE)]
    assert d.residual == {A: 700, CURVE: -700}


def test_jito_tip_is_a_fee_not_a_counterparty():
    tip = sorted(D.JITO_TIP)[0]
    k = [A, B, tip, SYS]
    d = D.decode(mk(k, [100_000, 0, 5, 1], [100_000 - 5000 - 700 - 50, 700, 55, 1],
                    [sys_transfer(k, A, B, 700), sys_transfer(k, A, tip, 50)]))
    assert [(e.src, e.dst) for e in d.edges] == [(A, B)] and not d.unresolved_sol


def test_lookup_table_keys_index_the_balances():
    k = [A, SYS, B]
    d = D.decode(mk(k, [100_000, 1, 0], [100_000 - 5000 - 700, 1, 700], [sys_transfer(k, A, B, 700)],
                    loaded={"writable": [B], "readonly": []}))
    assert d.keys == k and d.lamport_delta[B] == 700 and d.edges[0].dst == B


def test_key_count_mismatch_raises_instead_of_misbooking():
    k = [A, B, SYS]
    tx = mk(k, [1, 2], [1, 2], [])
    try:
        D.decode(tx)
    except ValueError:
        return
    raise AssertionError("mismatch accepted")


def test_transfer_fee_mint_shows_up_as_token_residual_not_silently():
    S, R, AUTH = "S" * 32, "R" * 32, A
    k = [AUTH, S, R, TOK, MINT]
    data = bytes([12]) + struct.pack("<QB", 1000, 6)
    d = D.decode(mk(k, [100_000, 2000, 2000, 1, 1], [95_000, 2000, 2000, 1, 1], [ix(k, TOK, [S, MINT, R, AUTH], data)],
                    pre_tok=[tb(k, S, MINT, AUTH, 1000), tb(k, R, MINT, B, 0)],
                    post_tok=[tb(k, S, MINT, AUTH, 0), tb(k, R, MINT, B, 990)]))
    assert d.token_residual == {R: -10} and d.owners[B].tokens[MINT] == 990


def test_trade_counterparty_is_not_a_destination():
    CURVE, T, TC = "Q" * 32, "T" * 32, "U" * 32
    k = [A, CURVE, T, TC, SYS, TOK]
    pay = sys_transfer(k, A, CURVE, 400_000)
    d = D.decode(mk(k, [1_000_000, 9, 2000, 2000, 1, 1], [1_000_000 - 5000 - 400_000, 400_009, 2000, 2000, 1, 1],
                    [pay, spl_transfer(k, TC, T, CURVE, 777)],
                    pre_tok=[tb(k, T, MINT, A, 0), tb(k, TC, MINT, CURVE, 1000)],
                    post_tok=[tb(k, T, MINT, A, 777), tb(k, TC, MINT, CURVE, 223)]))
    assert D.trade_counterparties(d, A) == {CURVE}
    h = History(A, SigWalk(A, [], True, "genesis", 1), [d])
    flows, _ = sol_flows(h)
    assert flows == []  # the edge exists on the transaction, and it is a trade, not funding
    assert any(e.dst == CURVE for e in d.edges)


def test_real_transactions_from_the_public_case():
    fx = json.loads((FIX / "h2w6_public_txs.json").read_text())
    pay = D.decode(fx["g2y_credit"])
    assert pay.conserved and fx["wallet"] in pay.owners
    e = [x for x in pay.edges if x.dst == fx["wallet"]]
    assert e[0].lamports == 2_976_815_600 and e[0].evidence == D.ONCHAIN_VERIFIED and e[0].src == fx["g2y"]
    buy = D.decode(fx["curve_buy"])
    ev = [x for x in buy.trade_events if x["user"] == fx["wallet"]][0]
    assert buy.conserved and ev["buy"] and ev["tok"] == 2_035_147_973_459 and ev["mint"] == fx["mint"]
    assert buy.owners[fx["wallet"]].tokens[fx["mint"]] == ev["tok"]
    sell = D.decode(fx["raydium_sell"])
    assert sell.conserved and sell.venues == ["raydium_v4"]
    assert sell.owners[fx["wallet"]].tokens[fx["mint"]] == -ev["tok"]
    sweep = D.decode(fx["sweep"])
    assert [(x.dst, x.evidence) for x in sweep.edges if x.src == fx["wallet"]] == [(fx["common_wallet"], D.ONCHAIN_VERIFIED)]


def test_node_parser_agrees_with_ours_on_the_stored_pairs():
    fx = json.loads((FIX / "h2w6_public_txs.json").read_text())
    for name, parsed in fx["parsed"].items():
        assert D.compare_decoders(fx[name], parsed) == [], name
