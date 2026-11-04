"""The tracer on a small invented world: where it goes, and where it says it stops."""
from forensics_v2 import decode as D
from forensics_v2.rpc import BudgetExhausted, SigWalk
from forensics_v2.trace import findings, render, trace

from .test_decode import A, B, C, E, SYS, mk, sys_transfer

SERVICE = "S" * 32
HUB = "H" * 32


def pay(src, dst, lamports, sig, slot):
    k = [src, dst, SYS]
    t = mk(k, [10**12, 0, 1], [10**12 - 5000 - lamports, lamports, 1], [sys_transfer(k, src, dst, lamports)])
    t["transaction"]["signatures"] = [sig]
    t["slot"] = slot
    return t


class FakeClient:
    """Answers history_txs from a table. An address absent from it is a wallet with no history."""

    def __init__(self, world, truncated=(), broke=()):
        self.world, self.truncated, self.broke = world, truncated, broke
        self.asked = []

    def history_txs(self, addr, t_from=None, t_to=None, token_accounts="balanceChanged", max_pages=20):
        self.asked.append(addr)
        if addr in self.broke:
            raise BudgetExhausted("no credit left")
        txs = [t for t in self.world if addr in t["transaction"]["message"]["accountKeys"]]
        sigs = [{"signature": t["transaction"]["signatures"][0], "slot": t["slot"], "blockTime": t["blockTime"]}
                for t in reversed(txs)]
        if addr in self.truncated:
            return txs, SigWalk(addr, sigs, False, "max_pages", max_pages)
        return txs, SigWalk(addr, sigs, True, "genesis", 1)


WORLD = [pay(SERVICE, A, 5 * 10**9, "fund", 1), pay(A, B, 2 * 10**9, "out1", 2), pay(A, C, 1 * 10**9, "out2", 3),
         pay(C, A, 10**8, "back", 4), pay(B, E, 10**9, "next", 5)]


def test_both_directions_with_signatures_and_evidence():
    g = trace(FakeClient(WORLD), A, "both", hops=1, services={SERVICE: {"name": "svc"}})
    edges = {(e["src"], e["dst"]): e for e in g.edges}
    assert edges[(SERVICE, A)]["signature"] == "fund" and edges[(SERVICE, A)]["evidence"] == D.ONCHAIN_VERIFIED
    assert edges[(SERVICE, A)]["lamports"] == 5 * 10**9 and edges[(SERVICE, A)]["instruction"] == "0"
    assert (A, B) in edges and (A, C) in edges and (C, A) in edges
    assert g.nodes[A]["coverage"]["reached_genesis"] and g.nodes[A]["coverage"]["first_observable_is_first_activity"]


def test_distinct_transfers_in_one_transaction_survive_graph_deduplication():
    k = [A, B, SYS]
    tx = mk(k, [100_000, 0, 1], [93_800, 1200, 1],
            [sys_transfer(k, A, B, 700), sys_transfer(k, A, B, 500)])
    # Read the same transaction from both endpoints and directions. Keep each
    # instruction once, rather than retaining only the first A -> B payment.
    g = trace(FakeClient([tx]), A, "both", hops=1, min_lamports=1, services={})
    assert [(e["instruction"], e["lamports"]) for e in g.edges] == [("0", 700), ("1", 500)]
    assert sum(e["lamports"] for e in g.edges) == 1200


def test_a_service_ends_the_path_and_says_why():
    c = FakeClient(WORLD)
    g = trace(c, A, "back", hops=2, services={SERVICE: {"name": "svc"}})
    assert SERVICE not in c.asked  # its internal ledger is not on chain: nothing is read past it
    assert any(s["address"] == SERVICE and s["reason"] == "service_boundary" for s in g.stops)


def test_hop_limit_and_structure():
    g = trace(FakeClient(WORLD), A, "forward", hops=1, services={})
    assert (B, E) in {(e["src"], e["dst"]) for e in g.edges}  # read while expanding B
    assert any(s["address"] == B and s["reason"] == "hop_limit" for s in g.stops)
    f = findings(g)
    assert f["returns"] == [tuple(sorted((A, C)))] and A in f["shared_sources"]
    assert "does not show that two wallets have the same owner" in render(g)


def test_truncated_history_is_said_and_not_expanded():
    c = FakeClient(WORLD, truncated={HUB, A})
    g = trace(c, A, "forward", hops=3, services={})
    assert any(s["address"] == A and s["reason"] == "history_truncated" for s in g.stops)
    assert c.asked == [A] and not g.nodes[A]["coverage"]["reached_genesis"]


def test_out_of_credit_gives_a_partial_report_that_says_so():
    g = trace(FakeClient(WORLD, broke={B}), A, "forward", hops=1, services={})
    assert g.budget_hit and any(s["address"] == B and s["reason"] == "credit_budget" for s in g.stops)
    assert "partial" in render(g)
    assert (A, B) in {(e["src"], e["dst"]) for e in g.edges}


def test_small_payments_and_pruned_branches_are_counted():
    many = [pay(A, chr(0x41 + i) * 31 + "Z", (i + 1) * 10**8, "m%d" % i, 10 + i) for i in range(6)]
    g = trace(FakeClient(many), A, "forward", hops=1, min_lamports=3 * 10**8, max_branches=2, services={})
    assert min(e["lamports"] for e in g.edges) >= 3 * 10**8
    pruned = [s for s in g.stops if s["reason"] == "branches_pruned"]
    assert pruned[0]["dropped"] == 2 and pruned[0]["lamports_dropped"] == 7 * 10**8
