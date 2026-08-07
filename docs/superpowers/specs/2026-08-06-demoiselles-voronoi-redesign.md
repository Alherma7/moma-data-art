# Demoiselles d'Avignon Voronoi redesign

## Amendment 2 (2026-08-07 session, later)

Amendment 1 below (cell *count* data-derived, cell *size* only
rank-ordered, no proportionality) was implemented and rendered, and the
user rejected it after seeing it: "si hay una celda de 1 obra se debe de
notar que es mucho más pequeña" — they want genuine proportional area,
not just correct ordering. This supersedes Amendment 1's "aproximado por
rango" stance entirely.

**New mechanism: a real weighted Voronoi diagram (power/Laguerre
diagram), not an ordinary Voronoi diagram.** Implemented and validated
numerically (mean absolute area error ~0.005 of canvas area across the
24 real categories, zero cell overlaps) before being wired into the
notebook — see `notebooks/04_demoiselles_prototyping.ipynb` for the
authoritative, current code; this doc records the *design*, not a
step-by-step build script (the notebook changed too fast across several
live iterations this session for the plan doc to stay a literal script).

- **Power diagram, not ordinary Voronoi.** Each site `i` gets a weight
  `w_i`; a point `x` belongs to site `i`'s cell iff
  `|x - p_i|² - w_i` is smaller than for every other site (power
  distance, not Euclidean distance). Computed via the standard
  lift-to-paraboloid trick: lift `(x_i, y_i)` to
  `(x_i, y_i, x_i² + y_i² - w_i)`, take `scipy.spatial.ConvexHull` of
  the lifted points, keep the **lower** hull facets
  (`hull.equations[:, 2] < 0`), and for each lower-hull triangle solve
  for its "power center" (the 2D point equidistant in power-distance
  from the triangle's 3 sites — a 2×2 linear system, the power-diagram
  analogue of a circumcenter). A site's cell is the convex hull of all
  power-centers of triangles containing it (power cells are always
  convex, so no angular sorting is needed — `shapely`'s `MultiPoint(...).convex_hull`
  does it directly). Sites are mirrored across all four canvas edges
  first (same trick as the old unweighted `bounded_voronoi_cells`) so
  every real site's cell closes inside the canvas.
- **Iterative solver, two knobs adjusted together per iteration:**
  1. *Weight update*: `w_i += lr * (target_frac_i - actual_frac_i)`,
     then re-center weights (`w -= w.mean()`) since power diagrams are
     invariant to a global additive shift in all weights.
  2. *Position update (partial Lloyd relaxation)*: nudge each site
     toward its own cell's centroid, `p_i += move_lr * (centroid_i - p_i)`,
     skipping the move if the centroid falls inside a face contour.
     Weight adjustment alone left 2-3 categories stuck far from target
     (their fixed anchor position was geometrically boxed in by
     neighbors); adding position relaxation alongside weight adjustment
     dropped mean absolute error from ~0.005 to ~0.00003 (pre-face-clip).
     ~250 iterations, `lr≈0.4`, `move_lr≈0.15` converges cleanly for 24
     sites on this canvas.
  3. Face clipping (`clip_faces`, unchanged from Amendment 1) is applied
     **after** convergence, not during — the solver converges on the
     full unit square, and whatever area a face steals from an
     adjacent cell afterward is accepted as a known, modest distortion
     (same trade-off already accepted for face-adjacent cells in the
     unweighted version).
- **Minimum-area floor, chosen explicitly over literal proportionality.**
  With real data this skewed (1 to 44,170 works — a ~44,000× range),
  literal proportional area makes the tiniest categories mathematically
  vanish (zero-area / absent from the diagram entirely). Asked directly,
  the user chose a visible floor over disappearance: `target_frac_i =
  max(raw_frac_i, MIN_FRAC)` (`MIN_FRAC = 0.01`, i.e. every category
  gets at least 1% of canvas area), renormalized to sum to 1 afterward.
  This means the smallest categories are **not** literally
  proportional — their area is a floor, not a measurement — which is a
  deliberate, known departure from "genuinely proportional" for the
  sake of every category staying visible and hoverable, matching the
  user's reference screenshot where even the smallest labeled regions
  remain visible slivers, not points.
- **Anchors, not a flat point cloud.** One site per category (24, ranked
  by count like before), placed via the same face-avoiding jittered-grid
  `generate_seed_points` already built in Task 1 — positions then move
  during Lloyd relaxation, so the initial placement only needs to be
  reasonably well-spread, not final.
- **Practical effect on the pipeline shape:** cell generation and
  category assignment are no longer separate steps (generate geometry,
  then separately rank-zip categories to cells). A weighted-diagram
  *site* **is** a category from the moment it's created — there is no
  post-hoc `_assign_labels_to_cells`-style rank matching anymore; that
  entire mechanism (introduced in Amendment 1) is deleted, not kept
  alongside the new one.

