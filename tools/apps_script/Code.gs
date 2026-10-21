/**
 * Tank Metrics — contact form receiver.
 *
 * Setup (one time):
 *   1. Create a Google Sheet, open Extensions > Apps Script.
 *   2. Delete the placeholder code and paste this whole file.
 *   3. Deploy > New deployment > Web app.
 *        Execute as:  Me
 *        Who has access:  Anyone
 *   4. Copy the /exec URL. That is the endpoint the website posts to.
 *
 * Every field is optional. Whatever the visitor fills in is stored; blank
 * fields are stored as empty strings, never as an error.
 */

var SHEET_NAME = 'Responses';
var FOLDER_NAME = 'Tank Metrics - Contact uploads';
var NOTIFY = true; // email yourself a copy of each message
var MAX_BYTES = 5 * 1024 * 1024;    // per file, matches the website's cap
var MAX_TOTAL = 10 * 1024 * 1024;   // all files together
var MAX_FILES = 5;

var HEADERS = ['Received', 'Name', 'Email', 'Phone', 'Message', 'Files', 'File links', 'Page'];

function doGet() {
  // Lets you confirm the deployment works by opening the URL in a browser.
  return reply({ ok: true, service: 'tank-metrics-contact' });
}

function doPost(e) {
  try {
    var raw = (e && e.postData && e.postData.contents) || '';
    var data = JSON.parse(raw || '{}');

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

    var sheet = getSheet();
    sheet.appendRow([
      new Date(),
      String(data.name || ''),
      String(data.email || ''),
      String(data.phone || ''),
      String(data.message || ''),
      names.join(', '),
      links.join('\n'),
      String(data.page || ''),
    ]);

    if (NOTIFY) {
      notify(data, names, links);
    }
    return reply({ ok: true });
  } catch (err) {
    // Still answer 200 with ok:false: the visitor sees the thank-you card
    // either way, and the failure is recorded here for you to inspect.
    console.error(err);
    return reply({ ok: false, error: String(err) });
  }
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
