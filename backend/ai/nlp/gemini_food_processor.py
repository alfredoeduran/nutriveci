"""
Procesador de alimentos basado en Gemini para NutriVeci.

Este módulo reemplaza la implementación basada en NLTK por una versión
que utiliza Gemini para el procesamiento de lenguaje natural.
"""
import os
import csv
import json
import pandas as pd
import asyncio
from typing import List, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

# Configurar Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class GeminiFoodProcessor:
    def __init__(self, data_path: str = None):
        """
        Inicializa el procesador de alimentos basado en Gemini.
        
        Args:
            data_path: Ruta al directorio de datos nutricionales
        """
        # Configurar modelo de Gemini
        try:
            # Para procesamiento de texto, usar el modelo flash por velocidad
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print(f"✅ Modelo Gemini inicializado correctamente")
        except Exception as e:
            print(f"❌ Error inicializando Gemini: {str(e)}")
            self.model = None
            
        # Cargar datos nutricionales si se proporciona una ruta
        self.food_data = {}
        if data_path:
            self.load_food_data(data_path)
            
        # Memoria para alimentos nuevos encontrados por Gemini
        self.memory_foods = {}
        
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
            
            # Cargar Open Food Facts si existe
            off_path = os.path.join(processed_dir, "open_food_facts.csv")
            if os.path.exists(off_path):
                self.food_data["open_food_facts"] = pd.read_csv(off_path, low_memory=False)
                print(f"✅ Cargados {len(self.food_data['open_food_facts'])} alimentos de Open Food Facts")
                
            # Intentar cargar alimentos en memoria si existe el archivo
            memory_path = os.path.join(processed_dir, "memory_foods.json")
            if os.path.exists(memory_path):
                try:
                    with open(memory_path, 'r', encoding='utf-8') as f:
                        self.memory_foods = json.load(f)
                    print(f"✅ Cargados {len(self.memory_foods)} alimentos de memoria")
                except Exception as e:
                    print(f"❌ Error cargando alimentos de memoria: {str(e)}")
                    self.memory_foods = {}
        
        except Exception as e:
            print(f"❌ Error cargando datos nutricionales: {str(e)}")
            
    def save_memory_foods(self, data_path: str) -> None:
        """
        Guarda los alimentos en memoria a un archivo JSON.
        
        Args:
            data_path: Ruta al directorio de datos
        """
        if not self.memory_foods:
            return
            
        try:
            processed_dir = os.path.join(data_path, "processed")
            os.makedirs(processed_dir, exist_ok=True)
            
            memory_path = os.path.join(processed_dir, "memory_foods.json")
            with open(memory_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory_foods, f, ensure_ascii=False, indent=2)
                
            print(f"✅ Guardados {len(self.memory_foods)} alimentos en memoria")
        except Exception as e:
            print(f"❌ Error guardando alimentos en memoria: {str(e)}")
    
    def translate_text(self, text: str, target_lang: str = "en") -> str:
        """
        Traduce texto entre español e inglés usando Gemini.
        
        Args:
            text: Texto a traducir
            target_lang: Idioma objetivo ('en' o 'es')
            
        Returns:
            Texto traducido
        """
        if not self.model:
            return text
            
        try:
            source_lang = "es" if target_lang == "en" else "en"
            
            prompt = f"""
            TASK: Translate the following text from {source_lang} to {target_lang}.
            Just return the translated text, nothing else.
            
            TEXT: {text}
            
            TRANSLATION:
            """
            
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ Error traduciendo texto: {str(e)}")
            return text
    
    def extract_food_items_sync(self, text: str) -> List[str]:
        """
        Versión sincrónica para extraer nombres de alimentos de un texto usando Gemini.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de alimentos identificados
        """
        if not self.model or not GOOGLE_API_KEY:
            print("❌ Modelo Gemini no configurado correctamente")
            return ["comida"]
            
        try:
            # Traducir el texto al inglés si está en español
            prompt_traduccion = f"""
            TAREA: Determina si el siguiente texto está en español y si lo está, tradúcelo al inglés.
            Si ya está en inglés, devuelve exactamente el mismo texto.
            
            TEXTO: {text}
            
            RESULTADO:
            """
            
            # Usar el modelo de la forma correcta
            translation_response = self.model.generate_content(prompt_traduccion)
            translated_text = translation_response.text.strip()
            
            # Definir prompt para identificar alimentos
            prompt = f"""
            TASK: Identify all food items mentioned in the following text.
            
            INSTRUCTIONS:
            - Return only the names of identified food items
            - Each food item should be on a separate line
            - Do not include anything else, just the food names
            - If there are no food items, respond with the word "none"
            
            TEXT: {translated_text}
            
            FOOD ITEMS:
            """
            
            # Generar respuesta
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            if result_text.lower() == "none":
                return []
                
            # Separar por líneas y limpiar
            english_foods = [food.strip() for food in result_text.split('\n') if food.strip()]
            
            # Traducir los nombres de alimentos de vuelta al español para mostrarlos al usuario
            spanish_foods = []
            for food in english_foods:
                spanish_food = self.translate_text(food, target_lang="es")
                spanish_foods.append(spanish_food)
                
            return spanish_foods
            
        except Exception as e:
            print(f"❌ Error en extract_food_items_sync: {str(e)}")
            return []
    
    # Mantenemos esta función por compatibilidad
    async def extract_food_items(self, text: str) -> List[str]:
        """
        Extrae nombres de alimentos de un texto usando Gemini.
        
        Args:
            text: Texto a analizar
            
        Returns:
            Lista de alimentos identificados
        """
        return self.extract_food_items_sync(text)
    
    def get_nutrition_info_sync(self, food_item: str) -> Dict[str, Any]:
        """
        Versión sincrónica para obtener información nutricional de un alimento.
        
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
            # Verificar si el alimento está en la memoria
            food_lower = food_item.lower()
            if food_lower in self.memory_foods:
                stored_info = self.memory_foods[food_lower]
                nutrition_info.update(stored_info)
                nutrition_info["source"] = "memory"
                return nutrition_info
            
            # Traducir el nombre del alimento al inglés para buscarlo en la base de datos
            english_food = self.translate_text(food_item, target_lang="en")
            
            # Buscar en las fuentes de datos cargadas
            found = False
            for source, df in self.food_data.items():
                if df is None or len(df) == 0 or 'name' not in df.columns:
                    continue
                    
                # Buscar coincidencias
                try:
                    matches = df[df['name'].str.contains(english_food, case=False, na=False)]
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
                        found = True
                        break
                except Exception as e:
                    print(f"Error al buscar coincidencias para {food_item}: {str(e)}")
                    continue
                    
            # Si no se encontró información en la base de datos, consultar a Gemini
            if not found:
                try:
                    self._enrich_with_gemini_sync(nutrition_info)
                    
                    # Guardar en memoria para futuras consultas
                    if nutrition_info["calories"] is not None:
                        self.memory_foods[food_lower] = {
                            "name": food_item,
                            "calories": nutrition_info["calories"],
                            "protein": nutrition_info["protein"],
                            "carbs": nutrition_info["carbs"],
                            "fat": nutrition_info["fat"]
                        }
                        
                        # Intentar guardar la memoria actualizada
                        data_dir = Path(__file__).resolve().parent.parent.parent.parent / "data"
                        self.save_memory_foods(str(data_dir))
                        
                except Exception as e:
                    print(f"Error al enriquecer con Gemini: {str(e)}")
                
        except Exception as e:
            print(f"Error al obtener información nutricional para {food_item}: {str(e)}")
        
        return nutrition_info
        
    # Mantenemos esta función por compatibilidad
    async def get_nutrition_info(self, food_item: str) -> Dict[str, Any]:
        """
        Obtiene información nutricional de un alimento.
        
        Args:
            food_item: Nombre del alimento
            
        Returns:
            Diccionario con información nutricional
        """
        return self.get_nutrition_info_sync(food_item)
    
    def _enrich_with_gemini_sync(self, nutrition_info: Dict[str, Any]) -> None:
        """
        Versión sincrónica del enriquecimiento con Gemini.
        
        Args:
            nutrition_info: Información nutricional a enriquecer (se modifica in-place)
        """
        try:
            food_name = nutrition_info["name"]
            # Traducir al inglés para mejor precisión
            english_food = self.translate_text(food_name, target_lang="en")
            print(f"  Solicitando información nutricional para: {english_food}")
            
            prompt = f"""
            TASK: Provide nutritional information for a portion of {english_food}.
            
            INSTRUCTIONS:
            - Return the information in this exact format without additional explanations or sources:
            calories: [number]
            protein: [number]
            carbohydrates: [number]
            fat: [number]
            - Use grams for protein, carbohydrates, and fat, and kilocalories for calories
            - If you don't know a value, just leave a dash (-)
            - Don't include units in the numbers
            - Use only numbers, no ranges or approximations
            - Do NOT include any text like "Fuente: gemini" or source attribution
            
            NUTRITIONAL INFORMATION:
            """
            
            # Generar respuesta de la forma correcta
            response = self.model.generate_content(prompt)
            
            # Eliminar cualquier atribución de fuente como "Fuente: gemini" de la respuesta
            raw_text = response.text.strip()
            lines = [line for line in raw_text.split('\n') if 'fuente:' not in line.lower() and 'source:' not in line.lower()]
            response_text = '\n'.join(lines)
            
            print(f"  Respuesta de Gemini: {response_text}")
            
            # Procesar respuesta
            for line in lines:
                if ':' not in line:
                    continue
                    
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                
                # Ignorar valores no numéricos
                if value == '-' or not value.replace('.', '').isdigit():
                    continue
                
                try:
                    value_float = float(value)
                    if 'calor' in key:
                        nutrition_info["calories"] = value_float
                    elif 'prote' in key:
                        nutrition_info["protein"] = value_float
                    elif 'carbo' in key:
                        nutrition_info["carbs"] = value_float
                    elif 'gras' in key or 'fat' in key:
                        nutrition_info["fat"] = value_float
                except ValueError:
                    continue
                    
            nutrition_info["source"] = "gemini"
            
            # Configurar valores predeterminados si no se obtuvieron de Gemini
            if nutrition_info["calories"] is None:
                nutrition_info["calories"] = 100.0  # Valor por defecto
            if nutrition_info["protein"] is None:
                nutrition_info["protein"] = 5.0
            if nutrition_info["carbs"] is None:
                nutrition_info["carbs"] = 10.0
            if nutrition_info["fat"] is None:
                nutrition_info["fat"] = 3.0
                
            print(f"  Información final: calorías={nutrition_info['calories']}, proteínas={nutrition_info['protein']}, carbos={nutrition_info['carbs']}, grasas={nutrition_info['fat']}")
            
        except Exception as e:
            print(f"Error enriqueciendo información con Gemini: {str(e)}")
            # Establecer valores predeterminados en caso de error
            nutrition_info["calories"] = 100.0
            nutrition_info["protein"] = 5.0
            nutrition_info["carbs"] = 10.0
            nutrition_info["fat"] = 3.0
            nutrition_info["source"] = "default"
    
    # Mantenemos esta función por compatibilidad
    async def _enrich_with_gemini(self, nutrition_info: Dict[str, Any]) -> None:
        """
        Versión asíncrona del enriquecimiento con Gemini.
        
        Args:
            nutrition_info: Información nutricional a enriquecer (se modifica in-place)
        """
        self._enrich_with_gemini_sync(nutrition_info)
    
    def integrate_vision_results_sync(self, detected_foods: List[str]) -> List[Dict[str, Any]]:
        """
        Versión sincrónica para integrar resultados de la visión por computadora con información nutricional.
        
        Args:
            detected_foods: Lista de alimentos detectados por la visión (en inglés)
            
        Returns:
            Lista de información nutricional para cada alimento detectado
        """
        nutrition_results = []
        print(f"Procesando {len(detected_foods)} alimentos detectados: {detected_foods}")
        
        for food in detected_foods:
            try:
                print(f"Procesando alimento: {food}")
                # Traducir los nombres de alimentos detectados al español para mostrarlos al usuario
                spanish_food = self.translate_text(food, target_lang="es")
                print(f"  Traducción al español: {spanish_food}")
                
                # Obtener información nutricional con el nombre en español
                nutrition_info = self.get_nutrition_info_sync(spanish_food)
                print(f"  Info nutricional (español): calorías = {nutrition_info['calories']}")
                
                # Si no se encontró información con el nombre en español, intentar con el nombre en inglés
                if nutrition_info["calories"] is None:
                    print(f"  No se encontró info con nombre español, intentando con inglés: {food}")
                    nutrition_info = self.get_nutrition_info_sync(food)
                    print(f"  Info nutricional (inglés): calorías = {nutrition_info['calories']}")
                    
                    # Usar el nombre en español si se encontró información
                    if nutrition_info["calories"] is not None:
                        nutrition_info["name"] = spanish_food
                
                # Si aún no hay información, forzar el enriquecimiento con Gemini
                if nutrition_info["calories"] is None:
                    print(f"  No se encontró info en bases de datos, forzando enriquecimiento con Gemini")
                    # Crear un objeto nutrition_info base y enriquecerlo
                    nutrition_info = {
                        "name": spanish_food,
                        "calories": None,
                        "protein": None,
                        "carbs": None,
                        "fat": None,
                        "source": None
                    }
                    self._enrich_with_gemini_sync(nutrition_info)
                    print(f"  Después de forzar Gemini: calorías = {nutrition_info['calories']}")
                
                nutrition_results.append(nutrition_info)
            except Exception as e:
                print(f"Error procesando alimento {food}: {str(e)}")
                # Agregar un resultado básico para evitar que falle todo el proceso
                nutrition_results.append({
                    "name": food,
                    "calories": 0,
                    "protein": 0,
                    "carbs": 0,
                    "fat": 0,
                    "source": "error"
                })
        
        return nutrition_results
    
    # Mantenemos esta función por compatibilidad
    async def integrate_vision_results(self, detected_foods: List[str]) -> List[Dict[str, Any]]:
        """
        Integra resultados de la visión por computadora con información nutricional.
        
        Args:
            detected_foods: Lista de alimentos detectados por la visión
            
        Returns:
            Lista de información nutricional para cada alimento detectado
        """
        return self.integrate_vision_results_sync(detected_foods) 