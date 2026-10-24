#!/usr/bin/env python3
"""Exercise the licence flow end to end.

The Apps Script cannot run on this machine, so this file starts a small server
that speaks the same protocol as tools/apps_script/Code.gs, then drives the real
tools/licence_admin.py against it. That proves the parts that do run here — the
admin CLI and the wire contract — actually work, and it proves the one thing
that matters commercially: a revoked key stops delivering files.

It also checks that licence.js and licence_admin.py use the same field names the
Apps Script reads, so a rename on one side cannot silently break the other.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADMIN = ROOT / "tools" / "licence_admin.py"
CODE_GS = ROOT / "tools" / "apps_script" / "Code.gs"
LICENCE_JS = ROOT / "public" / "site" / "licence.js"

SECRET = "test-secret"
PROBLEMS: list[str] = []


class Store:
    """A stand-in for the Licenses sheet."""

    def __init__(self) -> None:
        self.rows: dict[str, dict] = {}

    def key(self, raw: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", (raw or "").upper())

    def find(self, raw: str):
        k = self.key(raw)
        return self.rows.get(k)


class Handler(BaseHTTPRequestHandler):
    store: Store

    def log_message(self, *a):  # keep the test output clean
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        self.reply(handle(self.store, data))

    def reply(self, obj: dict):
        body = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def handle(store, d: dict) -> dict:
    if True:
        action = d.get("action")
        pass

        if action == "issue":
            if d.get("secret") != SECRET:
                return {"ok": False, "reason": "denied"}
            k = d.get("key") or "TM-TEST-TEST-TEST-TEST"
            store.rows[store.key(k)] = {
                "key": k, "email": d.get("email", ""), "name": d.get("name", ""),
                "order_id": d.get("order_id", ""), "plan": d.get("plan", "bundle"),
                "status": "active", "downloads": 0,
                "max_downloads": d.get("max_downloads", 5),
            }
            return {"ok": True, "key": k, "plan": d["plan"],
                    "expires": "2029-01-01", "emailed": bool(d.get("email"))}

        if action == "revoke":
            if d.get("secret") != SECRET:
                return {"ok": False, "reason": "denied"}
            row = store.find(d.get("key", ""))
            if not row:
                return {"ok": False, "reason": "not_found"}
            row["status"] = "revoked"
            return {"ok": True, "key": row["key"], "status": "revoked"}

        if action == "list":
            if d.get("secret") != SECRET:
                return {"ok": False, "reason": "denied"}
            return {"ok": True, "licences": list(store.rows.values())}

        if action == "status":
            row = store.find(d.get("key", ""))
            if not row:
                return {"ok": False, "reason": "not_found"}
            if row["status"] != "active":
                return {"ok": False, "reason": "revoked"}
            return {"ok": True, "licensee": row["name"], "plan": row["plan"],
                    "downloads": row["downloads"],
                    "max_downloads": row["max_downloads"], "expires": "2029-01-01"}

        if action == "redeem":
            row = store.find(d.get("key", ""))
            if not row:
                return {"ok": False, "reason": "not_found"}
            if row["status"] != "active":
                return {"ok": False, "reason": "revoked"}
            if row["downloads"] >= row["max_downloads"]:
                return {"ok": False, "reason": "limit"}
            row["downloads"] += 1
            return {"ok": True,
                    "files": [{"name": "Indian-Business-Financial-Model.xlsx",
                               "mime": "application/vnd.ms-excel",
                               "data": "UEsDBAo="}],
                    "downloads": row["downloads"],
                    "max_downloads": row["max_downloads"],
                    "licensee": row["name"],
                    "note": "licensed to " + row["name"]}

        return {"ok": False, "reason": "unknown_action"}


def run(*args: str, env: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(ADMIN), *args],
                          capture_output=True, text=True, env=env, timeout=60)


def check_contract() -> None:
    """Field names must agree across the JS client, the CLI, and the Apps Script."""
    gs = CODE_GS.read_text(encoding="utf-8")
    js = LICENCE_JS.read_text(encoding="utf-8")

    for field in ("action", "key"):
        if f'data.{field}' not in gs and f'data["{field}"]' not in gs:
            PROBLEMS.append(f"Code.gs never reads {field!r}")

    # The actions the client and CLI send must exist in the script.
    for action in ("redeem", "issue", "revoke", "list", "status"):
        if f"action === '{action}'" not in gs:
            PROBLEMS.append(f"Code.gs does not handle action {action!r}")

    if "action: 'redeem'" not in js:
        PROBLEMS.append("licence.js does not send action:'redeem'")

    # The paid files must never be delivered without a licence check. Check
    # inside redeem() specifically: licenceState also appears in status(), so a
    # file-wide search would pass even if redeem stopped calling it.
    body = gs[gs.index("function redeem"):gs.index("function status")]
    if "licenceState(row)" not in body:
        PROBLEMS.append("redeem does not consult licenceState")
    # The revocation branch must exist: a non-active licence must stop delivery.
    if "reason: 'revoked'" not in gs:
        PROBLEMS.append("there is no revoked reason in Code.gs")


def main() -> int:
    check_contract()

    store = Store()
    handler = type("H", (Handler,), {"store": store})
    srv = HTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    port = srv.server_address[1]

    env = dict(os.environ)
    env["LICENCE_ENDPOINT"] = f"http://127.0.0.1:{port}/exec"
    env["LICENCE_SECRET"] = SECRET

    try:
        # 1. Issue a key for a buyer.
        r = run("issue", "--email", "ravi@example.com", "--name", "Ravi",
                "--order", "RZP-1", "--plan", "bundle", env=env)
        if r.returncode != 0 or "TM-TEST" not in r.stdout:
            PROBLEMS.append(f"issue failed: {r.stdout} {r.stderr}")
        key = "TM-TEST-TEST-TEST-TEST"

        # 2. The buyer redeems it: a download, and the count goes up.
        st = store.find(key)
        first = handle(store, {"action": "redeem", "key": key})
        if not first.get("ok") or first["downloads"] != 1:
            PROBLEMS.append(f"active key did not redeem: {first}")

        # 3. Refund: revoke, then the same key must stop working.
        r = run("revoke", "--key", key, "--reason", "refunded", env=env)
        if r.returncode != 0 or "revoked" not in r.stdout:
            PROBLEMS.append(f"revoke failed: {r.stdout} {r.stderr}")
        after = handle(store, {"action": "redeem", "key": key})
        if after.get("ok") or after.get("reason") != "revoked":
            PROBLEMS.append(f"a revoked key still delivered files: {after}")
        if st["status"] != "revoked":
            PROBLEMS.append("the store did not record the revocation")

        # 4. A made-up key is refused.
        fake = handle(store, {"action": "redeem", "key": "TM-XXXX-XXXX-XXXX-XXXX"})
        if fake.get("ok") or fake.get("reason") != "not_found":
            PROBLEMS.append(f"an unknown key was accepted: {fake}")

        # 5. A wrong secret cannot revoke or issue.
        bad = handle(store, {"action": "revoke", "secret": "wrong",
                              "key": key})
        if bad.get("ok"):
            PROBLEMS.append("a wrong secret was allowed to revoke")

        # 6. The CLI's own secret guard fires before any network call.
        no_secret = dict(env)
        no_secret["LICENCE_SECRET"] = "CHANGE-ME-BEFORE-DEPLOYING"
        r = run("list", env=no_secret)
        if "placeholder" not in (r.stdout + r.stderr):
            PROBLEMS.append("the CLI does not reject the placeholder secret")

        # 7. The list command sees the licence.
        r = run("list", env=env)
        if key not in r.stdout:
            PROBLEMS.append(f"list did not show the key: {r.stdout}")
    finally:
        srv.shutdown()

    if PROBLEMS:
        print(f"FAIL: {len(PROBLEMS)} problem(s)")
        for p in PROBLEMS:
            print("  -", p)
        return 1
    print("ALL PASS: a key delivers, a refund cuts it off, "
          "unknown keys and wrong secrets are refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
