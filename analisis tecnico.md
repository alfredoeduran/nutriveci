# Análisis Técnico de NutriVeci Bot

## Introducción

NutriVeci es un bot de Telegram diseñado para proporcionar información nutricional, recomendaciones de recetas, y asistencia personalizada para la alimentación saludable. Este documento proporciona un análisis técnico detallado de la arquitectura y los componentes de software utilizados para ejecutar la aplicación `nutriveci_bot.py`.

## Estructura General del Proyecto

El proyecto está organizado en una arquitectura modular con los siguientes directorios principales:

```
backend/
  ├── ai/             # Componentes de inteligencia artificial
  │   ├── nlp/        # Procesamiento de lenguaje natural
  │   └── vision/     # Análisis de imágenes
  ├── bot/            # Archivos relacionados con el bot de Telegram
  ├── db/             # Interacción con bases de datos
  ├── api/            # API RESTful para servicios web
  └── main.py         # Punto de entrada para la API backend
```

## 1. Componentes Principales

### 1.1. Bot de Telegram (`backend/bot/`)

#### `nutriveci_bot.py`
El archivo principal del bot que integra todos los componentes y maneja la interacción con los usuarios a través de Telegram. Tiene más de 4000 líneas de código y contiene:

- Clase `ExtendedGeminiFoodProcessor`: Extiende la funcionalidad base del procesador de alimentos para incluir traducciones, análisis de textos y generación de información nutricional.
- Handlers para comandos de Telegram (/start, /menu, /help, etc.)
- Sistema de menús interactivos usando InlineKeyboardMarkup
- Procesadores para textos y fotos de alimentos
- Manejo de conversaciones mediante estados (ConversationHandler)
- Funcionalidades para recetas, recomendaciones, y perfiles de usuario

#### `food_processor.py`
Contiene la implementación de `ExtendedGeminiFoodProcessor`, una clase que extiende `GeminiFoodProcessor` con métodos adicionales para:

- Traducción de texto entre inglés y español
- Verificación si un texto se refiere a un alimento
- Extracción de nombres de alimentos de un texto
- Consulta de información nutricional
- Carga de datos desde USDA
- Generación de descripciones de alimentos

#### `telegram_handlers.py`
Define los manejadores básicos para comandos de Telegram como `/start`, `/menu`, y `/help`.

#### `recipe_manager.py`
Proporciona funcionalidades para:

- Gestionar datos de usuarios
- Guardar y cargar recetas en formato JSON
- Cargar recetas almacenadas localmente

#### `retry_handler.py`
Implementa la clase `RetryHandler` para manejar reintentos con espera exponencial cuando ocurren errores de red en las comunicaciones con Telegram.

#### `imghdr.py`
Módulo personalizado para la detección de tipos de imágenes, necesario para python-telegram-bot.

### 1.2. Inteligencia Artificial (`backend/ai/`)

#### `nlp/gemini_food_processor.py`
Procesador de alimentos basado en Google Gemini (IA generativa) para:

- Extraer nombres de alimentos de texto
- Obtener información nutricional
- Enriquecer datos nutricionales mediante generación de texto
- Integrar resultados de visión

#### `vision/food_detector_fixed.py`
Utiliza la API de Clarifai para detectar alimentos en imágenes:

- Analiza imágenes para identificar alimentos
- Proporciona puntuaciones de confianza para las detecciones
- Ofrece implementaciones sincrónicas y asincrónicas

#### `recommendation.py`
Sistema de recomendación para sugerir recetas basadas en:

- Historial de usuario
- Perfil nutricional
- Similitud entre recetas

#### `integrator.py`
Integra la información de diferentes fuentes para proporcionar respuestas coherentes.

### 1.3. Base de Datos (`backend/db/`)

#### `recipes.py`
Funciones asincrónicas para operaciones con recetas:

- Crear recetas
- Añadir ingredientes a recetas
- Obtener recetas por ID
- Consultar recetas de usuario
- Registrar interacciones con recetas
- Buscar recetas

