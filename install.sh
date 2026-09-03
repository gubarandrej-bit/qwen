#!/bin/bash

# Engineering Documentation Analysis System - Installation Script
# Скрипт установки системы анализа инженерной документации

set -e

echo "=========================================="
echo "Engineering Documentation Analysis System"
echo "Установка системы"
echo "=========================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка наличия необходимых утилит
check_requirements() {
    echo -e "${YELLOW}Проверка требований...${NC}"
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Ошибка: Python 3 не найден${NC}"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}Ошибка: npm не найден${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Требования выполнены${NC}"
}

# Установка backend
install_backend() {
    echo -e "${YELLOW}Установка backend...${NC}"
    
    cd backend
    
    # Создание виртуального окружения
    python3 -m venv venv
    source venv/bin/activate
    
    # Обновление pip
    pip install --upgrade pip
    
    # Установка зависимостей
    pip install -r requirements.txt
    
    # Создание директорий
    mkdir -p uploads reports
    
    # Создание .env файла
    cat > .env << ENVEOF
SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite+aiosqlite:///./engineering_docs.db
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
DEFAULT_ADMIN_LOGIN=admin
DEFAULT_ADMIN_PASSWORD=Admin@123
MAX_FILE_SIZE_MB=100
ENVEOF
    
    deactivate
    cd ..
    
    echo -e "${GREEN}✓ Backend установлен${NC}"
}

# Установка frontend
install_frontend() {
    echo -e "${YELLOW}Установка frontend...${NC}"
    
    cd frontend
    
    # Установка зависимостей
    npm install --yes
    
    # Сборка проекта
    npm run build
    
    cd ..
    
    echo -e "${GREEN}✓ Frontend установлен${NC}"
}

# Инициализация базы данных
init_database() {
    echo -e "${YELLOW}Инициализация базы данных...${NC}"
    
    cd backend
    source venv/bin/activate
    
    # Запуск приложения для создания БД
    python -c "from app.database.database import init_db; import asyncio; asyncio.run(init_db())"
    
    deactivate
    cd ..
    
    echo -e "${GREEN}✓ База данных инициализирована${NC}"
}

# Вывод информации о завершении
show_completion_info() {
    echo ""
    echo "=========================================="
    echo -e "${GREEN}Установка завершена успешно!${NC}"
    echo "=========================================="
    echo ""
    echo "Доступные команды:"
    echo ""
    echo "  Запуск backend:"
    echo "    cd backend"
    echo "    source venv/bin/activate"
    echo "    python main.py"
    echo ""
    echo "  Запуск frontend (режим разработки):"
    echo "    cd frontend"
    echo "    npm run dev"
    echo ""
    echo "  Запуск в production:"
    echo "    ./start.sh"
    echo ""
    echo "=========================================="
    echo "Доступ по умолчанию:"
    echo -e "${YELLOW}Логин: admin${NC}"
    echo -e "${YELLOW}Пароль: Admin@123${NC}"
    echo "=========================================="
    echo ""
    echo -e "${RED}ВАЖНО: Сразу после первого входа смените пароль администратора!${NC}"
    echo ""
}

# Основной процесс установки
main() {
    check_requirements
    install_backend
    install_frontend
    init_database
    show_completion_info
}

main
