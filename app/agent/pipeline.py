"""
Ties the tools together into the flow described in chat:

  search/SEC -> fetch raw text -> chunk -> store chunks in Chroma
             -> LLM extracts structured fields -> store in SQLite

Discipline enforced here (per the challenge brief, §15):
  - the LLM only ever summarizes text it was actually given, never asked to
    recall facts from memory
  - every structured fact keeps its source_url
  - if extraction can't find a fact in the text, it must say so rather than
    guess - see the prompt below
"""
import json
import re
from urllib.parse import urlsplit

import anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.chroma_store import add_chunks
from app.database import CaseStudy, Company
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
    """Lazy init so the app can start (and other endpoints work) even before
    ANTHROPIC_API_KEY is configured - only /api/research needs it."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def _message_text(message) -> str:
    """Join text blocks; reasoning/tool blocks may precede the JSON block."""
    return "".join(block.text for block in message.content if getattr(block, "text", None))

EXTRACTION_SYSTEM_PROMPT = """You extract structured facts about a company's go-to-market history \
from a provided text excerpt, for a market-research tool.

Rules:
- Use ONLY the text given to you. Never fill a field from general knowledge.
- If a fact isn't in the text, use null - do not guess or estimate.
- Return ONLY valid JSON, no preamble, no markdown fences.

Schema:
{
  "first_application": string | null,
  "first_customer_type": string | null,
  "go_to_market_route": string | null,
  "regulatory_path": string | null,
  "key_fact": string | null
}
"""

CASE_STUDY_EXTRACTION_SYSTEM_PROMPT = """You extract structured facts about a company's success story
from a provided text excerpt, for a market-research tool.

Rules:
- Use ONLY the text given to you. Never use outside knowledge or infer missing facts.
- Use null for an unavailable string and [] when no concrete success factor is stated.
- Success factors must be concrete actions, capabilities, partnerships, or market choices stated in the text; do not use vague adjectives.
- Return ONLY valid JSON, no preamble, no markdown fences.

Schema:
{
  "leader_name": string | null,
  "leader_background": string | null,
  "success_factors": [string, ...],
  "application": string | null,
  "market_route": string | null
}
"""


def _collect_source_urls(company_name: str, urls: list[str], query_hint: str | None) -> list[str]:
    if urls:
        return urls

    found = []
    web_hits = search_web(f"{company_name} {query_hint or 'go to market history'}", max_results=4)
    for hit in web_hits:
        url = hit.get("href")
        if url and url not in found:
            found.append(url)

    try:
        sec_hits = search_sec_filings(company_name)
        for hit in sec_hits[:2]:
            url = _sec_filing_url(hit)
            if url and url not in found:
                found.append(url)
    except Exception as exc:  # noqa: BLE001
        print(f"[pipeline] SEC search failed for {company_name}: {exc}")

    # Structured regulatory / clinical sources - these give traceable evidence
    # (clearance dates, trial phases, sponsors) that a web snippet can't.
    for search_fn, label in ((search_openfda_devices, "openFDA"), (search_clinical_trials, "ClinicalTrials.gov")):
        try:
            for hit in search_fn(company_name, limit=2):
                url = hit.get("href")
                if url and url not in found:
                    found.append(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[pipeline] {label} search failed for {company_name}: {exc}")

    return found


def _sec_filing_url(hit: dict) -> str | None:
    """Build a unique EDGAR URL from a full-text-search hit when possible."""
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
        # EDGAR archives remove dashes from the accession directory name.
        return f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{filename}"
    if cik:
        return f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=S-1"
    return None


def _extract_facts(text_excerpt: str) -> dict:
    if not settings.anthropic_api_key:
        return {"key_fact": "ANTHROPIC_API_KEY not set - skipped extraction"}

    message = _get_client().messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text_excerpt[:6000]}],
    )
    raw = _message_text(message)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"key_fact": raw[:300]}


def _extract_case_study_facts(text_excerpt: str) -> dict:
    if not settings.anthropic_api_key:
        return {
            "leader_name": None,
            "leader_background": None,
            "success_factors": [],
            "application": None,
            "market_route": None,
        }

    message = _get_client().messages.create(
        model="claude-sonnet-5",
        max_tokens=500,
        system=CASE_STUDY_EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text_excerpt[:6000]}],
    )
    raw = _message_text(message) or "{}"
    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        extracted = {}
    return {
        "leader_name": extracted.get("leader_name"),
        "leader_background": extracted.get("leader_background"),
        "success_factors": extracted.get("success_factors") if isinstance(extracted.get("success_factors"), list) else [],
        "application": extracted.get("application"),
        "market_route": extracted.get("market_route"),
    }


def _fetch_and_store_sources(
    company_name: str, urls: list[str], query_hint: str | None, record_type: str
) -> tuple[list[tuple[str, str]], list[dict]]:
    """Fetch sources, add their chunks, and fall back to a site's homepage."""
    used_sources: list[tuple[str, str]] = []
    failed_sources = []

    def process_source(url: str) -> None:
        text, error = fetch_page_text(url, return_error=True)
        if not text:
            failed_sources.append({"url": url, "error": error})
            return
        add_chunks(company_name, url, chunk_text(text), topic=query_hint or "", record_type=record_type)
        used_sources.append((url, text))

    for url in urls[:5]:
        process_source(url)

    if not used_sources and urls:
        fallback_urls = []
        for url in urls:
            parts = urlsplit(url)
            if parts.scheme in {"http", "https"} and parts.netloc:
                homepage = f"{parts.scheme}://{parts.netloc}/"
                if homepage not in urls and homepage not in fallback_urls:
                    fallback_urls.append(homepage)
        for url in fallback_urls[:5]:
            process_source(url)

    return used_sources, failed_sources


