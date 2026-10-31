"""
Web Search — DuckDuckGo, sin API key.
"""

import asyncio
import logging
from typing import List, Dict

log = logging.getLogger(__name__)


async def search(query: str, max_results: int = 5) -> List[Dict]:
    """Devuelve lista de {title, url, body}."""
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(DDGS().text(query, max_results=max_results))
        )
        return results or []
    except ImportError:
        log.error("[SEARCH] duckduckgo-search no instalado")
        return [{"title": "Error", "url": "", "body": "Instalar: pip install duckduckgo-search"}]
    except Exception as e:
        log.error(f"[SEARCH] Error: {e}")
        return [{"title": "Error búsqueda", "url": "", "body": str(e)[:200]}]


def format_results(results: List[Dict]) -> str:
    if not results:
        return "Sin resultados."
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Sin título")
        body = r.get("body", "")[:200]
        url = r.get("url", r.get("href", ""))
        lines.append(f"{i}. **{title}**\n   {body}")
        if url:
            lines.append(f"   {url}")
    return "\n".join(lines)
