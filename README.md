# Proteins.1 Opportunity Map — Backend

FastAPI backend for the AI Solution Sprint. Structured data (companies, scored
opportunities) lives in SQLite; raw research text lives in ChromaDB, chunked
and source-tagged so every claim on the map traces back to a URL.

## Quick start 

```bash
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env        # then fill in ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs (FastAPI auto-generates this — good for
testing endpoints without a frontend yet).

## Quick start (Docker)

```bash
cp .env.example .env        # fill in ANTHROPIC_API_KEY
docker compose up --build
```

`search_web()` uses the **Serper.dev** Google Search API when `SERPER_API_KEY`
is set (free tier: 2,500 one-time credits), and otherwise falls back to the
no-key DuckDuckGo/Bing path.

## Folder layout

```
app/
  main.py            FastAPI app, CORS, startup
  config.py           env vars + default OI weights
  database.py          SQLite models: Company, Opportunity
  schemas.py           Pydantic request/response models
  scoring.py            Opportunity Index formula + unit sanity-check helpers
                        (DB also has: CaseStudy, EvidenceRecord, DiscoveredCompany, DiscoveredArticle)
  chroma_store.py        embedded ChromaDB wrapper (add_chunks / query_evidence)
  agent/
    tools.py             search_web, search_sec_filings, fetch_page_text, chunk_text
    pipeline.py           orchestrates: search -> fetch -> chunk -> store -> LLM-extract
    discovery.py          landscape sweep: search -> classify company/article -> de-dupe -> store
  routers/
    opportunities.py       all /api/* endpoints
```

## Endpoints

| Method | Path | What it does |
|---|---|---|
| POST | `/api/research` | Runs the agent for one company: `{"company_name": "Quanterix", "query_hint": "first customers, first application"}` |
| POST | `/api/discover` | Sweeps the web for every company/article in the Proteins.1 landscape (single-molecule / ultra-sensitive protein diagnostics), classifies and de-dupes them into SQLite. Body is optional: `{"extra_terms": [...], "per_query": 8, "max_queries": 5}`. Each query ≈ 1 Serper credit; omit `max_queries` for the full ~70-query sweep. |
| GET | `/api/discovered-companies` | The company census, most-mentioned first. Optional `?category=` filter (brief §8.4 buckets). |
| GET | `/api/discovered-articles` | Discovered articles / filings / press items. Optional `?domain=` filter. |
| GET | `/api/opportunity-map` | Returns all scored opportunities. Pass `w_unmet_need`, `w_sensitivity_gain`, `w_market`, `w_regulatory_burden` as query params to re-score live from the UI sliders. |
| POST | `/api/opportunities` | Manually add/edit one opportunity row (disease area, scores 0-10, source_url, rationale) |
| POST | `/api/evidence` | `{"query": "how did Quanterix get first customers", "company": "Quanterix"}` — semantic search over the raw chunks, for the "click a point, see the source" UI interaction |

## Ground rules baked into this scaffold

- **No fabricated numbers.** `pipeline.py`'s extraction prompt is instructed to
  return `null` rather than guess when a fact isn't in the source text —
  don't loosen this prompt under time pressure.
- **Weights are never hidden.** `/api/opportunity-map` takes weights as query
  params so the frontend can expose them as sliders, per the brief's "no
  black boxes" scoring criterion.
- **Every Opportunity row has a `source_url` and a `verified` field**
  (`measured` / `vendor_claim` / `estimate` / `unconfirmed`) — fill these in
  honestly; an `unconfirmed` row is still useful, a silently-guessed one isn't.
- **Don't put Proteins.1's own internal figures** (funding, cost structure,
  target lists — brief §12) into any `Opportunity.rationale` or company
  summary that will be shown on the public dashboard.

## Next steps to wire up

1. Seed a few opportunities via `POST /api/opportunities` or a small seed
   script, using facts you've already gathered by hand.
2. Point a Streamlit/React frontend at `/api/opportunity-map` for the 2x2
   plot and at `/api/evidence` for the click-through detail panel.
3. If `research_company()` is too slow live during the demo, pre-run it for
   your 3-5 key comparables beforehand and cache the results — call it live
   on stage only for a "wow, it can research anything" moment.
