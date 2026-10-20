"""Utilidades de texto compartidas por los catálogos de estilo."""

import unicodedata


def normalize_name(text: str) -> str:
    """Normaliza un nombre para buscarlo en un catálogo.

    Pasa a minúsculas, quita acentos y convierte espacios a guiones
    bajos, para que "Gris Verdoso", "gris verdoso" y "gris_verdoso"
    sean equivalentes.
    """
    text = text.strip().lower().replace(" ", "_")
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))
