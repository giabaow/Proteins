"""
Discovery sweep: find European companies building a Proteins.1-type platform -
physics/label-driven single-molecule or ultra-sensitive protein detection,
novel enzyme-free signal amplification, single-molecule protein sequencing or
sizing. NOT ctDNA/genomic liquid biopsy, NOT antibody/reagent suppliers, NOT CROs.

    from app.database import SessionLocal
    from app.agent.discovery import discover
    discover(SessionLocal())                  # full sweep
    discover(SessionLocal(), max_queries=6)   # small, cheap sweep

Every web call goes through tools.search_web (Serper primary, no-key fallbacks),
so a sweep costs ~1 Serper credit per query. Non-European hits are dropped at
store time; hits whose country can't be determined are kept with country="".
"""
import re
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.orm import Session

from app.agent.tools import search_web
from app.database import DiscoveredArticle, DiscoveredCompany

# --- what to search for ----------------------------------------------------

TOPIC_QUERIES = [
    "single molecule protein detection company Europe",
    "single-molecule protein sequencing company Europe",
    "ultra-sensitive protein biomarker platform company Europe",
    "digital ELISA single molecule immunoassay company Europe",
    "enzyme-free signal amplification biomarker platform company",
    "mass photometry single molecule protein company",
    "nanopore protein sensing company Europe",
    "proximity extension assay proteomics company Europe",
    "single molecule proteomics startup Europe 2025 2026",
    "attomolar protein detection platform company Europe",
    "single protein molecule counting technology company",
    "label-free single molecule protein analysis company Europe",
    "affinity based single molecule protein readout company",
    "next generation protein detection platform Nordic",
    "VTT spinout protein diagnostics platform",
    "Horizon Europe single molecule protein detection project company",
    "microfluidic single molecule protein assay company Europe",
    "photonic biosensor single molecule protein company Europe",
]

# A few European companies confidently in this space, to anchor the sweep.
SEED_COMPANIES = [
    ("Olink", "Sweden"),
    ("Refeyn", "United Kingdom"),
    ("Oxford Nanopore Technologies", "United Kingdom"),
    ("Fluidic Analytics", "United Kingdom"),
    ("Depixus", "France"),
    ("Biognosys", "Switzerland"),
    ("Genomill Health", "Finland"),
    ("NanoTemper Technologies", "Germany"),
    ("Pixelgen Technologies", "Sweden"),
    ("Sengenics", "United Kingdom"),
]

# Our own company - never store it as a competitor.
SELF_DOMAINS = {"proteins1.com", "versilib.eu"}

# --- geography -----------------------------------------------------------

# ccTLD -> country. Presence of one of these is a strong location signal.
_CCTLD_COUNTRY = {
    "fi": "Finland", "se": "Sweden", "no": "Norway", "dk": "Denmark", "is": "Iceland",
    "de": "Germany", "fr": "France", "nl": "Netherlands", "be": "Belgium", "ch": "Switzerland",
    "at": "Austria", "es": "Spain", "it": "Italy", "ie": "Ireland", "pt": "Portugal",
    "pl": "Poland", "cz": "Czechia", "hu": "Hungary", "ro": "Romania", "gr": "Greece",
    "ee": "Estonia", "lv": "Latvia", "lt": "Lithuania", "si": "Slovenia", "sk": "Slovakia",
    "hr": "Croatia", "bg": "Bulgaria", "lu": "Luxembourg", "uk": "United Kingdom",
}
_EUROPEAN_COUNTRIES = set(_CCTLD_COUNTRY.values())

