"""The client against scripted replies: every failure must stay a failure, never an empty history."""
import io
import json
import urllib.error

import pytest

from forensics_v2 import keys as K
from forensics_v2 import rpc as R

KEY = "-".join(("1" * 8, "2" * 4, "3" * 4, "4" * 4, "5" * 12))  # synthetic, assembled so no key shape is in the file
KEY2 = "-".join(("a" * 8, "2" * 4, "3" * 4, "4" * 4, "5" * 12))
W = "W" * 44


class Reply:
    def __init__(self, obj):
        self.buf = io.BytesIO(json.dumps(obj).encode())

    def __enter__(self):
        return self.buf

    def __exit__(self, *a):
        return False


def opener(script):
    calls = []

    def _open(req, timeout=None):
        calls.append(json.loads(req.data))
        x = script.pop(0)
        if isinstance(x, Exception):
            raise x
        return Reply(x)

    _open.calls = calls
    return _open


def http(code, body=b""):
    return urllib.error.HTTPError("https://x/?api-key=" + KEY, code, "e", {}, io.BytesIO(body))


def ok(result):
    return {"jsonrpc": "2.0", "id": 1, "result": result}


def sigs(*names):
    return [{"signature": n, "blockTime": 1000 - i, "slot": 1} for i, n in enumerate(names)]


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    monkeypatch.setattr(R.time, "sleep", lambda s: None)
    monkeypatch.setattr(K.time, "sleep", lambda s: None)


def client(tmp_path, script, ceiling=1000, keys=(KEY,)):
    pool = K.KeyPool(list(keys), rps_per_key=1e6, rps_total=1e6)
    return R.RpcClient(pool, tmp_path, R.Budget(tmp_path / "credits", ceiling), opener=opener(script))


def test_short_page_is_not_genesis_until_confirmed(tmp_path):
    c = client(tmp_path, [ok(sigs("a", "b")), ok([]), ok([]), ok([])])
    w = c.walk(W)
    assert [s["signature"] for s in w.signatures] == ["a", "b"] and w.complete and w.stop == "genesis"
    assert c.net_calls == 4


def test_empty_answer_in_mid_history_does_not_end_the_walk(tmp_path):
    c = client(tmp_path, [ok(sigs("a")), ok([]), ok(sigs("b")), ok([]), ok([]), ok([])])
    w = c.walk(W)
    assert [s["signature"] for s in w.signatures] == ["a", "b"] and w.stop == "genesis"


def test_page_cap_is_incomplete_and_resumes_without_refetching(tmp_path):
    c = client(tmp_path, [ok(sigs("a")), ok(sigs("b"))])
    w = c.walk(W, max_pages=2)
    assert not w.complete and w.stop == "max_pages" and len(w.signatures) == 2
    c2 = client(tmp_path, [ok(sigs("c")), ok([]), ok([]), ok([])])
    w2 = c2.walk(W, max_pages=5)
    assert [s["signature"] for s in w2.signatures] == ["a", "b", "c"] and w2.complete
    assert c2._open.calls[0]["params"][1]["before"] == "b"
    c3 = client(tmp_path, [])
    assert c3.walk(W).complete and c3.net_calls == 0  # finished walks replay from disk


def test_outage_raises_instead_of_returning_nothing(tmp_path):
    c = client(tmp_path, [urllib.error.URLError("down")] * 8)
    with pytest.raises(R.RpcError):
        c.walk(W)


def test_rpc_error_object_raises(tmp_path):
    c = client(tmp_path, [{"error": {"code": -32602, "message": "bad"}}])
    with pytest.raises(R.RpcError):
        c.page(W)


def test_non_list_page_raises(tmp_path):
    c = client(tmp_path, [ok({"oops": 1})])
    with pytest.raises(R.RpcError):
        c.page(W)


def test_429_cools_and_retries(tmp_path):
    c = client(tmp_path, [http(429, b"slow down"), ok([])])
    assert c.page(W) == [] and c.net_calls == 2


def test_spent_key_is_retired_and_the_next_one_serves(tmp_path):
    c = client(tmp_path, [http(429, b'{"message":"max usage reached"}'), ok([])], keys=(KEY, KEY2))
    assert c.page(W) == []
    assert sum(1 for s in c.pool.status() if s["exhausted"]) == 1


def test_all_keys_spent_stops(tmp_path):
    c = client(tmp_path, [http(429, b"max usage reached")])
    with pytest.raises(RuntimeError):
        c.page(W)


def test_budget_stops_before_spending(tmp_path):
    c = client(tmp_path, [ok([]), ok([])], ceiling=1)
    c.page(W)
    with pytest.raises(R.BudgetExhausted):
        c.page(W)
    assert c.net_calls == 1 and c.budget.used() == 1


def test_run_limit_ignores_what_other_processes_spend(tmp_path):
    other = R.Budget(tmp_path / "credits", 100, run_limit=50)
    mine = R.Budget(tmp_path / "credits", 100, run_limit=2)
    other.charge(40)
    mine.charge(2)
    with pytest.raises(R.BudgetExhausted):
        mine.charge(1)
    assert other.used() == 42
    with pytest.raises(R.BudgetExhausted):
        R.Budget(tmp_path / "credits", 42).charge(1)  # the shared ceiling still binds everyone


def test_null_transaction_is_not_found_and_never_cached(tmp_path):
    c = client(tmp_path, [ok(None), ok(None), ok(None)])
    with pytest.raises(R.TxNotFound):
        c.tx("sig")
    assert c._tx_cached("sig") is None


