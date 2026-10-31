"""
Project Scaffold — crea la estructura base de un proyecto Next.js 15
====================================================================
El DAG genera código asumiendo que ya existe un proyecto base.
Este scaffold lo crea ANTES de que los agentes empiecen a escribir código.
Sin esto, el código generado no tiene dónde vivir y no puede ejecutarse.

Genera:
  package.json     — dependencias exactas Next.js 15 + React 19 + Tailwind v4
  next.config.ts   — configuración base
  tsconfig.json    — TypeScript estricto
  src/app/layout.tsx   — root layout con fuentes
  src/app/globals.css  — Tailwind v4 @theme base
  src/app/page.tsx     — placeholder (el agente lo sobreescribe)
  src/lib/utils.ts     — cn() helper para classnames
  public/.gitkeep      — directorio público vacío

Para proyectos sin frontend (api_only, cli_tool, telegram_bot):
  requirements.txt + main.py skeleton en Python.
"""

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)


def scaffold_nextjs(workspace: Path, project_name: str) -> str:
    """
    Crea estructura base de Next.js 15. Retorna resumen de lo creado.
    """
    workspace.mkdir(parents=True, exist_ok=True)
    created = []

    def write(rel: str, content: str):
        p = workspace / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():  # No sobreescribir si ya existe
            p.write_text(content, encoding="utf-8")
            created.append(rel)

    # ── package.json ──────────────────────────────────────────────────────
    pkg = {
        "name": project_name.lower().replace(" ", "-"),
        "version": "0.1.0",
        "private": True,
        "scripts": {
            "dev": "next dev --turbopack",
            "build": "next build",
            "start": "next start",
            "lint": "next lint",
        },
        "dependencies": {
            "next": "15.3.0",
            "react": "19.0.0",
            "react-dom": "19.0.0",
            "clsx": "^2.1.1",
            "tailwind-merge": "^2.5.4",
            "class-variance-authority": "^0.7.1",
            "lucide-react": "^0.468.0",
        },
        "devDependencies": {
            "@types/node": "^22",
            "@types/react": "^19",
            "@types/react-dom": "^19",
            "typescript": "^5.7.2",
            "@tailwindcss/postcss": "^4",
            "tailwindcss": "^4",
        },
    }
    write("package.json", json.dumps(pkg, indent=2))

    # ── next.config.ts ────────────────────────────────────────────────────
    write("next.config.ts", """\
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      { protocol: "https", hostname: "placehold.co" },
      { protocol: "https", hostname: "images.unsplash.com" },
    ],
  },
};

export default nextConfig;
""")

    # ── tsconfig.json ────────────────────────────────────────────────────
    write("tsconfig.json", """\
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
""")

    # ── postcss.config.mjs ───────────────────────────────────────────────
    write("postcss.config.mjs", """\
const config = { plugins: { "@tailwindcss/postcss": {} } };
export default config;
""")

    # ── src/app/globals.css ───────────────────────────────────────────────
    write("src/app/globals.css", f"""\
@import "tailwindcss";

@theme {{
  --font-sans: "Inter", "system-ui", sans-serif;
  --color-background: #0a0a0a;
  --color-foreground: #fafafa;
  --color-primary: #6366f1;
  --color-primary-foreground: #ffffff;
  --color-muted: #1a1a2e;
  --color-muted-foreground: #94a3b8;
  --color-border: rgba(255,255,255,0.08);
  --color-card: rgba(255,255,255,0.04);
  --radius: 0.75rem;
}}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
  background-color: var(--color-background);
  color: var(--color-foreground);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}}
""")

    # ── src/app/layout.tsx ───────────────────────────────────────────────
    display_name = project_name.replace("_", " ").replace("-", " ").title()
    write("src/app/layout.tsx", f"""\
import type {{ Metadata }} from "next";
import {{ Inter }} from "next/font/google";
import "./globals.css";

const inter = Inter({{ subsets: ["latin"], variable: "--font-sans" }});

export const metadata: Metadata = {{
  title: "{display_name}",
  description: "Generado por SDD Ecosystem",
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="es" className="dark">
      <body className={{`${{inter.variable}} antialiased`}}>{{children}}</body>
    </html>
  );
}}
""")

    # ── src/app/page.tsx (placeholder) ───────────────────────────────────
    write("src/app/page.tsx", f"""\
// Este archivo será sobreescrito por el agente de frontend
export default function HomePage() {{
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold text-white">{display_name}</h1>
      <p className="mt-4 text-muted-foreground">Generando contenido...</p>
    </main>
  );
}}
""")

    # ── src/lib/utils.ts ─────────────────────────────────────────────────
    write("src/lib/utils.ts", """\
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
""")

    # ── public/.gitkeep ──────────────────────────────────────────────────
    write("public/.gitkeep", "")

    # ── .gitignore del proyecto ───────────────────────────────────────────
    write(".gitignore", """\
# Next.js
.next/
out/
node_modules/
.env
.env.local
.env.production

# Build
build/
dist/

# OS
.DS_Store
Thumbs.db
""")

    log.info(f"[SCAFFOLD] Next.js creado en {workspace} — {len(created)} archivos")

    if not created:
        return f"Proyecto ya inicializado en {workspace}"

    return (
        f"Proyecto Next.js 15 scaffolded: {workspace.name}\n"
        f"Archivos creados: {', '.join(created[:6])}{'...' if len(created) > 6 else ''}\n"
        f"Ejecuta: cd {workspace} && npm install && npm run dev"
    )


