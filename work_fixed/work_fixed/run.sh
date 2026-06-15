#!/bin/bash
# Скрипт быстрого запуска приложения «Анализ данных о клиентах банка»

cd "$(dirname "$0")" || exit 1

echo "🏦 Запуск системы анализа данных о клиентах банка..."
echo "=================================================="
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Ошибка: Python3 не установлен"
    exit 1
fi

# Проверка необходимых пакетов
echo "✓ Проверка зависимостей..."
python3 -c "import pandas, numpy, matplotlib" 2>/dev/null || {
    echo "⚠️  Установка необходимых пакетов..."
    pip3 install -r requirements.txt
}

echo "✓ Запуск приложения..."
echo ""

# Запуск приложения
python3 scripts/main.py

echo ""
echo "=================================================="
echo "✓ Приложение завершено"
