"""The single frontend page. Two tabs:
  Overview - answers the three questions (leaders / what made the top 3 succeed /
             what Proteins.1 should do), server-rendered from the ranked data +
             the consolidated recommendation.
  Data     - everything collected (companies / census / articles), rendered
             client-side from an embedded copy, with search / filter / sort.

Reads reports/data/*.json  ->  writes reports/frontend.html
(also served by the FastAPI app at GET /)
"""
import html
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "frontend.html"

census = json.loads((DATA / "discovered_companies.json").read_text())
companies = json.loads((DATA / "companies.json").read_text())
articles = json.loads((DATA / "discovered_articles.json").read_text())
rec = (json.loads((DATA / "recommendation.json").read_text()) or [{}])[0]
_opp_path = DATA / "opportunity_pick.json"
opp = (json.loads(_opp_path.read_text()) or [{}])[0] if _opp_path.exists() else {}

MAXPTS = {"platform": 5, "stage": 5, "route": 5, "evidence": 3, "ecosystem": 2}
MAX_TOTAL = 32.5
generated = datetime.now(timezone.utc).strftime("%d %b %Y")

ranked = sorted([c for c in companies if (c.get("relevance_score") or 0) > 0],
                key=lambda c: -(c.get("relevance_score") or 0))
top10 = ranked[:10]
top3 = ranked[:3]
countries = sorted({c.get("country") for c in census if c.get("country")})
platforms = sorted({c.get("platform_type") for c in census if c.get("platform_type")})
adomains = sorted({a.get("domain") for a in articles if a.get("domain")})


def e(s):
    return html.escape(str(s or "").strip())


def bar(score, mx=MAX_TOTAL):
    return f'<span class="bar"><span class="bar-fill" style="width:{round(100*score/mx)}%"></span></span>'


# ---- Q1: the leaders (top 10) --------------------------------------------
def leader_card(c, i):
    return f"""      <article class="lcard">
        <div class="lcard-rank mono">{i:02d}</div>
        <h3>{e(c['name'])}</h3>
        <div class="lcard-meta mono">{e(c['country'])} &middot; {e(c.get('detection_modality') or c.get('technology_approach','')[:32] or 'platform')}</div>
        <div class="lcard-score">
          <span class="mono score-n">{c['relevance_score']:.1f}<span class="score-max">/{MAX_TOTAL:.0f}</span></span>
          {bar(c['relevance_score'])}
        </div>
        <p class="lcard-leader">{'<span class="mono tag">' + e(c['leader_name']) + '</span>' if c.get('leader_name') else '<span class="mono tag muted">leader not named</span>'}</p>
      </article>"""


q1_top3 = "\n".join(leader_card(c, i + 1) for i, c in enumerate(top3))
q1_rows = "\n".join(f"""        <tr>
          <td class="mono rk">{i}</td>
          <td class="nm">{e(c['name'])}</td>
          <td class="mono">{e(c['country'])}</td>
          <td class="mono muted">{e(c.get('detection_modality') or '')}</td>
          <td>{bar(c['relevance_score'])}</td>
          <td class="mono sc">{c['relevance_score']:.1f}</td>
        </tr>""" for i, c in enumerate(top10[3:], start=4))

# ---- Q2: what made the top 3 succeed -----------------------------------
def q2_card(c):
    factors = [f for f in (c.get("success_factors") or []) if isinstance(f, dict) and f.get("factor")][:3]
    fitems = "\n".join(
        f"""          <li>
            <span class="f-claim">{e(f['factor'])}</span>
            {f'<span class="f-ev">{e(f["evidence"])}</span>' if f.get('evidence') else ''}
          </li>""" for f in factors) or '<li class="muted">No concrete factors captured.</li>'
    return f"""      <article class="q2card">
        <header>
          <h3>{e(c['name'])}</h3>
          <p class="q2-leader mono">{e(c['leader_name']) or 'leader not named'}{(' &middot; ' + e(c['leader_role'])) if c.get('leader_role') else ''}</p>
        </header>
        <p class="q2-what">{e((c.get('what_they_do') or '')[:180])}</p>
        <ul class="factors">
{fitems}
        </ul>
      </article>"""


q2_cards = "\n".join(q2_card(c) for c in top3)

# ---- Q3: what Proteins.1 should do -----------------------------------
apps = "\n".join(f"""        <li>
          <span class="app-h">{e(a.get('application'))}</span>
          <span class="app-why">{e(a.get('rationale'))}</span>
        </li>""" for a in (rec.get("applications") or []))
route = "\n".join(f"""        <li>
          <span class="step-n mono">{i:02d}</span>
          <div><span class="step-h">{e(s.get('step'))}</span><span class="step-d">{e(s.get('detail'))}</span></div>
        </li>""" for i, s in enumerate(rec.get("market_route") or [], start=1))
rec_from = ", ".join(e(n) for n in (rec.get("from_companies") or []))

# ---- Q4: the disease-biomarker opportunity + first customer ------------
opp_has = bool((opp.get("biomarker") or "").strip())
opp_evidence = "\n".join(f"""        <li>
          <span class="app-h">{e(x.get('point'))}</span>
          {f'<span class="ev-src">{e(x.get("source"))}</span>' if x.get('source') else ''}
        </li>""" for x in (opp.get("evidence") or []))

PAYLOAD = json.dumps({"census": census, "companies": companies, "articles": articles,
                      "maxpts": MAXPTS, "max_total": MAX_TOTAL},
                     ensure_ascii=False, separators=(",", ":"))
OPT_C = "".join(f"<option>{e(c)}</option>" for c in countries)
OPT_P = "".join(f"<option>{e(p)}</option>" for p in platforms)
OPT_D = "".join(f"<option>{e(d)}</option>" for d in adomains)

