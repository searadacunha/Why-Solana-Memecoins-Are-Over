# K. Post-hoc checks (descriptive, added after reading tables B to J)

## 1. Hubs reached (first hub on each path)

131 distinct hubs; touched by two operators or more: 26; SOL reaching hubs 22170, of which through hubs shared by two operators or more 14110.

| hub | operators | primary wallets | direction | SOL on the edge into it | in the frozen tables |
|---|---:|---:|---|---:|---|
| iGdFcQoyR2 | 5 | 6 | up | 28 | yes |
| A3xp8M8swE | 3 | 4 | down | 78 | no |
| jqd63a5wxb | 3 | 3 | down/up | 6 | no |
| 2DEEdv8Hx5 | 2 | 9 | down/up | 7059 | no |
| BfWSJADbWP | 2 | 4 | down/up | 4199 | no |
| FK13gGS8yr | 2 | 5 | down/up | 2372 | no |
| 5A8rJUX82s | 2 | 2 | down | 109 | no |
| EAHyDdCg9S | 2 | 3 | up | 60 | no |
| 4QnqW79Q4S | 2 | 2 | down | 42 | no |
| 35Lopfe9H8 | 2 | 2 | down | 38 | yes |
| 5zEo97KwHH | 2 | 3 | down/up | 26 | no |
| 8G83ekgmB6 | 2 | 2 | down | 19 | no |
| Ek2M9VCNtQ | 2 | 1 | down | 6 | no |
| DFZaXcTj6b | 2 | 1 | down | 6 | no |
| 3FfXZyAVsY | 2 | 1 | down | 6 | no |
| EitseL4jgW | 2 | 1 | down | 6 | no |
| GGCU7sYGLd | 2 | 1 | down | 6 | no |
| 2xv5WhEiG7 | 2 | 1 | down | 6 | no |
| 6vvMpwpBd2 | 2 | 1 | down | 6 | no |
| Ffq77wXpuW | 2 | 1 | down | 6 | no |

## 2. Sensitivity: hubs allowed to join operators (not the plan's rule)

Operator components without hubs (the plan): sizes [7, 5, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]. With hubs: sizes [18, 1, 1, 1, 1, 1, 1].
Leave one shared hub out: the largest component keeps 17 to 18 operators (smallest without 2DEEdv8Hx5).
Operators outside the largest component with hubs: c:8peR5ucxZnSFWY, c:EwFgFSw9KHqVw3, k:20.20+19.92+19, k:21.39+21.26+21, k:21.40+21.14+21, k:22.04+21.96+19.
Hubs joining only through a direct transfer they co-signed as recipient: 106 such hubs, 16 shared by two operators or more; components [14, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]; leaving one of these hubs out keeps 13 to 14 operators in the largest.

## 3. Every edge touching a wallet shared by two operators (non-hub)

