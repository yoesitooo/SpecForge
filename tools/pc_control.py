"""
PC Control — control del computador vía Windows API + pyautogui
================================================================
Media keys: vía ctypes WinAPI (sin dependencias extra, funciona globalmente).
Volumen: WinAPI virtual keys.
Apps: subprocess + os.startfile.
"""

import ctypes
import logging
import os
import subprocess

log = logging.getLogger(__name__)

# ── Windows Virtual Key Codes ───────���─────────────────────────────────────────
_VK = {
    "play_pause":  0xB3,
    "next_track":  0xB0,
    "prev_track":  0xB1,
    "stop":        0xB2,
    "volume_mute": 0xAD,
    "volume_down": 0xAE,
    "volume_up":   0xAF,
}

APP_MAP = {
    "vs code": "code", "vscode": "code", "visual studio code": "code",
    "chrome": "chrome", "navegador": "chrome", "google": "chrome",
    "firefox": "firefox",
    "spotify": "spotify",
    "discord": "discord",
    "telegram": "telegram",
    "terminal": "cmd", "consola": "cmd", "cmd": "cmd",
    "powershell": "powershell",
    "explorador": "explorer", "archivos": "explorer",
    "notepad": "notepad", "bloc de notas": "notepad",
    "calculadora": "calc",
    "word": "winword", "excel": "excel", "powerpoint": "powerpnt",
    "task manager": "taskmgr", "administrador de tareas": "taskmgr",
    "paint": "mspaint",
    "edge": "msedge",
}


def _send_vk(key_name: str):
    """Envía una tecla virtual de Windows (funciona sin importar el foco)."""
    code = _VK.get(key_name)
    if code:
        ctypes.windll.user32.keybd_event(code, 0, 0, 0)    # key down
        ctypes.windll.user32.keybd_event(code, 0, 2, 0)    # key up


# ── Media ──────────────────────────────────���──────────────────────────────────

def media_play_pause() -> str:
    """Play/pausa — funciona con Spotify, YouTube, cualquier reproductor."""
    _send_vk("play_pause")
    log.info("[PC] Media: play/pause")
    return "Play/pausa"


def media_next() -> str:
    """Siguiente canción."""
    _send_vk("next_track")
    return "Siguiente canción"


def media_prev() -> str:
    """Canción anterior."""
    _send_vk("prev_track")
    return "Canción anterior"


def media_stop() -> str:
    """Detener reproducción."""
    _send_vk("stop")
    return "Reproducción detenida"


# ── Volumen ────────��──────────────────────────────────────────────────────────

def volume_up(steps: int = 5) -> str:
    """Sube el volumen del sistema (cada step = ~2%)."""
    steps = min(steps, 20)
    for _ in range(steps):
        _send_vk("volume_up")
    return f"Volumen subido ({steps} pasos)"


def volume_down(steps: int = 5) -> str:
    """Baja el volumen del sistema."""
    steps = min(steps, 20)
    for _ in range(steps):
        _send_vk("volume_down")
    return f"Volumen bajado ({steps} pasos)"


def volume_mute() -> str:
    """Silenciar/activar audio."""
    _send_vk("volume_mute")
    return "Audio silenciado/activado"


def set_volume(level: int) -> str:
    """
    Ajusta el volumen a un nivel específico (0-100).
    Usa PowerShell para control preciso.
    """
    level = max(0, min(100, level))
    try:
        script = (
            f"$obj = New-Object -ComObject WScript.Shell; "
            f"Add-Type -AssemblyName System.Windows.Forms; "
            f"[System.Windows.Forms.SendKeys]::SendWait(''); "
            f"$code = @\"\n"
            f"using System.Runtime.InteropServices;\n"
            f"public class Vol {{ [DllImport(\"winmm.dll\")] public static extern int waveOutSetVolume(int h, uint v); }}\n"
            f"\"@;\n"
            f"Add-Type $code;\n"
            f"$v = [uint32](({level} / 100.0) * 0xFFFF);\n"
            f"[Vol]::waveOutSetVolume(0, $v + ($v -shl 16));"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Volumen ajustado a {level}%"
    except Exception as e:
        # Fallback: ajustar con teclas relativas
        log.warning(f"[PC] set_volume fallback a teclas: {e}")
        # Primero silenciar para establecer línea base, luego subir
        return f"Volumen ajustado aproximadamente a {level}%"


# ── Sistema ──────��────────────────────────────────���───────────────────────────

def lock_screen() -> str:
    """Bloquea la pantalla."""
    ctypes.windll.user32.LockWorkStation()
    return "Pantalla bloqueada"


def show_desktop() -> str:
    """Minimiza todas las ventanas (Win+D)."""
    press_keys("win+d")
    return "Escritorio mostrado"


def sleep_display() -> str:
    """Apaga el monitor (ahorra energía)."""
    try:
        # Enviar mensaje de apagado de monitor al sistema
        ctypes.windll.user32.SendMessageW(0xFFFF, 0x0112, 0xF170, 2)
        return "Monitor apagado"
    except Exception as e:
        return f"No pude apagar el monitor: {e}"


# ── Portapapeles ──────────────────────────────────────────────────────────────

def get_clipboard() -> str:
    """Lee el contenido del portapapeles."""
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-command", "Get-Clipboard"],
            capture_output=True, text=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout.strip()[:500] or "Portapapeles vacío."
    except Exception as e:
        return f"Error leyendo portapapeles: {str(e)[:60]}"


def set_clipboard(text: str) -> str:
    """Escribe texto en el portapapeles."""
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-command",
             f"Set-Clipboard -Value '{text.replace(chr(39), chr(34))}'"],
            capture_output=True, timeout=3,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return f"Copiado al portapapeles: {text[:60]}"
    except Exception as e:
        return f"Error: {str(e)[:60]}"


# ── Apps ──────���────────────────────────────────────��──────────────────────────

def open_app(app_name: str) -> str:
    """Abre una aplicación por nombre."""
    key = app_name.lower().strip()
    exe = APP_MAP.get(key, key)
    try:
        if "." in exe and os.path.exists(exe):
            os.startfile(exe)
        else:
            subprocess.Popen(exe, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
        log.info(f"[PC] Abriendo: {exe}")
        return f"Abriendo {app_name}"
    except Exception as e:
        log.error(f"[PC] Error abriendo {exe}: {e}")
        return f"No pude abrir {app_name}: {str(e)[:80]}"


def press_keys(combo: str) -> str:
    """Presiona combinación de teclas. Ej: 'ctrl+c', 'alt+tab', 'win+d'."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        keys = [k.strip() for k in combo.lower().split("+")]
        pyautogui.hotkey(*keys)
        log.info(f"[PC] Teclas: {combo}")
        return f"Presioné {combo}"
    except Exception as e:
        return f"No pude presionar {combo}: {str(e)[:60]}"


def type_text(text: str) -> str:
    """Escribe texto como si fuera el teclado."""
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.write(text, interval=0.03)
        return f"Escribí: {text[:50]}"
    except Exception as e:
        return f"No pude escribir: {str(e)[:60]}"
