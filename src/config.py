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
        "mujer": "#C97B63",
        "hombre": "#6E8CA0",
        "transgenero": "#D4A24C",
        "face": "#E8DCC8",
        "background": "#F2EADD",
        "black": "#111111",
    },
}
