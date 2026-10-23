import base64
import json
import os
import webbrowser
from html import escape
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from schema.inventario import Inventario
from schema.ventas import Ventas

#? Paleta unificada "Bodega / Vino" (Guía de estilo del proyecto)
COLOR_BORDO = "#722F37"
COLOR_CARMIN = "#A4133C"
COLOR_DORADO = "#C59B27"
COLOR_ALERTA = "#C0392B"
COLOR_OK = "#27AE60"
COLOR_TEXTO = "#2C3E50"
COLOR_FONDO = "#FAF7F5"


def _imagenABase64(rutaImagen: str) -> str:
    """Convierte una imagen PNG local a string base64 para incrustarla en el HTML."""
    if not rutaImagen or not os.path.exists(rutaImagen):
        return ""
    with open(rutaImagen, "rb") as archivo:
        codificado = base64.b64encode(archivo.read()).decode("utf-8")
    return f"data:image/png;base64,{codificado}"


def _opcionesHtml(valores, textoTodos: str | None = None) -> str:
    """Arma las etiquetas <option> de un <select> a partir de una lista de valores.

    Args:
        valores: Valores únicos a ofrecer como opciones.
        textoTodos: Si se indica, agrega al principio la opción "TODOS" con este texto.
    """
    opciones = [f'<option value="TODOS">{escape(textoTodos)}</option>'] if textoTodos else []
    opciones += [f'<option value="{escape(str(v))}">{escape(str(v))}</option>' for v in valores]
    return "".join(opciones)


def _aplicarEstiloPlotly(fig: go.Figure, titulo: str) -> go.Figure:
    """Aplica la guía de estilo unificada (tipografía Arial, colores de bodega y fondo limpio)."""
    fig.update_layout(
        title=dict(text=titulo, font=dict(size=17, family="Arial, sans-serif", color=COLOR_BORDO)),
        font=dict(family="Arial, sans-serif", color=COLOR_TEXTO),
        legend=dict(
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor="#DCD6D0",
            borderwidth=1,
        ),
        xaxis=dict(gridcolor="#EFECE6", zerolinecolor="#DCD6D0", showline=True, linecolor="#DCD6D0"),
        yaxis=dict(gridcolor="#EFECE6", zerolinecolor="#DCD6D0", showline=True, linecolor="#DCD6D0"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=40, t=80, b=50),
    )
    return fig


def crearGraficoBurbujas(dfConsolidado: pd.DataFrame) -> go.Figure:
    """Crea el gráfico de burbujas interactivo (Stock vs. Ventas + estado de reposición)."""
    tienePredicciones = (
        Ventas.COL_PREDICCION in dfConsolidado.columns
        and Ventas.COL_PREDICCION_DL in dfConsolidado.columns
    )

    columnasCustom = [
        Inventario.COL_VARIETAL,
        Inventario.COL_LINEA,
        Ventas.COL_INGRESO,
        Inventario.COL_REPOSICION,
        Inventario.COL_REPOSICION_NECESARIA,
    ]
    if tienePredicciones:
        columnasCustom.extend([Ventas.COL_PREDICCION, Ventas.COL_PREDICCION_DL])

    fig = px.scatter(
        dfConsolidado,
        x=Ventas.COL_UNIDADESV,
        y=Inventario.COL_STOCK,
        size=Ventas.COL_INGRESO,
        color=Inventario.COL_REPOSICION_NECESARIA,
        color_discrete_map={"SI": COLOR_ALERTA, "NO": COLOR_OK},
        labels={
            Ventas.COL_UNIDADESV: "Unidades Vendidas (Popularidad)",
            Inventario.COL_STOCK: "Stock Actual (Botellas en Depósito)",
            Inventario.COL_REPOSICION_NECESARIA: "¿Requiere Reposición?",
        },
        size_max=48,
        custom_data=columnasCustom,
    )

    extraHover = ""
    if tienePredicciones:
        extraHover = (
            "<b>Demanda Anual Est. (OLS):</b> %{customdata[5]:,.0f} u.<br>"
            "<b>Demanda Anual Est. (Red Neuronal):</b> %{customdata[6]:,.0f} u.<br>"
        )

    fig.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]} — Línea %{customdata[1]}</b><br>"
            "───────────────────────────────<br>"
            "<b>Ventas Reales:</b> %{x:,} botellas<br>"
            + extraHover
            + "<b>Stock Actual:</b> %{y:,} botellas<br>"
            "<b>Punto de Reposición:</b> %{customdata[3]:,} botellas<br>"
            "<b>Ingreso Total:</b> $%{customdata[2]:,.2f} USD<br>"
            "<b>¿Requiere Reposición?:</b> %{customdata[4]}<br>"
            "<extra></extra>"
        )
    )

    #? Botones nativos de Plotly para filtrar por estado de reposición.
    #? Plotly crea un trazo por cada valor de 'Reposicion Necesaria' en el orden en que aparece en los datos
    #? (no siempre "SI" primero), por eso la visibilidad se arma según el nombre real de cada trazo.
    nombresTrazos = [trazo.name for trazo in fig.data]
    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=1.0,
                y=1.15,
                xanchor="right",
                buttons=[
                    dict(label="Todos los SKUs", method="update",
                         args=[{"visible": [True for _ in nombresTrazos]}]),
                    dict(label="Solo Alerta Reposición (SI)", method="update",
                         args=[{"visible": [nombre == "SI" for nombre in nombresTrazos]}]),
                    dict(label="Solo Stock OK (NO)", method="update",
                         args=[{"visible": [nombre == "NO" for nombre in nombresTrazos]}]),
                ],
            )
        ]
    )

    return _aplicarEstiloPlotly(
        fig,
        "<b>Análisis de Inventario vs. Popularidad de Ventas</b><br>"
        "<sup>Tamaño = Ingreso Total (USD) · Color = Alerta de Reposición</sup>",
    )


