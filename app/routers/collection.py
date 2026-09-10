import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import Company, DiscoveredArticle, DiscoveredCompany, Recommendation, get_db
from app.schemas import (
    AnalyzeRequest,
    CompanyOut,
    DiscoverRequest,
    DiscoveredArticleOut,
    DiscoveredCompanyOut,
    EvidenceQuery,
    RankRequest,
    SuccessFactor,
)
from app.chroma_store import query_evidence
from app.agent.discovery import discover
from app.agent.pipeline import analyze_company, rank_companies, synthesize_recommendation

router = APIRouter(prefix="/api", tags=["collection"])


def _list(value: str) -> list:
    try:
        v = json.loads(value or "[]")
        return v if isinstance(v, list) else []
    except json.JSONDecodeError:
        return []


def _obj(value: str) -> dict:
    try:
        v = json.loads(value or "{}")
        return v if isinstance(v, dict) else {}
    except json.JSONDecodeError:
        return {}


def _discovered_out(row: DiscoveredCompany) -> DiscoveredCompanyOut:
    return DiscoveredCompanyOut(
        id=row.id, name=row.name or "", domain=row.domain, homepage_url=row.homepage_url or "",
        country=row.country or "", is_european=bool(row.is_european), platform_type=row.platform_type or "",
        description=row.description or "", source_query=row.source_query or "",
        mention_count=row.mention_count or 0, analysed=bool(row.analysed),
    )


def _article_out(row: DiscoveredArticle) -> DiscoveredArticleOut:
    return DiscoveredArticleOut(
        id=row.id, title=row.title or "", url=row.url, domain=row.domain or "",
        snippet=row.snippet or "", source_query=row.source_query or "",
    )


def _company_out(row: Company) -> CompanyOut:
    return CompanyOut(
        id=row.id, name=row.name, domain=row.domain or "", country=row.country or "",
        what_they_do=row.what_they_do or "", technology_approach=row.technology_approach or "",
        detection_modality=row.detection_modality or "", sensitivity_claim=row.sensitivity_claim or "",
        sample_requirement=row.sample_requirement or "", target_applications=_list(row.target_applications),
        stage=row.stage or "", funding_summary=row.funding_summary or "",
        key_partnerships=_list(row.key_partnerships), differentiators=_list(row.differentiators),
        leader_name=row.leader_name or "", leader_role=row.leader_role or "",
        leader_background=row.leader_background or "", why_worth_studying=row.why_worth_studying or "",
        success_factors=[SuccessFactor(factor=f.get("factor", ""), evidence=f.get("evidence", ""))
                         for f in _list(row.success_factors) if isinstance(f, dict) and f.get("factor")],
        application_suggestions=_list(row.application_suggestions),
        market_route_suggestions=_list(row.market_route_suggestions),
        route_summary=row.route_summary or "", confidence=row.confidence or "",
        score_platform=row.score_platform or 0, score_stage=row.score_stage or 0,
        score_route=row.score_route or 0, score_evidence=row.score_evidence or 0,
        score_ecosystem=row.score_ecosystem or 0, score_notes=_obj(row.score_notes),
        relevance_score=row.relevance_score or 0.0, rank=row.rank or 0, is_leader=bool(row.is_leader),
        source_urls=_list(row.source_urls),
    )


# --- discovery -----------------------------------------------------------

@router.post("/discover")
def discover_landscape(payload: DiscoverRequest, db: Session = Depends(get_db)):
    """Sweep the web for European single-molecule / ultra-sensitive protein-
    detection platform companies; de-duplicate, drop non-European hits, persist."""
    try:
        return discover(db, extra_terms=payload.extra_terms,
                        per_query=payload.per_query, max_queries=payload.max_queries)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/discovered-companies", response_model=list[DiscoveredCompanyOut])
def list_discovered(country: str | None = None, platform_type: str | None = None,
                    analysed: bool | None = None, db: Session = Depends(get_db)):
    q = db.query(DiscoveredCompany)
    if country:
        q = q.filter(DiscoveredCompany.country == country)
    if platform_type:
        q = q.filter(DiscoveredCompany.platform_type == platform_type)
    if analysed is not None:
        q = q.filter(DiscoveredCompany.analysed == analysed)
    return [_discovered_out(r) for r in q.order_by(DiscoveredCompany.mention_count.desc()).all()]


@router.get("/discovered-articles", response_model=list[DiscoveredArticleOut])
def list_articles(domain: str | None = None, db: Session = Depends(get_db)):
    q = db.query(DiscoveredArticle)
    if domain:
        q = q.filter(DiscoveredArticle.domain == domain)
    return [_article_out(r) for r in q.order_by(DiscoveredArticle.first_seen.desc()).all()]


# --- analysis + ranking ----------------------------------------------

@router.post("/analyze")
def analyze(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """Fetch a company's pages, extract facts, and synthesise its playbook into a
    `companies` row (leader, success factors, suggestions for Proteins.1)."""
    try:
        return analyze_company(db, payload.company_name, payload.urls)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rank")
def rank(payload: RankRequest, db: Session = Depends(get_db)):
    """Score every analysed company on relevance to Proteins.1 and flag the top
    `top_n` is_leader. Fixed formula, no LLM, re-runnable."""
    try:
        return rank_companies(db, top_n=payload.top_n)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/companies", response_model=list[CompanyOut])
def list_companies(leaders_only: bool = False, country: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Company)
    if leaders_only:
        q = q.filter(Company.is_leader.is_(True))
    if country:
        q = q.filter(Company.country == country)
    return [_company_out(r) for r in q.order_by(Company.rank).all()]


@router.post("/synthesize")
def synthesize(top_k: int = 3, db: Session = Depends(get_db)):
    """Build the consolidated application + market-route recommendation for
    Proteins.1 from the top-k companies' playbooks (frontend Overview, Q3)."""
    try:
        return synthesize_recommendation(db, top_k=top_k)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/recommendation")
def get_recommendation(db: Session = Depends(get_db)):
    row = db.query(Recommendation).filter(Recommendation.id == 1).first()
    if row is None:
        raise HTTPException(status_code=404, detail="no recommendation yet - run POST /api/synthesize")
    return {
        "from_companies": _list(row.from_companies),
        "headline": row.headline or "",
        "applications": _list(row.applications),
        "market_route": _list(row.market_route),
        "sequence": row.sequence or "",
    }


@router.post("/evidence")
def get_evidence(payload: EvidenceQuery):
    """Semantic search over the raw collected page text (Chroma)."""
    return query_evidence(payload.query, payload.company, payload.n_results)
