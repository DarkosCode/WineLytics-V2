# WineLytics - Sistema de Análisis de Bodega

"WineLytics" solo es el nombre ficticio del proyecto, el cual es una herramienta desarrollada en Python para el procesamiento de datos (ETL) y la visualización del rendimiento comercial e inventario de una bodega.
Permite analizar la popularidad de los vinos, la estacionalidad de las ventas, los canales de distribución y alertar sobre la necesidad de reposición de stock.

## 🛠️ Requisitos Previos

tener instalado:

- **Python 3.11 o superior** (requerido por las versiones de `pandas` y `numpy` de `requirements.txt`)
- **pip** (administrador de paquetes de Python)

## 🚀 Guía de Instalación y Uso Paso a Paso

Seguir estos pasos sencillos para clonar, configurar y ejecutar el proyecto en tu máquina local:

### Paso 1: Clonar el repositorio

Abre una terminal y clona el proyecto desde tu repositorio de GitHub:

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

Instala todas las librerías necesarias del proyecto utilizando el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Paso 4: Generar los datos de prueba (Ventas e Inventario)

El sistema utiliza archivos CSV simulados para los reportes. Genera estos datos corriendo el script de simulación:

```bash
python3 sources/generadorDeDatos.py
```

- **¿Qué hace esto?** Creará automáticamente una carpeta llamada `data/` en la raíz del proyecto y dentro generará dos archivos: `inventario.csv` (stock actual) y `ventas.csv` (historial de transacciones de vino).

### Paso 5: Ejecutar el análisis y visualización

Para correr toda la suite de reportes y procesamiento, simplemente ejecuta el archivo orquestador:

```bash
python3 main.py
```

- **Flujo del programa al ejecutar `main.py`:**
  1. **Procesamiento (ETL) + Modelos Analíticos (`dataProcessing.py`):**
     - Lee, limpia y transforma `ventas.csv` e `inventario.csv`.
     - Ejecuta `backend/statsAnalysis.py` (estadística descriptiva con `numpy`/`scipy` y regresión OLS con `statsmodels`, agregando `Prediccion_Ventas`).
     - Ejecuta `backend/deepLearning.py` (red neuronal `Dense 32 → 16 → 1` con `Keras`/`TensorFlow`, agregando `Prediccion_DL`).
     - Consolida inventario, ventas reales y pronósticos por Varietal y Línea.
  2. **Gráficos Estáticos con Estilo Unificado (`Matplotlib` y `Seaborn`):**
     - Guarda automáticamente `visuals/estacionalidadDeVentas.png` (mapa de calor de unidades por varietal y estación) y `visuals/UnidadesXCanalyMes.png` (barras de ventas mensuales por canal en español) sin bloquear la ejecución con ventanas emergentes.
  3. **Dashboard HTML Unificado (`visuals/reporte_interactivo.html`):**
     - Genera y abre en el navegador un único dashboard autocontenido que incluye: **barra de filtros interactivos**, **tarjetas de KPIs**, **gráficos interactivos de Plotly** (inventario vs. ventas, comparativa Real vs. OLS vs. Deep Learning y curva de aprendizaje MSE), los **gráficos de Matplotlib y Seaborn incrustados en Base64**, las tablas de **Estadística Descriptiva / OLS** y un **Simulador de Demanda por Transacción**.

---

## 📁 Estructura del Proyecto

- **`data/`:** Contiene los archivos de origen de datos generados (`ventas.csv` e `inventario.csv`). _Creado dinámicamente_.
- **`schema/`:** Define las constantes y estructuras de columnas para evitar errores de nombres.
- **`sources/`:** Módulos encargados de leer, limpiar (nulos, duplicados, validación de rangos) y enriquecer los datos de entrada (ingresos, meses en español y estaciones), además del generador de datos sintéticos.
- **`backend/`:** Análisis estadístico y modelos predictivos integrados al flujo principal:
  - `statsAnalysis.py`: calcula estadística descriptiva y pruebas de hipótesis (`numpy` / `scipy.stats`: media, mediana, desvío, correlación de Pearson y ANOVA por estación) y ajusta una regresión lineal OLS (`statsmodels`) evaluada tanto in-sample como en el conjunto de prueba (80/20). Se puede ejecutar de forma independiente con `python3 backend/statsAnalysis.py`.
  - `deepLearning.py`: entrena una red neuronal (`Keras` / `TensorFlow`, `Dense 32 → 16 → 1`) que estima las unidades vendidas, devuelve métricas sobre el mismo conjunto de prueba (`R²`, `MAE`, `RMSE`) y genera `Prediccion_DL` con `agregarPrediccionesDL()`. Se puede ejecutar de forma independiente con `python3 backend/deepLearning.py`.
- **`.agents/`:** Reglas del proyecto para asistentes de IA (`AGENTS.md`).
- **`visuals/`:** Módulos de visualización con paleta temática "Bodega / Vino" (`matplotUtils.py`, `seabornUtils.py`, `plotlyUtils.py`) y salidas exportadas (`estacionalidadDeVentas.png`, `UnidadesXCanalyMes.png` y el dashboard unificado `reporte_interactivo.html`).
- **`dataProcessing.py`:** Módulo ETL y analítico principal que ejecuta la limpieza, los modelos de `backend/` y la consolidación de datos.
- **`main.py`:** Orquestador principal que ejecuta todo el pipeline y construye el dashboard interactivo.
