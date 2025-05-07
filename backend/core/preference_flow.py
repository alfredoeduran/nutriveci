from enum import Enum
import json
from typing import Dict, List, Optional, Tuple, Union
from uuid import UUID

from backend.db import crud
from backend.db.models import DietaryProfileCreate, User, UserPreferenceCreate

# Clave para almacenar el estado del flujo en los datos de sesión
PREFERENCE_FLOW_STATE_KEY = "preference_flow_state"


class FlowState(str, Enum):
    """Estados posibles del flujo de registro de preferencias"""
    INITIAL = "initial"
    DIET_TYPE = "diet_type"
    ALLERGENS = "allergens"
    INTOLERANCES = "intolerances"
    MEDICAL_CONDITIONS = "medical_conditions"
    FAVORITE_FOODS = "favorite_foods"
    DISLIKED_FOODS = "disliked_foods"
    CUISINES = "cuisines"
    COOKING_SKILL = "cooking_skill"
    COOKING_FREQUENCY = "cooking_frequency"
    BUDGET = "budget"
    HOUSEHOLD_SIZE = "household_size"
    DIET_GOALS = "diet_goals"
    COMPLETED = "completed"


class PreferenceResponse:
    """Clase para manejar respuestas del flujo de preferencias"""
    def __init__(
        self,
        message: str,
        options: Optional[List[str]] = None,
        state: FlowState = FlowState.INITIAL,
        completed: bool = False,
    ):
        self.message = message
        self.options = options or []
        self.state = state
        self.completed = completed


