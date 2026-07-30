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
        "terracotta": "#B5651D",
        "pink": "#D9A5A0",
        "cream": "#E8DCC8",
        "brown": "#3B2A20",
        "background": "#EFE6D8",
    },
    "dance": {
        "orange": "#E2725B",
        "green": "#5C8A3A",
        "blue": "#3C6997",
    },
}

GEOMETRIZE_CONFIGS = {
    "mondrian": {
        "image": IMAGES_DIR / "mondrian_composition.jpg",
        "shape_kind": "rectangle",
        "n_shapes": 120,
        "n_candidates": 60,
        "n_refine": 20,
    },
    "demoiselles": {
        "image": IMAGES_DIR / "les_demoiselles_davignon.png",
        "shape_kind": "triangle",
        "n_shapes": 200,
        "n_candidates": 60,
        "n_refine": 20,
    },
    "dance": {
        "image": IMAGES_DIR / "dance_i.png",
        "shape_kind": "ellipse",
        "n_shapes": 150,
        "n_candidates": 60,
        "n_refine": 20,
    },
}
