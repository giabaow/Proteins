"""OPTION 2 - Ranked shortlist. Score every profiled EU peer on relevance to
Proteins.1, show the top 5 as deep briefings + a 'not shortlisted' table with
the reason each was cut. Transparent formula, no black box.

Reads data/eu_competitors.db -> writes scratchpad/shortlist.html
"""
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "eu_competitors.db"
OUT = Path(__file__).with_name("shortlist.html")
SHORTLIST_N = 5

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
companies = {r["name"]: r for r in db.execute("select * from discovered_companies")}
profiles = {r["company_name"]: r for r in db.execute("select * from competitor_profiles")}
insights = {r["company_name"]: r for r in db.execute("select * from leader_insights")}
total_companies = db.execute("select count(*) from discovered_companies").fetchone()[0]


def esc(s): return html.escape(str(s or "").strip())
def jlist(s):
    try:
        v = json.loads(s or "[]"); return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []

# ---------------------------------------------------------------- scoring
# relevance = 2.0*platform + 1.5*stage + 1.5*route + 1.0*evidence + 1.0*ecosystem
WEIGHTS = {"platform": 2.0, "stage": 1.5, "route": 1.5, "evidence": 1.0, "ecosystem": 1.0}
MAXPTS = {"platform": 5, "stage": 5, "route": 5, "evidence": 3, "ecosystem": 2}
MAX_TOTAL = sum(WEIGHTS[k] * MAXPTS[k] for k in WEIGHTS)  # 32.5

_PLATFORM_SCORE = {
    "single-molecule detection / digital assay": 5,
    "single-molecule protein sequencing": 5,
    "enzyme-free signal amplification": 5,
    "nanopore protein sensing": 5,
    "mass photometry": 4,
    "affinity / photonic single-molecule readout": 4,
    "microfluidic protein analysis": 3,
    "proximity extension assay (PEA)": 2,
}
_NORDIC = {"Finland", "Sweden", "Norway", "Denmark", "Iceland"}
_NEAR_EU = {"Germany", "Netherlands", "France", "Belgium", "Estonia", "Austria", "Ireland",
            "Switzerland", "United Kingdom", "Spain", "Italy"}
_ROUTE_KEYS = ("spinout", "spin-out", "spin out", "university", "research use", "research-use", " ruo",
               "grant", "non-dilutive", "nondilutive", "seed", "series a", "series b", "staged",
               "benchmark", "publication", "peer-reviewed", "clinical partnership", "pilot",
               "regulatory clearance", "accreditation", "iso 15189", "mhra", "ce mark", "ce-mark")


def _field(store, name, col):
    row = store.get(name)
    return (row[col] if row is not None else "") or ""


def score_platform(name):
    pt = _field(companies, name, "platform_type")
    if pt in _PLATFORM_SCORE:
        return _PLATFORM_SCORE[pt], pt
    tech = _field(profiles, name, "technology_approach")
    t = tech.lower()
    if any(k in t for k in ("single molecule", "single-molecule", "nanopore", "enzyme-free", "enzyme free")):
        return 5, "single-molecule (from tech description)"
    if any(k in t for k in ("mass photometry", "interferometric", "plasmon", "photonic")):
        return 4, "label-free single-molecule optics"
    if any(k in t for k in ("microfluidic", "diffusional")):
        return 3, "microfluidic protein analysis"
    if "proximity extension" in t or "pea" in t:
        return 2, "affinity / high-plex proteomics"
    if any(k in t for k in ("mass spectrometry", "chromatography", "sample prep", "sample-prep")):
        return 1, "MS / sample-prep, adjacent"
    return 2, "unclassified"


def score_stage(name):
    p = profiles.get(name)
    blob = " ".join(str(p[k] or "") for k in ("stage", "funding_summary", "what_they_do")).lower() if p else ""
    if any(k in blob for k in ("acquired", "nasdaq", "public company", "ipo", "thermo fisher")):
        return 2, "later-stage / acquired / public"
    if any(k in blob for k in ("early access", "series a", "series b", "recently launched", "spinout", "spin-out", "seed round")):
        return 5, "at the RUO->commercial transition"
    if "research use" in blob or "research-use" in blob:
        return 4, "research-use instrument company"
    if "commercial" in blob:
        return 3, "established commercial"
    if any(k in blob for k in ("service", "characterization tool", "characterisation tool")):
        return 2, "characterisation tool / services"
    return 3, "stage unclear"


