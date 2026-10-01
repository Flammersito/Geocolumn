# GeoColumn

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
  600/700), e indicadores de alteración hidrotermal.
- Renderizador básico (`geocolumn.rendering.column_renderer`): dibuja
  la columna con colores, patrones (aproximados vía `hatch` de
  matplotlib) y una leyenda separada.

Ver `docs/reference/README.md` para los documentos de referencia usados
en el diseño del catálogo de patrones.

## Instalación (desarrollo)

```bash
pip install -r requirements.txt
pytest tests/
```

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
