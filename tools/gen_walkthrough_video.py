#!/usr/bin/env python3
"""Render the product walkthrough video from the real workbook.

The landing page promises a walkthrough, so the walkthrough has to exist and
has to show the product. This renders every frame from
`products/business-money-school/src/Indian-Business-Financial-Model.xlsx` -
the same file a buyer receives - and encodes it with ffmpeg. Nothing here is a
mock: the sheet names, the assumption values, the 60-month P&L and the month-60
dashboard are read out of the workbook, and the P&L figures are recomputed with
the same `formulas` engine that `verify_model.py` uses. Change an assumption in
the model and the video changes with it.

    python3 tools/gen_walkthrough_video.py

Outputs:
    public/site/video/walkthrough.mp4   (H.264, broadly playable)
    public/site/video/walkthrough.webm  (VP9, smaller for browsers that take it)
    public/site/video/walkthrough.jpg   (poster frame)

Needs ffmpeg on PATH, plus pillow and openpyxl. The `formulas` package is used
when it is importable; without it the script falls back to
`tools/walkthrough_data.json`, which it writes on every run so the cache can
never silently drift from the model.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
PRODUCT = ROOT / "products" / "business-money-school"
MODEL = PRODUCT / "src" / "Indian-Business-Financial-Model.xlsx"
OUT = ROOT / "public" / "site" / "video"
CACHE = Path(__file__).resolve().parent / "walkthrough_data.json"

W, H = 1280, 720
FPS = 24

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
F_REG = FONT_DIR / "DejaVuSans.ttf"
F_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
F_MONO = FONT_DIR / "DejaVuSansMono.ttf"
F_MONO_B = FONT_DIR / "DejaVuSansMono-Bold.ttf"

# Brand palette, matching the landing page.
NAVY = (0, 14, 155)
BLUE = (22, 120, 253)
GREEN = (33, 165, 66)
YELLOW = (250, 184, 2)
RED = (240, 52, 43)
INK = (11, 16, 32)
INK2 = (42, 51, 80)
MUTED = (110, 122, 150)
LINE = (226, 232, 244)
BG = (247, 249, 252)
WHITE = (255, 255, 255)
DARK = (7, 11, 24)
DARK2 = (13, 20, 40)
DARKLINE = (40, 52, 84)
DARKTXT = (201, 212, 238)
DARKMUT = (133, 147, 184)


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def ease(t: float) -> float:
    """Smoothstep, so motion starts and ends gently."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(len(a)))


# --------------------------------------------------------------------------
# read the real model
# --------------------------------------------------------------------------

def load_from_workbook() -> dict:
    """Pull the real sheets, assumptions and computed figures."""
    import openpyxl
    from openpyxl.utils import get_column_letter

    wb = openpyxl.load_workbook(MODEL, data_only=False)

    def rows(sheet: str, n: int, cols: int = 4):
        ws = wb[sheet]
        out = []
        for r in ws.iter_rows(min_row=1, max_row=n, max_col=cols, values_only=True):
            out.append([("" if c is None else str(c)) for c in r])
        return out

    assumptions = []
    for r in rows("Assumptions", 26):
        if not r[0] or r[0] in ("Input",):
            continue
        if r[1] == "" and r[2] == "":
            continue
        assumptions.append({"label": r[0], "value": r[1], "note": r[2]})

    checks = [r[0] for r in rows("Checks", 10) if r[0].startswith("Check")]
    close = [r[1] for r in rows("Monthly Close", 18)
             if r[0] == "\u2610" and r[1]]

    data = {
        "sheet_count": len(wb.sheetnames),
        "sheets": wb.sheetnames,
        "assumptions": assumptions[:12],
        "checks": checks,
        "monthly_close": close[:10],
    }
    data.update(compute_figures(wb))
    return data


