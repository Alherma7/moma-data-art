import pandas as pd

from src import data


def test_classify_medium_matches_known_keywords():
    assert data.classify_medium("Oil on canvas") == "painting"
    assert data.classify_medium("Gelatin silver print") == "photography"
    assert data.classify_medium(None) == "unknown"
    assert data.classify_medium("Unrecognizable stuff") == "other"


def test_simplify_gender_handles_known_patterns():
    assert data.simplify_gender(["male"]) == "male"
    assert data.simplify_gender(["female"]) == "female"
    assert data.simplify_gender(["male", "female"]) == "mixed"
    assert data.simplify_gender([]) == "unknown"
    assert data.simplify_gender(None) == "unknown"
    assert data.simplify_gender([None, ""]) == "unknown"
    assert data.simplify_gender(["non-binary"]) == "other"
    assert data.simplify_gender(["male (trans? ftm?)"]) == "male"
    assert data.simplify_gender(["female (transwoman)"]) == "female"


def test_clean_nationalities_drops_null_and_empty_entries():
    assert data.clean_nationalities(["American"]) == ["American"]
    assert data.clean_nationalities(["American", "", None]) == ["American"]
    assert data.clean_nationalities([]) == []
    assert data.clean_nationalities(None) == []


def test_get_region_maps_known_and_unknown_nationalities():
    assert data.get_region("American") == "North America"
    assert data.get_region("French") == "Europe"
    assert data.get_region("Atlantean") == "unknown"


def test_classify_decade_extracts_earliest_year():
    assert data.classify_decade("1913") == ("1910s", 1913)
    assert data.classify_decade("1913-1914") == ("1910s", 1913)
    assert data.classify_decade(None) == ("unknown", None)
    assert data.classify_decade("n.d.") == ("unknown", None)


def test_clean_artworks_adds_expected_columns():
    df = pd.DataFrame({
        "Medium": ["Oil on canvas"],
        "Gender": [["male"]],
        "Nationality": [["American"]],
        "Date": ["1913"],
    })
    cleaned = data.clean_artworks(df)
    for column in [
        "Medium_category", "Gender_simple", "Nationality_list",
        "Region_list", "Decade", "Year_min",
    ]:
        assert column in cleaned.columns
    assert cleaned.loc[0, "Medium_category"] == "painting"
    assert cleaned.loc[0, "Decade"] == "1910s"


def test_classify_credit_matches_known_keywords():
    assert data.classify_credit("Gift of the artist") == "donated/gifts"
    assert data.classify_credit("Purchase") == "purchase/acquired"
    assert data.classify_credit("Mrs. Simon Guggenheim Fund") == "fund/institutions"
    assert data.classify_credit(None) == "other/unknown"
    assert data.classify_credit("Totally unrecognized text") == "other/unknown"


def test_count_participants_counts_list_length():
    assert data.count_participants(["male", "female"]) == 2
    assert data.count_participants(["male"]) == 1
    assert data.count_participants([]) == 0
    assert data.count_participants(None) == 0
