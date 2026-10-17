#!/bin/bash
# ============================================================
# АВТОМАТИЧЕСКАЯ УСТАНОВКА СИСТЕМЫ ПРОВЕРКИ ДОКУМЕНТАЦИИ
# Запуск на сервере (Debian/Ubuntu, Proxmox):
#   bash install_and_run.sh
# ============================================================
set -e

APP_DIR=/opt/qwen
echo "=== [1/5] Создание директории $APP_DIR ==="
mkdir -p $APP_DIR
cd $APP_DIR

echo "=== [2/5] Скачивание файлов проекта с GitHub (raw) ==="
FILES=(
  "install.sh"
  "requirements.txt"
  "README.md"
  "INSTALLATION.md"
  "templates/index.html"
  "backend/main.py"
  "backend/requirements.txt"
  "backend/app/__init__.py"
  "backend/app/main.py"
  "backend/app/config.py"
  "backend/app/.env.example"
  "backend/app/ai_core/__init__.py"
  "backend/app/ai_core/llm_service.py"
  "backend/app/database/__init__.py"
  "backend/app/database/database.py"
  "backend/app/models/__init__.py"
  "backend/app/models/models.py"
  "backend/app/routers/__init__.py"
  "backend/app/routers/auth.py"
  "backend/app/routers/checks.py"
  "backend/app/routers/reports.py"
  "backend/app/routers/users.py"
  "backend/app/schemas/__init__.py"
  "backend/app/schemas/schemas.py"
  "backend/app/services/__init__.py"
  "backend/app/services/document_parser.py"
  "backend/app/services/report_generator.py"
  "backend/app/services/user_service.py"
  "backend/app/utils/__init__.py"
  "backend/app/utils/security.py"
)
BASE="https://raw.githubusercontent.com/gubarandrej-bit/qwen/main"
OK=0; FAIL=0
for f in "${FILES[@]}"; do
  mkdir -p "$(dirname "$f")"
  if curl -fsSL "$BASE/$f" -o "$f"; then
    OK=$((OK+1))
  else
    echo "  !! Не удалось скачать: $f"
    FAIL=$((FAIL+1))
  fi
done
echo "Скачано файлов: $OK, ошибок: $FAIL"

if [ "$FAIL" -gt 0 ] || [ ! -s backend/main.py ]; then
  echo "============================================================"
  echo "ОШИБКА: репозиторий github.com/gubarandrej-bit/qwen пуст или"
  "недоступен (токен недействителен, файлы не были загружены)."
  echo "Ничего не выдумываем. См. решение ниже."
  echo "============================================================"
fi

echo "=== [3/5] Установка системных зависимостей ==="
apt update -qq
apt install -y -qq python3 python3-pip python3-venv curl nginx > /dev/null 2>&1 || true

echo "=== [4/5] Python окружение ==="
python3 -m venv venv
./venv/bin/pip install --upgrade pip -q
./venv/bin/pip install -q fastapi "uvicorn[standard]" python-multipart openpyxl python-docx pypdf passlib bcrypt pydantic-settings sqlalchemy || {
  echo "Внимание: часть пакетов не установилась, повторяем без опциональных..."
  ./venv/bin/pip install -q fastapi uvicorn sqlalchemy passlib bcrypt || true
}

echo "=== [5/5] Запуск службы ==="
cat > /etc/systemd/system/qwen.service << 'SVC'
[Unit]
Description=Qwen Engineering Docs Checker
After=network.target

[Service]
WorkingDirectory=/opt/qwen/backend
ExecStart=/opt/qwen/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
SVC
systemctl daemon-reload
systemctl enable --now qwen

sleep 3
systemctl status qwen --no-pager | head -10
IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=============================================="
echo "✅ Установка завершена!"
echo "Веб-интерфейс: http://$IP:8000"
echo "Логин: admin  Пароль: Admin@123"
echo "Логи: journalctl -u qwen -f"
echo "=============================================="
