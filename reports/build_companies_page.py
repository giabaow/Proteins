"""COMPANIES - every analysed European platform company as a briefing: what they
do, the leader worth studying, what made them succeed, and application +
market-route suggestions for Proteins.1. Companies the relevance score flags as
leaders carry a badge.

Reads data/eu_competitors.db (`companies` table) -> writes reports/companies.html
"""
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "eu_competitors.db"
OUT = Path(__file__).with_name("companies.html")
MAXPTS = {"platform": 5, "stage": 5, "route": 5, "evidence": 3, "ecosystem": 2}
MAX_TOTAL = 32

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
rows = list(db.execute("select * from companies order by rank"))
total_companies = db.execute("select count(*) from discovered_companies").fetchone()[0]
total_articles = db.execute("select count(*) from discovered_articles").fetchone()[0]
leaders = sum(1 for r in rows if r["is_leader"])
named = sum(1 for r in rows if (r["leader_name"] or "").strip())
by_country = {}
for r in rows:
    by_country[r["country"] or "—"] = by_country.get(r["country"] or "—", 0) + 1


def esc(s): return html.escape(str(s or "").strip())
def jlist(s):
    try:
        v = json.loads(s or "[]"); return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []
def cid(name):
    return "c-" + "".join(ch if ch.isalnum() else "-" for ch in name.lower())


generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

overview = []
for r in rows:
    overview.append(f"""      <tr>
        <td><a href="#{cid(r['name'])}">{esc(r['name'])}</a></td>
        <td>{'<span class="badge">leader</span>' if r['is_leader'] else '<span class="dim mono">#'+str(r['rank'])+'</span>'}</td>
        <td class="mono">{esc(r['leader_name']) or '<span class="none">not named</span>'}</td>
        <td class="mono">{esc(r['country'])}</td>
        <td class="mono dim">{esc((r['detection_modality'] or '')[:26])}</td>
        <td><span class="chip chip-{(r['confidence'] or 'unrated').lower()}">{esc(r['confidence'] or 'unrated')}</span></td>
      </tr>""")

cards = []
for r in rows:
    name = r["name"]
    conf = (r["confidence"] or "unrated").lower()
    factors = jlist(r["success_factors"])
    factor_html = "".join(
        f'<li><span class="f-claim">{esc(f.get("factor"))}</span>'
        + (f'<span class="f-ev">{esc(f.get("evidence"))}</span>' if f.get("evidence") else "")
        + "</li>"
        for f in factors if isinstance(f, dict) and f.get("factor")
    ) or '<li class="none">No concrete factors extracted from the sources.</li>'
    apps = "".join(f"<li>{esc(a)}</li>" for a in jlist(r["application_suggestions"])) or '<li class="none">-</li>'
    routes = "".join(f"<li>{esc(x)}</li>" for x in jlist(r["market_route_suggestions"])) or '<li class="none">-</li>'
    diffs = jlist(r["differentiators"])
    diff_html = ("".join(f"<li>{esc(d)}</li>" for d in diffs[:6])) if diffs else ""
    srcs = jlist(r["source_urls"])
    src_html = " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(u.split("/")[2] if "//" in u else u)}</a>'
                          for u in srcs[:8]) or '<span class="none">no sources recorded</span>'
    lead = esc(r["leader_name"]) or '<span class="none">Not named in the collected sources.</span>'
    role = f'<span class="l-role">{esc(r["leader_role"])}</span>' if r["leader_role"] else ""
    badge = f'<span class="rank-badge mono">#{r["rank"]} · leader</span>' if r["is_leader"] else f'<span class="rank-badge mono dim">#{r["rank"]}</span>'
    tech = f'<p class="ctx ctx-tech"><span class="k">Mechanism</span> {esc(r["technology_approach"])}</p>' if r["technology_approach"] else ""
    sens = f'<p class="ctx ctx-tech"><span class="k">Sensitivity</span> {esc(r["sensitivity_claim"])}</p>' if r["sensitivity_claim"] else ""
    meta_bits = [b for b in (r["country"], r["stage"], r["detection_modality"]) if b]

    cards.append(f"""  <article class="brief" id="{cid(name)}">
    <header class="brief-h">
      <div class="brief-id">{badge}
        <h3>{esc(name)}</h3>
        <span class="mono meta">{esc(' · '.join(meta_bits))}</span>
      </div>
      <span class="chip chip-{conf}">{esc(conf)} confidence</span>
    </header>
    {f'<p class="ctx">{esc(r["what_they_do"])}</p>' if r['what_they_do'] else ''}
    {tech}{sens}

    <section class="blk">
      <span class="eyebrow">The leader to study</span>
      <p class="l-name">{lead}{role}</p>
      {f'<p class="l-bg">{esc(r["leader_background"])}</p>' if r['leader_background'] else ''}
      {f'<p class="l-why"><span class="k">Why worth studying</span> {esc(r["why_worth_studying"])}</p>' if r['why_worth_studying'] else ''}
    </section>

    <section class="blk">
      <span class="eyebrow">What made them succeed</span>
      <ul class="factors">{factor_html}</ul>
    </section>

    <section class="blk rec">
      <span class="eyebrow">For Proteins.1</span>
      <div class="rec-cols">
        <div><span class="k">Applications to consider</span><ul class="sugg">{apps}</ul></div>
        <div><span class="k">Market-route moves</span><ul class="sugg">{routes}</ul></div>
      </div>
      {f'<div class="route"><span class="k">Suggested sequence</span><p>{esc(r["route_summary"])}</p></div>' if r['route_summary'] else ''}
    </section>
    {f'<section class="blk"><span class="eyebrow">Their differentiators (claimed)</span><ul class="sugg plain">{diff_html}</ul></section>' if diff_html else ''}
    <footer class="brief-f mono">Score {r['relevance_score']:.1f}/{MAX_TOTAL} (plat {r['score_platform']} · stage {r['score_stage']} · route {r['score_route']} · evid {r['score_evidence']} · eco {r['score_ecosystem']}) &nbsp;·&nbsp; Sources · {src_html}</footer>
  </article>""")

