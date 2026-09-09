"""Fresh EU platform-competitor collection: discovery -> profile -> leader insight."""
import time, warnings, traceback, json
warnings.filterwarnings("ignore")

from app import database
from app.database import (SessionLocal, DiscoveredCompany, CompetitorProfile,
                          LeaderInsight, DiscoveredArticle)
from app.agent.discovery import discover
from app.agent.pipeline import research_competitor, analyze_leader

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

# junk domains that slipped past classification in earlier runs
JUNK = {"marketresearchfuture.com", "startupblink.com", "metwarebio.com", "instagram.com",
        "grandviewresearch.com", "mordorintelligence.com", "researchandmarkets.com"}

database.init_db()
log("fresh db at", database.settings.sqlite_path)

db = SessionLocal()
res = discover(db)
log(f"discover: {res['queries_run']} queries -> {res['companies_found']} EU companies "
    f"({res['new_companies']} new), {res['articles_found']} articles, "
    f"{res['dropped_non_european']} non-EU dropped")
purged = db.query(DiscoveredCompany).filter(DiscoveredCompany.domain.in_(JUNK)).delete(synchronize_session=False)
db.commit()
log(f"purged {purged} junk company rows")
db.close()

db = SessionLocal()
targets = [c.name for c in db.query(DiscoveredCompany)
           .filter(DiscoveredCompany.country != "")
           .order_by(DiscoveredCompany.mention_count.desc()).limit(15).all()]
db.close()
log(f"profiling + analysing {len(targets)}: {targets}")

for name in targets:
    db = SessionLocal()
    try:
        t0 = time.time()
        pr = research_competitor(db, name)
        p = pr["profile"]
        nf = sum(1 for k in ("what_they_do", "technology_approach", "detection_modality",
                             "sensitivity_claim", "sample_requirement", "stage", "funding_summary") if p.get(k))
        ins = analyze_leader(db, name)
        log(f"  {name}: profile {nf}/7 fields, {len(p['differentiators'])} diffs | "
            f"leader={ins['leader_name'] or '-'!r} factors={len(ins['success_factors'])} "
            f"apps={len(ins['application_suggestions'])} routes={len(ins['market_route_suggestions'])} "
            f"conf={ins['confidence']} ({time.time()-t0:.0f}s)")
    except Exception:
        log(f"  {name}: ERROR"); traceback.print_exc()
    finally:
        db.close()

db = SessionLocal()
log("=== SNAPSHOT ===")
log(f"discovered_companies : {db.query(DiscoveredCompany).count()}")
log(f"competitor_profiles  : {db.query(CompetitorProfile).count()}")
log(f"leader_insights      : {db.query(LeaderInsight).count()}")
log(f"discovered_articles  : {db.query(DiscoveredArticle).count()}")
from collections import Counter
cc = Counter(c.country or "(unknown)" for c in db.query(DiscoveredCompany).all())
log("companies by country: " + ", ".join(f"{k}:{v}" for k, v in cc.most_common()))
db.close()
log("DONE")