TEMPLATE = r"""<title>Proteins.1 Landscape</title>
<meta name="description" content="The European single-molecule protein-diagnostics landscape for Proteins.1 - who the leaders are, what made the top three succeed, and the application and go-to-market route to apply. Plus every record we collected.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap">
<style>
:root{
  color-scheme:light;
  --bg:#FFFFFF; --bg-soft:#F7F8FB; --bg-softer:#F1F3F8;
  --card:#FFFFFF; --border:#E8EAF2; --border-2:#DCDFEA;
  --ink:#0F1222; --ink-2:#474C61; --ink-3:#878CA0;
  --brand:#4F46E5; --brand-2:#7C3AED; --brand-ink:#4338CA;
  --brand-wash:#EEF0FF; --brand-wash-2:#F4F2FF;
  --good:#15803D; --good-wash:#EBFBF1;
  --grad:linear-gradient(135deg,#4F46E5 0%,#7C3AED 100%);
  --sh-sm:0 1px 2px rgba(16,18,34,.05),0 1px 3px rgba(16,18,34,.04);
  --sh-md:0 6px 18px rgba(16,18,34,.07),0 2px 6px rgba(16,18,34,.04);
  --sh-lg:0 18px 40px rgba(79,70,229,.14),0 6px 16px rgba(16,18,34,.06);
  --r:16px; --r-sm:11px; --r-pill:999px;
  --container:1160px;
}
*{box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{margin:0;background:var(--bg);color:var(--ink);
  font-family:"Inter",system-ui,-apple-system,sans-serif;font-size:16px;line-height:1.6;
  -webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility;}
h1,h2,h3,h4{font-family:"Sora","Inter",sans-serif;line-height:1.15;letter-spacing:-.02em;margin:0;text-wrap:balance;}
a{color:var(--brand);text-decoration:none;}
a:hover{color:var(--brand-ink);}
.mono{font-family:"JetBrains Mono",ui-monospace,Menlo,monospace;}
.muted{color:var(--ink-3);}
:focus-visible{outline:2.5px solid var(--brand);outline-offset:3px;border-radius:6px;}
.container{max-width:var(--container);margin:0 auto;padding:0 32px;}
section{padding:104px 0;}
section.alt{background:var(--bg-soft);}
.eyebrow{font-family:"JetBrains Mono",monospace;font-size:12px;font-weight:500;letter-spacing:.16em;
  text-transform:uppercase;color:var(--brand);}
.sec-head{max-width:60ch;margin-bottom:48px;}
.sec-head h2{font-size:clamp(1.9rem,3.4vw,2.6rem);font-weight:700;margin:.35em 0 .4em;}
.sec-head p{color:var(--ink-2);font-size:1.08rem;margin:0;}

/* nav */
header.nav{position:sticky;top:0;z-index:50;background:rgba(255,255,255,.82);
  backdrop-filter:saturate(180%) blur(12px);border-bottom:1px solid var(--border);}
.nav-in{display:flex;align-items:center;gap:28px;height:68px;}
.brand{display:flex;align-items:center;gap:10px;font-family:"Sora",sans-serif;font-weight:700;
  font-size:1.02rem;color:var(--ink);letter-spacing:-.01em;}
.brand .mk{width:26px;height:26px;border-radius:8px;background:var(--grad);
  box-shadow:0 2px 8px rgba(79,70,229,.35);display:grid;place-items:center;color:#fff;font-size:13px;}
.nav-links{display:flex;gap:6px;margin-left:8px;}
.nav-links button{appearance:none;background:none;border:none;cursor:pointer;font:inherit;
  font-size:.95rem;font-weight:500;color:var(--ink-2);padding:8px 14px;border-radius:var(--r-pill);
  transition:background .15s,color .15s;}
.nav-links button:hover{background:var(--bg-softer);color:var(--ink);}
.nav-links button[aria-current="true"]{background:var(--brand-wash);color:var(--brand-ink);font-weight:600;}
.nav-cta{margin-left:auto;}
.btn{display:inline-flex;align-items:center;gap:8px;font:inherit;font-weight:600;font-size:.95rem;
  padding:11px 20px;border-radius:var(--r-pill);cursor:pointer;border:1px solid transparent;
  transition:transform .12s ease,box-shadow .18s ease,background .15s;white-space:nowrap;}
.btn-primary{background:var(--grad);color:#fff;box-shadow:0 4px 14px rgba(79,70,229,.32);}
.btn-primary:hover{transform:translateY(-1px);box-shadow:0 10px 24px rgba(79,70,229,.38);color:#fff;}
.btn-primary:active{transform:translateY(0);}
.btn-ghost{background:var(--card);color:var(--ink);border-color:var(--border-2);box-shadow:var(--sh-sm);}
.btn-ghost:hover{transform:translateY(-1px);box-shadow:var(--sh-md);color:var(--ink);}

/* hero */
.hero{padding:88px 0 96px;}
.hero-grid{display:grid;grid-template-columns:1.08fr .92fr;gap:64px;align-items:center;}
.hero h1{font-size:clamp(2.4rem,5vw,3.7rem);font-weight:800;}
.hero .lede{font-size:1.18rem;color:var(--ink-2);margin:22px 0 32px;max-width:52ch;}
.hero-cta{display:flex;gap:14px;flex-wrap:wrap;}
.hero-stats{display:flex;gap:30px;margin-top:40px;flex-wrap:wrap;}
.hero-stats div{display:flex;flex-direction:column;}
.hero-stats b{font-family:"Sora",sans-serif;font-size:1.5rem;font-weight:700;}
.hero-stats span{font-size:.82rem;color:var(--ink-3);font-family:"JetBrains Mono",monospace;letter-spacing:.04em;}
.hero-visual{position:relative;}
.hero-visual .blob{position:absolute;inset:-14% -10% -10% -6%;background:var(--grad);opacity:.14;
  filter:blur(46px);border-radius:50%;z-index:0;}
.preview{position:relative;z-index:1;background:var(--card);border:1px solid var(--border);
  border-radius:var(--r);box-shadow:var(--sh-lg);padding:22px;}
.preview-h{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.preview-h .k{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);}
.preview-h .dot{width:8px;height:8px;border-radius:50%;background:var(--good);box-shadow:0 0 0 3px var(--good-wash);}
.prow{display:grid;grid-template-columns:24px 1fr auto;gap:12px;align-items:center;padding:12px 6px;border-top:1px solid var(--border);}
.prow:first-of-type{border-top:none;}
.prow .pn{font-family:"JetBrains Mono",monospace;color:var(--ink-3);font-size:13px;}
.prow .pname{font-weight:600;font-size:.98rem;}
.prow .pmeta{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-3);}
.prow .pscore{font-family:"JetBrains Mono",monospace;font-weight:500;font-size:.95rem;color:var(--brand-ink);}
.bar{display:block;height:7px;width:100%;background:var(--bg-softer);border-radius:var(--r-pill);overflow:hidden;margin-top:5px;}
.bar-fill{display:block;height:100%;background:var(--grad);border-radius:var(--r-pill);}

/* Q1 leaders */
.lgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin-bottom:28px;}
.lcard{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:24px;
  box-shadow:var(--sh-sm);transition:transform .15s ease,box-shadow .2s ease;}
.lcard:hover{transform:translateY(-3px);box-shadow:var(--sh-lg);}
.lcard-rank{font-size:.85rem;color:var(--brand);font-weight:500;letter-spacing:.08em;}
.lcard h3{font-size:1.32rem;font-weight:700;margin:6px 0 4px;}
.lcard-meta{font-size:11.5px;color:var(--ink-3);}
.lcard-score{margin:16px 0 12px;}
.score-n{font-size:1.35rem;font-weight:500;color:var(--ink);}
.score-max{font-size:.85rem;color:var(--ink-3);}
.tag{display:inline-block;background:var(--brand-wash);color:var(--brand-ink);font-size:11px;
  padding:3px 9px;border-radius:var(--r-pill);}
.tag.muted{background:var(--bg-softer);color:var(--ink-3);}
.ltable-wrap{border:1px solid var(--border);border-radius:var(--r);overflow:hidden;background:var(--card);box-shadow:var(--sh-sm);}
table{border-collapse:collapse;width:100%;font-size:14px;}
.ltable th{font-family:"JetBrains Mono",monospace;font-size:10.5px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--ink-3);text-align:left;padding:13px 18px;background:var(--bg-soft);}
.ltable td{padding:13px 18px;border-top:1px solid var(--border);vertical-align:middle;}
.ltable td.nm{font-weight:600;}
.ltable td.rk{color:var(--ink-3);}
.ltable td.sc{font-weight:500;color:var(--brand-ink);}
.ltable td:nth-child(5){width:180px;}

/* Q2 */
.q2grid{display:grid;grid-template-columns:repeat(3,1fr);gap:22px;}
.q2card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:26px;
  box-shadow:var(--sh-sm);transition:transform .15s ease,box-shadow .2s ease;display:flex;flex-direction:column;}
.q2card:hover{transform:translateY(-3px);box-shadow:var(--sh-lg);}
.q2card h3{font-size:1.3rem;font-weight:700;}
.q2-leader{font-size:11.5px;color:var(--brand-ink);margin:6px 0 0;}
.q2-what{font-size:.92rem;color:var(--ink-3);margin:12px 0 4px;}
.factors{list-style:none;padding:0;margin:16px 0 0;display:flex;flex-direction:column;gap:14px;}
.factors li{padding-left:20px;position:relative;}
.factors li::before{content:"";position:absolute;left:0;top:8px;width:8px;height:8px;border-radius:3px;background:var(--brand);}
.f-claim{display:block;font-weight:600;font-size:.94rem;}
.f-ev{display:block;font-size:.86rem;color:var(--ink-3);margin-top:3px;font-style:italic;}

/* Q3 */
.rec-head{background:var(--grad);color:#fff;border-radius:var(--r);padding:34px 36px;box-shadow:var(--sh-lg);margin-bottom:34px;}
.rec-head .k{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;opacity:.85;}
.rec-head p{font-family:"Sora",sans-serif;font-size:clamp(1.15rem,2vw,1.5rem);font-weight:600;line-height:1.4;margin:12px 0 0;}
.rec-cols{display:grid;grid-template-columns:1fr 1fr;gap:34px;}
.rec-cols h3{font-size:1.15rem;font-weight:700;margin-bottom:16px;}
.applist{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:16px;}
.applist li{background:var(--card);border:1px solid var(--border);border-radius:var(--r-sm);padding:16px 18px;box-shadow:var(--sh-sm);}
.app-h{display:block;font-weight:600;font-size:.98rem;}
.app-why{display:block;font-size:.87rem;color:var(--ink-3);margin-top:5px;}
.steplist{list-style:none;padding:0;margin:0;counter-reset:s;display:flex;flex-direction:column;gap:4px;}
.steplist li{display:grid;grid-template-columns:34px 1fr;gap:14px;padding:16px 0;border-top:1px solid var(--border);}
.steplist li:first-child{border-top:none;}
.step-n{color:var(--brand);font-weight:500;font-size:.9rem;padding-top:2px;}
.step-h{display:block;font-weight:600;font-size:.96rem;}
.step-d{display:block;font-size:.87rem;color:var(--ink-3);margin-top:4px;}
.seq{margin-top:34px;background:var(--card);border:1px solid var(--border);border-left:3px solid var(--brand);
  border-radius:var(--r-sm);padding:22px 24px;}
.seq .k{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--ink-3);}
.seq p{margin:8px 0 0;color:var(--ink-2);font-size:1.02rem;}

/* Q4 opportunity pick */
.pick-head{background:var(--grad);color:#fff;border-radius:var(--r);padding:32px 36px;box-shadow:var(--sh-lg);margin-bottom:30px;}
.pick-head .k{font-family:"JetBrains Mono",monospace;font-size:11px;letter-spacing:.14em;text-transform:uppercase;opacity:.85;}
.pick-marker{font-family:"Sora",sans-serif;font-size:clamp(1.5rem,3vw,2.1rem);font-weight:700;line-height:1.2;margin:8px 0 14px;letter-spacing:-.02em;}
.pick-head p{margin:0;font-size:1.02rem;line-height:1.55;opacity:.96;max-width:70ch;}
.pick-cols{display:grid;grid-template-columns:1fr 1fr;gap:30px;}
.pick-cols h3{font-size:1.1rem;font-weight:700;margin-bottom:12px;}
.pick-cols .card{background:var(--card);border:1px solid var(--border);border-radius:var(--r-sm);padding:20px 22px;box-shadow:var(--sh-sm);height:100%;}
.pick-cols .card p{margin:0 0 12px;font-size:.94rem;color:var(--ink-2);}
.pick-cols .card p:last-child{margin-bottom:0;}
.pick-cols .who{font-weight:700;color:var(--ink);font-size:1rem;}
.ev-list{list-style:none;padding:0;margin:22px 0 0;display:flex;flex-direction:column;gap:12px;}
.ev-list li{background:var(--card);border:1px solid var(--border);border-radius:var(--r-sm);padding:14px 16px;box-shadow:var(--sh-sm);}
.ev-src{display:inline-block;margin-top:6px;font-family:"JetBrains Mono",monospace;font-size:10.5px;
  color:var(--brand-ink);background:var(--brand-wash);border-radius:var(--r-pill);padding:2px 9px;}
.runner{margin-top:24px;font-size:.92rem;color:var(--ink-3);}
.runner b{color:var(--ink-2);font-weight:600;}
.q4-empty{background:var(--bg-softer);border:1px dashed var(--border-2);border-radius:var(--r);
  padding:32px;text-align:center;color:var(--ink-2);}
.q4-empty code{font-family:"JetBrains Mono",monospace;background:var(--card);border:1px solid var(--border);
  border-radius:6px;padding:2px 8px;font-size:.86rem;}

/* CTA band */
.cta-band{background:var(--bg-softer);border-radius:var(--r);padding:48px;text-align:center;}
.cta-band h2{font-size:1.7rem;font-weight:700;}
.cta-band p{color:var(--ink-2);margin:12px auto 26px;max-width:46ch;}

/* footer */
footer.ft{border-top:1px solid var(--border);padding:40px 0;color:var(--ink-3);font-size:.85rem;}
.ft-in{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;font-family:"JetBrains Mono",monospace;}

/* tab panels */
.panel[hidden]{display:none;}

/* --- Data tab --- */
.data-sub{display:flex;gap:8px;margin-bottom:26px;flex-wrap:wrap;}
.data-sub button{appearance:none;font:inherit;font-weight:500;font-size:.9rem;cursor:pointer;
  padding:9px 16px;border-radius:var(--r-pill);border:1px solid var(--border-2);background:var(--card);
  color:var(--ink-2);box-shadow:var(--sh-sm);transition:.15s;}
.data-sub button:hover{color:var(--ink);}
.data-sub button[aria-current="true"]{background:var(--brand);color:#fff;border-color:transparent;box-shadow:0 4px 12px rgba(79,70,229,.3);}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:20px;}
.controls input[type=search],.controls select{font:inherit;font-size:.9rem;padding:9px 13px;border-radius:var(--r-sm);
  border:1px solid var(--border-2);background:var(--card);color:var(--ink);box-shadow:var(--sh-sm);}
.controls input[type=search]{min-width:240px;flex:1;}
.controls label{font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--ink-2);display:flex;align-items:center;gap:7px;cursor:pointer;}
.controls .count{margin-left:auto;font-family:"JetBrains Mono",monospace;font-size:12px;color:var(--ink-3);}
.co{border:1px solid var(--border);border-radius:var(--r-sm);background:var(--card);margin-bottom:12px;box-shadow:var(--sh-sm);overflow:hidden;}
.co-h{display:grid;grid-template-columns:38px 1fr auto;gap:14px;align-items:center;width:100%;text-align:left;
  background:none;border:none;cursor:pointer;font:inherit;color:inherit;padding:16px 20px;transition:background .15s;}
.co-h:hover{background:var(--bg-soft);}
.co-rank{font-family:"JetBrains Mono",monospace;color:var(--ink-3);font-size:13px;}
.co-name{font-weight:600;font-size:1.05rem;}
.co-sub{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-3);margin-top:2px;}
.co-right{display:flex;align-items:center;gap:12px;}
.co-score{font-family:"JetBrains Mono",monospace;font-weight:500;color:var(--brand-ink);}
.chip{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:.04em;text-transform:uppercase;
  padding:3px 9px;border-radius:var(--r-pill);border:1px solid var(--border-2);color:var(--ink-3);white-space:nowrap;}
.chip-high{color:var(--good);border-color:#B7E4C7;background:var(--good-wash);}
.chip-medium{color:#B45309;border-color:#FCD9A8;background:#FFF7ED;}
.badge{font-family:"JetBrains Mono",monospace;font-size:10px;letter-spacing:.05em;text-transform:uppercase;
  color:#fff;background:var(--grad);border-radius:var(--r-pill);padding:2px 9px;}
.co-body{padding:8px 22px 24px;border-top:1px solid var(--border);}
.co-body[hidden]{display:none;}
.sec-blk{margin-top:22px;}
.sec-blk>.k{display:block;font-family:"JetBrains Mono",monospace;font-size:10.5px;letter-spacing:.1em;
  text-transform:uppercase;color:var(--brand);padding-bottom:7px;border-bottom:1px solid var(--brand-wash);margin-bottom:11px;}
.kv{display:grid;grid-template-columns:150px 1fr;gap:5px 16px;font-size:13.5px;}
.kv dt{font-family:"JetBrains Mono",monospace;font-size:11px;text-transform:uppercase;color:var(--ink-3);}
.kv dd{margin:0;}
.prose{color:var(--ink-2);max-width:70ch;}
ul.arrow{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:7px;font-size:13.5px;}
ul.arrow li{padding-left:18px;position:relative;max-width:70ch;}
ul.arrow li::before{content:"\2192";position:absolute;left:0;color:var(--brand);}
.tbl-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--card);box-shadow:var(--sh-sm);}
.dtable{font-size:13px;font-variant-numeric:tabular-nums;}
.dtable th{cursor:pointer;position:sticky;top:0;background:var(--bg-soft);font-family:"JetBrains Mono",monospace;
  font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-3);padding:10px 14px;text-align:left;white-space:nowrap;}
.dtable th.sorted::after{content:" \25be";color:var(--brand);}
.dtable th.sorted.asc::after{content:" \25b4";}
.dtable td{padding:10px 14px;border-top:1px solid var(--border);vertical-align:top;}
.dtable tr.expandable{cursor:pointer;}
.dtable tr.expandable:hover{background:var(--bg-soft);}
.dtable tr.detail td{background:var(--bg-soft);color:var(--ink-3);font-size:12.5px;}
.dtable tr.detail[hidden]{display:none;}
.art{padding:14px 0;border-top:1px solid var(--border);}
.art:first-child{border-top:none;}
.art-t{font-weight:600;font-size:14px;}
.art-m{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-3);margin-top:3px;}
.art-s{color:var(--ink-3);font-size:13px;margin-top:5px;max-width:80ch;}
.none{color:var(--ink-3);font-style:italic;}
.srcs{font-family:"JetBrains Mono",monospace;font-size:11px;color:var(--ink-3);word-break:break-all;}
.srcs a{color:var(--ink-2);}
.bars2{display:flex;flex-direction:column;gap:6px;max-width:430px;}
.sb{display:grid;grid-template-columns:80px 1fr 54px;gap:10px;align-items:center;font-family:"JetBrains Mono",monospace;font-size:10.5px;}
.sb-k{text-transform:uppercase;color:var(--ink-3);}
.sb-t{height:6px;background:var(--bg-softer);border-radius:var(--r-pill);overflow:hidden;}
.sb-f{display:block;height:100%;background:var(--grad);}
.sb-v{text-align:right;color:var(--ink-3);}

@media (max-width:960px){
  .hero-grid{grid-template-columns:1fr;gap:44px;}
  .lgrid,.q2grid{grid-template-columns:1fr;}
  .rec-cols{grid-template-columns:1fr;}
  section{padding:72px 0;}
}
@media (max-width:600px){
  .container{padding:0 20px;}
  .nav-links{display:none;}
  .hero h1{font-size:2.1rem;}
  .co-h{grid-template-columns:30px 1fr;}
  .co-right{grid-column:2;margin-top:8px;}
  .kv{grid-template-columns:1fr;}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important;}}
</style>

<header class="nav">
  <div class="container nav-in">
    <span class="brand"><span class="mk">P1</span>Proteins.1 Landscape</span>
    <nav class="nav-links" aria-label="Sections">
      <button data-tab="overview" aria-current="true">Overview</button>
      <button data-tab="data" aria-current="false">Data</button>
    </nav>
    <span class="nav-cta"><button class="btn btn-primary" data-jump="q1">See the leaders</button></span>
  </div>
</header>

<main>
<div class="panel" id="panel-overview">

  <section class="hero">
    <div class="container hero-grid">
      <div>
        <span class="eyebrow">Competitive intelligence &middot; __GENERATED__</span>
        <h1>The European playbook for single-molecule protein diagnostics.</h1>
        <p class="lede">We swept the European field for companies building a Proteins.1-type platform,
        analysed the strongest, and scored each on how transferable its playbook is. Here is who leads,
        what made the top three win, and the route Proteins.1 can run.</p>
        <div class="hero-cta">
          <button class="btn btn-primary" data-jump="q3">What Proteins.1 should do</button>
          <button class="btn btn-ghost" data-tab="data">Browse the data</button>
        </div>
        <div class="hero-stats">
          <div><b>__N_CENSUS__</b><span>in census</span></div>
          <div><b>__N_ANALYSED__</b><span>analysed</span></div>
          <div><b>__N_TOP10__</b><span>leaders</span></div>
          <div><b>__N_ARTICLES__</b><span>sources</span></div>
        </div>
      </div>
      <div class="hero-visual">
        <div class="blob" aria-hidden="true"></div>
        <div class="preview">
          <div class="preview-h"><span class="k">Top of the field</span><span class="dot" aria-hidden="true"></span></div>
__PREVIEW_ROWS__
        </div>
      </div>
    </div>
  </section>

  <section id="q1" class="alt">
    <div class="container">
      <div class="sec-head">
        <span class="eyebrow">Question 1</span>
        <h2>Who leads this field</h2>
        <p>The ten European platform companies whose playbook scores highest for transferability to
        Proteins.1 &mdash; a fixed formula over mechanism fit, stage, go-to-market pattern, evidence
        quality, and ecosystem proximity (max __MAX_TOTAL__).</p>
      </div>
      <div class="lgrid">
__Q1_TOP3__
      </div>
      <div class="ltable-wrap">
        <table class="ltable">
          <thead><tr><th>#</th><th>Company</th><th>Country</th><th>Modality</th><th>Relevance</th><th>Score</th></tr></thead>
          <tbody>
__Q1_ROWS__
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section id="q2">
    <div class="container">
      <div class="sec-head">
        <span class="eyebrow">Question 2</span>
        <h2>What made the top three succeed</h2>
        <p>For the three highest-scoring companies, the concrete moves behind their traction &mdash;
        drawn only from their own pages, filings and press.</p>
      </div>
      <div class="q2grid">
__Q2_CARDS__
      </div>
    </div>
  </section>

  <section id="q3" class="alt">
    <div class="container">
      <div class="sec-head">
        <span class="eyebrow">Question 3</span>
        <h2>What Proteins.1 should do</h2>
        <p>One consolidated recommendation, synthesised from the playbooks of __REC_FROM__.</p>
      </div>
      <div class="rec-head">
        <span class="k">The core move</span>
        <p>__REC_HEADLINE__</p>
      </div>
      <div class="rec-cols">
        <div>
          <h3>Applications to pursue</h3>
          <ul class="applist">
__REC_APPS__
          </ul>
        </div>
        <div>
          <h3>Market-route sequence</h3>
          <ol class="steplist">
__REC_ROUTE__
          </ol>
        </div>
      </div>
      <div class="seq">
        <span class="k">Over time</span>
        <p>__REC_SEQ__</p>
      </div>
    </div>
  </section>

  <section id="q4">
    <div class="container">
      <div class="sec-head">
        <span class="eyebrow">Question 4</span>
        <h2>The opportunity to pursue first</h2>
        <p>Which specific disease&ndash;biomarker opportunity benefits most from Proteins.1&rsquo;s
        ultra-sensitive, multiplexed platform &mdash; and which customer would pay for it first.
        Reasoned against the competitor landscape and the article set.</p>
      </div>
__Q4_BODY__
    </div>
  </section>

  <section>
    <div class="container">
      <div class="cta-band">
        <h2>Every record, one place</h2>
        <p>The full census, all analysed companies with their scores, and every background source we
        pulled &mdash; searchable and filterable.</p>
        <button class="btn btn-primary" data-tab="data">Open the data</button>
      </div>
    </div>
  </section>

</div>

<div class="panel" id="panel-data" hidden>
  <section>
    <div class="container">
      <div class="sec-head">
        <span class="eyebrow">The data we have</span>
        <h2>Everything collected</h2>
        <p>__N_CENSUS__ companies in the discovery census, __N_ANALYSED__ analysed with full playbooks
        and relevance scores, and __N_ARTICLES__ background articles.</p>
      </div>

      <div class="data-sub" role="tablist">
        <button data-d="companies" aria-current="true">Companies <span class="mono">__N_ANALYSED__</span></button>
        <button data-d="census" aria-current="false">Census <span class="mono">__N_CENSUS__</span></button>
        <button data-d="articles" aria-current="false">Articles <span class="mono">__N_ARTICLES__</span></button>
      </div>

      <div id="d-companies">
        <div class="controls">
          <input type="search" id="co-q" placeholder="Search company, leader, technology, factor...">
          <select id="co-country"><option value="">All countries</option>__OPT_C__</select>
          <label><input type="checkbox" id="co-leaders"> leaders only</label>
          <select id="co-sort"><option value="rank">sort: rank</option><option value="score">sort: score</option><option value="name">sort: name</option></select>
          <span class="count" id="co-count"></span>
        </div>
        <div id="co-list"></div>
      </div>

      <div id="d-census" hidden>
        <div class="controls">
          <input type="search" id="cs-q" placeholder="Search name, domain, description...">
          <select id="cs-country"><option value="">All countries</option>__OPT_C__</select>
          <select id="cs-platform"><option value="">All platform types</option>__OPT_P__</select>
          <label><input type="checkbox" id="cs-analysed"> analysed only</label>
          <span class="count" id="cs-count"></span>
        </div>
        <div class="tbl-wrap"><table class="dtable" id="cs-table">
          <thead><tr><th data-s="name">Company</th><th data-s="country">Country</th><th data-s="platform_type">Platform type</th><th data-s="mention_count" class="sorted">Mentions</th><th data-s="analysed">Analysed</th></tr></thead>
          <tbody></tbody>
        </table></div>
      </div>

      <div id="d-articles" hidden>
        <div class="controls">
          <input type="search" id="ar-q" placeholder="Search title, snippet, domain...">
          <select id="ar-domain"><option value="">All domains</option>__OPT_D__</select>
          <span class="count" id="ar-count"></span>
        </div>
        <div id="ar-list"></div>
      </div>
    </div>
  </section>
</div>
</main>

<footer class="ft">
  <div class="container ft-in">
    <span>Proteins.1 competitive landscape &middot; generated __GENERATED__</span>
    <span>facts &amp; leaders from cited sources &middot; scores &amp; recommendation are analytical</span>
  </div>
</footer>

<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const $=id=>document.getElementById(id);
const esc=s=>(s==null?'':String(s)).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const arr=v=>Array.isArray(v)?v:[];
const host=u=>{try{return new URL(u).host}catch(e){return u}};

/* top-level tabs */
const tabBtns=[...document.querySelectorAll('[data-tab]')];
function showTab(name){
  document.getElementById('panel-overview').hidden=(name!=='overview');
  document.getElementById('panel-data').hidden=(name!=='data');
  document.querySelectorAll('.nav-links button').forEach(b=>b.setAttribute('aria-current',b.dataset.tab===name));
  window.scrollTo({top:0,behavior:'smooth'});
}
tabBtns.forEach(b=>b.addEventListener('click',()=>showTab(b.dataset.tab)));
document.querySelectorAll('[data-jump]').forEach(b=>b.addEventListener('click',()=>{
  showTab('overview');
  setTimeout(()=>document.getElementById(b.dataset.jump).scrollIntoView({behavior:'smooth'}),40);
}));

/* data sub-tabs */
document.querySelectorAll('.data-sub button').forEach(b=>b.addEventListener('click',()=>{
  const d=b.dataset.d;
  document.querySelectorAll('.data-sub button').forEach(x=>x.setAttribute('aria-current',x===b));
  ['companies','census','articles'].forEach(n=>document.getElementById('d-'+n).hidden=(n!==d));
}));

/* companies */
function scoreBars(c){return Object.keys(D.maxpts).map(k=>{
  const v=c['score_'+k]||0,p=Math.round(100*v/D.maxpts[k]);
  return '<span class="sb"><span class="sb-k">'+k+'</span><span class="sb-t"><span class="sb-f" style="width:'+p+'%"></span></span><span class="sb-v">'+v+'/'+D.maxpts[k]+'</span></span>';
}).join('')}
function kv(rows){const r=rows.filter(x=>x[1]);return r.length?'<dl class="kv">'+r.map(x=>'<dt>'+x[0]+'</dt><dd>'+esc(x[1])+'</dd>').join('')+'</dl>':''}
function li(a){return arr(a).length?'<ul class="arrow">'+arr(a).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'<p class="none">-</p>'}
function coBody(c){
  const notes=Object.entries(c.score_notes||{}).map(x=>x[0]+': '+esc(x[1])).join(' &middot; ');
  const facts=arr(c.success_factors).filter(x=>x&&x.factor);
  return ''
  +'<div class="sec-blk"><span class="k">What they do</span>'
  +(c.what_they_do?'<p class="prose">'+esc(c.what_they_do)+'</p>':'<p class="none">not captured</p>')
  +kv([['Mechanism',c.technology_approach],['Modality',c.detection_modality],['Sensitivity',c.sensitivity_claim],['Sample',c.sample_requirement],['Stage',c.stage],['Funding',c.funding_summary],['Applications',arr(c.target_applications).join(', ')],['Partnerships',arr(c.key_partnerships).join(', ')]])
  +'</div>'
  +'<div class="sec-blk"><span class="k">The leader to study</span><p><strong>'+(esc(c.leader_name)||'<span class="none">not named</span>')+'</strong>'+(c.leader_role?' <span class="none">'+esc(c.leader_role)+'</span>':'')+'</p>'
  +(c.leader_background?'<p class="prose">'+esc(c.leader_background)+'</p>':'')
  +(c.why_worth_studying?'<p class="prose"><em>'+esc(c.why_worth_studying)+'</em></p>':'')+'</div>'
  +'<div class="sec-blk"><span class="k">What made them succeed</span>'+(facts.length?'<ul class="arrow">'+facts.map(f=>'<li>'+esc(f.factor)+(f.evidence?'<br><span class="none">'+esc(f.evidence)+'</span>':'')+'</li>').join('')+'</ul>':'<p class="none">none captured</p>')+'</div>'
  +'<div class="sec-blk"><span class="k">For Proteins.1 &mdash; applications</span>'+li(c.application_suggestions)+'</div>'
  +'<div class="sec-blk"><span class="k">For Proteins.1 &mdash; market-route moves</span>'+li(c.market_route_suggestions)+'</div>'
  +(c.route_summary?'<div class="sec-blk"><span class="k">Suggested sequence</span><p class="prose">'+esc(c.route_summary)+'</p></div>':'')
  +(arr(c.differentiators).length?'<div class="sec-blk"><span class="k">Their differentiators (claimed)</span>'+li(c.differentiators)+'</div>':'')
  +'<div class="sec-blk"><span class="k">Relevance score &mdash; '+(c.relevance_score||0).toFixed(1)+' / '+D.max_total+'</span><div class="bars2">'+scoreBars(c)+'</div>'+(notes?'<p class="none" style="font-size:12px;margin-top:8px">'+notes+'</p>':'')+'</div>'
  +'<div class="sec-blk"><span class="k">Sources</span><p class="srcs">'+(arr(c.source_urls).map(u=>'<a href="'+esc(u)+'" rel="noopener">'+esc(host(u))+'</a>').join(' &middot; ')||'<span class="none">none recorded</span>')+'</p></div>';
}
function renderCompanies(){
  const q=$('co-q').value.toLowerCase().trim(),ct=$('co-country').value,lo=$('co-leaders').checked,so=$('co-sort').value;
  let rows=D.companies.slice();
  if(ct)rows=rows.filter(c=>c.country===ct);
  if(lo)rows=rows.filter(c=>c.is_leader);
  if(q)rows=rows.filter(c=>JSON.stringify(c).toLowerCase().includes(q));
  rows.sort((a,b)=>so==='name'?a.name.localeCompare(b.name):so==='score'?(b.relevance_score||0)-(a.relevance_score||0):(a.rank||99)-(b.rank||99));
  $('co-count').textContent=rows.length+' / '+D.companies.length;
  const open=new Set([...document.querySelectorAll('#co-list .co-body:not([hidden])')].map(x=>x.dataset.n));
  $('co-list').innerHTML=rows.map((c,i)=>{
    const cf=(c.confidence||'unrated').toLowerCase();
    const o=open.has(c.name)||(open.size===0&&i===0&&!q&&!ct&&!lo);
    return '<div class="co"><button class="co-h" aria-expanded="'+o+'" data-n="'+esc(c.name)+'">'
      +'<span class="co-rank">#'+(c.rank||'?')+'</span>'
      +'<span><span class="co-name">'+esc(c.name)+'</span><span class="co-sub">'+esc(c.country||'-')+(c.detection_modality?' &middot; '+esc(c.detection_modality):'')+'</span></span>'
      +'<span class="co-right">'+(c.is_leader?'<span class="badge">leader</span>':'')+'<span class="chip chip-'+cf+'">'+cf+'</span><span class="co-score">'+(c.relevance_score||0).toFixed(1)+'</span></span>'
      +'</button><div class="co-body" data-n="'+esc(c.name)+'"'+(o?'':' hidden')+'>'+coBody(c)+'</div></div>';
  }).join('')||'<p class="none">No companies match.</p>';
  document.querySelectorAll('#co-list .co-h').forEach(btn=>btn.addEventListener('click',()=>{
    const b=btn.nextElementSibling,h=b.hidden;b.hidden=!h;btn.setAttribute('aria-expanded',h);
  }));
}
['co-q','co-country','co-leaders','co-sort'].forEach(id=>document.getElementById(id).addEventListener('input',renderCompanies));

/* census */
let cs={k:'mention_count',a:false};
function renderCensus(){
  const q=$('cs-q').value.toLowerCase().trim(),ct=$('cs-country').value,pl=$('cs-platform').value,an=$('cs-analysed').checked;
  let rows=D.census.slice();
  if(ct)rows=rows.filter(r=>r.country===ct);
  if(pl)rows=rows.filter(r=>r.platform_type===pl);
  if(an)rows=rows.filter(r=>r.analysed);
  if(q)rows=rows.filter(r=>(r.name+' '+r.domain+' '+r.description).toLowerCase().includes(q));
  rows.sort((a,b)=>{let x=a[cs.k],y=b[cs.k];
    if(typeof x==='string'||typeof y==='string')return cs.a?String(x).localeCompare(String(y)):String(y).localeCompare(String(x));
    return cs.a?(x||0)-(y||0):(y||0)-(x||0);});
  $('cs-count').textContent=rows.length+' / '+D.census.length;
  document.querySelector('#cs-table tbody').innerHTML=rows.map(r=>
    '<tr class="expandable"><td><strong>'+esc(r.name)+'</strong> '+(r.domain?'<a href="https://'+esc(r.domain)+'" rel="noopener" class="none">'+esc(r.domain)+'</a>':'')+'</td>'
    +'<td class="mono">'+esc(r.country||'?')+'</td><td class="mono none">'+esc(r.platform_type||'')+'</td>'
    +'<td class="mono">'+(r.mention_count||0)+'</td><td class="mono">'+(r.analysed?'yes':'')+'</td></tr>'
    +'<tr class="detail" hidden><td colspan="5">'+(esc(r.description)||'<span class="none">no description</span>')+'<br><span class="none">found by: '+esc(r.source_query||'-')+'</span></td></tr>'
  ).join('')||'<tr><td colspan="5" class="none">No companies match.</td></tr>';
  document.querySelectorAll('#cs-table tr.expandable').forEach(tr=>tr.addEventListener('click',()=>{
    const d=tr.nextElementSibling;if(d&&d.classList.contains('detail'))d.hidden=!d.hidden;}));
  document.querySelectorAll('#cs-table th').forEach(th=>{
    th.classList.toggle('sorted',th.dataset.s===cs.k);th.classList.toggle('asc',cs.a&&th.dataset.s===cs.k);});
}
document.querySelectorAll('#cs-table th').forEach(th=>th.addEventListener('click',()=>{
  const k=th.dataset.s,txt=(k==='name'||k==='country'||k==='platform_type');
  cs={k:k,a:cs.k===k?!cs.a:txt};renderCensus();}));
['cs-q','cs-country','cs-platform','cs-analysed'].forEach(id=>document.getElementById(id).addEventListener('input',renderCensus));

/* articles */
function renderArticles(){
  const q=$('ar-q').value.toLowerCase().trim(),dm=$('ar-domain').value;
  let rows=D.articles.slice();
  if(dm)rows=rows.filter(a=>a.domain===dm);
  if(q)rows=rows.filter(a=>(a.title+' '+a.domain+' '+a.snippet).toLowerCase().includes(q));
  rows.sort((a,b)=>(a.domain||'').localeCompare(b.domain||'')||(a.title||'').localeCompare(b.title||''));
  $('ar-count').textContent=rows.length+' / '+D.articles.length;
  $('ar-list').innerHTML=rows.map(a=>'<div class="art"><div class="art-t"><a href="'+esc(a.url)+'" rel="noopener">'+(esc(a.title)||esc(a.url))+'</a></div>'
    +'<div class="art-m">'+esc(a.domain||host(a.url))+' &nbsp;&middot;&nbsp; found by: '+esc(a.source_query||'-')+'</div>'
    +(a.snippet?'<div class="art-s">'+esc(a.snippet)+'</div>':'')+'</div>').join('')||'<p class="none">No articles match.</p>';
}
['ar-q','ar-domain'].forEach(id=>document.getElementById(id).addEventListener('input',renderArticles));

renderCompanies();renderCensus();renderArticles();
</script>
"""