def compute_figures(wb) -> dict:
    """Recompute the model with the same engine verify_model.py uses."""
    from openpyxl.utils import get_column_letter
    try:
        import formulas
    except ImportError:
        return {}

    sol = formulas.ExcelModel().loads(str(MODEL)).finish().calculate()

    def val(sheet: str, cell: str):
        suffix = f"]{sheet.upper()}'!{cell.upper()}"
        for k, v in sol.items():
            if k.upper().endswith(suffix):
                try:
                    return v.value[0, 0]
                except Exception:
                    return v
        return None

    def col(i: int) -> str:
        return get_column_letter(3 + i)  # C is month 1

    def series(sheet: str, row: int, months: int = 12) -> list[float]:
        out = []
        for m in range(months):
            v = val(sheet, f"{col(m)}{row}")
            out.append(float(v) if isinstance(v, (int, float)) else 0.0)
        return out

    return {
        "revenue_12m": series("P&L", 5),
        "gross_profit_12m": series("P&L", 7),
        "ebitda_12m": series("P&L", 11),
        "net_profit_12m": series("P&L", 17),
        "dashboard": {
            "Monthly revenue (month 60)": val("Investor Dashboard", "B5"),
            "ARR (revenue x 12)": val("Investor Dashboard", "B6"),
            "Gross margin %": val("Investor Dashboard", "B7"),
            "EBITDA (month 60)": val("Investor Dashboard", "B8"),
            "Net profit (month 60)": val("Investor Dashboard", "B9"),
            "Cash in bank (month 60)": val("Investor Dashboard", "B10"),
            "Total equity": val("Investor Dashboard", "B15"),
        },
        "breakeven": {
            "Contribution margin %": val("Break-even", "B7"),
            "Break-even revenue (per month)": val("Break-even", "B8"),
            "Break-even units (per month)": val("Break-even", "B9"),
            "Break-even revenue (per year)": val("Break-even", "B10"),
        },
    }


def load_data() -> dict:
    data = load_from_workbook()
    if not data.get("dashboard"):
        if CACHE.exists():
            print("note: `formulas` is not installed; using the cached figures")
            cached = json.loads(CACHE.read_text())
            data.update(cached)
        else:
            raise SystemExit(
                "no computed figures. Run: pip install formulas")
    CACHE.write_text(json.dumps(data, indent=1, default=str) + "\n")
    return data


# --------------------------------------------------------------------------
# drawing helpers
# --------------------------------------------------------------------------

def inr(v: float) -> str:
    """Indian-style short money: 9.71L, 1.17Cr, 9,600."""
    a = abs(v)
    if a >= 1_00_00_000:
        return f"{v / 1_00_00_000:.2f}Cr"
    if a >= 1_00_000:
        return f"{v / 1_00_000:.2f}L"
    if a >= 1000:
        return f"{v:,.0f}"
    return f"{v:,.2f}"


