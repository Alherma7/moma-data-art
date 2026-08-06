# Mondrian Real-Geometry Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. This plan is notebook-first and interactive — do NOT use subagent-driven-development, since most tasks end with a handoff to the user running notebook cells and reporting back before the next task starts.

**Goal:** Build the Mondrian chart from the painting's own digitized rectangles, prototyped and validated interactively in a notebook, then graduated into `src/` once the user confirms each piece works.

**Architecture:** A new prototyping notebook (`notebooks/03_mondrian_prototyping.ipynb`) is where the rectangle geometry, the decade-assignment logic, and the final render are built and checked cell-by-cell by the user. Only once all three are validated there does the code move into `src/mondrian_geometry.py` and `src/charts.py`, gaining proper pytest tests at that point. `notebooks/02_chart_prototyping.ipynb` then exercises the graduated version against the real dataset as the final check.

**Tech Stack:** Python, pandas, Plotly (`plotly.graph_objects`), pytest, Jupyter.

## Global Constraints

- Rectangle coordinates are normalized to [0, 1] in **plot space**: `y0=0` is the bottom of the image, `y1=1` is the top (Plotly's native axis direction — not image top-left convention).
- Only colored cells (red/blue/yellow/black) are digitized. White background is never represented as a rectangle and never carries data.
- A rectangle's fill color is always its painted color — color is never a data encoding. Only hover text carries the decade/count.
- `mondrian_treemap` renders pure vector shapes — no background image.
- Notebooks are executed by the user, never by the implementer. Every task below that touches a notebook ends with a handoff step: prepare the cell(s), stop, and wait for the user to run them and report back before starting the next task.
- Nothing here touches Demoiselles/Dance — that code no longer exists in this repo (removed in the prior cleanup pass) and is out of scope until its own future redesign.

---

### Task 1: Prototype the rectangle geometry

**Files:**
- Create: `notebooks/03_mondrian_prototyping.ipynb`

**Interfaces:**
- Produces (in-notebook, not yet in `src/`): `MONDRIAN_RECTANGLES: list[dict]` — each dict has `x0, y0, x1, y1` (floats in [0, 1]) and `color` (one of `"red"`, `"blue"`, `"yellow"`, `"black"`). Consumed by Task 2 and Task 3 (same notebook), later graduated in Task 4.

- [ ] **Step 1: Create the notebook with a title cell and a setup cell**

Markdown cell:
```markdown
# 03 - Mondrian prototyping

Build and check the digitized rectangle geometry, the decade-assignment
logic, and the final render here, cell by cell, before any of it moves
into `src/`. Nothing in this notebook is wired into the rest of the
project until Task 4 graduates the validated code.
```

Code cell:
```python
import sys
sys.path.insert(0, "..")

import plotly.graph_objects as go

from src import config

palette = config.PALETTES["mondrian"]
```

- [ ] **Step 2: Add the geometry cell**

Markdown cell:
```markdown
## Geometry

Digitized from `images/mondrian_composition.jpg`. Coordinates are
normalized to [0, 1] in plot space (y0=0 is the bottom of the image,
matching Plotly's axis direction, not image top-left convention).
```

Code cell — this is a starting point, expected to be adjusted after Step 3's visual check:
```python
MONDRIAN_RECTANGLES = [
    {"x0": 0.165, "y0": 0.55, "x1": 0.195, "y1": 0.73, "color": "yellow"},
    {"x0": 0.195, "y0": 0.55, "x1": 0.27, "y1": 0.73, "color": "red"},
    {"x0": 0.31, "y0": 0.25, "x1": 0.53, "y1": 0.55, "color": "red"},
    {"x0": 0.535, "y0": 0.55, "x1": 0.65, "y1": 0.73, "color": "yellow"},
    {"x0": 0.735, "y0": 0.65, "x1": 0.78, "y1": 0.73, "color": "blue"},
    {"x0": 0.78, "y0": 0.65, "x1": 0.83, "y1": 0.73, "color": "black"},
    {"x0": 0.65, "y0": 0.37, "x1": 0.78, "y1": 0.55, "color": "red"},
    {"x0": 0.78, "y0": 0.37, "x1": 0.80, "y1": 0.47, "color": "yellow"},
    {"x0": 0.165, "y0": 0.25, "x1": 0.27, "y1": 0.37, "color": "blue"},
    {"x0": 0.285, "y0": 0.15, "x1": 0.305, "y1": 0.55, "color": "yellow"},
    {"x0": 0.53, "y0": 0.25, "x1": 0.58, "y1": 0.37, "color": "black"},
    {"x0": 0.53, "y0": 0.15, "x1": 0.65, "y1": 0.25, "color": "blue"},
]

for rect in MONDRIAN_RECTANGLES:
    assert 0 <= rect["x0"] < rect["x1"] <= 1
    assert 0 <= rect["y0"] < rect["y1"] <= 1
    assert rect["color"] in palette
len(MONDRIAN_RECTANGLES)
```

- [ ] **Step 3: Add a visual-check cell**

```python
def rectangle_trace(rect, hovertemplate="<extra></extra>", text=None):
    x0, y0, x1, y1 = rect["x0"], rect["y0"], rect["x1"], rect["y1"]
    return go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        fill="toself",
        fillcolor=palette[rect["color"]],
        line=dict(color=palette["black"], width=2),
        mode="lines",
        hovertemplate=hovertemplate,
        text=text,
        showlegend=False,
    )

fig = go.Figure()
for rect in MONDRIAN_RECTANGLES:
    fig.add_trace(rectangle_trace(rect))
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

Do not run the notebook. Tell the user it's ready, and wait for them to run these cells and compare the render against `images/mondrian_composition.jpg`. If a rectangle is off, they adjust its coordinates in the geometry cell and re-run Step 3's cell — iterate until it reads as the source image. Do not start Task 2 until they confirm it matches.

---

### Task 2: Prototype the decade-assignment logic

**Files:**
- Modify: `notebooks/03_mondrian_prototyping.ipynb`

**Interfaces:**
- Consumes: `MONDRIAN_RECTANGLES` (Task 1, for `len()` only).
- Produces (in-notebook): `_assign_decades_to_rectangles(decade_counts: dict[str, int], n_rectangles: int) -> list[tuple[str, int] | None]` — length `n_rectangles`, rank order (largest-rectangle-first), each entry either `(decade_label, count)` or `None`. Consumed by Task 3 and graduated in Task 4.

- [ ] **Step 1: Add the assignment-logic cell**

Markdown cell:
```markdown
## Decade-to-rectangle assignment

Geometry stays fixed — assignment is rank-based, not size-based. The
largest rectangle gets the most-acquired decade, ranked on down. If there
are more decades than rectangles, the smallest decades pool into a single
"Other" entry first (then the result is re-sorted, since the pooled total
can outrank an individually-kept decade). If there are more rectangles
than decades, the smallest-ranked rectangles are left unassigned.
```

Code cell:
```python
def _assign_decades_to_rectangles(decade_counts, n_rectangles):
    items = sorted(decade_counts.items(), key=lambda kv: kv[1], reverse=True)
    if len(items) > n_rectangles:
        keep = items[: n_rectangles - 1]
        other_total = sum(count for _, count in items[n_rectangles - 1:])
        items = keep + [("Other", other_total)]
        items.sort(key=lambda kv: kv[1], reverse=True)
    assignments = list(items) + [None] * (n_rectangles - len(items))
    return assignments[:n_rectangles]
```

- [ ] **Step 2: Add an inline-check cell**

```python
# Exact match: ranks straightforwardly by count
assert _assign_decades_to_rectangles({"1990s": 50, "1960s": 100, "2000s": 20}, 3) == \
    [("1960s", 100), ("1990s", 50), ("2000s", 20)]

# More decades than rectangles: smallest pool into "Other"
assert _assign_decades_to_rectangles(
    {"1960s": 100, "1970s": 80, "1980s": 10, "1990s": 5, "2000s": 3}, 3
) == [("1960s", 100), ("1970s", 80), ("Other", 18)]

# "Other"'s pooled total can outrank individually-kept decades -- must re-sort
assert _assign_decades_to_rectangles(
    {"1960s": 50, "1970s": 40, "1980s": 30, "1990s": 25, "2000s": 20}, 3
) == [("Other", 75), ("1960s", 50), ("1970s", 40)]

# More rectangles than decades: leftover rectangles get no data
assert _assign_decades_to_rectangles({"1960s": 100, "1970s": 80}, 4) == \
    [("1960s", 100), ("1970s", 80), None, None]

print("all assignment checks passed")
```

- [ ] **Step 3: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run these two cells and confirm the checks pass and the logic reads correctly before starting Task 3.

---

### Task 3: Prototype the final render against real data

**Files:**
- Modify: `notebooks/03_mondrian_prototyping.ipynb`

**Interfaces:**
- Consumes: `MONDRIAN_RECTANGLES` (Task 1), `rectangle_trace` (Task 1, Step 3), `_assign_decades_to_rectangles` (Task 2), `data.load_raw_data`/`data.clean_artworks` (existing, produce `Decade_acquired`).
- Produces (in-notebook): `mondrian_treemap(df)` — the function graduated as-is in Task 4.

- [ ] **Step 1: Add a data-loading cell**

Markdown cell:
```markdown
## Final render, with real data
```

Code cell:
```python
from src import data

df = data.load_raw_data()
cleaned = data.clean_artworks(df)
cleaned["Decade_acquired"].value_counts()
```

- [ ] **Step 2: Add the `mondrian_treemap` cell**

```python
def mondrian_treemap(df):
    known = df[df["Decade_acquired"] != "unknown"]
    decade_counts = known["Decade_acquired"].value_counts().to_dict()

    rectangles_sorted = sorted(
        MONDRIAN_RECTANGLES,
        key=lambda r: (r["x1"] - r["x0"]) * (r["y1"] - r["y0"]),
        reverse=True,
    )
    assignments = _assign_decades_to_rectangles(decade_counts, len(rectangles_sorted))

    fig = go.Figure()
    for rect, assignment in zip(rectangles_sorted, assignments):
        if assignment is not None:
            decade, count = assignment
            hovertemplate = f"{decade}<br>%{{text}} artworks<extra></extra>"
            text = str(count)
        else:
            hovertemplate = "<extra></extra>"
            text = None
        fig.add_trace(rectangle_trace(rect, hovertemplate=hovertemplate, text=text))

    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
        showlegend=False,
        margin=dict(t=20, l=0, r=0, b=0),
    )
    return fig

