/**
 * Tank Metrics — contact form receiver AND licence-gated product delivery.
 *
 * Setup (one time):
 *   1. Create a Google Sheet, open Extensions > Apps Script.
 *   2. Delete the placeholder code and paste this whole file.
 *   3. Deploy > New deployment > Web app.
 *        Execute as:  Me
 *        Who has access:  Anyone
 *   4. Copy the /exec URL. That is the endpoint the website posts to.
 *   5. Put the paid files in a Drive folder named PAID_FOLDER_NAME (below).
 *      Leave them PRIVATE. Do not share them. The script reads them as you.
 *
 * Why the licence layer exists: a file that has been downloaded cannot be made
 * un-copyable, but it can be made hard to GET. The paid files have no public
 * URL at all — the only way to receive one is to present a licence key that is
 * active. Revoke the key (a refund) and delivery stops immediately.
 *
 * Actions (POST JSON, field "action"):
 *   redeem  {key, email}    -> delivers the files for an active key
 *   status  {key}           -> validity and downloads left, no delivery
 *   issue   {secret, email, name, order_id, plan}  -> creates a key (admin)
 *   revoke  {secret, key, reason}                  -> locks a key (refund)
 *   list    {secret}                               -> the licence table
 *
 * A POST with no "action" is still a contact message, exactly as before.
 */

var SHEET_NAME = 'Responses';
var LICENSE_SHEET = 'Licenses';
var LOG_SHEET = 'Access log';
var PAID_FOLDER_NAME = 'Tank Metrics - Paid products';

// Defaults for a new licence; override per issue call.
var DEFAULT_MAX_DOWNLOADS = 5;      // a genuine buyer needs one or two
var DEFAULT_VALID_DAYS = 365 * 3;   // three years

// Which files a plan unlocks. Names must match the files in the Drive folder.
var PLANS = {
  'model': ['Indian-Business-Financial-Model.xlsx'],
  'manual': ['Masterclass-Manual.pdf'],
  'bundle': ['Indian-Business-Financial-Model.xlsx', 'Masterclass-Manual.pdf'],
};

// Admin actions require this. CHANGE IT before deploying, and keep it out of
// the website's JavaScript — it is only ever used from your own terminal.
var ADMIN_SECRET = 'CHANGE-ME-BEFORE-DEPLOYING';

var LICENSE_HEADERS = ['Key', 'Name', 'Email', 'Order id', 'Plan', 'Status',
                       'Created', 'Expires', 'Downloads', 'Max downloads',
                       'Last download', 'Note'];
var LOG_HEADERS = ['When', 'Key', 'Email', 'Action', 'Result', 'Files'];
var FOLDER_NAME = 'Tank Metrics - Contact uploads';
var NOTIFY = true; // email yourself a copy of each message
var MAX_BYTES = 5 * 1024 * 1024;    // per file, matches the website's cap
var MAX_TOTAL = 10 * 1024 * 1024;   // all files together
var MAX_FILES = 5;

var HEADERS = ['Received', 'Name', 'Email', 'Phone', 'Message', 'Files', 'File links', 'Page'];

function doGet() {
  // Lets you confirm the deployment works by opening the URL in a browser.
  return reply({ ok: true, service: 'tank-metrics-contact-and-licence' });
}

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || '';
    var data = JSON.parse(raw || '{}');

    // A POST carrying an action is a licence request; anything else is a
    // contact message, so the existing form keeps working untouched.
    if (data.action) {
      return handleAction(data);
    }
    return handleContact(data);
  } catch (err) {
    // Answer 200 with ok:false: the visitor sees the thank-you card either
    // way, and the failure is recorded here for you to inspect.
    console.error(err);
    return reply({ ok: false, error: String(err) });
  }
}

// ---------------------------------------------------------------------------
// Licence actions
// ---------------------------------------------------------------------------

function handleAction(data) {
  var action = String(data.action);

  if (action === 'redeem') return redeem(data);
  if (action === 'status') return status(data);

  // Everything below is admin and needs the secret.
  if (String(data.secret || '') !== ADMIN_SECRET) {
    log('(admin)', '', action, 'denied');
    return reply({ ok: false, reason: 'denied' });
  }
  if (action === 'issue') return issue(data);
  if (action === 'revoke') return revoke(data);
  if (action === 'list') return listLicences();

  return reply({ ok: false, reason: 'unknown_action' });
}

