@echo off
title Jarvis — Voz + Telegram + Visual
cd /d "%~dp0"
echo.
echo  Modo combinado: voz + Telegram al mismo tiempo
echo  Abre http://localhost:8000/jarvis en el navegador
echo  Di "Jarvis" para activar por voz
echo  O escribe en Telegram
echo.
set TRANSPORT_MODE=voice
set ENABLE_HTTP=true
python main.py
pause
