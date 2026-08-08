import math

import numpy as np
import pandas as pd
from shapely.geometry import Point

from src import demoiselles_geometry as geo


def test_face_polygons_are_valid():
    for polygon in geo.FACE_POLYGONS:
        assert polygon.is_valid


def test_generate_seed_points_excludes_face_interiors():
    for x, y in geo.generate_seed_points(n=30):
        for polygon in geo.FACE_POLYGONS:
            assert not polygon.contains(Point(x, y))


def test_generate_seed_points_is_deterministic():
    first = geo.generate_seed_points(n=20, seed=7)
    second = geo.generate_seed_points(n=20, seed=7)
    assert first == second


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
    df = pd.DataFrame({
        "Gender": [["male", "female"], ["male"], ["unknown-value"]],
        "Decade_acquired": ["1960s", "1960s", "1970s"],
    })
    counts = geo.person_gender_decade_counts(df)
    assert counts == {("1960s", "Hombre"): 2, ("1960s", "Mujer"): 1}


def test_category_items_ranks_by_count_descending():
    df = pd.DataFrame({
        "Gender": [["male"]] * 3 + [["female"]] * 10,
        "Decade_acquired": ["1960s"] * 3 + ["1970s"] * 10,
    })
    items = geo.category_items(df)
    assert items == [(("1970s", "Mujer"), 10), (("1960s", "Hombre"), 3)]


def test_target_fracs_sums_to_one_and_floors_the_smallest_category():
    items = [("a", 999), ("b", 1)]
    fracs = geo.target_fracs(items, min_frac=0.1)
    assert math.isclose(fracs.sum(), 1.0)
    raw_share = 1 / 1000
    assert fracs[1] > raw_share  # flooring lifts it well above its true 0.1% share


def test_power_diagram_splits_two_equal_weight_sites_down_the_middle():
    cells = geo.power_diagram([(0.25, 0.5), (0.75, 0.5)], weights=[0.0, 0.0])
    assert set(cells) == {0, 1}
    assert math.isclose(cells[0].area, cells[1].area, rel_tol=1e-6)


def test_power_diagram_gives_more_area_to_a_higher_weight_site():
    cells = geo.power_diagram([(0.3, 0.5), (0.7, 0.5)], weights=[0.1, -0.1])
    assert cells[0].area > cells[1].area


def test_solve_weighted_voronoi_converges_toward_target_fracs():
    anchors = geo.generate_seed_points(n=4, seed=1)
    target = np.array([0.7, 0.1, 0.1, 0.1])
    cells, weights, positions = geo.solve_weighted_voronoi(
        anchors, target, geo.FACE_POLYGONS, iterations=100
    )
    assert len(cells) == 4
    assert len(weights) == len(positions) == 4
    areas = np.array([cells[i].area for i in range(4)])
    fractions = areas / areas.sum()
    assert np.abs(fractions - target).max() < 0.05


def test_clip_faces_removes_overlapping_area():
    from shapely.geometry import Polygon

    cell = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    face = Polygon([(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)])
    clipped = geo.clip_faces({0: cell}, [face])
    assert list(clipped) == [0]
    assert clipped[0].area < cell.area
    assert math.isclose(clipped[0].area, cell.area - face.area)


def test_clip_faces_drops_cells_fully_covered_by_a_face():
    from shapely.geometry import Polygon

    cell = Polygon([(0.4, 0.4), (0.5, 0.4), (0.5, 0.5), (0.4, 0.5)])
    face = Polygon([(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)])
    clipped = geo.clip_faces({0: cell}, [face])
    assert clipped == {}


def test_build_cells_keys_align_with_returned_items():
    df = pd.DataFrame({
        "Gender": [["male"]] * 10 + [["female"]] * 5 + [["transgender"]] * 2,
        "Decade_acquired": ["1960s"] * 10 + ["1970s"] * 5 + ["1980s"] * 2,
    })
    items, cells = geo.build_cells(df)
    assert len(items) == 3
    assert all(0 <= i < len(items) for i in cells)


def test_module_level_cells_built_from_real_data_stay_within_canvas():
    for cell in geo.DEMOISELLES_CELLS.values():
        assert cell.area <= 1.0
    assert 0 < len(geo.DEMOISELLES_CELLS) <= len(geo.CATEGORY_ITEMS)
