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

import pandas as pd
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
COL_CANAL: str = Ventas.COL_CANAL
COL_VARIETAL: str = Ventas.COL_VARIETAL
COL_ESTACION: str = Ventas.COL_ESTACION
COL_PREDICCION: str = Ventas.COL_PREDICCION

#? Variables categóricas que se transforman en dummies
COLUMNAS_CATEGORICAS: List[str] = [COL_CANAL, COL_VARIETAL, COL_ESTACION]

COLUMNAS_REQUERIDAS: List[str] = [COL_UNIDADES, COL_PRECIO, *COLUMNAS_CATEGORICAS]


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
            - ``metricasDict``: diccionario con ``r2``, ``r2Adj``,
              ``fPvalue``, ``aic``, ``bic`` y ``coeficientes``
              (``{variable: valor}``).
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

    metricasDict: Dict[str, Any] = {
        "r2": float(modelo.rsquared),
        "r2Adj": float(modelo.rsquared_adj),
        "fPvalue": float(modelo.f_pvalue),
        "aic": float(modelo.aic),
        "bic": float(modelo.bic),
        "coeficientes": {var: float(coef) for var, coef in modelo.params.items()},
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

    print("\n=== Métricas clave ===")
    print(f"R²          : {metricas['r2']:.4f}")
    print(f"R² ajustado : {metricas['r2Adj']:.4f}")
    print(f"p-valor (F) : {metricas['fPvalue']:.4e}")
    print(f"AIC         : {metricas['aic']:.2f}")
    print(f"BIC         : {metricas['bic']:.2f}")
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
