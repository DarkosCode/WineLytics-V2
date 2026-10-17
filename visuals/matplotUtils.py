import os
import numpy as np
import matplotlib.pyplot as plt
from schema.ventas import Ventas

#? Paleta unificada "Bodega / Vino" (Guía de estilo del proyecto)
COLOR_BORDO = "#722F37"
COLOR_TEXTO = "#2C3E50"
COLOR_FONDO = "#FAF7F5"


def graficarEstacionalidadVarietales(df, mostrarVentana: bool = False):
    """Genera y guarda el mapa de calor (heatmap) con Matplotlib de unidades vendidas por varietal y estación.

    Args:
        df: DataFrame de ventas enriquecido.
        mostrarVentana: Si es True, abre la ventana interactiva de Matplotlib (`plt.show()`).

    Returns:
        Ruta absoluta del archivo PNG generado, o None si el DataFrame está vacío.
    """
    #? Check de si se crearon los datos o no antes de ejecutar los graficos
    if df is None or df.empty:
        print("El DataFrame está vacío o no existe.")
        return None

    # 1. Agrupar para obtener el total de unidades vendidas por Varietal y Estacion
    pivotDf = (
        df.groupby([Ventas.COL_VARIETAL, Ventas.COL_ESTACION])[Ventas.COL_UNIDADESV]
        .sum()
        .unstack(fill_value=0)
    )

    # 2. Reordenar las columnas en orden 'cronológico' de las estaciones
    ordenEstaciones = ['Verano', 'Otoño', 'Invierno', 'Primavera']
    columnasExistentes = [est for est in ordenEstaciones if est in pivotDf.columns]
    pivotDf = pivotDf.reindex(columns=columnasExistentes)

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)

    #? Paleta cálida de bodega (PuRd)
    im = ax.imshow(pivotDf.values, cmap='PuRd', aspect='auto')

    # Etiquetas de los ejes
    ax.set_xticks(np.arange(len(pivotDf.columns)))
    ax.set_yticks(np.arange(len(pivotDf.index)))
    ax.set_xticklabels(pivotDf.columns, fontsize=11, color=COLOR_TEXTO)
    ax.set_yticklabels(pivotDf.index, fontsize=11, color=COLOR_TEXTO)

    # Agregar la colorbar a la derecha
    cbar = ax.figure.colorbar(im, ax=ax, pad=0.04)
    cbar.ax.set_ylabel("Total Unidades Vendidas", rotation=-90, va="bottom", fontsize=11, labelpad=10, color=COLOR_TEXTO)

    #? Añadir los números dentro de cada celda (texto blanco en celdas oscuras para buen contraste)
    umbralContraste = (pivotDf.values.max() + pivotDf.values.min()) / 2.0
    for i in range(len(pivotDf.index)):
        for j in range(len(pivotDf.columns)):
            val = pivotDf.values[i, j]
            colorTextoCelda = "white" if val > umbralContraste else COLOR_TEXTO
            ax.text(
                j, i, f"{val:,}",
                ha="center", va="center",
                color=colorTextoCelda, fontsize=10, fontweight="bold"
            )

    ax.set_title(
        "Estacionalidad de Ventas de Vino por Varietal\n(Suma de Unidades Vendidas)",
        fontsize=14, fontweight='bold', pad=20, color=COLOR_BORDO
    )
    ax.set_xlabel("Estación del Año", fontsize=12, labelpad=10, fontweight='semibold', color=COLOR_TEXTO)
    ax.set_ylabel("Varietal de Vino", fontsize=12, labelpad=10, fontweight='semibold', color=COLOR_TEXTO)

    plt.tight_layout()

    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaPng = os.path.join(baseDir, "visuals", "estacionalidadDeVentas.png")
    fig.savefig(rutaPng, dpi=150, bbox_inches="tight", facecolor=COLOR_FONDO)

    if mostrarVentana:
        plt.show()
    else:
        plt.close(fig)

    return rutaPng
