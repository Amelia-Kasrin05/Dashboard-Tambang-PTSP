@echo off
cd /d "%~dp0"
echo ========================================================
echo   MINING DASHBOARD LAUNCHER
echo   Memastikan Environment Python yang Benar (System)
echo ========================================================

echo Menjalankan: python -m streamlit run app.py
echo.
python -m streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Terjadi kesalahan.
    pause
)
