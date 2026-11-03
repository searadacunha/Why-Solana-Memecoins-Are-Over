"""Read X posts by ID through the public embed endpoint and keep what it returned, with a hash.

Usage: col_10_x_posts.py <id or url>... ; follows the reply chain upward. A post that cannot be read is
recorded as unreadable, never dropped. Time comes from the ID itself as well as from the endpoint, and both must agree.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from lib import OUT, utc

STORE = OUT / "x_posts.jsonl"
URL = "https://cdn.syndication.twimg.com/tweet-result?"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def snowflake_ts(i: str) -> int:
    return ((int(i) >> 22) + 1288834974657) // 1000


def known() -> dict[str, dict]:
    if not STORE.exists():
        return {}
    with open(STORE) as f:
        return {r["id"]: r for r in map(json.loads, f)}


def resolve(u: str) -> str | None:
    """Final target of a t.co link, read from its redirect only."""
    class NoFollow(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    try:
        urllib.request.build_opener(NoFollow).open(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=20)
    except urllib.error.HTTPError as e:
        return e.headers.get("location")
    except (urllib.error.URLError, TimeoutError):
        return None
    return None


def fetch(tid: str) -> dict:
    q = urllib.parse.urlencode({"id": tid, "token": "a"})
    base = {"id": tid, "id_time_utc": utc(snowflake_ts(tid)), "fetched_at_unix": int(time.time()), "source": "x-syndication"}
    try:
        with urllib.request.urlopen(urllib.request.Request(URL + q, headers={"User-Agent": UA}), timeout=30) as r:
            raw = r.read()
    except urllib.error.HTTPError as e:
        return {**base, "readable": False, "http": e.code}
    t = json.loads(raw)
    if t.get("__typename") != "Tweet":
        return {**base, "readable": False, "typename": t.get("__typename")}
    links = sorted(set(re.findall(r"https://t\.co/\w+", t.get("text", ""))))
    return {**base, "readable": True, "sha256_raw": hashlib.sha256(raw).hexdigest(),
            "screen_name": (t.get("user") or {}).get("screen_name"), "created_at": t.get("created_at"),
            "text": html.unescape(t.get("text", "")), "in_reply_to": t.get("in_reply_to_status_id_str"),
            "in_reply_to_user": t.get("in_reply_to_screen_name"),
            "quoted": (t.get("quoted_tweet") or {}).get("id_str"),
            "favorites": t.get("favorite_count"), "replies": t.get("conversation_count"),
            "links": {u: resolve(u) for u in links}}


def main() -> None:
    have = known()
    todo = [re.search(r"(\d{15,25})", a).group(1) for a in sys.argv[1:]]
    OUT.mkdir(parents=True, exist_ok=True)
    while todo:
        tid = todo.pop(0)
        if tid in have:
            r = have[tid]
        else:
            r = fetch(tid)
            have[tid] = r
            with open(STORE, "a") as f:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            time.sleep(1.0)
        print(r["id_time_utc"], r.get("screen_name"), "readable" if r["readable"] else "UNREADABLE", "|",
              (r.get("text") or "")[:400].replace("\n", " "), "|", r.get("links"), "| reply_to", r.get("in_reply_to"),
              "| quoted", r.get("quoted"), flush=True)
        for nxt in (r.get("in_reply_to"), r.get("quoted")):
            if nxt and nxt not in have:
                todo.append(nxt)


if __name__ == "__main__":
    main()
