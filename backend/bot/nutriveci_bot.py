"""
NutriVeci Bot de Telegram con interfaz de botones y menús.
"""
import os
import sys
import json
import logging
import time
import random
from datetime import datetime
from pathlib import Path
import asyncio
import uuid

# Agregar la raíz del proyecto al path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

# Importar el módulo imghdr personalizado (necesario para python-telegram-bot)
sys.path.insert(0, str(Path(__file__).parent))
import imghdr

# Importar dependencias de Telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler,
    Filters, CallbackContext, ConversationHandler
)
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                           TimedOut, NetworkError, RetryAfter)
from dotenv import load_dotenv

# Importar componentes del proyecto
from backend.ai.vision.food_detector_fixed import FoodDetector
from backend.ai.nlp.gemini_food_processor import GeminiFoodProcessor
from backend.db.recipes import (
    create_recipe, add_ingredient_to_recipe, get_recipe_by_id,
    get_user_recipes, add_recipe_to_history, search_recipes
)

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Clase auxiliar para manejar reintentos
class RetryHandler:
    """Clase para gestionar reintentos con espera exponencial."""
    
    def __init__(self, max_retries=3, base_delay=1, max_delay=30):
        """
        Inicializa el gestor de reintentos.
        
        Args:
            max_retries: Número máximo de reintentos
            base_delay: Retraso base en segundos
            max_delay: Retraso máximo en segundos
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute_with_retry(self, func, *args, **kwargs):
        """
        Ejecuta una función con reintentos.
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            Exception: Si todos los reintentos fallan
        """
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except (NetworkError, TimedOut, RetryAfter) as e:
                last_exception = e
                if attempt < self.max_retries:
                    # Calcular retraso con backoff exponencial y jitter
                    delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                    logger.warning(f"Error de red en intento {attempt+1}/{self.max_retries+1}. Reintentando en {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"Todos los reintentos fallaron: {str(e)}")
                    raise last_exception
            except Exception as e:
                # Para otros errores, no reintentamos
                logger.error(f"Error no recuperable: {str(e)}")
                raise e

# Crear instancia del manejador de reintentos
retry_handler = RetryHandler()

# Cargar variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configurar componentes
DATA_PATH = os.path.join(ROOT_DIR, "data")
food_detector = FoodDetector()

class ExtendedGeminiFoodProcessor(GeminiFoodProcessor):
    """Extensión del procesador Gemini con funcionalidades adicionales e integración con la API NLP."""
    
    def __init__(self, data_path=None):
        super().__init__(data_path)
        # URL base para la API (configurable por variable de entorno)
        self.api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        # Diccionario de alimentos comunes (español -> inglés)
        self.common_foods = {
            "manzana": "apple", "naranja": "orange", "plátano": "banana", "platano": "banana", 
            "pera": "pear", "uva": "grape", "kiwi": "kiwi", "fresa": "strawberry", 
            "arroz": "rice", "pasta": "pasta", "pan": "bread", "leche": "milk", 
            "queso": "cheese", "yogur": "yogurt", "huevo": "egg", "pollo": "chicken", 
            "carne": "meat", "pescado": "fish", "atún": "tuna", "atun": "tuna", 
            "salmón": "salmon", "salmon": "salmon", "cerdo": "pork", "res": "beef", 
            "tomate": "tomato", "lechuga": "lettuce", "zanahoria": "carrot", 
            "papa": "potato", "patata": "potato", "cebolla": "onion", "ajo": "garlic", 
            "brócoli": "broccoli", "brocoli": "broccoli", "coliflor": "cauliflower", "espinaca": "spinach",
            "maíz": "corn", "maiz": "corn", "frijol": "bean", "frijoles": "beans",
            "lenteja": "lentil", "lentejas": "lentils", "garbanzo": "chickpea", 
            "garbanzos": "chickpeas", "pimiento": "pepper", "azúcar": "sugar", "azucar": "sugar",
            "sal": "salt", "aceite": "oil", "mantequilla": "butter", "chocolate": "chocolate",
            "café": "coffee", "cafe": "coffee", "té": "tea", "te": "tea", "agua": "water"
        }
    
    def translate_text_sync(self, text, source_lang="es", target_lang="en"):
        """
        Traduce el texto desde un idioma a otro.
        
        Args:
            text: Texto a traducir.
            source_lang: Idioma fuente.
            target_lang: Idioma destino.
            
        Returns:
            str: Texto traducido.
        """
        try:
            # En una implementación real, aquí se llamaría a la API de Gemini
            # Aquí usamos una implementación simplificada
            # Ejemplo:
            if source_lang == "es" and target_lang == "en":
                # Diccionario ampliado de traducción español-inglés
                translations = {
                    "arroz": "rice",
                    "pollo": "chicken",
                    "huevo": "egg",
                    "brócoli": "broccoli",
                    "brocoli": "broccoli",
                    "leche": "milk",
                    "carne": "meat",
                    "pescado": "fish",
                    "frijoles": "beans",
                    "frijol": "bean",
                    "pan": "bread",
                    "tomate": "tomato",
                    "zanahoria": "carrot",
                    "cebolla": "onion",
                    "ajo": "garlic",
                    "queso": "cheese",
                    "manzana": "apple",
                    "plátano": "banana",
                    "platano": "banana",
                    "pasta": "pasta",
                    "azúcar": "sugar",
                    "azucar": "sugar",
                    "sal": "salt",
                    "pimienta": "pepper",
                    "aceite": "oil",
                    "mantequilla": "butter",
                    "agua": "water",
                    "café": "coffee",
                    "cafe": "coffee",
                    "té": "tea",
                    "te": "tea",
                    "naranja": "orange",
                    "limón": "lemon",
                    "limon": "lemon",
                    "lechuga": "lettuce",
                    "papa": "potato",
                    "patata": "potato",
                    "cerdo": "pork",
                    "res": "beef",
                    "atún": "tuna",
                    "atun": "tuna",
                    "salmón": "salmon",
                    "salmon": "salmon",
                    "maíz": "corn",
                    "maiz": "corn",
                    "avena": "oatmeal",
                    "chocolate": "chocolate",
                    "fresa": "strawberry",
                    "uva": "grape",
                    "pera": "pear",
                    "durazno": "peach",
                    "piña": "pineapple",
                    "mango": "mango",
                    "yogur": "yogurt",
                    "yogurt": "yogurt",
                    "calabaza": "pumpkin",
                    "espinaca": "spinach",
                    "coliflor": "cauliflower",
                    "habas": "beans",
                    "lentejas": "lentils",
                    "garbanzos": "chickpeas"
                }
                
                # Si está en el diccionario, devolver traducción; de lo contrario, mantener original
                return translations.get(text.lower(), text)
            elif source_lang == "en" and target_lang == "es":
                # Diccionario ampliado de traducción inglés-español
                translations = {
                    "rice": "arroz",
                    "chicken": "pollo",
                    "egg": "huevo",
                    "broccoli": "brócoli",
                    "milk": "leche",
                    "meat": "carne",
                    "fish": "pescado",
                    "beans": "frijoles",
                    "bean": "frijol",
                    "bread": "pan",
                    "tomato": "tomate",
                    "carrot": "zanahoria",
                    "onion": "cebolla",
                    "garlic": "ajo",
                    "cheese": "queso", 
                    "apple": "manzana",
                    "banana": "plátano",
                    "pasta": "pasta",
                    "sugar": "azúcar",
                    "salt": "sal",
                    "pepper": "pimienta",
                    "oil": "aceite",
                    "butter": "mantequilla",
                    "water": "agua",
                    "coffee": "café",
                    "tea": "té",
                    "orange": "naranja",
                    "lemon": "limón",
                    "lettuce": "lechuga",
                    "potato": "papa",
                    "pork": "cerdo",
                    "beef": "res",
                    "tuna": "atún",
                    "salmon": "salmón",
                    "corn": "maíz",
                    "oatmeal": "avena",
                    "chocolate": "chocolate",
                    "strawberry": "fresa",
                    "grape": "uva",
                    "pear": "pera",
                    "peach": "durazno",
                    "pineapple": "piña",
                    "mango": "mango",
                    "yogurt": "yogur",
                    "pumpkin": "calabaza",
                    "spinach": "espinaca",
                    "cauliflower": "coliflor",
                    "lentils": "lentejas",
                    "chickpeas": "garbanzos"
                }
                return translations.get(text.lower(), text)
            else:
                # Para otras combinaciones de idiomas, devolver el texto original
                return text
        except Exception as e:
            logger.error(f"Error en traducción: {str(e)}")
            return text  # Devolver el texto original si hay un error
    
    def check_food_with_nlp_api(self, text, user_id=None):
        """
        Consulta la API NLP para determinar si el texto es un alimento y obtener información.
        
        Args:
            text: Texto a analizar
            user_id: ID del usuario (opcional)
            
        Returns:
            dict: Respuesta del modelo con información sobre si es comida, intención, etc.
        """
        try:
            # Log inicial para depuración
            logger.info(f"API_CHECK: Verificando si '{text}' es un alimento...")
            
            # Lista extendida de palabras comunes que NO son alimentos (para filtrado)
            non_food_words = [
                # Construcción y objetos de casa
                "puerta", "ventana", "casa", "edificio", "auto", "carro", "tren", "avión", "avion",
                "silla", "mesa", "sofá", "sofa", "escritorio", "cama", "armario", "estante", "escalera",
                "piso", "techo", "pared", "azulejo", "ladrillo", "cemento", "piedra", "madera", "clavo",
                "tornillo", "martillo", "destornillador", "taladro", "pintura", "pincel", "rodillo",
                # Objetos personales y electrónicos
                "libro", "revista", "periódico", "periodico", "ropa", "zapatos", "sombrero", 
                "computadora", "teléfono", "telefono", "tablet", "televisor", "televisión", "radio",
                "reloj", "bolso", "cartera", "llave", "billetera", "moneda", "billete", "laptop",
                # Materiales
                "plástico", "plastico", "vidrio", "metal", "papel", "cartón", "carton", "tela",
                "algodón", "algodon", "lana", "cuero", "hierro", "acero", "cobre", "aluminio",
                # Lugares
                "oficina", "escuela", "hospital", "tienda", "parque", "jardín", "jardin", "calle",
                "avenida", "carretera", "autopista", "ciudad", "pueblo", "país", "pais", "continente",
                # Otras categorías irrelevantes
                "hola", "adiós", "adios", "gracias", "por favor", "ayuda", "que tal", "como estas"
            ]
            
            # Preparar texto para análisis
            text_lower = text.lower()
            words = text_lower.split()
            
            # Paso 1: Verificación prioritaria - Rechazar inmediatamente si contiene palabras de la lista negra
            for word in words:
                if word in non_food_words:
                    logger.info(f"API_CHECK: Palabra no-alimento detectada inmediatamente: '{word}' en '{text}'. RESULTADO: NO ES ALIMENTO")
                    return {
                        "is_food": False,
                        "intent": "otro",
                        "entities": {},
                        "generated_text": f"Lo siento, '{text}' no parece ser un alimento. Puedo ayudarte con información sobre alimentos como arroz, pollo, manzana, etc.",
                        "source": "strict_non_food_filter"
                    }
            
            # Paso 2: Verificar si hay coincidencia directa con alimentos conocidos
            food_matches = []
            for word in words:
                if word in self.common_foods:
                    food_matches.append(word)
                    
            if food_matches:
                logger.info(f"API_CHECK: Alimentos detectados localmente: {food_matches} en '{text}'. RESULTADO: ES ALIMENTO")
                # Convertir a entidades para la respuesta
                entities = {f"food_{i}": food for i, food in enumerate(food_matches, 1)}
                return {
                    "is_food": True,
                    "intent": "consultar_ingrediente",
                    "entities": entities,
                    "generated_text": f"Encontré información sobre {', '.join(food_matches)}.",
                    "source": "common_food_lookup"
                }
            
            # Paso 3: Verificación con Gemini para consultas que no estamos seguros
            # Consultar directamente a Gemini si el texto se refiere a un alimento
            try:
                food_check_prompt = f"""
                TAREA: Determina si el texto "{text}" se refiere a un alimento o bebida que los humanos consumen normalmente.
                
                RESPONDE ÚNICAMENTE con "SI" (si es un alimento/bebida) o "NO" (si no es un alimento/bebida).
                
                Ejemplos:
                - "manzana" → SI
                - "arroz" → SI
                - "puerta" → NO
                - "cemento" → NO
                - "escritorio" → NO
                - "edificio" → NO
                - "agua" → SI
                - "carne" → SI
                - "café" → SI
                - "piedra" → NO
                """
                
                food_check_response = self.model.generate_content(food_check_prompt)
                is_food_gemini = food_check_response.text.strip().upper() == "SI"
                
                if not is_food_gemini:
                    logger.info(f"Gemini directamente indica que '{text}' NO es un alimento")
                    return {
                        "is_food": False,
                        "intent": "otro",
                        "entities": {},
                        "generated_text": f"Lo siento, '{text}' no parece ser un alimento. Puedo ayudarte con información sobre alimentos como arroz, pollo, manzana, etc.",
                        "source": "gemini_direct_check"
                    }
            except Exception as e:
                logger.warning(f"Error en la verificación directa con Gemini: {str(e)}")
                # Si falla la verificación directa, continuar con el flujo normal
            
            # Paso 4: Si no hay coincidencia directa, consultar la API NLP
            import requests
            
            # Punto final de la API NLP
            nlp_url = f"{self.api_base_url}/api/nlp/interpret"
            
            # Crear payload
            payload = {
                "text": text,
                "user_id": str(user_id) if user_id else "unknown",
                "source": "telegram"
            }
            
            # Realizar solicitud a la API
            response = requests.post(nlp_url, json=payload, timeout=10)
            
            # Verificar si la respuesta es exitosa
            if response.status_code == 200:
                api_response = response.json()
                
                # Si la respuesta contiene "is_food", usarla directamente
                if "is_food" in api_response:
                    return {
                        "is_food": api_response.get("is_food", False),
                        "intent": api_response.get("intent", "desconocido"),
                        "entities": api_response.get("entities", {}),
                        "generated_text": api_response.get("generated_text", ""),
                        "source": "nlp_api"
                    }
                # Si no contiene "is_food", deducirlo de la intención
                else:
                    intent = api_response.get("intent", "")
                    is_food = "buscar_receta" in intent or "consultar_ingrediente" in intent
                    return {
                        "is_food": is_food,
                        "intent": intent,
                        "entities": api_response.get("entities", {}),
                        "generated_text": api_response.get("generated_text", ""),
                        "source": "nlp_api"
                    }
            else:
                # Paso 5: Si la API falla, intentar una detección de similitud con alimentos conocidos
                logger.warning(f"Error de API NLP: {response.status_code} - Usando detección fallback")
                
                # Verificar similitud parcial con alimentos conocidos
                partial_matches = []
                for word in words:
                    if len(word) >= 4:  # Palabras muy cortas pueden dar falsos positivos
                        for food in self.common_foods:
                            # Si hay una coincidencia parcial (ej: "manz" para "manzana")
                            if (word in food or food in word) and word not in partial_matches:
                                # Verificar que la palabra no esté en la lista de no-alimentos
                                if word not in non_food_words:
                                    partial_matches.append(food)
                                    break
                
                if partial_matches:
                    logger.info(f"Alimentos detectados por similitud: {partial_matches}")
                    entities = {f"food_{i}": food for i, food in enumerate(partial_matches, 1)}
                    return {
                        "is_food": True,
                        "intent": "consultar_ingrediente",
                        "entities": entities,
                        "generated_text": f"Encontré información sobre {', '.join(partial_matches)}.",
                        "source": "partial_match"
                    }
                
                # Si no hay coincidencias, devolver error
                return {
                    "is_food": False,
                    "error": f"Error comunicándose con la API: {response.status_code}",
                    "generated_text": f"No pude determinar si '{text}' es un alimento. Por favor, intenta nuevamente con un nombre de alimento específico.",
                    "source": "error"
                }
                
        except Exception as e:
            # Capturar excepciones y devolver respuesta de error
            logger.error(f"Excepción consultando API NLP: {str(e)}")
            return {
                "is_food": False,
                "error": f"Error: {str(e)}",
                "generated_text": f"Ocurrió un error procesando tu consulta. Por favor, intenta nuevamente.",
                "source": "error"
            }
    
    def is_food_related(self, text, user_id=None):
        """
        Determina si un texto está relacionado con alimentos usando la API NLP y validación adicional.
        
        Args:
            text: Texto a analizar.
            user_id: ID del usuario para contexto (opcional)
            
        Returns:
            bool: True si está relacionado con alimentos, False en caso contrario.
        """
        # Log inicial para depuración
        logger.info(f"FOOD_CHECK: Verificando si '{text}' es un alimento...")
        
        # Paso 1: Verificación rápida con lista local de alimentos comunes
        text_lower = text.lower()
        words = text_lower.split()
        
        # Verificar si hay palabras que no son alimentos (lista expandida)
        non_food_words = [
            # Construcción y objetos de casa
            "puerta", "ventana", "casa", "edificio", "auto", "carro", "tren", "avión", "avion",
            "silla", "mesa", "sofá", "sofa", "escritorio", "cama", "armario", "estante", "escalera",
            "piso", "techo", "pared", "azulejo", "ladrillo", "cemento", "piedra", "madera", "clavo",
            "tornillo", "martillo", "destornillador", "taladro", "pintura", "pincel", "rodillo",
            # Objetos personales y electrónicos
            "libro", "revista", "periódico", "periodico", "ropa", "zapatos", "sombrero", 
            "computadora", "teléfono", "telefono", "tablet", "televisor", "televisión", "radio",
            "reloj", "bolso", "cartera", "llave", "billetera", "moneda", "billete", "laptop",
            # Materiales
            "plástico", "plastico", "vidrio", "metal", "papel", "cartón", "carton", "tela",
            "algodón", "algodon", "lana", "cuero", "hierro", "acero", "cobre", "aluminio",
            # Lugares
            "oficina", "escuela", "hospital", "tienda", "parque", "jardín", "jardin", "calle",
            "avenida", "carretera", "autopista", "ciudad", "pueblo", "país", "pais", "continente",
            # Otras categorías irrelevantes
            "hola", "adiós", "adios", "gracias", "por favor", "ayuda", "que tal", "como estas"
        ]
        
        # Si CUALQUIER palabra en la consulta está en la lista de no-alimentos, retornar False
        for word in words:
            if word in non_food_words:
                logger.info(f"FOOD_CHECK: Palabra '{word}' encontrada en lista de no-alimentos. RESULTADO: NO ES ALIMENTO")
                return False
        
        # Verificar coincidencia directa con alimentos conocidos
        food_match_found = False
        for word in words:
            if word in self.common_foods:
                logger.info(f"FOOD_CHECK: Palabra '{word}' encontrada en diccionario de alimentos. RESULTADO: ES ALIMENTO")
                food_match_found = True
                break
        
        # Si se encontró una coincidencia directa con un alimento conocido, retornar True
        if food_match_found:
            return True
        
        # VERIFICACIÓN DIRECTA CON GEMINI
        # Esta verificación es crítica para palabras que no están en nuestras listas
        try:
            # Construir prompt para verificación específica de si es alimento
            food_check_prompt = f"""
            TAREA: Determina si el texto "{text}" se refiere a un alimento o bebida que los humanos consumen normalmente.
            
            RESPONDE ÚNICAMENTE con "SI" (si es un alimento/bebida) o "NO" (si no es un alimento/bebida).
            
            Ejemplos que son alimentos (respuesta = SI):
            - "manzana"
            - "arroz"
            - "agua"
            - "café"
            - "carne"
            
            Ejemplos que NO son alimentos (respuesta = NO):
            - "puerta"
            - "cemento"
            - "escritorio"
            - "edificio"
            - "piedra"
            - "ventana"
            """
            
            # Llamar a Gemini y obtener respuesta
            food_check_response = self.model.generate_content(food_check_prompt)
            response_text = food_check_response.text.strip().upper()
            
            # Registrar la respuesta exacta
            logger.info(f"FOOD_CHECK: Respuesta de Gemini para '{text}': '{response_text}'")
            
            # Evaluar la respuesta
            if response_text == "NO" or "NO" in response_text:
                logger.info(f"FOOD_CHECK: Gemini indica que '{text}' NO es un alimento. RESULTADO: NO ES ALIMENTO")
                return False
            elif response_text == "SI" or "SÍ" in response_text or "SI" in response_text:
                logger.info(f"FOOD_CHECK: Gemini indica que '{text}' ES un alimento. RESULTADO: ES ALIMENTO")
                return True
            else:
                logger.warning(f"FOOD_CHECK: Respuesta ambigua de Gemini para '{text}': '{response_text}'")
                # Si la respuesta es ambigua, continuar con otras verificaciones
        
        except Exception as e:
            logger.error(f"FOOD_CHECK: Error consultando Gemini: {str(e)}")
            # Si hay un error, continuar con otras verificaciones
        
        # Paso 2: Usar la API NLP como verificación secundaria
        try:
            result = self.check_food_with_nlp_api(text, user_id)
            is_food = result.get("is_food", False)
            logger.info(f"FOOD_CHECK: Verificación por API NLP para '{text}' resultado: {is_food}")
            
            if is_food:
                return True
            
            # Si la API dice que no es alimento, hacer una verificación final de similitud
            # Comprobar similitud parcial con alimentos conocidos
            food_similarity_found = False
            matching_food = None
            
            for word in words:
                if len(word) >= 4:  # Ignorar palabras muy cortas
                    for food in self.common_foods:
                        if word in food or food in word:
                            logger.info(f"FOOD_CHECK: Similitud parcial: '{word}' similar a '{food}'")
                            food_similarity_found = True
                            matching_food = food
                            break
                    if food_similarity_found:
                        break
            
            # Si se encontró similitud, verificar que no sea palabra prohibida
            if food_similarity_found:
                # Verificación adicional: si la palabra completa está en non_food_words, rechazar
                for word in words:
                    full_word_match = False
                    for food in self.common_foods:
                        if word == food:  # Solo coincidencia exacta
                            full_word_match = True
                            break
                    
                    if not full_word_match and word in non_food_words:
                        logger.info(f"FOOD_CHECK: Palabra '{word}' encontrada en lista de no-alimentos. RESULTADO: NO ES ALIMENTO")
                        return False
                
                logger.info(f"FOOD_CHECK: Similitud parcial aceptada para '{text}' similar a '{matching_food}'. RESULTADO: ES ALIMENTO")
                return True
            
            # Si llegamos aquí y ninguna verificación dio positivo, comprobar una última vez con Gemini
            try:
                # Construir un prompt más específico
                category_prompt = f"""
                ¿La palabra o frase "{text}" se refiere a un alimento/comida/bebida que los humanos consumen, o es otra cosa?
                
                Ejemplos de alimentos: manzana, arroz, agua, café, pollo, pan, queso, azúcar
                Ejemplos de NO alimentos: puerta, escritorio, cemento, edificio, silla, computadora
                
                Responde ÚNICAMENTE 'ALIMENTO' o 'NO ALIMENTO', sin más texto.
                """
                
                category_response = self.model.generate_content(category_prompt)
                category_text = category_response.text.strip().upper()
                
                logger.info(f"FOOD_CHECK: Segunda verificación con Gemini para '{text}': '{category_text}'")
                
                if "NO ALIMENTO" in category_text or "NO ES ALIMENTO" in category_text:
                    logger.info(f"FOOD_CHECK: Segunda verificación confirma que '{text}' NO es alimento. RESULTADO: NO ES ALIMENTO")
                    return False
                elif "ALIMENTO" in category_text and "NO ALIMENTO" not in category_text:
                    logger.info(f"FOOD_CHECK: Segunda verificación confirma que '{text}' ES alimento. RESULTADO: ES ALIMENTO")
                    return True
            except Exception as e:
                logger.error(f"FOOD_CHECK: Error en segunda verificación con Gemini: {str(e)}")
                # Continuar con el flujo normal en caso de error
        
        except Exception as e:
            logger.error(f"FOOD_CHECK: Error general en verificación de alimento: {str(e)}")
            # En caso de error, ser conservador y asumir que no es alimento
            return False
        
        # Si llegamos aquí, no encontramos evidencia suficiente para considerarlo un alimento
        logger.info(f"FOOD_CHECK: No hay evidencia suficiente para '{text}'. RESULTADO: NO ES ALIMENTO")
        return False
    
    def extract_food_items_sync(self, text, user_id=None):
        """
        Extrae alimentos del texto de forma síncrona usando la API NLP.
        
        Args:
            text: Texto a analizar.
            user_id: ID del usuario para contexto (opcional)
            
        Returns:
            list: Lista de alimentos encontrados.
        """
        # Consultar la API NLP
        result = self.check_food_with_nlp_api(text, user_id)
        
        # Extraer entidades si es un alimento
        if result.get("is_food", False):
            entities = result.get("entities", {})
            
            # Manejar diferentes formatos de entidades
            if isinstance(entities, dict):
                # Si es diccionario, extraer valores
                return list(entities.values())
            elif isinstance(entities, list):
                # Si ya es lista, usarla directamente
                return entities
            else:
                # Si es otro tipo, intentar convertirlo a lista
                try:
                    return [str(entities)]
                except:
                    return []
        
        # Si no es alimento o hay error, devolver lista vacía
        return []
    
    def load_usda_food_data(self, food_name):
        """
        Busca información nutricional en el dataset USDA.
        
        Args:
            food_name: Nombre del alimento a buscar
            
        Returns:
            dict: Información nutricional o None si no se encuentra
        """
        try:
            import pandas as pd
            
            # Ruta al dataset USDA
            usda_path = os.path.join(self.data_path, "processed", "usda_food_data.csv")
            
            if not os.path.exists(usda_path):
                logger.warning(f"Dataset USDA no encontrado en {usda_path}")
                return None
            
            # Cargar dataset (sólo columnas necesarias para optimizar memoria)
            usda_df = pd.read_csv(usda_path, low_memory=False, 
                               usecols=["name", "calories", "protein_g", "carbohydrates_g", "fat_g"])
            
            # Buscar coincidencias
            food_name_lower = food_name.lower()
            matches = usda_df[usda_df["name"].str.lower().str.contains(food_name_lower, na=False)]
            
            if not matches.empty:
                # Tomar el primer resultado
                match = matches.iloc[0]
                
                return {
                    "name": match["name"],
                    "calories": float(match["calories"]) if pd.notna(match["calories"]) else None,
                    "protein": float(match["protein_g"]) if pd.notna(match["protein_g"]) else None,
                    "carbs": float(match["carbohydrates_g"]) if pd.notna(match["carbohydrates_g"]) else None,
                    "fat": float(match["fat_g"]) if pd.notna(match["fat_g"]) else None,
                    "source": "usda"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando en USDA: {str(e)}")
            return None
    
    def generate_nutrition_info(self, food_name):
        """
        Genera información nutricional usando Gemini cuando no hay datos disponibles.
        
        Args:
            food_name: Nombre del alimento
            
        Returns:
            dict: Información nutricional generada
        """
        try:
            # Prompt para generar información nutricional
            prompt = f"""
            Genera información nutricional aproximada para: {food_name}
            
            Responde SOLO en formato JSON con esta estructura exacta:
            {{
              "calories": [calorías por 100g - número],
              "protein": [proteínas en gramos por 100g - número],
              "carbs": [carbohidratos en gramos por 100g - número],
              "fat": [grasas en gramos por 100g - número]
            }}
            
            No incluyas texto adicional, solo el JSON.
            """
            
            # Generar respuesta con Gemini
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Parsear el JSON de la respuesta
            import re
            import json
            
            # Buscar el JSON en la respuesta
            json_match = re.search(r'({.*})', response_text, re.DOTALL)
            if json_match:
                response_json = json.loads(json_match.group(1))
                
                # Construir respuesta
                return {
                    "name": food_name,
                    "calories": response_json.get("calories"),
                    "protein": response_json.get("protein"),
                    "carbs": response_json.get("carbs"),
                    "fat": response_json.get("fat"),
                    "source": "gemini_generated"
                }
            
            # Fallback si no se puede parsear JSON
            return {
                "name": food_name,
                "calories": 100,  # Valores de ejemplo
                "protein": 5,
                "carbs": 15,
                "fat": 2,
                "source": "gemini_fallback"
            }
            
        except Exception as e:
            logger.error(f"Error generando información nutricional: {str(e)}")
            # Valores de fallback
            return {
                "name": food_name,
                "calories": 100,
                "protein": 5,
                "carbs": 15,
                "fat": 2,
                "source": "gemini_error"
            }
    
    def get_nutrition_info_sync(self, food_name, user_id=None):
        """
        Obtiene información nutricional de forma síncrona consultando primero la API NLP.
        
        Args:
            food_name: Nombre del alimento
            user_id: ID del usuario (opcional)
            
        Returns:
            dict: Información nutricional
        """
        # Consultar la API NLP primero
        nlp_result = self.check_food_with_nlp_api(food_name, user_id)
        
        # Si no es un alimento según NLP, devolver respuesta de error
        if not nlp_result.get("is_food", False):
            return {
                "name": food_name,
                "calories": None,
                "protein": None,
                "carbs": None,
                "fat": None,
                "is_food": False,
                "generated_text": nlp_result.get("generated_text", "")
            }
        
        # Si es un alimento, proceder a obtener información nutricional
        logger.info(f"Obteniendo información nutricional para: {food_name}")
        
        # Guardar el nombre original en español
        food_name_es = food_name  
        
        # Traducir al inglés para buscar en las bases de datos
        food_name_en = self.translate_text_sync(food_name, "es", "en")
        logger.info(f"Nombre traducido al inglés: {food_name_en}")
        
        # Buscar en dataset USDA
        usda_info = self.load_usda_food_data(food_name_en)
        
        # Si se encontró en USDA, usar esa información
        if usda_info:
            logger.info(f"Encontrada información en USDA para: {food_name_en}")
            
            # Asegurarse de usar el nombre en español
            usda_info["name_en"] = usda_info.get("name", food_name_en)  # Guardar nombre en inglés
            usda_info["name"] = food_name_es  # Usar nombre en español como principal
            usda_info["is_food"] = True
            
            # Generar texto descriptivo con Gemini
            description = self.generate_food_description(food_name_es, usda_info)
            
            # Verificar y asegurar que la descripción esté en español
            if any(word in description.lower() for word in ["the", "and", "with", "food", "provides"]):
                logger.warning(f"La descripción parece estar en inglés, traduciéndola")
                description = self.translate_text_sync(description, "en", "es")
            
            usda_info["generated_text"] = description
            return usda_info
        
        # Si no está en USDA, generar con Gemini
        logger.info(f"No se encontró en USDA, generando información para: {food_name_en}")
        generated_info = self.generate_nutrition_info(food_name_en)
        
        # Asegurarse de usar el nombre en español
        generated_info["name_en"] = food_name_en  # Guardar nombre en inglés
        generated_info["name"] = food_name_es  # Usar nombre en español como principal
        generated_info["is_food"] = True
        
        # Generar texto descriptivo con Gemini
        description = self.generate_food_description(food_name_es, generated_info)
        
        # Verificar y asegurar que la descripción esté en español
        if any(word in description.lower() for word in ["the", "and", "with", "food", "provides"]):
            logger.warning(f"La descripción parece estar en inglés, traduciéndola")
            description = self.translate_text_sync(description, "en", "es")
        
        generated_info["generated_text"] = description
        return generated_info
    
    def generate_food_description(self, food_name, nutrition_info):
        """
        Genera una descripción del alimento con Gemini en español.
        
        Args:
            food_name: Nombre del alimento
            nutrition_info: Información nutricional
            
        Returns:
            str: Descripción generada en español
        """
        try:
            # Construir prompt con información nutricional
            calories = nutrition_info.get("calories", "desconocidas")
            protein = nutrition_info.get("protein", "desconocida")
            carbs = nutrition_info.get("carbs", "desconocidos")
            fat = nutrition_info.get("fat", "desconocida")
            
            prompt = f"""
            INSTRUCCIONES: Genera una descripción nutricional COMPLETAMENTE EN ESPAÑOL para el alimento: {food_name}
            
            IMPORTANTE: Tu respuesta DEBE estar TOTALMENTE en ESPAÑOL. NO USES NINGUNA PALABRA EN INGLÉS.
            
            Información nutricional disponible (por 100g):
            - Calorías: {calories} kcal
            - Proteínas: {protein} g
            - Carbohidratos: {carbs} g
            - Grasas: {fat} g
            
            Incluye:
            1. Breve descripción del alimento
            2. Beneficios para la salud
            3. Formas recomendadas de consumo
            4. Un dato nutricional interesante
            
            FORMATO: Responde DIRECTAMENTE con el texto, sin títulos ni secciones. 
            La respuesta debe ser completa pero concisa (máx. 150 palabras).
            La respuesta debe estar COMPLETAMENTE EN ESPAÑOL.
            """
            
            # Generar respuesta con Gemini
            response = self.model.generate_content(prompt)
            description = response.text.strip()
            
            # Verificar si la respuesta contiene palabras en inglés comunes
            english_words = ["the", "with", "and", "food", "provides", "contains", "rich", "source", "health", "benefits"]
            has_english = any(word in description.lower().split() for word in english_words)
            
            # Si parece estar en inglés, intentar de nuevo con un prompt más explícito
            if has_english:
                logger.warning(f"Descripción parece contener palabras en inglés. Regenerando en español puro.")
                
                spanish_prompt = f"""
                TAREA: Describe el alimento "{food_name}" y sus propiedades nutricionales.
                
                REQUISITO CRÍTICO: La respuesta DEBE estar TOTALMENTE EN ESPAÑOL, sin ninguna palabra en inglés.
                
                Datos (por 100g):
                - Calorías: {calories} kcal
                - Proteínas: {protein} g
                - Carbohidratos: {carbs} g
                - Grasas: {fat} g
                
                Incluye: descripción, beneficios, consumo y dato interesante.
                Sé breve pero completo (máx 150 palabras).
                RESPONDE ÚNICAMENTE EN ESPAÑOL.
                """
                
                response = self.model.generate_content(spanish_prompt)
                description = response.text.strip()
                
                # Verificar una vez más
                if any(word in description.lower().split() for word in english_words):
                    # Traducir al español como último recurso
                    description = self.translate_text_sync(description, "en", "es")
            
            return description
            
        except Exception as e:
            logger.error(f"Error generando descripción: {str(e)}")
            # Fallback simple
            return f"{food_name} es un alimento que aporta aproximadamente {nutrition_info.get('calories', 100)} kcal por cada 100g. Es recomendable incluirlo en una dieta balanceada."

food_processor = ExtendedGeminiFoodProcessor(DATA_PATH)

# Estados para el ConversationHandler
MAIN_MENU, TEXT_FOOD, IMAGE_FOOD, COMPLETE_MEAL_MENU, FOOD_HISTORY, CREATE_RECIPE, ADD_INGREDIENTS, VIEW_RECIPES, REQUEST_RECIPE = range(9)

# Datos temporales
recipe_context = {}  # Almacena contexto durante creación de recetas
user_data = {}  # Almacena datos de usuarios

def get_user_data(user_id):
    """
    Obtiene o inicializa los datos de un usuario.
    
    Args:
        user_id: ID del usuario
        
    Returns:
        dict: Datos del usuario
    """
    if user_id not in user_data:
        user_data[user_id] = {
            "history": [],  # Historial de búsquedas
            "daily_calories": 0.0,  # Calorías acumuladas hoy
            "preferences": {},  # Preferencias del usuario
            "last_interaction": datetime.now().isoformat()  # Última interacción
        }
    return user_data[user_id]

def get_main_menu_keyboard():
    """
    Genera el teclado para el menú principal.
    
    Returns:
        InlineKeyboardMarkup: Teclado con botones
    """
    keyboard = [
        [InlineKeyboardButton("🥗 Ingresar alimento", callback_data='food_input')],
        [InlineKeyboardButton("🍽️ Ingresar plato completo", callback_data='meal_input')],
        [InlineKeyboardButton("📋 Ver historial", callback_data='history')],
        [InlineKeyboardButton("📊 Calorías acumuladas", callback_data='calories')],
        [InlineKeyboardButton("📖 Mis recetas", callback_data='view_recipes')],
        [InlineKeyboardButton("🧪 Crear receta", callback_data='create_recipe')],
        [InlineKeyboardButton("🔍 Solicitar receta", callback_data='request_recipe')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_food_input_keyboard():
    """
    Genera el teclado con alimentos comunes sugeridos.
    
    Returns:
        InlineKeyboardMarkup: Teclado con botones
    """
    keyboard = [
        [
            InlineKeyboardButton("🍚 Arroz", callback_data='food_arroz'),
            InlineKeyboardButton("🥚 Huevo", callback_data='food_huevo'),
            InlineKeyboardButton("🐔 Pollo", callback_data='food_pollo')
        ],
        [
            InlineKeyboardButton("🥦 Brócoli", callback_data='food_brócoli'),
            InlineKeyboardButton("🥛 Leche", callback_data='food_leche'),
            InlineKeyboardButton("🍎 Manzana", callback_data='food_manzana')
        ],
        [InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_complete_meal_menu_keyboard():
    """
    Genera el teclado para ingresar plato completo.
    
    Returns:
        InlineKeyboardMarkup: Teclado con botones
    """
    keyboard = [
        [InlineKeyboardButton("📝 Texto (separado por comas)", callback_data='meal_text')],
        [InlineKeyboardButton("🖼️ Foto del plato", callback_data='meal_image')],
        [InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_action_keyboard():
    """
    Genera el teclado con acciones después de mostrar información.
    
    Returns:
        InlineKeyboardMarkup: Teclado con botones
    """
    keyboard = [
        [InlineKeyboardButton("➕ Agregar otro alimento", callback_data='food_input')],
        [InlineKeyboardButton("📋 Ver historial", callback_data='history')],
        [InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_recipe_menu_keyboard():
    """
    Genera el teclado para el menú de creación de receta.
    
    Returns:
        InlineKeyboardMarkup: Teclado con botones
    """
    keyboard = [
        [InlineKeyboardButton("➕ Agregar ingredientes", callback_data='add_ingredients')],
        [InlineKeyboardButton("💾 Guardar receta", callback_data='save_recipe')],
        [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_recipe')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_ingredients_keyboard():
    """
    Genera el teclado para agregar ingredientes.
    
    Returns:
        InlineKeyboardMarkup: Teclado con botones
    """
    keyboard = [
        [InlineKeyboardButton("✅ Terminar de agregar", callback_data='finish_adding')],
        [InlineKeyboardButton("❌ Cancelar", callback_data='cancel_recipe')]
    ]
    return InlineKeyboardMarkup(keyboard)

def start(update: Update, context: CallbackContext) -> int:
    """Inicia la conversación y muestra el menú principal."""
    user = update.effective_user
    
    # Inicializar datos de usuario si no existen
    get_user_data(user.id)
    
    # Mensaje de bienvenida
    update.message.reply_text(
        f"Hola {user.first_name}! 👋\n\n"
        "Soy NutriVeci 🥗, tu asistente nutricional personal.\n\n"
        "¿Qué te gustaría hacer hoy?",
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

def menu_command(update: Update, context: CallbackContext) -> int:
    """Muestra el menú principal."""
    update.message.reply_text(
        "Menú Principal - Selecciona una opción:",
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

def help_command(update: Update, context: CallbackContext) -> None:
    """Muestra información de ayuda."""
    update.message.reply_text(
        "🔍 *Guía de NutriVeci* 🥗\n\n"
        "• Usa el menú para navegar por las opciones\n"
        "• Consulta información de alimentos individuales\n"
        "• Analiza platos completos con fotos o texto\n"
        "• Revisa tu historial de consultas\n"
        "• Crea y guarda tus propias recetas\n\n"
        "Para volver al menú principal en cualquier momento, escribe /menu.",
        parse_mode=ParseMode.MARKDOWN
    )

def reset_command(update: Update, context: CallbackContext) -> int:
    """Reinicia los datos del usuario."""
    user_id = update.effective_user.id
    
    # Reiniciar datos
    if user_id in user_data:
        user_data[user_id] = {
            "history": [],
            "daily_calories": 0.0,
            "preferences": {},
            "last_interaction": datetime.now().isoformat()
        }
    
    update.message.reply_text(
        "✅ Datos reiniciados correctamente.\n"
        "Tu historial y calorías acumuladas han sido borrados.",
        reply_markup=get_main_menu_keyboard()
    )
    
    return MAIN_MENU

def button_handler(update: Update, context: CallbackContext) -> int:
    """Maneja las interacciones con botones."""
    query = update.callback_query
    
    try:
        query.answer()
    except Exception as e:
        logger.warning(f"No se pudo responder al callback query: {str(e)}")
    
    data = query.data
    user_id = query.from_user.id
    
    # Manejo de los diferentes botones
    if data == 'main_menu':
        try:
            query.edit_message_text(
                "Menú Principal - Selecciona una opción:",
                reply_markup=get_main_menu_keyboard()
            )
        except Exception as e:
            logger.error(f"Error editando mensaje: {str(e)}")
            # Intenta enviar un nuevo mensaje en lugar de editar
            context.bot.send_message(
                chat_id=query.message.chat_id,
                text="Menú Principal - Selecciona una opción:",
                reply_markup=get_main_menu_keyboard()
            )
        return MAIN_MENU
        
    elif data == 'food_input':
        query.edit_message_text(
            "🥗 *Ingresar alimento*\n\n"
            "Escribe el nombre de un alimento o selecciona uno de los sugeridos:",
            reply_markup=get_food_input_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return TEXT_FOOD
        
    elif data == 'meal_input':
        query.edit_message_text(
            "🍽️ *Ingresar plato completo*\n\n"
            "¿Cómo quieres ingresar tu plato?",
            reply_markup=get_complete_meal_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return COMPLETE_MEAL_MENU
        
    elif data == 'meal_text':
        query.edit_message_text(
            "📝 Por favor, escribe los alimentos de tu plato separados por comas.\n"
            "Ejemplo: *pollo, arroz, ensalada*",
            parse_mode=ParseMode.MARKDOWN
        )
        return TEXT_FOOD
        
    elif data == 'meal_image':
        query.edit_message_text(
            "🖼️ Por favor, envía una foto de tu plato y analizaré los alimentos que contiene."
        )
        return IMAGE_FOOD
        
    elif data == 'history':
        user_info = get_user_data(user_id)
        history = user_info["history"]
        
        if not history:
            query.edit_message_text(
                "No tienes búsquedas recientes.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            history_text = "*Historial de búsquedas:*\n\n"
            for i, item in enumerate(history[-10:], 1):  # Mostrar los últimos 10 elementos
                food_name = item["name"]
                calories = item["calories"] if item["calories"] is not None else "N/A"
                history_text += f"{i}. {food_name}: {calories} kcal\n"
            
            query.edit_message_text(
                history_text,
                reply_markup=get_action_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        return FOOD_HISTORY
        
    elif data == 'calories':
        user_info = get_user_data(user_id)
        daily_calories = user_info["daily_calories"]
        
        query.edit_message_text(
            f"📊 *Calorías acumuladas hoy:* {daily_calories:.1f} kcal\n\n"
            "Recuerda que una dieta balanceada es importante para mantener una buena salud. "
            "El número de calorías diarias recomendadas varía según edad, sexo, peso y nivel de actividad física.",
            reply_markup=get_action_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return MAIN_MENU
        
    elif data == 'clear_history':
        user_info = get_user_data(user_id)
        user_info["history"] = []
        
        query.edit_message_text(
            "✅ Historial limpiado correctamente.",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
        
    elif data == 'recent_foods':
        user_info = get_user_data(user_id)
        history = user_info["history"]
        
        if not history:
            query.edit_message_text(
                "No hay alimentos recientes en tu historial.",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            recent_text = "*Alimentos recientes:*\n\n"
            for i, item in enumerate(history[-5:], 1):  # Mostrar los últimos 5 elementos
                food_name = item["name"]
                calories = item["calories"] if item["calories"] is not None else "N/A"
                recent_text += f"{i}. {food_name}: {calories} kcal\n"
            
            query.edit_message_text(
                recent_text,
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        return MAIN_MENU
    
    elif data == 'create_recipe':
        # Iniciar proceso de creación de receta
        query.edit_message_text(
            "🧪 *Crear receta nueva*\n\n"
            "Por favor, escribe el nombre de tu receta:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Inicializar contexto para la receta
        recipe_context[user_id] = {
            "step": "name",
            "name": "",
            "description": "",
            "ingredients": []
        }
        
        return CREATE_RECIPE
        
    elif data == 'view_recipes':
        # Ver recetas guardadas
        try:
            # Mensajes de carga
            query.edit_message_text("Cargando tus recetas... ⏳")
            
            # Cargar recetas desde el archivo local filtradas por usuario
            local_recipes = load_saved_recipes(limit=20, user_id=user_id)
            
            # Intentar cargar también desde Supabase (si está configurado)
            supabase_recipes = []
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    # Si el loop está cerrado, crear uno nuevo
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Ejecutar la función asíncrona de forma segura
                if loop.is_running():
                    # Si el loop ya está corriendo, usar un enfoque diferente
                    future = asyncio.run_coroutine_threadsafe(
                        get_user_recipes(str(user_id), limit=10),
                        loop
                    )
                    # Esperar el resultado con timeout
                    supabase_recipes = future.result(timeout=5)
                else:
                    # Si el loop no está corriendo, podemos ejecutar normalmente
                    supabase_recipes = loop.run_until_complete(get_user_recipes(str(user_id), limit=10))
            except Exception as e:
                logger.warning(f"No se pudieron cargar recetas de Supabase: {str(e)}")
                # Continuar con las recetas locales solamente
            
            # Combinar recetas de ambas fuentes
            all_recipes = local_recipes + supabase_recipes
            
            if not all_recipes:
                # Si no hay recetas, mostrar mensaje y opciones para solicitar receta
                query.edit_message_text(
                    "No tienes recetas guardadas aún. ¡Solicita una receta nueva!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔍 Solicitar receta", callback_data='request_recipe')],
                        [InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')]
                    ])
                )
            else:
                # Si hay recetas, mostrarlas
                # Ordenar por fecha si es posible
                try:
                    all_recipes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
                except Exception as e:
                    logger.warning(f"No se pudieron ordenar las recetas: {str(e)}")
                
                # Crear texto y teclado para mostrar
                recipes_text = "📖 *Tus recetas guardadas:*\n\n"
                keyboard = []
                
                # Añadir cada receta al texto y al teclado
                for i, recipe in enumerate(all_recipes, 1):
                    try:
                        # Determinar nombre y origen de forma segura
                        recipe_name = recipe.get('name', f"Receta {i}")
                        if not isinstance(recipe_name, str):
                            recipe_name = f"Receta {i}"
                        
                        source = recipe.get('source', 'desconocido')
                        source_emoji = "🤖" if source == "gemini" else "📚" if source == "foodcom" else "💾"
                        
                        # Añadir al texto
                        recipes_text += f"{i}. {source_emoji} {recipe_name}\n"
                        
                        # El callback_data debe tener un formato que indique si es local o Supabase
                        recipe_id = str(recipe.get('id', f"id-{i}"))
                        # Limitar longitud del id para evitar problemas con Telegram
                        if len(recipe_id) > 30:
                            recipe_id = recipe_id[:30]
                        
                        # Determinar si es local o supabase basado en su posición en la lista
                        callback_suffix = recipe_id
                        
                        # Añadir al teclado
                        keyboard.append([
                            InlineKeyboardButton(
                                f"{source_emoji} {recipe_name[:30]}{'...' if len(recipe_name) > 30 else ''}", 
                                callback_data=f"recipe_{callback_suffix}"
                            )
                        ])
                    except Exception as e:
                        logger.error(f"Error procesando receta #{i}: {str(e)}")
                        continue
                
                # Agregar botón para volver
                keyboard.append([
                    InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')
                ])
                
                # Mostrar recetas
                try:
                    query.edit_message_text(
                        recipes_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
                except Exception as e:
                    # Si hay problema mostrando todas las recetas (texto muy largo), mostrar menos
                    logger.warning(f"Problema mostrando todas las recetas: {str(e)}")
                    query.edit_message_text(
                        "📖 *Tus recetas guardadas:*\n\n" + 
                        f"Se encontraron {len(all_recipes)} recetas. Selecciona una para ver detalles:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode=ParseMode.MARKDOWN
                    )
            
            return VIEW_RECIPES
            
        except Exception as e:
            logger.error(f"Error cargando recetas: {str(e)}", exc_info=True)
            query.edit_message_text(
                "Error al cargar tus recetas. Por favor, intenta de nuevo.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        
    elif data == 'add_ingredients':
        # Agregar ingredientes a la receta en creación
        if user_id not in recipe_context:
            # Si no hay receta en creación, regresar al menú principal
            query.edit_message_text(
                "No hay una receta en proceso de creación.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        
        query.edit_message_text(
            f"🧪 *Agregando ingredientes a: {recipe_context[user_id]['name']}*\n\n"
            "Por favor, ingresa cada ingrediente con su cantidad en este formato:\n"
            "*Ingrediente - cantidad*\n\n"
            "Ejemplo: *Harina - 2 tazas*\n\n"
            "Ingresa un ingrediente a la vez y presiona enviar.",
            reply_markup=get_ingredients_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        recipe_context[user_id]["step"] = "ingredients"
        return ADD_INGREDIENTS
        
    elif data == 'finish_adding':
        # Terminar de agregar ingredientes
        if user_id not in recipe_context:
            query.edit_message_text(
                "No hay una receta en proceso de creación.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        
        # Mostrar resumen de la receta
        recipe = recipe_context[user_id]
        
        summary = f"🧪 *Receta: {recipe['name']}*\n\n"
        summary += f"📝 *Descripción:* {recipe['description']}\n\n"
        summary += "🥗 *Ingredientes:*\n"
        
        if recipe['ingredients']:
            for i, ingredient in enumerate(recipe['ingredients'], 1):
                summary += f"{i}. {ingredient['name']} - {ingredient['quantity']}\n"
        else:
            summary += "No se han agregado ingredientes aún.\n"
        
        summary += "\n¿Qué deseas hacer ahora?"
        
        query.edit_message_text(
            summary,
            reply_markup=get_recipe_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return CREATE_RECIPE
        
    elif data == 'save_recipe':
        # Guardar la receta en la base de datos
        if user_id not in recipe_context:
            query.edit_message_text(
                "No hay una receta en proceso de creación.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        
        recipe = recipe_context[user_id]
        
        try:
            # Crear la receta primero
            loop = asyncio.get_event_loop()
            created_recipe = loop.run_until_complete(create_recipe(recipe['name'], recipe['description']))
            
            if not created_recipe or 'id' not in created_recipe:
                raise Exception("Error al crear la receta")
            
            recipe_id = created_recipe['id']
            
            # Agregar cada ingrediente
            if recipe['ingredients']:
                for ingredient in recipe['ingredients']:
                    loop.run_until_complete(add_ingredient_to_recipe(
                        recipe_id, 
                        ingredient['name'], 
                        ingredient['quantity']
                    ))
            
            # Registrar en el historial del usuario
            loop.run_until_complete(add_recipe_to_history(str(user_id), recipe_id, "user_created"))
            
            # Limpiar el contexto
            del recipe_context[user_id]
            
            query.edit_message_text(
                "✅ ¡Receta guardada correctamente!\n\n"
                f"Tu receta *{recipe['name']}* ha sido guardada y ahora puedes consultarla en cualquier momento.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 Ver mis recetas", callback_data='view_recipes')],
                    [InlineKeyboardButton("🏠 Menú principal", callback_data='main_menu')]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error guardando receta: {str(e)}")
            query.edit_message_text(
                "❌ Lo siento, ocurrió un error al guardar la receta. Por favor, intenta de nuevo.",
                reply_markup=get_main_menu_keyboard()
            )
        
        return MAIN_MENU
        
    elif data == 'cancel_recipe':
        # Cancelar la creación de la receta
        if user_id in recipe_context:
            del recipe_context[user_id]
        
        query.edit_message_text(
            "❌ Creación de receta cancelada.",
            reply_markup=get_main_menu_keyboard()
        )
        
        return MAIN_MENU
        
    elif data.startswith('recipe_'):
        # Ver detalles de una receta específica
        recipe_id_info = data[7:]  # Extraer el ID e información de la receta
        
        try:
            # Mostrar mensaje de carga
            try:
                query.edit_message_text("Cargando detalles de la receta... ⏳")
            except Exception as e:
                logger.warning(f"No se pudo mostrar mensaje de carga: {str(e)}")
            
            # Dependiendo del formato del ID, cargar desde Supabase o archivo local
            recipe = None
            
            if recipe_id_info.startswith('local_'):
                # Es una receta local, cargar desde memory_recetas.json
                recipe_id = recipe_id_info[6:]  # Quitar 'local_'
                logger.info(f"Buscando receta local con ID: {recipe_id}")
                local_recipes = load_saved_recipes()
                
                # Buscar la receta con el ID correspondiente
                for r in local_recipes:
                    if str(r.get('id', '')) == recipe_id:
                        recipe = r
                        logger.info(f"Receta local encontrada: {r.get('name', 'Sin nombre')}")
                        break
            
            elif recipe_id_info.startswith('supabase_'):
                # Es una receta de Supabase
                recipe_id = recipe_id_info[9:]  # Quitar 'supabase_'
                logger.info(f"Buscando receta Supabase con ID: {recipe_id}")
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                    
                    if loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(
                            get_recipe_by_id(recipe_id),
                            loop
                        )
                        recipe = future.result(timeout=5)
                    else:
                        recipe = loop.run_until_complete(get_recipe_by_id(recipe_id))
                    
                    logger.info(f"Receta Supabase encontrada: {recipe.get('name', 'Sin nombre')}")
                except Exception as e:
                    logger.error(f"Error cargando receta de Supabase: {str(e)}")
            
            else:
                # Formato simplificado - buscar directamente en memory_recetas.json
                recipe_id = recipe_id_info
                logger.info(f"Buscando receta con ID: {recipe_id}")
                
                # Buscar primero en las recetas locales
                local_recipes = load_saved_recipes(limit=100)  # Aumentar límite para no perder recetas
                
                # Si estamos en un contexto de usuario, intentar también con recetas filtradas
                if user_id:
                    user_recipes = load_saved_recipes(limit=100, user_id=user_id)
                    # Combinar ambas listas sin duplicados
                    seen_ids = set(r.get('id', '') for r in local_recipes)
                    for r in user_recipes:
                        if r.get('id', '') not in seen_ids:
                            local_recipes.append(r)
                
                logger.info(f"Cargadas {len(local_recipes)} recetas locales para búsqueda")
                
                for r in local_recipes:
                    r_id = str(r.get('id', ''))
                    # Depurar cada ID para encontrar problemas
                    logger.info(f"Comparando IDs: '{r_id}' con '{recipe_id}'")
                    
                    # Permitir coincidencias parciales si los IDs son truncados
                    if r_id == recipe_id or r_id.startswith(recipe_id) or recipe_id.startswith(r_id):
                        recipe = r
                        logger.info(f"Receta local encontrada: {r.get('name', 'Sin nombre')}")
                        break
                
                # Solo si no se encuentra localmente, intentar en Supabase
                if not recipe:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_closed():
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                        
                        if loop.is_running():
                            future = asyncio.run_coroutine_threadsafe(
                                get_recipe_by_id(recipe_id),
                                loop
                            )
                            recipe = future.result(timeout=5)
                        else:
                            recipe = loop.run_until_complete(get_recipe_by_id(recipe_id))
                    except Exception as e:
                        logger.warning(f"No se pudo cargar receta {recipe_id} de Supabase: {str(e)}")
            
            if not recipe:
                logger.warning(f"Receta no encontrada con ID: {recipe_id_info}")
                query.edit_message_text(
                    "Receta no encontrada.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📖 Ver otras recetas", callback_data='view_recipes')],
                        [InlineKeyboardButton("🏠 Menú principal", callback_data='main_menu')]
                    ])
                )
                return MAIN_MENU
            
            # Mostrar detalles de la receta
            recipe_text = f"🧪 *{recipe.get('name', 'Receta sin nombre')}*\n\n"
            
            # Información sobre la fuente
            source = recipe.get('source', 'desconocido')
            if source == "gemini":
                recipe_text += "🤖 *Fuente:* Generada por IA\n\n"
            elif source == "foodcom":
                recipe_text += "📚 *Fuente:* Recetario Food.com\n\n"
            
            # Descripción
            if recipe.get('description'):
                recipe_text += f"📝 *Descripción:* {recipe.get('description')}\n\n"
            
            # Ingredientes
            recipe_text += "🥗 *Ingredientes:*\n"
            
            # Manejar diferentes formatos de ingredientes
            ingredients = recipe.get('ingredients', [])
            if isinstance(ingredients, list):
                for i, ingredient in enumerate(ingredients, 1):
                    # Verificar el formato del ingrediente (dependiendo si es de Supabase o local)
                    if isinstance(ingredient, dict) and 'name' in ingredient and 'quantity' in ingredient:
                        # Formato Supabase
                        recipe_text += f"{i}. {ingredient['name']} - {ingredient['quantity']}\n"
                    else:
                        # Formato local/simple
                        recipe_text += f"{i}. {ingredient}\n"
            else:
                recipe_text += "No hay ingredientes registrados para esta receta.\n"
            
            # Pasos/Instrucciones
            steps = recipe.get('steps', [])
            if steps:
                recipe_text += "\n📋 *Instrucciones:*\n"
                for i, step in enumerate(steps, 1):
                    recipe_text += f"{i}. {step}\n"
            
            # Si el texto es muy largo, acortarlo para evitar errores de Telegram
            if len(recipe_text) > 4000:
                recipe_text = recipe_text[:3900] + "\n\n... (texto truncado debido a limitaciones de Telegram)"
            
            query.edit_message_text(
                recipe_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📖 Ver otras recetas", callback_data='view_recipes')],
                    [InlineKeyboardButton("🏠 Menú principal", callback_data='main_menu')]
                ]),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error cargando detalles de receta: {str(e)}", exc_info=True)
            try:
                query.edit_message_text(
                    "Error al cargar los detalles de la receta. Por favor, intenta de nuevo.",
                    reply_markup=get_main_menu_keyboard()
                )
            except:
                # Si hay problemas con la edición, intentar con un mensaje nuevo
                context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="Error al cargar los detalles de la receta. Por favor, intenta de nuevo.",
                    reply_markup=get_main_menu_keyboard()
                )
        
        return MAIN_MENU
    
    # Manejar botones de alimentos sugeridos
    elif data.startswith('food_'):
        food_name = data[5:]
        process_food_item(query, food_name)
        return MAIN_MENU
    
    elif data == 'request_recipe':
        # Solicitar receta a partir de ingredientes
        query.edit_message_text(
            "🔍 *Solicitar receta*\n\n"
            "Por favor, escribe los ingredientes que tienes disponibles, separados por comas.\n"
            "Ejemplo: *arroz, huevo, brócoli*\n\n"
            "Buscaré una receta que puedas preparar con estos ingredientes.",
            parse_mode=ParseMode.MARKDOWN
        )
        return REQUEST_RECIPE
    
    # Valor por defecto
    return MAIN_MENU

def process_food_item(query_or_update, food_name):
    """
    Procesa un alimento y muestra su información nutricional.
    Funciona tanto con CallbackQuery como con Update.
    """
    is_query = hasattr(query_or_update, 'edit_message_text')
    
    if is_query:
        user_id = query_or_update.from_user.id
        send_func = query_or_update.edit_message_text
    else:
        user_id = query_or_update.effective_user.id
        send_func = query_or_update.message.reply_text
        # Mensaje de espera
        query_or_update.message.reply_text("Analizando el alimento... ⏳")
    
    # Consultar a API NLP para determinar si es un alimento y obtener información
    nutrition_info = food_processor.get_nutrition_info_sync(food_name, user_id)
    
    # Si no es un alimento, mostrar mensaje de la API NLP (generado por Gemini)
    if not nutrition_info.get("is_food", False):
        generated_text = nutrition_info.get("generated_text", "")
        if not generated_text:
            generated_text = f"Lo sentimos, '{food_name}' no parece ser un alimento. Puedo proporcionarte información sobre alimentos y nutrición. Prueba con alimentos como: pollo, arroz, manzana, leche, etc."
        
        send_func(
            generated_text,
            reply_markup=get_main_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Si no hay información nutricional básica, mostrar mensaje
    if nutrition_info.get("calories") is None and nutrition_info.get("protein") is None:
        send_func(
            f"No he podido encontrar información nutricional detallada para *{food_name}*. " +
            (nutrition_info.get("generated_text", "") or "Intenta con otro alimento."),
            reply_markup=get_action_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Guardar en el historial
    user_info = get_user_data(user_id)
    user_info["history"].append(nutrition_info)
    
    # Actualizar calorías diarias si hay información
    if nutrition_info.get("calories") is not None:
        user_info["daily_calories"] += nutrition_info.get("calories", 0)
    
    # Usar el texto generado por Gemini si está disponible
    if "generated_text" in nutrition_info and nutrition_info["generated_text"]:
        # Construir mensaje con la información generada por Gemini
        message = f"🥗 *{nutrition_info['name']}*\n\n"
        message += nutrition_info["generated_text"] + "\n\n"
        
        # Añadir información nutricional resumida
        message += "*Información nutricional por 100g:*\n"
        if nutrition_info.get("calories") is not None:
            message += f"• Calorías: {nutrition_info['calories']:.1f} kcal\n"
        if nutrition_info.get("protein") is not None:
            message += f"• Proteínas: {nutrition_info['protein']:.1f} g\n"
        if nutrition_info.get("carbs") is not None:
            message += f"• Carbohidratos: {nutrition_info['carbs']:.1f} g\n"
        if nutrition_info.get("fat") is not None:
            message += f"• Grasas: {nutrition_info['fat']:.1f} g\n"
        
        # Mostrar calorías acumuladas
        message += f"\n📊 Calorías acumuladas hoy: {user_info['daily_calories']:.1f} kcal"
        
        send_func(
            message,
            reply_markup=get_action_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Construir mensaje simplificado (para caso de fallback)
        message = f"🥗 *{nutrition_info['name']}*\n\n"
        
        if nutrition_info.get("calories") is not None:
            message += f"• Calorías: {nutrition_info['calories']:.1f} kcal\n"
        else:
            message += "• Calorías: No disponible\n"
        
        if nutrition_info.get("protein") is not None:
            message += f"• Proteínas: {nutrition_info['protein']:.1f} g\n"
        if nutrition_info.get("carbs") is not None:
            message += f"• Carbohidratos: {nutrition_info['carbs']:.1f} g\n"
        if nutrition_info.get("fat") is not None:
            message += f"• Grasas: {nutrition_info['fat']:.1f} g\n"
            
        # Mostrar calorías acumuladas
        message += f"\n📊 Calorías acumuladas hoy: {user_info['daily_calories']:.1f} kcal"
        
        send_func(
            message,
            reply_markup=get_action_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )

def handle_text(update: Update, context: CallbackContext) -> int:
    """Maneja los mensajes de texto para detectar alimentos."""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Verificar si hay comas para determinar si es una lista de alimentos
    if ',' in text:
        # Mensaje de espera
        wait_message = update.message.reply_text("Analizando los alimentos... ⏳")
        
        # Separar alimentos y procesar individualmente
        food_items = [item.strip() for item in text.split(',') if item.strip()]
        
        if not food_items:
            update.message.reply_text(
                "No he podido identificar alimentos en tu mensaje. Por favor, sé más específico.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        
        try:
            # Verificar cada alimento utilizando la API NLP
            valid_foods = []
            for food in food_items:
                if food_processor.is_food_related(food, user_id):
                    valid_foods.append(food)
            
            # Si no se identificaron alimentos válidos
            if not valid_foods:
                # Obtener una respuesta generada por Gemini para un caso de error
                nlp_result = food_processor.check_food_with_nlp_api(text, user_id)
                
                context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=wait_message.message_id
                )
                
                update.message.reply_text(
                    nlp_result.get("generated_text", 
                    "No he podido identificar alimentos válidos en tu mensaje. Por favor, intenta de nuevo con alimentos como: pollo, arroz, manzana, etc."),
                    reply_markup=get_main_menu_keyboard(),
                    parse_mode=ParseMode.MARKDOWN
                )
                return MAIN_MENU
            
            # Procesar cada alimento válido
            all_foods_info = []
            total_calories = 0
            
            for food in valid_foods:
                # Obtener información nutricional
                nutrition_info = food_processor.get_nutrition_info_sync(food, user_id)
                all_foods_info.append(nutrition_info)
                
                # Acumular calorías
                if nutrition_info.get("calories") is not None:
                    total_calories += nutrition_info.get("calories", 0)
                
                # Guardar en el historial
                user_info = get_user_data(user_id)
                user_info["history"].append(nutrition_info)
                
                # Actualizar calorías diarias
                if nutrition_info.get("calories") is not None:
                    user_info["daily_calories"] += nutrition_info.get("calories", 0)
            
            # Construir mensaje con todos los alimentos
            message = "🍽️ *Información nutricional del plato:*\n\n"
            
            for info in all_foods_info:
                message += f"🥗 *{info['name']}*\n"
                
                if info.get("calories") is not None:
                    message += f"• Calorías: {info['calories']:.1f} kcal\n"
                if info.get("protein") is not None:
                    message += f"• Proteínas: {info['protein']:.1f} g\n"
                if info.get("carbs") is not None:
                    message += f"• Carbohidratos: {info['carbs']:.1f} g\n"
                if info.get("fat") is not None:
                    message += f"• Grasas: {info['fat']:.1f} g\n"
                
                message += "\n"
            
            message += f"*Total de calorías del plato: {total_calories:.1f} kcal*\n\n"
            
            # Generar recomendaciones con Gemini
            try:
                foods_str = ", ".join(valid_foods)
                prompt = f"""
                Genera una breve recomendación nutricional en español para un plato que contiene estos alimentos: {foods_str}
                
                La recomendación debe:
                1. Ser corta (máximo 3 puntos)
                2. Incluir consejos prácticos
                3. Estar totalmente en español
                
                Responde solo con los puntos, sin introducción ni conclusión. Cada punto debe comenzar con un emoji relevante.
                """
                
                recommendations = food_processor.model.generate_content(prompt)
                message += "💡 *Recomendaciones:*\n" + recommendations.text.strip() + "\n"
            except Exception as e:
                logger.error(f"Error generando recomendaciones: {str(e)}")
                # Recomendaciones predeterminadas
                message += "💡 *Recomendaciones:*\n"
                message += "• Procura mantener una alimentación variada\n"
                message += "• No olvides incluir frutas y verduras\n"
                message += "• Bebe suficiente agua durante el día\n"
            
            # Mostrar calorías acumuladas
            user_info = get_user_data(user_id)
            message += f"\n📊 Calorías acumuladas hoy: {user_info['daily_calories']:.1f} kcal"
            
            # Eliminar mensaje de espera
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=wait_message.message_id
            )
            
            update.message.reply_text(
                message,
                reply_markup=get_action_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            logger.error(f"Error procesando alimentos: {str(e)}", exc_info=True)
            # Intenta eliminar mensaje de espera
            try:
                context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=wait_message.message_id
                )
            except:
                pass
                
            update.message.reply_text(
                "Lo siento, tuve un problema procesando los alimentos. Por favor, intenta de nuevo.",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        # Consultar a la API NLP para validar si es alimento
        nlp_result = food_processor.check_food_with_nlp_api(text, user_id)
        
        # Si no es un alimento según la API, mostrar el mensaje generado
        if not nlp_result.get("is_food", False):
            update.message.reply_text(
                nlp_result.get("generated_text", 
                "Lo sentimos, tu mensaje no parece estar relacionado con alimentos. Soy un asistente nutricional que puede proporcionarte información sobre alimentos y recetas. Prueba preguntándome sobre alimentos como: pollo, arroz, manzana, etc."),
                reply_markup=get_main_menu_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
            return MAIN_MENU
        
        # Procesar como un solo alimento si es válido
        process_food_item(update, text)
    
    return MAIN_MENU

def handle_photo(update: Update, context: CallbackContext) -> int:
    """Maneja las fotos enviadas por el usuario."""
    # Mensaje de espera
    try:
        wait_message = retry_handler.execute_with_retry(
            update.message.reply_text,
            "Analizando la imagen... ⏳"
        )
    except Exception as e:
        logger.error(f"Error enviando mensaje de espera: {str(e)}")
        # Continuar aunque no se pueda enviar el mensaje de espera
    
    try:
        # Obtener la foto de mayor resolución
        photo = update.message.photo[-1]
        logger.info(f"Foto recibida. File ID: {photo.file_id}, Dimensiones: {photo.width}x{photo.height}")
        
        # Descargar la foto como bytes
        try:
            photo_file = retry_handler.execute_with_retry(photo.get_file)
        except Exception as e:
            logger.error(f"Error obteniendo archivo de foto: {str(e)}")
            update.message.reply_text(
                "Error descargando la imagen. Verifica tu conexión a Internet y vuelve a intentarlo.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
        
        # Obtener directamente los bytes de la imagen
        import io
        import requests
        
        # Verificar si estamos en un entorno local o en la nube
        file_url = photo_file.file_path
        photo_bytes = None
        
        try:
            if not file_url.startswith('http'):
                # Si estamos en local, descargar usando el método estándar
                photo_bytes = retry_handler.execute_with_retry(photo_file.download_as_bytearray)
            else:
                # Si es una URL, usar requests para descargar
                logger.info(f"Descargando desde URL: {file_url}")
                for attempt in range(3):  # Intentar hasta 3 veces
                    try:
                        response = requests.get(file_url, timeout=10)
                        if response.status_code == 200:
                            photo_bytes = response.content
                            break
                    except requests.RequestException as e:
                        logger.warning(f"Error descargando imagen (intento {attempt+1}/3): {str(e)}")
                        time.sleep(2 ** attempt)  # Backoff exponencial
        except Exception as e:
            logger.error(f"Error descargando imagen: {str(e)}")
            
        if photo_bytes is None:
            update.message.reply_text(
                "No se pudo descargar la imagen. Por favor, intenta de nuevo o usa una imagen diferente.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
            
        logger.info(f"Imagen descargada: {len(photo_bytes)} bytes")
        
        # Detectar alimentos en la imagen usando Clarifai
        detection_result = food_detector.detect_food_sync(photo_bytes)
        
        logger.info(f"Resultado de Clarifai: {detection_result}")
        
        if not detection_result["success"] or not detection_result["detected_foods"]:
            if "error" in detection_result:
                logger.error(f"Error de Clarifai: {detection_result['error']}")
                retry_handler.execute_with_retry(
                    update.message.reply_text,
                    f"Error al analizar la imagen: {detection_result['error']}\n"
                    "Por favor, intenta con otra foto.",
                    reply_markup=get_action_keyboard()
                )
            else:
                retry_handler.execute_with_retry(
                    update.message.reply_text,
                    "No he podido identificar alimentos en esta imagen. Por favor, intenta con otra foto más clara.",
                    reply_markup=get_action_keyboard()
                )
            return MAIN_MENU
        
        # Obtener los alimentos detectados (en inglés)
        foods_en = detection_result["detected_foods"]
        
        # Verificar cada alimento detectado
        valid_foods_en = []
        for food in foods_en:
            # Traducir al español para verificar si es un alimento
            try:
                food_es = food_processor.translate_text_sync(food, source_lang="en", target_lang="es")
                if food_processor.is_food_related(food_es):
                    valid_foods_en.append(food)
            except Exception as e:
                logger.error(f"Error verificando alimento {food}: {str(e)}")
                # Incluir de todas formas si hay un error en la verificación
                valid_foods_en.append(food)
        
        # Si no quedan alimentos válidos después del filtrado
        if not valid_foods_en:
            retry_handler.execute_with_retry(
                update.message.reply_text,
                "La imagen no contiene alimentos válidos. Por favor, intenta con otra foto.",
                reply_markup=get_action_keyboard()
            )
            return MAIN_MENU
        
        # Traducir al español para mostrarlos al usuario
        foods_es = []
        for food in valid_foods_en:
            try:
                # Traducir del inglés al español
                food_es = food_processor.translate_text_sync(food, source_lang="en", target_lang="es")
                foods_es.append(food_es)
            except Exception as e:
                logger.error(f"Error traduciendo alimento {food}: {str(e)}")
                foods_es.append(food)  # Usar el original si falla la traducción
        
        # Mensaje con los alimentos detectados
        foods_message = "He detectado los siguientes alimentos:\n\n"
        for i, food_es in enumerate(foods_es):
            food_en = valid_foods_en[i]  # Alimento original en inglés
            confidence = detection_result["confidence_scores"].get(food_en, 0) * 100
            foods_message += f"• {food_es} (confianza: {confidence:.1f}%)\n"
        
        retry_handler.execute_with_retry(
            update.message.reply_text,
            foods_message
        )
        
        try:
            # Obtener información nutricional de los alimentos (usando nombres en inglés)
            all_foods_info = food_processor.integrate_vision_results_sync(valid_foods_en)
            
            # Verificar si hay información nutricional
            if not all_foods_info:
                logger.warning("No se obtuvo información nutricional de los alimentos detectados")
                retry_handler.execute_with_retry(
                    update.message.reply_text,
                    "No he podido obtener información nutricional detallada. Esto puede deberse a una limitación en nuestra base de datos.",
                    reply_markup=get_action_keyboard()
                )
                return MAIN_MENU
            
            # Construir mensaje con información nutricional en español
            nutrition_message = "📊 *Información nutricional:*\n\n"
            total_calories = 0
            
            # Usar nombres en español para el mensaje, pero mantener info nutricional
            for i, info in enumerate(all_foods_info):
                # Verificar si hay información válida
                if not info or "name" not in info:
                    continue
                
                # Reemplazar nombre en inglés por nombre en español
                if i < len(foods_es):
                    info_with_spanish_name = info.copy()
                    info_with_spanish_name["name"] = foods_es[i]
                    
                    nutrition_message += f"🍽️ *{info_with_spanish_name['name']}*\n"
                    
                    if info.get("calories") is not None:
                        nutrition_message += f"• Calorías: {info['calories']:.1f} kcal\n"
                        total_calories += info['calories']
                    if info.get("protein") is not None:
                        nutrition_message += f"• Proteínas: {info['protein']:.1f} g\n"
                    if info.get("carbs") is not None:
                        nutrition_message += f"• Carbohidratos: {info['carbs']:.1f} g\n"
                    if info.get("fat") is not None:
                        nutrition_message += f"• Grasas: {info['fat']:.1f} g\n"
                    
                    nutrition_message += "\n"
                    
                    # Guardar en el historial solo si hay información nutricional válida
                    if info.get("calories") is not None:
                        user_info = get_user_data(update.effective_user.id)
                        user_info["history"].append(info_with_spanish_name)
            
            # Actualizar calorías diarias
            user_info = get_user_data(update.effective_user.id)
            user_info["daily_calories"] += total_calories
            
            nutrition_message += f"*Total de calorías estimadas: {total_calories:.1f} kcal*\n\n"
            
            # Agregar recomendaciones generales
            nutrition_message += "💡 *Recomendaciones:*\n"
            nutrition_message += "• Mantén una dieta equilibrada con variedad de alimentos\n"
            nutrition_message += "• No olvides incluir frutas y verduras en tu alimentación diaria\n"
            nutrition_message += "• Bebe suficiente agua durante el día\n"
            
            # Mostrar calorías acumuladas
            nutrition_message += f"\n📊 Calorías acumuladas hoy: {user_info['daily_calories']:.1f} kcal"
            
            retry_handler.execute_with_retry(
                update.message.reply_text,
                nutrition_message,
                reply_markup=get_action_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error procesando información nutricional: {str(e)}", exc_info=True)
            retry_handler.execute_with_retry(
                update.message.reply_text,
                "He detectado los alimentos, pero ocurrió un error al procesar la información nutricional. Por favor, intenta de nuevo.",
                reply_markup=get_action_keyboard()
            )
        
    except Exception as e:
        logger.error(f"Error procesando imagen: {str(e)}", exc_info=True)
        retry_handler.execute_with_retry(
            update.message.reply_text,
            "Lo siento, ha ocurrido un error al procesar la imagen. Por favor, intenta de nuevo.",
            reply_markup=get_main_menu_keyboard()
        )
    
    return MAIN_MENU

def fallback_handler(update: Update, context: CallbackContext) -> int:
    """Maneja los eventos no reconocidos."""
    update.message.reply_text(
        "No he entendido ese comando. ¿Qué te gustaría hacer?",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

def error_handler(update: Update, context: CallbackContext) -> None:
    """Maneja los errores."""
    error = context.error
    logger.error(f"Error: {error}", exc_info=True)
    
    # Verificar tipo de error
    if hasattr(error, "message") and "Query is too old" in str(error):
        # Error de consulta antigua, no necesita notificación al usuario
        logger.warning("Ignorando error de consulta antigua")
        return
    
    try:
        # Determinar qué tipo de actualización es y responder apropiadamente
        if update and update.effective_message:
            # Errores de red/conexión
            if "Connection" in str(error) or "HTTPSConnectionPool" in str(error):
                update.effective_message.reply_text(
                    "Estoy experimentando problemas de conexión. Por favor, intenta de nuevo en unos momentos."
                )
            else:
                # Otros errores
                update.effective_message.reply_text(
                    "Lo siento, ha ocurrido un error inesperado. Por favor, intenta de nuevo."
                )
        elif update and update.callback_query:
            # Para errores en callbacks que no han expirado
            if "Query is too old" not in str(error):
                context.bot.send_message(
                    chat_id=update.callback_query.message.chat_id,
                    text="Lo siento, ha ocurrido un error procesando tu solicitud. Por favor, intenta de nuevo."
                )
    except Exception as e:
        logger.error(f"Error durante el manejo de errores: {str(e)}")

# Agregar manejadores para los nuevos estados
def recipe_conversation_handler(update: Update, context: CallbackContext) -> int:
    """Maneja la conversación para crear recetas."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Verificar si hay un contexto de receta activo
    if user_id not in recipe_context:
        update.message.reply_text(
            "Parece que no hay una creación de receta activa. Por favor, inicia de nuevo.",
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # Obtener el paso actual
    step = recipe_context[user_id]["step"]
    
    if step == "name":
        # Guardar el nombre y solicitar descripción
        recipe_context[user_id]["name"] = text
        recipe_context[user_id]["step"] = "description"
        
        update.message.reply_text(
            f"🧪 *Nombre de la receta:* {text}\n\n"
            "Ahora, por favor, escribe una breve descripción de la receta:",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return CREATE_RECIPE
        
    elif step == "description":
        # Guardar la descripción y continuar con ingredientes
        recipe_context[user_id]["description"] = text
        
        # Mostrar resumen y opciones
        recipe = recipe_context[user_id]
        
        summary = f"🧪 *Receta: {recipe['name']}*\n\n"
        summary += f"📝 *Descripción:* {recipe['description']}\n\n"
        summary += "Ahora puedes agregar ingredientes a tu receta."
        
        update.message.reply_text(
            summary,
            reply_markup=get_recipe_menu_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return CREATE_RECIPE
        
    elif step == "ingredients":
        # Procesar ingrediente ingresado
        if "-" not in text:
            update.message.reply_text(
                "⚠️ Formato incorrecto. Por favor, ingresa el ingrediente en formato:\n"
                "*Ingrediente - cantidad*\n\n"
                "Ejemplo: *Harina - 2 tazas*",
                parse_mode=ParseMode.MARKDOWN
            )
            return ADD_INGREDIENTS
        
        # Separar ingrediente y cantidad
        parts = text.split("-", 1)
        ingredient_name = parts[0].strip()
        quantity = parts[1].strip()
        
        # Agregar a la lista de ingredientes
        if "ingredients" not in recipe_context[user_id]:
            recipe_context[user_id]["ingredients"] = []
        
        recipe_context[user_id]["ingredients"].append({
            "name": ingredient_name,
            "quantity": quantity
        })
        
        # Mostrar mensaje de confirmación
        ingredients_count = len(recipe_context[user_id]["ingredients"])
        
        update.message.reply_text(
            f"✅ Ingrediente agregado: *{ingredient_name} - {quantity}*\n\n"
            f"Total de ingredientes: {ingredients_count}\n\n"
            "Puedes seguir agregando más ingredientes o presionar 'Terminar' cuando hayas acabado.",
            reply_markup=get_ingredients_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ADD_INGREDIENTS
    
    # Si llegamos aquí, algo salió mal, volver al menú principal
    return MAIN_MENU

def save_recipe_to_json(recipe_data, user_id=None):
    """
    Guarda una receta en formato JSON acumulándola con las existentes.
    
    Args:
        recipe_data: Diccionario con datos de la receta
        user_id: ID del usuario que guarda la receta (opcional)
        
    Returns:
        str: Ruta del archivo guardado
    """
    # Crear directorio si no existe
    memory_dir = os.path.join(DATA_PATH, "processed")
    os.makedirs(memory_dir, exist_ok=True)
    
    # Ruta del archivo JSON de memoria de recetas
    json_path = os.path.join(memory_dir, "memory_recetas.json")
    
    # Cargar recetas existentes o crear nueva lista
    existing_recipes = []
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    existing_recipes = existing_data
        except (json.JSONDecodeError, FileNotFoundError):
            existing_recipes = []
    
    # Generar ID único para la receta si no tiene uno
    if "id" not in recipe_data:
        recipe_data["id"] = str(uuid.uuid4())
    
    # Añadir timestamp si no tiene
    if "created_at" not in recipe_data:
        recipe_data["created_at"] = datetime.now().isoformat()
    
    # Añadir user_id si se proporciona
    if user_id is not None:
        recipe_data["user_id"] = str(user_id)
    
    # Añadir la nueva receta
    existing_recipes.append(recipe_data)
    
    # Guardar todas las recetas
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(existing_recipes, f, ensure_ascii=False, indent=2)
    
    return json_path

def handle_recipe_request(update: Update, context: CallbackContext) -> int:
    """Maneja la solicitud de receta basada en ingredientes."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Registro inicial para depuración
    logger.info(f"RECIPE_REQUEST: Solicitud de receta con texto: '{text}'")
    
    # Tratar de separar los ingredientes por comas, si hay
    if ',' in text:
        ingredients = [item.strip() for item in text.split(',') if item.strip()]
        logger.info(f"RECIPE_REQUEST: Ingredientes extraídos por comas: {ingredients}")
    else:
        # Si no hay comas, consultar a la API NLP para extraer alimentos
        logger.info(f"RECIPE_REQUEST: No hay comas, usando API NLP para extraer alimentos")
        nlp_result = food_processor.check_food_with_nlp_api(text, user_id)
        
        # Extraer entidades de alimentos de la respuesta
        if nlp_result.get("is_food", False):
            entities = nlp_result.get("entities", {})
            logger.info(f"RECIPE_REQUEST: Entidades detectadas por API NLP: {entities}")
            
            # Convertir entidades a lista de ingredientes
            if isinstance(entities, dict):
                ingredients = list(entities.values())
            elif isinstance(entities, list):
                ingredients = entities
            else:
                # Intentar fallback con extract_food_items_sync
                logger.info(f"RECIPE_REQUEST: Formato de entidades desconocido, usando extract_food_items_sync")
                ingredients = food_processor.extract_food_items_sync(text, user_id)
            
            logger.info(f"RECIPE_REQUEST: Ingredientes extraídos del texto: {ingredients}")
        else:
            # Si no es sobre alimentos, mostrar mensaje generado por la API
            logger.info(f"RECIPE_REQUEST: API NLP indica que no hay alimentos en: '{text}'")
            update.message.reply_text(
                nlp_result.get("generated_text", 
                "No he podido identificar ingredientes en tu mensaje. Por favor, especifica mejor los ingredientes separados por comas, como: arroz, huevo, brócoli."),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
    
    # Si no hay ingredientes, informar al usuario
    if not ingredients:
        logger.info(f"RECIPE_REQUEST: No se encontraron ingredientes en: '{text}'")
        update.message.reply_text(
            "No he podido identificar ingredientes en tu mensaje. Por favor, especifica mejor los ingredientes separados por comas, como:\n"
            "*arroz, huevo, brócoli*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # VERIFICACIÓN ADICIONAL: Validar que todos los ingredientes son alimentos antes de continuar
    valid_ingredients = []
    invalid_ingredients = []
    
    logger.info(f"RECIPE_REQUEST: Validando {len(ingredients)} ingredientes extraídos")
    for ingredient in ingredients:
        # Verificar si realmente es un alimento usando la función is_food_related
        logger.info(f"RECIPE_REQUEST: Verificando si '{ingredient}' es un alimento")
        is_food = food_processor.is_food_related(ingredient, user_id)
        logger.info(f"RECIPE_REQUEST: Resultado para '{ingredient}': {'ES alimento' if is_food else 'NO ES alimento'}")
        
        if is_food:
            valid_ingredients.append(ingredient)
            logger.info(f"RECIPE_REQUEST: '{ingredient}' añadido a ingredientes válidos")
        else:
            invalid_ingredients.append(ingredient)
            logger.info(f"RECIPE_REQUEST: '{ingredient}' añadido a ingredientes inválidos")
    
    # VERIFICACIÓN FINAL CON GEMINI PARA CASOS DUDOSOS
    # Si tenemos mezcla de ingredientes válidos e inválidos, hacer una verificación adicional
    if valid_ingredients and invalid_ingredients:
        logger.info(f"RECIPE_REQUEST: Se encontraron ingredientes mixtos. Verificando con Gemini")
        try:
            # Verificar cada ingrediente inválido una última vez
            still_invalid = []
            for ingredient in invalid_ingredients:
                prompt = f"""
                ¿La palabra "{ingredient}" se refiere a un alimento que los humanos consumen?
                Responde SOLO con SI o NO.
                """
                
                response = food_processor.model.generate_content(prompt)
                answer = response.text.strip().upper()
                logger.info(f"RECIPE_REQUEST: Verificación final con Gemini para '{ingredient}': '{answer}'")
                
                if "SI" in answer or "SÍ" in answer:
                    logger.info(f"RECIPE_REQUEST: Gemini confirmó que '{ingredient}' ES alimento")
                    valid_ingredients.append(ingredient)
                else:
                    logger.info(f"RECIPE_REQUEST: Gemini confirmó que '{ingredient}' NO es alimento")
                    still_invalid.append(ingredient)
            
            # Actualizar lista de ingredientes inválidos
            invalid_ingredients = still_invalid
        except Exception as e:
            logger.error(f"RECIPE_REQUEST: Error en verificación final: {str(e)}")
            # Mantener listas originales en caso de error
    
    # Si hay ingredientes inválidos, mostrar mensaje informativo
    if invalid_ingredients:
        invalid_text = ", ".join(invalid_ingredients)
        logger.info(f"RECIPE_REQUEST: Rechazando ingredientes inválidos: {invalid_ingredients}")
        update.message.reply_text(
            f"Lo siento, no puedo crear una receta con los siguientes ingredientes que no son alimentos: *{invalid_text}*\n\n"
            "Por favor, intenta nuevamente sólo con alimentos.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # Si no quedan ingredientes válidos después del filtrado
    if not valid_ingredients:
        logger.info(f"RECIPE_REQUEST: No quedaron ingredientes válidos después del filtrado")
        update.message.reply_text(
            "No he podido identificar alimentos válidos en tu mensaje. Por favor, especifica ingredientes como:\n"
            "*arroz, huevo, brócoli*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
        return MAIN_MENU
    
    # Mensaje de espera
    logger.info(f"RECIPE_REQUEST: Procesando receta con ingredientes válidos: {valid_ingredients}")
    wait_message = update.message.reply_text("Buscando recetas... ⏳")
    
    try:
        # Traducir ingredientes al inglés para buscar en dataset
        english_ingredients = []
        for ingredient in valid_ingredients:
            try:
                translated = food_processor.translate_text_sync(ingredient, "es", "en")
                english_ingredients.append(translated)
                logger.info(f"RECIPE_REQUEST: Traducido '{ingredient}' a '{translated}'")
            except Exception as e:
                logger.error(f"RECIPE_REQUEST: Error traduciendo ingrediente {ingredient}: {str(e)}")
                english_ingredients.append(ingredient)  # Usar original si falla
        
        logger.info(f"RECIPE_REQUEST: Ingredientes traducidos: {english_ingredients}")
        
        # Buscar receta en dataset FoodCom
        recipe_found = False
        recipe_data = None
        
        # Buscar en el dataset
        try:
            import pandas as pd
            import random
            
            # Ruta al dataset
            dataset_path = os.path.join(DATA_PATH, "processed", "foodcom_recipes.csv")
            
            if os.path.exists(dataset_path):
                # Cargar una muestra del dataset para búsqueda
                recipes_df = pd.read_csv(dataset_path, nrows=200)
                
                # Buscar recetas que contengan al menos la mitad de los ingredientes
                for idx, row in recipes_df.iterrows():
                    ingredients_list = str(row['ingredients']).lower()
                    
                    # Verificar coincidencias
                    matches = sum(1 for ing in english_ingredients if ing.lower() in ingredients_list)
                    if matches >= len(english_ingredients) / 2:
                        recipe_found = True
                        
                        # Extraer datos de la receta
                        recipe_steps = eval(row['steps']) if isinstance(row['steps'], str) else []
                        recipe_ingredients = eval(row['ingredients']) if isinstance(row['ingredients'], str) else []
                        
                        # Traducir de inglés a español
                        spanish_name = food_processor.translate_text_sync(row['name'], source_lang="en", target_lang="es")
                        spanish_description = food_processor.translate_text_sync(row['description'], source_lang="en", target_lang="es") if isinstance(row['description'], str) else "Sin descripción"
                        
                        spanish_ingredients = []
                        for ing in recipe_ingredients:
                            spanish_ing = food_processor.translate_text_sync(ing, source_lang="en", target_lang="es")
                            spanish_ingredients.append(spanish_ing)
                        
                        spanish_steps = []
                        for step in recipe_steps:
                            spanish_step = food_processor.translate_text_sync(step, source_lang="en", target_lang="es")
                            spanish_steps.append(spanish_step)
                        
                        recipe_data = {
                            "name": spanish_name,
                            "ingredients": spanish_ingredients,
                            "steps": spanish_steps,
                            "description": spanish_description,
                            "source": "foodcom",
                            "original_query": text,
                            "original_ingredients": valid_ingredients,
                            "translated_ingredients": english_ingredients
                        }
                        break
        except Exception as e:
            logger.error(f"Error buscando receta en dataset: {str(e)}")
            # Continuar con generación por Gemini
        
        # Si no encontramos una receta, generar una con Gemini
        if not recipe_data:
            try:
                # Construir prompt para Gemini para generar receta en español
                ingredients_str = ", ".join(valid_ingredients)
                prompt = f"""
                TAREA: Genera una receta en español usando estos ingredientes: {ingredients_str}.
                
                INSTRUCCIONES:
                - La receta debe ser COMPLETAMENTE EN ESPAÑOL
                - La receta debe ser sencilla y fácil de preparar
                - Incluye un nombre creativo y atractivo para la receta
                - Proporciona una breve descripción que incluya beneficios nutricionales
                - Lista todos los ingredientes necesarios con cantidades
                - Proporciona instrucciones paso a paso para la preparación
                - Incluye algún consejo de preparación o valor nutricional al final
                - Responde SOLAMENTE en formato JSON con esta estructura exacta:
                {{
                  "name": "Nombre de la receta",
                  "description": "Breve descripción",
                  "ingredients": ["Ingrediente 1 con cantidad", "Ingrediente 2 con cantidad", "..."],
                  "steps": ["Paso 1: ...", "Paso 2: ...", "..."],
                  "tip": "Consejo nutricional o de preparación"
                }}
                - No incluyas comentarios ni texto adicional, solo el JSON
                - TODA LA INFORMACIÓN DEBE ESTAR EN ESPAÑOL
                
                RECETA:
                """
                
                # Generar receta con Gemini
                recipe_json = food_processor.model.generate_content(prompt)
                recipe_text = recipe_json.text.strip()
                
                # Parsear el JSON de la respuesta
                import re
                import json
                
                # Extraer solo el JSON si hay texto adicional
                json_match = re.search(r'({.*})', recipe_text, re.DOTALL)
                if json_match:
                    recipe_text = json_match.group(1)
                
                recipe_data = json.loads(recipe_text)
                
                # Añadir metadatos
                recipe_data["source"] = "gemini"
                recipe_data["original_query"] = text
                recipe_data["original_ingredients"] = valid_ingredients
                
            except Exception as e:
                logger.error(f"Error generando receta con Gemini: {str(e)}", exc_info=True)
                
                # Obtener un mensaje personalizado de Gemini para el error
                try:
                    error_prompt = f"""
                    Genera un mensaje amigable y en español explicando que no se pudo crear una receta con estos ingredientes: {', '.join(valid_ingredients)}.
                    Incluye una disculpa, una posible razón y una sugerencia para el usuario.
                    El mensaje debe ser breve (máximo 3 frases) y estar completamente en español.
                    """
                    error_response = food_processor.model.generate_content(error_prompt)
                    error_message = error_response.text.strip()
                    
                    # Eliminar mensaje de espera
                    context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=wait_message.message_id
                    )
                    
                    update.message.reply_text(
                        error_message,
                        reply_markup=get_main_menu_keyboard()
                    )
                    return MAIN_MENU
                    
                except:
                    # Receta fallback si falla Gemini por completo
                    recipe_data = {
                        "name": f"Receta con {', '.join(valid_ingredients[:3])}",
                        "description": f"Receta sencilla usando {', '.join(valid_ingredients)}",
                        "ingredients": [f"{ing} - cantidad al gusto" for ing in valid_ingredients],
                        "steps": [
                            "Paso 1: Preparar todos los ingredientes.",
                            f"Paso 2: Cocinar {valid_ingredients[0]} según sus instrucciones habituales.",
                            "Paso 3: Añadir el resto de ingredientes y mezclar bien.",
                            "Paso 4: Cocinar a fuego medio hasta que esté listo.",
                            "Paso 5: Servir caliente."
                        ],
                        "source": "fallback",
                        "original_query": text,
                        "original_ingredients": valid_ingredients
                    }
        
        # Guardar la receta en memory_recetas.json
        json_path = save_recipe_to_json(recipe_data, user_id=user_id)
        
        # Crear mensaje de respuesta
        response = f"🧪 *{recipe_data['name']}*\n\n"
        response += f"📝 *Descripción:* {recipe_data['description']}\n\n"
        response += "🥗 *Ingredientes:*\n"
        
        for i, ingredient in enumerate(recipe_data['ingredients'], 1):
            response += f"{i}. {ingredient}\n"
        
        response += "\n📋 *Instrucciones:*\n"
        
        for i, step in enumerate(recipe_data['steps'], 1):
            response += f"{i}. {step}\n"
        
        # Añadir consejo si existe
        if "tip" in recipe_data and recipe_data["tip"]:
            response += f"\n💡 *Consejo:* {recipe_data['tip']}\n"
        
        # Eliminar mensaje de espera y mostrar resultado
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=wait_message.message_id
            )
        except Exception as e:
            logger.error(f"Error eliminando mensaje de espera: {str(e)}")
        
        update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_action_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error general en receta: {str(e)}", exc_info=True)
        try:
            context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=wait_message.message_id
            )
        except:
            pass
            
        # Intentar generar un mensaje de error personalizado
        try:
            error_prompt = "Genera un mensaje corto y amable en español para disculparse por un error al generar una receta. Máximo 2 frases."
            error_response = food_processor.model.generate_content(error_prompt)
            error_message = error_response.text.strip()
            
            update.message.reply_text(
                error_message,
                reply_markup=get_main_menu_keyboard()
            )
        except:
            # Mensaje de error fallback
            update.message.reply_text(
                "Lo siento, tuve un problema generando la receta. Por favor, intenta de nuevo.",
                reply_markup=get_main_menu_keyboard()
            )
    
    return MAIN_MENU

def load_saved_recipes(limit=20, user_id=None):
    """
    Carga las recetas guardadas del archivo memory_recetas.json.
    
    Args:
        limit: Número máximo de recetas a devolver (las más recientes)
        user_id: ID del usuario para filtrar recetas (opcional)
        
    Returns:
        List[Dict]: Lista de recetas guardadas
    """
    # Ruta del archivo JSON de memoria de recetas
    memory_dir = os.path.join(DATA_PATH, "processed")
    json_path = os.path.join(memory_dir, "memory_recetas.json")
    
    # Verificar si existe el archivo
    if not os.path.exists(json_path):
        logger.warning(f"Archivo de recetas {json_path} no encontrado")
        return []
    
    try:
        # Cargar recetas
        with open(json_path, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
        
        if not isinstance(recipes, list):
            logger.warning(f"Formato incorrecto en {json_path}, se esperaba una lista")
            return []
        
        # Filtrar por user_id si se proporciona
        if user_id is not None:
            user_id_str = str(user_id)
            # Incluir recetas sin user_id (globales) y las del usuario específico
            recipes = [r for r in recipes if "user_id" not in r or r.get("user_id") == user_id_str]
            logger.info(f"Filtrado: {len(recipes)} recetas para usuario {user_id}")
        
        # Ordenar por fecha de creación (más recientes primero)
        try:
            recipes.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        except Exception as e:
            logger.warning(f"No se pudieron ordenar las recetas por fecha: {str(e)}")
        
        # Limitamos la cantidad
        return recipes[:limit]
    
    except json.JSONDecodeError as e:
        # Error específico de formato JSON
        line_col = f"línea {e.lineno}, columna {e.colno}"
        logger.error(f"Error de formato JSON en {json_path} ({line_col}): {str(e)}")
        
        # Intentar corrección automática del archivo
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Intentar reparar problemas comunes
            if content.strip().endswith(',]'):
                # Corregir coma final antes del corchete
                content = content.replace(',]', ']')
                
                # Guardar archivo corregido
                with open(json_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Intentar cargar de nuevo
                with open(json_path, 'r', encoding='utf-8') as f:
                    recipes = json.load(f)
                logger.info(f"Archivo JSON corregido automáticamente")
                return recipes[:limit]
        except Exception as repair_error:
            logger.error(f"No se pudo reparar el archivo JSON: {str(repair_error)}")
        
        return []
    except Exception as e:
        logger.error(f"Error cargando recetas guardadas: {str(e)}")
        return []

def main() -> None:
    """Inicia el bot."""
    # Verificar token
    if not TELEGRAM_TOKEN:
        logger.error("Variable de entorno TELEGRAM_BOT_TOKEN no configurada")
        return
    
    try:
        # Configurar tiempo de espera más largo y retries
        request_kwargs = {
            'read_timeout': 10,
            'connect_timeout': 10,
            'con_pool_size': 8,
        }
        
        # Inicializar el Updater con parámetros mejorados
        updater = Updater(TELEGRAM_TOKEN, use_context=True, request_kwargs=request_kwargs)
        dispatcher = updater.dispatcher
        
        # Crear manejador de conversación
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler('start', start),
                CommandHandler('menu', menu_command)
            ],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(button_handler)
                ],
                TEXT_FOOD: [
                    MessageHandler(Filters.text & ~Filters.command, handle_text),
                    CallbackQueryHandler(button_handler)
                ],
                IMAGE_FOOD: [
                    MessageHandler(Filters.photo, handle_photo),
                    CallbackQueryHandler(button_handler)
                ],
                COMPLETE_MEAL_MENU: [
                    CallbackQueryHandler(button_handler)
                ],
                FOOD_HISTORY: [
                    CallbackQueryHandler(button_handler)
                ],
                CREATE_RECIPE: [
                    MessageHandler(Filters.text & ~Filters.command, recipe_conversation_handler),
                    CallbackQueryHandler(button_handler)
                ],
                ADD_INGREDIENTS: [
                    MessageHandler(Filters.text & ~Filters.command, recipe_conversation_handler),
                    CallbackQueryHandler(button_handler)
                ],
                VIEW_RECIPES: [
                    CallbackQueryHandler(button_handler)
                ],
                REQUEST_RECIPE: [
                    MessageHandler(Filters.text & ~Filters.command, handle_recipe_request),
                    CallbackQueryHandler(button_handler)
                ]
            },
            fallbacks=[
                MessageHandler(Filters.all, fallback_handler)
            ]
        )
        
        # Agregar el manejador de conversación
        dispatcher.add_handler(conv_handler)
        
        # Agregar manejadores adicionales
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CommandHandler("reset", reset_command))
        
        # Agregar manejador de errores
        dispatcher.add_error_handler(error_handler)
        
        # Iniciar el bot con parámetros mejorados
        logger.info("Iniciando bot de Telegram...")
        # Configurar polling con reintentos y tiempo de espera mejorado
        updater.start_polling(
            poll_interval=1.0,     # Intervalo entre revisiones de nuevos mensajes
            timeout=30,            # Tiempo de espera para long-polling
            drop_pending_updates=True,  # Ignorar actualizaciones mientras el bot estaba apagado
            allowed_updates=["message", "callback_query", "chat_member"]  # Tipos específicos de actualizaciones
        )
        print("✅ Bot iniciado correctamente")
        
        # Mensaje de información sobre red en la consola
        try:
            import socket
            host_name = socket.gethostname()
            host_ip = socket.gethostbyname(host_name)
            print(f"📡 Información de red: IP: {host_ip}, Hostname: {host_name}")
            print(f"📡 Verificando conexión a api.telegram.org...")
            socket.create_connection(("api.telegram.org", 443), timeout=5)
            print(f"📡 Conexión a api.telegram.org exitosa")
        except Exception as e:
            print(f"❌ Problema de conexión a la red: {str(e)}")
            print("⚠️ Verifica tu conexión a Internet y configuración de firewall")
        
        updater.idle()
        
    except Exception as e:
        logger.error(f"Error iniciando el bot: {str(e)}", exc_info=True)

if __name__ == "__main__":
    main() 