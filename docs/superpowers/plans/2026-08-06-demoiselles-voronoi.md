# Demoiselles Voronoi Implementation Plan

## Task 5 complete (2026-08-08 session)

Graduated from `notebooks/04_demoiselles_prototyping.ipynb` into
`src/demoiselles_geometry.py` (`FACE_CONTOURS`, `generate_seed_points`,
`classify_gender`, `person_gender_decade_counts`, `category_items`,
`target_fracs`, `power_diagram`, `solve_weighted_voronoi`, `clip_faces`,
`build_cells`, and the module-level `CATEGORY_ITEMS`/`DEMOISELLES_CELLS`
built once at import time from the real cleaned dataset) and
`src/charts.py::demoiselles_voronoi`, written fresh from the notebook's
actual weighted-solver + face-clipping code as flagged below — not from
this plan's Task 5 code blocks, which described the old unweighted
mechanism. `tests/test_demoiselles_geometry.py` (15 tests) and
additions to `tests/test_charts.py` (5 tests) bring the project to 42
passing tests. The graduated `charts.demoiselles_voronoi(cleaned)` was
rendered and confirmed pixel-identical to the notebook's last validated
render. Task 6 (pointing `notebooks/02_chart_prototyping.ipynb` at the
graduated function) is still open.

## Amendment 2 (2026-08-07 session, later)

The "Amendment (2026-08-07 session)" below (data-derived cell *count*,
rank-ordered cell *size*, no weighted Voronoi) was implemented, rendered,
and rejected by the user after seeing it — they want cell area genuinely
proportional to artwork count, not just correctly ordered ("si hay una
celda de 1 obra se debe de notar que es mucho más pequeña"). The
mechanism changed to a **weighted Voronoi (power) diagram** with an
iterative weight+position solver — full design rationale in
`docs/superpowers/specs/2026-08-06-demoiselles-voronoi-redesign.md`'s
"Amendment 2". This obsoletes Task 2's `bounded_voronoi_cells` (ordinary,
unweighted Voronoi) and all of Task 3 (`_assign_labels_to_cells` rank-zip
assignment) below — **that code was deleted from the notebook, not kept
alongside the new mechanism**, per this project's established practice
of physically removing superseded code rather than leaving both versions
in place. Task 4's `demoiselles_voronoi` was rewritten to consume the new
solver's per-category cells directly instead of zipping
`cells_sorted`/`_assign_labels_to_cells`. `notebooks/04_demoiselles_prototyping.ipynb`
is the authoritative source for the current implementation — the
task-by-task steps below (Amendment 1 onward) describe the design that
was superseded, kept for history, not as a script to re-run.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This plan is notebook-first and interactive — do NOT use subagent-driven-development, since most tasks end with a handoff to the user running notebook cells and reporting back before the next task starts.

**Goal:** Build the Demoiselles d'Avignon chart from a real Voronoi tessellation of the canvas, prototyped and validated interactively in a notebook, then graduated into `src/` once the user confirms each piece works.

**Architecture:** A new prototyping notebook (`notebooks/04_demoiselles_prototyping.ipynb`) is where the face contours, seed points, bounded Voronoi tessellation, face clipping, gender/decade assignment, and final render are built and checked cell-by-cell by the user. Only once all of it is validated there does the code move into `src/demoiselles_geometry.py` and `src/charts.py`, gaining proper pytest tests at that point. `notebooks/02_chart_prototyping.ipynb` then exercises the graduated version against the real dataset as the final check — same shape as the Mondrian plan (`docs/superpowers/plans/2026-08-06-mondrian-real-geometry.md`).

**Tech Stack:** Python, pandas, numpy, scipy (`scipy.spatial.Voronoi`), shapely, Plotly (`plotly.graph_objects`), pytest, Jupyter.

## Amendment (2026-08-07 session)

Task 1 (face contours + a fixed ~40-seed tessellation) was prototyped and
found not to read well: most cells ended up unassigned/neutral because
the fixed cell count rarely matched the real number of (decade, gender)
categories. New rule: **the number of data-bearing cells equals the
number of categories in the real data**, capped at `MAX_CELLS = 40` with
the smallest pooled into "Other" beyond the cap. Cell size is still not
an exact proportional/weighted-Voronoi encoding — an ordinary
tessellation over `n_cells` seed points is generated, then the
naturally-largest cells go to the highest-count categories by rank
(same principle as before, just with cell *count* now data-derived).
Practical effect: **category counts must be computed before seed points
are generated**, since `n_cells` feeds `generate_seed_points(n, seed)`.
This reorders the task sequence — gender classification and
`person_gender_decade_counts` (originally Task 3, Steps 1-2) now run
immediately after face contours (Task 1) and before the Voronoi
tessellation (Task 2), rather than after it. Face contours themselves
are unaffected — still fixed, hand-digitized, independent of data. The
user has already approved the face-contour polygons produced in Task 1
as good enough for this prototype stage; no further iteration on those
coordinates is planned right now.

## Global Constraints

