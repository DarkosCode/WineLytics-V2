# Registro de cambios — WineLytics-V2

Historial cronológico de los cambios realizados en el proyecto.
Cada entrada indica **qué** se cambió, **por qué** y los **archivos** afectados.

---

## 2026-10-15

### 1. Módulo de análisis estadístico (`statsmodels`)
- **Qué:** se implementó `ejecutar_analisis_estadistico(df_ventas)`, una regresión lineal OLS de
  `Unidades Vendidas ~ Precio Unitario + dummies(Canal de Venta) + dummies(Linea)`.
  Imprime el resumen del modelo, agrega la columna `Prediccion_Ventas` y retorna
  `(df_ventas, metricas_dict, modelo)`. `metricas_dict` contiene `r2`, `r2_adj`, `aic`, `f_pvalue` y `coeficientes`.
- **Por qué:** cumplir con la consigna de descripción/pronóstico estadístico.
- **Detalles:** trabaja sobre una copia del DataFrame, valida columnas requeridas y convierte las dummies a `float`
  (statsmodels no acepta `bool`). Tiene un bloque `__main__` para probarlo de forma independiente.
- **Archivos:** `backend/stats_analysis.py` (nuevo contenido).
- **Resultado inicial:** R² ≈ 0.003. El modelo no explicaba nada porque los datos sintéticos generaban las unidades al azar.

### 2. Generador de datos con correlaciones reales
- **Qué:** las `Unidades_Vendidas` ahora se calculan como `250 - 3.5 × precio`, multiplicado por un factor estacional
  (×1.5 Malbec/Cabernet en Invierno, ×1.6 Torrontés en Verano), más ruido gaussiano (σ = 20), redondeado a entero
  con un mínimo de 20.
- **Por qué:** para que los modelos estadísticos y de Machine Learning encuentren relaciones con sentido de negocio.
- **Detalles:**
  - Las estaciones usan la misma regla que `sources/ventas_csv.py`; antes se usaban otros meses.
  - El código se organizó en funciones con `if __name__ == "__main__":`, así que importar el módulo ya no
    sobrescribe los CSV.
  - Se mantuvieron la semilla 42, las columnas y el esquema de precios.
- **Archivos:** `sources/generadorDeDatos.py`, `data/ventas.csv` (regenerado). `data/inventario.csv` quedó idéntico.
- **Resultado:** correlación unidades–precio de -0.73. R² de `stats_analysis.py`: 0.003 → 0.539.
  Agregando Varietal × Estación al modelo llega a 0.886.
- **Pendiente:** incorporar Varietal y Estación a `stats_analysis.py`. Precio y Línea siguen siendo casi colineales.

### 3. Modelo estadístico con Varietal y Estación (sin Línea)
- **Qué:** el modelo pasa a ser
  `Unidades Vendidas ~ Precio Unitario + dummies(Canal de Venta) + dummies(Varietal) + dummies(Estacion)`.
  Las dummies se generan con `drop_first=True, dtype=float`. Se agregó `bic` a `metricas_dict`, que ahora tiene
  `r2`, `r2_adj`, `f_pvalue`, `aic`, `bic` y `coeficientes`.
- **Por qué:** aprovechar el efecto estacional de los datos nuevos. Se quitó `Linea` porque el precio depende casi por
  completo de la línea (multicolinealidad).
- **Detalles:**
  - `Estacion` pasa a ser columna requerida y `Linea` deja de serlo.
  - En el bloque `__main__` se quitó la lectura directa del CSV como alternativa (no generaba `Estacion`): ahora
    siempre se usa `cargarVentas()`.
  - El bloque `__main__` captura y cuenta las advertencias de la ejecución.
- **Archivos:** `backend/stats_analysis.py`.
- **Resultado:** R² 0.539 → **0.662** (R² ajustado 0.660, p-valor F ≈ 5e-274, AIC 12070, BIC 12116). El número de
  condición bajó de 546 a 117. 0 advertencias.
- **Pendiente:** el modelo suma los efectos por separado y no captura "tinto en Invierno" ni "Torrontés en Verano"
  (subestima Torrontés en Verano). Agregar la interacción Varietal × Estación debería llevar el R² a ~0.88 (valor medido en la entrada 2, con Línea incluida).
  `Canal de Venta` no resultó significativo (p = 0.96).

