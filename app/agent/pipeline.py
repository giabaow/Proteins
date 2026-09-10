"""
Company analysis + ranking.

  analyze_company()  - for one European platform company: collect its own pages
                       (+ SEC / trial / FDA records), store the raw text in
                       Chroma, and LLM-extract into ONE `companies` row -
                       structured facts + the playbook worth learning from.
  rank_companies()   - score every analysed company on relevance to Proteins.1
                       with a fixed formula and flag the top ones is_leader.

Discipline: the LLM only ever summarises text it was given; every row keeps its
source_urls; a fact not in the text is "" / [], never a guess. The ranking is
pure arithmetic over those outputs - no LLM, so it is repeatable.
"""
import json
import re

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.chroma_store import add_chunks
from app.database import Company, DiscoveredCompany, Recommendation
from app.agent.tools import (
    search_web,
    search_sec_filings,
    search_openfda_devices,
    search_clinical_trials,
    fetch_page_text,
    chunk_text,
)

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _message_text(message) -> str:
    return "".join(block.text for block in message.content if getattr(block, "text", None))


def _llm_json(system_prompt: str, user_text: str, max_tokens: int = 4000) -> dict:
    """Call the model and parse its JSON reply. Returns {} on any failure.

    NOTE: claude-sonnet-5 emits a thinking block that also draws on max_tokens,
    so keep max_tokens generous (>= ~3000) or the text reply is truncated away.
    """
    if not settings.anthropic_api_key or not user_text.strip():
        return {}
    try:
        message = _get_client().messages.create(
            model="claude-sonnet-5",
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_text}],
        )
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] LLM call failed: {exc}")
        return {}
    raw = _message_text(message).strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].removeprefix("json").strip() if raw.count("```") >= 2 else raw
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {}
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return {}


# ---------------------------------------------------------------------------
# Step 1 - extract facts from each fetched page
# ---------------------------------------------------------------------------

PROFILE_SYSTEM_PROMPT = """You build a structured profile of a diagnostics / life-science company from \
provided text excerpts, for a competitive-landscape database. The company is being studied as a \
possible peer of a single-molecule, enzyme-free protein-detection platform.

Rules:
- Use ONLY the text given to you. Never use outside knowledge or infer missing facts.
- Use null for an unavailable string; use [] for an unavailable list.
- Quote sensitivity and sample-volume claims verbatim when present.
- List items must be concrete (a named partner, a stated application, a specific claim) - no vague adjectives.
- Return ONLY valid JSON, no preamble, no markdown fences.

Schema:
{
  "what_they_do": string | null,
  "technology_approach": string | null,
  "detection_modality": string | null,
  "sensitivity_claim": string | null,
  "sample_requirement": string | null,
  "target_applications": [string, ...],
  "stage": string | null,
  "funding_summary": string | null,
  "key_partnerships": [string, ...],
  "differentiators": [string, ...]
}
"""

_LIST_FIELDS = ("target_applications", "key_partnerships", "differentiators")
_STR_FIELDS = ("what_they_do", "technology_approach", "detection_modality",
               "sensitivity_claim", "sample_requirement", "stage", "funding_summary")


def _extract_profile(text_excerpt: str) -> dict:
    empty = {f: None for f in _STR_FIELDS} | {f: [] for f in _LIST_FIELDS}
    parsed = _llm_json(PROFILE_SYSTEM_PROMPT, text_excerpt[:12000], max_tokens=4000)
    out = dict(empty)
    for f in _STR_FIELDS:
        if isinstance(parsed.get(f), str) and parsed[f].strip():
            out[f] = parsed[f].strip()
    for f in _LIST_FIELDS:
        if isinstance(parsed.get(f), list):
            out[f] = [str(x).strip() for x in parsed[f] if str(x).strip()]
    return out


def _merge(base: dict, new: dict) -> dict:
    for f in _STR_FIELDS:
        if not base.get(f) and new.get(f):
            base[f] = new[f]
    for f in _LIST_FIELDS:
        seen = {s.lower() for s in base.get(f, [])}
        base[f] = base.get(f, []) + [x for x in new.get(f, []) if x.lower() not in seen]
    return base


