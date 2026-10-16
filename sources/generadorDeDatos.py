import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime, timedelta

#? Permite importar 'schema' aunque se ejecute como 'python3 sources/generadorDeDatos.py'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.ventas import Ventas
from schema.inventario import Inventario

#! Archivo para la generacion del dataset a trabajar luego, creado con ayuda de la IA Gemini con reglas y pedidos especificos
#! Teniendo en cuenta la estructura del proyecto definida en base a las clases de Programacion (sobretodo la clase donde 
#! se vio todo lo de pacientes, schema, etc.)

# Determinar la raíz del proyecto (un nivel arriba de 'sources/')
#? Esto es para que si se ejecuta desde otro lado, o desde otra carpeta, nos aseguremos de que igual siempre salga bien
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

SEMILLA = 42

#! Configuración de parámetros de negocio de la Bodega
varietales = ['Malbec', 'Cabernet Sauvignon', 'Tempranillo', 'Torrontés'] #? 4 varietales de vino máximos
lineas = ['Joven', 'Reserva', 'Gran Reserva'] #? Lineas pensadas segun maduracion (tiempo) del vino
canales = ['Mercado Interno', 'Exportación'] #? Canales de venta, impacto en el precio

#! Parámetros del modelo de demanda (cómo se generan las 'Unidades Vendidas')
#? Relación inversa con el precio: unidadesEsperadas = UNIDADES_BASE - PENDIENTE_PRECIO * precio
#? Ej: un Joven local (~8 USD) espera ~222 botellas, un Gran Reserva de exportación (~45 USD) ~92
UNIDADES_BASE = 250.0
PENDIENTE_PRECIO = 3.5
#? Multiplicadores estacionales (misma definición de estaciones que sources.ventasCsv.py)
FACTOR_TINTOS_INVIERNO = 1.5   # Malbec y Cabernet Sauvignon en Invierno
FACTOR_TORRONTES_VERANO = 1.6  # Torrontés en Verano
#? Ruido gaussiano para que los datos no sean perfectamente deterministas
DESVIO_RUIDO = 20.0
#? Piso de unidades por transacción (siempre enteros positivos)
UNIDADES_MINIMAS = 20


def obtenerEstacion(mes: int) -> str:
    """Devuelve la estación (hemisferio sur) para un número de mes.

    Usa exactamente la misma regla que `cargarVentas()` en sources.ventasCsv.py,
    para que el efecto estacional generado coincida con la columna 'Estacion'.
    """
    if mes in [12, 1, 2]:
        return 'Verano'
    elif mes in [3, 4, 5]:
        return 'Otoño'
    elif mes in [6, 7, 8]:
        return 'Invierno'
    else:
        return 'Primavera'


def calcularPrecioUnitario(lin: str, canal: str) -> float:
    """Calcula el precio unitario según la línea y el canal, con una variación de ±5%."""
    #! Definición de Precios Base (Escala homogénea en USD equivalentes para comparar rentabilidad)
    if lin == 'Gran Reserva':
        precioBase = 45.0 if canal == 'Exportación' else 30.0
    elif lin == 'Reserva':
        precioBase = 22.0 if canal == 'Exportación' else 15.0
    else: 
        precioBase = 12.0 if canal == 'Exportación' else 8.0
    #? Es decir siempre es mas barato a la venta local
        
    # Genera un factor al azar entre 0.95 (95%) y 1.05 (105%)
    factorVariacion = np.random.uniform(0.95, 1.05)
    # Se lo aplicamos al precio base
    return round(precioBase * factorVariacion, 2)


def calcularUnidadesVendidas(precioUnitario: float, var: str, estacion: str) -> int:
    """Genera las unidades vendidas de una transacción a partir de variables de negocio.

    1. Demanda base con relación inversa al precio (a mayor precio, menos botellas).
    2. Efecto estacional: tintos fuertes en Invierno y Torrontés en Verano.
    3. Ruido gaussiano para darle realismo.
    4. Redondeo a entero con un mínimo de UNIDADES_MINIMAS.
    """
    unidadesEsperadas = UNIDADES_BASE - PENDIENTE_PRECIO * precioUnitario

    # Simulación de estacionalidad real mendocina según la estación
    factorEstacional = 1.0
    if estacion == 'Verano' and var == 'Torrontés': # El blanco explota en verano
        factorEstacional = FACTOR_TORRONTES_VERANO
    elif estacion == 'Invierno' and var in ['Malbec', 'Cabernet Sauvignon']: # Los tintos pesan más en invierno
        factorEstacional = FACTOR_TINTOS_INVIERNO
    unidadesEsperadas *= factorEstacional

    ruido = np.random.normal(0, DESVIO_RUIDO)

    # Cantidades vendidas (En botellas individuales)
    return max(UNIDADES_MINIMAS, int(round(unidadesEsperadas + ruido)))