### 4. Revisión de documentación (README)
- **Qué:** se corrigió el nombre (`WineLitycs` → `WineLytics`), el nombre del repo en el `git clone`
  (`Parcial1_POAD` → `WineLytics-V2`) y la versión mínima de Python (3.8 → 3.11, por `pandas 3.x`/`numpy 2.x`).
  Se agregaron `backend/` y `.agents/` a la estructura del proyecto.
- **Por qué:** el README no reflejaba el estado actual del proyecto.
- **Archivos:** `README.md`.
- **Pendiente:** integrar `ejecutar_analisis_estadistico` en `main.py`; `backend/deep_learning.py` sigue vacío;
  `requirements.txt` mezcla versiones fijadas con rangos (`>=`) y sus dependencias (`dash`, `flask`, `tensorflow`)
  no se usan aún.

### 5. Migración del código a camelCase
- **Qué:** se renombraron archivos (`matplot_utils`→`matplotUtils`, `seaborn_utils`→`seabornUtils`,
  `plotly_utils`→`plotlyUtils`, `ventas_csv`→`ventasCsv`, `inventario_csv`→`inventarioCsv`,
  `stats_analysis`→`statsAnalysis`, `deep_learning`→`deepLearning`), funciones y variables de
  `generadorDeDatos.py`, `statsAnalysis.py` y los `sources`/`visuals` (p. ej. `generar_ventas`→`generarVentas`,
  `ejecutar_analisis_estadistico`→`ejecutarAnalisisEstadistico`, claves `r2_adj`→`r2Adj`, `f_pvalue`→`fPvalue`).
- **Por qué:** unificar el estilo de nombres del proyecto.
- **Detalles:** se mantienen sin cambios las constantes en MAYÚSCULAS (`COL_*`, `BASE_DIR`), los nombres de
  las librerías y los encabezados de los CSV (`Stock_Actual`, `Unidades_Vendidas`, etc.).
- **Archivos:** todos los `.py`, `README.md`. Imports actualizados con `git mv`.
- **Resultado:** `statsAnalysis.py` da los mismos resultados (R² 0.662, 0 advertencias) y los gráficos
  de Matplotlib/Seaborn y el generador corren sin errores.
- **Corrección:** las claves del diccionario de métricas (`r2_adj`, `f_pvalue`) quedaron sin migrar en esta
  entrada; se pasaron a `r2Adj` y `fPvalue` en la entrada 6.

### 6. Centralización de constantes de columnas en `schema/`
- **Qué:** `schema/ventas.py` y `schema/inventario.py` ahora definen también las columnas derivadas
  (`COL_INGRESO`, `COL_MES`, `COL_PREDICCION`, `COL_REPOSICION_NECESARIA`) y los encabezados originales de los
  CSV (`CSV_*`). Todos los módulos las importan en lugar de repetir el texto.
- **Por qué:** cambiar un nombre de columna en un solo lugar, sin strings desactualizados que fallen en silencio.
- **Detalles:**
  - `statsAnalysis.py` ya no redefine los nombres: los toma de `Ventas`.
  - `generadorDeDatos.py` escribe los encabezados con `CSV_*` y agrega la raíz del proyecto al `sys.path`
    para poder importar `schema` al ejecutarse como script.
  - Claves de métricas: `r2_adj`→`r2Adj`, `f_pvalue`→`fPvalue`.
- **Archivos:** `schema/ventas.py`, `schema/inventario.py`, `sources/*`, `dataProcessing.py`,
  `visuals/seabornUtils.py`, `visuals/plotlyUtils.py`, `backend/statsAnalysis.py`.
- **Resultado:** el generador produce CSV idénticos (mismo md5), `statsAnalysis.py` da las mismas métricas y
  `main.py` genera los tres gráficos sin errores.

### 7. Módulo de Deep Learning (`tensorflow` / Keras)
- **Qué:** se implementó `entrenarModeloDeepLearning(dfVentas, epochs=50, batchSize=32)`, una red neuronal de
  regresión `Dense(32, relu) → Dense(16, relu) → Dense(1, lineal)` que estima `Unidades Vendidas` a partir de
  `Precio Unitario`, `Canal de Venta`, `Varietal` y `Estacion`. Retorna
  `(modelo, history, metricasDict, (xTest, yTest, yPred))`; `metricasDict` tiene `r2`, `mae` y `rmse`.
