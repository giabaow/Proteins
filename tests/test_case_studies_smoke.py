"""Run: python -m tests.test_case_studies_smoke"""
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database
from app.main import app


def run_smoke_test() -> None:
    original_engine = database.engine
    original_session = database.SessionLocal
    with TemporaryDirectory() as temp_dir:
        test_engine = create_engine(
            f"sqlite:///{temp_dir}/case_studies.db", connect_args={"check_same_thread": False}
        )
        database.engine = test_engine
        database.SessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
        database.Base.metadata.create_all(bind=test_engine)

        try:
            with TestClient(app) as client:
                payload = {
                    "company_name": "Example Diagnostics",
                    "leader_name": "Ada Example",
                    "leader_background": "Former clinical-laboratory founder.",
                    "success_factors": [{"factor": "Partnered with biobanks", "source_url": "https://example.test/source"}],
                    "application": "Early cancer detection",
                    "market_route": "RUO-first",
                    "source_urls": ["https://example.test/source"],
                    "verified": "vendor_claim",
                }
                created = client.post("/api/case-studies", json=payload)
                assert created.status_code == 200, created.text
                listed = client.get("/api/case-studies")
                assert listed.status_code == 200, listed.text

                evidence_payload = {
                    "company_name": "Example Diagnostics",
                    "dimension": "payer_path",
                    "claim": "A reimbursement precedent exists for this test category.",
                    "source_url": "https://example.test/payer",
                    "excerpt": "Published coverage decision.",
                    "evidence_status": "measured",
                }
                evidence_created = client.post("/api/evidence-records", json=evidence_payload)
                assert evidence_created.status_code == 200, evidence_created.text
                evidence_listed = client.get("/api/evidence-records?company_name=Example%20Diagnostics")
                assert evidence_listed.status_code == 200, evidence_listed.text

            row = next(item for item in listed.json() if item["id"] == created.json()["id"])
            assert row["company_name"] == payload["company_name"]
            assert row["success_factors"] == payload["success_factors"]
            assert row["market_route"] == "RUO-first"
            assert evidence_listed.json()[0]["dimension"] == "payer_path"
            assert evidence_listed.json()[0]["source_url"] == "https://example.test/payer"
        finally:
            database.SessionLocal = original_session
            database.engine = original_engine


if __name__ == "__main__":
    run_smoke_test()
    print("case-study smoke test passed")
