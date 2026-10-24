#!/usr/bin/env python3
"""The stylesheet for the Indian Business Financial Model landing page.

Kept in its own module so `gen_landing_page.py` reads as page structure rather
than 600 lines of CSS.

Everything is scoped under `.lp` (landing page). The site's global style.css
styles bare `h2`, `.card`, `.grid` and `.btn-primary`, so an unscoped rule here
would quietly restyle the 127 pages that share that file. The scope also lets
this page use Poppins throughout while the rest of the site keeps Gloock
headings, which is what the product's own brand asks for.

Colour tokens are the brand palette, not the site palette: the product has its
own navy/blue/green/yellow/red and a dark hero, and it must not inherit the
saffron accents used by the calculators.
"""

LP_CSS = """
.lp{
  --lp-navy:#000E9B; --lp-blue:#1678FD; --lp-green:#21A542;
  --lp-yellow:#FAB802; --lp-red:#F0342B;
  --lp-ink:#0B1020; --lp-ink-2:#2A3350; --lp-muted:#5A6480;
  --lp-line:#E3E8F2; --lp-bg:#F7F9FC; --lp-dark:#070B18; --lp-dark-2:#0D1428;
  --lp-card:#FFFFFF;
  --lp-radius:18px; --lp-radius-sm:12px;
  --lp-shadow:0 1px 2px rgba(11,16,32,.04),0 8px 24px rgba(11,16,32,.06);
  --lp-shadow-lg:0 2px 4px rgba(11,16,32,.05),0 24px 56px rgba(11,16,32,.12);
  --lp-wrap:1160px;
  background:var(--lp-bg); color:var(--lp-ink);
  font-family:Poppins,sans-serif; -webkit-font-smoothing:antialiased;
  overflow-x:hidden;
}
.lp *{box-sizing:border-box}
.lp h1,.lp h2,.lp h3,.lp h4,.lp p,.lp ul,.lp ol,.lp li,.lp figure{margin:0;padding:0}
.lp ul,.lp ol{list-style:none}
.lp h1,.lp h2,.lp h3,.lp h4{font-family:Poppins,sans-serif;font-weight:700;letter-spacing:-.02em;line-height:1.15}
.lp a{color:inherit;text-decoration:none}
.lp img,.lp svg{display:block;max-width:100%}
.lp .wrap{max-width:var(--lp-wrap);margin:0 auto;padding:0 22px}
.lp .sec{padding:78px 0}
.lp .sec-tight{padding:54px 0}
.lp .eyebrow{
  display:inline-flex;align-items:center;gap:8px;font-size:12px;font-weight:600;
  letter-spacing:.09em;text-transform:uppercase;color:var(--lp-blue);
  background:rgba(22,120,253,.09);border:1px solid rgba(22,120,253,.2);
  padding:6px 13px;border-radius:999px;margin-bottom:16px;
}
.lp .sec-head{max-width:760px;margin:0 auto 46px;text-align:center}
.lp .sec-head h2{font-size:clamp(26px,3.4vw,40px);margin-bottom:14px}
.lp .sec-head p{color:var(--lp-muted);font-size:16px;line-height:1.7}
.lp .lead{color:var(--lp-muted);font-size:16px;line-height:1.75}
.lp .grad-text{
  background:linear-gradient(96deg,var(--lp-blue),var(--lp-green));
  -webkit-background-clip:text;background-clip:text;color:transparent;
}

/* ---------- buttons ---------- */
.lp .btn{
  display:inline-flex;align-items:center;justify-content:center;gap:9px;
  font-family:Poppins,sans-serif;font-weight:600;font-size:15px;
  padding:15px 28px;border-radius:999px;border:1.5px solid transparent;
  cursor:pointer;transition:transform .18s cubic-bezier(.34,1.56,.64,1),
  box-shadow .18s ease,background .18s ease,border-color .18s ease;
  text-align:center;line-height:1.2;
}
.lp .btn-primary{
  color:#fff;background:linear-gradient(100deg,var(--lp-navy),var(--lp-blue) 55%,var(--lp-blue));
  box-shadow:0 10px 26px rgba(22,120,253,.32);
}
.lp .btn-primary:hover{transform:translateY(-2px);box-shadow:0 16px 36px rgba(22,120,253,.4)}
.lp .btn-ghost{color:var(--lp-ink);background:#fff;border-color:var(--lp-line)}
.lp .btn-ghost:hover{border-color:var(--lp-blue);color:var(--lp-blue);transform:translateY(-2px)}
.lp .btn-dark{color:#fff;background:rgba(255,255,255,.09);border-color:rgba(255,255,255,.26)}
.lp .btn-dark:hover{background:rgba(255,255,255,.16);transform:translateY(-2px)}
.lp .btn-block{width:100%}
.lp .btn:focus-visible,.lp a:focus-visible,.lp summary:focus-visible,
.lp button:focus-visible,.lp input:focus-visible{
  outline:2.5px solid var(--lp-blue);outline-offset:3px;border-radius:6px;
}
.lp .btn-row{display:flex;flex-wrap:wrap;gap:14px}

/* ---------- hero ---------- */
.lp .hero{
  position:relative;background:var(--lp-dark);color:#fff;overflow:hidden;
  padding:76px 0 84px;
}
.lp .hero::before{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:
    radial-gradient(720px 420px at 12% -8%,rgba(22,120,253,.30),transparent 62%),
    radial-gradient(560px 380px at 88% 6%,rgba(33,165,66,.20),transparent 60%),
    radial-gradient(520px 360px at 62% 108%,rgba(0,14,155,.42),transparent 62%);
}
.lp .hero::after{
  content:"";position:absolute;inset:0;pointer-events:none;opacity:.5;
  background-image:linear-gradient(rgba(255,255,255,.045) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(255,255,255,.045) 1px,transparent 1px);
  background-size:58px 58px;
  -webkit-mask-image:radial-gradient(ellipse 88% 72% at 50% 22%,#000,transparent 76%);
  mask-image:radial-gradient(ellipse 88% 72% at 50% 22%,#000,transparent 76%);
}
.lp .hero .wrap{position:relative;z-index:2}
.lp .hero-grid{display:grid;grid-template-columns:1.02fr .98fr;gap:56px;align-items:center}
.lp .hero-tag{
  display:inline-flex;align-items:center;gap:9px;font-size:12.5px;font-weight:600;
  letter-spacing:.05em;text-transform:uppercase;color:#DCE6FF;
  background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18);
  padding:7px 14px;border-radius:999px;margin-bottom:22px;
}
.lp .hero-tag .dot{width:7px;height:7px;border-radius:50%;background:var(--lp-green);
  box-shadow:0 0 0 4px rgba(33,165,66,.22)}
.lp .hero h1{font-size:clamp(31px,4.5vw,54px);line-height:1.08;margin-bottom:20px}
.lp .hero h1 em{
  font-style:normal;
  background:linear-gradient(96deg,#63A9FF,#7BE39A);
  -webkit-background-clip:text;background-clip:text;color:transparent;
}
.lp .hero .sub{color:#B9C4E0;font-size:clamp(15px,1.55vw,17.5px);line-height:1.72;max-width:56ch}
.lp .hero-cta{margin-top:32px}
.lp .hero-note{margin-top:16px;font-size:13px;color:#8E9BC0}
.lp .hero-note a{color:#B9C4E0;text-decoration:underline}
.lp .facts{
  display:flex;flex-wrap:wrap;gap:10px;margin-top:30px;padding-top:26px;
  border-top:1px solid rgba(255,255,255,.12);
}
.lp .fact{
  display:flex;flex-direction:column;gap:2px;padding:11px 15px;border-radius:12px;
  background:rgba(255,255,255,.055);border:1px solid rgba(255,255,255,.12);
  min-width:104px;
}
.lp .fact b{font-size:17px;font-weight:700;color:#fff}
.lp .fact span{font-size:11.5px;color:#93A0C4;letter-spacing:.02em}

/* ---------- hero mockup ---------- */
.lp .mock{
  position:relative;border-radius:20px;padding:15px;
  background:linear-gradient(160deg,rgba(255,255,255,.13),rgba(255,255,255,.05));
  border:1px solid rgba(255,255,255,.16);
  box-shadow:0 30px 70px rgba(0,0,0,.5);
  backdrop-filter:blur(3px);
}
.lp .mock-bar{display:flex;align-items:center;gap:7px;padding:0 3px 12px}
.lp .mock-bar i{width:10px;height:10px;border-radius:50%;display:block}
.lp .mock-bar i:nth-child(1){background:#FF6058}
.lp .mock-bar i:nth-child(2){background:#FFBD2E}
.lp .mock-bar i:nth-child(3){background:#28C840}
.lp .mock-bar span{margin-left:8px;font-size:11.5px;color:#93A0C4;letter-spacing:.04em}
.lp .mock-body{
  background:#0B1226;border-radius:13px;border:1px solid rgba(255,255,255,.09);
  padding:15px;display:grid;gap:12px;
}
.lp .kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}
.lp .kpi{
  background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.09);
  border-radius:10px;padding:10px 11px;
}
.lp .kpi small{display:block;font-size:9.5px;color:#8593B8;letter-spacing:.06em;
  text-transform:uppercase;margin-bottom:4px}
.lp .kpi b{font-size:15px;color:#fff;font-weight:700}
.lp .kpi .up{font-size:10px;color:#5BD98A;font-weight:600;margin-left:4px}
.lp .chart{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-radius:10px;padding:11px}
.lp .chart .cap{display:flex;justify-content:space-between;font-size:10px;
  color:#8593B8;margin-bottom:8px}
.lp .chart .cap b{color:#C9D4EE;font-weight:600}
.lp .sheet{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
  border-radius:10px;padding:11px;overflow:hidden}
.lp .sheet .cap{font-size:10px;color:#8593B8;margin-bottom:8px;display:flex;
  justify-content:space-between}
.lp .sheet table{width:100%;border-collapse:collapse;font-size:10.5px;
  font-variant-numeric:tabular-nums}
.lp .sheet th{text-align:left;color:#8593B8;font-weight:600;font-size:9.5px;
  padding:3px 5px;border-bottom:1px solid rgba(255,255,255,.09)}
.lp .sheet td{padding:3.5px 5px;color:#C9D4EE;border-bottom:1px solid rgba(255,255,255,.05)}
.lp .sheet td:not(:first-child),.lp .sheet th:not(:first-child){text-align:right}
.lp .sheet tr.ok td:first-child{color:#5BD98A}
.lp .sheet tr.ok td:last-child{color:#5BD98A}
.lp .badge{
  position:absolute;display:flex;align-items:center;gap:8px;padding:10px 14px;
  border-radius:13px;background:#fff;color:var(--lp-ink);
  box-shadow:0 14px 34px rgba(0,0,0,.34);font-size:12.5px;font-weight:600;
}
.lp .badge svg{flex:none}
.lp .badge-a{top:-16px;left:-14px}
.lp .badge-b{bottom:-18px;right:-10px}
.lp .badge small{display:block;font-size:10px;color:var(--lp-muted);font-weight:500}

/* ---------- logo/trust strip ---------- */
.lp .strip{background:#fff;border-bottom:1px solid var(--lp-line);padding:26px 0}
.lp .strip-in{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;
  gap:14px 34px}
.lp .strip span{display:flex;align-items:center;gap:9px;font-size:13.5px;
  color:var(--lp-ink-2);font-weight:500}
.lp .strip svg{color:var(--lp-green);flex:none}

/* ---------- generic cards ---------- */
.lp .cards{display:grid;gap:18px}
.lp .cards-2{grid-template-columns:repeat(2,1fr)}
.lp .cards-3{grid-template-columns:repeat(3,1fr)}
.lp .cards-4{grid-template-columns:repeat(4,1fr)}
.lp .card{
  background:var(--lp-card);border:1px solid var(--lp-line);
  border-radius:var(--lp-radius);padding:26px 24px;
  box-shadow:var(--lp-shadow);display:flex;flex-direction:column;gap:11px;
  transition:transform .2s ease,box-shadow .2s ease,border-color .2s ease;
}
.lp .card:hover{transform:translateY(-3px);box-shadow:var(--lp-shadow-lg);
  border-color:rgba(22,120,253,.32)}
.lp .card h3{font-size:16.5px}
.lp .card p{color:var(--lp-muted);font-size:14.5px;line-height:1.65}
.lp .card .ico{
  width:44px;height:44px;border-radius:12px;display:flex;align-items:center;
  justify-content:center;flex:none;
  background:linear-gradient(140deg,rgba(22,120,253,.13),rgba(33,165,66,.11));
  color:var(--lp-blue);
}
.lp .card .num{
  font-size:12px;font-weight:700;color:var(--lp-blue);letter-spacing:.06em;
}

/* ---------- 21 sheets grid ---------- */
.lp .sheets{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.lp .sheet-card{
  background:#fff;border:1px solid var(--lp-line);border-radius:14px;
  padding:17px 18px;display:flex;gap:13px;align-items:flex-start;
  transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease;
}
.lp .sheet-card:hover{transform:translateY(-2px);border-color:rgba(22,120,253,.34);
  box-shadow:var(--lp-shadow)}
.lp .sheet-card .n{
  flex:none;width:28px;height:28px;border-radius:9px;display:flex;
  align-items:center;justify-content:center;font-size:11.5px;font-weight:700;
  color:var(--lp-navy);background:rgba(0,14,155,.08);
}
.lp .sheet-card h4{font-size:14px;margin-bottom:5px}
.lp .sheet-card p{font-size:12.8px;color:var(--lp-muted);line-height:1.55}

/* ---------- interactive preview ---------- */
.lp .demo{
  background:#fff;border:1px solid var(--lp-line);border-radius:22px;
  box-shadow:var(--lp-shadow-lg);overflow:hidden;
}
.lp .demo-head{
  padding:20px 24px;border-bottom:1px solid var(--lp-line);
  display:flex;flex-wrap:wrap;align-items:center;gap:14px;justify-content:space-between;
  background:linear-gradient(180deg,#fff,#FAFCFF);
}
.lp .demo-head h3{font-size:16px}
.lp .demo-head p{font-size:12.5px;color:var(--lp-muted);margin-top:3px}
.lp .tabs{display:flex;flex-wrap:wrap;gap:7px}
.lp .tab{
  font-family:Poppins,sans-serif;font-size:12.5px;font-weight:600;cursor:pointer;
  padding:9px 15px;border-radius:999px;border:1px solid var(--lp-line);
  background:#fff;color:var(--lp-ink-2);
  transition:all .16s ease;
}
.lp .tab:hover{border-color:var(--lp-blue);color:var(--lp-blue)}
.lp .tab[aria-selected="true"]{
  background:linear-gradient(100deg,var(--lp-navy),var(--lp-blue));
  border-color:transparent;color:#fff;box-shadow:0 6px 16px rgba(22,120,253,.3);
}
.lp .demo-body{display:grid;grid-template-columns:1.15fr .85fr}
.lp .demo-metrics{
  padding:26px 24px;display:grid;grid-template-columns:repeat(2,1fr);gap:14px;
  border-right:1px solid var(--lp-line);
}
.lp .metric{
  background:var(--lp-bg);border:1px solid var(--lp-line);border-radius:14px;
  padding:15px 16px;
}
.lp .metric small{display:block;font-size:11px;color:var(--lp-muted);
  letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px;font-weight:600}
.lp .metric b{font-size:23px;font-weight:700;color:var(--lp-ink);
  font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.lp .metric .trend{font-size:11.5px;font-weight:600;color:var(--lp-green);
  margin-top:4px;display:block}
.lp .demo-side{padding:26px 24px;display:flex;flex-direction:column;gap:16px}
.lp .driver{
  background:linear-gradient(140deg,rgba(0,14,155,.05),rgba(22,120,253,.06));
  border:1px solid rgba(22,120,253,.16);border-radius:14px;padding:16px 17px;
}
.lp .driver small{font-size:10.5px;font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;color:var(--lp-blue)}
.lp .driver b{display:block;font-size:15.5px;margin:6px 0 7px}
.lp .driver p{font-size:13px;color:var(--lp-muted);line-height:1.6}
.lp .demo-note{
  padding:14px 24px;background:#FFFBF0;border-top:1px solid #F4E4B8;
  font-size:12.5px;color:#6B5A1E;line-height:1.6;
}
.lp .demo-note strong{color:#4A3D10}

/* ---------- curriculum ---------- */
.lp .cur{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}
.lp .part{
  background:#fff;border:1px solid var(--lp-line);border-radius:16px;padding:22px 22px;
  box-shadow:var(--lp-shadow);display:flex;gap:15px;
}
.lp .part .pn{
  flex:none;width:38px;height:38px;border-radius:11px;display:flex;
  align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;
  background:linear-gradient(140deg,var(--lp-navy),var(--lp-blue));
}
.lp .part h3{font-size:15.5px;margin-bottom:8px}
.lp .part ul{display:flex;flex-direction:column;gap:5px}
.lp .part li{font-size:13px;color:var(--lp-muted);line-height:1.5;
  padding-left:15px;position:relative}
.lp .part li::before{content:"";position:absolute;left:0;top:7px;width:5px;height:5px;
  border-radius:50%;background:var(--lp-green)}

/* ---------- how it works ---------- */
.lp .steps{display:grid;grid-template-columns:repeat(5,1fr);gap:16px}
.lp .step{
  background:#fff;border:1px solid var(--lp-line);border-radius:16px;
  padding:22px 19px;box-shadow:var(--lp-shadow);position:relative;
}
.lp .step .sn{
  width:34px;height:34px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:14px;font-weight:700;color:#fff;margin-bottom:13px;
  background:linear-gradient(140deg,var(--lp-blue),var(--lp-green));
}
.lp .step h3{font-size:14.5px;margin-bottom:7px}
.lp .step p{font-size:13px;color:var(--lp-muted);line-height:1.6}

/* ---------- pricing ---------- */
.lp .price-wrap{display:grid;grid-template-columns:1.05fr .95fr;gap:26px;align-items:start}
.lp .price-card{
  background:#fff;border:1.5px solid rgba(22,120,253,.28);border-radius:22px;
  padding:34px 32px;box-shadow:var(--lp-shadow-lg);position:relative;
}
.lp .price-badge{
  position:absolute;top:-14px;left:32px;font-size:11.5px;font-weight:700;
  letter-spacing:.05em;text-transform:uppercase;color:#fff;padding:7px 15px;
  border-radius:999px;background:linear-gradient(100deg,var(--lp-navy),var(--lp-blue));
  box-shadow:0 8px 20px rgba(22,120,253,.34);
}
.lp .price-now{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:8px 0 6px}
.lp .price-now b{font-size:46px;font-weight:700;letter-spacing:-.03em;line-height:1}
.lp .price-now s{font-size:19px;color:#98A2BE}
.lp .price-now em{font-style:normal;font-size:12.5px;font-weight:600;color:var(--lp-green);
  background:rgba(33,165,66,.1);border:1px solid rgba(33,165,66,.24);
  padding:4px 10px;border-radius:999px}
.lp .price-note{font-size:13px;color:var(--lp-muted);line-height:1.6;margin-bottom:22px}
.lp .ticks{display:flex;flex-direction:column;gap:11px;margin-bottom:26px}
.lp .ticks li{display:flex;gap:11px;align-items:flex-start;font-size:14px;
  color:var(--lp-ink-2);line-height:1.55}
.lp .ticks svg{flex:none;margin-top:2px;color:var(--lp-green)}
.lp .refund{font-size:12.5px;color:var(--lp-muted);margin-top:16px;line-height:1.65}
.lp .refund a{color:var(--lp-blue);text-decoration:underline}
.lp .price-side{display:flex;flex-direction:column;gap:16px}
.lp .side-card{
  background:#fff;border:1px solid var(--lp-line);border-radius:18px;padding:24px 24px;
  box-shadow:var(--lp-shadow);
}
.lp .side-card h3{font-size:15.5px;margin-bottom:9px}
.lp .side-card p{font-size:13.5px;color:var(--lp-muted);line-height:1.65}
.lp .side-card ul{display:flex;flex-direction:column;gap:8px;margin-top:12px}
.lp .side-card li{font-size:13.5px;color:var(--lp-ink-2);line-height:1.55;
  padding-left:16px;position:relative}
.lp .side-card li::before{content:"";position:absolute;left:0;top:7px;width:5px;
  height:5px;border-radius:50%;background:var(--lp-blue)}
.lp .side-dark{background:var(--lp-dark);color:#fff;border-color:transparent}
.lp .side-dark h3{color:#fff}
.lp .side-dark p,.lp .side-dark li{color:#B9C4E0}
.lp .side-dark li::before{background:var(--lp-green)}

/* ---------- faq ---------- */
.lp .faq{max-width:860px;margin:0 auto}
.lp .faq details{
  background:#fff;border:1px solid var(--lp-line);border-radius:14px;
  margin-bottom:11px;box-shadow:var(--lp-shadow);overflow:hidden;
}
.lp .faq details[open]{border-color:rgba(22,120,253,.3)}
.lp .faq summary{
  cursor:pointer;padding:19px 22px;font-size:15.5px;font-weight:600;
  display:flex;align-items:center;justify-content:space-between;gap:16px;
  list-style:none;color:var(--lp-ink);
}
.lp .faq summary::-webkit-details-marker{display:none}
.lp .faq summary::after{
  content:"";flex:none;width:11px;height:11px;border-right:2.5px solid var(--lp-blue);
  border-bottom:2.5px solid var(--lp-blue);transform:rotate(45deg);
  transition:transform .22s ease;margin-top:-4px;
}
.lp .faq details[open] summary::after{transform:rotate(225deg);margin-top:4px}
.lp .faq .a{padding:0 22px 20px;color:var(--lp-muted);font-size:14px;line-height:1.72}
.lp .faq .a a{color:var(--lp-blue);text-decoration:underline}

/* ---------- disclaimer + final cta ---------- */
.lp .disc{
  background:#fff;border:1px solid var(--lp-line);border-left:4px solid var(--lp-yellow);
  border-radius:14px;padding:22px 24px;box-shadow:var(--lp-shadow);
}
.lp .disc h3{font-size:14px;margin-bottom:9px;letter-spacing:.01em}
.lp .disc p{font-size:13.2px;color:var(--lp-muted);line-height:1.7}
.lp .final{
  background:var(--lp-dark);color:#fff;border-radius:24px;padding:54px 40px;
  text-align:center;position:relative;overflow:hidden;
}
.lp .final::before{
  content:"";position:absolute;inset:0;pointer-events:none;
  background:
    radial-gradient(520px 320px at 20% 0%,rgba(22,120,253,.30),transparent 62%),
    radial-gradient(460px 300px at 84% 100%,rgba(33,165,66,.22),transparent 62%);
}
.lp .final>*{position:relative;z-index:1}
.lp .final h2{font-size:clamp(24px,3.2vw,36px);margin-bottom:14px}
.lp .final p{color:#B9C4E0;font-size:15.5px;line-height:1.7;max-width:62ch;
  margin:0 auto 28px}
.lp .final .btn-row{justify-content:center}
.lp .final small{display:block;margin-top:18px;color:#8E9BC0;font-size:12.5px}

/* ---------- footer note ---------- */
.lp .lp-foot{
  background:#fff;border-top:1px solid var(--lp-line);padding:34px 0 44px;
}
.lp .lp-foot-in{display:flex;flex-wrap:wrap;gap:18px;justify-content:space-between;
  align-items:center}
.lp .lp-foot p{font-size:12.5px;color:var(--lp-muted);line-height:1.6;max-width:70ch}
.lp .lp-foot nav{display:flex;flex-wrap:wrap;gap:8px 20px}
.lp .lp-foot nav a{font-size:13px;color:var(--lp-ink-2);font-weight:500}
.lp .lp-foot nav a:hover{color:var(--lp-blue);text-decoration:underline}

/* ---------- licence unlock ---------- */
.lp .unlock{
  max-width:720px;margin:0 auto;background:#fff;border:1px solid var(--lp-line);
  border-radius:var(--lp-radius);padding:34px 32px;box-shadow:var(--lp-shadow);
  text-align:center;
}
.lp .unlock h2{font-size:clamp(22px,2.6vw,30px);margin-bottom:10px}
.lp .unlock > p{color:var(--lp-muted);font-size:15px;line-height:1.7}
.lp .unlock code{
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px;
  background:rgba(11,16,32,.06);padding:2px 7px;border-radius:6px;
}
.lp .licence-form{display:flex;flex-wrap:wrap;gap:10px;margin:20px 0 4px;
  text-align:left}
.lp .licence-form label{
  flex:1 1 100%;font-size:13px;font-weight:600;color:var(--lp-ink-2);
}
.lp .licence-form input{
  flex:1 1 260px;min-width:0;padding:14px 16px;font-size:15px;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;letter-spacing:.06em;
  text-transform:uppercase;color:var(--lp-ink);background:var(--lp-bg);
  border:1.5px solid var(--lp-line);border-radius:var(--lp-radius-sm);
}
.lp .licence-form input:focus{
  outline:none;border-color:var(--lp-blue);
  box-shadow:0 0 0 3px rgba(22,120,253,.16);
}
.lp .licence-form button{
  flex:0 0 auto;padding:14px 26px;font-family:Poppins,sans-serif;
  font-weight:600;font-size:15px;color:#fff;background:var(--lp-navy);
  border:0;border-radius:999px;cursor:pointer;transition:background .18s ease;
}
.lp .licence-form button:hover:not(:disabled){background:var(--lp-blue)}
.lp .licence-form button:disabled{opacity:.6;cursor:progress}
.lp .licence-result{
  margin:16px 0 0;padding:14px 18px;border-radius:var(--lp-radius-sm);
  font-size:14.5px;line-height:1.6;text-align:left;
}
.lp .licence-info{background:#EEF4FB;border-left:4px solid var(--lp-blue)}
.lp .licence-good{background:#EFF8F0;border-left:4px solid var(--lp-green)}
.lp .licence-bad{background:#FDECEC;border-left:4px solid var(--lp-red)}
.lp .licence-result code{
  font-family:ui-monospace,Menlo,monospace;background:rgba(0,0,0,.06);
  padding:1px 5px;border-radius:4px;
}
.lp .unlock-hint{font-size:13px;color:var(--lp-muted);margin-top:14px}
.lp .unlock-hint a{color:var(--lp-blue);font-weight:600}
.lp .unlock-hint a:hover{text-decoration:underline}

/* ---------- reveal animation ---------- */
/* Progressive enhancement: the content is visible by default, and the script
   adds `.lp-anim` to <html> only when it is able to reveal it again. Hiding the
   sections in plain CSS instead would mean a single script error, or a browser
   that never fires IntersectionObserver, leaves a sales page that is blank
   above the fold. This page cannot afford that. */
.lp-anim .rv{opacity:0;transform:translateY(18px);
  transition:opacity .6s ease,transform .6s cubic-bezier(.22,1,.36,1)}
.lp-anim .rv.in{opacity:1;transform:none}
@media (prefers-reduced-motion:reduce){
  .lp-anim .rv{opacity:1;transform:none;transition:none}
  .lp .card:hover,.lp .sheet-card:hover,.lp .btn:hover{transform:none}
}

/* ---------- responsive ---------- */
@media (max-width:1080px){
  .lp .hero-grid{grid-template-columns:1fr;gap:44px}
  .lp .sheets{grid-template-columns:repeat(2,1fr)}
  .lp .steps{grid-template-columns:repeat(2,1fr)}
  .lp .demo-body{grid-template-columns:1fr}
  .lp .demo-metrics{border-right:0;border-bottom:1px solid var(--lp-line)}
  .lp .price-wrap{grid-template-columns:1fr}
  .lp .cards-4{grid-template-columns:repeat(2,1fr)}
  .lp .cur{grid-template-columns:1fr}
}
@media (max-width:760px){
  .lp .sec{padding:54px 0}
  .lp .sec-tight{padding:40px 0}
  .lp .sec-head{margin-bottom:32px}
  /* The topbar is position:fixed on mobile (71px tall), so it floats over the
     top of the page. The other pages get away with it because their hero is a
     pale gradient; this hero is near-black, so anything within 71px of the top
     is visibly cut in half. Clear the header plus a little breathing room. */
  .lp .hero{padding:96px 0 60px}
  .lp .cards-2,.lp .cards-3,.lp .cards-4{grid-template-columns:1fr}
  .lp .sheets{grid-template-columns:1fr}
  .lp .steps{grid-template-columns:1fr}
  .lp .demo-metrics{grid-template-columns:1fr;padding:20px 18px}
  .lp .demo-side{padding:20px 18px}
  .lp .demo-head{padding:18px 18px}
  .lp .demo-note{padding:14px 18px}
  .lp .price-card{padding:28px 20px}
  .lp .price-badge{left:20px}
  .lp .unlock{padding:26px 20px}
  .lp .licence-form button{width:100%}
  .lp .price-now b{font-size:38px}
  .lp .final{padding:40px 22px;border-radius:18px}
  .lp .kpis{grid-template-columns:1fr 1fr}
  .lp .badge-a{left:-6px;top:-13px}
  .lp .badge-b{right:-4px;bottom:-14px}
  .lp .mock{padding:11px}
  .lp .btn{padding:14px 22px;font-size:14.5px}
  .lp .hero-cta .btn{width:100%}
  .lp .lp-foot-in{flex-direction:column;align-items:flex-start}
}
@media (max-width:420px){
  .lp .kpis{grid-template-columns:1fr}
  .lp .facts{gap:8px}
  .lp .fact{flex:1 1 calc(50% - 8px);min-width:0}
}
"""
