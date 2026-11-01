@echo off
title Jarvis — Telegram
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
echo.
echo  Bot de Telegram activo
echo  Escribele a tu bot en Telegram
echo  Ctrl+C para detener
echo.
set TRANSPORT_MODE=telegram
%PY% main.py
pause
