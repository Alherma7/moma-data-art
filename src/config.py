from pathlib import Path

RANDOM_STATE = 42

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_PROCESSED_DIR = ROOT_DIR / "data" / "processed"
IMAGES_DIR = ROOT_DIR / "images"
OUTPUTS_DIR = ROOT_DIR / "outputs"

MOMA_ARTWORKS_URL = "https://raw.githubusercontent.com/MoMA/collection/master/Artworks.json"
MOMA_ARTISTS_URL = "https://raw.githubusercontent.com/MoMA/collection/master/Artists.json"

PALETTES = {
    "mondrian": {
        "red": "#D40920",
        "blue": "#1356A2",
        "yellow": "#F7D842",
        "black": "#111111",
        "background": "#F2F0E6",
    },
    "demoiselles": {
        # Sampled directly from images/les_demoiselles_davignon.png (rose
        # flesh/dress, blue-grey drapery, olive-green mask stripes). Fails
        # the dataviz skill's categorical accessibility validator (chroma
        # floor, CVD separation) -- kept anyway, by explicit user request,
        # for fidelity to the source painting over accessibility.
        "mujer": "#A97878",
        "hombre": "#71969F",
        "transgenero": "#566454",
        "face": "#E8DCC8",
        "background": "#F2EADD",
        "black": "#111111",
    },
}