- Coordinates are normalized to [0, 1] in **plot space**: `y=0` is the bottom of the image, `y=1` is the top (Plotly's native axis direction — not image top-left convention). Same convention as Mondrian.
- Face contours are fixed and independent of data. The *number* of Voronoi/data cells is data-derived (`n_cells = min(category_count, MAX_CELLS)`); their individual assignment is still rank-based, not an exact proportional encoding — same "assignment is rank-based" principle as Mondrian, just with cell count no longer fixed.
- **Unlike Mondrian, color IS a data encoding here** — a cell's fill color is the gender bucket of its assigned (decade, gender) combination. There is no "painted color" to preserve, since Cubist faceting has no consistent flat-region palette to digitize.
- Hover text is decade + count only (e.g. `"1960s<br>42 obras"`) — gender is never repeated in hover text, since it's already shown via cell color and the legend.
- Fill-hover labels MUST use `text=` + `hoverinfo="text"` with `hoveron="fills"` — **never** `hovertemplate`, which plotly.js silently discards for `hoveron='fills'` hovers (forces `hovertemplate: false` internally and falls back to trace `text`/name instead). This bug was found and fixed for Mondrian in `src/charts.py::_rectangle_trace`; the same rule applies to every new trace-building helper written here.
- Face contours are purely decorative: never subdivided by seed points, never carry data, never show hover text.
- No decorative overshoot lines or cross-ticks for this first version (unlike Mondrian).
- Notebooks are executed by the user, never by the implementer. Every task below that touches a notebook ends with a handoff step: prepare the cell(s), stop, and wait for the user to run them and report back before starting the next task.
- Nothing here touches Mondrian's existing shipped code (`src/mondrian_geometry.py`, `src/charts.py::mondrian_treemap`, their tests) — this is new, additive work living in its own module.

---

### Task 1: Dependencies, palette, face contours, and seed points

**Files:**
- Modify: `requirements.txt`
- Modify: `src/config.py`
- Create: `notebooks/04_demoiselles_prototyping.ipynb`

**Interfaces:**
- Produces: `config.PALETTES["demoiselles"]` (dict with keys `mujer`, `hombre`, `transgenero`, `face`, `background`, `black`). Produces (in-notebook, not yet in `src/`): `FACE_CONTOURS: list[list[tuple[float, float]]]` (5 rough polygons, coordinates in [0, 1] plot space), `FACE_POLYGONS: list[shapely.geometry.Polygon]`, `generate_seed_points(n, seed) -> list[tuple[float, float]]`, `SEED_POINTS: list[tuple[float, float]]`. Consumed by Task 2 and Task 3 (same notebook), later graduated in Task 5.

- [ ] **Step 1: Add scipy and shapely to `requirements.txt`**

Replace the file's contents with:
```
pandas
numpy
pillow
plotly
pyarrow
pytest
scipy
shapely
```

- [ ] **Step 2: Add the `demoiselles` palette to `src/config.py`**

Add a second entry to the existing `PALETTES` dict (after the `"mondrian"` entry, still inside the same dict literal):
```python
    "demoiselles": {
        "mujer": "#C97B63",
        "hombre": "#6E8CA0",
        "transgenero": "#D4A24C",
        "face": "#E8DCC8",
        "background": "#F2EADD",
        "black": "#111111",
    },
```

- [ ] **Step 3: Tell the user to install the new dependencies**

Do not run anything. Tell the user to run `pip install -r requirements.txt` in their environment before running any notebook cells below, since Steps 5+ import `scipy` and `shapely`.

- [ ] **Step 4: Create the notebook with a title cell and a setup cell**

Markdown cell:
```markdown
# 04 - Demoiselles prototyping

Build and check the face contours, seed points, bounded Voronoi
tessellation, face clipping, and the gender/decade assignment and final
render here, cell by cell, before any of it moves into `src/`. Nothing in
this notebook is wired into the rest of the project until Task 5
graduates the validated code.
```

Code cell:
```python
import sys
sys.path.insert(0, "..")

import numpy as np
import plotly.graph_objects as go
from shapely.geometry import Point, Polygon

from src import config

palette = config.PALETTES["demoiselles"]
```

- [ ] **Step 5: Add the face-contours cell**

Markdown cell:
```markdown
## Face contours

Rough polygons digitized from `images/les_demoiselles_davignon.png`, one
per figure. These are never subdivided by seed points and never carry
data — they render as flat decorative fills.
```

Code cell — starting point, expected to be adjusted after Step 7's visual check:
```python
FACE_CONTOURS = [
    [(0.08, 0.55), (0.20, 0.58), (0.22, 0.78), (0.15, 0.88), (0.06, 0.78), (0.05, 0.62)],
    [(0.24, 0.58), (0.36, 0.60), (0.38, 0.80), (0.30, 0.90), (0.20, 0.80), (0.22, 0.64)],
    [(0.42, 0.58), (0.54, 0.60), (0.56, 0.82), (0.47, 0.92), (0.38, 0.80), (0.40, 0.64)],
    [(0.64, 0.58), (0.76, 0.60), (0.79, 0.82), (0.70, 0.94), (0.60, 0.82), (0.62, 0.64)],
    [(0.70, 0.16), (0.84, 0.14), (0.90, 0.30), (0.82, 0.42), (0.70, 0.36), (0.66, 0.24)],
]

FACE_POLYGONS = [Polygon(points) for points in FACE_CONTOURS]

for polygon in FACE_POLYGONS:
    assert polygon.is_valid
len(FACE_POLYGONS)
```

- [ ] **Step 6: Add the seed-point generation cell**

Markdown cell:
```markdown
## Seed points

A jittered grid over the whole canvas (figures and background alike),
with points inside any face contour discarded before tessellation.
```

Code cell:
```python
def generate_seed_points(n=40, seed=config.RANDOM_STATE):
    rng = np.random.default_rng(seed)
    grid_size = int(np.ceil(np.sqrt(n * 1.5)))
    xs = np.linspace(0.03, 0.97, grid_size)
    ys = np.linspace(0.03, 0.97, grid_size)
    candidates = [(x, y) for x in xs for y in ys]
    jitter = rng.uniform(-0.03, 0.03, size=(len(candidates), 2))
    jittered = [(x + jx, y + jy) for (x, y), (jx, jy) in zip(candidates, jitter)]
    points = [
        (x, y) for x, y in jittered
        if not any(polygon.contains(Point(x, y)) for polygon in FACE_POLYGONS)
    ]
    return points[:n]

SEED_POINTS = generate_seed_points()
len(SEED_POINTS)
```

- [ ] **Step 7: Add a visual-check cell**

```python
def contour_trace(points, color):
    closed = list(points) + [points[0]]
    xs, ys = zip(*closed)
    return go.Scatter(
        x=list(xs), y=list(ys), mode="lines",
        line=dict(color=color, width=2), fill="toself",
        fillcolor=palette["face"], hoverinfo="skip", showlegend=False,
    )

fig = go.Figure()
for contour in FACE_CONTOURS:
    fig.add_trace(contour_trace(contour, palette["black"]))
fig.add_trace(go.Scatter(
    x=[p[0] for p in SEED_POINTS], y=[p[1] for p in SEED_POINTS],
    mode="markers", marker=dict(size=5, color=palette["black"]),
    showlegend=False,
))
fig.update_layout(
    plot_bgcolor=palette["background"],
    xaxis=dict(visible=False, range=[0, 1]),
    yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
    showlegend=False,
    margin=dict(t=20, l=0, r=0, b=0),
)
fig.show()
```

- [ ] **Step 8: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run these cells and compare the render against `images/les_demoiselles_davignon.png`. If a face contour is off, they adjust its coordinates in the face-contours cell and re-run Steps 6-7's cells (seed points depend on the contours, so both must re-run) — iterate until the contours read as the five figures' faces and no seed point lands inside one. Do not start Task 2 until they confirm it matches.

---

### Task 2: Prototype the bounded Voronoi tessellation and face clipping

**Files:**
- Modify: `notebooks/04_demoiselles_prototyping.ipynb`

**Interfaces:**
- Consumes: `FACE_POLYGONS` (Task 1); `data.load_raw_data`/`data.clean_artworks` (existing, produce `Decade_acquired`), the raw `Gender` column — moved up from what was originally Task 3, Steps 1-2, since seed count now depends on category count (see Amendment above).
- Produces (in-notebook): `classify_gender(raw) -> str | None`, `person_gender_decade_counts(df) -> dict[tuple[str, str], int]`, `MAX_CELLS`, `n_cells`, a re-generated `SEED_POINTS` sized to `n_cells`, `bounded_voronoi_cells(seed_points, bounds) -> list[Polygon]`, `clip_faces(cells, face_polygons) -> list[Polygon | MultiPolygon]`. Consumed by Task 3 and Task 4, later graduated in Task 5.

- [ ] **Step 0: Add gender classification, counts, and a data-sized `SEED_POINTS`**

Markdown cell:
```markdown
## Category counts (drives cell count)

The number of data-bearing Voronoi cells equals the number of (decade,
gender) categories actually present in the cleaned data, capped at
`MAX_CELLS` — categories beyond the cap are pooled into a single "Other"
entry (the final pooling/rank-assignment happens in Task 3; here we only
need the *count* to size the seed points). This must run before
`generate_seed_points`, so `SEED_POINTS` from Task 1 is regenerated here
with a data-derived `n` instead of its fixed default.
```

Code cell (gender classification, checked against the real distinct `Gender` values, same as before):
```python
def classify_gender(raw):
    if not isinstance(raw, str):
        return None
    g = raw.strip().lower()
    if "trans" in g:
        return "Transgénero"
    if g.startswith("female"):
        return "Mujer"
    if g.startswith("male"):
        return "Hombre"
    return None

assert classify_gender("male") == "Hombre"
assert classify_gender("female") == "Mujer"
assert classify_gender("female (transwoman)") == "Transgénero"
assert classify_gender("male (trans? ftm?)") == "Transgénero"
assert classify_gender("transgender woman") == "Transgénero"
assert classify_gender("") is None
assert classify_gender("non-binary") is None
assert classify_gender("gender non-conforming") is None
print("all gender classification checks passed")
```

Code cell (person-level counts, same as before):
```python
def person_gender_decade_counts(df):
    known = df[df["Decade_acquired"] != "unknown"]
    counts = {}
    for genders, decade in zip(known["Gender"], known["Decade_acquired"]):
        if not isinstance(genders, list):
            continue
        for raw in genders:
            bucket = classify_gender(raw)
            if bucket is None:
                continue
            key = (decade, bucket)
            counts[key] = counts.get(key, 0) + 1
    return counts
```

Code cell (real-data counts, cap, and a data-sized `SEED_POINTS`):
```python
from src import data

df = data.load_raw_data()
cleaned = data.clean_artworks(df)
counts = person_gender_decade_counts(cleaned)

MAX_CELLS = 40
n_cells = min(len(counts), MAX_CELLS)

SEED_POINTS = generate_seed_points(n=n_cells)
len(counts), n_cells, len(SEED_POINTS)
```

- [ ] **Step 1: Add the bounded-Voronoi cell**

Markdown cell:
```markdown
## Bounded Voronoi tessellation

`scipy.spatial.Voronoi` produces unbounded regions for points on the
convex hull. The standard fix is to mirror every seed point across all
four canvas edges before tessellating — the extra mirrored points force
every original point's region to close inside the canvas, without
distorting the interior cells. Regions are then clipped to the exact
[0, 1] x [0, 1] canvas rectangle.
```

Code cell:
```python
from scipy.spatial import Voronoi
from shapely.geometry import box

def _mirror_points(points, bounds):
    minx, miny, maxx, maxy = bounds
    mirrored = []
    for x, y in points:
        mirrored.append((2 * minx - x, y))
        mirrored.append((2 * maxx - x, y))
        mirrored.append((x, 2 * miny - y))
        mirrored.append((x, 2 * maxy - y))
    return mirrored

def bounded_voronoi_cells(seed_points, bounds=(0.0, 0.0, 1.0, 1.0)):
    all_points = list(seed_points) + _mirror_points(seed_points, bounds)
    vor = Voronoi(all_points)
    boundary = box(*bounds)
    cells = []
    for i in range(len(seed_points)):
        region = vor.regions[vor.point_region[i]]
        if not region or -1 in region:
            continue
        polygon_points = [vor.vertices[v] for v in region]
        cell = Polygon(polygon_points).intersection(boundary)
        if not cell.is_empty:
            cells.append(cell)
    return cells

RAW_CELLS = bounded_voronoi_cells(SEED_POINTS)
len(RAW_CELLS)
```

- [ ] **Step 2: Add the face-clipping cell**

Markdown cell:
```markdown
## Face clipping

Raw Voronoi regions can geometrically extend past their generating point
and overlap a nearby face, even though no seed point was placed inside
one. Every cell is intersected against any face it overlaps and the
overlapping area is subtracted, so faces stay undivided decoration.
`Polygon.difference()` can return a `MultiPolygon` when a face splits a
cell into two pieces — downstream code must handle both types.
```

Code cell:
```python
def clip_faces(cells, face_polygons):
    clipped = []
    for cell in cells:
        result = cell
        for face in face_polygons:
            if result.intersects(face):
                result = result.difference(face)
        if not result.is_empty:
            clipped.append(result)
    return clipped

DEMOISELLES_CELLS = clip_faces(RAW_CELLS, FACE_POLYGONS)
len(DEMOISELLES_CELLS)
```

- [ ] **Step 3: Add a visual-check cell**

```python
def polygon_to_traces(polygon, fillcolor, line_color, hovertext=None):
    geoms = polygon.geoms if polygon.geom_type == "MultiPolygon" else [polygon]
    traces = []
    for geom in geoms:
        xs, ys = geom.exterior.xy
        traces.append(go.Scatter(
            x=list(xs), y=list(ys),
            fill="toself", fillcolor=fillcolor,
            line=dict(color=line_color, width=2),
            mode="lines", hoveron="fills", name="",
            text=hovertext, hoverinfo="text" if hovertext else "skip",
            showlegend=False,
        ))
    return traces

fig = go.Figure()
for face in FACE_POLYGONS:
    for trace in polygon_to_traces(face, palette["face"], palette["black"]):
        fig.add_trace(trace)
for cell in DEMOISELLES_CELLS:
    for trace in polygon_to_traces(cell, palette["background"], palette["black"]):
        fig.add_trace(trace)
fig.update_layout(
    plot_bgcolor=palette["background"],
    xaxis=dict(visible=False, range=[0, 1]),
    yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
    showlegend=False,
    margin=dict(t=20, l=0, r=0, b=0),
)
fig.show()
```

- [ ] **Step 4: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run these cells and confirm: every cell stays within the canvas, no cell visibly overlaps a face, and the overall tessellation looks reasonable (some small or oddly-shaped cells near face boundaries are expected and fine). Do not start Task 3 until they confirm.

---

### Task 3: Prototype the generalized rank assignment

**Files:**
- Modify: `notebooks/04_demoiselles_prototyping.ipynb`

**Interfaces:**
- Consumes: `counts`, `n_cells` (Task 2, Step 0 — gender classification and person-level counting moved there since seed count depends on them).
- Produces (in-notebook): `_assign_labels_to_cells(counts: dict, n_cells: int) -> list[tuple[Any, int] | None]`. Consumed by Task 4, later graduated in Task 5.

- [ ] **Step 1: Add the generalized rank-assignment cell**

Markdown cell:
```markdown
## Rank assignment, generalized to (decade, gender) labels

Same rank-based logic as Mondrian's `_assign_decades_to_rectangles`, but
the label is now a `(decade, gender)` tuple instead of a bare decade
string. If a pooled "Other" entry ends up needed (more label
combinations than cells), it mixes genders by construction, so it can't
carry a single gender color — the render step (Task 4) treats it like an
unassigned cell visually (neutral fill) while still showing its pooled
count in the hover text.
```

Code cell:
```python
def _assign_labels_to_cells(counts, n_cells):
    items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    if len(items) > n_cells:
        keep = items[: n_cells - 1]
        other_total = sum(count for _, count in items[n_cells - 1:])
        items = keep + [("Other", other_total)]
        items.sort(key=lambda kv: kv[1], reverse=True)
    assignments = list(items) + [None] * (n_cells - len(items))
    return assignments[:n_cells]
```

- [ ] **Step 2: Add an inline-check cell**

```python
# Exact match: ranks straightforwardly by count, tuple labels preserved
result = _assign_labels_to_cells(
    {("1990s", "Mujer"): 50, ("1960s", "Hombre"): 100, ("2000s", "Transgénero"): 20}, 3
)
assert result == [
    (("1960s", "Hombre"), 100), (("1990s", "Mujer"), 50), (("2000s", "Transgénero"), 20)
]

# More combinations than cells: smallest pool into "Other"
result = _assign_labels_to_cells(
    {
        ("1960s", "Hombre"): 100, ("1970s", "Mujer"): 80, ("1980s", "Hombre"): 10,
        ("1990s", "Mujer"): 5, ("2000s", "Transgénero"): 3,
    },
    3,
)
assert result == [(("1960s", "Hombre"), 100), (("1970s", "Mujer"), 80), ("Other", 18)]

# More cells than combinations: leftover cells get no data
result = _assign_labels_to_cells({("1960s", "Hombre"): 100, ("1970s", "Mujer"): 80}, 4)
assert result == [(("1960s", "Hombre"), 100), (("1970s", "Mujer"), 80), None, None]

print("all assignment checks passed")
```

- [ ] **Step 3: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run these cells and confirm the assertion checks pass. `counts` was already inspected in Task 2, Step 0 (`len(counts)`, `n_cells`) — re-check those numbers still look plausible here since this cell relies on `n_cells` matching `len(counts)` up to the `MAX_CELLS` cap. Do not start Task 4 until they confirm.

---

### Task 4: Prototype the final render with real data, palette, and legend

**Files:**
- Modify: `notebooks/04_demoiselles_prototyping.ipynb`

**Interfaces:**
- Consumes: `FACE_POLYGONS` (Task 1), `DEMOISELLES_CELLS`, `polygon_to_traces` (Task 2), `person_gender_decade_counts` (Task 2, Step 0), `_assign_labels_to_cells` (Task 3), `cleaned` (Task 2, Step 0).
- Produces (in-notebook): `demoiselles_voronoi(df) -> go.Figure` — the function graduated as-is in Task 5.

- [ ] **Step 1: Add the legend-proxy cell**

Markdown cell:
```markdown
## Final render, with real data

Plotly doesn't auto-generate a legend for `fill='toself'` traces, so
three invisible proxy marker traces (one per gender bucket) are added
purely to produce the three legend entries.
```

Code cell:
```python
_GENDER_PALETTE_KEYS = {"Mujer": "mujer", "Hombre": "hombre", "Transgénero": "transgenero"}

def _legend_proxy_traces(palette):
    return [
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=palette[palette_key]),
            name=label, showlegend=True,
        )
        for label, palette_key in _GENDER_PALETTE_KEYS.items()
    ]
```

- [ ] **Step 2: Add the `demoiselles_voronoi` cell**

```python
def demoiselles_voronoi(df):
    counts = person_gender_decade_counts(df)
    cells_sorted = sorted(DEMOISELLES_CELLS, key=lambda cell: cell.area, reverse=True)
    assignments = _assign_labels_to_cells(counts, len(cells_sorted))

    fig = go.Figure()
    for face in FACE_POLYGONS:
        for trace in polygon_to_traces(face, palette["face"], palette["black"]):
            fig.add_trace(trace)

    for cell, assignment in zip(cells_sorted, assignments):
        if assignment is not None and isinstance(assignment[0], tuple):
            (decade, gender), count = assignment
            fillcolor = palette[_GENDER_PALETTE_KEYS[gender]]
            hovertext = f"{decade}<br>{count} obras"
        elif assignment is not None:
            _, count = assignment
            fillcolor = palette["face"]
            hovertext = f"Other<br>{count} obras"
        else:
            fillcolor = palette["face"]
            hovertext = None
        for trace in polygon_to_traces(cell, fillcolor, palette["black"], hovertext=hovertext):
            fig.add_trace(trace)

    for trace in _legend_proxy_traces(palette):
        fig.add_trace(trace)

    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
        showlegend=True,
        margin=dict(t=20, l=0, r=0, b=0),
    )
    return fig

demoiselles_voronoi(cleaned).show()
```

- [ ] **Step 3: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run these cells and confirm: hovering a colored cell shows a plausible decade and count (never a gender word), the legend shows all three gender entries with the right colors, the largest colored cell carries the highest-ranked (decade, gender) combination, and faces render as flat undivided decoration. Do not start Task 5 until they confirm.

---

### Task 5: Graduate the validated code into `src/`

**Note (2026-08-07 amendment):** the code blocks below still show
`SEED_POINTS`/`DEMOISELLES_CELLS` as fixed module-level constants
computed at import time — that assumption no longer holds now that seed
count depends on `n_cells` (data-derived). By the time this task is
actually reached, `demoiselles_geometry` needs a function (e.g.
`build_cells(n_cells) -> list[Polygon]`) that `charts.demoiselles_voronoi(df)`
calls after computing `counts`/`n_cells` from `df`, rather than importing
pre-computed module-level cells. Revisit these code blocks against
whatever the notebook actually looks like once Tasks 2-4 are
re-validated under the new design — don't copy them verbatim.

**Files:**
- Create: `src/demoiselles_geometry.py`
- Create: `tests/test_demoiselles_geometry.py`
- Modify: `src/charts.py` (add the graduated functions; update the top import line)
- Modify: `tests/test_charts.py` (add tests alongside the existing Mondrian tests)

**Interfaces:**
- Consumes: the user-approved `FACE_CONTOURS`, `generate_seed_points`, `bounded_voronoi_cells`, `clip_faces`, `classify_gender`, `person_gender_decade_counts` from `notebooks/04_demoiselles_prototyping.ipynb` (Tasks 1-3) — copied over, not re-derived. If the user adjusted any face-contour coordinates or the seed count during iteration, use their final values here, not the starting points shown above. `polygon_to_traces`, `_legend_proxy_traces`, `_assign_labels_to_cells`, `demoiselles_voronoi` from Tasks 2-4.
- Produces: `demoiselles_geometry.FACE_CONTOURS`, `demoiselles_geometry.FACE_POLYGONS`, `demoiselles_geometry.SEED_POINTS`, `demoiselles_geometry.DEMOISELLES_CELLS`, `charts._polygon_traces`, `charts._legend_proxy_traces`, `charts._assign_labels_to_cells`, `charts.demoiselles_voronoi(df) -> go.Figure`. The notebook's `polygon_to_traces` becomes `charts._polygon_traces` (underscore-prefixed, private, matching `_rectangle_trace`'s convention) and gains an explicit `palette` parameter instead of closing over a notebook-global — same small adaptation Mondrian's graduation made.

