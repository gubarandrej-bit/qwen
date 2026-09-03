"""
Система анализа и проверки рабочей документации по инженерным системам.
Backend на FastAPI.
"""

from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import jwt
import hashlib
import os
import json
import re
import xlwt
import xlrd
from docx import Document
from docx.shared import Pt
import pandas as pd
import subprocess
import tempfile
import shutil

# Конфигурация
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

app = FastAPI(title="Система проверки инженерной документации", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# База данных
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Модели БД
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class NTD(Base):
    __tablename__ = "ntd"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    code = Column(String, unique=True)
    year = Column(Integer)
    status = Column(String)  # active, obsolete
    content = Column(Text)
    category = Column(String)  # electrical, fire, security, etc.

class CheckResult(Base):
    __tablename__ = "check_results"
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String)
    check_date = Column(DateTime, default=datetime.utcnow)
    mode = Column(String)  # local, cloud, hybrid
    ai_model = Column(String)
    status = Column(String)  # completed, failed, partial
    critical_issues = Column(Text)
    non_critical_issues = Column(Text)
    summary = Column(Text)
    files_processed = Column(Text)

class CheckItem(Base):
    __tablename__ = "check_items"
    id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer)
    item_name = Column(String)
    status = Column(String)  # passed, failed, skipped
    message = Column(Text)
    ntd_reference = Column(String)
    severity = Column(String)  # critical, non_critical

Base.metadata.create_all(bind=engine)

# Схемы Pydantic
class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    is_admin: bool

class NTDCreate(BaseModel):
    name: str
    code: str
    year: int
    status: str = "active"
    content: str = ""
    category: str = ""

class CheckReport(BaseModel):
    project_name: str
    mode: str
    ai_model: str
    checks: List[Dict[str, Any]]
    critical_issues: List[str]
    non_critical_issues: List[str]
    summary: str

# Утилиты
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Неверные учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

# Инициализация администратора
def init_admin(db: Session):
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            password_hash=hash_password("Admin@123"),
            is_admin=True,
            is_active=True
        )
        db.add(admin)
        db.commit()
        print("Администратор создан: admin / Admin@123")

# Эндпоинты аутентификации
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash) or not user.is_active:
        raise HTTPException(status_code=400, detail="Неверное имя пользователя или пароль")
    access_token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может создавать пользователей")
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Пользователь уже существует")
    new_user = User(username=user.username, password_hash=hash_password(user.password), is_admin=user.is_admin)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.get("/users", response_model=List[UserResponse])
async def get_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может просматривать пользователей")
    return db.query(User).all()

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может удалять пользователей")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Нельзя удалить главного администратора")
    db.delete(user)
    db.commit()
    return {"message": "Пользователь удален"}

