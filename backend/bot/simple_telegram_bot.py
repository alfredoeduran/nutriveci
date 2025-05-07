"""
Bot de Telegram minimalista para NutriVeci.
"""
import os
import sys
import asyncio
from pathlib import Path

# Agregar la raíz del proyecto al path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

# Importar el módulo imghdr personalizado
sys.path.insert(0, str(Path(__file__).parent))
import imghdr

# Importar después de configurar el path
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from dotenv import load_dotenv

# Importar después de configurar el path
from backend.ai.vision.food_detector_fixed import FoodDetector
from backend.ai.nlp.gemini_food_processor import GeminiFoodProcessor

# Cargar variables de entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Configurar componentes
DATA_PATH = os.path.join(ROOT_DIR, "data")
food_detector = FoodDetector()
food_processor = GeminiFoodProcessor(DATA_PATH)

# Configurar el estado global
user_conversations = {}

def start_command(update: Update, context: CallbackContext) -> None:
    """Maneja el comando /start."""
    user = update.effective_user
    welcome_message = f"""
¡Hola {user.first_name}! Soy NutriVeci, tu asistente nutricional.

Puedo ayudarte con:
- Recomendaciones de recetas
- Consejos nutricionales
- Información sobre ingredientes
- Análisis de fotos de alimentos

Envíame un mensaje con tu pregunta o una foto de alimentos para comenzar.
"""
    update.message.reply_text(welcome_message)

def help_command(update: Update, context: CallbackContext) -> None:
    """Maneja el comando /help."""
    help_text = """
Comandos disponibles:
/start - Iniciar conversación
/help - Mostrar esta ayuda

También puedes:
- Enviarme mensajes para pedir información nutricional
- Enviarme fotos de alimentos para que los analice
"""
    update.message.reply_text(help_text)

