"""Renderizado básico de columnas estratigráficas con matplotlib.

Primera etapa del motor de renderizado: dibuja cada unidad como un
rectángulo coloreado según su litología, con un patrón FGDC
aproximado (via hatch) y, si aplica, una franja indicadora de
alteración hidrotermal al margen. Todavía no incluye símbolos,
fósiles, ni los patrones vectoriales oficiales (ver docs/reference/
para cuando se implemente esa etapa).
"""

import hashlib
import textwrap
import warnings

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from geocolumn.core.column import StratigraphicColumn
from geocolumn.core.models import ContactType
from geocolumn.styles.alteration import resolve_alteration_color
from geocolumn.styles.colors import resolve_color
from geocolumn.styles.grain_scales import GrainScale, resolve_grain_scale
from geocolumn.styles.lithologies import LithologyCatalog, LithologyStyle, default_catalog
from geocolumn.styles.patterns import resolve_pattern

# Paleta cualitativa de 20 colores, estable entre ejecuciones. Se usa
# como respaldo cuando una unidad no tiene color catalogado.
_PALETTE = plt.get_cmap("tab20").colors

# Ancho de la franja de alteración, en las mismas unidades que el
# cuerpo de la columna (que ocupa x en [0, 1]).
_ALTERATION_STRIP_WIDTH = 0.15
_ALTERATION_STRIP_GAP = 0.03


# Grosor de las líneas de textura (hatch). El valor por defecto de
# matplotlib (1.0) se ve pesado en unidades angostas. Solo se aplica en
# matplotlib >= 3.10, donde cada parche puede tener su propio grosor.
_HATCH_LINEWIDTH = 0.5

# Número mínimo de filas que reserva la leyenda, para que el tamaño de
# los cuadros no dependa de cuántas litologías haya.
_LEGEND_MIN_ROWS = 9

# Anchos dentro del panel de la leyenda (su eje x va de 0 a _LEGEND_XLIM):
# el cuadro de litología mide 1, y el texto empieza justo después.
_LEGEND_XLIM = 3.0
_LEGEND_SWATCH_WIDTH = 0.8
_LEGEND_ALTERATION_SWATCH_WIDTH = 0.4
_LEGEND_TEXT_GAP = 0.15

# Ancho máximo (en caracteres) de las etiquetas de la leyenda antes de
# partirlas en varias líneas.
_LEGEND_LABEL_WIDTH = 18


# Pista de vetas, a la derecha de la columna (coordenadas x del eje de la columna).
_VEIN_TRACK_X0 = 1.12
_VEIN_TRACK_X1 = 1.32
_VEIN_LABEL_X = 1.36
_VEIN_RIGHT_XLIM = 1.6
# Altura mínima visible de una veta, como fracción de la altura total de la
# columna: una veta de 15 cm en una columna de 100 m no se vería a escala.
_VEIN_MIN_HEIGHT_FRACTION = 0.012

_CONTACT_LABELS = {
    ContactType.GRADUAL: "Contacto gradual",
    ContactType.EROSIVE: "Contacto erosivo",
    ContactType.FAULT: "Falla",
    ContactType.INFERRED: "Contacto inferido",
}


def _contact_line(contact: ContactType, x0: float, x1: float, y: float, amplitude: float):
    """Devuelve `(xs, ys, estilo)` de la línea que representa un contacto.

    Neto: línea fina continua. Gradual: punteada. Erosivo: ondulada.
    Falla: línea gruesa. Inferido: línea a rayas. `amplitude` es la
    amplitud de la onda del contacto erosivo, en unidades del eje y.
    """
    xs = np.array([x0, x1], dtype=float)
    ys = np.array([y, y], dtype=float)
    style = {"color": "black", "linewidth": 0.8, "linestyle": "-"}
    if contact == ContactType.GRADUAL:
        style.update(linestyle=":", linewidth=1.4)
    elif contact == ContactType.INFERRED:
        style.update(linestyle=(0, (5, 2.5)), linewidth=1.3)
    elif contact == ContactType.FAULT:
        style.update(linewidth=2.4)
    elif contact == ContactType.EROSIVE and x1 > x0:
        waves = max(2, round(10 * (x1 - x0)))
        xs = np.linspace(x0, x1, 40 * waves)
        ys = y + amplitude * np.sin(2 * np.pi * waves * (xs - x0) / (x1 - x0))
    return xs, ys, style


