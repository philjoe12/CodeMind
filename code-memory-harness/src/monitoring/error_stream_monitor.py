import asyncio
from pathlib import Path
from typing import AsyncIterator, Optional


class ErrorStreamMonitor:
    """Asynchronously monitor a log file for error messages."""

    def __init__(self, log_path: str, poll_interval: float = 0.2) -> None:
        self.log_path = Path(log_path)
        self.poll_interval = poll_interval
        self._position = 0

    async def stream_errors(self) -> AsyncIterator[str]:
        """Yield new lines from the log file as they appear."""
        self.log_path.touch(exist_ok=True)
        with self.log_path.open("r") as f:
            f.seek(self._position)
            while True:
                line = f.readline()
                if not line:
                    await asyncio.sleep(self.poll_interval)
                    continue
                self._position = f.tell()
                yield line.rstrip("\n")

    async def tail(self, callback) -> None:
        """Utility helper to call *callback* for each error line."""
        async for line in self.stream_errors():
            await callback(line)