def crearGraficoComparativaModelos(dfVentas: pd.DataFrame) -> go.Figure:
    """Compara las unidades medias Reales vs. Predicción OLS vs. Predicción Deep Learning por Estación y Varietal."""
    ordenEstaciones = Ventas.ORDEN_ESTACIONES
    varietales = ["Todos", *sorted(dfVentas[Ventas.COL_VARIETAL].unique().tolist())]

    fig = go.Figure()
    botones = []

    for idx, var in enumerate(varietales):
        dfSub = dfVentas if var == "Todos" else dfVentas[dfVentas[Ventas.COL_VARIETAL] == var]
        resumen = (
            dfSub.groupby(Ventas.COL_ESTACION)[
                [Ventas.COL_UNIDADESV, Ventas.COL_PREDICCION, Ventas.COL_PREDICCION_DL]
            ]
            .mean()
            .reindex(ordenEstaciones)
            .reset_index()
        )
        visible = idx == 0

        fig.add_trace(
            go.Bar(
                name="Venta Real (Promedio)",
                x=resumen[Ventas.COL_ESTACION],
                y=resumen[Ventas.COL_UNIDADESV],
                marker_color=COLOR_BORDO,
                visible=visible,
                hovertemplate="<b>Real:</b> %{y:.1f} botellas<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Modelo Estadístico (OLS)",
                x=resumen[Ventas.COL_ESTACION],
                y=resumen[Ventas.COL_PREDICCION],
                marker_color="#8E9AAF",
                visible=visible,
                hovertemplate="<b>OLS:</b> %{y:.1f} botellas<extra></extra>",
            )
        )
        fig.add_trace(
            go.Bar(
                name="Deep Learning (Red Densa)",
                x=resumen[Ventas.COL_ESTACION],
                y=resumen[Ventas.COL_PREDICCION_DL],
                marker_color=COLOR_DORADO,
                visible=visible,
                hovertemplate="<b>Red Neuronal:</b> %{y:.1f} botellas<extra></extra>",
            )
        )

        visMask = [False] * (len(varietales) * 3)
        visMask[idx * 3 : idx * 3 + 3] = [True, True, True]
        botones.append(
            dict(
                label=f"Varietal: {var}",
                method="update",
                args=[{"visible": visMask}],
            )
        )

    fig.update_layout(
        barmode="group",
        xaxis_title="Estación del Año",
        yaxis_title="Promedio de Unidades por Transacción",
        updatemenus=[
            dict(
                active=0,
                buttons=botones,
                x=1.0,
                y=1.16,
                xanchor="right",
                bgcolor="#FAF7F5",
                bordercolor=COLOR_BORDO,
            )
        ],
    )

    return _aplicarEstiloPlotly(
        fig,
        "<b>Comparación de Modelos: Ventas Reales vs. OLS vs. Deep Learning</b><br>"
        "<sup>Promedios sobre todo el histórico (la métrica fuera de muestra está en los KPIs y el simulador). "
        "Observá cómo cada modelo sigue el efecto de la estación en cada varietal</sup>",
    )


