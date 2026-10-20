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