def _draw_outlines(ax: Axes, drawn: list, amplitude: float, tol: float) -> list[ContactType]:
    """Dibuja el contorno de cada unidad, con el estilo de su contacto superior.

    `drawn` es una lista de `(unidad, techo_visual, base_visual, ancho)`.
    El contacto entre una unidad y la que tiene encima lo define el
    `top_contact` de la unidad de abajo. Solo la parte compartida entre
    ambas lleva el estilo del contacto; si una es más ancha que la otra,
    el tramo expuesto se dibuja como borde normal.

    Returns:
        Los tipos de contacto no netos que se dibujaron, sin repetir y en
        el orden en que aparecen (para la leyenda).
    """
    solid = {"color": "black", "linewidth": 0.8, "solid_capstyle": "butt", "zorder": 3}
    found: list[ContactType] = []

    def hline(x0: float, x1: float, y: float) -> None:
        ax.plot([x0, x1], [y, y], **solid)

    for i, (unit, v_top, v_bottom, width) in enumerate(drawn):
        above = next((d for j, d in enumerate(drawn) if j != i and abs(d[2] - v_top) <= tol), None)
        below = next((d for j, d in enumerate(drawn) if j != i and abs(d[1] - v_bottom) <= tol), None)

        ax.plot([0, 0], [v_bottom, v_top], **solid)
        ax.plot([width, width], [v_bottom, v_top], **solid)

        if above is None:
            hline(0, width, v_top)
        else:
            shared = min(width, above[3])
            if shared > 0:
                xs, ys, style = _contact_line(unit.top_contact, 0, shared, v_top, amplitude)
                ax.plot(xs, ys, solid_capstyle="butt", zorder=3, **style)
                if unit.top_contact != ContactType.SHARP and unit.top_contact not in found:
                    found.append(unit.top_contact)
            if width > shared:
                hline(shared, width, v_top)

        if below is None:
            hline(0, width, v_bottom)
        elif width > below[3]:
            hline(below[3], width, v_bottom)

    return found


def _draw_veins(
    ax: Axes,
    column: StratigraphicColumn,
    catalog: LithologyCatalog,
    entries: dict[str, tuple],
    axis: str,
    lowest: float,
    highest: float,
) -> None:
    """Dibuja las vetas en una pista a la derecha de la columna.

    Cada veta es un rectángulo en su altura (o profundidad), con su
    espesor real rotulado. Si es muy delgada para verse a escala, se
    dibuja con una altura mínima visible (el rótulo conserva el espesor
    real). Un hilo punteado la une con el borde de la columna.
    """
    span = (highest - lowest) or 1.0
    min_height = _VEIN_MIN_HEIGHT_FRACTION * span
    v_top_of_column = highest if axis == "height" else lowest

    for vein, (start, end) in zip(column.veins, column.resolve_vein_positions()):
        style = catalog.get(vein.lithology)
        color = _resolve_unit_color(vein, style)
        hatch = _resolve_unit_hatch(vein, style)
        thickness = end - start
        center = (start + end) / 2
        draw_height = max(thickness, min_height)

        rect = patches.Rectangle(
            (_VEIN_TRACK_X0, center - draw_height / 2),
            width=_VEIN_TRACK_X1 - _VEIN_TRACK_X0, height=draw_height,
            facecolor=color, edgecolor="black", linewidth=0, hatch=hatch,
        )
        _style_hatch(rect)
        ax.add_patch(rect)
        ax.plot(
            [_VEIN_TRACK_X0, _VEIN_TRACK_X1, _VEIN_TRACK_X1, _VEIN_TRACK_X0, _VEIN_TRACK_X0],
            [center - draw_height / 2, center - draw_height / 2,
             center + draw_height / 2, center + draw_height / 2, center - draw_height / 2],
            color="black", linewidth=0.8, zorder=3,
        )
        ax.plot([1.0, _VEIN_TRACK_X0], [center, center], color="0.5", linewidth=0.5,
                linestyle=":", zorder=2)
        label_text = f"{thickness * 100:.0f} cm" if thickness < 1 else f"{thickness:.1f} m"
        ax.text(_VEIN_LABEL_X, center, label_text, va="center", ha="left", fontsize=7)

        legend_label = style.display_name if style else vein.lithology
        entries.setdefault(legend_label, (color, hatch))

    ax.annotate("Vetas", xy=((_VEIN_TRACK_X0 + _VEIN_TRACK_X1) / 2, v_top_of_column),
                xytext=(0, 3), textcoords="offset points",
                ha="center", va="bottom", fontsize=8, fontweight="bold")


