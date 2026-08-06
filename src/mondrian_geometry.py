import random

from . import config

# Digitized from images/mondrian_composition.jpg. Coordinates are
# normalized to [0, 1] in plot space: y0=0 is the bottom of the image,
# y1=1 is the top (Plotly's axis direction, not image top-left convention).
MONDRIAN_RECTANGLES = [
    {"x0": 0.15, "y0": 0.65, "x1": 0.20, "y1": 0.75, "color": "yellow"},
    {"x0": 0.20, "y0": 0.55, "x1": 0.25, "y1": 0.75, "color": "red"},
    {"x0": 0.30, "y0": 0.25, "x1": 0.55, "y1": 0.55, "color": "red"},
    {"x0": 0.55, "y0": 0.55, "x1": 0.65, "y1": 0.75, "color": "yellow"},
    {"x0": 0.75, "y0": 0.65, "x1": 0.80, "y1": 0.75, "color": "blue"},
    {"x0": 0.80, "y0": 0.65, "x1": 0.85, "y1": 0.75, "color": "black"},
    {"x0": 0.65, "y0": 0.35, "x1": 0.80, "y1": 0.55, "color": "red"},
    {"x0": 0.80, "y0": 0.35, "x1": 0.85, "y1": 0.45, "color": "yellow"},
    {"x0": 0.15, "y0": 0.25, "x1": 0.25, "y1": 0.35, "color": "blue"},
    {"x0": 0.25, "y0": 0.25, "x1": 0.30, "y1": 0.55, "color": "yellow"},
    {"x0": 0.55, "y0": 0.25, "x1": 0.60, "y1": 0.35, "color": "black"},
    {"x0": 0.55, "y0": 0.15, "x1": 0.65, "y1": 0.25, "color": "blue"},
    {"x0": 0.25, "y0": 0.15, "x1": 0.30, "y1": 0.25, "color": "yellow"},
]

MIN_ARM_GAP = 0.03  # minimum remaining length beyond a cross tick's crossing point


def fill_background_cells(rectangles):
    """Merge the free (non-colored) grid cells implied by rectangles'
    edges into the fewest possible background rectangles -- greedy
    maximal-rectangle tiling, so dividing lines only appear where a
    colored rectangle's real edge forces them."""
    xs = sorted({r["x0"] for r in rectangles} | {r["x1"] for r in rectangles})
    ys = sorted({r["y0"] for r in rectangles} | {r["y1"] for r in rectangles})
    n_cols, n_rows = len(xs) - 1, len(ys) - 1

    def is_covered(cx, cy):
        return any(r["x0"] <= cx <= r["x1"] and r["y0"] <= cy <= r["y1"] for r in rectangles)

    free = {}
    for i in range(n_cols):
        for j in range(n_rows):
            cx_mid = (xs[i] + xs[i + 1]) / 2
            cy_mid = (ys[j] + ys[j + 1]) / 2
            free[(i, j)] = not is_covered(cx_mid, cy_mid)

    merged = []
    for j in range(n_rows):
        i = 0
        while i < n_cols:
            if not free[(i, j)]:
                i += 1
                continue

            i_end = i
            while i_end + 1 < n_cols and free[(i_end + 1, j)]:
                i_end += 1

            j_end = j
            while j_end + 1 < n_rows and all(free[(k, j_end + 1)] for k in range(i, i_end + 1)):
                j_end += 1

            for jj in range(j, j_end + 1):
                for ii in range(i, i_end + 1):
                    free[(ii, jj)] = False

            merged.append({
                "x0": xs[i], "y0": ys[j],
                "x1": xs[i_end + 1], "y1": ys[j_end + 1],
                "color": "background",
            })
            i = i_end + 1
    return merged


def line_overshoots(colored, seed, min_extra=0.08, max_extra=0.20):
    """Every internal grid line that reaches the top/bottom/left/right
    edge of the whole composition gets a short stroke continuing past
    that edge, with a random extra length. Each overshoot is a dict, not
    a raw point pair: {orientation, fixed, edge, tip}. "vertical" means
    x is fixed and edge/tip are y values (a top/bottom overshoot);
    "horizontal" means y is fixed and edge/tip are x values (a
    left/right overshoot). Only a colored rectangle's own edge (never a
    background cell's) that reaches the perimeter produces a stroke."""
    rng = random.Random(seed)
    xs = sorted({r["x0"] for r in colored} | {r["x1"] for r in colored})
    ys = sorted({r["y0"] for r in colored} | {r["y1"] for r in colored})
    x_min, x_max = xs[0], xs[-1]
    y_min, y_max = ys[0], ys[-1]

    lines = []
    for x in xs[1:-1]:
        if any(r["y1"] == y_max and x in (r["x0"], r["x1"]) for r in colored):
            lines.append({"orientation": "vertical", "fixed": x,
                           "edge": y_max, "tip": y_max + rng.uniform(min_extra, max_extra)})
        if any(r["y0"] == y_min and x in (r["x0"], r["x1"]) for r in colored):
            lines.append({"orientation": "vertical", "fixed": x,
                           "edge": y_min, "tip": y_min - rng.uniform(min_extra, max_extra)})
    for y in ys[1:-1]:
        if any(r["x0"] == x_min and y in (r["y0"], r["y1"]) for r in colored):
            lines.append({"orientation": "horizontal", "fixed": y,
                           "edge": x_min, "tip": x_min - rng.uniform(min_extra, max_extra)})
        if any(r["x1"] == x_max and y in (r["y0"], r["y1"]) for r in colored):
            lines.append({"orientation": "horizontal", "fixed": y,
                           "edge": x_max, "tip": x_max + rng.uniform(min_extra, max_extra)})
    return lines


