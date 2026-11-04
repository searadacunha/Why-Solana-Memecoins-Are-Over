# Figures of reports/nine_wallets/README.md (group15_detail.json). Kept as run, for the record; run from the repository root.
"""Facts for the nine-wallet report, from cached data: the 15 wallets, token by token, and the money."""
import json, os, sys, datetime as dt, collections
sys.path.insert(0, os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2'))
from forensics_v2.__main__ import client
from forensics_v2.investigations import nine_wallets as N
from forensics_v2 import decode as D
from forensics_v2.trace import history, sol_flows, trips, load_services
c = client(200)
R = os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2/forensics_v2/reports/nine_wallets')
group = json.load(open(R + '/group15.json'))['group']
def g(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%d %H:%M:%S') if t else None
svc = load_services()
ERG = 'ERGbjcz9fs95YKvM6zXqvEaicK4VPPo2JwNV8beGKZM4'
out = {'wallets': []}
per = collections.defaultdict(lambda: {'wallets': set(), 'out': 0, 'in': 0, 'buy_t': [], 'sell_t': [], 'slots': [], 'sizes': collections.Counter(), 'venues_buy': collections.Counter(), 'venues_sell': collections.Counter(), 'open': 0, 'signers': collections.Counter()})
credit = []; sweeps = []; other_out = collections.Counter(); inflow_other = collections.Counter()
for w in group:
    h = history(c, w, max_pages=10)
    fl, un = sol_flows(h)
    cred = [f for f in fl if f.dst == w and f.src == N.G2Y]
    assert h.walk.stop == 'genesis' and h.txs[0].signature == cred[0].signature and len(cred) == 1
    credit.append({'wallet': w, 'sig': cred[0].signature, 'lamports': cred[0].lamports, 'utc': g(cred[0].ts), 'slot': cred[0].slot, 'instruction': cred[0].path, 'evidence': cred[0].evidence})
    assert not un
    for f in fl:
        if f.src == w and f.dst == ERG: sweeps.append({'wallet': w, 'sig': f.signature, 'lamports': f.lamports, 'utc': g(f.ts), 'evidence': f.evidence, 'instruction': f.path})
        elif f.src == w: other_out[f.dst] += f.lamports
        elif f.dst == w and f.src != N.G2Y: inflow_other[f.src] += f.lamports
    for t in trips(h.txs, w):
        p = per[t.mint]; p['wallets'].add(w); p['out'] += t.sol_out; p['in'] += t.sol_in; p['open'] += not t.closed
    for d in h.txs:
        for m, tk in D.traded_mints(d, w).items():
            p = per[m]
            if tk > 0:
                p['buy_t'].append(d.block_time); p['slots'].append(d.slot); p['sizes'][tk] += 1
                for v in d.venues: p['venues_buy'][v] += 1
                p['signers'][tuple(d.signers) == (w,)] += 1
            else:
                p['sell_t'].append(d.block_time)
                for v in d.venues: p['venues_sell'][v] += 1
    out['wallets'].append({'wallet': w, 'first_tx_is_credit': True, 'n_tx': len(h.txs), 'last_utc': g(h.txs[-1].block_time), 'lamports_in': sum(f.lamports for f in cred), 'realised_lamports': sum(t.realised for t in trips(h.txs, w)), 'bal_end': None})
tokens = []
for m, p in sorted(per.items(), key=lambda kv: min(kv[1]['buy_t'] or [9e12])):
    tokens.append({'mint': m, 'n_wallets': len(p['wallets']), 'sol_out': p['out'] / 1e9, 'sol_in': p['in'] / 1e9, 'realised': (p['in'] - p['out']) / 1e9, 'first_buy': g(min(p['buy_t'] or [0])), 'buy_span_s': (max(p['buy_t']) - min(p['buy_t'])) if p['buy_t'] else None, 'slot_span': (max(p['slots']) - min(p['slots'])) if p['slots'] else None, 'top_size': p['sizes'].most_common(1)[0] if p['sizes'] else None, 'first_sell': g(min(p['sell_t'] or [0])), 'sell_span_s': (max(p['sell_t']) - min(p['sell_t'])) if p['sell_t'] else None, 'venue_buy': p['venues_buy'].most_common(2), 'venue_sell': p['venues_sell'].most_common(2), 'open_trips': p['open'], 'own_signed': dict((str(k), v) for k, v in p['signers'].items())})
out['credits'] = sorted(credit, key=lambda x: x['slot']); out['sweeps'] = sorted(sweeps, key=lambda x: x['utc']); out['tokens'] = tokens
out['other_outflows_sol'] = {k: v / 1e9 for k, v in other_out.most_common(12)}; out['other_inflows_sol'] = {k: v / 1e9 for k, v in inflow_other.most_common(12)}
ts = [x['utc'] for x in out['credits']]
out['summary'] = {'n': len(group), 'first_credit': ts[0], 'last_credit': ts[-1], 'total_credited_sol': sum(x['lamports'] for x in credit) / 1e9, 'swept_to_common_sol': sum(x['lamports'] for x in sweeps) / 1e9, 'n_sweeps': len(sweeps), 'realised_all_tokens_sol': sum(w['realised_lamports'] for w in out['wallets']) / 1e9, 'other_outflows_total_sol': sum(other_out.values()) / 1e9}
json.dump(out, open(R + '/group15_detail.json', 'w'), indent=1)
print(json.dumps(out['summary'], indent=0)); print('other out', list(out['other_outflows_sol'].items())[:6]); print('other in', out['other_inflows_sol'])
for t in tokens[:14]:
    print(t['mint'][:8], t['n_wallets'], 'out %.2f in %.2f = %+.2f' % (t['sol_out'], t['sol_in'], t['realised']), t['first_buy'][5:], 'spanS', t['buy_span_s'], 'slots', t['slot_span'], 'size', t['top_size'], 'sellSpanS', t['sell_span_s'], 'buy', t['venue_buy'][:1], 'sell', t['venue_sell'][:1], 'open', t['open_trips'])
print('sweep times', sorted({x['utc'][:13] for x in sweeps}), 'net', c.net_calls)
ev = N.curve_order(c)
print('curve buyers ranks of 15', sorted(ev['rank'][w] for w in group))
print('curve first buys <= rank40 share of A', [ev['rank'].get(w) for w in group if ev['rank'].get(w, 999) <= 40])
print('creator rank', ev['rank'].get('ApBXF9f1tgk8FTDbUonjTmGnWBCJRyedKKD26HP3Tp7X'))