- **Por qué:** cumplir con la consigna de Aprendizaje Profundo del segundo parcial.
- **Detalles:**
  - Mismas variables que `statsAnalysis.py` (One-Hot con `drop_first=True, dtype=float`), con los nombres de
    columnas tomados de `schema/ventas.py`.
  - Split 80/20 (`random_state=42`); `StandardScaler` ajustado solo con train.
  - Adam (`learning_rate=0.01`), pérdida `mse`, métrica `mae`, `validation_split=0.2`, `verbose=0` y semilla
    fija con `keras.utils.set_random_seed(42)`.
  - La capa de entrada se declara con `keras.layers.Input(shape=...)` en lugar de `input_shape` en la primera
    `Dense`, porque Keras 3 desaconseja ese argumento (la arquitectura es la misma).
  - Bloque `__main__` con resumen de la red, métricas y una muestra de predicciones.
- **Archivos:** `backend/deepLearning.py` (nuevo contenido).
- **Resultado (test):** R² 0.873, MAE 17.27, RMSE 21.79 unidades. Supera al modelo OLS (R² 0.662 en todos los
  datos), probablemente porque la red capta la interacción Varietal × Estación.
- **Pendiente:** integrar `statsAnalysis` y `deepLearning` en `main.py`; graficar `history` (pérdida) y real vs.
  predicho; `requirements.txt` ya incluye `tensorflow` y `scikit-learn`, pero sin versiones fijas.

---

## 2026-10-17

### 8. Limpieza de ETL, estadística descriptiva (`scipy`) y evaluación justa OLS vs. DL
- **Qué:**
  - En `sources/ventasCsv.py` y `sources/inventarioCsv.py` se agregaron eliminación de duplicados (`drop_duplicates`), validación de rangos lógicos (unidades y precios $> 0$, stock $\ge 0$) y traducción de los meses al español (`Enero` a `Diciembre`).
  - En `schema/ventas.py` se agregó la constante `COL_PREDICCION_DL = "Prediccion_DL"`.
  - En `backend/statsAnalysis.py` se implementó `calcularEstadisticaDescriptiva(dfVentas)` con `numpy` y `scipy.stats` (resumen de media/mediana/desvío/rango, correlación de Pearson `pearsonr` entre precio y unidades, y test ANOVA de una vía `f_oneway` de unidades por estación). Además, `ejecutarAnalisisEstadistico` ahora evalúa también el OLS sobre el mismo split 80/20 (`random_state=42`) que usa la red neuronal, agregando `r2Test`, `maeTest`, `rmseTest` y `descriptiva` a `metricasDict`.
  - En `backend/deepLearning.py` se agregó la función auxiliar `agregarPrediccionesDL(dfVentas, modelo)` para generar la columna `Prediccion_DL` sobre el DataFrame completo reutilizando el `StandardScaler` ajustado en entrenamiento.
- **Por qué:** completar los criterios de ETL y Estadística de la rúbrica del Parcial 2, corregir los meses en inglés y permitir una comparación metodológicamente justa entre OLS y Deep Learning sobre el mismo conjunto de prueba.
- **Archivos:** `schema/ventas.py`, `sources/ventasCsv.py`, `sources/inventarioCsv.py`, `backend/statsAnalysis.py`, `backend/deepLearning.py`.
- **Resultado:**
  - Estadística descriptiva: correlación Precio–Unidades $r = -0.7324$ ($p \approx 3.06 \times 10^{-202}$); ANOVA por estación $F = 43.52$ ($p \approx 1.08 \times 10^{-26}$).
  - Comparación justa en test (20%, semilla 42): OLS obtiene $R^2 = 0.6739$, $\text{MAE} = 27.62$, $\text{RMSE} = 34.97$, mientras que la red neuronal logra $R^2 = 0.8734$, $\text{MAE} = 17.27$, $\text{RMSE} = 21.79$.
- **Pendiente:** unificar paleta visual y construir el reporte HTML único interactivo integrado en `main.py`.

