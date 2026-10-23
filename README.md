# WineLytics-V2 - Sistema de Análisis de Bodega

**WineLytics-V2** es una herramienta desarrollada en Python (nombre ficticio) para el procesamiento de datos (ETL), el análisis estadístico, el aprendizaje profundo y la visualización del rendimiento comercial e inventario de una bodega.

Permite analizar la popularidad de los vinos, la estacionalidad de las ventas, los canales de distribución, pronosticar la demanda (regresión OLS vs. red neuronal) y alertar sobre la necesidad de reposición de stock. El resultado final es un **dashboard HTML interactivo** (`visuals/reporte_interactivo.html`).

## 🛠️ Requisitos Previos

- **Python 3.11 o superior** (requerido por las versiones de `pandas` y `numpy` de `requirements.txt`). El proyecto fue probado con Python 3.12.
- **pip** (administrador de paquetes de Python).
- **Conexión a internet** al instalar las dependencias y, luego, para ver los gráficos interactivos de Plotly del dashboard (ver [Notas importantes](#-notas-importantes)).
- Espacio en disco: `tensorflow` es una dependencia pesada (varios cientos de MB).

## 🚀 Guía de Instalación y Uso Paso a Paso

### Paso 1: Clonar el repositorio

Abre una terminal y clona el proyecto desde GitHub:

```bash
git clone https://github.com/DarkosCode/WineLytics-V2.git
cd WineLytics-V2
```

### Paso 2: Configurar el entorno virtual (Recomendado)

Para mantener limpias tus librerías y evitar conflictos, crea y activa un entorno virtual de Python:

- **En Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- **En Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\Activate.ps1
  ```

### Paso 3: Instalar las dependencias

Instala todas las librerías necesarias del proyecto utilizando el archivo `requirements.txt` (puede tardar unos minutos por `tensorflow`):

```bash
pip install -r requirements.txt
```

### Paso 4: Ejecutar el proyecto

Para correr toda la suite (datos, modelos, gráficos y dashboard), ejecuta el archivo orquestador:

```bash
python3 main.py
```

> **Primera ejecución:** los archivos `data/ventas.csv` e `data/inventario.csv` **no vienen en el repositorio** (son datos sintéticos que se generan). Si no existen, `main.py` los crea automáticamente. Al usar una semilla fija (42), siempre se generan **exactamente los mismos datos**.
>
> Si prefieres generarlos a mano (o regenerarlos), ejecuta `python3 sources/generadorDeDatos.py`. Esto crea la carpeta `data/` con `inventario.csv` (stock actual) y `ventas.csv` (1200 transacciones de venta de 2025).

- **Flujo del programa al ejecutar `main.py`:**
  0. **Datos:** si faltan los CSV de `data/`, se generan con `sources/generadorDeDatos.py`.
  1. **Procesamiento (ETL) + Modelos Analíticos (`dataProcessing.py`):**
     - Lee, limpia y transforma `ventas.csv` e `inventario.csv` (nulos, duplicados, rangos válidos, meses en español, estaciones, ingresos y alerta de reposición).
     - Ejecuta `backend/statsAnalysis.py`: estadística descriptiva con `numpy`/`scipy` (media, mediana, desvío, correlación de Pearson y ANOVA por estación) y regresión OLS con `statsmodels`, agregando `Prediccion_Ventas`. Imprime en consola el resumen completo del modelo.
     - Ejecuta `backend/deepLearning.py`: red neuronal `Dense 32 → 16 → 1` con `Keras`/`TensorFlow`, agregando `Prediccion_DL`. Ambos modelos se evalúan sobre el mismo conjunto de prueba (80/20, semilla 42).
     - Consolida inventario, ventas reales y pronósticos por Varietal y Línea.
  2. **Gráficos estáticos (`Matplotlib` y `Seaborn`):** guarda automáticamente `visuals/estacionalidadDeVentas.png` (mapa de calor de unidades por varietal y estación) y `visuals/UnidadesXCanalyMes.png` (barras de ventas mensuales por canal), sin abrir ventanas emergentes.
  3. **Dashboard HTML (`visuals/reporte_interactivo.html`):** genera y abre en el navegador un único dashboard con: **barra de filtros interactivos** (varietal, estación y canal), **tarjetas de KPIs**, **gráficos interactivos de Plotly** (inventario vs. ventas con filtro de alerta de reposición, comparativa Real vs. OLS vs. Deep Learning y curva de aprendizaje MSE), los **gráficos de Matplotlib y Seaborn incrustados en Base64**, las tablas de **Estadística Descriptiva / OLS** y un **Simulador de Demanda por Transacción**.

### Ejecución de módulos por separado (opcional)

```bash
python3 sources/generadorDeDatos.py   # genera/regenera data/*.csv
python3 backend/statsAnalysis.py      # estadística descriptiva + OLS (imprime métricas)
python3 backend/deepLearning.py       # entrena la red neuronal (imprime métricas)
```

### Resultados de referencia (datos con semilla 42)

| Modelo | R² (test 20%) | MAE | RMSE |
|---|---|---|---|
| Regresión OLS (`statsmodels`) | 0.674 | 27.62 u. | 34.97 u. |
| Red neuronal (`Keras`) | 0.873 | 17.27 u. | 21.79 u. |

La red neuronal supera al OLS porque capta la interacción Varietal × Estación (p. ej. Torrontés en verano, tintos en invierno), que el modelo lineal no incluye.

---

## ⚠️ Notas importantes

- **El dashboard necesita internet para los gráficos de Plotly.** El archivo HTML carga la librería JavaScript de Plotly desde su CDN oficial. Sin conexión, los gráficos interactivos no se dibujan. Todo lo demás (KPIs, tablas, imágenes de Matplotlib/Seaborn, filtros y simulador) está incrustado en el propio archivo y funciona sin internet.
- **Archivos generados (no versionados):** `data/*.csv`, `visuals/*.png` y `visuals/reporte_interactivo.html` están en `.gitignore`: se vuelven a crear cada vez que se ejecuta el proyecto.
- **Se abre el navegador automáticamente** al final de `main.py`. Si estás en un servidor sin interfaz gráfica, abre manualmente el archivo `visuals/reporte_interactivo.html`.
- **TensorFlow** puede imprimir mensajes informativos (oneDNN / CUDA) en la consola; no son errores. El proyecto no requiere GPU.
- La ejecución completa tarda entre 30 y 60 segundos, principalmente por el entrenamiento de la red neuronal.

## 📁 Estructura del Proyecto

- **`data/`:** Datos de origen (`ventas.csv` e `inventario.csv`). _Se generan al ejecutar el proyecto; no están en el repositorio_.
- **`schema/`:** Define las constantes de columnas (`Ventas`, `Inventario`) y la regla de estaciones del año, para evitar errores de nombres y duplicación de lógica.
- **`sources/`:** Módulos que leen, limpian (nulos, duplicados, validación de rangos) y enriquecen los datos de entrada (ingresos, meses en español y estaciones) — `ventasCsv.py` e `inventarioCsv.py` — además del generador de datos sintéticos (`generadorDeDatos.py`).
- **`backend/`:** Análisis estadístico y modelos predictivos integrados al flujo principal:
  - `statsAnalysis.py`: estadística descriptiva y pruebas de hipótesis (`numpy` / `scipy.stats`) y regresión lineal OLS (`statsmodels`) evaluada in-sample y en el conjunto de prueba (80/20).
  - `deepLearning.py`: red neuronal (`Keras` / `TensorFlow`, `Dense 32 → 16 → 1`) que estima las unidades vendidas, con métricas (`R²`, `MAE`, `RMSE`) sobre el mismo conjunto de prueba, y `agregarPrediccionesDL()` para generar `Prediccion_DL`.
- **`visuals/`:** Módulos de visualización con paleta temática "Bodega / Vino" (`matplotUtils.py`, `seabornUtils.py`, `plotlyUtils.py`) y sus salidas (`estacionalidadDeVentas.png`, `UnidadesXCanalyMes.png` y el dashboard `reporte_interactivo.html`).
- **`dataProcessing.py`:** Módulo ETL y analítico principal: ejecuta la limpieza, los modelos de `backend/` y la consolidación de datos.
- **`main.py`:** Orquestador principal: asegura los datos, ejecuta todo el pipeline y construye el dashboard interactivo.
- **`requirements.txt`:** Dependencias del proyecto (versiones fijadas).
- **`CHANGELOG.md`:** Registro cronológico de los cambios realizados en el proyecto.
- **`.agents/`:** Reglas del proyecto para asistentes de IA (`AGENTS.md`).