| shared wallet | primary | operator | direction | hop | edge | SOL | week |
|---|---|---|---|---:|---|---:|---|
| 27NsskNe | J4C5rKtK | k:21.13+21.0 | up | 1 | 27NsskNe funded J4C5rKtK | 1.0 | 2026-W35 |
| 27NsskNe | 8xxJcwB2 | k:21.13+21.0 | up | 1 | 27NsskNe funded 8xxJcwB2 | 1.0 | 2026-W35 |
| 27NsskNe | 92hhkb9q | k:20.32+19.9 | up | 1 | 27NsskNe funded 92hhkb9q | 1.0 | 2026-W34 |
| 27NsskNe | wopbKaNS | k:21.13+21.0 | down | 1 | wopbKaNS sent to 27NsskNe | 1.0 | 2026-W35 |
| 27NsskNe | wopbKaNS | k:21.13+21.0 | down | 1 | wopbKaNS sent to 27NsskNe | 1289.1 | 2026-W35 |
| 27NsskNe | wopbKaNS | k:21.13+21.0 | down | 1 | wopbKaNS sent to 27NsskNe | 1.0 | 2026-W35 |
| 27NsskNe | BAKRUbZT | k:21.13+21.0 | down | 1 | BAKRUbZT sent to 27NsskNe | 1.0 | 2026-W35 |
| 27NsskNe | BAKRUbZT | k:21.13+21.0 | down | 1 | BAKRUbZT sent to 27NsskNe | 988.3 | 2026-W35 |
| 7a2zhDAJ | vF9GBSqp | c:HxYyavxib9 | down | 3 | LoPQ2pSX sent to 7a2zhDAJ | 26.2 | 2026-W37 |
| 7a2zhDAJ | 67qjEdzL | k:21.13+21.0 | down | 2 | DMbFS7pD sent to 7a2zhDAJ | 2.8 | 2026-W36 |
| 7a2zhDAJ | 67qjEdzL | k:21.13+21.0 | down | 2 | DMbFS7pD sent to 7a2zhDAJ | 2.8 | 2026-W36 |
| 7oobYnBy | vF9GBSqp | c:HxYyavxib9 | down | 1 | vF9GBSqp sent to 7oobYnBy | 1.0 | 2026-W37 |
| 7oobYnBy | 67qjEdzL | k:21.13+21.0 | down | 1 | 67qjEdzL sent to 7oobYnBy | 2.8 | 2026-W36 |
| 8zHcWujH | BRKGcMhX | k:20.68+20.5 | down | 5 | 4d9oHZa2 sent to 8zHcWujH | 28.4 | 2026-W35 |
| 8zHcWujH | Axiwxae6 | c:2YKa6U61fo | down | 4 | DeZFXx4j sent to 8zHcWujH | 4.9 | 2026-W39 |
| AP6c8AS1 | 4aEJJD6D | k:21.59+21.2 | down | 1 | 4aEJJD6D sent to AP6c8AS1 | 4.0 | 2026-W40 |
| AP6c8AS1 | 35Lopfe9 | c:Fb2TAFf2zd | down | 1 | 35Lopfe9 sent to AP6c8AS1 | 4.0 | 2026-W40 |
| AyBdrsDJ | 6PKtd15f | k:21.13+21.0 | up | 1 | AyBdrsDJ funded 6PKtd15f | 0.1 | 2026-W35 |
| AyBdrsDJ | BAKRUbZT | k:21.13+21.0 | down | 1 | BAKRUbZT sent to AyBdrsDJ | 287.9 | 2026-W35 |
| AyBdrsDJ | 44AKqBs4 | k:20.68+20.5 | down | 3 | HtSjejQ8 sent to AyBdrsDJ | 10.0 | 2026-W34 |
| AyBdrsDJ | J4C5rKtK | k:21.13+21.0 | down | 1 | J4C5rKtK sent to AyBdrsDJ | 389.5 | 2026-W35 |
| CS1egm8U | 4aEJJD6D | k:21.59+21.2 | down | 1 | 4aEJJD6D sent to CS1egm8U | 4.0 | 2026-W40 |
| CS1egm8U | 35Lopfe9 | c:Fb2TAFf2zd | down | 1 | 35Lopfe9 sent to CS1egm8U | 4.0 | 2026-W40 |
| CekCebfL | 3fzT6gaf | c:5MSpdabaEo | up | 1 | CekCebfL funded 3fzT6gaf | 1.0 | 2026-W38 |
| CekCebfL | 8E2rmKvu | c:Gug21eQUwm | down | 2 | DRUKt6L9 sent to CekCebfL | 530.0 | 2026-W39 |
| CekCebfL | 8E2rmKvu | c:Gug21eQUwm | down | 2 | DRUKt6L9 sent to CekCebfL | 530.0 | 2026-W39 |
| CrAtVXEZ | Axiwxae6 | c:2YKa6U61fo | down | 2 | DkorT3SS sent to CrAtVXEZ | 5.0 | 2026-W39 |
| CrAtVXEZ | 6KinmsEQ | k:21.13+21.0 | down | 3 | C5PAys2w sent to CrAtVXEZ | 5.0 | 2026-W36 |
| DRUKt6L9 | DjJMVMy3 | c:8uM3AeYfpA | up | 1 | DRUKt6L9 funded DjJMVMy3 | 160.0 | 2026-W39 |
| DRUKt6L9 | 4aEJJD6D | k:21.59+21.2 | up | 1 | DRUKt6L9 funded 4aEJJD6D | 0.2 | 2026-W40 |
| DRUKt6L9 | 8E2rmKvu | c:Gug21eQUwm | down | 1 | 8E2rmKvu sent to DRUKt6L9 | 1.0 | 2026-W39 |
| DRUKt6L9 | 8E2rmKvu | c:Gug21eQUwm | down | 1 | 8E2rmKvu sent to DRUKt6L9 | 682.5 | 2026-W39 |
| ED1oUL2L | vF9GBSqp | c:HxYyavxib9 | down | 1 | vF9GBSqp sent to ED1oUL2L | 1.0 | 2026-W37 |
| ED1oUL2L | 67qjEdzL | k:21.13+21.0 | down | 1 | 67qjEdzL sent to ED1oUL2L | 2.8 | 2026-W36 |
| EcnoSUW5 | vF9GBSqp | c:HxYyavxib9 | down | 1 | vF9GBSqp sent to EcnoSUW5 | 1.0 | 2026-W37 |
| EcnoSUW5 | 67qjEdzL | k:21.13+21.0 | down | 1 | 67qjEdzL sent to EcnoSUW5 | 2.8 | 2026-W36 |
| FEiQigJg | 4aEJJD6D | k:21.59+21.2 | down | 1 | 4aEJJD6D sent to FEiQigJg | 4.0 | 2026-W40 |
| FEiQigJg | 35Lopfe9 | c:Fb2TAFf2zd | down | 1 | 35Lopfe9 sent to FEiQigJg | 4.0 | 2026-W40 |
| FizVVLFL | 4aEJJD6D | k:21.59+21.2 | down | 1 | 4aEJJD6D sent to FizVVLFL | 4.0 | 2026-W40 |
| FizVVLFL | 35Lopfe9 | c:Fb2TAFf2zd | down | 1 | 35Lopfe9 sent to FizVVLFL | 4.0 | 2026-W40 |
| GMVasHNA | 4aEJJD6D | k:21.59+21.2 | down | 1 | 4aEJJD6D sent to GMVasHNA | 4.0 | 2026-W40 |
| GMVasHNA | 35Lopfe9 | c:Fb2TAFf2zd | down | 1 | 35Lopfe9 sent to GMVasHNA | 4.0 | 2026-W40 |
| H9tyeSef | 5pQ9ZVZ2 | k:20.20+20.1 | down | 1 | 5pQ9ZVZ2 sent to H9tyeSef | 2.5 | 2026-W35 |
| H9tyeSef | 6PKtd15f | k:21.13+21.0 | down | 1 | 6PKtd15f sent to H9tyeSef | 3.0 | 2026-W35 |

