"""One wallet inside a UTC window. Usage: col_06_windows.py <addr> <start> <end> <pages> <credit limit>"""
from __future__ import annotations

import calendar
import sys
import time

from flows import stream
from lib import client, utc


def ts(s: str) -> int:
    return calendar.timegm(time.strptime(s, "%Y-%m-%d %H:%M:%S"))


c = client(run_limit=int(sys.argv[5]))
r = stream(c, sys.argv[1], int(sys.argv[4]), ts(sys.argv[2]), ts(sys.argv[3]))
print(sys.argv[1][:10], "pages", r["pages"], "txs", r["txs"], "done", r["done"], "until", utc(r["last_ts"]), "total", c.budget.used())
