# Second pass on the published case: finds the 15 same-size buyers, written after the first pass showed 9 of them. Kept as run, for the record; run from the repository root.
"""Second pass on the case: the 15 same-size buyers, the deployer, the group's other tokens, common destinations."""
import json, os, sys, datetime as dt, collections
sys.path.insert(0, os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2'))
from forensics_v2.__main__ import client
from forensics_v2.investigations import nine_wallets as N
from forensics_v2 import decode as D
from forensics_v2.trace import history, sol_flows, trips, load_services
c = client(1200)
cv = N.curve_order(c)
SIZE = 2035147973459
ev = cv['events']
group = [e['user'] for e in ev if e['buy'] and e['tok'] == SIZE]
assert len(group) == 15 and set(N.NINE) <= set(group)
six = [w for w in group if w not in N.NINE]
def g(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%m-%d %H:%M:%S') if t else None
hist = {w: history(c, w, max_pages=10) for w in group}
creator = 'ApBXF9f1tgk8FTDbUonjTmGnWBCJRyedKKD26HP3Tp7X'
hc = history(c, creator, max_pages=3)
fl, _ = sol_flows(hc)
print('deployer txs', len(hc.txs), hc.walk.stop, 'first', g(hc.txs[0].block_time))
print(' in', [(x.src[:8], round(x.lamports / 1e9, 4), g(x.ts), x.evidence[:6]) for x in fl if x.dst == creator][:6])
print(' out', [(x.dst[:8], round(x.lamports / 1e9, 4), g(x.ts), x.evidence[:6]) for x in fl if x.src == creator][:8])
print('deployer rank on curve', cv['rank'].get(creator), 'first buy sol', cv['first'].get(creator, {}).get('sol'), 'tok', cv['first'].get(creator, {}).get('tok'))
print('\nthe other six')
for w in six:
    h = hist[w]; f, _ = sol_flows(h)
    ins = [x for x in f if x.dst == w]
    first = ins[0] if ins else None
    print(w[:8], 'txs', len(h.txs), h.walk.stop, 'firstIn', (first.src[:8], first.lamports, g(first.ts), first.evidence[:6]) if first else None, 'nIn', len(ins), 'sell', [(l.lamport_delta.get(w), g(l.block_time), l.slot) for l in h.txs if D.traded_mints(l, w).get(N.MINT, 0) < 0][:1])
# other mints, per wallet of the 15
perm = collections.defaultdict(dict)
for w, h in hist.items():
    for d in h.txs:
        for m, t in D.traded_mints(d, w).items():
            if t > 0:
                perm[m].setdefault(w, []).append((d.slot, t, d.lamport_delta.get(w, 0), d.block_time))
print('\nmints bought by >=2 of the 15')
rows = sorted(perm.items(), key=lambda kv: min(x[0][0] for x in kv[1].values()))
for m, by in rows:
    if len(by) < 2:
        continue
    sizes = collections.Counter(v[0][1] for v in by.values())
    slots = [v[0][0] for v in by.values()]
    print(m[:10], 'n', len(by), 'nineN', sum(1 for w in by if w in N.NINE), 'first', g(min(v[0][3] for v in by.values())), 'slotspan', max(slots) - min(slots), 'topsize', sizes.most_common(1)[0], 'SOL', round(sum(-v[0][2] for v in by.values()) / 1e9, 3))
# common destinations across all 15, excluding protocol and fee-like
svc = load_services()
dest = collections.defaultdict(lambda: collections.defaultdict(int)); tt = {}
for w, h in hist.items():
    f, _ = sol_flows(h)
    for x in f:
        if x.src == w and x.lamports >= 50_000_000 and x.dst not in svc and x.dst != N.CURVE:
            dest[x.dst][w] += x.lamports; tt.setdefault(x.dst, []).append(x.ts)
print('\ncommon destinations (>=0.05 SOL, >=3 wallets)')
for d, by in sorted(dest.items(), key=lambda kv: -sum(kv[1].values())):
    if len(by) >= 3:
        ts = tt[d]
        print(d[:10], 'wallets', len(by), 'nine', sum(1 for w in by if w in N.NINE), 'SOL', round(sum(by.values()) / 1e9, 3), g(min(ts)), g(max(ts)), 'span_s', max(ts) - min(ts))
# PnL and where it ends
pnl = {w: sum(t.realised for t in trips(h.txs, w)) for w, h in hist.items()}
print('\nrealised by wallet SOL', {w[:6]: round(v / 1e9, 3) for w, v in pnl.items()}, 'sum', round(sum(pnl.values()) / 1e9, 3))
print('last activity', sorted({g(h.txs[-1].block_time)[:5] for h in hist.values()}))
print('net', c.net_calls, 'cache', c.cache_hits)
json.dump({'group': group, 'six': six}, open(os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2/forensics_v2/reports/nine_wallets/group15.json'), 'w'), indent=1)
