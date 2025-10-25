from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from .schema_discovery import SchemaDiscovery
from .text_to_sql import TextToSQLConverter
from .document_processor import KeywordDocumentProcessor
from ..core.cache import cached
import logging
import time

logger = logging.getLogger(__name__)

class QueryEngine:
    """
    Main query processing engine
    - Classifies query type
    - Routes to appropriate handler
    - Caches results for performance
    """
    def __init__(
        self,
        session: AsyncSession,
        schema: Dict[str, Any],
        doc_processor: KeywordDocumentProcessor
    ):
        self.session = session
        self.schema = schema
        self.doc_processor = doc_processor
        self.text_to_sql = TextToSQLConverter()

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process natural language query:
        - Classify query type (SQL/document/hybrid)
        - Execute with caching
        - Return results with metrics
        """
        start_time = time.time()
        try:
            # Classify query type
            query_type = self._classify_query(user_query)
            
            result = {
                "query": user_query,
                "query_type": query_type,
                "results": [],
                "sources": [],
                "performance": {},
                "cached": False # This will be set by the decorator if hit
            }

            # Route to handler
            if query_type == "sql":
                sql_results = await self._handle_sql_query(user_query)
                result.update(sql_results) # merge dict
                result["results"] = sql_results.get("data")
                result["sources"] = ["database"]
            elif query_type == "document":
                doc_results = await self._handle_document_query(user_query)
                result.update(doc_results) # merge dict
                result["results"] = doc_results.get("documents")
                result["sources"] = ["documents"]
            elif query_type == "hybrid":
                sql_results = await self._handle_sql_query(user_query)
                doc_results = await self._handle_document_query(user_query)
                result["results"] = {
                    "database": sql_results,
                    "documents": doc_results
                }
                result["sources"] = ["database", "documents"]

            # Performance metrics
            end_time = time.time()
            result["performance"] = {
                "response_time": round(end_time - start_time, 3),
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Query processing error: {e}")
            return {
                "query": user_query,
                "error": str(e),
                "query_type": "unknown"
            }

    def _classify_query(self, query: str) -> str:
        """
        Classify query type:
        - sql: Database queries (counts, aggregations, filters)
        - document: Document content queries (skills, reviews)
        - hybrid: Both
        """
        query_lower = query.lower()
        
        # SQL keywords
        sql_keywords = [
            "how many", "count", "average", "total", "sum",
            "list all", "show me", "find employees", "department",
            "salary", "highest", "lowest", "hired"
        ]
        
        # Document keywords
        doc_keywords = [
            "skills", "experience", "resume", "review",
            "performance", "feedback", "qualified", "expertise",
            "python", "javascript", "java" # Technical skills
        ]
        
        sql_score = sum(1 for kw in sql_keywords if kw in query_lower)
        doc_score = sum(1 for kw in doc_keywords if kw in query_lower)

        if sql_score > 0 and doc_score > 0:
            return "hybrid"
        elif sql_score > doc_score:
            return "sql"
        elif doc_score > 0:
            return "document"
        else:
            return "sql" # Default

    @cached(prefix="sql_query", ttl=300)
    async def _handle_sql_query(self, query: str) -> Dict:
        """Handle SQL-based queries with caching"""
        # Generate SQL
        sql_result = await self.text_to_sql.generate_sql(query, self.schema)
        
        if sql_result.get("error"):
            return {"error": sql_result["error"]}
            
        # Execute SQL
        sql_query = sql_result["sql"]
        try:
            result = await self.session.execute(text(sql_query))
            rows = result.fetchall()
            
            # Convert to list of dicts
            columns = result.keys()
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "sql": sql_query,
                "data": data,
                "row_count": len(data)
            }
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            return {"error": f"SQL execution failed: {str(e)}"}

    async def _handle_document_query(self, query: str) -> Dict:
        """Handle document-based queries"""
        results = await self.doc_processor.search(query, top_k=5)
        return {
            "documents": results,
            "count": len(results)
        }