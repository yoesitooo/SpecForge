@echo off
rem Uso: specforge generar "idea"  |  specforge reparar RUTA --prueba "pytest -q"  |  specforge diagnostico
rem No cambia de carpeta: las rutas que pases son relativas a donde estas.
set "SF=%~dp0"
if exist "%SF%.venv\Scripts\python.exe" (set "PY=%SF%.venv\Scripts\python.exe") else (set "PY=python")
set "PYTHONPATH=%SF%;%PYTHONPATH%"
"%PY%" -m specforge %*
