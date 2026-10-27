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

## Orientación: afloramiento (altura) o sondaje (profundidad)

GeoColumn deduce cómo mediste la columna a partir de las columnas del Excel:

| Si escribes…                         | Modo       | Eje en la figura                          |
|--------------------------------------|------------|-------------------------------------------|
| `base_height_m` y `top_height_m`     | `height`   | Altura desde la base (0 abajo), lo más joven arriba |
| solo `thickness_m`                   | `height`   | Se apilan hacia arriba; la primera fila es la base |
| `top_depth_m` y `base_depth_m`       | `depth`    | Profundidad (0 arriba, crece hacia abajo) |

Para columnas de afloramiento, lista las unidades **desde la base** hacia
arriba. Mezclar alturas y profundidades, o poner la base por encima del
techo, genera un error explícito. Puedes forzar el modo con
`axis="height"` o `axis="depth"` en `read_column_from_excel` y
`StratigraphicColumn.from_dicts`.

## Contactos

`top_contact` describe el contacto en el **techo** de la unidad, es decir,
con la unidad que tiene encima (en una columna de afloramiento, la unidad
de arriba es la más joven). El techo de la unidad más alta no tiene unidad
encima, así que ahí no se dibuja contacto.

| Valor (o en español)      | Dibujo            |
|---------------------------|-------------------|
| `sharp` / `neto`          | línea continua fina (por defecto) |
| `gradual`                 | línea punteada    |
| `erosive` / `erosivo`     | línea ondulada    |
| `fault` / `falla`         | línea gruesa      |
| `inferred` / `inferido`   | línea a rayas     |

Los contactos no netos aparecen en una sección "Contactos" de la leyenda.

## Vetas

Una fila con `kind` = `vein` (o `veta`) es una veta, no una unidad de roca.
No se apila: se dibuja en una pista aparte a la derecha de la columna, en
su altura, con su espesor rotulado. Necesita su posición (`base_height_m`,
o `top_depth_m` en modo profundidad) y su espesor (`thickness_m` en metros,
15 cm = 0.15, o la otra posición). Si la veta es demasiado delgada para
verse a escala, se dibuja con una altura mínima visible; el rótulo conserva
el espesor real.

## Perfil granulométrico (columnas sedimentarias)

En una columna sedimentaria, el ancho de cada capa representa su
granulometría. Escribe el valor en la columna `grain_size` del Excel y
activa una escala al dibujar:

```python
fig, _ = render_column(column, grain_scale="siliciclastic")  # arcilla → canto
fig, _ = render_column(column, grain_scale="carbonate")      # mudstone → boundstone (Dunham)
```

Las dos escalas son independientes (no hay una equivalencia universal
entre, por ejemplo, un wackestone y un tamaño de arena). Las unidades
sin `grain_size` (por ejemplo, una lava) se dibujan a todo el ancho, y
un valor que no pertenezca a la escala genera una advertencia. Sin
`grain_scale`, todas las unidades miden lo mismo.

## Ejemplos

- `examples/ejemplo_volcanosedimentario.xlsx`: secuencia volcano-sedimentaria
  con alteración hidrotermal, en profundidad (estilo sondaje).
- `examples/ejemplo_tesis.xlsx`: columna de campo de tres unidades con
  contactos inferidos y tres vetas de cuarzo (valores de ejemplo).
- `examples/ejemplo_sedimentario.xlsx`: dos hojas (siliciclástica y
  carbonatos) en altura (estilo afloramiento), con espesores y
  granulometrías variables.

Cada uno tiene su script (`python examples/ejemplo_*.py`) que genera la figura.

## Licencia

MIT — ver [LICENSE](LICENSE).
