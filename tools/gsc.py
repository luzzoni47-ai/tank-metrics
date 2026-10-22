#!/usr/bin/env python3
"""Talk to the Google Search Console API with a service-account key.

Google's own client library is not installed in this container, and pulling it
in needs a lockfile change, so this signs the OAuth JWT itself with the
`openssl` binary that is already here. No third-party dependency.

The key is read from, in order:
  1. $GSC_SA_JSON  - the raw JSON of the service-account key
  2. $GSC_SA_FILE  - a path to that JSON
  3. ~/.gsc_service_account.json

The service account's email must be added as a user in Search Console
(Settings -> Users and permissions -> Add user, permission "Full"), otherwise
every call comes back 403.

    python3 tools/gsc.py sites                 # which properties can I see
    python3 tools/gsc.py sitemaps               # what is submitted
    python3 tools/gsc.py submit                 # (re)submit sitemap.xml
    python3 tools/gsc.py submit-urls            # ask Google to crawl each page
    python3 tools/gsc.py inspect <url>          # index status of one page
    python3 tools/gsc.py analytics [days]       # top queries + pages
"""
from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "tankmetrics.in"
SITEMAP_PATH = "/sitemap.xml"
SCOPES = "https://www.googleapis.com/auth/webmasters"
TOKEN_URI = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/webmasters/v3"
INSPECT_API = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"

# The property string differs by property type and the API is strict about it:
# a Domain property is "sc-domain:tankmetrics.in", a URL-prefix property is
# "https://tankmetrics.in/". Sir has (or had) both, so resolve it at runtime
# from /sites instead of hardcoding - a wrong string is an opaque 403/404.
SITE = ""


def load_key() -> dict:
    raw = os.environ.get("GSC_SA_JSON")
    if raw:
        return json.loads(raw)
    path = os.environ.get("GSC_SA_FILE")
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    default = Path.home() / ".gsc_service_account.json"
    if default.exists():
        return json.loads(default.read_text(encoding="utf-8"))
    sys.exit(
        "no service-account key found.\n"
        "Set GSC_SA_JSON (the JSON itself) or GSC_SA_FILE (a path to it), or save "
        f"it as {default}."
    )


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign(message: bytes, pem: str) -> bytes:
    # `openssl dgst -sign` will not read the key from /dev/stdin on this build
    # ("Could not find private key"), so the key goes through a temp file.
    tmp = Path("/tmp/_gsc_key.pem")
    tmp.write_text(pem, encoding="utf-8")
    try:
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", str(tmp)],
            input=message,
            capture_output=True,
        )
    finally:
        tmp.unlink(missing_ok=True)
    if proc.returncode != 0:
        sys.exit("openssl could not sign the JWT: " + proc.stderr.decode())
    return proc.stdout


def access_token(key: dict) -> str:
    now = int(time.time())
    header = b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = b64(
        json.dumps(
            {
                "iss": key["client_email"],
                "scope": SCOPES,
                "aud": TOKEN_URI,
                "iat": now,
                "exp": now + 3600,
            }
        ).encode()
    )
    signing_input = f"{header}.{claims}".encode()
    sig = b64(sign(signing_input, key["private_key"]))
    assertion = f"{header}.{claims}.{sig}"

    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode()
    req = urllib.request.Request(TOKEN_URI, data=body)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"token exchange failed ({e.code}): {e.read().decode()[:400]}")


