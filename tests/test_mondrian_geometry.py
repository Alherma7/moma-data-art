import math

from src import mondrian_geometry


def test_all_rectangles_have_valid_bounds():
    for rect in mondrian_geometry.MONDRIAN_RECTANGLES:
        assert 0 <= rect["x0"] < rect["x1"] <= 1
        assert 0 <= rect["y0"] < rect["y1"] <= 1


def test_all_rectangle_colors_are_primary_or_black():
    allowed = {"red", "blue", "yellow", "black"}
    for rect in mondrian_geometry.MONDRIAN_RECTANGLES:
        assert rect["color"] in allowed


def test_background_rectangles_tile_the_bounding_box_without_gaps():
    colored = mondrian_geometry.MONDRIAN_RECTANGLES
    background = mondrian_geometry.MONDRIAN_BACKGROUND_RECTANGLES
    x_min = min(r["x0"] for r in colored)
    x_max = max(r["x1"] for r in colored)
    y_min = min(r["y0"] for r in colored)
    y_max = max(r["y1"] for r in colored)
    bounding_area = (x_max - x_min) * (y_max - y_min)

    def area(rect):
        return (rect["x1"] - rect["x0"]) * (rect["y1"] - rect["y0"])

    total_area = sum(area(r) for r in colored) + sum(area(r) for r in background)
    assert math.isclose(total_area, bounding_area, rel_tol=1e-9)


def test_fill_background_cells_covers_a_simple_gap():
    colored = [
        {"x0": 0.0, "y0": 0.0, "x1": 0.5, "y1": 1.0, "color": "red"},
        {"x0": 0.5, "y0": 0.0, "x1": 1.0, "y1": 0.5, "color": "blue"},
    ]
    background = mondrian_geometry.fill_background_cells(colored)
    assert background == [{"x0": 0.5, "y0": 0.5, "x1": 1.0, "y1": 1.0, "color": "background"}]


def test_line_overshoots_deterministic_with_fixed_extra():
    colored = [
        {"x0": 0.0, "y0": 0.0, "x1": 0.5, "y1": 0.5, "color": "red"},
        {"x0": 0.5, "y0": 0.5, "x1": 1.0, "y1": 1.0, "color": "blue"},
    ]
    lines = mondrian_geometry.line_overshoots(colored, seed=1, min_extra=0.05, max_extra=0.05)
    assert len(lines) == 4
    by_key = {(line["orientation"], line["edge"]): line for line in lines}
    assert by_key[("vertical", 1.0)]["tip"] == 1.05  # top
    assert by_key[("vertical", 0.0)]["tip"] == -0.05  # bottom
    assert by_key[("horizontal", 0.0)]["tip"] == -0.05  # left
    assert by_key[("horizontal", 1.0)]["tip"] == 1.05  # right


def test_line_length_and_segment():
    vertical = {"orientation": "vertical", "fixed": 0.3, "edge": 0.7, "tip": 0.9}
    assert math.isclose(mondrian_geometry.line_length(vertical), 0.2)
    assert mondrian_geometry.line_segment(vertical) == ((0.3, 0.7), (0.3, 0.9))

    horizontal = {"orientation": "horizontal", "fixed": 0.4, "edge": 0.1, "tip": 0.0}
    assert math.isclose(mondrian_geometry.line_length(horizontal), 0.1)
    assert mondrian_geometry.line_segment(horizontal) == ((0.1, 0.4), (0.0, 0.4))


def test_free_cross_ticks_picks_longest_base_and_valid_reference():
    lines = [
        {"orientation": "vertical", "fixed": 0.3, "edge": 1.0, "tip": 1.20},    # length 0.20 (longest vertical)
        {"orientation": "vertical", "fixed": 0.6, "edge": 1.0, "tip": 1.10},    # length 0.10
        {"orientation": "horizontal", "fixed": 0.4, "edge": 0.0, "tip": -0.15},  # length 0.15 (longest horizontal)
        {"orientation": "horizontal", "fixed": 0.7, "edge": 0.0, "tip": -0.05},  # length 0.05
    ]
    ticks = mondrian_geometry.free_cross_ticks(lines)
    assert len(ticks) == 2

    # base = longest vertical (len 0.20); its valid reference is the
    # longest OTHER line with len <= 0.20 - MIN_ARM_GAP (0.17): the 0.15
    # horizontal line beats the 0.10 vertical one.
    tick_on_vertical_base = next(t for t in ticks if t["orientation"] == "horizontal")
    assert math.isclose(tick_on_vertical_base["fixed"], 1.0 + 0.15)
    assert math.isclose(tick_on_vertical_base["edge"], 0.3 - 0.15 / 2)
    assert math.isclose(tick_on_vertical_base["tip"], 0.3 + 0.15 / 2)

    # base = longest horizontal (len 0.15); its valid reference is the
    # longest OTHER line with len <= 0.15 - MIN_ARM_GAP (0.12): the 0.10
    # vertical line beats the 0.05 horizontal one.
    tick_on_horizontal_base = next(t for t in ticks if t["orientation"] == "vertical")
    assert math.isclose(tick_on_horizontal_base["fixed"], 0.0 - 0.10)
    assert math.isclose(tick_on_horizontal_base["edge"], 0.4 - 0.10 / 2)
    assert math.isclose(tick_on_horizontal_base["tip"], 0.4 + 0.10 / 2)


def test_free_cross_ticks_skips_a_base_with_no_short_enough_reference():
    lines = [
        {"orientation": "vertical", "fixed": 0.3, "edge": 1.0, "tip": 1.05},     # length 0.05, shortest overall
        {"orientation": "horizontal", "fixed": 0.4, "edge": 0.0, "tip": -0.20},  # length 0.20
    ]
    ticks = mondrian_geometry.free_cross_ticks(lines)
    # The horizontal base (0.20) finds the vertical line (0.05) as a valid
    # reference. The vertical base (0.05) has nothing short enough to be a
    # reference, so it's skipped entirely.
    assert len(ticks) == 1
    assert ticks[0]["orientation"] == "vertical"


def test_background_edge_segments_opens_corners_away_from_colored_blocks():
    colored = [{"x0": 0.0, "y0": 0.0, "x1": 0.5, "y1": 0.5, "color": "red"}]
    background = {"x0": 0.5, "y0": 0.0, "x1": 1.0, "y1": 1.0, "color": "background"}
    segments = mondrian_geometry.background_edge_segments(background, colored, gap_fraction=0.5)

    bottom = segments[0]
    (bx0, by0), (bx1, by1) = bottom
    # bottom-left (0.5, 0.0) touches the red rectangle's right edge -> closed
    assert (bx0, by0) == (0.5, 0.0)
    # bottom-right (1.0, 0.0) touches no colored block -> pulled back (open)
    assert bx1 < 1.0
