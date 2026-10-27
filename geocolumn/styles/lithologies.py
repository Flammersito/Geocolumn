"""Catálogo extensible de litologías.

Une el nombre de una litología con su apariencia por defecto: un color
(nombre del catálogo de colores) y un código de patrón FGDC. Así, el
usuario puede escribir solo `lithology: arenisca` en su Excel y obtener
automáticamente un color y un patrón razonables, sin tener que
especificarlos unidad por unidad.

Prioridad de apariencia en el renderizador (de mayor a menor):
    1. Lo que el usuario escribió explícitamente en la unidad
       (`color` / `pattern`).
    2. El estilo por defecto de la litología en el catálogo.
    3. Un color automático (hash del nombre) y sin patrón.

Cobertura: rocas sedimentarias, volcánicas/piroclásticas, intrusivas,
metamórficas y de veta/mena. Los colores siguen convenciones comunes en
columnas estratigráficas (caliza en azul claro, arenisca en amarillo,
carbón en negro, etc.) pero son solo valores por defecto.

El catálogo es una clase, no un diccionario global, para que cada
usuario pueda ampliarlo (`register`) sin afectar el de otros ni el del
paquete.
"""

from dataclasses import dataclass
from typing import Iterable, Iterator, Optional

from geocolumn.styles._text import normalize_name


@dataclass(frozen=True)
class LithologyStyle:
    """Apariencia por defecto de una litología.

    Attributes:
        key: Identificador canónico (ej. "arenisca"), en el formato en
            que se escribiría en el Excel.
        display_name: Nombre legible para la leyenda (ej. "Arenisca").
        color: Nombre de color del catálogo de colores, o `None`.
        pattern: Código de patrón FGDC (ej. "607"), o `None` si no hay
            un patrón oficial adecuado (por ejemplo, la brecha
            hidrotermal).
        aliases: Sinónimos que también deben reconocerse (ej. nombres
            en inglés).
    """

    key: str
    display_name: str
    color: Optional[str] = None
    pattern: Optional[str] = None
    aliases: tuple[str, ...] = ()


class LithologyCatalog:
    """Colección buscable y ampliable de `LithologyStyle`.

    Las búsquedas ignoran mayúsculas, acentos y espacios/guiones bajos:
    "Arenisca Tobácea" y "arenisca_tobacea" son la misma litología.
    """

    def __init__(self, styles: Iterable[LithologyStyle] = ()) -> None:
        self._index: dict[str, LithologyStyle] = {}
        self._styles: list[LithologyStyle] = []
        for style in styles:
            self.register(style)

    def register(self, style: LithologyStyle, overwrite: bool = False) -> None:
        """Agrega una litología (y sus alias) al catálogo.

        Raises:
            ValueError: Si el nombre o algún alias ya existe y
                `overwrite` es False. Preferimos un error explícito a
                que una litología pise a otra sin que el usuario lo note.
        """
        names = [normalize_name(style.key)] + [normalize_name(a) for a in style.aliases]
        if not overwrite:
            clashes = [n for n in names if n in self._index]
            if clashes:
                raise ValueError(
                    f"La litología '{style.key}' choca con una ya registrada: "
                    f"{', '.join(clashes)}. Usa overwrite=True para reemplazarla."
                )
        for name in names:
            self._index[name] = style
        if style not in self._styles:
            self._styles.append(style)

    def get(self, name: Optional[str]) -> Optional[LithologyStyle]:
        """Devuelve el estilo de una litología, o `None` si no está catalogada."""
        if not name:
            return None
        return self._index.get(normalize_name(name))

    def __contains__(self, name: object) -> bool:
        return isinstance(name, str) and self.get(name) is not None

    def __iter__(self) -> Iterator[LithologyStyle]:
        return iter(self._styles)

    def __len__(self) -> int:
        return len(self._styles)


_L = LithologyStyle

