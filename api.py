import folium
from geopy.geocoders import Nominatim
import requests
import webbrowser
import tkinter as tk
from tkinter import simpledialog, messagebox

# Tu API Key de Google
API_KEY = 'AIzaSyDrx4GgcWXJpXuLp_H2uDtJ53hb82KCbTs'

# Función para obtener coordenadas del punto de interés
def obtener_coordenadas(direccion):
    geolocator = Nominatim(user_agent="myGeocoder")
    location = geolocator.geocode(direccion)
    if location:
        return location.latitude, location.longitude
    else:
        return None, None

# Función para buscar hoteles cercanos utilizando la API de Google Places
def buscar_hoteles_cercanos(lat, lng, radio=5000):
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radio}&type=lodging&key={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    else:
        return []

# Función para crear el mapa y la ruta
def crear_mapa(punto_interes, hotel):
    # Crear un mapa centrado en el punto de interés
    map = folium.Map(location=[punto_interes[0], punto_interes[1]], zoom_start=15)

    # Añadir un marcador para el punto de interés
    folium.Marker(location=[punto_interes[0], punto_interes[1]], popup="Punto de Interés", icon=folium.Icon(color='blue')).add_to(map)

    # Añadir un marcador para el hotel
    folium.Marker(location=[hotel['geometry']['location']['lat'], hotel['geometry']['location']['lng']], popup=hotel['name'], icon=folium.Icon(color='red')).add_to(map)

    # Dibujar la ruta
    folium.PolyLine(locations=[(punto_interes[0], punto_interes[1]), (hotel['geometry']['location']['lat'], hotel['geometry']['location']['lng'])], color='green').add_to(map)

    # Guardar el mapa en un archivo HTML
    map.save("ruta_hotel.html")

    # Abrir el archivo HTML en el navegador
    webbrowser.open("ruta_hotel.html")

# Función para manejar el flujo de la aplicación
def main():
    root = tk.Tk()
    root.withdraw()

    # Obtener el punto de interés del usuario
    punto_interes = simpledialog.askstring("Punto de Interés", "Ingrese el punto de interés:")
    if not punto_interes:
        messagebox.showerror("Error", "Debe ingresar un punto de interés.")
        return

    # Obtener coordenadas del punto de interés
    lat, lng = obtener_coordenadas(punto_interes)
    if not lat or not lng:
        messagebox.showerror("Error", "No se pudieron obtener las coordenadas del punto de interés.")
        return

    # Buscar hoteles cercanos
    hoteles_cercanos = buscar_hoteles_cercanos(lat, lng)
    if not hoteles_cercanos:
        messagebox.showerror("Error", "No se encontraron hoteles cercanos.")
        return

    # Tomar el primer hotel de la lista
    hotel_cercano = hoteles_cercanos[0]

    # Crear el mapa y la ruta
    crear_mapa((lat, lng), hotel_cercano)

if __name__ == "__main__":
    main()