def scaffold_python(workspace: Path, project_name: str, project_type: str = "api") -> str:
    """Estructura base para proyectos Python puro (API, bot, CLI, agente)."""
    workspace.mkdir(parents=True, exist_ok=True)
    created = []

    def write(rel: str, content: str):
        p = workspace / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            created.append(rel)

    name = project_name.lower().replace(" ", "_").replace("-", "_")

    write("requirements.txt", "# Dependencias del proyecto\n# Generado por SDD Ecosystem\n")
    write(".env.example", "# Variables de entorno\n")
    write(".gitignore", "__pycache__/\n*.pyc\n.env\n*.db\n.venv/\n")
    write("README.md", f"# {project_name}\n\nGenerado por SDD Ecosystem.\n")

    if project_type == "telegram_bot":
        write("main.py", f"\"\"\"Bot de Telegram — {project_name}\"\"\"\nimport asyncio\n\nasync def main():\n    pass\n\nif __name__ == '__main__':\n    asyncio.run(main())\n")
        write("handlers/__init__.py", "")
        write("services/__init__.py", "")
    elif project_type == "api_service":
        write("main.py", f"\"\"\"API — {project_name}\"\"\"\nfrom fastapi import FastAPI\n\napp = FastAPI(title='{project_name}')\n\n@app.get('/health')\ndef health(): return {{'status': 'ok'}}\n")
        write("routers/__init__.py", "")
        write("models/__init__.py", "")
        write("schemas/__init__.py", "")
    elif project_type == "cli_tool":
        write(f"{name}.py", f"\"\"\"CLI — {project_name}\"\"\"\nimport typer\n\napp = typer.Typer()\n\n@app.command()\ndef main(): pass\n\nif __name__ == '__main__':\n    app()\n")
    else:
        write("main.py", f"\"\"\"Proyecto: {project_name}\"\"\"\n")

    return (
        f"Proyecto Python scaffolded: {workspace.name}\n"
        f"Tipo: {project_type}\n"
        f"Archivos: {', '.join(created)}"
    )


def scaffold_project(workspace_root: str, project_name: str, project_type: str = "web_saas") -> str:
    """
    Punto de entrada principal. Elige scaffold según el tipo.
    """
    clean_name = project_name.strip().replace(" ", "_")
    workspace = Path(workspace_root) / clean_name

    PYTHON_TYPES = {"telegram_bot", "discord_bot", "api_service", "data_pipeline", "cli_tool", "ai_agent"}

    if project_type in PYTHON_TYPES:
        return scaffold_python(workspace, project_name, project_type)
    else:
        # web_saas, landing, ecommerce, dashboard, mobile_app, desktop_app
        return scaffold_nextjs(workspace, project_name)
