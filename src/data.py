import re

import pandas as pd

_MEDIUM_CATEGORIES = {
    "painting": ["oil", "acrylic", "watercolor", "tempera", "gouache", "fresco", "enamel", "paint", "color"],
    "drawing": ["pencil", "graphite", "charcoal", "ink", "pastel", "crayon", "chalk", "pen", "pasted", "paper", "drawing"],
    "photography": ["photograph", "gelatin silver", "c-print", "chromogenic", "digital image", "film", "silver", "albumen", "photogravure", "collotype"],
    "printmaking": ["lithograph", "etching", "engraving", "woodcut", "screenprint", "serigraph", "aquatint", "mezzotint", "drypoint", "offset", "portfolio", "linoleum", "poster", "silkscreen", "print", "printed"],
    "sculpture": ["bronze", "stone", "marble", "wood", "ceramic", "plaster", "resin", "metal", "wax", "plastic", "steel"],
    "installation": ["installation", "video art", "single-channel video", "video installation"],
    "electronic": ["digital art", "electronic", "programming", "video games", "graphic art software", "digital"],
    "film": ["animation", "stop motion", "puppet film", "live action", "cinematography", "video", "sound"],
    "literature": ["book", "letterpress", "writing", "vellum", "papyrus", "journal"],
    "ceramics": ["clay", "porcelain", "pottery", "terracotta", "tile", "bone china"],
    "performing arts": ["performance", "dance", "theatre", "re-enactment"],
}

_REGION_MAP = {
    "North America": ["American", "Canadian"],
    "Latin America": ["Mexican", "Argentine", "Brazilian", "Peruvian", "Chilean", "Cuban", "Colombian", "Venezuelan"],
    "Europe": ["French", "German", "British", "Spanish", "Italian", "Swiss", "Dutch", "Polish", "Austrian", "Irish", "Portuguese", "Czech", "Belgian", "Greek", "Hungarian", "Norwegian", "Swedish", "Finnish", "Danish", "English", "Scottish"],
    "Europe/Asia": ["Russian", "Turkish"],
    "Asia": ["Chinese", "Japanese", "Indian", "Korean", "Vietnamese", "Filipino", "Israeli", "Iranian"],
    "Africa": ["Egyptian", "South African", "Nigerian", "Moroccan"],
    "Oceania": ["Australian", "New Zealander"],
}

_DECADE_PATTERN = re.compile(r"[1-2][0-9]{3}")


def classify_medium(medium) -> str:
    """Bucket a raw Medium string into a coarse category.

    Refined from the category keyword list validated in the original PRA1
    notebook (Visualizacion_Datos_PRA1_Alejandro_Hernandez_Mairal-Copy1.ipynb).
    """
    if pd.isna(medium):
        return "unknown"
    m = medium.lower()
    for category, keywords in _MEDIUM_CATEGORIES.items():
        if any(keyword in m for keyword in keywords):
            return category
    return "other"


def simplify_gender(genders) -> str:
    """Collapse MoMA's per-constituent Gender list to male/female/other/mixed/unknown.

    Artworks.json stores Gender as a list of lowercase strings per artist
    credited on the work (e.g. ["male"], ["female", "male"], [] for none) —
    not the CSV's single "(Male) (Female)" text field the original PRA1
    notebook's simplify_gender() parsed with parentheses regexes. Observed
    real values (from data/raw/Artworks.json) beyond plain "male"/"female":
    "female (transwoman)", "male (trans? ftm?)", "non-binary", "gender
    non-conforming", "transgender woman", plus null/empty-string entries
    inside otherwise non-empty lists.
    """
    if not isinstance(genders, list):
        return "unknown"
    cleaned = [g.strip().lower() for g in genders if isinstance(g, str) and g.strip()]
    if not cleaned:
        return "unknown"

    is_male = any(g.startswith("male") for g in cleaned)
    is_female = any(g.startswith("female") for g in cleaned)
    is_other = any(not g.startswith(("male", "female")) for g in cleaned)

    categories_present = sum([is_male, is_female, is_other])
    if categories_present > 1:
        return "mixed"
    if is_male:
        return "male"
    if is_female:
        return "female"
    return "other"


def clean_nationalities(nationalities) -> list:
    """Drop null/empty entries from MoMA's per-constituent Nationality list.

    Artworks.json already stores Nationality as a list (e.g. ["Austrian"],
    []) rather than the CSV's single "(Austrian)" text field the original
    notebook's extract_nationalities() regex-parsed; some lists contain
    null or empty-string entries mixed in with real values.
    """
    if not isinstance(nationalities, list):
        return []
    return [n.strip() for n in nationalities if isinstance(n, str) and n.strip()]


def get_region(nationality: str) -> str:
    """Map a single nationality string to a coarse world region."""
    for region, countries in _REGION_MAP.items():
        if nationality in countries:
            return region
    return "unknown"


def classify_decade(date):
    """Extract the earliest 4-digit year found in a free-text Date field
    and bucket it into a decade string, e.g. "1910s"."""
    if pd.isna(date) or str(date).strip() == "":
        return "unknown", None
    years = [int(y) for y in _DECADE_PATTERN.findall(str(date))]
    if not years:
        return "unknown", None
    year = min(years)
    decade = f"{(year // 10) * 10}s"
    return decade, year


def clean_artworks(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all categorization functions to a raw Artworks dataframe."""
    df = df.copy()
    df["Medium_category"] = df["Medium"].apply(classify_medium)
    df["Gender_simple"] = df["Gender"].apply(simplify_gender)
    df["Nationality_list"] = df["Nationality"].apply(clean_nationalities)
    df["Region_list"] = df["Nationality_list"].apply(
        lambda names: [get_region(n) for n in names] if names else ["unknown"]
    )
    df[["Decade", "Year_min"]] = df["Date"].apply(
        lambda d: pd.Series(classify_decade(d))
    )
    return df
