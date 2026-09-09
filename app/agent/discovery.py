"""
Landscape discovery: sweep the web for every company and article relevant to
Proteins.1's space (single-molecule / ultra-sensitive protein diagnostics), then
de-duplicate and persist the census to SQLite.

This is the "AI does the collecting and structuring" step from the brief: run a
curated set of searches, classify each hit as a *company site* or an *article*,
and keep a growing, traceable list rather than a hand-curated spreadsheet.

    from app.database import SessionLocal
    from app.agent.discovery import discover
    discover(SessionLocal(), max_queries=5)      # small, cheap sweep
    discover(SessionLocal())                     # full landscape sweep

Every web call goes through tools.search_web (Serper.dev primary, no-key
fallbacks), so a sweep costs ~1 Serper credit per query.
"""
import re
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.orm import Session

from app.agent.tools import search_web
from app.database import DiscoveredArticle, DiscoveredCompany

# --- what to search for -------------------------------------------------------

# Themes that define the space, straight from the challenge brief.
TOPIC_QUERIES = [
    "single molecule protein detection company",
    "ultra-sensitive proteomics platform company",
    "digital ELISA Simoa competitor platform",
    "proximity extension assay proteomics company",
    "single-molecule proteomics startup 2025 2026",
    "enzyme-free biomarker signal amplification diagnostics",
    "attomolar protein biomarker detection assay",
    "plasma p-tau217 blood test company",
    "neurofilament light chain NfL assay commercial",
    "GFAP amyloid plasma assay diagnostics company",
    "multi-cancer early detection blood test company",
    "liquid biopsy protein biomarker company",
    "minimal residual disease ctDNA protein assay company",
    "LINE-1 ORF1p circulating cancer biomarker assay",
    "single-molecule counting immunoassay instrument vendor",
    "high-plex proteomics panel company",
    "RUO to IVD diagnostic commercialization strategy",
    "Finnish Nordic proteomics diagnostics company",
    "companion diagnostic protein biomarker pharma partnership",
    "proteomics platform Series C IPO 2025",
]

# Named comparables from brief section 8.4, grouped as the brief groups them.
SEED_COMPANIES = {
    "ultra-sensitive & high-plex proteomics": [
        "Quanterix", "Olink", "SomaLogic", "Alamar Biosciences", "Nautilus Biotechnology",
        "Nomic Bio", "Seer", "Standard BioTools", "Meso Scale Discovery", "Bio-Rad", "Luminex",
    ],
    "liquid biopsy & screening": [
        "Guardant Health", "Natera", "Exact Sciences", "GRAIL", "Freenome", "DELFI Diagnostics",
        "Harbinger Health", "Nucleix", "Foundation Medicine", "Personalis", "Adela",
    ],
    "neuro diagnostics": [
        "C2N Diagnostics", "Fujirebio", "ALZpath", "Roche Diagnostics", "Labcorp",
    ],
    "nordic / finnish ecosystem": [
        "Nightingale Health", "Genomill", "Uniogen", "Medix Biochemica", "HyTest", "Hidex",
        "Aidian", "Labsystems Diagnostics", "Biohit", "Elypta", "Immunovia", "Reccan Diagnostics",
        "SAGA Diagnostics", "Hedera Dx",
    ],
}

# --- classification ---------------------------------------------------------

# Hosts that are always articles/filings/profiles, never "the company we found".
PUBLISHER_DOMAINS = {
    "nature.com", "science.org", "thelancet.com", "cell.com", "nejm.org", "bmj.com",
    "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "europepmc.org", "biorxiv.org",
    "medrxiv.org", "sciencedirect.com", "springer.com", "wiley.com", "mdpi.com",
    "frontiersin.org", "aacrjournals.org", "pnas.org", "researchgate.net", "semanticscholar.org",
    "acs.org", "oup.com", "tandfonline.com", "karger.com", "rupress.org", "physiology.org",
    "spandidos-publications.com", "jci.org", "asm.org", "elifesciences.org", "plos.org",
    "sec.gov", "fda.gov", "clinicaltrials.gov", "cms.gov", "cordis.europa.eu", "nih.gov",
    "fiercebiotech.com", "genomeweb.com", "statnews.com", "endpts.com", "medtechdive.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com", "biospace.com", "labiotech.eu",
    "precisionmedicineonline.com", "360dx.com", "drugdiscoverynews.com", "biopharmadive.com",
    "wikipedia.org", "linkedin.com", "substack.com", "medium.com", "forbes.com", "reuters.com",
    "bloomberg.com", "wsj.com", "ft.com", "techcrunch.com", "crunchbase.com", "pitchbook.com",
    "youtube.com", "twitter.com", "x.com", "prevention.com", "news-medical.net",
}

