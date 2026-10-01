# H. Hypotheses: one economic unit, a common execution service, independent traders

| observation | value | A one unit | B execution service | C independent traders |
|---|---|---|---|---|
| sniper always sends to the same exit wallet | 42 % (null 0 %) | expected | expected | not expected |
| exit wallet keeps the same funder | 30 % (null 0 %) | expected | expected (service funder) | weak |
| capital reaches the launch funder | 51 % of events (null 3 %) | expected | expected if the funder is the service's wallet | weak |
| same terminal wallet across events | 36 % (null 2 %) | expected | per client | weak |
| capital reaches a hub | 23 % of branches | possible | possible (client withdrawals) | possible |
| capital reaches the deployer network | 0 % of events (null 0 %) | expected if the deployer is part of the unit | separate deployer networks | not expected |
| capital funds a later launch | 52 % of events (null 29 %) | expected | expected (the service re-funds) | weak |

What would separate A from B is where the capital goes after the funder: to one owner (A) or to several clients (B). The funder's own outflows are not collected in this study.
