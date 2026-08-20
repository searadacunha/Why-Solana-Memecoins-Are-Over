"""settings: how a script decides it may go online, and how a key is kept out
of anything printed or written.

Every one of these runs against a temporary repository root, never the real one:
the working copy carries a .env with a live key, and a test must not read it.
"""
import pytest

import settings


@pytest.fixture(autouse=True)
def isolated_root(tmp_path, monkeypatch):
    """No inherited key, no real .env."""
    monkeypatch.setattr(settings, "ROOT", str(tmp_path))
    for name in settings._ENV_NAMES:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("PUMP_PRIVATE_ROOT", raising=False)
    monkeypatch.delenv("EXPL_LEDGER_ADDR", raising=False)
    return tmp_path


# ------------------------------------------------------------------ keys ----
def test_no_key_anywhere_is_an_empty_list_not_a_crash():
    assert settings.helius_keys() == []


def test_keys_come_from_the_environment_comma_separated():
    import os
    os.environ["HELIUS_API_KEYS"] = " k1 , k2,k3 "
    try:
        assert settings.helius_keys() == ["k1", "k2", "k3"]
    finally:
        del os.environ["HELIUS_API_KEYS"]


def test_every_accepted_variable_name_is_read(monkeypatch):
    monkeypatch.setenv("HELIUS_KEY", "solo")
    assert settings.helius_keys() == ["solo"]


def test_duplicates_are_dropped_and_the_order_is_kept(monkeypatch):
    monkeypatch.setenv("HELIUS_API_KEYS", "a,b,a,c,b")
    assert settings.helius_keys() == ["a", "b", "c"]


def test_dotenv_is_read_and_merged_after_the_environment(isolated_root, monkeypatch):
    (isolated_root / ".env").write_text(
        "# a comment\n"
        "\n"
        "NOT_A_KEY_LINE\n"
        "OTHER=ignored\n"
        'HELIUS_API_KEYS="fromfile1", fromfile2\n'
    )
    monkeypatch.setenv("HELIUS_API_KEYS", "fromenv")
    assert settings.helius_keys() == ["fromenv", "fromfile1", "fromfile2"]


def test_dotenv_absent_is_simply_no_key(isolated_root):
    assert not (isolated_root / ".env").exists()
    assert settings._from_dotenv() == []


def test_require_helius_refuses_instead_of_running_keyless():
    with pytest.raises(SystemExit) as e:
        settings.require_helius()
    assert "HELIUS_API_KEYS" in str(e.value)


# -------------------------------------------------------------- redaction ---
def test_redact_key_strips_every_known_key(monkeypatch):
    """This is what keeps a key out of an error message written into an
    artefact (see 09_bundle_snipe.py, which stores `err:` rows)."""
    monkeypatch.setenv("HELIUS_API_KEYS", "SECRET1,SECRET2")
    text = "GET https://x/?api-key=SECRET1 failed, retry on SECRET2"
    out = settings.redact_key(text)
    assert "SECRET1" not in out and "SECRET2" not in out
    assert out.count("<HELIUS_KEY>") == 2


def test_redact_key_leaves_text_alone_when_there_is_no_key():
    assert settings.redact_key("nothing to hide") == "nothing to hide"


# ----------------------------------------------------------------- inputs ---
def test_private_root_absent_is_none_unless_required():
    assert settings.private_root() is None
    with pytest.raises(SystemExit):
        settings.private_root(required=True)


def test_private_root_pointing_nowhere_is_an_error_not_a_none(monkeypatch, tmp_path):
    monkeypatch.setenv("PUMP_PRIVATE_ROOT", str(tmp_path / "does-not-exist"))
    with pytest.raises(SystemExit) as e:
        settings.private_root()
    assert "missing directory" in str(e.value)


def test_ledger_address_must_be_base58(monkeypatch):
    monkeypatch.setenv("EXPL_LEDGER_ADDR",
                       "6tmiM84AxMzmXzRByq7m1dgNkHtn9wp671e1GMe2ZmWU")
    assert settings.expl_ledger_addr().startswith("6tmiM84")
    monkeypatch.setenv("EXPL_LEDGER_ADDR", "0OIl" * 8)   # hors alphabet base58
    with pytest.raises(SystemExit):
        settings.expl_ledger_addr()


def test_ledger_address_absent_is_none_when_probed_not_required():
    assert settings.expl_ledger_addr(required=False) is None
    with pytest.raises(SystemExit):
        settings.expl_ledger_addr()
