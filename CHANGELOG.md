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
