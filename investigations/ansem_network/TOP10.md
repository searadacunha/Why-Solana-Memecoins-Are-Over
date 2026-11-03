# Top 10 findings and open leads

Ranked by how much each separates the hypotheses. H1: Ansem organised it. H0a: others used his name and he took the token up later. H0b: a professional operator runs many launches, ANSEM among them. H0c: independent operators and shared tools create links that mean nothing. Items marked (X) are exploratory: tests added after seeing data.

## Findings

| # | Finding | Effect on the hypotheses | Evidence |
|---|---|---|---|
| 1 | His published wallet has no transaction before the second of his post, signs nothing for more than six days, and does not move ANSEM before 28 June | No on-chain contact through this wallet before launch. Says nothing on other wallets or off-chain contact | E01, E02, E15 |
| 2 | No direct SOL either way between the six wallets tied to him and the nine family wallets, and no token transfer signed by his wallet to them (X) | A direct money link is absent where it is read in full. Indirect paths are only partly tested | `evidence/link_tests_extended.json` |
| 3 | The deployer sends him tokens from 75 mints, and 21 of its own launches give him 650 M or more after ANSEM, 20 of them after "dont send it to my wallet" (X) | The deployer does not follow his public request. Whether it heeds a private one is not visible | E18, E20, `evidence/followups.json` |
| 4 | 176 gifts of 650 M or more go to 111 recipients. He gets 25, the next wallet 7 (X) | Gifts are a general method of this deployer. He is still its largest recipient, see 9 | `evidence/followups.json` |
| 5 | The first buy of 5 SOL or more after his post comes 23 seconds later. Sellers out-take buyers in the 15 minutes before (X) | No visible accumulation ahead of it. The post names no token, so why this token ran is not fully explained | E16, E17, `evidence/numbers.json` |
| 6 | Nine wallets, at least 952 launches, thousands of SOL exchanged, since at least January 2025 | R3 holds on the launch side. Fits H0b | `WALLETS.csv` |
| 7 | 635 senders gave his wallet at least 100 M of a token. At least 6 of the 634 others are tied to the deployer, and most were never read (X) | Gifts were common. Not an independent control, so it does not separate H0a from a wider single operator | `TOKENS_SENT_TO_ANSEM_WALLET.csv` |
| 8 | Launches follow specific linked X posts by a median of 31 seconds, and 14 of 23 stated shares match on chain (X). Handles in links are not verified as authors | Lead on how the operator chooses launches. Not on Ansem: 0 of those posts are his | `evidence/post_vs_launch.json` |
| 9 | The deployer favours his wallet by every count, including 20 fee pushes against 2 at most for anyone else (X) | **Leans toward a relationship or toward courting one. Unexplained** | `evidence/followups.json`, `evidence/deployer_cranks.csv` |
| 10 | 17,630 transfers leave his wallet unsigned, across 36 mints that all have a permanent delegate | A naive reading would find a false return flow to the deployer | E21, `evidence/followups.json` |

## Open leads

| # | Lead | Why it matters | How |
|---|---|---|---|
| 1 | Exchange records behind the short-lived wallets that receive from `GV6UUmNx`, and the family's deposits | The only thing that could prove or kill a common owner on the money side | Legal process only. Not doable here |
| 2 | The 414 cited posts that cannot be read, above all under the handles `@Supermanonchain` and `@NikolaiFrandsen` | Does any of them claim the deployer's wallet, or show contact with him? | Wayback CDX and FxTwitter, listed in `TOOLS_REVIEW.md` |
| 3 | Finish the family's walks over 2026, the ten wallets of 21:01:38, and the exits of `AQd3h5tk` | Closes the hub test, which is partial | About 20,000 credits |
| 4 | Other wallets he may control: the sources of `7oU9nR9V`, `BrV2WXWw`, old addresses | The tests only cover wallets tied to him | Trace, then re-run `code/ana_31_links_extended.py` |
| 5 | Classify `BY4StcU9` | It funds the deployer first and ends 12 of 15 chains of the 13:58:54 group in the August note. Service or link? | Larger sample and exchange lists in `TOOLS_REVIEW.md` |
| 6 | Walk the 13:58:54 group and the comparison senders | Tests H0c against one operator, and whether the group ties to anyone here | About 5,000 credits |
| 7 | Classify `BrV2WXWw`'s 280 transactions touching ANSEM | Says whether wallets tied to him sold or only provided liquidity | Decode Meteora events, `TOOLS_REVIEW.md` |
| 8 | Who controls the largest receivers of the 28 June transfers, such as `5URyNUmhcuWdZiiQrtNdFrSbQPfq72UV2gqQasr9c19Y` | No SOL from them reaches `GV6UUmNx`. Their exits are not read | Read their exits |
| 9 | Who runs `8wvqvPt1` | A sample shows two recipients, 200 pushes to him and 31 to another wallet. Not classified | About 1,000 credits |
| 10 | The gap of 21 to 25 June on ANSEM's trades, and fee settings for the 106 later launches | Completes two tables | About 10,000 credits |
