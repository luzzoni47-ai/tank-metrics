// Run every generated tool page through a real DOM: set the inputs, fire
// input events, and confirm the readout changes and never shows NaN.
// Catches wiring regressions that a pure compute() test cannot see.
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('jsdom');

const DIR = path.join(__dirname, '..', 'public', 'site', 'tools');
const files = fs.readdirSync(DIR).filter(f => f.endsWith('.html'));

function valueFor(input, n) {
  const type = input.getAttribute('type');
  if (type === 'date') return '1995-06-15';
  if (type === 'text') return ['Rahul', 'Priya'][n % 2];
  const key = input.getAttribute('data-k') || '';
  const unit = (input.parentElement.querySelector('.unit') || {}).textContent || '';
  if (unit.includes('%') || /rate|pct|margin/i.test(key)) return '18';
  if (/year|month|tenure|period|hour|week|day/i.test(key)) return '5';
  // Distinct amounts per field, so a two-amount tool sees a real ratio
  // instead of two tiny values that round to the same displayed string.
  return ['500000', '200000', '50000', '300000'][n % 4];
}

let bad = 0;
for (const f of files) {
  const dom = new JSDOM(fs.readFileSync(path.join(DIR, f), 'utf8'),
    { runScripts: 'dangerously', pretendToBeVisual: true });
  const { document } = dom.window;
  const inputs = [...document.querySelectorAll('[data-k]')];
  if (!inputs.length) { console.log(`${f}: NO INPUTS`); bad++; continue; }
  const before = document.getElementById('out').innerHTML;
  inputs.forEach((i, n) => {
    i.value = valueFor(i, n);
    i.dispatchEvent(new dom.window.Event('input', { bubbles: true }));
  });
  const after = document.getElementById('out').innerHTML;
  if (after === before) { console.log(`${f}: readout did not change`); bad++; continue; }
  if (/NaN|Infinity|undefined/.test(after)) {
    console.log(`${f}: bad output -> ${after.replace(/<[^>]+>/g, ' ').trim()}`);
    bad++;
  }
  dom.window.close();
}
console.log(`tool pages DOM-tested: ${files.length}`);
console.log(bad ? `FAILURES: ${bad}` : 'ALL PASS: every page reacts to input with clean values');
