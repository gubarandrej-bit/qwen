#!/bin/bash

# Engineering Documentation Analysis System - Full Installation Script
# Полный скрипт установки системы анализа инженерной документации
# Для серверов на базе Debian/Ubuntu

set -e

echo "=========================================="
echo "Engineering Documentation Analysis System"
echo "Полная установка системы"
echo "=========================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация
INSTALL_DIR="/opt/qwen"
SERVICE_NAME="qwen-engineering"
ADMIN_LOGIN="admin"
ADMIN_PASSWORD="Admin@123"

# Логирование
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ОШИБКА]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[УСПЕХ]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ВНИМАНИЕ]${NC} $1"
}

# Проверка прав root
check_root() {
    if [ "$EUID" -ne 0 ]; then 
        error "Запустите скрипт от имени root (sudo ./install.sh)"
        exit 1
    fi
    success "Права root подтверждены"
}

# Обновление системы
update_system() {
    log "Обновление списков пакетов..."
    apt update -qq
    
    log "Обновление установленных пакетов..."
    apt upgrade -y -qq
    
    success "Система обновлена"
}

# Установка системных зависимостей
install_system_deps() {
    log "Установка системных зависимостей..."
    
    DEPS=(
        python3
        python3-pip
        python3-venv
        python3-dev
        git
        curl
        wget
        build-essential
        libpoppler-cpp-dev
        poppler-utils
        ffmpeg
        libsm6
        libxext6
        libffi-dev
        libssl-dev
        pkg-config
        nodejs
        npm
        nginx
    )
    
    for dep in "${DEPS[@]}"; do
        if ! dpkg -l | grep -q "^ii  $dep "; then
            echo "  Установка: $dep"
            apt install -y -qq "$dep" || warning "Не удалось установить $dep"
        fi
    done
    
    # Установка dwg библиотеки (если доступна)
    if ! dpkg -l | grep -q "libdwg"; then
        warning "Библиотека DWG может быть недоступна в репозиториях"
        warning "Для работы с DWG файлами потребуется ручная установка libdwg"
    fi
    
    success "Системные зависимости установлены"
}

# Создание директории установки
create_install_dir() {
    log "Создание директории установки: $INSTALL_DIR"
    
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Клонирование репозитория если это чистая установка
    if [ ! -d ".git" ]; then
        log "Клонирование репозитория..."
        git clone https://github.com/gubarandrej-bit/qwen.git .
    fi
    
    success "Директория установки готова"
}

# Установка backend
install_backend() {
    log "Установка backend компонента..."
    
    cd "$INSTALL_DIR/backend"
    
    # Создание виртуального окружения
    log "Создание Python виртуального окружения..."
    python3 -m venv venv
    
    # Активация окружения
    source venv/bin/activate
    
    # Обновление pip
    log "Обновление pip..."
    pip install --upgrade pip -q
    
    # Установка зависимостей
    log "Установка Python зависимостей..."
    pip install -r requirements.txt -q
    
    # Создание директорий
    mkdir -p uploads reports logs
    
    # Генерация секретного ключа
    SECRET_KEY=$(openssl rand -hex 32)
    
    # Создание .env файла
    log "Создание конфигурационного файла .env..."
    cat > .env << ENVEOF
# Security Settings
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite+aiosqlite:///./engineering_docs.db

# Directories
UPLOAD_DIR=./uploads
REPORTS_DIR=./reports
LOGS_DIR=./logs

# Admin Credentials
DEFAULT_ADMIN_LOGIN=$ADMIN_LOGIN
DEFAULT_ADMIN_PASSWORD=$ADMIN_PASSWORD

# Application Settings
MAX_FILE_SIZE_MB=100
MODE=local

# AI Settings (для локального режима)
LOCAL_AI_MODEL=qwen-local
MAX_TOKENS=4096

# Server Settings
HOST=0.0.0.0
PORT=8000
ENVEOF
    
    # Деактивация окружения
    deactivate
    
    success "Backend установлен"
}

# Установка frontend
install_frontend() {
    log "Установка frontend компонента..."
    
    cd "$INSTALL_DIR/frontend"
    
    # Установка зависимостей
    log "Установка Node.js зависимостей..."
    npm install --silent
    
    # Сборка проекта
    log "Сборка frontend приложения..."
    npm run build --silent
    
    success "Frontend установлен"
}

# Инициализация базы данных
init_database() {
    log "Инициализация базы данных..."
    
    cd "$INSTALL_DIR/backend"
    source venv/bin/activate
    
    # Запуск инициализации БД
    python -c "from app.database.database import init_db; import asyncio; asyncio.run(init_db())" 2>/dev/null || {
        warning "Автоматическая инициализация БД не выполнена"
        warning "База данных будет создана при первом запуске приложения"
    }
    
    deactivate
    cd "$INSTALL_DIR"
    
    success "База данных инициализирована"
}

