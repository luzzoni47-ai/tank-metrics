# The 20 tools, divided across the automations

Sir listed 20 SEO tools. No single run should carry all 20 - that is what made
`daily SEO` and `daily blog + SEO` time out at 30 minutes. Each tool now has ONE
owning automation, and each automation reads only its own slice. Do not pick up a
tool that belongs to another automation.

| # | Tool | Owning automation | What it actually does (no login) |
|---|------|-------------------|----------------------------------|
| 1 | Google Search Console | `daily SEO` + `Top-1 push` | `tools/gsc.py` (OAuth) - inspect, sitemaps, analytics, `gsc_triage.py` |
| 2 | PageSpeed Insights | `daily SEO` | free public API, home + one calculator |
| 3 | Screaming Frog | `weekly site health` | `seo_monitor.py --local` + `site_health` crawl |
| 4 | Google Keyword Planner | `daily guide` | `tools/keyword_radar.py` (Google autocomplete, no key) |
| 5 | AnswerThePublic | `daily guide` | keyword_radar `+` gap phrases |
| 6 | ChatGPT for ideas | `daily news` | the agent's own reasoning, grounded in real sources |
| 7 | Yoast | `daily SEO` | `seo_monitor.py` (title/description length, canonical, schema) |
| 8 | Rank Math | `daily SEO` | same as Yoast - this is a static site, not WordPress |
| 9 | Ahrefs | `daily SEO` | `content_uniqueness.py` (the honest proxy: content quality) |
| 10 | SEMrush | `daily SEO` | `content_uniqueness.py` + `seo_monitor.py` |
| 11 | Quora | `site authority` | PREPARE one answer; Sir posts from his account |
| 12 | Reddit | `site authority` | PREPARE one answer; Sir posts from his account |
| 13 | Medium | `site authority` | PREPARE a title + canonical; Sir posts |
| 14 | LinkedIn | `site authority` | PREPARE a post; Sir posts |
| 15 | GuestPostTracker | `site authority` | editor pitch drafts, `tools/outreach/` |
| 16 | HARO | `site authority` | journalist-pitch drafts, `tools/outreach/` |
| 17 | Crunchbase | `site authority` | listing packet, Sir submits |
| 18 | Product Hunt | `site authority` | listing packet, Sir submits |
| 19 | Indie Hackers | `site authority` | listing packet, Sir submits |
| 20 | Google My Business | **Sir's own account** | the agent cannot log in; one-time setup |

## Hard rule that never changes

The agent PREPARES. It never posts to Quora, Reddit, Medium or LinkedIn, never
sends an outreach email, never submits a directory listing, and never buys a
link. Sir sends and submits from his own accounts. That is why the citations the
site earns are worth having.
