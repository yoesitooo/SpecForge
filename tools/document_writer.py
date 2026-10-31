"""
Document Writer — Word, Excel, PowerPoint, PDF, notas de texto
==============================================================
Todos los archivos se guardan en ~/Documents/Jarvis/ y se abren automáticamente.
El LLM genera el contenido como argumentos estructurados; este módulo da formato.
"""

import logging
import os
import webbrowser
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

JARVIS_DOCS = Path.home() / "Documents" / "Jarvis"


def _folder() -> Path:
    JARVIS_DOCS.mkdir(parents=True, exist_ok=True)
    return JARVIS_DOCS


def _stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _open(path: Path):
    try:
        os.startfile(str(path))
    except Exception as e:
        log.warning(f"[DOCS] No pude abrir {path}: {e}")


# ── Word ──────────────────────────────────────────────────────────────────────

def create_word_doc(
    title: str,
    sections: list[dict],
    filename: str = "",
    author: str = "Jarvis",
) -> str:
    """
    Crea un documento Word (.docx).

    sections: lista de {"heading": "...", "content": "..."}
    Ejemplo:
      [{"heading": "Resumen", "content": "Este proyecto..."},
       {"heading": "Objetivos", "content": "1. Automatizar..."}]
    """
    try:
        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
    except ImportError:
        return "Error: instala python-docx con pip install python-docx"

    doc = Document()

    # Título principal
    title_par = doc.add_heading(title, level=0)
    title_par.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Metadata sutil
    meta = doc.add_paragraph(f"Generado por Jarvis · {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.runs[0].font.color.rgb = RGBColor(0x80, 0x80, 0x80)
    meta.runs[0].font.size = Pt(9)

    doc.add_paragraph()  # Espacio

    for section in sections:
        heading = section.get("heading", "")
        content = section.get("content", "")
        if heading:
            doc.add_heading(heading, level=1)
        if content:
            # Soporta saltos de línea como ítems de lista
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    continue
                if line.startswith(("- ", "• ", "* ")):
                    doc.add_paragraph(line[2:], style="List Bullet")
                elif line[0].isdigit() and ". " in line[:4]:
                    doc.add_paragraph(line.split(". ", 1)[-1], style="List Number")
                else:
                    doc.add_paragraph(line)

    fname = (filename or f"{title.replace(' ', '_')}_{_stamp()}") + ".docx"
    path = _folder() / fname
    doc.save(str(path))
    _open(path)
    log.info(f"[DOCS] Word creado: {path}")
    return f"Documento Word creado: {path.name}\nGuardado en: {path.parent}"


# ── Excel ─────────────────────────────────────────────────────────────────────

def create_excel(
    title: str,
    headers: list[str],
    rows: list[list],
    filename: str = "",
    sheet_name: str = "Datos",
) -> str:
    """
    Crea una hoja de cálculo Excel (.xlsx).

    headers: ["Nombre", "Precio", "Cantidad"]
    rows: [["Pizza Margherita", 25000, 3], ["Pizza BBQ", 28000, 2]]
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        return "Error: instala openpyxl con pip install openpyxl"

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name

    # Título
    ws.merge_cells(f"A1:{get_column_letter(len(headers))}1")
    ws["A1"] = title
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = Alignment(horizontal="center")

    # Headers con estilo
    header_fill = PatternFill("solid", fgColor="1F4E79")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Datos con filas alternadas
    alt_fill = PatternFill("solid", fgColor="EBF3FB")
    for r_idx, row in enumerate(rows, 3):
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=val)
            if r_idx % 2 == 1:
                cell.fill = alt_fill
            cell.alignment = Alignment(horizontal="left")

    # Auto-ancho de columnas
    for col in ws.columns:
        max_len = max((len(str(c.value or "")) for c in col), default=10)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len + 4, 40)

    fname = (filename or f"{title.replace(' ', '_')}_{_stamp()}") + ".xlsx"
    path = _folder() / fname
    wb.save(str(path))
    _open(path)
    log.info(f"[DOCS] Excel creado: {path}")
    return f"Excel creado: {path.name} ({len(rows)} filas)\nGuardado en: {path.parent}"


# ── PowerPoint ────────────────────────────────────────────────────────────────

def create_presentation(
    title: str,
    slides: list[dict],
    filename: str = "",
) -> str:
    """
    Crea presentación PowerPoint (.pptx).

    slides: lista de {"title": "...", "content": "...", "notes": "..."}
    El content puede tener ítems separados por \\n para bullets automáticos.
    """
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
    except ImportError:
        return "Error: instala python-pptx con pip install python-pptx"

    prs = Presentation()
    prs.slide_width  = Inches(13.33)
    prs.slide_height = Inches(7.5)

    # Slide de título
    slide_layout = prs.slide_layouts[0]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = title
    if slide.placeholders[1] is not None:
        slide.placeholders[1].text = f"Generado por Jarvis · {datetime.now().strftime('%d/%m/%Y')}"

    # Slides de contenido
    content_layout = prs.slide_layouts[1]  # Title + Content
    for s in slides:
        sl = prs.slides.add_slide(content_layout)
        sl.shapes.title.text = s.get("title", "")

        tf = sl.placeholders[1].text_frame
        tf.clear()
        content = s.get("content", "")
        lines = [l.strip() for l in content.split("\n") if l.strip()]

        for i, line in enumerate(lines):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()

            # Bullets automáticos si empieza con - o •
            if line.startswith(("- ", "• ", "* ")):
                p.level = 1
                line = line[2:]
            else:
                p.level = 0

            p.text = line

        # Notas del presentador
        notes = s.get("notes", "")
        if notes:
            sl.notes_slide.notes_text_frame.text = notes

    fname = (filename or f"{title.replace(' ', '_')}_{_stamp()}") + ".pptx"
    path = _folder() / fname
    prs.save(str(path))
    _open(path)
    log.info(f"[DOCS] PPT creado: {path}")
    return f"Presentación creada: {path.name} ({len(slides)} slides)\nGuardado en: {path.parent}"


# ── PDF ───────────────────────────────────────────────────────────────────────

def create_pdf(
    title: str,
    content: str,
    filename: str = "",
) -> str:
    """
    Crea un PDF simple con título y contenido.
    Ideal para reportes, resúmenes, briefs.
    """
    try:
        from fpdf import FPDF
    except ImportError:
        return "Error: instala fpdf2 con pip install fpdf2"

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(31, 78, 121)
            self.cell(0, 10, title, align="C", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(31, 78, 121)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Generado por Jarvis · {datetime.now().strftime('%d/%m/%Y')} · Pág. {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(40, 40, 40)

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            pdf.ln(3)
            continue
        # Detectar títulos de sección (líneas en MAYÚSCULAS o que terminan en :)
        if line.isupper() or (line.endswith(":") and len(line) < 60):
            pdf.ln(2)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(31, 78, 121)
            pdf.cell(0, 8, line, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(40, 40, 40)
        elif line.startswith(("- ", "• ")):
            pdf.cell(6, 6, "•")
            pdf.multi_cell(0, 6, line[2:])
        else:
            pdf.multi_cell(0, 6, line)

    fname = (filename or f"{title.replace(' ', '_')}_{_stamp()}") + ".pdf"
    path = _folder() / fname
    pdf.output(str(path))
    _open(path)
    log.info(f"[DOCS] PDF creado: {path}")
    return f"PDF creado: {path.name}\nGuardado en: {path.parent}"


# ── Texto / Nota rápida ───────────────────────────────────────────────────────

def write_note(content: str, filename: str = "") -> str:
    """Guarda una nota rápida en texto plano (.txt)."""
    fname = (filename or f"nota_{_stamp()}") + ".txt"
    path = _folder() / fname
    path.write_text(content, encoding="utf-8")
    _open(path)
    log.info(f"[DOCS] Nota creada: {path}")
    return f"Nota guardada: {path.name}"


# ── Utilidades ────────────────────────────────────────────────────────────────

def open_file(filepath: str) -> str:
    """Abre cualquier archivo con la aplicación por defecto."""
    p = Path(filepath)
    if not p.exists():
        # Buscar en la carpeta de Jarvis
        candidate = JARVIS_DOCS / filepath
        if candidate.exists():
            p = candidate
        else:
            return f"Archivo no encontrado: {filepath}"
    try:
        os.startfile(str(p))
        return f"Abriendo: {p.name}"
    except Exception as e:
        return f"No pude abrir {p.name}: {e}"


def list_files(subfolder: str = "") -> str:
    """Lista los archivos guardados por Jarvis."""
    folder = JARVIS_DOCS / subfolder if subfolder else JARVIS_DOCS
    if not folder.exists():
        return "No hay archivos guardados aún."

    files = sorted(folder.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True)
    if not files:
        return "Carpeta vacía."

    lines = [f"Archivos en {folder}:", ""]
    for f in files[:20]:
        size = f.stat().st_size
        size_str = f"{size // 1024} KB" if size > 1024 else f"{size} B"
        modified = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d/%m %H:%M")
        lines.append(f"  {f.name:45s} {size_str:8s} {modified}")

    return "\n".join(lines)