/** A buyer presents a key and receives the files, base64-encoded. */
function redeem(data) {
  var key = normaliseKey(data.key);
  var row = findLicence(key);
  if (!row) {
    log(key, data.email || '', 'redeem', 'not_found');
    return reply({ ok: false, reason: 'not_found' });
  }

  var check = licenceState(row);
  if (!check.ok) {
    log(key, row.values[2], 'redeem', check.reason);
    return reply({ ok: false, reason: check.reason, message: check.message });
  }

  var names = PLANS[row.values[4]] || [];
  if (!names.length) {
    log(key, row.values[2], 'redeem', 'unknown_plan');
    return reply({ ok: false, reason: 'unknown_plan' });
  }

  var folder = getPaidFolder();
  var files = [];
  for (var i = 0; i < names.length; i++) {
    var it = folder.getFilesByName(names[i]);
    if (!it.hasNext()) continue;
    var f = it.next();
    files.push({
      name: names[i],
      mime: f.getMimeType(),
      data: Utilities.base64Encode(f.getBlob().getBytes()),
    });
  }

  if (!files.length) {
    log(key, row.values[2], 'redeem', 'files_missing');
    return reply({ ok: false, reason: 'files_missing' });
  }

  // Count the download only once the files are ready to send.
  var downloads = Number(row.values[8] || 0) + 1;
  var sheet = getLicenceSheet();
  sheet.getRange(row.index, 9).setValue(downloads);
  sheet.getRange(row.index, 11).setValue(new Date());

  log(key, row.values[2], 'redeem', 'delivered', names.join(', '));
  return reply({
    ok: true,
    files: files,
    downloads: downloads,
    max_downloads: Number(row.values[9] || DEFAULT_MAX_DOWNLOADS),
    licensee: row.values[1] || '',
    note: 'This copy is licensed to ' + (row.values[1] || row.values[2] || 'the buyer') +
          '. Please do not share it.',
  });
}

/** Validity without delivering, so the page can show a clear message. */
function status(data) {
  var key = normaliseKey(data.key);
  var row = findLicence(key);
  if (!row) return reply({ ok: false, reason: 'not_found' });
  var check = licenceState(row);
  if (!check.ok) return reply({ ok: false, reason: check.reason, message: check.message });
  return reply({
    ok: true,
    licensee: row.values[1] || '',
    plan: row.values[4],
    downloads: Number(row.values[8] || 0),
    max_downloads: Number(row.values[9] || DEFAULT_MAX_DOWNLOADS),
    expires: String(row.values[7] || ''),
  });
}

/** Admin: create a licence for an order. */
function issue(data) {
  var key = data.key ? normaliseKey(data.key) : newKey();
  if (findLicence(key)) return reply({ ok: false, reason: 'duplicate' });

  var plan = String(data.plan || 'bundle');
  if (!PLANS[plan]) return reply({ ok: false, reason: 'unknown_plan' });

  var days = Number(data.valid_days || DEFAULT_VALID_DAYS);
  var expires = new Date();
  expires.setDate(expires.getDate() + days);

  getLicenceSheet().appendRow([
    key,
    String(data.name || ''),
    String(data.email || ''),
    String(data.order_id || ''),
    plan,
    'active',
    new Date(),
    expires,
    0,
    Number(data.max_downloads || DEFAULT_MAX_DOWNLOADS),
    '',
    String(data.note || ''),
  ]);

  log(key, data.email || '', 'issue', 'created', plan);

  // Email the buyer their key, so you do not have to. Only when an email is
  // given, and only when asked (send_email defaults to true).
  var emailed = false;
  if (data.email && data.send_email !== false) {
    emailed = emailBuyer(String(data.email), String(data.name || ''), key,
                         plan, expires);
  }

  return reply({ ok: true, key: key, plan: plan, expires: expires,
                 emailed: emailed });
}

