"""The volume guard, the store's replay safety, and the books it re-checks."""
import os

import pytest

from forensics_v2 import decode as D
from forensics_v2 import storage as S

from .test_decode import A, B, SYS, mk, sys_transfer


def test_root_needs_a_marker(tmp_path, monkeypatch):
    monkeypatch.setenv("FORENSICS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(S, "MIN_FREE_BYTES", 0)
    with pytest.raises(S.StorageError):
        S.data_root(allow_internal=True)
    (tmp_path / S.MARKER).write_text("")
    assert S.data_root(allow_internal=True) == tmp_path


def test_nearly_full_volume_refuses(tmp_path, monkeypatch):
    monkeypatch.setenv("FORENSICS_DATA_ROOT", str(tmp_path))
    (tmp_path / S.MARKER).write_text("")
    monkeypatch.setattr(S, "MIN_FREE_BYTES", 10**18)
    monkeypatch.setattr(S, "INTERNAL_MIN_FREE_BYTES", 10**18)  # whichever disk this test runs on
    with pytest.raises(S.StorageError):
        S.data_root(allow_internal=True)


def test_disconnected_volume_refuses_rather_than_writing_elsewhere(tmp_path, monkeypatch):
    monkeypatch.setenv("FORENSICS_DATA_ROOT", str(tmp_path / "not_mounted"))
    with pytest.raises(S.StorageError):
        S.sub("rpc_raw", allow_internal=True)
    assert not (tmp_path / "not_mounted").exists()


def test_internal_disk_refused_by_default(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / S.MARKER).write_text("")
    monkeypatch.setenv("FORENSICS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(S.Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(S, "CONFIG", tmp_path / "absent.json")
    assert os.stat(tmp_path).st_dev == os.stat(home).st_dev
    with pytest.raises(S.StorageError):
        S.data_root()


def test_internal_disk_needs_a_written_quota_and_the_floor(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (tmp_path / S.MARKER).write_text("")
    cfg = tmp_path / "c.json"
    cfg.write_text('{"internal_quota_bytes": 1000}')
    monkeypatch.setenv("FORENSICS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(S.Path, "home", classmethod(lambda cls: home))
    monkeypatch.setattr(S, "CONFIG", cfg)
    monkeypatch.setattr(S, "INTERNAL_MIN_FREE_BYTES", 0)
    assert S.data_root() == tmp_path and S.internal_quota() == 1000
    monkeypatch.setattr(S, "INTERNAL_MIN_FREE_BYTES", 10**18)
    with pytest.raises(S.StorageError):
        S.data_root()


def test_missing_config_is_explicit(monkeypatch, tmp_path):
    monkeypatch.delenv("FORENSICS_DATA_ROOT", raising=False)
    monkeypatch.setattr(S, "CONFIG", tmp_path / "absent.json")
    with pytest.raises(S.StorageError):
        S.data_root()


def _tx(sig="SIG"):
    k = [A, B, SYS]
    t = mk(k, [100_000, 0, 1], [100_000 - 5000 - 700, 700, 1], [sys_transfer(k, A, B, 700)])
    t["transaction"]["signatures"] = [sig]
    return D.decode(t)


def test_replay_books_nothing_twice():
    st = pytest.importorskip("forensics_v2.store")
    con = st.connect()
    assert st.ingest(con, [_tx(), _tx("OTHER")]) == 2
    first = st.counts(con)
    assert st.ingest(con, [_tx(), _tx("OTHER")]) == 0
    assert st.counts(con) == first and first["transactions"] == 2 and first["funding_edges"] == 2
    assert set(st.TABLES) >= {"coverage", "rpc_provenance", "wallet_clusters", "realized_pnl"}


def test_books_balance_and_a_broken_row_is_caught():
    st = pytest.importorskip("forensics_v2.store")
    con = st.connect()
    st.ingest(con, [_tx()])
    r = st.reconcile(con)
    assert r["tx_not_conserved"] == 0 and r["tx_owner_sum_plus_fee_nonzero"] == 0 and r["edges_on_unknown_tx"] == 0
    con.execute("UPDATE balance_movements SET native = native + 1 WHERE owner = ?", [B])
    assert st.reconcile(con)["tx_owner_sum_plus_fee_nonzero"] == 1


def test_amounts_keep_every_lamport():
    st = pytest.importorskip("forensics_v2.store")
    con = st.connect()
    k = [A, B, SYS]
    big = 2**63 + 12345
    d = D.decode(mk(k, [big * 2, 0, 1], [big * 2 - 5000 - big, big, 1], [sys_transfer(k, A, B, big)]))
    st.ingest(con, [d])
    assert con.execute("SELECT lamports FROM funding_edges").fetchone()[0] == big
