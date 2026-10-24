import os
import sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

#? Permite importar 'schema' aunque se ejecute directo como 'python3 sources/generadorDeDatos.py'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.ventas import Ventas
from schema.inventario import Inventario

#! Archivo para la generacion del dataset a trabajar luego, creado con ayuda de la IA con reglas y pedidos especificos
#! Teniendo en cuenta la estructura del proyecto definida en base a las clases de Programacion (sobretodo la clase donde
#! se vio todo lo de pacientes, schema, etc.)

#? Esto es para que si se ejecuta desde otro lado, o desde otra carpeta, nos aseguremos de que igual siempre salga bien
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

SEMILLA = 42

#! Configuración de parámetros de negocio de la Bodega
varietales = ["Malbec", "Cabernet Sauvignon", "Tempranillo", "Torrontés"] #? 4 varietales de vino máximos
lineas = ["Joven", "Reserva", "Gran Reserva"] #? Lineas pensadas segun maduracion (tiempo) del vino
canales = ["Mercado Interno", "Exportación"] #? Canales de venta, impacto en el precio

#! Parámetros para simular las 'Unidades Vendidas'
#? Relación inversa con el precio: a más precio, menos unidades base se venden
UNIDADES_BASE = 250.0
PENDIENTE_PRECIO = 3.5
FACTOR_TINTOS_INVIERNO = 1.5   # Malbec y Cabernet Sauvignon se venden más en Invierno
FACTOR_TORRONTES_VERANO = 1.6  # El Torrontés se vende más en Verano
DESVIO_RUIDO = 20.0
UNIDADES_MINIMAS = 20


def calcularPrecioUnitario(lin, canal):
    #! Definición de Precios Base en USD equivalentes según línea y canal
    if lin == "Gran Reserva":
        precioBase = 45.0 if canal == "Exportación" else 30.0
    elif lin == "Reserva":
        precioBase = 22.0 if canal == "Exportación" else 15.0
    else:
        precioBase = 12.0 if canal == "Exportación" else 8.0
    #? Es decir siempre es mas barato a la venta local

    # Genera un factor al azar entre 0.95 (95%) y 1.05 (105%) y se lo aplica al precio base
    factorVariacion = np.random.uniform(0.95, 1.05)
    return round(precioBase * factorVariacion, 2)


def calcularUnidadesVendidas(precioUnitario, var, estacion):
    #? Calculamos las unidades base según el precio y después le aplicamos la estación y un poco de ruido aleatorio
    unidadesEsperadas = UNIDADES_BASE - PENDIENTE_PRECIO * precioUnitario

    # Simulación de estacionalidad mendocina según la estación
    factorEstacional = 1.0
    if estacion == "Verano" and var == "Torrontés": # El blanco explota en verano
        factorEstacional = FACTOR_TORRONTES_VERANO
    elif estacion == "Invierno" and var in ["Malbec", "Cabernet Sauvignon"]: # Los tintos pesan más en invierno
        factorEstacional = FACTOR_TINTOS_INVIERNO
    unidadesEsperadas *= factorEstacional

    ruido = np.random.normal(0, DESVIO_RUIDO)
    return max(UNIDADES_MINIMAS, int(round(unidadesEsperadas + ruido)))


def generarInventario():
    #! --- GENERACIÓN DEL INVENTARIO (dataset; stock actual en depósito) ---
    inventarioList = []
    for var in varietales:
        for lin in lineas:
            # Lógica de negocio: Las líneas premium tienen menos stock físico y umbrales más altos
            if lin == "Gran Reserva":
                stockActual = np.random.randint(1500, 4000)
                puntoReposicion = 2500  # Requiere más tiempo de anticipación por la crianza
            elif lin == "Reserva":
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


def generarVentas(nVentas=1200):
    #! --- GENERACIÓN DE HISTÓRICO DE VENTAS (1200 registros para poblar los gráficos) ---
    fechaInicio = datetime(2025, 1, 1)
    fechas = [fechaInicio + timedelta(days=int(np.random.randint(0, 365))) for _ in range(nVentas)]

    ventasList = []
    for i in range(nVentas):
        fecha = fechas[i]
        var = np.random.choice(varietales)
        lin = np.random.choice(lineas)
        canal = np.random.choice(canales, p=[0.6, 0.4]) # 60% consumo local, 40% exportación

        #? Primero calculamos el precio, porque las unidades dependen de él
        precioUnitario = calcularPrecioUnitario(lin, canal)
        estacion = Ventas.obtenerEstacion(fecha.month)
        unidadesVendidas = calcularUnidadesVendidas(precioUnitario, var, estacion)

        ventasList.append({
            Ventas.CSV_FECHA: fecha.strftime("%Y-%m-%d"),
            Ventas.CSV_VARIETAL: var,
            Ventas.CSV_LINEA: lin,
            Ventas.CSV_CANAL: canal,
            Ventas.CSV_UNIDADESV: unidadesVendidas,
            Ventas.CSV_PRECIOU: precioUnitario
        })

    dfVentas = pd.DataFrame(ventasList)
    # Ordenar cronológicamente las ventas para que los gráficos temporales tengan sentido directo
    return dfVentas.sort_values(Ventas.CSV_FECHA).reset_index(drop=True)


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fijar semilla para reproducibilidad (garantiza que los datos generados sean siempre los mismos)
    np.random.seed(SEMILLA)

    dfInventario = generarInventario()
    inventarioPath = os.path.join(DATA_DIR, "inventario.csv")
    dfInventario.to_csv(inventarioPath, index=False)
    print(f"Archivo '{inventarioPath}' creado con éxito.")

    nVentas = 1200
    print(f"Generando histórico de ventas ({nVentas} transacciones)...")
    dfVentas = generarVentas(nVentas)
    ventasPath = os.path.join(DATA_DIR, "ventas.csv")
    dfVentas.to_csv(ventasPath, index=False)
    print(f"Archivo '{ventasPath}' creado con éxito.")
    print("\nListo! Datos sintéticos generados en la carpeta data/ del proyecto.")


if __name__ == "__main__":
    main()
