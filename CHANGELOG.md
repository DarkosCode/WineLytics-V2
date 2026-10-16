# Registro de cambios — WineLytics

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
