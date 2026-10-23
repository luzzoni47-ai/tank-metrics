/* Tank Metrics site-wide menu drawer.
 *
 * The home page has its own category sidebar. Every other page used to carry a
 * menu button that was hidden and wired to nothing, so a visitor who landed on
 * a calculator from Google had no way to reach the blog, the news or another
 * tool without going back to the home page. This builds the same drawer on
 * every page: the three-dot button opens it, and the X at the BOTTOM closes it
 * (Sir asked for the close control at the bottom, where a thumb already is).
 */
(function () {
  "use strict";
  var POPULAR = [
    ["Loan EMI Calculator", "/loan-emi-calculator"],
    ["GST Calculator", "/gst-calculator"],
    ["Income Tax Calculator", "/income-tax-calculator-old-vs-new-regime"],
    ["SIP Calculator", "/sip-calculator"],
    ["Percentage Calculator", "/percentage-calculator"],
    ["Break-Even Point", "/break-even-point"],
    ["LTV:CAC Ratio", "/ltv-cac-ratio"],
    ["Burn Rate & Runway", "/burn-rate-and-runway"],
  ];
  var LINKS = [
    ["Home", "/"],
    ["News", "/news"],
    ["Blog", "/blog"],
    ["About", "/about"],
    ["Contact", "/contact"],
  ];

  // The home page ships its own category sidebar (with #sidebarClose) and
  // already wires #menuBtn to it. Leave that alone; this drawer is for the
  // pages that had a dead button.
  if (document.getElementById("sidebar")) return;

  var btn = document.getElementById("menuBtn");
  if (!btn) return;

  var drawer = null;

  function build() {
    drawer = document.createElement("aside");
    drawer.className = "nav-drawer";
    drawer.setAttribute("aria-hidden", "true");
    drawer.setAttribute("role", "dialog");
    drawer.setAttribute("aria-label", "Site menu");

    var head = document.createElement("div");
    head.className = "nav-drawer-head";
    head.innerHTML =
      '<span class="nav-drawer-mark" aria-hidden="true"><i>\u20b9</i></span>' +
      "<span><b>Tank Metrics</b><small>Simple money calculators</small></span>";
    drawer.appendChild(head);

    var nav = document.createElement("nav");
    nav.className = "nav-drawer-links";
    LINKS.forEach(function (pair) {
      var a = document.createElement("a");
      a.href = pair[1];
      a.textContent = pair[0];
      if (location.pathname === pair[1]) a.className = "active";
      nav.appendChild(a);
    });
    drawer.appendChild(nav);

    var label = document.createElement("p");
    label.className = "nav-drawer-label";
    label.textContent = "Popular calculators";
    drawer.appendChild(label);

    var list = document.createElement("div");
    list.className = "nav-drawer-tools";
    POPULAR.forEach(function (pair) {
      var a = document.createElement("a");
      a.href = pair[1];
      a.textContent = pair[0];
      list.appendChild(a);
    });
    drawer.appendChild(list);

    // The close control sits at the bottom, inside the drawer's own scroll
    // area, so it is reachable with one thumb on a phone.
    var foot = document.createElement("div");
    foot.className = "nav-drawer-foot";
    var close = document.createElement("button");
    close.type = "button";
    close.className = "nav-drawer-close";
    close.setAttribute("aria-label", "Close menu");
    close.innerHTML = "\u00d7<span>Close</span>";
    close.addEventListener("click", shut);
    foot.appendChild(close);
    drawer.appendChild(foot);

    document.body.appendChild(drawer);

    var scrim = document.createElement("div");
    scrim.className = "nav-scrim";
    scrim.addEventListener("click", shut);
    document.body.appendChild(scrim);
    drawer._scrim = scrim;
  }

  function open() {
    if (!drawer) build();
    btn.setAttribute("aria-expanded", "true");
    drawer.setAttribute("aria-hidden", "false");
    document.documentElement.classList.add("nav-open");
    // Force a reflow instead of waiting for requestAnimationFrame. The drawer
    // is appended in the same tick, so the browser needs one layout pass to
    // register the closed position before the class flip can animate it; rAF
    // gives that, but it is throttled in some headless contexts and the drawer
    // then never opens at all. Reading offsetHeight flushes the layout and the
    // transition still runs.
    void drawer.offsetHeight;
    drawer.classList.add("open");
    drawer._scrim.classList.add("open");
  }

  function shut() {
    if (!drawer) return;
    btn.setAttribute("aria-expanded", "false");
    drawer.classList.remove("open");
    drawer._scrim.classList.remove("open");
    document.documentElement.classList.remove("nav-open");
    drawer.setAttribute("aria-hidden", "true");
  }

  btn.setAttribute("aria-expanded", "false");
  btn.addEventListener("click", function (e) {
    e.preventDefault();
    e.stopPropagation();
    if (drawer && drawer.classList.contains("open")) shut();
    else open();
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") shut();
  });
})();
