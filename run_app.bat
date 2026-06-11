@echo off
title PDC RAG Chatbot Launcher
echo ====================================================================
echo    Parallel ^& Distributed Computing RAG Chatbot Launcher
echo ====================================================================
echo.
echo [1/3] Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your system PATH.
    echo Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo [2/3] Verifying and installing Python dependencies...
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [WARNING] Failed to verify/install some libraries. Attempting to start server anyway...
)

echo [3/3] Launching Flask server backend...
echo.
echo --------------------------------------------------------------------
echo   Server is starting up!
echo   Open your browser and navigate to: http://127.0.0.1:5000
echo   To terminate the application, press Ctrl+C in this window.
echo --------------------------------------------------------------------
echo.
python app.py
pause