def score_route(name):
    ins = insights.get(name)
    if not ins:
        return 2, "no playbook synthesised yet"
    blob = " ".join([
        ins["route_summary"] or "",
        " ".join(jlist(ins["market_route_suggestions"])),
        " ".join(f.get("factor", "") for f in jlist(ins["success_factors"]) if isinstance(f, dict)),
    ]).lower()
    hits = sorted({k for k in _ROUTE_KEYS if k in blob})
    val = min(5, round(len(hits) / 2))
    label = "spinout / RUO-first / staged funding pattern" if val >= 4 else (
        "partly transferable path" if val >= 2 else "path hard to copy directly")
    return val, label


def score_evidence(name):
    c = _field(insights, name, "confidence")
    return {"high": 3, "medium": 2, "low": 1}.get(c.lower(), 0), f"{c or 'unrated'} confidence"


def score_ecosystem(name):
    ctry = _field(companies, name, "country")
    if ctry in _NORDIC:
        return 2, f"{ctry} - shares regulators, funders, talent pool with a Finnish company"
    if ctry in _NEAR_EU:
        return 1, f"{ctry} - European, same regulatory frame (IVDR / EMA)"
    return 0, "location unresolved"


scored = []
for name in insights:  # only companies we actually profiled + analysed
    parts = {
        "platform": score_platform(name),
        "stage": score_stage(name),
        "route": score_route(name),
        "evidence": score_evidence(name),
        "ecosystem": score_ecosystem(name),
    }
    total = sum(WEIGHTS[k] * parts[k][0] for k in parts)
    scored.append({"name": name, "parts": parts, "total": total})
scored.sort(key=lambda s: -s["total"])
for i, s in enumerate(scored, 1):
    s["rank"] = i

shortlist = scored[:SHORTLIST_N]
cutoff = shortlist[-1]["total"] if shortlist else 0
rest = scored[SHORTLIST_N:]


def cut_reason(s):
    """Biggest single point gap vs the cutoff score."""
    gaps = sorted(
        ((k, WEIGHTS[k] * (MAXPTS[k] - s["parts"][k][0])) for k in WEIGHTS),
        key=lambda kv: -kv[1],
    )
    worst = gaps[0][0]
    return {
        "platform": "detection mechanism further from a single-molecule protein readout",
        "stage": "later-stage or services-only - less useful as a near-term model",
        "route": "go-to-market harder for Proteins.1 to copy directly",
        "evidence": "playbook thinly documented in public sources",
        "ecosystem": "outside the Nordic / close-EU orbit",
    }[worst] + f" ({s['parts'][worst][1]})"


generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

# ------------------------------------------------------------- rendering
def bar(k, val):
    pct = round(100 * val / MAXPTS[k])
    return (f'<span class="sb"><span class="sb-k">{k}</span>'
            f'<span class="sb-track"><span class="sb-fill" style="width:{pct}%"></span></span>'
            f'<span class="sb-v">{val}/{MAXPTS[k]}</span></span>')

score_rows = []
for s in scored:
    name = s["name"]; cid = "c-" + "".join(ch if ch.isalnum() else "-" for ch in name.lower())
    inside = s["rank"] <= SHORTLIST_N
    ctry = esc((companies.get(name) or {}) and (companies.get(name)["country"] if companies.get(name) else ""))
    score_rows.append(f"""    <tr class="{'in' if inside else 'out'}">
      <td class="rk">{s['rank']}</td>
      <td>{'<a href="#'+cid+'">'+esc(name)+'</a>' if inside else esc(name)}</td>
      <td class="mono">{ctry}</td>
      <td class="mono">{s['parts']['platform'][0]}</td>
      <td class="mono">{s['parts']['stage'][0]}</td>
      <td class="mono">{s['parts']['route'][0]}</td>
      <td class="mono">{s['parts']['evidence'][0]}</td>
      <td class="mono">{s['parts']['ecosystem'][0]}</td>
      <td class="mono tot">{s['total']:.1f}</td>
    </tr>""")

