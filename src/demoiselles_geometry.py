from collections import defaultdict

import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import MultiPoint, Point, Polygon, box

from . import config, data

# Digitized from images/les_demoiselles_davignon.png. Coordinates are
# normalized to [0, 1] in plot space: y=0 is the bottom of the image,
# y=1 is the top (Plotly's axis direction, not image top-left convention).
FACE_CONTOURS = [
    [(0.20, 0.70), (0.25, 0.70), (0.30, 0.80), (0.25, 0.90), (0.20, 0.85), (0.15, 0.80)],
    [(0.35, 0.65), (0.45, 0.65), (0.45, 0.80), (0.40, 0.85), (0.35, 0.80), (0.30, 0.70)],
    [(0.50, 0.75), (0.55, 0.70), (0.60, 0.80), (0.60, 0.90), (0.50, 0.95), (0.45, 0.85)],
    [(0.75, 0.75), (0.85, 0.80), (0.90, 0.90), (0.80, 0.95), (0.75, 0.90), (0.70, 0.80)],
    [(0.75, 0.45), (0.85, 0.45), (0.90, 0.60), (0.85, 0.65), (0.75, 0.65), (0.70, 0.55)],
]

FACE_POLYGONS = [Polygon(points) for points in FACE_CONTOURS]

MAX_CELLS = 40
MIN_FRAC = 0.01  # floors each category's target area share so the smallest
# categories don't vanish under real data's ~44,000x count range


def generate_seed_points(n=40, seed=config.RANDOM_STATE):
    """Jittered grid over the whole canvas, with points inside any face
    contour discarded before tessellation. These are only a well-spread
    initial layout for the weighted-Voronoi solver's anchors -- it moves
    them during its position-relaxation step, so they don't need to be
    final."""
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
    # candidates are built in x-major grid order, so truncating to n without
    # shuffling first would systematically drop whichever columns come last
    # (e.g. the whole right edge of the canvas) instead of sampling evenly
    rng.shuffle(points)
    return points[:n]


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


def category_items(df):
    """(decade, gender) categories present in df, ranked by count
    descending -- fixes the index <-> category mapping used to size and
    label every cell (anchors, target areas, and the final render are
    all indexed the same way)."""
    counts = person_gender_decade_counts(df)
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)


def target_fracs(items, min_frac=MIN_FRAC):
    """Each category's target cell-area share, floored at min_frac -- a
    deliberate, known departure from exact proportionality for the
    smallest categories, matching the reference layout where even the
    smallest labeled regions stay visible slivers."""
    total = sum(count for _, count in items)
    raw = np.array([count / total for _, count in items])
    floored = np.maximum(raw, min_frac)
    return floored / floored.sum()