def test_transaction_cached_once(tmp_path):
    tx = {"slot": 1, "meta": {}, "transaction": {"signatures": ["sig"]}}
    c = client(tmp_path, [ok(tx)])
    assert c.tx("sig") == tx and c.tx("sig") == tx and c.net_calls == 1
    assert client(tmp_path, []).tx("sig") == tx


def test_read_cache_is_used_and_not_written(tmp_path):
    ro = tmp_path / "ro"
    ro.mkdir()
    (ro / "sig.json").write_text(json.dumps({"result": {"slot": 7}}))
    c = R.RpcClient(K.KeyPool([KEY]), tmp_path, R.Budget(tmp_path / "c", 0), [ro], opener=opener([]))
    assert c.tx("sig") == {"slot": 7} and c.net_calls == 0
    assert [p.name for p in ro.iterdir()] == ["sig.json"]


def test_cache_over_quota_moves_to_the_external_volume_without_stopping(tmp_path):
    hot, cold = tmp_path / "hot", tmp_path / "cold"
    hot.mkdir()
    cold.mkdir()
    (cold / R.storage.MARKER).write_text("")
    tx = {"slot": 1, "meta": {}, "transaction": {"signatures": ["s"]}}
    pool = K.KeyPool([KEY], rps_per_key=1e6, rps_total=1e6)
    c = R.RpcClient(pool, hot, R.Budget(hot / "credits", 100), opener=opener([ok(tx), ok(tx)]), legacy_root=cold, max_db_bytes=1)
    c.tx("a")  # first row creates the hot file, already over a 1-byte quota
    c.tx("b")
    assert (cold / "rpc_raw" / "tx.sqlite").exists()
    assert c._tx_cached("a") == tx and c._tx_cached("b") == tx


def test_cache_over_quota_with_the_volume_gone_refuses_rather_than_filling_the_disk(tmp_path):
    hot, cold = tmp_path / "hot", tmp_path / "unmounted"
    hot.mkdir()
    tx = {"slot": 1, "meta": {}, "transaction": {"signatures": ["s"]}}
    pool = K.KeyPool([KEY], rps_per_key=1e6, rps_total=1e6)
    c = R.RpcClient(pool, hot, R.Budget(hot / "credits", 100), opener=opener([ok(tx)]), legacy_root=cold, max_db_bytes=1)
    with pytest.raises(R.BudgetExhausted):
        c.tx("a")  # an empty database file already exceeds a 1-byte quota
    assert not cold.exists()


def test_older_cache_file_moves_into_the_database_on_first_read(tmp_path):
    tx = {"slot": 9}
    c = client(tmp_path, [])
    p = c._tx_path("old")
    p.parent.mkdir(parents=True)
    with R.gzip.open(p, "wt") as f:
        json.dump(tx, f)
    assert c.tx("old") == tx
    p.unlink()
    assert c.tx("old") == tx and c.net_calls == 0


def test_key_never_reaches_an_error_or_the_log(tmp_path):
    c = client(tmp_path, [http(403, ("invalid key " + KEY).encode())])
    with pytest.raises(R.RpcError) as e:
        c.page(W)
    assert KEY not in str(e.value)
    assert KEY not in (tmp_path / "rpc_raw" / "provenance.jsonl").read_text()
    assert KEY not in repr(c.pool) and KEY not in repr(c.pool._keys[0])


def _gtfa_item(sig):
    return {"slot": 5, "blockTime": 9, "transactionIndex": 3, "meta": {}, "transaction": {"signatures": [sig]}}


def test_history_pages_resume_from_token_and_charge_ten(tmp_path):
    c = client(tmp_path, [ok({"data": [_gtfa_item("a")], "paginationToken": "5:3"})])
    raw, w = c.history_txs(W, max_pages=1)
    assert not w.complete and len(raw) == 1 and c.budget.used() == 10
    c2 = client(tmp_path, [ok({"data": [_gtfa_item("b")], "paginationToken": None})])
    raw2, w2 = c2.history_txs(W, max_pages=5)
    assert [t["transaction"]["signatures"][0] for t in raw2] == ["a", "b"] and w2.complete and w2.stop == "genesis"
    assert c2._open.calls[0]["params"][1]["paginationToken"] == "5:3"
    assert client(tmp_path, []).history_txs(W)[1].complete


def test_history_with_a_time_window_does_not_claim_genesis(tmp_path):
    c = client(tmp_path, [ok({"data": [], "paginationToken": None})])
    _, w = c.history_txs(W, t_from=100)
    assert w.complete and w.stop == "window"


def test_history_malformed_reply_raises(tmp_path):
    c = client(tmp_path, [ok({"nope": []})])
    with pytest.raises(R.RpcError):
        c.history_txs(W)


def test_keys_are_read_only_from_helius_lines(tmp_path):
    f = tmp_path / "e"
    f.write_text("OTHER_KEY=%s\nHELIUS_API_KEYS=%s,%s\n# HELIUS_KEY=%s\n" % (KEY2, KEY, KEY, KEY2))
    assert K.keys_in_file(str(f), bare=False) == [KEY, KEY]
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"sources": [{"path": str(f)}], "pool_fingerprints": [K.fingerprint(KEY)]}))
    assert [s["fp"] for s in K.KeyPool.from_config(cfg).status()] == [K.fingerprint(KEY)]
