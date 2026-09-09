"""Render leader_insights (+ profile/company context) from data/eu_competitors.db
into a single self-contained HTML briefing: /scratchpad/leaders.html"""
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "eu_competitors.db"
OUT = Path(__file__).with_name("leaders.html")
TARGET_N = 15  # companies the collector aims to profile

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row

companies = {r["name"]: r for r in db.execute("select * from discovered_companies")}
profiles = {r["company_name"]: r for r in db.execute("select * from competitor_profiles")}
insights = list(db.execute("select * from leader_insights order by confidence desc, company_name"))
total_companies = db.execute("select count(*) from discovered_companies").fetchone()[0]
total_articles = db.execute("select count(*) from discovered_articles").fetchone()[0]


def esc(s):
    return html.escape(str(s or "").strip())


def jlist(s):
    try:
        v = json.loads(s or "[]")
        return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


CONF_RANK = {"high": 0, "medium": 1, "low": 2, "": 3}
insights.sort(key=lambda r: (CONF_RANK.get((r["confidence"] or "").lower(), 3), r["company_name"].lower()))

named = [r for r in insights if (r["leader_name"] or "").strip()]
by_country = {}
for r in insights:
    by_country[r["country"] or "—"] = by_country.get(r["country"] or "—", 0) + 1
conf_counts = {}
for r in insights:
    c = (r["confidence"] or "unrated").lower()
    conf_counts[c] = conf_counts.get(c, 0) + 1

generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

# ---- overview rows -------------------------------------------------------
overview_rows = []
for r in insights:
    cid = "c-" + "".join(ch if ch.isalnum() else "-" for ch in r["company_name"].lower())
    conf = (r["confidence"] or "unrated").lower()
    _p = profiles.get(r["company_name"])
    modality = (_p["detection_modality"] if _p else "") or ""
    overview_rows.append(f"""      <tr>
        <td><a href="#{cid}">{esc(r['company_name'])}</a></td>
        <td class="mono">{esc(r['leader_name']) or '<span class="none">not named</span>'}</td>
        <td>{esc(r['leader_role'])}</td>
        <td class="mono">{esc(r['country'])}</td>
        <td class="mono dim">{esc(modality[:26])}</td>
        <td><span class="chip chip-{conf}">{esc(conf)}</span></td>
      </tr>""")

