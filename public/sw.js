/* Tank Metrics service worker.
 *
 * Goal: the calculators keep working with no network. Every page of the site
 * is a static HTML file that carries its own logic, so once a page has been
 * seen it can be served from cache forever.
 *
 * Strategy
 *  - Precache the shell (stylesheet, manifest, icons) on install, then read
 *    /site/precache.json and store EVERY page in it. The whole site is meant
 *    to work offline, and caching only the pages a visitor happened to open
 *    left the other 100 calculators, the blog, the news and the legal pages
 *    dead the moment the network dropped.
 *  - Navigations: network first, fall back to the cached copy of the exact
 *    page, then to the cached home page. So a fresh page when online, and
 *    something useful when offline.
 *  - Other GETs (css, js, images): cache first, refresh in the background.
 *  - Never touch a non-GET, a cross-origin request, or the Apps Script
 *    endpoint (the contact form must always reach the network).
 */
const VERSION = "tm-v2";
const SHELL = VERSION + "-shell";
const PAGES = VERSION + "-pages";
const ASSETS = VERSION + "-assets";

const SHELL_URLS = [
  "/site/style.css",
  "/site/manifest.webmanifest",
  "/site/icon-192.png",
  "/site/icon-512.png",
  "/site/favicon.svg",
  "/site/pwa.js",
];

// Pulling 124 pages in one addAll means a single 404 aborts the whole install
// and the worker never activates, which is worse than the old behaviour. Add
// them one by one and ignore the strays.
function cachePages(cache, paths) {
  return Promise.all(
    paths.map((path) =>
      cache.add(path).catch(() => {})
    )
  );
}

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(SHELL)
      .then((cache) => cache.addAll(SHELL_URLS))
      .then(() =>
        fetch("/site/precache.json", { cache: "no-store" })
          .then((r) => (r.ok ? r.json() : null))
          .then((d) => (d && d.paths ? d.paths : []))
          .catch(() => [])
      )
      .then((paths) =>
        caches.open(PAGES).then((cache) => cachePages(cache, ["/"].concat(paths)))
      )
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => !k.startsWith(VERSION))
            .map((k) => caches.delete(k))
        )
      )
      .then(() => self.clients.claim())
  );
});

function isCacheable(request, url) {
  if (request.method !== "GET") return false;
  if (url.origin !== self.location.origin) return false;
  if (url.pathname.startsWith("/site/contact.js")) return false;
  // updates.json and the worker itself must always come from the network,
  // otherwise a cached copy hides every future deploy from the visitor.
  if (url.pathname === "/site/updates.json") return false;
  if (url.pathname === "/sw.js") return false;
  return true;
}

// A page the visitor has opened while the worker was already in charge gets
// stored at once. Without this, a first visit caches only the shell and the
// very page being read would be missing offline.
self.addEventListener("message", (event) => {
  const data = event.data || {};
  if (data.type !== "cache-page" || !data.url) return;
  const url = new URL(data.url, self.location.origin);
  if (url.origin !== self.location.origin) return;
  event.waitUntil(
    fetch(url)
      .then((response) => {
        if (response && response.ok) {
          return caches.open(PAGES).then((cache) => cache.put(url.pathname, response));
        }
      })
      .catch(() => {})
  );
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);
  if (!isCacheable(request, url)) return;

  // A page view: try the network so the visitor gets the newest build, and
  // fall back to the cached page (or the home page) when offline.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request)
        .then((response) => {
          const copy = response.clone();
          caches.open(PAGES).then((cache) => cache.put(request, copy));
          return response;
        })
        .catch(() =>
          caches.match(request).then(
            (hit) => hit || caches.match("/")
          )
        )
    );
    return;
  }

  // Static assets: serve the cached copy at once and refresh it quietly.
  event.respondWith(
    caches.match(request).then((hit) => {
      const network = fetch(request)
        .then((response) => {
          if (response && response.ok) {
            const copy = response.clone();
            caches.open(ASSETS).then((cache) => cache.put(request, copy));
          }
          return response;
        })
        .catch(() => hit);
      return hit || network;
    })
  );
});
