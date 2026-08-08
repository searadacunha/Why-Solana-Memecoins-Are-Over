"""check_no_secrets: the leak-pattern routing -- a planted key/path is a
finding, an allowlisted handle is routed to ALLOWED, and a low-entropy 32-char
token (the Solana System Program id) is not mistaken for a key."""
import importlib

gate = importlib.import_module("check_no_secrets")


def _run(text, allow=()):
    findings: list = []
    gate.scan_blob("f", text, "", findings, list(allow))
    return findings


def test_planted_key_and_path_are_findings():
    f = _run("k = 0123456789abcdef0123456789abcdef\npath = /Users/someone/secret")  # noqa: leakscan
    kinds = " ".join(k for k, *_ in f)
    assert "api key (32 hex)" in kinds
    assert "local path" in kinds


def test_system_program_id_is_not_a_key():
    # 32 identical chars (<=2 distinct) is the all-ones base58 System Program id.
    assert _run("owner = 11111111111111111111111111111111") == []


def test_allowlisted_reflink_is_routed_to_allowed_not_leak():
    line = "ocr = https://t.me/agamemnon_trojanbot?start=r-teamdacunha-abc"
    f = _run(line, allow=["teamdacunha"])
    assert f, "the reflink should still be detected"
    assert all(k.startswith("ALLOWED") for k, *_ in f), "and marked ALLOWED, not a leak"


def test_real_secret_not_allowed_by_a_nearby_handle():
    # An allowed word on the line must NOT whitelist a genuine key fragment.
    line = "teamdacunha key=0123456789abcdef0123456789abcdef"  # noqa: leakscan
    f = _run(line, allow=["teamdacunha"])
    assert any(k == "api key (32 hex)" and not k.startswith("ALLOWED") for k, *_ in f)


def test_read_list_ignores_comments_and_blanks(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("# comment\n\nTeamDaCunha\n")
    assert gate.read_list(str(p)) == ["teamdacunha"]   # lowercased, comment/blank dropped
