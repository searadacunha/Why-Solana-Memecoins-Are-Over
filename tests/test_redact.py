"""redact: label format, deterministic plain labels, pass-through/recursion of
scrub, and the salted-HMAC scheme used for the KYC deposit address."""
import hashlib
import hmac
import importlib

import redact


def test_is_redacted_recognises_only_the_label_shape():
    assert redact.is_redacted("RDCT-0123456789")
    assert not redact.is_redacted("RDCT-xyz")            # not 10 hex
    assert not redact.is_redacted("9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump")
    assert not redact.is_redacted(42)                    # non-str


def test_plain_label_is_deterministic_sha256_prefix():
    s = "SomeBase58LookingIdentifier1111111111111111"
    assert redact.label_of(s) == "RDCT-" + hashlib.sha256(s.encode()).hexdigest()[:10]


def test_scrub_passes_through_and_recurses():
    obj = {"mint": "unmapped_addr", "list": ["x", {"k": "y"}], "n": 3}
    assert redact.scrub(obj) == obj                      # nothing mapped -> identity
    assert redact.scrub(3) == 3
    assert redact.apply(123) == 123                      # non-str pass-through


def test_hmac_scheme_is_deterministic_under_a_salt(monkeypatch):
    salt_hex = "ab" * 32
    monkeypatch.setenv("REDACT_HMAC_SALT", salt_hex)
    r = importlib.reload(redact)
    try:
        expected = hmac.new(bytes.fromhex(salt_hex), b"any-address",
                            hashlib.sha256).hexdigest()
        assert r.hm("any-address") == expected
    finally:
        monkeypatch.delenv("REDACT_HMAC_SALT", raising=False)
        importlib.reload(redact)                         # restore module state


def test_hm_returns_none_without_a_salt(monkeypatch):
    monkeypatch.delenv("REDACT_HMAC_SALT", raising=False)
    monkeypatch.setattr(redact, "_SALT", None)
    assert redact.hm("anything") is None
