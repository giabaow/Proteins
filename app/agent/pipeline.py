"""
Competitor profiling: for one European platform company, collect its own pages
(+ SEC / trial / FDA records where relevant), store the raw text in Chroma, and
LLM-extract a structured profile into SQLite.

Discipline:
  - the LLM only ever summarises text it was actually given, never recalls from
    memory;
  - every profile keeps its source_urls;
  - a fact not in the text becomes null / [] - never a guess.
"""
import json
import re
from urllib.parse import urlsplit

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.chroma_store import add_chunks
from app.database import CompetitorProfile, DiscoveredCompany, LeaderInsight
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
    so keep max_tokens generous (>= ~3000) or the text reply is truncated to
    nothing.
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
  "what_they_do": string | null,            // 1-2 plain sentences
  "technology_approach": string | null,     // the detection mechanism, in their terms
  "detection_modality": string | null,      // "protein" | "DNA" | "RNA" | "multi-omic" | other stated
  "sensitivity_claim": string | null,       // verbatim
  "sample_requirement": string | null,      // volume / type, verbatim
  "target_applications": [string, ...],     // e.g. "oncology", "neurology", "immunology"
  "stage": string | null,                   // "research use only" | "clinical" | "commercial" | other stated
  "funding_summary": string | null,         // rounds / totals / investors, only if stated
  "key_partnerships": [string, ...],        // named organisations
  "differentiators": [string, ...]          // concrete claimed advantages
}
"""

_LIST_FIELDS = ("target_applications", "key_partnerships", "differentiators")
_STR_FIELDS = ("what_they_do", "technology_approach", "detection_modality",
               "sensitivity_claim", "sample_requirement", "stage", "funding_summary")


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


def _collect_source_urls(company_name: str, urls: list[str]) -> list[str]:
    if urls:
        return urls

    found: list[str] = []
    for hit in search_web(f"{company_name} technology platform sensitivity applications", max_results=5):
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
    """Fill blanks in base from new; union list fields."""
    for f in _STR_FIELDS:
        if not base.get(f) and new.get(f):
            base[f] = new[f]
    for f in _LIST_FIELDS:
        seen = {s.lower() for s in base.get(f, [])}
        base[f] = base.get(f, []) + [x for x in new.get(f, []) if x.lower() not in seen]
    return base


def research_competitor(db: Session, company_name: str, urls: list[str] | None = None) -> dict:
    """Profile one competitor end to end; upsert a CompetitorProfile row."""
    company = db.query(DiscoveredCompany).filter(DiscoveredCompany.name == company_name).first()
    source_urls = _collect_source_urls(company_name, urls or [])

    profile = {f: None for f in _STR_FIELDS} | {f: [] for f in _LIST_FIELDS}
    used, failed = [], []
    for url in source_urls[:6]:
        text, error = fetch_page_text(url, return_error=True)
        if not text:
            failed.append({"url": url, "error": error})
            continue
        add_chunks(company_name, url, chunk_text(text), topic="competitor-profile", record_type="competitor")
        _merge(profile, _extract_profile(text))
        used.append(url)

    row = db.query(CompetitorProfile).filter(CompetitorProfile.company_name == company_name).first()
    if row is None:
        row = CompetitorProfile(company_name=company_name)
        db.add(row)
    row.domain = company.domain if company else ""
    row.country = company.country if company else ""
    for f in _STR_FIELDS:
        setattr(row, f, profile[f] or "")
    for f in _LIST_FIELDS:
        setattr(row, f, json.dumps(profile[f]))
    row.source_urls = json.dumps(used)
    if company is not None:
        company.profiled = True
    db.commit()
    db.refresh(row)

    return {
        "company_name": company_name,
        "sources_used": used,
        "failed_sources": failed,
        "profile": {**{f: profile[f] for f in _STR_FIELDS}, **{f: profile[f] for f in _LIST_FIELDS}},
    }


# ---------------------------------------------------------------------------
# Leader / strategy synthesis - answers three questions per competitor:
#   1. the leader worth studying
#   2. what made them succeed
#   3. application + market-route suggestions FOR Proteins.1
# ---------------------------------------------------------------------------

LEADER_SYSTEM_PROMPT = """You analyse ONE company as a possible role model for Proteins.1 - a seed-stage \
Finnish deep-tech company (VTT spinout) with a physics-based, ENZYME-FREE platform that amplifies and \
reads single protein molecules, detecting biomarkers across DNA, RNA and proteins from very small \
samples at a sensitivity current instruments cannot reach. Early targets: oncology, neurology, \
immunology in RESEARCH use; regulated clinical diagnostics to follow.

