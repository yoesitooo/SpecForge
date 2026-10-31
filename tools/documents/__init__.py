"""documents/ — Generación de Word, Excel, PowerPoint, PDF y notas."""
from tools.document_writer import (
    create_word_doc,
    create_excel,
    create_presentation,
    create_pdf,
    write_note,
    open_file,
    list_files,
    JARVIS_DOCS,
)

__all__ = [
    "create_word_doc", "create_excel", "create_presentation",
    "create_pdf", "write_note", "open_file", "list_files",
    "JARVIS_DOCS",
]