# ---- detail cards -----------------------------------------------------
cards = []
for r in insights:
    name = r["company_name"]
    cid = "c-" + "".join(ch if ch.isalnum() else "-" for ch in name.lower())
    comp = companies.get(name)
    prof = profiles.get(name)
    conf = (r["confidence"] or "unrated").lower()
    home = (comp["homepage_url"] if comp else "") or ""
    platform = (comp["platform_type"] if comp else "") or ""
    what = (prof["what_they_do"] if prof else "") or ""
    tech = (prof["technology_approach"] if prof else "") or ""

    factors = jlist(r["success_factors"])
    factor_html = "".join(
        f"""<li><span class="f-claim">{esc(f.get('factor'))}</span>"""
        + (f"""<span class="f-ev">{esc(f.get('evidence'))}</span>""" if f.get("evidence") else "")
        + "</li>"
        for f in factors if isinstance(f, dict) and f.get("factor")
    ) or '<li class="none">No concrete factors extracted from the sources.</li>'

    apps = jlist(r["application_suggestions"])
    routes = jlist(r["market_route_suggestions"])
    apps_html = "".join(f"<li>{esc(a)}</li>" for a in apps) or '<li class="none">—</li>'
    routes_html = "".join(f"<li>{esc(x)}</li>" for x in routes) or '<li class="none">—</li>'

    srcs = jlist(r["source_urls"])
    src_html = " · ".join(
        f'<a href="{esc(u)}" rel="noopener">{esc(u.split("/")[2] if "//" in u else u)}</a>' for u in srcs[:8]
    ) or '<span class="none">no sources recorded</span>'

    context = ""
    if what:
        context += f'<p class="ctx">{esc(what)}</p>'
    if tech:
        context += f'<p class="ctx ctx-tech"><span class="k">Mechanism</span> {esc(tech)}</p>'

    route_summary = esc(r["route_summary"])
    route_block = f'<div class="route"><span class="k">Suggested sequence for Proteins.1</span><p>{route_summary}</p></div>' if route_summary else ""

    cards.append(f"""  <article class="brief" id="{cid}">
    <header class="brief-h">
      <div class="brief-id">
        <h3>{esc(name)}</h3>
        <span class="mono meta">{esc((comp['country'] if comp else '') or '—')}{(' · ' + esc(platform)) if platform else ''}</span>
      </div>
      <div class="brief-links">
        <span class="chip chip-{conf}">{esc(conf)} confidence</span>
        {f'<a class="home mono" href="{esc(home)}" rel="noopener">{esc(home.split("//")[-1].rstrip("/"))}</a>' if home else ''}
      </div>
    </header>
    {context}

    <section class="blk">
      <span class="eyebrow">The leader to study</span>
      <div class="leader">
        <p class="l-name">{esc(r['leader_name']) or '<span class="none">Not named in the collected sources.</span>'}
          {f'<span class="l-role">{esc(r["leader_role"])}</span>' if r['leader_role'] else ''}</p>
        {f'<p class="l-bg">{esc(r["leader_background"])}</p>' if r['leader_background'] else ''}
        {f'<p class="l-why"><span class="k">Why worth studying</span> {esc(r["why_worth_studying"])}</p>' if r['why_worth_studying'] else ''}
      </div>
    </section>

    <section class="blk">
      <span class="eyebrow">What made them succeed</span>
      <ul class="factors">{factor_html}</ul>
    </section>

    <section class="blk rec">
      <span class="eyebrow">For Proteins.1</span>
      <div class="rec-cols">
        <div><span class="k">Applications to consider</span><ul class="sugg">{apps_html}</ul></div>
        <div><span class="k">Market-route moves</span><ul class="sugg">{routes_html}</ul></div>
      </div>
      {route_block}
    </section>

    <footer class="brief-f mono">Sources · {src_html}</footer>
  </article>""")

progress_note = ""
if len(insights) < TARGET_N:
    progress_note = f"""<p class="progress">Collection in progress — {len(insights)} of ~{TARGET_N} European peers profiled so far. This page refreshes as the run completes.</p>"""

conf_strip = " · ".join(f'<span class="chip chip-{c if c in ("high","medium","low") else "unrated"}">{c} {n}</span>'
                        for c, n in sorted(conf_counts.items(), key=lambda kv: CONF_RANK.get(kv[0], 3)))
country_strip = ", ".join(f"{esc(k)} ({v})" for k, v in sorted(by_country.items(), key=lambda kv: -kv[1]))