### 9. Guía de estilo unificada, integración en `dataProcessing.py`/`main.py` y Dashboard HTML único
- **Qué:**
  - Se aplicó una paleta temática "Bodega / Vino" (`#722F37` bordó, `#A4133C` carmín, `#C59B27` dorado, `#C0392B` alerta, `#27AE60` stock OK, fondo `#FAF7F5`, fuente `Arial`) en `visuals/matplotUtils.py`, `visuals/seabornUtils.py` y `visuals/plotlyUtils.py`.
  - En `visuals/matplotUtils.py` se corrigió el subtítulo del heatmap a `(Suma de Unidades Vendidas)` y tanto `matplotUtils.py` como `seabornUtils.py` ahora exportan automáticamente sus PNG (`visuals/estacionalidadDeVentas.png` y `visuals/UnidadesXCanalyMes.png`) sin bloquear con `plt.show()` por defecto.
  - En `dataProcessing.py`, `procesarDatos()` ahora invoca `ejecutarAnalisisEstadistico` y `entrenarModeloDeepLearning` + `agregarPrediccionesDL`, enriqueciendo `dfVentas` y `dfConsolidado` con `Prediccion_Ventas` y `Prediccion_DL` y retornando las métricas y el historial de entrenamiento.
  - En `visuals/plotlyUtils.py` se implementó `generarDashboardHtml(...)`, que construye un único archivo autocontenido `visuals/reporte_interactivo.html` con: barra de filtros interactivos (Varietal, Estación, Canal), 6 tarjetas de KPIs, gráficos interactivos de Plotly (burbujas de inventario, comparativa Real vs. OLS vs. Deep Learning con filtro por varietal y curva de pérdida MSE), los 2 PNG de Matplotlib y Seaborn incrustados en Base64, tablas de Estadística Descriptiva / coeficientes OLS y un Simulador de Pronóstico de Demanda.
  - En `main.py` se conectó el flujo completo para generar los PNG y el dashboard HTML unificado.
  - Se fijaron las versiones exactas (`statsmodels==0.15.0`, `scipy==1.18.1`, `scikit-learn==1.9.1`, `tensorflow==2.21.0`) en `requirements.txt` y se eliminó `consignas_examen_parcial_nro_2.md:Zone.Identifier` agregando `*:Zone.Identifier` a `.gitignore`.
- **Por qué:** cumplir con el núcleo de la consigna 1 (integrar el backend analítico al dashboard aportando funcionalidad a la visualización) y contar con filtros, KPIs, guía de estilo y simulador para la documentación del Parcial 2.
- **Archivos:** `dataProcessing.py`, `main.py`, `visuals/matplotUtils.py`, `visuals/seabornUtils.py`, `visuals/plotlyUtils.py`, `requirements.txt`, `.gitignore`, `README.md`.
- **Resultado:** `main.py` ejecuta todo el pipeline de punta a punta sin advertencias y genera `visuals/reporte_interactivo.html` junto con las imágenes PNG actualizadas.
- **Pendiente:** redactar el documento de entrega del Parcial 2 (con diagrama Mermaid del pipeline, diccionario de datos, glosario de KPIs, capturas señalizadas y FAQ) y exportarlo a PDF.

### 10. Guía cronológica de estudio, documentación del Parcial 2 (`.md` + `.html` para PDF) y actualización de `.gitignore`
- **Qué:**
  - Se creó `EXPLICACION_FLUJO_PROYECTO.md` con la explicación cronológica paso a paso de todo el flujo de ejecución (`schema/` → `generadorDeDatos.py` → `main.py` → `dataProcessing.py` → `sources/` → `backend/` → `visuals/`).
  - Se crearon `DOCUMENTACION_PARCIAL2.md` y `DOCUMENTACION_PARCIAL2.html` (listo para exportar a PDF con `Ctrl + P`) cubriendo todas las secciones de la consigna 2 (`a. Portada`, `b. Proyecto`, `c. Documentación técnica`, `d. Gobierno de datos` y `e. Guía de usuario`).
  - Se actualizó `.gitignore` para excluir los archivos locales de examen y estudio (`consignas_examen_parcial_nro_2.md`, `analisis_estado_parcial2.md`, `EXPLICACION_FLUJO_PROYECTO.md`, `DOCUMENTACION_PARCIAL2.md`, `DOCUMENTACION_PARCIAL2.html`) del repositorio público.
- **Por qué:** completar el 50% de Documentación exigido en la rúbrica, facilitar la defensa oral del código y mantener limpio el repositorio de GitHub.
- **Archivos:** `.gitignore`, `CHANGELOG.md` (y archivos locales `EXPLICACION_FLUJO_PROYECTO.md`, `DOCUMENTACION_PARCIAL2.md`, `DOCUMENTACION_PARCIAL2.html`).
- **Resultado:** proyecto 100% completo en programación y documentación, listo para sincronizar con `origin/main`.

---

## 2026-10-23

