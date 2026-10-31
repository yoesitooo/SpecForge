"""
Browser Actions — Abre URLs, Spotify, YouTube en el navegador por defecto.
No requiere APIs ni OAuth. Todo via webbrowser estándar de Python.
"""

import webbrowser
import urllib.parse
import logging

log = logging.getLogger(__name__)


def open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    log.info(f"[BROWSER] Abriendo: {url}")
    return f"Abriendo en el navegador: {url}"


def open_spotify(query: str) -> str:
    encoded = urllib.parse.quote(query)
    url = f"https://open.spotify.com/search/{encoded}"
    webbrowser.open(url)
    log.info(f"[BROWSER] Spotify: {query}")
    return f"Buscando '{query}' en Spotify"


def open_youtube(query: str) -> str:
    encoded = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded}"
    webbrowser.open(url)
    log.info(f"[BROWSER] YouTube: {query}")
    return f"Buscando '{query}' en YouTube"


def open_google(query: str) -> str:
    encoded = urllib.parse.quote(query)
    url = f"https://www.google.com/search?q={encoded}"
    webbrowser.open(url)
    return f"Buscando '{query}' en Google"
