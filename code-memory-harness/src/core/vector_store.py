import faiss
import numpy as np
import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import hashlib
from dataclasses import dataclass
import json

@dataclass
class CodeChunk:
    """Represents a chunk of code with metadata"""
    content: str
    file_path: str
    start_line: int
    end_line: int
    chunk_type: str  # 'function', 'class', 'module', 'block'
    language: str
    embedding: Optional[np.ndarray] = None
    chunk_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.chunk_id:
            # Generate unique ID based on content and location
            unique_str = f"{self.file_path}:{self.start_line}:{self.end_line}:{self.content[:50]}"
            self.chunk_id = hashlib.md5(unique_str.encode()).hexdigest()

class SimpleVectorStore:
    """FAISS-based vector store for code embeddings"""
    
    def __init__(self, dimension: int = 1536, index_path: Optional[str] = None):
        self.dimension = dimension
        self.index_path = index_path or "vector_store.index"
        self.metadata_path = index_path.replace('.index', '_metadata.pkl') if index_path else "vector_store_metadata.pkl"
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.id_to_chunk: Dict[int, CodeChunk] = {}
        self.chunk_id_to_index: Dict[str, int] = {}
        self.current_idx = 0
        
    def add_chunks(self, chunks: List[CodeChunk]):
        """Add code chunks with their embeddings to the store"""
        embeddings = []
        valid_chunks = []
        
        for chunk in chunks:
            if chunk.embedding is not None:
                embeddings.append(chunk.embedding)
                valid_chunks.append(chunk)
        
        if not embeddings:
            return
        
        # Convert to numpy array
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS index
        self.index.add(embeddings_array)
        
        # Store metadata
        for chunk in valid_chunks:
            self.id_to_chunk[self.current_idx] = chunk
            self.chunk_id_to_index[chunk.chunk_id] = self.current_idx
            self.current_idx += 1
    
    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[CodeChunk, float]]:
        """Search for similar code chunks"""
        if self.index.ntotal == 0:
            return []
        
        # Ensure query embedding is the right shape
        query_embedding = np.array([query_embedding], dtype=np.float32)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        # Return chunks with distances
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1 and idx in self.id_to_chunk:
                chunk = self.id_to_chunk[idx]
                # Convert L2 distance to similarity score (0-1)
                similarity = 1 / (1 + distance)
                results.append((chunk, similarity))
        
        return results
    
    def save(self):
        """Persist the vector store to disk"""
        # Save FAISS index
        faiss.write_index(self.index, self.index_path)
        
        # Save metadata
        with open(self.metadata_path, 'wb') as f:
            pickle.dump({
                'id_to_chunk': self.id_to_chunk,
                'chunk_id_to_index': self.chunk_id_to_index,
                'current_idx': self.current_idx
            }, f)
    
    def load(self):
        """Load vector store from disk"""
        if Path(self.index_path).exists() and Path(self.metadata_path).exists():
            # Load FAISS index
            self.index = faiss.read_index(self.index_path)
            
            # Load metadata
            with open(self.metadata_path, 'rb') as f:
                metadata = pickle.load(f)
                self.id_to_chunk = metadata['id_to_chunk']
                self.chunk_id_to_index = metadata['chunk_id_to_index']
                self.current_idx = metadata['current_idx']
            
            return True
        return False
