# MoMA Data Art — Chart Redesign (v2)

Date: 2026-07-31

Supersedes the Pipeline A chart designs (`mondrian_treemap`,
`demoiselles_radar`, `dance_circular_bar`) from
`docs/superpowers/specs/2026-07-30-moma-data-art-design.md`. Everything else
in that spec (architecture, Geometrize pipeline, presentation layer, CI
refresh) is unchanged.

## Why

Task 7's qualitative gate (per the original spec: "does it read as the
target painting?") failed for all three charts once run against the real
data. The user had already solved this problem once, in a Tableau Public
project (`PRA1/VARIOS/Libro_probatinas.twb`) with three dashboards —
"Mondrian y obtenciones," "Picasso y el género," "Dispersión al ritmo de
Matisse" — that do read as their paintings. This spec ports those three
designs into `src/charts.py`, replacing the v1 designs rather than
iterating on them.

No prior Python/R script for the Tableau Voronoi was found in the original
project (only the `.twb`'s own worksheet definition) — it was built with a
Tableau extension with no reusable source. It is reimplemented from scratch
here.

## Data layer additions (`src/data.py`)

Three new outputs from `clean_artworks()`, alongside the existing
`Medium_category`/`Gender_simple`/`Nationality_list`/`Region_list`/`Decade`/
`Year_min`:

- **`Credit_category`**: `classify_credit(credit_line: str) -> str`, a
  keyword classifier over the `CreditLine` field, ported directly from the
  original PRA1 notebook's `classify_credit()` (validated there against the
  same field): `fund/institutions`, `purchase/acquired`, `donated/gifts`,
  `individual`, `other/unknown`.
- **`Num_participants`**: `count_participants(genders: list) -> int` =
  `len(genders)` if it's a list, else `0` — number of constituents credited
  on the artwork. (Simpler than the original's regex over the CSV field,
  since `Artworks.json`'s `Gender` is already a list per constituent.)
- **`Decade_acquired`** (and `Year_acquired`): the existing `classify_decade()`
  applied to `DateAcquired` instead of `Date` — no new function needed, it
  already extracts a 4-digit year from free text and buckets it into a
  decade string, and `DateAcquired` (format `YYYY-MM-DD`) parses through it
  unchanged.

`Gender_simple` is unchanged — the Voronoi chart's gender-ratio calculation
only needs counts where `Gender_simple` is `"male"` or `"female"`, which the
existing categories already support.

## The three charts (`src/charts.py`)

All three replace their v1 counterparts in place (same module, same public
call sites in `build_site.py`); two are renamed to match what they now do.

### `mondrian_treemap(df)` (grouping changed, same name)

Hierarchy `Decade_acquired → Credit_category`, box size = artwork count.
Reproduces the Tableau screenshot's coloring exactly:

1. Take the 5 decades with the highest total acquisition count.
2. Sort them chronologically.
3. Color the first three `red`, `blue`, `yellow` (in that order); color
   every decade after that `black`.

This is *not* a 4-color cycle — it's "3 primaries, then black for
everything else," matching the observed screenshot (1960→red, 1970→blue,
1990→yellow, 2000→black, 2010→black) and, incidentally, reading more like
an actual Mondrian composition (mostly black grid, a few color accents)
than a strict cycle would.

### `demoiselles_voronoi(df)` (renamed from `demoiselles_radar`)

One Voronoi cell per `Decade` (creation-date decade, matching the Tableau
subtitle "Décadas agrupadas según ... los artistas" grouped by decade, not
acquisition decade). Cell area ∝ total artwork count that decade. Cell
color on a continuous scale from pale pink (gender-balanced or
female-leaning) to dark maroon (male-dominated), computed as:

```
male_count / (male_count + female_count)
```

restricted to that decade's rows where `Gender_simple` is `"male"` or
`"female"` (decades with zero such rows get a neutral/gray fallback color).

Requires a new from-scratch module, **`src/voronoi_treemap.py`**, since no
Plotly chart type or maintained library produces a weighted Voronoi
treemap:

1. `sample_points(weights: dict[str, float], rng, total_points: int = 2000) -> dict[str, list[tuple[float, float]]]`:
   for each group (decade), sample a number of random points within a unit
   square proportional to its weight (share of total).
2. `voronoi_cells(points: dict[str, list[tuple[float, float]]]) -> dict[str, Polygon | MultiPolygon]`:
   run `scipy.spatial.Voronoi` on the *combined* point set (all groups
   together, each site tagged with its group), clip infinite/boundary
   cells to the unit square, then union all cells belonging to the same
   group into one polygon via `shapely.ops.unary_union`.
3. `demoiselles_voronoi()` calls both, computes each polygon's fill color
   from the gender ratio, and renders each merged polygon as its own
   `go.Scatter` trace with `fill='toself'` (one trace per decade, so each
   keeps its own hover label and color — consistent with how
   `demoiselles_radar` already used `go.Scatter`-family traces).

Cell edges will look organic/jagged rather than the smooth straight edges
of a true power-diagram-based weighted Voronoi treemap (e.g. Balzer &
Deussen's iterative algorithm) — an accepted trade-off, and one that
arguably fits the cubist theme better.

### `dance_scatter(df)` (renamed from `dance_circular_bar`)

One point per `Decade` (creation-date decade), restricted to group-authored
works (`Num_participants >= 2`):

- x = count of group-authored works that decade
- y = sum of `Num_participants` across those works that decade

Rendered with `images/dance_i.png` as a full-bleed background via Plotly's
`fig.add_layout_image(...)`, matching the Tableau dashboard's technique of
placing the painting as a background layer behind a transparent chart
(`Dance_invertido.png` behind the `scatter` worksheet in the original
`.twb`). Markers colored on a sequential scale through the existing `dance`
palette (orange → green → blue) by chronological decade order, echoing
Matisse's 3 flat colors.

## New dependency

`shapely`, added to `requirements.txt`, needed for polygon union in
`voronoi_treemap.py`.

## Testing plan

- `tests/test_data.py`: new tests for `classify_credit()`,
  `count_participants()`, and `Decade_acquired`/`Year_acquired` appearing in
  `clean_artworks()`'s output — same style as the existing tests (known
  inputs, including null/empty/boundary values, map to expected output).
- `tests/test_voronoi_treemap.py`: for a set of synthetic weights, verify
  (a) each group produces exactly one merged polygon, (b) polygon areas
  converge to the target weight proportions within a tolerance as sample
  density increases, (c) total polygon area conserves the bounding region
  (no gaps/overlaps beyond floating-point tolerance).
- `tests/test_charts.py`: the existing 3 tests are replaced (same file,
  `_sample_df()` fixture extended with `CreditLine`, `DateAcquired`,
  `Gender_simple` columns) — each function still asserts it returns a
  `go.Figure` with the right shape of data (e.g. `dance_scatter` produces
  exactly one point per group-work decade; `mondrian_treemap` only uses the
  4 palette colors).
- Pipeline A's qualitative gate (Task 7's prototyping notebook) is re-run
  against these new designs before they're considered final, per the
  original spec's rule.

## Migration notes

- `notebooks/02_chart_prototyping.ipynb` (already created, not yet
  executed) is updated in place to call the renamed functions
  (`demoiselles_voronoi`, `dance_scatter`) — no structural change to the
  notebook itself.
- `src/build_site.py` (not yet built as of this spec) will reference the
  renamed functions directly; no migration needed there since it doesn't
  exist yet.