def _style_hatch(patch: patches.Patch) -> None:
    """Afina el grosor del hatch de un parche, si matplotlib lo permite."""
    if hasattr(patch, "set_hatch_linewidth"):
        patch.set_hatch_linewidth(_HATCH_LINEWIDTH)


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


def _resolve_unit_width(unit, scale: GrainScale | None) -> float:
    """Ancho relativo (0 a 1) de una unidad según su granulometría.

    Sin escala, o sin `grain_size`, la unidad ocupa todo el ancho. Si
    `grain_size` tiene un valor que la escala no reconoce (por ejemplo,
    un error de dedo o un rango como "arena fina a media"), se emite una
    advertencia en vez de ignorarlo en silencio.
    """
    if scale is None or not unit.grain_size:
        return 1.0
    width = scale.width_for(unit.grain_size)
    if width is None:
        warnings.warn(
            f"Unidad '{unit.unit_id}': la granulometría '{unit.grain_size}' no está en la "
            f"escala '{scale.name}'; se dibujará a todo el ancho.",
            stacklevel=3,
        )
        return 1.0
    return width


def render_column(
    column: StratigraphicColumn,
    figsize: tuple[float, float] = (6, 10),
    catalog: LithologyCatalog | None = None,
    grain_scale: "str | GrainScale | None" = None,
) -> tuple[Figure, tuple[Axes, Axes]]:
    """Dibuja una columna estratigráfica como rectángulos de litología.

    Cada unidad se dibuja como un rectángulo cuya altura es su espesor
    (resuelto mediante `column.resolve_positions()`), coloreado según
    `unit.color` (si está en el catálogo) con el patrón FGDC de
    `unit.pattern` (si está catalogado). Si la unidad tiene alteración
    hidrotermal catalogada, se dibuja además una franja angosta a su
    izquierda con el color indicador correspondiente (se usa solo la
    primera alteración de la lista, por simplicidad).

    El eje Y depende de `column.axis`: en modo `"height"` (columnas de
    afloramiento) es la altura desde la base, creciendo hacia arriba y
    con lo más joven arriba; en modo `"depth"` (sondajes) es la
    profundidad, con el punto más somero arriba y creciendo hacia abajo.
    La columna
    no lleva etiquetas de texto junto a cada rectángulo; en vez de
    eso, se dibuja una leyenda aparte con una entrada por cada
    litología y por cada tipo de alteración presentes.

    Si se indica `grain_scale`, el ancho de cada unidad depende de su
    `grain_size` (finas angostas, gruesas anchas), con un eje
    horizontal que muestra los niveles de la escala. Las unidades sin
    `grain_size` (por ejemplo, una lava) se dibujan a todo el ancho; si
    el valor no pertenece a la escala, se advierte y se dibuja a todo
    el ancho. Sin `grain_scale`, todas las unidades miden lo mismo.

    Args:
        column: La columna a dibujar. Debe tener suficiente información
            de profundidad o espesor en cada unidad (ver
            `StratigraphicColumn.resolve_positions`).
        figsize: Tamaño de la figura en pulgadas.
        catalog: Catálogo de litologías con los colores y patrones por
            defecto. Si es `None`, se usa el catálogo por defecto de
            GeoColumn (`default_catalog()`). Pasa uno propio, ampliado
            con `register`, para incluir litologías adicionales.
        grain_scale: Escala granulométrica: `"siliciclastic"`,
            `"carbonate"` o una `GrainScale` propia. `None` (por
            defecto) dibuja todas las unidades a todo el ancho.

    Returns:
        Una tupla `(figura, (eje_columna, eje_leyenda))` de matplotlib,
        para que el llamador pueda seguir modificando la figura o
        exportarla.
    """
    positions = column.resolve_positions()
    axis = column.resolved_axis()
    catalog = catalog if catalog is not None else default_catalog()
    scale = resolve_grain_scale(grain_scale)

    # Con perfil granulométrico, la columna necesita más ancho que la leyenda.
    width_ratios = [1.5, 1] if scale is not None else [1, 1.3]
    fig, (column_ax, legend_ax) = plt.subplots(
        ncols=2, figsize=figsize, gridspec_kw={"width_ratios": width_ratios}
    )

    lithology_entries: dict[str, tuple] = {}   # nombre en leyenda -> (color, hatch)
    alteration_entries: dict[str, str] = {}    # nombre de alteración -> color

    lowest = min(start for start, _ in positions)
    highest = max(end for _, end in positions)
    span = (highest - lowest) or 1.0

    # Se recorre de arriba hacia abajo (visualmente), para que la leyenda
    # liste las litologías en el mismo orden en que aparecen en la columna.
    visual_order = sorted(zip(column, positions), key=lambda pair: pair[1][0],
                          reverse=(axis == "height"))

    # Geometría visual de cada unidad: (unidad, techo, base, ancho). En modo
    # altura el techo es el extremo mayor; en profundidad, el menor.
    drawn = []
    for unit, (start, end) in visual_order:
        v_top, v_bottom = (end, start) if axis == "height" else (start, end)
        drawn.append((unit, v_top, v_bottom, _resolve_unit_width(unit, scale)))

    for unit, v_top, v_bottom, width in drawn:
        y0 = min(v_top, v_bottom)
        height = abs(v_top - v_bottom)
        style = catalog.get(unit.lithology)
        color = _resolve_unit_color(unit, style)
        hatch = _resolve_unit_hatch(unit, style)
        label = style.display_name if style else unit.lithology

        # El borde se dibuja aparte (_draw_outlines), con el estilo de cada
        # contacto; por eso el rectángulo no lleva borde propio.
        rect = patches.Rectangle(
            (0, y0), width=width, height=height,
            facecolor=color, edgecolor="black", linewidth=0, hatch=hatch,
        )
        _style_hatch(rect)
        column_ax.add_patch(rect)
        lithology_entries.setdefault(label, (color, hatch))

        if unit.hydrothermal_alteration:
            primary_alteration = unit.hydrothermal_alteration[0]
            alteration_color = resolve_alteration_color(primary_alteration)
            if alteration_color is not None:
                strip = patches.Rectangle(
                    (-_ALTERATION_STRIP_WIDTH - _ALTERATION_STRIP_GAP, y0),
                    width=_ALTERATION_STRIP_WIDTH, height=height,
                    facecolor=alteration_color, edgecolor="black", linewidth=0.6,
                )
                column_ax.add_patch(strip)
                alteration_entries.setdefault(primary_alteration, alteration_color)

    contact_entries = _draw_outlines(column_ax, drawn, amplitude=0.008 * span, tol=1e-6 * span)

    if column.veins:
        _draw_veins(column_ax, column, catalog, lithology_entries, axis, lowest, highest)

    has_alteration_strip = bool(alteration_entries)
    left_xlim = -_ALTERATION_STRIP_WIDTH - _ALTERATION_STRIP_GAP if has_alteration_strip else 0
    column_ax.set_xlim(left_xlim, _VEIN_RIGHT_XLIM if column.veins else 1)
    if axis == "depth":
        column_ax.set_ylim(highest, lowest)  # invertido: la profundidad crece hacia abajo
        column_ax.set_ylabel("Profundidad (m)")
    else:
        column_ax.set_ylim(lowest, highest)  # la altura crece hacia arriba; lo más joven arriba
        column_ax.set_ylabel("Altura (m)")
    if scale is not None:
        column_ax.vlines(
            scale.tick_positions(), lowest, highest,
            colors="0.8", linestyles="--", linewidth=0.5, zorder=0,
        )
        column_ax.set_xticks(scale.tick_positions())
        column_ax.set_xticklabels(scale.tick_labels(), rotation=90, fontsize=7)
        column_ax.set_xlabel(scale.title, fontsize=9)
    else:
        column_ax.set_xticks([])

    _draw_legend(legend_ax, lithology_entries, alteration_entries, contact_entries)

    if column.name:
        fig.suptitle(column.name, fontsize=12)
        fig.tight_layout(rect=(0, 0, 1, 0.96))
    else:
        fig.tight_layout()

    return fig, (column_ax, legend_ax)


