"""Contenedor de una secuencia completa de unidades estratigráficas.

Deliberadamente NO depende de ningún lector de I/O (Excel, CSV, etc.):
solo conoce `StratigraphicUnit`. Los lectores concretos viven en
`geocolumn.io` y construyen un `StratigraphicColumn` a partir de sus
propias fuentes, pero esta clase nunca importa hacia afuera de `core`.
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional

from geocolumn.core.models import StratigraphicUnit


@dataclass
class StratigraphicColumn:
    """Una columna estratigráfica completa: una secuencia ordenada de unidades.

    El orden de la lista define el orden de la columna tal como fue
    ingresada (por ejemplo, de techo a base en un log de sondaje). Esta
    clase todavía no impone validaciones de continuidad entre
    profundidades (ej. que `base_depth` de una unidad coincida con
    `top_depth` de la siguiente) — esa validación se añadirá cuando el
    renderizador la necesite, para no adelantarnos a una regla que
    todavía no hemos probado contra datos reales.
    """

    units: list[StratigraphicUnit] = field(default_factory=list)
    name: Optional[str] = None  # nombre opcional (ej. "Sondaje DDH-01")

    @classmethod
    def from_dicts(cls, data: list[dict], name: Optional[str] = None) -> "StratigraphicColumn":
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
        units = [StratigraphicUnit.from_dict(d) for d in data]
        return cls(units=units, name=name)

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
                (ni profundidades ni `thickness`) para ubicarla.
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
            depths.append((top, base))
            running_depth = base

        return depths

    def __len__(self) -> int:
        return len(self.units)

    def __iter__(self) -> Iterator[StratigraphicUnit]:
        return iter(self.units)

    def __getitem__(self, index):
        return self.units[index]
