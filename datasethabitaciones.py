import pandas as pd
import random

# Cargar el dataset original
df = pd.read_csv('habitaciones_existentes.csv')

# Tipos de cama y tipos de servicio
tipos_cama = ["Habitación con una cama", "Habitación con cama doble", "Habitación con cama matrimonial"]
tipos_servicio = ["Habitación con Jacuzzi", "Habitación con Frigobar", "Habitación con Spa"]

# Asignar tipos de cama y tipos de servicio aleatoriamente
df['Tipo de cama'] = [random.choice(tipos_cama) for _ in range(len(df))]
df['TipoServicio'] = [random.choice(tipos_servicio) for _ in range(len(df))]

# Reordenar las columnas
df = df[['HotelID', 'HabitacionID', 'Precio', 'Tipo de cama', 'TipoServicio']]

# Asegurar que cada hotel tenga 15 habitaciones
hoteles = df['HotelID'].unique()
nuevo_df = pd.DataFrame()

for hotel in hoteles:
    habitaciones_hotel = df[df['HotelID'] == hotel]
    if len(habitaciones_hotel) > 15:
        habitaciones_hotel = habitaciones_hotel.sample(15)
    elif len(habitaciones_hotel) < 15:
        while len(habitaciones_hotel) < 15:
            new_habitacion = habitaciones_hotel.sample(1)
            new_habitacion['HabitacionID'] = new_habitacion['HabitacionID'].str.replace(r'H\d+_', f'H{hotel}_')
            habitaciones_hotel = pd.concat([habitaciones_hotel, new_habitacion], ignore_index=True)
    nuevo_df = pd.concat([nuevo_df, habitaciones_hotel], ignore_index=True)

# Guardar el nuevo dataset
nuevo_df.to_csv('nuevo_habitaciones.csv', index=False)

# Mostrar el nuevo dataset
print(nuevo_df)
