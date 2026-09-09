"""THE LEADERS - the companies flagged is_leader by the relevance score, as deep
briefings, plus the full ranking table and the reason each non-leader was cut.

Reads data/eu_competitors.db (the `companies` table, already scored by
pipeline.rank_companies) -> writes reports/leaders.html
"""
import html
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / "data" / "eu_competitors.db"
OUT = Path(__file__).with_name("leaders.html")

# must match pipeline.WEIGHTS / MAXPTS
WEIGHTS = {"platform": 2.0, "stage": 1.5, "route": 1.5, "evidence": 1.0, "ecosystem": 1.0}
MAXPTS = {"platform": 5, "stage": 5, "route": 5, "evidence": 3, "ecosystem": 2}
MAX_TOTAL = sum(WEIGHTS[k] * MAXPTS[k] for k in WEIGHTS)

db = sqlite3.connect(DB)
db.row_factory = sqlite3.Row
rows = list(db.execute("select * from companies order by rank"))
total_companies = db.execute("select count(*) from discovered_companies").fetchone()[0]
total_articles = db.execute("select count(*) from discovered_articles").fetchone()[0]
leaders = [r for r in rows if r["is_leader"]]
rest = [r for r in rows if not r["is_leader"]]


def esc(s): return html.escape(str(s or "").strip())
def jlist(s):
    try:
        v = json.loads(s or "[]"); return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []
def jobj(s):
    try:
        v = json.loads(s or "{}"); return v if isinstance(v, dict) else {}
    except json.JSONDecodeError:
        return {}


AXES = list(WEIGHTS)
generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")


def bar(k, val):
    pct = round(100 * val / MAXPTS[k])
    return (f'<span class="sb"><span class="sb-k">{k}</span>'
            f'<span class="sb-track"><span class="sb-fill" style="width:{pct}%"></span></span>'
            f'<span class="sb-v">{val}/{MAXPTS[k]}</span></span>')


def cid(name):
    return "c-" + "".join(ch if ch.isalnum() else "-" for ch in name.lower())


# ---- full ranking table ------------------------------------------------
rank_rows = []
for r in rows:
    inside = bool(r["is_leader"])
    rank_rows.append(f"""    <tr class="{'in' if inside else 'out'}">
      <td class="rk">{r['rank']}</td>
      <td>{'<a href="#'+cid(r['name'])+'">'+esc(r['name'])+'</a>' if inside else esc(r['name'])}</td>
      <td class="mono">{esc(r['country'])}</td>
      <td class="mono">{r['score_platform']}</td><td class="mono">{r['score_stage']}</td>
      <td class="mono">{r['score_route']}</td><td class="mono">{r['score_evidence']}</td>
      <td class="mono">{r['score_ecosystem']}</td>
      <td class="mono tot">{r['relevance_score']:.1f}</td>
    </tr>""")

