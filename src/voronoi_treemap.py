import math
import random

import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

_BOUNDS = box(0, 0, 1, 1)
_CLUSTER_AREA_BUDGET = 0.3  # total disk area across ALL groups combined, as
# a share of the unit square. Fixed regardless of group count -- since
# sum(share) == 1 for any number of groups, this keeps total packing needs
# constant. Area proportionality is approximate by design: exact weighted-Voronoi-treemap
# area matching would need an iterative algorithm (e.g., Balzer & Deussen); this
# scales cluster radius/point-count with weight as a practical approximation instead.


def sample_points(weights: dict, rng: random.Random, total_points: int = 2000) -> dict:
    """Sample points clustered per group, so each group occupies a spatially
    contiguous region rather than being scattered across the whole unit
    square. Cluster radius scales with sqrt(weight share) so cluster AREA
    (not just point count) tracks each group's target proportion, and point
    count still scales with weight too (largest-remainder allocation),
    keeping point density comparable across differently-sized clusters."""
    groups = list(weights.keys())
    if not groups:
        return {}
    total_weight = sum(weights.values())

    raw_counts = {g: total_points * weights[g] / total_weight for g in groups}
    counts = {g: int(raw_counts[g]) for g in groups}
    remainder = total_points - sum(counts.values())
    by_fractional_part = sorted(
        groups, key=lambda g: raw_counts[g] - counts[g], reverse=True
    )
    for g in by_fractional_part[:remainder]:
        counts[g] += 1

    while True:
        zero_groups = [g for g in groups if counts[g] == 0]
        if not zero_groups:
            break
        donor = max(groups, key=lambda h: counts[h])
        if counts[donor] <= 1:
            break  # can't donate further without creating a new zero elsewhere
        counts[donor] -= 1
        counts[zero_groups[0]] = 1

    k = math.sqrt(_CLUSTER_AREA_BUDGET / math.pi)
    radii = {
        g: max(0.02, k * math.sqrt(weights[g] / total_weight))
        for g in groups
    }

    anchors = {}
    for g in groups:
        # Rejection-sample an anchor that doesn't overlap any previously
        # placed group's disk. If 500 attempts all fail (dense/many-group
        # layouts), silently accept the last candidate anyway rather than
        # looping forever -- slight overlap only degrades contiguity, not
        # correctness, so "full separation" here is best-effort, not absolute.
        for _attempt in range(500):
            candidate = (rng.uniform(0.1, 0.9), rng.uniform(0.1, 0.9))
            if all(
                math.dist(candidate, anchors[h]) >= radii[g] + radii[h]
                for h in anchors
            ):
                break
        anchors[g] = candidate

    return {
        g: [
            (
                min(1.0, max(0.0, rng.gauss(anchors[g][0], radii[g] / 2))),
                min(1.0, max(0.0, rng.gauss(anchors[g][1], radii[g] / 2))),
            )
            for _ in range(counts[g])
        ]
        for g in groups
    }


def voronoi_cells(points: dict) -> dict:
    """Compute a Voronoi diagram over all groups' combined points, clipped
    to the unit square, with same-group cells unioned together. Each
    group's value is usually a single Polygon but may come back as a
    MultiPolygon when its points' regions don't all merge into one
    contiguous shape.

    Every point is mirrored across all 4 edges of the unit square before
    running scipy's Voronoi — a standard trick that gives every original
    (non-mirrored) point a finite region, since an infinite/unbounded
    Voronoi cell can't be clipped to a polygon.
    """
    groups = list(points.keys())
    labels = []
    coords = []
    for group in groups:
        for x, y in points[group]:
            labels.append(group)
            coords.append((x, y))
    if not coords:
        return {}
    coords = np.array(coords)
    n = len(coords)

    mirrored = np.vstack([
        coords,
        np.column_stack([-coords[:, 0], coords[:, 1]]),
        np.column_stack([2 - coords[:, 0], coords[:, 1]]),
        np.column_stack([coords[:, 0], -coords[:, 1]]),
        np.column_stack([coords[:, 0], 2 - coords[:, 1]]),
    ])
    vor = Voronoi(mirrored)

    polygons_by_group = {}
    for i in range(n):
        region = vor.regions[vor.point_region[i]]
        if not region or -1 in region:
            continue
        vertices = [vor.vertices[v] for v in region]
        polygon = Polygon(vertices).intersection(_BOUNDS)
        # A region that merely grazes the unit square's boundary can clip
        # down to a degenerate LineString/Point/GeometryCollection instead
        # of a Polygon; skip those too since downstream rendering assumes
        # Polygon/MultiPolygon geometry.
        if polygon.is_empty or polygon.geom_type != "Polygon":
            continue
        polygons_by_group.setdefault(labels[i], []).append(polygon)

    return {
        group: unary_union(polys)
        for group, polys in polygons_by_group.items()
    }
