import ast
import os
from typing import List, Optional, Tuple
from pathlib import Path
import re

from src.core.vector_store import CodeChunk

class CodeParser:
    """Parse code files into semantic chunks"""
    
    def __init__(self, chunk_size: int = 50, overlap: int = 10):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.supported_extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust'
        }
    
    def parse_file(self, file_path: str) -> List[CodeChunk]:
        """Parse a single file into code chunks"""
        path = Path(file_path)
        
        if path.suffix not in self.supported_extensions:
            return []
        
        language = self.supported_extensions[path.suffix]
        
        try:
            content = path.read_text(encoding='utf-8')
        except:
            return []
        
        # Use language-specific parser
        if language == 'python':
            return self._parse_python(content, file_path)
        else:
            # Fallback to line-based chunking for other languages
            return self._parse_generic(content, file_path, language)
    
    def _parse_python(self, content: str, file_path: str) -> List[CodeChunk]:
        """Parse Python code using AST"""
        chunks = []
        
        try:
            tree = ast.parse(content)
        except:
            # If AST parsing fails, fall back to generic parsing
            return self._parse_generic(content, file_path, 'python')
        
        # Extract module-level docstring
        module_docstring = ast.get_docstring(tree)
        if module_docstring:
            chunks.append(CodeChunk(
                content=module_docstring,
                file_path=file_path,
                start_line=1,
                end_line=len(module_docstring.split('\n')),
                chunk_type='module',
                language='python'
            ))
        
        # Extract classes and functions
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                chunk = self._extract_class_chunk(node, content, file_path)
                if chunk:
                    chunks.append(chunk)
                    
            elif isinstance(node, ast.FunctionDef):
                # Only top-level functions (not methods)
                if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) 
                          if hasattr(parent, 'body') and node in parent.body):
                    chunk = self._extract_function_chunk(node, content, file_path)
                    if chunk:
                        chunks.append(chunk)
        
        # Also add reasonable-sized code blocks
        lines = content.split('\n')
        for i in range(0, len(lines), self.chunk_size - self.overlap):
            end = min(i + self.chunk_size, len(lines))
            chunk_content = '\n'.join(lines[i:end])
            
            # Skip if this chunk is mostly empty
            if len(chunk_content.strip()) < 10:
                continue
                
            chunks.append(CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=i + 1,
                end_line=end,
                chunk_type='block',
                language='python'
            ))
        
        return chunks
    
    def _extract_class_chunk(self, node: ast.ClassDef, content: str, file_path: str) -> Optional[CodeChunk]:
        """Extract a class definition as a chunk"""
        lines = content.split('\n')
        
        # Get the class definition and its immediate methods
        start_line = node.lineno - 1
        end_line = start_line
        
        # Find the end of the class
        for child in node.body:
            if hasattr(child, 'lineno'):
                end_line = max(end_line, getattr(child, 'end_lineno', child.lineno))
        
        # Include some context
        start_line = max(0, start_line - 2)
        end_line = min(len(lines), end_line + 2)
        
        chunk_content = '\n'.join(lines[start_line:end_line])
        
        return CodeChunk(
            content=chunk_content,
            file_path=file_path,
            start_line=start_line + 1,
            end_line=end_line,
            chunk_type='class',
            language='python'
        )
    
    def _extract_function_chunk(self, node: ast.FunctionDef, content: str, file_path: str) -> Optional[CodeChunk]:
        """Extract a function definition as a chunk"""
        lines = content.split('\n')
        
        start_line = node.lineno - 1
        end_line = getattr(node, 'end_lineno', node.lineno)
        
        # Include decorators and some context
        for decorator in node.decorator_list:
            if hasattr(decorator, 'lineno'):
                start_line = min(start_line, decorator.lineno - 1)
        
        start_line = max(0, start_line - 1)
        end_line = min(len(lines), end_line + 1)
        
        chunk_content = '\n'.join(lines[start_line:end_line])
        
        return CodeChunk(
            content=chunk_content,
            file_path=file_path,
            start_line=start_line + 1,
            end_line=end_line,
            chunk_type='function',
            language='python'
        )
    
    def _parse_generic(self, content: str, file_path: str, language: str) -> List[CodeChunk]:
        """Generic parsing for non-Python languages"""
        chunks = []
        lines = content.split('\n')
        
        # Simple heuristic: look for function/class definitions
        function_patterns = {
            'javascript': r'(function\s+\w+|const\s+\w+\s*=\s*\(|class\s+\w+)',
            'typescript': r'(function\s+\w+|const\s+\w+\s*=\s*\(|class\s+\w+)',
            'java': r'(public|private|protected)?\s*(static)?\s*(class|interface|void|int|String)',
            'go': r'func\s+(\(\w+\s+\*?\w+\))?\s*\w+',
            'rust': r'(fn\s+\w+|struct\s+\w+|impl\s+\w+)',
            'c': r'(\w+\s+)?\w+\s*\([^)]*\)\s*{',
            'cpp': r'(class\s+\w+|(\w+\s+)?\w+\s*\([^)]*\)\s*{)'
        }
        
        pattern = function_patterns.get(language)
        
        if pattern:
            # Find function/class boundaries
            boundaries = []
            for i, line in enumerate(lines):
                if re.search(pattern, line):
                    boundaries.append(i)
            
            # Create chunks around these boundaries
            for i, start in enumerate(boundaries):
                end = boundaries[i + 1] if i + 1 < len(boundaries) else min(start + self.chunk_size, len(lines))
                
                chunk_content = '\n'.join(lines[start:end])
                chunks.append(CodeChunk(
                    content=chunk_content,
                    file_path=file_path,
                    start_line=start + 1,
                    end_line=end,
                    chunk_type='function',
                    language=language
                ))
        
        # Also add regular chunks
        for i in range(0, len(lines), self.chunk_size - self.overlap):
            end = min(i + self.chunk_size, len(lines))
            chunk_content = '\n'.join(lines[i:end])
            
            if len(chunk_content.strip()) < 10:
                continue
                
            chunks.append(CodeChunk(
                content=chunk_content,
                file_path=file_path,
                start_line=i + 1,
                end_line=end,
                chunk_type='block',
                language=language
            ))
        
        return chunks
