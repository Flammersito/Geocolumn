"""Renderizado básico de columnas estratigráficas con matplotlib.

Primera etapa del motor de renderizado: dibuja cada unidad como un
rectángulo coloreado según su litología, con un patrón FGDC
aproximado (via hatch) y, si aplica, una franja indicadora de
alteración hidrotermal al margen. Todavía no incluye símbolos,
fósiles, ni los patrones vectoriales oficiales (ver docs/reference/
para cuando se implemente esa etapa).
"""

import hashlib
import warnings

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from geocolumn.core.column import StratigraphicColumn
from geocolumn.styles.alteration import resolve_alteration_color
from geocolumn.styles.colors import resolve_color
from geocolumn.styles.lithologies import LithologyCatalog, LithologyStyle, default_catalog
from geocolumn.styles.patterns import resolve_pattern

# Paleta cualitativa de 20 colores, estable entre ejecuciones. Se usa
# como respaldo cuando una unidad no tiene color catalogado.
_PALETTE = plt.get_cmap("tab20").colors

# Ancho de la franja de alteración, en las mismas unidades que el
# cuerpo de la columna (que ocupa x en [0, 1]).
_ALTERATION_STRIP_WIDTH = 0.15
_ALTERATION_STRIP_GAP = 0.03


def _hash_color_for_lithology(lithology: str) -> tuple:
    """Asigna un color determinista a una litología, como respaldo.

    Se usa cuando `unit.color` no está definido o no coincide con
    ningún nombre del catálogo (`geocolumn.styles.colors`). Dos
    litologías con nombres distintos reciben, con alta probabilidad,
    colores distintos y consistentes entre figuras — pero el color no
    tiene significado geológico convencional, a diferencia de uno
    tomado del catálogo.
    """
    digest = hashlib.sha256(lithology.encode("utf-8")).hexdigest()
    index = int(digest, 16) % len(_PALETTE)
    return _PALETTE[index]


def _resolve_unit_color(unit, style: LithologyStyle | None) -> str | tuple:
    """Determina el color final a usar para una unidad.

    Prioridad: 1) `unit.color` si está en el catálogo de colores,
    2) el color por defecto de la litología, 3) un color determinista
    por hash del nombre de la litología.
    """
    explicit = resolve_color(unit.color)
    if explicit is not None:
        return explicit
    if style is not None:
        default = resolve_color(style.color)
        if default is not None:
            return default
    return _hash_color_for_lithology(unit.lithology)


def _resolve_unit_hatch(unit, style: LithologyStyle | None) -> str | None:
    """Determina el `hatch` (textura) a usar para una unidad.

    Prioridad: 1) `unit.pattern` si es un código FGDC catalogado,
    2) el patrón por defecto de la litología, 3) sin patrón.

    Si `unit.pattern` tiene un valor que no está en el catálogo (por
    ejemplo, un error de dedo), se emite una advertencia en vez de
    ignorarlo en silencio, y se recurre al patrón de la litología.
    """
    if unit.pattern:
        explicit = resolve_pattern(unit.pattern)
        if explicit is not None:
            return explicit["hatch"]
        warnings.warn(
            f"Unidad '{unit.unit_id}': el patrón '{unit.pattern}' no está en el "
            "catálogo de patrones FGDC; se usará el patrón por defecto de la litología.",
            stacklevel=3,
        )
    if style is not None and style.pattern:
        default = resolve_pattern(style.pattern)
        if default is not None:
            return default["hatch"]
    return None


