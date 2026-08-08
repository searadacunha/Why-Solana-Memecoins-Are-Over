"""rpc_client: the single Helius client's failure contract -- the behaviour the
whole hardening rests on ("a failed call raises, never a silent empty result").
Tested with a mocked transport; no network."""
import json
import urllib.error
import urllib.request

import pytest

import rpc_client


class _Resp:
    def __init__(self, payload):
        self._b = json.dumps(payload).encode()

    def read(self):
        return self._b

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


@pytest.fixture(autouse=True)
def _fake_keys(monkeypatch):
    # A key must exist or _next_key() calls settings.require_helius() -> SystemExit.
    monkeypatch.setattr(rpc_client, "_KEYS", ["testkey"])
    rpc_client._COOLDOWN.clear()
    yield


def _patch_response(monkeypatch, payload):
    monkeypatch.setattr(urllib.request, "urlopen",
                        lambda req, timeout=0: _Resp(payload))


def test_rpc_returns_result_on_success(monkeypatch):
    _patch_response(monkeypatch, {"jsonrpc": "2.0", "id": 1, "result": {"ok": 1}})
    assert rpc_client.rpc("getX", []) == {"ok": 1}


def test_sigs_raises_on_null_result(monkeypatch):
    # null result is a FAILURE, not an empty page -- the core contract.
    _patch_response(monkeypatch, {"jsonrpc": "2.0", "id": 1, "result": None})
    with pytest.raises(rpc_client.HeliusError):
        rpc_client.sigs("SomeAddr")


def test_sigs_returns_empty_list_on_genuine_empty(monkeypatch):
    _patch_response(monkeypatch, {"jsonrpc": "2.0", "id": 1, "result": []})
    assert rpc_client.sigs("SomeAddr") == []


def test_enhanced_raises_on_non_list(monkeypatch):
    _patch_response(monkeypatch, {"error": "nope"})     # enhanced expects a list
    with pytest.raises(rpc_client.HeliusError):
        rpc_client.enhanced("SomeAddr")


def test_tolerate_codes_returns_none_but_untolerated_raises(monkeypatch):
    _patch_response(monkeypatch, {"error": {"code": -32009, "message": "slot skipped"}})
    assert rpc_client.rpc("getBlock", [1], tolerate_codes=(-32009,)) is None
    with pytest.raises(rpc_client.HeliusError):
        rpc_client.rpc("getBlock", [1])                 # same error, not tolerated


def test_non_retryable_http_error_raises(monkeypatch):
    def _boom(req, timeout=0):
        raise urllib.error.HTTPError(req.full_url if hasattr(req, "full_url") else "u",
                                     404, "Not Found", {}, None)
    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    with pytest.raises(rpc_client.HeliusError):
        rpc_client.rpc("getX", [])


def test_key_cooldown_rotates_off_a_cooling_key(monkeypatch):
    import time
    monkeypatch.setattr(rpc_client, "_KEYS", ["a", "b"])
    rpc_client._COOLDOWN.clear()
    rpc_client._COOLDOWN["a"] = time.time() + 100       # 'a' is cooling
    # Over several picks, a cooling key must not be handed out while a fresh one exists.
    picks = {rpc_client._available_key() for _ in range(6)}
    assert "b" in picks and "a" not in picks
