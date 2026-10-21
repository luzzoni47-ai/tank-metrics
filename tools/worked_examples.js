// Evaluate a calculator COMPUTE against supplied inputs, so the long-form
// copy can quote real, arithmetically correct numbers instead of invented ones.
// Reads {calcId: {inputs, env?}} on stdin, prints {calcId: rows} on stdout.
const fs = require("fs");
const path = require("path");
const DATA = JSON.parse(fs.readFileSync(path.join(__dirname, "calcs.json"), "utf8"));
const helpers = DATA.helpers;
const env = new Function("return function(){" + helpers + ";return {val,inr,inr2,pct,num,fmtIN,numberToWordsIndian};}")()();
let raw = "";
process.stdin.on("data", d => raw += d);
process.stdin.on("end", () => {
  const req = JSON.parse(raw || "{}");
  const out = {};
  for (const [id, spec] of Object.entries(req)) {
    const c = DATA.calcs.find(x => x.id === id);
    if (!c) { out[id] = { error: "unknown calculator " + id }; continue; }
    try {
      const fn = new Function("val", "inr", "inr2", "pct", "num", "fmtIN",
        "numberToWordsIndian", "return (" + c.compute + ")");
      const r = fn(env.val, env.inr, env.inr2, env.pct, env.num, env.fmtIN,
        env.numberToWordsIndian)(spec.inputs || {});
      out[id] = { rows: r.rows || [], tip: r.tip || null };
    } catch (e) { out[id] = { error: e.message }; }
  }
  process.stdout.write(JSON.stringify(out));
});