# ---------------------------------------------------------------------------
# Step 2 - synthesise the playbook (leader, what worked, what P1 should copy)
# ---------------------------------------------------------------------------

PLAYBOOK_SYSTEM_PROMPT = """You analyse ONE company as a possible role model for Proteins.1 - a seed-stage \
Finnish deep-tech company (VTT spinout) with a physics-based, ENZYME-FREE platform that amplifies and \
reads single protein molecules, detecting biomarkers across DNA, RNA and proteins from very small \
samples at a sensitivity current instruments cannot reach. Early targets: oncology, neurology, \
immunology in RESEARCH use; regulated clinical diagnostics to follow.

You are given text excerpts about the company (its own pages, filings, news) plus a structured fact \
sheet. Answer three questions.

Grounding rules:
- leader_name, leader_role, leader_background, why_worth_studying, success_factors: use ONLY the \
provided text. If the person is not named in the text, set leader_name to null. Never invent a name.
- success_factors must be CONCRETE (a named partner, a specific deal, a regulatory milestone, a \
funding event, a product decision) - not vague adjectives. Each needs a one-line "evidence" quote \
or paraphrase from the text.
- application_suggestions and market_route_suggestions are YOUR recommendations FOR Proteins.1, \
reasoned from what THIS company actually did. They may go beyond the text but must stay tied to this \
company's playbook. Keep them specific and actionable.
- route_summary: 2-4 sentences - the sequence you would advise Proteins.1 to follow, citing this \
company as the precedent.
- confidence: "high" if the person and >=3 success factors are clearly in the text; "medium" if \
partial; "low" if the text is thin.

Return ONLY JSON, no markdown fences:
{
  "leader_name": string | null,
  "leader_role": string | null,
  "leader_background": string | null,
  "why_worth_studying": string | null,
  "success_factors": [ {"factor": string, "evidence": string} ],
  "application_suggestions": [string],
  "market_route_suggestions": [string],
  "route_summary": string | null,
  "confidence": "high" | "medium" | "low"
}
"""


def _sec_filing_url(hit: dict) -> str | None:
    source = hit.get("_source") or {}
    accession = source.get("accession_number") or source.get("accessionNo") or hit.get("_id", "")
    accession_match = re.search(r"\d{10}-\d{2}-\d{6}", str(accession))
    accession = accession_match.group(0) if accession_match else ""
    cik = source.get("cik") or source.get("cik_number") or source.get("ciks")
    if isinstance(cik, list):
        cik = cik[0] if cik else None
    cik_match = re.search(r"\d+", str(cik or ""))
    cik = cik_match.group(0) if cik_match else ""
    filename = source.get("filename") or source.get("file_name") or source.get("document_filename")
    if cik and accession and filename:
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{filename}"
    if cik:
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=S-1"
    return None


def _collect_source_urls(company_name: str, extra_query: str) -> list[str]:
    found: list[str] = []
    for hit in search_web(f"{company_name} {extra_query}", max_results=5):
        url = hit.get("href")
        if url and url not in found:
            found.append(url)
    try:
        for hit in search_sec_filings(company_name)[:1]:
            url = _sec_filing_url(hit)
            if url and url not in found:
                found.append(url)
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] SEC search failed for {company_name}: {exc}")
    for search_fn, label in ((search_openfda_devices, "openFDA"), (search_clinical_trials, "ClinicalTrials.gov")):
        try:
            for hit in search_fn(company_name, limit=1):
                url = hit.get("href")
                if url and url not in found:
                    found.append(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] {label} search failed for {company_name}: {exc}")
    return found


