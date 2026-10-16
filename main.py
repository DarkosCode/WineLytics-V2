from dataProcessing import procesarDatos
from visuals.matplotUtils import graficarEstacionalidadVarietales
from visuals.seabornUtils import graficarVentasXCanal
from visuals.plotlyUtils import graficarPlotlyBurbujas

def main():
    datos = procesarDatos()
    
    graficarEstacionalidadVarietales(datos["ventas"])
    graficarVentasXCanal(datos["ventas"])
    graficarPlotlyBurbujas(datos["consolidado"])

if __name__ == "__main__":
    main()
