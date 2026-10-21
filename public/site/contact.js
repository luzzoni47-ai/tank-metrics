/* Tank Metrics contact form.
 *
 * Posts to a Google Apps Script web app (see tools/apps_script/Code.gs),
 * which writes the row into a Google Sheet and drops any upload in Drive.
 *
 * Every field is optional on purpose: the visitor may send only a name, only
 * a message, only a screenshot, or nothing at all. The button always works and
 * the thank-you card always appears, so a visitor never hits a dead end.
 */
(function () {
  'use strict';

  // Replace this with the /exec URL from the Apps Script deployment.
  var ENDPOINT = 'PASTE_YOUR_APPS_SCRIPT_EXEC_URL_HERE';

  var MAX_BYTES = 5 * 1024 * 1024;

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

  function readFile(file) {
    return new Promise(function (resolve) {
      if (!file) return resolve(null);
      if (file.size > MAX_BYTES) return resolve('too-big');
      var reader = new FileReader();
      reader.onload = function () { resolve(reader.result); };
      reader.onerror = function () { resolve('unreadable'); };
      reader.readAsDataURL(file);
    });
  }

  if (picker && note) {
    picker.addEventListener('change', function () {
      var f = picker.files && picker.files[0];
      if (!f) return;
      note.textContent = f.name + ' — ' + Math.round(f.size / 1024) + ' KB';
    });
  }

  form.addEventListener('submit', function (event) {
    event.preventDefault();

    // Honeypot. Hidden from people, so anything here is a bot.
    if (val('bot-field')) {
      showThanks();
      return;
    }

    var file = picker && picker.files ? picker.files[0] : null;

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

    readFile(file).then(function (dataUrl) {
      var payload = {
        name: val('name'),
        email: val('email'),
        phone: val('phone'),
        message: val('message'),
        page: location.pathname,
        fileName: dataUrl && dataUrl !== 'too-big' && file ? file.name : '',
        fileData: dataUrl && dataUrl !== 'too-big' ? dataUrl : ''
      };

      var oversized = dataUrl === 'too-big';
      var failed = oversized || dataUrl === 'unreadable';

      var send = (failed || !configured())
        ? Promise.resolve()
        : fetch(ENDPOINT, {
            method: 'POST',
            // text/plain keeps this a CORS "simple request": Apps Script does
            // not answer a preflight, so application/json would be blocked.
            headers: { 'Content-Type': 'text/plain;charset=utf-8' },
            body: JSON.stringify(payload)
          }).catch(function () { failed = true; });

      send.then(function () {
        if (oversized) {
          showThanks('Thanks! Your message reached us. The file was over 5 MB, so it was skipped — email it across if it matters.');
        } else if (failed) {
          showThanks("Thanks! We got your message. The file didn't upload, but the rest did.");
        } else {
          showThanks();
        }
        form.reset();
        if (note) note.textContent = 'Photo, PDF ya document — 5 MB tak.';
        form.style.display = 'none';
        if (button) {
          button.disabled = false;
          button.textContent = '🚀 Send Message';
        }
      });
    });
  });
})();
