"""Decode one raw getTransaction result (encoding "json") into exact economic movements.

Pure and stdlib-only: no network, no float on any money value. Amounts are integers
(lamports, raw token units).

Three layers, each checked against the chain's own balances:
  1. instruction events: System and SPL Token/Token-2022 instructions, outer and inner, in order;
  2. reconciliation: replaying layer 1 must land on postBalances. What does not is a residual,
     for example a program moving lamports it owns (pump.fun pays a seller that way);
  3. owner nets: per owner, native SOL + wrapped SOL + token-account rent, and token deltas.

A net change of balance does not by itself say who paid whom, so `edges()` only names a
counterparty when the instructions or the arithmetic force it, and says UNRESOLVED otherwise.
"""
from __future__ import annotations

import base64
import struct
from dataclasses import dataclass, field
from typing import Any, Optional

ONCHAIN_VERIFIED = "ONCHAIN_VERIFIED"
STRONG_TECHNICAL_INFERENCE = "STRONG_TECHNICAL_INFERENCE"
STATISTICAL_ASSOCIATION = "STATISTICAL_ASSOCIATION"
EXPLORATORY_HYPOTHESIS = "EXPLORATORY_HYPOTHESIS"
UNRESOLVED = "UNRESOLVED"
REFUTED = "REFUTED"
EVIDENCE_LEVELS = (ONCHAIN_VERIFIED, STRONG_TECHNICAL_INFERENCE, STATISTICAL_ASSOCIATION,
                   EXPLORATORY_HYPOTHESIS, UNRESOLVED, REFUTED)

SYSTEM = "11111111111111111111111111111111"
TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN22 = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
WSOL = "So11111111111111111111111111111111111111112"
PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
PUMPSWAP = "pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"

VENUES = {
    PUMP: "pump", PUMPSWAP: "pumpswap",
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "raydium_v4",
    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": "raydium_clmm",
    "CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C": "raydium_cpmm",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "jupiter",
    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": "orca",
    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": "meteora_dlmm",
    "Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB": "meteora_damm",
    "MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG": "moonshot",
}

# Jito's published tip accounts: a payment to one is a fee, not a counterparty.
JITO_TIP = frozenset({
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5", "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY", "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh", "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL", "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
})

_B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_B58_INDEX = {c: i for i, c in enumerate(_B58)}
TRADE_EVENT = bytes.fromhex("bddb7fd34ee661ee")


