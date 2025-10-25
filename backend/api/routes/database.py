from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ...core.database import get_db
from ...services.schema_discovery import SchemaDiscovery
from pydantic import BaseModel
from ...core.cache import cache
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/database", tags=["database"])

class DatabaseConnection(BaseModel):
    connection_string: str
    test_connection: bool = True

class ConnectionResponse(BaseModel):
    success: bool
    message: str
    schema_summary: dict

@router.post("/connect", response_model=ConnectionResponse)
async def connect_database(
    connection: DatabaseConnection,
    db: AsyncSession = Depends(get_db)
):
    """Connect to database and discover schema"""
    try:
        # Test connection
        if connection.test_connection:
            await db.execute(text("SELECT 1"))
            
        # Discover schema
        schema_discovery = SchemaDiscovery(db)
        schema = await schema_discovery.analyze_database()
        
        # Store in cache
        await cache.set("database_schema", schema, ttl=3600)
        
        return ConnectionResponse(
            success=True,
            message="Database connected successfully",
            schema_summary=schema["summary"]
        )
    except Exception as e:
        logger.error(f"Connection error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/schema")
async def get_schema():
    """Get discovered schema"""
    schema = await cache.get("database_schema")
    if not schema:
        raise HTTPException(
            status_code=404,
            detail="No schema found. Connect to database first."
        )
    return schema