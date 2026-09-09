"""DATA EXPLORER - one interactive page over everything in data/eu_competitors.db:
the full EU census (discovered_companies), the analysed companies with their
playbooks + relevance scores, and the background article set. Self-contained:
the data is embedded and rendered client-side.

Reads reports/data/*.json (run reports/export_json.py first) -> reports/explorer.html
"""
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
OUT = HERE / "explorer.html"

census = json.loads((DATA / "discovered_companies.json").read_text())
companies = json.loads((DATA / "companies.json").read_text())
articles = json.loads((DATA / "discovered_articles.json").read_text())

MAXPTS = {"platform": 5, "stage": 5, "route": 5, "evidence": 3, "ecosystem": 2}
MAX_TOTAL = 32.5

generated = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")
countries = sorted({c.get("country") for c in census if c.get("country")})
platforms = sorted({c.get("platform_type") for c in census if c.get("platform_type")})
article_domains = sorted({a.get("domain") for a in articles if a.get("domain")})
n_leaders = sum(1 for c in companies if c.get("is_leader"))
n_analysed = len(companies)
n_named = sum(1 for c in companies if (c.get("leader_name") or "").strip())

payload = json.dumps({
    "census": census, "companies": companies, "articles": articles,
    "maxpts": MAXPTS, "max_total": MAX_TOTAL, "generated": generated,
}, ensure_ascii=False, separators=(",", ":"))


def opts(values):
    return "".join(f"<option>{v}</option>" for v in values)


