import random

from src import voronoi_treemap


def test_sample_points_allocates_proportional_to_weight():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 3.0}, rng, total_points=400)
    assert set(points.keys()) == {"a", "b"}
    assert len(points["a"]) == 100
    assert len(points["b"]) == 300
    for group_points in points.values():
        for x, y in group_points:
            assert 0.0 <= x <= 1.0
            assert 0.0 <= y <= 1.0


def test_sample_points_gives_every_group_at_least_one_point():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 0.001}, rng, total_points=10)
    assert len(points["b"]) >= 1
    assert sum(len(v) for v in points.values()) == 10


import pytest


def test_voronoi_cells_returns_one_polygon_per_group():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 1.0}, rng, total_points=200)
    cells = voronoi_treemap.voronoi_cells(points)
    assert set(cells.keys()) == {"a", "b"}
    for polygon in cells.values():
        assert polygon.is_valid
        assert polygon.area > 0


def test_voronoi_cells_areas_are_roughly_proportional_to_weight():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 3.0}, rng, total_points=800)
    cells = voronoi_treemap.voronoi_cells(points)
    ratio = cells["b"].area / cells["a"].area
    assert 2.0 < ratio < 4.0  # target 3.0; generous tolerance for sampling noise


def test_voronoi_cells_cover_the_unit_square_without_gaps():
    rng = random.Random(42)
    points = voronoi_treemap.sample_points({"a": 1.0, "b": 1.0, "c": 1.0}, rng, total_points=600)
    cells = voronoi_treemap.voronoi_cells(points)
    total_area = sum(polygon.area for polygon in cells.values())
    assert total_area == pytest.approx(1.0, abs=0.02)


def test_voronoi_cells_are_mostly_contiguous():
    rng = random.Random(42)
    weights = {"a": 1.0, "b": 1.0, "c": 1.0, "d": 1.0, "e": 1.0}
    points = voronoi_treemap.sample_points(weights, rng, total_points=1000)
    cells = voronoi_treemap.voronoi_cells(points)
    for group, polygon in cells.items():
        if polygon.geom_type == "MultiPolygon":
            largest = max(part.area for part in polygon.geoms)
            assert largest / polygon.area > 0.9, (
                f"{group} fragmented: largest piece is only "
                f"{largest / polygon.area:.0%} of its total area"
            )
