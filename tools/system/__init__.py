"""system/ — Control del PC, navegador y portapapeles."""
from tools.pc_control      import open_app, press_keys, type_text, get_clipboard
from tools.browser_actions import open_url, open_spotify, open_youtube, open_google

__all__ = [
    "open_app", "press_keys", "type_text", "get_clipboard",
    "open_url", "open_spotify", "open_youtube", "open_google",
]