TEMPLATE = r"""<title>EU Platform Competitor Explorer</title>
<meta name="description" content="Every record collected on European single-molecule / ultra-sensitive protein-detection companies - the full census, the analysed companies with playbooks and relevance scores, and the background articles - in one browsable page.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,500&display=swap">
<style>
:root {
  --ground:#F5F7F8; --surface:#FFFFFF; --panel:#EBF0F1; --panel-2:#E2E9EA;
  --ink:#16201F; --ink-soft:#47585A; --ink-faint:#7B8A8C; --rule:#D6DDDE;
  --accent:#0E7C86; --accent-line:#0E7C8633; --accent-wash:#0E7C860F;
  --good:#2E7D4F; --mid:#8A6414; --low:#7C8A8C;
}
@media (prefers-color-scheme:dark) {
  :root:not([data-theme="light"]) {
    --ground:#0E1416; --surface:#151D1F; --panel:#182224; --panel-2:#1E282A;
    --ink:#E7ECEC; --ink-soft:#A6B3B4; --ink-faint:#6C7C7E; --rule:#26312F;
    --accent:#43B7C1; --accent-line:#43B7C140; --accent-wash:#43B7C114;
    --good:#63BA88; --mid:#D2A452; --low:#7E8C8E;
  }
}
:root[data-theme="dark"] {
  --ground:#0E1416; --surface:#151D1F; --panel:#182224; --panel-2:#1E282A;
  --ink:#E7ECEC; --ink-soft:#A6B3B4; --ink-faint:#6C7C7E; --rule:#26312F;
  --accent:#43B7C1; --accent-line:#43B7C140; --accent-wash:#43B7C114;
  --good:#63BA88; --mid:#D2A452; --low:#7E8C8E;
}
* { box-sizing:border-box; }
body { margin:0; background:var(--ground); color:var(--ink);
  font-family:"IBM Plex Sans",system-ui,sans-serif; font-size:15px; line-height:1.55; -webkit-font-smoothing:antialiased; }
.wrap { max-width:1060px; margin:0 auto; padding:48px 24px 120px; }
a { color:var(--accent); text-decoration:none; } a:hover { text-decoration:underline; }
:focus-visible { outline:2px solid var(--accent); outline-offset:2px; border-radius:3px; }
.mono { font-family:"IBM Plex Mono",ui-monospace,Menlo,monospace; }
.none { color:var(--ink-faint); font-style:italic; }
.dim { color:var(--ink-faint); }
.k { font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.09em;
  text-transform:uppercase; color:var(--ink-faint); }
header.top { border-bottom:1px solid var(--rule); padding-bottom:22px; margin-bottom:22px; }
.eyebrow { font-family:"IBM Plex Mono",monospace; font-size:11.5px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--accent); }
h1 { font-size:2rem; font-weight:600; margin:.3em 0 .35em; letter-spacing:-.015em; text-wrap:balance; }
.lede { max-width:64ch; color:var(--ink-soft); margin:0; }
.stats { display:flex; flex-wrap:wrap; gap:8px 22px; margin-top:18px;
  font-family:"IBM Plex Mono",monospace; font-size:12px; color:var(--ink-soft); }
.stats b { color:var(--ink); font-weight:600; }
.tabs { display:flex; gap:4px; border-bottom:1px solid var(--rule); margin-bottom:18px; }
.tab { appearance:none; background:none; border:none; cursor:pointer; color:var(--ink-faint);
  font:inherit; font-family:"IBM Plex Mono",monospace; font-size:12px; letter-spacing:.06em;
  text-transform:uppercase; padding:10px 14px; border-bottom:2px solid transparent; }
.tab[aria-selected="true"] { color:var(--ink); border-bottom-color:var(--accent); }
.tab .c { color:var(--ink-faint); margin-left:6px; }
.controls { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:16px; align-items:center; }
.controls input[type=search], .controls select { font:inherit; font-size:13px; padding:7px 10px;
  background:var(--surface); color:var(--ink); border:1px solid var(--rule); border-radius:4px; }
.controls input[type=search] { min-width:220px; flex:1; }
.controls label { font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--ink-soft);
  display:flex; align-items:center; gap:6px; }
.count { margin-left:auto; font-family:"IBM Plex Mono",monospace; font-size:11.5px; color:var(--ink-faint); }
.chip { display:inline-block; font-family:"IBM Plex Mono",monospace; font-size:10.5px; letter-spacing:.03em;
  text-transform:uppercase; padding:2px 7px; border-radius:2px; border:1px solid var(--rule); color:var(--ink-soft); white-space:nowrap; }
.chip-high { color:var(--good); border-color:color-mix(in srgb,var(--good) 45%,transparent); }
.chip-medium { color:var(--mid); border-color:color-mix(in srgb,var(--mid) 45%,transparent); }
.chip-low,.chip-unrated { color:var(--low); }
.badge { font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.06em; text-transform:uppercase;
  color:var(--accent); border:1px solid var(--accent-line); border-radius:2px; padding:1px 6px; }
.co { border:1px solid var(--rule); border-radius:5px; background:var(--surface); margin-bottom:10px; overflow:hidden; }
.co-h { display:grid; grid-template-columns:34px 1fr auto; gap:12px; align-items:center; width:100%;
  text-align:left; background:none; border:none; cursor:pointer; font:inherit; color:inherit; padding:13px 16px; }
.co-h:hover { background:var(--accent-wash); }
.co-rank { font-family:"IBM Plex Mono",monospace; color:var(--ink-faint); font-size:13px; }
.co-name { font-weight:600; font-size:1.05rem; }
.co-sub { font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-faint); margin-top:2px; }
.co-right { display:flex; align-items:center; gap:10px; }
.co-score { font-family:"IBM Plex Mono",monospace; font-size:13px; font-weight:600; }
.co-body { padding:4px 18px 22px; border-top:1px solid var(--rule); }
.co-body[hidden] { display:none; }
.sec { margin-top:20px; }
.sec > .k { display:block; padding-bottom:6px; border-bottom:1px solid var(--accent-line); margin-bottom:10px; color:var(--accent); }
.kv { display:grid; grid-template-columns:150px 1fr; gap:4px 14px; font-size:13.5px; }
.kv dt { font-family:"IBM Plex Mono",monospace; font-size:11px; text-transform:uppercase; letter-spacing:.05em; color:var(--ink-faint); }
.kv dd { margin:0; }
.prose { font-family:"Source Serif 4",Georgia,serif; font-size:1rem; color:var(--ink-soft); max-width:64ch; }
ul.tight { margin:0; padding-left:18px; display:flex; flex-direction:column; gap:5px; font-size:13.5px; }
ul.arrow { list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:7px; font-size:13.5px; }
ul.arrow li { padding-left:16px; position:relative; max-width:64ch; }
ul.arrow li::before { content:"\2192"; position:absolute; left:0; color:var(--accent); }
.factor { max-width:64ch; }
.factor .f-ev { display:block; font-family:"Source Serif 4",Georgia,serif; font-size:.92rem; color:var(--ink-soft);
  border-left:2px solid var(--rule); padding-left:12px; margin-top:3px; }
.route { font-family:"Source Serif 4",Georgia,serif; font-size:1.05rem; color:var(--ink); max-width:64ch;
  background:var(--accent-wash); border:1px solid var(--accent-line); border-radius:4px; padding:14px 16px; margin-top:6px; }
.bars { display:flex; flex-direction:column; gap:6px; max-width:420px; }
.sb { display:grid; grid-template-columns:78px 1fr 58px; align-items:center; gap:10px;
  font-family:"IBM Plex Mono",monospace; font-size:10.5px; }
.sb-k { text-transform:uppercase; letter-spacing:.05em; color:var(--ink-faint); }
.sb-track { height:6px; background:var(--rule); border-radius:3px; overflow:hidden; }
.sb-fill { display:block; height:100%; background:var(--accent); }
.sb-v { text-align:right; color:var(--ink-soft); }
.srcs { font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-faint); word-break:break-all; }
.srcs a { color:var(--ink-soft); }
.tbl-scroll { overflow-x:auto; border:1px solid var(--rule); border-radius:5px; background:var(--surface); }
table { border-collapse:collapse; width:100%; font-size:13px; font-variant-numeric:tabular-nums; }
th,td { text-align:left; padding:8px 12px; border-bottom:1px solid var(--rule); vertical-align:top; }
thead th { font-family:"IBM Plex Mono",monospace; font-size:10px; letter-spacing:.06em; text-transform:uppercase;
  color:var(--ink-faint); background:var(--panel); cursor:pointer; white-space:nowrap; position:sticky; top:0; }
thead th.sorted::after { content:" \25be"; color:var(--accent); }
thead th.sorted.asc::after { content:" \25b4"; }
tbody tr:last-child td { border-bottom:none; }
tbody tr.expandable { cursor:pointer; }
tbody tr.expandable:hover { background:var(--accent-wash); }
tr.detail td { background:var(--panel); font-size:12.5px; color:var(--ink-soft); }
tr.detail[hidden] { display:none; }
.art { padding:12px 0; border-bottom:1px solid var(--rule); }
.art:last-child { border-bottom:none; }
.art-t { font-weight:500; font-size:14px; }
.art-m { font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-faint); margin-top:2px; }
.art-s { color:var(--ink-soft); font-size:13px; margin-top:4px; max-width:78ch; }
footer.pg { margin-top:56px; padding-top:18px; border-top:1px solid var(--rule);
  font-family:"IBM Plex Mono",monospace; font-size:11px; color:var(--ink-faint); }
@media (max-width:640px) {
  .wrap { padding:36px 16px 90px; }
  .co-h { grid-template-columns:28px 1fr; } .co-right { grid-column:2; margin-top:6px; }
  .kv { grid-template-columns:1fr; } .kv dt { margin-top:6px; }
}
@media (prefers-reduced-motion:reduce) { * { transition:none!important; } }
</style>

<div class="wrap">
<header class="top">
  <span class="eyebrow">Proteins.1 &middot; competitive intelligence</span>
  <h1>EU Platform Competitor Explorer</h1>
  <p class="lede">Everything collected on European single-molecule / ultra-sensitive protein-detection
  companies: the full discovery census, the analysed companies with their playbooks and relevance
  scores, and the background article set.</p>
  <div class="stats">
    <span><b>__N_CENSUS__</b> in census</span>
    <span><b>__N_ANALYSED__</b> analysed</span>
    <span><b>__N_LEADERS__</b> leaders</span>
    <span><b>__N_NAMED__</b> named leader</span>
    <span><b>__N_ARTICLES__</b> articles</span>
    <span><b>__N_COUNTRIES__</b> countries</span>
  </div>
</header>

<div class="tabs" role="tablist">
  <button class="tab" id="tab-companies" role="tab" aria-selected="true" aria-controls="p-companies">Companies <span class="c">__N_ANALYSED__</span></button>
  <button class="tab" id="tab-census" role="tab" aria-selected="false" aria-controls="p-census">Census <span class="c">__N_CENSUS__</span></button>
  <button class="tab" id="tab-articles" role="tab" aria-selected="false" aria-controls="p-articles">Articles <span class="c">__N_ARTICLES__</span></button>
</div>

<section id="p-companies" role="tabpanel" aria-labelledby="tab-companies">
  <div class="controls">
    <input type="search" id="co-q" placeholder="Search company, leader, technology, factor...">
    <select id="co-country"><option value="">All countries</option>__OPT_COUNTRIES__</select>
    <label><input type="checkbox" id="co-leaders"> leaders only</label>
    <select id="co-sort">
      <option value="rank">sort: rank</option>
      <option value="score">sort: score</option>
      <option value="name">sort: name</option>
    </select>
    <span class="count" id="co-count"></span>
  </div>
  <div id="co-list"></div>
</section>

<section id="p-census" role="tabpanel" aria-labelledby="tab-census" hidden>
  <div class="controls">
    <input type="search" id="cs-q" placeholder="Search name, domain, description...">
    <select id="cs-country"><option value="">All countries</option>__OPT_COUNTRIES__</select>
    <select id="cs-platform"><option value="">All platform types</option>__OPT_PLATFORMS__</select>
    <label><input type="checkbox" id="cs-analysed"> analysed only</label>
    <span class="count" id="cs-count"></span>
  </div>
  <div class="tbl-scroll"><table id="cs-table">
    <thead><tr>
      <th data-sort="name">Company</th><th data-sort="country">Country</th>
      <th data-sort="platform_type">Platform type</th>
      <th data-sort="mention_count" class="sorted">Mentions</th>
      <th data-sort="analysed">Analysed</th>
    </tr></thead>
    <tbody></tbody>
  </table></div>
</section>

<section id="p-articles" role="tabpanel" aria-labelledby="tab-articles" hidden>
  <div class="controls">
    <input type="search" id="ar-q" placeholder="Search title, snippet, domain...">
    <select id="ar-domain"><option value="">All domains</option>__OPT_DOMAINS__</select>
    <span class="count" id="ar-count"></span>
  </div>
  <div id="ar-list"></div>
</section>

<footer class="pg">Generated __GENERATED__ from data/eu_competitors.db &middot; facts, leaders and success
factors from cited sources only; relevance scores and route suggestions are analytical guidance for Proteins.1.</footer>
</div>

<script id="data" type="application/json">__PAYLOAD__</script>
<script>
const D = JSON.parse(document.getElementById('data').textContent);
const esc = s => (s==null?'':String(s)).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const arr = v => Array.isArray(v) ? v : [];
const host = u => { try { return new URL(u).host; } catch (e) { return u; } };

const tabs = [...document.querySelectorAll('.tab')];
tabs.forEach(t => t.addEventListener('click', () => {
  tabs.forEach(x => x.setAttribute('aria-selected', x === t));
  ['companies','census','articles'].forEach(n =>
    document.getElementById('p-'+n).hidden = ('tab-'+n !== t.id));
}));

function scoreBars(c) {
  const mp = D.maxpts;
  return Object.keys(mp).map(k => {
    const v = c['score_'+k] || 0, pct = Math.round(100*v/mp[k]);
    return '<span class="sb"><span class="sb-k">'+k+'</span><span class="sb-track"><span class="sb-fill" style="width:'+pct+'%"></span></span><span class="sb-v">'+v+'/'+mp[k]+'</span></span>';
  }).join('');
}
function factorList(c) {
  const f = arr(c.success_factors).filter(x => x && x.factor);
  if (!f.length) return '<p class="none">No concrete factors extracted from the sources.</p>';
  return '<ul class="arrow">' + f.map(x =>
    '<li class="factor"><span>'+esc(x.factor)+'</span>'+(x.evidence?'<span class="f-ev">'+esc(x.evidence)+'</span>':'')+'</li>').join('') + '</ul>';
}
function kvBlock(rows) {
  const r = rows.filter(x => x[1]);
  if (!r.length) return '';
  return '<dl class="kv">' + r.map(x => '<dt>'+x[0]+'</dt><dd>'+esc(x[1])+'</dd>').join('') + '</dl>';
}
function liBlock(a) {
  return arr(a).length ? '<ul class="arrow">'+arr(a).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>' : '<p class="none">-</p>';
}
function companyBody(c) {
  const notes = Object.entries(c.score_notes||{}).map(e => e[0]+': '+esc(e[1])).join(' &middot; ');
  return ''
  + '<div class="sec"><span class="k">What they do</span>'
  +   (c.what_they_do ? '<p class="prose">'+esc(c.what_they_do)+'</p>' : '<p class="none">not captured</p>')
  +   kvBlock([
        ['Mechanism', c.technology_approach], ['Modality', c.detection_modality],
        ['Sensitivity', c.sensitivity_claim], ['Sample', c.sample_requirement],
        ['Stage', c.stage], ['Funding', c.funding_summary],
        ['Applications', arr(c.target_applications).join(', ')],
        ['Partnerships', arr(c.key_partnerships).join(', ')],
      ])
  + '</div>'
  + '<div class="sec"><span class="k">The leader to study</span>'
  +   '<p><strong>'+(esc(c.leader_name)||'<span class="none">not named in the sources</span>')+'</strong>'
  +   (c.leader_role ? ' <span class="dim">'+esc(c.leader_role)+'</span>' : '') + '</p>'
  +   (c.leader_background ? '<p class="prose">'+esc(c.leader_background)+'</p>' : '')
  +   (c.why_worth_studying ? '<p><span class="k">Why</span> '+esc(c.why_worth_studying)+'</p>' : '')
  + '</div>'
  + '<div class="sec"><span class="k">What made them succeed</span>'+factorList(c)+'</div>'
  + '<div class="sec"><span class="k">For Proteins.1 &mdash; applications</span>'+liBlock(c.application_suggestions)+'</div>'
  + '<div class="sec"><span class="k">For Proteins.1 &mdash; market-route moves</span>'+liBlock(c.market_route_suggestions)+'</div>'
  + (c.route_summary ? '<div class="sec"><span class="k">Suggested sequence</span><p class="route">'+esc(c.route_summary)+'</p></div>' : '')
  + (arr(c.differentiators).length ? '<div class="sec"><span class="k">Their differentiators (claimed)</span><ul class="tight">'+arr(c.differentiators).map(d=>'<li>'+esc(d)+'</li>').join('')+'</ul></div>' : '')
  + '<div class="sec"><span class="k">Relevance score &mdash; '+(c.relevance_score||0).toFixed(1)+' / '+D.max_total+'</span>'
  +   '<div class="bars">'+scoreBars(c)+'</div>'
  +   (notes ? '<p class="dim" style="font-size:12px;margin-top:8px">'+notes+'</p>' : '')
  + '</div>'
  + '<div class="sec"><span class="k">Sources</span><p class="srcs">'
  +   (arr(c.source_urls).map(u=>'<a href="'+esc(u)+'" rel="noopener">'+esc(host(u))+'</a>').join(' &middot; ') || '<span class="none">none recorded</span>')
  + '</p></div>';
}
function renderCompanies() {
  const q = document.getElementById('co-q').value.toLowerCase().trim();
  const ctry = document.getElementById('co-country').value;
  const leadersOnly = document.getElementById('co-leaders').checked;
  const sort = document.getElementById('co-sort').value;
  let rows = D.companies.slice();
  if (ctry) rows = rows.filter(c => c.country === ctry);
  if (leadersOnly) rows = rows.filter(c => c.is_leader);
  if (q) rows = rows.filter(c => JSON.stringify(c).toLowerCase().includes(q));
  rows.sort((a,b) =>
    sort==='name' ? a.name.localeCompare(b.name) :
    sort==='score' ? (b.relevance_score||0)-(a.relevance_score||0) :
    (a.rank||99)-(b.rank||99));
  document.getElementById('co-count').textContent = rows.length + ' / ' + D.companies.length;
  const open = new Set([...document.querySelectorAll('#co-list .co-body:not([hidden])')].map(e => e.dataset.name));
  document.getElementById('co-list').innerHTML = rows.map((c,i) => {
    const conf = (c.confidence||'unrated').toLowerCase();
    const isOpen = open.has(c.name) || (open.size===0 && i===0 && !q && !ctry && !leadersOnly);
    return '<div class="co">'
      + '<button class="co-h" aria-expanded="'+isOpen+'" data-name="'+esc(c.name)+'">'
      +   '<span class="co-rank">#'+(c.rank||'?')+'</span>'
      +   '<span><span class="co-name">'+esc(c.name)+'</span>'
      +     '<span class="co-sub">'+esc(c.country||'-')+(c.detection_modality?' &middot; '+esc(c.detection_modality):'')+'</span></span>'
      +   '<span class="co-right">'
      +     (c.is_leader?'<span class="badge">leader</span>':'')
      +     '<span class="chip chip-'+conf+'">'+conf+'</span>'
      +     '<span class="co-score">'+(c.relevance_score||0).toFixed(1)+'</span>'
      +   '</span>'
      + '</button>'
      + '<div class="co-body" data-name="'+esc(c.name)+'"'+(isOpen?'':' hidden')+'>'+companyBody(c)+'</div>'
      + '</div>';
  }).join('') || '<p class="none">No companies match.</p>';
  document.querySelectorAll('#co-list .co-h').forEach(btn => btn.addEventListener('click', () => {
    const body = btn.nextElementSibling, wasHidden = body.hidden;
    body.hidden = !wasHidden; btn.setAttribute('aria-expanded', wasHidden);
  }));
}
['co-q','co-country','co-leaders','co-sort'].forEach(id =>
  document.getElementById(id).addEventListener('input', renderCompanies));

let csSort = { key:'mention_count', asc:false };
function renderCensus() {
  const q = document.getElementById('cs-q').value.toLowerCase().trim();
  const ctry = document.getElementById('cs-country').value;
  const plat = document.getElementById('cs-platform').value;
  const analysed = document.getElementById('cs-analysed').checked;
  let rows = D.census.slice();
  if (ctry) rows = rows.filter(r => r.country === ctry);
  if (plat) rows = rows.filter(r => r.platform_type === plat);
  if (analysed) rows = rows.filter(r => r.analysed);
  if (q) rows = rows.filter(r => (r.name+' '+r.domain+' '+r.description).toLowerCase().includes(q));
  rows.sort((a,b) => {
    let x=a[csSort.key], y=b[csSort.key];
    if (typeof x==='string' || typeof y==='string')
      return csSort.asc ? String(x).localeCompare(String(y)) : String(y).localeCompare(String(x));
    return csSort.asc ? (x||0)-(y||0) : (y||0)-(x||0);
  });
  document.getElementById('cs-count').textContent = rows.length + ' / ' + D.census.length;
  const tb = document.querySelector('#cs-table tbody');
  tb.innerHTML = rows.map(r =>
    '<tr class="expandable">'
    + '<td>'+esc(r.name)+' '+(r.domain?'<a href="https://'+esc(r.domain)+'" rel="noopener" class="dim">'+esc(r.domain)+'</a>':'')+'</td>'
    + '<td class="mono">'+esc(r.country||'?')+'</td>'
    + '<td class="mono dim">'+esc(r.platform_type||'')+'</td>'
    + '<td class="mono">'+(r.mention_count||0)+'</td>'
    + '<td class="mono">'+(r.analysed?'yes':'')+'</td>'
    + '</tr>'
    + '<tr class="detail" hidden><td colspan="5">'+(esc(r.description)||'<span class="none">no description captured</span>')
    +   '<br><span class="dim">found by: '+esc(r.source_query||'-')+'</span></td></tr>'
  ).join('') || '<tr><td colspan="5" class="none">No companies match.</td></tr>';
  tb.querySelectorAll('tr.expandable').forEach(tr => tr.addEventListener('click', () => {
    const d = tr.nextElementSibling; if (d && d.classList.contains('detail')) d.hidden = !d.hidden;
  }));
  document.querySelectorAll('#cs-table th').forEach(th => {
    th.classList.toggle('sorted', th.dataset.sort===csSort.key);
    th.classList.toggle('asc', csSort.asc && th.dataset.sort===csSort.key);
  });
}
document.querySelectorAll('#cs-table th').forEach(th => th.addEventListener('click', () => {
  const k = th.dataset.sort;
  const textCol = (k==='name'||k==='country'||k==='platform_type');
  csSort = { key:k, asc: csSort.key===k ? !csSort.asc : textCol };
  renderCensus();
}));
['cs-q','cs-country','cs-platform','cs-analysed'].forEach(id =>
  document.getElementById(id).addEventListener('input', renderCensus));

function renderArticles() {
  const q = document.getElementById('ar-q').value.toLowerCase().trim();
  const dom = document.getElementById('ar-domain').value;
  let rows = D.articles.slice();
  if (dom) rows = rows.filter(a => a.domain === dom);
  if (q) rows = rows.filter(a => (a.title+' '+a.domain+' '+a.snippet).toLowerCase().includes(q));
  rows.sort((a,b) => (a.domain||'').localeCompare(b.domain||'') || (a.title||'').localeCompare(b.title||''));
  document.getElementById('ar-count').textContent = rows.length + ' / ' + D.articles.length;
  document.getElementById('ar-list').innerHTML = rows.map(a =>
    '<div class="art">'
    + '<div class="art-t"><a href="'+esc(a.url)+'" rel="noopener">'+(esc(a.title)||esc(a.url))+'</a></div>'
    + '<div class="art-m">'+esc(a.domain||host(a.url))+' &nbsp;&middot;&nbsp; found by: '+esc(a.source_query||'-')+'</div>'
    + (a.snippet?'<div class="art-s">'+esc(a.snippet)+'</div>':'')
    + '</div>').join('') || '<p class="none">No articles match.</p>';
}
['ar-q','ar-domain'].forEach(id => document.getElementById(id).addEventListener('input', renderArticles));

renderCompanies(); renderCensus(); renderArticles();
</script>
"""

html = (TEMPLATE
        .replace("__N_CENSUS__", str(len(census)))
        .replace("__N_ANALYSED__", str(n_analysed))
        .replace("__N_LEADERS__", str(n_leaders))
        .replace("__N_NAMED__", str(n_named))
        .replace("__N_ARTICLES__", str(len(articles)))
        .replace("__N_COUNTRIES__", str(len(countries)))
        .replace("__OPT_COUNTRIES__", opts(countries))
        .replace("__OPT_PLATFORMS__", opts(platforms))
        .replace("__OPT_DOMAINS__", opts(article_domains))
        .replace("__GENERATED__", generated)
        .replace("__PAYLOAD__", payload))

OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT}  ({len(html):,} bytes)  census {len(census)} · companies {len(companies)} · articles {len(articles)}")
