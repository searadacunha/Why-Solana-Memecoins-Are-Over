"""hlib.is_b58_pubkey: the base58 + 32-byte validity check used to tell a real
Solana pubkey from a lookalike string."""
import hlib


def test_accepts_a_real_pump_mint():
    assert hlib.is_b58_pubkey("9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump")
    assert hlib.is_b58_pubkey("G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t")


def test_rejects_wrong_length():
    assert not hlib.is_b58_pubkey("tooShort")
    assert not hlib.is_b58_pubkey("")


def test_rejects_non_base58_characters():
    # 0, O, I, l are not in the base58 alphabet.
    assert not hlib.is_b58_pubkey("0OIl0OIl0OIl0OIl0OIl0OIl0OIl0OIl")
    assert not hlib.is_b58_pubkey("has a space in it 111111111111111111")
