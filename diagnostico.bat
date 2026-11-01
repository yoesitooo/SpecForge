@echo off
title SpecForge — Diagnostico de proveedores
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (set "PY=python")
%PY% -m providers.diagnostico
pause
