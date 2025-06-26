import asyncio
from pathlib import Path
import yaml

class MVPValidator:
    """Validates the memory harness with real scenarios"""
    
    def __init__(self, config_path: str):
        self.config = yaml.safe_load(Path(config_path).read_text())
        self.results = []
        
    async def validate_mvp(self):
        """Run comprehensive validation suite"""
        
        # 1. Validate RAG accuracy
        print("🔍 Testing RAG retrieval accuracy...")
        rag_results = await self.test_rag_accuracy()
        
        # 2. Validate context compression
        print("📦 Testing context compression...")
        compression_results = await self.test_context_compression()
        
        # 3. Validate error fix generation
        print("🔧 Testing error fix generation...")
        fix_results = await self.test_error_fixes()
        
        # 4. Validate stochastic test generation
        print("🎲 Testing stochastic test generation...")
        test_gen_results = await self.test_generation_quality()
        
        # 5. End-to-end workflow test
        print("🔄 Testing end-to-end workflow...")
        e2e_results = await self.test_full_workflow()
        
        return self.compile_results()
    
    async def test_rag_accuracy(self):
        """Test: Can we retrieve relevant code given a query?"""
        test_cases = [
            {
                "query": "function that handles user authentication",
                "expected_files": ["auth.py", "middleware/auth.js"],
                "expected_relevance": 0.8
            },
            {
                "query": "database connection error handling",
                "expected_patterns": ["try/except", "connection.close()"],
                "expected_relevance": 0.75
            }
        ]
        
        results = []
        for test in test_cases:
            retrieved = await self.memory_harness.retrieve(test["query"])
            relevance = self.calculate_relevance(retrieved, test)
            results.append({
                "test": test["query"],
                "passed": relevance >= test["expected_relevance"],
                "relevance": relevance
            })
        
        return results