class PreferenceFlow:
    """
    Clase para manejar el flujo conversacional de registro de preferencias.
    Gestiona el estado del flujo y la transición entre etapas.
    """
    
    # Dieta común
    DIET_TYPES = ["omnívoro", "vegetariano", "vegano", "pescatariano", "flexitariano", "keto", "paleo", "otro"]
    
    # Alérgenos comunes
    COMMON_ALLERGENS = [
        "leche", "huevos", "pescado", "mariscos", "nueces", "maní", "soya", 
        "trigo", "gluten", "sésamo", "ninguno"
    ]
    
    # Intolerancias comunes
    COMMON_INTOLERANCES = [
        "lactosa", "gluten", "fructosa", "sacarosa", "sorbitol", "histamina", 
        "salicilatos", "cafeína", "sulfitos", "ninguna"
    ]
    
    # Condiciones médicas relacionadas con la alimentación
    COMMON_MEDICAL_CONDITIONS = [
        "diabetes", "hipertensión", "colesterol alto", "celiaquía", "enfermedad de Crohn",
        "síndrome de intestino irritable", "reflujo ácido", "gota", "hipotiroidismo", 
        "hipertiroidismo", "ninguna"
    ]
    
    # Tipos de cocina
    CUISINE_TYPES = [
        "mexicana", "italiana", "china", "japonesa", "india", "tailandesa", 
        "mediterránea", "francesa", "española", "peruana", "argentina", "colombiana", 
        "venezolana", "estadounidense", "coreana", "medio oriente"
    ]
    
    # Niveles de habilidad culinaria
    COOKING_SKILL_LEVELS = ["principiante", "intermedio", "avanzado"]
    
    # Frecuencia de cocción
    COOKING_FREQUENCIES = ["diario", "varias veces por semana", "semanal", "ocasional", "raramente"]
    
    # Objetivos dietéticos
    DIET_GOALS = [
        "perder peso", "ganar peso", "mantener peso", "aumentar masa muscular", 
        "mejorar salud general", "mejorar digestión", "reducir inflamación", 
        "aumentar energía", "controlar condición médica", "ninguno específico"
    ]
    
    def __init__(self, user_id: UUID):
        """
        Inicializar el flujo de preferencias para un usuario.
        
        Args:
            user_id: ID del usuario para el que se está configurando preferencias
        """
        self.user_id = user_id
        self.state = FlowState.INITIAL
        self.preference_data = {}
        self.dietary_data = {}
        self.user_data = {}
    
    async def start(self) -> PreferenceResponse:
        """
        Iniciar el flujo de registro de preferencias.
        
        Returns:
            Respuesta con el mensaje inicial y opciones
        """
        # Verificar si el usuario ya tiene preferencias
        user_pref = await crud.get_user_preference(self.user_id)
        dietary_profile = await crud.get_dietary_profile(self.user_id)
        user = await crud.get_user(self.user_id)
        
        # Inicializar con datos existentes si los hay
        if user_pref:
            self.preference_data = user_pref.dict(exclude={"id", "created_at", "updated_at"})
        
        if dietary_profile:
            self.dietary_data = dietary_profile.dict(exclude={"id", "created_at", "updated_at"})
        
        if user:
            self.user_data = {
                "budget": user.budget,
                "household_size": user.household_size,
                "restrictions": user.restrictions
            }
        
        # Avanzar al primer estado si no está en estado inicial
        if self.state == FlowState.INITIAL:
            return await self.transition_to(FlowState.DIET_TYPE)
        
        return PreferenceResponse(
            message="¡Bienvenido al registro de preferencias alimenticias! Vamos a hacerte algunas preguntas para personalizar tus recomendaciones.",
            state=self.state
        )
    
    async def process_input(self, user_input: str) -> PreferenceResponse:
        """
        Procesar la entrada del usuario y avanzar en el flujo.
        
        Args:
            user_input: Texto ingresado por el usuario
        
        Returns:
            Respuesta con el siguiente mensaje y opciones
        """
        # Normalizar entrada
        user_input = user_input.lower().strip()
        
        # Manejar respuestas según el estado actual
        if self.state == FlowState.DIET_TYPE:
            if user_input in self.DIET_TYPES or user_input == "otro":
                self.dietary_data["diet_type"] = user_input
                return await self.transition_to(FlowState.ALLERGENS)
            else:
                return PreferenceResponse(
                    message="Por favor, selecciona un tipo de dieta válido de la lista.",
                    options=self.DIET_TYPES,
                    state=self.state
                )
                
        elif self.state == FlowState.ALLERGENS:
            allergens = [a.strip() for a in user_input.split(',')]
            self.dietary_data["allergens"] = allergens
            return await self.transition_to(FlowState.INTOLERANCES)
            
        elif self.state == FlowState.INTOLERANCES:
            intolerances = [i.strip() for i in user_input.split(',')]
            self.dietary_data["intolerances"] = intolerances
            return await self.transition_to(FlowState.MEDICAL_CONDITIONS)
            
        elif self.state == FlowState.MEDICAL_CONDITIONS:
            conditions = [c.strip() for c in user_input.split(',')]
            self.dietary_data["medical_conditions"] = conditions
            return await self.transition_to(FlowState.FAVORITE_FOODS)
            
        elif self.state == FlowState.FAVORITE_FOODS:
            favorites = [f.strip() for f in user_input.split(',')]
            self.preference_data["favorite_foods"] = favorites
            return await self.transition_to(FlowState.DISLIKED_FOODS)
            
        elif self.state == FlowState.DISLIKED_FOODS:
            dislikes = [d.strip() for d in user_input.split(',')]
            self.preference_data["disliked_foods"] = dislikes
            return await self.transition_to(FlowState.CUISINES)
            
        elif self.state == FlowState.CUISINES:
            cuisines = [c.strip() for c in user_input.split(',')]
            self.preference_data["preferred_cuisines"] = cuisines
            return await self.transition_to(FlowState.COOKING_SKILL)
            
        elif self.state == FlowState.COOKING_SKILL:
            if user_input in self.COOKING_SKILL_LEVELS:
                self.preference_data["cooking_skill_level"] = user_input
                return await self.transition_to(FlowState.COOKING_FREQUENCY)
            else:
                return PreferenceResponse(
                    message="Por favor, selecciona un nivel de habilidad válido.",
                    options=self.COOKING_SKILL_LEVELS,
                    state=self.state
                )
                
        elif self.state == FlowState.COOKING_FREQUENCY:
            if user_input in self.COOKING_FREQUENCIES or user_input in [f[:7] for f in self.COOKING_FREQUENCIES]:
                self.preference_data["cooking_frequency"] = user_input
                return await self.transition_to(FlowState.BUDGET)
            else:
                return PreferenceResponse(
                    message="Por favor, selecciona una frecuencia válida.",
                    options=self.COOKING_FREQUENCIES,
                    state=self.state
                )
                
        elif self.state == FlowState.BUDGET:
            try:
                budget = float(user_input)
                self.user_data["budget"] = budget
                return await self.transition_to(FlowState.HOUSEHOLD_SIZE)
            except ValueError:
                return PreferenceResponse(
                    message="Por favor, ingresa un número válido para tu presupuesto semanal de alimentos.",
                    state=self.state
                )
                
        elif self.state == FlowState.HOUSEHOLD_SIZE:
            try:
                household_size = int(user_input)
                self.user_data["household_size"] = household_size
                return await self.transition_to(FlowState.DIET_GOALS)
            except ValueError:
                return PreferenceResponse(
                    message="Por favor, ingresa un número válido para el tamaño de tu hogar.",
                    state=self.state
                )
                
        elif self.state == FlowState.DIET_GOALS:
            goals = [g.strip() for g in user_input.split(',')]
            self.dietary_data["diet_goals"] = goals
            return await self.transition_to(FlowState.COMPLETED)
            
        # Estado por defecto si algo no se maneja correctamente
        return PreferenceResponse(
            message="Lo siento, hubo un error procesando tu respuesta. Intenta nuevamente.",
            state=self.state
        )
    
    async def transition_to(self, new_state: FlowState) -> PreferenceResponse:
        """
        Transicionar a un nuevo estado en el flujo.
        
        Args:
            new_state: Estado al que se desea transicionar
        
        Returns:
            Respuesta con el mensaje y opciones para el nuevo estado
        """
        self.state = new_state
        
        if new_state == FlowState.DIET_TYPE:
            return PreferenceResponse(
                message="¿Qué tipo de dieta sigues habitualmente?",
                options=self.DIET_TYPES,
                state=new_state
            )
            
        elif new_state == FlowState.ALLERGENS:
            return PreferenceResponse(
                message="¿Tienes alguna alergia alimentaria? (separa múltiples alergias con comas, o escribe 'ninguno')",
                options=self.COMMON_ALLERGENS,
                state=new_state
            )
            
        elif new_state == FlowState.INTOLERANCES:
            return PreferenceResponse(
                message="¿Tienes alguna intolerancia alimentaria? (separa múltiples intolerancias con comas, o escribe 'ninguna')",
                options=self.COMMON_INTOLERANCES,
                state=new_state
            )
            
        elif new_state == FlowState.MEDICAL_CONDITIONS:
            return PreferenceResponse(
                message="¿Tienes alguna condición médica que afecte tu alimentación? (separa múltiples condiciones con comas, o escribe 'ninguna')",
                options=self.COMMON_MEDICAL_CONDITIONS,
                state=new_state
            )
            
        elif new_state == FlowState.FAVORITE_FOODS:
            return PreferenceResponse(
                message="¿Cuáles son tus alimentos favoritos? (separa múltiples alimentos con comas)",
                state=new_state
            )
            
        elif new_state == FlowState.DISLIKED_FOODS:
            return PreferenceResponse(
                message="¿Hay alimentos que no te gusten o prefieras evitar? (separa múltiples alimentos con comas, o escribe 'ninguno')",
                state=new_state
            )
            
        elif new_state == FlowState.CUISINES:
            return PreferenceResponse(
                message="¿Qué tipos de cocina te gustan? (separa múltiples cocinas con comas)",
                options=self.CUISINE_TYPES,
                state=new_state
            )
            
        elif new_state == FlowState.COOKING_SKILL:
            return PreferenceResponse(
                message="¿Cómo describirías tu nivel de habilidad en la cocina?",
                options=self.COOKING_SKILL_LEVELS,
                state=new_state
            )
            
        elif new_state == FlowState.COOKING_FREQUENCY:
            return PreferenceResponse(
                message="¿Con qué frecuencia cocinas en casa?",
                options=self.COOKING_FREQUENCIES,
                state=new_state
            )
            
        elif new_state == FlowState.BUDGET:
            return PreferenceResponse(
                message="¿Cuál es tu presupuesto semanal aproximado para alimentos? (ingresa solo el número)",
                state=new_state
            )
            
        elif new_state == FlowState.HOUSEHOLD_SIZE:
            return PreferenceResponse(
                message="¿Cuántas personas hay en tu hogar? (ingresa solo el número)",
                state=new_state
            )
            
        elif new_state == FlowState.DIET_GOALS:
            return PreferenceResponse(
                message="¿Tienes algún objetivo dietético específico? (separa múltiples objetivos con comas, o escribe 'ninguno')",
                options=self.DIET_GOALS,
                state=new_state
            )
            
        elif new_state == FlowState.COMPLETED:
            # Guardar todos los datos recopilados
            await self.save_preferences()
            
            return PreferenceResponse(
                message="¡Gracias! Hemos guardado tus preferencias alimenticias. Ahora podremos ofrecerte recomendaciones más personalizadas.",
                completed=True,
                state=new_state
            )
            
        # Estado por defecto
        return PreferenceResponse(
            message="Continuemos con el registro de tus preferencias.",
            state=new_state
        )
    
    async def save_preferences(self) -> Tuple[bool, bool, bool]:
        """
        Guardar todas las preferencias recopiladas en la base de datos.
        
        Returns:
            Tupla con éxito de guardado (preferencias, dietario, usuario)
        """
        preference_success = False
        dietary_success = False
        user_success = False
        
        # Guardar preferencias
        if self.preference_data:
            self.preference_data["user_id"] = self.user_id
            preference_create = UserPreferenceCreate(**self.preference_data)
            preference_result = await crud.create_user_preference(preference_create)
            preference_success = preference_result is not None
        
        # Guardar perfil dietético
        if self.dietary_data:
            self.dietary_data["user_id"] = self.user_id
            dietary_create = DietaryProfileCreate(**self.dietary_data)
            dietary_result = await crud.create_dietary_profile(dietary_create)
            dietary_success = dietary_result is not None
        
        # Actualizar datos del usuario
        if self.user_data:
            user_result = await crud.update_user(self.user_id, self.user_data)
            user_success = user_result is not None
        
        return (preference_success, dietary_success, user_success)

    @classmethod
    async def from_session(cls, user_id: UUID, session_id: UUID) -> 'PreferenceFlow':
        """
        Cargar un flujo de preferencias desde una sesión existente.
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
            
        Returns:
            Instancia de PreferenceFlow con el estado recuperado o nueva si no existe
        """
        # Crear una instancia inicial
        flow = cls(user_id)
        
        # Intentar obtener la sesión
        session = await crud.get_session(session_id)
        if not session or not session.is_active:
            # Si no hay sesión activa, iniciar un nuevo flujo
            await flow.start()
            return flow
        
        # Buscar el estado del flujo en los datos almacenados en la sesión
        session_data = session.token or "{}"  # Usar el campo token para almacenar datos (en un entorno real habría un campo específico)
        try:
            session_data_dict = json.loads(session_data)
            flow_state_data = session_data_dict.get(PREFERENCE_FLOW_STATE_KEY)
            
            if flow_state_data:
                # Recuperar el estado del flujo
                flow.state = FlowState(flow_state_data.get("state", FlowState.INITIAL))
                flow.preference_data = flow_state_data.get("preference_data", {})
                flow.dietary_data = flow_state_data.get("dietary_data", {})
                flow.user_data = flow_state_data.get("user_data", {})
                
                # Si ya se completó el flujo, iniciar uno nuevo
                if flow.state == FlowState.COMPLETED:
                    flow.state = FlowState.INITIAL
                    await flow.start()
            else:
                # Iniciar un nuevo flujo si no hay datos
                await flow.start()
                
        except (json.JSONDecodeError, ValueError):
            # Si hay error al decodificar, iniciar un nuevo flujo
            await flow.start()
            
        return flow
    
    async def save_to_session(self, session_id: UUID) -> bool:
        """
        Guardar el estado actual del flujo en la sesión.
        
        Args:
            session_id: ID de la sesión donde guardar
            
        Returns:
            True si se guardó correctamente, False en caso contrario
        """
        # Obtener la sesión
        session = await crud.get_session(session_id)
        if not session or not session.is_active:
            return False
        
        # Preparar los datos a guardar
        flow_state_data = {
            "state": self.state,
            "preference_data": self.preference_data,
            "dietary_data": self.dietary_data,
            "user_data": self.user_data
        }
        
        # Cargar los datos existentes o crear nuevos
        try:
            session_data = session.token or "{}"
            session_data_dict = json.loads(session_data)
        except json.JSONDecodeError:
            session_data_dict = {}
            
        # Actualizar con el nuevo estado
        session_data_dict[PREFERENCE_FLOW_STATE_KEY] = flow_state_data
        
        # Guardar en la sesión
        new_session_data = json.dumps(session_data_dict)
        updated_session = await crud.update_session(
            session_id, 
            {"token": new_session_data}  # Usar el campo token para almacenar datos
        )
        
        return updated_session is not None


# Funciones auxiliares
async def get_preference_flow(user_id: UUID, session_id: Optional[UUID] = None) -> PreferenceFlow:
    """
    Obtener una instancia de flujo de preferencias para un usuario.
    Si se proporciona session_id, intenta recuperar el estado desde la sesión.
    
    Args:
        user_id: ID del usuario
        session_id: ID de la sesión (opcional)
        
    Returns:
        Instancia de PreferenceFlow inicializada
    """
    if session_id:
        # Intentar cargar desde la sesión
        flow = await PreferenceFlow.from_session(user_id, session_id)
    else:
        # Crear nuevo flujo
        flow = PreferenceFlow(user_id)
        await flow.start()
        
    return flow


async def save_preference_flow(flow: PreferenceFlow, session_id: UUID) -> bool:
    """
    Guardar el estado de un flujo de preferencias en una sesión.
    
    Args:
        flow: Instancia de PreferenceFlow a guardar
        session_id: ID de la sesión donde guardar
        
    Returns:
        True si se guardó correctamente, False en caso contrario
    """
    return await flow.save_to_session(session_id) 