"""
Quick MVP to demonstrate core functionality
"""

import asyncio

from src.core.memory_engine import MemoryEngine
from src.ai_integration.openai_reasoning import OpenAIReasoningModel


async def quick_mvp_demo() -> bool:
    """Run a short demo showing how the memory engine can be used."""
    # 1. Initialize with a small codebase
    engine = MemoryEngine(
        codebase_path="./examples/simple_python_project",
        model=OpenAIReasoningModel(api_key="your-key"),
    )

    # 2. Index the codebase
    print("Indexing codebase...")
    await engine.index_codebase()

    # 3. Simulate an error
    error = {
        "type": "AttributeError",
        "message": "'NoneType' object has no attribute 'split'",
        "file": "data_processor.py",
        "line": 42,
    }

    # 4. Get AI-powered fix with memory context
    print("Generating fix...")
    fix = await engine.generate_fix(error)
    print(f"Suggested fix: {fix}")

    # 5. Generate tests for the fix
    print("Generating tests...")
    tests = await engine.generate_stochastic_tests(fix)

    # 6. Validate the fix works
    print("Validating fix...")
    validation = await engine.validate_fix(fix, tests)

    return validation


# Run: python -m asyncio examples.quickstart
