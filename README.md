# Proteins.1 — EU Platform-Competitor Collector

A focused data-collection backend: build a clean, source-traceable census of
**European companies building a Proteins.1-type platform** — physics/affinity-
driven single-molecule or ultra-sensitive protein detection, enzyme-free signal
amplification, single-molecule protein sequencing or sizing.

Not in scope: ctDNA / genomic liquid biopsy, antibody / reagent suppliers, CROs,
and non-European companies (dropped at store time).

No scoring, no opportunity map — this stage only collects and structures. The
next stage compares these competitors against Proteins.1.

## Quick start

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in ANTHROPIC_API_KEY (+ SERPER_API_KEY for reliable search)
uvicorn app.main:app --reload
```

`docker compose up --build` also works. API docs at http://localhost:8000/docs.

## Data model (`data/eu_competitors.db`)

| Table | What |
|---|---|
| `discovered_companies` | The census. One row per European platform company: `name, domain, country, platform_type, description, mention_count, analysed`. Keyed by domain; repeat sweeps de-duplicate. |
| `companies` | An **analysed** company: structured facts (`what_they_do, technology_approach, detection_modality, sensitivity_claim, sample_requirement, target_applications[], stage, funding_summary, key_partnerships[], differentiators[]` — from its own pages, never guessed), the **playbook** (`leader_name/role/background, why_worth_studying, success_factors[], application_suggestions[], market_route_suggestions[], route_summary, confidence`), and a **relevance score** (`score_platform/stage/route/evidence/ecosystem, relevance_score, rank, is_leader`). |
| `discovered_articles` | Background papers / news on the technology field. |

Raw page text is chunked into ChromaDB (`chroma_data/`), source-tagged, for
semantic lookup via `/api/evidence`.

## Pipeline

```
discover()         sweep -> classify -> country-filter -> de-dupe -> discovered_companies
analyze_company()  a company's pages -> Chroma -> LLM extract facts + synthesise playbook -> companies row
rank_companies()   score every companies row (fixed formula, no LLM) -> set rank + is_leader
```

Score: `relevance = 2·platform + 1.5·stage + 1.5·route + 1·evidence + 1·ecosystem`
(max 32.5). The top `top_n` (default 5) are flagged `is_leader` — the companies
whose playbook is most transferable to Proteins.1.

## Endpoints

| Method | Path | |
|---|---|---|
| POST | `/api/discover` | Run the landscape sweep. Body optional: `{"extra_terms": [...], "per_query": 8, "max_queries": 6}`. ~1 Serper credit per query. |
| GET | `/api/discovered-companies` | The census. Filters: `?country=`, `?platform_type=`, `?analysed=`. |
| GET | `/api/discovered-articles` | `?domain=` filter. |
| POST | `/api/analyze` | `{"company_name": "Refeyn", "urls": []}` — fetch pages, extract facts, synthesise the playbook into a `companies` row. |
| POST | `/api/rank` | `{"top_n": 5}` — score every analysed company; flag the leaders. |
| GET | `/api/companies` | The analysed companies, by rank. `?leaders_only=true`, `?country=`. |
| POST | `/api/evidence` | Semantic search over the raw collected text. |

## Layout

```
app/
  main.py            FastAPI app
  config.py          env vars + store paths
  database.py        SQLite models: DiscoveredCompany, Company, DiscoveredArticle
  schemas.py         Pydantic request/response models
  chroma_store.py    embedded ChromaDB wrapper
  agent/
    tools.py         search_web (Serper + fallbacks), SEC / openFDA / ClinicalTrials, fetch_page_text
    discovery.py     EU platform-company sweep
    pipeline.py      analyze_company (facts + playbook) + rank_companies (relevance score, is_leader)
  routers/
    collection.py    all /api/* endpoints
reports/             build_companies_page.py, build_leaders_page.py, export_json.py + data/*.json
scripts/             collect.py (end-to-end run), migrate_to_companies.py (one-off)
```

## Ground rules

- **No fabricated facts.** The profile prompt returns `null` / `[]` rather than
  guessing when something isn't in the source text. Keep it that way.
- **Every profile keeps its `source_urls`.**
- **European only.** `discovery.py` drops hits whose country resolves to a
  non-European location; undetermined-country hits are kept with `country=""`
  for a human to prune.
