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
        # Hacer una solicitud a la API de NLP para interpretar el texto
        # Esta llamada ahora devolverá el campo is_food
        try:
            # URL de la API (configurada para localhost o la URL de producción)
            api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
            nlp_url = f"{api_base_url}/api/nlp/interpret"
            
            # Preparar datos para la solicitud
            user_id = user_profile.get("id") if user_profile else None
            source = user_profile.get("source", "app") if user_profile else "app"
            
            # Crear payload
            payload = {
                "text": text,
                "user_id": user_id,
                "source": source
            }
            
            # Importar aiohttp solo cuando sea necesario
            import aiohttp
            
            # Hacer solicitud a la API
            async with aiohttp.ClientSession() as session:
                async with session.post(nlp_url, json=payload) as response:
                    if response.status != 200:
                        # Si hay un error, usar el procesamiento local
                        print(f"Error conectando a la API NLP: {response.status}")
                        return await self._process_text_locally(text, user_profile)
                    
                    # Obtener la respuesta
                    api_response = await response.json()
                    
                    # Procesar la respuesta
                    return {
                        "intent": api_response.get("intent", "desconocido"),
                        "entities": api_response.get("entities", {}),
                        "is_food": "buscar_receta" in api_response.get("intent", "") or 
                                  "consultar_ingrediente" in api_response.get("intent", ""),
                        "generated_text": api_response.get("generated_text", ""),
                        "source": "nlp_api"
                    }
                    
        except Exception as e:
            print(f"Error al conectar con la API NLP: {str(e)}")
            # Si falla la API, usar procesamiento local
            return await self._process_text_locally(text, user_profile)
    
    async def _process_text_locally(self, text: str, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Procesa el texto localmente si la API no está disponible.
        """
        # Extraer alimentos del texto
        food_items = await self.food_processor.extract_food_items(text)
        
        # Lista de palabras comunes que no son alimentos
        non_food_words = [
            "puerta", "ventana", "casa", "edificio", "auto", "carro", "tren", "avión", "avion",
            "libro", "revista", "periódico", "periodico", "ropa", "zapatos", "sombrero", 
            "computadora", "teléfono", "telefono", "tablet", "silla", "mesa", "sofá", "sofa"
        ]
        
        # Verificar si hay palabras que no son alimentos
        input_tokens = text.lower().split()
        non_food_matches = [word for word in input_tokens if word in non_food_words]
        
        # Determinar si el texto contiene referencias a alimentos
        # Si hay coincidencias con palabras que no son alimentos y no hay alimentos identificados,
        # consideramos que no es una consulta sobre alimentos
        is_food = len(food_items) > 0 and len(non_food_matches) == 0
        
        # Obtener información nutricional de los alimentos
        nutrition_info = []
        for food in food_items:
            food_nutrition = await self.food_processor.get_nutrition_info(food)
            nutrition_info.append(food_nutrition)
        
        # Generar respuesta usando Gemini
        response = await self._generate_response(text, nutrition_info, user_profile, is_food)
        
        return {
            "food_items": food_items,
            "nutrition_info": nutrition_info,
            "is_food": is_food,
            "intent": "buscar_receta" if is_food else "otro",
            "entities": {f"entity_{i+1}": food for i, food in enumerate(food_items)},
            "generated_text": response,
            "source": "text_analysis_local"
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
                               user_profile: Dict[str, Any] = None,
                               is_food: bool = True) -> str:
        """
        Genera una respuesta usando el modelo de lenguaje Gemini.
        
        Args:
            input_text: Texto de entrada
            nutrition_info: Información nutricional de los alimentos detectados
            user_profile: Perfil del usuario
            is_food: Indica si la consulta es sobre alimentos
            
        Returns:
            Texto generado
        """
        if not self.gemini_model:
            return "Lo siento, el modelo de lenguaje no está disponible en este momento."
        
        # Construir el contexto
        context = "Eres NutriVeci, un asistente nutricional en español que proporciona información precisa y consejos sobre alimentación saludable.\n\n"
        context += "IMPORTANTE: TODAS TUS RESPUESTAS DEBEN SER EN ESPAÑOL. Si encuentras información en inglés, TRADÚCELA.\n\n"
        
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
        
        # Si no es consulta sobre alimentos, proporcionar información general del bot
        if not is_food and not nutrition_info:
            context += """
            El usuario ha enviado una consulta que no parece estar relacionada con alimentos o nutrición.
            Responde con un mensaje amigable en ESPAÑOL explicando las funcionalidades que ofreces como asistente nutricional.
            Menciona que puedes proporcionar:
            - Recomendaciones de recetas
            - Consejos nutricionales
            - Información sobre ingredientes y alimentos
            - Análisis de alimentos
            - Planificación de comidas
            
            Pregunta al usuario en qué le puedes ayudar específicamente sobre alimentación y nutrición.
            """
            try:
                response = await self.gemini_model.generate_content_async(context + f"\nConsulta del usuario: {input_text}")
                return response.text
            except Exception as e:
                print(f"Error generando respuesta con Gemini: {str(e)}")
                return """
                Soy un asistente nutricional inteligente que puede ayudarte con:
                - Recomendaciones de recetas
                - Consejos nutricionales
                - Información sobre ingredientes
                - Análisis de alimentos
                - Planificación de comidas
                
                ¿En qué puedo ayudarte hoy con tus consultas sobre alimentación y nutrición?
                """
        
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
            context += "Proporciona información nutricional detallada sobre los alimentos detectados EN ESPAÑOL. Incluye beneficios para la salud, recomendaciones de consumo, y posibles recetas saludables que los incluyan. ASEGÚRATE DE QUE TODA LA INFORMACIÓN ESTÉ EN ESPAÑOL, incluso si los datos originales estaban en inglés.\n\n"
        else:
            context += "Responde a la consulta del usuario de forma precisa y útil EN ESPAÑOL, ofreciendo consejos nutricionales y recomendaciones saludables.\n\n"
        
        try:
            # Generar respuesta
            response = await self.gemini_model.generate_content_async(context)
            return response.text
        except Exception as e:
            print(f"Error generando respuesta con Gemini: {str(e)}")
            return "Lo siento, hubo un error generando la respuesta. Por favor, intenta de nuevo." 