#### `supabase.py`
Cliente para interactuar con Supabase, una alternativa a Firebase basada en PostgreSQL.

#### `models.py`
Define los modelos de datos para la aplicación.

#### `crud.py`
Operaciones CRUD (Crear, Leer, Actualizar, Eliminar) para diferentes entidades.

### 1.4. API (`backend/api/`)

#### Rutas definidas en `main.py`:
- `/api/users`
- `/api/auth`
- `/api/preferences`
- `/api/ingredients`
- `/api/recipes`
- `/api/admin`
- `/api/nlp`

## 2. Flujo de Ejecución

1. **Inicialización del Bot**:
   - Se cargan variables de entorno de `.env`
   - Se inicializan componentes como el detector de alimentos y el procesador de alimentos
   - Se configuran los handlers de Telegram

2. **Interacción con el Usuario**:
   - El usuario envía mensajes o comandos al bot
   - El sistema de ConversationHandler gestiona el estado de la conversación
   - Se muestran menús interactivos mediante botones inline

3. **Procesamiento de Alimentos**:
   - Cuando el usuario envía texto, se analiza utilizando NLP para identificar alimentos
   - Si envía fotos, se utiliza visión por computadora para detectar alimentos
   - Los resultados se enriquecen con información nutricional

4. **Gestión de Recetas**:
   - Los usuarios pueden solicitar, buscar y guardar recetas
   - El sistema de recomendación sugiere recetas relevantes
   - Las recetas se almacenan en Supabase y localmente

## 3. Tecnologías Utilizadas

### 3.1. Frameworks y Bibliotecas

- **Python-Telegram-Bot**: Framework para crear bots de Telegram
- **FastAPI**: Framework web para la API REST
- **Google Gemini**: Modelo de IA generativa para NLP
- **Clarifai**: API de visión por computadora para detección de alimentos
- **Supabase**: Base de datos en la nube basada en PostgreSQL
- **asyncio**: Para operaciones asincrónicas

### 3.2. Servicios Externos

- **Telegram Bot API**: Para la interfaz de usuario del bot
- **Google AI (Gemini)**: Para procesamiento de lenguaje natural avanzado
- **Clarifai API**: Para análisis de imágenes y detección de alimentos
- **Supabase**: Como base de datos principal

## 4. Dependencias y Configuración

El archivo `requirements.txt` en el directorio `backend/` contiene todas las dependencias Python necesarias para ejecutar el bot.

Variables de entorno requeridas:
- `TELEGRAM_BOT_TOKEN`: Token para el bot de Telegram
- `GOOGLE_API_KEY`: Clave API para acceder a Google Gemini
- `CLARIFAI_PAT`: Token de acceso personal para Clarifai
- `SUPABASE_URL` y `SUPABASE_KEY`: Credenciales para Supabase
- `API_BASE_URL`: URL base para la API (por defecto http://localhost:8000)

## 5. Ejecución

El archivo `nutriveci_bot.py` contiene una función `main()` que configura y ejecuta el bot. La ejecución típica sería:

```python
if __name__ == "__main__":
    main()
```

## 6. Consideraciones Adicionales

- **Procesamiento multimodal**: El bot puede procesar tanto texto como imágenes
- **Arquitectura híbrida**: Combina operaciones sincrónicas y asincrónicas
- **Respaldo local**: Datos críticos se almacenan tanto en la nube como localmente
- **Sistema de reintentos**: Manejo robusto de errores de red con reintentos exponenciales
- **Traducción incorporada**: Procesamiento bilingüe español-inglés

## Conclusión

NutriVeci es un bot de Telegram sofisticado que combina múltiples tecnologías de IA (NLP y visión por computadora) con una base de datos robusta para ofrecer asistencia nutricional personalizada. Su arquitectura modular facilita la extensión y mantenimiento del código, permitiendo agregar nuevas funcionalidades de manera eficiente. 