# NutriVeci - Estructura del Proyecto

Este documento explica la función principal de cada carpeta en el proyecto NutriVeci, un asistente nutricional basado en chatbot con inteligencia artificial.

## Estructura de Directorios Raíz

### 📁 .venv/ y venv/
- **Función**: Entornos virtuales de Python que contienen las dependencias aisladas del proyecto, asegurando compatibilidad y reproducibilidad del entorno de desarrollo.

### 📁 .git/
- **Función**: Directorio de control de versiones Git, mantiene el historial de cambios y permite la colaboración entre desarrolladores.

### 📁 docs/
- **Función**: Almacena toda la documentación del proyecto, incluyendo planes de desarrollo, esquemas, guías técnicas y contexto general del proyecto.
  - `contexto.md`: Describe la estructura y componentes del proyecto NutriVeci.
  - `development_plan.md`: Detalla las fases y tareas de desarrollo del proyecto.
  - `schema.md`: Proporciona la estructura general del proyecto y sus componentes.
  - `context.md`: Explica el flujo y características de la aplicación, incluyendo tecnologías sugeridas.
  - `pasoapaso.md`: Guía paso a paso para ejecutar el chat web con el modelo de lenguaje.
  - `supabase-schema-lylyodfxokhlpaxtctou.png`: Representación visual del esquema de la base de datos.

### 📁 backend/
- **Función**: Contiene todo el código del servidor, la lógica del chatbot, integración con IA y manejo de base de datos.
  - `api/`: Endpoints de la API HTTP para comunicación con el frontend y webhooks de Telegram.
  - `bot/`: Implementación principal de la lógica del chatbot y manejo de conversaciones.
  - `bots/`: Módulos o extensiones de habilidades específicas del bot.
  - `core/`: Lógica de negocio principal como cálculos nutricionales y funcionalidades compartidas.
  - `db/`: Código relacionado con la base de datos, modelos ORM y consultas.
  - `ai/`: Componentes de IA para interactuar con modelos de lenguaje y APIs de visión.
  - `schemas/`: Definición de estructuras de datos para validación y serialización.
  - `logging/`: Configuración y gestión de registros de eventos.
  - `__pycache__/`: Caché de Python (automáticamente generado).
  - `main.py`: Punto de entrada principal de la aplicación backend.
  - `requirements.txt`: Dependencias específicas del backend.

### 📁 frontend/
- **Función**: Contiene la aplicación React para la interfaz de usuario web.
  - `src/`: Código fuente principal de la aplicación React.
    - `components/`: Componentes reutilizables de la interfaz (chatbox, formularios, etc).
    - `services/`: Servicios para comunicación con el Backend API.
    - `utils/`: Funciones de utilidad específicas del frontend.
  - `public/`: Archivos estáticos como HTML principal, favicon, etc.

### 📁 web/
- **Función**: Contiene archivos web adicionales o estáticos no gestionados por el frontend React.
  - `index.html`: Página principal del sitio web.
  - `main.js`: Lógica principal de JavaScript para la interfaz web.
  - `admin_panel.html` y `admin_panel.js`: Interfaz de administración.
  - `styles.css`: Estilos CSS para las páginas web.
  - `css/`: Directorio con archivos de estilos adicionales.
  - `js/`: Directorio con scripts JavaScript adicionales.

### 📁 scripts/
- **Función**: Scripts de utilidad para tareas como inicialización de base de datos, importación de datos y diagnóstico.
  - `import_foodcom_to_supabase.py`: Importa datos de Food.com a Supabase.
  - `export_recipes_to_csv.py`: Exporta recetas a formato CSV.
  - `download_foodcom_dataset.py`: Descarga el dataset de Food.com.
  - `diagnose.py`: Herramienta de diagnóstico del sistema.
  - `download_datasets.py`: Descarga datasets necesarios para el proyecto.
  - `populate_ingredients.py`: Pobla la base de datos con ingredientes.
  - `setup_db.py`: Configura la estructura inicial de la base de datos.

### 📁 tests/
- **Función**: Contiene archivos para pruebas unitarias y de integración, asegurando la calidad del código.

### 📁 data/
- **Función**: Almacenamiento de datos estáticos, datasets descargados y archivos de configuración.
  - `processed/`: Datos procesados y listos para usar.
  - `datasets/`: Datasets completos descargados.
  - `raw/`: Datos sin procesar.
  - `seed_data/`: Datos iniciales para poblar la base de datos.

