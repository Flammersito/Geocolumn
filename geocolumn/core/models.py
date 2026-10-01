"""Modelos de datos centrales de GeoColumn.

Este módulo define las estructuras de datos que representan una columna
estratigráfica y sus unidades, de forma completamente independiente de
cómo se leen (Excel, CSV, GIS, o directamente en código) o de cómo se
dibujan (matplotlib, etc.). No depende de pandas ni de ningún lector
concreto: `from_dict` trabaja sobre diccionarios ya "limpios" (sin NaN),
y es responsabilidad de cada lector normalizar sus datos antes de
llamarlo. Esta es la única puerta de entrada para construir una unidad
a partir de datos externos, sin importar su origen.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class ContactType(Enum):
    """Tipo de contacto en el límite superior de una unidad estratigráfica."""

    SHARP = "sharp"      # contacto neto
    GRADUAL = "gradual"  # contacto gradual
    EROSIVE = "erosive"  # contacto erosivo
    FAULT = "fault"       # falla


@dataclass
class GeologicAge:
    """Edad geológica de una unidad estratigráfica.

    Se modela como un rango (min/max en millones de años) en vez de un
    único valor, ya que rara vez se conoce la edad exacta de una unidad;
    lo habitual es conocer un rango o asignarla a un piso/época.
    """

    unit_name: Optional[str] = None   # ej. "Mioceno", "Fm. Río Blanco"
    min_age_ma: Optional[float] = None
    max_age_ma: Optional[float] = None
    period: Optional[str] = None
    epoch: Optional[str] = None


def _coerce_list(value: Any) -> list[str]:
    """Normaliza un valor a lista de strings.

    Acepta `None` (-> lista vacía), una lista ya construida en Python, o
    un string con elementos separados por `;` (la misma convención usada
    en las plantillas de Excel). Aceptar ambas formas es lo que permite
    que el mismo campo se escriba igual de fácil en una celda de Excel
    que en un diccionario escrito a mano en código.
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    return [item.strip() for item in text.split(";") if item.strip()]


def _coerce_contact(value: Any) -> ContactType:
    """Normaliza un valor a `ContactType`, con error explícito si no es válido."""
    if value is None:
        return ContactType.SHARP
    if isinstance(value, ContactType):
        return value
    text = str(value).strip().lower()
    try:
        return ContactType(text)
    except ValueError:
        valid = ", ".join(c.value for c in ContactType)
        raise ValueError(
            f"Tipo de contacto '{value}' no reconocido. Valores válidos: {valid}"
        )


def _coerce_float(value: Any) -> Optional[float]:
    """Normaliza un valor a float, o None si está vacío."""
    if value is None or value == "":
        return None
    return float(value)


@dataclass
class StratigraphicUnit:
    """Una unidad individual dentro de una columna estratigráfica.

    La geometría vertical se maneja mediante `top_depth` y `base_depth`
    (profundidades desde la superficie o desde el punto de referencia del
    sondaje/perfil). El espesor (`thickness`) es un campo de respaldo
    para los casos en que no se dispone de profundidades, pero siempre
    que existan `top_depth` y `base_depth`, estas son la fuente de verdad
    y `computed_thickness` las usa para calcular el espesor real.
    """

    # --- Identificación y geometría ---
    unit_id: str
    top_depth: Optional[float] = None
    base_depth: Optional[float] = None
    thickness: Optional[float] = None

    # --- Litología y apariencia ---
    lithology: str = "unknown"
    color: Optional[str] = None
    pattern: Optional[str] = None
    grain_size: Optional[str] = None

    # --- Estructuras y contenido fósil (listas simples de nombres, v1) ---
    sedimentary_structures: list[str] = field(default_factory=list)
    fossils: list[str] = field(default_factory=list)
    samples: list[str] = field(default_factory=list)

    # --- Geología económica / alteración ---
    # Se modelan como listas porque en la práctica una unidad casi
    # siempre presenta más de un tipo de alteración o mineral de mena
    # superpuestos (ej. silicificación + argílica avanzada).
    hydrothermal_alteration: list[str] = field(default_factory=list)
    mineralization: list[str] = field(default_factory=list)

    # --- Contactos ---
    top_contact: ContactType = ContactType.SHARP

    # --- Temporalidad ---
    age: Optional[GeologicAge] = None

    # --- Extras ---
    photos: list[str] = field(default_factory=list)
    observations: Optional[str] = None

    @property
    def computed_thickness(self) -> Optional[float]:
        """Espesor de la unidad, priorizando el cálculo desde profundidades.

        Returns:
            La diferencia `base_depth - top_depth` si ambas están definidas;
            si no, el valor de `thickness` si existe; si no hay suficiente
            información, `None`.
        """
        if self.top_depth is not None and self.base_depth is not None:
            return self.base_depth - self.top_depth
        return self.thickness

    @classmethod
    def from_dict(cls, data: dict) -> "StratigraphicUnit":
        """Construye una unidad a partir de un diccionario "plano".

        Esta es la ruta de entrada compartida por todos los lectores
        (Excel, CSV en el futuro, o listas de diccionarios escritas
        directamente en código), de forma que la validación y las
        convenciones (como el separador `;` para listas) sean
        exactamente las mismas sin importar la fuente de datos.

        Claves reconocidas: unit_id, top_depth, base_depth, thickness,
        lithology, color, pattern, grain_size, sedimentary_structures,
        fossils, samples, hydrothermal_alteration, mineralization,
        top_contact, age_unit_name, age_min_ma, age_max_ma, age_period,
        age_epoch, photos, observations.

        Raises:
            ValueError: Si falta `unit_id`, o si `top_contact` no es un
                valor reconocido.
        """
        if not data.get("unit_id"):
            raise ValueError("Cada unidad requiere un 'unit_id'.")

        age = None
        age_keys = ("age_unit_name", "age_min_ma", "age_max_ma", "age_period", "age_epoch")
        if any(data.get(k) is not None for k in age_keys):
            age = GeologicAge(
                unit_name=data.get("age_unit_name"),
                min_age_ma=_coerce_float(data.get("age_min_ma")),
                max_age_ma=_coerce_float(data.get("age_max_ma")),
                period=data.get("age_period"),
                epoch=data.get("age_epoch"),
            )

        return cls(
            unit_id=str(data["unit_id"]),
            top_depth=_coerce_float(data.get("top_depth")),
            base_depth=_coerce_float(data.get("base_depth")),
            thickness=_coerce_float(data.get("thickness")),
            lithology=data.get("lithology") or "unknown",
            color=data.get("color"),
            pattern=data.get("pattern"),
            grain_size=data.get("grain_size"),
            sedimentary_structures=_coerce_list(data.get("sedimentary_structures")),
            fossils=_coerce_list(data.get("fossils")),
            samples=_coerce_list(data.get("samples")),
            hydrothermal_alteration=_coerce_list(data.get("hydrothermal_alteration")),
            mineralization=_coerce_list(data.get("mineralization")),
            top_contact=_coerce_contact(data.get("top_contact")),
            age=age,
            photos=_coerce_list(data.get("photos")),
            observations=data.get("observations"),
        )
