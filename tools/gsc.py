#!/usr/bin/env python3
"""Talk to the Google Search Console API with OAuth or a service-account key.

Google's own client library is not installed in this container, and pulling it
in needs a lockfile change, so this signs the OAuth JWT itself with the
`openssl` binary that is already here. No third-party dependency.

Credentials, in order:
  1. Service account - $GSC_SA_JSON, $GSC_SA_FILE, ~/.gsc_service_account.json
  2. OAuth user token - $GSC_OAUTH_JSON, $GSC_OAUTH_FILE, ~/.gsc_oauth.json

Path 1 signs a JWT with `openssl`; path 2 exchanges a refresh token, so it also
needs no third-party library. Use path 2 when the organisation enforces
`iam.disableServiceAccountKeyCreation` and a service-account key cannot be
created - that is a common secure-by-default policy, not a misconfiguration.

Whichever identity is used must be added as a user on the property in Search
Console (Settings -> Users and permissions -> Add user, permission "Full"),
otherwise every call comes back 403.

    python3 tools/gsc.py sites                 # which properties can I see
    python3 tools/gsc.py sitemaps               # what is submitted
    python3 tools/gsc.py submit                 # (re)submit sitemap.xml
    python3 tools/gsc.py submit-urls            # ask Google to crawl each page
    python3 tools/gsc.py inspect <url>          # index status of one page
    python3 tools/gsc.py analytics [days]       # top queries + pages
    python3 tools/gsc.py questions [days] [n]   # question-type queries (regex filter)
    python3 tools/gsc.py auth-code             # print the OAuth consent URL
    python3 tools/gsc.py auth-exchange <code>  # trade the code for a token
"""
from __future__ import annotations

import base64
import json
import os
import re
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

# The OAuth client id/secret are not secrets in the sense a refresh token is -
# they identify the app, not the user - but they still should not be committed.
# They live in tools/.gsc_client.json (gitignored), so a session reset that wipes
# the home directory does not force Sir through the Google Cloud console again.
CLIENT_FILE = ROOT / "tools" / ".gsc_client.json"


def client_creds() -> dict:
    """Client id/secret from env first, then the gitignored local file."""
    cid = os.environ.get("GSC_OAUTH_CLIENT_ID")
    secret = os.environ.get("GSC_OAUTH_CLIENT_SECRET", "")
    if cid and secret:
        return {"client_id": cid, "client_secret": secret}
    if CLIENT_FILE.exists():
        d = json.loads(CLIENT_FILE.read_text(encoding="utf-8"))
        return {
            "client_id": cid or d.get("client_id", ""),
            "client_secret": secret or d.get("client_secret", ""),
        }
    return {"client_id": cid or "", "client_secret": secret}


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
        "no credentials found.\n"
        "OAuth (use this if service-account keys are blocked by policy): run\n"
        "  python3 tools/gsc.py auth-code   # then auth-exchange <code>\n"
        "Service account: set GSC_SA_JSON (the JSON itself) or GSC_SA_FILE (a "
        f"path to it), or save it as {default}."
    )


OAUTH_TOKEN_URI = "https://oauth2.googleapis.com/token"
OAUTH_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
# Google's OAuth flow only redirects to a registered URI. The loopback form
# ("http://localhost") needs no client secret and no web server: the user opens
# the consent URL, Google redirects to localhost with ?code=..., and the address
# bar still shows that code even though nothing is listening. That is why this
# works on a headless box with no browser.
# Overridable: Google allows the loopback forms for Desktop clients, and if the
# console only accepts one of them, GSC_OAUTH_REDIRECT fixes it without an edit.
OAUTH_REDIRECT = os.environ.get("GSC_OAUTH_REDIRECT", "http://localhost")


