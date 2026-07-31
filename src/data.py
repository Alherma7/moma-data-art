import re
import urllib.request
from pathlib import Path

import pandas as pd

from . import config

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

_CREDIT_CATEGORIES = {
    "fund/institutions": ["fund", "foundation", "endowment", "charitable trust", "council", "university", "museum", "comitte"],
    "purchase/acquired": ["purchase", "puchase", "acquired", "acquisition", "exchange", "transferred", "collection", "commissioned"],
    "donated/gifts": ["donated", "donor", "gift", "giff", "given", "generosity", "courtesy", "bequest", "estate", "testamentary"],
    "individual": ["j. b. neumann", "abraham", "blanchette", "mr.", "ms.", "individual"],
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


def classify_credit(credit_line) -> str:
    """Bucket a raw CreditLine string into a coarse acquisition-source
    category. Ported from the original PRA1 notebook's classify_credit(),
    validated there against this same field."""
    if pd.isna(credit_line):
        return "other/unknown"
    c = credit_line.lower().strip()
    for category, keywords in _CREDIT_CATEGORIES.items():
        if any(keyword in c for keyword in keywords):
            return category
    return "other/unknown"


def count_participants(genders) -> int:
    """Number of constituents credited on an artwork — Artworks.json's
    Gender field is a list with one entry per credited artist, so its
    length is the participant count directly (no regex parsing needed,
    unlike the original CSV-based notebook's count_participants())."""
    return len(genders) if isinstance(genders, list) else 0


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
    df["Credit_category"] = df["CreditLine"].apply(classify_credit)
    df["Num_participants"] = df["Gender"].apply(count_participants)
    df[["Decade_acquired", "Year_acquired"]] = df["DateAcquired"].apply(
        lambda d: pd.Series(classify_decade(d))
    )
    return df


def download_raw_data() -> None:
    """Fetch fresh copies of Artworks.json/Artists.json from MoMA's GitHub repo."""
    config.DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(config.MOMA_ARTWORKS_URL, config.DATA_RAW_DIR / "Artworks.json")
    urllib.request.urlretrieve(config.MOMA_ARTISTS_URL, config.DATA_RAW_DIR / "Artists.json")


def load_raw_data() -> pd.DataFrame:
    """Load whatever Artworks.json is currently in data/raw/."""
    return pd.read_json(config.DATA_RAW_DIR / "Artworks.json", convert_dates=False)


def save_processed(df: pd.DataFrame) -> Path:
    config.DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = config.DATA_PROCESSED_DIR / "artworks_clean.parquet"
    df.to_parquet(out_path)
    return out_path
