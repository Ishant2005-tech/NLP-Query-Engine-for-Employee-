from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import uuid
import os
from ...services.document_processor import KeywordDocumentProcessor
from ...core.config import settings
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["documents"])

# Global document processor
doc_processor = KeywordDocumentProcessor()

# Job status storage
job_status = {}

class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    processed: int
    total: int
    details: dict | None = None
    error: str | None = None

async def process_documents_task(job_id: str, file_paths: List[str]):
    """Background task to process documents"""
    try:
        result = await doc_processor.process_documents(file_paths)
        job_status[job_id] = {
            "status": "completed",
            "progress": 1.0,
            "processed": result["processed"],
            "total": result["processed"] + result["failed"], # Corrected typo from PDF
            "details": result
        }
    except Exception as e:
        logger.error(f"Processing error: {e}")
        job_status[job_id] = {
            "status": "failed",
            "progress": 0.0,
            "error": str(e)
        }

@router.post("/upload", response_model=UploadResponse)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload and process documents"""
    try:
        job_id = str(uuid.uuid4())
        
        # Save files
        file_paths = []
        for file in files:
            # Validate file type
            ext = file.filename.split('.')[-1].lower()
            if ext not in ['pdf', 'docx', 'txt']:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type not allowed: {ext}"
                )
                
            # Validate size
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
            if size > settings.MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large: {file.filename}"
                )
                
            # Save file
            file_path = os.path.join(
                settings.UPLOAD_DIR,
                f"{job_id}_{file.filename}"
            )
            with open(file_path, 'wb') as f:
                content = await file.read()
                f.write(content)
            file_paths.append(file_path)
            
        # Initialize job status
        job_status[job_id] = {
            "status": "processing",
            "progress": 0.0,
            "processed": 0,
            "total": len(files)
        }
        
        # Process in background
        background_tasks.add_task(
            process_documents_task,
            job_id,
            file_paths
        )
        
        return UploadResponse(
            job_id=job_id,
            status="processing",
            message=f"Processing {len(files)} documents"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Get document processing status"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
        
    status = job_status[job_id]
    
    return StatusResponse(
        job_id=job_id,
        status=status["status"],
        progress=status["progress"],
        processed=status.get("processed", 0),
        total=status.get("total", 0),
        details=status.get("details"),
        error=status.get("error")
    )