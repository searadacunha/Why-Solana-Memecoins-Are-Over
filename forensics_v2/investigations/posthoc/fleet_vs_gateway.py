"""The published fleet against the gateway's ordinary traffic. Local data only: the frozen study's list of public payouts, and the burst sample.

python -m forensics_v2.investigations.posthoc.fleet_vs_gateway <burst sample json>
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from ..gateway_bursts import MIN_MEMBERS, SLOT_SPAN, outcomes
from ..trades_2024 import STUDY

OUT = Path(__file__).resolve().parents[2] / "reports" / "fleet_structure"
FEE_PCT_MILLI, FEE_FIXED = (
    6,
    5_184_400,
)  # read from the amounts: payout = requested x 0.994 - 0.0051844 SOL, requested in hundredths of a SOL
SPAN_S, FLEET_LAM, FLEET_N = 380, 2_976_815_600, 15


def requested(lam: int):
    """The round request behind a payout under the fee line, or None."""
    x = (lam + FEE_FIXED) * 1000
    if x % (1000 - FEE_PCT_MILLI):
        return None
    x //= 1000 - FEE_PCT_MILLI
    return x if x % 10_000_000 == 0 else None


def day(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d")


def strict_mints(members):
    by = defaultdict(list)
    for m in members:
        for b in m["buys"]:
            by[(b["mint"], b["tok"])].append((b["slot"], m["wallet"]))
    out = set()
    for (mint, _), rows in by.items():
        rows.sort()
        if any(len({w for s, w in rows[i:] if s - rows[i][0] <= SLOT_SPAN}) >= MIN_MEMBERS for i in range(len(rows))):
            out.add(mint)
    return out


def main():
    data = json.loads((STUDY / "data/payouts.json").read_text())
    pays = data["payouts"] if isinstance(data, dict) else data
    by_amount = defaultdict(list)
    for p in pays:
        by_amount[p["lam"]].append(p["t"])
    n = len(pays)
    fit = sum(len(v) for k, v in by_amount.items() if requested(k))
    repeated = sum(len(v) for v in by_amount.values() if len(v) >= 2)
    top = [
        {
            "lamports": k,
            "payouts": len(v),
            "requested_sol": (requested(k) or 0) / 1e9 or None,
            "first": day(min(v)),
            "last": day(max(v)),
        }
        for k, v in sorted(by_amount.items(), key=lambda kv: -len(kv[1]))[:12]
    ]
    fit_days = defaultdict(lambda: [0, 0])
    for p in pays:
        fit_days[day(p["t"])][0] += bool(requested(p["lam"]))
        fit_days[day(p["t"])][1] += 1
    # how often does one exact amount reach 15 payouts inside 380 s?
    tail = []
    for k, ts in by_amount.items():
        ts.sort()
        i, last_end = 0, -1
        for j in range(len(ts)):
            while ts[j] - ts[i] > SPAN_S:
                i += 1
            if j - i + 1 >= FLEET_N and ts[i] > last_end:
                tail.append({"lamports": k, "start": day(ts[i]), "fits_fee_line": bool(requested(k))})
                last_end = ts[j]
    fleet_rate = len(by_amount[FLEET_LAM]) / max(1, len({day(t) for t in by_amount[FLEET_LAM]}))
    bursts = json.loads(Path(sys.argv[1]).read_text())["bursts"]
    rows = []
    for i, b in enumerate(bursts):
        ms = b["members"]
        dest = defaultdict(set)
        mint_w = defaultdict(set)
        for m in ms:
            for d in m["dest"]:
                dest[d].add(m["wallet"])
            for x in m["buys"]:
                mint_w[x["mint"]].add(m["wallet"])
        rows.append(
            {
                "i": i,
                "day": day(b["t0"]),
                "lamports": b["lam"],
                "payouts": b["size"],
                "wallets": len({m["wallet"] for m in ms}),
                "O1": outcomes(ms)["O1"],
                "strict_mints": sorted(strict_mints(ms)),
                "mints_5_wallets": sorted(k for k, v in mint_w.items() if len(v) >= MIN_MEMBERS),
                "destinations_5_wallets": sorted(k for k, v in dest.items() if len(v) >= MIN_MEMBERS),
                "largest_destination_share": max((len(v) for v in dest.values()), default=0),
                "all_wallets": sorted({m["wallet"] for m in ms}),
            }
        )
    strict = [r for r in rows if r["O1"]]
    pairs = []
    for x in range(len(strict)):
        for y in range(x + 1, len(strict)):
            a, b = strict[x], strict[y]
            pairs.append(
                {
                    "a": a["i"],
                    "b": b["i"],
                    "same_destination": sorted(set(a["destinations_5_wallets"]) & set(b["destinations_5_wallets"])),
                    "same_strict_mints": len(set(a["strict_mints"]) & set(b["strict_mints"])),
                    "same_wallets": len(set(a["all_wallets"]) & set(b["all_wallets"])),
                }
            )
    fleet = json.loads((OUT.parent / "nine_wallets" / "group15_detail.json").read_text())
    fleet_strict = [t["mint"] for t in fleet["tokens"] if t["slot_span"] <= SLOT_SPAN and t["n_wallets"] >= MIN_MEMBERS]
    res = {
        "payouts": n,
        "days": len(fit_days),
        "share_on_fee_line": round(fit / n, 4),
        "share_repeated_exactly": round(repeated / n, 4),
        "distinct_amounts": len(by_amount),
        "top_amounts": top,
        "days_with_over_half_on_line": sum(a * 2 > b for a, b in fit_days.values()),
        "share_on_line_first_last_day": [
            round(fit_days[min(fit_days)][0] / fit_days[min(fit_days)][1], 3),
            round(fit_days[max(fit_days)][0] / fit_days[max(fit_days)][1], 3),
        ],
        "windows_15_in_380s": len(tail),
        "windows_on_fee_line": sum(t["fits_fee_line"] for t in tail),
        "windows_by_amount": Counter(t["lamports"] for t in tail).most_common(8),
        "fleet_amount_payouts": len(by_amount[FLEET_LAM]),
        "fleet_amount_per_active_day": round(fleet_rate, 2),
        "sampled_bursts": len(rows),
        "by_strict_mint_count": dict(sorted(Counter(len(r["strict_mints"]) for r in rows).items())),
        "strict_bursts": [{k: v for k, v in r.items() if k != "all_wallets"} for r in strict],
        "strict_pairs_sharing": [p for p in pairs if p["same_destination"] or p["same_strict_mints"] or p["same_wallets"]],
        "fleet_strict_tokens": len(fleet_strict),
        "fleet_tokens": len(fleet["tokens"]),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "results.json").write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("strict_bursts",)}, indent=0)[:2600])


if __name__ == "__main__":
    main()
