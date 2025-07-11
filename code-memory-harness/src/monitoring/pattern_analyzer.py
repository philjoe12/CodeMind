from collections import Counter
import re
from typing import List, Tuple


class PatternAnalyzer:
    """Analyze error message patterns and track their frequency."""

    def __init__(self) -> None:
        self._counter: Counter[str] = Counter()

    def add_line(self, line: str) -> None:
        """Normalize the error line and update frequency stats."""
        pattern = self._normalize(line)
        self._counter[pattern] += 1

    def top_patterns(self, n: int = 5) -> List[Tuple[str, int]]:
        """Return the most common normalized patterns."""
        return self._counter.most_common(n)

    def _normalize(self, line: str) -> str:
        # Replace numbers and file line references with placeholders
        line = re.sub(r"\d+", "<num>", line)
        line = re.sub(r"(File\s+\".*?\", line <num>)", "File <path>, line <num>", line)
        return line.strip()
