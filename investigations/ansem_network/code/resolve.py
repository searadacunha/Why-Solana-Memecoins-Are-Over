"""Full addresses from prefixes, read from walked rows only. An address is never completed by hand."""
from __future__ import annotations

import sys

import duckdb

from lib import DATA


def full(prefixes: list[str]) -> dict[str, list[str]]:
    con = duckdb.connect(config={"memory_limit": "800MB"})
    src = str(DATA / "rows" / "*.jsonl")
    con.execute(f"""CREATE TABLE a AS SELECT DISTINCT unnest([src,dst]) x FROM read_json('{src}', union_by_name=true,
        maximum_object_size=8000000, sample_size=20000, columns={{src:'VARCHAR',dst:'VARCHAR'}})""")
    return {p: [r[0] for r in con.execute("SELECT x FROM a WHERE x LIKE ?", [p + "%"]).fetchall()] for p in prefixes}


if __name__ == "__main__":
    for k, v in full(sys.argv[1:]).items():
        print(k, v)
