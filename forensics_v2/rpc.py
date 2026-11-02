"""Bounded, cached, loud Solana JSON-RPC client.

- A call returns its result or raises. An outage is never an empty history.
- Transactions are immutable, so they are cached forever, and existing caches are read first.
- A signature walk says how it ended: an interrupted or capped walk is `complete=False`, and resumes.
- A global credit ceiling, shared by all processes, stops the work instead of spending past it.
- Every network call is logged with its key's fingerprint, never the key.
"""
from __future__ import annotations

import fcntl
import gzip
import json
import shutil
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from . import storage
from .keys import KeyPool, redact

URL = "https://mainnet.helius-rpc.com/?api-key="
PAGE = 1000
EMPTY_CONFIRMATIONS = 2
NULL_TX_RETRIES = 2
_TRANSIENT_HTTP = (408, 500, 502, 503, 504)


class RpcError(RuntimeError):
    pass


class BudgetExhausted(RpcError):
    pass


class TxNotFound(RpcError):
    """The node answered null: not an outage. The signature may be pruned or wrong."""


@dataclass
class SigWalk:
    """Signatures newest first. `stop` is genesis, window or max_pages."""
    address: str
    signatures: list[dict[str, Any]]
    complete: bool
    stop: str
    pages: int

    def first_observable(self) -> Optional[dict[str, Any]]:
        """Oldest signature read. Only the wallet's first activity if the walk reached genesis."""
        return self.signatures[-1] if self.signatures else None


