import tkinter as tk
from tkinter import messagebox, ttk
import requests
import pandas as pd
import numpy as np
import random
from collections import defaultdict

# API Key de Google
API_KEY = 'AIzaSyDrx4GgcWXJpXuLp_H2uDtJ53hb82KCbTs'

# Leer el dataset de hoteles
def leer_dataset_hoteles():
    df = pd.read_csv('hoteles_existentes.csv')
    columnas_esperadas = ['HotelID', 'Ciudad', 'Nombre', 'Direccion', 'Valoracion', 'TotalOpiniones', 'Lat', 'Lng']
    for columna in columnas_esperadas:
        if columna not in df.columns:
            raise KeyError(f"Falta la columna '{columna}' en el dataset de hoteles")
    return df

# Leer el dataset de habitaciones
def leer_dataset_habitaciones():
    df = pd.read_csv('habitaciones_existentes.csv')
    columnas_esperadas = ['HotelID', 'HabitacionID', 'Precio', 'TipoCama', 'TipoServicio']
    for columna in columnas_esperadas:
        if columna not in df.columns:
            raise KeyError(f"Falta la columna '{columna}' en el dataset de habitaciones")
    return df

# Función para obtener coordenadas de una dirección
def obtener_coordenadas(direccion):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json().get('results', [])
        if results:
            location = results[0].get('geometry', {}).get('location', {})
            return location.get('lat'), location.get('lng')
    print(f"Error {response.status_code}: No se pudieron obtener las coordenadas de {direccion}")
    return None, None

# Caché para almacenar las distancias calculadas
distancia_cache = defaultdict(lambda: None)

# Función para calcular distancia usando Google Distance Matrix API
def calcular_distancia(punto_interes, hotel):
    clave_cache = (punto_interes, (hotel['Lat'], hotel['Lng']))
    if distancia_cache[clave_cache] is None:
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={punto_interes[0]},{punto_interes[1]}&destinations={hotel['Lat']},{hotel['Lng']}&key={API_KEY}"
        response = requests.get(url)
        if response.status_code == 200:
            distance_info = response.json().get('rows', [])[0].get('elements', [])[0].get('distance', {})
            if distance_info:
                distancia_cache[clave_cache] = distance_info.get('value') / 1000  # convertir a km
    return distancia_cache[clave_cache]

