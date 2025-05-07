from typing import List, Dict
from uuid import uuid4

def generar_receta_con_llm(texto_usuario: str, ingredientes: List[str]) -> Dict:
    """
    Llama al LLM para generar una receta estructurada a partir del texto del usuario y los ingredientes detectados.
    Devuelve un dict con los campos principales de la receta.
    """
    # Aquí deberías llamar a tu modelo LLM real (ejemplo con Gemini, puedes adaptar)
    # Simulación básica:
    nombre = f"Receta especial con {' y '.join(ingredientes)}"
    instrucciones = f"Instrucciones generadas para: {' y '.join(ingredientes)}."
    return {
        "id": str(uuid4()),
        "name": nombre,
        "description": f"Receta generada automáticamente para: {', '.join(ingredientes)}.",
        "instructions": instrucciones,
        "ingredients": ingredientes
    }
