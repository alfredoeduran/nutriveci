"""
Versión simplificada del procesador de alimentos sin dependencias de modelos de aprendizaje profundo.
"""
import os
import json
import csv
import re
from typing import List, Dict, Optional, Any, Tuple
import pandas as pd
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
import aiohttp

# Descargar recursos de NLTK necesarios
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

# Lista predefinida de términos relacionados con alimentos
FOOD_RELATED_TERMS = [
    "food", "comida", "alimento", "meal", "dish", "recipe", "receta", "ingredient", "ingrediente",
    "fruit", "fruta", "vegetable", "verdura", "meat", "carne", "fish", "pescado", "dairy", "lácteo",
    "breakfast", "desayuno", "lunch", "almuerzo", "dinner", "cena", "snack", "merienda",
    "protein", "proteína", "carb", "carbohidrato", "fat", "grasa", "vitamin", "vitamina"
]

# Lista de alimentos comunes
COMMON_FOODS = [
    # Frutas
    "apple", "manzana", "banana", "plátano", "orange", "naranja", "strawberry", "fresa", "grape", "uva",
    # Verduras
    "carrot", "zanahoria", "potato", "patata", "tomato", "tomate", "onion", "cebolla", "lettuce", "lechuga",
    # Carnes
    "chicken", "pollo", "beef", "res", "pork", "cerdo", "fish", "pescado", "salmon", "salmón",
    # Lácteos
    "milk", "leche", "cheese", "queso", "yogurt", "yogur",
    # Otros
    "rice", "arroz", "bread", "pan", "pasta", "sandwich", "sándwich", "soup", "sopa", "salad", "ensalada"
]

