/* Phone-only pagination for the listing grids (/blog Guides, /blog News, /news).
 *
 * Sir's ask: on a phone the guides grid is one long scroll of every card. Show
 * 10 at a time and put a numbered pager under them, in the logo's own colours.
 *
 * This is progressive enhancement, not a filter. Every card stays in the DOM and
 * only the visible slice is toggled with a class, so:
 *   - with JS off, or on a desktop, the full list still renders and every link
 *     stays crawlable (Google reads the DOM, not the layout);
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

  function isPhone() {
    return window.matchMedia("(max-width:760px)").matches;
  }

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
    built.push({ grid: grid, cards: cards, nav: nav, show: show });
    show(0, false);
  }

  function clear() {
    // Leaving phone width must show every card again, and tear the pager down
    // completely. Without the teardown a rotate back to portrait would find
    // `dataset.paged` still set, skip the rebuild, and leave all 45 cards
    // visible with no pager.
    built.forEach(function (item) {
      item.cards.forEach(function (c) { c.classList.remove("page-hidden"); });
      item.grid.classList.remove("paged");
      delete item.grid.dataset.paged;
      if (item.nav.parentNode) item.nav.parentNode.removeChild(item.nav);
    });
    built = [];
  }

  function build() {
    if (!isPhone()) { clear(); return; }
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
  window.addEventListener("resize", build);
})();
