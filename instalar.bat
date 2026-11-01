@echo off
title SpecForge — Instalacion
cd /d "%~dp0"
echo.
echo  1/4 Creando entorno virtual (.venv)...
if not exist ".venv\Scripts\python.exe" python -m venv .venv || goto :error
echo  2/4 Instalando dependencias...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul
".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
echo  3/4 Preparando .env...
if not exist ".env" (copy ".env.example" ".env" >nul & echo     Se creo .env: agrega al menos una clave gratis o inicia sesion con agy / claude.) else (echo     .env ya existe, no se toca.)
echo  4/4 Probando proveedores...
".venv\Scripts\python.exe" -m specforge diagnostico
echo.
echo  Listo. Ejemplo: specforge generar "agenda de citas para un consultorio"
pause
exit /b 0
:error
echo  La instalacion fallo. Revisa el mensaje de arriba.
pause
exit /b 1
