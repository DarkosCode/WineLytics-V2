import os
import pandas as pd
import numpy as np
from schema.inventario import Inventario

def cargarInventario():
    """Lee data/inventario.csv y lo devuelve limpio y enriquecido, listo para analizar.

    Pasos: renombra los encabezados al esquema del proyecto (schema/inventario.py), reemplaza nulos,
    elimina duplicados por (Varietal, Línea), descarta stock negativo y agrega la columna
    'Reposicion Necesaria' ("SI" si el stock está por debajo del punto de reposición, "NO" si no).

    Returns:
        DataFrame de inventario limpio.

    Raises:
        FileNotFoundError: Si data/inventario.csv no existe (hay que correr sources/generadorDeDatos.py).
    """
    #? ↘ Esto asegura q se lea siempre bien la ruta, sea donde sea que estes parado
    baseDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rutaCsv = os.path.join(baseDir, "data", "inventario.csv")

    if not os.path.exists(rutaCsv):
        raise FileNotFoundError(
            f"No se encontró '{rutaCsv}'. Generá los datos primero con: python3 sources/generadorDeDatos.py"
        )
    
    dfCsv = pd.read_csv(rutaCsv)
    
    #? Renombrar columnas para que coincidan con el 'schema'
    dfCsv = dfCsv.rename(columns={Inventario.CSV_VARIETAL: Inventario.COL_VARIETAL,
                                  Inventario.CSV_LINEA: Inventario.COL_LINEA,
                                  Inventario.CSV_STOCK: Inventario.COL_STOCK,
                                  Inventario.CSV_REPOSICION: Inventario.COL_REPOSICION})     
    
    #? Limpieza de nulos, convertidor de valores float
    dfCsv[Inventario.COL_STOCK] = dfCsv[Inventario.COL_STOCK].fillna(0).astype(int)
    dfCsv[Inventario.COL_REPOSICION] = dfCsv[Inventario.COL_REPOSICION].fillna(0).astype(int)
        #* Ayudita propia de memoria; el metodo fillna() solo va a convertir a 0 los valores NaN

    #? Eliminación de duplicados por clave de producto (Varietal + Línea) y validación de stock no negativo
    dfCsv = dfCsv.drop_duplicates(subset=[Inventario.COL_VARIETAL, Inventario.COL_LINEA])
    dfCsv = dfCsv[dfCsv[Inventario.COL_STOCK] >= 0].copy()

    #? Columna agregada, que dice si se necesita reposicion, teniendo en cuenta el stock y el punto
    dfCsv[Inventario.COL_REPOSICION_NECESARIA] = np.where(
        dfCsv[Inventario.COL_STOCK] < dfCsv[Inventario.COL_REPOSICION], "SI", "NO")

    return dfCsv
