"""
System Info — estado del computador en tiempo real
===================================================
CPU, RAM, disco, batería, procesos, temperatura.
Requiere: psutil (pip install psutil)
"""

import logging

log = logging.getLogger(__name__)


def get_status() -> str:
    """Resumen completo del estado del sistema."""
    try:
        import psutil
        lines = []

        # CPU
        cpu = psutil.cpu_percent(interval=0.5)
        cores = psutil.cpu_count()
        lines.append(f"CPU: {cpu}% ({cores} núcleos)")

        # RAM
        mem = psutil.virtual_memory()
        used_gb = mem.used / 1e9
        total_gb = mem.total / 1e9
        lines.append(f"RAM: {used_gb:.1f} / {total_gb:.1f} GB ({mem.percent}%)")

        # Disco principal
        disk = psutil.disk_usage("/")
        free_gb = disk.free / 1e9
        total_disk = disk.total / 1e9
        lines.append(f"Disco C: {free_gb:.1f} GB libres de {total_disk:.1f} GB ({disk.percent}% usado)")

        # Batería
        try:
            bat = psutil.sensors_battery()
            if bat:
                status = "cargando" if bat.power_plugged else "descargando"
                lines.append(f"Batería: {bat.percent:.0f}% ({status})")
        except Exception:
            pass

        return " | ".join(lines)

    except ImportError:
        return "psutil no instalado. Ejecuta: pip install psutil"
    except Exception as e:
        return f"Error obteniendo info del sistema: {e}"


def get_cpu() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        freq = psutil.cpu_freq()
        freq_str = f" a {freq.current:.0f} MHz" if freq else ""
        return f"CPU al {cpu}%{freq_str}"
    except Exception as e:
        return f"Error: {e}"


def get_ram() -> str:
    try:
        import psutil
        mem = psutil.virtual_memory()
        used = mem.used / 1e9
        total = mem.total / 1e9
        avail = mem.available / 1e9
        return f"RAM: {used:.1f} GB usados de {total:.1f} GB ({avail:.1f} GB disponibles)"
    except Exception as e:
        return f"Error: {e}"


def get_disk(path: str = "/") -> str:
    try:
        import psutil
        disk = psutil.disk_usage(path)
        free = disk.free / 1e9
        total = disk.total / 1e9
        return f"Disco: {free:.1f} GB libres de {total:.1f} GB ({disk.percent}% ocupado)"
    except Exception as e:
        return f"Error: {e}"


def get_top_processes(n: int = 5) -> str:
    """Los N procesos que más CPU consumen."""
    try:
        import psutil
        procs = []
        for p in psutil.process_iter(['name', 'cpu_percent', 'memory_percent']):
            try:
                procs.append(p.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        procs.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        lines = [f"{p['name']} — CPU {p.get('cpu_percent',0):.1f}% | RAM {p.get('memory_percent',0):.1f}%"
                 for p in procs[:n]]
        return "\n".join(lines) if lines else "No hay procesos visibles."
    except Exception as e:
        return f"Error: {e}"


def kill_process(name: str) -> str:
    """Cierra un proceso por nombre."""
    try:
        import psutil
        killed = []
        for p in psutil.process_iter(['name', 'pid']):
            try:
                if name.lower() in p.info['name'].lower():
                    p.kill()
                    killed.append(p.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        if killed:
            return f"Cerré: {', '.join(set(killed))}"
        return f"No encontré ningún proceso llamado '{name}'."
    except Exception as e:
        return f"Error: {e}"
