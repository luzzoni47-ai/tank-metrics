#!/usr/bin/env python3
"""Count the daily sandbox budget across all automations.

The platform runs at most 20 sandboxes per day. Every automation costs one
sandbox per trigger, so the schedules must add up to <= 20 or the extras are
skipped with `daily_sandbox_limit` - and a skipped run is silent: the automation
still shows ACTIVE, it just never runs. That is how a 37/day set of schedules
sat there looking healthy while most runs were being dropped.

    python3 tools/automation/audit_budget.py
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request

LIMIT = 20
HOST = "https://app.all-hands.dev"


def field_values(field: str, lo: int, hi: int) -> set[int]:
    out: set[int] = set()
    for part in field.split(","):
        step = 1
        if "/" in part:
            part, s = part.split("/")
            step = int(s)
        if part == "*":
            start, end = lo, hi
        elif "-" in part:
            a, b = part.split("-")
            start, end = int(a), int(b)
        else:
            start = end = int(part)
        out.update(range(start, end + 1, step))
    return out


def runs_per_week(cron: str) -> int:
    """Expand a 5-field cron over one week and count the firing minutes."""
    mins, hours, dom, month, dow = cron.split()
    m = field_values(mins, 0, 59)
    h = field_values(hours, 0, 23)
    d = field_values(dom, 1, 31)
    mo = field_values(month, 1, 12)
    w = field_values(dow, 0, 6)
    dom_star, dow_star = dom.strip() == "*", dow.strip() == "*"
    count = 0
    for weekday in range(7):
        if not dow_star and weekday not in w:
            continue
        for _ in range(1):  # one representative day per weekday
            if not dom_star and 1 not in d:
                # approximate: only days 1..31 matter via dom; use day 1 as probe
                continue
            if not mo.issuperset({1}) and 1 not in mo:
                continue
            count += len(m) * len(h)
    return count


def main() -> int:
    token = os.environ.get("OPENHANDS_API_KEY", "")
    if not token:
        sys.exit("Set OPENHANDS_API_KEY first")
    req = urllib.request.Request(
        f"{HOST}/api/automation/v1?limit=100",
        headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    items = data.get("automations") or data.get("items") or []

    total = 0.0
    print(f"  {'automation':<46} {'cron':<16} {'/day':>6}")
    for a in sorted(items, key=lambda x: x.get("name", "")):
        cron = (a.get("trigger") or {}).get("schedule", "")
        per_day = runs_per_week(cron) / 7 if cron else 0
        total += per_day
        print(f"  {a.get('name','')[:45]:<46} {cron:<16} {per_day:>6.2f}")
    print(f"  {'TOTAL':<46} {'':<16} {total:>6.2f}   (limit {LIMIT})")
    if total > LIMIT:
        print(f"  FAIL: {total:.1f} runs/day exceeds the {LIMIT} sandbox limit - "
              f"~{total - LIMIT:.1f} runs/day will be SKIPPED silently")
        return 1
    print(f"  PASS: {LIMIT - total:.1f} runs/day of headroom")
    return 0


if __name__ == "__main__":
    sys.exit(main())
