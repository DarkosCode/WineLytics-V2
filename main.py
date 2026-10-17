from dataProcessing import procesarDatos
from visuals.matplotUtils import graficarEstacionalidadVarietales
from visuals.seabornUtils import graficarVentasXCanal
from visuals.plotlyUtils import generarDashboardHtml


def main():
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
