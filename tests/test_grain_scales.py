"""Pruebas unitarias para geocolumn.styles.grain_scales."""

import pytest

from geocolumn.styles.grain_scales import (
    CARBONATE_SCALE,
    SILICICLASTIC_SCALE,
    GrainLevel,
    GrainScale,
    resolve_grain_scale,
)


def test_widths_increase_with_coarseness():
    for scale in (SILICICLASTIC_SCALE, CARBONATE_SCALE):
        widths = [scale.width_for(level.key) for level in scale.levels]
        assert widths == sorted(widths)
        assert len(set(widths)) == len(widths)  # todos distintos


def test_finest_is_one_nth_and_coarsest_is_full_width():
    n = len(SILICICLASTIC_SCALE.levels)
    assert SILICICLASTIC_SCALE.width_for("arcilla") == pytest.approx(1 / n)
    assert SILICICLASTIC_SCALE.width_for("canto") == pytest.approx(1.0)


def test_lookup_ignores_case_accents_and_spaces():
    scale = SILICICLASTIC_SCALE
    assert scale.width_for("Arena Media") == scale.width_for("arena_media")
    assert scale.width_for("Gránulo") == scale.width_for("granulo")


def test_lookup_accepts_english_aliases():
    scale = SILICICLASTIC_SCALE
    assert scale.width_for("medium sand") == scale.width_for("arena_media")
    assert scale.width_for("silt") == scale.width_for("limo")


def test_unknown_or_empty_returns_none():
    assert SILICICLASTIC_SCALE.width_for("arena fina a media") is None
    assert SILICICLASTIC_SCALE.width_for(None) is None
    assert SILICICLASTIC_SCALE.width_for("") is None


def test_dunham_order_is_mudstone_wackestone_packstone_grainstone():
    w = CARBONATE_SCALE.width_for
    assert w("mudstone") < w("wackestone") < w("packstone") < w("grainstone")


def test_scales_do_not_mix():
    """Un término de Dunham no existe en la escala siliciclástica y viceversa."""
    assert SILICICLASTIC_SCALE.width_for("wackestone") is None
    assert CARBONATE_SCALE.width_for("arena media") is None


def test_ticks_match_levels_and_end_at_one():
    scale = SILICICLASTIC_SCALE
    assert len(scale.tick_positions()) == len(scale.levels) == len(scale.tick_labels())
    assert scale.tick_positions()[-1] == pytest.approx(1.0)


def test_resolve_grain_scale_by_name_instance_and_none():
    assert resolve_grain_scale("siliciclastic") is SILICICLASTIC_SCALE
    assert resolve_grain_scale("Carbonate") is CARBONATE_SCALE
    assert resolve_grain_scale(CARBONATE_SCALE) is CARBONATE_SCALE
    assert resolve_grain_scale(None) is None


def test_resolve_grain_scale_rejects_unknown_name():
    with pytest.raises(ValueError, match="siliciclastic"):
        resolve_grain_scale("volcanica")


def test_custom_scale_works_and_empty_scale_is_rejected():
    custom = GrainScale("mia", "Mi escala", [GrainLevel("a", "A"), GrainLevel("b", "B")])
    assert custom.width_for("a") == 0.5
    assert custom.width_for("b") == 1.0
    with pytest.raises(ValueError):
        GrainScale("vacia", "Vacía", [])
