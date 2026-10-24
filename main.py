import os
from dataProcessing import procesarDatos
from sources.generadorDeDatos import main as generarDatos, DATA_DIR
from visuals.matplotUtils import graficarEstacionalidadVarietales
from visuals.seabornUtils import graficarVentasXCanal
from visuals.plotlyUtils import generarDashboardHtml

def asegurarDatos():
    #? Si todavía no están creados los CSV en data/, los generamos automáticamente con la semilla 42
    rutaVentas = os.path.join(DATA_DIR, "ventas.csv")
    rutaInventario = os.path.join(DATA_DIR, "inventario.csv")

    if not os.path.exists(rutaVentas) or not os.path.exists(rutaInventario):
        print("No se encontraron los CSV en data/. Generándolos automáticamente...")
        generarDatos()

def main():
    #? 0. Verificamos que existan los archivos de datos antes de arrancar
    asegurarDatos()

    #? 1. Procesamos los datos (ETL) y corremos los modelos de Estadística y Deep Learning
    datos = procesarDatos()

    #? 2. Generamos y guardamos los gráficos de Matplotlib y Seaborn en visuals/
    rutaHeatmap = graficarEstacionalidadVarietales(datos["ventas"], mostrarVentana=False)
    rutaBarras = graficarVentasXCanal(datos["ventas"], mostrarVentana=False)

    #? 3. Armamos el dashboard HTML interactivo con todos los gráficos, KPIs y el simulador
    generarDashboardHtml(
        datos=datos,
        rutaHeatmapPng=rutaHeatmap,
        rutaBarrasPng=rutaBarras,
        abrirNavegador=True
    )

if __name__ == "__main__":
    main()
