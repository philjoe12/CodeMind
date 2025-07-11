"""Utility to run generated tests using pytest."""

import os
import subprocess
import tempfile
from typing import Tuple


class TestRunner:
    """Execute tests and return result information."""

    def run(self, test_code: str, cwd: str = ".") -> Tuple[int, str, str]:
        """Run the given test code in a temporary file.

        Returns a tuple of (returncode, stdout, stderr).
        """
        with tempfile.NamedTemporaryFile("w", suffix="_test.py", delete=False) as f:
            f.write(test_code)
            test_path = f.name

        try:
            proc = subprocess.run(
                ["pytest", "-q", test_path],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            return proc.returncode, proc.stdout, proc.stderr
        finally:
            os.remove(test_path)
