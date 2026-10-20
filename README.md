# GeoColumn

<!-- Una vez conectado a GitHub, reemplaza "usuario/geocolumn" por tu
     ruta real (ej. "santi-rojas/geocolumn") para que el badge funcione:
     ![Tests](https://github.com/usuario/geocolumn/actions/workflows/tests.yml/badge.svg) -->

Software de código abierto en Python para generar columnas estratigráficas
de calidad profesional a partir de datos estructurados (Excel, y en el
futuro CSV, GeoPackage/Shapefile), pensado para geólogos, estudiantes e
investigadores.

## Estado actual

Etapa temprana de desarrollo. Hasta ahora:

- Modelo de datos (`geocolumn.core`): `StratigraphicUnit`, `GeologicAge`,
  `StratigraphicColumn`, con un constructor `from_dict`/`from_dicts`
  compartido por todas las fuentes de entrada.
- Lector de Excel (`geocolumn.io.excel_reader`).
- Catálogos de estilo (`geocolumn.styles`): colores descriptivos,
  patrones litológicos (numeración oficial FGDC-STD-013-2006, series
  600/700), indicadores de alteración hidrotermal y un **catálogo
  extensible de litologías** (sedimentarias, volcánicas, intrusivas,
  metamórficas y de veta) que asigna color y patrón por defecto.
- Renderizador básico (`geocolumn.rendering.column_renderer`): dibuja
  la columna con colores, patrones (aproximados vía `hatch` de
  matplotlib) y una leyenda separada.

Ver `docs/reference/README.md` para los documentos de referencia usados
en el diseño del catálogo de patrones.

## Instalación (desarrollo)

```bash
pip install -e ".[dev]"
pytest tests/
```

Con `pip install -e .` el paquete queda disponible desde cualquier
notebook o script de Jupyter/Anaconda (`import geocolumn`).

## Uso rápido

```python
from geocolumn.io.excel_reader import read_column_from_excel
from geocolumn.rendering.column_renderer import render_column

column = read_column_from_excel("mi_columna.xlsx")

# o, sin Excel, directamente en código:
from geocolumn.core.column import StratigraphicColumn
column = StratigraphicColumn.from_dicts([
    {"unit_id": "A1", "top_depth": 0, "base_depth": 15, "lithology": "andesita"},
])

fig, _ = render_column(column)
fig.savefig("columna.png", dpi=300)
```

## Litologías: color y patrón automáticos

Basta con escribir el nombre de la litología (`arenisca`, `caliza`,
`andesita_lava`, `granito`…; también sus nombres en inglés). GeoColumn
pone el color y el patrón FGDC por defecto. Lo que escribas
explícitamente en una unidad (`color`, `pattern`) tiene prioridad.
Un código de `pattern` que no exista genera una advertencia.

Para agregar tus propias litologías:

```python
from geocolumn.styles.lithologies import LithologyStyle, default_catalog

catalog = default_catalog()
catalog.register(LithologyStyle("skarn", "Skarn", color="verde_oscuro", pattern="718"))

fig, _ = render_column(column, catalog=catalog)
```

## Ejemplo completo

`examples/ejemplo_volcanosedimentario.xlsx` es una plantilla lista para
copiar y modificar; `python examples/ejemplo_volcanosedimentario.py`
genera la figura.

## Licencia

MIT — ver [LICENSE](LICENSE).
