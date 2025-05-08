from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import logging

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    """
    Manejador del comando /start.
    
    Args:
        update: Objeto de actualización de Telegram
        context: Contexto del callback
    """
    user = update.effective_user
    logger.info(f"Usuario {user.first_name} ha iniciado el bot.")
    update.message.reply_text(
        f"Hola {user.first_name}, bienvenido a Nutriveci Bot! Usa /menu para ver las opciones disponibles."
    )


def menu_command(update: Update, context: CallbackContext) -> None:
    """
    Manejador del comando /menu.
    
    Args:
        update: Objeto de actualización de Telegram
        context: Contexto del callback
    """
    logger.info("Mostrando menú de opciones.")
    keyboard = [
        [InlineKeyboardButton("Ver recetas", callback_data='view_recipes')],
        [InlineKeyboardButton("Añadir receta", callback_data='add_recipe')],
        [InlineKeyboardButton("Ayuda", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Selecciona una opción:', reply_markup=reply_markup)


def help_command(update: Update, context: CallbackContext) -> None:
    """
    Manejador del comando /help.
    
    Args:
        update: Objeto de actualización de Telegram
        context: Contexto del callback
    """
    logger.info("Mostrando mensaje de ayuda.")
    update.message.reply_text(
        "Aquí tienes algunos comandos que puedes usar:\n"
        "/start - Inicia el bot\n"
        "/menu - Muestra el menú de opciones\n"
        "/help - Muestra este mensaje de ayuda"
    )


def button(update: Update, context: CallbackContext) -> None:
    """
    Manejador para los botones del menú.
    
    Args:
        update: Objeto de actualización de Telegram
        context: Contexto del callback
    """
    query = update.callback_query
    query.answer()
    
    logger.info(f"Botón presionado: {query.data}")
    
    if query.data == 'view_recipes':
        query.edit_message_text(text="Aquí están tus recetas guardadas.")
    elif query.data == 'add_recipe':
        query.edit_message_text(text="Funcionalidad para añadir recetas próximamente.")
    elif query.data == 'help':
        query.edit_message_text(text="Aquí tienes algunos comandos que puedes usar:\n"
                                "/start - Inicia el bot\n"
                                "/menu - Muestra el menú de opciones\n"
                                "/help - Muestra este mensaje de ayuda")
    else:
        query.edit_message_text(text="Opción no reconocida.") 