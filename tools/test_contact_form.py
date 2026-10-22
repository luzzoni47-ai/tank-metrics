"""Guards the contact form on /site/contact.html.

The form exists to catch messages from people who arrive off social media.
Every field is optional on purpose: a visitor may send only a name, only a
screenshot, or nothing at all, and must never be stopped by a browser
validation bubble or an alert(). A field that quietly becomes `required`
again, or a submit handler that throws, would silently cost real messages,
so each of those is asserted here.

Chromium is driven headlessly with --dump-dom, the same way test_layout.py
does it, so this needs no Next server and no Playwright install.
"""

import html as html_mod
import json
import re
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public"

PROBE = """<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body><pre id="out">pending</pre><script>
const f = document.createElement('iframe');
f.style.width = '100%%'; f.style.height = '900px'; f.src = '/site/contact.html';
const dialogs = [];
f.onload = async () => {
  const w = f.contentWindow, d = f.contentDocument;
  w.alert = m => dialogs.push(String(m));
  w.confirm = m => { dialogs.push(String(m)); return false; };
  const out = {};
  out.requiredCount = d.querySelectorAll('#contactForm [required]').length;
  out.phoneOnPage = d.body.innerHTML.includes('88515510022');
  out.hasFileInput = !!d.querySelector('#attachment');
  out.hasPhoneInput = !!d.querySelector('#phone');
  // Count the visible word, not a class name, so renaming the tag cannot hide it.
  out.optionalLabels = (d.querySelector('#contactForm').textContent.match(/optional/gi) || []).length;
  out.button = !!d.querySelector('#sendBtn');
  // Multiple screenshots in one go: the attribute, and the live note that
  // tells the visitor how many they picked.
  const picker = d.querySelector('#attachment');
  out.hasMultiple = !!(picker && picker.multiple);
  try {
    const dt = new DataTransfer();
    dt.items.add(new File(['aa'], 'shot-1.png', { type: 'image/png' }));
    dt.items.add(new File(['bb'], 'shot-2.png', { type: 'image/png' }));
    picker.files = dt.files;
    picker.dispatchEvent(new Event('change'));
    out.multiNote = d.querySelector('#fileNote').textContent;
  } catch (e) { out.multiNote = 'ERROR ' + e; }
  // The endpoint is a literal placeholder until the owner pastes the Apps
  // Script URL, and the form behaves differently in each state.
  const src = await (await fetch('/site/contact.js')).text();
  out.configured = !src.includes('PASTE_YOUR_APPS_SCRIPT_EXEC_URL_HERE');
  const btn = d.querySelector('#sendBtn');
  if (btn) btn.click();
  setTimeout(() => {
    const succ = d.querySelector('#formSuccess');
    const form = d.querySelector('#contactForm');
    out.thanksVisible = getComputedStyle(succ).display !== 'none';
    out.formHidden = getComputedStyle(form).display === 'none';
    out.dialogs = dialogs.length;
    document.getElementById('out').textContent = JSON.stringify(out);
  }, 2500);
};
document.body.appendChild(f);
</script></body></html>
"""

CHECKS = [
    ("requiredCount", 0, "no field may be required"),
    ("phoneOnPage", False, "the owner's phone number must not be published"),
    ("hasFileInput", True, "screenshot upload must exist"),
    ("hasPhoneInput", True, "an optional phone field must exist"),
    ("optionalLabels", 0, "no field may be tagged optional"),
    ("button", True, "submit button must exist"),
    ("hasMultiple", True, "several screenshots must be selectable at once"),
    ("thanksVisible", True, "the visitor must always get a reply on send"),
    ("dialogs", 0, "no alert() may block the visitor"),
]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> int:
    probe = PUBLIC / "_contact_probe.html"
    probe.write_text(PROBE, encoding="utf-8")
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=PUBLIC, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(40):
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    break
            except OSError:
                time.sleep(0.1)
        dom = subprocess.run(
            ["chromium", "--headless", "--disable-gpu", "--no-sandbox",
             "--window-size=390,844", "--virtual-time-budget=15000",
             "--dump-dom", f"http://127.0.0.1:{port}/_contact_probe.html"],
            capture_output=True, text=True, timeout=180,
        ).stdout
    finally:
        server.terminate()
        probe.unlink(missing_ok=True)

    m = re.search(r'<pre id="out">(.*?)</pre>', dom, re.S)
    if not m:
        print("FAIL: probe produced no output")
        return 1

    data = json.loads(html_mod.unescape(m.group(1)))
    failures = [
        f"{key}: got {data.get(key)!r}, want {want!r} ({why})"
        for key, want, why in CHECKS if data.get(key) != want
    ]

    # The collapse only happens on a real send. While the endpoint is still the
    # placeholder the form must stay open, because nothing was stored.
    want_hidden = bool(data.get("configured"))
    if data.get("formHidden") != want_hidden:
        state = "set" if want_hidden else "still a placeholder"
        failures.append(
            f"formHidden: got {data.get('formHidden')!r}, want {want_hidden!r} "
            f"(endpoint is {state})"
        )

    # Picking two files must be reported back to the visitor by name, so a
    # silent failure to attach screenshots cannot go unnoticed.
    note = str(data.get("multiNote", ""))
    if "shot-1.png" not in note or "shot-2.png" not in note:
        failures.append(
            f"multiNote: got {note!r}, want both file names listed"
        )

    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for f in failures:
            print("  " + f)
        return 1
    print(f"ALL PASS: contact form is safe (endpoint configured: {want_hidden})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