def call(url: str, token: str, method: str = "GET", payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode()[:600]
        if e.code == 403:
            detail += (
                "\n(403 usually means the service-account email was never added "
                "as a user on the property in Search Console.)"
            )
        sys.exit(f"{method} {url} -> {e.code}\n{detail}")


def resolve_site(token: str) -> str:
    """Pick the property to act on: prefer the Domain property, else the
    https URL-prefix one, else whatever is visible."""
    global SITE
    if SITE:
        return SITE
    data = call(f"{API}/sites", token)
    entries = data.get("siteEntry", [])
    if not entries:
        sys.exit(
            "this service account can see no properties. Add its email "
            f"({load_key()['client_email']}) as a user in Search Console first."
        )
    urls = [e["siteUrl"] for e in entries]
    for want in (f"sc-domain:{HOST}", f"https://{HOST}/", f"http://{HOST}/"):
        if want in urls:
            SITE = want
            return SITE
    SITE = urls[0]
    print(f"(using property {SITE}; expected one for {HOST})")
    return SITE


def cmd_sites(token: str) -> None:
    data = call(f"{API}/sites", token)
    entries = data.get("siteEntry", [])
    if not entries:
        print("no properties visible to this service account")
        return
    for e in entries:
        print(f"{e['permissionLevel']:<20} {e['siteUrl']}")


def sitemap_url() -> str:
    """The sitemaps API always takes the full URL. (The property-type rule -
    Domain wants the full URL, URL-prefix wants just `sitemap.xml` - applies to
    the Search Console UI box, not this API.)"""
    return f"https://{HOST}{SITEMAP_PATH}"


def cmd_sitemaps(token: str) -> None:
    site = resolve_site(token)
    data = call(f"{API}/sites/{urllib.parse.quote(site, safe='')}/sitemaps", token)
    subs = data.get("sitemap", [])
    if not subs:
        print("no sitemaps submitted")
        return
    for s in subs:
        print(f"{s.get('path')}")
        print(f"  last downloaded: {s.get('lastDownloaded', '-')}")
        print(f"  errors: {s.get('errors', 0)}  warnings: {s.get('warnings', 0)}")
        for c in s.get("contents", []):
            print(f"  submitted: {c.get('submitted')}  indexed: {c.get('indexed', '?')}")


def cmd_submit(token: str) -> None:
    site = resolve_site(token)
    url = sitemap_url()
    call(
        f"{API}/sites/{urllib.parse.quote(site, safe='')}/sitemaps/{urllib.parse.quote(url, safe='')}",
        token,
        method="PUT",
    )
    print(f"submitted {url} to property {site}")


def cmd_submit_urls(token: str) -> None:
    """Google has no public 'submit this URL' API; the closest is a URL
    inspection request per page (which nudges a recrawl) plus a sitemap PUT."""
    resolve_site(token)
    listing = ROOT / "tools" / "gsc_submit_list.txt"
    urls = [u.strip() for u in listing.read_text(encoding="utf-8").splitlines() if u.strip()]
    print(f"nudging {len(urls)} URL(s) via URL inspection")
    ok = 0
    for u in urls:
        try:
            call(
                INSPECT_API,
                token,
                method="POST",
                payload={"inspectionUrl": u, "siteUrl": SITE},
            )
            ok += 1
        except SystemExit as e:
            print("  fail", u, str(e)[:160])
    print(f"  {ok}/{len(urls)} accepted")
    cmd_submit(token)


def cmd_inspect(token: str, url: str) -> None:
    site = resolve_site(token)
    data = call(
        INSPECT_API,
        token,
        method="POST",
        payload={"inspectionUrl": url, "siteUrl": site},
    )
    r = data.get("inspectionResult", {})
    idx = r.get("indexStatusResult", {})
    print(f"url: {url}")
    print(f"  verdict:        {idx.get('verdict')}")
    print(f"  coverage:       {idx.get('coverageState')}")
    print(f"  indexing state: {idx.get('indexingState')}")
    print(f"  robots:         {idx.get('robotsTxtState')}")
    print(f"  last crawl:     {idx.get('lastCrawlTime', '-')}")
    print(f"  canonical (google): {idx.get('googleCanonical')}")
    print(f"  canonical (user):   {idx.get('userCanonical')}")


def cmd_analytics(token: str, days: int) -> None:
    site = resolve_site(token)
    end = time.strftime("%Y-%m-%d")
    start = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
    payload = {
        "startDate": start,
        "endDate": end,
        "dimensions": ["query"],
        "rowLimit": 25,
    }
    data = call(
        f"{API}/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query",
        token,
        method="POST",
        payload=payload,
    )
    rows = data.get("rows", [])
    print(f"top queries {start} .. {end}")
    if not rows:
        print("  (no data yet - the property may be too new)")
    for r in rows:
        print(f"  {r['clicks']:>4} clicks  {r['impressions']:>6} imp  {r['keys'][0]}")


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    token = access_token(load_key())
    cmd = sys.argv[1]
    if cmd == "sites":
        cmd_sites(token)
    elif cmd == "sitemaps":
        cmd_sitemaps(token)
    elif cmd == "submit":
        cmd_submit(token)
    elif cmd == "submit-urls":
        cmd_submit_urls(token)
    elif cmd == "inspect":
        cmd_inspect(token, sys.argv[2])
    elif cmd == "analytics":
        cmd_analytics(token, int(sys.argv[2]) if len(sys.argv) > 2 else 28)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
