from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import os
import aiofiles
from datetime import datetime
from app.database.database import get_db
from app.routers.auth import get_current_user
from app.models.models import User, Check, CheckFile, CheckStatus, EngineeringSystem, NTDDocument
from app.schemas.schemas import CheckCreate, CheckResponse, CheckResultResponse, NTDDocumentCreate, NTDDocumentUpdate, NTDDocumentResponse, NTDCategory
from app.config import settings

router = APIRouter(prefix="/checks", tags=["Checks"])


@router.post("", response_model=CheckResponse)
async def create_check(
    check_data: CheckCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check = Check(
        user_id=current_user.id,
        name=check_data.name,
        engineering_system=check_data.engineering_system,
        mode=check_data.mode.value,
        ai_model=check_data.ai_model,
        status=CheckStatus.PENDING
    )
    db.add(check)
    await db.commit()
    await db.refresh(check)
    return check


@router.get("", response_model=List[CheckResponse])
async def get_checks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    # Admin sees all, others see only their own
    if current_user.role.value == "admin":
        result = await db.execute(select(Check))
    else:
        result = await db.execute(select(Check).where(Check.user_id == current_user.id))
    checks = result.scalars().all()
    return checks


@router.get("/{check_id}", response_model=CheckResponse)
async def get_check(
    check_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    result = await db.execute(select(Check).where(Check.id == check_id))
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    # Check access
    if current_user.role.value != "admin" and check.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return check


@router.post("/{check_id}/upload")
async def upload_files(
    check_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    result = await db.execute(select(Check).where(Check.id == check_id))
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    if current_user.role.value != "admin" and check.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    uploaded_files = []
    
    for file in files:
        ext = file.filename.split(".")[-1].lower()
        if ext not in settings.ALLOWED_EXTENSIONS:
            continue
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        check_file = CheckFile(
            check_id=check_id,
            file_name=file.filename,
            file_path=file_path,
            file_type=ext
        )
        db.add(check_file)
        uploaded_files.append({
            "file_name": file.filename,
            "file_path": file_path,
            "file_type": ext,
            "file_size": len(content)
        })
    
    await db.commit()
    return {"uploaded_files": uploaded_files}


@router.get("/ntd", response_model=List[NTDDocumentResponse])
async def get_ntd_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from sqlalchemy import select
    result = await db.execute(select(NTDDocument).where(NTDDocument.is_actual == True))
    documents = result.scalars().all()
    return documents


@router.post("/ntd", response_model=NTDDocumentResponse)
async def add_ntd_document(
    doc_data: NTDDocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    doc = NTDDocument(**doc_data.model_dump())
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


@router.put("/ntd/{doc_id}", response_model=NTDDocumentResponse)
async def update_ntd_document(
    doc_id: int,
    doc_data: NTDDocumentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    from sqlalchemy import select
    result = await db.execute(select(NTDDocument).where(NTDDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    update_data = {k: v for k, v in doc_data.model_dump().items() if v is not None}
    for key, value in update_data.items():
        setattr(doc, key, value)
    
    await db.commit()
    await db.refresh(doc)
    return doc


@router.delete("/ntd/{doc_id}")
async def delete_ntd_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    from sqlalchemy import select, delete
    result = await db.execute(select(NTDDocument).where(NTDDocument.id == doc_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    await db.execute(delete(NTDDocument).where(NTDDocument.id == doc_id))
    await db.commit()
    return {"message": "Document deleted successfully"}
