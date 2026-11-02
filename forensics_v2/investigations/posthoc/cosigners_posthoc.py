# Post hoc section of reports/cosigners/README.md. Kept as run, for the record; run from the repository root.
"""Post hoc, descriptive, cached only: separate real payers from disposable signers. Written after the plan's verdicts."""
import json, os, sys, collections
sys.path.insert(0, os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2'))
from forensics_v2.__main__ import client
from forensics_v2 import storage
from forensics_v2.trace import history
from forensics_v2.investigations import cosigners as C
c = client(0)
store = storage.data_root() / 'intermediate' / 'cosigners'
lst = json.loads((store / 'list.json').read_text())
rows = json.loads((store / 'rows.json').read_text())
known = C.known_operator_wallets()
res = {}
payer_hubs = collections.defaultdict(set); dest_hubs = collections.defaultdict(set)
for w, r in rows.items():
    payers = collections.Counter(); fee_self = sweeps_in = n = disposable = out = in_sol = 0
    dests = collections.Counter()
    for s in C.WINDOWS:
        h = history(c, w, t_from=s, t_to=min(s + C.DAY - 1, C.HARD_END - 1), token_accounts='none', max_pages=1)
        for d in h.txs:
            n += 1
            fee_self += d.fee_payer == w
            if not d.ok: continue
            for e in d.edges:
                if e.dst == w:
                    payers[e.src] += e.lamports; payer_hubs[e.src].add(w); in_sol += e.lamports
                elif e.src == w:
                    dests[e.dst] += e.lamports; dest_hubs[e.dst].add(w); out += e.lamports
            disposable += sum(1 for s2 in d.signers if s2 != w and s2 not in d.owners)
    res[w] = {'group': r['group'], 'n': n, 'fee_self': fee_self / n if n else None, 'n_payers': len(payers), 'n_dests': len(dests),
              'known_payers': sum(1 for p in payers if p in known), 'known_payer_sol_share': sum(v for p, v in payers.items() if p in known) / max(1, sum(payers.values())),
              'in_sol': in_sol / 1e9, 'out_sol': out / 1e9, 'top_payer_share': payers.most_common(1)[0][1] / sum(payers.values()) if payers else None,
              'top_dest_share': dests.most_common(1)[0][1] / sum(dests.values()) if dests else None, 'signers_without_balance_change': disposable}
def med(v):
    v = sorted(x for x in v if x is not None); return (v[(len(v) - 1) // 2] + v[len(v) // 2]) / 2 if v else None
multi = {w for w, o in lst['cosigners'].items() if len(o) >= 2}
sets = {'cosigner': [r for r in res.values() if r['group'] == 'cosigner'], 'multi_operator': [res[w] for w in multi if w in res], 'control': [r for r in res.values() if r['group'] == 'control']}
out = {k: {m: med([r[m] for r in v]) for m in ('n', 'fee_self', 'n_payers', 'n_dests', 'known_payers', 'known_payer_sol_share', 'in_sol', 'out_sol', 'top_payer_share', 'top_dest_share', 'signers_without_balance_change')} | {'wallets': len(v)} for k, v in sets.items()}
hubs = set(rows)
out['payers_reaching_2_or_more_of_these_wallets'] = sum(1 for p, s in payer_hubs.items() if len(s) >= 2)
out['payers_total'] = len(payer_hubs)
out['destinations_reached_by_2_or_more'] = sum(1 for p, s in dest_hubs.items() if len(s) >= 2)
out['destinations_total'] = len(dest_hubs)
top = sorted(dest_hubs.items(), key=lambda kv: -len(kv[1]))[:5]
out['top_shared_destination_fanin'] = [len(s) for _, s in top]
out['hub_to_hub_edges'] = sum(1 for p in payer_hubs if p in hubs)
print(json.dumps(out, indent=0)); print('net', c.net_calls)
R = os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2/forensics_v2/reports/cosigners/posthoc.json')
json.dump(out, open(R, 'w'), indent=1)
