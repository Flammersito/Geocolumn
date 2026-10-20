"""Catálogo de indicadores visuales para alteración hidrotermal.

A diferencia de las litologías, el estándar FGDC no define patrones de
relleno para zonas de alteración — en la convención cartográfica
geológica, la alteración suele indicarse con símbolos de superposición
o franjas de color, no con el mismo vocabulario de patrones
litológicos. Por eso GeoColumn la representa de forma separada: una
franja de color angosta al margen de cada unidad (ver
`rendering.column_renderer`), no un patrón de relleno.

Este catálogo es intencionalmente pequeño y empieza con los tipos de
alteración más comunes en sistemas epitermales/pórfido. Se amplía
agregando entradas aquí conforme se necesiten.
"""

from geocolumn.styles._text import normalize_name

ALTERATION_CATALOG: dict[str, str] = {
    "propilitica": "#6fae6f",
    "propilitica_debil": "#a9cfa9",
    "argilica": "#d9a441",
    "argilica_moderada": "#e0b868",
    "argilica_avanzada": "#c97a1f",
    "silicificacion": "#c2c2c2",
    "silicificacion_intensa": "#8c8c8c",
    "potasica": "#b84c4c",
    "filica": "#8c7ab8",
    "sericitica": "#8c7ab8",
}


def resolve_alteration_color(name: str | None) -> str | None:
    """Busca un nombre de alteración en el catálogo.

    Returns:
        El color indicador correspondiente, o `None` si `name` es
        `None`/vacío o no está catalogado.
    """
    if not name:
        return None
    return ALTERATION_CATALOG.get(normalize_name(name))
