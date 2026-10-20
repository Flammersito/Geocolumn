"""Catálogo de patrones litológicos.

Las claves de este catálogo son los números oficiales de patrón del
estándar FGDC "Digital Cartographic Standard for Geologic Map
Symbolization" (FGDC-STD-013-2006), específicamente de las series 600
(litologías sedimentarias) y 700 (metamórficas, ígneas y de veta) —
ambas series están explícitamente reservadas por el estándar para uso
en columnas estratigráficas. Los números y nombres en inglés fueron
verificados contra el PDF oficial (ver docs/reference/README.md).

Implementación actual (v1, "Opción A"): cada patrón se aproxima con las
texturas ('hatch') integradas de matplotlib — un vocabulario limitado
(~10 caracteres combinables), consistente en pantalla sin importar el
espesor de la unidad, pero NO los símbolos vectoriales oficiales del
estándar. Por esa limitación, algunos patrones distintos se ven
parecidos; el color de la litología ayuda a distinguirlos. Es una base
reemplazable: cuando se implementen los patrones vectoriales reales
("Opción B"), solo cambia el valor `hatch` de cada entrada, nunca las
claves ni la API del renderizador. Un `hatch` de `None` significa
relleno sólido (sin textura), como el carbón.
"""

PATTERN_CATALOG: dict[str, dict] = {
    # --- Serie 600: litologías sedimentarias ---
    "601": {"name": "Gravel or conglomerate (1st option)", "hatch": "oO"},
    "605": {"name": "Breccia (1st option)", "hatch": "o"},
    "607": {"name": "Massive sand or sandstone", "hatch": "."},
    "608": {"name": "Bedded sand or sandstone", "hatch": "-."},
    "609": {"name": "Crossbedded sand or sandstone (1st option)", "hatch": "./"},
    "616": {"name": "Silt, siltstone, or shaly silt", "hatch": "|."},
    "619": {"name": "Sandy or silty shale", "hatch": "--"},
    "620": {"name": "Clay or clay shale", "hatch": "---"},
    "623": {"name": "Calcareous shale or marl", "hatch": "-+"},
    "624": {"name": "Carbonaceous shale", "hatch": "--x"},
    "627": {"name": "Limestone", "hatch": "+"},
    "642": {"name": "Dolostone or dolomite", "hatch": "x"},
    "649": {"name": "Bedded chert (1st option)", "hatch": "xx"},
    "658": {"name": "Coal", "hatch": None},
    "667": {"name": "Gypsum", "hatch": "+x"},
    "668": {"name": "Salt", "hatch": "++"},
    # --- Serie 700: metamórficas, ígneas y de veta ---
    "701": {"name": "Metamorphism", "hatch": "//"},
    "702": {"name": "Quartzite", "hatch": ".."},
    "703": {"name": "Slate", "hatch": "\\\\"},
    "705": {"name": "Schist", "hatch": "/\\"},
    "708": {"name": "Gneiss", "hatch": "//\\\\"},
    "710": {"name": "Soapstone, talc, or serpentinite", "hatch": "\\."},
    "711": {"name": "Tuffaceous rock", "hatch": "*."},
    "712": {"name": "Crystal tuff", "hatch": "x."},
    "714": {"name": "Volcanic breccia and tuff", "hatch": "O."},
    "715": {"name": "Volcanic breccia or agglomerate", "hatch": "O"},
    "717": {"name": "Basaltic flows", "hatch": "||"},
    "718": {"name": "Granite (1st option)", "hatch": "x*"},
    "721": {"name": "Igneous rock (1st option)", "hatch": "*"},
    "722": {"name": "Igneous rock (2nd option)", "hatch": "**"},
    "723": {"name": "Igneous rock (3rd option)", "hatch": "*-"},
    "729": {"name": "Porphyritic rock (1st option)", "hatch": "O*"},
    "731": {"name": "Vitrophyre", "hatch": "\\|"},
    "732": {"name": "Quartz", "hatch": "x-"},
    "733": {"name": "Ore", "hatch": "+O"},
}


def resolve_pattern(code: str | None) -> dict | None:
    """Busca un código de patrón FGDC en el catálogo.

    Returns:
        Un dict con `name` y `hatch`, o `None` si `code` es `None` o
        no está catalogado (en cuyo caso el llamador decide qué hacer:
        usar un patrón por defecto, avisar al usuario, etc.).
    """
    if not code:
        return None
    return PATTERN_CATALOG.get(str(code).strip())
