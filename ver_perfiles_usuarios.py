import os
import json
from datetime import datetime

# Ruta al archivo de perfiles
data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
profiles_path = os.path.join(data_path, "user_profiles.json")

def formato_legible(valor):
    """Da formato más legible a ciertos valores"""
    if isinstance(valor, list):
        return ", ".join(valor) if valor else "Ninguno/a"
    return valor if valor else "No especificado"

# Cabecera del informe
print("\n" + "="*60)
print(" INFORME DE PERFILES DE USUARIO EN NUTRIVECI ".center(60, "="))
print("="*60)
print(f"Fecha del informe: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
print("-"*60 + "\n")

# Verificar si existe el archivo de perfiles
if os.path.exists(profiles_path):
    try:
        # Cargar los perfiles desde el archivo JSON
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        
        # Mostrar cantidad de perfiles
        total_profiles = len(profiles)
        print(f"Total de perfiles encontrados: {total_profiles}\n")
        
        if total_profiles > 0:
            print("-"*60)
            # Mostrar cada perfil con formato mejorado
            for i, (user_id, profile) in enumerate(profiles.items(), 1):
                print(f"PERFIL #{i} - ID: {user_id}")
                print(f"  Edad:       {formato_legible(profile.get('edad'))}")
                print(f"  Género:     {formato_legible(profile.get('genero'))}")
                print(f"  Peso:       {formato_legible(profile.get('peso'))}")
                print(f"  Patologías: {formato_legible(profile.get('patologias', []))}")
                print(f"  Alergias:   {formato_legible(profile.get('alergias', []))}")
                
                # Añadir otros campos si existen en el perfil
                for key, value in profile.items():
                    if key not in ['edad', 'genero', 'peso', 'patologias', 'alergias']:
                        print(f"  {key.capitalize()}: {formato_legible(value)}")
                
                print("-"*60)
        else:
            print("El archivo de perfiles existe pero está vacío.")
            
    except json.JSONDecodeError as e:
        print(f"Error al leer el archivo de perfiles: formato JSON inválido")
        print(f"Detalles del error: {str(e)}")
    except Exception as e:
        print(f"Error inesperado al leer perfiles: {str(e)}")
else:
    print("No se encontró el archivo de perfiles en esta ubicación:")
    print(f"  {profiles_path}")
    print("\nNota: El archivo se creará automáticamente cuando un usuario")
    print("complete su perfil en la sección de recetas recomendadas.")

print("\n" + "="*60)
print(" FIN DEL INFORME ".center(60, "="))
print("="*60) 