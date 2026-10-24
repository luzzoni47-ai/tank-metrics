#!/usr/bin/env python3
"""Admin the product licences from the terminal.

Sir does not want to open a spreadsheet to issue a key or, more importantly, to
cut off a refunded buyer. This talks to the same Apps Script endpoint the site
uses, with the ADMIN_SECRET.

    # one-time: put the secret and endpoint in your shell
    export LICENCE_ENDPOINT="https://script.google.com/macros/s/.../exec"
    export LICENCE_SECRET="the-secret-you-set-in-Code.gs"

    python3 tools/licence_admin.py issue  --email buyer@x.com --name "Ravi" \
        --order RZP-12345 --plan bundle
    python3 tools/licence_admin.py revoke --key TM-ABCD-EFGH-JKLM-NPQR \
        --reason "refunded, order RZP-12345"
    python3 tools/licence_admin.py list
    python3 tools/licence_admin.py status --key TM-...

The revoke command is the refund path: after it runs, that key stops delivering
files, immediately, for everyone.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

PLANS = ("model", "manual", "bundle")


def call(payload: dict) -> dict:
    endpoint = os.environ.get("LICENCE_ENDPOINT", "").strip()
    # https in production; plain http is allowed only against localhost, so the
    # test suite can run the CLI without weakening the real guard.
    local = endpoint.startswith("http://127.0.0.1") or endpoint.startswith("http://localhost")
    if not (endpoint.startswith("https://") or local):
        sys.exit("Set LICENCE_ENDPOINT to the Apps Script /exec URL first.")

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        endpoint, data=body,
        # text/plain keeps this a simple request, which Apps Script answers
        # without a CORS preflight.
        headers={"Content-Type": "text/plain;charset=utf-8"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code}: {e.read()[:400]!r}")
    except urllib.error.URLError as e:
        sys.exit(f"Could not reach the licence endpoint: {e}")


def secret() -> str:
    s = os.environ.get("LICENCE_SECRET", "").strip()
    if not s:
        sys.exit("Set LICENCE_SECRET to the secret in Code.gs first.")
    if s == "CHANGE-ME-BEFORE-DEPLOYING":
        sys.exit("The secret in Code.gs is still the placeholder. Change it.")
    return s


def cmd_issue(a) -> int:
    res = call({"action": "issue", "secret": secret(), "email": a.email,
                "name": a.name or "", "order_id": a.order or "",
                "plan": a.plan, "max_downloads": a.max_downloads,
                "valid_days": a.valid_days, "send_email": not a.no_email})
    if not res.get("ok"):
        print("failed:", res.get("reason", res))
        return 1
    print(f"key       {res['key']}")
    print(f"plan      {res['plan']}")
    print(f"expires   {res['expires']}")
    print(f"emailed   {'yes' if res.get('emailed') else 'no'}")
    return 0


def cmd_revoke(a) -> int:
    res = call({"action": "revoke", "secret": secret(), "key": a.key,
                "reason": a.reason or "refunded"})
    if not res.get("ok"):
        print("failed:", res.get("reason", res))
        return 1
    print(f"{res['key']} is now {res['status']}. "
          "That key will no longer deliver files.")
    return 0


def cmd_status(a) -> int:
    res = call({"action": "status", "key": a.key})
    print(json.dumps(res, indent=2))
    return 0 if res.get("ok") else 1


def cmd_list(a) -> int:
    res = call({"action": "list", "secret": secret()})
    if not res.get("ok"):
        print("failed:", res.get("reason", res))
        return 1
    rows = res.get("licences", [])
    if not rows:
        print("no licences issued yet")
        return 0
    print(f"{'KEY':<24} {'STATUS':<9} {'DL':<6} {'PLAN':<8} EMAIL")
    for r in rows:
        print(f"{r['key']:<24} {r['status']:<9} "
              f"{str(r['downloads']) + '/' + str(r['max_downloads']):<6} "
              f"{r['plan']:<8} {r['email']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Admin product licences.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("issue", help="create a licence for an order")
    p.add_argument("--email", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--order", default="")
    p.add_argument("--plan", default="bundle", choices=PLANS)
    p.add_argument("--max-downloads", type=int, default=5)
    p.add_argument("--valid-days", type=int, default=1095)
    p.add_argument("--no-email", action="store_true",
                   help="do not email the buyer the key")
    p.set_defaults(fn=cmd_issue)

    p = sub.add_parser("revoke", help="lock a key (the refund path)")
    p.add_argument("--key", required=True)
    p.add_argument("--reason", default="refunded")
    p.set_defaults(fn=cmd_revoke)

    p = sub.add_parser("status", help="check one key")
    p.add_argument("--key", required=True)
    p.set_defaults(fn=cmd_status)

    p = sub.add_parser("list", help="list every licence")
    p.set_defaults(fn=cmd_list)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
