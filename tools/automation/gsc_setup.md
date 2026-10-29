# Giving the agent Search Console access (one-time setup)

`tools/gsc.py` talks to the Search Console API. It cannot log into the Search
Console UI - that needs your Google login and an MFA code. Instead it uses a
credential you create once, after which the agent reads index status and search
analytics on its own, every day, with no login.

**Nobody should ever paste their Google password into this repo or a chat.**
Both options below hand over exactly the access that is needed and nothing more.

There are two ways to authenticate. **Pick OAuth if Google blocks service
account keys** - which is the case for tankmetrics.in (the organisation enforces
`iam.disableServiceAccountKeyCreation`, so the JSON key cannot be created).

---

## Option A - OAuth (use this when service-account keys are blocked)

This signs in as **your own Google account** instead of a robot, so the key
policy does not apply. It still needs no browser on the agent machine.

1. **Create a project** - https://console.cloud.google.com/ , project picker ->
   "New project", name it `tankmetrics-gsc`, Create.

2. **Enable the API** - "APIs & Services" -> "Library", search **Google Search
   Console API**, open it, **Enable**.

3. **OAuth consent screen** - "APIs & Services" -> "OAuth consent screen".
   - User type: **External** -> Create.
   - App name `tankmetrics-gsc`, your email as support and developer contact.
   - Save and continue through Scopes and Test users.
   - On the "Test users" step **add your own Google email**. While the app is in
     "Testing" only test users can consent; that is fine for a single user.

4. **Create the client** - "APIs & Services" -> "Credentials" ->
   "Create credentials" -> **OAuth client ID**.
   - Application type: **Desktop app**.
   - Create. Copy the **Client ID** and **Client secret**.

5. **Get the consent URL** (on the agent machine, or anywhere):

   ```
   GSC_OAUTH_CLIENT_ID=<client id> python3 tools/gsc.py auth-code
   ```

   It prints a long `https://accounts.google.com/o/oauth2/v2/auth?...` URL.

6. **Open that URL** in any browser, sign in with the Google account that owns
   the tankmetrics.in property, and approve. Google redirects to
   `http://localhost/?code=...`. **The page will fail to load - that is
   expected** (nothing is listening on localhost). Copy the `code=...` value
   out of the address bar.

7. **Exchange the code for a stored token:**

   ```
   GSC_OAUTH_CLIENT_ID=<client id> GSC_OAUTH_CLIENT_SECRET=<secret> \
     python3 tools/gsc.py auth-exchange <code>
   ```

   It writes `~/.gsc_oauth.json` (mode 600) with the refresh token. The refresh
   token does not expire, so this is a one-time step.

   Alternatively store it as the secret **`GSC_OAUTH_JSON`** (the whole JSON on
   one line) plus `GSC_OAUTH_CLIENT_ID` / `GSC_OAUTH_CLIENT_SECRET`.

8. **Verify:** `python3 tools/gsc.py sites` should list the tankmetrics.in
   property. Your Google account is already an owner, so no extra user step is
   needed.

To revoke later: delete `~/.gsc_oauth.json` and remove the app under
https://myaccount.google.com/permissions .

---

## Option B - Service account (only if key creation is allowed)

Blocked on tankmetrics.in. Kept here for other properties.

1. Project + enable the API as in Option A steps 1-2.
2. "IAM & Admin" -> "Service Accounts" -> "Create service account"
   (`tankmetrics-gsc`, no roles needed).
3. Keys tab -> "Add key" -> "Create new key" -> **JSON**. If this is refused with
   `iam.disableServiceAccountKeyCreation`, use Option A instead.
4. Copy the `client_email` from the JSON, then add it in Search Console:
   property -> Settings -> Users and permissions -> Add user -> that email ->
   **Full**.
5. Give the agent the JSON as `GSC_SA_JSON` (the JSON itself) or `GSC_SA_FILE`
   (a path), or save it as `~/.gsc_service_account.json`.

Never commit the JSON. `tools/gsc.py` reads it from the environment or your home
directory, never from the repo.

---

## What the agent can then do, every day

| Command | What it gives |
|---|---|
| `gsc.py sites` | confirm the property is visible |
| `gsc.py sitemaps` | submitted vs indexed count, errors, last download |
| `gsc.py submit` | re-submit sitemap.xml |
| `gsc.py submit-urls` | inspect every URL in `tools/gsc_submit_list.txt` and re-submit the sitemap |
| `gsc.py inspect <url>` | one page's verdict: "Crawled - currently not indexed", "Discovered - not indexed", duplicate, canonical mismatch, last crawl |
| `gsc.py analytics 28` | top queries and pages by clicks and impressions |

`inspect` is the important one: it turns "59 not indexed" from a number into a
reason per page, which is exactly what is needed to fix it.

## What the API still cannot do

Google exposes no "Request Indexing" button through the API - that action is
UI-only. The API can *report* index status and *re-submit the sitemap*, and it
can inspect a URL to force Google to look again. Pressing the button in the
Search Console UI stays a human job for the handful of pages that matter most.

## If neither option works

Skip Search Console and let the agent keep working from the outside: it can
already measure every indexing blocker except Google's own verdict per page
(`tools/content_uniqueness.py` for duplicates, `tools/seo_monitor.py` for
technical faults, `tools/indexnow_submit.py` for Bing/Yandex and AI answers).