## Amendment 1 (2026-08-07 session, earlier — partially superseded above)

The first prototype (fixed ~40 seed points, independent of the data,
zipped by rank to whatever (decade, gender) combinations existed) didn't
read well once rendered: most cells ended up unassigned/neutral because
the fixed cell count rarely matched the real number of categories. The
design changes to: **the number of data-bearing Voronoi cells equals the
number of (decade, gender) categories actually present in the cleaned
data**, capped at `MAX_CELLS` (40, matching the old fixed density) —
categories beyond the cap are pooled into a single "Other" entry, same
pooling rule as before. Cell *size* is still not an exact proportional
encoding (no weighted/power Voronoi, no iterative area-fitting
algorithm): cells are generated by an ordinary unweighted Voronoi
tessellation over `n_cells` seed points, then the naturally-largest
cells are handed to the highest-count categories by rank — the same
zip-by-rank principle as Mondrian and as the original prototype, just
with the cell *count* now matched to the category count instead of
fixed. This means seed-point generation (and therefore the Voronoi
tessellation) can only happen **after** the (decade, gender) counts are
computed from the real data — the "Data mapping" step now runs before
the "Geometry" step, reversing the original build order. Face contours
are unaffected — still fixed, hand-digitized, independent of data.

## Concept

Same principle as the Mondrian chart: the painting's own real geometry is
the data container, revealed on hover. Rectangles don't fit Picasso's
fractured, angular style, so this chart uses a Voronoi diagram computed
over the canvas of `images/les_demoiselles_davignon.png` instead — cells
carved out of the picture plane, echoing Picasso's own faceted shapes,
holding real MoMA collection data.

Unlike Mondrian, where color is always the painting's real color and data
lives only in the hover text, here **color is a data encoding** (gender)
because the painting itself has no consistent per-region color scheme to
preserve — Cubist faceting doesn't map to flat regions the way Mondrian's
primary-color blocks do.

## Data mapping

- **Gender per person**: classified per credited person (not per artwork)
  from the raw MoMA `Gender` field. Checked against the real distinct
  values in `data/raw/Artworks.json`:

  | Raw value | Count | Bucket |
  |---|---|---|
  | `male` | 139,556 | Hombre |
  | `female` | 23,888 | Mujer |
  | `female (transwoman)` | 62 | Transgénero |
  | `male (trans? ftm?)` | 11 | Transgénero |
  | `transgender woman` | 1 | Transgénero |
  | `` (empty) | 1,713 | discarded |
  | `non-binary` | 13 | discarded |
  | `gender non-conforming` | 2 | discarded |

  Rule, evaluated in this order: value contains "trans" → Transgénero;
  else starts with "female" → Mujer; else starts with "male" → Hombre;
  anything else is discarded from the count. Checking "trans" first is
  what correctly buckets `female (transwoman)` and `male (trans? ftm?)`
  into Transgénero instead of leaking into Mujer/Hombre by prefix match.
  The three discarded values (empty, non-binary, gender non-conforming)
  are genuinely distinct categories or missing data, not wording variants
  of the three buckets — nothing is being incorrectly dropped.

- **Decade**: `Decade_acquired`, same field and logic as Mondrian.

- **Cell count**: count (decade, gender) combinations, e.g.
  `("1960s", "Mujer")`. `n_cells = min(len(counts), MAX_CELLS)` with
  `MAX_CELLS = 40`. If there are more combinations than `MAX_CELLS`, the
  smallest are pooled into a single "Other" entry so the category count
  itself is capped at `MAX_CELLS` (same pooling rule as before, just
  applied before seed generation instead of after). `n_cells` seed points
  are then generated (see Geometry) and tessellated, so **every cell
  ends up assigned to a category** — there are no leftover
  neutral/unassigned cells in the normal case.
- **Cell assignment**: categories are ranked by count descending; Voronoi
  cells are ranked by their naturally-occurring area descending (no
  weighted/power Voronoi — an ordinary tessellation over `n_cells` seed
  points already produces cells of varying size just from the spatial
  layout, and this is treated as good enough for rank purposes rather
  than exact proportionality). Categories are zipped to cells by rank,
  generalizing Mondrian's `_assign_decades_to_rectangles` so the "label"
  is a `(decade, gender)` tuple instead of a bare decade — the largest
  cell gets the highest-count category, and so on down.

- **Color** = gender of the combination assigned to that cell. Unassigned
  cells get a neutral, undifferentiated fill.

- **Hover** = decade + artwork count only (e.g. "1960s · 42 obras").
  Gender is not repeated in the hover text since it's already
  communicated by the cell's color and the legend.

