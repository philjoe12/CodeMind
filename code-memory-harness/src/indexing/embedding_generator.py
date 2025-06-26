import openai
from typing import List, Optional
import numpy as np
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import os
from sentence_transformers import SentenceTransformer

class EmbeddingGenerator:
    """Generate embeddings for code chunks"""
    
    def __init__(self, provider: str = "openai", model_name: Optional[str] = None, api_key: Optional[str] = None):
        self.provider = provider
        
        if provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key required")
            openai.api_key = self.api_key
            self.model_name = model_name or "text-embedding-ada-002"
            self.dimension = 1536
            
        elif provider == "local":
            # Use sentence-transformers for local embeddings
            self.model_name = model_name or "microsoft/codebert-base"
            self.model = SentenceTransformer(self.model_name)
            self.dimension = self.model.get_sentence_embedding_dimension()
        
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        if self.provider == "openai":
            response = openai.Embedding.create(
                input=text,
                model=self.model_name
            )
            return np.array(response['data'][0]['embedding'], dtype=np.float32)
            
        elif self.provider == "local":
            # Add code-specific prefix for better embeddings
            code_text = f"Code: {text}"
            embedding = self.model.encode(code_text)
            return np.array(embedding, dtype=np.float32)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[np.ndarray]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        
        if self.provider == "openai":
            # OpenAI supports batch embedding
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                response = openai.Embedding.create(
                    input=batch,
                    model=self.model_name
                )
                batch_embeddings = [np.array(item['embedding'], dtype=np.float32) 
                                  for item in response['data']]
                embeddings.extend(batch_embeddings)
                
                # Rate limiting
                if i + batch_size < len(texts):
                    time.sleep(0.1)
                    
        elif self.provider == "local":
            # Local models can handle larger batches
            code_texts = [f"Code: {text}" for text in texts]
            embeddings = self.model.encode(code_texts, batch_size=batch_size)
            embeddings = [np.array(emb, dtype=np.float32) for emb in embeddings]
        
        return embeddings
