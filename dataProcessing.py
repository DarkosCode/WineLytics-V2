import pandas as pd
from sources.inventarioCsv import cargarInventario
from sources.ventasCsv import cargarVentas
from schema.ventas import Ventas
from backend.statsAnalysis import ejecutarAnalisisEstadistico
from backend.deepLearning import entrenarModeloDeepLearning, agregarPrediccionesDL

def procesarDatos():
    #? 1. Cargar los DataFrames desde los CSV, pero pasando primero por los sources que estructuran y limpian
    dfInventario = cargarInventario()
    dfVentas = cargarVentas()

    #? 2. Ejecutar el análisis estadístico (OLS + estadística descriptiva con NumPy y SciPy)
    #? Esto le suma la columna 'Prediccion_Ventas' a dfVentas
    dfVentas, metricasOls, modeloOls = ejecutarAnalisisEstadistico(dfVentas)

    #? 3. Entrenar la Red Neuronal (Keras) y agregar la columna 'Prediccion_DL' a dfVentas
    modeloDl, historyDl, metricasDl, (xTest, yTest, yPredDl) = entrenarModeloDeepLearning(dfVentas)
    dfVentas = agregarPrediccionesDL(dfVentas, modeloDl)

    #? 4. Agrupar las ventas por Varietal y Linea para sumar unidades reales, ingresos y predicciones de cada vino
    columnasASumar = [
        Ventas.COL_UNIDADESV,
        Ventas.COL_INGRESO,
        Ventas.COL_PREDICCION,
        Ventas.COL_PREDICCION_DL
    ]
    ventasResumen = dfVentas.groupby([Ventas.COL_VARIETAL, Ventas.COL_LINEA])[columnasASumar].sum().reset_index()

    #? 5. Cruzar ('Mergear') el inventario con el resumen de ventas
    #? Usamos 'inner' porque queremos analizar los vinos que existen en ambos datasets
    dfConsolidado = pd.merge(
        dfInventario,
        ventasResumen,
        on=[Ventas.COL_VARIETAL, Ventas.COL_LINEA],
        how="inner"
    )

    #? Retornamos los DataFrames estructurados y los resultados del backend en un diccionario
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
            "modelo": modeloDl
        },
        "modeloOls": modeloOls
    }

if __name__ == "__main__":
    resultados = procesarDatos()
