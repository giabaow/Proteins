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
from app.database import CompetitorProfile, DiscoveredCompany
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
    if not settings.anthropic_api_key or not text_excerpt.strip():
        return empty
    message = _get_client().messages.create(
        model="claude-sonnet-5",
        max_tokens=700,
        system=PROFILE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text_excerpt[:9000]}],
    )
    try:
        parsed = json.loads(_message_text(message) or "{}")
    except json.JSONDecodeError:
        return empty
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