# Настройка nginx
setup_nginx() {
    log "Настройка nginx..."
    
    # Создание конфигурации nginx
    cat > /etc/nginx/sites-available/$SERVICE_NAME << 'NGINXEOF'
server {
    listen 80;
    server_name _;
    
    client_max_body_size 100M;
    
    # Frontend static files
    location / {
        root /opt/qwen/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Static files from backend
    location /static/ {
        proxy_pass http://127.0.0.1:8000/static/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Reports download
    location /reports/ {
        proxy_pass http://127.0.0.1:8000/reports/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        alias /opt/qwen/backend/reports/;
    }
}
NGINXEOF
    
    # Включение сайта
    ln -sf /etc/nginx/sites-available/$SERVICE_NAME /etc/nginx/sites-enabled/
    
    # Удаление дефолтного сайта если существует
    rm -f /etc/nginx/sites-enabled/default
    
    # Проверка конфигурации
    if nginx -t -q; then
        systemctl restart nginx
        systemctl enable nginx
        success "Nginx настроен и запущен"
    else
        error "Ошибка в конфигурации nginx"
        return 1
    fi
}

# Создание systemd сервиса
create_systemd_service() {
    log "Создание systemd сервиса..."
    
    cat > /etc/systemd/system/${SERVICE_NAME}.service << SERVICEEOF
[Unit]
Description=Engineering Documentation Analysis System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=$INSTALL_DIR/backend
Environment="PATH=$INSTALL_DIR/backend/venv/bin"
ExecStart=$INSTALL_DIR/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:$INSTALL_DIR/backend/logs/app.log
StandardError=append:$INSTALL_DIR/backend/logs/error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
SERVICEEOF
    
    # Перезагрузка systemd
    systemctl daemon-reload
    
    # Запуск сервиса
    systemctl start $SERVICE_NAME
    systemctl enable $SERVICE_NAME
    
    # Проверка статуса
    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        success "Systemd сервис создан и запущен"
    else
        warning "Сервис не запустился автоматически, проверьте логи"
    fi
}

# Настройка брандмауэра
setup_firewall() {
    if command -v ufw &> /dev/null; then
        log "Настройка брандмауэра UFW..."
        
        if ! ufw status | grep -q "Status: active"; then
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw allow 22/tcp
            echo "y" | ufw enable
            success "Брандмауэр UFW настроен"
        else
            ufw allow 80/tcp
            ufw allow 443/tcp
            success "Правила UFW обновлены"
        fi
    else
        warning "UFW не установлен, настройка брандмауэра пропущена"
    fi
}

# Вывод итоговой информации
show_completion_info() {
    clear
    echo ""
    echo "=========================================="
    echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!        ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
    echo "=========================================="
    echo ""
    echo -e "${BLUE}Система установлена по адресу:${NC}"
    echo "  http://$(hostname -I | awk '{print $1}' 2>/dev/null || echo 'SERVER_IP')"
    echo ""
    echo "=========================================="
    echo -e "${YELLOW}ДАННЫЕ ДЛЯ ПЕРВОГО ВХОДА:${NC}"
    echo "=========================================="
    echo -e "  ${GREEN}Логин:${NC}  $ADMIN_LOGIN"
    echo -e "  ${GREEN}Пароль:${NC} $ADMIN_PASSWORD"
    echo "=========================================="
    echo ""
    echo -e "${RED}⚠️  ВАЖНО: Сразу после первого входа смените пароль администратора!${NC}"
    echo ""
    echo "=========================================="
    echo -e "${BLUE}КОМАНДЫ УПРАВЛЕНИЯ:${NC}"
    echo "=========================================="
    echo ""
    echo "  Просмотр статуса сервиса:"
    echo -e "    ${YELLOW}systemctl status $SERVICE_NAME${NC}"
    echo ""
    echo "  Перезапуск сервиса:"
    echo -e "    ${YELLOW}systemctl restart $SERVICE_NAME${NC}"
    echo ""
    echo "  Остановка сервиса:"
    echo -e "    ${YELLOW}systemctl stop $SERVICE_NAME${NC}"
    echo ""
    echo "  Просмотр логов (в реальном времени):"
    echo -e "    ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
    echo ""
    echo "  Просмотр логов приложения:"
    echo -e "    ${YELLOW}tail -f $INSTALL_DIR/backend/logs/app.log${NC}"
    echo ""
    echo "  Обновление системы:"
    echo -e "    ${YELLOW}cd $INSTALL_DIR && git pull && systemctl restart $SERVICE_NAME${NC}"
    echo ""
    echo "=========================================="
    echo -e "${BLUE}РАСПОЛОЖЕНИЕ ФАЙЛОВ:${NC}"
    echo "=========================================="
    echo "  Директория установки: $INSTALL_DIR"
    echo "  Backend:              $INSTALL_DIR/backend"
    echo "  Frontend:             $INSTALL_DIR/frontend"
    echo "  База данных:          $INSTALL_DIR/backend/engineering_docs.db"
    echo "  Загрузки:             $INSTALL_DIR/backend/uploads"
    echo "  Отчеты:               $INSTALL_DIR/backend/reports"
    echo "  Логи:                 $INSTALL_DIR/backend/logs"
    echo "  Nginx конфиг:         /etc/nginx/sites-available/$SERVICE_NAME"
    echo "  Systemd сервис:       /etc/systemd/system/${SERVICE_NAME}.service"
    echo "=========================================="
    echo ""
    echo -e "${GREEN}Система готова к работе!${NC}"
    echo ""
}

# Основной процесс установки
main() {
    echo ""
    check_root
    echo ""
    
    warning "Начинается полная установка системы"
    warning "Процесс может занять 10-15 минут"
    echo ""
    read -p "Продолжить? (y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        error "Установка отменена"
        exit 1
    fi
    
    echo ""
    update_system
    echo ""
    install_system_deps
    echo ""
    create_install_dir
    echo ""
    install_backend
    echo ""
    install_frontend
    echo ""
    init_database
    echo ""
    setup_nginx
    echo ""
    create_systemd_service
    echo ""
    setup_firewall
    echo ""
    
    show_completion_info
}

# Запуск основной функции
main "$@"
