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

echo [3/3] Launching Streamlit application...
echo.
echo --------------------------------------------------------------------
echo   Application is starting up!
echo   Streamlit will automatically open a browser window.
echo   To terminate the application, press Ctrl+C in this window.
echo --------------------------------------------------------------------
echo.
python -m streamlit run streamlit_app.py
pause
