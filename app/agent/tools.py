"""
Low-level tools the agent pipeline calls. Kept as plain functions (not framework
tool decorators) so they're easy to unit-test and swap - wrap them for
LangChain/LangGraph if you want a more autonomous agent loop.

Rate limiting: a 1s sleep before each fetch is intentional - don't remove it
during the demo, a 403 mid-pitch is worse than a slightly slower pipeline.
"""
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import requests
import trafilatura
from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ResearchAgent/1.0; hackathon project)"}

_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)


def _search_serper(query: str, max_results: int) -> list[dict]:
    """Serper.dev Google Search API - reliable, not rate-limit-prone, needs a key.

    Free tier is 2,500 one-time credits (one credit per query); paid after that.
    Returns [] (never raises) so callers fall through to the no-key backends on
    any failure or missing key. Get a key at https://serper.dev/
    """
    if not settings.serper_api_key:
        return []
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            json={"q": query, "num": max_results},
            headers={
                "X-API-KEY": settings.serper_api_key,
                "Content-Type": "application/json",
            },
            timeout=15,
        )
        response.raise_for_status()
        results = response.json().get("organic", [])
        # Normalise to the {title, href, body} shape the rest of the pipeline
        # expects from the DDG backend.
        return [
            {
                "title": item.get("title", ""),
                "href": item.get("link", ""),
                "body": item.get("snippet", ""),
            }
            for item in results
            if item.get("link")
        ][:max_results]
    except (requests.RequestException, ValueError) as exc:
        print(f"[search_web] Serper.dev search failed: {exc}")
        return []


