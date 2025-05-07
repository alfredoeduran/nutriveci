import os
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import json
from datetime import datetime
from uuid import uuid4
from typing import Optional, Dict, Any, List

from backend.db.models import Conversation, ConversationCreate, UserCreate
from backend.db import crud

# Cargar variables de entorno
load_dotenv()

# Configurar el router sin prefijo (se añadirá en main.py)
router = APIRouter()

class NLPRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    source: Optional[str] = "web"

class NLPResponse(BaseModel):
    intent: str = "generacion"
    entities: dict = {}
    generated_text: str
    conversation_id: Optional[str] = None
    error: Optional[str] = None

# Configuración de Gemini
MODEL_NAME_COMERCIAL = "Gemini 1.5 Flash"
MODEL_NAME_API = "models/gemini-1.5-flash"

# Verificar API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY no está configurada en las variables de entorno")

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(MODEL_NAME_API)

class GeminiError(Exception):
    """Excepción personalizada para errores de Gemini"""
    pass

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(GeminiError)
)
def gemini_generate_structured(text: str, user_context: str = "") -> dict:
    """Genera una respuesta estructurada usando Gemini con reintentos automáticos."""
    prompt = f"""
Eres un asistente nutricional inteligente. Analiza el siguiente mensaje del usuario y responde en formato JSON con los siguientes campos:
- "intent": intención principal del usuario (por ejemplo: buscar_receta, pedir_consejo, consultar_ingrediente, saludo, despedida, etc)
- "entities": lista de ingredientes, condiciones de salud o conceptos relevantes mencionados (por ejemplo: ["pollo", "diabetes", "sin gluten"])
- "generated_text": respuesta conversacional adecuada para el usuario

Ejemplo de respuesta:
{{
  "intent": "buscar_receta",
  "entities": ["pollo", "sin gluten"],
  "generated_text": "Aquí tienes una receta de pollo sin gluten que te puede interesar..."
}}

Mensaje del usuario: "{text}"
Responde SOLO en JSON válido.

Contexto del usuario:
{user_context}
"""
    try:
        print("[DEBUG] Enviando prompt a Gemini...")
        start_time = datetime.now()
        response = model.generate_content(prompt)
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[DEBUG] Respuesta de Gemini recibida en {elapsed:.2f}s")
        
        if not response.text:
            raise GeminiError("Respuesta vacía de Gemini")
            
        # Intentar extraer JSON de la respuesta
        try:
            start = response.text.find('{')
            end = response.text.rfind('}') + 1
            json_str = response.text[start:end]
            data = json.loads(json_str)
            
            # Validar estructura de respuesta
            required_fields = ["intent", "entities", "generated_text"]
            if not all(field in data for field in required_fields):
                raise GeminiError("Respuesta de Gemini no contiene todos los campos requeridos")
                
            return {
                "intent": data.get("intent", "desconocido"),
                "entities": data.get("entities", []),
                "generated_text": data.get("generated_text", response.text)
            }
        except json.JSONDecodeError as e:
            raise GeminiError(f"Error decodificando JSON de Gemini: {str(e)}")
            
    except Exception as e:
        if isinstance(e, GeminiError):
            raise
        raise GeminiError(f"Error inesperado en Gemini: {str(e)}")

@router.post("/nlp/interpret", response_model=NLPResponse)
async def interpret_text(request: NLPRequest):
    """Procesa el texto del usuario y genera una respuesta."""
    try:
        # Validar user_id
        if not request.user_id or str(request.user_id).strip() == "" or request.user_id == "None":
            return NLPResponse(
                intent="error",
                entities={},
                generated_text="Se requiere un identificador de usuario válido",
                error="USER_ID_REQUIRED"
            )
        
        # Obtener perfil de usuario
        user_profile = await crud.get_user(request.user_id)
        if not user_profile:
            # Si no existe el usuario, crear uno nuevo
            user_profile = await crud.create_user(UserCreate(
                web_id=request.user_id if request.source == "web" else None,
                telegram_id=request.user_id if request.source == "telegram" else None,
                source=request.source
            ))
        
        # Generar respuesta con Gemini
        try:
            # Añadir contexto del usuario al prompt
            user_context = f"""
            Usuario: {user_profile.name or 'Anónimo'}
            Edad: {user_profile.age or 'No especificada'}
            Peso: {user_profile.weight or 'No especificado'} kg
            Altura: {user_profile.height or 'No especificada'} cm
            Alergias: {', '.join(user_profile.allergies) if user_profile.allergies else 'Ninguna'}
            """
            
            result = gemini_generate_structured(request.text, user_context)
        except GeminiError as e:
            return NLPResponse(
                intent="error",
                entities={},
                generated_text=f"Error al procesar tu mensaje: {str(e)}",
                error="GEMINI_ERROR"
            )
        
        # Guardar la conversación
        try:
            conversation = ConversationCreate(
                user_id=request.user_id,
                message=request.text,
                response=result,
                source=request.source
            )
            saved_conversation = await crud.save_conversation(conversation)
        except Exception as e:
            print(f"[ERROR] Error al guardar conversación: {str(e)}")
            saved_conversation = None
        
        # Procesar entidades y sugerir recetas si es necesario
        entities = result["entities"]
        if isinstance(entities, list):
            entities_list = entities
            entities = {f"entity_{i+1}": v for i, v in enumerate(entities_list)}
        elif not isinstance(entities, dict):
            entities_list = [str(entities)]
            entities = {"value": str(entities)}
        else:
            entities_list = list(entities.values())
            
        # Buscar recetas si la intención es buscar_receta
        recetas_sugeridas = []
        if result["intent"] == "buscar_receta" and entities_list:
            try:
                # Buscar recetas que contengan los ingredientes mencionados
                recetas = await crud.search_recipes_by_ingredients(entities_list, limit=3)
                if recetas:
                    recetas_sugeridas = [r.name for r in recetas]
                    result["generated_text"] += "\n\nRecetas sugeridas:\n" + "\n".join(f"- {r}" for r in recetas_sugeridas)
            except Exception as e:
                print(f"[ERROR] Error al buscar recetas: {str(e)}")
        
        return NLPResponse(
            intent=result["intent"],
            entities=entities,
            generated_text=result["generated_text"],
            conversation_id=saved_conversation.id if saved_conversation else None
        )
        
    except Exception as e:
        print(f"[ERROR] Error inesperado en interpret_text: {str(e)}")
        return NLPResponse(
            intent="error",
            entities={},
            generated_text="Ocurrió un error inesperado al procesar tu mensaje",
            error="UNEXPECTED_ERROR"
        )

