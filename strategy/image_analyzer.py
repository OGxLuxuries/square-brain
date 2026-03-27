"""
Basic image analyser for Polytopia screenshots.

Uses Pillow to inspect colours and dominant hues to infer:
  - Terrain type (desert, forest, mountain, water, plains)
  - Approximate tribe hint
  - Visible resource types
"""

from __future__ import annotations

import os
from collections import Counter
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from PIL import Image
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Colour maps (approximate Polytopia palette)
# ---------------------------------------------------------------------------

# (R-range, G-range, B-range) → terrain label
_TERRAIN_COLOURS: List[Tuple[Tuple[int, int], Tuple[int, int], Tuple[int, int], str]] = [
    # (r_min, r_max), (g_min, g_max), (b_min, b_max), label
    ((200, 255), (180, 240), (100, 180), "plains"),
    ((30, 100),  (100, 200), (30, 100),  "forest"),
    ((180, 240), (190, 240), (190, 255), "mountain"),  # grey/white peaks
    ((20, 120),  (80, 180),  (150, 255), "water"),
    ((200, 255), (180, 240), (100, 170), "desert"),
    ((220, 255), (220, 255), (220, 255), "snow"),
]

# Rough tribe → dominant terrain mapping
_TRIBE_TERRAIN_MAP: Dict[str, str] = {
    "plains":   "imperius",
    "forest":   "bardur",
    "mountain": "xin-xi",
    "water":    "kickoo",
    "desert":   "oumaji",
    "snow":     "polaris",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class ImageAnalyzer:
    """
    Analyses a Polytopia screenshot and returns inferred game context.

    Parameters
    ----------
    image_path : str | Path
        Path to the screenshot image file.
    """

    def __init__(self, image_path: str | Path) -> None:
        if not _PIL_AVAILABLE:
            raise ImportError(
                "Pillow is required for image analysis. "
                "Install it with: pip install Pillow"
            )
        self.image_path = Path(image_path)
        if not self.image_path.exists():
            raise FileNotFoundError(f"Image not found: {self.image_path}")
        self._image: Optional[Image.Image] = None

    def load(self) -> "ImageAnalyzer":
        """Load the image from disk."""
        self._image = Image.open(self.image_path).convert("RGB")
        return self

    def dominant_terrain(self) -> str:
        """
        Sample pixel colours across the image and return the most common
        terrain type.
        """
        if self._image is None:
            self.load()

        img = self._image
        # Downsample for speed
        small = img.resize((80, 60))
        # get_flattened_data preferred in Pillow 14+; getdata() still works but is deprecated
        try:
            pixels = list(small.get_flattened_data())
        except AttributeError:
            pixels = list(small.getdata())

        counts: Counter[str] = Counter()
        for r, g, b in pixels:
            for (r_min, r_max), (g_min, g_max), (b_min, b_max), label in _TERRAIN_COLOURS:
                if r_min <= r <= r_max and g_min <= g <= g_max and b_min <= b <= b_max:
                    counts[label] += 1
                    break

        if not counts:
            return "unknown"
        return counts.most_common(1)[0][0]

    def infer_tribe(self) -> str:
        """Guess the player's tribe from the dominant terrain."""
        terrain = self.dominant_terrain()
        return _TRIBE_TERRAIN_MAP.get(terrain, "imperius")

    def detect_resources(self) -> List[str]:
        """
        Return a list of resource types likely present based on terrain colours.
        This is a heuristic — not 100% accurate without a full CV pipeline.
        """
        if self._image is None:
            self.load()

        terrain = self.dominant_terrain()
        resource_map: Dict[str, List[str]] = {
            "forest":   ["forest", "animal"],
            "water":    ["fish", "coral"],
            "mountain": ["mountain", "ore"],
            "plains":   ["farm", "animal"],
            "desert":   ["ruin"],
            "snow":     ["animal"],
            "unknown":  [],
        }
        return resource_map.get(terrain, [])

    def describe(self) -> str:
        """Return a short human-readable description of the image analysis."""
        terrain = self.dominant_terrain()
        tribe_hint = self.infer_tribe()
        resources = self.detect_resources()
        res_str = ", ".join(resources) if resources else "none detected"
        return (
            f"Dominant terrain : {terrain}\n"
            f"Likely tribe hint: {tribe_hint}\n"
            f"Detected resources: {res_str}"
        )


def analyze_image(image_path: str | Path) -> Dict[str, object]:
    """
    Convenience wrapper — analyse an image and return a dict of results.

    Returns
    -------
    dict with keys ``terrain``, ``tribe_hint``, ``resources``, ``description``.
    """
    analyzer = ImageAnalyzer(image_path).load()
    return {
        "terrain":     analyzer.dominant_terrain(),
        "tribe_hint":  analyzer.infer_tribe(),
        "resources":   analyzer.detect_resources(),
        "description": analyzer.describe(),
    }
