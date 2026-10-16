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
git clone https://github.com/tu-usuario/WineLytics-V2.git
cd WineLytics-V2
```

_(Reemplaza la URL con la dirección real)._

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
  1. **Procesamiento (ETL):** El sistema lee, limpia, calcula los ingresos de ventas, determina las estaciones y cruza las ventas con el stock físico.
  2. **Gráfico 1 (Matplotlib):** Se abrirá un mapa de calor que analiza las ventas de cada varietal por estación del año. **Debes cerrar esta ventana de gráfico para continuar.**
  3. **Gráfico 2 (Seaborn):** Se abrirá un gráfico de barras comparando las ventas mensuales en el Mercado Interno vs. Exportación. **Debes cerrar esta ventana para continuar.**
  4. **Gráfico 3 (Plotly):** Generará un archivo HTML interactivo en `visuals/reporte_interactivo.html` y abrirá una pestaña en tu navegador predeterminado para que puedas interactuar con el gráfico de burbujas (hacer zoom, filtrar por leyenda, ver detalles al pasar el cursor).

---

## 📁 Estructura del Proyecto

- **`data/`:** Contiene los archivos de origen de datos generados (`ventas.csv` e `inventario.csv`). _Creado dinámicamente_.
- **`schema/`:** Define las constantes y estructuras de columnas para evitar errores de nombres.
- **`sources/`:** Módulos encargados de leer, limpiar y enriquecer los datos de entrada, además del generador de datos sintéticos.
- **`backend/`:** Análisis estadístico y modelos predictivos. `statsAnalysis.py` ajusta una regresión lineal OLS (`statsmodels`) sobre las ventas y devuelve predicciones y métricas (R², AIC, BIC, coeficientes); se ejecuta de forma independiente con `python3 backend/statsAnalysis.py`. `deepLearning.py` entrena una red neuronal (Keras / TensorFlow, `Dense 32 → 16 → 1`) que estima las unidades vendidas y devuelve R², MAE y RMSE sobre el conjunto de prueba; se ejecuta con `python3 backend/deepLearning.py`. Ninguno de los dos módulos está integrado todavía en `main.py`.
- **`.agents/`:** Reglas del proyecto para asistentes de IA (`AGENTS.md`).
- **`visuals/`:** Contiene los archivos generadores de gráficos (`matplotUtils.py`, `seabornUtils.py`, `plotlyUtils.py`). Aquí también se creará el reporte interactivo HTML.
- **`dataProcessing.py`:** Módulo ETL principal que procesa, agrupa y consolida la información para que sea consumida por los reportes.
- **`main.py`:** Orquestador principal del proyecto.