# Función del algoritmo genético
def algoritmo_genetico(punto_interes_coord, df_hoteles, df_habitaciones, datos):
    tamano_poblacion = int(datos['TamanoPoblacion'])
    max_tamano_poblacion = int(datos['MaxTamanoPoblacion'])
    num_generaciones = int(datos['NumGeneraciones'])
    tasa_mutacion_individuo = float(datos['TasaMutacionIndividuo'])
    tasa_mutacion_gen = float(datos['TasaMutacionGen'])

    columnas = ['HotelID', 'Nombre', 'HabitacionID', 'Precio', 'Distancia', 'Valoracion', 'TipoServicio', 'TipoCama']

    # Orden de preferencia para camas y servicios
    preferencia_camas = ["Habitación con una cama", "Habitación con cama doble", "Habitación con cama matrimonial"]
    preferencia_servicios = ["Habitación con Frigobar", "Habitación con Jacuzzi", "Habitación con Spa"]

    # Crear la población inicial de individuos
    def crear_individuo(hotel, habitacion):
        distancia = calcular_distancia(punto_interes_coord, hotel)
        tipo_cama = habitacion['TipoCama'] if habitacion['TipoCama'] in datos['TipoCama'] else preferencia_camas[0]
        tipo_servicio = habitacion['TipoServicio'] if habitacion['TipoServicio'] in datos['TipoServicio'] else preferencia_servicios[0]
        return [hotel['HotelID'], hotel['Nombre'], habitacion['HabitacionID'], habitacion['Precio'], distancia, hotel['Valoracion'], tipo_servicio, tipo_cama]

    def evaluar_individuo(individuo):
        if len(individuo) != 8:
            raise ValueError(f"El individuo tiene una longitud incorrecta: {len(individuo)}")
        precio, distancia, valoracion, tipo_servicio, tipo_cama = individuo[3:8]
        error = (
            abs(precio - datos['CostoDeseado']) / datos['CostoDeseado'] +
            abs(distancia - datos['Distancia']) / datos['Distancia'] +
            abs(valoracion - datos['PuntajeDeseado']) / datos['PuntajeDeseado']
        )
        # Penalizaciones
        if tipo_cama not in datos['TipoCama']:
            error += 0.1  # Penalización leve por tipo de cama no preferido
        if tipo_servicio not in datos['TipoServicio']:
            error += 0.1  # Penalización leve por tipo de servicio no preferido
        return error

    def seleccionar_parejas(poblacion, errores):
        seleccionados = random.choices(poblacion, weights=[1/e for e in errores], k=len(poblacion))
        if len(seleccionados) % 2 != 0:
            seleccionados.append(random.choice(seleccionados))
        parejas = [(seleccionados[i], seleccionados[i+1]) for i in range(0, len(seleccionados), 2)]
        return parejas

    def cruzar(padre1, padre2):
        punto_cruce = random.randint(1, len(padre1) - 1)
        hijo1 = padre1[:punto_cruce] + padre2[punto_cruce:]
        hijo2 = padre2[:punto_cruce] + padre1[punto_cruce:]
        return hijo1, hijo2

    def mutar(individuo):
        if random.random() < tasa_mutacion_individuo:
            columnas_para_mutar = ['HotelID', 'HabitacionID', 'Precio', 'TipoCama', 'TipoServicio']
            individuo_mutado = [
                gen if random.random() > tasa_mutacion_gen or col not in columnas_para_mutar else random.choice(df_habitaciones[col].unique())
                for gen, col in zip(individuo, columnas)
            ]
            # Asegurarse de que 'Distancia' y 'Valoracion' se mantengan sin cambios.
            individuo_mutado[4] = calcular_distancia(punto_interes_coord, df_hoteles[df_hoteles['HotelID'] == individuo_mutado[0]].iloc[0])
            individuo_mutado[5] = df_hoteles[df_hoteles['HotelID'] == individuo_mutado[0]].iloc[0]['Valoracion']
            return individuo_mutado
        return individuo

    def podar_poblacion(poblacion, max_tamano):
        poblacion_unica = list(set(map(tuple, poblacion)))
        if len(poblacion_unica) > max_tamano:
            errores = [evaluar_individuo(individuo) for individuo in poblacion_unica]
            seleccionados = sorted(zip(poblacion_unica, errores), key=lambda x: x[1])[:max_tamano]
            poblacion_podada = [individuo for individuo, _ in seleccionados]
        else:
            poblacion_podada = poblacion_unica
        return poblacion_podada

    # Calcular la distancia a cada hotel
    df_hoteles['Distancia'] = df_hoteles.apply(lambda x: calcular_distancia(punto_interes_coord, x), axis=1)

    # Seleccionar los 5 hoteles más cercanos y con mejor valoración, asegurando que sean distintos
    mejores_hoteles = df_hoteles.sort_values(by=['Distancia', 'Valoracion'], ascending=[True, False]).drop_duplicates(subset=['HotelID']).head(5)

    # Buscar la mejor habitación en cada uno de los 5 mejores hoteles
    mejores_habitaciones = []
    for _, hotel in mejores_hoteles.iterrows():
        habitaciones = df_habitaciones[df_habitaciones['HotelID'] == hotel['HotelID']]
        mejor_habitacion = None
        mejor_error = float('inf')
        for _, habitacion in habitaciones.iterrows():
            individuo = crear_individuo(hotel, habitacion)
            error = evaluar_individuo(individuo)
            if error < mejor_error:
                mejor_habitacion = individuo
                mejor_error = error
        if mejor_habitacion:
            mejores_habitaciones.append(mejor_habitacion)

    return [dict(zip(columnas, habitacion)) for habitacion in mejores_habitaciones], []

# Función para mostrar el resultado en una tabla
def mostrar_resultado_tabla(mejores_habitaciones):
    ventana_resultados = tk.Toplevel(root)
    ventana_resultados.title("Resultados de la Optimización")

    tabla = ttk.Treeview(ventana_resultados, columns=('HotelID', 'Nombre', 'HabitacionID', 'Precio', 'Distancia', 'Valoracion', 'TipoServicio', 'TipoCama'), show='headings')
    tabla.heading('HotelID', text='Hotel ID')
    tabla.heading('Nombre', text='Nombre del Hotel')
    tabla.heading('HabitacionID', text='Número de Habitación')
    tabla.heading('Precio', text='Precio')
    tabla.heading('Distancia', text='Distancia')
    tabla.heading('Valoracion', text='Valoración')
    tabla.heading('TipoServicio', text='Tipo de Servicio')
    tabla.heading('TipoCama', text='Tipo de Cama')

    for habitacion in mejores_habitaciones:
        tabla.insert('', tk.END, values=(habitacion['HotelID'], habitacion['Nombre'], habitacion['HabitacionID'], habitacion['Precio'], habitacion['Distancia'], habitacion['Valoracion'], habitacion['TipoServicio'], habitacion['TipoCama']))

    tabla.pack(fill=tk.BOTH, expand=True)

