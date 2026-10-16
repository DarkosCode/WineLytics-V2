import os
import pandas as pd
from schema.ventas import Ventas

def cargarVentas():
    #? ↘ Esto asegura q se lea siempre bien la ruta, sea donde sea que estes parado
    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaCsv = os.path.join(baseDir, "data", "ventas.csv")
    
    dfCsv = pd.read_csv(rutaCsv) 
    
    dfCsv = dfCsv.rename(columns={Ventas.CSV_FECHA: Ventas.COL_FECHA,
                              Ventas.CSV_VARIETAL: Ventas.COL_VARIETAL,
                              Ventas.CSV_LINEA: Ventas.COL_LINEA,
                              Ventas.CSV_CANAL: Ventas.COL_CANAL,
                              Ventas.CSV_UNIDADESV: Ventas.COL_UNIDADESV, 
                              Ventas.CSV_PRECIOU: Ventas.COL_PRECIOU}) 
    
    #? Limpiando y asegurando que no hayan valores nulos
    dfCsv[Ventas.COL_UNIDADESV] = dfCsv[Ventas.COL_UNIDADESV].fillna(0).astype(int)
    dfCsv[Ventas.COL_PRECIOU] = dfCsv[Ventas.COL_PRECIOU].fillna(0).astype(float)
    
    #? Columa nueva de ingresos totales
    dfCsv[Ventas.COL_INGRESO] = dfCsv[Ventas.COL_UNIDADESV] * dfCsv[Ventas.COL_PRECIOU]
    
    #? Colunna nueva de mes, extrayeeendo los datos de la columna fecha
    dfCsv[Ventas.COL_FECHA] = pd.to_datetime(dfCsv[Ventas.COL_FECHA])
    dfCsv[Ventas.COL_MES] = dfCsv[Ventas.COL_FECHA].dt.month_name()
    
    #? Columna nueva de Estacion (teniendo en cuenta Argentina/Sudamerica)
    def obtenerEstacion(mes):
        if mes in [12, 1, 2]:
            return 'Verano'
        elif mes in [3, 4, 5]:
            return 'Otoño'
        elif mes in [6, 7, 8]:
            return 'Invierno'
        else:
            return 'Primavera'
    
    #? En la columna ESTACION, colocamos el resultado de pasarle a todos los valores de la columna FECHA
    #? la funcion de obtenerEstacion()
    dfCsv[Ventas.COL_ESTACION] = dfCsv[Ventas.COL_FECHA].dt.month.apply(obtenerEstacion)
    
    return dfCsv