def render_column(
    column: StratigraphicColumn,
    figsize: tuple[float, float] = (6, 10),
    catalog: LithologyCatalog | None = None,
) -> tuple[Figure, tuple[Axes, Axes]]:
    """Dibuja una columna estratigráfica como rectángulos de litología.

    Cada unidad se dibuja como un rectángulo cuya altura es su espesor
    (resuelto mediante `column.resolve_depths()`), coloreado según
    `unit.color` (si está en el catálogo) con el patrón FGDC de
    `unit.pattern` (si está catalogado). Si la unidad tiene alteración
    hidrotermal catalogada, se dibuja además una franja angosta a su
    izquierda con el color indicador correspondiente (se usa solo la
    primera alteración de la lista, por simplicidad).

    El eje Y representa profundidad, con el punto más somero arriba y
    aumentando hacia abajo, como es convención en geología. La columna
    no lleva etiquetas de texto junto a cada rectángulo; en vez de
    eso, se dibuja una leyenda aparte con una entrada por cada
    litología y por cada tipo de alteración presentes.

    Args:
        column: La columna a dibujar. Debe tener suficiente información
            de profundidad o espesor en cada unidad (ver
            `StratigraphicColumn.resolve_depths`).
        figsize: Tamaño de la figura en pulgadas.
        catalog: Catálogo de litologías con los colores y patrones por
            defecto. Si es `None`, se usa el catálogo por defecto de
            GeoColumn (`default_catalog()`). Pasa uno propio, ampliado
            con `register`, para incluir litologías adicionales.

    Returns:
        Una tupla `(figura, (eje_columna, eje_leyenda))` de matplotlib,
        para que el llamador pueda seguir modificando la figura o
        exportarla.
    """
    depths = column.resolve_depths()
    catalog = catalog if catalog is not None else default_catalog()

    fig, (column_ax, legend_ax) = plt.subplots(
        ncols=2, figsize=figsize, gridspec_kw={"width_ratios": [1, 1.3]}
    )

    lithology_entries: dict[str, tuple] = {}   # nombre en leyenda -> (color, hatch)
    alteration_entries: dict[str, str] = {}    # nombre de alteración -> color

    for unit, (top, base) in zip(column, depths):
        height = base - top
        style = catalog.get(unit.lithology)
        color = _resolve_unit_color(unit, style)
        hatch = _resolve_unit_hatch(unit, style)
        label = style.display_name if style else unit.lithology

        rect = patches.Rectangle(
            (0, top), width=1, height=height,
            facecolor=color, edgecolor="black", linewidth=0.8, hatch=hatch,
        )
        column_ax.add_patch(rect)
        lithology_entries.setdefault(label, (color, hatch))

        if unit.hydrothermal_alteration:
            primary_alteration = unit.hydrothermal_alteration[0]
            alteration_color = resolve_alteration_color(primary_alteration)
            if alteration_color is not None:
                strip = patches.Rectangle(
                    (-_ALTERATION_STRIP_WIDTH - _ALTERATION_STRIP_GAP, top),
                    width=_ALTERATION_STRIP_WIDTH, height=height,
                    facecolor=alteration_color, edgecolor="black", linewidth=0.6,
                )
                column_ax.add_patch(strip)
                alteration_entries.setdefault(primary_alteration, alteration_color)

    top_min = min(top for top, _ in depths)
    base_max = max(base for _, base in depths)

    has_alteration_strip = bool(alteration_entries)
    left_xlim = -_ALTERATION_STRIP_WIDTH - _ALTERATION_STRIP_GAP if has_alteration_strip else 0
    column_ax.set_xlim(left_xlim, 1)
    column_ax.set_ylim(base_max, top_min)  # invertido: profundidad crece hacia abajo
    column_ax.set_xticks([])
    column_ax.set_ylabel("Profundidad (m)")

    _draw_legend(legend_ax, lithology_entries, alteration_entries)

    if column.name:
        fig.suptitle(column.name, fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.96))
    else:
        fig.tight_layout()

    return fig, (column_ax, legend_ax)


def _draw_legend(
    ax: Axes,
    lithology_entries: dict[str, tuple],
    alteration_entries: dict[str, str],
) -> None:
    """Dibuja la leyenda: litologías (color + patrón) y, aparte, alteraciones."""
    swatch_height = 0.8
    gap = 0.4
    y = 0.0

    ax.text(0, y, "Litología", fontsize=10, fontweight="bold", va="bottom")
    y += 0.5

    for lithology, (color, hatch) in lithology_entries.items():
        rect = patches.Rectangle(
            (0, y), width=1, height=swatch_height,
            facecolor=color, edgecolor="black", linewidth=0.8, hatch=hatch,
        )
        ax.add_patch(rect)
        ax.text(1.2, y + swatch_height / 2, lithology, va="center", ha="left", fontsize=9)
        y += swatch_height + gap

    if alteration_entries:
        y += gap  # separación extra antes de la sección de alteración
        ax.text(0, y, "Alteración hidrotermal", fontsize=10, fontweight="bold", va="bottom")
        y += 0.5

        for alteration, color in alteration_entries.items():
            rect = patches.Rectangle(
                (0, y), width=_ALTERATION_STRIP_WIDTH, height=swatch_height,
                facecolor=color, edgecolor="black", linewidth=0.6,
            )
            ax.add_patch(rect)
            ax.text(_ALTERATION_STRIP_WIDTH + 0.1, y + swatch_height / 2, alteration.replace("_", " "),
                    va="center", ha="left", fontsize=9)
            y += swatch_height + gap

    ax.set_xlim(0, 1)
    ax.set_ylim(y, -gap)
    ax.axis("off")
