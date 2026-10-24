import os
import seaborn as sns
import matplotlib.pyplot as plt
from schema.ventas import Ventas

#? Colores de la guía de estilo del proyecto ("Bodega / Vino")
COLOR_BORDO = "#722F37"
COLOR_DORADO = "#C59B27"
COLOR_TEXTO = "#2C3E50"
COLOR_FONDO = "#FAF7F5"

ORDEN_MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

def graficarVentasXCanal(df, mostrarVentana=False):
    #? Genera el gráfico de barras agrupadas con Seaborn comparando las ventas por mes y canal

    #? Check de si se crearon los datos o no antes de ejecutar los graficos
    if df is None or df.empty:
        print("El DataFrame está vacío o no existe.")
        return None

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=COLOR_FONDO)
    ax.set_facecolor(COLOR_FONDO)

    mesesPresentes = []
    mesesEnDf = df[Ventas.COL_MES].unique()
    for m in ORDEN_MESES:
        if m in mesesEnDf:
            mesesPresentes.append(m)

    sns.barplot(
        data=df,
        x=Ventas.COL_MES,
        y=Ventas.COL_UNIDADESV,
        hue=Ventas.COL_CANAL,
        order=mesesPresentes,
        estimator=sum,
        errorbar=None,
        palette={"Mercado Interno": COLOR_BORDO, "Exportación": COLOR_DORADO},
        ax=ax
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

    # Guardar imagen PNG en la carpeta visuals/ para sumarla al dashboard
    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaPng = os.path.join(baseDir, "visuals", "UnidadesXCanalyMes.png")
    fig.savefig(rutaPng, dpi=150, bbox_inches="tight", facecolor=COLOR_FONDO)

    if mostrarVentana:
        plt.show()
    else:
        plt.close(fig)

    return rutaPng