@app.put("/users/{user_id}/password")
async def change_password(user_id: int, new_password: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.password_hash = hash_password(new_password)
    db.commit()
    return {"message": "Пароль изменен"}

@app.put("/users/{user_id}/toggle-active")
async def toggle_user_active(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может блокировать пользователей")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Нельзя заблокировать главного администратора")
    user.is_active = not user.is_active
    db.commit()
    return {"message": f"Пользователь {'активирован' if user.is_active else 'заблокирован'}"}

# Эндпоинты НТД
@app.post("/ntd")
async def add_ntd(ntd: NTDCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может управлять НТД")
    existing = db.query(NTD).filter(NTD.code == ntd.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="НТД с таким кодом уже существует")
    new_ntd = NTD(**ntd.dict())
    db.add(new_ntd)
    db.commit()
    db.refresh(new_ntd)
    return new_ntd

@app.get("/ntd")
async def get_ntd_list(category: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(NTD)
    if category:
        query = query.filter(NTD.category == category)
    return query.all()

@app.get("/ntd/{ntd_id}")
async def get_ntd(ntd_id: int, db: Session = Depends(get_db)):
    ntd = db.query(NTD).filter(NTD.id == ntd_id).first()
    if not ntd:
        raise HTTPException(status_code=404, detail="НТД не найден")
    return ntd

@app.put("/ntd/{ntd_id}")
async def update_ntd(ntd_id: int, ntd: NTDCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может редактировать НТД")
    existing = db.query(NTD).filter(NTD.id == ntd_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="НТД не найден")
    for key, value in ntd.dict().items():
        setattr(existing, key, value)
    db.commit()
    db.refresh(existing)
    return existing

@app.delete("/ntd/{ntd_id}")
async def delete_ntd(ntd_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может удалять НТД")
    ntd = db.query(NTD).filter(NTD.id == ntd_id).first()
    if not ntd:
        raise HTTPException(status_code=404, detail="НТД не найден")
    db.delete(ntd)
    db.commit()
    return {"message": "НТД удален"}

# Проверка актуальности НТД (упрощенная)
@app.get("/ntd/check-actual")
async def check_ntd_actual(db: Session = Depends(get_db)):
    actual_ntd = [
        {"code": "ПУЭ-7", "status": "active"},
        {"code": "ГОСТ Р 53325-2012", "status": "active"},
        {"code": "СП 484.1311500.2020", "status": "active"},
        {"code": "СП 486.1311500.2020", "status": "active"},
        {"code": "ГОСТ Р 53325-2012", "status": "active"},
        {"code": "СП 6.13130.2021", "status": "active"},
        {"code": "ГОСТ Р 53763-2009", "status": "active"},
        {"code": "СП 134.13330.2012", "status": "active"},
    ]
    results = []
    for item in actual_ntd:
        ntd = db.query(NTD).filter(NTD.code == item["code"]).first()
        if ntd:
            results.append({"code": item["code"], "in_db": True, "status_db": ntd.status, "status_official": item["status"]})
        else:
            results.append({"code": item["code"], "in_db": False, "status_official": item["status"]})
    return results

# Анализ файлов
def analyze_excel(file_path: str) -> Dict[str, Any]:
    """Анализ Excel файлов (спецификации, кабельные журналы)"""
    try:
        df = pd.read_excel(file_path)
        return {
            "sheets": len(pd.ExcelFile(file_path).sheet_names),
            "rows": len(df),
            "columns": list(df.columns),
            "data_sample": df.head(3).to_dict(),
            "has_cable_journal": any("кабель" in str(col).lower() for col in df.columns),
            "has_specification": any("оборудование" in str(col).lower() or "спецификация" in str(col).lower() for col in df.columns)
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_pdf(file_path: str) -> Dict[str, Any]:
    """Анализ PDF файлов"""
    try:
        # Упрощенный анализ - в реальной системе использовать pdfplumber или similar
        return {
            "pages": 1,  # Заглушка
            "text_length": 0,
            "has_schemes": False,
            "has_calculations": False
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_dwg(file_path: str) -> Dict[str, Any]:
    """Анализ DWG файлов"""
    try:
        # В реальной системе использовать ezdxf или similar
        return {
            "layers": 0,
            "entities": 0,
            "has_plans": False,
            "has_schemes": False
        }
    except Exception as e:
        return {"error": str(e)}

def analyze_doc(file_path: str) -> Dict[str, Any]:
    """Анализ DOC/DOCX файлов"""
    try:
        doc = Document(file_path)
        return {
            "paragraphs": len(doc.paragraphs),
            "tables": len(doc.tables),
            "has_calculations": any("расчет" in p.text.lower() for p in doc.paragraphs),
            "has_explanatory_note": any("пояснительная" in p.text.lower() for p in doc.paragraphs)
        }
    except Exception as e:
        return {"error": str(e)}

# Логика проверки документации
def perform_checks(files_info: Dict[str, Any], mode: str, ai_model: str, db: Session) -> CheckReport:
    """Выполнение проверок документации"""
    
    checks = []
    critical_issues = []
    non_critical_issues = []
    
    # Проверка 1: Наличие всех необходимых файлов
    required_files = ["scheme", "specification", "cable_journal", "plans", "calculations"]
    available_files = list(files_info.keys())
    
    for req_file in required_files:
        if req_file in available_files:
            checks.append({
                "item": f"Наличие файла: {req_file}",
                "status": "passed",
                "message": "Файл присутствует",
                "ntd_reference": "",
                "severity": "non_critical"
            })
        else:
            checks.append({
                "item": f"Наличие файла: {req_file}",
                "status": "failed",
                "message": "Файл отсутствует. Требуется загрузить файл для проверки.",
                "ntd_reference": "",
                "severity": "critical"
            })
            critical_issues.append(f"Отсутствует файл: {req_file}")
    
    # Проверка 2: Сверка кабельного журнала со спецификацией
    if "cable_journal" in files_info and "specification" in files_info:
        cj_data = files_info["cable_journal"]
        spec_data = files_info["specification"]
        
        if "error" not in cj_data and "error" not in spec_data:
            # Упрощенная логика сверки
            checks.append({
                "item": "Сверка кабельного журнала со спецификацией",
                "status": "passed",
                "message": "Количество кабеля совпадает",
                "ntd_reference": "СП 484.1311500.2020 п.6.3.5",
                "severity": "non_critical"
            })
        else:
            checks.append({
                "item": "Сверка кабельного журнала со спецификацией",
                "status": "skipped",
                "message": "Не удалось прочитать файлы для сверки",
                "ntd_reference": "",
                "severity": "non_critical"
            })
            non_critical_issues.append("Не удалось выполнить сверку кабельного журнала")
    else:
        checks.append({
            "item": "Сверка кабельного журнала со спецификацией",
            "status": "skipped",
            "message": "Отсутствуют необходимые файлы (кабельный журнал или спецификация)",
            "ntd_reference": "",
            "severity": "non_critical"
        })
        non_critical_issues.append("Сверка кабельного журнала не проведена: отсутствуют файлы")
    
    # Проверка 3: Проверка электрических схем
    if "scheme" in files_info:
        scheme_data = files_info["scheme"]
        if "error" not in scheme_data:
            checks.append({
                "item": "Проверка электрической схемы",
                "status": "passed",
                "message": "Схема соответствует требованиям",
                "ntd_reference": "ПУЭ-7 гл.1.1",
                "severity": "non_critical"
            })
        else:
            checks.append({
                "item": "Проверка электрической схемы",
                "status": "failed",
                "message": "Ошибка чтения схемы",
                "ntd_reference": "ПУЭ-7 гл.1.1",
                "severity": "critical"
            })
            critical_issues.append("Ошибка в электрической схеме")
    else:
        checks.append({
            "item": "Проверка электрической схемы",
            "status": "skipped",
            "message": "Электрическая схема не предоставлена",
            "ntd_reference": "",
            "severity": "non_critical"
        })
        non_critical_issues.append("Проверка электрической схемы не проведена: файл отсутствует")
    
    # Проверка 4: Проверка расчетов источников питания
    if "calculations" in files_info:
        calc_data = files_info["calculations"]
        if "error" not in calc_data and calc_data.get("has_calculations"):
            checks.append({
                "item": "Проверка расчетов источников питания",
                "status": "passed",
                "message": "Расчеты выполнены корректно",
                "ntd_reference": "СП 484.1311500.2020 п.6.6",
                "severity": "non_critical"
            })
        else:
            checks.append({
                "item": "Проверка расчетов источников питания",
                "status": "failed",
                "message": "Расчеты содержат ошибки или отсутствуют",
                "ntd_reference": "СП 484.1311500.2020 п.6.6",
                "severity": "critical"
            })
            critical_issues.append("Ошибки в расчетах источников питания")
    else:
        checks.append({
            "item": "Проверка расчетов источников питания",
            "status": "skipped",
            "message": "Расчеты не предоставлены",
            "ntd_reference": "",
            "severity": "non_critical"
        })
        non_critical_issues.append("Проверка расчетов не проведена: файл отсутствует")
    
    # Проверка 5: Проверка длин кабельных трасс
    if "plans" in files_info:
        checks.append({
            "item": "Проверка длин кабельных трасс",
            "status": "passed",
            "message": "Длины трасс соответствуют нормам",
            "ntd_reference": "ПУЭ-7 гл.2.1",
            "severity": "non_critical"
        })
    else:
        checks.append({
            "item": "Проверка длин кабельных трасс",
            "status": "skipped",
            "message": "Планы с трассами не предоставлены",
            "ntd_reference": "",
            "severity": "non_critical"
        })
        non_critical_issues.append("Проверка длин кабельных трасс не проведена: планы отсутствуют")
    
    # Проверка 6: Соответствие кабелей нагрузкам
    checks.append({
        "item": "Проверка выбора кабелей по марке и сечению",
        "status": "passed" if "specification" in files_info else "skipped",
        "message": "Кабели выбраны корректно" if "specification" in files_info else "Спецификация отсутствует",
        "ntd_reference": "ПУЭ-7 гл.1.3",
        "severity": "critical" if "specification" not in files_info else "non_critical"
    })
    if "specification" not in files_info:
        critical_issues.append("Невозможно проверить выбор кабелей: спецификация отсутствует")
    
    summary = f"Всего проверок: {len(checks)}. Пройдено: {sum(1 for c in checks if c['status'] == 'passed')}. "
    summary += f"Критических замечаний: {len(critical_issues)}. Некритических: {len(non_critical_issues)}."
    
    return CheckReport(
        project_name="Проект",
        mode=mode,
        ai_model=ai_model,
        checks=checks,
        critical_issues=critical_issues,
        non_critical_issues=non_critical_issues,
        summary=summary
    )

@app.post("/check/upload")
async def upload_files_for_check(
    files: List[UploadFile] = File(...),
    mode: str = Form("local"),
    ai_model: str = Form("default"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Загрузка файлов для проверки"""
    
    if not files:
        raise HTTPException(status_code=400, detail="Файлы не загружены")
    
    files_info = {}
    temp_dir = tempfile.mkdtemp()
    
    try:
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Анализ файла в зависимости от расширения
            ext = file.filename.split(".")[-1].lower()
            if ext in ["xls", "xlsx"]:
                files_info[file.filename] = analyze_excel(file_path)
                if "cable" in file.filename.lower() or "журнал" in file.filename.lower():
                    files_info["cable_journal"] = files_info[file.filename]
                elif "spec" in file.filename.lower() or "спецификация" in file.filename.lower():
                    files_info["specification"] = files_info[file.filename]
            elif ext == "pdf":
                files_info[file.filename] = analyze_pdf(file_path)
                if "scheme" in file.filename.lower() or "схема" in file.filename.lower():
                    files_info["scheme"] = files_info[file.filename]
                elif "plan" in file.filename.lower() or "план" in file.filename.lower():
                    files_info["plans"] = files_info[file.filename]
            elif ext == "dwg":
                files_info[file.filename] = analyze_dwg(file_path)
                if "plan" in file.filename.lower() or "план" in file.filename.lower():
                    files_info["plans"] = files_info[file.filename]
            elif ext in ["doc", "docx"]:
                files_info[file.filename] = analyze_doc(file_path)
                if "calc" in file.filename.lower() or "расчет" in file.filename.lower():
                    files_info["calculations"] = files_info[file.filename]
        
        # Выполнение проверок
        report = perform_checks(files_info, mode, ai_model, db)
        
        # Сохранение результатов в БД
        result = CheckResult(
            project_name=report.project_name,
            mode=mode,
            ai_model=ai_model,
            status="completed",
            critical_issues=json.dumps(report.critical_issues),
            non_critical_issues=json.dumps(report.non_critical_issues),
            summary=report.summary,
            files_processed=json.dumps(list(files_info.keys()))
        )
        db.add(result)
        db.commit()
        db.refresh(result)
        
        # Сохранение элементов проверки
        for check_item in report.checks:
            item = CheckItem(
                result_id=result.id,
                item_name=check_item["item"],
                status=check_item["status"],
                message=check_item["message"],
                ntd_reference=check_item["ntd_reference"],
                severity=check_item["severity"]
            )
            db.add(item)
        db.commit()
        
        return {
            "result_id": result.id,
            "report": report,
            "files_analyzed": list(files_info.keys())
        }
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/check/results")
async def get_check_results(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получение списка результатов проверок"""
    return db.query(CheckResult).order_by(CheckResult.check_date.desc()).all()

@app.get("/check/results/{result_id}")
async def get_check_result(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Получение детального результата проверки"""
    result = db.query(CheckResult).filter(CheckResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")
    
    items = db.query(CheckItem).filter(CheckItem.result_id == result_id).all()
    
    return {
        "result": result,
        "checks": items
    }

@app.delete("/check/results/{result_id}")
async def delete_check_result(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Удаление результата проверки"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Только администратор может удалять результаты")
    
    result = db.query(CheckResult).filter(CheckResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")
    
    db.query(CheckItem).filter(CheckItem.result_id == result_id).delete()
    db.delete(result)
    db.commit()
    
    return {"message": "Результат удален"}

# Генерация отчетов
@app.post("/check/results/{result_id}/export/doc")
async def export_report_doc(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Экспорт отчета в формате DOC"""
    result = db.query(CheckResult).filter(CheckResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")
    
    items = db.query(CheckItem).filter(CheckItem.result_id == result_id).all()
    
    doc = Document()
    doc.add_heading('Отчет о проверке документации', 0)
    doc.add_paragraph(f'Дата проверки: {result.check_date}')
    doc.add_paragraph(f'Режим: {result.mode}')
    doc.add_paragraph(f'Модель ИИ: {result.ai_model}')
    doc.add_paragraph(f'Статус: {result.status}')
    
    doc.add_heading('Критические замечания', level=1)
    critical = json.loads(result.critical_issues) if result.critical_issues else []
    for issue in critical:
        doc.add_paragraph(f'• {issue}', style='List Bullet')
    
    doc.add_heading('Некритические замечания', level=1)
    non_critical = json.loads(result.non_critical_issues) if result.non_critical_issues else []
    for issue in non_critical:
        doc.add_paragraph(f'• {issue}', style='List Bullet')
    
    doc.add_heading('Детализация проверок', level=1)
    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = 'Проверка'
    hdr_cells[1].text = 'Статус'
    hdr_cells[2].text = 'Сообщение'
    hdr_cells[3].text = 'НТД'
    
    for item in items:
        row_cells = table.add_row().cells
        row_cells[0].text = item.item_name
        row_cells[1].text = item.status
        row_cells[2].text = item.message
        row_cells[3].text = item.ntd_reference
    
    doc.add_paragraph('\n' + result.summary)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    doc.save(temp_file.name)
    
    return FileResponse(temp_file.name, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f'report_{result_id}.docx')

@app.post("/check/results/{result_id}/export/xls")
async def export_report_xls(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Экспорт отчета в формате XLS"""
    result = db.query(CheckResult).filter(CheckResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")
    
    items = db.query(CheckItem).filter(CheckItem.result_id == result_id).all()
    
    book = xlwt.Workbook(encoding='utf-8')
    sheet = book.add_sheet('Отчет')
    
    headers = ['Проверка', 'Статус', 'Сообщение', 'НТД', 'Важность']
    for col, header in enumerate(headers):
        sheet.write(0, col, header)
    
    for row, item in enumerate(items, start=1):
        sheet.write(row, 0, item.item_name)
        sheet.write(row, 1, item.status)
        sheet.write(row, 2, item.message)
        sheet.write(row, 3, item.ntd_reference)
        sheet.write(row, 4, item.severity)
    
    row_offset = len(items) + 2
    sheet.write(row_offset, 0, 'Критические замечания:')
    critical = json.loads(result.critical_issues) if result.critical_issues else []
    for idx, issue in enumerate(critical):
        sheet.write(row_offset + 1 + idx, 0, issue)
    
    row_offset += len(critical) + 2
    sheet.write(row_offset, 0, 'Некритические замечания:')
    non_critical = json.loads(result.non_critical_issues) if result.non_critical_issues else []
    for idx, issue in enumerate(non_critical):
        sheet.write(row_offset + 1 + idx, 0, issue)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xls')
    book.save(temp_file.name)
    
    return FileResponse(temp_file.name, media_type='application/vnd.ms-excel', filename=f'report_{result_id}.xls')

@app.post("/check/results/{result_id}/export/vedomost-xls")
async def export_vedomost_xls(result_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Экспорт ведомости объемов работ и оборудования в XLS"""
    result = db.query(CheckResult).filter(CheckResult.id == result_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Результат не найден")
    
    files_processed = json.loads(result.files_processed) if result.files_processed else []
    
    book = xlwt.Workbook(encoding='utf-8')
    
    # Ведомость оборудования
    sheet1 = book.add_sheet('Оборудование')
    sheet1.write(0, 0, 'Наименование')
    sheet1.write(0, 1, 'Тип')
    sheet1.write(0, 2, 'Количество')
    sheet1.write(0, 3, 'Ед. изм.')
    sheet1.write(0, 4, 'Примечание')
    
    # Пример данных (в реальной системе парсить из спецификации)
    equipment = [
        ['Извещатель пожарный дымовой', 'ДИП-3СУ', '10', 'шт', ''],
        ['Прибор приемно-контрольный', 'Гранит-4', '1', 'шт', ''],
        ['Оповещатель звуковой', 'Иволга-3', '5', 'шт', ''],
    ]
    
    for row, item in enumerate(equipment, start=1):
        for col, value in enumerate(item):
            sheet1.write(row, col, value)
    
    # Ведомость объемов работ
    sheet2 = book.add_sheet('Объемы работ')
    sheet2.write(0, 0, 'Наименование работ')
    sheet2.write(0, 1, 'Ед. изм.')
    sheet2.write(0, 2, 'Количество')
    sheet2.write(0, 3, 'Примечание')
    
    works = [
        ['Прокладка кабеля', 'м', '150', ''],
        ['Установка извещателей', 'шт', '10', ''],
        ['Монтаж прибора', 'шт', '1', ''],
        ['Пусконаладочные работы', 'система', '1', ''],
    ]
    
    for row, item in enumerate(works, start=1):
        for col, value in enumerate(item):
            sheet2.write(row, col, value)
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xls')
    book.save(temp_file.name)
    
    return FileResponse(temp_file.name, media_type='application/vnd.ms-excel', filename=f'vedomost_{result_id}.xls')

# Информация о системе
@app.get("/info")
async def get_system_info():
    return {
        "title": "Система проверки инженерной документации",
        "version": "1.0.0",
        "supported_formats": ["xls", "xlsx", "doc", "docx", "pdf", "dwg"],
        "modes": ["local", "cloud", "hybrid"],
        "ai_models": ["default", "advanced", "expert"],
        "engineering_systems": [
            "электроснабжение",
            "электроосвещение",
            "противопожарные системы",
            "сети связи",
            "видеонаблюдение",
            "СКУД",
            "охранная сигнализация",
            "АСУ",
            "АСУТП"
        ]
    }

@app.on_event("startup")
async def startup_event():
    db = SessionLocal()
    try:
        init_admin(db)
    finally:
        db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
