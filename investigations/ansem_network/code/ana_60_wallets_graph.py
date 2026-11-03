"""WALLETS.csv and graph.html from walked rows. No network. Every full address here was printed by a query first."""
from __future__ import annotations

import csv
import json

import duckdb

from ana_30_links import DEPLOYER_SIDE, EARLY, GV, SIDE_WALLETS
from lib import DATA, MINT, OUT, sol, utc

Y = DEPLOYER_SIDE[0]
FAMILY_HUBS = ["AQd3h5tkbdhTiWv7WmiCbm8uwjYi8vTBbMzEtAGtf1T5", "3CdoiTcGfGJPzMJLEFkiCSK3xqjb2u7q7dUHwAsxtrjr", "CUHzepW8KDN9DPvVCfMx6U7QePzwS2ybvG9VRfNUyZRg",
               "78cYfp9LY7GVvWbDxNL5hd4KrZV7ymnGbsiQHoNyqUqf", "D1iQkE4kQamiQToRUyf5byVdx8tQs6wEQxtsujX6qVZX", "6RKXDtfLnBeqDg2AWNoL2bHoU1vTQyjMMaJZM93AGWwq",
               "9o6dSoZjui8BCDH7NFAryq6QyVSffgGtGuEkH1tNPNQY", "FZEFKLaBSjQ4XaxuLnGWdzxpkujt4MxVjdi7z34NyLbA"]
ANSEM_SIDE = [GV, "7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM", "BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG",
              "H3t5AYjF4ukuZ1HL2WCQqtSucRWWSZSoaiwYoWeshKPJ", "EvktFyjtaToEGWnKVSJnwJacDvFBddzrxtUmiN795k8D", "2YPypQAQkFFtmwNgEcmnyqe2EJTThzoMTeUuMYmYcPiT"]
OTHERS = ["7ZV54HcwtzRhZSEPskT8ox5hn9yNocK9xpe4BQXoziaP", "GeBJSHK4WsGrz2HRvTbqvWGx4JRMpHfJG2ikzrYBDuwR", "GLC6w9gud93rW7XhFU2QH2eS9Z1qtu8umSXK7BwuA8oe",
          "2xpKBkzBoAretBBsJYmhzouZR1WZuZFuT6jwoRSFz8Ed", "8wvqvPt1DDdjdghpMpp7ueQFUL5Js5zux4pPeRFXWteB", "DiDDYQpUrWNcaM5AwxkoWJ7VAjBuZyg25Jkvsa9ZosQB",
          "EnNEiTdV9g2Yau2pHipMvxjjrrMtkECG8Hj8a9WqXGzw", "AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm", "Dt4gYgAUts6puim6yj4m874V5TuGUGFyZVv4RNpFvUkY",
          "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq"]
SERVICES = {"9obNtb5GyUegcs3a1CbBkLuc5hEWynWfJC6gjz5uWQkE": "High-volume hot wallet, 15,861 SOL, not labelled",
            "4NyK1AdJBNbgaJ9EsKz3J4rfeHsuYdjkTPg3JaNdLeFw": "High-volume hot wallet, 17,873 SOL, not labelled",
            "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LGFJ8N4dK3WjS": "High-volume hot wallet, 1,192 SOL, not labelled",
            "2snHHreXbpJ7UwZxPe37gnUNf7Wx7wv6UKDSR2JckKuS": "Service by the plan's test: 537 counterparties in its first 1,000 transactions",
            "BY4StcU9Y2BpgH8quZzorg31EGE4L1rjomN8FNsCBEcx": "Labelled HTX in the author's August notes, not verified on chain",
            "FpwQQhQQoEaVu3WU2qZMfF1hx48YyfwsLoRgXG83E99Q": "High-volume hot wallet, 17,690 SOL, not labelled",
            "5F1seMKUqSNhv45f6FhB2cFmgJbk8U1avJw7M6TexUq1": "High-volume hot wallet, 1,267 SOL, not labelled",
            "G2YxRa6wt1qePMwfJzdXZG62ej4qaTC7YURzuh2Lwd3t": "ChangeNOW gateway, public attribution in forensics_v2",
            "GMCJvYGf5Ex2ARiMquaBDqU6iKM8uiEQkB8jCnoNfHpC": "Pool, owned by the GoonFi program",
            "4rJggoVMajEUtipev1XhSMjESYk8Zibz6CDHPtUe1mem": "Pool, owned by the GoonFi program",
            "8FnX3xo2yYw3EUE6w3nQA4GfXGS9wpK6oj3veJpbFzLo": "Pool, owned by the BisonFi program",
            "uxtoRPdPjRekYmxs1uUqVRZWh38iqonc9KgPuZXPeSY": "Fee account of the Uxento launch tool (name inferred from its metadata host)"}