class SimpleFoodProcessor:
    def __init__(self, data_path: str = None):
        """
        Inicializa el procesador simple de alimentos.
        
        Args:
            data_path: Ruta al directorio de datos
        """
        self.data_path = data_path
        self.food_data = {}
        
        # Cargar datos de alimentos si existe el archivo
        if data_path:
            food_data_path = os.path.join(data_path, "food_data.json")
            if os.path.exists(food_data_path):
                try:
                    with open(food_data_path, "r", encoding="utf-8") as f:
                        self.food_data = json.load(f)
                    print(f"✅ Datos de alimentos cargados: {len(self.food_data)} elementos")
                except Exception as e:
                    print(f"❌ Error cargando datos de alimentos: {str(e)}")
        
        # Lista de palabras que no son alimentos para filtrar falsos positivos
        self.non_food_words = [
            "puerta", "ventana", "casa", "edificio", "auto", "carro", "tren", "avión", "avion",
            "libro", "revista", "periódico", "periodico", "ropa", "zapatos", "sombrero", 
            "computadora", "teléfono", "telefono", "tablet", "silla", "mesa", "sofá", "sofa",
            "hola", "adiós", "adios", "gracias", "por favor", "ayuda", "que tal", "como estas",
            "buenos días", "buenas tardes", "buenas noches"
        ]
                
    async def extract_food_items(self, text: str) -> List[str]:
        """
        Extrae menciones de alimentos del texto del usuario.
        Método simplificado usando listas predefinidas y validación.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de alimentos detectados
        """
        # Lista base de alimentos comunes en español
        common_foods = [
            "manzana", "naranja", "plátano", "platano", "banana", "pera", "uva", "kiwi", "fresa", 
            "arroz", "pasta", "pan", "leche", "queso", "yogur", "huevo", "pollo", "carne", "pescado",
            "atún", "atun", "salmón", "salmon", "cerdo", "res", "tomate", "lechuga", "zanahoria", 
            "papa", "patata", "cebolla", "ajo", "brócoli", "brocoli", "coliflor", "espinaca", 
            "maíz", "maiz", "frijol", "lenteja", "garbanzo", "almendra", "nuez", "avellana", 
            "miel", "azúcar", "azucar", "sal", "pimienta", "aceite", "mantequilla", "chocolate",
            "café", "cafe", "té", "te", "jugo", "agua", "refresco", "cerveza", "vino"
        ]
        
        # Convertir texto a minúsculas y dividir en tokens
        text_lower = text.lower()
        words = text_lower.split()
        
        # Filtrar tokens que son alimentos
        detected_foods = []
        
        # Comprobar si hay coincidencias con alimentos comunes
        for word in words:
            # Eliminar caracteres especiales y puntuación
            clean_word = ''.join(c for c in word if c.isalnum() or c.isspace())
            
            # Verificar que no sea una palabra que no es alimento
            if clean_word in self.non_food_words:
                continue
                
            # Verificar si es un alimento conocido
            if clean_word in common_foods or clean_word in self.food_data:
                detected_foods.append(clean_word)
                continue
                
            # Comprobar si alguna palabra se parece a un alimento conocido
            for food in common_foods:
                # Si hay suficiente coincidencia (por ejemplo, "manzan" para "manzana")
                if len(clean_word) > 3 and (clean_word in food or food in clean_word):
                    # Usar la palabra completa del alimento para normalizar
                    detected_foods.append(food)
                    break
        
        return list(set(detected_foods))  # Eliminar duplicados
    
    async def get_nutrition_info(self, food_name: str) -> Dict[str, Any]:
        """
        Obtiene información nutricional de un alimento.
        
        Args:
            food_name: Nombre del alimento
            
        Returns:
            Diccionario con información nutricional
        """
        # Si tenemos datos locales, usarlos primero
        if food_name in self.food_data:
            return self.food_data[food_name]
        
        # Si no, intentar obtener información de FoodData Central API
        try:
            nutrition_info = await self._fetch_nutrition_info(food_name)
            # Traducir la información al español
            nutrition_info["name_es"] = await self._translate_to_spanish(nutrition_info["name"])
            return nutrition_info
        except Exception as e:
            print(f"Error obteniendo información de {food_name}: {str(e)}")
            # Devolver información básica si falla
            return {
                "name": food_name,
                "name_es": food_name,  # Mantener el nombre original en español
                "calories": None,
                "protein": None,
                "carbs": None,
                "fat": None
            }
    
    async def _fetch_nutrition_info(self, food_name: str) -> Dict[str, Any]:
        """
        Consulta a FoodData Central API para obtener información nutricional.
        
        Args:
            food_name: Nombre del alimento
            
        Returns:
            Diccionario con información nutricional
        """
        # Esta es una simulación simplificada
        # En una implementación real, se usaría una API como USDA FoodData Central
        return {
            "name": food_name,
            "calories": 100,  # Valores ficticios para demostración
            "protein": 5,
            "carbs": 15,
            "fat": 2
        }
    
    async def _translate_to_spanish(self, text: str) -> str:
        """
        Traduce texto al español si es necesario.
        
        Args:
            text: Texto a traducir
            
        Returns:
            Texto traducido
        """
        # Diccionario simple de traducción inglés-español
        translations = {
            "apple": "manzana",
            "orange": "naranja",
            "banana": "plátano",
            "pear": "pera",
            "grape": "uva",
            "strawberry": "fresa",
            "rice": "arroz",
            "pasta": "pasta",
            "bread": "pan",
            "milk": "leche",
            "cheese": "queso",
            "yogurt": "yogur",
            "egg": "huevo",
            "chicken": "pollo",
            "meat": "carne",
            "fish": "pescado",
            "tuna": "atún",
            "salmon": "salmón",
            "pork": "cerdo",
            "beef": "res",
            "tomato": "tomate",
            "lettuce": "lechuga",
            "carrot": "zanahoria",
            "potato": "papa",
            "onion": "cebolla",
            "garlic": "ajo",
            "broccoli": "brócoli",
            "cauliflower": "coliflor",
            "spinach": "espinaca",
            "corn": "maíz",
            "bean": "frijol",
            "lentil": "lenteja",
            "chickpea": "garbanzo",
            "almond": "almendra",
            "walnut": "nuez",
            "hazelnut": "avellana",
            "honey": "miel",
            "sugar": "azúcar",
            "salt": "sal",
            "pepper": "pimienta",
            "oil": "aceite",
            "butter": "mantequilla",
            "chocolate": "chocolate",
            "coffee": "café",
            "tea": "té",
            "juice": "jugo",
            "water": "agua",
            "soda": "refresco",
            "beer": "cerveza",
            "wine": "vino"
        }
        
        # Comprobar si el texto está en inglés y tiene traducción
        text_lower = text.lower()
        if text_lower in translations:
            return translations[text_lower]
        
        # Si no hay traducción, devolver el texto original
        return text
        
    async def integrate_vision_results(self, detected_foods: List[str]) -> List[Dict[str, Any]]:
        """
        Integra resultados de visión para obtener información nutricional.
        
        Args:
            detected_foods: Lista de alimentos detectados
            
        Returns:
            Lista de diccionarios con información nutricional
        """
        nutrition_info = []
        
        for food in detected_foods:
            food_info = await self.get_nutrition_info(food)
            nutrition_info.append(food_info)
            
        return nutrition_info 