#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fparse.py -- one raw transaction of a launch window -> one compact record.

A trade is read from balance changes, never from instruction names, so it
works whatever router or bot program sent it (per-wallet SOL: see leg_sol):
  * the token leg is the change of the mint balance of each owner
    (pre/postTokenBalances); the venue's own accounts are recognised as the
    bonding curve (its PDA, derived from the mint) and the pool (the owner that
    holds both the mint and wrapped SOL);
  * the SOL leg is what the venue received or paid: the curve account's
    lamports, or the pool's wrapped-SOL balance. That is the exact flow at the
    venue, fees of routers and tips excluded;
  * the trader is the non-venue owner whose token balance moved the most.
Instruction names from the logs are used only for events that move no trader
balance: the creation (CreateV2 / Create) and the migration (MigrateV2 /
Migrate). A transaction that only opens a token account is kept as "ata":
a wallet getting ready to trade, which is itself information.

The order of the transactions of one slot is unknown (the RPC gives no index),
so records carry the slot and the block time, and nothing more precise.
"""
from __future__ import annotations

import importlib.util
import os
from typing import Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
_spec = importlib.util.spec_from_file_location("bundle09", os.path.join(ROOT, "code", "09_bundle_snipe.py"))
_b09 = importlib.util.module_from_spec(_spec)  # type: ignore[arg-type]
_spec.loader.exec_module(_b09)  # type: ignore[union-attr]
bonding_curve_pda = _b09.bonding_curve_pda   # the repository's own PDA derivation, reused

WSOL = "So11111111111111111111111111111111111111112"
PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMPSWAP = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"
JITO_TIPS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5", "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY", "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh", "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL", "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
}
ROUTERS = {"JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "jupiter",
           "6m2CDdhRgxpH4WjvdzxAYbGxwdGUz5MziiL5jek2kBma": "okx",
           "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "raydium",
           "DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH": "dflow"}


def _amount(b: dict[str, Any]) -> float:
    return float(b["uiTokenAmount"].get("uiAmount") or 0.0)


def _instructions(t: dict[str, Any]) -> list[dict[str, Any]]:
    msg = t["transaction"]["message"]
    out = list(msg.get("instructions") or [])
    for g in (t["meta"].get("innerInstructions") or []):
        out += g.get("instructions") or []
    return out


def curve_transfers(t: dict[str, Any], curve: str) -> dict[str, float]:
    """{payer: SOL} sent to the curve by System transfers only. For the creation
    transaction: buyers_of_tx would also count the rent that creates the curve
    account (about 0.0016 SOL); the creator's own first buy is the transfer."""
    out: dict[str, float] = {}
    for ix in _instructions(t):
        p = ix.get("parsed") or {} if ix.get("program") == "system" else {}
        info = p.get("info") or {}
        if p.get("type") in ("transfer", "transferWithSeed") and info.get("destination") == curve:
            lp = int(info.get("lamports") or 0)
            if info.get("source") and lp > 0:
                out[info["source"]] = out.get(info["source"], 0.0) + lp / 1e9
    return out


