# E. Capital recycling

## Direct destinations of the primary wallets' outgoing SOL

| destination | transfers | SOL | primary wallets | operators |
|---|---:|---:|---:|---:|
| previously unseen wallet | 242 | 10105.8 | 36 | 19 |
| known hub | 153 | 20320.1 | 40 | 14 |
| sniper, same operator | 8 | 184.0 | 2 | 2 |
| deployer network | 2 | 6.2 | 2 | 1 |
| other known wallet | 2 | 1076.5 | 1 | 1 |
| exit wallet | 1 | 0.4 | 1 | 1 |

## Indirect: a wallet on a downstream path that later funds a frozen launch

Downstream branches 408; reaching a wallet that later funds a sniper or deployer: 119.

| relation | links | SOL | delay median (min) | repeated pairs |
|---|---:|---:|---:|---:|
| same operator's snipers | 115 | 6586.9 | 10 | 11 |
| another operator's snipers | 3 | 120.4 | 1681 | 1 |
| deployer funding | 1 | 1.0 | 8822 | 0 |

Recycling into a population wallet (another funder or collector of the 62): 111.
- BRKGcMhX -> DGPvfk73 funds sniper of 628Yd6Wt (k:22.30+21.16+), 1681 min later
- BRKGcMhX -> DGPvfk73 funds sniper of 628Yd6Wt (k:22.30+21.16+), 1681 min later
- 6KinmsEQ -> 5tzFkiKs funds deployer of Drk3CtZE (c:8QyCAzLox4ai), 8822 min later
- 44AKqBs4 -> Dkcuf38G funds sniper of 2jHstNzq (k:20.32+19.97+), 167 min later

Null D (recipient launches drawn from the frozen funding events of the same ISO week): share to the same operator 0.966 | 0.129 [0.0756, 0.185] | 100 % | 0.0010 | x7.47
