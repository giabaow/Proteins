# reports/

Presentation layer over `data/eu_competitors.db`. Nothing here touches the
database — each script reads it and emits HTML or JSON.

| File | What it does |
|---|---|
| `build_frontend_page.py` | Builds `frontend.html` — the single page the app serves at `GET /`. **Overview** tab answers the three questions (leaders / what made the top 3 succeed / what Proteins.1 should do, from `data/recommendation.json`); **Data** tab is a client-side browser of the census, the analysed companies, and the articles. |
| `export_json.py` | Dumps `discovered_companies`, `companies`, `recommendation`, `discovered_articles` to `reports/data/*.json` (the `.db` itself is gitignored). |
| `data/*.json` | Committed snapshot the frontend embeds. |

The relevance score lives in the `companies` table, written by
`app.agent.pipeline.rank_companies` (fixed formula, no LLM, re-runnable):

```
relevance = 2·platform + 1.5·stage + 1.5·route + 1·evidence + 1·ecosystem   (max 32.5)
```
Top `top_n` (10) → `is_leader`. The Q3 recommendation is one `Recommendation`
row synthesised by `synthesize_recommendation` from the top 3 playbooks.

## Regenerate

```bash
PYTHONPATH=. python scripts/collect.py     # discover -> analyze_company -> rank -> synthesize (writes the .db)
python reports/export_json.py              # refresh reports/data/*.json
python reports/build_frontend_page.py      # -> reports/frontend.html  (served at GET /)
```

Facts and leaders are extracted only from cited sources; the relevance score
and the recommendation are analytical.
