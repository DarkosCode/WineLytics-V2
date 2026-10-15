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

import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper

#? Nombres de columnas (coinciden con schema/ventas.py)
COL_UNIDADES: str = "Unidades Vendidas"
COL_PRECIO: str = "Precio Unitario"
COL_CANAL: str = "Canal de Venta"
COL_VARIETAL: str = "Varietal"
COL_ESTACION: str = "Estacion"
COL_PREDICCION: str = "Prediccion_Ventas"

#? Variables categóricas que se transforman en dummies
COLUMNAS_CATEGORICAS: List[str] = [COL_CANAL, COL_VARIETAL, COL_ESTACION]

COLUMNAS_REQUERIDAS: List[str] = [COL_UNIDADES, COL_PRECIO, *COLUMNAS_CATEGORICAS]


def _validar_columnas(df: pd.DataFrame) -> None:
    """Verifica que el DataFrame tenga todas las columnas necesarias.

    Args:
        df: DataFrame de ventas a validar.

    Raises:
        ValueError: Si falta alguna de las columnas requeridas.
    """
    faltantes = [col for col in COLUMNAS_REQUERIDAS if col not in df.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas en df_ventas: {faltantes}")


def _preparar_variables(df: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
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


def ejecutar_analisis_estadistico(
    df_ventas: pd.DataFrame,
) -> Tuple[pd.DataFrame, Dict[str, Any], RegressionResultsWrapper]:
    """Ajusta un modelo OLS sobre las ventas y genera predicciones y métricas.

    Modelo:
        Unidades Vendidas ~ const + Precio Unitario + dummies(Canal de Venta)
                            + dummies(Varietal) + dummies(Estacion)

    Args:
        df_ventas: DataFrame con, al menos, las columnas 'Unidades Vendidas',
            'Precio Unitario', 'Canal de Venta', 'Varietal' y 'Estacion'
            (esta última la genera ``sources.ventas_csv.cargarVentas``).

    Returns:
        Tupla ``(df_ventas, metricas_dict, modelo)`` donde:
            - ``df_ventas``: copia del DataFrame de entrada con la columna
              nueva 'Prediccion_Ventas'.
            - ``metricas_dict``: diccionario con ``r2``, ``r2_adj``,
              ``f_pvalue``, ``aic``, ``bic`` y ``coeficientes``
              (``{variable: valor}``).
            - ``modelo``: resultado ajustado de ``sm.OLS(...).fit()``.

    Raises:
        ValueError: Si faltan columnas requeridas en ``df_ventas``.
    """
    _validar_columnas(df_ventas)

    #? Trabajamos sobre una copia para no modificar el DataFrame original
    df_resultado = df_ventas.copy()

    y, X = _preparar_variables(df_resultado)
    modelo: RegressionResultsWrapper = sm.OLS(y, X).fit()

    print(modelo.summary())

    df_resultado[COL_PREDICCION] = modelo.predict(X)

    metricas_dict: Dict[str, Any] = {
        "r2": float(modelo.rsquared),
        "r2_adj": float(modelo.rsquared_adj),
        "f_pvalue": float(modelo.f_pvalue),
        "aic": float(modelo.aic),
        "bic": float(modelo.bic),
        "coeficientes": {var: float(coef) for var, coef in modelo.params.items()},
    }

    return df_resultado, metricas_dict, modelo


if __name__ == "__main__":
    import os
    import sys
    import warnings

    #? Agregamos la raíz del proyecto al path para poder importar 'sources'
    #? aunque el script se ejecute directamente desde backend/
    RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if RAIZ_PROYECTO not in sys.path:
        sys.path.insert(0, RAIZ_PROYECTO)

    #? cargarVentas() es la fuente oficial: renombra columnas y crea 'Estacion'
    from sources.ventas_csv import cargarVentas

    #? Capturamos cualquier advertencia para confirmar que el análisis corre limpio
    with warnings.catch_warnings(record=True) as advertencias:
        warnings.simplefilter("always")
        df = cargarVentas()
        df_pred, metricas, _ = ejecutar_analisis_estadistico(df)

    print("\n=== Métricas clave ===")
    print(f"R²          : {metricas['r2']:.4f}")
    print(f"R² ajustado : {metricas['r2_adj']:.4f}")
    print(f"p-valor (F) : {metricas['f_pvalue']:.4e}")
    print(f"AIC         : {metricas['aic']:.2f}")
    print(f"BIC         : {metricas['bic']:.2f}")
    print("Coeficientes:")
    for variable, coef in metricas["coeficientes"].items():
        print(f"  {variable:<35} {coef:>10.4f}")

    print("\n=== Muestra de predicciones ===")
    print(
        df_pred[[COL_VARIETAL, COL_ESTACION, COL_CANAL, COL_PRECIO, COL_UNIDADES, COL_PREDICCION]]
        .head(10)
        .to_string()
    )

    print(f"\nAdvertencias durante la ejecución: {len(advertencias)}")
    for adv in advertencias:
        print(f"  - {adv.category.__name__}: {adv.message}")
