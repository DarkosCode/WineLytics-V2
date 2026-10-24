import os
import sys

#? Para que TensorFlow no llene la consola de carteles informativos al arrancar
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow import keras

#? Permite importar 'schema' aunque ejecutemos este archivo directo desde backend/
raizProyecto = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if raizProyecto not in sys.path:
    sys.path.insert(0, raizProyecto)

from schema.ventas import Ventas

COLUMNAS_CATEGORICAS = [Ventas.COL_CANAL, Ventas.COL_VARIETAL, Ventas.COL_ESTACION]

SEMILLA = 42
TAMANIO_TEST = 0.2
LEARNING_RATE = 0.01


def prepararVariables(df):
    #? Armamos la matriz X (Precio + dummies de Canal, Varietal y Estación) y el vector objetivo y (Unidades)
    dummies = pd.get_dummies(df[COLUMNAS_CATEGORICAS], drop_first=True, dtype=float)
    X = pd.concat([df[[Ventas.COL_PRECIOU]].astype(float), dummies], axis=1)
    y = df[Ventas.COL_UNIDADESV].astype(float)
    return X, y


def construirModelo(nFeatures):
    #? Red neuronal secuencial con 2 capas ocultas (32 y 16 neuronas con ReLU) y 1 salida lineal
    modelo = keras.Sequential([
        keras.layers.Input(shape=(nFeatures,)),
        keras.layers.Dense(32, activation="relu"),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(1, activation="linear")
    ])
    modelo.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss="mse",
        metrics=["mae"]
    )
    return modelo


def entrenarModeloDeepLearning(dfVentas, epochs=50, batchSize=32):
    #? Fijamos la semilla para que el entrenamiento dé siempre el mismo resultado
    keras.utils.set_random_seed(SEMILLA)

    X, y = prepararVariables(dfVentas.copy())

    #? Dividimos 80% para entrenar y 20% para probar
    XTrain, xTest, yTrain, yTest = train_test_split(
        X, y, test_size=TAMANIO_TEST, random_state=SEMILLA
    )

    #? Escalamos los datos para que la red neuronal entrene mejor (ajustando solo con los datos de train)
    scaler = StandardScaler()
    XTrain = scaler.fit_transform(XTrain)
    xTest = scaler.transform(xTest)

    modelo = construirModelo(XTrain.shape[1])

    #? Guardamos el scaler y las columnas dentro del modelo para usarlos después en agregarPrediccionesDL()
    modelo.scaler = scaler
    modelo.columnasX = list(X.columns)

    history = modelo.fit(
        XTrain,
        yTrain,
        epochs=epochs,
        batch_size=batchSize,
        validation_split=0.2,
        verbose=0
    )

    yPred = modelo.predict(xTest, verbose=0).flatten()

    metricasDict = {
        "r2": float(r2_score(yTest, yPred)),
        "mae": float(mean_absolute_error(yTest, yPred)),
        "rmse": float(np.sqrt(mean_squared_error(yTest, yPred)))
    }

    return modelo, history, metricasDict, (xTest, yTest, yPred)


def agregarPrediccionesDL(dfVentas, modelo):
    #? Calcula las predicciones de la red neuronal para todas las filas y las guarda en 'Prediccion_DL'
    dfResultado = dfVentas.copy()
    X, _ = prepararVariables(dfResultado)
    X = X.reindex(columns=modelo.columnasX, fill_value=0.0)
    xEscalado = modelo.scaler.transform(X)
    dfResultado[Ventas.COL_PREDICCION_DL] = modelo.predict(xEscalado, verbose=0).flatten()
    return dfResultado


if __name__ == "__main__":
    from sources.ventasCsv import cargarVentas

    df = cargarVentas()
    modelo, history, metricas, (xTest, yTest, yPred) = entrenarModeloDeepLearning(df)
    dfConDl = agregarPrediccionesDL(df, modelo)

    print("\n=== Resumen de la red neuronal ===")
    modelo.summary()

    print("\n=== Métricas en el conjunto de prueba (20%) ===")
    print(f"R²   : {metricas['r2']:.4f}")
    print(f"MAE  : {metricas['mae']:.2f} unidades")
    print(f"RMSE : {metricas['rmse']:.2f} unidades")