def b58decode(s: str) -> bytes:
    n = 0
    for c in s:
        n = n * 58 + _B58_INDEX[c]
    body = n.to_bytes((n.bit_length() + 7) // 8, "big")
    return b"\0" * (len(s) - len(s.lstrip("1"))) + body


def b58encode(b: bytes) -> str:
    n = int.from_bytes(b, "big")
    s = ""
    while n:
        n, r = divmod(n, 58)
        s = _B58[r] + s
    return "1" * (len(b) - len(b.lstrip(b"\0"))) + s


@dataclass(frozen=True)
class Transfer:
    """One instruction-level movement. `path` is "3" for outer 3, "3.2" for its third inner."""
    kind: str  # sol_transfer | sol_create | spl | close_refund | wsol_lamports | mint | burn
    src: Optional[str]
    dst: Optional[str]
    amount: int
    path: str
    mint: Optional[str] = None
    src_owner: Optional[str] = None
    dst_owner: Optional[str] = None


@dataclass(frozen=True)
class TokenAccount:
    mint: str
    owner: Optional[str]
    program: Optional[str] = None
    decimals: Optional[int] = None


@dataclass
class OwnerNet:
    native: int = 0   # lamports of the account itself, fee included for the fee payer
    wsol: int = 0     # change of wrapped SOL in this owner's token accounts
    rent: int = 0     # lamport change of its token accounts that is not wrapped SOL
    tokens: dict[str, int] = field(default_factory=dict)

    @property
    def sol(self) -> int:
        return self.native + self.wsol + self.rent


@dataclass(frozen=True)
class Edge:
    src: str
    dst: str
    lamports: int
    evidence: str
    basis: str  # instruction | net_single_payer | net_single_receiver
    path: Optional[str] = None


@dataclass
class Decoded:
    signature: str
    slot: int
    block_time: Optional[int]
    ok: bool
    fee: int
    fee_payer: str
    signers: list[str]
    keys: list[str]
    programs: list[str]
    venues: list[str]
    transfers: list[Transfer]
    token_accounts: dict[str, TokenAccount]
    owners: dict[str, OwnerNet]
    lamport_delta: dict[str, int]
    residual: dict[str, int]         # postBalance minus the replay of the instructions
    token_residual: dict[str, int]   # same for token amounts, by token account
    conserved: bool                  # sum of lamport changes == -fee, always true on a sane tx
    trade_events: list[dict[str, Any]]
    edges: list[Edge]
    unresolved_sol: dict[str, int]   # per owner, lamports no edge could account for


def account_keys(tx: dict[str, Any]) -> list[str]:
    """Static keys, then the lookup-table ones, in the order balances are indexed.

    jsonParsed already merges looked-up keys into accountKeys, as objects, so adding
    loadedAddresses again would shift every index beyond them.
    """
    raw = tx["transaction"]["message"]["accountKeys"]
    if raw and isinstance(raw[0], dict):
        return [x["pubkey"] for x in raw]
    loaded = (tx.get("meta") or {}).get("loadedAddresses") or {}
    return list(raw) + list(loaded.get("writable") or []) + list(loaded.get("readonly") or [])


def _walk_instructions(tx: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Instructions in execution order: outer i, then its inner ones."""
    inner = {g["index"]: g["instructions"] for g in tx["meta"].get("innerInstructions") or []}
    out: list[tuple[str, dict[str, Any]]] = []
    for i, ix in enumerate(tx["transaction"]["message"]["instructions"]):
        out.append((str(i), ix))
        out.extend(("%d.%d" % (i, j), sub) for j, sub in enumerate(inner.get(i, [])))
    return out


def _token_map(tx: dict[str, Any], keys: list[str]) -> dict[str, TokenAccount]:
    m = tx["meta"]
    out: dict[str, TokenAccount] = {}
    for b in (m.get("preTokenBalances") or []) + (m.get("postTokenBalances") or []):
        ui = b.get("uiTokenAmount") or {}
        out[keys[b["accountIndex"]]] = TokenAccount(b["mint"], b.get("owner"), b.get("programId"), ui.get("decimals"))
    return out


def _token_amounts(balances: Optional[list[dict[str, Any]]], keys: list[str]) -> dict[str, int]:
    return {keys[b["accountIndex"]]: int(b["uiTokenAmount"]["amount"]) for b in balances or []}


def _trade_events(tx: dict[str, Any]) -> list[dict[str, Any]]:
    """pump.fun TradeEvents from the logs. Layout checked on real 2024 transactions:
    mint(32) sol(u64) tok(u64) is_buy(u8) user(32) ts(i64) vsol(u64) vtok(u64) [rsol rtok]."""
    out: list[dict[str, Any]] = []
    for line in tx["meta"].get("logMessages") or []:
        if not line.startswith("Program data: "):
            continue
        try:
            raw = base64.b64decode(line[14:], validate=True)
        except ValueError:
            continue  # a truncated or foreign log line is not an event; balances still decide
        if raw[:8] != TRADE_EVENT or len(raw) < 113:
            continue
        sol, tok = struct.unpack_from("<QQ", raw, 40)
        ts, vsol, vtok = struct.unpack_from("<qQQ", raw, 89)
        ev = {"mint": b58encode(raw[8:40]), "sol": sol, "tok": tok, "buy": raw[56] == 1,
              "user": b58encode(raw[57:89]), "ts": ts, "vsol": vsol, "vtok": vtok, "rsol": None, "rtok": None}
        if len(raw) >= 129:
            ev["rsol"], ev["rtok"] = struct.unpack_from("<QQ", raw, 113)
        out.append(ev)
    return out


def decode(tx: dict[str, Any]) -> Decoded:
    """Decode a raw (encoding "json") getTransaction result. Raises on a jsonParsed instruction."""
    meta = tx["meta"]
    keys = account_keys(tx)
    pre, post = meta["preBalances"], meta["postBalances"]
    if len(keys) != len(pre):
        raise ValueError("%d keys against %d balances" % (len(keys), len(pre)))
    delta = {k: post[i] - pre[i] for i, k in enumerate(keys) if post[i] != pre[i]}
    fee = meta["fee"]
    ok = meta.get("err") is None
    fee_payer = keys[0]
    header = tx["transaction"]["message"].get("header") or {}
    signers = keys[:header.get("numRequiredSignatures", 1)]
    tokens = _token_map(tx, keys)
    pre_tok = _token_amounts(meta.get("preTokenBalances"), keys)
    post_tok = _token_amounts(meta.get("postTokenBalances"), keys)

    bal = {k: pre[i] for i, k in enumerate(keys)}
    bal[fee_payer] -= fee
    run_tok = dict(pre_tok)
    transfers: list[Transfer] = []
    programs: set[str] = set()

    def owner_of(acct: str) -> Optional[str]:
        t = tokens.get(acct)
        return t.owner if t else None

    def mint_of(acct: str) -> Optional[str]:
        t = tokens.get(acct)
        return t.mint if t else None

    def move_sol(kind: str, src: str, dst: str, amount: int, path: str) -> None:
        bal[src] = bal.get(src, 0) - amount
        bal[dst] = bal.get(dst, 0) + amount
        transfers.append(Transfer(kind, src, dst, amount, path))

    for path, ix in _walk_instructions(tx):
        if "programIdIndex" not in ix:
            raise ValueError("decode() takes encoding json, got a parsed instruction at " + path)
        prog = keys[ix["programIdIndex"]]
        programs.add(prog)
        if not ok:
            continue  # a failed transaction moves nothing but its fee
        if prog not in (SYSTEM, TOKEN, TOKEN22):
            continue
        data = b58decode(ix.get("data") or "")
        acc = [keys[a] for a in ix["accounts"]]
        if prog == SYSTEM and len(data) >= 4:
            tag = struct.unpack_from("<I", data, 0)[0]
            if tag == 2 and len(data) >= 12:  # Transfer
                move_sol("sol_transfer", acc[0], acc[1], struct.unpack_from("<Q", data, 4)[0], path)
            elif tag == 0 and len(data) >= 12:  # CreateAccount
                move_sol("sol_create", acc[0], acc[1], struct.unpack_from("<Q", data, 4)[0], path)
            elif tag == 3:  # CreateAccountWithSeed: base(32), seed len(u64), seed, lamports(u64)...
                seed_len = struct.unpack_from("<Q", data, 36)[0]
                move_sol("sol_create", acc[0], acc[1], struct.unpack_from("<Q", data, 44 + seed_len)[0], path)
            elif tag == 5 and len(data) >= 12:  # WithdrawNonceAccount: nonce account, destination
                move_sol("sol_transfer", acc[0], acc[1], struct.unpack_from("<Q", data, 4)[0], path)
            elif tag == 11 and len(data) >= 12:  # TransferWithSeed: source is acc[0], acc[2] the destination
                move_sol("sol_transfer", acc[0], acc[2], struct.unpack_from("<Q", data, 4)[0], path)
        elif prog in (TOKEN, TOKEN22) and data:
            tag = data[0]
            if tag == 1:  # InitializeAccount: account, mint, owner
                tokens[acc[0]] = TokenAccount(acc[1], acc[2], prog)
            elif tag == 16:  # InitializeAccount2: account, mint; owner in the data
                tokens[acc[0]] = TokenAccount(acc[1], b58encode(data[1:33]), prog)
            elif tag == 18:  # InitializeAccount3: same, without the rent sysvar
                tokens[acc[0]] = TokenAccount(acc[1], b58encode(data[1:33]), prog)
            elif tag in (3, 12) or (tag == 26 and len(data) > 1 and data[1] == 1):
                withheld = 0
                if tag == 3:
                    src, dst, mint, amount = acc[0], acc[1], None, struct.unpack_from("<Q", data, 1)[0]
                elif tag == 12:
                    src, mint, dst, amount = acc[0], acc[1], acc[2], struct.unpack_from("<Q", data, 1)[0]
                else:  # TransferCheckedWithFee: amount(u64) decimals(u8) fee(u64), fee kept on the destination
                    src, mint, dst, amount = acc[0], acc[1], acc[2], struct.unpack_from("<Q", data, 2)[0]
                    withheld = struct.unpack_from("<Q", data, 11)[0]
                mint = mint or mint_of(src) or mint_of(dst)
                transfers.append(Transfer("spl", src, dst, amount, path, mint, owner_of(src), owner_of(dst)))
                run_tok[src] = run_tok.get(src, 0) - amount
                run_tok[dst] = run_tok.get(dst, 0) + amount - withheld
                if mint == WSOL:  # native token transfers carry their lamports with them
                    bal[src] = bal.get(src, 0) - amount
                    bal[dst] = bal.get(dst, 0) + amount
            elif tag in (7, 14):  # MintTo: mint, destination
                amount = struct.unpack_from("<Q", data, 1)[0]
                transfers.append(Transfer("mint", None, acc[1], amount, path, acc[0], None, owner_of(acc[1])))
                run_tok[acc[1]] = run_tok.get(acc[1], 0) + amount
            elif tag in (8, 15):  # Burn: account, mint
                amount = struct.unpack_from("<Q", data, 1)[0]
                transfers.append(Transfer("burn", acc[0], None, amount, path, acc[1], owner_of(acc[0]), None))
                run_tok[acc[0]] = run_tok.get(acc[0], 0) - amount
            elif tag == 9:  # CloseAccount: account, destination, owner. All lamports leave.
                amount = bal.get(acc[0], 0)
                transfers.append(Transfer("close_refund", acc[0], acc[1], amount, path, mint_of(acc[0]),
                                          owner_of(acc[0]), None))
                bal[acc[1]] = bal.get(acc[1], 0) + amount
                bal[acc[0]] = 0
                run_tok[acc[0]] = 0

    residual = {k: post[i] - bal.get(k, 0) for i, k in enumerate(keys) if post[i] != bal.get(k, 0)}
    token_residual = {}
    for acct in set(run_tok) | set(post_tok):
        # Wrapped SOL amounts follow lamports at init and SyncNative, and bal already tracks those.
        d = post_tok.get(acct, 0) - run_tok.get(acct, 0)
        if d and mint_of(acct) != WSOL:
            token_residual[acct] = d

    owners: dict[str, OwnerNet] = {}

    def net_of(owner: str) -> OwnerNet:
        return owners.setdefault(owner, OwnerNet())

    for k, d in delta.items():
        t = tokens.get(k)
        if t is None:
            net_of(k).native += d
        elif t.owner is None:
            net_of(k).native += d  # shortcut: an RPC result without owner is booked on the account itself
    for acct, t in tokens.items():
        if t.owner is None:
            continue
        lam = delta.get(acct, 0)
        tok = post_tok.get(acct, 0) - pre_tok.get(acct, 0)
        n = net_of(t.owner)
        if t.mint == WSOL:
            n.wsol += tok
            n.rent += lam - tok
        else:
            n.rent += lam
            if tok:
                n.tokens[t.mint] = n.tokens.get(t.mint, 0) + tok
    owners = {o: n for o, n in owners.items() if n.sol or n.tokens or o == fee_payer}

    trade_events = _trade_events(tx) if ok else []
    edges, unresolved = _edges(owners, transfers, tokens, fee, fee_payer, residual) if ok else ([], {})
    return Decoded(
        signature=tx["transaction"]["signatures"][0], slot=tx["slot"], block_time=tx.get("blockTime"),
        ok=ok, fee=fee, fee_payer=fee_payer, signers=signers, keys=keys,
        programs=sorted(programs), venues=sorted({VENUES[p] for p in programs if p in VENUES}),
        transfers=transfers, token_accounts=tokens, owners=owners, lamport_delta=delta,
        residual=residual, token_residual=token_residual, conserved=sum(delta.values()) == -fee,
        trade_events=trade_events, edges=edges, unresolved_sol=unresolved)


def _edges(owners: dict[str, OwnerNet], transfers: list[Transfer], tokens: dict[str, TokenAccount],
           fee: int, fee_payer: str, residual: dict[str, int]) -> tuple[list[Edge], dict[str, int]]:
    """Who paid whom, in SOL. Instructions first, then only what the arithmetic forces.

    Works on the owners' nets without the fee: a direct transfer is taken up to what both sides
    still have to explain, and the rest is attributed only when one side has a single member.
    With several payers and several receivers left, the remainder stays unresolved.
    """
    room = {o: n.sol + (fee if o == fee_payer else 0) for o, n in owners.items()}
    room = {o: v for o, v in room.items() if v and o not in JITO_TIP}
    edges: list[Edge] = []

    def holder(addr: Optional[str]) -> Optional[str]:
        t = tokens.get(addr) if addr else None
        return t.owner if t and t.owner else addr

    for t in transfers:
        if t.kind not in ("sol_transfer", "sol_create", "spl", "close_refund"):
            continue
        if t.kind == "spl" and t.mint != WSOL:
            continue
        src, dst = holder(t.src), holder(t.dst)
        if dst in JITO_TIP and src in room:
            room[src] += t.amount
            continue
        if not src or not dst or src == dst or room.get(src, 0) >= 0 or room.get(dst, 0) <= 0:
            continue
        x = min(t.amount, -room[src], room[dst])
        if x <= 0:
            continue
        edges.append(Edge(src, dst, x, ONCHAIN_VERIFIED, "instruction", t.path))
        room[src] += x
        room[dst] -= x

    payers = {o: -v for o, v in room.items() if v < 0}
    receivers = {o: v for o, v in room.items() if v > 0}
    if len(payers) == 1 and receivers:
        src = next(iter(payers))
        for dst, v in sorted(receivers.items()):
            x = min(v, payers[src])
            if x > 0:
                edges.append(Edge(src, dst, x, STRONG_TECHNICAL_INFERENCE, "net_single_payer"))
                room[src] += x
                room[dst] -= x
                payers[src] -= x
    elif len(receivers) == 1 and payers:
        dst = next(iter(receivers))
        for src, v in sorted(payers.items()):
            x = min(v, receivers[dst])
            if x > 0:
                edges.append(Edge(src, dst, x, STRONG_TECHNICAL_INFERENCE, "net_single_receiver"))
                room[src] += x
                room[dst] -= x
                receivers[dst] -= x
    return edges, {o: v for o, v in room.items() if v}


def traded_mints(d: Decoded, owner: str) -> dict[str, int]:
    """Non-WSOL token deltas of an owner in a successful transaction."""
    n = d.owners.get(owner)
    return {m: v for m, v in n.tokens.items() if m != WSOL and v} if n and d.ok else {}


def trade_counterparties(d: Decoded, owner: str) -> set[str]:
    """Who took the other side of an owner's trade: anyone whose balance of a mint it traded moved
    the opposite way. That is the bonding curve or the pool authority, not a recipient of funds."""
    out: set[str] = set()
    for mint, dt in traded_mints(d, owner).items():
        for other, n in d.owners.items():
            if other != owner and n.tokens.get(mint, 0) * dt < 0:
                out.add(other)
    return out


def parsed_transfers(tx: dict[str, Any]) -> list[Transfer]:
    """Second, independent reading: the RPC node's own jsonParsed decoder, for comparison.

    Only for agreement checks on hard transactions. A disagreement with decode() is kept and
    reported, never reconciled by changing either side.
    """
    out: list[Transfer] = []
    for path, ix in _walk_instructions(tx):
        p = ix.get("parsed")
        if not isinstance(p, dict):
            continue
        prog = ix.get("program")
        info, typ = p.get("info") or {}, p.get("type")
        if prog == "system" and typ in ("transfer", "transferWithSeed"):
            out.append(Transfer("sol_transfer", info["source"], info["destination"], int(info["lamports"]), path))
        elif prog == "system" and typ in ("createAccount", "createAccountWithSeed"):
            out.append(Transfer("sol_create", info["source"], info["newAccount"], int(info["lamports"]), path))
        elif prog in ("spl-token", "spl-token-2022"):
            if typ == "transfer":
                out.append(Transfer("spl", info["source"], info["destination"], int(info["amount"]), path))
            elif typ == "transferChecked":
                out.append(Transfer("spl", info["source"], info["destination"],
                                    int(info["tokenAmount"]["amount"]), path, info.get("mint")))
            elif typ in ("mintTo", "mintToChecked"):
                amount = info.get("amount") or info["tokenAmount"]["amount"]
                out.append(Transfer("mint", None, info["account"], int(amount), path, info.get("mint")))
            elif typ in ("burn", "burnChecked"):
                amount = info.get("amount") or info["tokenAmount"]["amount"]
                out.append(Transfer("burn", info["account"], None, int(amount), path, info.get("mint")))
            elif typ == "closeAccount":
                out.append(Transfer("close_refund", info["account"], info["destination"], -1, path))
    return out


def compare_decoders(raw: dict[str, Any], parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Differences between decode() and the node's jsonParsed reading, by instruction path.

    close_refund amounts are not given by jsonParsed (-1 there), so only the accounts are compared.
    """
    a = {(t.path, t.kind): t for t in decode(raw).transfers}
    b = {(t.path, t.kind): t for t in parsed_transfers(parsed)}
    out: list[dict[str, Any]] = []
    for key in sorted(set(a) | set(b)):
        x, y = a.get(key), b.get(key)
        if x is None or y is None:
            out.append({"path": key[0], "kind": key[1], "only_in": "decode" if y is None else "parsed"})
        elif (x.src, x.dst) != (y.src, y.dst) or (y.amount != -1 and x.amount != y.amount):
            out.append({"path": key[0], "kind": key[1], "decode": [x.src, x.dst, x.amount],
                        "parsed": [y.src, y.dst, y.amount]})
    return out
