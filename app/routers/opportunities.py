from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import json

from app.database import (
    CaseStudy,
    DiscoveredArticle,
    DiscoveredCompany,
    EvidenceRecord,
    get_db,
    Opportunity,
)
from app.schemas import (
    CaseStudyIn,
    CaseStudyOut,
    DiscoverRequest,
    DiscoveredArticleOut,
    DiscoveredCompanyOut,
    EvidenceRecordIn,
    EvidenceRecordOut,
    EvidenceQuery,
    OpportunityIn,
    OpportunityOut,
    ResearchRequest,
    Weights,
)
from app.scoring import opportunity_index
from app.chroma_store import query_evidence
from app.agent.discovery import discover
from app.agent.pipeline import research_case_study, research_company

router = APIRouter(prefix="/api", tags=["opportunities"])

EVIDENCE_DIMENSIONS = {
    "unmet_need",
    "clinical_decision",
    "payer_path",
    "evidence_cost",
    "sample_access",
    "incumbent_intensity",
    "time_to_revenue",
    "defensibility",
}


def _to_out(row: Opportunity, weights: Weights) -> OpportunityOut:
    oi = opportunity_index(
        row.unmet_need, row.sensitivity_gain, row.market_size, row.regulatory_burden,
        weights.w_unmet_need, weights.w_sensitivity_gain, weights.w_market, weights.w_regulatory_burden,
    )
    return OpportunityOut(
        id=row.id,
        disease_area=row.disease_area,
        marker_class=row.marker_class,
        customer_segment=row.customer_segment,
        revenue_model=row.revenue_model,
        unmet_need=row.unmet_need,
        sensitivity_gain=row.sensitivity_gain,
        market_size=row.market_size,
        regulatory_burden=row.regulatory_burden,
        rationale=row.rationale,
        source_url=row.source_url,
        verified=row.verified,
        opportunity_index=round(oi, 3),
    )


def _decode_list(value: str) -> list:
    try:
        decoded = json.loads(value or "[]")
        return decoded if isinstance(decoded, list) else []
    except json.JSONDecodeError:
        return []


def _case_study_out(row: CaseStudy) -> CaseStudyOut:
    return CaseStudyOut(
        id=row.id,
        company_name=row.company_name,
        leader_name=row.leader_name,
        leader_background=row.leader_background,
        success_factors=_decode_list(row.success_factors),
        application=row.application,
        market_route=row.market_route,
        source_urls=_decode_list(row.source_urls),
        verified=row.verified,
    )


def _evidence_out(row: EvidenceRecord) -> EvidenceRecordOut:
    return EvidenceRecordOut(
        id=row.id,
        opportunity_id=row.opportunity_id,
        company_name=row.company_name,
        dimension=row.dimension,
        claim=row.claim,
        source_url=row.source_url,
        excerpt=row.excerpt,
        evidence_status=row.evidence_status,
    )


@router.post("/opportunities", response_model=OpportunityOut)
def create_opportunity(payload: OpportunityIn, db: Session = Depends(get_db)):
    row = Opportunity(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row, Weights())


@router.get("/opportunity-map", response_model=list[OpportunityOut])
def get_opportunity_map(
    w_unmet_need: float = 0.3,
    w_sensitivity_gain: float = 0.2,
    w_market: float = 0.3,
    w_regulatory_burden: float = 0.2,
    db: Session = Depends(get_db),
):
    """
    This is what the frontend calls to draw the map. Weights come from the
    UI sliders (brief: weights must be visible/adjustable, not hidden).
    """
    weights = Weights(
        w_unmet_need=w_unmet_need,
        w_sensitivity_gain=w_sensitivity_gain,
        w_market=w_market,
        w_regulatory_burden=w_regulatory_burden,
    )
    rows = db.query(Opportunity).all()
    return [_to_out(r, weights) for r in rows]


@router.post("/research")
def trigger_research(payload: ResearchRequest, db: Session = Depends(get_db)):
    """Kick off the agent pipeline for one company - fetch, chunk, extract, store."""
    try:
        return research_company(db, payload.company_name, payload.urls, payload.query_hint)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/research-case-study")
