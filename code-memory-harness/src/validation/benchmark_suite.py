import time
import numpy as np
import resource


class PerformanceBenchmark:
    """Measure system performance metrics"""

    def __init__(self, engine):
        self.engine = engine

    async def run_benchmarks(self):
        benchmarks = {
            "indexing_speed": self.benchmark_indexing,
            "retrieval_latency": self.benchmark_retrieval,
            "context_compression": self.benchmark_compression,
            "fix_generation_time": self.benchmark_fix_generation,
            "memory_overhead": self.benchmark_memory_usage,
        }

        results = {}
        for name, benchmark in benchmarks.items():
            print(f"Running {name} benchmark...")
            results[name] = await benchmark()

        return results

    async def benchmark_indexing(self):
        start = time.time()
        self.engine.index_codebase()
        return {"seconds": time.time() - start}

    async def benchmark_compression(self):
        dummy = [
            {
                "content": "x = 1",
                "file_path": "tmp.py",
                "start_line": 1,
                "end_line": 1,
                "chunk_type": "block",
                "similarity": 1.0,
            }
        ] * 50
        start = time.time()
        self.engine.context_compressor.compress_chunks(dummy)
        return {"seconds": time.time() - start}

    async def benchmark_fix_generation(self):
        generate = getattr(self.engine, "generate_fix", None)
        if not generate:
            return {"supported": False}
        start = time.time()
        await generate({"message": "test"})
        return {"seconds": time.time() - start, "supported": True}

    async def benchmark_memory_usage(self):
        usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {"max_rss": usage}

    async def benchmark_retrieval(self):
        """Target: <100ms for 95th percentile"""
        latencies = []
        for _ in range(100):
            start = time.time()
            await self.engine.retrieve("test query")
            latencies.append(time.time() - start)

        return {
            "p50": np.percentile(latencies, 50),
            "p95": np.percentile(latencies, 95),
            "p99": np.percentile(latencies, 99),
        }
