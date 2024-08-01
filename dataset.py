import pandas as pd
import requests
import random

# Tu API Key de Google
API_KEY = 'AIzaSyDrx4GgcWXJpXuLp_H2uDtJ53hb82KCbTs'

# Función para buscar hoteles en una ciudad usando la API de Google Places
def buscar_hoteles(ciudad):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=hoteles+en+{ciudad}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        print(f"Error {response.status_code}: No se pudieron buscar hoteles en {ciudad}")
        return []

# Función para obtener detalles de un hotel usando la API de Google Places
def obtener_detalles_hotel(place_id):
    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('result', {})
    else:
        print(f"Error {response.status_code}: No se pudieron obtener detalles para el place_id {place_id}")
        return {}

# Función para generar datos para las habitaciones
def generar_habitaciones(hotel_id):
    habitaciones = []
    for i in range(15):
        precio = round(random.uniform(500, 5000), 2)
        tipo_servicio = random.choice(["Habitación con Jacuzzi", "Habitación con Frigobar", "Habitación con Spa"])
        tipo_cama = random.choice(["Habitación con una cama", "Habitación con cama doble", "Habitación con cama matrimonial"])
        habitaciones.append({
            "HotelID": hotel_id,
            "HabitacionID": f"H{hotel_id}_{i+1}",
            "Precio": precio,
            "Tipo de cama": tipo_cama,
            "TipoServicio": tipo_servicio
        })
    return habitaciones

# Ciudades de interés
ciudades = [
    "Tuxtla Gutierrez, Chiapas", 
    "San Cristobal De las Casas, Chiapas", 
    "Arriaga, Chiapas", 
    "Tonalá, Chiapas"
]

# Lista para almacenar datos de hoteles y habitaciones
data_hoteles = []
data_habitaciones = []

hotel_id = 1
for ciudad in ciudades:
    hoteles = buscar_hoteles(ciudad)
    for hotel in hoteles:
        detalles = obtener_detalles_hotel(hotel['place_id'])
        if detalles:
            data_hoteles.append({
                "HotelID": hotel_id,
                "Ciudad": ciudad,
                "Nombre": detalles.get('name', 'N/A'),
                "Direccion": detalles.get('formatted_address', 'N/A'),
                "Valoracion": detalles.get('rating', 0),
                "TotalOpiniones": detalles.get('user_ratings_total', 0),
                "Lat": detalles['geometry']['location']['lat'],
                "Lng": detalles['geometry']['location']['lng']
            })
            data_habitaciones.extend(generar_habitaciones(hotel_id))
            hotel_id += 1

# Convertir listas a DataFrames y guardar en CSV
df_hoteles = pd.DataFrame(data_hoteles)
df_hoteles.to_csv('hoteles_existentes.csv', index=False)

df_habitaciones = pd.DataFrame(data_habitaciones)
df_habitaciones.to_csv('habitaciones_existentes.csv', index=False)

print("Datos de hoteles y habitaciones generados y guardados en 'hoteles_existentes.csv' y 'habitaciones_existentes.csv'")
