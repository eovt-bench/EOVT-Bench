from __future__ import annotations

import numpy as np


def crop_histogram(image: np.ndarray, bbox: tuple[float, float, float, float], bins: int = 16) -> np.ndarray:
    """Return a compact normalized RGB histogram for one detection crop."""
    height, width = image.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, x2 = sorted((max(0, min(width, int(x1))), max(0, min(width, int(x2)))))
    y1, y2 = sorted((max(0, min(height, int(y1))), max(0, min(height, int(y2)))))
    if x2 <= x1 or y2 <= y1:
        return np.zeros(bins * 3, dtype=np.float32)
    crop = image[y1:y2, x1:x2, :3]
    parts = []
    for channel in range(3):
        hist, _ = np.histogram(crop[..., channel], bins=bins, range=(0, 256))
        parts.append(hist.astype(np.float32))
    vector = np.concatenate(parts)
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm > 0 else vector


def cosine_similarity(left: np.ndarray | None, right: np.ndarray | None) -> float:
    if left is None or right is None or left.shape != right.shape:
        return 0.0
    denom = float(np.linalg.norm(left) * np.linalg.norm(right))
    return float(np.dot(left, right) / denom) if denom > 0 else 0.0

