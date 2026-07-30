# MoMA Data Art

Data-driven visualizations styled after three MoMA paintings, plus a
from-scratch Python reimplementation of the Geometrize image-to-polygon
technique. Full design: `docs/superpowers/specs/2026-07-30-moma-data-art-design.md`.

## Progress

- [x] Project scaffolding
- [x] Data pipeline (`src/data.py`, tested against the real dataset)
- [ ] Chart functions (Mondrian, Demoiselles, Dance I) — in progress
- [ ] Geometrize engine
- [ ] Static site + GitHub Pages
- [ ] Scheduled data refresh

Note: `Artworks.json` stores `Gender`/`Nationality` as lists per constituent
(e.g. `["male"]`, `["Austrian"]`, `[]`), not the CSV's parenthesized text
field the original PRA1 notebook parsed — `src/data.py` was corrected and
tested against the real schema after an initial CSV-based port failed on
the actual data. See `docs/superpowers/plans/2026-07-30-moma-data-art.md`
Task 2 for details.

`notebooks/01_eda.ipynb` is ready — open it in Jupyter and run the cells to
review the real distributions (Medium_category, Gender_simple, Region_list,
Decade) before Task 4 starts.

## Next steps

- [ ] Add Starry Night and Water Lilies (see spec's Extensibility section)
- [ ] Push this repo to GitHub and link it from the Alherma7 profile README
