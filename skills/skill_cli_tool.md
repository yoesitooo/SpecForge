# Skill: CLI Tool (Typer + Rich)

## Stack
- **Framework:** Typer (basado en Click, con type hints)
- **Output:** Rich (tablas, progreso, colores, panels)
- **Config:** Dynaconf o simple TOML en ~/.config/
- **Packaging:** pyproject.toml con [project.scripts]
- **Testing:** pytest + typer.testing.CliRunner

## Estructura
```
mytool/
├── __init__.py
├── cli.py               # Comandos Typer
├── core/
│   ├── __init__.py
│   └── logic.py         # Lógica de negocio (sin I/O)
├── config.py            # Configuración del usuario
└── utils.py
pyproject.toml
```

## Setup base
```python
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="Descripción de la herramienta")
console = Console()

@app.command()
def main(
    input: str = typer.Argument(..., help="Archivo de entrada"),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
    output: Path = typer.Option(Path("output.txt"), "--output", "-o"),
):
    """Procesa el archivo de entrada."""
    if verbose:
        console.print(f"[dim]Procesando {input}...[/dim]")
    ...

if __name__ == "__main__":
    app()
```

## Output con Rich
```python
# Tabla
table = Table(title="Resultados")
table.add_column("ID", style="cyan")
table.add_column("Nombre", style="green")
table.add_column("Estado")
for row in data:
    table.add_row(str(row.id), row.name, "[green]OK[/green]")
console.print(table)

# Barra de progreso
from rich.progress import track
for item in track(items, description="Procesando..."):
    process(item)

# Panel de error
from rich.panel import Panel
console.print(Panel(f"[red]Error:[/red] {msg}", title="Fallo"))
raise typer.Exit(1)
```

## Config persistente
```python
import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "mytool" / "config.toml"

def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    return tomllib.loads(CONFIG_PATH.read_text())
```

## Subcomandos
```python
app = typer.Typer()
db_app = typer.Typer()
app.add_typer(db_app, name="db")

@db_app.command("migrate")
def db_migrate(): ...

@db_app.command("seed")
def db_seed(): ...
# Uso: mytool db migrate
```

## pyproject.toml para instalación
```toml
[project.scripts]
mytool = "mytool.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## Reglas
- Toda I/O en cli.py, lógica en core/
- Errores: `console.print("[red]Error[/red]")` + `raise typer.Exit(1)`
- Confirmaciones destructivas: `typer.confirm("¿Seguro?", abort=True)`
- Autocompletion gratis con Typer + `typer.completion.install()`