def _factsheet(profile: dict) -> str:
    lines = [f"{k}: {profile.get(k)}" for k in _STR_FIELDS] + [
        f"target_applications: {', '.join(profile.get('target_applications', []))}",
        f"key_partnerships: {', '.join(profile.get('key_partnerships', []))}",
        f"differentiators: {', '.join(profile.get('differentiators', []))}",
    ]
    return "STRUCTURED FACT SHEET:\n" + "\n".join(
        l for l in lines if not l.endswith(": None") and not l.endswith(": ") and not l.endswith(": []")
    )


def analyze_company(db: Session, company_name: str, urls: list[str] | None = None) -> dict:
    """Collect a company's pages, extract facts, synthesise the playbook, and
    upsert one `companies` row. Does NOT score - call rank_companies() for that."""
    disc = db.query(DiscoveredCompany).filter(DiscoveredCompany.name == company_name).first()

    fact_urls = list(urls or []) or _collect_source_urls(company_name, "technology platform sensitivity applications")
    play_urls = list(fact_urls)
    for hit in search_web(f"{company_name} founder CEO history funding go-to-market strategy milestones", max_results=5):
        u = hit.get("href")
        if u and u not in play_urls:
            play_urls.append(u)

    # --- facts ---------------------------------------------------------------
    profile = {f: None for f in _STR_FIELDS} | {f: [] for f in _LIST_FIELDS}
    used, failed, page_text = [], [], []
    for url in play_urls[:7]:
        text, error = fetch_page_text(url, return_error=True)
        if not text:
            failed.append({"url": url, "error": error})
            continue
        add_chunks(company_name, url, chunk_text(text), topic="company", record_type="company")
        if url in fact_urls:
            _merge(profile, _extract_profile(text))
        page_text.append(f"[SOURCE] {url}\n{text[:6000]}")
        used.append(url)
    profile = {k: (v if v is not None else ("" if k in _STR_FIELDS else [])) for k, v in profile.items()}

    # --- playbook ---------------------------------------------------------
    context = _factsheet(profile) + "\n\n" + "\n\n".join(page_text)
    data = _llm_json(PLAYBOOK_SYSTEM_PROMPT, f"COMPANY: {company_name}\n\n{context}"[:60000], max_tokens=6000)

    def _slist(key):
        v = data.get(key)
        return [x for x in v if isinstance(x, str) and x.strip()] if isinstance(v, list) else []

    factors = []
    for f in (data.get("success_factors") or []):
        if isinstance(f, dict) and f.get("factor"):
            factors.append({"factor": str(f["factor"]).strip(), "evidence": str(f.get("evidence", "")).strip()})
        elif isinstance(f, str) and f.strip():
            factors.append({"factor": f.strip(), "evidence": ""})

    # --- upsert -------------------------------------------------------------
    row = db.query(Company).filter(Company.name == company_name).first()
    if row is None:
        row = Company(name=company_name)
        db.add(row)
    row.domain = disc.domain if disc else ""
    row.country = disc.country if disc else ""
    for f in _STR_FIELDS:
        setattr(row, f, profile[f])
    row.target_applications = json.dumps(profile["target_applications"])
    row.key_partnerships = json.dumps(profile["key_partnerships"])
    row.differentiators = json.dumps(profile["differentiators"])
    row.leader_name = (data.get("leader_name") or "").strip()
    row.leader_role = (data.get("leader_role") or "").strip()
    row.leader_background = (data.get("leader_background") or "").strip()
    row.why_worth_studying = (data.get("why_worth_studying") or "").strip()
    row.success_factors = json.dumps(factors)
    row.application_suggestions = json.dumps(_slist("application_suggestions"))
    row.market_route_suggestions = json.dumps(_slist("market_route_suggestions"))
    row.route_summary = (data.get("route_summary") or "").strip()
    row.confidence = (data.get("confidence") or "").strip().lower()
    row.source_urls = json.dumps(used)
    if disc is not None:
        disc.analysed = True
    db.commit()
    db.refresh(row)

    return {
        "company_name": company_name,
        "sources_used": used,
        "failed_sources": failed,
        "leader_name": row.leader_name,
        "success_factors": factors,
        "confidence": row.confidence,
    }


