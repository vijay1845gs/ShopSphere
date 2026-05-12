@echo off
title ShopSphere Startup

echo =====================================
echo Starting ShopSphere Services...
echo =====================================
echo.

REM Go to project folder
cd /d "%~dp0"

REM Check if venv exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Creating virtual environment...
    python -m venv venv

    echo Installing dependencies...
    call venv\Scripts\activate
    pip install -r requirements.txt
)

REM Activate virtual environment
call venv\Scripts\activate

echo Starting Django Server...
start "1/3 - Django Server" cmd /k "title 1/3 - Django Server && python manage.py runserver"

timeout /t 3 >nul

echo Checking Redis...
start "2/3 - Redis" cmd /k "title 2/3 - Redis && memurai-cli ping && echo Redis Running"

timeout /t 2 >nul

echo Starting Celery Worker...
start "3/3 - Celery Worker" cmd /k "title 3/3 - Celery Worker && python -m celery -A config worker -l info -P solo"

echo.
echo =====================================
echo ShopSphere Started Successfully!
echo =====================================
pause