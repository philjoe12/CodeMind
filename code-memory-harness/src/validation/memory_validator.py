from typing import Dict, Any

from .drift_detector import DriftDetector


class MemoryValidator:
    """Validate stored memory entries against the current codebase."""

    def __init__(self, detector: DriftDetector | None = None) -> None:
        self.detector = detector or DriftDetector()

    def validate(self, memory_item: Dict[str, Any], current_content: str) -> Dict[str, Any]:
        similarity = self.detector.similarity(memory_item.get("content", ""), current_content)
        return {
            "memory_id": memory_item.get("chunk_id"),
            "similarity": similarity,
        }

    def should_update(self, memory_item: Dict[str, Any], current_content: str, threshold: float = 0.7) -> bool:
        return self.detector.is_drifted(memory_item.get("content", ""), current_content, threshold)
