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
| `discovered_companies` | The census. One row per European platform company: `name, domain, country, platform_type, description, mention_count, profiled`. Keyed by domain; repeat sweeps de-duplicate. |
| `competitor_profiles` | Deep, source-traceable profile for companies worth detailing: `what_they_do, technology_approach, detection_modality, sensitivity_claim, sample_requirement, target_applications[], stage, funding_summary, key_partnerships[], differentiators[], source_urls[]`. Every field is a fact from the company's own pages or empty — never guessed. |
| `discovered_articles` | Background papers / news on the technology field. |

Raw page text is chunked into ChromaDB (`chroma_data/`), source-tagged, for
semantic lookup via `/api/evidence`.

## Endpoints

| Method | Path | |
|---|---|---|
| POST | `/api/discover` | Run the landscape sweep. Body optional: `{"extra_terms": [...], "per_query": 8, "max_queries": 6}`. Each query ≈ 1 Serper credit; omit `max_queries` for the full sweep. |
| GET | `/api/discovered-companies` | The census. Filters: `?country=`, `?platform_type=`, `?profiled=`. |
| GET | `/api/discovered-articles` | `?domain=` filter. |
| POST | `/api/profile` | `{"company_name": "Refeyn", "urls": []}` — fetch the company's pages and LLM-extract a `competitor_profiles` row. |
| GET | `/api/competitors` | The deep profiles. `?country=` filter. |
| POST | `/api/evidence` | Semantic search over the raw collected text. |

## Layout

```
app/
  main.py            FastAPI app
  config.py          env vars + store paths
  database.py        SQLite models: DiscoveredCompany, CompetitorProfile, DiscoveredArticle
  schemas.py         Pydantic request/response models
  chroma_store.py    embedded ChromaDB wrapper
  agent/
    tools.py         search_web (Serper + fallbacks), SEC / openFDA / ClinicalTrials, fetch_page_text
    discovery.py     EU platform-company sweep: search -> classify -> country-filter -> de-dupe -> store
    pipeline.py      research_competitor: fetch a company's pages -> chunk -> Chroma -> LLM-extract profile
  routers/
    collection.py    all /api/* endpoints
```

## Ground rules

- **No fabricated facts.** The profile prompt returns `null` / `[]` rather than
  guessing when something isn't in the source text. Keep it that way.
- **Every profile keeps its `source_urls`.**
- **European only.** `discovery.py` drops hits whose country resolves to a
  non-European location; undetermined-country hits are kept with `country=""`
  for a human to prune.