You are given text excerpts about the company (its own pages, filings, news) plus a structured fact \
sheet. Answer three questions.

Grounding rules:
- leader_name, leader_role, leader_background, why_worth_studying, success_factors: use ONLY the \
provided text. If the leader is not named in the text, set leader_name to null. Never invent a name.
- success_factors must be CONCRETE (a named partner, a specific deal, a regulatory milestone, a \
sequencing choice, a funding event) - not vague adjectives. Each needs a one-line "evidence" quote/paraphrase from the text.
- application_suggestions and market_route_suggestions are YOUR recommendations FOR Proteins.1, \
reasoned from what THIS company actually did. They may go beyond the text but must stay tied to this \
company's playbook. Keep them specific and actionable.
- route_summary: 2-4 sentences - the sequence you would advise Proteins.1 to follow, citing this \
company as the precedent.
- confidence: "high" if the leader and >=3 success factors are clearly in the text; "medium" if \
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


def _profile_factsheet(row: CompetitorProfile | None) -> str:
    if row is None:
        return ""
    def _l(v):
        try:
            return ", ".join(json.loads(v or "[]"))
        except json.JSONDecodeError:
            return ""
    lines = [
        f"what_they_do: {row.what_they_do}",
        f"technology_approach: {row.technology_approach}",
        f"detection_modality: {row.detection_modality}",
        f"sensitivity_claim: {row.sensitivity_claim}",
        f"sample_requirement: {row.sample_requirement}",
        f"stage: {row.stage}",
        f"funding_summary: {row.funding_summary}",
        f"target_applications: {_l(row.target_applications)}",
        f"key_partnerships: {_l(row.key_partnerships)}",
        f"differentiators: {_l(row.differentiators)}",
    ]
    return "STRUCTURED FACT SHEET:\n" + "\n".join(l for l in lines if not l.endswith(": ") and not l.endswith(": None"))


def analyze_leader(db: Session, company_name: str, urls: list[str] | None = None) -> dict:
    """Retrieve leadership / strategy material, synthesise answers to the three
    questions, and upsert a LeaderInsight row."""
    company = db.query(DiscoveredCompany).filter(DiscoveredCompany.name == company_name).first()
    profile = db.query(CompetitorProfile).filter(CompetitorProfile.company_name == company_name).first()

    seed_urls = list(urls or [])
    if profile and profile.source_urls:
        try:
            seed_urls += [u for u in json.loads(profile.source_urls) if u not in seed_urls]
        except json.JSONDecodeError:
            pass
    for hit in search_web(f"{company_name} founder CEO history funding go-to-market strategy milestones", max_results=5):
        u = hit.get("href")
        if u and u not in seed_urls:
            seed_urls.append(u)

    parts, used, failed = [], [], []
    for url in seed_urls[:7]:
        text, error = fetch_page_text(url, return_error=True)
        if not text:
            failed.append({"url": url, "error": error})
            continue
        add_chunks(company_name, url, chunk_text(text), topic="leader-analysis", record_type="leader")
        parts.append(f"[SOURCE] {url}\n{text[:6000]}")
        used.append(url)

    context = _profile_factsheet(profile) + "\n\n" + "\n\n".join(parts)
    data = _llm_json(LEADER_SYSTEM_PROMPT, f"COMPANY: {company_name}\n\n{context}"[:60000], max_tokens=6000)

    def _slist(key):
        v = data.get(key)
        return [x for x in v if isinstance(x, str) and x.strip()] if isinstance(v, list) else []

    factors = []
    for f in (data.get("success_factors") or []):
        if isinstance(f, dict) and f.get("factor"):
            factors.append({"factor": str(f["factor"]).strip(), "evidence": str(f.get("evidence", "")).strip()})
        elif isinstance(f, str) and f.strip():
            factors.append({"factor": f.strip(), "evidence": ""})

    row = db.query(LeaderInsight).filter(LeaderInsight.company_name == company_name).first()
    if row is None:
        row = LeaderInsight(company_name=company_name)
        db.add(row)
    row.domain = company.domain if company else (profile.domain if profile else "")
    row.country = company.country if company else (profile.country if profile else "")
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
    db.commit()
    db.refresh(row)

    return {
        "company_name": company_name,
        "sources_used": used,
        "failed_sources": failed,
        "leader_name": row.leader_name,
        "success_factors": factors,
        "application_suggestions": _slist("application_suggestions"),
        "market_route_suggestions": _slist("market_route_suggestions"),
        "route_summary": row.route_summary,
        "confidence": row.confidence,
    }
