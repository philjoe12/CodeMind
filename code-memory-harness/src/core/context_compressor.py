from typing import List, Dict
import tiktoken

class ContextCompressor:
    """Compress retrieved chunks to fit within token limits"""
    
    def __init__(self, model: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model)
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    def compress_chunks(self, chunks: List[Dict], max_tokens: int = 3000) -> str:
        """Compress chunks to fit within token limit while preserving information"""
        
        # Sort chunks by relevance
        chunks_sorted = sorted(chunks, key=lambda x: x['similarity'], reverse=True)
        
        compressed_context = []
        total_tokens = 0
        
        for chunk in chunks_sorted:
            # Format chunk with metadata
            chunk_text = self._format_chunk(chunk)
            chunk_tokens = self.count_tokens(chunk_text)
            
            # Check if adding this chunk would exceed limit
            if total_tokens + chunk_tokens > max_tokens:
                # Try to add a compressed version
                compressed_chunk = self._compress_single_chunk(chunk, max_tokens - total_tokens)
                if compressed_chunk:
                    compressed_context.append(compressed_chunk)
                    total_tokens += self.count_tokens(compressed_chunk)
                break
            else:
                compressed_context.append(chunk_text)
                total_tokens += chunk_tokens
        
        return "\n\n---\n\n".join(compressed_context)
    
    def _format_chunk(self, chunk: Dict) -> str:
        """Format a chunk with metadata"""
        header = f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']})"
        return f"{header}\n```\n{chunk['content']}\n```"
    
    def _compress_single_chunk(self, chunk: Dict, available_tokens: int) -> str:
        """Compress a single chunk to fit within available tokens"""
        
        # Simple compression: take first N lines that fit
        lines = chunk['content'].split('\n')
        compressed_lines = []
        
        header = f"File: {chunk['file_path']} (lines {chunk['start_line']}-{chunk['end_line']}) [TRUNCATED]"
        current_tokens = self.count_tokens(header) + 10  # Buffer for formatting
        
        for line in lines:
            line_tokens = self.count_tokens(line)
            if current_tokens + line_tokens > available_tokens:
                break
            compressed_lines.append(line)
            current_tokens += line_tokens
        
        if compressed_lines:
            return f"{header}\n```\n{chr(10).join(compressed_lines)}\n```"
        
        return None