ROLE = {Y: "Deployer of ANSEM and of 839 launches", GV: "Wallet Ansem links in his own post",
        "7oU9nR9VEvFPwvp2PpXo2LQc6A92QRhcUTwhLWT7MsDM": "Receives 491 M ANSEM from GV6UUmNx", "BrV2WXWw5wU9pca4Nu4FJLhLU5cAbrkmLfXQmYm3ZZJG": "Receives 5,148 SOL from GV6UUmNx, then provides liquidity on Meteora",
        "H3t5AYjF4ukuZ1HL2WCQqtSucRWWSZSoaiwYoWeshKPJ": "One-use hop, 3,000 SOL", "EvktFyjtaToEGWnKVSJnwJacDvFBddzrxtUmiN795k8D": "One-use hop, 2,200 SOL", "2YPypQAQkFFtmwNgEcmnyqe2EJTThzoMTeUuMYmYcPiT": "One-use hop, 1,333 SOL",
        "AVAZvHLR2PcWpDf8BXY4rVxNHYRBytycHkcB5z5QNXYm": "Kolscan calls it Ansem. He denies it", "Dt4gYgAUts6puim6yj4m874V5TuGUGFyZVv4RNpFvUkY": "Received the first Black Bull's 400 M tokens and fees",
        "9ryBR3SnxgGPhWsKvsfxuNHUCTt6tSpLe8wrKCShXLaq": "Bot: last curve buy and migration in the creation slot", "8wvqvPt1DDdjdghpMpp7ueQFUL5Js5zux4pPeRFXWteB": "Pushed 5,132 SOL of fees to GV6UUmNx on 28 June, owner unknown",
        "DiDDYQpUrWNcaM5AwxkoWJ7VAjBuZyg25Jkvsa9ZosQB": "Pushes fees, owner unknown", "EnNEiTdV9g2Yau2pHipMvxjjrrMtkECG8Hj8a9WqXGzw": "Pushes fees, owner unknown",
        "7ZV54HcwtzRhZSEPskT8ox5hn9yNocK9xpe4BQXoziaP": "Other deployer: 300 M of its token to GV6UUmNx at 21:02:21", "GeBJSHK4WsGrz2HRvTbqvWGx4JRMpHfJG2ikzrYBDuwR": "Other deployer: 20 mints gifted to GV6UUmNx",
        "GLC6w9gud93rW7XhFU2QH2eS9Z1qtu8umSXK7BwuA8oe": "Other sender: 29 mints gifted to GV6UUmNx", "2xpKBkzBoAretBBsJYmhzouZR1WZuZFuT6jwoRSFz8Ed": "Other deployer: 17 mints gifted to GV6UUmNx"}
GROUPS = [("family", "Deployer family", DEPLOYER_SIDE + FAMILY_HUBS), ("ansem", "Ansem wallet and exits", ANSEM_SIDE), ("side", "Served by the Ansem wallet on 28 June", SIDE_WALLETS),
          ("early", "Early holders and first buyers", EARLY), ("other", "Others: other senders, fee pushers, denied wallet", OTHERS), ("service", "Services and pools", list(SERVICES))]
TOKENS = ["9cRCn9rGT8V2imeM2BaKs13yhMEais3ruM3rPvTGpump"]