def search_web(query: str, max_results: int = 5) -> list[dict]:
    """General web search with a reliable API option and no-key fallbacks."""
    serper_results = _search_serper(query, max_results)
    if serper_results:
        return serper_results

    # The library defaults to DDG's API endpoint, which frequently returns a
    # transient 202 rate limit. Its HTML and Lite endpoints are independent
    # fallbacks and need no API key.
    for backend in ("api", "html", "lite"):
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, backend=backend, max_results=max_results))
            if results:
                return results
        except DuckDuckGoSearchException as exc:
            print(f"[search_web] DuckDuckGo {backend} search failed: {exc}")

    # Bing's RSS endpoint is a lightweight public fallback when all DDG
    # endpoints are rate-limited. It returns direct result links, not HTML
    # search-result wrappers.
    try:
        response = requests.get(
            "https://www.bing.com/search",
            params={"format": "rss", "q": query},
            headers=HEADERS,
            timeout=15,
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        results = []
        company_term = query.split()[0].lower()
        for item in root.findall("./channel/item"):
            link = item.findtext("link")
            title = item.findtext("title") or ""
            body = item.findtext("description") or ""
            # Some shared-network Bing responses are unrelated to the query.
            # Keep only results that visibly mention the requested company.
            if link and company_term in f"{title} {body} {link}".lower():
                results.append({"title": title, "href": link, "body": body})
            if len(results) >= max_results:
                break
        if results:
            return results
    except (requests.RequestException, ET.ParseError) as exc:
        print(f"[search_web] Bing RSS search failed: {exc}")
    return search_free_research_sources(query, max_results)


def search_free_research_sources(query: str, max_results: int = 5) -> list[dict]:
    """No-key scholarly and clinical sources suitable for diagnostics research."""
    results = []
    try:
        response = requests.get(
            "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
            params={"query": query, "format": "json", "pageSize": max_results},
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        for item in response.json().get("resultList", {}).get("result", []):
            source, identifier = item.get("source"), item.get("id")
            if source and identifier:
                results.append({"title": item.get("title", ""), "href": f"https://europepmc.org/article/{source}/{identifier}", "body": item.get("abstractText", "")})
    except (requests.RequestException, ValueError) as exc:
        print(f"[search_free_research_sources] Europe PMC failed: {exc}")

    if len(results) >= max_results:
        return results[:max_results]
    results.extend(search_clinical_trials(query, limit=max_results - len(results)))
    return results[:max_results]


def search_clinical_trials(term: str, limit: int = 5) -> list[dict]:
    """ClinicalTrials.gov v2 - free, no key. Good for evidence on trial phase,
    cohort size, sponsor and endpoints behind an opportunity or a company."""
    try:
        response = requests.get(
            "https://clinicaltrials.gov/api/v2/studies",
            params={"query.term": term, "pageSize": limit, "sort": "LastUpdatePostDate:desc"},
            headers=HEADERS,
            timeout=20,
        )
        response.raise_for_status()
        studies = response.json().get("studies", [])
    except (requests.RequestException, ValueError) as exc:
        print(f"[search_clinical_trials] failed for {term!r}: {exc}")
        return []

    out = []
    for study in studies:
        protocol = study.get("protocolSection", {})
        nct_id = protocol.get("identificationModule", {}).get("nctId")
        if not nct_id:
            continue
        status = protocol.get("statusModule", {}).get("overallStatus", "")
        phases = ", ".join(protocol.get("designModule", {}).get("phases", []) or [])
        sponsor = protocol.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name", "")
        summary = protocol.get("descriptionModule", {}).get("briefSummary", "")
        blurb = " | ".join(p for p in (status, f"phase {phases}" if phases else "", f"sponsor: {sponsor}" if sponsor else "") if p)
        out.append({
            "title": protocol.get("identificationModule", {}).get("briefTitle", nct_id),
            "href": f"https://clinicaltrials.gov/study/{nct_id}",
            "body": f"{blurb}. {summary}".strip(),
        })
    return out


def search_openfda_devices(term: str, limit: int = 5) -> list[dict]:
    """openFDA 510(k) + PMA device databases - free, no key (IP rate-limited).

    Matches on the applicant/company name, newest decisions first. This is the
    regulatory-path evidence the pipeline otherwise can't get: clearance type,
    decision date, product code, predicate.
    """
    endpoints = (
        ("510k", "https://api.fda.gov/device/510k.json",
         "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMN/pmn.cfm?ID={}", "k_number", "device_name"),
        ("pma", "https://api.fda.gov/device/pma.json",
         "https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfPMA/pma.cfm?id={}", "pma_number", "trade_name"),
    )
    out: list[dict] = []
    seen: set[str] = set()  # PMA supplements repeat the same number
    for kind, api_url, page_tmpl, id_field, name_field in endpoints:
        try:
            response = requests.get(
                api_url,
                params={"search": f'applicant:"{term}"', "limit": limit, "sort": "decision_date:desc"},
                headers=HEADERS,
                timeout=20,
            )
            if response.status_code == 404:  # openFDA's "no matches"
                continue
            response.raise_for_status()
            records = response.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            print(f"[search_openfda_devices] {kind} failed for {term!r}: {exc}")
            continue

        for rec in records:
            record_id = rec.get(id_field)
            if not record_id or record_id in seen:
                continue
            seen.add(record_id)
            decided = rec.get("decision_date", "")
            desc = rec.get("decision_description") or rec.get("decision_code", "")
            product_code = rec.get("product_code", "")
            out.append({
                "title": f"{rec.get(name_field) or record_id} ({kind.upper()} {record_id})",
                "href": page_tmpl.format(record_id),
                "body": f"{rec.get('applicant', '')} - decided {decided} ({desc}); product code {product_code}".strip(),
            })
    return out


def search_sec_filings(company: str, form_type: str = "S-1") -> list[dict]:
    """SEC EDGAR full-text search - free, no API key, and not rate-limit-sensitive."""
    headers = {"User-Agent": settings.sec_user_agent or HEADERS["User-Agent"]}
    try:
        resp = requests.get(
            "https://efts.sec.gov/LATEST/search-index",
            params={"q": company, "forms": form_type},
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("hits", {}).get("hits", [])
    except requests.RequestException as exc:
        print(f"[search_sec_filings] full-text search unavailable: {exc}")

    # efts.sec.gov is occasionally unavailable on restricted networks. The
    # public company-ticker directory lives on www.sec.gov and lets us still
    # resolve a company name to a CIK, from which the pipeline builds a filing
    # index URL.
    try:
        resp = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers, timeout=15)
        resp.raise_for_status()
        needle = company.lower()
        matches = [
            {"_source": {"cik": str(row["cik_str"])}}
            for row in resp.json().values()
            if needle in row.get("title", "").lower()
        ]
        return matches[:2]
    except (requests.RequestException, ValueError, KeyError) as fallback_exc:
        print(f"[search_sec_filings] ticker-directory fallback failed: {fallback_exc}")
        return []


def fetch_page_text(url: str, return_error: bool = False) -> str | tuple[str, str | None]:
    """Fetch a URL and extract clean article text (strips nav/ads/boilerplate).

    Set ``return_error`` for callers that need to surface a per-URL failure to
    their users instead of silently treating it as an empty page.
    """
    time.sleep(1)  # be polite - see module docstring
    try:
        # trafilatura 1.12's fetch_url() does not accept custom headers.  Fetch
        # ourselves so the User-Agent is consistently sent, then hand the HTML
        # to trafilatura only for extraction.
        headers = HEADERS
        if urlsplit(url).netloc.lower().endswith("sec.gov") and settings.sec_user_agent:
            headers = {"User-Agent": settings.sec_user_agent}
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        text = trafilatura.extract(response.text)
        result = text or ""
        error = None if result else "No extractable text found in the response"
        return (result, error) if return_error else result
    except Exception as exc:  # noqa: BLE001 - hackathon: log and move on, don't crash the pipeline
        print(f"[fetch_page_text] failed for {url}: {exc}")
        return ("", str(exc)) if return_error else ""


def chunk_text(text: str) -> list[str]:
    """Split raw text into ~500-word overlapping chunks for embedding/storage."""
    if not text.strip():
        return []
    return _splitter.split_text(text)
