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
food_processor = GeminiFoodProcessor(DATA_PATH)

# Estados para el ConversationHandler
MAIN_MENU, TEXT_FOOD, IMAGE_FOOD, COMPLETE_MEAL_MENU, FOOD_HISTORY = range(5)

# Datos de usuario (en memoria - en producción usar base de datos)
user_data = {}

def get_user_data(user_id):
    """Obtiene o crea datos de usuario."""
    if user_id not in user_data:
        user_data[user_id] = {
            "history": [],
            "daily_calories": 0,
            "last_date": datetime.now().strftime("%Y-%m-%d")
        }
    
    # Resetear calorías si es un nuevo día
    current_date = datetime.now().strftime("%Y-%m-%d")
    if user_data[user_id]["last_date"] != current_date:
        user_data[user_id]["daily_calories"] = 0
        user_data[user_id]["last_date"] = current_date
    
    return user_data[user_id]

def get_main_menu_keyboard():
    """Genera el teclado para el menú principal."""
    keyboard = [
        [InlineKeyboardButton("🥗 Ingresar alimento", callback_data='food_input')],
        [InlineKeyboardButton("🍽️ Ingresar plato completo", callback_data='meal_input')],
        [InlineKeyboardButton("📝 Historial de búsquedas", callback_data='history')],
        [InlineKeyboardButton("📊 Calorías acumuladas del día", callback_data='calories')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_complete_meal_menu_keyboard():
    """Genera el teclado para el menú de plato completo."""
    keyboard = [
        [InlineKeyboardButton("📝 Texto", callback_data='meal_text')],
        [InlineKeyboardButton("🖼️ Imagen", callback_data='meal_image')],
        [InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_food_input_keyboard():
    """Genera el teclado para el menú de ingreso de alimentos."""
    # Obtener alimentos sugeridos (comunes)
    suggested_foods = ["Pollo", "Arroz", "Manzana", "Pan", "Leche"]
    
    keyboard = []
    # Crear botones para cada alimento sugerido
    for i in range(0, len(suggested_foods), 2):
        row = []
        row.append(InlineKeyboardButton(suggested_foods[i], callback_data=f'food_{suggested_foods[i]}'))
        if i + 1 < len(suggested_foods):
            row.append(InlineKeyboardButton(suggested_foods[i+1], callback_data=f'food_{suggested_foods[i+1]}'))
        keyboard.append(row)
    
    # Botón para volver al menú principal
    keyboard.append([InlineKeyboardButton("🔙 Volver al menú principal", callback_data='main_menu')])
    
    return InlineKeyboardMarkup(keyboard)

def get_action_keyboard():
    """Genera el teclado para las acciones rápidas."""
    keyboard = [
        [InlineKeyboardButton("🏠 Menú principal", callback_data='main_menu')],
        [InlineKeyboardButton("🗑️ Limpiar historial", callback_data='clear_history')],
        [InlineKeyboardButton("👀 Ver últimos alimentos", callback_data='recent_foods')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Comandos
def start(update: Update, context: CallbackContext) -> int:
    """Maneja el comando /start y presenta el menú principal."""
    user = update.effective_user
    
    # Inicializar datos de usuario
    get_user_data(user.id)
    
    welcome_message = f"""
¡Hola {user.first_name}! Soy *NutriVeci*, tu asistente nutricional. 🥗

Puedo ayudarte con:
• Información nutricional de alimentos
• Análisis de platos completos
• Seguimiento de calorías diarias
• Recomendaciones alimenticias

¿En qué puedo ayudarte hoy?
"""
    
    update.message.reply_text(
        welcome_message,
        reply_markup=get_main_menu_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    
    return MAIN_MENU

def help_command(update: Update, context: CallbackContext) -> None:
    """Maneja el comando /help."""
    help_text = """
*Comandos disponibles:*
/start - Iniciar o reiniciar el bot
/help - Mostrar esta ayuda
/menu - Mostrar el menú principal
/reset - Reiniciar las calorías del día

*Funciones:*
• *Ingresar alimento* - Obtén información nutricional de un alimento específico
• *Ingresar plato completo* - Analiza varios alimentos a la vez o una imagen
• *Historial* - Revisa tus búsquedas recientes
• *Calorías del día* - Consulta tu consumo calórico diario

Para comenzar, usa /start o /menu.
"""
    update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

def menu_command(update: Update, context: CallbackContext) -> int:
    """Maneja el comando /menu y muestra el menú principal."""
    update.message.reply_text(
        "¿Qué te gustaría hacer?",
        reply_markup=get_main_menu_keyboard()
    )
    return MAIN_MENU

def reset_command(update: Update, context: CallbackContext) -> None:
    """Reinicia el contador de calorías diarias."""
    user_id = update.effective_user.id
    user_info = get_user_data(user_id)
    user_info["daily_calories"] = 0
    
    update.message.reply_text(
        "✅ ¡Contador de calorías diarias reiniciado!",
        reply_markup=get_action_keyboard()
    )

# Manejadores de callback queries (botones)
def button_handler(update: Update, context: CallbackContext) -> int:
    """Maneja los callbacks de los botones inline."""
    query = update.callback_query
    try:
        query.answer()
    except Exception as e:
        logger.warning(f"No se pudo responder al callback query: {str(e)}")
        # Continuar con el proceso aunque no se pueda responder al query
    
    # Extraer el callback_data para determinar la acción
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
    
    # Manejar botones de alimentos sugeridos
    elif data.startswith('food_'):
        food_name = data[5:]
        process_food_item(query, food_name)
        return MAIN_MENU
    
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
    
    # Obtener información nutricional
    nutrition_info = food_processor.get_nutrition_info_sync(food_name)
    
    # Construir mensaje con la información
    if nutrition_info["calories"] is None and nutrition_info["protein"] is None:
        # No se encontró información
        send_func(
            f"No he podido encontrar información nutricional para *{food_name}*.",
            reply_markup=get_action_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Guardar en el historial
    user_info = get_user_data(user_id)
    user_info["history"].append(nutrition_info)
    
    # Actualizar calorías diarias si hay información
    if nutrition_info["calories"] is not None:
        user_info["daily_calories"] += nutrition_info["calories"]
    
    # Construir mensaje
    message = f"🥗 *{nutrition_info['name']}*\n\n"
    
    if nutrition_info["calories"] is not None:
        message += f"• Calorías: {nutrition_info['calories']:.1f} kcal\n"
    if nutrition_info["protein"] is not None:
        message += f"• Proteínas: {nutrition_info['protein']:.1f} g\n"
    if nutrition_info["carbs"] is not None:
        message += f"• Carbohidratos: {nutrition_info['carbs']:.1f} g\n"
    if nutrition_info["fat"] is not None:
        message += f"• Grasas: {nutrition_info['fat']:.1f} g\n"
    
    # Agregar recomendaciones según el tipo de alimento
    message += "\n💡 *Recomendaciones:*\n"
    
    if nutrition_info["carbs"] is not None and nutrition_info["carbs"] > 15:
        message += "• Rico en carbohidratos, ideal para actividad física\n"
    if nutrition_info["protein"] is not None and nutrition_info["protein"] > 10:
        message += "• Buena fuente de proteínas para músculos\n"
    if nutrition_info["fat"] is not None and nutrition_info["fat"] < 5:
        message += "• Bajo en grasas, adecuado para dieta balanceada\n"
    else:
        message += "• Procura mantener una alimentación variada y equilibrada\n"
    
    # Mostrar calorías acumuladas
    message += f"\n📊 Calorías acumuladas hoy: {user_info['daily_calories']:.1f} kcal"
    
    send_func(
        message,
        reply_markup=get_action_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

# Manejadores de mensajes
def handle_text(update: Update, context: CallbackContext) -> int:
    """Maneja los mensajes de texto para detectar alimentos."""
    text = update.message.text
    
    # Detectar si es una lista de alimentos (separados por comas)
    if ',' in text:
        # Mensaje de espera
        update.message.reply_text("Analizando los alimentos... ⏳")
        
        # Separar alimentos y procesar individualmente
        food_items = [item.strip() for item in text.split(',') if item.strip()]
        
        if not food_items:
            update.message.reply_text(
                "No he podido identificar alimentos en tu mensaje. Por favor, sé más específico.",
                reply_markup=get_main_menu_keyboard()
            )
            return MAIN_MENU
            
        # Mostrar cada alimento encontrado
        update.message.reply_text(f"He encontrado {len(food_items)} alimentos en tu mensaje:")
        
        # Procesar cada alimento
        all_foods_info = []
        total_calories = 0
        
        for food in food_items:
            # Obtener información nutricional
            nutrition_info = food_processor.get_nutrition_info_sync(food)
            all_foods_info.append(nutrition_info)
            
            # Acumular calorías
            if nutrition_info["calories"] is not None:
                total_calories += nutrition_info["calories"]
            
            # Guardar en el historial
            user_info = get_user_data(update.effective_user.id)
            user_info["history"].append(nutrition_info)
            
            # Actualizar calorías diarias
            if nutrition_info["calories"] is not None:
                user_info["daily_calories"] += nutrition_info["calories"]
        
        # Construir mensaje con todos los alimentos
        message = "🍽️ *Información nutricional del plato:*\n\n"
        
        for info in all_foods_info:
            message += f"🥗 *{info['name']}*\n"
            
            if info["calories"] is not None:
                message += f"• Calorías: {info['calories']:.1f} kcal\n"
            if info["protein"] is not None:
                message += f"• Proteínas: {info['protein']:.1f} g\n"
            if info["carbs"] is not None:
                message += f"• Carbohidratos: {info['carbs']:.1f} g\n"
            if info["fat"] is not None:
                message += f"• Grasas: {info['fat']:.1f} g\n"
            
            message += "\n"
        
        message += f"*Total de calorías del plato: {total_calories:.1f} kcal*\n\n"
        
        # Recomendaciones
        message += "💡 *Recomendaciones:*\n"
        message += "• Procura mantener una alimentación variada\n"
        message += "• No olvides incluir frutas y verduras\n"
        message += "• Bebe suficiente agua durante el día\n"
        
        # Mostrar calorías acumuladas
        user_info = get_user_data(update.effective_user.id)
        message += f"\n📊 Calorías acumuladas hoy: {user_info['daily_calories']:.1f} kcal"
        
        update.message.reply_text(
            message,
            reply_markup=get_action_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
        
    else:
        # Procesar como un solo alimento
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
        
        # Obtener los alimentos detectados
        foods = detection_result["detected_foods"]
        
        # Mensaje con los alimentos detectados
        foods_message = "He detectado los siguientes alimentos:\n\n"
        for food in foods:
            confidence = detection_result["confidence_scores"].get(food, 0) * 100
            foods_message += f"• {food} (confianza: {confidence:.1f}%)\n"
        
        retry_handler.execute_with_retry(
            update.message.reply_text,
            foods_message
        )
        
        try:
            # Obtener información nutricional de los alimentos
            all_foods_info = food_processor.integrate_vision_results_sync(foods)
            
            # Verificar si hay información nutricional
            if not all_foods_info:
                logger.warning("No se obtuvo información nutricional de los alimentos detectados")
                retry_handler.execute_with_retry(
                    update.message.reply_text,
                    "No he podido obtener información nutricional detallada. Esto puede deberse a una limitación en nuestra base de datos.",
                    reply_markup=get_action_keyboard()
                )
                return MAIN_MENU
            
            # Construir mensaje con información nutricional
            nutrition_message = "📊 *Información nutricional:*\n\n"
            total_calories = 0
            
            for info in all_foods_info:
                # Verificar si hay información válida
                if not info or "name" not in info:
                    continue
                    
                nutrition_message += f"🍽️ *{info['name']}*\n"
                
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
                    user_info["history"].append(info)
            
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