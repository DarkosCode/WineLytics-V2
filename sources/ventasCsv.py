import os
import pandas as pd
from schema.ventas import Ventas

def cargarVentas():
    #? ↘ Esto asegura q se lea siempre bien la ruta, sea donde sea que estes parado
    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaCsv = os.path.join(baseDir, "data", "ventas.csv")

    if not os.path.exists(rutaCsv):
        raise FileNotFoundError(
            f"No se encontró '{rutaCsv}'. Primero hay que generar los datos con: python3 sources/generadorDeDatos.py"
        )

    dfCsv = pd.read_csv(rutaCsv)

    dfCsv = dfCsv.rename(columns={
        Ventas.CSV_FECHA: Ventas.COL_FECHA,
        Ventas.CSV_VARIETAL: Ventas.COL_VARIETAL,
        Ventas.CSV_LINEA: Ventas.COL_LINEA,
        Ventas.CSV_CANAL: Ventas.COL_CANAL,
        Ventas.CSV_UNIDADESV: Ventas.COL_UNIDADESV,
        Ventas.CSV_PRECIOU: Ventas.COL_PRECIOU
    })

    #? Limpiando y asegurando que no hayan valores nulos
    dfCsv[Ventas.COL_UNIDADESV] = dfCsv[Ventas.COL_UNIDADESV].fillna(0).astype(int)
    dfCsv[Ventas.COL_PRECIOU] = dfCsv[Ventas.COL_PRECIOU].fillna(0).astype(float)

    #? Sacamos filas duplicadas y nos quedamos solo con ventas donde unidades y precio sean mayores a 0
    dfCsv = dfCsv.drop_duplicates()
    dfCsv = dfCsv[(dfCsv[Ventas.COL_UNIDADESV] > 0) & (dfCsv[Ventas.COL_PRECIOU] > 0)].copy()

    #? Columna nueva de ingresos totales
    dfCsv[Ventas.COL_INGRESO] = dfCsv[Ventas.COL_UNIDADESV] * dfCsv[Ventas.COL_PRECIOU]

    #? Columna nueva de mes en español, extrayendo el número de mes de la columna fecha
    dfCsv[Ventas.COL_FECHA] = pd.to_datetime(dfCsv[Ventas.COL_FECHA])
    mesesEs = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    dfCsv[Ventas.COL_MES] = dfCsv[Ventas.COL_FECHA].dt.month.map(mesesEs)

    #? En la columna ESTACION, colocamos el resultado de pasarle el mes a Ventas.obtenerEstacion()
    dfCsv[Ventas.COL_ESTACION] = dfCsv[Ventas.COL_FECHA].dt.month.apply(Ventas.obtenerEstacion)

    return dfCsv