def _legend_text(ax: Axes, x: float, y: float, text: str) -> None:
    """Escribe una etiqueta de leyenda, partida en líneas si es larga.

    Se excluye del cálculo de `tight_layout` (`in_layout=False`): así las
    etiquetas largas no encogen el panel de la columna.
    """
    wrapped = textwrap.fill(text, width=_LEGEND_LABEL_WIDTH)
    artist = ax.text(x, y, wrapped, va="center", ha="left", fontsize=9)
    artist.set_in_layout(False)


def _draw_legend(
    ax: Axes,
    lithology_entries: dict[str, tuple],
    alteration_entries: dict[str, str],
    contact_entries: list[ContactType] = (),
) -> None:
    """Dibuja la leyenda: litologías (color + patrón) y, aparte, alteraciones y contactos."""
    swatch_height = 0.8
    gap = 0.4
    y = 0.0

    ax.text(0, y, "Litología", fontsize=10, fontweight="bold", va="bottom")
    y += 0.5

    for lithology, (color, hatch) in lithology_entries.items():
        rect = patches.Rectangle(
            (0, y), width=_LEGEND_SWATCH_WIDTH, height=swatch_height,
            facecolor=color, edgecolor="black", linewidth=0.8, hatch=hatch,
        )
        _style_hatch(rect)
        ax.add_patch(rect)
        _legend_text(ax, _LEGEND_SWATCH_WIDTH + _LEGEND_TEXT_GAP, y + swatch_height / 2, lithology)
        y += swatch_height + gap

    if alteration_entries:
        y += gap  # separación extra antes de la sección de alteración
        ax.text(0, y, "Alteración hidrotermal", fontsize=10, fontweight="bold", va="bottom")
        y += 0.5

        for alteration, color in alteration_entries.items():
            rect = patches.Rectangle(
                (0, y), width=_LEGEND_ALTERATION_SWATCH_WIDTH, height=swatch_height,
                facecolor=color, edgecolor="black", linewidth=0.6,
            )
            ax.add_patch(rect)
            _legend_text(ax, _LEGEND_ALTERATION_SWATCH_WIDTH + _LEGEND_TEXT_GAP,
                         y + swatch_height / 2, alteration.replace("_", " "))
            y += swatch_height + gap

    if contact_entries:
        y += gap
        ax.text(0, y, "Contactos", fontsize=10, fontweight="bold", va="bottom")
        y += 0.5

        for contact in contact_entries:
            xs, ys, style = _contact_line(contact, 0, _LEGEND_SWATCH_WIDTH, y + swatch_height / 2,
                                          amplitude=0.1)
            ax.plot(xs, ys, solid_capstyle="butt", **style)
            _legend_text(ax, _LEGEND_SWATCH_WIDTH + _LEGEND_TEXT_GAP, y + swatch_height / 2,
                         _CONTACT_LABELS[contact])
            y += swatch_height + gap

    ax.set_xlim(0, _LEGEND_XLIM)
    ax.set_ylim(max(y, _LEGEND_MIN_ROWS * (swatch_height + gap)), -gap)
    ax.axis("off")