# ---------------------------------------------------------------------------
# Step 3 - rank the analysed companies; flag the leaders
# ---------------------------------------------------------------------------

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
_ROUTE_KEYS = ("spinout", "spin-out", "spin out", "university", "research use", "research-use", " ruo",
               "grant", "non-dilutive", "nondilutive", "seed round", "series a", "series b", "staged",
               "benchmark", "publication", "peer-reviewed", "clinical partnership", "pilot",
               "regulatory clearance", "accreditation", "iso 15189", "mhra", "ce mark", "ce-mark",
               "510(k)", "de novo")


def _score_platform(company: Company, disc: DiscoveredCompany | None):
    pt = (disc.platform_type if disc else "") or ""
    if pt in _PLATFORM_SCORE:
        return _PLATFORM_SCORE[pt], pt
    t = (company.technology_approach or "").lower()
    if any(k in t for k in ("single molecule", "single-molecule", "nanopore", "enzyme-free", "enzyme free")):
        return 5, "single-molecule (from tech description)"
    if any(k in t for k in ("mass photometry", "interferometric", "plasmon", "photonic")):
        return 4, "label-free single-molecule optics"
    if any(k in t for k in ("microfluidic", "diffusional")):
        return 3, "microfluidic protein analysis"
    if "proximity extension" in t:
        return 2, "affinity / high-plex proteomics"
    if any(k in t for k in ("mass spectrometry", "chromatography", "sample prep", "sample-prep")):
        return 1, "MS / sample-prep, adjacent"
    return 2, "mechanism unclassified"


def _score_stage(company: Company):
    blob = " ".join([company.stage or "", company.funding_summary or "", company.what_they_do or ""]).lower()
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


def _score_route(company: Company):
    blob = " ".join([
        company.route_summary or "",
        " ".join(json.loads(company.market_route_suggestions or "[]")),
        " ".join(f.get("factor", "") for f in json.loads(company.success_factors or "[]") if isinstance(f, dict)),
    ]).lower()
    hits = sorted({k.strip() for k in _ROUTE_KEYS if k in blob})
    val = min(5, round(len(hits) / 2))
    label = "spinout / RUO-first / staged-funding pattern" if val >= 4 else (
        "partly transferable path" if val >= 2 else "path hard to copy directly")
    return val, label


def _score_evidence(company: Company):
    c = (company.confidence or "").lower()
    return {"high": 3, "medium": 2, "low": 1}.get(c, 0), f"{c or 'unrated'} confidence"


def _score_ecosystem(company: Company):
    c = company.country or ""
    if c in _NORDIC:
        return 2, f"{c} - shares regulators, funders, talent pool with a Finnish company"
    if c:
        return 1, f"{c} - European, same regulatory frame (IVDR / EMA)"
    return 0, "location unresolved"


def rank_companies(db: Session, top_n: int = 5) -> dict:
    """Score every analysed company; flag the top `top_n` is_leader. Pure
    arithmetic over the stored fields - no LLM, re-runnable."""
    discovered = {d.name: d for d in db.query(DiscoveredCompany)}
    rows = db.query(Company).all()

    scored = []
    for row in rows:
        parts = {
            "platform": _score_platform(row, discovered.get(row.name)),
            "stage": _score_stage(row),
            "route": _score_route(row),
            "evidence": _score_evidence(row),
            "ecosystem": _score_ecosystem(row),
        }
        total = round(sum(WEIGHTS[k] * parts[k][0] for k in parts), 2)
        row.score_platform = parts["platform"][0]
        row.score_stage = parts["stage"][0]
        row.score_route = parts["route"][0]
        row.score_evidence = parts["evidence"][0]
        row.score_ecosystem = parts["ecosystem"][0]
        row.score_notes = json.dumps({k: parts[k][1] for k in parts})
        row.relevance_score = total
        scored.append((total, row))

    scored.sort(key=lambda t: -t[0])
    for i, (total, row) in enumerate(scored, 1):
        row.rank = i
        row.is_leader = i <= top_n
    db.commit()

    return {
        "ranked": len(scored),
        "leaders": [r.name for _t, r in scored[:top_n]],
        "max_score": MAX_TOTAL,
        "table": [
            {"rank": r.rank, "name": r.name, "country": r.country, "score": r.relevance_score,
             "is_leader": r.is_leader,
             "parts": {"platform": r.score_platform, "stage": r.score_stage, "route": r.score_route,
                       "evidence": r.score_evidence, "ecosystem": r.score_ecosystem}}
            for _t, r in scored
        ],
    }


