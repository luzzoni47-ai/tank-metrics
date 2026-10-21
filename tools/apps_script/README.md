# Contact form — one-time setup

The contact form on `/contact` posts to a Google Apps Script web app. The
script writes every message into a Google Sheet and drops any uploaded file in
a Google Drive folder. It is free and has no monthly limit.

**This is a one-time job.** Once it is done, nothing here needs touching again —
the daily automations never read or change this setup.

The website side is already finished. Only the Google side is left, because it
needs your own Google login.

---

## What you do (about 10 minutes)

### 1. Make the Sheet

1. Open <https://sheets.new>. Name it `Tank Metrics Contact`.
2. Menu: **Extensions → Apps Script**. A code editor opens in a new tab.

### 2. Paste the code

1. In the editor, select everything in `Code.gs` and delete it.
2. Open `tools/apps_script/Code.gs` from this repo, copy the whole file, paste it in.
3. Press **Ctrl+S** (or the save icon).

### 3. Deploy it

1. Top right: **Deploy → New deployment**.
2. Click the gear icon next to "Select type" and pick **Web app**.
3. Set:
   - **Description**: `contact v1`
   - **Execute as**: **Me**
   - **Who has access**: **Anyone**
4. Click **Deploy**. Google asks for permission — click **Authorize access**,
   pick your account, then **Advanced → Go to (unsafe)** → **Allow**.
   (It says "unsafe" because the script is yours and Google has not reviewed
   it. That is normal for a personal script.)
5. Copy the **Web app URL**. It ends with `/exec`.

### 4. Give the URL to the website

Open `public/site/contact.js` and replace the placeholder on line 14:

```js
var ENDPOINT = 'PASTE_YOUR_APPS_SCRIPT_EXEC_URL_HERE';
```

with your real URL:

```js
var ENDPOINT = 'https://script.google.com/macros/s/AKfy.../exec';
```

Save the file. Then commit and deploy, or just tell the agent: *"contact.js me
endpoint lag gaya, deploy kar do"*.

### 5. Check it works

1. Open <https://tankmetrics.in/contact>.
2. Fill nothing at all and press **Send Message**. You should see the green
   thank-you card.
3. Open your Google Sheet. A new row must appear within a few seconds.

If the row does not appear, see below.

---

## What you get

**The Sheet** — one row per message:

| Received | Name | Email | Phone | Message | Files | File links | Page |
|---|---|---|---|---|---|---|---|

Blank fields are stored empty. Nothing is ever rejected, because every field
is optional by design.

**Email** — the script also emails you a copy of each message, so you notice it
without opening the Sheet.

**Files** — uploads land in a Drive folder called `Tank Metrics - Contact
uploads`. A visitor can attach up to **5 files at once** (screenshots, photos,
PDFs), each up to 5 MB and 10 MB in total. The Sheet row lists every name and
every Drive link. Anything over those limits is skipped by name and the visitor
is told which ones, so the written message always gets through.

---

## Notes

- **Every field is optional.** Name, email, phone, message and the file can all
  be blank. The visitor always gets a thank-you card and never sees a browser
  validation bubble or an `alert()`. `tools/test_contact_form.py` enforces this.
- **Your phone number is not on the site.** It was removed from `/contact`
  along with the floating WhatsApp button. If you want it back, say so.
- **The URL is not a secret.** It appears in `contact.js`, which every browser
  downloads. That is how Apps Script web apps work. Abuse is limited by the
  honeypot field and by Google's own quotas (see below). If spam ever becomes a
  problem, add a Turnstile/reCAPTCHA check before the `appendRow` call.
- **Google quotas** (a personal account): ~90 minutes of script run time per day
  and 100 emails per day. A contact form will not come close.
- **If you redeploy**, you get a *new* URL. Update `contact.js` again. Editing
  the code and saving does **not** change the URL if you use
  **Deploy → Manage deployments → edit (pencil) → Version: New version**.

---

## If something breaks

| Symptom | Cause | Fix |
|---|---|---|
| Green card, but no Sheet row | `contact.js` still has the placeholder | Do step 4 |
| Green card, no row, URL is set | Deployment is not "Anyone" | Manage deployments → edit → Who has access: **Anyone** |
| Nothing happens on click | Browser console shows a CSP error | `next.config.mjs` lost `script.google.com` from `connect-src` |
| Row appears but files are missing | Over 5 MB each, over 10 MB total, or more than 5 | The card names the skipped files; ask for them by email |
| Console says *ENDPOINT is not set* | Same as row 1 | Do step 4 |

Check the browser console (F12 → Console) first — it names the exact problem.

## What was verified

`python3 tools/test_contact_form.py` drives headless Chromium and asserts:

- no field is `required`
- the owner's phone number is gone
- all five fields are labelled optional
- several screenshots can be picked in one go, and the note names them
- the file and phone inputs exist
- an empty submit still produces a reply
- no `alert()` ever blocks the visitor
- the form collapses only when the endpoint is really configured

Run it after any change to `contact.html`, `contact.js` or `style.css`. It is
also part of all three daily automation prompts, so a daily run cannot quietly
break the form.
