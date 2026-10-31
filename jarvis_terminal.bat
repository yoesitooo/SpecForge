@echo off
title Jarvis — Terminal
cd /d "%~dp0"
echo.
echo  Jarvis en modo terminal (sin microfono)
echo  Escribe "ayuda" para ver comandos
echo.
set TRANSPORT_MODE=cli
python main.py
pause
