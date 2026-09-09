"""
SQLite via SQLAlchemy. One file, no server to run.

Two tiers of collected data:
  - DiscoveredCompany : the census - every European single-molecule / ultra-
    sensitive protein-detection platform the discovery sweep turns up.
  - CompetitorProfile : a structured deep profile for the ones worth detailing,
    LLM-extracted from their own pages (facts only, never guessed).
  - DiscoveredArticle : background literature / news on the technology space.

Raw page text lives in ChromaDB (see chroma_store.py), source-tagged.
"""
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

os.makedirs(os.path.dirname(settings.sqlite_path) or ".", exist_ok=True)

engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class DiscoveredCompany(Base):
    """One European company building a Proteins.1-type platform (single-molecule
    / ultra-sensitive protein detection, novel signal amplification, single-
    molecule protein sequencing/sizing). Keyed by registrable domain so repeat
    sweeps de-duplicate."""
    __tablename__ = "discovered_companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, default="")
    domain = Column(String, unique=True, index=True, nullable=False)
    homepage_url = Column(String, default="")
    country = Column(String, default="", index=True)     # best-guess, "" if undetermined
    is_european = Column(Boolean, default=True)
    platform_type = Column(String, default="")           # e.g. "mass photometry", "PEA", "nanopore"
    description = Column(Text, default="")               # best search snippet seen
    source_query = Column(String, default="")
    mention_count = Column(Integer, default=0)
    profiled = Column(Boolean, default=False)            # has a CompetitorProfile row
    first_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CompetitorProfile(Base):
    """Structured, source-traceable profile of one competitor. Every string field
    is either a fact stated on the company's own pages or null - never inferred.
    List fields are JSON-encoded strings."""
    __tablename__ = "competitor_profiles"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, index=True, nullable=False)
    domain = Column(String, default="")
    country = Column(String, default="")

    what_they_do = Column(Text, default="")             # 1-2 sentence plain summary
    technology_approach = Column(Text, default="")      # the mechanism, in their words
    detection_modality = Column(String, default="")     # protein / DNA / RNA / multi-omic
    sensitivity_claim = Column(Text, default="")        # verbatim if stated
    sample_requirement = Column(Text, default="")       # volume / type if stated
    target_applications = Column(Text, default="[]")    # JSON list: oncology, neurology, ...
    stage = Column(String, default="")                  # research-use / clinical / commercial
    funding_summary = Column(Text, default="")
    key_partnerships = Column(Text, default="[]")       # JSON list
    differentiators = Column(Text, default="[]")        # JSON list of concrete claims
    source_urls = Column(Text, default="[]")            # JSON list
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class LeaderInsight(Base):
    """Per-competitor synthesis that answers the three study questions:
      1. the leader worth studying (name / role / background - from sources)
      2. what made them succeed (concrete, evidenced factors - from sources)
      3. application + market-route suggestions FOR Proteins.1 (recommendation,
         reasoned from this company's actual playbook)
    List fields are JSON-encoded."""
    __tablename__ = "leader_insights"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, index=True, nullable=False)
    domain = Column(String, default="")
    country = Column(String, default="")

    # Q1
    leader_name = Column(String, default="")
    leader_role = Column(String, default="")
    leader_background = Column(Text, default="")
    why_worth_studying = Column(Text, default="")

    # Q2  -> JSON list of {"factor": ..., "evidence": ...}
    success_factors = Column(Text, default="[]")

    # Q3  -> JSON lists of strings + a prose sequence
    application_suggestions = Column(Text, default="[]")
    market_route_suggestions = Column(Text, default="[]")
    route_summary = Column(Text, default="")

    confidence = Column(String, default="")             # high / medium / low
    source_urls = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class DiscoveredArticle(Base):
    """A background article / paper / news item on the single-molecule /
    ultra-sensitive protein-detection field. Keyed by normalised URL."""
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