# deep briefings for the shortlist (reuses option 1's structure, tightened)
cards = []
for s in shortlist:
    name = s["name"]; cid = "c-" + "".join(ch if ch.isalnum() else "-" for ch in name.lower())
    comp = companies.get(name); prof = profiles.get(name); ins = insights.get(name) or {}
    conf = ((ins["confidence"] if ins else "") or "unrated").lower()
    home = (comp["homepage_url"] if comp else "") or ""
    platform = (comp["platform_type"] if comp else "") or ""
    what = (prof["what_they_do"] if prof else "") or ""

    why_parts = " · ".join(f"{k} {s['parts'][k][0]}/{MAXPTS[k]}" for k in WEIGHTS)
    scorebars = "".join(bar(k, s["parts"][k][0]) for k in WEIGHTS)

    factors = jlist(ins["success_factors"]) if ins else []
    factor_html = "".join(
        f'<li><span class="f-claim">{esc(f.get("factor"))}</span>'
        + (f'<span class="f-ev">{esc(f.get("evidence"))}</span>' if f.get("evidence") else "")
        + "</li>"
        for f in factors if isinstance(f, dict) and f.get("factor")
    ) or '<li class="none">No concrete factors extracted.</li>'

    apps = jlist(ins["application_suggestions"]) if ins else []
    routes = jlist(ins["market_route_suggestions"]) if ins else []
    apps_html = "".join(f"<li>{esc(a)}</li>" for a in apps) or '<li class="none">-</li>'
    routes_html = "".join(f"<li>{esc(x)}</li>" for x in routes) or '<li class="none">-</li>'
    route_summary = esc(ins["route_summary"] if ins else "")
    srcs = jlist(ins["source_urls"]) if ins else []
    src_html = " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(u.split("/")[2] if "//" in u else u)}</a>'
                          for u in srcs[:8]) or '<span class="none">no sources recorded</span>'

    lead_line = esc(ins["leader_name"] if ins else "") or '<span class="none">not named in sources</span>'
    lead_role = f'<span class="l-role">{esc(ins["leader_role"])}</span>' if ins and ins["leader_role"] else ""

    cards.append(f"""  <article class="brief" id="{cid}">
    <header class="brief-h">
      <div class="brief-id">
        <span class="rank-badge mono">#{s['rank']}</span>
        <h3>{esc(name)}</h3>
        <span class="mono meta">{esc((comp['country'] if comp else '') or '-')}{(' · ' + esc(platform)) if platform else ''}</span>
      </div>
      <span class="chip chip-{conf}">{esc(conf)} confidence</span>
    </header>
    {f'<p class="ctx">{esc(what)}</p>' if what else ''}

    <div class="scorecard">
      <span class="k">Relevance to Proteins.1 &mdash; {s['total']:.1f} / {MAX_TOTAL:.1f}</span>
      <div class="bars">{scorebars}</div>
    </div>

    <section class="blk">
      <span class="eyebrow">The leader to study</span>
      <p class="l-name">{lead_line}{lead_role}</p>
      {f'<p class="l-bg">{esc(ins["leader_background"])}</p>' if ins and ins["leader_background"] else ''}
      {f'<p class="l-why"><span class="k">Why</span> {esc(ins["why_worth_studying"])}</p>' if ins and ins["why_worth_studying"] else ''}
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
      {f'<div class="route"><span class="k">Suggested sequence</span><p>{route_summary}</p></div>' if route_summary else ''}
    </section>
    <footer class="brief-f mono">Sources · {src_html}</footer>
  </article>""")

cut_rows = "".join(
    f'<tr><td class="rk">{s["rank"]}</td><td>{esc(s["name"])}</td>'
    f'<td class="mono">{s["total"]:.1f}</td><td>{esc(cut_reason(s))}</td></tr>'
    for s in rest
) or '<tr><td colspan="4" class="none">Every profiled peer is in the shortlist so far.</td></tr>'

progress = ""
if len(insights) < 12:
    progress = f'<p class="progress">Collection in progress &mdash; {len(insights)} peers profiled. Ranking and shortlist update as the run completes.</p>'