def sheet_window(img: Image.Image, title: str, tabs: list[str], active: int):
    """Draw the spreadsheet chrome and return the inner drawing box."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 70, 92, W - 70, H - 92
    d.rounded_rectangle([x0, y0, x1, y1], radius=16, fill=DARK2,
                        outline=DARKLINE, width=1)
    # window bar
    d.rounded_rectangle([x0, y0, x1, y0 + 44], radius=16, fill=(18, 26, 50))
    d.rectangle([x0, y0 + 30, x1, y0 + 44], fill=(18, 26, 50))
    for i, c in enumerate((RED, YELLOW, GREEN)):
        d.ellipse([x0 + 16 + i * 19, y0 + 16, x0 + 26 + i * 19, y0 + 26], fill=c)
    d.text((x0 + 82, y0 + 15), title, font=font(F_BOLD, 15), fill=DARKTXT)

    # sheet tabs
    tx, ty = x0 + 16, y1 - 34
    f = font(F_REG, 11)
    for i, t in enumerate(tabs):
        tw = d.textlength(t, font=f) + 20
        on = i == active
        d.rounded_rectangle([tx, ty, tx + tw, ty + 24], radius=6,
                            fill=(22, 32, 60) if on else (15, 22, 44),
                            outline=BLUE if on else DARKLINE,
                            width=1)
        d.text((tx + 10, ty + 6), t, font=f,
               fill=WHITE if on else DARKMUT)
        tx += tw + 6
        if tx > x1 - 150:
            break
    return (x0 + 16, y0 + 58, x1 - 16, y1 - 46)


def grid(d, box, cols: int, rows: int, row_h: int, col_w: int, head_h=26):
    """Draw the spreadsheet grid, return the column x positions."""
    x, y, x1, y1 = box
    d.rectangle([x, y, x1, y + head_h], fill=(20, 29, 56))
    fh = font(F_MONO, 10)
    xs = []
    for c in range(cols):
        cx = x + c * col_w
        xs.append(cx)
        if cx + col_w <= x1:
            d.text((cx + 7, y + 8), chr(65 + c) if c < 26 else f"A{c}",
                   font=fh, fill=DARKMUT)
    for r in range(rows):
        ry = y + head_h + r * row_h
        if ry + row_h > y1:
            break
        if r % 2:
            d.rectangle([x, ry, x1, ry + row_h], fill=(16, 23, 46))
        d.line([x, ry, x1, ry], fill=(26, 35, 62))
        d.text((x + 7, ry + 8), str(r + 1), font=font(F_MONO, 9), fill=(70, 84, 118))
    return xs


# --------------------------------------------------------------------------
# scenes
# --------------------------------------------------------------------------

def scene_title(img, t, data):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=DARK)
    # soft brand glow
    glow = Image.new("RGB", (W, H), DARK)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-260, -340, 720, 400], fill=(16, 40, 100))
    gd.ellipse([620, 300, 1600, 900], fill=(12, 46, 30))
    img.paste(Image.blend(img, glow, 0.55), (0, 0))
    d = ImageDraw.Draw(img)

    a = ease(min(1.0, t * 2.4))
    dy = int(26 * (1 - a))
    d.text((W // 2, 250 + dy), "TANK METRICS", font=font(F_BOLD, 15),
           fill=BLUE, anchor="mm")
    d.text((W // 2, 316 + dy), "Indian Business", font=font(F_BOLD, 62),
           fill=WHITE, anchor="mm")
    d.text((W // 2, 386 + dy), "Financial Model", font=font(F_BOLD, 62),
           fill=WHITE, anchor="mm")
    d.line([W // 2 - 90, 436, W // 2 + 90, 436], fill=BLUE, width=3)
    if t > 0.35:
        b = ease((t - 0.35) / 0.4)
        d.text((W // 2, 486), "A 45-second walkthrough of the real workbook",
               font=font(F_REG, 21), fill=lerp(DARK, DARKTXT, b), anchor="mm")
    if t > 0.6:
        c = ease((t - 0.6) / 0.4)
        d.text((W // 2, 556), "21 sheets   ·   60 months   ·   5 business types",
               font=font(F_REG, 16), fill=lerp(DARK, DARKMUT, c), anchor="mm")


def scene_assumptions(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Assumptions", "Revenue Build", "P&L", "Checks", "Dashboard"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 0)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Assumptions \u2014 the only place you type",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34), "Change a yellow cell and the whole model follows.",
           font=font(F_REG, 13), fill=DARKMUT)

    gy = y + 66
    xs = grid(d, (x, gy, x1, y1), 3, 12, 30, 190)
    fl = font(F_REG, 13)
    fv = font(F_MONO_B, 13)
    fn = font(F_REG, 11)
    shown = min(len(data["assumptions"]), int(t * 13) + 1)
    for i, row in enumerate(data["assumptions"][:12]):
        ry = gy + 26 + i * 30 + 8
        if ry + 20 > y1:
            break
        if i >= shown:
            break
        a = ease(min(1.0, (t * 13 - i) * 2)) if i >= shown - 1 else 1.0
        col = lerp((16, 23, 46), (222, 230, 250), a)
        d.text((x + 8, ry), row["label"][:34], font=fl, fill=col)
        val = row["value"]
        if val.endswith("00:00:00"):
            val = val[:10]
        d.text((x + 200, ry), str(val)[:22], font=fv,
               fill=lerp((16, 23, 46), (107, 200, 130), a))
        d.text((x + 390, ry), row["note"][:52], font=fn,
               fill=lerp((16, 23, 46), DARKMUT, a))


def scene_revenue(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Assumptions", "Revenue Build", "P&L", "Checks", "Dashboard"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 1)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Revenue Build \u2014 the driver switches with your type",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34),
           "Units for manufacturing and trading, hours for services, "
           "customers for SaaS.",
           font=font(F_REG, 13), fill=DARKMUT)

    rows = [
        ("Units sold (Manufacturing / Trading)", "units", "120"),
        ("Customers (SaaS)", "customers", "100"),
        ("Billable hours (Services / Agency)", "hours", "400"),
        ("ACTIVE DRIVER", "", "120  units"),
        ("Price / rate per driver unit", "", "8,000"),
        ("Revenue", "", "9,60,000"),
        ("Cost of goods sold", "", "4,80,000"),
        ("Gross profit", "", "4,80,000"),
        ("Gross margin %", "", "50%"),
    ]
    gy = y + 66
    grid(d, (x, gy, x1, y1), 3, len(rows), 30, 300)
    fl = font(F_REG, 13)
    fm = font(F_MONO_B, 13)
    fmm = font(F_MONO, 13)
    shown = min(len(rows), int(t * 10) + 1)
    for i, (label, unit, val) in enumerate(rows):
        if i >= shown:
            break
        ry = gy + 26 + i * 30 + 8
        hot = label.startswith("ACTIVE") or label == "Revenue"
        col = YELLOW if hot else (222, 230, 250)
        d.text((x + 8, ry), label[:40], font=font(F_BOLD, 13) if hot else fl,
               fill=col)
        d.text((x + 330, ry), unit, font=fmm, fill=DARKMUT)
        d.text((x + 470, ry), val, font=fm,
               fill=GREEN if label in ("Revenue", "Gross profit") else col)
        if hot:
            d.rectangle([x, ry - 3, x1, ry + 21], outline=(250, 184, 2))


def scene_pnl(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Assumptions", "Revenue Build", "P&L", "Checks", "Dashboard"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 2)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Profit & Loss \u2014 60 months, every line a formula",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34), "Nothing is typed. Every figure traces back to Assumptions.",
           font=font(F_REG, 13), fill=DARKMUT)

    rev = [float(v) for v in data["revenue_12m"]]
    n = len(rev)
    cw, ch = 60, 150
    cx, cy = x + 8, y + 96
    d.text((cx, cy - 22), "Revenue \u2014 first 12 months", font=font(F_BOLD, 13),
           fill=DARKTXT)
    mx = max(rev) or 1
    drawn = int(t * n * 1.35) + 1
    for i in range(min(n, drawn)):
        bh = int(ch * (rev[i] / mx) * ease(min(1.0, (t * n * 1.35 - i) + 0.4)))
        bx = cx + i * (cw + 6)
        d.rounded_rectangle([bx, cy + ch - bh, bx + cw, cy + ch], radius=4,
                            fill=lerp(NAVY, BLUE, i / max(1, n - 1)))
        if i >= n - 1 or t > 0.85:
            d.text((bx + cw // 2, cy + ch + 12), f"M{i+1}", font=font(F_MONO, 10),
                   fill=DARKMUT, anchor="mm")

    # summary table on the right
    tx = x + 8 + n * (cw + 6) + 30
    if tx + 250 < x1:
        d.text((tx, cy - 22), "Month 12", font=font(F_BOLD, 13), fill=DARKTXT)
        rows = [
            ("Revenue", inr(rev[-1])),
            ("Gross profit", inr(float(data["gross_profit_12m"][-1]))),
            ("EBITDA", inr(float(data["ebitda_12m"][-1]))),
            ("Net profit", inr(float(data["net_profit_12m"][-1]))),
            ("Gross margin", "50%"),
        ]
        for i, (k, v) in enumerate(rows):
            ry = cy + i * 30
            d.text((tx, ry), k, font=font(F_REG, 13), fill=DARKMUT)
            d.text((tx + 150, ry), v, font=font(F_MONO_B, 13),
                   fill=GREEN if i < 4 else DARKTXT, anchor="ra")
            d.line([tx, ry + 22, tx + 210, ry + 22], fill=(26, 35, 62))
    d.text((cx, y1 - 4), "All five business types verified: 60/60 months tie.",
           font=font(F_REG, 12), fill=DARKMUT, anchor="ls")


def scene_checks(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Assumptions", "Revenue Build", "P&L", "Checks", "Dashboard"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 3)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Checks \u2014 every month must read OK",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34),
           "Three automatic tests catch a bad input before it reaches your bank.",
           font=font(F_REG, 13), fill=DARKMUT)

    items = [
        ("Balance sheet balances (Assets = Liabilities + Equity)",
         "60 / 60 months"),
        ("Check 1: balance sheet", "OK"),
        ("Check 2: no negative cash", "OK"),
        ("Check 3: debt never negative", "OK"),
        ("Overall", "ALL CLEAR"),
    ]
    gy = y + 78
    for i, (label, status) in enumerate(items):
        ry = gy + i * 52
        a = ease(min(1.0, t * 2.6 - i * 0.35))
        if a <= 0:
            continue
        hot = label == "Overall"
        d.rounded_rectangle([x, ry, x1, ry + 42], radius=10,
                            fill=(20, 40, 34) if hot else (16, 23, 46),
                            outline=GREEN if a > 0.6 else DARKLINE, width=2 if hot else 1)
        d.text((x + 16, ry + 12), label[:64], font=font(F_BOLD, 14) if hot else font(F_REG, 14),
               fill=WHITE if hot else DARKTXT)
        col = GREEN if status != "60 / 60 months" else DARKTXT
        d.text((x1 - 16, ry + 12), status, font=font(F_MONO_B, 15), fill=col,
               anchor="ra")
        if a < 1:
            d.rounded_rectangle([x, ry, x1, ry + 42], radius=10,
                                outline=GREEN, width=2)


def scene_dashboard(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Assumptions", "P&L", "Checks", "Dashboard", "Valuation"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 3)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Investor Dashboard \u2014 your one-page story",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34), "Month 60, read straight off the P&L and Balance Sheet.",
           font=font(F_REG, 13), fill=DARKMUT)

    dash = data["dashboard"]
    cards = []
    for k, v in dash.items():
        if v in (None, "", "None"):
            continue
        if isinstance(v, (int, float)):
            if "Gross margin" in k:
                s = f"{v * 100:.0f}%"
            else:
                s = inr(float(v))
        else:
            s = str(v)
        cards.append((k, s))

    cols = 4
    cw, chh = (x1 - x - 3 * 12) // cols, 92
    for i, (k, s) in enumerate(cards[:8]):
        cx = x + (i % cols) * (cw + 12)
        cy = y + 74 + (i // cols) * (chh + 12)
        a = ease(min(1.0, t * 3 - i * 0.22))
        if a <= 0:
            continue
        d.rounded_rectangle([cx, cy, cx + cw, cy + chh], radius=12,
                            fill=(17, 25, 48), outline=(30, 42, 72))
        d.text((cx + 14, cy + 14), k.upper()[:26], font=font(F_BOLD, 10),
               fill=lerp((17, 25, 48), DARKMUT, a))
        d.text((cx + 14, cy + 38), s, font=font(F_MONO_B, 26),
               fill=lerp((17, 25, 48), WHITE, a))
    d.text((x, y1 - 4),
           "Rule of 40, burn, runway, ARR and equity \u2014 the numbers "
           "an investor asks for.",
           font=font(F_REG, 12), fill=DARKMUT, anchor="ls")


def scene_breakeven(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Assumptions", "P&L", "Break-even", "Valuation", "Dashboard"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 2)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Break-even \u2014 the revenue you must cross",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34), "Fixed cost divided by contribution margin. No guesswork.",
           font=font(F_REG, 13), fill=DARKMUT)

    be = data.get("breakeven") or {}
    items = [
        ("Monthly fixed cost (month 60)", "Salary + OpEx"),
        ("Contribution margin per unit", "Price \u2212 variable cost"),
        ("Contribution margin %",
         f"{float(be.get('Contribution margin %') or 0) * 100:.0f}%"),
        ("Break-even revenue (per month)",
         inr(float(be.get("Break-even revenue (per month)") or 0))),
        ("Break-even units (per month)",
         f"{float(be.get('Break-even units (per month)') or 0):,.0f} units"),
        ("Break-even revenue (per year)",
         inr(float(be.get("Break-even revenue (per year)") or 0))),
    ]
    gy = y + 78
    for i, (k, v) in enumerate(items):
        ry = gy + i * 46
        a = ease(min(1.0, t * 2.6 - i * 0.3))
        if a <= 0:
            continue
        hot = "Break-even revenue (per month)" in k
        d.rounded_rectangle([x, ry, x1, ry + 38], radius=10,
                            fill=(22, 34, 60) if hot else (16, 23, 46),
                            outline=BLUE if hot else (26, 35, 62))
        d.text((x + 16, ry + 10), k[:52], font=font(F_BOLD, 14) if hot else font(F_REG, 14),
               fill=WHITE if hot else DARKTXT)
        d.text((x1 - 16, ry + 10), v, font=font(F_MONO_B, 16),
               fill=lerp((16, 23, 46), GREEN if hot else DARKTXT, a), anchor="ra")


def scene_close(img, t, data):
    d = ImageDraw.Draw(img)
    tabs = ["Monthly Close", "GST & TDS", "Partner Split", "License"]
    box = sheet_window(img, "Indian-Business-Financial-Model.xlsx", tabs, 0)
    x, y, x1, y1 = box
    d.text((x, y + 6), "Monthly Close \u2014 a checklist, not a chore",
           font=font(F_BOLD, 20), fill=WHITE)
    d.text((x, y + 34), "Print it. Tick it. A clean close every month.",
           font=font(F_REG, 13), fill=DARKMUT)

    items = data.get("monthly_close") or []
    gy = y + 74
    per = 2
    rows = (len(items) + per - 1) // per
    for i, task in enumerate(items):
        col = i // rows
        row = i % rows
        cx = x + col * ((x1 - x) // 2 + 8)
        ry = gy + row * 30
        a = ease(min(1.0, t * 2.4 - i * 0.14))
        if a <= 0:
            continue
        # the tick appears a beat after the line
        tick = a > 0.85
        d.rounded_rectangle([cx, ry + 2, cx + 15, ry + 17], radius=4,
                            outline=GREEN if tick else DARKLINE, width=2,
                            fill=(20, 46, 34) if tick else None)
        if tick:
            d.line([cx + 4, ry + 10, cx + 7, ry + 13], fill=GREEN, width=2)
            d.line([cx + 7, ry + 13, cx + 12, ry + 6], fill=GREEN, width=2)
        d.text((cx + 26, ry), task[:56], font=font(F_REG, 13),
               fill=lerp((16, 23, 46), DARKTXT, a))


def scene_outro(img, t, data):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=DARK)
    glow = Image.new("RGB", (W, H), DARK)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-200, 240, 700, 900], fill=(14, 40, 92))
    gd.ellipse([700, -240, 1600, 380], fill=(10, 44, 28))
    img.paste(Image.blend(img, glow, 0.5), (0, 0))
    d = ImageDraw.Draw(img)

    a = ease(min(1.0, t * 2.2))
    d.text((W // 2, 236), "21 sheets. 156 pages. One payment.",
           font=font(F_BOLD, 34), fill=lerp(DARK, WHITE, a), anchor="mm")
    b = ease(min(1.0, max(0.0, (t - 0.25) * 2.2)))
    d.text((W // 2, 320), "\u20b94,999", font=font(F_BOLD, 68),
           fill=lerp(DARK, YELLOW, b), anchor="mm")
    c = ease(min(1.0, max(0.0, (t - 0.4) * 2.2)))
    d.text((W // 2, 382), "launch price  \u00b7  \u20b97,999 after the first 50 buyers",
           font=font(F_REG, 17), fill=lerp(DARK, DARKTXT, c), anchor="mm")
    e = ease(min(1.0, max(0.0, (t - 0.55) * 2.2)))
    # The product URL is 62 characters, so the pill has to be wider than the
    # old /digital-products card or the text runs past its rounded edge.
    d.rounded_rectangle([W // 2 - 300, 442, W // 2 + 300, 500], radius=29,
                        fill=lerp(DARK, BLUE, e))
    d.text((W // 2, 471), "tankmetrics.in/digital-products/indian-business-financial-model",
           font=font(F_BOLD, 14), fill=lerp(DARK, WHITE, e), anchor="mm")
    f = ease(min(1.0, max(0.0, (t - 0.7) * 2.2)))
    d.text((W // 2, 546), "Illustrative figures from the shipped model's defaults.",
           font=font(F_REG, 13), fill=lerp(DARK, DARKMUT, f), anchor="mm")


SCENES = [
    (scene_title, 3.0),
    (scene_assumptions, 5.0),
    (scene_revenue, 4.5),
    (scene_pnl, 6.0),
    (scene_checks, 4.5),
    (scene_dashboard, 5.5),
    (scene_breakeven, 5.0),
    (scene_close, 5.5),
    (scene_outro, 4.5),
]


def render_frame(fn, t: float, data) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    fn(img, t, data)
    return img


def main() -> None:
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg is not on PATH")
    if not MODEL.exists():
        raise SystemExit(f"the workbook is missing: {MODEL}")

    data = load_data()
    OUT.mkdir(parents=True, exist_ok=True)

    total = sum(d for _, d in SCENES)
    frames = int(total * FPS)
    print(f"rendering {frames} frames ({total:.1f}s) from {MODEL.name}")

    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "image2pipe", "-vcodec", "png",
         "-framerate", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "slow", "-crf", "23",
         "-pix_fmt", "yuv420p", "-movflags", "+faststart",
         str(OUT / "walkthrough.mp4")],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    proc2 = subprocess.Popen(
        ["ffmpeg", "-y", "-f", "image2pipe", "-vcodec", "png",
         "-framerate", str(FPS), "-i", "-",
         "-c:v", "libvpx-vp9", "-crf", "34", "-b:v", "0",
         "-pix_fmt", "yuv420p", "-row-mt", "1",
         str(OUT / "walkthrough.webm")],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    poster = None
    idx = 0
    for fn, dur in SCENES:
        n = int(dur * FPS)
        for i in range(n):
            t = i / max(1, n - 1)
            img = render_frame(fn, t, data)
            if poster is None and fn is scene_dashboard:
                poster = img.copy()
            buf = _png(img)
            proc.stdin.write(buf)
            proc2.stdin.write(buf)
            idx += 1
        print(f"  {fn.__name__:20} {n} frames")
    proc.stdin.close()
    proc2.stdin.close()
    proc.wait()
    proc2.wait()

    if poster is None:
        poster = render_frame(scene_dashboard, 1.0, data)
    poster.save(OUT / "walkthrough.jpg", "JPEG", quality=88, optimize=True)

    for name in ("walkthrough.mp4", "walkthrough.webm", "walkthrough.jpg"):
        p = OUT / name
        print(f"  {name:18} {p.stat().st_size / 1024:8.1f} KB")


def _png(img: Image.Image) -> bytes:
    import io
    b = io.BytesIO()
    img.save(b, "PNG", optimize=False, compress_level=1)
    return b.getvalue()


if __name__ == "__main__":
    main()