# ---------------------------------------------------------------------------
# Step 4 - synthesise ONE consolidated recommendation for Proteins.1 from the
# playbooks of the top-scoring companies (Overview / question 3)
# ---------------------------------------------------------------------------

RECOMMENDATION_PROMPT = """You are advising Proteins.1 - a seed-stage Finnish deep-tech company (VTT \
spinout) with a physics-based, ENZYME-FREE platform that amplifies and reads single protein molecules \
across DNA, RNA and proteins from tiny samples, at a sensitivity current instruments cannot reach. \
Early targets: oncology, neurology, immunology in RESEARCH use; regulated clinical diagnostics later.

You are given the playbooks (leader, success factors, and their own suggestions for Proteins.1) of \
the 2-3 highest-relevance European peer companies. Synthesise ONE consolidated recommendation - not a \
per-company list. Merge overlapping advice, resolve contradictions, and keep it specific and \
actionable for a company at Proteins.1's stage.

Return ONLY JSON, no markdown fences:
{
  "headline": string,                         // one sentence - the core takeaway
  "applications": [                            // 3-5 concrete application bets, most important first
     {"application": string, "rationale": string}   // rationale cites which peer(s) support it
  ],
  "market_route": [                            // 4-6 ordered go-to-market moves
     {"step": string, "detail": string}
  ],
  "sequence": string                          // 3-5 sentences - the recommended order over time
}
"""


def synthesize_recommendation(db: Session, top_k: int = 3) -> dict:
    """Build the single Recommendation row from the top-k companies by score."""
    top = (db.query(Company).filter(Company.relevance_score > 0)
           .order_by(Company.rank).limit(top_k).all())
    if not top:
        return {"error": "no ranked companies"}

    blocks = []
    for c in top:
        factors = [f.get("factor", "") for f in json.loads(c.success_factors or "[]") if isinstance(f, dict)]
        blocks.append(
            f"### {c.name} ({c.country}) - relevance {c.relevance_score}\n"
            f"what they do: {c.what_they_do}\n"
            f"leader: {c.leader_name} ({c.leader_role})\n"
            f"success factors: {'; '.join(factors)}\n"
            f"their application suggestions for Proteins.1: {'; '.join(json.loads(c.application_suggestions or '[]'))}\n"
            f"their market-route suggestions: {'; '.join(json.loads(c.market_route_suggestions or '[]'))}\n"
            f"their route summary: {c.route_summary}"
        )
    data = _llm_json(RECOMMENDATION_PROMPT, "\n\n".join(blocks)[:60000], max_tokens=6000)

    def _pairs(key, a, b):
        out = []
        for item in (data.get(key) or []):
            if isinstance(item, dict) and item.get(a):
                out.append({a: str(item[a]).strip(), b: str(item.get(b, "")).strip()})
        return out

    row = db.query(Recommendation).filter(Recommendation.id == 1).first()
    if row is None:
        row = Recommendation(id=1)
        db.add(row)
    row.from_companies = json.dumps([c.name for c in top])
    row.headline = (data.get("headline") or "").strip()
    row.applications = json.dumps(_pairs("applications", "application", "rationale"))
    row.market_route = json.dumps(_pairs("market_route", "step", "detail"))
    row.sequence = (data.get("sequence") or "").strip()
    db.commit()
    db.refresh(row)
    return {
        "from_companies": [c.name for c in top],
        "headline": row.headline,
        "applications": json.loads(row.applications),
        "market_route": json.loads(row.market_route),
        "sequence": row.sequence,
    }