def crearGraficoCurvaAprendizaje(historyDict: dict) -> go.Figure:
    """Grafica la evolución del error (Loss MSE) en entrenamiento y validación por época."""
    epocas = list(range(1, len(historyDict.get("loss", [])) + 1))
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=epocas,
            y=historyDict.get("loss", []),
            mode="lines+markers",
            name="Entrenamiento (Train MSE)",
            line=dict(color=COLOR_BORDO, width=2.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=epocas,
            y=historyDict.get("val_loss", []),
            mode="lines+markers",
            name="Validación (Val MSE)",
            line=dict(color=COLOR_DORADO, width=2.5, dash="dash"),
        )
    )

    fig.update_layout(
        xaxis_title="Época (Epoch)",
        yaxis_title="Error Cuadrático Medio (MSE)",
    )

    return _aplicarEstiloPlotly(
        fig,
        "<b>Curva de Aprendizaje — Red Neuronal (Keras Dense 32→16→1)</b><br>"
        "<sup>Evolución de la función de pérdida (MSE) en entrenamiento y validación a lo largo de las épocas</sup>",
    )


def generarDashboardHtml(
    datos: dict,
    rutaHeatmapPng: str | None = None,
    rutaBarrasPng: str | None = None,
    abrirNavegador: bool = True,
) -> str:
    """Construye y guarda el Dashboard HTML único e interactivo (`visuals/reporte_interactivo.html`).

    Incluye: barra de filtros, tarjetas de KPIs, gráficos de Plotly (burbujas de inventario, comparativa
    Real vs. OLS vs. Deep Learning y curva de aprendizaje), los PNG de Matplotlib y Seaborn incrustados
    en Base64, las tablas de estadística descriptiva / OLS y el simulador de demanda.

    Nota: el JavaScript de Plotly se carga desde su CDN oficial, así que la página necesita conexión a
    internet para dibujar los gráficos interactivos. El resto del contenido (KPIs, tablas, imágenes,
    filtros y simulador) está incrustado en el propio archivo.

    Args:
        datos: Diccionario devuelto por ``dataProcessing.procesarDatos()``.
        rutaHeatmapPng: Ruta del PNG del mapa de calor (Matplotlib) a incrustar.
        rutaBarrasPng: Ruta del PNG del gráfico de barras (Seaborn) a incrustar.
        abrirNavegador: Si es True, abre el HTML generado en el navegador predeterminado.

    Returns:
        Ruta absoluta del archivo HTML generado.
    """
    dfVentas: pd.DataFrame = datos["ventas"]
    dfInventario: pd.DataFrame = datos["inventario"]
    dfConsolidado: pd.DataFrame = datos["consolidado"]
    metricasOls: dict = datos["estadistica"]
    datosDl: dict = datos["deepLearning"]
    metricasDl: dict = datosDl["metricas"]
    desc: dict = metricasOls["descriptiva"]

    #? 1. Figuras interactivas de Plotly exportadas como fragmentos HTML
    #? Plotly.js se carga una sola vez desde el CDN (include_plotlyjs="cdn"): mantiene el HTML liviano
    #? pero requiere internet para ver los gráficos interactivos (ver README).
    figBurbujas = crearGraficoBurbujas(dfConsolidado)
    figComparativa = crearGraficoComparativaModelos(dfVentas)
    figCurva = crearGraficoCurvaAprendizaje(datosDl["history"])

    htmlBurbujas = figBurbujas.to_html(full_html=False, include_plotlyjs="cdn")
    htmlComparativa = figComparativa.to_html(full_html=False, include_plotlyjs=False)
    htmlCurva = figCurva.to_html(full_html=False, include_plotlyjs=False)

    #? 2. Imágenes estáticas de Matplotlib y Seaborn en Base64 (viajan dentro del propio HTML)
    b64Heatmap = _imagenABase64(rutaHeatmapPng) if rutaHeatmapPng else ""
    b64Barras = _imagenABase64(rutaBarrasPng) if rutaBarrasPng else ""

    #? 3. Opciones de los filtros y del simulador, generadas desde los datos (sin listas escritas a mano)
    varietales = sorted(dfVentas[Ventas.COL_VARIETAL].unique())
    estaciones = [e for e in Ventas.ORDEN_ESTACIONES if e in set(dfVentas[Ventas.COL_ESTACION])]
    canales = sorted(dfVentas[Ventas.COL_CANAL].unique())
    #? Líneas ordenadas por precio medio (Joven < Reserva < Gran Reserva), con su rango de precios real
    preciosPorLinea = dfVentas.groupby(Ventas.COL_LINEA)[Ventas.COL_PRECIOU].agg(["mean", "min", "max"]).sort_values("mean")
    opcionesLineaSim = "".join(
        f'<option value="{escape(str(lin))}">{escape(str(lin))} (${fila["min"]:.0f} - ${fila["max"]:.0f} USD)</option>'
        for lin, fila in preciosPorLinea.iterrows()
    )
    opcionesVarietalFiltro = _opcionesHtml(varietales, "Todos los Varietales")
    opcionesEstacionFiltro = _opcionesHtml(estaciones, "Todas las Estaciones")
    opcionesCanalFiltro = _opcionesHtml(canales, "Todos los Canales")
    opcionesVarietalSim = _opcionesHtml(varietales)
    opcionesEstacionSim = _opcionesHtml(estaciones)
    opcionesCanalSim = _opcionesHtml(canales)

    #? 4. Registros por transacción para los filtros de KPIs y el simulador (se calculan en el navegador)
    registrosJson = []
    for _, fila in dfVentas.iterrows():
        registrosJson.append(
            {
                "varietal": str(fila[Ventas.COL_VARIETAL]),
                "linea": str(fila[Ventas.COL_LINEA]),
                "canal": str(fila[Ventas.COL_CANAL]),
                "estacion": str(fila[Ventas.COL_ESTACION]),
                "precio": float(fila[Ventas.COL_PRECIOU]),
                "unidades": int(fila[Ventas.COL_UNIDADESV]),
                "ingreso": float(fila[Ventas.COL_INGRESO]),
                "predOls": float(fila[Ventas.COL_PREDICCION]),
                "predDl": float(fila[Ventas.COL_PREDICCION_DL]),
            }
        )

    skusTotal = int(len(dfInventario))
    skusReponer = int((dfInventario[Inventario.COL_REPOSICION_NECESARIA] == "SI").sum())

    #? Coeficientes del modelo OLS para el simulador interactivo y para la tabla técnica
    coefsOls = metricasOls["coeficientes"]
    filasCoefHtml = "".join(
        f"<tr><td>{var}</td><td style='text-align:right; font-weight:bold;'>{val:,.4f}</td></tr>"
        for var, val in coefsOls.items()
    )

    resumenDesc = desc["resumen"]
    filasDescHtml = "".join(
        f"<tr>"
        f"<td><b>{col}</b></td>"
        f"<td style='text-align:right;'>{vals['media']:,.2f}</td>"
        f"<td style='text-align:right;'>{vals['mediana']:,.2f}</td>"
        f"<td style='text-align:right;'>{vals['desvio']:,.2f}</td>"
        f"<td style='text-align:right;'>{vals['minimo']:,.2f} – {vals['maximo']:,.2f}</td>"
        f"</tr>"
        for col, vals in resumenDesc.items()
    )

    htmlCompleto = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WineLytics-V2 — Dashboard Analítico de Bodega</title>
    <style>
        :root {{
            --bordo: {COLOR_BORDO};
            --carmin: {COLOR_CARMIN};
            --dorado: {COLOR_DORADO};
            --alerta: {COLOR_ALERTA};
            --ok: {COLOR_OK};
            --texto: {COLOR_TEXTO};
            --fondo: {COLOR_FONDO};
        }}
        * {{ box-sizing: border-box; }}
        body {{
            margin: 0;
            font-family: Arial, Helvetica, sans-serif;
            background-color: var(--fondo);
            color: var(--texto);
            line-height: 1.5;
        }}
        header {{
            background: linear-gradient(135deg, var(--bordo) 0%, #4A1C22 100%);
            color: white;
            padding: 22px 36px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 4px solid var(--dorado);
        }}
        header h1 {{ margin: 0; font-size: 26px; letter-spacing: 0.5px; }}
        header p {{ margin: 4px 0 0; font-size: 14px; opacity: 0.9; }}
        .badge-header {{
            background: rgba(255,255,255,0.15);
            border: 1px solid var(--dorado);
            padding: 8px 14px;
            border-radius: 6px;
            font-size: 13px;
        }}
        .contenedor {{ max-width: 1380px; margin: 0 auto; padding: 24px 32px; }}

        /* Barra de Filtros Globales */
        .barra-filtros {{
            background: white;
            border: 1px solid #E2DCD5;
            border-left: 5px solid var(--bordo);
            border-radius: 8px;
            padding: 16px 22px;
            margin-bottom: 24px;
            display: flex;
            flex-wrap: wrap;
            gap: 18px;
            align-items: center;
            box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        }}
        .grupo-filtro {{ display: flex; flex-direction: column; gap: 4px; min-width: 180px; }}
        .grupo-filtro label {{ font-size: 12px; font-weight: bold; color: var(--bordo); text-transform: uppercase; }}
        .grupo-filtro select {{
            padding: 8px 10px;
            border: 1px solid #C8C0B8;
            border-radius: 5px;
            font-size: 14px;
            background: #FFF;
            color: var(--texto);
        }}
        .btn-reset {{
            margin-top: 18px;
            padding: 8px 16px;
            background: var(--bordo);
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
        }}
        .btn-reset:hover {{ background: var(--carmin); }}

        /* Grilla de KPIs */
        .grilla-kpis {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 28px;
        }}
        .tarjeta-kpi {{
            background: white;
            border-radius: 8px;
            padding: 16px 18px;
            border-top: 4px solid var(--bordo);
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
        }}
        .tarjeta-kpi.dorado {{ border-top-color: var(--dorado); }}
        .tarjeta-kpi.alerta {{ border-top-color: var(--alerta); }}
        .kpi-titulo {{ font-size: 12px; text-transform: uppercase; color: #6C7A89; font-weight: bold; }}
        .kpi-valor {{ font-size: 24px; font-weight: bold; color: var(--texto); margin: 6px 0 4px; }}
        .kpi-sub {{ font-size: 12px; color: #555; }}

        /* Secciones y Tarjetas */
        .titulo-seccion {{
            font-size: 20px;
            color: var(--bordo);
            border-bottom: 2px solid var(--dorado);
            padding-bottom: 6px;
            margin: 32px 0 16px;
        }}
        .tarjeta {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 22px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.05);
            border: 1px solid #EAE4DC;
        }}
        .grilla-dos {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(520px, 1fr));
            gap: 20px;
        }}
        .img-reporte {{ width: 100%; height: auto; border-radius: 6px; border: 1px solid #EFECE6; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 8px; }}
        th {{ background: var(--bordo); color: white; text-align: left; padding: 10px; }}
        td {{ padding: 9px 10px; border-bottom: 1px solid #EFECE6; }}
        tr:nth-child(even) {{ background: #FAF7F5; }}

        /* Simulador */
        .simulador-box {{
            background: #FDFBF7;
            border: 2px solid var(--dorado);
            border-radius: 8px;
            padding: 18px 22px;
        }}
        .resultado-sim {{
            display: flex;
            gap: 20px;
            margin-top: 14px;
            flex-wrap: wrap;
        }}
        .caja-pred {{
            flex: 1;
            min-width: 200px;
            background: white;
            padding: 14px;
            border-radius: 6px;
            border-left: 4px solid var(--bordo);
            box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        }}
        .caja-pred.dl {{ border-left-color: var(--dorado); }}
        footer {{
            text-align: center;
            padding: 20px;
            font-size: 13px;
            color: #666;
            border-top: 1px solid #E2DCD5;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <header>
        <div>
            <h1>🍷 WineLytics-V2 — Dashboard Analítico de Bodega</h1>
            <p>Sistema Integrado de ETL, Visualización, Estadística Inferencial (OLS / SciPy) y Deep Learning (Keras / TensorFlow)</p>
        </div>
        <div class="badge-header">
            Semilla reproducible: <b>42</b> · Registros: <b>{len(dfVentas):,}</b>
        </div>
    </header>

    <div class="contenedor">
        <!-- BARRA DE FILTROS INTERACTIVOS -->
        <section class="barra-filtros" id="seccion-filtros">
            <div class="grupo-filtro">
                <label for="filtroVarietal">Filtrar por Varietal</label>
                <select id="filtroVarietal" onchange="actualizarKPIs()">
                    {opcionesVarietalFiltro}
                </select>
            </div>
            <div class="grupo-filtro">
                <label for="filtroEstacion">Filtrar por Estación</label>
                <select id="filtroEstacion" onchange="actualizarKPIs()">
                    {opcionesEstacionFiltro}
                </select>
            </div>
            <div class="grupo-filtro">
                <label for="filtroCanal">Filtrar por Canal de Venta</label>
                <select id="filtroCanal" onchange="actualizarKPIs()">
                    {opcionesCanalFiltro}
                </select>
            </div>
            <button class="btn-reset" onclick="resetearFiltros()">Restablecer Filtros</button>
        </section>

        <!-- TARJETAS DE KPIs -->
        <section class="grilla-kpis" id="seccion-kpis">
            <div class="tarjeta-kpi">
                <div class="kpi-titulo">Ingreso Total</div>
                <div class="kpi-valor" id="kpiIngreso">$0</div>
                <div class="kpi-sub" id="kpiTransacciones">Cargando transacciones…</div>
            </div>
            <div class="tarjeta-kpi">
                <div class="kpi-titulo">Unidades Vendidas</div>
                <div class="kpi-valor" id="kpiUnidades">0</div>
                <div class="kpi-sub" id="kpiPromedioUnidades">Promedio por venta</div>
            </div>
            <div class="tarjeta-kpi dorado">
                <div class="kpi-titulo">Ticket Promedio</div>
                <div class="kpi-valor" id="kpiTicket">$0</div>
                <div class="kpi-sub" id="kpiPrecioMedio">Precio medio x botella</div>
            </div>
            <div class="tarjeta-kpi dorado">
                <div class="kpi-titulo">Share Exportación</div>
                <div class="kpi-valor" id="kpiExportacion">0%</div>
                <div class="kpi-sub">Sobre ingresos filtrados</div>
            </div>
            <div class="tarjeta-kpi alerta">
                <div class="kpi-titulo">Alerta de Stock (SKUs)</div>
                <div class="kpi-valor">{skusReponer} / {skusTotal}</div>
                <div class="kpi-sub">Vinos bajo punto de reposición</div>
            </div>
            <div class="tarjeta-kpi dorado">
                <div class="kpi-titulo">R² de los Modelos (Test 20%)</div>
                <div class="kpi-valor">DL {metricasDl['r2']*100:.1f}% vs OLS {metricasOls['r2Test']*100:.1f}%</div>
                <div class="kpi-sub">R² en conjunto de prueba (semilla 42)</div>
            </div>
        </section>

        <!-- SECCIÓN 1: VISUALIZACIONES COMERCIALES Y DE INVENTARIO -->
        <h2 class="titulo-seccion">1. Visualización Comercial y Estado de Inventario (Plotly · Matplotlib · Seaborn)</h2>
        <div class="tarjeta">
            {htmlBurbujas}
        </div>
        <div class="grilla-dos">
            <div class="tarjeta">
                <h3 style="margin-top:0; color:var(--bordo);">Mapa de Calor de Estacionalidad (Matplotlib)</h3>
                <img class="img-reporte" src="{b64Heatmap}" alt="Mapa de calor de estacionalidad por varietal">
            </div>
            <div class="tarjeta">
                <h3 style="margin-top:0; color:var(--bordo);">Ventas Mensuales por Canal (Seaborn)</h3>
                <img class="img-reporte" src="{b64Barras}" alt="Gráfico de barras de unidades por mes y canal">
            </div>
        </div>

        <!-- SECCIÓN 2: ESTADÍSTICA DESCRIPTIVA E INFERENCIAL -->
        <h2 class="titulo-seccion">2. Análisis Estadístico Descriptivo y Regresión OLS (NumPy · SciPy · Statsmodels)</h2>
        <div class="grilla-dos">
            <div class="tarjeta">
                <h3 style="margin-top:0; color:var(--bordo);">Estadística Descriptiva y Pruebas de Hipótesis (SciPy)</h3>
                <table>
                    <thead>
                        <tr>
                            <th>Variable</th>
                            <th style="text-align:right;">Media</th>
                            <th style="text-align:right;">Mediana</th>
                            <th style="text-align:right;">Desvío Est.</th>
                            <th style="text-align:right;">Rango [Mín – Máx]</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filasDescHtml}
                    </tbody>
                </table>
                <div style="margin-top:16px; padding:12px; background:#FAF7F5; border-left:4px solid var(--bordo); border-radius:4px;">
                    <p style="margin:4px 0;"><b>• Correlación de Pearson (Precio vs. Unidades):</b>
                        r = <b>{desc['pearsonPrecioUnidades']['r']:.4f}</b> (p-valor = {desc['pearsonPrecioUnidades']['pValor']:.2e})
                        → <i>Relación inversa fuerte y estadísticamente significativa.</i>
                    </p>
                    <p style="margin:4px 0;"><b>• Test ANOVA por Estación (Unidades):</b>
                        F = <b>{desc['anovaEstacion']['fStat']:.2f}</b> (p-valor = {desc['anovaEstacion']['pValor']:.2e})
                        → <i>Las ventas medias varían significativamente según la estación del año.</i>
                    </p>
                </div>
            </div>

            <div class="tarjeta">
                <h3 style="margin-top:0; color:var(--bordo);">Modelo de Regresión Lineal Múltiple (OLS — Statsmodels)</h3>
                <p style="margin-top:0; font-size:13px; color:#555;">
                    <b>R² in-sample:</b> {metricasOls['r2']:.4f} ·
                    <b>R² Ajustado:</b> {metricasOls['r2Adj']:.4f} ·
                    <b>R² Test (20%):</b> {metricasOls['r2Test']:.4f} ·
                    <b>MAE Test:</b> {metricasOls['maeTest']:.2f} u. ·
                    <b>AIC:</b> {metricasOls['aic']:.1f}
                </p>
                <table>
                    <thead>
                        <tr>
                            <th>Variable / Categoría (Base: Cabernet, Exportación, Invierno)</th>
                            <th style="text-align:right;">Coeficiente (β)</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filasCoefHtml}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- SECCIÓN 3: DEEP LEARNING Y SIMULADOR DE DEMANDA -->
        <h2 class="titulo-seccion">3. Aprendizaje Profundo (Keras / TensorFlow) y Simulador de Demanda</h2>
        <div class="grilla-dos">
            <div class="tarjeta">
                {htmlComparativa}
            </div>
            <div class="tarjeta">
                {htmlCurva}
            </div>
        </div>

        <div class="tarjeta simulador-box" id="seccion-simulador">
            <h3 style="margin-top:0; color:var(--bordo);">🔮 Simulador de Pronóstico de Demanda por Transacción (OLS vs. Red Neuronal)</h3>
            <p style="margin-top:0; font-size:14px;">
                Seleccioná una combinación comercial para comparar la estimación del modelo lineal frente a la Red Neuronal Densa (<b>Dense 32 → 16 → 1</b>):
            </p>
            <div class="barra-filtros" style="margin-bottom:10px; border-left-color:var(--dorado);">
                <div class="grupo-filtro">
                    <label for="simVarietal">Varietal</label>
                    <select id="simVarietal" onchange="actualizarSimulador()">
                        {opcionesVarietalSim}
                    </select>
                </div>
                <div class="grupo-filtro">
                    <label for="simEstacion">Estación</label>
                    <select id="simEstacion" onchange="actualizarSimulador()">
                        {opcionesEstacionSim}
                    </select>
                </div>
                <div class="grupo-filtro">
                    <label for="simLinea">Línea (define rango de precio)</label>
                    <select id="simLinea" onchange="actualizarSimulador()">
                        {opcionesLineaSim}
                    </select>
                </div>
                <div class="grupo-filtro">
                    <label for="simCanal">Canal de Venta</label>
                    <select id="simCanal" onchange="actualizarSimulador()">
                        {opcionesCanalSim}
                    </select>
                </div>
            </div>
            <div class="resultado-sim">
                <div class="caja-pred">
                    <div class="kpi-titulo">Demanda Histórica Real (Promedio)</div>
                    <div class="kpi-valor" id="simReal">-</div>
                    <div class="kpi-sub" id="simPrecio">Precio medio del segmento</div>
                </div>
                <div class="caja-pred">
                    <div class="kpi-titulo">Pronóstico Regresión OLS (Statsmodels)</div>
                    <div class="kpi-valor" id="simOls">-</div>
                    <div class="kpi-sub">MAE global en test: {metricasOls['maeTest']:.2f} botellas</div>
                </div>
                <div class="caja-pred dl">
                    <div class="kpi-titulo">Pronóstico Deep Learning (Keras / TF)</div>
                    <div class="kpi-valor" id="simDl">-</div>
                    <div class="kpi-sub">MAE global en test: <b>{metricasDl['mae']:.2f} botellas (R² {metricasDl['r2']:.3f})</b></div>
                </div>
            </div>
        </div>
    </div>

    <footer>
        WineLytics V2 · Instituto Superior Manuel Belgrano · Programación Orientada al Análisis de Datos (2026)
    </footer>

    <script>
        const DATOS_VENTAS = {json.dumps(registrosJson, ensure_ascii=False)};

        function formatearMoneda(valor) {{
            return "$" + valor.toLocaleString("en-US", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }});
        }}

        function actualizarKPIs() {{
            const varSel = document.getElementById("filtroVarietal").value;
            const estSel = document.getElementById("filtroEstacion").value;
            const canSel = document.getElementById("filtroCanal").value;

            const filtrados = DATOS_VENTAS.filter(d =>
                (varSel === "TODOS" || d.varietal === varSel) &&
                (estSel === "TODOS" || d.estacion === estSel) &&
                (canSel === "TODOS" || d.canal === canSel)
            );

            const n = filtrados.length;
            const totalIngreso = filtrados.reduce((acc, d) => acc + d.ingreso, 0);
            const totalUnidades = filtrados.reduce((acc, d) => acc + d.unidades, 0);
            const ingresoExp = filtrados.filter(d => d.canal === "Exportación").reduce((acc, d) => acc + d.ingreso, 0);
            const precioMedio = n > 0 ? filtrados.reduce((acc, d) => acc + d.precio, 0) / n : 0;

            document.getElementById("kpiIngreso").textContent = formatearMoneda(totalIngreso);
            document.getElementById("kpiTransacciones").textContent = n.toLocaleString() + " transacciones";
            document.getElementById("kpiUnidades").textContent = totalUnidades.toLocaleString() + " u.";
            document.getElementById("kpiPromedioUnidades").textContent =
                (n > 0 ? (totalUnidades / n).toFixed(1) : "0") + " botellas / venta";
            document.getElementById("kpiTicket").textContent = formatearMoneda(n > 0 ? totalIngreso / n : 0);
            document.getElementById("kpiPrecioMedio").textContent =
                "Precio medio: " + formatearMoneda(precioMedio) + " / botella";
            document.getElementById("kpiExportacion").textContent =
                (totalIngreso > 0 ? ((ingresoExp / totalIngreso) * 100).toFixed(1) : "0.0") + "%";
        }}

        function resetearFiltros() {{
            document.getElementById("filtroVarietal").value = "TODOS";
            document.getElementById("filtroEstacion").value = "TODOS";
            document.getElementById("filtroCanal").value = "TODOS";
            actualizarKPIs();
        }}

        function actualizarSimulador() {{
            const varSel = document.getElementById("simVarietal").value;
            const estSel = document.getElementById("simEstacion").value;
            const linSel = document.getElementById("simLinea").value;
            const canSel = document.getElementById("simCanal").value;

            const segmento = DATOS_VENTAS.filter(d =>
                d.varietal === varSel &&
                d.estacion === estSel &&
                d.linea === linSel &&
                d.canal === canSel
            );

            if (segmento.length === 0) {{
                document.getElementById("simReal").textContent = "Sin datos";
                document.getElementById("simOls").textContent = "-";
                document.getElementById("simDl").textContent = "-";
                return;
            }}

            const n = segmento.length;
            const mediaReal = segmento.reduce((a, d) => a + d.unidades, 0) / n;
            const mediaOls = segmento.reduce((a, d) => a + d.predOls, 0) / n;
            const mediaDl = segmento.reduce((a, d) => a + d.predDl, 0) / n;
            const mediaPrecio = segmento.reduce((a, d) => a + d.precio, 0) / n;

            document.getElementById("simReal").textContent = Math.round(mediaReal) + " botellas";
            document.getElementById("simPrecio").textContent =
                "Precio medio segmento: $" + mediaPrecio.toFixed(2) + " USD (" + n + " muestras)";
            document.getElementById("simOls").textContent = Math.round(mediaOls) + " botellas";
            document.getElementById("simDl").textContent = Math.round(mediaDl) + " botellas";
        }}

        actualizarKPIs();
        actualizarSimulador();
    </script>
</body>
</html>
"""

    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaHtml = os.path.join(baseDir, "visuals", "reporte_interactivo.html")
    with open(rutaHtml, "w", encoding="utf-8") as f:
        f.write(htmlCompleto)

    print(f"Dashboard HTML unificado guardado exitosamente en: {rutaHtml}")

    if abrirNavegador:
        try:
            webbrowser.open(f"file://{os.path.abspath(rutaHtml)}")
        except Exception as e:
            print(f"No se pudo abrir automáticamente el navegador web: {e}")

    return rutaHtml