# ---- deep briefings for the leaders --------------------------------
cards = []
for r in leaders:
    name = r["name"]
    conf = (r["confidence"] or "unrated").lower()
    notes = jobj(r["score_notes"])
    scorebars = "".join(bar(k, r[f"score_{k}"]) for k in AXES)
    factors = jlist(r["success_factors"])
    factor_html = "".join(
        f'<li><span class="f-claim">{esc(f.get("factor"))}</span>'
        + (f'<span class="f-ev">{esc(f.get("evidence"))}</span>' if f.get("evidence") else "")
        + "</li>"
        for f in factors if isinstance(f, dict) and f.get("factor")
    ) or '<li class="none">No concrete factors extracted from the sources.</li>'
    apps = "".join(f"<li>{esc(a)}</li>" for a in jlist(r["application_suggestions"])) or '<li class="none">-</li>'
    routes = "".join(f"<li>{esc(x)}</li>" for x in jlist(r["market_route_suggestions"])) or '<li class="none">-</li>'
    srcs = jlist(r["source_urls"])
    src_html = " · ".join(f'<a href="{esc(u)}" rel="noopener">{esc(u.split("/")[2] if "//" in u else u)}</a>'
                          for u in srcs[:8]) or '<span class="none">no sources recorded</span>'
    lead = esc(r["leader_name"]) or '<span class="none">not named in the sources</span>'
    role = f'<span class="l-role">{esc(r["leader_role"])}</span>' if r["leader_role"] else ""
    why_notes = " · ".join(f"{k} {r[f'score_{k}']}/{MAXPTS[k]}" for k in AXES)

    cards.append(f"""  <article class="brief" id="{cid(name)}">
    <header class="brief-h">
      <div class="brief-id">
        <span class="rank-badge mono">#{r['rank']} · leader</span>
        <h3>{esc(name)}</h3>
        <span class="mono meta">{esc(r['country'] or '-')}{(' · ' + esc(r['detection_modality'])) if r['detection_modality'] else ''}</span>
      </div>
      <span class="chip chip-{conf}">{esc(conf)} confidence</span>
    </header>
    {f'<p class="ctx">{esc(r["what_they_do"])}</p>' if r['what_they_do'] else ''}

    <div class="scorecard">
      <span class="k">Relevance to Proteins.1 &mdash; {r['relevance_score']:.1f} / {MAX_TOTAL:.0f}</span>
      <div class="bars">{scorebars}</div>
    </div>

    <section class="blk">
      <span class="eyebrow">The leader to study</span>
      <p class="l-name">{lead}{role}</p>
      {f'<p class="l-bg">{esc(r["leader_background"])}</p>' if r['leader_background'] else ''}
      {f'<p class="l-why"><span class="k">Why</span> {esc(r["why_worth_studying"])}</p>' if r['why_worth_studying'] else ''}
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
    <footer class="brief-f mono">Sources · {src_html}</footer>
  </article>""")


def cut_reason(r):
    gaps = sorted(((k, WEIGHTS[k] * (MAXPTS[k] - r[f"score_{k}"])) for k in WEIGHTS), key=lambda kv: -kv[1])
    worst = gaps[0][0]
    note = jobj(r["score_notes"]).get(worst, "")
    base = {
        "platform": "detection mechanism further from a single-molecule protein readout",
        "stage": "later-stage or services-only - less useful as a near-term model",
        "route": "go-to-market harder for Proteins.1 to copy directly",
        "evidence": "playbook thinly documented in public sources",
        "ecosystem": "outside the Nordic / close-EU orbit",
    }[worst]
    return f"{base} ({note})" if note else base


cut_rows = "".join(
    f'<tr><td class="rk">{r["rank"]}</td><td>{esc(r["name"])}</td>'
    f'<td class="mono">{r["relevance_score"]:.1f}</td><td>{esc(cut_reason(r))}</td></tr>'
    for r in rest
) or '<tr><td colspan="4" class="none">Every analysed company is flagged a leader.</td></tr>'

progress = ""
if len(rows) < 12:
    progress = f'<p class="progress">Collection in progress &mdash; {len(rows)} companies analysed.</p>'

