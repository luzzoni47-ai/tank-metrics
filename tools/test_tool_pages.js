// Verify every generated tool page: the embedded COMPUTE must return finite
// numbers for plausible inputs, and the page must carry its SEO essentials.
// Run after tools/gen_tool_pages.py.
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const SITE = path.join(ROOT, 'public', 'site');
const TOOLS = path.join(SITE, 'tools');
const DATA = JSON.parse(fs.readFileSync(path.join(__dirname, 'calcs.json'), 'utf8'));

function slugify(name) {
  let s = name.toLowerCase().replace(/&/g, ' and ').replace(/%/g, ' percent ');
  s = s.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  return s.replace(/-{2,}/g, '-');
}
const seen = {};
const slugs = {};
const catNames = Object.fromEntries(DATA.cats.map(c => [c.id, c.name]));
for (const c of DATA.calcs) {
  let s = slugify(c.name);
  if (seen[s]) s = s + '-' + slugify(catNames[c.cat] || c.cat);
  else seen[s] = 1;
  slugs[c.id] = s;
}

const helpers = DATA.helpers;

function sampleFor(inp) {
  if (inp.type === 'date') return '1995-06-15';
  if (inp.type === 'text') return 'Rahul';
  const k = inp.k.toLowerCase();
  if (k.includes('pct') || k.includes('rate') || k.includes('margin') || k.includes('roi')) return '12';
  if (k.includes('year') || k.includes('yr')) return '5';
  if (k.includes('month')) return '24';
  if (k.includes('p') && inp.u === '₹') return '500000';
  if (inp.u === '₹') return '100000';
  return '10';
}

let failed = 0;
const problems = [];
for (const c of DATA.calcs) {
  const file = path.join(TOOLS, slugs[c.id] + '.html');
  if (!fs.existsSync(file)) { problems.push(`${c.id}: missing page`); failed++; continue; }
  const html = fs.readFileSync(file, 'utf8');

  for (const need of ['<title>', 'name="description"', 'rel="canonical"',
    'application/ld+json', '<h1>', 'data-k=', 'G-MHZ0V6HFC6']) {
    if (!html.includes(need)) { problems.push(`${c.id}: page lacks ${need}`); failed++; }
  }

  const inputs = {};
  for (const i of c.inputs) inputs[i.k] = sampleFor(i);

  let rows;
  try {
    const env = new Function('return function(){' + helpers + ';return {val,inr,inr2,pct,num,fmtIN,numberToWordsIndian};}')()();
    const fn = new Function('val', 'inr', 'inr2', 'pct', 'num', 'fmtIN',
      'numberToWordsIndian', 'return (' + c.compute + ')');
    rows = fn(env.val, env.inr, env.inr2, env.pct, env.num, env.fmtIN, env.numberToWordsIndian)(inputs).rows || [];
  } catch (e) {
    problems.push(`${c.id}: compute threw ${e.message}`);
    failed++;
    continue;
  }
  if (!rows.length) { problems.push(`${c.id}: no result rows`); failed++; continue; }
  for (const r of rows) {
    if (r.v == null || /NaN|Infinity/.test(String(r.v))) {
      problems.push(`${c.id}: bad value "${r.l}"=${r.v} inputs=${JSON.stringify(inputs)}`);
      failed++;
    }
  }
}

console.log(`pages checked: ${DATA.calcs.length}`);
if (failed) {
  console.log(`FAILURES: ${failed}`);
  problems.slice(0, 25).forEach(p => console.log('  - ' + p));
} else {
  console.log('ALL PASS: every tool page renders finite results with SEO essentials');
}
