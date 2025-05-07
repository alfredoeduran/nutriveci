# NutriVeci Project - Guía para Desarrolladores sobre la Estructura y Componentes

## 1. Introducción ✅

Este documento guía a los desarrolladores a través de la estructura del proyecto NutriVeci, un asistente nutricional basado en chatbot. Explica la organización del código, la integración de componentes clave como IA y base de datos, y aborda la inclusión de interfaces como una aplicación web y un bot de Telegram, así como el uso de APIs de Visión y datasets externos.

Una estructura de proyecto bien definida es crucial para facilitar el desarrollo colaborativo, la organización del código y la futura escalabilidad y mantenimiento.

## 2. Visión General del Proyecto ✅

NutriVeci es una aplicación que busca asistir a los usuarios con información nutricional y recetas, adaptándose a sus perfiles (género, peso, altura, etc.) y restricciones (alergias, enfermedades). El proyecto consta de:

* Un **Backend** (Python/FastAPI) que actúa como API, aloja la lógica del chatbot, interactúa con la base de datos y se comunica con los modelos/servicios de Inteligencia Artificial.
* Un **Frontend Web** (React) que proporciona una interfaz de usuario web.
* Una interfaz **Bot de Telegram** que permite a los usuarios interactuar con el asistente a través de la aplicación de mensajería.
* Componentes de **Inteligencia Artificial**, incluyendo un modelo de lenguaje (como Gemini 1.5 Flash) para el manejo del lenguaje natural y la generación de texto (recetas, información) y un componente de Visión por Computadora (vía API externa o modelo propio) para el análisis de imágenes de alimentos.
* Una **Base de Datos** para persistir información de usuarios, perfiles y otros datos relevantes.

## 3. Estructura del Directorio Raíz ✅

nutriveci_proyect/
├── .venv/             # Entorno virtual de Python (recomendado)
├── venv/              # Posible entorno virtual adicional (asegurar exclusión en .gitignore)
├── .git/              # Repositorio Git para control de versiones
├── docs/              # Documentación del proyecto (planes, guías, esquemas)
├── backend/           # Código de la aplicación del Backend
├── frontend/          # Código de la aplicación del Frontend Web (Interfaz de Usuario)
├── web/               # Posibles archivos web adicionales o estáticos no gestionados por el frontend (a clarificar/consolidar)
├── scripts/           # Scripts de utilidad (ej: inicialización de DB, despliegue)
├── tests/             # Archivos para pruebas (unitarias, de integración)
├── data/              # Almacenamiento de datos estáticos, datasets descargados, archivos de configuración de datos nutricionales
├── requirements.txt   # Dependencias principales del proyecto (Python)
├── .gitignore         # Reglas para ignorar archivos en Git (incluir entornos virtuales, archivos .env, caché)
└── README.md          # Documentación principal del proyecto


* La separación de `backend/` y `frontend/` es estándar y correcta.
* `data/` es adecuado para los datasets que descargues y la información nutricional que no resida en la base de datos principal.
* Asegúrate de que `.gitignore` excluya correctamente los entornos virtuales (`.venv/`, `venv/`) y cualquier archivo de variables de entorno (`.env`).

## 4. Estructura del Backend ✅

backend/
├── api/             # Endpoints de la API HTTP (para Frontend Web y Webhooks de Telegram si aplica)
├── bot/             # Implementación principal de la lógica del chatbot (manejo de conversación, estado)
├── bots/            # Posibles módulos o extensiones de habilidades específicas del bot (ej: handlers para recetas, perfil, etc.)
├── core/            # Lógica de negocio principal y funcionalidades compartidas (ej: cálculos nutricionales)
├── db/              # Código relacionado con la base de datos (modelos ORM, migraciones, consultas)
├── schemas/         # Definición de la estructura de datos (para validación, serialización - ej: Pydantic)
├── ai/              # Componentes de Inteligencia Artificial (interacción con LLM y APIs de Visión)
├── logging/         # Configuración y manejo del registro de eventos (logs)
├── config/          # (Sugerido) Archivos de configuración, carga de variables de entorno
├── pycache/     # Caché de Python (ignorar)
├── main.py          # Punto de entrada principal de la aplicación backend (inicialización de FastAPI, middlewares, rutas)
└── requirements.txt # Dependencias específicas del backend


* **`api/`**: Aquí definirás rutas como `/web/chat` (para el frontend web), y potencialmente `/telegram/webhook` (para recibir actualizaciones de Telegram si usas este método).
* **`bot/` y `bots/`**: Contendrán la lógica para procesar los mensajes entrantes de cualquier interfaz (web o Telegram), mantener el estado del usuario, y dirigir la solicitud al módulo `ai/` o `core/` apropiado.
* **`core/`**: Funciones como cálculo de calorías basadas en el perfil, verificación de alergias contra ingredientes, etc.
* **`db/`**: Modelos de usuario, perfil nutricional, historial de conversación, recetas guardadas, etc.
* **`ai/`**: **Este directorio es fundamental y centraliza la inteligencia del bot.** Aquí se implementará:
    * La lógica para interactuar con la API de **Gemini 1.5 Flash (o el LLM elegido)**, construyendo dinámicamente los **prompts** basados en la entrada del usuario, el historial de conversación, el perfil del usuario y los resultados del análisis de imagen.
    * La lógica para integrar **APIs de Visión por Computadora (Google Cloud Vision API, Azure AI Vision, u otros)**: recibir la imagen, llamar a la API con las credenciales configuradas, parsear la respuesta para identificar alimentos y sus propiedades.
    * La **lógica de integración**: Combinar la información de alimentos detectados por visión, los datos del perfil del usuario (alergias, enfermedades) obtenidos de `db/`, y los datos nutricionales (de `db/` o `data/`) para formar el contexto completo que se enviará al LLM en el prompt.
    * Procesamiento de la respuesta del LLM para adaptarla al formato final de salida.