HTML = f"""<title>Five Peers to Copy</title>
<meta name="description" content="European single-molecule protein-detection peers ranked by relevance to Proteins.1 - the top five as deep briefings, the rest with the reason they were cut.">
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
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:16px; line-height:1.6;
  -webkit-font-smoothing:antialiased; }}
.wrap {{ max-width:920px; margin:0 auto; padding:64px 28px 120px; }}
a {{ color:var(--accent); text-decoration:none; }} a:hover {{ text-decoration:underline; }}
a:focus-visible {{ outline:2px solid var(--accent); outline-offset:2px; border-radius:2px; }}
.mono {{ font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace; }}
.none {{ color:var(--ink-faint); font-style:italic; }}
.k {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-faint); margin-bottom:4px; }}

header.top {{ border-bottom:1px solid var(--rule); padding-bottom:26px; margin-bottom:34px; }}
.eyebrow-top {{ font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent); }}
h1 {{ font-size:2.55rem; line-height:1.08; font-weight:600; margin:.35em 0 .3em; text-wrap:balance;
  letter-spacing:-.015em; }}
.lede {{ max-width:var(--measure); color:var(--ink-soft); font-size:1.05rem; margin:0; }}
.progress {{ margin:16px 0 0; font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--mid); }}

.rubric {{ margin:22px 0 0; padding:16px 18px; background:var(--surface); border:1px solid var(--rule);
  border-radius:4px; font-size:13.5px; color:var(--ink-soft); }}
.rubric .k {{ margin-bottom:6px; }}
.rubric code {{ font-family:"IBM Plex Mono",monospace; color:var(--ink); font-size:12.5px; }}

h2 {{ font-family:"IBM Plex Mono",monospace; text-transform:uppercase; font-size:12px;
  letter-spacing:.12em; color:var(--ink-faint); margin:46px 0 14px; font-weight:600; }}
.tbl-scroll {{ overflow-x:auto; border:1px solid var(--rule); border-radius:3px; background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; font-variant-numeric:tabular-nums; }}
th,td {{ text-align:left; padding:9px 12px; border-bottom:1px solid var(--rule); vertical-align:top; }}
thead th {{ font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.08em;
  text-transform:uppercase; color:var(--ink-faint); background:var(--panel); }}
tbody tr:last-child td {{ border-bottom:none; }}
td.rk {{ color:var(--ink-faint); font-family:"IBM Plex Mono",monospace; width:2.5em; }}
td.tot {{ font-weight:600; color:var(--ink); }}
tr.in td {{ background:var(--accent-wash); }}
tr.out {{ color:var(--ink-soft); }}

.brief {{ padding:40px 0 8px; border-top:1px solid var(--rule); margin-top:38px; }}
.brief:first-of-type {{ border-top:none; }}
.brief-h {{ display:flex; justify-content:space-between; align-items:baseline; gap:16px; flex-wrap:wrap; }}
.brief-id {{ display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; }}
.rank-badge {{ font-size:1rem; font-weight:600; color:var(--accent); }}
.brief-id h3 {{ font-size:1.7rem; font-weight:600; margin:0; letter-spacing:-.01em; }}
.brief-id .meta {{ font-size:12px; color:var(--ink-faint); }}
.ctx {{ max-width:var(--measure); color:var(--ink-soft); margin:14px 0 0; font-size:.97rem; }}

.scorecard {{ margin-top:20px; padding:16px 18px; background:var(--panel); border-radius:4px; }}
.bars {{ display:flex; flex-direction:column; gap:7px; margin-top:8px; }}
.sb {{ display:grid; grid-template-columns:88px 1fr 42px; align-items:center; gap:10px;
  font-family:"IBM Plex Mono",monospace; font-size:11px; }}
.sb-k {{ text-transform:uppercase; letter-spacing:.06em; color:var(--ink-faint); }}
.sb-track {{ height:6px; background:var(--rule); border-radius:3px; overflow:hidden; }}
.sb-fill {{ display:block; height:100%; background:var(--accent); }}
.sb-v {{ text-align:right; color:var(--ink-soft); }}

.blk {{ margin-top:24px; }}
.eyebrow {{ display:block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.12em;
  text-transform:uppercase; color:var(--accent); padding-bottom:8px; border-bottom:1px solid var(--accent-line);
  margin-bottom:13px; }}
.l-name {{ font-size:1.12rem; font-weight:600; margin:0; }}
.l-role {{ font-weight:400; color:var(--ink-soft); font-size:.93rem; margin-left:8px; }}
.l-bg {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.02rem; color:var(--ink-soft);
  max-width:var(--measure); margin:8px 0 0; }}
.l-why {{ max-width:var(--measure); margin:10px 0 0; font-size:.94rem; }}
.l-why .k {{ display:inline; margin-right:6px; }}
ul.factors {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:11px; }}
ul.factors li {{ max-width:var(--measure); }}
.f-claim {{ display:block; font-weight:500; }}
.f-ev {{ display:block; font-family:"Source Serif 4",Georgia,serif; font-size:.94rem; color:var(--ink-soft);
  padding-left:14px; border-left:2px solid var(--rule); margin-top:4px; }}
.rec {{ background:var(--accent-wash); border:1px solid var(--accent-line); border-radius:4px; padding:20px 20px 22px; }}
.rec .eyebrow {{ border-bottom-color:var(--accent-line); }}
.rec-cols {{ display:grid; grid-template-columns:1fr 1fr; gap:20px 28px; }}
ul.sugg {{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:8px; font-size:.93rem; }}
ul.sugg li {{ padding-left:16px; position:relative; }}
ul.sugg li::before {{ content:"\\2192"; position:absolute; left:0; color:var(--accent); }}
.route {{ margin-top:18px; padding-top:16px; border-top:1px solid var(--accent-line); }}
.route p {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.07rem; line-height:1.55; margin:4px 0 0;
  max-width:var(--measure); color:var(--ink); }}
.brief-f {{ margin-top:22px; font-size:11.5px; color:var(--ink-faint); }}
.brief-f a {{ color:var(--ink-soft); }}
.chip {{ display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:11px; letter-spacing:.04em;
  text-transform:uppercase; padding:2px 8px; border-radius:2px; border:1px solid var(--rule);
  color:var(--ink-soft); white-space:nowrap; }}
.chip-high {{ color:var(--good); border-color:color-mix(in srgb,var(--good) 45%,transparent); }}
.chip-medium {{ color:var(--mid); border-color:color-mix(in srgb,var(--mid) 45%,transparent); }}
.chip-low,.chip-unrated {{ color:var(--low); }}
footer.pg {{ margin-top:70px; padding-top:20px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--ink-faint); }}
@media (max-width:620px) {{
  .wrap {{ padding:44px 20px 90px; }} h1 {{ font-size:2rem; }}
  .rec-cols {{ grid-template-columns:1fr; }} .brief-h {{ flex-direction:column; gap:8px; }}
  .sb {{ grid-template-columns:80px 1fr 38px; }}
}}
@media (prefers-reduced-motion:reduce) {{ * {{ transition:none!important; animation:none!important; }} }}
</style>
<div class="wrap">
<header class="top">
  <span class="eyebrow-top">Proteins.1 · competitive intelligence · option 2</span>
  <h1>Five Peers to Copy</h1>
  <p class="lede">Every profiled European single-molecule / ultra-sensitive protein-detection peer,
  ranked by how transferable its playbook is to Proteins.1. The top five get a full briefing;
  the rest are listed with the reason they were cut.</p>
  {progress}
  <div class="rubric">
    <span class="k">How the score is built (same formula for every company, re-runnable)</span>
    <code>relevance = 2.0·platform + 1.5·stage + 1.5·route + 1.0·evidence + 1.0·ecosystem</code><br>
    <b>platform</b> 0&ndash;5 how close the detection mechanism is to a physics-based, enzyme-free
    single-molecule protein readout &middot; <b>stage</b> 0&ndash;5 proximity to the RUO&rarr;commercial
    transition Proteins.1 faces &middot; <b>route</b> 0&ndash;5 spinout / RUO-first / staged-funding /
    clinical-partnership pattern present in their history &middot; <b>evidence</b> 0&ndash;3 how well the
    playbook is documented &middot; <b>ecosystem</b> 0&ndash;2 Nordic / close-EU proximity to a Finnish company.
    Max {MAX_TOTAL:.1f}.
  </div>
</header>

<h2>Ranking &mdash; {len(scored)} peers, census of {total_companies}</h2>
<div class="tbl-scroll"><table>
  <thead><tr><th>#</th><th>Company</th><th>Country</th><th>Plat</th><th>Stage</th><th>Route</th><th>Evid</th><th>Eco</th><th>Score</th></tr></thead>
  <tbody>
{''.join(score_rows)}
  </tbody>
</table></div>

<h2>The shortlist &mdash; deep briefings</h2>
{''.join(cards)}

<h2>Not shortlisted</h2>
<div class="tbl-scroll"><table>
  <thead><tr><th>#</th><th>Company</th><th>Score</th><th>Why it was cut</th></tr></thead>
  <tbody>{cut_rows}</tbody>
</table></div>

<footer class="pg">Generated {generated} from data/eu_competitors.db · leader &amp; success factors from cited
sources only; relevance score and route suggestions are analytical guidance for Proteins.1.</footer>
</div>
"""
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT}  ({len(HTML):,} bytes; {len(scored)} scored, shortlist of {len(shortlist)})")
for s in scored:
    print(f"  #{s['rank']:>2} {s['total']:5.1f}  {s['name']:<28} "
          + " ".join(f"{k[:4]}{s['parts'][k][0]}" for k in WEIGHTS))
