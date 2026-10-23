class Ventas:
    """Esquema del dataset de ventas: nombres de columnas y reglas de negocio compartidas.

    Es la única fuente de verdad de los nombres de columna del histórico de ventas;
    el resto del proyecto los importa desde acá en lugar de repetir los textos.
    """

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

    #? Estaciones en orden 'cronológico' (hemisferio sur), usado al ordenar ejes y filtros de los gráficos
    ORDEN_ESTACIONES = ["Verano", "Otoño", "Invierno", "Primavera"]

    @staticmethod
    def obtenerEstacion(mes: int) -> str:
        """Devuelve la estación del año (Argentina / hemisferio sur) para un número de mes (1-12).

        Es la única definición de estaciones del proyecto: la usan tanto el generador de datos
        como la carga de ventas, para que el efecto estacional generado coincida con la columna 'Estacion'.
        """
        if mes in [12, 1, 2]:
            return 'Verano'
        elif mes in [3, 4, 5]:
            return 'Otoño'
        elif mes in [6, 7, 8]:
            return 'Invierno'
        else:
            return 'Primavera'
