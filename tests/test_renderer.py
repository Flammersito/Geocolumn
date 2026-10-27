"""Pruebas unitarias para geocolumn.rendering.column_renderer."""

import matplotlib
matplotlib.use("Agg")  # backend sin pantalla, necesario para correr en pruebas

from geocolumn.core.column import StratigraphicColumn
from geocolumn.rendering.column_renderer import render_column


def _simple_column() -> StratigraphicColumn:
    return StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 10, "lithology": "arenisca",
             "pattern": "607"},
            {"unit_id": "A2", "top_depth": 10, "base_depth": 18, "lithology": "lutita"},
            {"unit_id": "A3", "top_depth": 18, "base_depth": 25, "lithology": "arenisca",
             "pattern": "607"},  # misma litología que A1, debe compartir entrada de leyenda
        ],
        name="Columna de prueba",
    )


def test_render_column_draws_one_rectangle_per_unit():
    column = _simple_column()
    fig, (column_ax, legend_ax) = render_column(column)
    assert len(column_ax.patches) == len(column)


def test_render_column_legend_has_one_entry_per_unique_lithology():
    column = _simple_column()
    fig, (column_ax, legend_ax) = render_column(column)
    unique_lithologies = {unit.lithology for unit in column}
    assert len(legend_ax.patches) == len(unique_lithologies)


def test_render_column_sets_title_from_column_name():
    column = _simple_column()
    fig, _ = render_column(column)
    assert fig._suptitle.get_text() == "Columna de prueba"


def test_render_column_works_without_name():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca"}]
    )
    fig, (column_ax, legend_ax) = render_column(column)
    assert fig._suptitle is None


# --- Catálogo de litologías y prioridad de apariencia ---

import warnings

import pytest

from geocolumn.styles.lithologies import LithologyStyle, default_catalog


def _hatches(column_ax):
    return [p.get_hatch() for p in column_ax.patches]


def _facecolors(column_ax):
    return [p.get_facecolor() for p in column_ax.patches]


def test_catalog_provides_default_pattern_when_unit_has_none():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca"}]
    )
    _, (column_ax, _) = render_column(column)
    assert _hatches(column_ax) == ["."]  # patrón 607


def test_explicit_unit_pattern_overrides_catalog_default():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca",
          "pattern": "627"}]  # caliza
    )
    _, (column_ax, _) = render_column(column)
    assert _hatches(column_ax) == ["+"]


def test_explicit_unit_color_overrides_catalog_default():
    default_col = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca"}]
    )
    custom_col = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca",
          "color": "negro"}]
    )
    _, (ax_default, _) = render_column(default_col)
    _, (ax_custom, _) = render_column(custom_col)
    assert _facecolors(ax_default) != _facecolors(ax_custom)


def test_unknown_pattern_code_warns_and_falls_back_to_lithology_default():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca",
          "pattern": "999999"}]
    )
    with pytest.warns(UserWarning, match="999999"):
        _, (column_ax, _) = render_column(column)
    assert _hatches(column_ax) == ["."]


def test_unknown_lithology_still_renders_without_pattern():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "roca_rara"}]
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # no debe emitir advertencias
        _, (column_ax, _) = render_column(column)
    assert not any(_hatches(column_ax))  # sin patrón (None o "" según la versión)


def test_custom_catalog_is_used():
    catalog = default_catalog()
    catalog.register(LithologyStyle("skarn", "Skarn", "verde_oscuro", "718"))
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "skarn"}]
    )
    _, (column_ax, _) = render_column(column, catalog=catalog)
    assert _hatches(column_ax) == ["x*"]


def test_aliases_share_one_legend_entry():
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca"},
            {"unit_id": "A2", "top_depth": 5, "base_depth": 9, "lithology": "sandstone"},
        ]
    )
    _, (_, legend_ax) = render_column(column)
    assert len(legend_ax.patches) == 1


# --- Perfil granulométrico ---

def _widths(column_ax):
    return [p.get_width() for p in column_ax.patches]


