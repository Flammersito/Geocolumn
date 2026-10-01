"""Catálogo de colores para litologías.

El campo `StratigraphicUnit.color` es texto libre descriptivo (lo que
un geólogo anotaría en campo, ej. "gris verdoso"), pensado para ser
legible por humanos, no necesariamente un color válido de matplotlib.
Este catálogo traduce nombres comunes en español a colores concretos,
para que el usuario tenga control real sobre la apariencia sin tener
que escribir códigos hexadecimales.

Es intencionalmente pequeño por ahora: se amplía agregando entradas
aquí conforme se necesiten, no es necesario cubrir todos los colores
posibles de una vez.
"""

import unicodedata

COLOR_CATALOG: dict[str, str] = {
    "gris": "#808080",
    "gris_claro": "#bfbfbf",
    "gris_oscuro": "#4d4d4d",
    "gris_verdoso": "#8c9c8c",
    "gris_beige": "#b8ad93",
    "verde": "#2e8b57",
    "verde_oscuro": "#1f4d2e",
    "verde_grisaceo": "#7a8c7a",
    "beige": "#e8dcc0",
    "blanco": "#f5f5f5",
    "blanco_a_gris_claro": "#eaeaea",
    "negro": "#1a1a1a",
    "amarillo": "#f0c93f",
    "rojo": "#b33c3c",
    "cafe": "#8b5e3c",
    "morado": "#7a5a8c",
    "rosa": "#f28c8c",
}


def _normalize(text: str) -> str:
    """Normaliza un nombre de color para buscarlo en el catálogo.

    Pasa a minúsculas, quita acentos y convierte espacios a guiones
    bajos, para que "Gris Verdoso" y "gris_verdoso" sean equivalentes.
    """
    text = text.strip().lower().replace(" ", "_")
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def resolve_color(name: str | None) -> str | None:
    """Busca un nombre de color en el catálogo.

    Returns:
        El color de matplotlib correspondiente, o `None` si `name` es
        `None` o no está catalogado (en cuyo caso el llamador debe
        decidir un color de respaldo).
    """
    if not name:
        return None
    return COLOR_CATALOG.get(_normalize(name))