- [ ] **Step 1: Write `src/demoiselles_geometry.py`**

```python
import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Point, Polygon, box

from . import config

# Digitized from images/les_demoiselles_davignon.png. Coordinates are
# normalized to [0, 1] in plot space: y=0 is the bottom of the image,
# y=1 is the top (Plotly's axis direction, not image top-left convention).
FACE_CONTOURS = [
    # <-- paste the final, user-approved list from notebook Task 1 here -->
]

FACE_POLYGONS = [Polygon(points) for points in FACE_CONTOURS]


def generate_seed_points(n=40, seed=config.RANDOM_STATE):
    """Jittered grid over the whole canvas, with points inside any face
    contour discarded before tessellation."""
    rng = np.random.default_rng(seed)
    grid_size = int(np.ceil(np.sqrt(n * 1.5)))
    xs = np.linspace(0.03, 0.97, grid_size)
    ys = np.linspace(0.03, 0.97, grid_size)
    candidates = [(x, y) for x in xs for y in ys]
    jitter = rng.uniform(-0.03, 0.03, size=(len(candidates), 2))
    jittered = [(x + jx, y + jy) for (x, y), (jx, jy) in zip(candidates, jitter)]
    points = [
        (x, y) for x, y in jittered
        if not any(polygon.contains(Point(x, y)) for polygon in FACE_POLYGONS)
    ]
    return points[:n]


def _mirror_points(points, bounds):
    minx, miny, maxx, maxy = bounds
    mirrored = []
    for x, y in points:
        mirrored.append((2 * minx - x, y))
        mirrored.append((2 * maxx - x, y))
        mirrored.append((x, 2 * miny - y))
        mirrored.append((x, 2 * maxy - y))
    return mirrored


def bounded_voronoi_cells(seed_points, bounds=(0.0, 0.0, 1.0, 1.0)):
    """Voronoi cells for seed_points, closed inside bounds. Mirrors every
    point across all four canvas edges before tessellating so every
    original point's region is finite, then clips to the exact canvas
    rectangle."""
    all_points = list(seed_points) + _mirror_points(seed_points, bounds)
    vor = Voronoi(all_points)
    boundary = box(*bounds)
    cells = []
    for i in range(len(seed_points)):
        region = vor.regions[vor.point_region[i]]
        if not region or -1 in region:
            continue
        polygon_points = [vor.vertices[v] for v in region]
        cell = Polygon(polygon_points).intersection(boundary)
        if not cell.is_empty:
            cells.append(cell)
    return cells


def clip_faces(cells, face_polygons):
    """Subtract any overlapping face contour from each cell. Polygon.difference()
    can return a MultiPolygon when a face splits a cell -- callers must
    handle both Polygon and MultiPolygon."""
    clipped = []
    for cell in cells:
        result = cell
        for face in face_polygons:
            if result.intersects(face):
                result = result.difference(face)
        if not result.is_empty:
            clipped.append(result)
    return clipped


def classify_gender(raw):
    """Bucket a raw MoMA Gender string into Mujer/Hombre/Transgenero, or
    None if it doesn't fit any of the three (checked against the real
    distinct values in data/raw/Artworks.json -- contains-trans is
    checked before the prefix checks so values like "female
    (transwoman)" land in Transgenero, not Mujer)."""
    if not isinstance(raw, str):
        return None
    g = raw.strip().lower()
    if "trans" in g:
        return "Transgénero"
    if g.startswith("female"):
        return "Mujer"
    if g.startswith("male"):
        return "Hombre"
    return None


def person_gender_decade_counts(df):
    """Count (decade, gender) combinations per credited person (Gender is
    a list per artwork, one entry per credited person) on known-decade
    artworks."""
    known = df[df["Decade_acquired"] != "unknown"]
    counts = {}
    for genders, decade in zip(known["Gender"], known["Decade_acquired"]):
        if not isinstance(genders, list):
            continue
        for raw in genders:
            bucket = classify_gender(raw)
            if bucket is None:
                continue
            key = (decade, bucket)
            counts[key] = counts.get(key, 0) + 1
    return counts


SEED_POINTS = generate_seed_points()
DEMOISELLES_CELLS = clip_faces(bounded_voronoi_cells(SEED_POINTS), FACE_POLYGONS)
```