- **Legend**: Plotly doesn't auto-generate a legend for `fill='toself'`
  traces without empty rendered points, so three invisible proxy traces
  (one per gender bucket, zero-length geometry, `showlegend=True`,
  `name=<gender>`, matching fill color) are added purely to produce the
  three legend entries.

## Geometry

- **Face contours**: ~5 rough polygons (one per figure in the painting),
  hand-digitized from `images/les_demoiselles_davignon.png` the same way
  as Mondrian's rectangles — proposed as starting coordinates by Claude,
  adjusted cell-by-cell in the notebook by the user against the real
  image.
- **Seed points**: a jittered grid (fixed seed via `config.RANDOM_STATE`)
  covering the *entire* canvas — figures and background alike, per the
  user's direction that data isn't restricted to the background. Points
  falling inside a face contour are discarded before tessellation, so
  faces are never subdivided by seed density. Point count is `n_cells`
  (see Data mapping's "Cell count"), not a fixed density — the same
  `generate_seed_points(n, seed)` function, just called with a
  data-derived `n` instead of a constant default.
- **Voronoi diagram**: `scipy.spatial.Voronoi` over the surviving seed
  points. Infinite regions are bounded to the canvas rectangle (standard
  bounded-Voronoi clipping).
- **Face clipping**: every resulting cell is intersected against the face
  contours with `shapely` (`cell.difference(face_polygon)` for any face
  it overlaps), so no data cell geometrically invades a face even though
  raw Voronoi regions can extend past their generating point.
- **Faces as decoration**: face contours are drawn as flat, undivided
  fills with no hover and no ranked data — analogous to Mondrian's
  background rectangles — in the neutral face color from the palette.
  It is expected that many cells (especially ones split or shrunk by
  face clipping) will end up small or oddly shaped; this is accepted as
  a known property of a first prototype, not something to special-case
  away.
- **No extra decoration**: unlike Mondrian, no overshoot lines or
  cross-tick ornaments for this first version.

## Palette

Representational tones drawn from the painting, but functioning here as
a genuine data encoding rather than the painting's literal colors:

| Role | Color |
|---|---|
| Mujer | `#C97B63` (terracotta rose) |
| Hombre | `#6E8CA0` (grey-blue) |
| Transgénero | `#D4A24C` (golden ochre) |
| Face (decorative, no data) | `#E8DCC8` (neutral beige) |
| Plot background | `#F2EADD` (light cream, matched to the painting's overall tone) |

Added to `src/config.py` as a new `"demoiselles"` entry in `PALETTES`,
alongside the existing `"mondrian"` entry.

## Development workflow

Notebook-first, identical process to Mondrian: the user runs and verifies
every cell themselves in `notebooks/04_demoiselles_prototyping.ipynb`;
Claude prepares cells but never executes them on the user's behalf. Once
the prototype is validated end-to-end against real data, the code
graduates into `src/demoiselles_geometry.py` (face contours, seed
generation, Voronoi computation, face-clipping, cell-to-rank assignment
helpers — mirroring `src/mondrian_geometry.py`'s structure) and
`src/charts.py` gains a new `demoiselles_voronoi(df)` function alongside
the existing `mondrian_treemap(df)`.

## Dependencies

`scipy` (for `scipy.spatial.Voronoi`) and `shapely` (for polygon
clipping/difference) are added back to `requirements.txt` — both were
removed during the project reset since the old, different, weighted
Voronoi-treemap approach (`src/voronoi_treemap.py`, deleted) no longer
existed to need them.

## Testing

Same shape as Mondrian's test suite:
- `tests/test_demoiselles_geometry.py`: seed-point generation excludes
  points inside face contours (deterministic, given the fixed random
  seed); bounded-Voronoi clipping keeps all cells within canvas bounds;
  face-clipping actually removes face-overlapping area from a cell
  (synthetic fixture); rank-assignment generalizes correctly to
  `(decade, gender)` tuples, including the "Other" pooling and re-sort
  behavior already proven for Mondrian's decade-only case.
- `tests/test_charts.py`: `demoiselles_voronoi(df)` returns a
  `go.Figure`; the highest-ranked (decade, gender) combination lands on
  the largest cell; hover text contains decade + count but not gender;
  legend proxy traces exist for all three gender buckets with the
  correct colors; unassigned cells have empty hover, matching the
  `hoveron='fills'` + `text=`/`hoverinfo="text"` pattern already fixed
  for Mondrian (never `hovertemplate`, which plotly.js silently discards
  on fill hovers).

## Migration notes

No prior Demoiselles code exists in the repo (deleted in full during the
2026-08-06 project reset) — this is a fresh build, not a migration.
