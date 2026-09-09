from typing import Optional
from pydantic import BaseModel, Field


class OpportunityIn(BaseModel):
    disease_area: str
    marker_class: str = ""
    customer_segment: str = ""
    revenue_model: str = ""
    unmet_need: float = Field(ge=0, le=10)
    sensitivity_gain: float = Field(ge=0, le=10)
    market_size: float = Field(ge=0, le=10)
    regulatory_burden: float = Field(ge=0, le=10)
    rationale: str = ""
    source_url: str = ""
    verified: str = "unconfirmed"  # measured | vendor_claim | estimate | unconfirmed


class OpportunityOut(OpportunityIn):
    id: int
    opportunity_index: float


class Weights(BaseModel):
    """Must sum to ~1.0. Exposed to the UI - brief explicitly wants weights visible, not hidden."""
    w_unmet_need: float = 0.3
    w_sensitivity_gain: float = 0.2
    w_market: float = 0.3
    w_regulatory_burden: float = 0.2


class ResearchRequest(BaseModel):
    company_name: str
    urls: list[str] = []  # optional - if empty, agent will search for some
    query_hint: Optional[str] = None  # e.g. "go-to-market history, first customers"


class EvidenceQuery(BaseModel):
    query: str
    company: Optional[str] = None
    n_results: int = 3


class EvidenceRecordIn(BaseModel):
    opportunity_id: int | None = None
    company_name: str = ""
    dimension: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    excerpt: str = ""
    evidence_status: str = "unconfirmed"  # measured | vendor_claim | estimate | unconfirmed


class EvidenceRecordOut(EvidenceRecordIn):
    id: int


class SuccessFactor(BaseModel):
    factor: str
    source_url: str


class CaseStudyIn(BaseModel):
    company_name: str
    leader_name: str = ""
    leader_background: str = ""
    success_factors: list[SuccessFactor] = []
    application: str = ""
    market_route: str = ""
    source_urls: list[str] = []
    verified: str = "unconfirmed"  # measured | vendor_claim | estimate | unconfirmed


class CaseStudyOut(CaseStudyIn):
    id: int


class DiscoverRequest(BaseModel):
    extra_terms: list[str] = []          # extra queries on top of the built-in landscape set
    per_query: int = Field(default=8, ge=1, le=20)
    max_queries: Optional[int] = Field(default=None, ge=1)  # cap the sweep (each query ~1 Serper credit)


class DiscoveredCompanyOut(BaseModel):
    id: int
    name: str
    domain: str
    homepage_url: str
    description: str
    category: str
    source_query: str
    mention_count: int


class DiscoveredArticleOut(BaseModel):
    id: int
    title: str
    url: str
    domain: str
    snippet: str
    source_query: str
