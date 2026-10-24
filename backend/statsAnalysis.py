import os
import sys
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import statsmodels.api as sm

#? Permite importar 'schema' aunque ejecutemos este archivo directo desde backend/
raizProyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if raizProyecto not in sys.path:
    sys.path.insert(0, raizProyecto)

from schema.ventas import Ventas

#? Variables categóricas que pasamos a numéricas (dummies) para el modelo
#? No incluimos 'Linea' porque el precio ya depende casi al 100% de la línea, y poner las dos genera multicolinealidad
COLUMNAS_CATEGORICAS = [Ventas.COL_CANAL, Ventas.COL_VARIETAL, Ventas.COL_ESTACION]

#? Usamos la misma semilla y porcentaje de test (20%) que en deepLearning.py para poder compararlos bien
SEMILLA = 42
TAMANIO_TEST = 0.2


def prepararVariables(df):
    #? Convertimos las columnas de texto en columnas de 0 y 1 (dummies)
    #? drop_first=True saca una categoría base para evitar redundancia en la regresión
    dummies = pd.get_dummies(df[COLUMNAS_CATEGORICAS], drop_first=True, dtype=float)

    X = pd.concat([df[[Ventas.COL_PRECIOU]].astype(float), dummies], axis=1)
    X = sm.add_constant(X)

    y = df[Ventas.COL_UNIDADESV].astype(float)
    return y, X


def calcularEstadisticaDescriptiva(dfVentas):
    #? 1. Calculamos media, mediana, desvío estándar, mínimo y máximo con NumPy
    columnasNumericas = [Ventas.COL_UNIDADESV, Ventas.COL_PRECIOU, Ventas.COL_INGRESO]
    resumen = {}

    for col in columnasNumericas:
        if col in dfVentas.columns:
            serie = dfVentas[col].astype(float)
            resumen[col] = {
                "media": float(np.mean(serie)),
                "mediana": float(np.median(serie)),
                "desvio": float(np.std(serie, ddof=1)),
                "minimo": float(np.min(serie)),
                "maximo": float(np.max(serie))
            }

    #? 2. Correlación de Pearson (SciPy): para ver qué tan relacionada está la baja de ventas cuando sube el precio
    rPearson, pPearson = stats.pearsonr(
        dfVentas[Ventas.COL_PRECIOU].astype(float),
        dfVentas[Ventas.COL_UNIDADESV].astype(float)
    )

    #? 3. Test ANOVA (SciPy): para comprobar si las ventas cambian de verdad según la estación del año
    gruposEstacion = []
    for _, grupo in dfVentas.groupby(Ventas.COL_ESTACION):
        gruposEstacion.append(grupo[Ventas.COL_UNIDADESV].astype(float).values)

    fStat, pAnova = stats.f_oneway(*gruposEstacion)

    promedioPorEstacion = dfVentas.groupby(Ventas.COL_ESTACION)[Ventas.COL_UNIDADESV].mean().round(2).to_dict()

    return {
        "resumen": resumen,
        "pearsonPrecioUnidades": {
            "r": float(rPearson),
            "pValor": float(pPearson)
        },
        "anovaEstacion": {
            "fStat": float(fStat),
            "pValor": float(pAnova),
            "promedioPorEstacion": promedioPorEstacion
        }
    }


def ejecutarAnalisisEstadistico(dfVentas):
    #? Trabajamos sobre una copia para no pisar el DataFrame original sin querer
    dfResultado = dfVentas.copy()

    #? Ajustamos el modelo de Regresión Lineal Múltiple (OLS) con Statsmodels
    y, X = prepararVariables(dfResultado)
    modelo = sm.OLS(y, X).fit()

    print(modelo.summary())

    #? Guardamos las predicciones en una columna nueva del DataFrame
    dfResultado[Ventas.COL_PREDICCION] = modelo.predict(X)

    #? Evaluamos el modelo separando 80% entrenamiento y 20% prueba (igual que en la red neuronal)
    XTrain, xTest, yTrain, yTest = train_test_split(
        X, y, test_size=TAMANIO_TEST, random_state=SEMILLA
    )
    modeloTrain = sm.OLS(yTrain, XTrain).fit()
    yPredTest = modeloTrain.predict(xTest)

    descriptiva = calcularEstadisticaDescriptiva(dfResultado)

    coeficientes = {}
    for var, coef in modelo.params.items():
        coeficientes[var] = float(coef)

    metricasDict = {
        "r2": float(modelo.rsquared),
        "r2Adj": float(modelo.rsquared_adj),
        "fPvalue": float(modelo.f_pvalue),
        "aic": float(modelo.aic),
        "bic": float(modelo.bic),
        "r2Test": float(r2_score(yTest, yPredTest)),
        "maeTest": float(mean_absolute_error(yTest, yPredTest)),
        "rmseTest": float(np.sqrt(mean_squared_error(yTest, yPredTest))),
        "coeficientes": coeficientes,
        "descriptiva": descriptiva
    }

    return dfResultado, metricasDict, modelo


if __name__ == "__main__":
    from sources.ventasCsv import cargarVentas

    df = cargarVentas()
    dfPred, metricas, _ = ejecutarAnalisisEstadistico(df)

    desc = metricas["descriptiva"]
    print("\n=== Estadística descriptiva (NumPy / SciPy) ===")
    for col, vals in desc["resumen"].items():
        print(
            f"  {col}: Media = {vals['media']:.2f} | Mediana = {vals['mediana']:.2f} "
            f"| Desvío = {vals['desvio']:.2f} | Rango = [{vals['minimo']:.2f}, {vals['maximo']:.2f}]"
        )
    print(f"  Correlación Pearson (Precio vs Unidades): r = {desc['pearsonPrecioUnidades']['r']:.4f}")
    print(f"  ANOVA por Estación (Unidades): F = {desc['anovaEstacion']['fStat']:.2f}")

    print("\n=== Métricas clave OLS ===")
    print(f"R² (in-sample) : {metricas['r2']:.4f}")
    print(f"R² (test 20%)  : {metricas['r2Test']:.4f}")
    print(f"MAE (test 20%) : {metricas['maeTest']:.2f} unidades")
    print(f"RMSE (test 20%): {metricas['rmseTest']:.2f} unidades")
