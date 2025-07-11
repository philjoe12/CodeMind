"""Generate simple Hypothesis tests for functions."""

from typing import Callable, List
import inspect


class StochasticTestGenerator:
    """Create property-based tests using Hypothesis."""

    def __init__(self, max_examples: int = 25) -> None:
        self.max_examples = max_examples

    def _annotation_to_strategy(self, annotation) -> str:
        from hypothesis import strategies as st

        mapping = {
            int: "st.integers()",
            float: "st.floats()",
            str: "st.text()",
            bool: "st.booleans()",
        }
        return mapping.get(annotation, "st.none()")

    def generate_test_code(self, func: Callable) -> str:
        sig = inspect.signature(func)
        param_names = list(sig.parameters.keys())
        strategies = []
        for name, param in sig.parameters.items():
            strategies.append(f"{name}={self._annotation_to_strategy(param.annotation)}")

        strategies_str = ", ".join(strategies)

        lines: List[str] = [
            "from hypothesis import given, strategies as st",
            "",
            f"@given({strategies_str})",
            f"def test_{func.__name__}({', '.join(param_names)}):",
            f"    {func.__name__}({', '.join(param_names)})",
        ]
        return "\n".join(lines)
