import os
import json
from typing import List, Dict, Any
import PyPDF2
import docx
import re
from collections import defaultdict
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)

class KeywordDocumentProcessor:
    """
    Simple keyword-based document search
    - No ML dependencies
    - Fast and reliable
    - "Good engineering over complex solutions"
    """
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.keyword_index: Dict[str, List[int]] = defaultdict(list)
        self.index_file = os.path.join(settings.INDEX_DIR, "keyword_index.json")
        
        # Create directories
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        os.makedirs(settings.INDEX_DIR, exist_ok=True)
        
        # Load existing index
        self._load_index()

    async def process_documents(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Process documents with keyword extraction:
        - Extract text from files
        - Build keyword index
        - Store for fast retrieval
        """
        results = {
            "processed": 0,
            "failed": 0,
            "total_documents": 0,
            "documents": []
        }
        
        for file_path in file_paths:
            try:
                # Extract text
                text = self._extract_text(file_path)
                
                # Extract keywords
                keywords = self._extract_keywords(text)
                
                # Store document
                doc_id = len(self.documents)
                doc = {
                    "id": doc_id,
                    "file": os.path.basename(file_path),
                    "text": text,
                    "keywords": list(keywords),
                    "preview": text[:200] + "..." if len(text) > 200 else text
                }
                self.documents.append(doc)
                
                # Update keyword index
                for keyword in keywords:
                    self.keyword_index[keyword.lower()].append(doc_id)
                    
                results["processed"] += 1
                results["documents"].append({
                    "file": doc["file"],
                    "keywords_found": len(keywords)
                })
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results["failed"] += 1
                
        results["total_documents"] = len(self.documents)
        
        # Save index
        self._save_index()
        logger.info(f"Processed {results['processed']} documents")
        return results

    def _extract_text(self, file_path: str) -> str:
        """Extract text from different file formats"""
        ext = file_path.split('.')[-1].lower()
        if ext == 'pdf':
            return self._extract_pdf(file_path)
        elif ext == 'docx':
            return self._extract_docx(file_path)
        elif ext == 'txt':
            return self._extract_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        text = ""
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
        return text

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT"""
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

    def _extract_keywords(self, text: str) -> set:
        """
        Extract meaningful keywords:
        - Remove common words (stopwords)
        - Extract technical terms, skills, etc.
        """
        # Simple tokenization
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Common stopwords
        stopwords = {
            'the', 'is', 'at', 'which', 'on', 'and', 'a', 'an', 'as', 'are',
            'was', 'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'with', 'from', 'for',
            'but', 'not', 'all', 'any', 'some', 'such', 'into', 'just', 'than',
            'very', 'too', 'also', 'only', 'then', 'when', 'where', 'how', 'why'
        }
        
        # Filter keywords
        keywords = {w for w in words if w not in stopwords and len(w) > 2}
        return keywords

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Keyword-based search:
        - Extract keywords from query
        - Find documents with matching keywords
        - Rank by number of matches
        """
        # Extract query keywords
        query_keywords = self._extract_keywords(query)
        if not query_keywords:
            return []
            
        # Find matching documents
        doc_scores = defaultdict(int)
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.keyword_index:
                for doc_id in self.keyword_index[keyword_lower]:
                    doc_scores[doc_id] += 1
                    
        # Sort by score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1], reverse=True
        )[:top_k]
        
        # Get document details
        results = []
        for doc_id, score in sorted_docs:
            if doc_id < len(self.documents):
                doc = self.documents[doc_id].copy()
                doc["match_score"] = score
                doc["matched_keywords"] = [
                    kw for kw in query_keywords
                    if kw.lower() in doc["keywords"]
                ]
                results.append(doc)
        return results

    def _save_index(self):
        """Save keyword index to disk"""
        try:
            index_data = {
                "documents": self.documents,
                "keyword_index": {
                    k: list(v) for k, v in self.keyword_index.items()
                }
            }
            with open(self.index_file, 'w') as f:
                json.dump(index_data, f)
        except Exception as e:
            logger.error(f"Error saving index: {e}")

    def _load_index(self):
        """Load keyword index from disk"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as f:
                    index_data = json.load(f)
                    self.documents = index_data.get("documents", [])
                    self.keyword_index = defaultdict(
                        list,
                        {k: v for k, v in index_data.get("keyword_index", {}).items()}
                    )
                logger.info(f"Loaded {len(self.documents)} documents from index")
        except Exception as e:
            logger.error(f"Error loading index: {e}")