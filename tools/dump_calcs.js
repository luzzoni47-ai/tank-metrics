// Dump CALCS/CATS plus the shared helpers out of index.html so the tool-page
// generator can reuse the exact same arithmetic as the live site.
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', 'public/site/index.html'), 'utf8');

function grabArray(name) {
  const start = src.indexOf(name + '=[');
  const from = src.indexOf('[', start);
  let depth = 0;
  for (let i = from; i < src.length; i++) {
    if (src[i] === '[') depth++;
    else if (src[i] === ']') { depth--; if (!depth) return src.slice(from, i + 1); }
  }
  throw new Error('unclosed array: ' + name);
}

function grabFunction(name) {
  const i = src.indexOf('function ' + name + '(');
  if (i < 0) return null;
  let depth = 0;
  for (let k = src.indexOf('{', i); k < src.length; k++) {
    if (src[k] === '{') depth++;
    else if (src[k] === '}') { depth--; if (!depth) return src.slice(i, k + 1); }
  }
  return null;
}

const CALCS = eval('(' + grabArray('CALCS') + ')');
const CATS = eval('(' + grabArray('CATS') + ')');
const helpers = ['fmtIN', 'val', 'inr', 'inr2', 'pct', 'num', 'twoDigits',
  'threeDigits', 'numberToWordsIndian'].map(grabFunction).filter(Boolean);
const wordArrays = ['ONES', 'TENS'].map(n => n + '=' + grabArray(n) + ';').join('\n');

const out = {
  cats: CATS,
  calcs: CALCS.map(c => ({
    id: c.id, cat: c.cat, name: c.name, desc: c.desc, bench: c.bench || '',
    inputs: c.inputs || [],
    compute: (c.compute || function () { return { rows: [] }; }).toString(),
  })),
  helpers: wordArrays + '\n' + helpers.join('\n'),
};
fs.writeFileSync(path.join(__dirname, 'calcs.json'), JSON.stringify(out, null, 1));
console.log('calcs:', out.calcs.length, '| cats:', out.cats.length, '| helpers:', helpers.length);