def line_length(line):
    return abs(line["tip"] - line["edge"])


def line_segment(line):
    """A line dict's two endpoints as ((x0, y0), (x1, y1))."""
    a, b = line["edge"], line["tip"]
    if line["orientation"] == "vertical":
        return (line["fixed"], a), (line["fixed"], b)
    return (a, line["fixed"]), (b, line["fixed"])


def free_cross_ticks(lines):
    """Deterministic: each tick's base is the longest line of its own
    orientation (one vertical, one horizontal); its reference is the
    longest line -- any orientation -- that's shorter than the base by
    at least MIN_ARM_GAP (so the arm beyond the crossing point is always
    long enough to read as a "+", not a "T"). The tick crosses the base
    at a distance from its edge equal to the reference's length, and the
    tick's own length is the reference's length too."""

    def make_tick(orientation):
        same_orientation = [l for l in lines if l["orientation"] == orientation]
        if not same_orientation:
            return None
        base = max(same_orientation, key=line_length)
        base_len = line_length(base)
        candidates = [
            l for l in lines
            if l is not base and line_length(l) <= base_len - MIN_ARM_GAP
        ]
        if not candidates:
            return None
        reference = max(candidates, key=line_length)
        ref_len = line_length(reference)
        direction = 1 if base["tip"] >= base["edge"] else -1
        cross_at = base["edge"] + ref_len * direction
        return {
            "orientation": "horizontal" if orientation == "vertical" else "vertical",
            "fixed": cross_at,
            "edge": base["fixed"] - ref_len / 2,
            "tip": base["fixed"] + ref_len / 2,
        }

    return [t for t in (make_tick("vertical"), make_tick("horizontal")) if t is not None]


def _on_colored_boundary(x, y, colored):
    for r in colored:
        on_vertical_edge = x in (r["x0"], r["x1"]) and r["y0"] <= y <= r["y1"]
        on_horizontal_edge = y in (r["y0"], r["y1"]) and r["x0"] <= x <= r["x1"]
        if on_vertical_edge or on_horizontal_edge:
            return True
    return False


def _shrink_segment(start, end, gap_at_start, gap_at_end):
    (x0, y0), (x1, y1) = start, end
    dx, dy = x1 - x0, y1 - y0
    length = (dx ** 2 + dy ** 2) ** 0.5
    if length == 0:
        return start, end
    ux, uy = dx / length, dy / length
    new_start = (x0 + ux * gap_at_start, y0 + uy * gap_at_start)
    new_end = (x1 - ux * gap_at_end, y1 - uy * gap_at_end)
    return new_start, new_end


def background_edge_segments(rect, colored, gap_fraction=1 / 2):
    """A background rectangle's 4 edges, each pulled back at a corner
    that isn't touched by any colored rectangle's boundary -- an "open"
    corner instead of a fully joined one."""
    x0, y0, x1, y1 = rect["x0"], rect["y0"], rect["x1"], rect["y1"]
    corners = {"bl": (x0, y0), "br": (x1, y0), "tr": (x1, y1), "tl": (x0, y1)}
    open_corner = {
        name: not _on_colored_boundary(x, y, colored) for name, (x, y) in corners.items()
    }

    edges = [
        (corners["bl"], corners["br"], "bl", "br"),
        (corners["br"], corners["tr"], "br", "tr"),
        (corners["tr"], corners["tl"], "tr", "tl"),
        (corners["tl"], corners["bl"], "tl", "bl"),
    ]
    segments = []
    for start, end, start_name, end_name in edges:
        length = ((end[0] - start[0]) ** 2 + (end[1] - start[1]) ** 2) ** 0.5
        gap_start = length * gap_fraction if open_corner[start_name] else 0
        gap_end = length * gap_fraction if open_corner[end_name] else 0
        segments.append(_shrink_segment(start, end, gap_start, gap_end))
    return segments


MONDRIAN_BACKGROUND_RECTANGLES = fill_background_cells(MONDRIAN_RECTANGLES)
MONDRIAN_LINE_OVERSHOOTS = line_overshoots(MONDRIAN_RECTANGLES, seed=config.RANDOM_STATE)
MONDRIAN_CROSS_TICKS = free_cross_ticks(MONDRIAN_LINE_OVERSHOOTS)
