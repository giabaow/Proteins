"""End-to-end collection for the EU platform-competitor census.

  1. discover()          - sweep the web for European single-molecule / ultra-
                           sensitive protein-detection platform companies
  2. analyze_company()   - for the most-cited located companies: facts + playbook
  3. rank_companies()    - score every analysed company; flag the leaders

    PYTHONPATH=. python scripts/collect.py
    PYTHONPATH=. python scripts/collect.py 8      # cap to 8 companies (cheaper)
"""
import sys
import time
import traceback
import warnings

warnings.filterwarnings("ignore")

from app import database
from app.database import Company, DiscoveredArticle, DiscoveredCompany, SessionLocal
from app.agent.discovery import discover
from app.agent.pipeline import analyze_company, rank_companies, synthesize_recommendation

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 16
TOP_N = 10        # companies flagged is_leader
TOP_K = 3         # companies the Q3 recommendation is synthesised from


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


database.init_db()
log("db:", database.settings.sqlite_path)

db = SessionLocal()
res = discover(db)
log(f"discover: {res['queries_run']} queries -> {res['companies_found']} EU companies "
    f"({res['new_companies']} new), {res['articles_found']} articles, {res['dropped_non_european']} non-EU dropped")
db.close()

db = SessionLocal()
targets = [c.name for c in db.query(DiscoveredCompany)
           .filter(DiscoveredCompany.country != "")
           .order_by(DiscoveredCompany.mention_count.desc()).limit(LIMIT).all()]
db.close()
log(f"analysing {len(targets)}: {targets}")

for name in targets:
    db = SessionLocal()
    try:
        t0 = time.time()
        out = analyze_company(db, name)
        nf = sum(1 for k in ("what_they_do", "technology_approach", "detection_modality", "sensitivity_claim",
                             "sample_requirement", "stage", "funding_summary")
                 if getattr(db.query(Company).filter(Company.name == name).first(), k))
        log(f"  {name}: {nf}/7 facts | leader={out['leader_name'] or '-'!r} "
            f"factors={len(out['success_factors'])} conf={out['confidence']} "
            f"({len(out['sources_used'])} src, {time.time()-t0:.0f}s)")
    except Exception:
        log(f"  {name}: ERROR")
        traceback.print_exc()
    finally:
        db.close()

db = SessionLocal()
res = rank_companies(db, top_n=TOP_N)
log(f"ranked {res['ranked']}; leaders: {res['leaders']}")
rec = synthesize_recommendation(db, top_k=TOP_K)
log(f"recommendation from {rec.get('from_companies')}: {len(rec.get('applications', []))} apps, "
    f"{len(rec.get('market_route', []))} route steps")
log("=== SNAPSHOT ===")
log(f"discovered_companies : {db.query(DiscoveredCompany).count()}")
log(f"companies            : {db.query(Company).count()}")
log(f"  of which leaders    : {db.query(Company).filter(Company.is_leader.is_(True)).count()}")
log(f"discovered_articles  : {db.query(DiscoveredArticle).count()}")
db.close()
log("DONE")
