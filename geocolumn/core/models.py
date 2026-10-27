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

    SHARP = "sharp"        # contacto neto
    GRADUAL = "gradual"    # contacto gradual
    EROSIVE = "erosive"    # contacto erosivo
    FAULT = "fault"        # falla
    INFERRED = "inferred"  # contacto inferido (no observado en campo)


# Nombres en español que también se aceptan en el Excel.
_CONTACT_ALIASES = {
    "neto": ContactType.SHARP,
    "gradacional": ContactType.GRADUAL,
    "erosivo": ContactType.EROSIVE,
    "erosional": ContactType.EROSIVE,
    "falla": ContactType.FAULT,
    "inferido": ContactType.INFERRED,
}

# Tipos de elemento que puede representar una fila: una unidad de roca
# (se apila en la columna) o una veta (se dibuja aparte, en su posición).
VALID_KINDS = ("unit", "vein")
_KIND_ALIASES = {"unidad": "unit", "veta": "vein"}


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
    if text in _CONTACT_ALIASES:
        return _CONTACT_ALIASES[text]
    try:
        return ContactType(text)
    except ValueError:
        valid = ", ".join(c.value for c in ContactType)
        spanish = ", ".join(_CONTACT_ALIASES)
        raise ValueError(
            f"Tipo de contacto '{value}' no reconocido. Valores válidos: {valid} "
            f"(o en español: {spanish})"
        )


def _coerce_kind(value: Any) -> str:
    """Normaliza el tipo de elemento de una fila ("unit" o "vein")."""
    if value is None or str(value).strip() == "":
        return "unit"
    text = str(value).strip().lower()
    text = _KIND_ALIASES.get(text, text)
    if text not in VALID_KINDS:
        raise ValueError(
            f"kind '{value}' no reconocido. Opciones: unit (unidad), vein (veta)"
        )
    return text


def _coerce_float(value: Any) -> Optional[float]:
    """Normaliza un valor a float, o None si está vacío."""
    if value is None or value == "":
        return None
    return float(value)


@dataclass
class StratigraphicUnit:
    """Una unidad individual dentro de una columna estratigráfica.

    La geometría vertical se puede dar de tres formas (ver
    `StratigraphicColumn.resolve_positions`):

    - Profundidades (`top_depth`, `base_depth`), medidas hacia abajo desde
      un punto de referencia: lo habitual en sondajes.
    - Alturas (`base_height`, `top_height`), medidas hacia arriba desde la
      base de la columna: lo habitual en columnas de afloramiento.
    - Solo espesor (`thickness`), cuando no hay posiciones explícitas.

    Siempre que existan ambas posiciones de un mismo tipo, estas son la
    fuente de verdad y `computed_thickness` las usa para calcular el
    espesor real.
    """

    # --- Identificación y geometría ---
    unit_id: str
    top_depth: Optional[float] = None
    base_depth: Optional[float] = None
    thickness: Optional[float] = None
    top_height: Optional[float] = None    # altura del techo sobre la base de la columna
    base_height: Optional[float] = None   # altura de la base sobre la base de la columna

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

    # --- Tipo de elemento ---
    # "unit": unidad de roca que se apila en la columna. "vein": veta, que
    # se dibuja en una pista aparte y necesita una posición explícita.
    kind: str = "unit"

    @property
    def computed_thickness(self) -> Optional[float]:
        """Espesor de la unidad, priorizando el cálculo desde profundidades.

        Returns:
            La diferencia `base_depth - top_depth` si ambas están definidas;
            si no, `top_height - base_height` si ambas están definidas; si
            no, el valor de `thickness` si existe; si no hay suficiente
            información, `None`.
        """
        if self.top_depth is not None and self.base_depth is not None:
            return self.base_depth - self.top_depth
        if self.top_height is not None and self.base_height is not None:
            return self.top_height - self.base_height
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
        top_height, base_height, lithology, color, pattern, grain_size, sedimentary_structures,
        fossils, samples, hydrothermal_alteration, mineralization,
        top_contact, age_unit_name, age_min_ma, age_max_ma, age_period,
        age_epoch, photos, observations, kind.

        Raises:
            ValueError: Si falta `unit_id`, o si `top_contact` o `kind` no
                son valores reconocidos.
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
            top_height=_coerce_float(data.get("top_height")),
            base_height=_coerce_float(data.get("base_height")),
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
            kind=_coerce_kind(data.get("kind")),
        )
