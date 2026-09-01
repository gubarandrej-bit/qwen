from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.database.database import Base


class UserRole(enum.Enum):
    ADMIN = "admin"
    ENGINEER = "engineer"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    login = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.ENGINEER)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timetimezone=True), onupdate=func.now())

    checks = relationship("Check", back_populates="user")


class EngineeringSystem(enum.Enum):
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


class CheckStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Check(Base):
    __tablename__ = "checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(255), nullable=False)
    engineering_system = Column(SQLEnum(EngineeringSystem))
    status = Column(SQLEnum(CheckStatus), default=CheckStatus.PENDING)
    mode = Column(String(20), default="local")  # local, cloud, hybrid
    ai_model = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))

    user = relationship("User", back_populates="checks")
    files = relationship("CheckFile", back_populates="check")
    results = relationship("CheckResult", back_populates="check")


class CheckFile(Base):
    __tablename__ = "check_files"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("checks.id"))
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20))
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    check = relationship("Check", back_populates="files")


class CheckType(enum.Enum):
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


class SeverityLevel(enum.Enum):
    CRITICAL = "critical"
    NON_CRITICAL = "non_critical"
    INFO = "info"


class CheckResult(Base):
    __tablename__ = "check_results"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(Integer, ForeignKey("checks.id"))
    check_type = Column(SQLEnum(CheckType))
    status = Column(String(20))  # passed, failed, skipped, error
    severity = Column(SQLEnum(SeverityLevel), default=SeverityLevel.INFO)
    message = Column(Text)
    ntd_reference = Column(String(255))  # ссылка на пункт НТД
    details = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    check = relationship("Check", back_populates="results")


class NTDCategory(enum.Enum):
    PUE = "PUE"
    GOST = "GOST"
    SP = "SP"
    FZ = "FZ"
    OTHER = "OTHER"


class NTDDocument(Base):
    __tablename__ = "ntd_documents"

    id = Column(Integer, primary_key=True, index=True)
    doc_number = Column(String(50), nullable=False)
    doc_name = Column(String(500), nullable=False)
    category = Column(SQLEnum(NTDCategory))
    approval_date = Column(DateTime(timezone=True))
    is_actual = Column(Boolean, default=True)
    description = Column(Text)
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AIModel(Base):
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    model_type = Column(String(50))  # local, cloud
    description = Column(Text)
    is_available = Column(Boolean, default=True)
    model_path = Column(String(500))
    api_endpoint = Column(String(500))