def _power_center(p1, w1, p2, w2, p3, w3):
    """The point equidistant, in power-distance, from all 3 weighted
    sites -- the power-diagram analogue of a circumcenter. Solves a 2x2
    linear system derived by subtracting the power-distance equations
    pairwise (the quadratic terms cancel)."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    A = np.array([[2 * (x2 - x1), 2 * (y2 - y1)], [2 * (x3 - x1), 2 * (y3 - y1)]])
    b = np.array([
        (w1 - w2) + (x2**2 - x1**2) + (y2**2 - y1**2),
        (w1 - w3) + (x3**2 - x1**2) + (y3**2 - y1**2),
    ])
    if abs(np.linalg.det(A)) < 1e-12:
        return None
    return tuple(np.linalg.solve(A, b))


def _mirror_weighted(points, weights, bounds):
    minx, miny, maxx, maxy = bounds
    mirrored_points, mirrored_weights = [], []
    for (x, y), w in zip(points, weights):
        mirrored_points += [(2 * minx - x, y), (2 * maxx - x, y), (x, 2 * miny - y), (x, 2 * maxy - y)]
        mirrored_weights += [w, w, w, w]
    return mirrored_points, mirrored_weights


def power_diagram(points, weights, bounds=(0.0, 0.0, 1.0, 1.0)):
    """Power/Laguerre-Voronoi diagram of weighted sites, closed inside
    bounds via the same mirror-across-every-edge trick used for an
    ordinary bounded Voronoi diagram. Computed via the standard
    lift-to-paraboloid trick: lift each site to
    (x, y, x^2+y^2-w), take the convex hull, keep the lower-hull facets,
    and solve each lower-hull triangle's power center. A site's cell is
    the convex hull of every power center from a triangle containing it
    (power cells are always convex, so no angular sorting is needed).
    Returns {site_index: Polygon}, omitting any site whose cell vanished
    (fewer than 3 power-center vertices)."""
    n = len(points)
    mirror_points, mirror_weights = _mirror_weighted(points, weights, bounds)
    all_points = list(points) + mirror_points
    all_weights = list(weights) + mirror_weights
    lifted = np.array([[x, y, x * x + y * y - w] for (x, y), w in zip(all_points, all_weights)])
    hull = ConvexHull(lifted)
    lower_hull = hull.simplices[hull.equations[:, 2] < -1e-9]

    site_vertices = defaultdict(list)
    for i, j, k in lower_hull:
        center = _power_center(
            all_points[i], all_weights[i], all_points[j], all_weights[j], all_points[k], all_weights[k]
        )
        if center is None:
            continue
        for site in (i, j, k):
            site_vertices[site].append(center)

    boundary = box(*bounds)
    cells = {}
    for i in range(n):
        vertices = site_vertices.get(i)
        if not vertices or len(vertices) < 3:
            continue
        hull_polygon = MultiPoint(vertices).convex_hull
        if hull_polygon.geom_type != "Polygon":
            continue
        cell = hull_polygon.intersection(boundary)
        if not cell.is_empty and cell.geom_type == "Polygon":
            cells[i] = cell
    return cells


def solve_weighted_voronoi(
    anchors, target_fracs, face_polygons, bounds=(0.0, 0.0, 1.0, 1.0),
    iterations=250, weight_lr=0.4, move_lr=0.15,
):
    """Iteratively adjusts each site's weight (to push its cell area
    toward target_fracs) and position (partial Lloyd relaxation toward
    its own cell centroid, skipped if that centroid falls inside a face
    contour). Weight adjustment alone leaves some cells stuck far from
    target when their fixed position is geometrically boxed in by
    neighbors; moving positions alongside weights fixes that. Returns
    (cells, weights, positions)."""
    n = len(anchors)
    positions = [tuple(p) for p in anchors]
    weights = np.zeros(n)
    total_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])

    for _ in range(iterations):
        cells = power_diagram(positions, weights, bounds)
        areas = np.array([cells[i].area if i in cells else 0.0 for i in range(n)])
        error = target_fracs - areas / total_area
        weights = weights + weight_lr * error
        weights -= weights.mean()  # power diagrams are invariant to a global weight shift

        new_positions = []
        for i in range(n):
            cell = cells.get(i)
            if cell is None or cell.is_empty:
                new_positions.append(positions[i])
                continue
            cx, cy = cell.centroid.x, cell.centroid.y
            if any(face.contains(Point(cx, cy)) for face in face_polygons):
                new_positions.append(positions[i])
                continue
            ox, oy = positions[i]
            nx = min(max(ox + move_lr * (cx - ox), 0.01), 0.99)
            ny = min(max(oy + move_lr * (cy - oy), 0.01), 0.99)
            new_positions.append((nx, ny))
        positions = new_positions

    return power_diagram(positions, weights, bounds), weights, positions


def clip_faces(cells, face_polygons):
    """Subtract any overlapping face contour from each cell
    ({site_index: Polygon} -> {site_index: Polygon | MultiPolygon},
    dropping any cell fully covered by a face). Applied after the solver
    converges, not during -- the solver optimizes cell area against the
    full canvas, so a cell that ends up next to a face loses some area
    to it afterward; an accepted, modest departure from exact target
    proportionality for cells near a face."""
    clipped = {}
    for i, cell in cells.items():
        result = cell
        for face in face_polygons:
            if result.intersects(face):
                result = result.difference(face)
        if not result.is_empty:
            clipped[i] = result
    return clipped


def build_cells(df):
    """Run the full pipeline -- category ranking, target areas, the
    weighted-Voronoi solve, and face clipping -- once for df. Returns
    (items, cells): items is category_items(df) truncated to MAX_CELLS
    (categories beyond the cap are silently dropped, not pooled -- real
    data has 24 categories, well under the cap, so pooling was never
    needed); cells is {index: Polygon | MultiPolygon} keyed into items by
    position."""
    items = category_items(df)[:MAX_CELLS]
    anchors = generate_seed_points(n=len(items))
    fracs = target_fracs(items)
    weighted_cells, _weights, _positions = solve_weighted_voronoi(anchors, fracs, FACE_POLYGONS)
    cells = clip_faces(weighted_cells, FACE_POLYGONS)
    return items, cells


CATEGORY_ITEMS, DEMOISELLES_CELLS = build_cells(data.clean_artworks(data.load_raw_data()))