### 📄 requirements.txt
- **Función**: Lista de dependencias principales de Python para el proyecto completo.

### 📄 .gitignore
- **Función**: Especifica los archivos y directorios que Git debe ignorar, como entornos virtuales y archivos de configuración sensibles.

### 📄 README.md
- **Función**: Documentación principal del proyecto, proporciona una visión general e instrucciones para comenzar.

## Flujo de Datos y Comunicación

1. El usuario interactúa con la aplicación a través del frontend web o el bot de Telegram.
2. Las solicitudes se envían al backend a través de endpoints API.
3. El backend procesa las solicitudes utilizando:
   - Componentes de IA para procesamiento de lenguaje natural
   - Base de datos para perfiles de usuario y datos nutricionales
   - Lógica de negocio para cálculos y recomendaciones
4. Las respuestas son devueltas al cliente (frontend web o bot Telegram) para presentarlas al usuario.

## Arquitectura del Sistema

NutriVeci sigue una arquitectura de tres capas:
1. **Capa de Presentación**: frontend/ y web/ (interfaces de usuario)
2. **Capa de Lógica de Negocio**: backend/ (procesamiento y lógica)
3. **Capa de Datos**: base de datos Supabase (almacenamiento persistente)

Con integración de servicios de IA para enriquecer la funcionalidad del chatbot nutricional.

## Carpetas Clave para el Bot de Telegram y Procesamiento de Datos

### Funcionamiento del Bot de Telegram

El bot de Telegram funciona principalmente mediante la interacción de estas carpetas:

