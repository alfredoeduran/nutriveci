import os
import logging
import requests
import pandas as pd
from backend.ai.nlp.gemini_food_processor import GeminiFoodProcessor

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

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
    
    def integrate_vision_results_sync(self, food_items):
        """
        Procesa una lista de alimentos detectados en imágenes y obtiene información nutricional.
        
        Args:
            food_items: Lista de nombres de alimentos en inglés
            
        Returns:
            list: Lista de diccionarios con información nutricional de cada alimento
        """
        if not food_items:
            logger.warning("No se recibieron alimentos para procesar en integrate_vision_results_sync")
            return []
        
        logger.info(f"Procesando {len(food_items)} alimentos detectados: {food_items}")
        
        # Lista para almacenar la información nutricional de cada alimento
        results = []
        
        # Procesar cada alimento individualmente
        for food in food_items:
            try:
                # Buscar en USDA primero
                nutrition_info = self.load_usda_food_data(food)
                
                # Si no está en USDA, generar con Gemini
                if not nutrition_info:
                    logger.info(f"Alimento '{food}' no encontrado en USDA, generando información...")
                    nutrition_info = self.generate_nutrition_info(food)
                
                # Asegurarse de establecer el nombre
                nutrition_info["name"] = food
                nutrition_info["is_food"] = True
                
                # Agregar a resultados
                results.append(nutrition_info)
                
            except Exception as e:
                logger.error(f"Error procesando alimento '{food}': {str(e)}")
                # Agregar entrada con error
                results.append({
                    "name": food,
                    "calories": 100,  # Valores aproximados por defecto
                    "protein": 5,
                    "carbs": 15,
                    "fat": 2,
                    "source": "error_fallback",
                    "error": str(e)
                })
        
        logger.info(f"Procesados {len(results)} alimentos con información nutricional")
        return results 