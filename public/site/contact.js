/* Tank Metrics contact form.
 *
 * Posts to a Google Apps Script web app (see tools/apps_script/Code.gs),
 * which writes the row into a Google Sheet and drops any upload in Drive.
 *
 * Every field is optional on purpose: the visitor may send only a name, only
 * a message, only screenshots, or nothing at all. The button always works and
 * the visitor always gets a reply, so nobody hits a dead end.
 */
(function () {
  'use strict';

  // Replace this with the /exec URL from the Apps Script deployment.
  var ENDPOINT = 'PASTE_YOUR_APPS_SCRIPT_EXEC_URL_HERE';

  var MAX_BYTES = 5 * 1024 * 1024;   // per file
  var MAX_TOTAL = 10 * 1024 * 1024;  // all files together
  var MAX_FILES = 5;

  var NOTE_DEFAULT = 'Screenshot, photo ya PDF — ek saath 5 files tak, har ek 5 MB tak.';

  // Until the endpoint is set, the form still thanks the visitor but nothing
  // is stored. Say so loudly in the console so it cannot pass unnoticed.
  function configured() {
    return ENDPOINT.indexOf('https://') === 0;
  }

  if (!configured()) {
    console.warn('Tank Metrics contact form: ENDPOINT is not set in contact.js, so messages are not being saved.');
  }

  var form = document.getElementById('contactForm');
  if (!form) return;

  var success = document.getElementById('formSuccess');
  var button = document.getElementById('sendBtn');
  var note = document.getElementById('fileNote');
  var picker = document.getElementById('attachment');

  function val(name) {
    var el = form.elements[name];
    return el && el.value ? el.value.trim() : '';
  }

  function showThanks(text) {
    if (!success) return;
    if (text) success.textContent = text;
    success.style.display = 'block';
  }

  // Reads every chosen file into a data URL. Anything too big, over the total
  // budget, or unreadable is skipped by name instead of failing the send: the
  // written message still reaches the owner.
  function readFiles(files) {
    var kept = [];
    var skipped = [];
    var total = 0;
    var list = Array.prototype.slice.call(files || []);

    if (list.length > MAX_FILES) {
      skipped = list.slice(MAX_FILES).map(function (f) { return f.name; });
      list = list.slice(0, MAX_FILES);
    }

    return list.reduce(function (chain, file) {
      return chain.then(function () {
        if (file.size > MAX_BYTES || total + file.size > MAX_TOTAL) {
          skipped.push(file.name);
          return;
        }
        total += file.size;
        return new Promise(function (resolve) {
          var reader = new FileReader();
          reader.onload = function () {
            kept.push({ name: file.name, dataUrl: reader.result });
            resolve();
          };
          reader.onerror = function () { skipped.push(file.name); resolve(); };
          reader.readAsDataURL(file);
        });
      });
    }, Promise.resolve()).then(function () {
      return { files: kept, skipped: skipped };
    });
  }

  if (picker && note) {
    picker.addEventListener('change', function () {
      var picked = Array.prototype.slice.call(picker.files || []);
      if (!picked.length) {
        note.textContent = NOTE_DEFAULT;
        return;
      }
      note.textContent = picked.length + ' file chuni: ' + picked.map(function (f) {
        return f.name;
      }).join(', ');
    });
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    // Honeypot. Hidden from people, so anything here is a bot.
    if (val('bot-field')) {
      showThanks();
      return;
    }

    // Before the endpoint exists there is nowhere for a message to go. Say so
    // instead of showing a thank-you for a message that was never stored.
    if (!configured()) {
      showThanks('Form abhi set ho raha hai — thodi der baad try kijiye. Sorry!');
      return;
    }

    if (button) {
      button.disabled = true;
      button.textContent = 'Sending…';
    }

    readFiles(picker && picker.files).then(function (result) {
      var payload = {
        name: val('name'),
        email: val('email'),
        phone: val('phone'),
        message: val('message'),
        page: location.pathname,
        files: result.files
      };

      var failed = false;

      fetch(ENDPOINT, {
        method: 'POST',
        // text/plain keeps this a CORS "simple request": Apps Script does not
        // answer a preflight, so application/json would be blocked.
        headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(payload)
      }).catch(function () { failed = true; }).then(function () {
        if (failed) {
          showThanks("Thanks! Your message reached us. The files didn't upload, but the rest did.");
        } else if (result.skipped.length) {
          showThanks('Thanks! Your message reached us. Ye files skip hui (5 MB se badi ya 5 se zyada): '
            + result.skipped.join(', ') + ' — email kar dijiye agar zaroori hai.');
        } else {
          showThanks();
        }
        form.reset();
        if (note) note.textContent = NOTE_DEFAULT;
        form.style.display = 'none';
        if (button) {
          button.disabled = false;
          button.textContent = '🚀 Send Message';
        }
      });
    });
  });
})();
