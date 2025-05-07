"""
Integrador de los distintos componentes de IA del sistema.
"""
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from backend.ai.vision.food_detector import FoodDetector
from backend.ai.nlp.simple_food_processor import SimpleFoodProcessor

# Cargar variables de entorno
load_dotenv()

class NutriVeciAI:
    def __init__(self, data_path: str = None):
        """
        Inicializa el integrador de IA para NutriVeci.
        
        Args:
            data_path: Ruta al directorio de datos nutricionales
        """
        # Configurar Gemini
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ API de Gemini configurada correctamente")
        else:
            self.gemini_model = None
            print("❌ ADVERTENCIA: GOOGLE_API_KEY o GEMINI_API_KEY no configurada. El modelo de lenguaje no estará disponible.")
        
        # Inicializar detector de alimentos (Clarifai)
        self.food_detector = FoodDetector()
        
        # Inicializar procesador de alimentos (versión simple)
        self.food_processor = SimpleFoodProcessor(data_path)
    
    async def analyze_text(self, text: str, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analiza texto del usuario para identificar alimentos y generar respuestas.
        
        Args:
            text: Texto a analizar
            user_profile: Perfil del usuario (opcional)
            
        Returns:
            Diccionario con la respuesta generada y metadatos
        """
        # Extraer alimentos del texto
        food_items = await self.food_processor.extract_food_items(text)
        
        # Obtener información nutricional de los alimentos
        nutrition_info = []
        for food in food_items:
            food_nutrition = await self.food_processor.get_nutrition_info(food)
            nutrition_info.append(food_nutrition)
        
        # Generar respuesta usando Gemini
        response = await self._generate_response(text, nutrition_info, user_profile)
        
        return {
            "food_items": food_items,
            "nutrition_info": nutrition_info,
            "generated_text": response,
            "source": "text_analysis"
        }
    
    async def analyze_image(self, image_bytes: bytes, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analiza una imagen para identificar alimentos y generar respuestas.
        
        Args:
            image_bytes: Datos binarios de la imagen
            user_profile: Perfil del usuario (opcional)
            
        Returns:
            Diccionario con la respuesta generada y metadatos
        """
        # Detectar alimentos en la imagen usando Clarifai
        detection_result = await self.food_detector.detect_food(image_bytes)
        
        if not detection_result["success"]:
            return {
                "error": detection_result.get("error", "Error al procesar la imagen"),
                "success": False
            }
        
        detected_foods = detection_result["detected_foods"]
        
        if not detected_foods:
            return {
                "error": "No se detectaron alimentos en la imagen",
                "success": False
            }
        
        # Obtener información nutricional de los alimentos detectados
        nutrition_info = await self.food_processor.integrate_vision_results(detected_foods)
        
        # Generar respuesta usando Gemini
        prompt = f"Se han detectado los siguientes alimentos en la imagen: {', '.join(detected_foods)}"
        response = await self._generate_response(prompt, nutrition_info, user_profile)
        
        return {
            "detected_foods": detected_foods,
            "confidence_scores": detection_result["confidence_scores"],
            "nutrition_info": nutrition_info,
            "generated_text": response,
            "success": True,
            "source": "image_analysis"
        }
    
    async def _generate_response(self, 
                               input_text: str, 
                               nutrition_info: List[Dict[str, Any]],
                               user_profile: Dict[str, Any] = None) -> str:
        """
        Genera una respuesta usando el modelo de lenguaje Gemini.
        
        Args:
            input_text: Texto de entrada
            nutrition_info: Información nutricional de los alimentos detectados
            user_profile: Perfil del usuario
            
        Returns:
            Texto generado
        """
        if not self.gemini_model:
            return "Lo siento, el modelo de lenguaje no está disponible en este momento."
        
        # Construir el contexto
        context = "Eres NutriVeci, un asistente nutricional que proporciona información precisa y consejos sobre alimentación saludable.\n\n"
        
        # Añadir información del perfil de usuario si está disponible
        if user_profile:
            context += "Perfil del usuario:\n"
            if "name" in user_profile and user_profile["name"]:
                context += f"- Nombre: {user_profile['name']}\n"
            if "age" in user_profile and user_profile["age"]:
                context += f"- Edad: {user_profile['age']}\n"
            if "weight" in user_profile and user_profile["weight"]:
                context += f"- Peso: {user_profile['weight']} kg\n"
            if "height" in user_profile and user_profile["height"]:
                context += f"- Altura: {user_profile['height']} cm\n"
            if "allergies" in user_profile and user_profile["allergies"]:
                allergies = ", ".join(user_profile["allergies"])
                context += f"- Alergias: {allergies}\n"
            context += "\n"
        
        # Añadir información nutricional de los alimentos detectados
        if nutrition_info:
            context += "Información nutricional detectada:\n"
            for info in nutrition_info:
                context += f"- Alimento: {info['name']}\n"
                if info["calories"] is not None:
                    context += f"  - Calorías: {info['calories']} kcal\n"
                if info["protein"] is not None:
                    context += f"  - Proteínas: {info['protein']} g\n"
                if info["carbs"] is not None:
                    context += f"  - Carbohidratos: {info['carbs']} g\n"
                if info["fat"] is not None:
                    context += f"  - Grasas: {info['fat']} g\n"
            context += "\n"
        
        # Consulta del usuario
        context += f"Consulta del usuario: {input_text}\n\n"
        
        # Instrucción clara para el modelo
        if nutrition_info:
            context += "Proporciona información nutricional detallada sobre los alimentos detectados. Incluye beneficios para la salud, recomendaciones de consumo, y posibles recetas saludables que los incluyan.\n\n"
        else:
            context += "Responde a la consulta del usuario de forma precisa y útil, ofreciendo consejos nutricionales y recomendaciones saludables.\n\n"
        
        try:
            # Generar respuesta
            response = await self.gemini_model.generate_content_async(context)
            return response.text
        except Exception as e:
            print(f"Error generando respuesta con Gemini: {str(e)}")
            return "Lo siento, hubo un error generando la respuesta. Por favor, intenta de nuevo." 