- [ ] **Step 2: Write `tests/test_demoiselles_geometry.py`**

```python
import math

from shapely.geometry import Point, Polygon, box

from src import demoiselles_geometry as geo


def test_face_polygons_are_valid():
    for polygon in geo.FACE_POLYGONS:
        assert polygon.is_valid


def test_seed_points_exclude_face_interiors():
    for x, y in geo.SEED_POINTS:
        for polygon in geo.FACE_POLYGONS:
            assert not polygon.contains(Point(x, y))


def test_generate_seed_points_is_deterministic():
    first = geo.generate_seed_points(n=20, seed=7)
    second = geo.generate_seed_points(n=20, seed=7)
    assert first == second


def test_bounded_voronoi_cells_stay_within_bounds():
    seed_points = [(0.2, 0.2), (0.8, 0.2), (0.5, 0.8), (0.3, 0.6), (0.7, 0.5)]
    cells = geo.bounded_voronoi_cells(seed_points)
    boundary = box(0.0, 0.0, 1.0, 1.0)
    for cell in cells:
        assert boundary.contains(cell) or math.isclose(cell.area, cell.intersection(boundary).area)


def test_clip_faces_removes_overlapping_area():
    cell = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    face = Polygon([(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)])
    clipped = geo.clip_faces([cell], [face])
    assert len(clipped) == 1
    assert clipped[0].area < cell.area
    assert math.isclose(clipped[0].area, cell.area - face.area)


def test_clip_faces_drops_cells_fully_covered_by_a_face():
    cell = Polygon([(0.4, 0.4), (0.5, 0.4), (0.5, 0.5), (0.4, 0.5)])
    face = Polygon([(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)])
    clipped = geo.clip_faces([cell], [face])
    assert clipped == []


def test_classify_gender_buckets_real_observed_values():
    assert geo.classify_gender("male") == "Hombre"
    assert geo.classify_gender("female") == "Mujer"
    assert geo.classify_gender("female (transwoman)") == "Transgénero"
    assert geo.classify_gender("male (trans? ftm?)") == "Transgénero"
    assert geo.classify_gender("transgender woman") == "Transgénero"


def test_classify_gender_discards_non_bucket_values():
    assert geo.classify_gender("") is None
    assert geo.classify_gender("non-binary") is None
    assert geo.classify_gender("gender non-conforming") is None
    assert geo.classify_gender(None) is None


def test_person_gender_decade_counts_counts_per_person():
    import pandas as pd

    df = pd.DataFrame({
        "Gender": [["male", "female"], ["male"], ["unknown-value"]],
        "Decade_acquired": ["1960s", "1960s", "1970s"],
    })
    counts = geo.person_gender_decade_counts(df)
    assert counts == {("1960s", "Hombre"): 2, ("1960s", "Mujer"): 1}
```