def _grain_column():
    return StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "lutita",
             "grain_size": "arcilla"},
            {"unit_id": "A2", "top_depth": 5, "base_depth": 9, "lithology": "arenisca",
             "grain_size": "arena media"},
            {"unit_id": "A3", "top_depth": 9, "base_depth": 10, "lithology": "conglomerado",
             "grain_size": "canto"},
        ]
    )


def test_without_grain_scale_all_units_have_full_width():
    _, (column_ax, _) = render_column(_grain_column())
    assert _widths(column_ax) == [1.0, 1.0, 1.0]


def test_grain_scale_sets_width_from_grain_size():
    _, (column_ax, _) = render_column(_grain_column(), grain_scale="siliciclastic")
    widths = _widths(column_ax)
    assert widths == sorted(widths) and len(set(widths)) == 3
    assert widths[2] == pytest.approx(1.0)  # canto = el más grueso


def test_grain_scale_draws_axis_with_level_labels():
    _, (column_ax, _) = render_column(_grain_column(), grain_scale="siliciclastic")
    labels = [t.get_text() for t in column_ax.get_xticklabels()]
    assert labels[0] == "Arcilla" and labels[-1] == "Canto"
    assert column_ax.get_xlabel() == "Granulometría"


def test_unit_without_grain_size_is_full_width_without_warning():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "L1", "top_depth": 0, "base_depth": 5, "lithology": "andesita_lava"}]
    )
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        _, (column_ax, _) = render_column(column, grain_scale="siliciclastic")
    assert _widths(column_ax) == [1.0]


def test_unknown_grain_size_warns_and_is_full_width():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "arenisca",
          "grain_size": "arena fina a media"}]
    )
    with pytest.warns(UserWarning, match="arena fina a media"):
        _, (column_ax, _) = render_column(column, grain_scale="siliciclastic")
    assert _widths(column_ax) == [1.0]


def test_carbonate_scale_uses_dunham_labels():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "C1", "top_depth": 0, "base_depth": 5, "lithology": "caliza",
          "grain_size": "wackestone"}]
    )
    _, (column_ax, _) = render_column(column, grain_scale="carbonate")
    assert "Packstone" in [t.get_text() for t in column_ax.get_xticklabels()]


def test_invalid_grain_scale_name_raises():
    with pytest.raises(ValueError, match="no reconocida"):
        render_column(_grain_column(), grain_scale="volcanica")


# --- Orientación del eje ---

def test_height_mode_axis_grows_upward_and_is_labeled_height():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "base_height": 0, "top_height": 5, "lithology": "lutita"}]
    )
    _, (column_ax, _) = render_column(column)
    low, high = column_ax.get_ylim()
    assert low < high
    assert column_ax.get_ylabel() == "Altura (m)"


def test_depth_mode_axis_is_inverted_and_labeled_depth():
    column = StratigraphicColumn.from_dicts(
        [{"unit_id": "A1", "top_depth": 0, "base_depth": 5, "lithology": "lutita"}]
    )
    _, (column_ax, _) = render_column(column)
    top, bottom = column_ax.get_ylim()
    assert top > bottom
    assert column_ax.get_ylabel() == "Profundidad (m)"


def test_height_mode_legend_lists_youngest_unit_first():
    """Las unidades se ingresan desde la base; la leyenda sigue el orden visual (techo primero)."""
    column = StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "base_height": 0, "top_height": 5, "lithology": "lutita"},
            {"unit_id": "A2", "base_height": 5, "top_height": 9, "lithology": "arenisca"},
        ]
    )
    _, (_, legend_ax) = render_column(column)
    labels = [t.get_text() for t in legend_ax.texts]
    assert labels[1:] == ["Arenisca", "Lutita"]


# --- Contactos y vetas ---

from geocolumn.core.models import ContactType