# City / country strings that appear in search snippets and "about" text.
_LOCATION_HINTS = {
    "United Kingdom": ["united kingdom", " uk", "u.k.", "england", "scotland", "cambridge, uk",
                       "oxford, uk", "london", "manchester", "edinburgh"],
    "Germany": ["germany", "münchen", "munich", "berlin", "heidelberg", "hamburg", "cologne", "leipzig"],
    "France": ["france", "paris", "lyon", "grenoble", "strasbourg", "toulouse"],
    "Sweden": ["sweden", "stockholm", "uppsala", "lund", "gothenburg", "göteborg"],
    "Finland": ["finland", "helsinki", "espoo", "tampere", "oulu", "turku"],
    "Switzerland": ["switzerland", "zurich", "zürich", "basel", "lausanne", "geneva", "lonay"],
    "Netherlands": ["netherlands", "amsterdam", "rotterdam", "utrecht", "eindhoven", "leiden", "delft"],
    "Denmark": ["denmark", "copenhagen", "aarhus", "odense"],
    "Norway": ["norway", "oslo", "bergen", "trondheim"],
    "Belgium": ["belgium", "brussels", "ghent", "leuven", "antwerp"],
    "Austria": ["austria", "vienna", "graz", "innsbruck"],
    "Ireland": ["ireland", "dublin", "galway", "cork"],
    "Spain": ["spain", "barcelona", "madrid", "valencia"],
    "Italy": ["italy", "milan", "rome", "turin", "bologna"],
    "Estonia": ["estonia", "tallinn", "tartu"],
    "Iceland": ["iceland", "reykjavik"],
}
_NON_EUROPEAN_HINTS = [
    "billerica", "massachusetts", ", ma ", "california", ", ca ", "san diego", "san francisco",
    "boston", "new york", "seattle", "menlo park", "south san francisco", "cambridge, ma",
    "united states", "u.s.", " usa", "singapore", "shanghai", "beijing", "tokyo", "seoul",
    "australia", "canada", "toronto", "bengaluru", "india",
]


def guess_country(domain: str, text: str) -> tuple[str, bool]:
    """Return (country, is_european). country is "" when undetermined."""
    tld = domain.rsplit(".", 1)[-1]
    if tld in _CCTLD_COUNTRY:
        return _CCTLD_COUNTRY[tld], True

    blob = text.lower()
    if any(h in blob for h in _NON_EUROPEAN_HINTS):
        return "", False
    for country, hints in _LOCATION_HINTS.items():
        if any(h in blob for h in hints):
            return country, True
    return "", True  # undetermined - keep, let a human prune


# --- platform classification ------------------------------------------

_PLATFORM_HINTS = [
    ("mass photometry", ["mass photometry", "mass photometer"]),
    ("single-molecule protein sequencing", ["protein sequencing", "single-molecule sequencing", "single molecule sequencing"]),
    ("nanopore protein sensing", ["nanopore"]),
    ("single-molecule detection / digital assay", ["single molecule", "single-molecule", "digital elisa", "digital immunoassay", "simoa"]),
    ("proximity extension assay (PEA)", ["proximity extension", "pea assay"]),
    ("enzyme-free signal amplification", ["enzyme-free", "enzyme free", "isothermal amplification"]),
    ("microfluidic protein analysis", ["microfluidic", "diffusional sizing"]),
    ("affinity / photonic single-molecule readout", ["nanophotonic", "plasmonic", "photonic biosensor", "affinity mediated"]),
]


def guess_platform_type(text: str) -> str:
    blob = text.lower()
    for label, hints in _PLATFORM_HINTS:
        if any(h in blob for h in hints):
            return label
    return ""


# --- article vs company ---------------------------------------------

PUBLISHER_DOMAINS = {
    "nature.com", "science.org", "thelancet.com", "cell.com", "nejm.org", "bmj.com",
    "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "europepmc.org", "biorxiv.org", "medrxiv.org",
    "sciencedirect.com", "springer.com", "wiley.com", "mdpi.com", "frontiersin.org", "pnas.org",
    "acs.org", "oup.com", "tandfonline.com", "researchgate.net", "semanticscholar.org",
    "rsc.org", "elifesciences.org", "plos.org", "plos.org",
    "sec.gov", "fda.gov", "clinicaltrials.gov", "cordis.europa.eu", "ec.europa.eu",
    "fiercebiotech.com", "genomeweb.com", "labiotech.eu", "sifted.eu", "endpts.com",
    "businesswire.com", "prnewswire.com", "globenewswire.com", "biospace.com", "360dx.com",
    "insideprecisionmedicine.com", "drugtargetreview.com", "technologynetworks.com",
    "wikipedia.org", "linkedin.com", "substack.com", "medium.com", "crunchbase.com",
    "pitchbook.com", "dealroom.co", "youtube.com", "twitter.com", "x.com", "reuters.com",
    "bloomberg.com",
}
_NEWS_PATH_HINTS = (
    "/news", "/press", "/press-release", "/newsroom", "/media", "/article", "/articles",
    "/blog", "/insights", "/publication", "/resources/",
)
_DATE_IN_PATH = re.compile(r"/20[12]\d[/-]")
_TWO_LEVEL_TLDS = (".co.uk", ".org.uk", ".ac.uk", ".com.de")


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
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/") or "/", "", ""))


