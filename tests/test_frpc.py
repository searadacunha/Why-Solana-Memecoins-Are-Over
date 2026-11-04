"""The paced collector must reject malformed replies, just like the core client."""
import importlib
import io
import json
from pathlib import Path

import pytest


@pytest.fixture
def client(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(root / "post_detection_forensics" / "code"))
    module = importlib.import_module("frpc")
    monkeypatch.setattr(module, "_take", lambda: "synthetic_key")
    return module


def reply(client, monkeypatch, payload):
    monkeypatch.setattr(client.urllib.request, "urlopen",
                        lambda *args, **kwargs: io.BytesIO(json.dumps(payload).encode()))


@pytest.mark.parametrize("payload", [None, [], {}, {"jsonrpc": "2.0", "id": 1}, {"error": None}])
def test_missing_result_is_not_an_unavailable_transaction(client, monkeypatch, payload):
    reply(client, monkeypatch, payload)
    with pytest.raises(client.HeliusError):
        client.rpc("getTransaction", ["synthetic"])


@pytest.mark.parametrize("result", [None, {}, False, 0, ""])
def test_malformed_signature_page_is_not_a_complete_empty_history(client, monkeypatch, result):
    reply(client, monkeypatch, {"result": result})
    with pytest.raises(client.HeliusError):
        client.rpc("getSignaturesForAddress", ["synthetic"])
    with pytest.raises(client.HeliusError):
        client.sigs("synthetic")


def test_explicit_empty_signature_page_is_valid(client, monkeypatch):
    reply(client, monkeypatch, {"result": []})
    assert client.sigs("synthetic") == []


def test_explicit_null_transaction_remains_valid(client, monkeypatch):
    reply(client, monkeypatch, {"result": None})
    assert client.rpc("getTransaction", ["synthetic"]) is None


def test_only_named_rpc_error_codes_can_be_tolerated(client, monkeypatch):
    reply(client, monkeypatch, {"error": {"code": -32009, "message": "skipped slot"}})
    assert client.rpc("getBlock", [1], tolerate=(-32009,)) is None
    with pytest.raises(client.HeliusError):
        client.rpc("getBlock", [1])
