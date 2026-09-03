from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class UserBase(BaseModel):
    login: str
    role: UserRole = UserRole.ENGINEER


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_blocked: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    login: Optional[str] = None


class EngineeringSystem(str, Enum):
    ELECTRIC_SUPPLY = "electrosnabzhenie"
    ELECTRIC_LIGHTING = "electroosveshchenie"
    FIRE_ALARM = "pozarnaya_signalizatsiya"
    FIRE_VOICE = "SOUE"
    FIRE_SUPPRESSION = "pozharotushenie"
    NETWORKS_SCS = "SKS"
    NETWORKS_LAN = "LVS"
    NETWORKS_FOCL = "VOLS"
    VIDEO_SURVEILLANCE = "videonablyudenie"
    ACCESS_CONTROL = "SKUD"
    SECURITY_ALARM = "okhrannaya_signalizatsiya"
    ASU = "ASU"
    ASUTP = "ASUTP"


class CheckMode(str, Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    HYBRID = "hybrid"


class CheckCreate(BaseModel):
    name: str
    engineering_system: EngineeringSystem
    mode: CheckMode = CheckMode.LOCAL
    ai_model: Optional[str] = None


class CheckResponse(BaseModel):
    id: int
    user_id: int
    name: str
    engineering_system: EngineeringSystem
    status: str
    mode: str
    ai_model: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class CheckType(str, Enum):
    SCHEME_ELECTRIC = "scheme_electric"
    SCHEME_STRUCTURAL = "scheme_structural"
    CABLE_LENGTH = "cable_length"
    CABLE_JOURNAL_SPEC = "cable_journal_spec"
    EQUIPMENT_SPEC = "equipment_spec"
    CABLE_SELECTION = "cable_selection"
    POWER_SUPPLY_CALC = "power_supply_calc"
    BATTERY_SELECTION = "battery_selection"
    NTD_COMPLIANCE = "ntd_compliance"
    CALCULATIONS_VERIFY = "calculations_verify"


class SeverityLevel(str, Enum):
    CRITICAL = "critical"
    NON_CRITICAL = "non_critical"
    INFO = "info"


class CheckResultCreate(BaseModel):
    check_type: CheckType
    status: str
    severity: SeverityLevel = SeverityLevel.INFO
    message: str
    ntd_reference: Optional[str] = None
    details: Optional[str] = None


class CheckResultResponse(CheckResultCreate):
    id: int
    check_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class NTDCategory(str, Enum):
    PUE = "PUE"
    GOST = "GOST"
    SP = "SP"
    FZ = "FZ"
    OTHER = "OTHER"


class NTDDocumentCreate(BaseModel):
    doc_number: str
    doc_name: str
    category: NTDCategory
    approval_date: Optional[datetime] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_actual: bool = True


class NTDDocumentUpdate(BaseModel):
    doc_number: Optional[str] = None
    doc_name: Optional[str] = None
    category: Optional[NTDCategory] = None
    approval_date: Optional[datetime] = None
    description: Optional[str] = None
    content: Optional[str] = None
    is_actual: Optional[bool] = None


class NTDDocumentResponse(NTDDocumentCreate):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class AIModelResponse(BaseModel):
    id: int
    name: str
    model_type: str
    description: Optional[str]
    is_available: bool

    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    check_id: int
    format: str  # doc, xls


class FileUploadResponse(BaseModel):
    file_name: str
    file_path: str
    file_type: str
    file_size: int
