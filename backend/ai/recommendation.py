"""
Sistema de recomendación personalizado para NutriVeci
Utiliza Collaborative Filtering con SVD para recomendar recetas adaptadas a los usuarios
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from surprise import Dataset, Reader, SVD
    from surprise.model_selection import train_test_split
except ImportError:
    logger.warning("La biblioteca Surprise no está instalada. Ejecuta 'pip install scikit-surprise' para habilitar el sistema de recomendación.")

# Agregar raíz del proyecto al path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ROOT_DIR))
DATA_PATH = os.path.join(ROOT_DIR, "data")

class RecipeRecommender:
    """Sistema de recomendación de recetas personalizado"""
    
    def __init__(self):
        self.model = None
        self.recipe_df = None
        self.interactions_df = None
        self.user_profiles = {}
        self.is_initialized = False
        self.has_surprise = 'surprise' in sys.modules
        
        # Intentar cargar datos iniciales
        try:
            self._load_recipe_data()
            self._load_user_interactions()
            
            if self.has_surprise and not self.interactions_df.empty:
                self._train_model()
                self.is_initialized = True
                logger.info("Sistema de recomendación inicializado correctamente")
            else:
                if not self.has_surprise:
                    logger.warning("Sistema de recomendación en modo limitado: Surprise no instalado")
                else:
                    logger.warning("Sistema de recomendación en modo limitado: No hay suficientes datos de interacción")
        except Exception as e:
            logger.error(f"Error inicializando el sistema de recomendación: {str(e)}")
    
    def _load_recipe_data(self):
        """Carga datos de recetas desde Food.com y memoria local"""
        # Ruta al dataset de Food.com
        foodcom_path = os.path.join(DATA_PATH, "processed", "foodcom_recipes.csv")
        memory_path = os.path.join(DATA_PATH, "processed", "memory_recetas.json")
        
        recipes = []
        
        # Cargar recetas de Food.com si existe
        if os.path.exists(foodcom_path):
            try:
                # Cargar una muestra del dataset para no consumir demasiada memoria
                foodcom_df = pd.read_csv(foodcom_path, nrows=1000)
                # Extraer columnas relevantes
                for _, row in foodcom_df.iterrows():
                    recipe = {
                        'id': f"foodcom_{row.get('id', hash(row.get('name', '')))}",
                        'name': row.get('name', 'Sin nombre'),
                        'description': row.get('description', ''),
                        'ingredients': eval(row.get('ingredients', '[]')) if isinstance(row.get('ingredients'), str) else [],
                        'steps': eval(row.get('steps', '[]')) if isinstance(row.get('steps'), str) else [],
                        'source': 'foodcom',
                        # Metadatos para filtrado
                        'calories': row.get('calories', 0),
                        'total_fat': row.get('total_fat', 0),
                        'sugar': row.get('sugar', 0),
                        'sodium': row.get('sodium', 0),
                        'protein': row.get('protein', 0),
                        'carbohydrates': row.get('carbohydrates', 0),
                        'difficulty': 'medium', # Valor predeterminado
                        'tags': [],
                    }
                    recipes.append(recipe)
                logger.info(f"Cargadas {len(recipes)} recetas de Food.com")
            except Exception as e:
                logger.error(f"Error cargando recetas de Food.com: {str(e)}")
        
        # Cargar recetas de memoria local si existe
        if os.path.exists(memory_path):
            try:
                with open(memory_path, 'r', encoding='utf-8') as f:
                    memory_recipes = json.load(f)
                
                # Añadir recetas de memoria local
                for recipe in memory_recipes:
                    # Verificar que tenga ID
                    if 'id' not in recipe:
                        recipe['id'] = f"local_{hash(recipe.get('name', ''))}"
                    else:
                        recipe['id'] = f"local_{recipe['id']}"
                    
                    # Añadir metadatos para filtrado si no existen
                    if 'calories' not in recipe:
                        recipe['calories'] = 0
                    if 'protein' not in recipe:
                        recipe['protein'] = 0
                    if 'carbohydrates' not in recipe:
                        recipe['carbohydrates'] = 0
                    if 'total_fat' not in recipe:
                        recipe['total_fat'] = 0
                    if 'difficulty' not in recipe:
                        recipe['difficulty'] = 'medium'
                    if 'tags' not in recipe:
                        recipe['tags'] = []
                    
                    recipes.append(recipe)
                
                logger.info(f"Cargadas {len(memory_recipes)} recetas de memoria local")
            except Exception as e:
                logger.error(f"Error cargando recetas de memoria local: {str(e)}")
        
        # Crear DataFrame con todas las recetas
        if recipes:
            self.recipe_df = pd.DataFrame(recipes)
            logger.info(f"Total de recetas cargadas: {len(self.recipe_df)}")
        else:
            # Crear DataFrame vacío si no hay recetas
            self.recipe_df = pd.DataFrame(columns=['id', 'name', 'description', 'ingredients', 'steps', 'source',
                                                   'calories', 'total_fat', 'sugar', 'sodium', 'protein', 
                                                   'carbohydrates', 'difficulty', 'tags'])
            logger.warning("No se encontraron recetas para cargar")
    
    def _load_user_interactions(self):
        """Carga las interacciones de los usuarios con recetas desde el histórico"""
        # Archivo para almacenar interacciones (crear si no existe)
        interactions_path = os.path.join(DATA_PATH, "processed", "user_recipe_interactions.csv")
        
        if os.path.exists(interactions_path):
            try:
                self.interactions_df = pd.read_csv(interactions_path)
                logger.info(f"Cargadas {len(self.interactions_df)} interacciones de usuarios")
            except Exception as e:
                logger.error(f"Error cargando interacciones: {str(e)}")
                self.interactions_df = pd.DataFrame(columns=['user_id', 'recipe_id', 'rating', 'timestamp'])
        else:
            # Crear DataFrame vacío si no existe el archivo
            self.interactions_df = pd.DataFrame(columns=['user_id', 'recipe_id', 'rating', 'timestamp'])
            self.interactions_df.to_csv(interactions_path, index=False)
            logger.info("Creado nuevo archivo de interacciones de usuarios")
    
    def _train_model(self):
        """Entrena el modelo de recomendación SVD con los datos disponibles"""
        if not self.has_surprise:
            logger.warning("No se puede entrenar el modelo: Surprise no está instalado")
            return
        
        if len(self.interactions_df) < 10:
            logger.warning("No hay suficientes datos para entrenar un modelo de recomendación")
            return
        
        try:
            # Preparar datos para Surprise
            reader = Reader(rating_scale=(0, 1))
            data = Dataset.load_from_df(self.interactions_df[['user_id', 'recipe_id', 'rating']], reader)
            
            # Entrenar modelo SVD
            trainset = data.build_full_trainset()
            self.model = SVD(n_factors=20, n_epochs=10)
            self.model.fit(trainset)
            
            logger.info("Modelo de recomendación entrenado correctamente")
        except Exception as e:
            logger.error(f"Error entrenando modelo de recomendación: {str(e)}")
    
    def add_user_interaction(self, user_id, recipe_id, rating=1.0):
        """
        Registra una interacción de usuario con una receta
        
        Args:
            user_id: ID del usuario
            recipe_id: ID de la receta
            rating: Valoración (0.5=vista, 1.0=guardada/favorita)
        """
        import datetime
        
        # Convertir IDs a string
        user_id = str(user_id)
        recipe_id = str(recipe_id)
        
        # Añadir interacción al DataFrame
        new_interaction = pd.DataFrame({
            'user_id': [user_id],
            'recipe_id': [recipe_id],
            'rating': [rating],
            'timestamp': [datetime.datetime.now().isoformat()]
        })
        
        self.interactions_df = pd.concat([self.interactions_df, new_interaction], ignore_index=True)
        
        # Guardar interacciones
        interactions_path = os.path.join(DATA_PATH, "processed", "user_recipe_interactions.csv")
        self.interactions_df.to_csv(interactions_path, index=False)
        
        # Reentrenar modelo si hay suficientes datos
        if len(self.interactions_df) >= 10 and self.has_surprise:
            self._train_model()
            self.is_initialized = True
        
        logger.info(f"Registrada interacción de usuario {user_id} con receta {recipe_id}")
    
    def set_user_profile(self, user_id, profile_data):
        """
        Establece o actualiza el perfil de un usuario para filtrado de recomendaciones
        
        Args:
            user_id: ID del usuario
            profile_data: Diccionario con datos del perfil (edad, peso, sexo, patologías, etc.)
        """
        # Convertir ID a string
        user_id = str(user_id)
        
        # Almacenar perfil
        self.user_profiles[user_id] = profile_data
        
        # Guardar perfiles en archivo
        profiles_path = os.path.join(DATA_PATH, "processed", "user_profiles.json")
        try:
            # Cargar perfiles existentes
            profiles = {}
            if os.path.exists(profiles_path):
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
            
            # Actualizar perfil
            profiles[user_id] = profile_data
            
            # Guardar perfiles
            with open(profiles_path, 'w', encoding='utf-8') as f:
                json.dump(profiles, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Perfil de usuario {user_id} actualizado correctamente")
        except Exception as e:
            logger.error(f"Error guardando perfil de usuario: {str(e)}")
    
    def get_user_profile(self, user_id):
        """
        Obtiene el perfil de un usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            dict: Datos del perfil o diccionario vacío si no existe
        """
        # Convertir ID a string
        user_id = str(user_id)
        
        # Verificar si existe en memoria
        if user_id in self.user_profiles:
            return self.user_profiles[user_id]
        
        # Intentar cargar desde archivo
        profiles_path = os.path.join(DATA_PATH, "processed", "user_profiles.json")
        if os.path.exists(profiles_path):
            try:
                with open(profiles_path, 'r', encoding='utf-8') as f:
                    profiles = json.load(f)
                
                if user_id in profiles:
                    # Guardar en memoria para futuros accesos
                    self.user_profiles[user_id] = profiles[user_id]
                    return profiles[user_id]
            except Exception as e:
                logger.error(f"Error cargando perfil de usuario: {str(e)}")
        
        # Si no existe, devolver diccionario vacío
        return {}
    
    def recommend_recipes(self, user_id, n=5, filter_by_profile=True):
        """
        Recomienda recetas para un usuario
        
        Args:
            user_id: ID del usuario
            n: Número de recetas a recomendar
            filter_by_profile: Si se deben filtrar las recetas según el perfil del usuario
            
        Returns:
            list: Lista de diccionarios con información de las recetas recomendadas
        """
        # Convertir ID a string
        user_id = str(user_id)
        
        # Verificar si hay recetas
        if self.recipe_df is None or len(self.recipe_df) == 0:
            logger.warning("No hay recetas disponibles para recomendar")
            return []
        
        # Obtener recetas que el usuario ha visto
        user_recipes = []
        if not self.interactions_df.empty:
            user_recipes = self.interactions_df[self.interactions_df['user_id'] == user_id]['recipe_id'].unique()
        
        # Si tiene pocas interacciones, recomendar recetas populares o aleatorias
        if (not self.is_initialized or not self.has_surprise) or len(user_recipes) < 3:
            logger.info(f"Usando recomendación basada en popularidad/filtros para usuario {user_id}")
            return self._recommend_without_model(user_id, n, filter_by_profile)
        
        try:
            # Obtener todas las recetas que el usuario no ha visto
            all_recipes = self.recipe_df['id'].unique()
            unseen_recipes = np.setdiff1d(all_recipes, user_recipes)
            
            if len(unseen_recipes) == 0:
                return self._recommend_without_model(user_id, n, filter_by_profile)
            
            # Filtrar recetas por perfil del usuario si es necesario
            filtered_recipes = unseen_recipes
            if filter_by_profile:
                filtered_recipes = self._filter_by_profile(user_id, unseen_recipes)
                
                if len(filtered_recipes) == 0:
                    logger.warning(f"No hay recetas que cumplan con el perfil del usuario {user_id}")
                    # Usar recetas sin filtrar si no hay coincidencias
                    filtered_recipes = unseen_recipes
            
            # Predecir ratings para recetas no vistas
            predictions = []
            for recipe_id in filtered_recipes:
                try:
                    pred = self.model.predict(user_id, recipe_id)
                    predictions.append(pred)
                except Exception as e:
                    logger.error(f"Error prediciendo rating para receta {recipe_id}: {str(e)}")
            
            # Ordenar por predicción y obtener top N
            predictions.sort(key=lambda x: x.est, reverse=True)
            top_recipe_ids = [pred.iid for pred in predictions[:n]]
            
            # Obtener información completa de las recetas
            recommended_recipes = []
            for recipe_id in top_recipe_ids:
                recipe_info = self.recipe_df[self.recipe_df['id'] == recipe_id].to_dict('records')
                if recipe_info:
                    recommended_recipes.append(recipe_info[0])
            
            logger.info(f"Recomendadas {len(recommended_recipes)} recetas para usuario {user_id} usando collaborative filtering")
            return recommended_recipes
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones con modelo: {str(e)}")
            # Fallback a recomendación sin modelo
            return self._recommend_without_model(user_id, n, filter_by_profile)
    
    def _recommend_without_model(self, user_id, n=5, filter_by_profile=True):
        """
        Recomienda recetas sin usar el modelo (para nuevos usuarios o cuando el modelo no está disponible)
        
        Args:
            user_id: ID del usuario
            n: Número de recetas a recomendar
            filter_by_profile: Si se deben filtrar las recetas según el perfil del usuario
            
        Returns:
            list: Lista de diccionarios con información de las recetas recomendadas
        """
        # Obtener recetas que el usuario ha visto
        user_recipes = []
        if not self.interactions_df.empty:
            user_recipes = self.interactions_df[self.interactions_df['user_id'] == user_id]['recipe_id'].unique()
        
        # Filtrar recetas que el usuario no ha visto
        recipes_df = self.recipe_df[~self.recipe_df['id'].isin(user_recipes)].copy()
        
        # Si no quedan recetas, devolver lista vacía
        if len(recipes_df) == 0:
            return []
        
        # Filtrar por perfil del usuario si es necesario
        if filter_by_profile:
            recipes_df = self._filter_by_profile_df(user_id, recipes_df)
            
            # Si no quedan recetas después del filtrado, usar todas las no vistas
            if len(recipes_df) == 0:
                recipes_df = self.recipe_df[~self.recipe_df['id'].isin(user_recipes)].copy()
        
        # Obtener recetas más populares
        if not self.interactions_df.empty:
            # Calcular popularidad basada en interacciones
            popularity = self.interactions_df.groupby('recipe_id').count()['user_id'].reset_index()
            popularity.columns = ['id', 'popularity']
            
            # Unir con recetas disponibles
            recipes_df = recipes_df.merge(popularity, on='id', how='left')
            recipes_df['popularity'].fillna(0, inplace=True)
            
            # Ordenar por popularidad
            recipes_df.sort_values('popularity', ascending=False, inplace=True)
        else:
            # Si no hay datos de interacción, ordenar aleatoriamente
            recipes_df = recipes_df.sample(frac=1).reset_index(drop=True)
        
        # Obtener top N recetas
        top_recipes = recipes_df.head(n).to_dict('records')
        
        logger.info(f"Recomendadas {len(top_recipes)} recetas para usuario {user_id} usando popularidad/filtros")
        return top_recipes
    
    def _filter_by_profile(self, user_id, recipe_ids):
        """
        Filtra recetas según el perfil del usuario
        
        Args:
            user_id: ID del usuario
            recipe_ids: Lista de IDs de recetas a filtrar
            
        Returns:
            list: Lista de IDs de recetas filtradas
        """
        # Obtener perfiles para filtrado
        profile = self.get_user_profile(user_id)
        
        if not profile:
            return recipe_ids
        
        # Filtrar recetas que coincidan con el perfil
        filtered_df = self.recipe_df[self.recipe_df['id'].isin(recipe_ids)].copy()
        
        # Aplicar filtros según el perfil
        if filtered_df.empty:
            return recipe_ids
        
        return self._filter_by_profile_df(user_id, filtered_df)['id'].tolist()
    
    def _filter_by_profile_df(self, user_id, recipes_df):
        """
        Filtra DataFrame de recetas según el perfil del usuario
        
        Args:
            user_id: ID del usuario
            recipes_df: DataFrame de recetas a filtrar
            
        Returns:
            DataFrame: DataFrame filtrado
        """
        # Obtener perfiles para filtrado
        profile = self.get_user_profile(user_id)
        
        if not profile or recipes_df.empty:
            return recipes_df
        
        # Filtrar según patologías/alergias
        if 'patologias' in profile and profile['patologias']:
            filtered_df = recipes_df.copy()
            
            # Filtrar por hipertensión (menos sodio)
            if 'hipertension' in profile['patologias'] or 'presion alta' in profile['patologias']:
                # Filtrar recetas con bajo contenido de sodio
                if 'sodium' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['sodium'] < 500]
            
            # Filtrar por diabetes (menos azúcar)
            if 'diabetes' in profile['patologias']:
                # Filtrar recetas con bajo contenido de azúcar
                if 'sugar' in filtered_df.columns:
                    filtered_df = filtered_df[filtered_df['sugar'] < 10]
            
            # Filtrar por alergias
            if 'alergias' in profile and profile['alergias']:
                # Para cada alergia, filtrar recetas que no contengan ese ingrediente
                for alergia in profile['alergias']:
                    # Filtrar por ingredientes (campo es una lista de strings)
                    filtered_df = filtered_df[filtered_df['ingredients'].apply(
                        lambda x: not any(alergia.lower() in ing.lower() for ing in x if isinstance(ing, str))
                    )]
            
            # Si no quedan recetas después del filtrado, usar recetas originales
            if filtered_df.empty:
                logger.warning(f"No hay recetas que cumplan con todas las restricciones para usuario {user_id}")
                return recipes_df
            
            recipes_df = filtered_df
        
        # Filtrar por nivel de dificultad (basado en la edad)
        if 'edad' in profile:
            try:
                edad = int(profile['edad'])
                if edad > 65:
                    # Para adultos mayores, recomendar recetas más sencillas
                    recetas_faciles = recipes_df[recipes_df['difficulty'] != 'hard'].copy()
                    if not recetas_faciles.empty:
                        recipes_df = recetas_faciles
            except:
                pass
        
        return recipes_df

# Crear instancia global
recommender = RecipeRecommender()

def get_recommender():
    """
    Obtiene la instancia global del recomendador
    
    Returns:
        RecipeRecommender: Instancia del recomendador
    """
    return recommender

# Método para reentrenar el modelo bajo demanda
def retrain_model():
    """
    Reentrenar el modelo de recomendación con los datos actualizados
    
    Returns:
        bool: True si se reentrenó correctamente, False en caso contrario
    """
    try:
        recommender._load_recipe_data()
        recommender._load_user_interactions()
        recommender._train_model()
        return True
    except Exception as e:
        logger.error(f"Error reentrenando modelo: {str(e)}")
        return False 