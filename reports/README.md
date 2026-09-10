# reports/

Presentation layer over `data/eu_competitors.db`. Nothing here touches the
database — each script reads it and emits a standalone HTML page or JSON.

| File | What it does |
|---|---|
| `build_companies_page.py` | **Companies** — every analysed company as a briefing: what they do, the leader to study, what made them succeed, application + market-route suggestions for Proteins.1. Score-flagged leaders are badged. Writes `companies.html`. |
| `build_leaders_page.py` | **The Leaders** — the companies the relevance score flags `is_leader`, as deep briefings, plus the full ranking table and the reason each non-leader was cut. Writes `leaders.html`. |
| `build_explorer_page.py` | **Explorer** — one interactive page over *all* the data: census, analysed companies, and articles, with search / filter / sort, rendered client-side from an embedded copy. Writes `explorer.html`. |
| `build_frontend_page.py` | **The frontend** (`frontend.html`) — the single page the app serves at `GET /`. Two tabs: **Overview** answers the three questions (leaders / what made the top 3 succeed / what Proteins.1 should do, from `recommendation.json`), **Data** is the Explorer's browse view. Premium light theme. |
| `export_json.py` | Dumps `discovered_companies`, `companies`, `recommendation`, `discovered_articles` to `reports/data/*.json` (the `.db` itself is gitignored). |
| `data/*.json` | Committed snapshot of the census and the analysed companies. |

The relevance score lives in the `companies` table, written by
`app.agent.pipeline.rank_companies` — the report scripts just read it. Formula
(fixed, no LLM, re-runnable):

```
relevance = 2.0·platform + 1.5·stage + 1.5·route + 1.0·evidence + 1.0·ecosystem   (max 32.5)
```
`platform` mechanism closeness · `stage` proximity to the RUO→commercial transition ·
`route` transferable go-to-market pattern · `evidence` documentation quality ·
`ecosystem` Nordic / close-EU proximity. Top N (default 5) → `is_leader`.

## Regenerate

```bash
PYTHONPATH=. python scripts/collect.py     # discover -> analyze_company -> rank_companies (writes the .db)
python reports/export_json.py              # refresh reports/data/*.json
python reports/build_frontend_page.py      # -> reports/frontend.html   (served at GET /)
python reports/build_companies_page.py     # -> reports/companies.html  (standalone)
python reports/build_leaders_page.py       # -> reports/leaders.html    (standalone)
python reports/build_explorer_page.py      # -> reports/explorer.html   (standalone)
```

Leader name and success factors are extracted only from cited sources; the
suggestions for Proteins.1 and the relevance score are analytical.
