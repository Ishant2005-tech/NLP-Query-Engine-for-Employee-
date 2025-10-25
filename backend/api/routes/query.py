from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...services.query_engine import QueryEngine
from ...core.cache import cache
from pydantic import BaseModel
from typing import Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/query", tags=["query"])

# Query history
query_history = []

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    query_type: str
    results: Any
    sources: list
    performance: dict
    cached: bool = False

@router.post("/", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """Process natural language query"""
    try:
        # Get schema
        schema = await cache.get("database_schema")
        if not schema:
            raise HTTPException(
                status_code=400,
                detail="Database not connected. Please connect first."
            )
            
        # Get document processor (from the global instance in documents.py)
        from .documents import doc_processor
        
        # Create query engine
        engine = QueryEngine(db, schema, doc_processor)
        
        # Process query
        result = await engine.process_query(request.query)
        
        # Add to history
        query_history.append({
            "query": request.query,
            "timestamp": str(datetime.now()),
            "query_type": result["query_type"]
        })
        
        # Check if result was cached (decorator adds this)
        if result.get("cached", False):
             result["performance"]["cached"] = True

        return QueryResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history")
async def get_history():
    """Get query history"""
    return {"history": query_history[-50:]} # Return last 50 queries