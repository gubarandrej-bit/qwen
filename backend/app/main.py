from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os

from app.database.database import init_db, get_db
from app.config import settings
from app.routers import auth, users, checks, reports
from app.services.user_service import UserService
from app.models.models import User, UserRole, NTDDocument, NTDCategory, AIModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске приложения"""
    # Создание таблиц БД
    await init_db()
    
    # Создание администратора по умолчанию
    async for db in get_db():
        user_service = UserService(db)
        admin = await user_service.get_user_by_login(settings.DEFAULT_ADMIN_LOGIN)
        if not admin:
            await user_service.create_user(
                login=settings.DEFAULT_ADMIN_LOGIN,
                password=settings.DEFAULT_ADMIN_PASSWORD,
                role=UserRole.ADMIN
            )
            print(f"Admin user created: {settings.DEFAULT_ADMIN_LOGIN}")
        
        # Инициализация базовых НТД
        result = await db.execute(select(NTDDocument))
        existing_docs = result.scalars().all()
        if not existing_docs:
            # Добавляем основные НТД
            ntd_list = [
                {"doc_number": "ПУЭ-7", "doc_name": "Правила устройства электроустановок (7 издание)", "category": NTDCategory.PUE},
                {"doc_number": "ГОСТ Р 50571.1-2009", "doc_name": "Электроустановки низковольтные", "category": NTDCategory.GOST},
                {"doc_number": "СП 6.13130.2013", "doc_name": "Электроснабжение и электрооборудование объектов защиты", "category": NTDCategory.SP},
                {"doc_number": "СП 484.13130.2020", "doc_name": "Системы пожарной сигнализации и автоматизация противопожарной защиты", "category": NTDCategory.SP},
                {"doc_number": "ФЗ-123", "doc_name": "Технический регламент о требованиях пожарной безопасности", "category": NTDCategory.FZ},
                {"doc_number": "ГОСТ Р 53325-2012", "doc_name": "Техника пожарная. Технические средства пожарной автоматики", "category": NTDCategory.GOST},
                {"doc_number": "СП 7.13130.2013", "doc_name": "Отопление, вентиляция и кондиционирование", "category": NTDCategory.SP},
                {"doc_number": "ПУЭ-6", "doc_name": "Правила устройства электроустановок (6 издание)", "category": NTDCategory.PUE},
            ]
            
            for doc_data in ntd_list:
                doc = NTDDocument(**doc_data)
                db.add(doc)
            
            await db.commit()
            print("NTD documents initialized")
        
        # Инициализация моделей ИИ
        result = await db.execute(select(AIModel))
        existing_models = result.scalars().all()
        if not existing_models:
            ai_models = [
                {"name": "Qwen-2.5-1.5B", "model_type": "local", "description": "Локальная модель Qwen для анализа документации", "is_available": True},
                {"name": "Mistral-7B-Instruct", "model_type": "cloud", "description": "Облачная модель Mistral через HuggingFace API", "is_available": True},
                {"name": "Phi-2", "model_type": "cloud", "description": "Облачная модель Microsoft Phi-2", "is_available": True}
            ]
            
            for model_data in ai_models:
                model = AIModel(**model_data)
                db.add(model)
            
            await db.commit()
            print("AI models initialized")
        
        break
    
    yield
    
    # Очистка при завершении
    pass


app = FastAPI(
    title="Engineering Documentation Analysis System",
    description="Система анализа и проверки рабочей документации по инженерным системам",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(checks.router)
app.include_router(reports.router)


@app.get("/")
async def root():
    return {
        "message": "Engineering Documentation Analysis System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