/** Send the buyer their key and the download link. */
function emailBuyer(email, name, key, plan, expires) {
  try {
    var site = 'https://tankmetrics.in/digital-products';
    var body = [
      'Hi ' + (name || 'there') + ',',
      '',
      'Thank you for buying the Indian Business Financial Model. Your download',
      'is ready.',
      '',
      '  1. Open ' + site,
      '  2. Scroll to "Already bought? Get your files".',
      '  3. Enter this licence key:',
      '',
      '       ' + key,
      '',
      'The key unlocks: ' + (PLANS[plan] || []).join(' and '),
      '',
      'This key is personal to you and works on up to ' +
        DEFAULT_MAX_DOWNLOADS + ' devices. It stays valid until ' +
        Utilities.formatDate(expires, 'Asia/Kolkata', 'd MMM yyyy') + '.',
      '',
      'Your copy is watermarked with your details, so please keep it to',
      'yourself. If you lose the key, reply to this email and I will resend it.',
      '',
      'Any questions about the model, just reply.',
      '',
      'Tank Metrics',
      site,
    ].join('\n');

    MailApp.sendEmail({
      to: email,
      subject: 'Your Indian Business Financial Model — licence key',
      body: body,
    });
    return true;
  } catch (e) {
    console.error(e);
    return false;
  }
}

/** Admin: lock a key. This is the refund path. */
function revoke(data) {
  var key = normaliseKey(data.key);
  var row = findLicence(key);
  if (!row) return reply({ ok: false, reason: 'not_found' });
  var sheet = getLicenceSheet();
  sheet.getRange(row.index, 6).setValue('revoked');
  sheet.getRange(row.index, 12).setValue(String(data.reason || 'refunded'));
  log(key, row.values[2], 'revoke', 'revoked', String(data.reason || 'refunded'));
  return reply({ ok: true, key: key, status: 'revoked' });
}

function listLicences() {
  var sheet = getLicenceSheet();
  var last = sheet.getLastRow();
  if (last < 2) return reply({ ok: true, licences: [] });
  var values = sheet.getRange(2, 1, last - 1, LICENSE_HEADERS.length).getValues();
  var out = [];
  for (var i = 0; i < values.length; i++) {
    var v = values[i];
    out.push({
      key: v[0], name: v[1], email: v[2], order_id: v[3], plan: v[4],
      status: v[5], created: String(v[6]), expires: String(v[7]),
      downloads: Number(v[8] || 0), max_downloads: Number(v[9] || 0),
      last_download: String(v[10]), note: v[11],
    });
  }
  return reply({ ok: true, licences: out });
}

// ---------------------------------------------------------------------------
// Licence helpers
// ---------------------------------------------------------------------------

function licenceState(row) {
  if (String(row.values[5]) !== 'active') {
    return { ok: false, reason: 'revoked',
             message: 'This licence is no longer active. If you believe that is wrong, write to us.' };
  }
  var expires = row.values[7];
  if (expires && new Date(expires).getTime() < Date.now()) {
    return { ok: false, reason: 'expired',
             message: 'This licence has expired. Write to us and we will extend it.' };
  }
  var downloads = Number(row.values[8] || 0);
  var max = Number(row.values[9] || DEFAULT_MAX_DOWNLOADS);
  if (downloads >= max) {
    return { ok: false, reason: 'limit',
             message: 'This licence has reached its download limit (' + max +
                      '). Write to us and we will reset it.' };
  }
  return { ok: true };
}

function findLicence(key) {
  if (!key) return null;
  var sheet = getLicenceSheet();
  var last = sheet.getLastRow();
  if (last < 2) return null;
  var values = sheet.getRange(2, 1, last - 1, LICENSE_HEADERS.length).getValues();
  for (var i = 0; i < values.length; i++) {
    if (normaliseKey(values[i][0]) === key) {
      return { index: i + 2, values: values[i] };
    }
  }
  return null;
}

/** Accept the key however the buyer types it: spaces, dashes, lower case. */
function normaliseKey(raw) {
  return String(raw || '').toUpperCase().replace(/[^A-Z0-9]/g, '');
}

/** A key long enough not to be guessed: TM-XXXX-XXXX-XXXX-XXXX. */
function newKey() {
  var alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no I, O, 0, 1
  var parts = [];
  for (var g = 0; g < 4; g++) {
    var s = '';
    for (var i = 0; i < 4; i++) {
      s += alphabet.charAt(Math.floor(Math.random() * alphabet.length));
    }
    parts.push(s);
  }
  return 'TM-' + parts.join('-');
}