## 5. Estructura del Frontend Web ✅

frontend/
├── src/             # Código fuente principal de la aplicación React
│   ├── components/  # Componentes reutilizables de la UI (chatbox, formularios, visualizadores)
│   ├── services/    # Lógica para comunicarse con el Backend API (ej: llamadas a /api/web/chat)
│   ├── contexts/    # (Opcional) Contextos de React para estado global (ej: perfil de usuario, estado de carga)
│   └── utils/       # Funciones de ayuda específicas del frontend
└── public/          # Archivos estáticos (HTML principal, favicon, etc.)


* Estructura estándar de React. Los servicios (`services/`) son clave para la comunicación con el backend.

## 6. Integración de Interfaces: Frontend Web y Telegram ❌

El diseño propuesto soporta múltiples interfaces porque la lógica principal reside en el Backend.

* **Frontend Web:** Se comunica con el backend a través de los endpoints definidos en `backend/api/` (ej: `/web/chat`). La comunicación es típicamente solicitud/respuesta HTTP.
* **Telegram Bot:**
    * Se necesita una biblioteca de Python para interactuar con la API de Telegram (ej. `python-telegram-bot`).
    * Configuración: Necesitas obtener un **Token de Bot** de @BotFather en Telegram. Este token es sensible y debe gestionarse como una variable de entorno (`TELEGRAM_BOT_TOKEN`).
    * Conexión con el Backend: Hay dos métodos principales:
        * **Webhooks:** Telegram envía una solicitud HTTP a un endpoint específico de tu backend (ej. `/telegram/webhook`) cada vez que hay una actualización (mensaje nuevo, foto, etc.). Tu backend recibe esta solicitud, procesa la actualización usando la lógica del bot, y usa la API de Telegram (via la biblioteca Python) para enviar la respuesta de vuelta. Este método requiere que tu backend sea accesible públicamente en internet con un dominio y HTTPS.
        * **Long Polling:** Tu backend hace peticiones regulares a la API de Telegram preguntando si hay actualizaciones nuevas. Esto es más simple para desarrollo local o entornos sin exposición pública directa, pero menos eficiente en escala.
    * La lógica para procesar las actualizaciones de Telegram y enviar respuestas debe integrarse en los módulos `backend/bot/` y `backend/api/` (si usas webhooks).

## 7. Integración de APIs de Visión por Computadora ❌

La integración de la visión por computadora se realizará **luego de que la funcionalidad básica de chat (texto) funcione correctamente** tanto en la interfaz web como en Telegram.

* **Objetivo:** Permitir al bot analizar imágenes de alimentos para identificar ingredientes, platos o estimar porciones, e integrar esta información en la respuesta nutricional/receta.
* **Implementación:** Se hará principalmente en el directorio `backend/ai/`.
    * El endpoint de API (`backend/api/`) para recibir imágenes (ej. `/upload_image` o integrado en `/chat`) recibirá la imagen del frontend (web o Telegram).
    * La lógica en `backend/bot/` o `backend/core/` detectará que se ha recibido una imagen y llamará al módulo `backend/ai/`.
    * Dentro de `backend/ai/`, se implementará el código para:
        * Cargar las **credenciales** de la API de Visión seleccionada (Google Cloud Vision API, Azure AI Vision, etc.) - gestionadas como variables de entorno.
        * Realizar la llamada (petición HTTP) a la API de Visión, enviando los datos de la imagen.
        * Parsear la respuesta de la API para extraer las etiquetas (nombres de alimentos/objetos detectados) y su confianza.
        * **Crucial:** Utilizar las etiquetas detectadas para buscar información nutricional relevante en tu base de datos (`db/`) o archivos de datos (`data/`). Por ejemplo, si detecta "manzana" y "almendras", buscará las calorías, macros, etc., de manzanas y almendras.
        * Integrar esta información nutricional y la lista de alimentos detectados en el prompt que se enviará al modelo de lenguaje (Gemini 1.5 Flash) para que genere una respuesta coherente que combine el análisis de imagen con la información nutricional y el contexto del usuario.

## 8. Búsqueda y Uso de Datasets de Kaggle ❌

Kaggle es una excelente fuente para obtener datos que complementen tu base de datos o que sirvan como base para tus módulos de AI.

