"""
Módulo de análisis estadístico de WineLytics.

Ajusta un modelo de Regresión Lineal por Mínimos Cuadrados Ordinarios (OLS)
con ``statsmodels`` para describir / pronosticar las 'Unidades Vendidas' en
función del 'Precio Unitario', el 'Canal de Venta', el 'Varietal' y la
'Estacion' del año.

'Linea' se excluye a propósito: el precio depende casi por completo de la
línea (Joven < Reserva < Gran Reserva), por lo que incluir ambas genera
multicolinealidad y coeficientes inestables.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

#? Permite importar 'schema' aunque el script se ejecute directamente desde backend/
RAIZ_PROYECTO: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ_PROYECTO not in sys.path:
    sys.path.insert(0, RAIZ_PROYECTO)

from schema.ventas import Ventas

#? Nombres de columnas (definidos en schema/ventas.py)
COL_UNIDADES: str = Ventas.COL_UNIDADESV
COL_PRECIO: str = Ventas.COL_PRECIOU
COL_INGRESO: str = Ventas.COL_INGRESO
COL_CANAL: str = Ventas.COL_CANAL
COL_VARIETAL: str = Ventas.COL_VARIETAL
COL_ESTACION: str = Ventas.COL_ESTACION
COL_PREDICCION: str = Ventas.COL_PREDICCION

#? Variables categóricas que se transforman en dummies
COLUMNAS_CATEGORICAS: List[str] = [COL_CANAL, COL_VARIETAL, COL_ESTACION]

COLUMNAS_REQUERIDAS: List[str] = [COL_UNIDADES, COL_PRECIO, *COLUMNAS_CATEGORICAS]

#? Mismo split que backend/deepLearning.py para comparar ambos modelos en igualdad de condiciones
SEMILLA: int = 42
TAMANIO_TEST: float = 0.2


def _validarColumnas(df: pd.DataFrame) -> None:
    """Verifica que el DataFrame tenga todas las columnas necesarias.

    Args:
        df: DataFrame de ventas a validar.

    Raises:
        ValueError: Si falta alguna de las columnas requeridas.
    """
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en dfVentas: {faltantes}")


def _prepararVariables(df: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    """Construye la variable dependiente ``y`` y la matriz de diseño ``X``.

    - ``y``: 'Unidades Vendidas'.
    - ``X``: 'Precio Unitario' + dummies de 'Canal de Venta', 'Varietal' y
      'Estacion' (``drop_first=True`` para evitar la trampa de las variables
      ficticias) + constante (intercepto).

    Args:
        df: DataFrame de ventas ya validado.

    Returns:
        Tupla ``(y, X)`` lista para pasar a ``sm.OLS``.
    """
    #? dtype=float: statsmodels necesita valores numéricos (no bool)
    dummies = pd.get_dummies(df[COLUMNAS_CATEGORICAS], drop_first=True, dtype=float)

    X = pd.concat([df[[COL_PRECIO]].astype(float), dummies], axis=1)
    X = sm.add_constant(X)

    y = df[COL_UNIDADES].astype(float)
    return y, X


def calcularEstadisticaDescriptiva(dfVentas: pd.DataFrame) -> Dict[str, Any]:
    """Calcula métricas descriptivas y pruebas de hipótesis con NumPy y SciPy.

    Incluye:
    1. Resumen numérico (media, mediana, desvío estándar, mínimo y máximo).
    2. Correlación lineal de Pearson entre Precio Unitario y Unidades Vendidas.
    3. Test ANOVA de una vía (``scipy.stats.f_oneway``) de Unidades por Estación.

    Args:
        dfVentas: DataFrame de ventas ya validado.

    Returns:
        Diccionario con ``resumen``, ``pearsonPrecioUnidades`` y ``anovaEstacion``.
    """
    _validarColumnas(dfVentas)

    columnasNumericas = [COL_UNIDADES, COL_PRECIO]
    if COL_INGRESO in dfVentas.columns:
        columnasNumericas.append(COL_INGRESO)

    #? 1. Estadísticos de tendencia central y dispersión con NumPy / Pandas
    resumen: Dict[str, Dict[str, float]] = {}
    for col in columnasNumericas:
        serie = dfVentas[col].astype(float)
        resumen[col] = {
            "media": float(np.mean(serie)),
            "mediana": float(np.median(serie)),
            "desvio": float(np.std(serie, ddof=1)),
            "minimo": float(np.min(serie)),
            "maximo": float(np.max(serie)),
        }

    #? 2. Correlación de Pearson (SciPy): mide la relación lineal inversa precio-cantidad
    rPearson, pPearson = stats.pearsonr(
        dfVentas[COL_PRECIO].astype(float),
        dfVentas[COL_UNIDADES].astype(float),
    )

    #? 3. ANOVA de una vía (SciPy): evalúa si la media de unidades difiere entre estaciones
    gruposEstacion = [
        grupo[COL_UNIDADES].astype(float).values
        for _, grupo in dfVentas.groupby(COL_ESTACION)
    ]
    fStat, pAnova = stats.f_oneway(*gruposEstacion)

    promedioPorEstacion = (
        dfVentas.groupby(COL_ESTACION)[COL_UNIDADES]
        .mean()
        .round(2)
        .to_dict()
    )

    return {
        "resumen": resumen,
        "pearsonPrecioUnidades": {
            "r": float(rPearson),
            "pValor": float(pPearson),
        },
        "anovaEstacion": {
            "fStat": float(fStat),
            "pValor": float(pAnova),
            "promedioPorEstacion": {k: float(v) for k, v in promedioPorEstacion.items()},
        },
    }


def ejecutarAnalisisEstadistico(
    dfVentas: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Any], RegressionResultsWrapper]:
    """Ajusta un modelo OLS sobre las ventas y genera predicciones y métricas.

    Modelo:
        Unidades Vendidas ~ const + Precio Unitario + dummies(Canal de Venta)
                            + dummies(Varietal) + dummies(Estacion)

    Args:
        dfVentas: DataFrame con, al menos, las columnas 'Unidades Vendidas',
            'Precio Unitario', 'Canal de Venta', 'Varietal' y 'Estacion'
            (esta última la genera ``sources.ventasCsv.cargarVentas``).

    Returns:
        Tupla ``(dfVentas, metricasDict, modelo)`` donde:
            - ``dfVentas``: copia del DataFrame de entrada con la columna
              nueva 'Prediccion_Ventas'.
            - ``metricasDict``: diccionario con métricas in-sample (``r2``,
              ``r2Adj``, ``fPvalue``, ``aic``, ``bic``, ``coeficientes``),
              métricas en el conjunto de prueba 80/20 (``r2Test``, ``maeTest``,
              ``rmseTest``) y ``descriptiva`` (Pearson, ANOVA y resumen).
            - ``modelo``: resultado ajustado de ``sm.OLS(...).fit()``.

    Raises:
        ValueError: Si faltan columnas requeridas en ``dfVentas``.
    """
    _validarColumnas(dfVentas)

    #? Trabajamos sobre una copia para no modificar el DataFrame original
    dfResultado = dfVentas.copy()

    y, X = _prepararVariables(dfResultado)
    modelo: RegressionResultsWrapper = sm.OLS(y, X).fit()

    print(modelo.summary())

    dfResultado[COL_PREDICCION] = modelo.predict(X)

    #? Evaluación en el mismo split 80/20 que usa Deep Learning para una comparación justa
    XTrain, xTest, yTrain, yTest = train_test_split(
        X, y, test_size=TAMANIO_TEST, random_state=SEMILLA
    )
    modeloTrain = sm.OLS(yTrain, XTrain).fit()
    yPredTest = modeloTrain.predict(xTest)

    descriptiva = calcularEstadisticaDescriptiva(dfResultado)

    metricasDict: Dict[str, Any] = {
        "r2": float(modelo.rsquared),
        "r2Adj": float(modelo.rsquared_adj),
        "fPvalue": float(modelo.f_pvalue),
        "aic": float(modelo.aic),
        "bic": float(modelo.bic),
        "r2Test": float(r2_score(yTest, yPredTest)),
        "maeTest": float(mean_absolute_error(yTest, yPredTest)),
        "rmseTest": float(np.sqrt(mean_squared_error(yTest, yPredTest))),
        "coeficientes": {var: float(coef) for var, coef in modelo.params.items()},
        "descriptiva": descriptiva,
    }

    return dfResultado, metricasDict, modelo


if __name__ == "__main__":
    import warnings

    #? cargarVentas() es la fuente oficial: renombra columnas y crea 'Estacion'
    from sources.ventasCsv import cargarVentas

    #? Capturamos cualquier advertencia para confirmar que el análisis corre limpio
    with warnings.catch_warnings(record=True) as advertencias:
        warnings.simplefilter("always")
        df = cargarVentas()
        dfPred, metricas, _ = ejecutarAnalisisEstadistico(df)

    desc = metricas["descriptiva"]
    print("\n=== Estadística descriptiva (NumPy / SciPy) ===")
    for col, vals in desc["resumen"].items():
        print(
            f"  {col:<20} -> Media: {vals['media']:>8.2f} | Mediana: {vals['mediana']:>8.2f} "
            f"| Desvío: {vals['desvio']:>8.2f} | Rango: [{vals['minimo']:.2f}, {vals['maximo']:.2f}]"
        )
    print(
        f"  Correlación Pearson (Precio vs. Unidades): r = {desc['pearsonPrecioUnidades']['r']:.4f} "
        f"(p-valor = {desc['pearsonPrecioUnidades']['pValor']:.4e})"
    )
    print(
        f"  ANOVA por Estación (Unidades)            : F = {desc['anovaEstacion']['fStat']:.2f} "
        f"(p-valor = {desc['anovaEstacion']['pValor']:.4e})"
    )

    print("\n=== Métricas clave OLS ===")
    print(f"R² (in-sample) : {metricas['r2']:.4f}")
    print(f"R² ajustado    : {metricas['r2Adj']:.4f}")
    print(f"R² (test 20%)  : {metricas['r2Test']:.4f}")
    print(f"MAE (test 20%) : {metricas['maeTest']:.2f} unidades")
    print(f"RMSE (test 20%): {metricas['rmseTest']:.2f} unidades")
    print(f"p-valor (F)    : {metricas['fPvalue']:.4e}")
    print(f"AIC            : {metricas['aic']:.2f}")
    print(f"BIC            : {metricas['bic']:.2f}")
    print("Coeficientes:")
    for variable, coef in metricas["coeficientes"].items():
        print(f"  {variable:<35} {coef:>10.4f}")

    print("\n=== Muestra de predicciones ===")
    print(
        dfPred[[COL_VARIETAL, COL_ESTACION, COL_CANAL, COL_PRECIO, COL_UNIDADES, COL_PREDICCION]]
        .head(10)
        .to_string()
    )

    print(f"\nAdvertencias durante la ejecución: {len(advertencias)}")
    for adv in advertencias:
        print(f"  - {adv.category.__name__}: {adv.message}")
