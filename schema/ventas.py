class Ventas:
    #? Nombres de columnas ya normalizados (los que usa todo el proyecto)
    COL_FECHA = "Fecha"
    COL_VARIETAL = "Varietal"
    COL_LINEA = "Linea"
    COL_CANAL = "Canal de Venta"
    COL_UNIDADESV = "Unidades Vendidas"
    COL_PRECIOU = "Precio Unitario"
    COL_ESTACION = "Estacion"

    #? Columnas derivadas (se calculan en sources/ventasCsv.py y backend/)
    COL_INGRESO = "Ingreso Total"
    COL_MES = "Mes"
    COL_PREDICCION = "Prediccion_Ventas"
    COL_PREDICCION_DL = "Prediccion_DL"

    #? Encabezados originales de data/ventas.csv (los escribe sources/generadorDeDatos.py)
    CSV_FECHA = "Fecha"
    CSV_VARIETAL = "Varietal"
    CSV_LINEA = "Linea"
    CSV_CANAL = "Canal"
    CSV_UNIDADESV = "Unidades_Vendidas"
    CSV_PRECIOU = "Precio_Unitario"