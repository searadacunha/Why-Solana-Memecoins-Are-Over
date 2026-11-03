"""Largest single-recipient gift of each launch of the deployer, as a percentage of a 1,000,000,000 supply. From rows only."""
from __future__ import annotations

from collections import defaultdict

import duckdb

from lib import CREATOR, DATA


def largest_gift_share() -> dict[str, float]:
    con = duckdb.connect(config={"memory_limit": "800MB"})
    src = str(DATA / "rows" / (CREATOR + ".jsonl"))
    rows = con.execute(f"""SELECT DISTINCT sig, mint, dst, raw FROM read_json('{src}', maximum_object_size=8000000, sample_size=20000,
        columns={{kind:'VARCHAR',sig:'VARCHAR',src:'VARCHAR',dst:'VARCHAR',mint:'VARCHAR',raw:'HUGEINT'}})
        WHERE kind='token_transfer' AND src='{CREATOR}' AND dst IS NOT NULL AND dst<>src""").fetchall()
    sells = {x[0] for x in con.execute(f"""SELECT DISTINCT sig FROM read_json('{src}', maximum_object_size=8000000, sample_size=20000,
        columns={{kind:'VARCHAR',sig:'VARCHAR',sol:'HUGEINT'}}) WHERE kind='trade' AND sol>0""").fetchall()}
    per: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for s, m, d, a in rows:
        if s not in sells:
            per[m][d] += a
    return {m: max(v.values()) / 1e15 * 100 for m, v in per.items()}
