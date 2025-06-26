from openai import AsyncOpenAI
import json

from .model_interface import ReasoningModelInterface

class OpenAIReasoningModel(ReasoningModelInterface):
    """OpenAI o1 model integration"""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "o1-preview"  # or "o1-mini" for faster/cheaper

    async def generate_fix(self, error_context, code_context, memory_context):
        # o1 models excel at reasoning through complex problems
        prompt = f"""
        Analyze this error and provide a fix using chain-of-thought reasoning:
        
        Error: {json.dumps(error_context)}
        
        Relevant Code Context (retrieved via RAG):
        {code_context}
        
        Previous Similar Fixes:
        {json.dumps(memory_context[:3])}  # Limit to fit context
        
        Reason through:
        1. Root cause analysis
        2. Why previous fixes might/might not apply
        3. Optimal solution considering the codebase patterns
        """

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1  # Lower temperature for reasoning tasks
        )

        return response.choices[0].message.content

    async def generate_tests(self, function_code: str, test_strategy: str):
        raise NotImplementedError("Test generation not implemented")

    async def validate_memory(self, memory_item, current_code: str):
        raise NotImplementedError("Memory validation not implemented")
