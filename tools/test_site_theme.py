#!/usr/bin/env python3
"""Guard the dark-mode switch, the scroll bar and the rating card.

Three things have to hold at once, and each is easy to break in a way that
looks fine in a browser:

1. Every page carries the theme init and `theme.js`. A page that misses the
   inline init shows a white flash before the deferred script runs, and a page
   that misses `theme.js` has a switch that does nothing.
2. The rating card is on the calculators and nowhere else. A card on the
   privacy policy collects nothing and looks like a mistake.
3. The rating card never claims a number the server did not send. An invented
   average is a promise the site cannot keep, so the script is checked for a
   hard-coded rating and the pages for an `aggregateRating` block.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "public" / "site"

URL_MAP = json.loads((ROOT / "tools" / "url-map.json").read_text(encoding="utf-8"))
CALC_IDS = {c.strip("/") for c, t in URL_MAP.items() if t.startswith("/site/tools/")}

PAGES = sorted(set(SITE.rglob("*.html")) | {SITE / "index.html"})

results: list = []


def check(ok: bool, message: str) -> None:
    results.append((ok, message))


def read(page: Path) -> str:
    return page.read_text(encoding="utf-8")


def is_calculator(page: Path) -> bool:
    return page.parent.name == "tools" and page.stem in CALC_IDS


def check_assets() -> None:
    for name in ("theme.js", "rating.js"):
        path = SITE / name
        check(path.exists(), f"{name} exists")
        if path.exists():
            text = read(path)
            check(len(text) > 1500, f"{name} is a real script ({len(text)} bytes)")

    check((ROOT / "app" / "api" / "ratings" / "route.ts").exists(), "ratings API route exists")

    css = read(SITE / "style.css")
    for token in ('.tmr__star', 'html[data-theme="dark"]', '.scroll-progress', '.theme-btn'):
        check(token in css, f"style.css carries {token}")


def check_pages() -> None:
    missing_init, missing_script, rated_wrong = [], [], []
    for page in PAGES:
        text = read(page)
        rel = page.relative_to(SITE)
        if 'localStorage.getItem("tm:theme")' not in text:
            missing_init.append(str(rel))
        if "/site/theme.js" not in text:
            missing_script.append(str(rel))
        has_rating = "/site/rating.js" in text
        if has_rating != is_calculator(page):
            rated_wrong.append((str(rel), has_rating))

    check(not missing_init, f"theme init on every page ({len(missing_init)} missing)")
    check(not missing_script, f"theme.js on every page ({len(missing_script)} missing)")
    check(
        not rated_wrong,
        f"rating card on calculators only ({len(rated_wrong)} wrong): {rated_wrong[:5]}",
    )

    calc_pages = [p for p in PAGES if is_calculator(p)]
    check(len(calc_pages) == len(CALC_IDS), f"all {len(CALC_IDS)} calculators have a page")


def check_no_invented_rating() -> None:
    """The card must not carry a number of its own."""
    script = read(SITE / "rating.js")
    check("application/ld+json" not in script, "rating.js emits no structured data")
    check("ratingValue" not in script, "rating.js emits no ratingValue")
    # The only numbers the card can show come from the API payload.
    check("/api/ratings" in script, "rating.js reads the API")

    # No page may ship a self-serving rating block either: it earns no stars in
    # Google and risks a review-snippet penalty.
    offenders = [str(p.relative_to(SITE)) for p in PAGES if "aggregateRating" in read(p)]
    check(not offenders, f"no page ships aggregateRating ({offenders[:5]})")


def check_api_guards() -> None:
    route = read(ROOT / "app" / "api" / "ratings" / "route.ts")
    check("TOOL_ID" in route, "route validates the tool id")
    check("WRITE_LIMIT" in route, "route rate-limits writes")
    check("KV_REST_API_URL" in route, "route reads the Upstash URL")
    check("process.env" in route, "route reads credentials from the environment")


def check_style_dark_tokens() -> None:
    """Dark mode redefines tokens, not colours on individual rules."""
    from design import DARK_CSS, RATING_CSS  # noqa: E402

    check("--bg:" in DARK_CSS and "--ink:" in DARK_CSS, "dark block redefines the base tokens")
    check("prefers-reduced-motion" in RATING_CSS, "rating card respects reduced motion")
    check("prefers-reduced-motion" in DARK_CSS or "prefers-reduced-motion" in RATING_CSS,
          "the card stops moving when asked")


def main() -> int:
    sys.path.insert(0, str(ROOT / "tools"))
    check_assets()
    check_pages()
    check_no_invented_rating()
    check_api_guards()
    check_style_dark_tokens()

    failed = [m for ok, m in results if not ok]
    for ok, message in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {message}")
    print(f"\nPASS={len(results) - len(failed)} FAIL={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