def research_company(db: Session, company_name: str, urls: list[str] | None = None, query_hint: str | None = None) -> dict:
    """
    Main entry point: research one company end to end.
    Returns a summary dict; also persists chunks to Chroma and a Company row to SQLite.
    """
    urls = _collect_source_urls(company_name, urls or [], query_hint)

    source_texts, failed_sources = _fetch_and_store_sources(company_name, urls, query_hint, "opportunity")
    all_facts = []
    used_sources = []
    for url, text in source_texts:
        facts = _extract_facts(text)
        facts["source_url"] = url
        all_facts.append(facts)
        used_sources.append(url)

    summary_text = "; ".join(f.get("key_fact", "") for f in all_facts if f.get("key_fact"))

    company = db.query(Company).filter(Company.name == company_name).first()
    if company is None:
        company = Company(name=company_name)
        db.add(company)
    company.summary = summary_text
    company.source_url = "; ".join(used_sources)
    db.commit()
    db.refresh(company)

    return {
        "company": company_name,
        "sources_used": used_sources,
        "facts_per_source": all_facts,
        "failed_sources": failed_sources,
    }


def research_case_study(
    db: Session, company_name: str, urls: list[str] | None = None, query_hint: str | None = None
) -> dict:
    """Research and persist one structured, source-traceable competitor case study."""
    source_texts, failed_sources = _fetch_and_store_sources(
        company_name, _collect_source_urls(company_name, urls or [], query_hint), query_hint, "case_study"
    )
    facts_per_source = []
    success_factors = []
    for url, text in source_texts:
        facts = _extract_case_study_facts(text)
        facts["source_url"] = url
        facts_per_source.append(facts)
        for factor in facts["success_factors"]:
            if isinstance(factor, str) and factor.strip():
                success_factors.append({"factor": factor.strip(), "source_url": url})

    def first_fact(name: str) -> str:
        return next((facts[name] for facts in facts_per_source if facts.get(name)), "")

    used_urls = [url for url, _ in source_texts]
    row = db.query(CaseStudy).filter(CaseStudy.company_name == company_name).first()
    if row is None:
        row = CaseStudy(company_name=company_name)
        db.add(row)
    row.leader_name = first_fact("leader_name")
    row.leader_background = first_fact("leader_background")
    row.success_factors = json.dumps(success_factors)
    row.application = first_fact("application")
    row.market_route = first_fact("market_route")
    row.source_urls = json.dumps(used_urls)
    db.commit()
    db.refresh(row)

    return {
        "case_study": {
            "id": row.id,
            "company_name": row.company_name,
            "leader_name": row.leader_name,
            "leader_background": row.leader_background,
            "success_factors": success_factors,
            "application": row.application,
            "market_route": row.market_route,
            "source_urls": used_urls,
            "verified": row.verified,
        },
        "facts_per_source": facts_per_source,
        "failed_sources": failed_sources,
    }
