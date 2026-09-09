import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import CompetitorProfile, DiscoveredArticle, DiscoveredCompany, LeaderInsight, get_db
from app.schemas import (
    AnalyzeRequest,
    CompetitorProfileOut,
    DiscoverRequest,
    DiscoveredArticleOut,
    DiscoveredCompanyOut,
    EvidenceQuery,
    LeaderInsightOut,
    ProfileRequest,
    SuccessFactor,
)
from app.chroma_store import query_evidence
from app.agent.discovery import discover
from app.agent.pipeline import analyze_leader, research_competitor

router = APIRouter(prefix="/api", tags=["collection"])


def _decode_list(value: str) -> list:
    try:
        decoded = json.loads(value or "[]")
        return decoded if isinstance(decoded, list) else []
    except json.JSONDecodeError:
        return []


def _company_out(row: DiscoveredCompany) -> DiscoveredCompanyOut:
    return DiscoveredCompanyOut(
        id=row.id,
        name=row.name or "",
        domain=row.domain,
        homepage_url=row.homepage_url or "",
        country=row.country or "",
        is_european=bool(row.is_european),
        platform_type=row.platform_type or "",
        description=row.description or "",
        source_query=row.source_query or "",
        mention_count=row.mention_count or 0,
        profiled=bool(row.profiled),
    )


def _article_out(row: DiscoveredArticle) -> DiscoveredArticleOut:
    return DiscoveredArticleOut(
        id=row.id,
        title=row.title or "",
        url=row.url,
        domain=row.domain or "",
        snippet=row.snippet or "",
        source_query=row.source_query or "",
    )


def _profile_out(row: CompetitorProfile) -> CompetitorProfileOut:
    return CompetitorProfileOut(
        id=row.id,
        company_name=row.company_name,
        domain=row.domain or "",
        country=row.country or "",
        what_they_do=row.what_they_do or "",
        technology_approach=row.technology_approach or "",
        detection_modality=row.detection_modality or "",
        sensitivity_claim=row.sensitivity_claim or "",
        sample_requirement=row.sample_requirement or "",
        target_applications=_decode_list(row.target_applications),
        stage=row.stage or "",
        funding_summary=row.funding_summary or "",
        key_partnerships=_decode_list(row.key_partnerships),
        differentiators=_decode_list(row.differentiators),
        source_urls=_decode_list(row.source_urls),
    )


@router.post("/discover")
def discover_landscape(payload: DiscoverRequest, db: Session = Depends(get_db)):
    """Sweep the web for European single-molecule / ultra-sensitive protein-
    detection platform companies, de-duplicate, drop non-European hits, and
    persist. Each query costs ~1 Serper credit; pass max_queries to keep a run small."""
    try:
        return discover(
            db,
            extra_terms=payload.extra_terms,
            per_query=payload.per_query,
            max_queries=payload.max_queries,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/discovered-companies", response_model=list[DiscoveredCompanyOut])
def list_discovered_companies(
    country: str | None = None,
    platform_type: str | None = None,
    profiled: bool | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(DiscoveredCompany)
    if country:
        query = query.filter(DiscoveredCompany.country == country)
    if platform_type:
        query = query.filter(DiscoveredCompany.platform_type == platform_type)
    if profiled is not None:
        query = query.filter(DiscoveredCompany.profiled == profiled)
    rows = query.order_by(DiscoveredCompany.mention_count.desc()).all()
    return [_company_out(r) for r in rows]


@router.get("/discovered-articles", response_model=list[DiscoveredArticleOut])
def list_discovered_articles(domain: str | None = None, db: Session = Depends(get_db)):
    query = db.query(DiscoveredArticle)
    if domain:
        query = query.filter(DiscoveredArticle.domain == domain)
    rows = query.order_by(DiscoveredArticle.first_seen.desc()).all()
    return [_article_out(r) for r in rows]


@router.post("/profile")
def profile_competitor(payload: ProfileRequest, db: Session = Depends(get_db)):
    """Fetch a competitor's own pages and LLM-extract a structured profile."""
    try:
        return research_competitor(db, payload.company_name, payload.urls)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/competitors", response_model=list[CompetitorProfileOut])
def list_competitors(country: str | None = None, db: Session = Depends(get_db)):
    query = db.query(CompetitorProfile)
    if country:
        query = query.filter(CompetitorProfile.country == country)
    return [_profile_out(r) for r in query.order_by(CompetitorProfile.company_name).all()]


def _insight_out(row: LeaderInsight) -> LeaderInsightOut:
    raw_factors = _decode_list(row.success_factors)
    factors = [
        SuccessFactor(factor=f.get("factor", ""), evidence=f.get("evidence", ""))
        for f in raw_factors if isinstance(f, dict) and f.get("factor")
    ]
    return LeaderInsightOut(
        id=row.id,
        company_name=row.company_name,
        domain=row.domain or "",
        country=row.country or "",
        leader_name=row.leader_name or "",
        leader_role=row.leader_role or "",
        leader_background=row.leader_background or "",
        why_worth_studying=row.why_worth_studying or "",
        success_factors=factors,
        application_suggestions=_decode_list(row.application_suggestions),
        market_route_suggestions=_decode_list(row.market_route_suggestions),
        route_summary=row.route_summary or "",
        confidence=row.confidence or "",
        source_urls=_decode_list(row.source_urls),
    )


@router.post("/analyze")
def analyze_competitor_leader(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    """Answer, for one competitor: (1) the leader worth studying, (2) what made
    them succeed, (3) application + market-route suggestions for Proteins.1.
    Retrieves fresh leadership/strategy material, synthesises, and stores a
    leader_insights row."""
    try:
        return analyze_leader(db, payload.company_name, payload.urls)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/insights", response_model=list[LeaderInsightOut])
def list_insights(country: str | None = None, confidence: str | None = None, db: Session = Depends(get_db)):
    query = db.query(LeaderInsight)
    if country:
        query = query.filter(LeaderInsight.country == country)
    if confidence:
        query = query.filter(LeaderInsight.confidence == confidence)
    return [_insight_out(r) for r in query.order_by(LeaderInsight.company_name).all()]


@router.post("/evidence")
def get_evidence(payload: EvidenceQuery):
    """Semantic search over the raw collected page text (Chroma)."""
    return query_evidence(payload.query, payload.company, payload.n_results)
