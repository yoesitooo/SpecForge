@echo off
title Jarvis — Terminal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
echo.
echo  Jarvis en modo terminal (sin microfono)
echo  Escribe "ayuda" para ver comandos
echo.
set TRANSPORT_MODE=cli
%PY% main.py
pause