mondrian_treemap(cleaned).show()
```

- [ ] **Step 3: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run these cells and confirm: hovering each rectangle shows a plausible decade and artwork count, the largest rectangle carries the most-acquired decade, and the overall shape still reads as the source composition. Do not start Task 4 until they confirm.

---

### Task 4: Graduate the validated code into `src/`

**Files:**
- Create: `src/mondrian_geometry.py`
- Create: `tests/test_mondrian_geometry.py`
- Modify: `src/charts.py` (currently just `from . import config` — add the graduated functions)
- Create: `tests/test_charts.py`

**Interfaces:**
- Consumes: the user-approved `MONDRIAN_RECTANGLES`, `_assign_decades_to_rectangles`, and `mondrian_treemap` from `notebooks/03_mondrian_prototyping.ipynb` (Tasks 1-3) — copied over, not re-derived. If the user adjusted any rectangle coordinates during Task 1's iteration, use their final values here, not the Step 2 starting point.
- Produces: `mondrian_geometry.MONDRIAN_RECTANGLES`, `charts._rectangle_trace`, `charts._assign_decades_to_rectangles`, `charts.mondrian_treemap(df) -> go.Figure`. `_assign_decades_to_rectangles` and `mondrian_treemap` keep the exact names/bodies from the notebook — a direct move. The notebook's `rectangle_trace` becomes `charts._rectangle_trace` (underscore-prefixed, private, matching the module's convention) and gains an explicit `palette` parameter instead of closing over a notebook-global — a small, deliberate adaptation, not a like-for-like copy.

- [ ] **Step 1: Write `src/mondrian_geometry.py`**

```python
# Digitized from images/mondrian_composition.jpg. Coordinates are
# normalized to [0, 1] in plot space: y0=0 is the bottom of the image,
# y1=1 is the top (Plotly's axis direction, not image top-left convention).
MONDRIAN_RECTANGLES = [
    # <-- paste the final, user-approved list from notebook Task 1 here -->
]
```

- [ ] **Step 2: Write `tests/test_mondrian_geometry.py`**

```python
from src import config, mondrian_geometry


