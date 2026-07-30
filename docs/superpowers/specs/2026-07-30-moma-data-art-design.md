# MoMA Data Art — Design Spec

Date: 2026-07-30

## Purpose

Rework the original PRA1 project (MoMA collection data analysis + a manual,
disconnected recreation of famous paintings via the Geometrize web tool and
Tableau) into a single, reproducible Python project that does two things
properly and ties them together:

1. **Data → form:** visualizations built from real MoMA collection metadata,
   each designed to visually evoke a specific MoMA painting.
2. **Geometrize engine:** a from-scratch Python implementation of the
   Geometrize-style algorithm (image → geometric-primitive mosaic), replacing
   the manual web-tool + Tableau workflow the original project couldn't
   finish.

Both pipelines consume the same cleaned dataset/images and are combined in a
single static presentation page.

## Scope (v1)

Three paintings, chosen because source images and prior exploration already
exist from the original project:

- **Broadway Boogie Woogie** (Mondrian)
- **Les Demoiselles d'Avignon** (Picasso)
- **Dance (I)** (Matisse)

Starry Night (Van Gogh) and Water Lilies (Monet) are explicitly deferred to a
later iteration — the structure below must extend to them without rework
(one new chart function + one new Geometrize config entry per painting).

Out of scope for v1: Tableau, the manual Geometrize web tool, any non-Python
tooling.

## Architecture

```
data/MoMA GitHub (Artworks.json, Artists.json)
        │
        ▼
  src/data.py  (load, clean, categorize — reuses/refines the original notebook's logic)
        │
        ├──────────────────────────┬───────────────────────────
        ▼                          ▼
  Pipeline A: src/charts.py   Pipeline B: src/geometrize/
  (one function per painting) (hill-climbing engine, one config per painting)
        │                          │
        └──────────┬───────────────┘
                    ▼
          src/build_site.py
                    │
                    ▼
      outputs/site/  →  GitHub Pages (static HTML, Plotly figures embedded,
                         Geometrize SVGs embedded)
```

The two pipelines share input data/images but have no dependency on each
other; each can be built, tested, and validated independently.

## Project structure

(Adapted from the `structuring-ml-projects` skill skeleton — this isn't an ML
project, but the same discipline applies: cite sources, validate in a
notebook before wiring into `src/`, log negative results, and now also unit
test deterministic code.)

```
moma-data-art/
  .github/
    workflows/
      refresh-data.yml   # weekly cron + manual dispatch: re-download data, rebuild charts+site, skip Geometrize
  data/
    raw/            # Artworks.json, Artists.json (copied from the original
                    # PRA1/collection-v2025-11-25/ folder)
    processed/      # artworks_clean.parquet
  images/           # source images: broadway_boogie_woogie.jpg,
                    # les_demoiselles_davignon.jpg, dance_i.jpg
  notebooks/
    01_eda.ipynb
    02_chart_prototyping.ipynb        # one round per painting's chart, before graduating to src/charts.py
    03_geometrize_prototyping.ipynb   # tuning shape count/type/iterations per painting
  src/
    config.py          # paths, palettes per painting, RANDOM_STATE, shape-type per painting, iteration counts
    data.py             # load_raw_data(), clean/categorize (Decade, Nationality/Region, Medium_category, Gender_simple), save_processed()
    charts.py           # mondrian_treemap(), demoiselles_radar(), dance_circular_bar() — one function per painting, returns a Plotly figure
    geometrize/
      shapes.py          # candidate shape generation/mutation (rectangle, triangle, ellipse)
      engine.py           # hill-climbing loop: generate K candidates, score, keep best, refine, repeat until N shapes
      evaluate.py          # reconstruction-error metric (RMSE/SSIM) + reusable scoring function
    build_site.py         # load -> charts -> geometrize (reused unless --force-geometrize) -> assemble -> export static HTML
  tests/
    test_data.py          # unit tests for src/data.py cleaning/categorization functions
    test_geometrize_evaluate.py  # unit tests for the RMSE/SSIM metric itself
  outputs/
    charts/                # exported Plotly HTML per painting
    geometrize/              # final SVG per painting + error-convergence plot
    site/                     # final static page for GitHub Pages
  README.md              # Progress log + Next steps checklist
  RESOURCES.md            # every technique's source
```

`train.py` from the original skeleton is `build_site.py` here (no model being
trained; the "training" is the Geometrize hill-climbing loop, self-contained
inside `geometrize/engine.py`).

## Component design

### Data pipeline (`src/data.py`)

- `download_raw_data()`: fetches `Artworks.json`/`Artists.json` directly from
  `github.com/MoMA/collection` into `data/raw/`, overwriting any existing
  copy. Used by the CI refresh workflow, and optionally locally when you
  want a fresh pull instead of the bootstrapped copy.
- `load_raw_data()`: reads whatever is currently in `data/raw/` — for the
  initial local setup this is the copy bootstrapped once from
  `PRA1/collection-v2025-11-25/`, so a full first-time download isn't
  required.
- Cleaning/categorization reuses and refines the logic already validated in
  the original notebook: `Medium_category`, `Gender_simple`,
  `Decade`/`Year_norm`, `Nationality_list`/`Region_list`.
- `save_processed()` writes the single processed dataframe consumed by both
  pipelines.

