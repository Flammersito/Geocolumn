"""Configuración compartida de las pruebas."""

import matplotlib

matplotlib.use("Agg")  # backend sin pantalla

import matplotlib.pyplot as plt
import pytest


@pytest.fixture(autouse=True)
def close_figures():
    """Cierra todas las figuras después de cada prueba, para no acumularlas."""
    yield
    plt.close("all")
