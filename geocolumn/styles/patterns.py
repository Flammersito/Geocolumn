"""Catálogo de patrones litológicos.

Las claves de este catálogo son los números oficiales de patrón del
estándar FGDC "Digital Cartographic Standard for Geologic Map
Symbolization" (FGDC-STD-013-2006), específicamente de las series 600
(litologías sedimentarias) y 700 (metamórficas, ígneas y de veta) —
ambas series están explícitamente reservadas por el estándar para uso
en columnas estratigráficas.

Implementación actual (v1): cada patrón se aproxima con las texturas
('hatch') integradas de matplotlib — un vocabulario limitado (~10
texturas combinables), consistente en pantalla sin importar el
espesor de la unidad, pero NO los símbolos vectoriales oficiales del
estándar. Es una base reemplazable: cuando se implementen los
patrones vectoriales reales (ver PDF de referencia FGDC del
proyecto), solo cambia el valor `hatch` de cada entrada, nunca las
claves ni la API del renderizador.
"""

PATTERN_CATALOG: dict[str, dict] = {
    # --- Serie 600: litologías sedimentarias ---
    "605": {"name": "Breccia (1st option)", "hatch": "o"},
    "607": {"name": "Massive sand or sandstone", "hatch": "."},
    "608": {"name": "Bedded sand or sandstone", "hatch": "-."},
    "619": {"name": "Sandy or silty shale", "hatch": "--"},
    "620": {"name": "Clay or clay shale", "hatch": "---"},
    "627": {"name": "Limestone", "hatch": "+"},
    "642": {"name": "Dolostone or dolomite", "hatch": "x"},
    # --- Serie 700: metamórficas, ígneas y de veta ---
    "702": {"name": "Quartzite", "hatch": ".."},
    "711": {"name": "Tuffaceous rock", "hatch": ",."},
    "715": {"name": "Volcanic breccia or agglomerate", "hatch": "O"},
    "721": {"name": "Igneous rock (1st option)", "hatch": "*"},
}


def resolve_pattern(code: str | None) -> dict | None:
    """Busca un código de patrón FGDC en el catálogo.

    Returns:
        Un dict con `name` y `hatch`, o `None` si `code` es `None` o
        no está catalogado (en cuyo caso el llamador debe dibujar la
        unidad sin patrón, solo con color sólido).
    """
    if not code:
        return None
    return PATTERN_CATALOG.get(str(code).strip())
