import random

import numpy as np
from scipy.spatial import Voronoi
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

_BOUNDS = box(0, 0, 1, 1)


def sample_points(weights: dict, rng: random.Random, total_points: int = 2000) -> dict:
    """Sample points within the unit square [0,1]x[0,1], allocated to each
    group proportional to its weight (largest-remainder method, so counts
    sum to exactly total_points), with every group guaranteed at least 1
    point so it still produces a valid Voronoi cell downstream."""
    groups = list(weights.keys())
    total_weight = sum(weights.values())
    raw_counts = {g: total_points * weights[g] / total_weight for g in groups}
    counts = {g: int(raw_counts[g]) for g in groups}

    remainder = total_points - sum(counts.values())
    by_fractional_part = sorted(
        groups, key=lambda g: raw_counts[g] - counts[g], reverse=True
    )
    for g in by_fractional_part[:remainder]:
        counts[g] += 1

    zero_groups = [g for g in groups if counts[g] == 0]
    for g in zero_groups:
        donor = max(groups, key=lambda h: counts[h])
        counts[donor] -= 1
        counts[g] = 1

    return {
        g: [(rng.random(), rng.random()) for _ in range(counts[g])]
        for g in groups
    }


def voronoi_cells(points: dict) -> dict:
    """Compute a Voronoi diagram over all groups' combined points, clipped
    to the unit square, with same-group cells merged into one polygon.

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
        if polygon.is_empty:
            continue
        polygons_by_group.setdefault(labels[i], []).append(polygon)

    return {
        group: unary_union(polys)
        for group, polys in polygons_by_group.items()
    }