_NEWS_PATH_HINTS = (
    "/news", "/press", "/press-release", "/press-releases", "/newsroom", "/media",
    "/article", "/articles", "/blog", "/insights", "/resources/", "/publication",
    "/investor", "/investors",
)
_DATE_IN_PATH = re.compile(r"/20[12]\d[/-]")
_TWO_LEVEL_TLDS = (".co.uk", ".com.au", ".co.jp", ".co.nz", ".com.br", ".co.in")


def registrable_domain(url: str) -> str:
    host = (urlsplit(url).netloc or "").lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    labels = host.split(".")
    if len(labels) > 2 and host.endswith(_TWO_LEVEL_TLDS):
        return ".".join(labels[-3:])
    return ".".join(labels[-2:]) if len(labels) >= 2 else host


def normalize_url(url: str) -> str:
    parts = urlsplit(url)
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme, parts.netloc.lower(), path, "", ""))


def classify(url: str) -> str:
    """'article' for news / filings / journals / profiles, else 'company'."""
    path = urlsplit(url).path.lower()
    if registrable_domain(url) in PUBLISHER_DOMAINS:
        return "article"
    if path.endswith((".pdf", ".doc", ".docx")):
        return "article"
    if any(hint in path for hint in _NEWS_PATH_HINTS):
        return "article"
    if _DATE_IN_PATH.search(path):
        return "article"
    return "company"


def company_name_from_domain(domain: str) -> str:
    stem = domain.rsplit(".", 1)[0].split(".")[-1]
    parts = re.split(r"[-_]", stem)
    return " ".join(p.upper() if len(p) <= 3 else p.capitalize() for p in parts if p)


# --- the sweep -------------------------------------------------------------

def _build_queries(extra_terms: list[str] | None) -> list[tuple[str, str]]:
    """Return (query, category) pairs. Category tags where a hit came from."""
    queries: list[tuple[str, str]] = [(q, "") for q in TOPIC_QUERIES]
    for bucket, names in SEED_COMPANIES.items():
        for name in names:
            queries.append((f"{name} proteomics diagnostics company", bucket))
    queries += [(t, "user") for t in (extra_terms or [])]
    return queries


def discover(
    db: Session,
    extra_terms: list[str] | None = None,
    per_query: int = 8,
    max_queries: int | None = None,
) -> dict:
    """Run the landscape sweep, upsert results into SQLite, return a summary."""
    queries = _build_queries(extra_terms)
    if max_queries is not None:
        queries = queries[:max_queries]

    companies: dict[str, dict] = {}
    articles: dict[str, dict] = {}

    for query, category in queries:
        for hit in search_web(query, max_results=per_query):
            url = (hit.get("href") or "").strip()
            if not url.startswith("http"):
                continue
            title = (hit.get("title") or "").strip()
            snippet = (hit.get("body") or "").strip()

            if classify(url) == "company":
                domain = registrable_domain(url)
                if not domain:
                    continue
                rec = companies.setdefault(domain, {
                    "name": company_name_from_domain(domain),
                    "domain": domain,
                    "homepage_url": f"https://{domain}/",
                    "description": snippet,
                    "category": category,
                    "source_query": query,
                    "mentions": 0,
                })
                rec["mentions"] += 1
                if not rec["description"] and snippet:
                    rec["description"] = snippet
                if not rec["category"] and category:
                    rec["category"] = category
            else:
                key = normalize_url(url)
                articles.setdefault(key, {
                    "title": title or key,
                    "url": key,
                    "domain": registrable_domain(url),
                    "snippet": snippet,
                    "source_query": query,
                })

    new_companies, new_articles = _persist(db, companies, articles)

    return {
        "queries_run": len(queries),
        "companies_found": len(companies),
        "articles_found": len(articles),
        "new_companies": new_companies,
        "new_articles": new_articles,
        "companies": sorted(companies.values(), key=lambda r: -r["mentions"]),
        "articles": list(articles.values()),
    }


def _persist(db: Session, companies: dict[str, dict], articles: dict[str, dict]) -> tuple[int, int]:
    new_companies = 0
    for domain, rec in companies.items():
        row = db.query(DiscoveredCompany).filter(DiscoveredCompany.domain == domain).first()
        if row is None:
            row = DiscoveredCompany(domain=domain, name=rec["name"], homepage_url=rec["homepage_url"])
            db.add(row)
            new_companies += 1
        if not row.description:
            row.description = rec["description"]
        if not row.category:
            row.category = rec["category"]
        if not row.source_query:
            row.source_query = rec["source_query"]
        row.mention_count = (row.mention_count or 0) + rec["mentions"]

    new_articles = 0
    for url, rec in articles.items():
        exists = db.query(DiscoveredArticle).filter(DiscoveredArticle.url == url).first()
        if exists is None:
            db.add(DiscoveredArticle(
                url=url, title=rec["title"], domain=rec["domain"],
                snippet=rec["snippet"], source_query=rec["source_query"],
            ))
            new_articles += 1

    db.commit()
    return new_companies, new_articles