preview_rows = "\n".join(
    f"""          <div class="prow">
            <span class="pn">{i:02d}</span>
            <span><span class="pname">{e(c['name'])}</span><span class="pmeta">{e(c['country'])}</span>{bar(c['relevance_score'])}</span>
            <span class="pscore">{c['relevance_score']:.1f}</span>
          </div>""" for i, c in enumerate(top3, start=1))

if opp_has:
    q4_body = f"""      <div class="pick-head">
        <span class="k">{e(opp.get('disease_area'))}</span>
        <div class="pick-marker">{e(opp.get('biomarker'))}</div>
        <p>{e(opp.get('why_it_fits'))}</p>
      </div>
      <div class="pick-cols">
        <div><h3>Why the platform is decisive here</h3>
          <div class="card">
            <p><strong>Unmet need.</strong> {e(opp.get('unmet_need'))}</p>
            <p><strong>Why no competitor owns it.</strong> {e(opp.get('competitive_gap'))}</p>
          </div>
        </div>
        <div><h3>Who pays for it first</h3>
          <div class="card">
            <p class="who">{e(opp.get('first_customer'))}</p>
            <p>{e(opp.get('first_customer_why'))}</p>
          </div>
        </div>
      </div>
      <ul class="ev-list">
{opp_evidence}
      </ul>
      {f'<p class="runner"><b>Runner-up.</b> {e(opp.get("runner_up"))}</p>' if opp.get('runner_up') else ''}"""
