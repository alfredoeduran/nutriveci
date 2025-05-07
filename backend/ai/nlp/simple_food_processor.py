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
        Inicializa el procesador de alimentos.
        
        Args:
            data_path: Ruta al directorio de datos nutricionales
        """
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english')).union(set(stopwords.words('spanish')))
        
        # Cargar datos nutricionales si se proporciona una ruta
        self.food_data = {}
        if data_path:
            self.load_food_data(data_path)
        
        print("✅ Procesador de alimentos inicializado correctamente")
    
    def load_food_data(self, data_path: str) -> None:
        """
        Carga datos nutricionales desde archivos.
        
        Args:
            data_path: Ruta al directorio de datos
        """
        try:
            processed_dir = os.path.join(data_path, "processed")
            
            # Cargar datos USDA
            usda_path = os.path.join(processed_dir, "usda_food_data.csv")
            if os.path.exists(usda_path):
                self.food_data["usda"] = pd.read_csv(usda_path, low_memory=False)
                print(f"✅ Cargados {len(self.food_data['usda'])} alimentos de USDA")
            
            # Cargar Open Food Facts
            off_path = os.path.join(processed_dir, "open_food_facts.csv")
            if os.path.exists(off_path):
                self.food_data["open_food_facts"] = pd.read_csv(off_path, low_memory=False)
                print(f"✅ Cargados {len(self.food_data['open_food_facts'])} alimentos de Open Food Facts")
        
        except Exception as e:
            print(f"❌ Error cargando datos nutricionales: {str(e)}")
    
    def preprocess_text(self, text: str) -> List[str]:
        """
        Preprocesa el texto para análisis.
        
        Args:
            text: Texto a preprocesar
            
        Returns:
            Lista de tokens preprocesados
        """
        # Convertir a minúsculas
        text = text.lower()
        
        # Tokenizar
        tokens = word_tokenize(text)
        
        # Eliminar palabras vacías y puntación
        tokens = [token for token in tokens if token.isalpha() and token not in self.stop_words]
        
        # Lematizar
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        
        return tokens
    
    async def extract_food_items(self, text: str) -> List[str]:
        """
        Extrae nombres de alimentos de un texto.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de alimentos identificados
        """
        # Preprocesar texto
        tokens = self.preprocess_text(text)
        
        # Buscar alimentos conocidos
        food_items = []
        
        # Comprobar si los tokens coinciden con alimentos conocidos
        for token in tokens:
            # Verificar si el token está en la lista de alimentos comunes
            if token.lower() in [food.lower() for food in COMMON_FOODS]:
                if token not in food_items:
                    food_items.append(token)
            
            # Si no se encontraron alimentos específicos, buscar términos relacionados con comida
            if not food_items and token.lower() in [term.lower() for term in FOOD_RELATED_TERMS]:
                food_items.append("comida")
        
        return food_items
    
    async def get_nutrition_info(self, food_item: str) -> Dict[str, Any]:
        """
        Obtiene información nutricional de un alimento.
        
        Args:
            food_item: Nombre del alimento
            
        Returns:
            Diccionario con información nutricional
        """
        nutrition_info = {
            "name": food_item,
            "calories": None,
            "protein": None,
            "carbs": None,
            "fat": None,
            "source": None
        }
        
        try:
            # Buscar en las fuentes de datos cargadas
            for source, df in self.food_data.items():
                if df is None or len(df) == 0 or 'name' not in df.columns:
                    continue
                    
                # Buscar coincidencias
                try:
                    matches = df[df['name'].str.contains(food_item, case=False, na=False)]
                    if not matches.empty:
                        # Tomar el primer resultado
                        match = matches.iloc[0]
                        
                        # Mapear campos según la fuente
                        if source == "usda":
                            if "calories" in match and pd.notna(match["calories"]):
                                nutrition_info["calories"] = float(match["calories"])
                            if "protein_g" in match and pd.notna(match["protein_g"]):
                                nutrition_info["protein"] = float(match["protein_g"])
                            if "carbohydrates_g" in match and pd.notna(match["carbohydrates_g"]):
                                nutrition_info["carbs"] = float(match["carbohydrates_g"])
                            if "fat_g" in match and pd.notna(match["fat_g"]):
                                nutrition_info["fat"] = float(match["fat_g"])
                        
                        elif source == "open_food_facts":
                            if "energy-kcal_100g" in match and pd.notna(match["energy-kcal_100g"]):
                                nutrition_info["calories"] = float(match["energy-kcal_100g"])
                            if "proteins_100g" in match and pd.notna(match["proteins_100g"]):
                                nutrition_info["protein"] = float(match["proteins_100g"])
                            if "carbohydrates_100g" in match and pd.notna(match["carbohydrates_100g"]):
                                nutrition_info["carbs"] = float(match["carbohydrates_100g"])
                            if "fat_100g" in match and pd.notna(match["fat_100g"]):
                                nutrition_info["fat"] = float(match["fat_100g"])
                        
                        nutrition_info["source"] = source
                        break
                except Exception as e:
                    print(f"Error al buscar coincidencias para {food_item}: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error al obtener información nutricional para {food_item}: {str(e)}")
        
        return nutrition_info
    
    async def integrate_vision_results(self, detected_foods: List[str]) -> List[Dict[str, Any]]:
        """
        Integra resultados de la visión por computadora con información nutricional.
        
        Args:
            detected_foods: Lista de alimentos detectados por la visión
            
        Returns:
            Lista de información nutricional para cada alimento detectado
        """
        nutrition_results = []
        
        for food in detected_foods:
            nutrition_info = await self.get_nutrition_info(food)
            nutrition_results.append(nutrition_info)
        
        return nutrition_results 