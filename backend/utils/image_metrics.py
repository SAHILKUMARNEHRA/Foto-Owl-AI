from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def compute_brightness(image_path: Path) -> float:
    with Image.open(image_path) as image:
        grayscale = image.convert("L")
        return float(np.asarray(grayscale).mean())


def compute_blur_score(image_path: Path) -> float:
    with Image.open(image_path) as image:
        grayscale = image.convert("L")
        edges = grayscale.filter(ImageFilter.FIND_EDGES)
        values = np.asarray(edges, dtype=np.float32)
        return float(values.var())