# Los códigos de patrón corresponden a PATTERN_CATALOG (FGDC-STD-013-2006).
# Para las rocas ígneas, el estándar ofrece varias "opciones" genéricas de
# "Igneous rock" (721-728) sin asignarlas a un tipo específico; aquí se
# reparten entre andesita, dacita y riolita solo para poder distinguirlas
# visualmente, no porque el estándar las asocie a esas rocas.
DEFAULT_LITHOLOGIES: tuple[LithologyStyle, ...] = (
    # --- Sedimentarias ---
    _L("conglomerado", "Conglomerado", "naranja", "601", ("conglomerate",)),
    _L("brecha_sedimentaria", "Brecha sedimentaria", "ocre", "605", ("sedimentary_breccia",)),
    _L("arenisca", "Arenisca", "amarillo", "607", ("sandstone",)),
    _L("arenisca_estratificada", "Arenisca estratificada", "amarillo", "608"),
    _L("arenisca_cruzada", "Arenisca con estratificación cruzada", "amarillo", "609"),
    _L("arenisca_tobacea", "Arenisca tobácea", "gris_beige", "607"),
    _L("arenisca_volcaniclastica", "Arenisca volcaniclástica", "beige", "607"),
    _L("limolita", "Limolita", "beige", "616", ("siltstone",)),
    _L("lutita", "Lutita", "verde_grisaceo", "619", ("shale",)),
    _L("arcillolita", "Arcillolita", "gris_verdoso", "620", ("claystone",)),
    _L("marga", "Marga", "verde_claro", "623", ("marl",)),
    _L("lutita_carbonosa", "Lutita carbonosa", "gris_oscuro", "624"),
    _L("caliza", "Caliza", "azul_claro", "627", ("limestone",)),
    _L("dolomia", "Dolomía", "rosa", "642", ("dolostone", "dolomita")),
    _L("chert", "Chert", "gris_claro", "649", ("pedernal",)),
    _L("carbon", "Carbón", "negro", "658", ("coal",)),
    _L("yeso", "Yeso", "blanco", "667", ("gypsum",)),
    _L("sal", "Sal", "blanco_a_gris_claro", "668", ("halita", "salt")),
    # --- Volcánicas y piroclásticas ---
    _L("toba", "Toba", "gris_beige", "711", ("tuff",)),
    _L("toba_cristalina", "Toba cristalina", "blanco_a_gris_claro", "712", ("crystal_tuff",)),
    _L("toba_y_brecha", "Toba y brecha volcánica", "gris", "714"),
    _L("brecha_volcanica", "Brecha volcánica", "gris_oscuro", "715", ("aglomerado", "agglomerate")),
    _L("basalto", "Basalto", "gris_oscuro", "717", ("basalt", "flujo_basaltico")),
    _L("andesita", "Andesita", "verde_grisaceo", "721", ("andesite",)),
    _L("andesita_lava", "Lava andesítica", "verde_grisaceo", "721", ("lava_andesitica",)),
    _L("dacita", "Dacita", "gris_claro", "722", ("dacite", "domo_dacitico")),
    _L("riolita", "Riolita", "rosa", "723", ("rhyolite",)),
    _L("vitrofiro", "Vitrófiro", "gris", "731", ("vitrophyre",)),
    # --- Intrusivas ---
    _L("granito", "Granito", "salmon", "718", ("granite",)),
    _L("porfido", "Pórfido", "rojo", "729", ("porphyry", "roca_porfidica")),
    # --- Metamórficas ---
    _L("cuarcita", "Cuarcita", "blanco", "702", ("quartzite",)),
    _L("pizarra", "Pizarra", "gris_oscuro", "703", ("slate",)),
    _L("esquisto", "Esquisto", "verde_oscuro", "705", ("schist",)),
    _L("gneis", "Gneis", "gris", "708", ("gneiss",)),
    _L("serpentinita", "Serpentinita", "verde", "710", ("serpentinite",)),
    _L("roca_metamorfica", "Roca metamórfica", "gris_verdoso", "701", ("metamorphic_rock",)),
    # --- Veta y mena ---
    _L("veta_cuarzo", "Veta de cuarzo", "blanco", "732", ("cuarzo", "quartz_vein")),
    _L("mena", "Mena", "morado", "733", ("ore",)),
    # Sin patrón FGDC adecuado: el estándar no define uno para brecha
    # hidrotermal, así que se muestra con color sólido.
    _L("brecha_hidrotermal", "Brecha hidrotermal", "naranja", None, ("hydrothermal_breccia",)),
)


def default_catalog() -> LithologyCatalog:
    """Crea un catálogo nuevo con las litologías por defecto de GeoColumn.

    Devuelve una instancia independiente cada vez, así que el llamador
    puede ampliarla con `register` sin afectar a nadie más.
    """
    return LithologyCatalog(DEFAULT_LITHOLOGIES)