def trigger_case_study_research(payload: ResearchRequest, db: Session = Depends(get_db)):
    """Fetch, extract, and persist a structured comparable-company case study."""
    try:
        return research_case_study(db, payload.company_name, payload.urls, payload.query_hint)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/case-studies", response_model=list[CaseStudyOut])
def get_case_studies(db: Session = Depends(get_db)):
    return [_case_study_out(row) for row in db.query(CaseStudy).all()]


@router.post("/case-studies", response_model=CaseStudyOut)
def create_case_study(payload: CaseStudyIn, db: Session = Depends(get_db)):
    row = CaseStudy(
        company_name=payload.company_name,
        leader_name=payload.leader_name,
        leader_background=payload.leader_background,
        success_factors=json.dumps([factor.model_dump() for factor in payload.success_factors]),
        application=payload.application,
        market_route=payload.market_route,
        source_urls=json.dumps(payload.source_urls),
        verified=payload.verified,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _case_study_out(row)


@router.post("/evidence-records", response_model=EvidenceRecordOut)
def create_evidence_record(payload: EvidenceRecordIn, db: Session = Depends(get_db)):
    """Add one traceable claim for an opportunity-map scoring dimension."""
    if payload.dimension not in EVIDENCE_DIMENSIONS:
        raise HTTPException(status_code=422, detail=f"dimension must be one of: {', '.join(sorted(EVIDENCE_DIMENSIONS))}")
    row = EvidenceRecord(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _evidence_out(row)


@router.get("/evidence-records", response_model=list[EvidenceRecordOut])
def list_evidence_records(opportunity_id: int | None = None, company_name: str | None = None, db: Session = Depends(get_db)):
    query = db.query(EvidenceRecord)
    if opportunity_id is not None:
        query = query.filter(EvidenceRecord.opportunity_id == opportunity_id)
    if company_name:
        query = query.filter(EvidenceRecord.company_name == company_name)
    return [_evidence_out(row) for row in query.all()]


@router.post("/evidence")
def get_evidence(payload: EvidenceQuery):
    """Frontend calls this when the user clicks a point on the map, to show sourced text."""
    return query_evidence(payload.query, payload.company, payload.n_results)


def _discovered_company_out(row: DiscoveredCompany) -> DiscoveredCompanyOut:
    return DiscoveredCompanyOut(
        id=row.id,
        name=row.name or "",
        domain=row.domain,
        homepage_url=row.homepage_url or "",
        description=row.description or "",
        category=row.category or "",
        source_query=row.source_query or "",
        mention_count=row.mention_count or 0,
    )


def _discovered_article_out(row: DiscoveredArticle) -> DiscoveredArticleOut:
    return DiscoveredArticleOut(
        id=row.id,
        title=row.title or "",
        url=row.url,
        domain=row.domain or "",
        snippet=row.snippet or "",
        source_query=row.source_query or "",
    )


@router.post("/discover")
def discover_landscape(payload: DiscoverRequest, db: Session = Depends(get_db)):
    """Sweep the web for companies and articles across the Proteins.1 landscape,
    de-duplicate, and persist them. Each query costs ~1 Serper credit - pass
    max_queries to keep a run small."""
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
def list_discovered_companies(category: str | None = None, db: Session = Depends(get_db)):
    query = db.query(DiscoveredCompany)
    if category:
        query = query.filter(DiscoveredCompany.category == category)
    rows = query.order_by(DiscoveredCompany.mention_count.desc()).all()
    return [_discovered_company_out(row) for row in rows]


@router.get("/discovered-articles", response_model=list[DiscoveredArticleOut])
def list_discovered_articles(domain: str | None = None, db: Session = Depends(get_db)):
    query = db.query(DiscoveredArticle)
    if domain:
        query = query.filter(DiscoveredArticle.domain == domain)
    rows = query.order_by(DiscoveredArticle.first_seen.desc()).all()
    return [_discovered_article_out(row) for row in rows]