def test_all_rectangles_have_valid_bounds():
    for rect in mondrian_geometry.MONDRIAN_RECTANGLES:
        assert 0 <= rect["x0"] < rect["x1"] <= 1
        assert 0 <= rect["y0"] < rect["y1"] <= 1


def test_all_rectangle_colors_exist_in_palette():
    palette = config.PALETTES["mondrian"]
    for rect in mondrian_geometry.MONDRIAN_RECTANGLES:
        assert rect["color"] in palette


def test_at_least_one_rectangle_of_each_primary_color():
    colors_used = {rect["color"] for rect in mondrian_geometry.MONDRIAN_RECTANGLES}
    assert {"red", "blue", "yellow", "black"} <= colors_used
```

- [ ] **Step 3: Run it**

Run: `pytest tests/test_mondrian_geometry.py -v`
Expected: PASS (3 tests)

- [ ] **Step 4: Write `src/charts.py`**

Replace the file's contents (currently just `from . import config`) with:

```python
import plotly.graph_objects as go

from . import config, mondrian_geometry


def _rectangle_trace(rect, palette, hovertemplate="<extra></extra>", text=None):
    x0, y0, x1, y1 = rect["x0"], rect["y0"], rect["x1"], rect["y1"]
    return go.Scatter(
        x=[x0, x1, x1, x0, x0],
        y=[y0, y0, y1, y1, y0],
        fill="toself",
        fillcolor=palette[rect["color"]],
        line=dict(color=palette["black"], width=2),
        mode="lines",
        hovertemplate=hovertemplate,
        text=text,
        showlegend=False,
    )


