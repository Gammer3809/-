@echo off
REM Скрипт быстрого запуска приложения «Анализ данных о клиентах банка»

cd /d "%~dp0"

echo.
echo 🏦 Запуск системы анализа данных о клиентах банка...
echo ==================================================
echo.

REM Проверка Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Ошибка: Python не установлен
    pause
    exit /b 1
)

REM Проверка необходимых пакетов
echo ✓ Проверка зависимостей...
python -c "import pandas, numpy, matplotlib" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Установка необходимых пакетов...
    pip install -r requirements.txt
)

echo ✓ Запуск приложения...
echo.

REM Запуск приложения
python scripts\main.py

echo.
echo ==================================================
echo ✓ Приложение завершено
pause
