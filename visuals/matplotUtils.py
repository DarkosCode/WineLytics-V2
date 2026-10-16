import numpy as np
import matplotlib.pyplot as plt
from schema.ventas import Ventas

def graficarEstacionalidadVarietales(df):
    #? Genera un mapa de calor (heatmap) estático con Matplotlib que muestra la relación entre las unidades vendidas por varietal y la estación del año.

    #?Check de si se crearon los datos o no antes de ejecutar los graficos
    if df is None or df.empty:
        print("El DataFrame está vacío o no existe.")
        return

    # 1. Agrupar para obtener el total de unidades vendidas por Varietal y Estacion
    pivotDf = (
        df.groupby([Ventas.COL_VARIETAL, Ventas.COL_ESTACION])[Ventas.COL_UNIDADESV]
        .sum()
        .unstack(fill_value=0)
    )

    # 2. Reordenar las columnas en orden 'cronológico' de las estaciones
    ordenEstaciones = ['Verano', 'Otoño', 'Invierno', 'Primavera']
    
    columnasExistentes = []
    for est in ordenEstaciones:
        if est in pivotDf.columns:
            columnasExistentes.append(est)
    
    pivotDf = pivotDf.reindex(columns=columnasExistentes)

    fig, ax = plt.subplots(figsize=(10, 6))
    
    # paleta de colores
    im = ax.imshow(pivotDf.values, cmap='PuRd', aspect='auto')

    # etiquetas de los ejes
    ax.set_xticks(np.arange(len(pivotDf.columns)))
    ax.set_yticks(np.arange(len(pivotDf.index)))
    ax.set_xticklabels(pivotDf.columns, fontsize=11)
    ax.set_yticklabels(pivotDf.index, fontsize=11)

    # Agregar la colorbar a la derecha
    cbar = ax.figure.colorbar(im, ax=ax, pad=0.04)
    cbar.ax.set_ylabel("Total Unidades Vendidas", rotation=-90, va="bottom", fontsize=11, labelpad=10)

    # Añadir los numeros dentro de cada celda
    for i in range(len(pivotDf.index)):
        for j in range(len(pivotDf.columns)):
            val = pivotDf.values[i, j]
            ax.text(
                j, i, str(val), 
                ha="center", va="center", 
                color="black", fontsize=10
            )

    ax.set_title(
        "Estacionalidad de Ventas de Vino por Varietal\n(Frecuencia de Unidades Vendidas)", 
        fontsize=14, fontweight='bold', pad=20, color='#333333'
    )
    ax.set_xlabel("Estación del Año", fontsize=12, labelpad=10, fontweight='semibold')
    ax.set_ylabel("Varietal de Vino", fontsize=12, labelpad=10, fontweight='semibold')


    plt.tight_layout()
    plt.show()
