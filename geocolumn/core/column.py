"""Contenedor de una secuencia completa de unidades estratigráficas.

Deliberadamente NO depende de ningún lector de I/O (Excel, CSV, etc.):
solo conoce `StratigraphicUnit`. Los lectores concretos viven en
`geocolumn.io` y construyen un `StratigraphicColumn` a partir de sus
propias fuentes, pero esta clase nunca importa hacia afuera de `core`.
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional

from geocolumn.core.models import StratigraphicUnit

VALID_AXES = ("height", "depth")


@dataclass
class StratigraphicColumn:
    """Una columna estratigráfica completa: una secuencia ordenada de unidades.

    El orden de la lista es el orden en que se ingresaron las unidades;
    solo importa cuando las posiciones se deducen del espesor (la primera
    unidad queda en el origen y las demás se apilan a continuación).

    Hay dos formas de medir la posición vertical (`axis`):

    - `"height"`: altura desde la base de la columna, creciendo hacia
      arriba, con lo más joven arriba. Es la forma de las columnas de
      afloramiento. Se usa `base_height`/`top_height`, o `thickness`
      apilado desde la base (la primera unidad es la más baja).
    - `"depth"`: profundidad desde un punto de referencia, creciendo hacia
      abajo (sondajes). Se usa `top_depth`/`base_depth`, o `thickness`
      apilado hacia abajo (la primera unidad es la más somera).

    Si `axis` es `None`, se deduce de los datos: profundidades dan
    `"depth"`; alturas o solo espesores dan `"height"`.

    Las vetas (`veins`) son filas con `kind="vein"`. No se apilan con las
    unidades: cada una necesita su propia posición (ver
    `resolve_vein_positions`) y se dibuja en una pista aparte.
    """

    units: list[StratigraphicUnit] = field(default_factory=list)
    name: Optional[str] = None  # nombre opcional (ej. "Sondaje DDH-01")
    axis: Optional[str] = None  # "height", "depth" o None (se deduce)
    veins: list[StratigraphicUnit] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.axis is not None:
            axis = str(self.axis).strip().lower()
            if axis not in VALID_AXES:
                raise ValueError(
                    f"axis '{self.axis}' no reconocido. Opciones: {', '.join(VALID_AXES)}"
                )
            self.axis = axis

    @classmethod
    def from_units(
        cls,
        items: list[StratigraphicUnit],
        name: Optional[str] = None,
        axis: Optional[str] = None,
    ) -> "StratigraphicColumn":
        """Construye una columna separando unidades de roca y vetas según su `kind`."""
        return cls(
            units=[item for item in items if item.kind == "unit"],
            name=name,
            axis=axis,
            veins=[item for item in items if item.kind == "vein"],
        )

    @classmethod
    def from_dicts(
        cls, data: list[dict], name: Optional[str] = None, axis: Optional[str] = None
    ) -> "StratigraphicColumn":
        """Construye una columna a partir de una lista de diccionarios.

        Es la vía recomendada para ingresar datos directamente en código,
        sin archivo Excel, usando exactamente las mismas reglas de
        parseo y validación que el lector de Excel (separador `;` para
        listas, mismos nombres de tipo de contacto, etc.), porque ambas
        rutas pasan por `StratigraphicUnit.from_dict`.

        Ejemplo:
            >>> column = StratigraphicColumn.from_dicts([
            ...     {"unit_id": "A1", "top_depth": 0, "base_depth": 15,
            ...      "lithology": "andesita", "top_contact": "sharp"},
            ...     {"unit_id": "A2", "top_depth": 15, "base_depth": 28,
            ...      "lithology": "brecha_volcanica"},
            ... ])
        """
        return cls.from_units(
            [StratigraphicUnit.from_dict(d) for d in data], name=name, axis=axis
        )

    def resolve_depths(self) -> list[tuple[float, float]]:
        """Calcula el rango (top, base) en profundidad para cada unidad.

        Si una unidad ya trae `top_depth` y `base_depth`, se usan tal
        cual. Si falta alguna, se infiere asumiendo continuidad: el
        `top` se toma como la `base` de la unidad anterior (o 0.0 para
        la primera unidad), y el `base` se calcula sumando `thickness`.

        Esta es la primera validación de continuidad entre unidades que
        agregamos al proyecto — la dejamos simple a propósito: no
        verifica traslapes ni huecos explícitos, solo resuelve lo
        mínimo necesario para poder dibujar la columna.

        Returns:
            Lista de tuplas `(top, base)`, en el mismo orden que `units`.

        Raises:
            ValueError: Si una unidad no tiene suficiente información
                (ni profundidades ni `thickness`) para ubicarla, o si su
                `base_depth` es menor que su `top_depth`.
        """
        depths: list[tuple[float, float]] = []
        running_depth = 0.0

        for unit in self.units:
            if unit.top_depth is not None and unit.base_depth is not None:
                top, base = unit.top_depth, unit.base_depth
            elif unit.thickness is not None:
                top = unit.top_depth if unit.top_depth is not None else running_depth
                base = top + unit.thickness
            else:
                raise ValueError(
                    f"La unidad '{unit.unit_id}' no tiene suficiente información de "
                    "profundidad (ni top_depth/base_depth ni thickness)."
                )
            if base < top:
                raise ValueError(
                    f"La unidad '{unit.unit_id}': base_depth ({base}) es menor que "
                    f"top_depth ({top}). ¿Están invertidas?"
                )
            depths.append((top, base))
            running_depth = base

        return depths

    def resolved_axis(self) -> str:
        """Devuelve `"height"` o `"depth"`, deduciéndolo de los datos si hace falta.

        Raises:
            ValueError: Si `axis` es `None` y los datos mezclan profundidades
                con alturas.
        """
        if self.axis is not None:
            return self.axis
        everything = [*self.units, *self.veins]
        has_depth = any(u.top_depth is not None or u.base_depth is not None for u in everything)
        has_height = any(u.top_height is not None or u.base_height is not None for u in everything)
        if has_depth and has_height:
            raise ValueError(
                "La columna mezcla profundidades (top_depth/base_depth) con alturas "
                "(top_height/base_height). Usa un solo tipo, o indica axis='depth' o "
                "axis='height' si quieres forzarlo."
            )
        return "depth" if has_depth else "height"

    def resolve_positions(self) -> list[tuple[float, float]]:
        """Calcula `(inicio, fin)` de cada unidad sobre el eje vertical.

        Con eje `"depth"` devuelve `(top, base)` en profundidad. Con eje
        `"height"` devuelve `(base, top)` en altura sobre la base de la
        columna. En ambos casos `inicio <= fin`, y `fin - inicio` es el
        espesor de la unidad.

        Raises:
            ValueError: Si una unidad usa el tipo de posición equivocado
                para el eje de la columna, no tiene información suficiente,
                o tiene sus extremos invertidos.
        """
        axis = self.resolved_axis()
        if axis == "depth":
            for unit in self.units:
                if unit.top_height is not None or unit.base_height is not None:
                    raise ValueError(
                        f"La unidad '{unit.unit_id}' trae top_height/base_height, pero la "
                        "columna está en modo 'depth'. Usa top_depth/base_depth o crea la "
                        "columna con axis='height'."
                    )
            return self.resolve_depths()
        return self._resolve_heights()

    def resolve_vein_positions(self) -> list[tuple[float, float]]:
        """Calcula `(inicio, fin)` de cada veta sobre el eje vertical.

        A diferencia de las unidades, las vetas no se apilan: cada una debe
        decir dónde está. En modo `"height"` necesita `base_height` y
        (`top_height` o `thickness`); en modo `"depth"` necesita
        `top_depth` y (`base_depth` o `thickness`). El espesor va en metros
        (15 cm = 0.15).

        Raises:
            ValueError: Si a una veta le falta su posición o su espesor, usa
                el tipo de posición equivocado para el eje, o tiene los
                extremos invertidos.
        """
        axis = self.resolved_axis()
        if axis == "height":
            start_name, end_name = "base_height", "top_height"
            foreign = ("top_depth", "base_depth")
        else:
            start_name, end_name = "top_depth", "base_depth"
            foreign = ("top_height", "base_height")

        positions: list[tuple[float, float]] = []
        for vein in self.veins:
            if any(getattr(vein, name) is not None for name in foreign):
                raise ValueError(
                    f"La veta '{vein.unit_id}' usa {foreign[0]}/{foreign[1]}, pero la "
                    f"columna está en modo '{axis}'. Usa {start_name}/{end_name}."
                )
            start = getattr(vein, start_name)
            end = getattr(vein, end_name)
            if start is None:
                raise ValueError(
                    f"La veta '{vein.unit_id}' necesita {start_name} (su posición en la columna)."
                )
            if end is None:
                if vein.thickness is None:
                    raise ValueError(
                        f"La veta '{vein.unit_id}' necesita {end_name} o thickness (su espesor)."
                    )
                end = start + vein.thickness
            if end < start:
                raise ValueError(
                    f"La veta '{vein.unit_id}': {end_name} ({end}) es menor que "
                    f"{start_name} ({start}). ¿Están invertidas?"
                )
            positions.append((start, end))
        return positions

    def _resolve_heights(self) -> list[tuple[float, float]]:
        """Posiciones `(base, top)` en altura. Ver `resolve_positions`."""
        positions: list[tuple[float, float]] = []
        running_height = 0.0

        for unit in self.units:
            if unit.top_depth is not None or unit.base_depth is not None:
                raise ValueError(
                    f"La unidad '{unit.unit_id}' trae top_depth/base_depth, pero la "
                    "columna está en modo 'height'. Usa base_height/top_height (o "
                    "thickness) o crea la columna con axis='depth'."
                )
            if unit.base_height is not None and unit.top_height is not None:
                base, top = unit.base_height, unit.top_height
            elif unit.thickness is not None:
                base = unit.base_height if unit.base_height is not None else running_height
                top = base + unit.thickness
            else:
                raise ValueError(
                    f"La unidad '{unit.unit_id}' no tiene suficiente información de altura "
                    "(ni base_height/top_height ni thickness)."
                )
            if top < base:
                raise ValueError(
                    f"La unidad '{unit.unit_id}': top_height ({top}) es menor que "
                    f"base_height ({base}). ¿Están invertidas?"
                )
            positions.append((base, top))
            running_height = top

        return positions

    def __len__(self) -> int:
        return len(self.units)

    def __iter__(self) -> Iterator[StratigraphicUnit]:
        return iter(self.units)

    def __getitem__(self, index):
        return self.units[index]
