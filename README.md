# MoMA Data Art

Data-driven visualizations built from each painting's own real geometry:
a painting's shapes are digitized from the reference image and become the
container for real MoMA collection data, revealed on hover. Mondrian spec:
`docs/superpowers/specs/2026-08-06-mondrian-real-geometry-redesign.md`.

## Progress

- [x] Project scaffolding
- [x] Data pipeline (`src/data.py`, tested against the real dataset)
- [ ] Mondrian chart (real-geometry redesign) — in progress
- [ ] Demoiselles / Dance I redesign — planned, spec TBD
- [ ] Static site + GitHub Pages
- [ ] Scheduled data refresh

`notebooks/01_eda.ipynb` is ready — open it in Jupyter and run the cells to
review the real distributions (Medium_category, Gender_simple, Region_list,
Decade) before building further chart functions.

## Next steps

- [ ] Push this repo to GitHub and link it from the Alherma7 profile README
