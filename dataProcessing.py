import pandas as pd
from sources.inventarioCsv import cargarInventario
from sources.ventasCsv import cargarVentas
from schema.ventas import Ventas
from backend.statsAnalysis import ejecutarAnalisisEstadistico
from backend.deepLearning import entrenarModeloDeepLearning, agregarPrediccionesDL


def procesarDatos():
    """Ejecuta el pipeline de datos completo: ETL, análisis estadístico y Deep Learning.

    Carga y limpia los CSV (`sources/`), ajusta el modelo OLS y la red neuronal (`backend/`),
    agrega sus predicciones al DataFrame de ventas y lo cruza con el inventario.

    Returns:
        Diccionario con:
            - ``inventario``: DataFrame de inventario limpio.
            - ``ventas``: DataFrame de ventas con ``Prediccion_Ventas`` y ``Prediccion_DL``.
            - ``consolidado``: inventario + ventas/predicciones agrupadas por Varietal y Línea.
            - ``estadistica``: métricas del OLS y estadística descriptiva.
            - ``deepLearning``: métricas, historial de entrenamiento, valores de test y modelo de la red.
            - ``modeloOls``: modelo OLS ajustado (``statsmodels``).
    """
    #? 1. Cargar los DataFrames desde los CSV pasando por los módulos de limpieza y estructuración (sources/)
    dfInventario = cargarInventario()
    dfVentas = cargarVentas()

    #? 2. Ejecutar análisis estadístico (OLS + estadística descriptiva con NumPy/SciPy)
    #? Agrega la columna 'Prediccion_Ventas' al DataFrame de ventas
    dfVentas, metricasOls, modeloOls = ejecutarAnalisisEstadistico(dfVentas)

    #? 3. Entrenar modelo de Aprendizaje Profundo (Red Neuronal Keras) y generar 'Prediccion_DL'
    modeloDl, historyDl, metricasDl, (xTest, yTest, yPredDl) = entrenarModeloDeepLearning(dfVentas)
    dfVentas = agregarPrediccionesDL(dfVentas, modeloDl)

    #? 4. Agrupar las ventas por Varietal y Línea para calcular totales reales y pronosticados
    columnasSuma = [
        Ventas.COL_UNIDADESV,
        Ventas.COL_INGRESO,
        Ventas.COL_PREDICCION,
        Ventas.COL_PREDICCION_DL,
    ]
    ventasResumen = (
        dfVentas.groupby([Ventas.COL_VARIETAL, Ventas.COL_LINEA])[columnasSuma]
        .sum()
        .reset_index()
    )

    #? 5. Cruzar ('Mergear') el inventario con el resumen de ventas e indicadores predictivos
    dfConsolidado = pd.merge(
        dfInventario,
        ventasResumen,
        on=[Ventas.COL_VARIETAL, Ventas.COL_LINEA],
        how="inner",
    )

    #? Retornamos los DataFrames enriquecidos y los resultados del backend en un diccionario unificado
    return {
        "inventario": dfInventario,
        "ventas": dfVentas,
        "consolidado": dfConsolidado,
        "estadistica": metricasOls,
        "deepLearning": {
            "metricas": metricasDl,
            "history": historyDl.history,
            "yTest": yTest.tolist(),
            "yPred": yPredDl.tolist(),
            "modelo": modeloDl,
        },
        "modeloOls": modeloOls,
    }


if __name__ == "__main__":
    resultados = procesarDatos()
