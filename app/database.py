"""
SQLite via SQLAlchemy. One file, no server to run.

  - DiscoveredCompany : the census - every European single-molecule / ultra-
    sensitive protein-detection platform the discovery sweep turns up.
  - Company           : an analysed company - structured facts + playbook
    synthesis (LLM, facts-only) + a relevance score. The high scorers are
    flagged is_leader: the companies actually worth studying.
  - DiscoveredArticle : background literature / news on the technology space.

Raw page text lives in ChromaDB (see chroma_store.py), source-tagged.
"""
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

os.makedirs(os.path.dirname(settings.sqlite_path) or ".", exist_ok=True)

engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class DiscoveredCompany(Base):
    """One European company building a Proteins.1-type platform. Keyed by
    registrable domain so repeat sweeps de-duplicate."""
    __tablename__ = "discovered_companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="")
    domain = Column(String, unique=True, index=True, nullable=False)
    homepage_url = Column(String, default="")
    country = Column(String, default="", index=True)
    is_european = Column(Boolean, default=True)
    platform_type = Column(String, default="")
    description = Column(Text, default="")
    source_query = Column(String, default="")
    mention_count = Column(Integer, default=0)
    analysed = Column(Boolean, default=False)      # has a Company row
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Company(Base):
    """An analysed company: what it does (facts from its own pages), the playbook
    worth learning from, and a relevance score to Proteins.1. Every string field
    is a fact from the sources or "" - never inferred. List fields are JSON."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, default="")
    country = Column(String, default="", index=True)

    # --- what they do (facts, from their own pages) -------------------------
    what_they_do = Column(Text, default="")
    technology_approach = Column(Text, default="")
    detection_modality = Column(String, default="")       # protein / DNA / RNA / multi-omic
    sensitivity_claim = Column(Text, default="")          # verbatim
    sample_requirement = Column(Text, default="")         # verbatim
    target_applications = Column(Text, default="[]")      # JSON list
    stage = Column(String, default="")                    # research-use / clinical / commercial
    funding_summary = Column(Text, default="")
    key_partnerships = Column(Text, default="[]")         # JSON list

    # --- the playbook (synthesis, grounded in sources) --------------------
    leader_name = Column(String, default="")              # founder / CEO named in the sources
    leader_role = Column(String, default="")
    leader_background = Column(Text, default="")
    why_worth_studying = Column(Text, default="")
    success_factors = Column(Text, default="[]")          # JSON list of {factor, evidence}
    differentiators = Column(Text, default="[]")          # JSON list
    application_suggestions = Column(Text, default="[]")  # JSON list - for Proteins.1
    market_route_suggestions = Column(Text, default="[]") # JSON list - for Proteins.1
    route_summary = Column(Text, default="")
    confidence = Column(String, default="")              # high / medium / low - documentation quality

    # --- relevance score (see app/agent/pipeline.py rank_companies) -------
    score_platform = Column(Integer, default=0)           # 0-5  mechanism closeness
    score_stage = Column(Integer, default=0)              # 0-5  proximity to RUO->commercial
    score_route = Column(Integer, default=0)              # 0-5  transferable go-to-market pattern
    score_evidence = Column(Integer, default=0)           # 0-3  documentation quality
    score_ecosystem = Column(Integer, default=0)          # 0-2  Nordic / close-EU proximity
    score_notes = Column(Text, default="{}")             # JSON {axis: one-line reason}
    relevance_score = Column(Float, default=0.0)
    rank = Column(Integer, default=0)
    is_leader = Column(Boolean, default=False, index=True)

    source_urls = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DiscoveredArticle(Base):
    """A background article / paper / news item on the field. Keyed by URL."""
    __tablename__ = "discovered_articles"

    id = Column(Integer, primary_key=True)
    title = Column(String, default="")
    url = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, default="", index=True)
    snippet = Column(Text, default="")
    source_query = Column(String, default="")
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