Wallets that created (genesis funding) primary wallets of two operators or more: BfWSJADb (4 wallets: k:21.13+21.0, k:22.02+21.8), 5zEo97Kw (2 wallets: k:20.32+19.9, k:21.13+21.0), FRT9fNC4 (2 wallets: k:20.24+20.0, k:21.13+21.0), jqd63a5w (2 wallets: c:9TN2NEfg6v, c:HxYyavxib9, k:21.13+21.0), DRUKt6L9 (2 wallets: c:8uM3AeYfpA, k:21.59+21.2), 27NsskNe (3 wallets: k:20.32+19.9, k:21.13+21.0).
Primary wallets created by a hub: 36, by 18 distinct hubs; hubs that created wallets of two operators or more: 4.

## 4. Operator components (plan's rule)

- 7 operator(s), 452 sweeps in the exit sample: c:2YKa6U61fozw1a, c:9TN2NEfg6vfijy, c:HxYyavxib9P1oS, k:20.20+20.18+19, k:20.32+19.97+19, k:20.68+20.51+20, k:21.13+21.08+19
- 5 operator(s), 451 sweeps in the exit sample: c:5MSpdabaEo18hZ, c:8uM3AeYfpA88Z7, c:Fb2TAFf2zdgkf7, c:Gug21eQUwmZio4, k:21.59+21.27+20
- 1 operator(s), 3 sweeps in the exit sample: k:22.02+21.86+21
- 1 operator(s), 4 sweeps in the exit sample: c:8peR5ucxZnSFWY
- 1 operator(s), 135 sweeps in the exit sample: k:22.04+21.96+19
- 1 operator(s), 1 sweeps in the exit sample: k:21.40+21.14+21
- 1 operator(s), 7 sweeps in the exit sample: k:20.24+20.07+19
- 1 operator(s), 12 sweeps in the exit sample: c:BdE3C2tCtCwDi6
- 1 operator(s), 6 sweeps in the exit sample: c:EwFgFSw9KHqVw3
- 1 operator(s), 19 sweeps in the exit sample: k:21.39+21.26+21
- 1 operator(s), 26 sweeps in the exit sample: c:9FJvWMsUwgr7wd
- 1 operator(s), 6 sweeps in the exit sample: k:20.20+19.92+19
- 1 operator(s), 154 sweeps in the exit sample: k:20.80+20.21+19
- 1 operator(s), 4 sweeps in the exit sample: c:YSUcHvAijrKRgS

## 5. Ordered sequences: SOL into a bridge wallet from one operator's path, then SOL out of it to a primary wallet of another operator