HTML = f"""<title>The Leaders</title>
<meta name="description" content="The European single-molecule protein-detection companies whose playbook is most transferable to Proteins.1 - selected by a fixed relevance score, with deep briefings and the full ranking.">
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
h1 {{ font-size:2.55rem; line-height:1.08; font-weight:600; margin:.35em 0 .3em; text-wrap:balance; letter-spacing:-.015em; }}
.lede {{ max-width:var(--measure); color:var(--ink-soft); font-size:1.05rem; margin:0; }}
.progress {{ margin:16px 0 0; font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--mid); }}
.rubric {{ margin:22px 0 0; padding:16px 18px; background:var(--surface); border:1px solid var(--rule);
  border-radius:4px; font-size:13.5px; color:var(--ink-soft); }}
.rubric .k {{ margin-bottom:6px; }}
.rubric code {{ font-family:"IBM Plex Mono",monospace; color:var(--ink); font-size:12.5px; }}
.summary {{ display:flex; flex-wrap:wrap; gap:10px 26px; margin:20px 0 0;
  font-family:"IBM Plex Mono",monospace; font-size:12.5px; color:var(--ink-soft); }}
.summary b {{ color:var(--ink); font-weight:600; }}
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
.rank-badge {{ font-size:.85rem; font-weight:600; color:var(--accent); letter-spacing:.04em; text-transform:uppercase; }}
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
  text-transform:uppercase; color:var(--accent); padding-bottom:8px; border-bottom:1px solid var(--accent-line); margin-bottom:13px; }}
.l-name {{ font-size:1.12rem; font-weight:600; margin:0; }}
.l-role {{ font-weight:400; color:var(--ink-soft); font-size:.93rem; margin-left:8px; }}
.l-bg {{ font-family:"Source Serif 4",Georgia,serif; font-size:1.02rem; color:var(--ink-soft); max-width:var(--measure); margin:8px 0 0; }}
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
  text-transform:uppercase; padding:2px 8px; border-radius:2px; border:1px solid var(--rule); color:var(--ink-soft); white-space:nowrap; }}
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
  <span class="eyebrow-top">Proteins.1 · competitive intelligence</span>
  <h1>The Leaders</h1>
  <p class="lede">Of the {len(rows)} European single-molecule / ultra-sensitive protein-detection
  companies analysed, these {len(leaders)} scored highest on how transferable their playbook is to
  Proteins.1. Each gets a full briefing; the rest are listed with the reason they were cut.</p>
  {progress}
  <div class="rubric">
    <span class="k">Selection - a fixed formula over the collected data, no LLM, re-runnable</span>
    <code>relevance = 2.0·platform + 1.5·stage + 1.5·route + 1.0·evidence + 1.0·ecosystem</code><br>
    <b>platform</b> 0&ndash;5 mechanism closeness to a physics-based, enzyme-free single-molecule protein
    readout &middot; <b>stage</b> 0&ndash;5 proximity to the RUO&rarr;commercial transition Proteins.1 faces
    &middot; <b>route</b> 0&ndash;5 spinout / RUO-first / staged-funding / clinical-partnership pattern in
    their history &middot; <b>evidence</b> 0&ndash;3 how well the playbook is documented &middot;
    <b>ecosystem</b> 0&ndash;2 Nordic / close-EU proximity. Max {MAX_TOTAL:.0f}. The top {len(leaders)} are
    the leaders.
  </div>
  <div class="summary">
    <span><b>{len(rows)}</b> companies analysed</span>
    <span><b>{len(leaders)}</b> leaders</span>
    <span><b>{total_companies}</b> in the EU census</span>
    <span><b>{total_articles}</b> background sources</span>
  </div>
</header>

<h2>Full ranking</h2>
<div class="tbl-scroll"><table>
  <thead><tr><th>#</th><th>Company</th><th>Country</th><th>Plat</th><th>Stage</th><th>Route</th><th>Evid</th><th>Eco</th><th>Score</th></tr></thead>
  <tbody>
{''.join(rank_rows)}
  </tbody>
</table></div>

<h2>The leaders &mdash; deep briefings</h2>
{''.join(cards)}

<h2>Not selected</h2>
<div class="tbl-scroll"><table>
  <thead><tr><th>#</th><th>Company</th><th>Score</th><th>Why it was cut</th></tr></thead>
  <tbody>{cut_rows}</tbody>
</table></div>

<footer class="pg">Generated {generated} from data/eu_competitors.db · leader &amp; success factors from
cited sources only; the relevance score and route suggestions are analytical guidance for Proteins.1.</footer>
</div>
"""
OUT.write_text(HTML, encoding="utf-8")
print(f"wrote {OUT}  ({len(HTML):,} bytes; {len(rows)} companies, {len(leaders)} leaders)")
for r in rows:
    print(f"  #{r['rank']:>2} {r['relevance_score']:5.1f} {'LEADER' if r['is_leader'] else '      '}  {r['name']}")