### Pipeline A — data-driven charts (`src/charts.py`)

One function per painting, each returning a Plotly figure:

- **`mondrian_treemap(df)`**: hierarchy `Department` → `Classification`/
  `Medium_category`; box size = artwork count; color cycles Mondrian's
  palette (red `#D40920`, blue `#1356A2`, yellow `#F7D842`, black, off-white
  background); thick black tile borders to mimic the grid.
- **`demoiselles_radar(df)`**: 5 axes = 5 Departments/Classifications
  (echoing the painting's 5 figures); one semi-transparent overlapping trace
  per Region/Nationality (`fill='toself'`, low opacity) for a fragmented,
  cubist look; earthy/pink palette pulled from the painting.
- **`dance_circular_bar(df)`**: categories (top-N decades or regions)
  arranged in a ring; bar length = artwork count; color cycles Matisse's 3
  flat colors (orange, green, blue) — echoing the ring of 5 dancers.

Each chart function is validated in `02_chart_prototyping.ipynb` (does the
encoding honestly represent the data? does it read as the target painting?)
before graduating to `src/charts.py`, per the skill's graduation rule.

### Pipeline B — Geometrize engine (`src/geometrize/`)

A Python reimplementation of the Geometrize/`primitive` (Fogleman) algorithm:
hill-climbing placement of geometric primitives to approximate a target
image.

1. **Metric first**: reconstruction error (RMSE or SSIM) between the
   generated canvas and the target image — pinned before any engine code is
   written, since it drives every accept/reject decision.
2. Per new shape: generate *K* random candidates (position/size/
   rotation/color sampled from the target region), score each by how much it
   reduces the error, keep the best, refine it with a few more mutation
   rounds (the hill-climbing step).
3. Repeat until *N* shapes are placed or the error stops improving
   meaningfully.
4. Output: final SVG (embedded directly in the site — no raster needed) +
   an error-convergence plot saved to `outputs/geometrize/`.

**Shape type is a per-painting hyperparameter in `config.py`**: rectangles
for Mondrian (matches the painting's actual block composition — should
converge fast with few shapes), triangles for Les Demoiselles (fragmented
cubist planes), ellipses for Dance I (flat color regions, curved bodies).

## Testing plan

- `tests/test_data.py`: unit tests for each cleaning/categorization function
  in `src/data.py` — known inputs (including null/empty/boundary values) map
  to the expected output.
- `tests/test_geometrize_evaluate.py`: unit tests for the RMSE/SSIM formula
  itself (e.g. identical images → zero error; known synthetic diffs → known
  score).
- Pipeline A has no numeric win/lose gate (no ground truth); its check is
  qualitative, per the `dataviz` skill's principles — done in the
  prototyping notebook before a chart function graduates to `src/charts.py`.
- Pipeline B has a real quantitative gate: a hyperparameter change (shape
  count, candidates per iteration `K`) only gets promoted into `config.py`'s
  defaults if it improves the RMSE/SSIM curve without a disproportionate
  runtime cost — the same before/after discipline as the ML skill's gate,
  applied to image-reconstruction error instead of a model metric.

## Presentation layer

`src/build_site.py` assembles, per painting, a "triptych": the original
painting image, the data-driven chart (Plotly figure exported to
self-contained HTML), and the Geometrize SVG recreation, side by side, with a
short caption explaining the data→form mapping used. The three triptychs are
combined into one static HTML page (plain HTML/CSS, no JS framework) and
published via GitHub Pages — instant load, no server, no third-party
dependency.

## Automated data refresh (CI)

`github.com/MoMA/collection` is updated periodically (the README states data
is refreshed "on a regular basis"; the source repo's dated snapshot folders
confirm periodic releases, though no exact cadence is published). Rather
than hardcoding an assumed frequency, the pipeline re-checks on its own
schedule:

- A GitHub Actions workflow (`.github/workflows/refresh-data.yml`) runs on a
  weekly cron trigger (plus manual `workflow_dispatch` for on-demand runs):
  checkout → set up Python → run `src/data.py` to re-download and re-clean
  `Artworks.json`/`Artists.json` → regenerate only the Pipeline A chart
  figures → reassemble the site.
- **Geometrize outputs are not regenerated by this workflow.** Pipeline B
  depends only on the fixed painting images, not on MoMA's metadata, so
  `build_site.py` reuses the existing SVGs in `outputs/geometrize/` by
  default and only recomputes them if explicitly forced (e.g. a source image
  changes) — this keeps the scheduled run fast and avoids needless
  hill-climbing recomputation.
- If the refreshed data changes any chart output, the workflow commits the
  updated `outputs/` and `data/processed/` and the GitHub Pages deploy picks
  it up automatically; if nothing changed, the run is a no-op (no empty
  commits).

## Extensibility (deferred to a later iteration)

Adding Starry Night or Water Lilies later means: one new chart function in
`charts.py`, one new painting entry in `config.py` (palette + Geometrize
shape type), and one new triptych block in `build_site.py`. No structural
changes needed.

## Sources to record in RESOURCES.md

- Fogleman's `primitive` algorithm / Geometrize project — basis for the
  hill-climbing engine.
- Ken Flerlage's original SVG→Tableau script — prior technique this engine
  replaces.
- `github.com/MoMA/collection` — dataset source.