def _contact_column(contact, widths=("arcilla", "arcilla")):
    return StratigraphicColumn.from_dicts(
        [
            {"unit_id": "A1", "base_height": 0, "top_height": 5, "lithology": "lutita",
             "top_contact": contact, "grain_size": widths[0]},
            {"unit_id": "A2", "base_height": 5, "top_height": 9, "lithology": "arenisca",
             "grain_size": widths[1]},
        ]
    )


def _lines_at_height(column_ax, y):
    return [ln for ln in column_ax.lines
            if len(set(np.round(ln.get_ydata(), 6))) >= 1 and abs(float(np.mean(ln.get_ydata())) - y) < 0.05
            and len(ln.get_xdata()) >= 2 and ln.get_xdata()[0] != ln.get_xdata()[-1]]


import numpy as np


@pytest.mark.parametrize(
    "contact, linestyle_check",
    [
        ("inferido", lambda ln: ln.get_linestyle() not in ("-", ":") and ln.get_linewidth() == pytest.approx(1.3)),
        ("gradual", lambda ln: ln.get_linestyle() == ":"),
        ("falla", lambda ln: ln.get_linewidth() > 2),
    ],
)
def test_contact_styles_are_drawn_at_the_boundary(contact, linestyle_check):
    _, (column_ax, _) = render_column(_contact_column(contact))
    boundary = _lines_at_height(column_ax, 5.0)
    assert any(linestyle_check(ln) for ln in boundary)


def test_erosive_contact_is_wavy():
    _, (column_ax, _) = render_column(_contact_column("erosivo"))
    wavy = [ln for ln in _lines_at_height(column_ax, 5.0) if len(set(np.round(ln.get_ydata(), 6))) > 5]
    assert wavy


def test_sharp_contact_adds_no_contact_legend_section():
    _, (_, legend_ax) = render_column(_contact_column("neto"))
    assert "Contactos" not in [t.get_text() for t in legend_ax.texts]


def test_legend_lists_each_drawn_contact_type_once():
    _, (_, legend_ax) = render_column(_contact_column("inferido"))
    texts = [t.get_text() for t in legend_ax.texts]
    assert "Contactos" in texts and texts.count("Contacto inferido") == 1


def test_contact_only_covers_shared_width_when_units_differ():
    """Con perfil granulométrico, el contacto no debe pasar del ancho de la unidad más angosta."""
    column = _contact_column("inferido", widths=("arcilla", "arena media"))
    _, (column_ax, _) = render_column(column, grain_scale="siliciclastic")
    dashed = [ln for ln in _lines_at_height(column_ax, 5.0) if ln.get_linewidth() > 1.0]
    assert dashed and max(max(ln.get_xdata()) for ln in dashed) == pytest.approx(0.1)  # 1/10: arcilla


def _vein_column():
    return StratigraphicColumn.from_dicts(
        [
            {"unit_id": "T1", "base_height": 0, "top_height": 100, "lithology": "pizarra"},
            {"unit_id": "V1", "kind": "vein", "base_height": 30, "thickness": 0.6,
             "lithology": "veta_cuarzo"},
            {"unit_id": "V2", "kind": "vein", "base_height": 60, "thickness": 0.15,
             "lithology": "veta_cuarzo"},
        ]
    )


def test_veins_are_drawn_in_their_own_track_with_thickness_labels():
    _, (column_ax, legend_ax) = render_column(_vein_column())
    assert len(column_ax.patches) == 1 + 2  # unidad + 2 vetas
    labels = [t.get_text() for t in column_ax.texts]
    assert "60 cm" in labels and "15 cm" in labels and "Vetas" in labels
    assert "Veta de cuarzo" in [t.get_text() for t in legend_ax.texts]


def test_thin_veins_get_a_minimum_visible_height():
    _, (column_ax, _) = render_column(_vein_column())
    vein_rects = [p for p in column_ax.patches if p.get_x() > 1]
    assert all(r.get_height() >= 0.01 * 100 for r in vein_rects)  # 15 cm se dibuja visible


def test_columns_without_veins_have_no_vein_track():
    _, (column_ax, _) = render_column(_contact_column("neto"))
    assert column_ax.get_xlim()[1] == pytest.approx(1.0)
