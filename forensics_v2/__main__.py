"""Command line. Usage: python -m forensics_v2 trace <wallet> [--direction both] [--hops 2] [--credits 2000]"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import sys
from pathlib import Path

from . import decode as D
from . import storage
from .keys import KeyPool
from .rpc import Budget, RpcClient
from .trace import findings, render, trace


def read_caches() -> list[Path]:
    """Existing transaction caches, read only. $FORENSICS_READ_CACHES is a colon-separated list."""
    raw = os.environ.get("FORENSICS_READ_CACHES")
    if raw is None and storage.CONFIG.exists():
        raw = ":".join(json.loads(storage.CONFIG.read_text()).get("read_caches", []))
    return [Path(p) for p in (raw or "").split(":") if p and Path(p).is_dir()]


def client(credits: int) -> RpcClient:
    root = storage.data_root()
    cfg = json.loads(storage.CONFIG.read_text())
    used = Budget(root / "checkpoints" / "credits", cfg["credit_ceiling"])
    budget = Budget(used.path, min(cfg["credit_ceiling"], used.used() + credits))
    return RpcClient(KeyPool.from_config(), root, budget, read_caches())


def main() -> int:
    ap = argparse.ArgumentParser(prog="forensics_v2")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trace", help="funding and destination report for one wallet")
    t.add_argument("wallet")
    t.add_argument("--direction", choices=("back", "forward", "both"), default="both")
    t.add_argument("--hops", type=int, default=2)
    t.add_argument("--credits", type=int, default=2000, help="network credits this run may spend")
    t.add_argument("--min-sol", type=float, default=0.01)
    t.add_argument("--max-pages", type=int, default=20, help="signature pages per wallet before calling it truncated")
    t.add_argument("--t-from", type=int, help="unix time; earlier history is left out and the report says so")
    t.add_argument("--t-to", type=int, help="unix time; later history is left out and the report says so")
    t.add_argument("--out", type=Path, help="directory for report.md and graph.json (default: external volume)")
    d = sub.add_parser("tx", help="decode one transaction")
    d.add_argument("signature")
    a = ap.parse_args()

    if a.cmd == "tx":
        x = D.decode(client(5).tx(a.signature))
        print(json.dumps({"signature": x.signature, "ok": x.ok, "fee": x.fee, "signers": x.signers, "venues": x.venues,
                          "conserved": x.conserved, "residual": x.residual, "token_residual": x.token_residual,
                          "owners": {o: {"sol": n.sol, "native": n.native, "wsol": n.wsol, "rent": n.rent,
                                         "tokens": n.tokens} for o, n in x.owners.items()},
                          "edges": [dataclasses.asdict(e) for e in x.edges],
                          "unresolved_sol": x.unresolved_sol}, indent=1))
        return 0

    c = client(a.credits)
    g = trace(c, a.wallet, a.direction, a.hops, int(a.min_sol * 1e9), max_pages=a.max_pages,
              t_from=a.t_from, t_to=a.t_to)
    out = a.out or storage.sub("intermediate/trace/" + a.wallet)
    out.mkdir(parents=True, exist_ok=True)
    (out / "report.md").write_text(render(g))
    (out / "graph.json").write_text(json.dumps(
        {"seed": g.seed, "nodes": g.nodes, "edges": g.edges, "stops": g.stops, "budget_hit": g.budget_hit,
         "findings": findings(g), "net_calls": c.net_calls, "cache_hits": c.cache_hits}, indent=1))
    print(json.dumps({"seed": g.seed, "nodes": len(g.nodes), "edges": len(g.edges), "stops": len(g.stops),
                      "budget_hit": g.budget_hit, "net_calls": c.net_calls, "cache_hits": c.cache_hits,
                      "report": str(out / "report.md")}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
