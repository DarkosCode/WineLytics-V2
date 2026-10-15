import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

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
#? Relación inversa con el precio: unidades_esperadas = UNIDADES_BASE - PENDIENTE_PRECIO * precio
#? Ej: un Joven local (~8 USD) espera ~222 botellas, un Gran Reserva de exportación (~45 USD) ~92
UNIDADES_BASE = 250.0
PENDIENTE_PRECIO = 3.5
#? Multiplicadores estacionales (misma definición de estaciones que sources/ventas_csv.py)
FACTOR_TINTOS_INVIERNO = 1.5   # Malbec y Cabernet Sauvignon en Invierno
FACTOR_TORRONTES_VERANO = 1.6  # Torrontés en Verano
#? Ruido gaussiano para que los datos no sean perfectamente deterministas
DESVIO_RUIDO = 20.0
#? Piso de unidades por transacción (siempre enteros positivos)
UNIDADES_MINIMAS = 20


def obtener_estacion(mes: int) -> str:
    """Devuelve la estación (hemisferio sur) para un número de mes.

    Usa exactamente la misma regla que `cargarVentas()` en sources/ventas_csv.py,
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


def calcular_precio_unitario(lin: str, canal: str) -> float:
    """Calcula el precio unitario según la línea y el canal, con una variación de ±5%."""
    #! Definición de Precios Base (Escala homogénea en USD equivalentes para comparar rentabilidad)
    if lin == 'Gran Reserva':
        precio_base = 45.0 if canal == 'Exportación' else 30.0
    elif lin == 'Reserva':
        precio_base = 22.0 if canal == 'Exportación' else 15.0
    else: 
        precio_base = 12.0 if canal == 'Exportación' else 8.0
    #? Es decir siempre es mas barato a la venta local
        
    # Genera un factor al azar entre 0.95 (95%) y 1.05 (105%)
    factor_variacion = np.random.uniform(0.95, 1.05)
    # Se lo aplicamos al precio base
    return round(precio_base * factor_variacion, 2)


def calcular_unidades_vendidas(precio_unitario: float, var: str, estacion: str) -> int:
    """Genera las unidades vendidas de una transacción a partir de variables de negocio.

    1. Demanda base con relación inversa al precio (a mayor precio, menos botellas).
    2. Efecto estacional: tintos fuertes en Invierno y Torrontés en Verano.
    3. Ruido gaussiano para darle realismo.
    4. Redondeo a entero con un mínimo de UNIDADES_MINIMAS.
    """
    unidades_esperadas = UNIDADES_BASE - PENDIENTE_PRECIO * precio_unitario

    # Simulación de estacionalidad real mendocina según la estación
    factor_estacional = 1.0
    if estacion == 'Verano' and var == 'Torrontés': # El blanco explota en verano
        factor_estacional = FACTOR_TORRONTES_VERANO
    elif estacion == 'Invierno' and var in ['Malbec', 'Cabernet Sauvignon']: # Los tintos pesan más en invierno
        factor_estacional = FACTOR_TINTOS_INVIERNO
    unidades_esperadas *= factor_estacional

    ruido = np.random.normal(0, DESVIO_RUIDO)

    # Cantidades vendidas (En botellas individuales)
    return max(UNIDADES_MINIMAS, int(round(unidades_esperadas + ruido)))


def generar_inventario() -> pd.DataFrame:
    """Genera el dataset de inventario (stock actual en depósito)."""
    #! --- GENERACIÓN DEL INVENTARIO (dataset; stock actual en depósito) ---
    inventario_list = []
    for var in varietales:
        for lin in lineas:
            # Lógica de negocio: Las líneas premium tienen menos stock físico y umbrales más altos
            if lin == 'Gran Reserva':
                stock_actual = np.random.randint(1500, 4000)
                punto_reposicion = 2500  # Requiere más tiempo de anticipación por la crianza
            elif lin == 'Reserva':
                stock_actual = np.random.randint(4000, 9000)
                punto_reposicion = 3500
            else: # Joven
                stock_actual = np.random.randint(8000, 20000)
                punto_reposicion = 5000  # Alta rotación, reposición estándar

            inventario_list.append({
                'Varietal': var,
                'Linea': lin,
                'Stock_Actual': stock_actual,
                'Punto_Reposicion': punto_reposicion
            })

    return pd.DataFrame(inventario_list)


def generar_ventas(n_ventas: int = 1200) -> pd.DataFrame:
    """Genera el histórico de ventas con unidades correlacionadas a precio y estación."""
    #! --- GENERACIÓN DE HISTÓRICO DE VENTAS (1200 registros para poblar los gráficos) ---
    # Generar fechas aleatorias a lo largo de todo el año 2025 (para capturar estacionalidad mensual)
    fecha_inicio = datetime(2025, 1, 1)
    fechas = [fecha_inicio + timedelta(days=int(np.random.randint(0, 365))) for _ in range(n_ventas)]

    ventas_list = []
    for i in range(n_ventas):
        fecha = fechas[i]
        var = np.random.choice(varietales)
        lin = np.random.choice(lineas)
        canal = np.random.choice(canales, p=[0.6, 0.4]) # 60% consumo local, 40% exportación

        #? Primero el precio, porque las unidades dependen de él
        precio_unitario = calcular_precio_unitario(lin, canal)
        estacion = obtener_estacion(fecha.month)
        unidades_vendidas = calcular_unidades_vendidas(precio_unitario, var, estacion)

        ventas_list.append({
            'Fecha': fecha.strftime('%Y-%m-%d'),
            'Varietal': var,
            'Linea': lin,
            'Canal': canal,
            'Unidades_Vendidas': unidades_vendidas,
            'Precio_Unitario': precio_unitario
        })

    df_ventas = pd.DataFrame(ventas_list)
    # Ordenar cronológicamente las ventas para que los gráficos temporales tengan sentido directo
    return df_ventas.sort_values('Fecha').reset_index(drop=True)


def main() -> None:
    """Regenera data/inventario.csv y data/ventas.csv de forma reproducible."""
    # 1. Crear la carpeta 'data' en la raíz del proyecto
    os.makedirs(DATA_DIR, exist_ok=True)

    # Fijar semilla para reproducibilidad (Esto garantiza que la aleatoriedad sea idéntica siempre)
    #? Se fija acá y se genera el inventario primero, igual que antes, para que inventario.csv no cambie
    np.random.seed(SEMILLA)

    df_inventario = generar_inventario()
    # Guardar inventario usando DATA_DIR
    inventario_path = os.path.join(DATA_DIR, 'inventario.csv')
    df_inventario.to_csv(inventario_path, index=False)
    print(f"✅ Archivo '{inventario_path}' creado con éxito.")

    n_ventas = 1200
    print(f"⏳ Generando histórico de ventas ({n_ventas} transacciones)...")
    df_ventas = generar_ventas(n_ventas)
    # Guardar ventas usando DATA_DIR
    ventas_path = os.path.join(DATA_DIR, 'ventas.csv')
    df_ventas.to_csv(ventas_path, index=False)
    print(f"✅ Archivo '{ventas_path}' creado con éxito.")
    print("\n🎉 ¡Listo! Datos sintéticos generados en la raíz del proyecto.")


if __name__ == "__main__":
    main()