1. **backend/api/**: 
   - Contiene endpoints específicos como `/telegram/webhook` que recibe las actualizaciones enviadas por la API de Telegram
   - Valida y procesa las solicitudes entrantes de Telegram, extrayendo texto, imágenes y otros datos
   - Maneja la autenticación y seguridad en la comunicación con Telegram

2. **backend/bot/**: 
   - Implementa la lógica central del chatbot para Telegram
   - Contiene manejadores para diferentes tipos de mensajes (texto, imágenes, comandos)
   - Gestiona el estado de las conversaciones para mantener contexto entre mensajes
   - Utiliza la biblioteca `python-telegram-bot` para interactuar con la API de Telegram

3. **backend/bots/**: 
   - Contiene módulos especializados para diferentes capacidades del bot
   - Implementa handlers específicos para consultas nutricionales, búsqueda de recetas, etc.
   - Permite la extensibilidad de funcionalidades sin modificar el núcleo del bot

4. **backend/schemas/**: 
   - Define estructuras de datos para validación de mensajes entrantes y salientes
   - Modela la estructura de mensajes de Telegram para garantizar consistencia

### Procesamiento de Datos en el Backend

El procesamiento de datos ocurre principalmente en estas carpetas:

1. **backend/ai/**: 
   - Es el núcleo del procesamiento inteligente de datos
   - Integra modelos de lenguaje como Gemini 1.5 Flash para interpretar consultas
   - Contiene el código para construir prompts específicos según el contexto del usuario
   - Implementa la conexión con servicios de IA externos (APIs de Hugging Face, OpenAI, etc.)
   - Procesa imágenes de alimentos mediante APIs de visión por computadora
   - Transforma los resultados de los modelos de IA en respuestas estructuradas

2. **backend/db/**: 
   - Gestiona toda la interacción con la base de datos Supabase
   - Almacena y recupera perfiles de usuario, ingredientes, recetas y restricciones alimenticias
   - Implementa consultas optimizadas para obtener información nutricional
   - Mantiene la consistencia de datos entre sesiones de usuario

3. **backend/core/**: 
   - Contiene la lógica de negocio para cálculos nutricionales
   - Implementa algoritmos para combinar ingredientes y generar recetas
   - Aplica reglas de negocio (por ejemplo, filtrar recetas según alergias o enfermedades)
   - Valida recomendaciones nutricionales antes de entregarlas al usuario

4. **backend/logging/**: 
   - Registra todas las interacciones para análisis posterior
   - Almacena consultas y respuestas para entrenar modelos futuros
   - Monitorea el rendimiento y precisión del sistema

### Flujo de Procesamiento Real

Cuando un usuario envía un mensaje al bot de Telegram, ocurre el siguiente flujo:

1. La API de Telegram envía una actualización al webhook definido en **backend/api/**
2. El controlador del webhook extrae el mensaje y lo pasa al gestor principal en **backend/bot/**
3. El gestor identifica el tipo de mensaje y lo dirige al módulo especializado en **backend/bots/**
4. Si contiene una consulta nutricional o de recetas, el sistema:
   - Recupera el perfil del usuario desde **backend/db/**
   - Envía la consulta a los modelos de IA en **backend/ai/** junto con el contexto del usuario
   - El componente de IA procesa la consulta y genera una respuesta
   - La lógica en **backend/core/** valida y enriquece la respuesta con datos nutricionales
   - El resultado se formatea apropiadamente y se envía de vuelta al usuario
5. Todo el proceso se registra en **backend/logging/** para análisis y mejora futura

Este proceso permite que el bot de Telegram proporcione recomendaciones precisas y personalizadas basadas en el procesamiento avanzado de lenguaje natural y la integración con datos nutricionales estructurados.

## Tecnologías y Modelos de IA Utilizados

### Tecnologías Principales

#### Backend
- **Python**: Lenguaje principal del backend
- **FastAPI**: Framework web para creación de APIs, elegido por su rendimiento y facilidad para documentación
- **Supabase**: Plataforma de base de datos PostgreSQL con características de autenticación y APIs ya integradas
- **Python-Telegram-Bot**: Biblioteca para interactuar con la API de Telegram
- **Uvicorn**: Servidor ASGI para ejecutar la aplicación FastAPI
- **Pydantic**: Para validación de datos y serialización
- **SQLAlchemy**: ORM (Object-Relational Mapping) para interacción con la base de datos
- **JWT**: Para autenticación y manejo de sesiones
- **Asyncio**: Para manejo de operaciones asíncronas y concurrentes
- **Dotenv**: Para gestión de variables de entorno

#### Frontend
- **React**: Biblioteca JavaScript para construir la interfaz de usuario web
- **HTML/CSS/JavaScript**: Para la interfaz web básica en la carpeta 'web'

#### Herramientas de Datos
- **Pandas**: Para procesamiento y manipulación de datasets
- **NumPy**: Para operaciones numéricas y manipulación de arrays
- **Kaggle API**: Para descargar datasets nutricionales y de recetas
- **JSON**: Para almacenamiento local de datos y configuración

### Modelos de IA Implementados

#### Procesamiento de Lenguaje Natural (NLP)
- **Gemini 1.5 Flash**: Es el modelo principal utilizado en toda la aplicación para procesamiento de lenguaje natural, incluyendo interpretación de consultas, generación de respuestas, extracción de entidades alimenticias y creación de recetas

#### Modelos de Visión por Computadora
- **Clarifai API**: Principal motor de reconocimiento de imágenes utilizado para identificar alimentos en fotos
- **Azure AI Vision**: Como alternativa para reconocimiento de alimentos en imágenes

#### Datasets Utilizados
- **USDA FoodData Central**: Dataset con información nutricional detallada de miles de alimentos, almacenado en `data/processed/usda_food_data.csv`
- **Food.com Recipes**: Dataset con recetas e ingredientes, utilizado para búsqueda y recomendación de platos, almacenado en `data/processed/foodcom_recipes.csv`
- **Memory Recipes**: Colección local de recetas generadas y guardadas, almacenada en `data/processed/memory_recetas.json`

### Flujo de Integración de IA

1. **Entrada del Usuario**: Texto o imagen recibido a través de Telegram o interfaz web
2. **Procesamiento NLP**: 
   - El texto es procesado por Gemini 1.5 Flash para extraer intenciones y entidades clave
   - Si hay una imagen, se procesa con Clarifai API para identificar alimentos
3. **Consulta a Datasets**:
   - Los alimentos identificados se buscan en el dataset USDA para obtener información nutricional
   - Para recetas, se consulta el dataset Food.com o se generan con Gemini basándose en los ingredientes
4. **Generación de Contexto**:
   - Se combina el perfil del usuario (restricciones, preferencias) con los datos extraídos
   - Se recupera información nutricional relevante de la base de datos
5. **Generación de Respuestas**:
   - Para consultas nutricionales: Gemini 1.5 Flash genera respuestas informativas con datos del USDA
   - Para recetas: Se buscan recetas similares en Food.com o se generan con Gemini
6. **Almacenamiento Local**:
   - Las recetas generadas o consultadas se guardan en el archivo memory_recetas.json
   - El historial del usuario se mantiene en memoria durante la sesión

Esta integración de tecnologías, modelos de IA y datasets permite a NutriVeci ofrecer un asistente nutricional inteligente que equilibra precisión científica con personalización, basándose en datos nutricionales verificados del USDA y recetas reales de Food.com. 