def parse(t: dict[str, Any], mint: str, curve: str, pool_addr: Optional[str]) -> dict[str, Any]:
    """One successful transaction -> record. pool_addr is the PumpSwap pool of the
    mint, known from its migration transaction (None before it)."""
    meta = t["meta"]
    keys = [k["pubkey"] for k in t["transaction"]["message"]["accountKeys"]]
    signer = keys[0]
    n_sig = len(t["transaction"].get("signatures") or [1])
    fee = meta.get("fee") or 0
    logs = meta.get("logMessages") or []
    names = {ln.split("Instruction: ", 1)[1].strip() for ln in logs if "Instruction: " in ln}
    progs = set()
    tip = 0
    for ix in _instructions(t):
        p = ix.get("programId")
        if p:
            progs.add(p)
        parsed = ix.get("parsed")
        if isinstance(parsed, dict) and parsed.get("type") == "transfer" and ix.get("program") == "system":
            info = parsed.get("info") or {}
            if info.get("destination") in JITO_TIPS:
                tip += int(info.get("lamports") or 0)

    def by_owner(side: str, which: str) -> dict[str, float]:
        out: dict[str, float] = {}
        for b in meta.get(side) or []:
            if b.get("mint") == which:
                o = b.get("owner") or ""
                out[o] = out.get(o, 0.0) + _amount(b)
        return out
    tok_pre, tok_post = by_owner("preTokenBalances", mint), by_owner("postTokenBalances", mint)
    ws_pre, ws_post = by_owner("preTokenBalances", WSOL), by_owner("postTokenBalances", WSOL)
    dtok = {o: tok_post.get(o, 0.0) - tok_pre.get(o, 0.0) for o in set(tok_pre) | set(tok_post)}
    lam = {k: (meta["postBalances"][i] - meta["preBalances"][i]) / 1e9 for i, k in enumerate(keys)}
    curve_i = keys.index(curve) if curve in keys else None
    rec: dict[str, Any] = {"sig": t["transaction"]["signatures"][0], "slot": t["slot"], "bt": t.get("blockTime"),
                           "signer": signer, "n_sig": n_sig, "fee": fee, "prio": max(0, fee - 5000 * n_sig),
                           "tip": tip, "err": False, "router": sorted({ROUTERS[p] for p in progs if p in ROUTERS}),
                           "pump": PUMP in progs, "pumpswap": PUMPSWAP in progs, "n_prog": len(progs),
                           "dsol_signer": lam.get(signer, 0.0) + fee / 1e9}
    if pool_addr and pool_addr in tok_post:
        rec["pool_sol"] = ws_post.get(pool_addr, 0.0)
        rec["pool_tok"] = tok_post.get(pool_addr, 0.0)
    if curve in tok_post:
        rec["curve_tok"] = tok_post[curve]
    if curve_i is not None:
        rec["curve_lamports"] = meta["postBalances"][curve_i] / 1e9
    venue = None
    v_tok = v_sol = 0.0
    if pool_addr and (dtok.get(pool_addr) or ws_post.get(pool_addr, 0.0) != ws_pre.get(pool_addr, 0.0)):
        venue, v_tok, v_sol = "pool", dtok.get(pool_addr, 0.0), ws_post.get(pool_addr, 0.0) - ws_pre.get(pool_addr, 0.0)
    elif dtok.get(curve):
        venue, v_tok, v_sol = "curve", dtok[curve], lam.get(curve, 0.0)
    legs = {o: round(v, 6) for o, v in dtok.items() if o not in (pool_addr, curve) and abs(v) > 1e-6}
    if legs:
        rec["legs"] = legs
        # SOL attributable to each owner, never a pro-rata of tokens. For a curve
        # buy, the SOL each wallet itself sent to the curve, read from the System
        # transfers (code/09_bundle_snipe.buyers_of_tx, the repository's method;
        # it reproduces the detector's TradeEvent tickets to 0.000 SOL on 169
        # alerts). Otherwise the owner's net SOL change (lamports plus wrapped
        # SOL), the transaction fee added back for the fee payer.
        if venue == "curve" and v_tok < 0:
            rec["leg_sol"] = {o: lp / 1e9 for o, lp in _b09.buyers_of_tx(t, curve).items()}
        rec["owner_sol"] = {o: round(lam.get(o, 0.0) + ws_post.get(o, 0.0) - ws_pre.get(o, 0.0)
                                     + (fee / 1e9 if o == signer else 0.0), 9) for o in legs}
    kind = "other"
    if "CreateV2" in names or "Create" in names:
        kind = "create"
    elif "MigrateV2" in names or "Migrate" in names:
        kind = "migrate"
    elif venue and legs:
        kind = "buy" if v_tok < 0 else "sell"
    elif venue:
        kind = "buyburn" if (v_tok < 0 and v_sol > 0) else "venue_only"
    elif legs:
        kind = "transfer" if any(v < 0 for v in legs.values()) else "mint_in"
    elif any(o for o in tok_post if o not in tok_pre) or "InitializeAccount3" in names:
        kind = "ata"
    elif not names and not any(abs(v) > 1e-9 for v in dtok.values()):
        kind = "noop"
    if venue:
        rec.update({"venue": venue, "v_tok": v_tok, "v_sol": v_sol,
                    "price": abs(v_sol) / abs(v_tok) if v_tok else None})
    if legs:
        main = max(legs, key=lambda o: abs(legs[o]))
        rec["trader"] = main
    if kind == "create" and venue == "curve":
        # the curve's token balance rises in the creation transaction (the
        # supply lands on it), so the v_tok < 0 test above never fires there;
        # the creator's own first buy is read from its transfer to the curve
        rec["leg_sol"] = curve_transfers(t, curve)
    rec["kind"] = kind
    return rec


def pool_of(w: dict[str, Any], mint: str, curve: str) -> Optional[str]:
    """The pool: in the migration transaction, the owner (other than the curve)
    that ends with the largest balance of the mint and also holds wrapped SOL."""
    for s in w["sigs"]:
        t = w["txs"].get(s["sig"])
        if not t:
            continue
        logs = t["meta"].get("logMessages") or []
        if not any(("Instruction: MigrateV2" in ln or "Instruction: Migrate" in ln) for ln in logs):
            continue
        tok: dict[str, float] = {}
        ws: dict[str, float] = {}
        for b in t["meta"].get("postTokenBalances") or []:
            o = b.get("owner") or ""
            if b.get("mint") == mint:
                tok[o] = tok.get(o, 0.0) + _amount(b)
            elif b.get("mint") == WSOL:
                ws[o] = ws.get(o, 0.0) + _amount(b)
        cands = [o for o in tok if o != curve and o in ws]
        if cands:
            return max(cands, key=lambda o: tok[o])
    return None


def parse_window(w: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """(records sorted by slot, window facts: curve, pool, migration slot)."""
    mint = w["mint"]
    curve = bonding_curve_pda(mint)
    pool = pool_of(w, mint, curve)
    out = []
    for s in w["sigs"]:
        if s["err"]:
            out.append({"sig": s["sig"], "slot": s["slot"], "bt": s["bt"], "err": True, "kind": "failed"})
            continue
        out.append(parse(w["txs"][s["sig"]], mint, curve, pool))
    out.sort(key=lambda r: (r["slot"], r["bt"] or 0))
    mig = [r["slot"] for r in out if r["kind"] == "migrate"]
    return out, {"curve": curve, "pool": pool, "migration_slot": mig[0] if mig else None}