def load_oauth() -> dict:
    raw = os.environ.get("GSC_OAUTH_JSON")
    if raw:
        return json.loads(raw)
    path = os.environ.get("GSC_OAUTH_FILE")
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    # The home dir is wiped on a session reset, so also keep a copy inside the
    # repo (gitignored - this file holds a live refresh token) and read it first.
    local = ROOT / "tools" / ".gsc_oauth.json"
    if local.exists():
        return json.loads(local.read_text(encoding="utf-8"))
    default = Path.home() / ".gsc_oauth.json"
    if default.exists():
        return json.loads(default.read_text(encoding="utf-8"))
    sys.exit(
        "no OAuth token found.\n"
        "Set GSC_OAUTH_JSON (the JSON itself) or GSC_OAUTH_FILE (a path to it), or "
        f"save it as {default}.\n"
        "Run `gsc.py auth-code` then `gsc.py auth-exchange <code>` to create it."
    )


def cmd_auth_code() -> None:
    """Print the consent URL. The client id comes from client_creds() (env, then
    the gitignored tools/.gsc_client.json)."""
    cid = client_creds()["client_id"]
    if not cid:
        try:
            cid = load_oauth().get("client_id")
        except SystemExit:
            sys.exit(
                "need a client id: set GSC_OAUTH_CLIENT_ID or put it in "
                "tools/.gsc_client.json (from the OAuth 'Desktop app' client)."
            )
    if not cid:
        sys.exit("the OAuth file has no client_id; set GSC_OAUTH_CLIENT_ID.")
    params = urllib.parse.urlencode(
        {
            "client_id": cid,
            "redirect_uri": OAUTH_REDIRECT,
            "response_type": "code",
            "scope": SCOPES,
            "access_type": "offline",   # ask for a refresh token
            "prompt": "consent",        # force the refresh token on re-runs
        }
    )
    print(f"{OAUTH_AUTH_URI}?{params}")


def cmd_auth_exchange(code: str) -> None:
    creds = client_creds()
    cid = creds["client_id"]
    secret = creds["client_secret"]
    if not cid:
        try:
            existing = load_oauth()
            cid = cid or existing.get("client_id")
            secret = secret or existing.get("client_secret", "")
        except SystemExit:
            pass
    if not cid:
        sys.exit("need the client id: set GSC_OAUTH_CLIENT_ID or tools/.gsc_client.json.")
    body = urllib.parse.urlencode(
        {
            "client_id": cid,
            "client_secret": secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": OAUTH_REDIRECT,
        }
    ).encode()
    req = urllib.request.Request(OAUTH_TOKEN_URI, data=body)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"code exchange failed ({e.code}): {e.read().decode()[:400]}")
    if "refresh_token" not in data:
        sys.exit("no refresh_token in the response; re-run auth-code (it forces consent).")
    out = {
        "client_id": cid,
        "client_secret": secret,
        "refresh_token": data["refresh_token"],
    }
    dest = Path.home() / ".gsc_oauth.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    dest.chmod(0o600)
    print(f"wrote {dest} (mode 600). Delete it if you ever revoke access.")


def access_token_oauth() -> str:
    """Trade the stored refresh token for an access token."""
    cred = load_oauth()
    body = urllib.parse.urlencode(
        {
            "client_id": cred.get("client_id", os.environ.get("GSC_OAUTH_CLIENT_ID", "")),
            "client_secret": cred.get("client_secret", os.environ.get("GSC_OAUTH_CLIENT_SECRET", "")),
            "refresh_token": cred["refresh_token"],
            "grant_type": "refresh_token",
        }
    ).encode()
    req = urllib.request.Request(OAUTH_TOKEN_URI, data=body)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)["access_token"]
    except urllib.error.HTTPError as e:
        sys.exit(f"OAuth token exchange failed ({e.code}): {e.read().decode()[:400]}")


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


def question_re() -> re.Pattern:
    """Sir's Search Console filter, as one compiled pattern.

    In the GSC UI this is Performance -> Queries -> Add filter -> Custom
    (regex), pasted as-is. Same expression here so the tool and the UI agree on
    what counts as a question query.

        (?i).*(what|why|how|when|where|who|which|can|does|do|is|are|will|should|
        best way|how much|how many|meaning|definition|calculate|formula).*

    The alternation is ordered longest-first in the original, which matters for
    a human reading it but not for a regex engine; kept in the same order so the
    two can be diffed by eye.
    """
    return re.compile(
        r"(?i).*(what|why|how|when|where|who|which|can|does|do|is|are|will|"
        r"should|best way|how much|how many|meaning|definition|calculate|"
        r"formula).*"
    )


