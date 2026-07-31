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