HTML = f"""<title>Leaders Worth Studying</title>
<meta name="description" content="European single-molecule / ultra-sensitive protein-detection peers — the leader to study, what made them succeed, and what Proteins.1 should copy.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap">
<style>
:root {{
  --ground:#F5F7F8; --surface:#FFFFFF; --panel:#EBF0F1;
  --ink:#16201F; --ink-soft:#47585A; --ink-faint:#7B8A8C; --rule:#D6DDDE;
  --accent:#0E7C86; --accent-line:#0E7C8633; --accent-wash:#0E7C860F;
  --good:#2E7D4F; --mid:#8A6414; --low:#7C8A8C;
  --measure:66ch;
}}
:root:not([data-theme="light"]) {{ }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --ground:#0E1416; --surface:#151D1F; --panel:#182224;
    --ink:#E7ECEC; --ink-soft:#A6B3B4; --ink-faint:#6C7C7E; --rule:#26312F;
    --accent:#43B7C1; --accent-line:#43B7C140; --accent-wash:#43B7C114;
    --good:#63BA88; --mid:#D2A452; --low:#7E8C8E;
  }}
}}
:root[data-theme="dark"] {{
  --ground:#0E1416; --surface:#151D1F; --panel:#182224;
  --ink:#E7ECEC; --ink-soft:#A6B3B4; --ink-faint:#6C7C7E; --rule:#26312F;
  --accent:#43B7C1; --accent-line:#43B7C140; --accent-wash:#43B7C114;
  --good:#63BA88; --mid:#D2A452; --low:#7E8C8E;
}}

* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:900px; margin:0 auto; padding:64px 28px 120px; }}
a {{ color:var(--accent); text-decoration:none; }}
a:hover {{ text-decoration:underline; }}
a:focus-visible, tr:focus-within a {{ outline:2px solid var(--accent); outline-offset:2px; border-radius:2px; }}
.mono {{ font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace; }}
.none {{ color:var(--ink-faint); font-style:italic; }}
.k {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-faint); margin-bottom:3px; }}

/* masthead */
header.top {{ border-bottom:1px solid var(--rule); padding-bottom:28px; margin-bottom:36px; }}
.eyebrow-top {{ font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent); }}
h1 {{ font-size:2.55rem; line-height:1.1; font-weight:600; margin:.35em 0 .3em; text-wrap:balance;
  letter-spacing:-.015em; }}
.lede {{ max-width:var(--measure); color:var(--ink-soft); font-size:1.05rem; margin:0; }}
.progress {{ margin:18px 0 0; font-family:"IBM Plex Mono",monospace; font-size:12.5px;
  color:var(--mid); }}

/* summary strip */
.summary {{ display:flex; flex-wrap:wrap; gap:10px 26px; margin:24px 0 4px;
  font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--ink-soft); }}
.summary b {{ color:var(--ink); font-weight:600; }}

/* chips */
.chip {{ display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:11px;
  letter-spacing:.04em; text-transform:uppercase; padding:2px 8px; border-radius:2px;
  border:1px solid var(--rule); color:var(--ink-soft); white-space:nowrap; }}
.chip-high {{ color:var(--good); border-color:color-mix(in srgb,var(--good) 45%,transparent); }}
.chip-medium {{ color:var(--mid); border-color:color-mix(in srgb,var(--mid) 45%,transparent); }}
.chip-low, .chip-unrated {{ color:var(--low); }}

/* overview table */
h2 {{ font-size:1.05rem; font-weight:600; letter-spacing:.02em; margin:44px 0 14px;
  font-family:"IBM Plex Mono",monospace; text-transform:uppercase; font-size:12px;
  letter-spacing:.12em; color:var(--ink-faint); }}
.tbl-scroll {{ overflow-x:auto; border:1px solid var(--rule); border-radius:3px; background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th, td {{ text-align:left; padding:10px 14px; border-bottom:1px solid var(--rule); vertical-align:top; }}
thead th {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--ink-faint); background:var(--panel); position:sticky; top:0; }}
tbody tr:last-child td {{ border-bottom:none; }}
tbody tr:hover {{ background:var(--accent-wash); }}
td.dim {{ color:var(--ink-faint); }}

/* briefing cards */
.brief {{ padding:40px 0 8px; border-top:1px solid var(--rule); margin-top:40px; }}
.brief:first-of-type {{ border-top:none; }}
.brief-h {{ display:flex; justify-content:space-between; align-items:baseline; gap:18px; flex-wrap:wrap; }}
.brief-id h3 {{ font-size:1.7rem; font-weight:600; margin:0; letter-spacing:-.01em; }}
.brief-id .meta {{ font-size:12px; color:var(--ink-faint); }}
.brief-links {{ display:flex; align-items:center; gap:12px; flex-wrap:wrap; }}
.home {{ font-size:12px; }}
.ctx {{ max-width:var(--measure); color:var(--ink-soft); margin:14px 0 0; font-size:.97rem; }}
.ctx-tech {{ font-size:.9rem; }}
.ctx-tech .k {{ display:inline; margin-right:6px; }}

.blk {{ margin-top:26px; }}
.eyebrow {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.12em;
  text-transform:uppercase; color:var(--accent); padding-bottom:8px; border-bottom:1px solid var(--accent-line);
  margin-bottom:14px; }}

.leader .l-name {{ font-size:1.15rem; font-weight:600; margin:0; }}
.leader .l-role {{ font-weight:400; color:var(--ink-soft); font-size:.95rem; margin-left:8px; }}
.leader .l-bg {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.02rem; color:var(--ink-soft);
  max-width:var(--measure); margin:8px 0 0; }}
.leader .l-why {{ max-width:var(--measure); margin:12px 0 0; font-size:.95rem; }}
.leader .l-why .k {{ display:inline; margin-right:6px; }}

ul.factors {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:12px; }}
ul.factors li {{ max-width:var(--measure); }}
.f-claim {{ display:block; font-weight:500; }}
.f-ev {{ display:block; font-family:"Source Serif 4",Georgia,serif; font-size:.95rem;
  color:var(--ink-soft); padding-left:14px; border-left:2px solid var(--rule); margin-top:4px; }}

.rec {{ background:var(--accent-wash); border:1px solid var(--accent-line); border-radius:4px;
  padding:22px 22px 24px; }}
.rec .eyebrow {{ border-bottom-color:var(--accent-line); }}
.rec-cols {{ display:grid; grid-template-columns:1fr 1fr; gap:22px 30px; }}
ul.sugg {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:8px; font-size:.94rem; }}
ul.sugg li {{ padding-left:16px; position:relative; }}
ul.sugg li::before {{ content:"→"; position:absolute; left:0; color:var(--accent); }}
.route {{ margin-top:20px; padding-top:18px; border-top:1px solid var(--accent-line); }}
.route p {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.08rem; line-height:1.55;
  margin:4px 0 0; max-width:var(--measure); color:var(--ink); }}

.brief-f {{ margin-top:24px; font-size:11.5px; color:var(--ink-faint); }}
.brief-f a {{ color:var(--ink-soft); }}

footer.pg {{ margin-top:72px; padding-top:20px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--ink-faint); }}

@media (max-width:620px) {{
  .wrap {{ padding:44px 20px 90px; }}
  h1 {{ font-size:2rem; }}
  .rec-cols {{ grid-template-columns:1fr; }}
  .brief-h {{ flex-direction:column; gap:8px; }}
}}
@media (prefers-reduced-motion:reduce) {{ * {{ transition:none!important; animation:none!important; }} }}
</style>

<div class="wrap">
<header class="top">
  <span class="eyebrow-top">Proteins.1 · competitive intelligence</span>
  <h1>Leaders Worth Studying</h1>
  <p class="lede">European companies building a Proteins.1-type platform — single-molecule and
  ultra-sensitive protein detection, enzyme-free amplification, single-molecule protein
  sequencing. For each: the leader to study, what made them succeed, and what Proteins.1
  should copy.</p>
  {progress_note}
  <div class="summary">
    <span><b>{len(insights)}</b> peers analysed</span>
    <span><b>{len(named)}</b> with a named leader</span>
    <span><b>{total_companies}</b> in the EU census</span>
    <span><b>{total_articles}</b> background sources</span>
  </div>
  <div class="summary"><span>Confidence&nbsp;&nbsp;{conf_strip}</span></div>
  <div class="summary"><span>Countries&nbsp;&nbsp;{esc(country_strip)}</span></div>
</header>

<h2>All peers at a glance</h2>
<div class="tbl-scroll">
  <table>
    <thead><tr><th>Company</th><th>Leader</th><th>Role</th><th>Country</th><th>Modality</th><th>Conf.</th></tr></thead>
    <tbody>
{''.join(overview_rows)}
    </tbody>
  </table>
</div>

{''.join(cards)}

<footer class="pg">
  Generated {generated} from data/eu_competitors.db · answers 1) leader worth studying
  2) what made them succeed 3) application &amp; market-route suggestions.
  Questions 1–2 are drawn only from cited sources; question 3 is analytical guidance for Proteins.1.
</footer>
</div>
"""

OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT}  ({len(HTML):,} bytes, {len(insights)} insight rows)")
