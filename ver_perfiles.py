import os
import json
import sys

# Agregar la raíz del proyecto al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar la función get_user_data desde backend.bot.nutriveci_bot o recipe_manager
try:
    from backend.bot.nutriveci_bot import get_user_data, user_data
except ImportError:
    try:
        from backend.bot.recipe_manager import get_user_data, user_data
    except ImportError:
        print("No se pudo importar get_user_data")
        user_data = {}

# Verificar si hay un archivo user_profiles.json
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
profiles_path = os.path.join(data_path, "user_profiles.json")

print("=== Perfiles de Usuario en NutriVeci ===\n")

# 1. Verificar perfiles en memoria (datos actuales)
print("Perfiles en memoria (sesión actual):")
if user_data:
    for user_id, data in user_data.items():
        if 'profile' in data and data['profile']:
            print(f"\nUsuario ID: {user_id}")
            print(f"  Edad: {data['profile'].get('edad', 'No especificada')}")
            print(f"  Género: {data['profile'].get('genero', 'No especificado')}")
            print(f"  Peso: {data['profile'].get('peso', 'No especificado')}")
            
            patologias = data['profile'].get('patologias', [])
            print(f"  Patologías: {', '.join(patologias) if patologias else 'Ninguna'}")
            
            alergias = data['profile'].get('alergias', [])
            print(f"  Alergias: {', '.join(alergias) if alergias else 'Ninguna'}")
            print("-" * 40)
else:
    print("  No hay perfiles cargados en memoria.\n")

# 2. Verificar perfiles guardados en archivo
print("\nPerfiles guardados en archivo:")
if os.path.exists(profiles_path):
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            
        if profiles:
            for user_id, profile in profiles.items():
                print(f"\nUsuario ID: {user_id}")
                print(f"  Edad: {profile.get('edad', 'No especificada')}")
                print(f"  Género: {profile.get('genero', 'No especificado')}")
                print(f"  Peso: {profile.get('peso', 'No especificado')}")
                
                patologias = profile.get('patologias', [])
                print(f"  Patologías: {', '.join(patologias) if patologias else 'Ninguna'}")
                
                alergias = profile.get('alergias', [])
                print(f"  Alergias: {', '.join(alergias) if alergias else 'Ninguna'}")
                print("-" * 40)
        else:
            print("  El archivo de perfiles está vacío.")
    except Exception as e:
        print(f"  Error leyendo archivo de perfiles: {str(e)}")
else:
    print("  No existe el archivo de perfiles user_profiles.json")

# 3. Información sobre la base de datos
print("\nNota: Si el sistema está configurado con Supabase, los perfiles también")
print("podrían estar almacenados en la base de datos. Para acceder a estos datos,")
print("necesitarías consultar las tablas 'dietary_profiles' y 'user_preferences'.") 