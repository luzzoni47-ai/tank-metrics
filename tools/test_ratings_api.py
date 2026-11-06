#!/usr/bin/env python3
"""Guard the ratings API end to end, against a stand-in Upstash Redis.

The bug this exists for: the route read a single MGET as a flat list, but the
pipeline helper unwraps one result per *command*, so the reply was an array
holding an array. Every calculator therefore reported zero ratings while the
writes landed perfectly - the tally was in Redis the whole time and no page
could see it. Unit-testing the maths would not have caught it, because the
maths was right and the shape was wrong.

So this runs the real route: a small HTTP server speaks the Upstash pipeline
protocol in memory, `next dev` is started with KV_REST_API_URL pointed at it,
and the assertions are made over HTTP. It needs no credentials and touches no
real database.

    python3 tools/test_ratings_api.py
"""
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Store:
    """The handful of Redis commands the route uses, in memory."""

    def __init__(self) -> None:
        self.data: dict[str, int] = {}
        self.lock = threading.Lock()

    def run(self, command: list) -> object:
        op = str(command[0]).upper()
        with self.lock:
            if op == "INCR":
                key = command[1]
                self.data[key] = int(self.data.get(key, 0)) + 1
                return self.data[key]
            if op == "INCRBY":
                key, by = command[1], int(command[2])
                self.data[key] = int(self.data.get(key, 0)) + by
                return self.data[key]
            if op == "EXPIRE":
                return 1 if command[1] in self.data else 0
            if op == "MGET":
                return [self.data.get(k) for k in command[1:]]
            if op == "GET":
                return self.data.get(command[1])
            raise ValueError(f"unsupported command {op}")


class Handler(BaseHTTPRequestHandler):
    store: Store

    def do_POST(self) -> None:
        length = int(self.headers.get("content-length", 0))
        body = json.loads(self.rfile.read(length) or b"[]")
        # Upstash answers /pipeline with one {result} per command.
        if self.path.rstrip("/").endswith("/pipeline"):
            out = [{"result": self.store.run(c)} for c in body]
        else:
            out = {"result": self.store.run(body)}
        raw = json.dumps(out).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *a) -> None:
        pass


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get(url: str, timeout: int = 30) -> tuple[int, dict]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def post(url: str, payload: dict, timeout: int = 30) -> tuple[int, dict]:
    req = urllib.request.Request(
        url, method="POST", data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"{}")
        except Exception:
            return e.code, {}


def wait_for(url: str, seconds: int = 120) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as r:
                if r.status < 500:
                    return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    failures: list[str] = []

    def check(ok: bool, message: str) -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {message}")
        if not ok:
            failures.append(message)

    if not (ROOT / "node_modules" / "next").exists():
        print("SKIP: next is not installed (run npm install first)")
        return 0

    redis_port = free_port()
    app_port = free_port()
    store = Store()
    handler = type("H", (Handler,), {"store": store})
    server = ThreadingHTTPServer(("127.0.0.1", redis_port), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    env = dict(os.environ)
    env.update({
        "KV_REST_API_URL": f"http://127.0.0.1:{redis_port}",
        "KV_REST_API_TOKEN": "test-token",
        "PORT": str(app_port),
        "NODE_ENV": "development",
    })
    proc = subprocess.Popen(
        ["npx", "next", "dev", "-p", str(app_port)],
        cwd=ROOT, env=env,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    base = f"http://127.0.0.1:{app_port}"
    api = f"{base}/api/ratings"
    try:
        if not wait_for(f"{api}?tool=probe"):
            check(False, "the dev server started")
            return 1
        check(True, "the dev server started against the stand-in Redis")

        status, body = get(f"{api}?tool=sip-calculator")
        check(status == 200 and body.get("count") == 0, "a fresh calculator starts at zero")

        status, body = post(api, {"tool": "sip-calculator", "stars": 5})
        check(status == 200, "a first vote is accepted")
        check(body.get("count") == 1, f"a first vote counts (got {body.get('count')!r})")
        check(body.get("average") == 5, f"a first vote averages 5 (got {body.get('average')!r})")

        status, body = get(f"{api}?tool=sip-calculator")
        check(
            body.get("count") == 1 and body.get("average") == 5,
            "the vote survives a re-read - the shape bug returned zero here",
        )

        status, body = post(api, {"tool": "sip-calculator", "stars": 3, "prev": 5})
        check(
            body.get("count") == 1 and body.get("average") == 3,
            f"an edit moves the total and not the count (got {body.get('count')!r}/{body.get('average')!r})",
        )

        status, body = post(api, {"tool": "sip-calculator", "stars": 3, "prev": 3})
        check(
            body.get("count") == 1 and body.get("average") == 3,
            "re-submitting the same score changes nothing",
        )

        post(api, {"tool": "ppf-calculator", "stars": 4})
        post(api, {"tool": "ppf-calculator", "stars": 2})
        status, body = get(f"{api}?tool=ppf-calculator")
        check(
            body.get("count") == 2 and body.get("average") == 3,
            f"two voters average correctly (got {body.get('count')!r}/{body.get('average')!r})",
        )
        check(
            body.get("distribution") == [0, 1, 0, 1, 0],
            f"the histogram matches the votes (got {body.get('distribution')!r})",
        )

        status, body = get(f"{api}?tool=sip-calculator")
        check(body.get("count") == 1, "one calculator's votes do not leak into another")

        status, body = get(f"{api}?tool=../../etc/passwd")
        check(status == 400, "a traversal-shaped id is refused")
        status, body = post(api, {"tool": "sip-calculator", "stars": 9})
        check(status == 400, "an out-of-range score is refused")
        status, body = post(api, {"tool": "sip-calculator", "stars": "five"})
        check(status == 400, "a non-numeric score is refused")

        for i in range(40):
            status, body = post(api, {"tool": "flood-check", "stars": 1})
            if status == 429:
                break
        check(status == 429, "a burst from one network is capped")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        server.shutdown()

    print(f"\nPASS={len(failures) == 0} ({len(failures)} failure(s))")
    for f in failures:
        print(f"  - {f}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
