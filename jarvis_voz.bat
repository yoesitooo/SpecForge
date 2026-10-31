@echo off
title Jarvis — Modo Voz
cd /d "%~dp0"
echo.
echo  Iniciando Jarvis con voz y visual...
echo  Abre http://localhost:8000/jarvis en el navegador
echo  Di "Jarvis" para activar
echo.
set TRANSPORT_MODE=voice
set ENABLE_HTTP=true
python main.py
pause
