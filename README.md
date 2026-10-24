# WineLytics-V2 - Sistema de Análisis de Bodega

"WineLytics-V2" es el nombre ficticio del proyecto, el cual es una herramienta desarrollada en Python para el procesamiento de datos (ETL), el análisis estadístico, el aprendizaje profundo y la visualización del rendimiento comercial e inventario de una bodega.
Permite analizar la popularidad de los vinos, la estacionalidad de las ventas, los canales de distribución, pronosticar la demanda (comparando regresión lineal OLS contra una Red Neuronal) y alertar sobre la necesidad de reposición de stock en un **dashboard HTML interactivo** (`visuals/reporte_interactivo.html`).

## 🛠️ Requisitos Previos

Tener instalado:

- **Python 3.11 o superior** (requerido por las versiones de `pandas` y `numpy` de `requirements.txt`).
- **pip** (administrador de paquetes de Python).
- **Conexión a internet** para instalar los paquetes y para cargar la librería interactiva de Plotly desde su CDN al abrir el dashboard.

## 🚀 Guía de Instalación y Uso Paso a Paso

Seguir estos pasos sencillos para clonar, configurar y ejecutar el proyecto en tu máquina local:

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

Instala todas las librerías necesarias del proyecto utilizando el archivo `requirements.txt`:

```bash
pip install -r requirements.txt
```

### Paso 4: Generar los datos de prueba (Opcional)

El sistema utiliza archivos CSV simulados (`data/ventas.csv` y `data/inventario.csv`) con semilla fija (`42`) para que siempre se generen los mismos datos. Si no existen en la carpeta `data/`, `main.py` los crea automáticamente, pero también puedes generarlos manualmente corriendo:

```bash
python3 sources/generadorDeDatos.py
```

- **¿Qué hace esto?** Crea la carpeta `data/` en la raíz del proyecto y genera `inventario.csv` (stock actual de los 12 vinos) y `ventas.csv` (historial de 1200 transacciones de venta del año 2025).

### Paso 5: Ejecutar el análisis y el dashboard

Para correr todo el flujo de procesamiento, modelos y reportes, ejecuta el archivo orquestador:

```bash
python3 main.py
```

- **Flujo del programa al ejecutar `main.py`:**
  1. **Verificación de datos (`asegurarDatos`):** Si todavía no están creados los CSV en `data/`, los genera automáticamente.
  2. **Procesamiento (ETL) y Modelos (`dataProcessing.py`):**
     - Lee, limpia y estructura `ventas.csv` e `inventario.csv` (nulos, duplicados, rangos válidos, ingresos, meses en español, estaciones y alerta de reposición).
     - Ejecuta `backend/statsAnalysis.py`: calcula estadística descriptiva con `numpy` y `scipy` (media, mediana, desvío, correlación de Pearson y ANOVA por estación) y ajusta una regresión lineal múltiple OLS con `statsmodels`, sumando la columna `Prediccion_Ventas`.
     - Ejecuta `backend/deepLearning.py`: entrena una red neuronal densa (`Dense 32 → 16 → 1`) con `Keras / TensorFlow` y `scikit-learn`, sumando la columna `Prediccion_DL`.
     - Agrupa y cruza (`merge inner`) las ventas con el stock físico.
  3. **Gráficos de Matplotlib y Seaborn:** Genera y guarda en disco `visuals/estacionalidadDeVentas.png` (mapa de calor por varietal y estación) y `visuals/UnidadesXCanalyMes.png` (barras de ventas mensuales por canal).
  4. **Dashboard Interactivo (`visuals/reporte_interactivo.html`):** Arma un único reporte HTML que reúne la barra de filtros interactivos, las 6 tarjetas de KPIs, los gráficos interactivos de Plotly, los dos gráficos de Matplotlib y Seaborn incrustados, las tablas estadísticas y un Simulador de Pronóstico de Demanda, abriéndolo en el navegador.

---

## 📁 Estructura del Proyecto

- **`data/`:** Contiene los archivos de origen de datos generados (`ventas.csv` e `inventario.csv`). _Se crea dinámicamente al ejecutar el proyecto_.
- **`schema/`:** Define las constantes de columnas (`inventario.py` y `ventas.py`) y la función `obtenerEstacion()` para evitar errores de nombres y no repetir código.
- **`sources/`:** Módulos encargados de leer, limpiar y enriquecer los datos de entrada (`ventasCsv.py` e `inventarioCsv.py`), además del generador de datos sintéticos (`generadorDeDatos.py`).
- **`backend/`:** Análisis estadístico y modelos predictivos:
  - `statsAnalysis.py`: estadística descriptiva (`numpy` / `scipy.stats`) y regresión lineal OLS (`statsmodels`).
  - `deepLearning.py`: red neuronal densa (`Keras / TensorFlow` y `scikit-learn`) para predecir las unidades vendidas.
- **`visuals/`:** Contiene los archivos generadores de gráficos (`matplotUtils.py`, `seabornUtils.py`, `plotlyUtils.py`). Aquí también se guardan los PNG y el reporte interactivo HTML.
- **`dataProcessing.py`:** Módulo ETL principal que procesa los CSV, ejecuta los modelos del backend y consolida la información.
- **`main.py`:** Orquestador principal del proyecto.
- **`CHANGELOG.md`:** Registro cronológico de los cambios realizados en el proyecto.
