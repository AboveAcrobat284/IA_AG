import tkinter as tk
from tkinter import messagebox
import requests
import webview
import pandas as pd

# Tu API Key de Google
API_KEY = 'AIzaSyDrx4GgcWXJpXuLp_H2uDtJ53hb82KCbTs'

# Leer el dataset
def leer_dataset():
    return pd.read_csv('hoteles_existentes.csv')

# Función para obtener coordenadas de una dirección
def obtener_coordenadas(direccion):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={direccion}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        location = response.json().get('results', [])[0].get('geometry', {}).get('location', {})
        return location.get('lat'), location.get('lng')
    else:
        print(f"Error {response.status_code}: No se pudieron obtener las coordenadas de {direccion}")
        return None, None

# Función para calcular distancia usando Google Distance Matrix API
def calcular_distancia(punto_interes, hotel):
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={punto_interes[0]},{punto_interes[1]}&destinations={hotel['Lat']},{hotel['Lng']}&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        distance_info = response.json().get('rows', [])[0].get('elements', [])[0].get('distance', {})
        if distance_info:
            return distance_info.get('value') / 1000  # convertir a km
    return None

# Función para buscar el hotel más cercano
def buscar_hotel_mas_cercano(ciudad, punto_interes):
    # Obtener coordenadas del punto de interés
    lat_punto_interes, lng_punto_interes = obtener_coordenadas(punto_interes)
    if not lat_punto_interes or not lng_punto_interes:
        messagebox.showerror("Error", "No se pudieron obtener las coordenadas del punto de interés.")
        return None, None

    # Leer dataset y filtrar por ciudad
    df_hoteles = leer_dataset()
    df_ciudad = df_hoteles[df_hoteles['Ciudad'].str.contains(ciudad, case=False, na=False)]

    if df_ciudad.empty:
        messagebox.showerror("Error", f"No se encontraron hoteles en la ciudad {ciudad}.")
        return None, None

    # Calcular distancias
    punto_interes_coord = (lat_punto_interes, lng_punto_interes)
    df_ciudad['Distancia'] = df_ciudad.apply(lambda row: calcular_distancia(punto_interes_coord, row), axis=1)

    # Encontrar el hotel más cercano
    hotel_mas_cercano = df_ciudad.loc[df_ciudad['Distancia'].idxmin()]
    return hotel_mas_cercano, punto_interes_coord

# Función para generar el enlace de Google Maps
def generar_enlace_google_maps(punto_interes, hotel):
    base_url = "https://www.google.com/maps/dir/?api=1"
    origin = f"origin={punto_interes[0]},{punto_interes[1]}"
    destination = f"destination={hotel['Lat']},{hotel['Lng']}"
    travelmode = "travelmode=driving"
    return f"{base_url}&{origin}&{destination}&{travelmode}"

# Función para manejar el botón de búsqueda
def buscar():
    ciudad = entry_ciudad.get()
    punto_interes = entry_punto_interes.get()
    if not ciudad or not punto_interes:
        messagebox.showerror("Error", "Por favor ingrese la ciudad y el punto de interés.")
        return

    hotel_mas_cercano, punto_interes_coord = buscar_hotel_mas_cercano(ciudad, punto_interes)
    if hotel_mas_cercano is not None:
        mostrar_resultado(hotel_mas_cercano)
        enlace = generar_enlace_google_maps(punto_interes_coord, hotel_mas_cercano)
        ventana_mapa(enlace)

# Función para mostrar el resultado
def mostrar_resultado(hotel):
    resultado = f"Hotel más cercano:\n\nNombre: {hotel['Nombre']}\nDirección: {hotel['Direccion']}\nValoración: {hotel['Valoracion']}\nTotal Opiniones: {hotel['TotalOpiniones']}\nDistancia: {hotel['Distancia']:.2f} km"
    messagebox.showinfo("Resultado", resultado)

# Función para crear una nueva ventana con el mapa
def ventana_mapa(enlace):
    # Crear una nueva ventana de webview para mostrar el mapa
    map_window = webview.create_window('Mapa de Hoteles Cercanos', enlace, width=800, height=600)
    webview.start()

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Buscador de Hoteles Cercanos")
root.geometry("800x200")

frame = tk.Frame(root)
frame.pack(pady=10)

label_ciudad = tk.Label(frame, text="Ciudad:")
label_ciudad.grid(row=0, column=0, padx=5, pady=5)
entry_ciudad = tk.Entry(frame, width=50)
entry_ciudad.grid(row=0, column=1, padx=5, pady=5)

label_punto_interes = tk.Label(frame, text="Punto de Interés:")
label_punto_interes.grid(row=1, column=0, padx=5, pady=5)
entry_punto_interes = tk.Entry(frame, width=50)
entry_punto_interes.grid(row=1, column=1, padx=5, pady=5)

button_buscar = tk.Button(frame, text="Buscar", command=buscar)
button_buscar.grid(row=2, columnspan=2, pady=10)

root.mainloop()
