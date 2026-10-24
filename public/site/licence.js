/**
 * Tank Metrics — licence-gated download for the paid products.
 *
 * A buyer types the licence key they received with their order. The key is sent
 * to the Apps Script endpoint, which checks it against the Licenses sheet and,
 * only if it is active, returns the files as base64. The page turns that into a
 * download.
 *
 * Why the files are not simply linked: a public URL cannot be taken back. A key
 * can. Mark the licence "revoked" after a refund and the next redeem fails.
 *
 * Set ENDPOINT to the same /exec URL used by contact.js.
 */
(function () {
  'use strict';

  var ENDPOINT = 'https://script.google.com/macros/s/AKfycbzkt-62Lx2vjUsJaOEMk4Te6yMfZKXnAZhzz4yE0hvERa6DPJs31iYRBWtzosU5-m6c/exec';

  var form = document.getElementById('licence-form');
  if (!form) return;

  var input = document.getElementById('licence-key');
  var button = document.getElementById('licence-submit');
  var out = document.getElementById('licence-result');

  function configured() {
    return ENDPOINT.indexOf('https://') === 0;
  }

  function say(kind, html) {
    out.className = 'licence-result licence-' + kind;
    out.innerHTML = html;
    out.hidden = false;
  }

  function busy(on) {
    button.disabled = on;
    button.textContent = on ? 'Checking…' : 'Get my files';
  }

  // Turn a base64 payload into a Blob and hand it to the browser.
  function saveFile(file) {
    var bin = atob(file.data);
    var bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    var blob = new Blob([bytes], { type: file.mime || 'application/octet-stream' });
    var url = URL.createObjectURL(blob);
    var a = document.createElement('a');
    a.href = url;
    a.download = file.name;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // Give the browser a moment to start the download before releasing it.
    setTimeout(function () { URL.revokeObjectURL(url); }, 60000);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();

    var key = (input.value || '').trim();
    if (key.length < 8) {
      say('bad', 'Please enter the full licence key from your order email. It looks like <code>TM-XXXX-XXXX-XXXX-XXXX</code>.');
      return;
    }
    if (!configured()) {
      say('bad', 'Downloads are not switched on yet. Please email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a> with your order and I will send the files directly.');
      return;
    }

    busy(true);
    say('info', 'Checking your licence…');

    // text/plain avoids a CORS preflight, which Apps Script does not answer.
    fetch(ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain;charset=utf-8' },
      body: JSON.stringify({ action: 'redeem', key: key })
    })
      .then(function (r) { return r.json(); })
      .then(function (res) {
        busy(false);

        if (!res || !res.ok) {
          var reason = res && res.reason;
          if (reason === 'not_found') {
            say('bad', 'That key was not found. Please check for a typo, or email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a> with your order number.');
          } else if (reason === 'revoked') {
            say('bad', 'This licence is no longer active. If you think that is a mistake, email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a>.');
          } else if (reason === 'expired') {
            say('bad', 'This licence has expired. Email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a> and I will extend it.');
          } else if (reason === 'limit') {
            say('bad', 'This key has reached its download limit. Email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a> and I will reset it.');
          } else if (reason === 'files_missing') {
            say('bad', 'The files are not attached to your order yet. Email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a> and I will send them today.');
          } else {
            say('bad', 'Something went wrong. Please try again, or email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a>.');
          }
          return;
        }

        var names = [];
        for (var i = 0; i < res.files.length; i++) {
          saveFile(res.files[i]);
          names.push(res.files[i].name);
        }

        var left = Math.max(0, (res.max_downloads || 0) - (res.downloads || 0));
        var who = res.licensee ? (' Licensed to ' + res.licensee + '.') : '';
        say('good',
            '<strong>Thank you. Your download has started.</strong>' + who +
            ' This copy is watermarked with your details, so please keep it to ' +
            'yourself. You have ' + left + ' download' + (left === 1 ? '' : 's') +
            ' left on this key.');
      })
      .catch(function () {
        busy(false);
        say('bad', 'Could not reach the licence server. Please check your connection and try again, or email <a href="mailto:hello@tankmetrics.in">hello@tankmetrics.in</a>.');
      });
  });
})();
