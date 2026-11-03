# Top 10 findings and open leads

Ranked by how much each separates the hypotheses. H1: Ansem organised it. H0a: others used his name and he adopted the token later. H0b: a professional operator runs many launches, ANSEM among them. H0c: independent operators and shared tools create links that mean nothing.

## Findings

| # | Finding | Effect on the hypotheses | Evidence |
|---|---|---|---|
| 1 | His wallet has no transaction before the second of his post. It signs nothing for more than six days, and never moves ANSEM before 28 June | Rules out prior contact through this wallet. Against H1 in this form | E01, E02, E15 |
| 2 | No SOL and no signed token transfer from his wallet to the deployer's family, across its full history | The main prediction of H1 fails | `evidence/link_tests_extended.json` |
| 3 | The deployer sends him tokens from 50 launches, 21 of them at 650 M or more after ANSEM, while he asks not to be sent coins | The deployer acts on its own account. For H0a and H0b | E18, E20, `TOKENS.csv` |
| 4 | 635 senders gave his wallet at least 100 M of a token, 23 of them before he adopted any | ANSEM is one of many tributes, chosen later. For H0a | `TOKENS_SENT_TO_ANSEM_WALLET.csv` |
| 5 | The first buy of 5 SOL or more comes 23 seconds after his post at 14:03:08. Only 6.38 SOL bought in the 15 minutes before | No visible accumulation on foreknowledge. Against H1 | E16, E17 |
| 6 | The deployer sold out in 50 seconds for +73.34 SOL and never re-entered | An organiser who knew what was coming would not do this. Against H1 | E11 |
| 7 | Nine wallets, 952 launches, thousands of SOL exchanged, since January 2025 | H0b holds for the launch side | `WALLETS.csv` |
| 8 | Launches follow specific X posts by a median of 31 seconds, and 14 of 23 stated shares match on chain | The operator's trigger is public. Lead on who the operator is, not on Ansem | `evidence/post_vs_launch.json` |
| 9 | 20 fee pushes to his wallet, 73.7 % of the SOL the deployer pushed, against 2 at most for anyone else | **The one fact that leans toward a relationship.** Fees accrue where trading is, but this stays unexplained | `evidence/deployer_cranks.csv` |
| 10 | 17,630 transfers leave his wallet unsigned, through permanent delegates | A naive reading would have found a false return flow to the deployer | E21 |

## Open leads

| # | Lead | Why it matters | How |
|---|---|---|---|
| 1 | Exchange records behind his one-use exit wallets and the family's deposits | The only thing that could prove or kill a common owner on the money side | Legal process only. Not doable here |
| 2 | The 434 cited posts now gone, above all `@Supermanonchain` and `@NikolaiFrandsen` | Does any of them claim the deployer's wallet, or show contact with him? | Wayback CDX and FxTwitter, listed in `TOOLS_REVIEW.md` |
| 3 | Who runs `8wvqvPt1`, which pushed at least 5,132 SOL to his wallet on 28 June | If it serves only him, it is probably his. If many, it is a keeper | Read its other pushes. About 1,000 credits |
| 4 | Finish the family's walks over 2026, above all `FkCcgvCo`, `AvYukzeA` and the exits of `AQd3h5tk` | Closes the hub test, which is partial | About 20,000 credits |
| 5 | Other wallets he may control: the sources of `7oU9nR9V`, the LP wallet `BrV2WXWw`, and old addresses | The tests only cover wallets tied to him | Trace, then re-run `code/ana_31_links_extended.py` |
| 6 | The gap of 21 to 25 June on ANSEM's trades | Completes the re-entry test | About 10,000 credits, heavy automated volume |
| 7 | The largest receivers of his airdrop, such as `5URyNUmhcuWdZiiQrtNdFrSbQPfq72UV2gqQasr9c19Y` with 7,027 SOL of sales in August's count | Friends or side wallets? No SOL returns to his wallet. A third-party post ties this one to a trader's public profit post, unverified | Read their exits |
| 8 | One-slot buyer groups before the run | The August explanation fell (see `PROVENANCE.md`), and what binds these wallets is open. They are routine on this token, so it does not bear on foreknowledge | Compare on other tokens and days |
| 9 | Decode fee settings with the official IDL for the 106 later launches | Completes the fee table | `pump-fun/pump-public-docs`, no credits for logic, some for bodies |
| 10 | `49SecDmF`, the small wallet paid 1.0 SOL by both sides | Thin. Closes the last ordinary shared address | A public post asking for SOL around 1 July would settle it |
