from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.models.boq_file import BOQFile
from app.services.file_service import FileService
from app.utils.excel_processor import ExcelProcessor
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class ProcessFileRequest(BaseModel):
    column_mapping: Dict[str, str]
    has_headers: Optional[bool] = True
    sheet_name: Optional[str] = None
    auto_build_master: Optional[bool] = False  # Auto build master database after processing


@router.post("/upload", status_code=201)
async def upload_file(
    project_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload a BOQ Excel file
    Step 1: Upload file and analyze structure
    """
    # Validate file extension
    if not file.filename.endswith(tuple(settings.ALLOWED_EXTENSIONS)):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    try:
        service = FileService(db)
        processor = ExcelProcessor()
        
        # Calculate file hash
        file_content = await file.read()
        await file.seek(0)
        file_hash = processor.calculate_file_hash(file_content)

        # Check for duplicates
        existing_file = service.check_duplicate(file_hash)
        if existing_file:
            # Analyze structure even for duplicate files
            structure = service.analyze_file_structure(existing_file.file_path)
            return {
                "message": "File already exists",
                "file_id": existing_file.file_id,
                "filename": existing_file.file_name,
                "structure": structure,
                "is_duplicate": True
            }

        # Save file to disk
        file_path = service.save_uploaded_file(file.file, file.filename, project_id)
        
        # Analyze structure
        structure = service.analyze_file_structure(file_path)
        
        # Create BOQ file record
        boq_file = BOQFile(
            project_id=project_id,
            file_name=file.filename,
            file_hash=file_hash,
            file_path=file_path,
            total_rows=0,
            uploaded_by=current_user.user_id
        )
        db.add(boq_file)
        db.commit()
        db.refresh(boq_file)
        
        return {
            "file_id": boq_file.file_id,
            "filename": file.filename,
            "structure": structure,
            "message": "File uploaded successfully. Please confirm column mapping to process."
        }
    
    except Exception as e:
        logger.error(f"Error uploading file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{file_id}/process")
async def process_file(
    file_id: int,
    request: ProcessFileRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Process uploaded file with confirmed column mapping
    Step 2: Parse, clean, classify and save data

    Optional: Auto-build master database after processing
    """
    service = FileService(db)

    # Get file record
    boq_file = service.get_file(file_id)
    if not boq_file:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        # Process file (this might take a while for large files)
        result = service.process_file(
            file_id=file_id,
            file_path=boq_file.file_path,
            column_mapping=request.column_mapping,
            user_id=current_user.user_id
        )

        # Auto-build master database if requested
        master_stats = None
        if request.auto_build_master:
            from app.services.master_data_service import MasterDataService

            master_service = MasterDataService(db)
            master_stats = master_service.build_master_from_file(
                file_id=file_id,
                min_confidence=60.0,
                skip_unclassified=False
            )

        response = {
            "message": "File processed successfully",
            **result
        }

        if master_stats:
            response["master_build"] = master_stats

        return response

    except Exception as e:
        logger.error(f"Error processing file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}")
async def get_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get BOQ file details"""
    service = FileService(db)
    boq_file = service.get_file(file_id)
    
    if not boq_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {
        "file_id": boq_file.file_id,
        "project_id": boq_file.project_id,
        "file_name": boq_file.file_name,
        "total_rows": boq_file.total_rows,
        "total_amount": float(boq_file.total_amount) if boq_file.total_amount else 0,
        "status": boq_file.status,
        "uploaded_at": boq_file.uploaded_at,
        "uploaded_by": boq_file.uploaded_by
    }


@router.get("/project/{project_id}")
async def get_project_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all files for a project"""
    service = FileService(db)
    files = service.get_files_by_project(project_id)
    
    return {
        "project_id": project_id,
        "total_files": len(files),
        "files": [
            {
                "file_id": f.file_id,
                "file_name": f.file_name,
                "total_rows": f.total_rows,
                "total_amount": float(f.total_amount) if f.total_amount else 0,
                "status": f.status,
                "uploaded_at": f.uploaded_at
            }
            for f in files
        ]
    }


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete BOQ file"""
    service = FileService(db)
    success = service.delete_file(file_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    
    return None
