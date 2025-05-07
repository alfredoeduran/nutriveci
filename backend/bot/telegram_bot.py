import os
import sys
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
import asyncio
from backend.db import crud
from backend.db.models import UserCreate
from backend.ai.integrator import NutriVeciAI

# Añadir directorio raíz al path para importaciones
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))

# Cargar variables de entorno
load_dotenv()

# Configuración del bot
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN no está configurada en las variables de entorno")

# Inicializar integrador de IA
DATA_PATH = os.path.join(ROOT_DIR, "data")
ai_integrator = NutriVeciAI(data_path=DATA_PATH)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /start"""
    user = update.effective_user
    welcome_message = f"""
¡Hola {user.first_name}! Soy NutriVeci, tu asistente nutricional.

Puedo ayudarte con:
- Recomendaciones de recetas
- Consejos nutricionales
- Información sobre ingredientes
- Análisis de fotos de alimentos
- Planificación de comidas

Envíame un mensaje con tu pregunta o una foto de alimentos para comenzar.
"""
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /help"""
    help_text = """
Comandos disponibles:
/start - Iniciar conversación
/help - Mostrar esta ayuda
/profile - Ver tu perfil
/recipes - Buscar recetas

También puedes:
- Enviarme mensajes para pedir información nutricional
- Enviarme fotos de alimentos para que los analice
- Pedirme recetas saludables
- Consultar información de ingredientes
"""
    await update.message.reply_text(help_text)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja el comando /profile"""
    user = update.effective_user
    user_profile = await crud.get_user(str(user.id))
    
    if not user_profile:
        await update.message.reply_text(
            "No tienes un perfil configurado. Usa /start para comenzar."
        )
        return
    
    profile_text = f"""
Tu perfil:
Nombre: {user_profile.name or 'No especificado'}
Edad: {user_profile.age or 'No especificada'}
Peso: {user_profile.weight or 'No especificado'} kg
Altura: {user_profile.height or 'No especificada'} cm
Alergias: {', '.join(user_profile.allergies) if user_profile.allergies else 'Ninguna'}
"""
    await update.message.reply_text(profile_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los mensajes del usuario"""
    user = update.effective_user
    text = update.message.text
    
    # Crear o obtener usuario
    user_profile = await crud.get_user(str(user.id))
    if not user_profile:
        user_profile = await crud.create_user(UserCreate(
            telegram_id=str(user.id),
            name=user.first_name,
            source="telegram"
        ))
        user_profile_dict = user_profile.dict()
    else:
        user_profile_dict = user_profile.dict()
    
    # Mostrar mensaje de espera
    await update.message.reply_text("Procesando tu mensaje... ⏳")
    
    # Procesar mensaje con el integrador de IA
    try:
        response = await ai_integrator.analyze_text(text, user_profile_dict)
        
        if response.get("error"):
            await update.message.reply_text(f"Error: {response['error']}")
        else:
            await update.message.reply_text(response["generated_text"])
            
    except Exception as e:
        print(f"[ERROR] Error procesando mensaje: {str(e)}")
        await update.message.reply_text(
            "Lo siento, hubo un error procesando tu mensaje. Por favor, intenta de nuevo."
        )

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja las fotos enviadas por el usuario"""
    user = update.effective_user
    
    # Crear o obtener usuario
    user_profile = await crud.get_user(str(user.id))
    if not user_profile:
        user_profile = await crud.create_user(UserCreate(
            telegram_id=str(user.id),
            name=user.first_name,
            source="telegram"
        ))
        user_profile_dict = user_profile.dict()
    else:
        user_profile_dict = user_profile.dict()
    
    # Mostrar mensaje de espera
    await update.message.reply_text("Analizando la imagen... ⏳")
    
    # Obtener la foto de mayor resolución
    photo = update.message.photo[-1]
    
    # Descargar la foto
    photo_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Analizar la imagen con el integrador de IA
    try:
        analysis_result = await ai_integrator.analyze_image(photo_bytes, user_profile_dict)
        
        if not analysis_result.get("success", False):
            await update.message.reply_text(
                analysis_result.get("error", "Lo siento, hubo un error al procesar la imagen.")
            )
            return
        
        # Primera respuesta: alimentos detectados
        detected_foods = analysis_result.get("detected_foods", [])
        if detected_foods:
            foods_message = "He detectado los siguientes alimentos:\n\n"
            for food in detected_foods:
                confidence = analysis_result["confidence_scores"].get(food, 0) * 100
                foods_message += f"• {food} (confianza: {confidence:.1f}%)\n"
            
            await update.message.reply_text(foods_message)
        
        # Segunda respuesta: información nutricional y recomendaciones
        if analysis_result.get("generated_text"):
            await update.message.reply_text(analysis_result["generated_text"])
        else:
            await update.message.reply_text(
                "No pude generar información nutricional para estos alimentos."
            )
        
    except Exception as e:
        print(f"[ERROR] Error procesando imagen: {str(e)}")
        await update.message.reply_text(
            "Lo siento, hubo un error procesando la imagen. Por favor, intenta de nuevo."
        )

def main():
    """Inicia el bot"""
    # Crear aplicación más simple
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Añadir handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Iniciar bot con polling explícito
    print("Iniciando bot de Telegram...")
    application.run_polling(poll_interval=1.0, timeout=30)

if __name__ == "__main__":
    main() 