### 11. Revisión final: correcciones de bugs, documentación, dependencias y des-versionado de archivos generados
- **Qué:**
  - **Bug corregido (`visuals/plotlyUtils.py`):** los botones "Solo Alerta Reposición (SI)" / "Solo Stock OK (NO)" del gráfico de burbujas estaban invertidos, porque Plotly crea los trazos en el orden de aparición de los datos (`NO`, `SI`) y los botones asumían `SI`, `NO`. Ahora la visibilidad se arma según el nombre real de cada trazo.
  - **Código muerto eliminado:** `graficarPlotlyBurbujas()` (no se usaba y sobrescribía el dashboard).
  - **Dashboard sin listas fijas:** los selects de filtros y del simulador (varietal, estación, canal, línea con su rango de precios real) se generan desde los datos; se reemplazó el texto fijo "1,200 transacciones"; el KPI "Precisión Modelos" pasó a "R² de los Modelos"; se quitaron afirmaciones no calculadas en los títulos de los gráficos ("sin sobreajuste", "captura la interacción…") y se aclaró que la comparativa usa promedios sobre todo el histórico. El título pasó a "WineLytics-V2".
  - **Regla de estaciones unificada:** `Ventas.obtenerEstacion()` y `Ventas.ORDEN_ESTACIONES` en `schema/ventas.py`; la usan `generadorDeDatos.py`, `ventasCsv.py`, `matplotUtils.py` y `plotlyUtils.py` (antes estaba duplicada).
  - **Datos automáticos:** `main.py` ahora tiene `asegurarDatos()`, que genera `data/*.csv` si faltan. `cargarVentas()` / `cargarInventario()` lanzan un `FileNotFoundError` con la instrucción de qué hacer.
  - **Documentación:** docstrings en `schema/`, `cargarVentas`, `cargarInventario`, `procesarDatos`, `main`, `generarDashboardHtml` y `_opcionesHtml`; docstring de `statsAnalysis.py` actualizado (ahora incluye estadística descriptiva); nombre `WineLytics-V2` en README, `CHANGELOG.md` y docstrings de `backend/`. Se corrigió `TienePredicciones` → `tienePredicciones` y se quitó el import sin usar de `pandas` en `seabornUtils.py`.
  - **README reescrito** según el estado real del proyecto: título `WineLytics-V2`, requisitos (Python ≥ 3.11, internet), generación automática de datos, flujo completo, ejecución de módulos por separado, resultados de referencia, notas importantes (el dashboard necesita internet para los gráficos de Plotly por el CDN; archivos generados no versionados; se abre el navegador) y estructura completa (`backend/`, `CHANGELOG.md`, `.agents/`).
  - **`requirements.txt`:** se eliminaron 13 paquetes sin uso (`dash`, `Flask`, `Werkzeug`, `Jinja2`, `MarkupSafe`, `itsdangerous`, `blinker`, `click`, `janus`, `retrying`, `nest-asyncio`, `importlib_metadata`, `zipp`). Se verificó que ninguno sea dependencia de lo que sí se usa (`pip check` y `pip install --dry-run` sin conflictos).
  - **Des-versionado:** `git rm --cached` de `data/ventas.csv`, `data/inventario.csv`, `visuals/estacionalidadDeVentas.png` y `visuals/UnidadesXCanalyMes.png`; los archivos siguen en disco y ya están cubiertos por `.gitignore` (se actualizaron sus comentarios).
- **Por qué:** cerrar la revisión final del proyecto (funcionamiento, documentación y consistencia) antes de la entrega, y evitar versionar archivos que se regeneran solos.
- **Archivos:** `main.py`, `dataProcessing.py`, `schema/ventas.py`, `schema/inventario.py`, `sources/generadorDeDatos.py`, `sources/ventasCsv.py`, `sources/inventarioCsv.py`, `backend/statsAnalysis.py`, `backend/deepLearning.py`, `visuals/matplotUtils.py`, `visuals/seabornUtils.py`, `visuals/plotlyUtils.py`, `README.md`, `requirements.txt`, `.gitignore`, `CHANGELOG.md`.
- **Resultado:** en una copia del repo **sin CSV ni PNG**, `main.py` generó los datos, corrió todo el pipeline y produjo el dashboard sin errores. Los CSV generados son idénticos a los anteriores (mismo contenido), las métricas no cambiaron (OLS R² test 0.6739; DL R² test 0.873) y el JavaScript del dashboard es válido. Los botones de reposición ahora muestran el subconjunto correcto.
- **Pendiente:** hacer `commit` y `push` para actualizar el repositorio remoto. Quedaron sin cambiar, a propósito: el `print(modelo.summary())` dentro del pipeline y los atributos `_scaler` / `_columnasX` que se agregan al modelo Keras.

