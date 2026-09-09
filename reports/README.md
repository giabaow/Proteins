# reports/

Presentation layer over `data/eu_competitors.db`. Nothing here touches the
database — they read it and emit a standalone HTML page or JSON.

| File | What it does |
|---|---|
| `build_leaders_page.py` | **Option 1** — one briefing per profiled peer: the leader to study, what made them succeed, application + market-route suggestions for Proteins.1. Writes `leaders.html`. |
| `build_shortlist_page.py` | **Option 2** — scores every profiled peer on relevance to Proteins.1 (`2·platform + 1.5·stage + 1.5·route + 1·evidence + 1·ecosystem`), shows the top 5 as deep briefings and the rest with the reason each was cut. Writes `shortlist.html`. |
| `export_json.py` | Dumps the four tables to `reports/data/*.json` (the `.db` itself is gitignored). |
| `data/*.json` | Committed snapshot of the collected census, competitor profiles, and leader insights. |

## Regenerate

```bash
PYTHONPATH=. python scripts/collect.py     # discovery -> profile -> leader synthesis (writes the .db)
python reports/export_json.py              # refresh reports/data/*.json
python reports/build_leaders_page.py       # -> reports/leaders.html
python reports/build_shortlist_page.py     # -> reports/shortlist.html
```

Questions 1–2 (leader, success factors) are extracted only from cited sources.
Question 3 and the relevance score are analytical guidance for Proteins.1.