* **Proceso:**
    1.  Busca datasets relevantes en Kaggle.
    2.  Descarga los datasets que te interesen.
    3.  Almacena los archivos descargados en el directorio `data/`.
    4.  Desarrolla scripts (posiblemente en `scripts/` o lógica dentro de `backend/db/` o `backend/core/`) para procesar, limpiar y cargar estos datos en tu base de datos o convertirlos a un formato que tu backend pueda leer fácilmente.

* **Datasets Sugeridos en Kaggle (Busca por estos o términos similares):**
    * **Para Información Nutricional General:**
        * `USDA FoodData Central`: A menudo subido por usuarios. Es una fuente oficial de datos nutricionales de miles de alimentos. **Muy recomendado como base de datos de referencia.**
        * `Open Food Facts`: Datos de productos alimenticios, a veces más comerciales pero muy extensos.
        * Datasets de `Nutrition Facts` o `Food Calories`: Pueden ser compilaciones de diversas fuentes.
    * **Para Recetas:**
        * Datasets de `Recipes` de sitios web populares (ej. `Epicurious Recipes`, `Food.com Recipes`). Contienen ingredientes, instrucciones, a veces etiquetas/categorías, y en algunos casos, información nutricional.
        * Datasets de `Recipes` de sitios web populares (ej. `Epicurious Recipes`, `Food.com Recipes`). Contienen ingredientes, instrucciones, a veces etiquetas/categorías, y en algunos casos, información nutricional.
    * **Para Imágenes de Alimentos (para entrenar modelo o entender APIs):**
        * `Food-101`: Un dataset clásico de 101 categorías de alimentos con muchas imágenes. Útil para entender cómo funcionan los modelos de clasificación de alimentos.
        * Datasets más grandes o específicos de alimentos si necesitas mayor granularidad.

* **Uso en el Proyecto:**
    * Los datos nutricionales (USDA, etc.) se usarán en `backend/core/` y `backend/ai/` para proporcionar información precisa y para que la lógica de integración (combinando visión + datos + perfil) tenga datos fiables. Puedes cargarlos en tu base de datos (`db/`) o leerlos directamente de archivos si el formato es manejable.
    * Los datasets de recetas pueden usarse para enriquecer la capacidad del bot para dar variedad de recetas. Puedes almacenarlos en tu DB o tener un subconjunto accesible para el bot.
    * Los datasets de imágenes (como Food-101) son principalmente para referencia si decides entrenar un modelo de visión propio, aunque para un proyecto de curso el uso de una API pre-entrenada es mucho más rápido. Te ayudan a entender la granularidad de la clasificación de alimentos.

## 9. Optimización de la Estructura (Revisión) ✅

Revisando las sugerencias previas y los nuevos componentes:

1.  **Clarificar `bot/` vs `bots/`:** **Mantener la sugerencia.** Consolidar o definir roles claros.
2.  **Evaluar el directorio `web/`:** **Mantener la sugerencia.** Clarificar o eliminar si no es necesario para la aplicación React.
3.  **Agregar `config/` en el Backend:** **Recomendación fuerte.** Centralizar la carga de variables de entorno y configuraciones.
4.  **Manejo de Variables de Entorno (.env):** **Esencial y debe usarse.** Incluir Telegram Bot Token, claves de APIs de Visión, URL de DB, clave de API de Gemini, etc.
5.  **Documentar la Integración de IA:** **Mantener la sugerencia.** Documentar el flujo en `backend/ai/`.
6.  **Dockerización:** **Recomendación fuerte para despliegue y desarrollo consistente.** Añadir Dockerfiles y/o docker-compose.

## 10. Cómo Empezar a Desarrollar (Actualizado) ✅

1.  Clona el repositorio Git.
2.  Configura y activa tu entorno virtual de Python (ej. `python -m venv .venv` y `source .venv/bin/activate`).
3.  Instala las dependencias del backend (`pip install -r backend/requirements.txt`).
4.  Instala las dependencias del frontend (navega a `frontend/` y ejecuta `npm install` o `yarn install`).
5.  **Obtén las credenciales necesarias:**
    * Token de Telegram Bot (@BotFather).
    * Clave de API para Gemini 1.5 Flash (Google Cloud/Vertex AI).
    * Clave de API para el servicio de Visión elegido (Google Cloud Vision, Azure AI Vision, etc.).
    * Credenciales de la base de datos.
6.  **Crea un archivo `.env`** en la raíz del proyecto (o en `backend/config/`) y añade todas las credenciales y configuraciones necesarias como variables de entorno (consulta `backend/config/` si creas ese directorio). **Asegúrate de que `.env` esté en `.gitignore`**.
7.  Configura e inicializa tu base de datos (ej. ejecutando scripts en `backend/db/`).
8.  (Opcional pero recomendado) Descarga los datasets de Kaggle que necesites y colócalos en `data/`. Implementa la lógica para cargarlos en tu DB o usarlos directamente.
9.  Consulta la documentación en `docs/` para más detalles específicos (ej. `development_plan.md`, `pasoapaso.md`, `context.md`).

Esta guía actualizada proporciona un mapa más completo para construir tu asistente NutriVeci, integrando las diversas interfaces y componentes de IA y datos.
