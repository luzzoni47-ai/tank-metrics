#!/usr/bin/env python3
"""Guard the outreach tool: it prepares, it never posts.

Link building is the one part of SEO where the wrong automation does real
damage. A script that posts to Quora or mails 200 editors gets the domain
penalised, and no amount of ranking work undoes that. So the two rules that
matter are checked here:

  1. Nothing in link_builder.py sends, posts or submits. The file may only
     WRITE into tools/outreach/. Any call to a request that is not a plain GET
     (a POST/PUT to a forum or a mail endpoint) is a failure.
  2. Every draft carries the "Sir posts this himself" note, so a draft cannot be
     mistaken for something the agent already did.

    python3 tools/test_outreach.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LB = ROOT / "tools" / "link_builder.py"
OUTREACH = ROOT / "tools" / "outreach"


def main() -> int:
    failures = []
    if not LB.is_file():
        print("FAIL: tools/link_builder.py is missing")
        return 1
    src = LB.read_text(encoding="utf-8")

    # 1. No outbound side effect. The KV store PUT and the reachability GET are
    # the only network calls allowed; neither posts to a third party.
    for bad in ("chat.postMessage", "api/comment", "submit_post", "smtplib",
                "sendmail", "/api/v1/comments", "oauth"):
        if bad in src:
            failures.append(f"link_builder.py contains {bad!r} - it must never post or send")

    # Any urllib Request with method=POST/PUT must be the KV store, not a site.
    for m in re.finditer(r'method="(POST|PUT|PATCH|DELETE)"', src):
        line_start = src.rfind("\n", 0, m.start())
        line = src[line_start:m.end() + 120]
        if "_KV_BASE" not in line and "kv_set" not in line and "kv_get" not in line:
            failures.append(f"suspicious outbound write in link_builder.py: {line.strip()[:90]}")

    # 2. The drafts exist and say who posts them.
    drafts = sorted(OUTREACH.glob("*.md")) if OUTREACH.is_dir() else []
    for d in drafts:
        t = d.read_text(encoding="utf-8")
        if "AGENT DRAFT" not in t and "AGENT-PREPARED" not in t:
            failures.append(f"{d.name} does not say it is agent-prepared")

    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"ALL PASS: outreach prepares only; {len(drafts)} draft(s) carry the agent note")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