- [ ] **Step 3: Run it**

Run: `pytest tests/test_demoiselles_geometry.py -v`
Expected: PASS (9 tests)

- [ ] **Step 4: Update `src/charts.py`**

Add `demoiselles_geometry` to the top import line:
```python
from . import config, mondrian_geometry, demoiselles_geometry
```

Append these functions at the end of the file:
```python
def _polygon_traces(polygon, fillcolor, palette, hovertext=None):
    """Renders a shapely Polygon or MultiPolygon as one or more filled
    Plotly traces. Hover is driven by hoveron='fills' so the whole
    interior is hoverable; plotly.js ignores hovertemplate on fill
    hovers, so the label must be a scalar text with hoverinfo='text' (see
    _rectangle_trace above)."""
    geoms = polygon.geoms if polygon.geom_type == "MultiPolygon" else [polygon]
    traces = []
    for geom in geoms:
        xs, ys = geom.exterior.xy
        traces.append(go.Scatter(
            x=list(xs), y=list(ys),
            fill="toself", fillcolor=fillcolor,
            line=dict(color=palette["black"], width=2),
            mode="lines", hoveron="fills", name="",
            text=hovertext, hoverinfo="text" if hovertext else "skip",
            showlegend=False,
        ))
    return traces


_GENDER_PALETTE_KEYS = {"Mujer": "mujer", "Hombre": "hombre", "Transgénero": "transgenero"}


def _legend_proxy_traces(palette):
    """Invisible marker traces used only to produce legend entries --
    Plotly doesn't auto-generate a legend for fill='toself' traces."""
    return [
        go.Scatter(
            x=[None], y=[None], mode="markers",
            marker=dict(size=10, color=palette[palette_key]),
            name=label, showlegend=True,
        )
        for label, palette_key in _GENDER_PALETTE_KEYS.items()
    ]


def _assign_labels_to_cells(counts, n_cells):
    """Same rank-based logic as _assign_decades_to_rectangles, generalized
    to any hashable label (here, (decade, gender) tuples). A pooled
    "Other" entry mixes genders by construction and has no single color;
    callers render it like an unassigned cell but keep its pooled count
    in the hover text."""
    items = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    if len(items) > n_cells:
        keep = items[: n_cells - 1]
        other_total = sum(count for _, count in items[n_cells - 1:])
        items = keep + [("Other", other_total)]
        items.sort(key=lambda kv: kv[1], reverse=True)
    assignments = list(items) + [None] * (n_cells - len(items))
    return assignments[:n_cells]


def demoiselles_voronoi(df):
    """Voronoi cells tessellated over images/les_demoiselles_davignon.png
    (src/demoiselles_geometry.py), with faces clipped out as undivided
    decoration. Unlike mondrian_treemap, color IS a data encoding here:
    the most-acquired (decade, gender) combination is assigned to the
    largest cell, ranked on down, and the cell's fill color is that
    combination's gender. Hover shows decade + count only -- gender is
    already shown via color and the legend."""
    palette = config.PALETTES["demoiselles"]
    counts = demoiselles_geometry.person_gender_decade_counts(df)
    cells_sorted = sorted(
        demoiselles_geometry.DEMOISELLES_CELLS, key=lambda cell: cell.area, reverse=True
    )
    assignments = _assign_labels_to_cells(counts, len(cells_sorted))

    fig = go.Figure()
    for face in demoiselles_geometry.FACE_POLYGONS:
        for trace in _polygon_traces(face, palette["face"], palette):
            fig.add_trace(trace)

    for cell, assignment in zip(cells_sorted, assignments):
        if assignment is not None and isinstance(assignment[0], tuple):
            (decade, gender), count = assignment
            fillcolor = palette[_GENDER_PALETTE_KEYS[gender]]
            hovertext = f"{decade}<br>{count} obras"
        elif assignment is not None:
            _, count = assignment
            fillcolor = palette["face"]
            hovertext = f"Other<br>{count} obras"
        else:
            fillcolor = palette["face"]
            hovertext = None
        for trace in _polygon_traces(cell, fillcolor, palette, hovertext=hovertext):
            fig.add_trace(trace)

    for trace in _legend_proxy_traces(palette):
        fig.add_trace(trace)

    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
        showlegend=True,
        margin=dict(t=20, l=0, r=0, b=0),
    )
    return fig
```