function log(key, email, action, result, files) {
  try {
    getLogSheet().appendRow([new Date(), key || '', email || '', action || '',
                             result || '', files || '']);
  } catch (e) {
    console.error(e);
  }
}

function getLicenceSheet() {
  return sheetNamed(LICENSE_SHEET, LICENSE_HEADERS);
}

function getLogSheet() {
  return sheetNamed(LOG_SHEET, LOG_HEADERS);
}

function sheetNamed(name, headers) {
  var book = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = book.getSheetByName(name);
  if (!sheet) sheet = book.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.getRange(1, 1, 1, headers.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function getPaidFolder() {
  var it = DriveApp.getFoldersByName(PAID_FOLDER_NAME);
  return it.hasNext() ? it.next() : DriveApp.createFolder(PAID_FOLDER_NAME);
}

// ---------------------------------------------------------------------------
// Contact form (unchanged behaviour)
// ---------------------------------------------------------------------------

function handleContact(data) {
  // Honeypot: a real visitor never fills this. Answer 200 so the bot
  // believes it succeeded and does not retry.
  if (data.bot) {
    return reply({ ok: true });
  }

  // Accept both shapes: the current `files` array and the older single
  // `fileName`/`fileData` pair, so a browser holding a cached contact.js
  // still stores its upload instead of silently dropping it.
  var incoming = data.files;
  if (!incoming || !incoming.length) {
    incoming = data.fileData ? [{ name: data.fileName, dataUrl: data.fileData }] : [];
  }
  incoming = incoming.slice(0, MAX_FILES);

  var names = [];
  var links = [];
  var total = 0;

  for (var i = 0; i < incoming.length; i++) {
    var item = incoming[i] || {};
    if (!item.dataUrl || !item.name) continue;
    var bytes = String(item.dataUrl).length * 0.75;
    if (bytes > MAX_BYTES || total + bytes > MAX_TOTAL) continue;
    total += bytes;
    names.push(String(item.name));
    links.push(saveFile(String(item.name), item.dataUrl));
  }

  getSheet().appendRow([
    new Date(),
    String(data.name || ''),
    String(data.email || ''),
    String(data.phone || ''),
    String(data.message || ''),
    names.join(', '),
    links.join('\n'),
    String(data.page || ''),
  ]);

  if (NOTIFY) notify(data, names, links);
  return reply({ ok: true });
}

function getSheet() {
  var book = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = book.getSheetByName(SHEET_NAME);
  if (!sheet) {
    sheet = book.insertSheet(SHEET_NAME);
  }
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(HEADERS);
    sheet.getRange(1, 1, 1, HEADERS.length).setFontWeight('bold');
    sheet.setFrozenRows(1);
  }
  return sheet;
}

function saveFile(name, dataUrl) {
  var parts = String(dataUrl).split(',');
  var meta = parts[0] || '';
  var payload = parts[1] || '';
  var mime = (meta.match(/data:([^;]+)/) || [])[1] || 'application/octet-stream';

  // A base64 string grows ~33% over the raw bytes.
  if (payload.length * 0.75 > MAX_BYTES) {
    throw new Error('file too large');
  }

  var blob = Utilities.newBlob(Utilities.base64Decode(payload), mime, name);
  var folder = getFolder();
  return folder.createFile(blob).getUrl();
}

function getFolder() {
  var it = DriveApp.getFoldersByName(FOLDER_NAME);
  return it.hasNext() ? it.next() : DriveApp.createFolder(FOLDER_NAME);
}

function notify(data, names, links) {
  var who = String(data.name || 'Someone');
  var lines = [
    'New message from the Tank Metrics contact form.',
    '',
    'Name:    ' + (data.name || '(not given)'),
    'Email:   ' + (data.email || '(not given)'),
    'Phone:   ' + (data.phone || '(not given)'),
    'Message: ' + (data.message || '(not given)'),
    'Files:   ' + (names.length ? names.join(', ') : '(none)'),
  ];
  for (var i = 0; i < links.length; i++) {
    lines.push('Link:    ' + links[i]);
  }
  MailApp.sendEmail({
    to: Session.getEffectiveUser().getEmail(),
    subject: 'Tank Metrics contact: ' + who,
    body: lines.join('\n'),
  });
}

function reply(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