def handle_text(update: Update, context: CallbackContext) -> None:
    """Maneja los mensajes de texto."""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Mensaje de espera
    update.message.reply_text("Analizando tu mensaje... ⏳")
    
    try:
        # Usar la función asíncrona dentro de un nuevo bucle de eventos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        food_items = loop.run_until_complete(food_processor.extract_food_items(text))
        loop.close()
        
        if not food_items:
            update.message.reply_text(
                "No he podido identificar alimentos en tu mensaje. Por favor, sé más específico o envíame una foto de los alimentos."
            )
            return
        
        # Obtener información nutricional
        nutrition_info = []
        for food in food_items:
            # Crear un nuevo bucle para cada alimento
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            info = loop.run_until_complete(food_processor.get_nutrition_info(food))
            loop.close()
            nutrition_info.append(info)
        
        # Construir respuesta
        response = f"He encontrado información sobre los siguientes alimentos:\n\n"
        
        for info in nutrition_info:
            response += f"🍽️ *{info['name']}*\n"
            
            if info["calories"] is not None:
                response += f"• Calorías: {info['calories']} kcal\n"
            if info["protein"] is not None:
                response += f"• Proteínas: {info['protein']} g\n"
            if info["carbs"] is not None:
                response += f"• Carbohidratos: {info['carbs']} g\n"
            if info["fat"] is not None:
                response += f"• Grasas: {info['fat']} g\n"
            
            response += "\n"
        
        # Agregar recomendaciones generales
        response += "💡 *Recomendaciones:*\n"
        response += "• Mantén una dieta equilibrada con variedad de alimentos\n"
        response += "• No olvides incluir frutas y verduras en tu alimentación diaria\n"
        response += "• Bebe suficiente agua durante el día\n"
        
        update.message.reply_text(response, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error procesando mensaje: {str(e)}")
        update.message.reply_text(
            "Lo siento, ha ocurrido un error al procesar tu mensaje. Por favor, intenta de nuevo."
        )

def handle_photo(update: Update, context: CallbackContext) -> None:
    """Maneja las fotos enviadas por el usuario."""
    # Mensaje de espera
    update.message.reply_text("Analizando la imagen... ⏳")
    
    try:
        # Obtener la foto de mayor resolución
        photo = update.message.photo[-1]
        print(f"Foto recibida. File ID: {photo.file_id}, Dimensiones: {photo.width}x{photo.height}")
        
        # Descargar la foto como bytes
        photo_file = photo.get_file()
        
        # Obtener directamente los bytes de la imagen
        import io
        import requests
        from urllib.parse import urlparse
        
        # Verificar si estamos en un entorno local o en la nube
        file_url = photo_file.file_path
        if not file_url.startswith('http'):
            # Si estamos en local, descargar usando el método estándar
            photo_bytes = photo_file.download_as_bytearray()
        else:
            # Si es una URL, usar requests para descargar
            print(f"Descargando desde URL: {file_url}")
            response = requests.get(file_url)
            photo_bytes = response.content
        
        print(f"Imagen descargada: {len(photo_bytes)} bytes")
        
        # Detectar alimentos en la imagen
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        detection_result = loop.run_until_complete(food_detector.detect_food(photo_bytes))
        loop.close()
        
        print(f"Resultado de Clarifai: {detection_result}")
        
        if not detection_result["success"] or not detection_result["detected_foods"]:
            if "error" in detection_result:
                print(f"Error de Clarifai: {detection_result['error']}")
                update.message.reply_text(
                    f"Error al analizar la imagen: {detection_result['error']}\n"
                    "Por favor, intenta con otra foto."
                )
            else:
                update.message.reply_text(
                    "No he podido identificar alimentos en esta imagen. Por favor, intenta con otra foto más clara."
                )
            return
        
        # Obtener los alimentos detectados
        foods = detection_result["detected_foods"]
        
        # Mensaje con los alimentos detectados
        foods_message = "He detectado los siguientes alimentos:\n\n"
        for food in foods:
            confidence = detection_result["confidence_scores"].get(food, 0) * 100
            foods_message += f"• {food} (confianza: {confidence:.1f}%)\n"
        
        update.message.reply_text(foods_message)
        
        # Obtener información nutricional de los alimentos
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nutrition_results = loop.run_until_complete(food_processor.integrate_vision_results(foods))
        loop.close()
        
        # Construir mensaje con información nutricional
        nutrition_message = "📊 *Información nutricional:*\n\n"
        
        for info in nutrition_results:
            nutrition_message += f"🍽️ *{info['name']}*\n"
            
            if info["calories"] is not None:
                nutrition_message += f"• Calorías: {info['calories']} kcal\n"
            if info["protein"] is not None:
                nutrition_message += f"• Proteínas: {info['protein']} g\n"
            if info["carbs"] is not None:
                nutrition_message += f"• Carbohidratos: {info['carbs']} g\n"
            if info["fat"] is not None:
                nutrition_message += f"• Grasas: {info['fat']} g\n"
            
            nutrition_message += "\n"
        
        # Agregar recomendaciones generales
        nutrition_message += "💡 *Recomendaciones:*\n"
        nutrition_message += "• Mantén una dieta equilibrada con variedad de alimentos\n"
        nutrition_message += "• No olvides incluir frutas y verduras en tu alimentación diaria\n"
        nutrition_message += "• Bebe suficiente agua durante el día\n"
        
        update.message.reply_text(nutrition_message, parse_mode="Markdown")
        
    except Exception as e:
        print(f"Error procesando imagen: {str(e)}")
        update.message.reply_text(
            "Lo siento, ha ocurrido un error al procesar la imagen. Por favor, intenta de nuevo."
        )

def main() -> None:
    """Inicia el bot."""
    # Verificar token
    if not TELEGRAM_TOKEN:
        print("ERROR: Variable de entorno TELEGRAM_BOT_TOKEN no configurada")
        return
    
    try:
        # Inicializar el Updater
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Añadir manejadores
        dispatcher.add_handler(CommandHandler("start", start_command))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(MessageHandler(Filters.photo, handle_photo))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
        
        # Iniciar el bot
        print("Iniciando bot de Telegram...")
        updater.start_polling()
        print("✅ Bot iniciado correctamente")
        updater.idle()
        
    except Exception as e:
        print(f"Error iniciando el bot: {str(e)}")

if __name__ == "__main__":
    main() 