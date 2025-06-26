from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class ReasoningModelInterface(ABC):
    """Abstract interface for reasoning models"""

    @abstractmethod
    async def generate_fix(self, error_context: Dict,
                           code_context: str,
                           memory_context: List[Dict]) -> str:
        pass

    @abstractmethod
    async def generate_tests(self, function_code: str,
                             test_strategy: str) -> List[str]:
        pass

    @abstractmethod
    async def validate_memory(self, memory_item: Dict,
                              current_code: str) -> float:
        pass
