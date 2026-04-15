@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title UBP E-Learning Scraper - Persona 3 Reload UI
color 0B

echo ==============================================
echo   UBP E-Learning Scraper
echo   Persona 3 Reload Inspired Launcher
echo ==============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PY_CMD=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PY_CMD=python"
    ) else (
        echo Python tidak ditemukan.
        echo Install Python 3 dulu lalu centang "Add Python to PATH".
        pause
        exit /b 1
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo [1/4] Membuat virtual environment...
    call %PY_CMD% -m venv .venv
    if errorlevel 1 (
        echo Gagal membuat virtual environment.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Gagal mengaktifkan virtual environment.
    pause
    exit /b 1
)

echo [2/4] Update pip...
python -m pip install --upgrade pip >nul

echo [3/4] Install dependency...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Gagal install dependency.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy /y ".env.example" ".env" >nul
        echo.
        echo File .env dibuat dari .env.example
        echo Silakan isi MOODLE_USERNAME dan MOODLE_PASSWORD dulu.
        notepad .env
    ) else (
        echo MOODLE_USERNAME=isi_username_anda> .env
        echo MOODLE_PASSWORD=isi_password_anda>> .env
        notepad .env
    )
)

echo [4/4] Menjalankan aplikasi...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo Aplikasi berhenti karena error.
    pause
)