- [ ] **Step 5: Add tests to `tests/test_charts.py`**

Append these, keeping the existing Mondrian tests and imports as-is (add `demoiselles_geometry` to the existing `from src import charts, mondrian_geometry` line):
```python
def test_assign_labels_to_cells_handles_tuple_labels():
    counts = {("1990s", "Mujer"): 50, ("1960s", "Hombre"): 100, ("2000s", "Transgénero"): 20}
    result = charts._assign_labels_to_cells(counts, 3)
    assert result == [
        (("1960s", "Hombre"), 100), (("1990s", "Mujer"), 50), (("2000s", "Transgénero"), 20)
    ]


def test_assign_labels_to_cells_pools_smallest_into_other():
    counts = {
        ("1960s", "Hombre"): 100, ("1970s", "Mujer"): 80, ("1980s", "Hombre"): 10,
        ("1990s", "Mujer"): 5, ("2000s", "Transgénero"): 3,
    }
    result = charts._assign_labels_to_cells(counts, 3)
    assert result == [(("1960s", "Hombre"), 100), (("1970s", "Mujer"), 80), ("Other", 18)]


def test_demoiselles_voronoi_returns_figure():
    df = pd.DataFrame({
        "Gender": [["male"], ["female"], ["male", "female (transwoman)"]],
        "Decade_acquired": ["1960s", "1960s", "1970s"],
    })
    fig = charts.demoiselles_voronoi(df)
    assert isinstance(fig, go.Figure)


def test_demoiselles_voronoi_assigns_top_combination_to_largest_cell():
    df = pd.DataFrame({
        "Gender": [["male"]] * 10 + [["female"]] * 3,
        "Decade_acquired": ["1960s"] * 10 + ["1970s"] * 3,
    })
    fig = charts.demoiselles_voronoi(df)
    largest_cell = max(demoiselles_geometry.DEMOISELLES_CELLS, key=lambda cell: cell.area)
    n_faces = len(demoiselles_geometry.FACE_POLYGONS)
    largest_trace = fig.data[n_faces]
    assert largest_trace.x[0] == pytest.approx(list(largest_cell.exterior.xy[0])[0])
    assert "1960s" in largest_trace.text


def test_demoiselles_voronoi_hover_never_contains_a_gender_word():
    df = pd.DataFrame({
        "Gender": [["male"]] * 10 + [["female"]] * 3,
        "Decade_acquired": ["1960s"] * 10 + ["1970s"] * 3,
    })
    fig = charts.demoiselles_voronoi(df)
    for trace in fig.data:
        if trace.hoverinfo == "text" and trace.text:
            assert "Mujer" not in trace.text
            assert "Hombre" not in trace.text
            assert "Transgénero" not in trace.text


def test_demoiselles_voronoi_legend_has_three_gender_entries():
    df = pd.DataFrame({"Gender": [["male"]], "Decade_acquired": ["1960s"]})
    fig = charts.demoiselles_voronoi(df)
    legend_traces = [t for t in fig.data if t.showlegend]
    legend_names = {t.name for t in legend_traces}
    assert legend_names == {"Mujer", "Hombre", "Transgénero"}
    for trace in legend_traces:
        expected_color = config.PALETTES["demoiselles"][charts._GENDER_PALETTE_KEYS[trace.name]]
        assert trace.marker.color == expected_color


def test_demoiselles_voronoi_labels_fill_hover_via_text_not_hovertemplate():
    df = pd.DataFrame({"Gender": [["male"]], "Decade_acquired": ["1960s"]})
    fig = charts.demoiselles_voronoi(df)
    for trace in fig.data:
        if trace.hoveron == "fills":
            assert trace.hovertemplate is None
```

