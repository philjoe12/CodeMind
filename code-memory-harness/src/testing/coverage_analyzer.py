"""Simple wrapper around coverage.py to measure test coverage."""

import os
import subprocess
from typing import Dict


class CoverageAnalyzer:
    def run_with_coverage(self, test_path: str, src_path: str = ".") -> Dict[str, float]:
        """Run pytest with coverage and return the coverage percentage."""
        import coverage

        cov = coverage.Coverage(source=[src_path])
        cov.start()
        subprocess.run(["pytest", test_path], check=False)
        cov.stop()
        cov.save()

        percent = cov.report(show_missing=False)
        # Cleanup coverage files
        for fname in [".coverage", "htmlcov"]:
            if os.path.exists(fname):
                if os.path.isdir(fname):
                    subprocess.run(["rm", "-rf", fname])
                else:
                    os.remove(fname)

        return {"coverage_percent": percent}
