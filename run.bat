@echo off
title Autonomous Ops/Dev Agent with Real Guardrails
echo ===================================================================
echo   AUTONOMOUS OPS/DEV AGENT WITH REAL GUARDRAILS
echo   Self-Correcting Multi-Agent DevOps System with Control Dashboard
echo ===================================================================
echo.
echo [1/2] Launching backend server...
start "DevOps Agent Server" python run_server.py
echo.
echo Waiting 2 seconds for server startup...
timeout /t 2 /nobreak >nul
echo.
echo [2/2] Opening Control Dashboard in your browser...
start http://localhost:8000
echo.
echo ===================================================================
echo   System is LIVE at http://localhost:8000
echo   API Docs available at http://localhost:8000/docs
echo.
echo   Press any key to close this launcher.
echo ===================================================================
pause