def fetch_queries(token: str, days: int, limit: int = 25000) -> list[dict]:
    """Every query row in the window, paged.

    The API caps a single response at 25000 rows and the default page is 25,
    which is the same ceiling the UI shows. A question filter is only useful
    over the whole set - a query that earns 3 impressions is exactly the kind of
    long tail worth writing a page for - so page until the rows run out.
    """
    site = resolve_site(token)
    end = time.strftime("%Y-%m-%d")
    start = time.strftime("%Y-%m-%d", time.localtime(time.time() - days * 86400))
    url = f"{API}/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query"

    rows: list[dict] = []
    offset = 0
    while len(rows) < limit:
        data = call(url, token, method="POST", payload={
            "startDate": start, "endDate": end,
            "dimensions": ["query"], "rowLimit": 25000, "startRow": offset,
        })
        page = data.get("rows", [])
        if not page:
            break
        rows.extend(page)
        if len(page) < 25000:
            break
        offset += len(page)
    return rows


def cmd_questions(token: str, days: int, args: list[str]) -> None:
    """The question-type queries, i.e. Sir's GSC regex filter.

    Question queries are the ones a calculator page or a short explainer can
    answer, so they are the best guide for what to write next. Prints the total
    window first so the share of question traffic is visible, then the questions
    ranked by impressions, then the ones already earning clicks.
    """
    rx = question_re()
    rows = fetch_queries(token, days)
    if not rows:
        print("  (no data yet - the property may be too new)")
        return

    total_imp = sum(r["impressions"] for r in rows)
    total_clicks = sum(r["clicks"] for r in rows)
    qs = [r for r in rows if rx.match(r["keys"][0])]
    q_imp = sum(r["impressions"] for r in qs)
    q_clicks = sum(r["clicks"] for r in qs)

    print(f"queries {days}d: {len(rows)} total, {len(qs)} question-type "
          f"({len(qs) * 100 // max(len(rows), 1)}% of queries)")
    print(f"  impressions: {total_imp} total, {q_imp} question "
          f"({q_imp * 100 // max(total_imp, 1)}%)")
    print(f"  clicks:      {total_clicks} total, {q_clicks} question")

    top = int(args[0]) if args else 60
    qs.sort(key=lambda r: -r["impressions"])
    print(f"\ntop {min(top, len(qs))} question queries by impressions")
    for r in qs[:top]:
        pos = r.get("position", 0)
        print(f"  {r['clicks']:>3} clicks {r['impressions']:>5} imp  "
              f"pos {pos:>5.1f}  {r['keys'][0]}")

    clicked = [r for r in qs if r["clicks"] > 0]
    if clicked:
        print(f"\nquestion queries already earning clicks ({len(clicked)})")
        for r in sorted(clicked, key=lambda r: -r["clicks"]):
            print(f"  {r['clicks']:>3} clicks {r['impressions']:>5} imp  "
                  f"pos {r.get('position', 0):>5.1f}  {r['keys'][0]}")


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


def have_oauth() -> bool:
    if os.environ.get("GSC_OAUTH_JSON") or os.environ.get("GSC_OAUTH_FILE"):
        return True
    if (ROOT / "tools" / ".gsc_oauth.json").exists():
        return True
    return (Path.home() / ".gsc_oauth.json").exists()


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "auth-code":
        cmd_auth_code()
        return
    if cmd == "auth-exchange":
        if len(sys.argv) < 3:
            sys.exit("usage: gsc.py auth-exchange <code>")
        cmd_auth_exchange(sys.argv[2])
        return
    # Prefer OAuth when it is set up: it survives the key-creation policy.
    token = access_token_oauth() if have_oauth() else access_token(load_key())
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
    elif cmd == "questions":
        # gsc.py questions [days] [top]
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 28
        cmd_questions(token, days, sys.argv[3:])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