def _assign_decades_to_rectangles(decade_counts, n_rectangles):
    """Rank decades by count descending and zip them to rectangle ranks
    (rectangles are assumed pre-sorted by area descending by the caller).
    If there are more decades than rectangles, the smallest decades are
    pooled into a single "Other" entry and the result is re-sorted (the
    pooled total can outrank individually-kept decades). If there are
    more rectangles than decades, the smallest-ranked rectangles are left
    unassigned (None)."""
    items = sorted(decade_counts.items(), key=lambda kv: kv[1], reverse=True)
    if len(items) > n_rectangles:
        keep = items[: n_rectangles - 1]
        other_total = sum(count for _, count in items[n_rectangles - 1:])
        items = keep + [("Other", other_total)]
        items.sort(key=lambda kv: kv[1], reverse=True)
    assignments = list(items) + [None] * (n_rectangles - len(items))
    return assignments[:n_rectangles]


def mondrian_treemap(df):
    """Rectangles digitized from the reference Mondrian-style image
    (src/mondrian_geometry.py), rendered in their painted colors with the
    most-acquired decade assigned to the largest rectangle, ranked on
    down. Color is never a data encoding here -- only the hover text
    (decade + count) is."""
    palette = config.PALETTES["mondrian"]
    known = df[df["Decade_acquired"] != "unknown"]
    decade_counts = known["Decade_acquired"].value_counts().to_dict()

    rectangles_sorted = sorted(
        mondrian_geometry.MONDRIAN_RECTANGLES,
        key=lambda r: (r["x1"] - r["x0"]) * (r["y1"] - r["y0"]),
        reverse=True,
    )
    assignments = _assign_decades_to_rectangles(decade_counts, len(rectangles_sorted))

    fig = go.Figure()
    for rect, assignment in zip(rectangles_sorted, assignments):
        if assignment is not None:
            decade, count = assignment
            hovertemplate = f"{decade}<br>%{{text}} artworks<extra></extra>"
            text = str(count)
        else:
            hovertemplate = "<extra></extra>"
            text = None
        fig.add_trace(_rectangle_trace(rect, palette, hovertemplate=hovertemplate, text=text))

    fig.update_layout(
        plot_bgcolor=palette["background"],
        xaxis=dict(visible=False, range=[0, 1]),
        yaxis=dict(visible=False, range=[0, 1], scaleanchor="x"),
        showlegend=False,
        margin=dict(t=20, l=0, r=0, b=0),
    )
    return fig
