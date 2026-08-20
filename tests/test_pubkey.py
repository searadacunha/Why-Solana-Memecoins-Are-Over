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


def test_rejects_a_44_char_string_that_overflows_32_bytes():
    """The length window alone is not enough: 44 base58 characters can encode
    more than 2**256, and such a string is not a pubkey. This is the bound the
    check actually turns on."""
    # "zzz..." (44 chars) is the largest 44-character base58 value.
    assert not hlib.is_b58_pubkey("z" * 44)
    # The smallest 44-character string, on the other hand, decodes well below it.
    assert hlib.is_b58_pubkey("1" * 44)


def test_boundary_at_two_to_the_256():
    """Exactly 2**256 - 1 is the last accepted value, 2**256 the first rejected."""
    B58 = hlib.B58

    def enc(n: int) -> str:
        s = ""
        while n:
            n, r = divmod(n, 58)
            s = B58[r] + s
        return s.rjust(32, B58[0])

    assert hlib.is_b58_pubkey(enc(2 ** 256 - 1))
    assert not hlib.is_b58_pubkey(enc(2 ** 256))
