"""
SQLite via SQLAlchemy. One file, no server to run - fine for a 1-2 day sprint.
Holds the STRUCTURED side of the data (companies, opportunities, evidence pointers).
Raw text lives in ChromaDB (see chroma_store.py), not here.
"""
import os
from datetime import datetime, timezone

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

os.makedirs(os.path.dirname(settings.sqlite_path) or ".", exist_ok=True)

engine = create_engine(f"sqlite:///{settings.sqlite_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Company(Base):
    """A comparable / competitor company used as a case study."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True, nullable=False)
    summary = Column(Text, default="")
    source_url = Column(String, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class CaseStudy(Base):
    """Structured, source-traceable notes about one comparable company."""
    __tablename__ = "case_studies"

    id = Column(Integer, primary_key=True)
    company_name = Column(String, index=True, nullable=False)
    leader_name = Column(String, default="")
    leader_background = Column(Text, default="")
    # JSON list: [{"factor": "...", "source_url": "..."}]
    success_factors = Column(Text, default="[]")
    application = Column(Text, default="")
    market_route = Column(Text, default="")
    source_urls = Column(Text, default="[]")
    verified = Column(String, default="unconfirmed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class EvidenceRecord(Base):
    """One source-backed claim used to justify a map score or recommendation."""
    __tablename__ = "evidence_records"

    id = Column(Integer, primary_key=True)
    opportunity_id = Column(Integer, index=True, nullable=True)
    company_name = Column(String, index=True, default="")
    # Brief §14.1: unmet_need, clinical_decision, payer_path, evidence_cost,
    # sample_access, incumbent_intensity, time_to_revenue, defensibility.
    dimension = Column(String, nullable=False)
    claim = Column(Text, nullable=False)
    source_url = Column(String, nullable=False)
    excerpt = Column(Text, default="")
    evidence_status = Column(String, default="unconfirmed")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Opportunity(Base):
    """
    One (disease area x marker class x customer segment x revenue model) candidate,
    scored on the 4 dimensions of the Opportunity Index (brief §14.3).
    Every score MUST be traceable - source_url is not optional in practice.
    """
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True)
    disease_area = Column(String, nullable=False)
    marker_class = Column(String, default="")
    customer_segment = Column(String, default="")
    revenue_model = Column(String, default="")

    # Each 0-10, see app/scoring.py for what they mean
    unmet_need = Column(Float, default=0.0)
    sensitivity_gain = Column(Float, default=0.0)
    market_size = Column(Float, default=0.0)
    regulatory_burden = Column(Float, default=0.0)

    rationale = Column(Text, default="")   # short human/LLM-written justification
    source_url = Column(String, default="")  # primary evidence link - keep this filled in
    verified = Column(String, default="unconfirmed")  # "measured" | "vendor_claim" | "estimate" | "unconfirmed"

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
