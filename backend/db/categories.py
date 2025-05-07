"""
Sistema de categorización de ingredientes para NutriVeci.
Este módulo proporciona las definiciones y funciones para trabajar con categorías.
"""

from typing import Dict, List, Optional
from enum import Enum


class IngredientCategory(str, Enum):
    """Categorías principales de ingredientes"""
    FRUTAS = "frutas"
    VERDURAS = "verduras"
    CARNES = "carnes"
    LACTEOS = "lacteos"
    GRANOS = "granos"
    LEGUMBRES = "legumbres"
    ACEITES = "aceites"
    FRUTOS_SECOS = "frutos_secos"
    CONDIMENTOS = "condimentos"
    AZUCARES = "azucares"
    BEBIDAS = "bebidas"
    OTROS = "otros"


class PriceCategory(str, Enum):
    """Categorías de precio para ingredientes"""
    BAJO = "bajo"
    MEDIO = "medio"
    ALTO = "alto"


class NutritionalCategory(str, Enum):
    """Categorías nutricionales para ingredientes"""
    PROTEINAS = "proteinas"
    CARBOHIDRATOS = "carbohidratos"
    GRASAS_SALUDABLES = "grasas_saludables"
    GRASAS_SATURADAS = "grasas_saturadas"
    ALTO_FIBRA = "alto_fibra"
    ALTO_VITAMINAS = "alto_vitaminas"
    ALTO_MINERALES = "alto_minerales"
    BAJO_SODIO = "bajo_sodio"
    BAJO_AZUCAR = "bajo_azucar"


# Subcategorías específicas para cada categoría principal
SUBCATEGORIES: Dict[IngredientCategory, List[str]] = {
    IngredientCategory.FRUTAS: [
        "tropicales", "cítricos", "bayas", "frutas_de_hueso", "manzanas_y_peras", "melones", "frutos_exóticos"
    ],
    IngredientCategory.VERDURAS: [
        "hojas_verdes", "raíces", "crucíferas", "bulbos", "tallos", "hongos", "tubérculos", "calabazas"
    ],
    IngredientCategory.CARNES: [
        "res", "cerdo", "aves", "pescados", "mariscos", "carnes_procesadas", "vísceras", "caza"
    ],
    IngredientCategory.LACTEOS: [
        "leches", "quesos", "yogures", "cremas", "mantequillas", "helados", "postres_lácteos"
    ],
    IngredientCategory.GRANOS: [
        "arroz", "trigo", "maíz", "avena", "cebada", "quinoa", "centeno", "mijo"
    ],
    IngredientCategory.LEGUMBRES: [
        "frijoles", "lentejas", "garbanzos", "habas", "arvejas", "soya", "cacahuetes"
    ],
    IngredientCategory.ACEITES: [
        "oliva", "coco", "girasol", "canola", "sésamo", "maíz", "aguacate", "palma"
    ],
    IngredientCategory.FRUTOS_SECOS: [
        "almendras", "nueces", "pistachos", "anacardos", "avellanas", "semillas", "maníes"
    ],
    IngredientCategory.CONDIMENTOS: [
        "hierbas", "especias", "salsas", "aderezos", "vinagres", "sal", "picantes"
    ],
    IngredientCategory.AZUCARES: [
        "azúcar_refinada", "miel", "jarabes", "endulzantes_naturales", "endulzantes_artificiales"
    ],
    IngredientCategory.BEBIDAS: [
        "aguas", "jugos", "bebidas_gaseosas", "alcohólicas", "cafés", "tés", "bebidas_vegetales"
    ],
    IngredientCategory.OTROS: [
        "preparados", "suplementos", "alimentos_procesados", "conservas", "congelados"
    ]
}


# Regiones alimenticias comunes
REGIONS = [
    "mediterránea", "latinoamericana", "asiática", "europea", 
    "norteamericana", "africana", "medio_oriente", "caribeña",
    "local", "internacional"
]


def get_category_hierarchy() -> Dict:
    """
    Obtener la jerarquía completa de categorías y subcategorías
    
    Returns:
        Dict: Diccionario con la estructura jerárquica de categorías
    """
    return {
        "categories": {cat.value: {"subcategories": SUBCATEGORIES[cat]} for cat in IngredientCategory
        },
        "price_categories": [cat.value for cat in PriceCategory],
        "nutritional_categories": [cat.value for cat in NutritionalCategory],
        "regions": REGIONS
    }


def validate_category(category: str) -> bool:
    """
    Validar si una categoría existe en el sistema
    
    Args:
        category (str): Nombre de la categoría a validar
        
    Returns:
        bool: True si la categoría es válida, False en caso contrario
    """
    return category.lower() in [cat.value for cat in IngredientCategory]


def get_subcategories(category: str) -> Optional[List[str]]:
    """
    Obtener las subcategorías de una categoría principal
    
    Args:
        category (str): Nombre de la categoría principal
        
    Returns:
        Optional[List[str]]: Lista de subcategorías o None si la categoría no existe
    """
    try:
        return SUBCATEGORIES[IngredientCategory(category.lower())]
    except (ValueError, KeyError):
        return None


def get_nutritional_profile(category: str) -> Dict:
    """
    Obtener un perfil nutricional predeterminado basado en la categoría
    
    Args:
        category (str): Nombre de la categoría
        
    Returns:
        Dict: Perfil nutricional predeterminado
    """
    base_profile = {
        "calorias": 0,
        "proteinas": 0,
        "carbohidratos": 0,
        "grasas": 0,
        "fibra": 0,
        "azucares": 0
    }
    
    # Valores estimados para categorías principales
    if category == IngredientCategory.FRUTAS.value:
        return {**base_profile, "calorias": 60, "carbohidratos": 15, "fibra": 2, "azucares": 12}
    elif category == IngredientCategory.VERDURAS.value:
        return {**base_profile, "calorias": 25, "carbohidratos": 5, "proteinas": 1, "fibra": 2}
    elif category == IngredientCategory.CARNES.value:
        return {**base_profile, "calorias": 150, "proteinas": 25, "grasas": 8}
    elif category == IngredientCategory.LACTEOS.value:
        return {**base_profile, "calorias": 100, "proteinas": 7, "grasas": 5, "carbohidratos": 5}
    elif category == IngredientCategory.GRANOS.value:
        return {**base_profile, "calorias": 150, "carbohidratos": 30, "proteinas": 3, "fibra": 2}
    elif category == IngredientCategory.LEGUMBRES.value:
        return {**base_profile, "calorias": 120, "proteinas": 8, "carbohidratos": 20, "fibra": 7}
    elif category == IngredientCategory.ACEITES.value:
        return {**base_profile, "calorias": 120, "grasas": 14}
    elif category == IngredientCategory.FRUTOS_SECOS.value:
        return {**base_profile, "calorias": 180, "grasas": 15, "proteinas": 6, "fibra": 3}

    # Para otras categorías, devolver valores base
    return base_profile 