# Función para manejar el botón de búsqueda
def buscar():
    ciudad = ciudad_var.get()
    punto_interes = punto_interes_var.get()
    costo_deseado = float(precio_deseado_var.get())
    tipo_cama = [tipo for tipo, var in tipo_cama_vars.items() if var.get()]
    tipo_servicio = [tipo for tipo, var in tipo_servicio_vars.items() if var.get()]
    puntaje_deseado = float(puntaje_deseado_var.get())
    tamano_poblacion = int(tamano_poblacion_var.get())
    max_tamano_poblacion = int(max_tamano_poblacion_var.get())
    num_generaciones = int(num_generaciones_var.get())
    tasa_mutacion_individuo = float(tasa_mutacion_individuo_var.get())
    tasa_mutacion_gen = float(tasa_mutacion_gen_var.get())

    if not tipo_cama:
        tipo_cama = ["Habitación con una cama"]
    if not tipo_servicio:
        tipo_servicio = ["Habitación con Frigobar"]

    lat_punto_interes, lng_punto_interes = obtener_coordenadas(punto_interes)
    if not lat_punto_interes or not lng_punto_interes:
        messagebox.showerror("Error", "No se pudieron obtener las coordenadas del punto de interés.")
        return

    punto_interes_coord = (lat_punto_interes, lng_punto_interes)
    df_hoteles = leer_dataset_hoteles()
    df_habitaciones = leer_dataset_habitaciones()

    datos = {
        'CostoDeseado': costo_deseado,
        'Lat': punto_interes_coord[0],
        'Lng': punto_interes_coord[1],
        'Distancia': 10,  # Distancia inicial grande para optimizar
        'TipoCama': tipo_cama,
        'TipoServicio': tipo_servicio,
        'PuntajeDeseado': puntaje_deseado,
        'TamanoPoblacion': tamano_poblacion,
        'MaxTamanoPoblacion': max_tamano_poblacion,
        'NumGeneraciones': num_generaciones,
        'TasaMutacionIndividuo': tasa_mutacion_individuo,
        'TasaMutacionGen': tasa_mutacion_gen
    }

    mejores_habitaciones, historial_errores = algoritmo_genetico(punto_interes_coord, df_hoteles, df_habitaciones, datos)
    if mejores_habitaciones:
        mostrar_resultado_tabla(mejores_habitaciones)
    else:
        messagebox.showerror("Error", "No se encontraron habitaciones adecuadas.")

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Buscador de Hoteles Cercanos con Algoritmo Genético")
root.geometry("1000x800")

ciudad_var = tk.StringVar()
punto_interes_var = tk.StringVar()
precio_deseado_var = tk.StringVar()
puntaje_deseado_var = tk.StringVar()
tamano_poblacion_var = tk.StringVar()
max_tamano_poblacion_var = tk.StringVar()
num_generaciones_var = tk.StringVar()
tasa_mutacion_individuo_var = tk.StringVar()
tasa_mutacion_gen_var = tk.StringVar()

ciudades = ["Tuxtla Gutierrez, Chiapas", "Arriaga, Chiapas", "San Cristobal De las Casas", "Tonalá, Chiapas"]
tipos_cama = ["Habitación con una cama", "Habitación con cama doble", "Habitación con cama matrimonial"]
tipos_servicio = ["Habitación con Jacuzzi", "Habitación con Frigobar", "Habitación con Spa"]

tk.Label(root, text="Ciudad:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
tk.OptionMenu(root, ciudad_var, *ciudades).grid(row=0, column=1, padx=5, pady=5)
tk.Label(root, text="Punto de Interés:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=punto_interes_var).grid(row=1, column=1, padx=5, pady=5)
tk.Label(root, text="Costo Deseado:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=precio_deseado_var).grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="Tipo de Cama:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
tipo_cama_vars = {}
for i, tipo in enumerate(tipos_cama):
    var = tk.BooleanVar()
    chk = tk.Checkbutton(root, text=tipo, variable=var)
    chk.grid(row=3, column=i+1, padx=5, pady=5)
    tipo_cama_vars[tipo] = var

tk.Label(root, text="Tipo de Servicio:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
tipo_servicio_vars = {}
for i, tipo in enumerate(tipos_servicio):
    var = tk.BooleanVar()
    chk = tk.Checkbutton(root, text=tipo, variable=var)
    chk.grid(row=4, column=i+1, padx=5, pady=5)
    tipo_servicio_vars[tipo] = var

tk.Label(root, text="Puntaje Deseado:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=puntaje_deseado_var).grid(row=5, column=1, padx=5, pady=5)
tk.Label(root, text="Tamaño Inicial de la Población:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=tamano_poblacion_var).grid(row=6, column=1, padx=5, pady=5)
tk.Label(root, text="Tamaño Máximo de la Población:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=max_tamano_poblacion_var).grid(row=7, column=1, padx=5, pady=5)
tk.Label(root, text="Número de Generaciones:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=num_generaciones_var).grid(row=8, column=1, padx=5, pady=5)
tk.Label(root, text="Probabilidad de Mutación Individual:").grid(row=9, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=tasa_mutacion_individuo_var).grid(row=9, column=1, padx=5, pady=5)
tk.Label(root, text="Probabilidad de Mutación por Gen:").grid(row=10, column=0, sticky=tk.W, padx=5, pady=5)
tk.Entry(root, textvariable=tasa_mutacion_gen_var).grid(row=10, column=1, padx=5, pady=5)

tk.Button(root, text="Buscar", command=buscar).grid(row=11, column=0, columnspan=2, pady=10)

root.mainloop()