```

- [ ] **Step 5: Write `tests/test_charts.py`**

```python
import pandas as pd
import plotly.graph_objects as go

from src import charts, mondrian_geometry


def test_assign_decades_exact_match_ranks_by_count():
    counts = {"1990s": 50, "1960s": 100, "2000s": 20}
    result = charts._assign_decades_to_rectangles(counts, 3)
    assert result == [("1960s", 100), ("1990s", 50), ("2000s", 20)]


def test_assign_decades_pools_smallest_into_other_when_too_many():
    counts = {"1960s": 100, "1970s": 80, "1980s": 10, "1990s": 5, "2000s": 3}
    result = charts._assign_decades_to_rectangles(counts, 3)
    assert result == [("1960s", 100), ("1970s", 80), ("Other", 18)]


def test_assign_decades_resorts_other_by_its_own_total():
    counts = {"1960s": 50, "1970s": 40, "1980s": 30, "1990s": 25, "2000s": 20}
    result = charts._assign_decades_to_rectangles(counts, 3)
    assert result == [("Other", 75), ("1960s", 50), ("1970s", 40)]


def test_assign_decades_leaves_leftover_rectangles_unassigned():
    counts = {"1960s": 100, "1970s": 80}
    result = charts._assign_decades_to_rectangles(counts, 4)
    assert result == [("1960s", 100), ("1970s", 80), None, None]


def test_mondrian_treemap_returns_one_trace_per_rectangle():
    df = pd.DataFrame({"Decade_acquired": ["1960s", "1970s", "1990s"]})
    fig = charts.mondrian_treemap(df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == len(mondrian_geometry.MONDRIAN_RECTANGLES)


def test_mondrian_treemap_assigns_most_acquired_decade_to_largest_rectangle():
    df = pd.DataFrame({"Decade_acquired": ["1960s"] * 5 + ["1970s"] * 2 + ["1990s"] * 1})
    fig = charts.mondrian_treemap(df)
    largest_rect = max(
        mondrian_geometry.MONDRIAN_RECTANGLES,
        key=lambda r: (r["x1"] - r["x0"]) * (r["y1"] - r["y0"]),
    )
    largest_trace = fig.data[0]
    assert largest_trace.x[0] == largest_rect["x0"]
    assert "1960s" in largest_trace.hovertemplate


def test_mondrian_treemap_unassigned_rectangles_have_empty_hover():
    df = pd.DataFrame({"Decade_acquired": ["1960s"]})
    fig = charts.mondrian_treemap(df)
    empty_hover_traces = [t for t in fig.data if t.hovertemplate == "<extra></extra>"]
    assert len(empty_hover_traces) == len(mondrian_geometry.MONDRIAN_RECTANGLES) - 1
```

- [ ] **Step 6: Run the full suite**

Run: `pytest tests/ -v`
Expected: PASS (all tests, including the pre-existing `tests/test_data.py`)

- [ ] **Step 7: Commit**

```bash
git add src/mondrian_geometry.py src/charts.py tests/test_mondrian_geometry.py tests/test_charts.py
git commit -m "feat: graduate Mondrian real-geometry chart from prototyping notebook"
```

---

### Task 5: Final validation in the chart-prototyping notebook

**Files:**
- Modify: `notebooks/02_chart_prototyping.ipynb`

**Interfaces:**
- Consumes: `charts.mondrian_treemap` (Task 4) — the existing code cell (`charts.mondrian_treemap(cleaned).show()`) already calls it; no code cell change needed.

- [ ] **Step 1: Update the Mondrian markdown cell (`cell-2`)**

Replace its content with:
```markdown
## Mondrian treemap

Inspect: hover each rectangle — does it show a plausible decade and
artwork count? Does the largest rectangle correspond to the most-acquired
decade? Does the overall shape still read as `images/mondrian_composition.jpg`?
```

- [ ] **Step 2: Hand off to the user**

Do not run the notebook. Tell the user it's ready, and wait for them to run it end to end and confirm the graduated `charts.mondrian_treemap` still behaves exactly like what they approved in the prototyping notebook.

- [ ] **Step 3: Commit**

```bash
git add notebooks/02_chart_prototyping.ipynb
git commit -m "docs: point chart-prototyping notebook at the graduated Mondrian chart"
```