Add the missing imports at the top of the file (alongside the existing ones):
```python
import pytest

from src import charts, config, demoiselles_geometry, mondrian_geometry
```

- [ ] **Step 6: Run the full suite**

Run: `pytest tests/ -v`
Expected: PASS (all tests, including the pre-existing Mondrian and data tests)

- [ ] **Step 7: Commit**

```bash
git add requirements.txt src/config.py src/demoiselles_geometry.py src/charts.py tests/test_demoiselles_geometry.py tests/test_charts.py
git commit -m "feat: graduate Demoiselles Voronoi chart from prototyping notebook"
```

---

### Task 6: Final validation in the chart-prototyping notebook

**Files:**
- Modify: `notebooks/02_chart_prototyping.ipynb`

**Interfaces:**
- Consumes: `charts.demoiselles_voronoi` (Task 5).

- [ ] **Step 1: Add a code cell calling the graduated function**

Insert before the existing `## Findings` markdown cell:
```python
charts.demoiselles_voronoi(cleaned).show()
```

- [ ] **Step 2: Add a markdown cell above it**

```markdown
## Demoiselles Voronoi

Inspect: hovering a colored cell shows a plausible decade and count
(never a gender word), the legend shows all three gender entries, the
largest colored cell carries the highest-ranked (decade, gender)
combination, and faces render as flat undivided decoration matching
`images/les_demoiselles_davignon.png`.
```

- [ ] **Step 3: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run it end to end and confirm the graduated `charts.demoiselles_voronoi` still behaves exactly like what they approved in the prototyping notebook.

- [ ] **Step 4: Commit**

```bash
git add notebooks/02_chart_prototyping.ipynb
git commit -m "docs: point chart-prototyping notebook at the graduated Demoiselles chart"
```
