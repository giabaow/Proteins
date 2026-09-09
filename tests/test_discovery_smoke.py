"""Offline smoke test for the landscape discovery sweep.

Run: python -m tests.test_discovery_smoke

Stubs tools.search_web so it makes no network calls - checks classification,
de-duplication, persistence, and the /api endpoints.
"""
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
from app.agent import discovery
from app.main import app

FAKE_RESULTS = {
    "single molecule protein detection company": [
        {"title": "Quanterix | Simoa Technology", "href": "https://www.quanterix.com/simoa-technology/", "body": "Ultra-sensitive biomarker detection."},
        {"title": "The emerging landscape of single-molecule proteomics", "href": "https://www.nature.com/articles/s41587-024-1", "body": "Review article."},
        {"title": "Quanterix press release", "href": "https://ir.quanterix.com/news-releases/2025/detail", "body": "Q1 results."},
    ],
    "ultra-sensitive proteomics platform company": [
        {"title": "Alamar Biosciences - NULISA", "href": "https://alamarbio.com/technology/", "body": "Attomolar sensitivity proteomics."},
        {"title": "Quanterix home", "href": "https://quanterix.com/", "body": ""},
    ],
}


def fake_search_web(query: str, max_results: int = 5):
    return FAKE_RESULTS.get(query, [])[:max_results]


def run_smoke_test() -> None:
    original_engine, original_session = database.engine, database.SessionLocal
    original_search = discovery.search_web
    original_topics = discovery.TOPIC_QUERIES
    original_seeds = discovery.SEED_COMPANIES
    with TemporaryDirectory() as temp_dir:
        test_engine = create_engine(
            f"sqlite:///{temp_dir}/discovery.db", connect_args={"check_same_thread": False}
        )
        database.engine = test_engine
        database.SessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
        database.Base.metadata.create_all(bind=test_engine)
        discovery.search_web = fake_search_web
        discovery.TOPIC_QUERIES = list(FAKE_RESULTS.keys())
        discovery.SEED_COMPANIES = {}

        try:
            db = database.SessionLocal()
            res = discovery.discover(db, per_query=10)

            # quanterix.com: 2 company-page hits (one per query) collapse to one
            # row; the ir.quanterix.com press release is classified as an article.
            assert res["companies_found"] == 2, res
            assert res["articles_found"] == 2, res            # nature review + IR press release
            quanterix = next(c for c in res["companies"] if c["domain"] == "quanterix.com")
            assert quanterix["mentions"] == 2, quanterix
            db.close()

            # second identical run adds nothing
            db = database.SessionLocal()
            res2 = discovery.discover(db, per_query=10)
            assert res2["new_companies"] == 0 and res2["new_articles"] == 0, res2
            db.close()

            with TestClient(app) as client:
                companies = client.get("/api/discovered-companies")
                articles = client.get("/api/discovered-articles")
                assert companies.status_code == 200, companies.text
                assert articles.status_code == 200, articles.text
                domains = {c["domain"] for c in companies.json()}
                assert {"quanterix.com", "alamarbio.com"} <= domains, domains
                assert companies.json()[0]["domain"] == "quanterix.com"  # ordered by mention_count
                assert any(a["domain"] == "nature.com" for a in articles.json())
        finally:
            database.SessionLocal = original_session
            database.engine = original_engine
            discovery.search_web = original_search
            discovery.TOPIC_QUERIES = original_topics
            discovery.SEED_COMPANIES = original_seeds


if __name__ == "__main__":
    run_smoke_test()
    print("discovery smoke test passed")
