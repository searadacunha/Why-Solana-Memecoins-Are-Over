"""DuckDB store. Each event points at its signature, and replaying a transaction adds nothing.

Money columns are HUGEINT: lamports and raw token units, never a float. Primary keys are what keeps a
replay from booking the same movement twice, and `reconcile` re-checks the books after any ingest.
Tables without an ingest yet are declared so that their shape is settled; `counts()` shows them empty.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Optional

import duckdb

from . import decode as D

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions(signature VARCHAR PRIMARY KEY, slot UBIGINT NOT NULL, tx_index INTEGER,
    block_time BIGINT, ok BOOLEAN NOT NULL, fee HUGEINT NOT NULL, fee_payer VARCHAR NOT NULL, conserved BOOLEAN NOT NULL,
    n_lamport_residuals INTEGER NOT NULL, n_token_residuals INTEGER NOT NULL, venues VARCHAR);
CREATE TABLE IF NOT EXISTS instructions(signature VARCHAR, path VARCHAR, kind VARCHAR NOT NULL, src VARCHAR, dst VARCHAR,
    amount HUGEINT NOT NULL, mint VARCHAR, src_owner VARCHAR, dst_owner VARCHAR, PRIMARY KEY(signature, path, kind));
CREATE TABLE IF NOT EXISTS balance_movements(signature VARCHAR, owner VARCHAR, native HUGEINT NOT NULL,
    wsol HUGEINT NOT NULL, rent HUGEINT NOT NULL, PRIMARY KEY(signature, owner));
CREATE TABLE IF NOT EXISTS token_movements(signature VARCHAR, owner VARCHAR, mint VARCHAR, amount HUGEINT NOT NULL,
    PRIMARY KEY(signature, owner, mint));
CREATE TABLE IF NOT EXISTS token_accounts(account VARCHAR PRIMARY KEY, mint VARCHAR NOT NULL, owner VARCHAR, program VARCHAR);
CREATE TABLE IF NOT EXISTS funding_edges(signature VARCHAR, src VARCHAR, dst VARCHAR, lamports HUGEINT NOT NULL,
    evidence VARCHAR NOT NULL, basis VARCHAR NOT NULL, path VARCHAR NOT NULL, PRIMARY KEY(signature, src, dst, basis, path));
CREATE TABLE IF NOT EXISTS unresolved_sol(signature VARCHAR, owner VARCHAR, lamports HUGEINT NOT NULL,
    PRIMARY KEY(signature, owner));
CREATE TABLE IF NOT EXISTS swap_events(signature VARCHAR, owner VARCHAR, mint VARCHAR, token_delta HUGEINT NOT NULL,
    sol_lamports HUGEINT NOT NULL, side VARCHAR NOT NULL, venues VARCHAR, PRIMARY KEY(signature, owner, mint));
CREATE TABLE IF NOT EXISTS mint_creation(mint VARCHAR PRIMARY KEY, signature VARCHAR, slot UBIGINT, block_time BIGINT,
    creator VARCHAR, decimals INTEGER, supply HUGEINT);
CREATE TABLE IF NOT EXISTS liquidity_events(signature VARCHAR, mint VARCHAR, pool VARCHAR, kind VARCHAR,
    sol_lamports HUGEINT, token_amount HUGEINT, PRIMARY KEY(signature, mint, kind));
CREATE TABLE IF NOT EXISTS wallet_roles(wallet VARCHAR, role VARCHAR, evidence VARCHAR NOT NULL, source VARCHAR,
    PRIMARY KEY(wallet, role));
CREATE TABLE IF NOT EXISTS wallet_clusters(cluster_id VARCHAR, wallet VARCHAR, method VARCHAR NOT NULL,
    PRIMARY KEY(cluster_id, wallet, method));
CREATE TABLE IF NOT EXISTS cluster_evidence(cluster_id VARCHAR, claim VARCHAR, evidence VARCHAR NOT NULL, signature VARCHAR,
    note VARCHAR);
CREATE TABLE IF NOT EXISTS trade_positions(wallet VARCHAR, mint VARCHAR, t_open BIGINT, sig_open VARCHAR, t_close BIGINT,
    sol_out HUGEINT NOT NULL, sol_in HUGEINT NOT NULL, bought HUGEINT NOT NULL, sold HUGEINT NOT NULL, closed BOOLEAN NOT NULL,
    PRIMARY KEY(wallet, mint, t_open));
CREATE TABLE IF NOT EXISTS realized_pnl(wallet VARCHAR, mint VARCHAR, t_open BIGINT, lamports HUGEINT NOT NULL,
    definition VARCHAR NOT NULL, PRIMARY KEY(wallet, mint, t_open, definition));
CREATE TABLE IF NOT EXISTS capital_destinations(src VARCHAR, dst VARCHAR, lamports HUGEINT NOT NULL, hops INTEGER NOT NULL,
    evidence VARCHAR NOT NULL, terminal VARCHAR, PRIMARY KEY(src, dst, hops));
CREATE TABLE IF NOT EXISTS service_attributions(address VARCHAR PRIMARY KEY, name VARCHAR NOT NULL, kind VARCHAR, source VARCHAR);
CREATE TABLE IF NOT EXISTS coverage(address VARCHAR, t_from BIGINT, t_to BIGINT, complete BOOLEAN NOT NULL, stop VARCHAR,
    transactions INTEGER, reached_genesis BOOLEAN, PRIMARY KEY(address, t_from, t_to));
CREATE TABLE IF NOT EXISTS rpc_provenance(t BIGINT, method VARCHAR, subject VARCHAR, key_fingerprint VARCHAR, status VARCHAR,
    secs DOUBLE);
"""
TABLES = ("transactions", "instructions", "balance_movements", "token_movements", "token_accounts", "funding_edges",
          "unresolved_sol", "swap_events", "mint_creation", "liquidity_events", "wallet_roles", "wallet_clusters",
          "cluster_evidence", "trade_positions", "realized_pnl", "capital_destinations", "service_attributions",
          "coverage", "rpc_provenance")


