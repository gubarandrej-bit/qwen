from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import os
from datetime import datetime
from app.database.database import get_db
from app.routers.auth import get_current_user
from app.models.models import User, Check, CheckResult, CheckStatus, CheckType, SeverityLevel
from app.schemas.schemas import CheckResultResponse, ReportGenerateRequest
from app.services.report_generator import ReportGenerator
from app.services.document_parser import DocumentParser, CableJournalParser, SpecificationParser
from app.ai_core.llm_service import get_llm_service
from app.config import settings
from sqlalchemy import select

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("/generate")
async def generate_report(
    request: ReportGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Генерация отчета по результатам проверки"""
    # Получаем проверку
    result = await db.execute(select(Check).where(Check.id == request.check_id))
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    # Проверка доступа
    if current_user.role.value != "admin" and check.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Получаем результаты проверки
    result = await db.execute(
        select(CheckResult).where(CheckResult.check_id == request.check_id)
    )
    check_results = result.scalars().all()
    
    # Формируем данные для отчета
    check_info = {
        "name": check.name,
        "engineering_system": check.engineering_system.value,
        "mode": check.mode,
        "ai_model": check.ai_model,
        "status": check.status.value
    }
    
    results_data = []
    for r in check_results:
        results_data.append({
            "check_type": r.check_type.value if r.check_type else "",
            "status": r.status,
            "severity": r.severity.value if r.severity else "info",
            "message": r.message,
            "ntd_reference": r.ntd_reference,
            "details": r.details
        })
    
    # Получаем НТД
    from app.models.models import NTDDocument
    result = await db.execute(select(NTDDocument).where(NTDDocument.is_actual == True))
    ntd_docs = result.scalars().all()
    ntd_data = [{"doc_number": d.doc_number, "doc_name": d.doc_name} for d in ntd_docs]
    
    # Создаем директорию для отчетов
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if request.format.lower() == "doc":
        output_path = os.path.join(settings.REPORTS_DIR, f"report_{timestamp}.docx")
        ReportGenerator.generate_doc_report(check_info, results_data, ntd_data, output_path)
        return {"file_path": output_path, "format": "doc"}
    elif request.format.lower() == "xls":
        output_path = os.path.join(settings.REPORTS_DIR, f"report_{timestamp}.xlsx")
        ReportGenerator.generate_xls_report(check_info, results_data, output_path)
        return {"file_path": output_path, "format": "xls"}
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'doc' or 'xls'.")


@router.get("/{check_id}/ ведомость-кабеля")
async def generate_cable ведомость(
    check_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Генерация ведомости кабеля"""
    result = await db.execute(select(Check).where(Check.id == check_id))
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    if current_user.role.value != "admin" and check.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Здесь должна быть логика извлечения данных из кабельного журнала
    # Для примера возвращаем пустую ведомость
    cables = []  # Данные должны быть получены из parsed files
    
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(settings.REPORTS_DIR, f"cable_ведомость_{timestamp}.xlsx")
    
    ReportGenerator.generate_cable_ведомость(cables, output_path)
    return {"file_path": output_path}


@router.get("/{check_id}/ ведомость-оборудования")
async def generate_equipment ведомость(
    check_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Генерация ведомости оборудования"""
    result = await db.execute(select(Check).where(Check.id == check_id))
    check = result.scalar_one_or_none()
    if not check:
        raise HTTPException(status_code=404, detail="Check not found")
    
    if current_user.role.value != "admin" and check.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Здесь должна быть логика извлечения данных из спецификации
    equipment = []  # Данные должны быть получены из parsed files
    
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(settings.REPORTS_DIR, f"equipment_ведомость_{timestamp}.xlsx")
    
    ReportGenerator.generate_equipment_ведомость(equipment, output_path)
    return {"file_path": output_path}
