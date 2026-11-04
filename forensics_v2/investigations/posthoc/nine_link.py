# Does the common wallet connect the two historical collections? Section of the same report. Kept as run, for the record; run from the repository root.
"""Does the common wallet connect the two historical collections? Uses ERG's complete history, already read."""
import json, os, sys, datetime as dt, collections
sys.path.insert(0, os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2'))
from forensics_v2.__main__ import client
from forensics_v2.investigations import nine_wallets as N
from forensics_v2.trace import history, sol_flows
REPO = os.path.expanduser('~/Documents/Crypto/WSMO-forensics-v2')
R = REPO + '/forensics_v2/reports/nine_wallets'
c = client(400)
ERG = 'ERGbjcz9fs95YKvM6zXqvEaicK4VPPo2JwNV8beGKZM4'
def g(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime('%Y-%m-%d %H:%M')
group = set(json.load(open(R + '/group15.json'))['group'])
he = history(c, ERG, token_accounts='none', max_pages=25)
fe, ue = sol_flows(he)
print('ERG', len(he.txs), he.walk.stop, g(he.txs[0].block_time), g(he.txs[-1].block_time), 'unresolved', len(ue))
inn = collections.defaultdict(list); out = collections.defaultdict(list)
for f in fe:
    (inn[f.src] if f.dst == ERG else out[f.dst]).append(f)
e1 = json.load(open(REPO + '/data/trace_h2w6/e1_buyers_h2w6gm6jz.json'))
b = {x['wallet']: x['rank'] for x in e1['buyers']}
e2 = json.load(open(REPO + '/data/trace_h2w6/e2_funding_h2w6gm6jz.json'))
syn = json.load(open(REPO + '/data/trace_h2w6/SYNTHESE_h2w6gm6jz.json'))
s = json.dumps(e2)
chain = [m['de'] for m in syn['chaine_vers_G2Y']['maillons']] + [m['vers'] for m in syn['chaine_vers_G2Y']['maillons']]
print('chain', [x[:8] for x in chain])
fleets = {f.get('nom'): f.get('bailleur') for f in syn['flottes_de_naissance']}
print('fleets', {k: (v or '')[:8] for k, v in fleets.items()})
print('B first buyers touching ERG:', [(a[:8], b[a], 'in', round(sum(x.lamports for x in inn.get(a, [])) / 1e9, 3), 'out', round(sum(x.lamports for x in out.get(a, [])) / 1e9, 3)) for a in b if a in inn or a in out][:12])
for name, a in [('deployer ApBXF9', 'ApBXF9f1tgk8FTDbUonjTmGnWBCJRyedKKD26HP3Tp7X'), ('8RU58K', '8RU58KBpKYz5QRwfmR1QaQ1U75xtvPbLbuLfTN4nqz6v'), ('G9X7F4Jz', 'G9X7F4JzLzbSGMCndiBdWNi5YzZZakmtkdwq7xS3Q3FE'), ('AaZkwhki', 'AaZkwhkiDStDcgrU37XAj9fpNLrD8Erz5PNkdm4k5hjy'), ('G2Y', N.G2Y)]:
    print(name, 'to ERG', round(sum(x.lamports for x in inn.get(a, [])) / 1e9, 3), len(inn.get(a, [])), 'from ERG', round(sum(x.lamports for x in out.get(a, [])) / 1e9, 3), len(out.get(a, [])))
for k in ('G9X7F4Jz', 'AaZkwhki'):
    h = json.load(open(REPO + f'/data/trace_h2w6/e5_hub_{k}.json'))
    print(k, {x: h.get(x) for x in ('n_tx_lues', 'duree_heures', 'tx_par_jour_estime', 'n_destinataires_distincts', 'n_payeurs_distincts')})
g9 = inn.get('G9X7F4JzLzbSGMCndiBdWNi5YzZZakmtkdwq7xS3Q3FE', [])
print('G9X->ERG first', g(g9[0].ts), 'last', g(g9[-1].ts), 'dist', collections.Counter(round(x.lamports / 1e9) for x in g9).most_common(4), 'ev', collections.Counter(x.evidence[:6] for x in g9).most_common(2))
aw = 'AwzntLka'
top = sorted(out, key=lambda a: -sum(x.lamports for x in out[a]))[:3]
print('top out', [(a, round(sum(x.lamports for x in out[a]) / 1e9, 2), len(out[a]), g(out[a][0].ts), g(out[a][-1].ts)) for a in top])
g15in = sorted((x for a in inn if a in group for x in inn[a]), key=lambda x: x.ts)
print('from the 15: n', len(g15in), 'SOL', round(sum(x.lamports for x in g15in) / 1e9, 3))
# what ERG did within an hour after the sweeps
for t0 in sorted({x.ts // 3600 for x in g15in}):
    a = [f for f in fe if f.src == ERG and t0 * 3600 <= (f.ts or 0) < (t0 + 6) * 3600]
    print(' after sweep hour', g(t0 * 3600), 'ERG sends', [(f.dst[:8], round(f.lamports / 1e9, 2)) for f in sorted(a, key=lambda x: -x.lamports)[:4]])
# fleet-level: other wallets paying ERG around the same days, by shared-amount batches
near = [a for a in inn if a not in group and any(1734048000 <= (x.ts or 0) <= 1734480000 for x in inn[a])]
print('other payers of ERG within 13-17 Dec:', len(near), 'SOL', round(sum(x.lamports for a in near for x in inn[a] if 1734048000 <= (x.ts or 0) <= 1734480000) / 1e9, 2))
print('net', c.net_calls)
