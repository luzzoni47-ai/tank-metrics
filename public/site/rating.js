/* Tank Metrics rating card.
 *
 * One script, self-mounting, on every calculator page. Add
 *   <script defer src="/site/rating.js"></script>
 * and the card appears just above the site footer.
 *
 * Two things are kept, in two places, for two reasons:
 *   - the aggregate (count, average, distribution) lives in Redis, so every
 *     visitor sees the same number;
 *   - the visitor's own score lives in localStorage, so the card can say
 *     "you rated this 4" without the server ever learning who they are.
 *
 * There is no fake number anywhere in here. With no ratings the card says so,
 * plainly, and asks to be the first. A card that invented a rating would be a
 * promise the site cannot keep.
 *
 * No structured data is emitted on purpose: a self-serving aggregateRating
 * earns no stars in Google and risks a review-snippet penalty.
 */
(function () {
  "use strict";

  var API = "/api/ratings";
  var STORE_KEY = "tm:rating:";
  var STARS = 5;

  var STAR_PATH =
    "M12 2.4l2.92 5.92 6.53.95-4.73 4.6 1.12 6.5L12 17.3l-5.84 3.07 1.12-6.5-4.73-4.6 6.53-.95z";

  function toolId() {
    var p = location.pathname.replace(/\.html$/, "").replace(/^\/+|\/+$/g, "");
    if (!p || p === "index" || p === "site") return "home";
    return p.split("/").pop();
  }

  function still() {
    return !!(
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches
    );
  }

  function readLocal(id) {
    try {
      var v = parseInt(localStorage.getItem(STORE_KEY + id), 10);
      return v >= 1 && v <= STARS ? v : 0;
    } catch (e) {
      return 0;
    }
  }

  function writeLocal(id, stars) {
    try {
      localStorage.setItem(STORE_KEY + id, String(stars));
    } catch (e) {
      /* private mode — the aggregate still holds the vote */
    }
  }

  function request(method, body) {
    var init = { method: method, headers: { Accept: "application/json" } };
    if (body) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(body);
    }
    return fetch(API + "?tool=" + encodeURIComponent(toolId()), init).then(function (r) {
      if (!r.ok) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  function star(n) {
    var b = document.createElement("button");
    b.type = "button";
    b.className = "tmr__star";
    b.setAttribute("aria-label", n + (n === 1 ? " star" : " stars"));
    b.dataset.value = String(n);
    b.style.setProperty("--i", String(n - 1));
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + STAR_PATH + '"/></svg>';
    return b;
  }

  function confetti(host) {
    if (still()) return;
    var colours = ["#f2a600", "#4285f4", "#34a853", "#ff9933", "#ea4335"];
    for (var i = 0; i < 14; i++) {
      var bit = document.createElement("i");
      bit.className = "tmr__bit";
      var angle = (Math.PI * 2 * i) / 14 + Math.random() * 0.5;
      var dist = 60 + Math.random() * 80;
      bit.style.setProperty("--dx", Math.cos(angle) * dist + "px");
      bit.style.setProperty("--dy", Math.sin(angle) * dist * 0.8 + "px");
      bit.style.setProperty("--rot", Math.random() * 480 - 240 + "deg");
      bit.style.setProperty("--t", (0.9 + Math.random() * 0.4).toFixed(2) + "s");
      bit.style.borderRadius = i % 3 === 0 ? "50%" : "2px";
      bit.style.background = colours[i % colours.length];
      bit.style.animationDelay = i * 14 + "ms";
      host.appendChild(bit);
      (function (node) {
        setTimeout(function () {
          if (node.parentNode) node.parentNode.removeChild(node);
        }, 1600);
      })(bit);
    }
  }

  function build() {
    var id = toolId();
    var mine = readLocal(id);

    var root = document.createElement("section");
    root.className = "tmr";
    root.setAttribute("aria-label", "Rate this calculator");
    root.innerHTML =
      '<div class="tmr__inner">' +
      '<span class="tmr__aura" aria-hidden="true"></span>' +
      '<span class="tmr__eyebrow"><i class="tmr__pulse"></i> One tap &middot; one second</span>' +
      '<h2 class="tmr__title">Did this calculator help you?</h2>' +
      '<p class="tmr__sub"></p>' +
      '<div class="tmr__stars" role="group" aria-label="Rate from 1 to 5 stars"></div>' +
      '<div class="tmr__meta" aria-live="polite"></div>' +
      '<div class="tmr__meter"><div class="tmr__meterFill"></div></div>' +
      '<p class="tmr__note">Your score is saved in this browser. Only the ' +
      "average and the number of ratings are stored on our side.</p>" +
      "</div>";

    var inner = root.querySelector(".tmr__inner");
    var starRow = root.querySelector(".tmr__stars");
    var meta = root.querySelector(".tmr__meta");
    var sub = root.querySelector(".tmr__sub");
    var fill = root.querySelector(".tmr__meterFill");
    var buttons = [];

    for (var n = 1; n <= STARS; n++) {
      var b = star(n);
      starRow.appendChild(b);
      buttons.push(b);
    }

    if (!still()) {
      for (var s = 0; s < 5; s++) {
        var spark = document.createElement("i");
        spark.className = "tmr__spark";
        spark.style.left = 8 + Math.random() * 84 + "%";
        spark.style.top = 22 + Math.random() * 56 + "%";
        spark.style.setProperty("--dur", (7 + Math.random() * 5).toFixed(1) + "s");
        spark.style.setProperty("--delay", (Math.random() * 7).toFixed(1) + "s");
        inner.appendChild(spark);
      }
    }

    function setSub() {
      sub.textContent = mine
        ? "You rated this " + mine + " star" + (mine === 1 ? "" : "s") + ". Tap another star to change it."
        : "No sign-up, no email. Just tell us if the number made sense.";
    }

    // The fill runs left to right: each lit star pops a beat after the one
    // before it. The class is removed once the wave is over, because an
    // animation with fill-mode `both` would keep beating the hover transform.
    function paint(value, animate) {
      buttons.forEach(function (b, i) {
        var on = i < value;
        b.classList.remove("is-sweep");
        b.style.removeProperty("--sd");
        b.classList.toggle("is-lit", on);
        if (on && animate && !still()) {
          void b.offsetWidth;
          b.style.setProperty("--sd", i * 70 + "ms");
          b.classList.add("is-sweep");
          (function (node, delay) {
            setTimeout(function () {
              node.classList.remove("is-sweep");
            }, delay + 560);
          })(b, i * 70);
        }
      });
    }

    var base = null;

    function setMeta(html) {
      base = html;
      if (!starRow.dataset.hover) meta.innerHTML = html;
    }

    function showTally(count, average) {
      if (!count) {
        setMeta("<span>No ratings yet &mdash; be the first.</span>");
        fill.style.width = "0%";
        return;
      }
      var yours = mine ? '<span class="tmr__dot">&middot;</span><span class="tmr__count">you: ' + mine + " \u2605</span>" : "";
      setMeta(
        '<span class="tmr__avg">' + average.toFixed(1) + " \u2605</span>" +
          '<span class="tmr__dot">&middot;</span>' +
          '<span class="tmr__count">' + count + " rating" + (count === 1 ? "" : "s") + "</span>" +
          yours
      );
      fill.style.width = Math.round((average / STARS) * 100) + "%";
    }

    function thanks(value) {
      var lines = {
        1: "Thanks for the honest one star \u2014 tell us what to fix and we will.",
        2: "Two stars \u2014 thanks. That tells us where to improve.",
        3: "Three stars \u2014 cheers. Tell us what would make it a five.",
        4: "Four stars \u2014 that means a lot. Thank you!",
        5: "Five stars \u2014 you have made our day. Thank you!",
      };
      setMeta('<span class="tmr__thanks"><span class="tmr__check">\u2713</span> ' + lines[value] + "</span>");
    }

    // Hover preview lights stars 1..N so the row fills from the left exactly
    // the way the final rating will. Mouse-out restores the saved score, never
    // an empty row, so a saved score cannot be lost by accident.
    starRow.addEventListener("mouseover", function (e) {
      var b = e.target.closest(".tmr__star");
      if (!b) return;
      starRow.dataset.hover = b.dataset.value;
      var n = Number(b.dataset.value);
      meta.innerHTML = '<span class="tmr__preview">' + n + (n === 1 ? " star" : " stars") + "</span>";
    });
    starRow.addEventListener("mouseleave", function () {
      delete starRow.dataset.hover;
      if (base !== null) meta.innerHTML = base;
      paint(mine, false);
    });

    function rate(value) {
      var prev = mine;
      writeLocal(id, value);
      mine = value;
      setSub();
      paint(value, true);
      root.classList.add("is-lit");

      buttons[value - 1].classList.add("is-pop");
      setTimeout(function () {
        buttons[value - 1].classList.remove("is-pop");
      }, 640);

      if (!prev) confetti(inner);
      delete starRow.dataset.hover;
      thanks(value);

      request("POST", { tool: id, stars: value, prev: prev })
        .then(function (data) {
          setTimeout(function () {
            showTally(data.count || 0, data.average || 0);
          }, 4000);
        })
        .catch(function () {
          setTimeout(function () {
            meta.innerHTML =
              '<span class="tmr__count">Saved in this browser \u2014 you rated ' + value + " \u2605</span>";
          }, 4000);
        });
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function () {
        rate(parseInt(b.dataset.value, 10));
      });
    });

    starRow.addEventListener("keydown", function (e) {
      if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
      var idx = buttons.indexOf(document.activeElement);
      if (idx === -1) return;
      e.preventDefault();
      var next = e.key === "ArrowRight" ? Math.min(idx + 1, STARS - 1) : Math.max(idx - 1, 0);
      buttons[next].focus();
    });

    setSub();
    paint(mine, false);
    if (mine) root.classList.add("is-lit");
    else meta.innerHTML = '<span class="tmr__count">Tap a star \u2014 it only takes a second.</span>';

    request("GET")
      .then(function (data) {
        showTally(data.count || 0, data.average || 0);
      })
      .catch(function () {
        if (mine) showTally(0, 0);
      });

    return root;
  }

  function place(node) {
    var footer = document.querySelector("footer.site-footer") || document.querySelector("footer");
    if (footer && footer.parentNode) footer.parentNode.insertBefore(node, footer);
    else {
      var main = document.querySelector(".main") || document.querySelector("main");
      (main || document.body).appendChild(node);
    }
  }

  function mount() {
    if (document.querySelector(".tmr")) return;
    var node = build();
    place(node);

    function reveal() {
      node.classList.add("is-in");
      // Release the staggered entrance, so hover and click transforms are not
      // overridden by a finished animation.
      setTimeout(function () {
        node.classList.add("is-ready");
      }, 760);
    }

    if ("IntersectionObserver" in window) {
      var io = new IntersectionObserver(
        function (entries) {
          entries.forEach(function (entry) {
            if (!entry.isIntersecting) return;
            reveal();
            io.disconnect();
          });
        },
        { rootMargin: "0px 0px -8% 0px" }
      );
      io.observe(node);
      // The card must never stay invisible because the observer did not fire -
      // a restored scroll position, a print, or a browser that reports the
      // card as already in view all skip the callback. This is the guarantee.
      setTimeout(function () {
        if (!node.classList.contains("is-in")) {
          io.disconnect();
          reveal();
        }
      }, 2500);
    } else {
      reveal();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mount);
  } else {
    mount();
  }
})();
