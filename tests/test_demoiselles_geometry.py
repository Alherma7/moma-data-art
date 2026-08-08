import math

import numpy as np
import pandas as pd
import pytest
from PIL import Image
from shapely.geometry import Polygon

from src import demoiselles_geometry as geo


def test_face_polygons_are_valid():
    for polygon in geo.FACE_POLYGONS:
        assert polygon.is_valid


def test_anchors_align_one_to_one_with_real_categories():
    assert len(geo.ANCHORS) == len(geo.CATEGORY_ITEMS)


def test_classify_gender_buckets_real_observed_values():
    assert geo.classify_gender("male") == "Man"
    assert geo.classify_gender("female") == "Woman"
    assert geo.classify_gender("female (transwoman)") == "Transgender"
    assert geo.classify_gender("male (trans? ftm?)") == "Transgender"
    assert geo.classify_gender("transgender woman") == "Transgender"


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
    assert counts == {("1960s", "Man"): 2, ("1960s", "Woman"): 1}


def test_category_items_ranks_by_count_descending():
    df = pd.DataFrame({
        "Gender": [["male"]] * 3 + [["female"]] * 10,
        "Decade_acquired": ["1960s"] * 3 + ["1970s"] * 10,
    })
    items = geo.category_items(df)
    assert items == [(("1970s", "Woman"), 10), (("1960s", "Man"), 3)]


def test_target_fracs_sums_to_one_and_strictly_orders_the_tail():
    """sqrt-scaling replaced a hard floor that collapsed several small,
    distinct counts into an identical target area -- every distinct count
    must now map to a distinct, strictly ordered fraction."""
    items = [("a", 999), ("b", 4), ("c", 1)]
    fracs = geo.target_fracs(items)
    assert math.isclose(fracs.sum(), 1.0)
    assert fracs[0] > fracs[1] > fracs[2] > 0


def test_power_diagram_splits_two_equal_weight_sites_down_the_middle():
    cells = geo.power_diagram([(0.25, 0.5), (0.75, 0.5)], weights=[0.0, 0.0])
    assert set(cells) == {0, 1}
    assert math.isclose(cells[0].area, cells[1].area, rel_tol=1e-6)


def test_power_diagram_gives_more_area_to_a_higher_weight_site():
    cells = geo.power_diagram([(0.3, 0.5), (0.7, 0.5)], weights=[0.1, -0.1])
    assert cells[0].area > cells[1].area


def test_solve_cell_weights_converges_toward_target_fracs_without_moving_anchors():
    anchors = [(0.2, 0.2), (0.8, 0.2), (0.5, 0.8), (0.5, 0.4)]
    target = np.array([0.7, 0.1, 0.1, 0.1])
    cells, weights = geo.solve_cell_weights(anchors, target, iterations=100)
    assert len(cells) == 4
    assert len(weights) == 4
    areas = np.array([cells[i].area for i in range(4)])
    fractions = areas / areas.sum()
    assert np.abs(fractions - target).max() < 0.05


def test_clip_faces_removes_overlapping_area():
    cell = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
    face = Polygon([(0.4, 0.4), (0.6, 0.4), (0.6, 0.6), (0.4, 0.6)])
    clipped = geo.clip_faces({0: cell}, [face])
    assert list(clipped) == [0]
    assert clipped[0].area < cell.area
    assert math.isclose(clipped[0].area, cell.area - face.area)


def test_clip_faces_drops_cells_fully_covered_by_a_face():
    cell = Polygon([(0.4, 0.4), (0.5, 0.4), (0.5, 0.5), (0.4, 0.5)])
    face = Polygon([(0.3, 0.3), (0.7, 0.3), (0.7, 0.7), (0.3, 0.7)])
    clipped = geo.clip_faces({0: cell}, [face])
    assert clipped == {}


def test_face_image_crop_is_transparent_outside_the_polygon():
    painting = Image.new("RGB", (100, 100), (200, 100, 50))
    contour = [(0.4, 0.2), (0.6, 0.4), (0.4, 0.6), (0.2, 0.4)]  # diamond
    bbox, crop = geo.face_image_crop(contour, painting)
    assert bbox == pytest.approx((0.2, 0.2, 0.6, 0.6))
    corner_alpha = crop.getpixel((0, 0))[3]
    center_alpha = crop.getpixel((crop.width // 2, crop.height // 2))[3]
    assert corner_alpha == 0  # outside the diamond, inside its bbox
    assert center_alpha == 255


def test_module_level_cells_built_from_real_data_stay_within_canvas():
    for cell in geo.DEMOISELLES_CELLS.values():
        assert cell.area <= 1.0
    assert 0 < len(geo.DEMOISELLES_CELLS) <= len(geo.CATEGORY_ITEMS)


def test_module_level_face_image_crops_align_with_face_contours():
    assert len(geo.FACE_IMAGE_CROPS) == len(geo.FACE_CONTOURS)
    for bbox, crop in geo.FACE_IMAGE_CROPS:
        x0, y0, x1, y1 = bbox
        assert 0 <= x0 < x1 <= 1
        assert 0 <= y0 < y1 <= 1
        assert crop.mode == "RGBA"