def generarInventario() -> pd.DataFrame:
    """Genera el dataset de inventario (stock actual en depósito)."""
    #! --- GENERACIÓN DEL INVENTARIO (dataset; stock actual en depósito) ---
    inventarioList = []
    for var in varietales:
        for lin in lineas:
            # Lógica de negocio: Las líneas premium tienen menos stock físico y umbrales más altos
            if lin == 'Gran Reserva':
                stockActual = np.random.randint(1500, 4000)
                puntoReposicion = 2500  # Requiere más tiempo de anticipación por la crianza
            elif lin == 'Reserva':
                stockActual = np.random.randint(4000, 9000)
                puntoReposicion = 3500
            else: # Joven
                stockActual = np.random.randint(8000, 20000)
                puntoReposicion = 5000  # Alta rotación, reposición estándar

            inventarioList.append({
                Inventario.CSV_VARIETAL: var,
                Inventario.CSV_LINEA: lin,
                Inventario.CSV_STOCK: stockActual,
                Inventario.CSV_REPOSICION: puntoReposicion
            })

    return pd.DataFrame(inventarioList)


def generarVentas(nVentas: int = 1200) -> pd.DataFrame:
    """Genera el histórico de ventas con unidades correlacionadas a precio y estación."""
    #! --- GENERACIÓN DE HISTÓRICO DE VENTAS (1200 registros para poblar los gráficos) ---
    # Generar fechas aleatorias a lo largo de todo el año 2025 (para capturar estacionalidad mensual)
    fechaInicio = datetime(2025, 1, 1)
    fechas = [fechaInicio + timedelta(days=int(np.random.randint(0, 365))) for _ in range(nVentas)]

    ventasList = []
    for i in range(nVentas):
        fecha = fechas[i]
        var = np.random.choice(varietales)
        lin = np.random.choice(lineas)
        canal = np.random.choice(canales, p=[0.6, 0.4]) # 60% consumo local, 40% exportación

        #? Primero el precio, porque las unidades dependen de él
        precioUnitario = calcularPrecioUnitario(lin, canal)
        estacion = obtenerEstacion(fecha.month)
        unidadesVendidas = calcularUnidadesVendidas(precioUnitario, var, estacion)

        ventasList.append({
            Ventas.CSV_FECHA: fecha.strftime('%Y-%m-%d'),
            Ventas.CSV_VARIETAL: var,
            Ventas.CSV_LINEA: lin,
            Ventas.CSV_CANAL: canal,
            Ventas.CSV_UNIDADESV: unidadesVendidas,
            Ventas.CSV_PRECIOU: precioUnitario
        })

    dfVentas = pd.DataFrame(ventasList)
    # Ordenar cronológicamente las ventas para que los gráficos temporales tengan sentido directo
    return dfVentas.sort_values(Ventas.CSV_FECHA).reset_index(drop=True)


def main() -> None:
    """Regenera data/inventario.csv y data/ventas.csv de forma reproducible."""
    # 1. Crear la carpeta 'data' en la raíz del proyecto
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fijar semilla para reproducibilidad (Esto garantiza que la aleatoriedad sea idéntica siempre)
    #? Se fija acá y se genera el inventario primero, igual que antes, para que inventario.csv no cambie
    np.random.seed(SEMILLA)

    dfInventario = generarInventario()
    # Guardar inventario usando DATA_DIR
    inventarioPath = os.path.join(DATA_DIR, 'inventario.csv')
    dfInventario.to_csv(inventarioPath, index=False)
    print(f"✅ Archivo '{inventarioPath}' creado con éxito.")

    nVentas = 1200
    print(f"⏳ Generando histórico de ventas ({nVentas} transacciones)...")
    dfVentas = generarVentas(nVentas)
    # Guardar ventas usando DATA_DIR
    ventasPath = os.path.join(DATA_DIR, 'ventas.csv')
    dfVentas.to_csv(ventasPath, index=False)
    print(f"✅ Archivo '{ventasPath}' creado con éxito.")
    print("\n🎉 ¡Listo! Datos sintéticos generados en la raíz del proyecto.")


if __name__ == "__main__":
    main()
