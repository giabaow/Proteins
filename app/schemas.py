from typing import Optional
from pydantic import BaseModel, Field


class DiscoverRequest(BaseModel):
    extra_terms: list[str] = []          # extra queries on top of the built-in EU platform set
    per_query: int = Field(default=8, ge=1, le=20)
    max_queries: Optional[int] = Field(default=None, ge=1)  # cap the sweep (each query ~1 Serper credit)


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
    profiled: bool


class DiscoveredArticleOut(BaseModel):
    id: int
    title: str
    url: str
    domain: str
    snippet: str
    source_query: str


class ProfileRequest(BaseModel):
    company_name: str
    urls: list[str] = []                 # optional - if empty, the agent searches


class CompetitorProfileOut(BaseModel):
    id: int
    company_name: str
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
    source_urls: list[str]


class EvidenceQuery(BaseModel):
    query: str
    company: Optional[str] = None
    n_results: int = 3
