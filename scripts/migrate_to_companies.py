"""One-off: fold the old competitor_profiles + leader_insights tables into the
new unified `companies` table, then run the ranking. Safe to re-run.

    PYTHONPATH=. python scripts/migrate_to_companies.py
"""
import json
import sqlite3
import warnings

warnings.filterwarnings("ignore")

from app import database
from app.database import Company, SessionLocal
from app.agent.pipeline import rank_companies

database.init_db()  # creates the `companies` table if missing

raw = sqlite3.connect(database.settings.sqlite_path)
raw.row_factory = sqlite3.Row
existing = {t[0] for t in raw.execute("select name from sqlite_master where type='table'")}

# discovered_companies.profiled -> analysed (create_all won't alter columns)
dc_cols = {c["name"] for c in raw.execute("pragma table_info(discovered_companies)")}
if "profiled" in dc_cols and "analysed" not in dc_cols:
    raw.execute("alter table discovered_companies rename column profiled to analysed")
    raw.commit()
    print("renamed discovered_companies.profiled -> analysed")
elif "analysed" not in dc_cols:
    raw.execute("alter table discovered_companies add column analysed boolean default 0")
    raw.commit()
    print("added discovered_companies.analysed")

if "leader_insights" not in existing and "competitor_profiles" not in existing:
    print("nothing to migrate")
else:
    profiles = {r["company_name"]: r for r in raw.execute("select * from competitor_profiles")} \
        if "competitor_profiles" in existing else {}
    insights = {r["company_name"]: r for r in raw.execute("select * from leader_insights")} \
        if "leader_insights" in existing else {}
    names = sorted(set(profiles) | set(insights))

    db = SessionLocal()
    migrated = 0
    for name in names:
        p, ins = profiles.get(name), insights.get(name)
        row = db.query(Company).filter(Company.name == name).first()
        if row is None:
            row = Company(name=name)
            db.add(row)
        row.domain = (p["domain"] if p else "") or (ins["domain"] if ins else "") or ""
        row.country = (p["country"] if p else "") or (ins["country"] if ins else "") or ""
        if p:
            for f in ("what_they_do", "technology_approach", "detection_modality", "sensitivity_claim",
                      "sample_requirement", "stage", "funding_summary"):
                setattr(row, f, p[f] or "")
            row.target_applications = p["target_applications"] or "[]"
            row.key_partnerships = p["key_partnerships"] or "[]"
            row.differentiators = p["differentiators"] or "[]"
        if ins:
            for f in ("leader_name", "leader_role", "leader_background", "why_worth_studying",
                      "route_summary", "confidence"):
                setattr(row, f, ins[f] or "")
            row.success_factors = ins["success_factors"] or "[]"
            row.application_suggestions = ins["application_suggestions"] or "[]"
            row.market_route_suggestions = ins["market_route_suggestions"] or "[]"
        srcs = []
        for src in (ins["source_urls"] if ins else None, p["source_urls"] if p else None):
            try:
                srcs += [u for u in json.loads(src or "[]") if u not in srcs]
            except (json.JSONDecodeError, TypeError):
                pass
        row.source_urls = json.dumps(srcs)
        migrated += 1
    db.commit()
    db.close()
    print(f"migrated {migrated} companies")

    raw.execute("drop table if exists leader_insights")
    raw.execute("drop table if exists competitor_profiles")
    raw.commit()
    print("dropped old tables")

# mark analysed + rank
db = SessionLocal()
from app.database import DiscoveredCompany
analysed = {c.name for c in db.query(Company)}
for d in db.query(DiscoveredCompany):
    d.analysed = d.name in analysed
db.commit()
res = rank_companies(db, top_n=5)
db.close()
print(f"ranked {res['ranked']}; leaders: {res['leaders']}")
