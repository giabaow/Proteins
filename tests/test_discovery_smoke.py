"""Offline smoke test for the EU platform-competitor discovery sweep.

Run: python -m tests.test_discovery_smoke

Stubs tools.search_web so it makes no network calls - checks classification,
country filtering, de-duplication, persistence, and the /api endpoints.
"""
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
from app.agent import discovery
from app.main import app

FAKE_RESULTS = {
    "q-eu": [
        # Swedish ccTLD -> kept, country from TLD
        {"title": "Pixelgen Technologies - single-cell spatial proteomics", "href": "https://pixelgen.se/technology/", "body": "Stockholm-based molecular pixelation."},
        # .com but snippet names a UK city -> kept
        {"title": "Refeyn | Mass Photometry", "href": "https://refeyn.com/", "body": "Refeyn, Oxford, UK - single-molecule mass photometry for proteins."},
        # US location in snippet -> dropped
        {"title": "Quanterix - Simoa", "href": "https://quanterix.com/", "body": "Billerica, Massachusetts. Ultra-sensitive digital ELISA."},
        # publisher -> article, not company
        {"title": "The emerging landscape of single-molecule protein sequencing", "href": "https://www.nature.com/articles/s41587-024-1", "body": "Review."},
    ],
    "q-eu-2": [
        {"title": "Refeyn home", "href": "https://www.refeyn.com/", "body": ""},   # dup domain
    ],
}


def fake_search_web(query, max_results=5):
    return FAKE_RESULTS.get(query, [])[:max_results]


def run_smoke_test() -> None:
    orig = (database.engine, database.SessionLocal, discovery.search_web,
            discovery.TOPIC_QUERIES, discovery.SEED_COMPANIES)
    with TemporaryDirectory() as tmp:
        eng = create_engine(f"sqlite:///{tmp}/t.db", connect_args={"check_same_thread": False})
        database.engine = eng
        database.SessionLocal = sessionmaker(bind=eng, autoflush=False, autocommit=False)
        database.Base.metadata.create_all(bind=eng)
        discovery.search_web = fake_search_web
        discovery.TOPIC_QUERIES = ["q-eu", "q-eu-2"]
        discovery.SEED_COMPANIES = []

        try:
            db = database.SessionLocal()
            res = discovery.discover(db, per_query=10)
            assert res["companies_found"] == 2, res           # pixelgen + refeyn (quanterix dropped)
            assert res["dropped_non_european"] == 1, res      # quanterix.com
            assert res["articles_found"] == 1, res            # nature
            doms = {c["domain"] for c in res["companies"]}
            assert doms == {"pixelgen.se", "refeyn.com"}, doms
            pix = next(c for c in res["companies"] if c["domain"] == "pixelgen.se")
            assert pix["country"] == "Sweden", pix
            ref = next(c for c in res["companies"] if c["domain"] == "refeyn.com")
            assert ref["country"] == "United Kingdom", ref
            assert ref["platform_type"] == "mass photometry", ref
            assert ref["mentions"] == 2, ref                  # both queries, one row
            db.close()

            db = database.SessionLocal()
            res2 = discovery.discover(db, per_query=10)
            assert res2["new_companies"] == 0 and res2["new_articles"] == 0, res2
            db.close()

            with TestClient(app) as client:
                companies = client.get("/api/discovered-companies")
                assert companies.status_code == 200, companies.text
                assert {c["domain"] for c in companies.json()} == {"pixelgen.se", "refeyn.com"}
                se = client.get("/api/discovered-companies?country=Sweden")
                assert [c["domain"] for c in se.json()] == ["pixelgen.se"], se.json()
        finally:
            (database.engine, database.SessionLocal, discovery.search_web,
             discovery.TOPIC_QUERIES, discovery.SEED_COMPANIES) = orig


if __name__ == "__main__":
    run_smoke_test()
    print("discovery smoke test passed")
