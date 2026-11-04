/* Numbered pagination for the listing grids (/blog Guides, /blog News, /news).
 *
 * Sir's ask: show 10 cards at a time on both a phone and a PC, and put a
 * numbered pager (1 2 3 4 ...) under them in the logo's own colours. The
 * numbers run green, blue, red, yellow, slate, so a click always moves.
 *
 * This is progressive enhancement, not a filter. Every card stays in the DOM and
 * only the visible slice is toggled with a class, so:
 *   - with JS off the full list still renders and every link stays crawlable
 *     (Google reads the DOM, not the layout);
 *   - the tabs in blog.html keep working, because nothing is added or removed
 *     from the grid, only hidden.
 *
 * Re-running is safe: a grid that already carries a pager is skipped.
 */
(function () {
  "use strict";

  var PAGE_SIZE = 10;
  var GRIDS = [".blog-grid", "#newsGrid", "#guidesGrid"];
  // The logo palette, in order: green, blue, red, yellow, then a neutral slate
  // so a run of five pages never repeats a colour.
  var COLORS = ["#34a853", "#4285f4", "#ea4335", "#f2a600", "#7b8794"];
  var built = [];

  function pager(grid) {
    var cards = [].filter.call(grid.children, function (el) {
      return el.classList && el.classList.contains("blog-card");
    });
    if (cards.length <= PAGE_SIZE) return;

    var pages = Math.ceil(cards.length / PAGE_SIZE);
    var nav = document.createElement("nav");
    nav.className = "page-nav";
    nav.setAttribute("aria-label", "Pages");
    var buttons = [];

    function show(n, scroll) {
      cards.forEach(function (card, i) {
        var onPage = Math.floor(i / PAGE_SIZE) === n;
        card.classList.toggle("page-hidden", !onPage);
      });
      buttons.forEach(function (b, i) {
        b.classList.toggle("active", i === n);
        b.setAttribute("aria-current", i === n ? "page" : "false");
      });
      // Only scroll on a tap. Scrolling on the first render would yank the
      // page down when a visitor lands on /blog.
      if (scroll) grid.scrollIntoView({ block: "start", behavior: "smooth" });
    }

    for (var i = 0; i < pages; i++) {
      (function (n) {
        var b = document.createElement("button");
        b.type = "button";
        b.className = "page-num";
        b.textContent = String(n + 1);
        b.style.setProperty("--pg", COLORS[n % COLORS.length]);
        b.setAttribute("aria-label", "Page " + (n + 1) + " of " + pages);
        b.addEventListener("click", function () { show(n, true); });
        nav.appendChild(b);
        buttons.push(b);
      })(i);
    }

    grid.parentNode.insertBefore(nav, grid.nextSibling);
    grid.classList.add("paged");
    built.push({ grid: grid, cards: cards, nav: nav });
    show(0, false);
  }

  function build() {
    GRIDS.forEach(function (sel) {
      [].forEach.call(document.querySelectorAll(sel), function (grid) {
        if (grid.dataset.paged) return;
        var cards = grid.querySelectorAll(".blog-card");
        if (cards.length <= PAGE_SIZE) return;
        grid.dataset.paged = "1";
        pager(grid);
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }
  // No resize teardown: the page size is the same on every width now, so a
  // rotate or a window drag must not rebuild the pager or lose the current page.
  // build() is idempotent (grid.dataset.paged guard), so calling it again on a
  // resize that revealed new cards is safe.
  window.addEventListener("resize", build);
})();
