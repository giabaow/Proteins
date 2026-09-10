from typing import Optional
from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    extra_terms: list[str] = []
    per_query: int = Field(default=8, ge=1, le=20)
    max_queries: Optional[int] = Field(default=None, ge=1)


class DiscoveredCompanyOut(BaseModel):
    id: int
    name: str
    domain: str
    homepage_url: str
    country: str
    is_european: bool
    platform_type: str
    description: str
    source_query: str
    mention_count: int
    analysed: bool


class DiscoveredArticleOut(BaseModel):
    id: int
    title: str
    url: str
    domain: str
    snippet: str
    source_query: str


class AnalyzeRequest(BaseModel):
    company_name: str
    urls: list[str] = []


class RankRequest(BaseModel):
    top_n: int = Field(default=5, ge=1, le=50)


class SuccessFactor(BaseModel):
    factor: str
    evidence: str = ""


class CompanyOut(BaseModel):
    id: int
    name: str
    domain: str
    country: str

    what_they_do: str
    technology_approach: str
    detection_modality: str
    sensitivity_claim: str
    sample_requirement: str
    target_applications: list[str]
    stage: str
    funding_summary: str
    key_partnerships: list[str]
    differentiators: list[str]

    leader_name: str
    leader_role: str
    leader_background: str
    why_worth_studying: str
    success_factors: list[SuccessFactor]
    application_suggestions: list[str]
    market_route_suggestions: list[str]
    route_summary: str
    confidence: str

    score_platform: int
    score_stage: int
    score_route: int
    score_evidence: int
    score_ecosystem: int
    score_notes: dict
    relevance_score: float
    rank: int
    is_leader: bool

    technology_score: float
    technology_score_note: str
    funding_usd_m: float
    funding_basis: str

    source_urls: list[str]


class EvidenceQuery(BaseModel):
    query: str
    company: Optional[str] = None
    n_results: int = 3