def classify(url: str) -> str:
    path = urlsplit(url).path.lower()
    if registrable_domain(url) in PUBLISHER_DOMAINS:
        return "article"
    if path.endswith((".pdf", ".doc", ".docx")):
        return "article"
    if any(h in path for h in _NEWS_PATH_HINTS) or _DATE_IN_PATH.search(path):
        return "article"
    return "company"


def company_name_from_domain(domain: str) -> str:
    stem = domain.rsplit(".", 1)[0].split(".")[-1]
    parts = re.split(r"[-_]", stem)
    return " ".join(p.upper() if len(p) <= 3 else p.capitalize() for p in parts if p)


# --- the sweep ---------------------------------------------------------

def _build_queries(extra_terms):
    queries = [(q, "") for q in TOPIC_QUERIES]
    for name, _country in SEED_COMPANIES:
        queries.append((f"{name} single molecule protein detection platform", "seed"))
    queries += [(t, "user") for t in (extra_terms or [])]
    return queries


def discover(db: Session, extra_terms=None, per_query: int = 8, max_queries=None) -> dict:
    queries = _build_queries(extra_terms)
    if max_queries is not None:
        queries = queries[:max_queries]

    companies: dict[str, dict] = {}
    articles: dict[str, dict] = {}
    dropped_non_eu = 0

    for query, _tag in queries:
        for hit in search_web(query, max_results=per_query):
            url = (hit.get("href") or "").strip()
            if not url.startswith("http"):
                continue
            title = (hit.get("title") or "").strip()
            snippet = (hit.get("body") or "").strip()
            text = f"{title} {snippet} {url}"

            if classify(url) == "company":
                domain = registrable_domain(url)
                if not domain or domain in SELF_DOMAINS:
                    continue
                country, is_eu = guess_country(domain, text)
                if not is_eu:
                    dropped_non_eu += 1
                    continue
                rec = companies.setdefault(domain, {
                    "name": company_name_from_domain(domain),
                    "domain": domain,
                    "homepage_url": f"https://{domain}/",
                    "country": country,
                    "platform_type": guess_platform_type(text),
                    "description": snippet,
                    "source_query": query,
                    "mentions": 0,
                })
                rec["mentions"] += 1
                if not rec["description"] and snippet:
                    rec["description"] = snippet
                if not rec["country"] and country:
                    rec["country"] = country
                if not rec["platform_type"]:
                    rec["platform_type"] = guess_platform_type(text)
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
        "dropped_non_european": dropped_non_eu,
        "companies": sorted(companies.values(), key=lambda r: -r["mentions"]),
        "articles": list(articles.values()),
    }


def _persist(db, companies, articles):
    new_companies = 0
    for domain, rec in companies.items():
        row = db.query(DiscoveredCompany).filter(DiscoveredCompany.domain == domain).first()
        if row is None:
            row = DiscoveredCompany(domain=domain, name=rec["name"], homepage_url=rec["homepage_url"])
            db.add(row)
            new_companies += 1
        if not row.description:
            row.description = rec["description"]
        if not row.country:
            row.country = rec["country"]
        if not row.platform_type:
            row.platform_type = rec["platform_type"]
        if not row.source_query:
            row.source_query = rec["source_query"]
        row.mention_count = (row.mention_count or 0) + rec["mentions"]
        row.is_european = True

    new_articles = 0
    for url, rec in articles.items():
        if db.query(DiscoveredArticle).filter(DiscoveredArticle.url == url).first() is None:
            db.add(DiscoveredArticle(
                url=url, title=rec["title"], domain=rec["domain"],
                snippet=rec["snippet"], source_query=rec["source_query"],
            ))
            new_articles += 1

    db.commit()
    return new_companies, new_articles