### 12. Integración de ramas (`main` local y `origin/main`) y documento PDF de entrega
- **Qué:** se integró el historial divergente entre `main` local (commit con `ParcialN°2_FrancoCiccarelli_2do4ta.pdf`) y `origin/main` (commit de revisiones finales) mediante `git pull --rebase origin main`.
- **Por qué:** unificar los cambios finales de código/documentación con el archivo PDF de entrega del Parcial N°2 sin perder commits ni generar conflictos.
- **Archivos:** `ParcialN°2_FrancoCiccarelli_2do4ta.pdf`, `CHANGELOG.md`.
- **Resultado:** historial lineal y sincronizado con `origin/main`.

### 13. Auditoría final de documentación frente a las consignas del Examen Parcial N°2 y el estado actual del repositorio
- **Qué:**
  - Se verificó el cumplimiento punto por punto de `consignas_examen_parcial_nro_2.md` (Programación 50% + Documentación 50%).
  - Se regeneraron los artefactos locales (`data/*.csv`, `visuals/*.png` y `visuals/reporte_interactivo.html`) corriendo `main.py` con las últimas correcciones.
  - Se actualizaron `DOCUMENTACION_PARCIAL2.md`, `EXPLICACION_FLUJO_PROYECTO.md` y `analisis_estado_parcial2.md` para reflejar los cambios del commit `f8d2bc7`: función `asegurarDatos()` en `main.py`, regla centralizada `Ventas.obtenerEstacion()` y `Ventas.ORDEN_ESTACIONES` en `schema/ventas.py`, selectores dinámicos, título del KPI `R² de los Modelos (Test 20%)`, visibilidad dinámica de botones en `plotlyUtils.py`, aclaración del CDN de Plotly en la FAQ y nombre del estudiante (`Franco Ciccarelli`) en la portada.
- **Por qué:** asegurar que toda la documentación técnica, de usuario y de estudio coincida al 100% con el código actual del repositorio y con la rúbrica del examen.
- **Archivos:** `CHANGELOG.md` (y archivos locales `DOCUMENTACION_PARCIAL2.md`, `EXPLICACION_FLUJO_PROYECTO.md`, `analisis_estado_parcial2.md`).
- **Resultado:** documentación y código 100% alineados y verificados contra todas las consignas del Parcial N°2.

---

## 2026-10-24

### 14. Simplificación del código al estilo original del proyecto y rediseño de `ParcialN°2_FrancoCiccarelli_2do4ta.pdf` siguiendo el formato del Parcial 1
- **Qué:**
  - En la rama `simplificacionFinal`, se simplificaron todos los archivos de Python (`main.py`, `dataProcessing.py`, `schema/`, `sources/`, `backend/`, `visuals/`) y `README.md` para mantener el estilo original del Parcial 1 (comentarios `#?` / `#!`, funciones directas sin anotaciones de tipos complejas `typing` ni docstrings extensos), conservando exactamente la misma funcionalidad, datos y métricas.
  - En `visuals/plotlyUtils.py` se ajustó el ancho y la leyenda horizontal de los dos gráficos de la Sección 3 para que entren completos dentro de sus tarjetas sin recortarse.
  - Se rediseñaron `DOCUMENTACION_PARCIAL2.md`, `DOCUMENTACION_PARCIAL2.html` y `ParcialN°2_FrancoCiccarelli_2do4ta.pdf` tomando como base el diseño, tono de redacción, tipografía, portada, encabezados borravinos/azules, tablas oscuras (`#262626`) y capturas señalizadas con flechas/recuadros del documento del Parcial 1 (`ParcialNro1-FrancoCiccarelli2do4ta.pdf`), eliminando además la ruta y la hora del navegador en los bordes del PDF.
- **Por qué:** lograr que tanto el código como el PDF de entrega tengan una lectura natural y coherente con la entrega del Primer Parcial, cumpliendo todos los puntos exigidos en el Parcial 2.
- **Archivos:** `main.py`, `dataProcessing.py`, `schema/inventario.py`, `schema/ventas.py`, `sources/generadorDeDatos.py`, `sources/inventarioCsv.py`, `sources/ventasCsv.py`, `backend/statsAnalysis.py`, `backend/deepLearning.py`, `visuals/matplotUtils.py`, `visuals/seabornUtils.py`, `visuals/plotlyUtils.py`, `README.md`, `ParcialN°2_FrancoCiccarelli_2do4ta.pdf`, `.gitignore`, `CHANGELOG.md`.
- **Resultado:** el pipeline completo corre sin errores ni advertencias y el nuevo PDF de 17 páginas queda limpio y listo para presentar.