def main() -> None:
    con = duckdb.connect(config={"memory_limit": "1200MB", "threads": 2})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE r AS SELECT DISTINCT kind, sig, ts, src, dst, lamports, wallet FROM read_json('{src}', union_by_name=true, maximum_object_size=8000000, sample_size=20000,
        columns={{wallet:'VARCHAR',kind:'VARCHAR',sig:'VARCHAR',ts:'BIGINT',src:'VARCHAR',dst:'VARCHAR',lamports:'HUGEINT'}}) WHERE kind='sol'""")
    group_of = {a: g for g, _, members in GROUPS for a in members}
    con.execute("CREATE TABLE n AS SELECT unnest(?::VARCHAR[]) a", [list(group_of)])
    edges = []
    for s, d, c, lam, t0, t1, sig in con.execute("""SELECT src, dst, count(DISTINCT sig), sum(DISTINCT_L)::DOUBLE, min(ts), max(ts), min(sig) FROM
        (SELECT DISTINCT sig, src, dst, ts, lamports AS DISTINCT_L FROM r WHERE src IN (SELECT a FROM n) AND dst IN (SELECT a FROM n) AND lamports>=10000000)
        GROUP BY 1,2 HAVING sum(DISTINCT_L)>=500000000""").fetchall():
        edges.append({"s": s, "t": d, "kind": "sol", "sol": round(lam / 1e9, 3), "count": c, "t0": t0, "t1": t1, "sig": sig, "label": "SOL"})

    rows = list(csv.DictReader(open(OUT.parent / "TOKENS.csv")))
    mine = [r for r in rows if r["creator_wallet"] == Y]
    tok = sorted((r for r in mine if float(r["gift_to_ansem_wallet"]) >= 6e8), key=lambda r: r["created_utc"])
    first = next(r for r in mine if r["mint"].startswith("DQrHfTbn"))
    picks = [first] + tok
    token_nodes = []
    for r in picks:
        token_nodes.append({"id": r["mint"], "group": "token", "label": (r["symbol"] or "?")[:12], "role": "%s, created %s, dev buy %.1f SOL" % (r["name"], r["created_utc"], float(r["dev_buy_sol"]))})
        ts = int(__import__("calendar").timegm(__import__("time").strptime(r["created_utc"], "%Y-%m-%d %H:%M:%S")))
        edges.append({"s": Y, "t": r["mint"], "kind": "create", "sol": float(r["dev_buy_sol"]), "count": 1, "t0": ts, "t1": ts, "sig": r["create_signature"], "label": "created and bought"})
        g = float(r["gift_to_ansem_wallet"])
        if g > 0:
            edges.append({"s": r["mint"], "t": GV, "kind": "gift", "tokens": g, "count": 1, "t0": ts, "t1": ts, "sig": r["create_signature"], "label": "%.0f M tokens given, not signed by the receiver" % (g / 1e6)})
    edges.append({"s": first["mint"], "t": "Dt4gYgAUts6puim6yj4m874V5TuGUGFyZVv4RNpFvUkY", "kind": "gift", "tokens": 4e8, "count": 1, "t0": 1781624750, "t1": 1781624793, "sig": first["create_signature"], "label": "400 M tokens given"})
    edges.append({"s": MINT, "t": GV, "kind": "fee", "sol": 966.64, "count": 15, "t0": 1781644260, "t1": 1782683048, "sig": "see EVIDENCE_LEDGER.csv E13", "label": "creator fees of ANSEM until 28 June"})

    # wallets table
    ck = DATA / "checkpoints" / "stream"
    with open(OUT.parent / "WALLETS.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["address", "group", "role", "history_read", "first_seen_utc", "first_sol_from", "sol_in", "sol_out", "largest_destination", "largest_destination_sol", "evidence_level"])
        for g, name, members in GROUPS:
            for a in members:
                hist = "not walked"
                for p in list(ck.glob(a + "_*.json")):
                    st = json.loads(p.read_text())
                    first_walk = DATA / "checkpoints" / "gtfa" / (a + "_start_end_balanceChanged.jsonl")
                    extra = sum(len(json.loads(x)["sigs"]) for x in open(first_walk)) if first_walk.exists() else 0
                    hist = ("complete" if st["done"] else "capped") + ", %d tx" % (st["txs"] + extra)
                row = con.execute("SELECT min(ts), arg_min(src, ts) FILTER (WHERE dst=?), sum(lamports) FILTER (WHERE dst=?)::DOUBLE, sum(lamports) FILTER (WHERE src=?)::DOUBLE FROM (SELECT DISTINCT sig,src,dst,ts,lamports FROM r WHERE wallet=?)", [a, a, a, a]).fetchone()
                top = con.execute("SELECT dst, sum(lamports)::DOUBLE s FROM (SELECT DISTINCT sig,src,dst,lamports FROM r WHERE wallet=? AND src=?) GROUP BY 1 ORDER BY s DESC LIMIT 1", [a, a]).fetchone()
                lvl = {"family": "R3 same financial network, each edge has a signature", "ansem": "Self-claimed" if a == GV else "Direct transfers from the self-claimed wallet; ownership inferred, not claimed",
                       "side": "Received tokens from the self-claimed wallet; no ownership claim", "early": "Trader on the token; no link found", "other": "See role", "service": "Stop point, not a link"}[g]
                role = ROLE.get(a) or SERVICES.get(a) or {"family": "Exchanges SOL with the deployer's side", "side": "Received ANSEM signed by GV6UUmNx", "early": "Large early holder or buyer"}.get(g, "")
                w.writerow([a, name, role, hist, utc(row[0]), row[1] or "", sol(int(row[2] or 0)), sol(int(row[3] or 0)), top[0] if top else "", sol(int(top[1])) if top else "", lvl])

    nodes = [{"id": a, "group": g, "label": ("Deployer " if a == Y else "Ansem wallet " if a == GV else "") + a[:6], "role": ROLE.get(a) or SERVICES.get(a) or ""} for a, g in group_of.items()]
    touched = {e["s"] for e in edges} | {e["t"] for e in edges}
    nodes = [n for n in nodes if n["id"] in touched or n["id"] in (Y, GV)] + token_nodes
    data = {"nodes": nodes, "edges": edges, "groups": [(g, n) for g, n, _ in GROUPS] + [("token", "Tokens: the first Black Bull and every launch giving 600 M or more to the Ansem wallet")]}
    (OUT / "graph.json").write_text(json.dumps(data, indent=0, ensure_ascii=False))
    html = open(OUT.parent / "code" / "graph_template.html").read().replace("/*DATA*/null", json.dumps(data, ensure_ascii=False))
    (OUT.parent / "graph.html").write_text(html)
    print("nodes", len(nodes), "edges", len(edges), "cross edges family-ansem SOL:", sum(1 for e in edges if e["kind"] == "sol" and group_of.get(e["s"]) in ("family", "ansem") and group_of.get(e["t"]) in ("family", "ansem") and group_of[e["s"]] != group_of[e["t"]]))


if __name__ == "__main__":
    main()