class Budget:
    """Credit ceiling shared across processes through a locked counter file."""

    def __init__(self, path: Path, ceiling: int, run_limit: Optional[int] = None):
        self.path, self.ceiling, self.run_limit = path, ceiling, run_limit
        self.run_spent = 0
        path.parent.mkdir(parents=True, exist_ok=True)

    def charge(self, credits: int = 1) -> None:
        if self.run_limit is not None and self.run_spent + credits > self.run_limit:
            raise BudgetExhausted("this run's limit reached: %d of %d" % (self.run_spent, self.run_limit))
        with open(self.path, "a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.seek(0)
            used = int(f.read() or 0)
            if used + credits > self.ceiling:
                raise BudgetExhausted("credit ceiling reached: %d of %d" % (used, self.ceiling))
            f.seek(0)
            f.truncate()
            f.write(str(used + credits))
        self.run_spent += credits

    def used(self) -> int:
        return int(self.path.read_text() or 0) if self.path.exists() else 0


class RpcClient:
    def __init__(self, pool: KeyPool, root: Path, budget: Budget,
                 read_caches: Sequence[Path] = (), opener: Optional[Callable[..., Any]] = None,
                 legacy_root: Optional[Path] = None, max_db_bytes: int = 0):
        self.pool, self.root, self.budget = pool, root, budget
        self.read_caches = list(read_caches)
        self.legacy_root = legacy_root or root
        self.max_db_bytes = max_db_bytes
        self._open = opener or urllib.request.urlopen
        self.net_calls = 0
        self.cache_hits = 0
        self._db: Optional[sqlite3.Connection] = None
        self._db_ext: Optional[sqlite3.Connection] = None
        self._db_lock = threading.Lock()
        (root / "rpc_raw").mkdir(parents=True, exist_ok=True)
        self._log_path = root / "rpc_raw" / "provenance.jsonl"

    def _log(self, method: str, subject: str, fp: str, status: Any, secs: float) -> None:
        line = json.dumps({"t": int(time.time()), "m": method, "s": subject[:88], "k": fp,
                           "st": status, "secs": round(secs, 3)}) + "\n"
        with open(self._log_path, "a") as f:
            f.write(line)

    def call(self, method: str, params: list[Any], subject: str = "", tries: int = 8, credits: int = 1) -> Any:
        body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
        last = "no attempt"
        for attempt in range(tries):
            self.budget.charge(credits)
            key = self.pool.acquire()
            t0 = time.time()
            self.net_calls += 1
            try:
                req = urllib.request.Request(URL + key.value, body, {"Content-Type": "application/json"})
                with self._open(req, timeout=90) as r:
                    reply = json.load(r)
            except urllib.error.HTTPError as e:
                text = redact(e.read(300).decode(errors="ignore"))
                self._log(method, subject, key.fp, e.code, time.time() - t0)
                last = "HTTP %d %s" % (e.code, text[:120])
                if e.code == 429:
                    if "max usage" in text.lower():
                        self.pool.retire(key)
                    else:
                        self.pool.cool(key, min(30.0, 2.0 ** attempt))
                    continue
                if e.code in _TRANSIENT_HTTP:
                    time.sleep(min(30.0, 2.0 ** attempt))
                    continue
                raise RpcError("%s: %s" % (method, last)) from None
            except (urllib.error.URLError, TimeoutError, ConnectionError, json.JSONDecodeError) as e:
                self._log(method, subject, key.fp, type(e).__name__, time.time() - t0)
                last = type(e).__name__
                time.sleep(min(30.0, 2.0 ** attempt))
                continue
            self._log(method, subject, key.fp, 200, time.time() - t0)
            err = reply.get("error") if isinstance(reply, dict) else "not an object"
            if err:
                text = redact(json.dumps(err))
                last = text[:160]
                if "max usage" in text.lower():
                    self.pool.retire(key)
                    continue
                if isinstance(err, dict) and err.get("code") in (-32005, -32429, 429):
                    self.pool.cool(key, min(30.0, 2.0 ** attempt))
                    continue
                raise RpcError("%s: %s" % (method, last))
            if "result" not in reply:
                raise RpcError("%s: reply without result" % method)
            return reply["result"]
        raise RpcError("%s: gave up after %d tries, last: %s" % (method, tries, last))

    # ------------------------------------------------------------- transactions
    def _tx_path(self, sig: str) -> Path:
        """Older cache layout, one file per transaction: read only. It saturated a USB disk."""
        return self.legacy_root / "rpc_raw" / "tx" / sig[:2] / (sig + ".json.gz")

    def _open_db(self, attr: str, path: Path) -> sqlite3.Connection:
        with self._db_lock:
            db = getattr(self, attr)
            if db is None:
                path.parent.mkdir(parents=True, exist_ok=True)
                db = sqlite3.connect(path, check_same_thread=False, timeout=120)
                db.execute("PRAGMA journal_mode=WAL")
                db.execute("PRAGMA synchronous=NORMAL")
                db.execute("CREATE TABLE IF NOT EXISTS tx(sig TEXT PRIMARY KEY, body BLOB NOT NULL) WITHOUT ROWID")
                setattr(self, attr, db)
            return db

    def _db_conn(self) -> sqlite3.Connection:
        return self._open_db("_db", self.root / "rpc_raw" / "tx.sqlite")

    def _tx_cached(self, sig: str) -> Optional[dict[str, Any]]:
        dbs = [self._db_conn()]
        if self.legacy_root != self.root and (self.legacy_root / "rpc_raw" / "tx.sqlite").exists():
            dbs.append(self._overflow_conn())
        for db in dbs:
            with self._db_lock:
                row = db.execute("SELECT body FROM tx WHERE sig = ?", (sig,)).fetchone()
            if row:
                return json.loads(zlib.decompress(row[0]))
        p = self._tx_path(sig)
        if p.exists():
            with gzip.open(p, "rt") as f:
                tx = json.load(f)
            self._store_tx(sig, tx)  # next time from the database, not one small file on a slow disk
            return tx
        for c in self.read_caches:
            q = c / (sig + ".json")
            if q.exists():
                with open(q) as f:
                    return json.load(f)["result"]
        return None

    def tx(self, sig: str) -> dict[str, Any]:
        cached = self._tx_cached(sig)
        if cached is not None:
            self.cache_hits += 1
            return cached
        # Version 1 transactions exist since September 2026; a ceiling of 0 fails on them with -32015.
        params = [sig, {"encoding": "json", "maxSupportedTransactionVersion": 1}]
        r = self.call("getTransaction", params, sig)
        for _ in range(NULL_TX_RETRIES):  # a null under load is not an answer; it is never cached
            if r is not None:
                break
            time.sleep(1.0)
            r = self.call("getTransaction", params, sig)
        if r is None:
            raise TxNotFound(sig)
        self._store_tx(sig, r)
        return r

    def _store_txs(self, rows: list[tuple[str, dict[str, Any]]]) -> None:
        """One transaction per batch: a page of 100 costs one commit, not 100 files."""
        body = [(s, zlib.compress(json.dumps(t).encode(), 6)) for s, t in rows]
        if self._overflowing():
            db = self._overflow_conn()
        else:
            db = self._db_conn()
        with self._db_lock:
            db.executemany("INSERT OR IGNORE INTO tx(sig, body) VALUES (?, ?)", body)
            db.commit()

    def _overflowing(self) -> bool:
        """Over the quota, or under the internal disk's floor: new writes go to the external disk."""
        if not self.max_db_bytes:
            return False
        path = self.root / "rpc_raw" / "tx.sqlite"
        low = shutil.disk_usage(self.root).free < storage.INTERNAL_MIN_FREE_BYTES + 200_000_000
        return (path.exists() and path.stat().st_size > self.max_db_bytes) or low

    def _overflow_conn(self) -> sqlite3.Connection:
        if self.legacy_root == self.root:
            raise BudgetExhausted("cache quota reached and no external volume configured")
        if not (self.legacy_root / storage.MARKER).is_file():
            raise BudgetExhausted("cache quota reached and the external volume is not mounted")
        return self._open_db("_db_ext", self.legacy_root / "rpc_raw" / "tx.sqlite")

    def _store_tx(self, sig: str, tx: dict[str, Any]) -> None:
        self._store_txs([(sig, tx)])

    def tx_parsed(self, sig: str) -> dict[str, Any]:
        """The node's own jsonParsed reading, for decoder comparison only."""
        p = self.root / "rpc_raw" / "tx_parsed" / (sig + ".json.gz")
        if p.exists():
            with gzip.open(p, "rt") as f:
                return json.load(f)
        r = self.call("getTransaction", [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 1}], sig)
        if r is None:
            raise TxNotFound(sig)
        p.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(p, "wt") as f:
            json.dump(r, f)
        return r

    # ------------------------------------------------------------------ history
    def history_txs(self, addr: str, t_from: Optional[int] = None, t_to: Optional[int] = None,
                    token_accounts: str = "balanceChanged", max_pages: int = 20) -> tuple[list[dict[str, Any]], SigWalk]:
        """Full transactions of an address, oldest first, through Helius getTransactionsForAddress.

        With tokenAccounts=balanceChanged this also returns inflows to the address's token accounts,
        which signature walks of the owner miss. 100 transactions cost 10 credits against 101 the
        classic way. The response carries transactionIndex, so chain order inside a slot is exact.
        Resumable: the pagination token is saved after each page.
        """
        tag = "%s_%s_%s_%s.jsonl" % (addr, t_from or "start", t_to or "end", token_accounts)
        ck = self.root / "checkpoints" / "gtfa" / tag
        ck.parent.mkdir(parents=True, exist_ok=True)
        sigs: list[dict[str, Any]] = []
        token, pages, ended = None, 0, False
        if ck.exists():
            with open(ck) as f:
                for line in f:
                    row = json.loads(line)
                    sigs.extend(row["sigs"])
                    token, pages, ended = row["next"], pages + 1, row["next"] is None
        filters: dict[str, Any] = {"tokenAccounts": token_accounts}
        window = {k: v for k, v in (("gte", t_from), ("lte", t_to)) if v is not None}
        if window:
            filters["blockTime"] = window
        while not ended and pages < max_pages:
            cfg: dict[str, Any] = {"transactionDetails": "full", "sortOrder": "asc", "limit": 100, "filters": filters,
                                   "encoding": "json", "maxSupportedTransactionVersion": 1}
            if token:
                cfg["paginationToken"] = token
            r = self.call("getTransactionsForAddress", [addr, cfg], addr, credits=10)
            for _ in range(EMPTY_CONFIRMATIONS):  # an empty ending page is only believed after asking again
                if not (isinstance(r, dict) and r.get("data") == [] and r.get("paginationToken") is None):
                    break
                r = self.call("getTransactionsForAddress", [addr, cfg], addr, credits=10)
            data = r.get("data") if isinstance(r, dict) else None
            if not isinstance(data, list) or "paginationToken" not in r:
                raise RpcError("getTransactionsForAddress: malformed reply")
            rows = []
            for item in data:
                rows.append({"signature": item["transaction"]["signatures"][0], "slot": item["slot"],
                             "blockTime": item.get("blockTime"), "transactionIndex": item.get("transactionIndex")})
            # A transaction some read cache already holds is not stored twice.
            self._store_txs([(r["signature"], t) for r, t in zip(rows, data)
                             if not any((c / (r["signature"] + ".json")).exists() for c in self.read_caches)])
            token, pages, ended = r["paginationToken"], pages + 1, r["paginationToken"] is None
            sigs.extend(rows)
            with open(ck, "a") as f:
                f.write(json.dumps({"sigs": rows, "next": token}) + "\n")
        stop = ("genesis" if t_from is None else "window") if ended else "max_pages"
        walk = SigWalk(addr, list(reversed(sigs)), ended, stop, pages)
        return [self.tx(s["signature"]) for s in sigs], walk

    # --------------------------------------------------------------- signatures
    def page(self, addr: str, before: Optional[str] = None, limit: int = PAGE) -> list[dict[str, Any]]:
        p: dict[str, Any] = {"limit": limit}
        if before:
            p["before"] = before
        r = self.call("getSignaturesForAddress", [addr, p], addr)
        if not isinstance(r, list):
            raise RpcError("getSignaturesForAddress did not return a list")
        return r

    def walk(self, addr: str, stop_ts: Optional[int] = None, before: Optional[str] = None,
             max_pages: int = 50, checkpoint: bool = True) -> SigWalk:
        """Newest to oldest, resumable: a resume continues from the last signature already read."""
        ck = self.root / "checkpoints" / "sigs" / ("%s_%s_%s.jsonl" % (addr, before or "HEAD", stop_ts or "all"))
        sigs: list[dict[str, Any]] = []
        pages, cur = 0, before
        if checkpoint and ck.exists():
            with open(ck) as f:
                for line in f:
                    row = json.loads(line)
                    if row.get("end"):
                        return SigWalk(addr, sigs, row["complete"], row["end"], pages)
                    sigs.extend(row["page"])
                    pages += 1
            cur = sigs[-1]["signature"] if sigs else before
        ck.parent.mkdir(parents=True, exist_ok=True)

        def save(row: dict[str, Any]) -> None:
            if checkpoint:
                with open(ck, "a") as f:
                    f.write(json.dumps(row) + "\n")

        while True:
            if pages >= max_pages:
                return SigWalk(addr, sigs, False, "max_pages", pages)  # not saved: a larger cap may resume
            page = self.page(addr, cur)
            pages += 1
            if not page:
                # Under load Helius has answered [] in mid-history, and a short page proves nothing
                # either (docs/PITFALLS.md, data/trace_temoins/14_corrige_pages_vides.py). Genesis
                # takes an empty answer to the same question, confirmed.
                for _ in range(EMPTY_CONFIRMATIONS):
                    page = self.page(addr, cur)
                    if page:
                        break
                if not page:
                    save({"end": "genesis", "complete": True})
                    return SigWalk(addr, sigs, True, "genesis", pages)
            sigs.extend(page)
            save({"page": page})
            cur = page[-1]["signature"]
            oldest = page[-1].get("blockTime")
            if stop_ts is not None and oldest is not None and oldest < stop_ts:
                save({"end": "window", "complete": True})
                return SigWalk(addr, sigs, True, "window", pages)
