@echo off
title Jarvis — Telegram
cd /d "%~dp0"
echo.
echo  Bot de Telegram activo
echo  Escríbele a tu bot en Telegram
echo  Ctrl+C para detener
echo.
set TRANSPORT_MODE=telegram
python main.py
pause
