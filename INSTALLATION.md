# 📦 Полная инструкция по установке и запуску системы

## Вариант 1: Автоматическая установка (Рекомендуется)

### Шаг 1: Скачивание скрипта установки

```bash
cd /opt
sudo wget https://raw.githubusercontent.com/gubarandrej-bit/qwen/main/install.sh
sudo chmod +x install.sh
```

### Шаг 2: Запуск установки

```bash
sudo ./install.sh
```

Скрипт автоматически выполнит:
- ✅ Обновление системы
- ✅ Установку всех зависимостей (Python, Node.js, Nginx)
- ✅ Клонирование репозитория
- ✅ Настройку backend и frontend
- ✅ Инициализацию базы данных
- ✅ Настройку Nginx
- ✅ Создание systemd сервиса
- ✅ Настройку брандмауэра (UFW)

### Шаг 3: Проверка установки

После завершения вы увидите сообщение:

```
╔══════════════════════════════════════╗
║  УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!        ║
╚══════════════════════════════════════╝

Система установлена по адресу:
  http://192.168.1.100

ДАННЫЕ ДЛЯ ПЕРВОГО ВХОДА:
==========================================
  Логин:  admin
  Пароль: Admin@123
==========================================

⚠️  ВАЖНО: Сразу после первого входа смените пароль администратора!
```

---

## Вариант 2: Ручная установка (Для опытных пользователей)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых зависимостей
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    build-essential \
    libpoppler-cpp-dev \
    poppler-utils \
    ffmpeg \
    libsm6 \
    libxext6 \
    libffi-dev \
    libssl-dev \
    pkg-config \
    nodejs \
    npm \
    nginx
```

### Шаг 2: Клонирование репозитория

```bash
cd /opt
sudo git clone https://github.com/gubarandrej-bit/qwen.git
cd qwen
sudo chown -R $USER:$USER .
```

### Шаг 3: Настройка Backend

```bash
cd backend

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Обновление pip
pip install --upgrade pip

# Установка зависимостей
pip install -r requirements.txt

# Создание директорий
mkdir -p uploads reports logs

# Генерация секретного ключа
SECRET_KEY=$(openssl rand -hex 32)

# Создание файла конфигурации .env
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
DEFAULT_ADMIN_LOGIN=admin
DEFAULT_ADMIN_PASSWORD=Admin@123

# Application Settings
MAX_FILE_SIZE_MB=100
MODE=local

# AI Settings
LOCAL_AI_MODEL=qwen-local
MAX_TOKENS=4096

# Server Settings
HOST=0.0.0.0
PORT=8000
ENVEOF

# Деактивация окружения
deactivate
```

### Шаг 4: Настройка Frontend

```bash
cd frontend

# Установка зависимостей
npm install

# Сборка проекта для production
npm run build

# Возврат в корневую директорию
cd ..
```

### Шаг 5: Инициализация базы данных

```bash
cd backend
source venv/bin/activate

# Инициализация БД
python -c "from app.database.database import init_db; import asyncio; asyncio.run(init_db())"

deactivate
cd ..
```

### Шаг 6: Настройка Nginx

```bash
# Создание конфигурационного файла
sudo nano /etc/nginx/sites-available/qwen-engineering
```

Вставьте следующее содержимое:

```nginx
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
```

Сохраните файл (Ctrl+O, Enter) и выйдите (Ctrl+X).

```bash
# Включение сайта
sudo ln -sf /etc/nginx/sites-available/qwen-engineering /etc/nginx/sites-enabled/

# Удаление дефолтного сайта
sudo rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации
sudo nginx -t

# Перезапуск Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Шаг 7: Создание systemd сервиса

```bash
sudo nano /etc/systemd/system/qwen-engineering.service
```

Вставьте следующее содержимое:

```ini
[Unit]
Description=Engineering Documentation Analysis System
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/qwen/backend
Environment="PATH=/opt/qwen/backend/venv/bin"
ExecStart=/opt/qwen/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10
StandardOutput=append:/opt/qwen/backend/logs/app.log
StandardError=append:/opt/qwen/backend/logs/error.log

# Security settings
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Сохраните файл и выполните:

```bash
# Перезагрузка systemd
sudo systemctl daemon-reload

# Запуск сервиса
sudo systemctl start qwen-engineering
sudo systemctl enable qwen-engineering

