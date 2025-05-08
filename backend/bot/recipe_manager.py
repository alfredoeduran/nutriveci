import os
import json
import logging
import uuid
from datetime import datetime

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Datos temporales
recipe_context = {}  # Almacena contexto durante creación de recetas
user_data = {}  # Almacena datos de usuarios

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data")


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