from collections import defaultdict
from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import ConvexHull
from shapely.geometry import MultiPoint, Polygon, box

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

# Placed by hand (like FACE_CONTOURS), ordered to line up positionally with
# CATEGORY_ITEMS below (index 0 = highest-count category). Unlike the
# earlier jittered-grid version, the solver never moves these -- position is
# fixed once placed, only each cell's weight is adjusted to hit its target
# area. Approved as-is by the user without further hand-tuning.
ANCHORS = [
    (0.42, 0.01),  # 0: ('1960s', 'Hombre') (44170)
    (0.42, 0.62),  # 1: ('2010s', 'Hombre') (20360)
    (0.79, 0.01),  # 2: ('2000s', 'Hombre') (20334)
    (0.76, 0.19),  # 3: ('1970s', 'Hombre') (11697)
    (0.40, 0.95),  # 4: ('1980s', 'Hombre') (9452)
    (0.94, 0.78),  # 5: ('1990s', 'Hombre') (9164)
    (0.01, 0.78),  # 6: ('2010s', 'Mujer') (6911)
    (0.01, 0.43),  # 7: ('1940s', 'Hombre') (6733)
    (0.23, 0.05),  # 8: ('1950s', 'Hombre') (6023)
    (0.61, 0.80),  # 9: ('2000s', 'Mujer') (5752)
    (0.76, 0.95),  # 10: ('2020s', 'Hombre') (5710)
    (0.22, 0.38),  # 11: ('1990s', 'Mujer') (2935)
    (0.80, 0.42),  # 12: ('2020s', 'Mujer') (2040)
    (0.97, 0.23),  # 13: ('1970s', 'Mujer') (1664)
    (0.05, 0.03),  # 14: ('1930s', 'Hombre') (1655)
    (0.98, 0.41),  # 15: ('1980s', 'Mujer') (1190)
    (0.25, 0.99),  # 16: ('1960s', 'Mujer') (1156)
    (0.59, 0.43),  # 17: ('1940s', 'Mujer') (657)
    (0.21, 0.20),  # 18: ('1950s', 'Mujer') (390)
    (0.95, 0.96),  # 19: ('2020s', 'Transgénero') (63)
    (0.61, 0.58),  # 20: ('1930s', 'Mujer') (50)
    (0.39, 0.42),  # 21: ('1940s', 'Transgénero') (10)
    (0.40, 0.19),  # 22: ('1920s', 'Hombre') (9)
    (0.05, 0.61),  # 23: ('1950s', 'Transgénero') (1)
]


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
    label every cell (ANCHORS, target areas, and the final render are
    all indexed the same way)."""
    counts = person_gender_decade_counts(df)
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)


def target_fracs(items):
    """Each category's target cell-area share, scaled by sqrt(count)
    rather than linear count: real data spans a ~44,000x count range (1
    to 44,170), and a linear-area/floor scheme collapsed most of the tail
    into identically-sized cells once floored. sqrt keeps every
    category's area strictly ordered and visibly distinct without an
    artificial floor."""
    weights = np.array([count ** 0.5 for _, count in items])
    return weights / weights.sum()


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


def solve_cell_weights(anchors, target_fracs, bounds=(0.0, 0.0, 1.0, 1.0), iterations=250, weight_lr=0.4):
    """Iteratively adjusts each site's weight to push its cell area
    toward target_fracs. Positions are never touched -- anchors are
    placed by hand (see ANCHORS above), so the solver's only job is
    sizing. Returns (cells, weights)."""
    n = len(anchors)
    weights = np.zeros(n)
    total_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])

    for _ in range(iterations):
        cells = power_diagram(anchors, weights, bounds)
        areas = np.array([cells[i].area if i in cells else 0.0 for i in range(n)])
        error = target_fracs - areas / total_area
        weights = weights + weight_lr * error
        weights -= weights.mean()  # power diagrams are invariant to a global weight shift

    return power_diagram(anchors, weights, bounds), weights


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


def face_image_crop(contour, painting):
    """Masks painting to contour's shape (plot-space, y=0 at bottom) and
    returns (bbox, rgba_crop): bbox is the polygon's bounding box in
    normalized plot coordinates (x0, y0, x1, y1), rgba_crop is the
    painting cropped to that box with everything outside the polygon
    made transparent. Plotly can't clip an image to an arbitrary polygon
    natively, so the clipping happens here in PIL; the caller only needs
    to place a rectangle."""
    w, h = painting.size
    px_points = [(x * w, (1 - y) * h) for x, y in contour]
    xs = [p[0] for p in px_points]
    ys = [p[1] for p in px_points]
    x0_px, x1_px = min(xs), max(xs)
    y0_px, y1_px = min(ys), max(ys)

    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).polygon(px_points, fill=255)
    rgba = painting.convert("RGBA")
    rgba.putalpha(mask)
    crop = rgba.crop((int(x0_px), int(y0_px), int(x1_px) + 1, int(y1_px) + 1))

    bbox = (x0_px / w, 1 - y1_px / h, x1_px / w, 1 - y0_px / h)
    return bbox, crop


CATEGORY_ITEMS = category_items(data.clean_artworks(data.load_raw_data()))
assert len(ANCHORS) == len(CATEGORY_ITEMS)
TARGET_FRACS = target_fracs(CATEGORY_ITEMS)
_WEIGHTED_CELLS, _WEIGHTS = solve_cell_weights(ANCHORS, TARGET_FRACS)
DEMOISELLES_CELLS = clip_faces(_WEIGHTED_CELLS, FACE_POLYGONS)

PAINTING = Image.open(config.IMAGES_DIR / "les_demoiselles_davignon.png").convert("RGB")
FACE_IMAGE_CROPS = [face_image_crop(contour, PAINTING) for contour in FACE_CONTOURS]
