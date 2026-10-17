import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from schema.ventas import Ventas

#? Paleta unificada "Bodega / Vino" (Guía de estilo del proyecto)
COLOR_BORDO = "#722F37"
COLOR_DORADO = "#C59B27"
COLOR_TEXTO = "#2C3E50"
COLOR_FONDO = "#FAF7F5"

ORDEN_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]


def graficarVentasXCanal(df, mostrarVentana: bool = False):
    """Genera y guarda el gráfico de barras con Seaborn de unidades vendidas por mes y canal.

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

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)

    mesesPresentes = [m for m in ORDEN_MESES if m in df[Ventas.COL_MES].unique()]
    if not mesesPresentes:
        mesesPresentes = list(df.sort_values(by=Ventas.COL_FECHA)[Ventas.COL_MES].unique())

    sns.barplot(
        data=df,
        x=Ventas.COL_MES,
        y=Ventas.COL_UNIDADESV,
        hue=Ventas.COL_CANAL,
        order=mesesPresentes,
        estimator=sum,
        errorbar=None,
        palette={"Mercado Interno": COLOR_BORDO, "Exportación": COLOR_DORADO},
        ax=ax,
    )

    ax.set_title(
        "Unidades Vendidas por Mes y Canal de Venta",
        fontsize=14, fontweight="bold", pad=15, color=COLOR_BORDO
    )
    ax.set_xlabel("Mes", fontsize=12, fontweight="semibold", color=COLOR_TEXTO)
    ax.set_ylabel("Total Unidades Vendidas", fontsize=12, fontweight="semibold", color=COLOR_TEXTO)
    ax.tick_params(axis="x", rotation=30, colors=COLOR_TEXTO)
    ax.tick_params(axis="y", colors=COLOR_TEXTO)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    ax.legend(title="Canal de Venta", bbox_to_anchor=(1.02, 1), loc="upper left", frameon=True)

    plt.tight_layout()

    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaPng = os.path.join(baseDir, "visuals", "UnidadesXCanalyMes.png")
    fig.savefig(rutaPng, dpi=150, bbox_inches="tight", facecolor=COLOR_FONDO)

    if mostrarVentana:
        plt.show()
    else:
        plt.close(fig)

    return rutaPng
