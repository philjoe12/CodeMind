import json
import anthropic

from .model_interface import ReasoningModelInterface

class ClaudeReasoningModel(ReasoningModelInterface):
    """Claude-3 Opus integration with advanced reasoning"""

    def __init__(self, api_key: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-opus-20240229"

    async def generate_fix(self, error_context, code_context, memory_context):
        # Claude excels at nuanced code understanding
        prompt = f"""
        <error_analysis>
        Error Details: {json.dumps(error_context)}
        
        Retrieved Code Context:
        ```
        {code_context}
        ```
        
        Historical Fixes for Similar Errors:
        {self._format_memory_context(memory_context)}
        </error_analysis>
        
        Please analyze this error using systematic reasoning:
        1. Identify the error category and root cause
        2. Evaluate if historical fixes apply
        3. Propose a fix that maintains code consistency
        4. Explain potential side effects
        """

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    async def generate_tests(self, function_code: str, test_strategy: str):
        raise NotImplementedError("Test generation not implemented")

    async def validate_memory(self, memory_item, current_code: str):
        raise NotImplementedError("Memory validation not implemented")

    def _format_memory_context(self, memory_context):
        return "\n".join(json.dumps(item) for item in memory_context[:3])