def connect(path: Optional[Path] = None) -> Any:
    con = duckdb.connect(str(path) if path else ":memory:")
    con.execute(SCHEMA)
    return con


def ingest(con: Any, txs: Iterable[D.Decoded], tx_index: Optional[dict[str, int]] = None) -> int:
    """Add decoded transactions. Returns how many were new; a replay returns 0 and changes nothing."""
    new = 0
    for d in txs:
        before = con.execute("SELECT count(*) FROM transactions WHERE signature = ?", [d.signature]).fetchone()[0]
        if before:
            continue
        new += 1
        con.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    [d.signature, d.slot, (tx_index or {}).get(d.signature), d.block_time, d.ok, d.fee, d.fee_payer,
                     d.conserved, len(d.residual), len(d.token_residual), ",".join(d.venues)])
        seen = set()
        for t in d.transfers:
            if (t.path, t.kind) in seen:
                continue
            seen.add((t.path, t.kind))
            con.execute("INSERT INTO instructions VALUES (?,?,?,?,?,?,?,?,?)",
                        [d.signature, t.path, t.kind, t.src, t.dst, t.amount, t.mint, t.src_owner, t.dst_owner])
        for owner, n in d.owners.items():
            con.execute("INSERT INTO balance_movements VALUES (?,?,?,?,?)", [d.signature, owner, n.native, n.wsol, n.rent])
            for mint, amount in n.tokens.items():
                con.execute("INSERT INTO token_movements VALUES (?,?,?,?)", [d.signature, owner, mint, amount])
            for mint, dt in D.traded_mints(d, owner).items():
                side = "buy" if dt > 0 and n.sol < 0 else "sell" if dt < 0 and n.sol > 0 else "other"
                con.execute("INSERT INTO swap_events VALUES (?,?,?,?,?,?,?)",
                            [d.signature, owner, mint, dt, n.sol, side, ",".join(d.venues)])
        for acct, ta in d.token_accounts.items():
            con.execute("INSERT OR IGNORE INTO token_accounts VALUES (?,?,?,?)", [acct, ta.mint, ta.owner, ta.program])
        for e in d.edges:
            con.execute("INSERT OR IGNORE INTO funding_edges VALUES (?,?,?,?,?,?,?)",
                        [d.signature, e.src, e.dst, e.lamports, e.evidence, e.basis, e.path or ""])
        for owner, v in d.unresolved_sol.items():
            con.execute("INSERT INTO unresolved_sol VALUES (?,?,?)", [d.signature, owner, v])
    return new


def reconcile(con: Any) -> dict[str, Any]:
    """Books that must balance. Every value here should be 0 except the informational counts."""
    q = {
        "tx_not_conserved": "SELECT count(*) FROM transactions WHERE NOT conserved",
        "tx_owner_sum_plus_fee_nonzero": """
            SELECT count(*) FROM (SELECT b.signature, sum(native + wsol + rent) + any_value(t.fee) AS s
            FROM balance_movements b JOIN transactions t USING (signature) GROUP BY b.signature) WHERE s <> 0""",
        "edges_on_unknown_tx": "SELECT count(*) FROM funding_edges e ANTI JOIN transactions t USING (signature)",
        "failed_tx_with_edges": """
            SELECT count(*) FROM funding_edges e JOIN transactions t USING (signature) WHERE NOT t.ok""",
        "info_lamports_unresolved": "SELECT coalesce(sum(abs(lamports)), 0) FROM unresolved_sol",
        "info_transactions": "SELECT count(*) FROM transactions",
    }
    return {k: int(con.execute(v).fetchone()[0]) for k, v in q.items()}


def counts(con: Any) -> dict[str, int]:
    return {t: con.execute("SELECT count(*) FROM %s" % t).fetchone()[0] for t in TABLES}


def export_parquet(con: Any, out: Path, tables: Iterable[str] = TABLES) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for t in tables:
        con.execute("COPY %s TO '%s' (FORMAT parquet)" % (t, out / (t + ".parquet")))
