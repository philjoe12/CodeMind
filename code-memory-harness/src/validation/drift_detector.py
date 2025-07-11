import difflib


class DriftDetector:
    """Detect semantic drift between stored memory and current code."""

    @staticmethod
    def similarity(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a, b).ratio()

    def is_drifted(self, old: str, new: str, threshold: float = 0.7) -> bool:
        """Return True if similarity falls below the threshold."""
        return self.similarity(old, new) < threshold
