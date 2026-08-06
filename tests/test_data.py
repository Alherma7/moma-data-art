import pandas as pd

from src import data


def test_classify_medium_matches_known_keywords():
    assert data.classify_medium("Oil on canvas") == "painting"
    assert data.classify_medium("Gelatin silver print") == "photography"
    assert data.classify_medium(None) == "unknown"
    assert data.classify_medium("Unrecognizable stuff") == "other"


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
        "Nationality": [["American"]],
        "DateAcquired": ["1996-04-09"],
    })
    cleaned = data.clean_artworks(df)
    for column in [
        "Medium_category", "Nationality_list",
        "Region_list", "Decade_acquired", "Year_acquired",
    ]:
        assert column in cleaned.columns
    assert cleaned.loc[0, "Medium_category"] == "painting"
    assert cleaned.loc[0, "Decade_acquired"] == "1990s"
    assert cleaned.loc[0, "Year_acquired"] == 1996
