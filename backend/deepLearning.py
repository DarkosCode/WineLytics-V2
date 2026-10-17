"""
Módulo de Aprendizaje Profundo (Deep Learning) de WineLytics.

Entrena una red neuronal densa (Keras / TensorFlow) para estimar las
'Unidades Vendidas' a partir del 'Precio Unitario', el 'Canal de Venta',
el 'Varietal' y la 'Estacion' del año.

Arquitectura: Dense(32, relu) -> Dense(16, relu) -> Dense(1, lineal).
"""

from __future__ import annotations

import os
import sys

#? Reduce el ruido de logs informativos de TensorFlow (debe fijarse antes de importarlo)
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow import keras

#? Permite importar 'schema' y 'sources' aunque el script se ejecute directamente desde backend/
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
COL_PREDICCION_DL: str = Ventas.COL_PREDICCION_DL

#? Variables categóricas que se transforman en dummies (One-Hot Encoding)
COLUMNAS_CATEGORICAS: List[str] = [COL_CANAL, COL_VARIETAL, COL_ESTACION]

COLUMNAS_REQUERIDAS: List[str] = [COL_UNIDADES, COL_PRECIO, *COLUMNAS_CATEGORICAS]

SEMILLA: int = 42
TAMANIO_TEST: float = 0.2
LEARNING_RATE: float = 0.01


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


def _prepararVariables(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Construye la matriz de features ``X`` y el target ``y``.

    - ``y``: 'Unidades Vendidas'.
    - ``X``: 'Precio Unitario' + dummies de 'Canal de Venta', 'Varietal' y
      'Estacion' (``drop_first=True``).

    Args:
        df: DataFrame de ventas ya validado.

    Returns:
        Tupla ``(X, y)``.
    """
    dummies = pd.get_dummies(df[COLUMNAS_CATEGORICAS], drop_first=True, dtype=float)
    X = pd.concat([df[[COL_PRECIO]].astype(float), dummies], axis=1)
    y = df[COL_UNIDADES].astype(float)
    return X, y


def _construirModelo(nFeatures: int) -> keras.Sequential:
    """Crea y compila la red neuronal de regresión.

    Args:
        nFeatures: Cantidad de variables de entrada.

    Returns:
        Modelo Keras Sequential compilado (adam, mse, mae).
    """
    modelo = keras.Sequential([
        keras.layers.Input(shape=(nFeatures,)),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1, activation="linear"),
    ])
    modelo.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="mse",
        metrics=["mae"],
    )
    return modelo


def entrenarModeloDeepLearning(
    dfVentas: pd.DataFrame,
    epochs: int = 50,
    batchSize: int = 32,
) -> Tuple[keras.Sequential, keras.callbacks.History, Dict[str, float], Tuple[np.ndarray, pd.Series, np.ndarray]]:
    """Entrena una red neuronal para estimar las unidades vendidas.

    Pasos: validación de columnas, One-Hot Encoding, split 80/20,
    escalado con ``StandardScaler`` (ajustado solo en train), entrenamiento
    con ``validation_split=0.2`` y evaluación sobre el conjunto de prueba.

    Args:
        dfVentas: DataFrame con, al menos, las columnas 'Unidades Vendidas',
            'Precio Unitario', 'Canal de Venta', 'Varietal' y 'Estacion'
            (esta última la genera ``sources.ventasCsv.cargarVentas``).
        epochs: Cantidad de épocas de entrenamiento.
        batchSize: Tamaño del lote.

    Returns:
        Tupla ``(modelo, history, metricasDict, (xTest, yTest, yPred))`` donde:
            - ``modelo``: red neuronal entrenada (incluye atributos ``_scaler``
              y ``_columnasX`` para predecir sobre nuevos datos).
            - ``history``: historial de entrenamiento de Keras.
            - ``metricasDict``: diccionario con ``r2``, ``mae`` y ``rmse``
              calculados sobre el conjunto de prueba.
            - ``xTest``: features de prueba escaladas.
            - ``yTest``: valores reales de prueba.
            - ``yPred``: predicciones sobre el conjunto de prueba.

    Raises:
        ValueError: Si faltan columnas requeridas en ``dfVentas``.
    """
    _validarColumnas(dfVentas)

    #? Semilla reproducible (Python, NumPy y TensorFlow)
    keras.utils.set_random_seed(SEMILLA)

    X, y = _prepararVariables(dfVentas.copy())

    XTrain, xTest, yTrain, yTest = train_test_split(
        X, y, test_size=TAMANIO_TEST, random_state=SEMILLA
    )

    #? El scaler se ajusta solo con train para no filtrar información del test
    scaler = StandardScaler()
    XTrain = scaler.fit_transform(XTrain)
    xTest = scaler.transform(xTest)

    modelo = _construirModelo(XTrain.shape[1])

    #? Guardamos scaler y columnas en el modelo para poder predecir sobre cualquier DataFrame luego
    modelo._scaler = scaler  # type: ignore[attr-defined]
    modelo._columnasX = list(X.columns)  # type: ignore[attr-defined]

    history = modelo.fit(
        XTrain,
        yTrain,
        epochs=epochs,
        batch_size=batchSize,
        validation_split=0.2,
        verbose=0,
    )

    yPred = modelo.predict(xTest, verbose=0).flatten()

    metricasDict: Dict[str, float] = {
        "r2": float(r2_score(yTest, yPred)),
        "mae": float(mean_absolute_error(yTest, yPred)),
        "rmse": float(np.sqrt(mean_squared_error(yTest, yPred))),
    }

    return modelo, history, metricasDict, (xTest, yTest, yPred)


def agregarPrediccionesDL(
    dfVentas: pd.DataFrame,
    modelo: keras.Sequential,
) -> pd.DataFrame:
    """Agrega la columna 'Prediccion_DL' a una copia de ``dfVentas`` usando el modelo entrenado.

    Args:
        dfVentas: DataFrame de ventas con las columnas requeridas.
        modelo: Red neuronal devuelta por ``entrenarModeloDeepLearning``.

    Returns:
        Copia de ``dfVentas`` con la columna ``Prediccion_DL``.
    """
    _validarColumnas(dfVentas)
    dfResultado = dfVentas.copy()
    X, _ = _prepararVariables(dfResultado)
    X = X.reindex(columns=modelo._columnasX, fill_value=0.0)  # type: ignore[attr-defined]
    xEscalado = modelo._scaler.transform(X)  # type: ignore[attr-defined]
    dfResultado[COL_PREDICCION_DL] = modelo.predict(xEscalado, verbose=0).flatten()
    return dfResultado


if __name__ == "__main__":
    from sources.ventasCsv import cargarVentas

    #? cargarVentas() es la fuente oficial: renombra columnas y crea 'Estacion'
    df = cargarVentas()
    modelo, history, metricas, (xTest, yTest, yPred) = entrenarModeloDeepLearning(df)
    dfConDl = agregarPrediccionesDL(df, modelo)

    print("\n=== Resumen de la red neuronal ===")
    modelo.summary()

    print("\n=== Métricas en el conjunto de prueba ===")
    print(f"R²   : {metricas['r2']:.4f}")
    print(f"MAE  : {metricas['mae']:.2f} unidades")
    print(f"RMSE : {metricas['rmse']:.2f} unidades")

    print("\n=== Muestra de predicciones (real vs. estimado en test) ===")
    for real, pred in list(zip(yTest, yPred))[:10]:
        print(f"  Real: {real:>6.0f}   Estimado: {pred:>8.2f}")
