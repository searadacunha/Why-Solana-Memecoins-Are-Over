# Post hoc checks quoted in reports/gateway_bursts/README.md. Kept as run, for the record; run from the repository root.
"""Post hoc, descriptive: what O2 and O3 rest on. Written after results, so nothing here is a test."""
import json, os, sys, collections, datetime as dt
sys.path.insert(0, os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2'))
from forensics_v2 import storage
from forensics_v2.investigations.gateway_bursts import outcomes
d = json.loads((storage.data_root() / 'intermediate' / 'gateway_bursts.json').read_text())
B = d['bursts']
print('n_tx==100 (first page full):', sum(1 for b in B for m in b['members'] if m['n_tx'] >= 100), 'of', sum(len(b['members']) for b in B), 'median n_tx', sorted(m['n_tx'] for b in B for m in b['members'])[800])
dest_b = collections.Counter(); mint_b = collections.Counter()
for b in B:
    c = collections.Counter(x for m in b['members'] for x in m['dest'])
    dest_b.update(k for k, v in c.items() if v >= 5)
    mm = collections.defaultdict(set)
    for m in b['members']:
        for y in m['buys']:
            mm[y['mint']].add(m['wallet'])
    mint_b.update(k for k, v in mm.items() if len(v) >= 5)
print('destinations meeting O3 in N bursts, top:', [(k[:8], v) for k, v in dest_b.most_common(10)], 'distinct', len(dest_b))
print('mints meeting O2 in N bursts, top:', [(k[:8], v) for k, v in mint_b.most_common(10)], 'distinct', len(mint_b))
common = {k for k, v in dest_b.items() if v >= 8}
print('destinations in >=8 bursts', len(common), [k for k in list(common)[:6]])
ex = 0
for b in B:
    c = collections.Counter(x for m in b['members'] for x in m['dest'] if x not in common)
    ex += any(v >= 5 for v in c.values())
print('O3 without those', ex, 'of', len(B))
mints_common = {k for k, v in mint_b.items() if v >= 8}
print('mints in >=8 bursts', len(mints_common), [k for k in list(mints_common)[:6]])
ex2 = 0
for b in B:
    mm = collections.defaultdict(set)
    for m in b['members']:
        for y in m['buys']:
            if y['mint'] not in mints_common:
                mm[y['mint']].add(m['wallet'])
    ex2 += any(len(v) >= 5 for v in mm.values())
print('O2 without those', ex2)
o1 = [b for b in B if outcomes(b['members'])['O1']]
for b in o1:
    print('O1 burst', dt.datetime.fromtimestamp(b['t0'], dt.timezone.utc).strftime('%Y-%m-%d %H:%M'), b['lam'], 'size', b['size'], 'fresh', sum(1 for m in b['members'] if m.get('first_sig') == m.get('credit_sig')), 'O', outcomes(b['members']))
amt = collections.Counter(b['lam'] for b in B); print('amounts in sample', amt.most_common(5), 'in O1', collections.Counter(b['lam'] for b in o1).most_common(4))
print('share 2976815600 bursts meeting O1', sum(1 for b in o1 if b['lam'] == 2976815600), 'of', amt[2976815600])
