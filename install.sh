#!/bin/bash

# Скрипт автоматической установки системы проверки инженерной документации
# Для запуска: sudo ./install.sh

set -e

echo "=========================================="
echo "Система проверки инженерной документации"
echo "Установка на сервер"
echo "=========================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Запустите скрипт от имени root (sudo)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Начата установка...${NC}"

echo -e "${YELLOW}[1/8] Обновление пакетов...${NC}"
apt update -qq

echo -e "${YELLOW}[2/8] Установка системных зависимостей...${NC}"
apt install -y -qq python3 python3-pip python3-venv git curl wget nginx build-essential libpoppler-cpp-dev pkg-config > /dev/null 2>&1

APP_DIR="/opt/qwen"
echo -e "${YELLOW}[3/8] Создание директории $APP_DIR...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

echo -e "${YELLOW}[4/8] Создание виртуального окружения Python...${NC}"
python3 -m venv venv
source venv/bin/activate

echo -e "${YELLOW}[5/8] Установка Python пакетов...${NC}"
pip install --upgrade pip -q
if [ -f "/workspace/requirements.txt" ]; then
    cp /workspace/requirements.txt $APP_DIR/
    pip install -r requirements.txt -q
else
    pip install fastapi uvicorn sqlalchemy pydantic python-jose[cryptography] passlib[bcrypt] python-multipart pandas openpyxl xlwt xlrd python-docx PyPDF2 -q
fi

echo -e "${YELLOW}[6/8] Копирование файлов приложения...${NC}"
cp -r /workspace/backend $APP_DIR/
cp -r /workspace/templates $APP_DIR/

echo -e "${YELLOW}[7/8] Создание конфигурационного файла...${NC}"
cat > .env << ENVEOF
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=$(openssl rand -hex 32)
ADMIN_LOGIN=admin
ADMIN_PASSWORD=Admin@123
MODE=local
ENVEOF

echo -e "${YELLOW}[8/8] Настройка systemd сервиса...${NC}"
cat > /etc/systemd/system/qwen.service << EOFEOF
[Unit]
Description=Qwen Engineering Documentation Checker
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$APP_DIR/venv/bin"
ExecStart=$APP_DIR/venv/bin/python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOFEOF

echo -e "${YELLOW}Настройка Nginx...${NC}"
cat > /etc/nginx/sites-available/qwen << NGINXEOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 100M;
}
NGINXEOF

ln -sf /etc/nginx/sites-available/qwen /etc/nginx/sites-enabled/qwen
rm -f /etc/nginx/sites-enabled/default

echo -e "${YELLOW}Перезапуск служб...${NC}"
systemctl daemon-reload
systemctl enable qwen
systemctl start qwen
systemctl restart nginx

echo ""
echo -e "${GREEN}=========================================="
echo "✓ Установка завершена успешно!"
echo "==========================================${NC}"
echo ""
echo -e "${YELLOW}Доступ к системе:${NC}"
echo "  URL: http://$(hostname -I | awk '{print $1}')"
echo "  Логин: admin"
echo "  Пароль: Admin@123"
echo ""
echo -e "${YELLOW}Полезные команды:${NC}"
echo "  Статус службы: systemctl status qwen"
echo "  Просмотр логов: journalctl -u qwen -f"
echo "  Перезапуск: systemctl restart qwen"
echo ""
echo -e "${YELLOW}Важно:${NC}"
echo "  - Смените пароль администратора после первого входа!"
echo ""