progress = ""
if len(rows) < 12:
    progress = f'<p class="progress">Collection in progress &mdash; {len(rows)} companies analysed.</p>'
country_strip = ", ".join(f"{esc(k)} ({v})" for k, v in sorted(by_country.items(), key=lambda kv: -kv[1]))

HTML = f"""<title>Companies</title>
<meta name="description" content="Every analysed European single-molecule / ultra-sensitive protein-detection company - what they do, the leader to study, what made them succeed, and suggestions for Proteins.1. Score-flagged leaders are badged.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500;8..60,600&display=swap">
<style>
:root {{
  --ground:#F5F7F8; --surface:#FFFFFF; --panel:#EBF0F1;
  --ink:#16201F; --ink-soft:#47585A; --ink-faint:#7B8A8C; --rule:#D6DDDE;
  --accent:#0E7C86; --accent-line:#0E7C8633; --accent-wash:#0E7C860F;
  --good:#2E7D4F; --mid:#8A6414; --low:#7C8A8C; --measure:66ch;
}}
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
body {{ margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16px; line-height:1.6; -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:900px; margin:0 auto; padding:64px 28px 120px; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; border-radius:2px; }}
.mono {{ font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace; }}
.none {{ color:var(--ink-faint); font-style:italic; }} .dim {{ color:var(--ink-faint); }}
.k {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-faint); margin-bottom:3px; }}
header.top {{ border-bottom:1px solid var(--rule); padding-bottom:28px; margin-bottom:36px; }}
.eyebrow-top {{ font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent); }}
h1 {{ font-size:2.55rem; line-height:1.1; font-weight:600; margin:.35em 0 .3em; text-wrap:balance; letter-spacing:-.015em; }}
.lede {{ max-width:var(--measure); color:var(--ink-soft); font-size:1.05rem; margin:0; }}
.progress {{ margin:16px 0 0; font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--mid); }}
.summary {{ display:flex; flex-wrap:wrap; gap:10px 26px; margin:22px 0 4px;
  font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--ink-soft); }}
.summary b {{ color:var(--ink); font-weight:600; }}
.badge {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.08em; text-transform:uppercase;
  color:var(--accent); border:1px solid var(--accent-line); border-radius:2px; padding:1px 6px; }}
.chip {{ display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.04em;
  text-transform:uppercase; padding:2px 8px; border-radius:2px; border:1px solid var(--rule); color:var(--ink-soft); white-space:nowrap; }}
.chip-high {{ color:var(--good); border-color:color-mix(in srgb,var(--good) 45%,transparent); }}
.chip-medium {{ color:var(--mid); border-color:color-mix(in srgb,var(--mid) 45%,transparent); }}
.chip-low,.chip-unrated {{ color:var(--low); }}
h2 {{ font-family:"IBM Plex Mono",monospace; text-transform:uppercase; font-size:12px;
  letter-spacing:.12em; color:var(--ink-faint); margin:44px 0 14px; font-weight:600; }}
.tbl-scroll {{ overflow-x:auto; border:1px solid var(--rule); border-radius:3px; background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; font-size:14px; }}
th,td {{ text-align:left; padding:10px 14px; border-bottom:1px solid var(--rule); vertical-align:top; }}
thead th {{ font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.1em;
  text-transform:uppercase; color:var(--ink-faint); background:var(--panel); }}
tbody tr:last-child td {{ border-bottom:none; }}
tbody tr:hover {{ background:var(--accent-wash); }}
.brief {{ padding:40px 0 8px; border-top:1px solid var(--rule); margin-top:40px; }}
.brief:first-of-type {{ border-top:none; }}
.brief-h {{ display:flex; justify-content:space-between; align-items:baseline; gap:18px; flex-wrap:wrap; }}
.brief-id {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
.rank-badge {{ font-size:.8rem; font-weight:600; color:var(--accent); letter-spacing:.04em; text-transform:uppercase; }}
.rank-badge.dim {{ color:var(--ink-faint); font-weight:400; }}
.brief-id h3 {{ font-size:1.7rem; font-weight:600; margin:0; letter-spacing:-.01em; }}
.brief-id .meta {{ font-size:12px; color:var(--ink-faint); }}
.ctx {{ max-width:var(--measure); color:var(--ink-soft); margin:14px 0 0; font-size:.97rem; }}
.ctx-tech {{ font-size:.9rem; }} .ctx-tech .k {{ display:inline; margin-right:6px; }}
.blk {{ margin-top:26px; }}
.eyebrow {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.12em;
  text-transform:uppercase; color:var(--accent); padding-bottom:8px; border-bottom:1px solid var(--accent-line); margin-bottom:14px; }}
.l-name {{ font-size:1.15rem; font-weight:600; margin:0; }}
.l-role {{ font-weight:400; color:var(--ink-soft); font-size:.95rem; margin-left:8px; }}
.l-bg {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.02rem; color:var(--ink-soft); max-width:var(--measure); margin:8px 0 0; }}
.l-why {{ max-width:var(--measure); margin:12px 0 0; font-size:.95rem; }}
.l-why .k {{ display:inline; margin-right:6px; }}
ul.factors {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:12px; }}
ul.factors li {{ max-width:var(--measure); }}
.f-claim {{ display:block; font-weight:500; }}
.f-ev {{ display:block; font-family:"Source Serif 4",Georgia,serif; font-size:.95rem; color:var(--ink-soft);
  padding-left:14px; border-left:2px solid var(--rule); margin-top:4px; }}
.rec {{ background:var(--accent-wash); border:1px solid var(--accent-line); border-radius:4px; padding:22px 22px 24px; }}
.rec .eyebrow {{ border-bottom-color:var(--accent-line); }}
.rec-cols {{ display:grid; grid-template-columns:1fr 1fr; gap:22px 30px; }}
ul.sugg {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:8px; font-size:.94rem; }}
ul.sugg li {{ padding-left:16px; position:relative; }}
ul.sugg li::before {{ content:"\\2192"; position:absolute; left:0; color:var(--accent); }}
ul.sugg.plain li {{ padding-left:16px; }} ul.sugg.plain li::before {{ content:"·"; }}
.route {{ margin-top:20px; padding-top:18px; border-top:1px solid var(--accent-line); }}
.route p {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.08rem; line-height:1.55; margin:4px 0 0;
  max-width:var(--measure); color:var(--ink); }}
.brief-f {{ margin-top:24px; font-size:11.5px; color:var(--ink-faint); }}
.brief-f a {{ color:var(--ink-soft); }}
footer.pg {{ margin-top:72px; padding-top:20px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--ink-faint); }}
@media (max-width:620px) {{
  .wrap {{ padding:44px 20px 90px; }} h1 {{ font-size:2rem; }}
  .rec-cols {{ grid-template-columns:1fr; }} .brief-h {{ flex-direction:column; gap:8px; }}
}}
@media (prefers-reduced-motion:reduce) {{ * {{ transition:none!important; animation:none!important; }} }}
</style>
<div class="wrap">
<header class="top">
  <span class="eyebrow-top">Proteins.1 · competitive intelligence</span>
  <h1>Companies</h1>
  <p class="lede">Every European company analysed as a possible Proteins.1 peer &mdash; single-molecule
  and ultra-sensitive protein detection, enzyme-free amplification, single-molecule protein sequencing.
  For each: what they do, the leader to study, what made them succeed, and what Proteins.1 should copy.
  Companies the relevance score selects as <span class="badge">leaders</span> are on <a href="./the-leaders">the leaders page</a>.</p>
  {progress}
  <div class="summary">
    <span><b>{len(rows)}</b> companies analysed</span>
    <span><b>{leaders}</b> flagged as leaders</span>
    <span><b>{named}</b> with a named leader</span>
    <span><b>{total_companies}</b> in the EU census</span>
    <span><b>{total_articles}</b> background sources</span>
  </div>
  <div class="summary"><span>Countries&nbsp;&nbsp;{esc(country_strip)}</span></div>
</header>

<h2>All companies</h2>
<div class="tbl-scroll">
  <table>
    <thead><tr><th>Company</th><th>Rank</th><th>Leader</th><th>Country</th><th>Modality</th><th>Conf.</th></tr></thead>
    <tbody>
{''.join(overview)}
    </tbody>
  </table>
</div>

{''.join(cards)}

<footer class="pg">Generated {generated} from data/eu_competitors.db · what-they-do, the leader and the
success factors come only from cited sources; the score and the suggestions for Proteins.1 are analytical.</footer>
</div>
"""
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT}  ({len(HTML):,} bytes, {len(rows)} companies, {leaders} leaders)")
