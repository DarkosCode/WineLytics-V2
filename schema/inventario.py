class Inventario:
    """Esquema del dataset de inventario: nombres de columnas (normalizadas, derivadas y originales del CSV).

    Es la única fuente de verdad de los nombres de columna del inventario;
    el resto del proyecto los importa desde acá en lugar de repetir los textos.
    """

    #? Nombres de columnas ya normalizados (los que usa todo el proyecto)
    COL_VARIETAL = "Varietal"
    COL_LINEA = "Linea"
    COL_STOCK = "Stock Actual"
    COL_REPOSICION = "Punto de reposición"

    #? Columna derivada (se calcula en sources/inventarioCsv.py)
    COL_REPOSICION_NECESARIA = "Reposicion Necesaria"

    #? Encabezados originales de data/inventario.csv (los escribe sources/generadorDeDatos.py)
    CSV_VARIETAL = "Varietal"
    CSV_LINEA = "Linea"
    CSV_STOCK = "Stock_Actual"
    CSV_REPOSICION = "Punto_Reposicion"
