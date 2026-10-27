"""Escalas granulométricas para el ancho de las unidades en la columna.

En una columna estratigráfica sedimentaria, el ancho de cada capa
representa su granulometría (o su textura, en carbonatos): las capas
finas se dibujan angostas y las gruesas anchas, de modo que el contorno
de la columna muestra tendencias (grano-creciente, grano-decreciente).

Una `GrainScale` es una lista ordenada de niveles, de fino a grueso.
Cada nivel ocupa un escalón del eje horizontal: el nivel i de n termina
en x = (i + 1) / n. Las búsquedas ignoran mayúsculas, acentos y
espacios/guiones bajos.

Escalas incluidas:
    - "siliciclastic": clásticos siliciclásticos, basada en la escala de
      tamaño de grano de Udden-Wentworth (arcilla a canto).
    - "carbonate": texturas de rocas carbonatadas según Dunham (1962),
      con las categorías de Embry y Klovan (1971) para gruesos
      (floatstone, rudstone), de mudstone a boundstone.

Son escalas separadas a propósito: no existe una equivalencia
universal entre, por ejemplo, un wackestone y un tamaño de arena, así
que no las mezclamos en un solo eje. Se pueden definir escalas propias
creando una `GrainScale`.
"""

from dataclasses import dataclass
from typing import Optional

from geocolumn.styles._text import normalize_name


@dataclass(frozen=True)
class GrainLevel:
    """Un escalón de una escala granulométrica."""

    key: str                       # identificador canónico (ej. "arena_media")
    label: str                     # texto del eje (ej. "Arena media")
    aliases: tuple[str, ...] = ()  # sinónimos (ej. nombres en inglés)


class GrainScale:
    """Escala ordenada de niveles, de fino a grueso."""

    def __init__(self, name: str, title: str, levels: list[GrainLevel]) -> None:
        if not levels:
            raise ValueError("Una escala granulométrica necesita al menos un nivel.")
        self.name = name
        self.title = title            # título del eje en la figura
        self.levels = tuple(levels)
        self._index: dict[str, int] = {}
        for i, level in enumerate(self.levels):
            for alias in (level.key, level.label, *level.aliases):
                self._index[normalize_name(alias)] = i

    def level_index(self, name: Optional[str]) -> Optional[int]:
        """Posición (0 = más fino) de un nivel, o `None` si no se reconoce."""
        if not name:
            return None
        return self._index.get(normalize_name(name))

    def width_for(self, name: Optional[str]) -> Optional[float]:
        """Ancho relativo (0 a 1) de una unidad con esa granulometría.

        El nivel más fino mide 1/n y el más grueso mide 1.
        """
        index = self.level_index(name)
        if index is None:
            return None
        return (index + 1) / len(self.levels)

    def tick_positions(self) -> list[float]:
        """Posición x del borde derecho de cada nivel."""
        n = len(self.levels)
        return [(i + 1) / n for i in range(n)]

    def tick_labels(self) -> list[str]:
        return [level.label for level in self.levels]


_G = GrainLevel

SILICICLASTIC_SCALE = GrainScale(
    name="siliciclastic",
    title="Granulometría",
    levels=[
        _G("arcilla", "Arcilla", ("clay", "lodo")),
        _G("limo", "Limo", ("silt",)),
        _G("arena_muy_fina", "Arena muy fina", ("very_fine_sand", "arena_mf")),
        _G("arena_fina", "Arena fina", ("fine_sand", "arena_f")),
        _G("arena_media", "Arena media", ("medium_sand", "arena_m")),
        _G("arena_gruesa", "Arena gruesa", ("coarse_sand", "arena_g")),
        _G("arena_muy_gruesa", "Arena muy gruesa", ("very_coarse_sand", "arena_mg")),
        _G("granulo", "Gránulo", ("granule", "granulos")),
        _G("guijarro", "Guijarro", ("pebble", "guijarros")),
        _G("canto", "Canto", ("cobble", "cantos", "bloque", "boulder")),
    ],
)

CARBONATE_SCALE = GrainScale(
    name="carbonate",
    title="Textura (Dunham)",
    levels=[
        _G("mudstone", "Mudstone", ("lodolita_carbonatada",)),
        _G("wackestone", "Wackestone"),
        _G("packstone", "Packstone"),
        _G("grainstone", "Grainstone"),
        _G("floatstone", "Floatstone"),
        _G("rudstone", "Rudstone"),
        _G("boundstone", "Boundstone"),
    ],
)

GRAIN_SCALES: dict[str, GrainScale] = {
    SILICICLASTIC_SCALE.name: SILICICLASTIC_SCALE,
    CARBONATE_SCALE.name: CARBONATE_SCALE,
}


def resolve_grain_scale(scale: "str | GrainScale | None") -> Optional[GrainScale]:
    """Convierte un nombre ("siliciclastic", "carbonate") o una escala en `GrainScale`.

    Raises:
        ValueError: Si el nombre no corresponde a ninguna escala incluida.
    """
    if scale is None or isinstance(scale, GrainScale):
        return scale
    try:
        return GRAIN_SCALES[normalize_name(scale)]
    except KeyError:
        valid = ", ".join(GRAIN_SCALES)
        raise ValueError(f"Escala granulométrica '{scale}' no reconocida. Opciones: {valid}")
