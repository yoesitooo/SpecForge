import os
import subprocess
import sys
from datetime import datetime

# Calcula la ruta dinámica desde la ubicación del script
# scripts/ -> AgentHub/ -> skills/
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_HUB_DIR = os.path.dirname(SCRIPT_DIR)  # sube de scripts/ a AgentHub/
SKILLS_DIR = os.path.join(AGENT_HUB_DIR, "skills")
sys.path.append(SKILLS_DIR)

try:
    from engram import engram_sync, init_db
except ImportError:
    print("⚠️ No se pudo importar engram.py. Asegúrate de que el path es correcto.")
    engram_sync = None
    init_db = None

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR ejecutando: {command}\n{e.stderr}")
        return None

def sync_brain():
    print(f"[SYNC] Iniciando sincronizacion del Cerebro SDD... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Inicializar DB si es necesario
    if init_db:
        init_db()

    # 1. Exportar memoria Engram a JSON
    if engram_sync:
        export_path = os.path.join(AGENT_HUB_DIR, "memory", "engram_export.json")
        engram_sync(export_path)
        print("OK: Memoria Engram exportada a JSON.")

    # 2. Git Workflow
    print("GIT: Sincronizando con GitHub...")
    run_command("git add .")
    
    # Verificar si hay cambios
    status = run_command("git status --porcelain")
    if not status:
        print("DONE: Nada nuevo que sincronizar. El cerebro ya está al día.")
        return

    commit_msg = f"SDD Brain Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run_command(f'git commit -m "{commit_msg}"')
    
    # Intentar Push
    print("GIT: Empujando cambios a la nube...")
    # Asegurarnos de que estamos en la rama main
    run_command("git branch -M main")
    push_result = run_command("git push origin main")
    
    if push_result is not None:
        print("SUCCESS: [SYNC COMPLETO] El conocimiento ha sido respaldado en GitHub.")
    else:
        print("WARNING: El Push fallo. Probablemente necesitas configurar tus credenciales de GitHub.")

if __name__ == "__main__":
    sync_brain()