| bridge | from operator | in SOL | to wallet | to operator | out SOL | delay (h) | weeks |
|---|---|---:|---|---|---:|---:|---|
| AP6c8AS1 | c:Fb2TAFf2zd | 4.0 | 4aEJJD6D | k:21.59+21.2 | 1.5 | 5.0 | 2026-W40 -> 2026-W40 |
| AyBdrsDJ | k:20.68+20.5 | 10.0 | Dkcuf38G | k:20.32+19.9 | 180.5 | 0.4 | 2026-W34 -> 2026-W34 |
| AyBdrsDJ | k:20.68+20.5 | 10.0 | 6PKtd15f | k:21.13+21.0 | 0.1 | 181.6 | 2026-W34 -> 2026-W35 |
| AyBdrsDJ | k:20.68+20.5 | 10.0 | 6PKtd15f | k:21.13+21.0 | 389.4 | 181.6 | 2026-W34 -> 2026-W35 |
| CS1egm8U | c:Fb2TAFf2zd | 4.0 | 4aEJJD6D | k:21.59+21.2 | 2.6 | 5.0 | 2026-W40 -> 2026-W40 |
| DRUKt6L9 | c:Gug21eQUwm | 1.0 | DjJMVMy3 | c:8uM3AeYfpA | 160.0 | 23.9 | 2026-W39 -> 2026-W39 |
| DRUKt6L9 | c:Gug21eQUwm | 1.0 | 4aEJJD6D | k:21.59+21.2 | 0.2 | 48.5 | 2026-W39 -> 2026-W40 |
| DRUKt6L9 | c:Gug21eQUwm | 682.5 | DjJMVMy3 | c:8uM3AeYfpA | 160.0 | 23.9 | 2026-W39 -> 2026-W39 |
| DRUKt6L9 | c:Gug21eQUwm | 682.5 | 4aEJJD6D | k:21.59+21.2 | 0.2 | 48.5 | 2026-W39 -> 2026-W40 |
| FEiQigJg | c:Fb2TAFf2zd | 4.0 | 4aEJJD6D | k:21.59+21.2 | 2.6 | 5.0 | 2026-W40 -> 2026-W40 |
| FizVVLFL | c:Fb2TAFf2zd | 4.0 | 4aEJJD6D | k:21.59+21.2 | 3.2 | 5.0 | 2026-W40 -> 2026-W40 |
| GMVasHNA | c:Fb2TAFf2zd | 4.0 | 4aEJJD6D | k:21.59+21.2 | 2.2 | 5.0 | 2026-W40 -> 2026-W40 |
| H9tyeSef | k:20.20+20.1 | 2.5 | 6PKtd15f | k:21.13+21.0 | 2.6 | 155.2 | 2026-W35 -> 2026-W35 |

## 6. Hubs that both receive SOL from primary wallets and created primary wallets

| hub | primaries created | their operators | receives from operators | SOL in |
|---|---:|---|---|---:|
| 2DEEdv8Hx5 | 4 | c:9FJvWMsUwg | c:9FJvWMsUwg | 7032 |
| BfWSJADbWP | 4 | k:21.13+21.0, k:22.02+21.8 | k:21.13+21.0, k:22.02+21.8 | 4193 |
| 7KmKKVwmvQ | 5 | k:20.68+20.5 | k:20.68+20.5 | 2852 |
| FK13gGS8yr | 4 | k:21.13+21.0 | c:YSUcHvAijr, k:21.13+21.0 | 2368 |
| C7ovdUckfV | 2 | c:YSUcHvAijr | c:YSUcHvAijr | 1977 |
| 6mC5BXiNwr | 2 | k:21.13+21.0 | k:21.13+21.0 | 1158 |
| 8JrS3J9gvu | 1 | k:20.68+20.5 | k:20.68+20.5 | 258 |
| 52Mw3gkaqo | 1 | c:YSUcHvAijr | c:YSUcHvAijr | 61 |
| 5zEo97KwHH | 2 | k:20.32+19.9, k:21.13+21.0 | k:21.13+21.0 | 25 |
| 5tzFkiKscX | 1 | c:BdE3C2tCtC | k:21.13+21.0 | 5 |
| jqd63a5wxb | 2 | c:9TN2NEfg6v, c:HxYyavxib9, k:21.13+21.0 | c:HxYyavxib9, k:21.13+21.0 | 4 |
| 5VH2sWdKYZ | 1 | k:20.80+20.2 | c:HxYyavxib9 | 2 |

## 7. Does the destination sign the transfer it receives? (first hop of every downstream branch)

| destination | signature | transfers |
|---|---|---:|
| hub | destination signs | 130 |
| hub | destination signs (fee payer) | 23 |
| other | destination signs | 238 |
| other | destination signs (fee payer) | 17 |
