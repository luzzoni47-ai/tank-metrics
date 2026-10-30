# Naya site setup — ek hi toolset, kai sites

Sir ke paas 15+ sites hain. Sab par wahi crawler, wahi IndexNow ping, wahi Search
Console client aur wahi authority worker chalna chahiye. Isliye koi tool apne
source mein host ka naam nahi likhta — sab `tools/siteconfig.py` import karte hain.

## Ek site ka setup (naye repo mein)

1. **Repo copy karo**
   ```bash
   git clone <new-repo> /workspace/newsite
   cd /workspace/newsite
   ```

2. **Site ki pehchaan likho** — `tools/site.json.example` ko copy karo:
   ```bash
   cp tools/site.json.example .openhands/site.json
   ```
   Phir usme apna host, repo, brand aur IndexNow key bharo:
   ```json
   {
     "host": "client1.in",
     "repo": "owner/client1",
     "brand": "Client One",
     "indexnow_key": "32-char-key",
     "bing_user_agent": "ClientOne/1.0"
   }
   ```
   `.openhands/` **gitignored** hai — IndexNow key ek credential hai, repo mein
   nahi jaani chahiye.

3. **Check karo**
   ```bash
   python3 tools/siteconfig.py
   python3 tools/test_siteconfig.py
   ```
   Pehla command batayega kaunsi site load hui. Doosra fail karega agar koi tool
   host hardcode karta hai.

4. **Bina file badle test karna ho** (staging host ke liye):
   ```bash
   SITE_HOST=staging.client1.in SITE_REPO=owner/staging python3 tools/siteconfig.py
   ```

## Ek site = ek chat

Har site ka apna repo, apna `site.json`, apni memory (`.openhands/memory/`) aur
apni automation. Isi wajah se site A ka content site B par nahi jaa sakta.

## Ek Gmail = saari sites ka Search Console

Google Search Console ek hi account se **1,000 properties** tak leta hai. 15 sites
ke liye 15 Gmail **nahi** chahiye — ek Gmail, aur usme 15 properties add karo.
`tools/gsc.py` already `/sites` se list padhta hai, isliye code change nahi
karna padta.

## Jo abhi baaki hai (jab zaroorat pade)

- **WordPress sites:** REST API se chalega, har site ka **alag** Application
  Password. Draft banao, publish Sir karein.
- **AdSense:** apply karne se pehle Privacy Policy, About, Contact aur original
  content chahiye. Site par ye already hain.
- **Har site ka apna automation:** `tools/automation/` ka dhaancha wahi rahega,
  sirf `site.json` badlega.
