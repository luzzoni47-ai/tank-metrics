# Giving the agent Search Console access (one-time setup)

`tools/gsc.py` already talks to the Search Console API. It cannot log into the
Search Console UI — that needs your Google login and an MFA code. Instead it
uses a **service account**: a robot Google identity that you add to the
property once. After that the agent can read index status and search analytics
on its own, every day, with no login.

**Nobody should ever paste their Google password into this repo or a chat.**
The service account is the safe way to hand over exactly the access that is
needed and nothing more.

## What only you can do (about 5 minutes)

You need to be logged into the Google account that owns the tankmetrics.in
property in Search Console. (If the MFA loop blocks even that, the service
account cannot be created either — see "If you cannot log in" at the bottom.)

1. **Create a project** — go to https://console.cloud.google.com/ , click the
   project picker, "New project", name it `tankmetrics-gsc`, Create.

2. **Enable the API** — in that project go to "APIs & Services" → "Library",
   search for **Google Search Console API**, open it, click **Enable**.

3. **Create a service account** — "IAM & Admin" → "Service Accounts" →
   "Create service account". Name it `tankmetrics-gsc`. No roles are needed
   (Search Console permissions come from step 5, not from IAM). Click Done.

4. **Make its key** — click the new service account → "Keys" tab → "Add key" →
   "Create new key" → **JSON** → Create. A `.json` file downloads. Inside it,
   the `client_email` line looks like
   `tankmetrics-gsc@tankmetrics-gsc-123456.iam.gserviceaccount.com`. Copy that
   email.

5. **Add it to Search Console** — open https://search.google.com/search-console ,
   pick the tankmetrics.in property → "Settings" → "Users and permissions" →
   "Add user" → paste the `client_email` → permission **Full** → Add.

6. **Hand the key to the agent** — either
   - save the JSON as `~/.gsc_service_account.json` on the agent machine, or
   - add it as a secret named **`GSC_SA_JSON`** (the whole JSON on one line).

   Never commit the JSON. `tools/gsc.py` reads it from the environment or your
   home directory, never from the repo.

## Verify it works

```
python3 tools/gsc.py sites
```

It should print the tankmetrics.in property with `siteFullUser` (or higher). A
403 means step 5 was skipped or the email was mistyped.

## What the agent can then do, every day

| Command | What it gives |
|---|---|
| `gsc.py sites` | confirm the property is visible |
| `gsc.py sitemaps` | submitted vs indexed count, errors, last download |
| `gsc.py submit` | re-submit sitemap.xml |
| `gsc.py submit-urls` | inspect every URL in `tools/gsc_submit_list.txt` and re-submit the sitemap |
| `gsc.py inspect <url>` | one page's verdict: "Crawled – currently not indexed", "Discovered – not indexed", duplicate, canonical mismatch, last crawl |
| `gsc.py analytics 28` | top queries and pages by clicks and impressions |

`inspect` is the important one: it turns "59 not indexed" from a number into a
reason per page, which is exactly what is needed to fix it.

## What the API still cannot do

Google exposes no "Request Indexing" button through the API — that action is
UI-only. The API can *report* index status and *re-submit the sitemap*, and it
can inspect a URL to force Google to look again. Pressing the button in the
Search Console UI stays a human job for the handful of pages that matter most.

## If you cannot log in at all

If the MFA loop blocks Google entirely, the service account cannot be created
and this route is closed. The alternatives are:

- ask whoever manages the Google account to do steps 1-5, or
- recover the Google account's MFA first, or
- skip Search Console and let the agent keep working from the outside: it can
  already measure every indexing blocker except Google's own verdict per page
  (`tools/content_uniqueness.py` for duplicates, `tools/seo_monitor.py` for
  technical faults, `tools/indexnow_submit.py` for Bing/Yandex and AI answers).