# Проверка статуса
sudo systemctl status qwen-engineering
```

### Шаг 8: Настройка брандмауэра (опционально)

```bash
# Если UFW не активен
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable
```

---

## 🎬 Первый запуск и вход

1. **Откройте браузер** и перейдите по адресу:
   ```
   http://ВАШ_IP_СЕРВЕРА
   ```

2. **Введите учетные данные:**
   - Логин: `admin`
   - Пароль: `Admin@123`

3. **⚠️ ВАЖНО:** Сразу после входа смените пароль!

---

## 🔧 Управление системой

### Команды systemctl

```bash
# Проверка статуса
sudo systemctl status qwen-engineering

# Перезапуск
sudo systemctl restart qwen-engineering

# Остановка
sudo systemctl stop qwen-engineering

# Запуск
sudo systemctl start qwen-engineering

# Просмотр логов (real-time)
sudo journalctl -u qwen-engineering -f

# Просмотр последних 50 строк логов
sudo journalctl -u qwen-engineering -n 50 --no-pager
```

### Логи приложения

```bash
# Логи приложения
tail -f /opt/qwen/backend/logs/app.log

# Логи ошибок
tail -f /opt/qwen/backend/logs/error.log
```

### Обновление системы

```bash
cd /opt/qwen
sudo git pull
sudo systemctl restart qwen-engineering
```

### Резервное копирование

```bash
# Создание бэкапа БД
cp /opt/qwen/backend/engineering_docs.db /backup/engineering_docs_$(date +%Y%m%d_%H%M%S).db

# Восстановление из бэкапа
cp /backup/engineering_docs_20240101_120000.db /opt/qwen/backend/engineering_docs.db
sudo systemctl restart qwen-engineering
```

---

## 📡 API Документация

После запуска доступны:

- **Swagger UI:** `http://ВАШ_IP/api/docs`
- **ReDoc:** `http://ВАШ_IP/api/redoc`

### Тестирование API

```bash
# Получение токена доступа
curl -X POST "http://ВАШ_IP/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"Admin@123"}'

# Пример загрузки документа
curl -X POST "http://ВАШ_IP/api/documents/upload" \
  -H "Authorization: Bearer ВАШ_ТОКЕН" \
  -F "file=@/path/to/document.pdf"
```

---

## 🔒 Безопасность

### Смена пароля через консоль

```bash
cd /opt/qwen/backend
source venv/bin/activate

python -c "
from app.database.database import get_db
from app.services.user_service import UserService
from app.models.models import User
import asyncio
import bcrypt

async def change():
    async for db in get_db():
        user = await db.query(User).filter(User.login == 'admin').first()
        if user:
            hashed = bcrypt.hashpw('НовыйПароль123!', bcrypt.gensalt())
            user.hashed_password = hashed.decode()
            await db.commit()
            print('Пароль изменен')

asyncio.run(change())
"
```

### Настройка HTTPS (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ваш-домен.ru
```

---

## 🛠 Диагностика проблем

### Сервис не запускается

```bash
# Проверка логов systemd
journalctl -u qwen-engineering -n 100 --no-pager

# Проверка портов
ss -tlnp | grep :8000
ss -tlnp | grep :80

# Проверка конфигурации
cat /opt/qwen/backend/.env

# Переустановка зависимостей
cd /opt/qwen/backend
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Ошибки Nginx

```bash
# Проверка конфигурации
sudo nginx -t

# Перезапуск
sudo systemctl restart nginx

# Логи nginx
tail -f /var/log/nginx/error.log
```

### Проблемы с памятью

```bash
# Проверка использования памяти
free -h

# Очистка кэша
sync && echo 3 | sudo tee /proc/sys/vm/drop_caches
```

### Проблемы с местом на диске

```bash
# Проверка места
df -h

# Очистка старых логов
find /opt/qwen/backend/logs -name "*.log" -mtime +30 -delete

# Очистка системных пакетов
sudo apt clean
sudo apt autoremove -y
```

---

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи
2. Убедитесь что все порты открыты
3. Проверьте требования к системе
4. Создайте issue на GitHub: https://github.com/gubarandrej-bit/qwen/issues

---

**Версия инструкции:** 1.0  
**Дата:** 2024  
**Поддерживаемые ОС:** Debian 11/12, Ubuntu 20.04/22.04
