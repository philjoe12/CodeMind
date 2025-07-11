import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


class FixTracker:
    """Persist and query historical fix attempts."""

    def __init__(self, db_path: str = "fix_history.json") -> None:
        self.db_path = Path(db_path)
        self._history: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if self.db_path.exists():
            try:
                return json.loads(self.db_path.read_text())
            except Exception:
                return []
        return []

    def _save(self) -> None:
        self.db_path.write_text(json.dumps(self._history, indent=2))

    def record_fix(self, error: Dict[str, Any], fix: str, success: bool) -> None:
        """Record a fix attempt for an error."""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "fix": fix,
            "success": success,
        }
        self._history.append(entry)
        self._save()

    def history_for(self, error_type: str) -> List[Dict[str, Any]]:
        """Return history of fixes for a given error type."""
        return [e for e in self._history if e.get("error", {}).get("type") == error_type]
