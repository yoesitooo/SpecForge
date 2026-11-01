#!/usr/bin/env bash
# SpecForge — instalación en Linux / macOS
set -euo pipefail
cd "$(dirname "$0")"
echo "1/4 Creando entorno virtual (.venv)..."
[ -x .venv/bin/python ] || python3 -m venv .venv
echo "2/4 Instalando dependencias..."
.venv/bin/python -m pip install --upgrade pip >/dev/null
.venv/bin/python -m pip install -e .
echo "3/4 Preparando .env..."
if [ ! -f .env ]; then cp .env.example .env; echo "    Se creó .env: agrega al menos una clave gratis o inicia sesión con agy / claude."; else echo "    .env ya existe, no se toca."; fi
echo "4/4 Probando proveedores..."
.venv/bin/python -m specforge diagnostico || true
echo
echo "Listo. Activa el entorno (source .venv/bin/activate) y escribe: specforge"
