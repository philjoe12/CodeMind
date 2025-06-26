from pathlib import Path
from typing import List, Dict, Optional, Tuple
import json
import logging
from datetime import datetime

from src.core.vector_store import SimpleVectorStore, CodeChunk
from src.indexing.code_parser import CodeParser
from src.indexing.embedding_generator import EmbeddingGenerator
from src.core.context_compressor import ContextCompressor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MemoryEngine:
    """Main orchestration engine for the code memory system"""
    
    def __init__(self, 
                 codebase_path: str,
                 vector_store_path: Optional[str] = None,
                 embedding_provider: str = "openai",
                 api_key: Optional[str] = None):
        
        self.codebase_path = Path(codebase_path)
        self.vector_store = SimpleVectorStore(
            dimension=1536 if embedding_provider == "openai" else 768,
            index_path=vector_store_path
        )
        
        self.parser = CodeParser()
        self.embedding_generator = EmbeddingGenerator(
            provider=embedding_provider,
            api_key=api_key
        )
        self.context_compressor = ContextCompressor()
        
        # Try to load existing index
        if self.vector_store.load():
            logger.info("Loaded existing vector store")
        
    def index_codebase(self, file_extensions: Optional[List[str]] = None):
        """Index the entire codebase"""
        if file_extensions is None:
            file_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.c', '.cpp']
        
        all_chunks = []
        files_processed = 0
        
        # Walk through codebase
        for file_path in self.codebase_path.rglob('*'):
            # Skip common non-code directories
            if any(part in file_path.parts for part in ['.git', '__pycache__', 'node_modules', '.env']):
                continue
                
            if file_path.is_file() and file_path.suffix in file_extensions:
                logger.info(f"Processing {file_path}")
                
                # Parse file into chunks
                chunks = self.parser.parse_file(str(file_path))
                
                if chunks:
                    all_chunks.extend(chunks)
                    files_processed += 1
        
        logger.info(f"Parsed {len(all_chunks)} chunks from {files_processed} files")
        
        # Generate embeddings in batches
        logger.info("Generating embeddings...")
        chunk_texts = [chunk.content for chunk in all_chunks]
        embeddings = self.embedding_generator.generate_embeddings_batch(chunk_texts)
        
        # Assign embeddings to chunks
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk.embedding = embedding
        
        # Add to vector store
        self.vector_store.add_chunks(all_chunks)
        
        # Save index
        self.vector_store.save()
        logger.info(f"Indexed {len(all_chunks)} chunks successfully")
        
        return len(all_chunks)
    
    def retrieve(self, 
                query: str, 
                k: int = 5,
                file_filter: Optional[List[str]] = None,
                min_similarity: float = 0.3) -> List[Dict]:
        """Retrieve relevant code chunks for a query"""
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(query_embedding, k=k*2)  # Get more results for filtering
        
        # Filter results
        filtered_results = []
        for chunk, similarity in results:
            # Apply similarity threshold
            if similarity < min_similarity:
                continue
                
            # Apply file filter if specified
            if file_filter and not any(f in chunk.file_path for f in file_filter):
                continue
                
            filtered_results.append({
                'content': chunk.content,
                'file_path': chunk.file_path,
                'start_line': chunk.start_line,
                'end_line': chunk.end_line,
                'chunk_type': chunk.chunk_type,
                'similarity': similarity
            })
            
            if len(filtered_results) >= k:
                break
        
        return filtered_results
    
    def get_context_for_error(self, 
                             error: Dict,
                             max_tokens: int = 3000) -> str:
        """Get relevant context for an error"""
        
        # Build query from error information
        query_parts = []
        
        if 'message' in error:
            query_parts.append(error['message'])
        
        if 'type' in error:
            query_parts.append(f"error type: {error['type']}")
            
        if 'file' in error:
            query_parts.append(f"in file {error['file']}")
            
        if 'function' in error:
            query_parts.append(f"function {error['function']}")
        
        query = " ".join(query_parts)
        
        # Retrieve relevant chunks
        chunks = self.retrieve(query, k=10)
        
        # If error has a specific file, prioritize chunks from that file
        if 'file' in error:
            chunks.sort(key=lambda x: 0 if error['file'] in x['file_path'] else 1)
        
        # Compress context to fit token limit
        context = self.context_compressor.compress_chunks(chunks, max_tokens)
        
        return context
    
    def update_chunk(self, file_path: str, start_line: int, end_line: int, new_content: str):
        """Update a specific chunk (for incremental updates)"""
        # This would be implemented for real-time updates
        # For MVP, we'll re-index the file
        chunks = self.parser.parse_file(file_path)
        
        # Generate embeddings for new chunks
        chunk_texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings_batch(chunk_texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Update vector store (would need to implement removal of old chunks)
        self.vector_store.add_chunks(chunks)
        self.vector_store.save()
