@echo off
title Jarvis — Voz + Telegram + Visual
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
echo.
echo  Modo combinado: voz + Telegram al mismo tiempo
echo  Abre http://localhost:8000/jarvis en el navegador
echo  Di "Jarvis" para activar por voz, o escribe en Telegram
echo.
set TRANSPORT_MODE=voice,telegram
set ENABLE_HTTP=true
%PY% main.py
pause
