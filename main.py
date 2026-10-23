import os

from dataProcessing import procesarDatos
from sources.generadorDeDatos import main as generarDatos, DATA_DIR
from visuals.matplotUtils import graficarEstacionalidadVarietales
from visuals.seabornUtils import graficarVentasXCanal
from visuals.plotlyUtils import generarDashboardHtml


def asegurarDatos():
    """Genera los CSV de data/ si todavía no existen (están excluidos de git).

    La generación es reproducible (semilla 42): siempre produce los mismos datos.
    """
    archivos = ["ventas.csv", "inventario.csv"]
    if not all(os.path.exists(os.path.join(DATA_DIR, archivo)) for archivo in archivos):
        print("No se encontraron los CSV en data/. Generándolos automáticamente...")
        generarDatos()


def main():
    """Orquesta todo el proyecto: datos -> ETL y modelos -> gráficos -> dashboard HTML."""
    #? 0. Si es la primera ejecución (data/ vacío), generar los datos sintéticos
    asegurarDatos()

    #? 1. Ejecutar ETL + Análisis Estadístico (OLS / SciPy) + Aprendizaje Profundo (Keras / TensorFlow)
    datos = procesarDatos()

    #? 2. Generar y guardar las visualizaciones de Matplotlib y Seaborn con paleta unificada
    rutaHeatmap = graficarEstacionalidadVarietales(datos["ventas"], mostrarVentana=False)
    rutaBarras = graficarVentasXCanal(datos["ventas"], mostrarVentana=False)

    #? 3. Construir y abrir el Dashboard HTML único con KPIs, filtros, gráficos y simulador
    generarDashboardHtml(
        datos=datos,
        rutaHeatmapPng=rutaHeatmap,
        rutaBarrasPng=rutaBarras,
        abrirNavegador=True,
    )


if __name__ == "__main__":
    main()