else:
    q4_body = """      <div class="q4-empty">
        Not generated yet. Run <code>POST /api/pick-opportunity</code> (or
        <code>scripts/collect.py</code>) with an <code>ANTHROPIC_API_KEY</code> set, then
        <code>python reports/export_json.py &amp;&amp; python reports/build_frontend_page.py</code>.
      </div>"""

out = (TEMPLATE
       .replace("__GENERATED__", generated)
       .replace("__MAX_TOTAL__", f"{MAX_TOTAL:.0f}")
       .replace("__N_CENSUS__", str(len(census)))
       .replace("__N_ANALYSED__", str(len(companies)))
       .replace("__N_TOP10__", str(len(top10)))
       .replace("__N_ARTICLES__", str(len(articles)))
       .replace("__PREVIEW_ROWS__", preview_rows)
       .replace("__Q1_TOP3__", q1_top3)
       .replace("__Q1_ROWS__", q1_rows)
       .replace("__Q2_CARDS__", q2_cards)
       .replace("__REC_FROM__", rec_from or "the top companies")
       .replace("__REC_HEADLINE__", e(rec.get("headline")))
       .replace("__REC_APPS__", apps)
       .replace("__REC_ROUTE__", route)
       .replace("__REC_SEQ__", e(rec.get("sequence")))
       .replace("__Q4_BODY__", q4_body)
       .replace("__OPT_C__", OPT_C)
       .replace("__OPT_P__", OPT_P)
       .replace("__OPT_D__", OPT_D)
       .replace("__PAYLOAD__", PAYLOAD))

OUT.write_text(out, encoding="utf-8")
print(f"wrote {OUT}  ({len(out):,} bytes)  top10={len(top10)} top3={[c['name'] for c in top3]}")
