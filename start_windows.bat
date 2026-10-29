@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv315\Scripts\python.exe" (
    py -3.15 -m venv .venv315
    if errorlevel 1 goto error
)
.venv315\Scripts\python.exe -m pip install -r requirements.lock
if errorlevel 1 goto error
.venv315\Scripts\python.exe -m streamlit run app.py
if errorlevel 1 goto error
exit /b 0
:error
echo.
echo Startup failed. Copy the error text from this window.
pause
exit /b 1
