/* Tank Metrics app shell: install offer, update notice, offline use.
 *
 * A returning visitor should learn three things, and never more than one at a
 * time, so all three share a single strip at the bottom of the page:
 *
 *  1. The site can be installed as an app. Chrome fires beforeinstallprompt
 *     once the site qualifies; iOS has no such event, so an iOS visitor is
 *     told to use the share sheet instead. Offered only after a minute of real
 *     use, never on arrival, and not again for a fortnight if dismissed.
 *  2. A new build is live. The service worker reports a controller change, and
 *     we offer a one-tap refresh. A first-time visitor who gets a controller
 *     for the first time is not seeing an update, so they are not told.
 *  3. New calculators or posts have landed, read from /site/updates.json. That
 *     file is never cached, so even a tab left open for hours notices a deploy.
 *     The first visit records the version silently; the banner starts with the
 *     next one. A visitor who allowed notifications also gets a real one.
 *
 * All state is local plus that static file, so the site stays a static site.
 */
(function () {
  "use strict";
  var SEEN_KEY = "tm-seen-updates";
  var OPT_IN_KEY = "tm-notify-optin";
  var INSTALL_SNOOZE = "tm-install-snooze";
  var NOTIFY_SNOOZE = "tm-notify-snooze";
  var ENGAGE_MS = 60000;      // a minute of use before we ask for anything
  var POLL_MS = 300000;       // re-check for new content every 5 minutes
  var SNOOZE_MS = 12096e5;    // a fortnight

  var banner = null;
  var installEvent = null;
  var engaged = false;

  function store(key) { try { return localStorage.getItem(key); } catch (e) { return null; } }
  function save(key, value) { try { localStorage.setItem(key, value); } catch (e) {} }
  function snoozed(key) {
    var t = parseInt(store(key) || "0", 10);
    return t && Date.now() - t < SNOOZE_MS;
  }

  function show(kind, text, actionLabel, action, onDismiss) {
    if (banner) banner.remove();
    banner = document.createElement("div");
    banner.className = "pwa-banner pwa-" + kind;
    banner.setAttribute("role", "status");
    var span = document.createElement("span");
    span.textContent = text;
    banner.appendChild(span);
    if (actionLabel && action) {
      var btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = actionLabel;
      btn.addEventListener("click", action);
      banner.appendChild(btn);
    }
    var close = document.createElement("button");
    close.type = "button";
    close.className = "pwa-x";
    close.setAttribute("aria-label", "Dismiss");
    close.textContent = "\u00d7";
    close.addEventListener("click", function () {
      if (onDismiss) onDismiss();
      banner.remove();
      banner = null;
    });
    banner.appendChild(close);
    document.body.appendChild(banner);
  }

  function hide() { if (banner) { banner.remove(); banner = null; } }

  function notify(label) {
    if (!window.Notification || Notification.permission !== "granted") return;
    try {
      new Notification("Tank Metrics", { body: label, icon: "/site/icon-192.png" });
    } catch (e) {}
  }

  // --- 1. Offline support + new-build notice ----------------------------
  if ("serviceWorker" in navigator) {
    var hadController = !!navigator.serviceWorker.controller;
    navigator.serviceWorker.register("/sw.js").catch(function () {});
    navigator.serviceWorker.addEventListener("controllerchange", function () {
      if (!hadController) return;
      show("update", "A newer version is ready.", "Refresh", function () {
        window.location.reload();
      });
    });
    // The worker only caches pages it is already controlling, so a first visit
    // would not store the page being read. Hand it over once it is in charge.
    function cacheThisPage() {
      var sw = navigator.serviceWorker.controller;
      if (sw) sw.postMessage({ type: "cache-page", url: window.location.pathname });
    }
    navigator.serviceWorker.ready.then(cacheThisPage);
    navigator.serviceWorker.addEventListener("controllerchange", cacheThisPage);
  }

  // --- 2. Install offer --------------------------------------------------
  function offerInstall() {
    if (window.matchMedia("(display-mode: standalone)").matches) return;
    if (snoozed(INSTALL_SNOOZE)) return;
    if (installEvent) {
      show("install", "Use Tank Metrics like an app, offline too.", "Install", function () {
        installEvent.prompt();
        installEvent = null;
        hide();
      }, function () { save(INSTALL_SNOOZE, String(Date.now())); });
      return;
    }
    // iOS never fires beforeinstallprompt, so point at the share sheet.
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
      show("install", "Add Tank Metrics to your home screen: tap Share, then Add to Home Screen.",
        null, null, function () { save(INSTALL_SNOOZE, String(Date.now())); });
    }
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    installEvent = e;
    // Chrome may only call this after the engagement timer has already fired.
    if (engaged) offerInstall();
  });

  function offerNotifications() {
    if (!window.Notification || Notification.permission !== "default") return;
    if (store(OPT_IN_KEY) || snoozed(NOTIFY_SNOOZE)) return;
    show("news", "Get told when new calculators are added?", "Enable", function () {
      save(OPT_IN_KEY, "1");
      Notification.requestPermission().then(function (p) {
        hide();
        if (p === "granted") notify("You will hear from us when something new lands.");
      });
    }, function () { save(NOTIFY_SNOOZE, String(Date.now())); });
  }

  setTimeout(function () {
    engaged = true;
    if (installEvent) offerInstall();
    else offerNotifications();
  }, ENGAGE_MS);

  // --- 3. New content since the last visit ------------------------------
  function announce(data) {
    var seen = store(SEEN_KEY);
    // A first-ever visit is not an update: record the version quietly so the
    // banner starts appearing from the next deploy onwards.
    if (seen === null) { save(SEEN_KEY, data.version); return; }
    if (seen === data.version) return;
    save(SEEN_KEY, data.version);
    var label = data.label || "New calculators have been added.";
    notify(label);
    show("news", label, "See what's new", function () {
      window.location.href = data.href || "/blog";
    });
  }

  function checkUpdates() {
    fetch("/site/updates.json", { cache: "no-store" })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { if (d && d.version) announce(d); })
      .catch(function () {});
  }
  checkUpdates();
  setInterval(checkUpdates, POLL_MS);
})();
