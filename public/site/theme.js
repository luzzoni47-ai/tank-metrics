/* Tank Metrics theme switch and scroll progress.
 *
 * One script on every page, so the two things a visitor expects to follow them
 * around - the light/dark choice and the reading position - behave the same
 * everywhere.
 *
 * The choice is stored as "light" or "dark" in localStorage, and the stored
 * value wins over the operating system. `theme-init.js`, a tiny inline script
 * in the head, applies the stored value before the first paint; without it a
 * dark-mode visitor sees a white flash on every navigation, because this file
 * is deferred.
 *
 * A first-time visitor follows their system, and keeps following it while it
 * changes, until they tap the switch once. After that the tap is the rule.
 */
(function () {
  "use strict";

  var KEY = "tm:theme";
  var root = document.documentElement;

  function stored() {
    try {
      var v = localStorage.getItem(KEY);
      return v === "light" || v === "dark" ? v : null;
    } catch (e) {
      return null;
    }
  }

  function save(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (e) {
      /* private mode — the choice lasts for this page only */
    }
  }

  // Every browser this site targets has matchMedia, but a page that throws
  // here would lose the switch entirely, so the guard is cheap insurance and
  // lets the file run under a test DOM.
  var media =
    window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)");

  function current() {
    return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
  }

  function apply(value) {
    root.setAttribute("data-theme", value);
    // The address-bar tint follows the page, or the browser chrome clashes.
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", value === "dark" ? "#0E1116" : "#FF9933");
    var btn = document.getElementById("themeBtn");
    if (btn) {
      var next = value === "dark" ? "light" : "dark";
      btn.setAttribute("aria-label", "Switch to " + next + " mode");
      btn.title = "Switch to " + next + " mode";
      btn.dataset.next = next;
    }
  }

  // A visitor who has never chosen follows the system, live.
  if (media) {
    media.addEventListener("change", function (e) {
      if (!stored()) apply(e.matches ? "dark" : "light");
    });
  }

  function button() {
    var b = document.createElement("button");
    b.type = "button";
    b.id = "themeBtn";
    b.className = "theme-btn";
    b.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" ' +
      'stroke-linecap="round" aria-hidden="true">' +
      '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4' +
      'M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
    b.addEventListener("click", function () {
      var next = current() === "dark" ? "light" : "dark";
      save(next);
      apply(next);
    });
    return b;
  }

  // The switch goes next to the menu button, which every page already has in
  // the same place. The home page has its own nav, so it gets the same button
  // inserted before its menu button.
  function mount() {
    if (document.getElementById("themeBtn")) return;
    var menu = document.getElementById("menuBtn");
    if (menu && menu.parentNode) menu.parentNode.insertBefore(button(), menu);
    else {
      var host = document.querySelector(".topbar-inner") || document.querySelector(".nav-inner");
      if (host) host.appendChild(button());
    }
    apply(current());
  }

  /* ---- scroll progress ---- */
  function progress() {
    var bar = document.createElement("div");
    bar.className = "scroll-progress";
    bar.setAttribute("aria-hidden", "true");
    bar.innerHTML = "<i></i>";
    document.body.appendChild(bar);
    var fill = bar.firstChild;
    var ticking = false;

    function paint() {
      ticking = false;
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var pct = max > 0 ? (doc.scrollTop / max) * 100 : 0;
      fill.style.width = (pct < 0.2 ? 0 : pct) + "%";
    }

    window.addEventListener(
      "scroll",
      function () {
        if (ticking) return;
        ticking = true;
        window.requestAnimationFrame(paint);
      },
      { passive: true }
    );
    window.addEventListener("resize", paint, { passive: true });
    paint();
  }

  function start() {
    mount();
    progress();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
