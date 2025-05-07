"""
Script para diagnosticar problemas en el proyecto.
"""
import os
import sys
import importlib
import importlib.util
from pathlib import Path

# Añadir directorio raíz al path
ROOT_DIR = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIR))

def check_module_exists(module_name):
    """Verifica si un módulo está instalado."""
    try:
        importlib.import_module(module_name)
        print(f"✅ Módulo {module_name} encontrado")
        return True
    except ImportError as e:
        print(f"❌ Módulo {module_name} no encontrado: {str(e)}")
        return False

def check_file_exists(file_path):
    """Verifica si un archivo existe."""
    abs_path = os.path.join(ROOT_DIR, file_path)
    if os.path.exists(abs_path):
        print(f"✅ Archivo {file_path} encontrado")
        return True
    else:
        print(f"❌ Archivo {file_path} no encontrado")
        return False

def check_python_version():
    """Verifica la versión de Python."""
    print(f"Python {sys.version}")
    return sys.version_info

def check_transformers_config():
    """Verifica la configuración de Transformers si está instalado."""
    if check_module_exists("transformers"):
        try:
            from transformers import pipeline
            print("   Intentando crear un pipeline de clasificación...")
            try:
                classifier = pipeline("zero-shot-classification")
                print("   ✅ Pipeline creado con éxito")
            except Exception as e:
                print(f"   ❌ Error al crear pipeline: {str(e)}")
        except Exception as e:
            print(f"   ❌ Error al importar pipeline: {str(e)}")

def check_telegram_bot():
    """Verifica la configuración de python-telegram-bot."""
    if check_module_exists("telegram"):
        try:
            from telegram.ext import Application
            print("   Verificando versión de python-telegram-bot...")
            import telegram
            print(f"   Versión: {telegram.__version__}")
        except Exception as e:
            print(f"   ❌ Error al importar Application: {str(e)}")

def main():
    """Función principal."""
    print("=== Diagnóstico del sistema ===")
    
    # Verificar versión de Python
    print("\n== Versión de Python ==")
    check_python_version()
    
    # Verificar módulos clave
    print("\n== Módulos requeridos ==")
    check_module_exists("nltk")
    check_module_exists("pandas")
    check_module_exists("kaggle")
    check_module_exists("clarifai_grpc")
    check_module_exists("google.generativeai")
    check_module_exists("telegram")
    check_module_exists("transformers")
    check_module_exists("fastapi")
    
    # Verificar archivos clave
    print("\n== Archivos clave ==")
    check_file_exists("backend/ai/nlp/food_processor.py")
    check_file_exists("backend/ai/vision/food_detector.py")
    check_file_exists("backend/ai/integrator.py")
    check_file_exists("backend/bot/telegram_bot.py")
    check_file_exists("data/processed/usda_food_data.csv")
    
    # Verificar Transformers
    print("\n== Verificación de Transformers ==")
    check_transformers_config()
    
    # Verificar python-telegram-bot
    print("\n== Verificación de python-telegram-bot ==")
    check_telegram_bot()
    
    print("\n=== Diagnóstico completado ===")

if __name__ == "__main__":
    main() 