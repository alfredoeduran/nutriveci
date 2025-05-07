# Flujo y Características de la Aplicación NutriVeci

A continuación, se detalla el flujo de la aplicación, sus características principales y las tecnologías sugeridas, basado en el documento proporcionado y los requisitos adicionales.
## Tecnologia de la aplicacion

**Frontend:**
* **Chat Web:** HTML, CSS, JavaScript.
* **Bot de Telegram:** Interfaz vía app Telegram (gestionado por librería backend).
* *(Opcional - App Nativa):* Flutter / React Native.

**Marco UI (Framework UI para Chat Web):**
* **Básico:** Vanilla JavaScript.
* *(Opcional - Avanzado):* Alpine.js, htmx, React, Vue, Svelte.

**Procesamiento de la IA:**
* **Lenguaje Principal:** Python.
* **Bibliotecas NLP:** `Transformers` (Hugging Face), `spaCy`, `NLTK`.
* **Modelos NLP:** DistilBERT, FLAN-T5, GPT-Neo, Llama 2 (versiones ligeras).
* **Bibliotecas ML:** `Scikit-learn`, `LightGBM`, `Keras`/`TensorFlow`/`PyTorch`.
* **Modelos ML (Clasif./Recom.):** Random Forest, KNN, Regresión Logística, Árboles de Decisión, MLP.

**Metodologia (IA):**
* Procesamiento de Lenguaje Natural (NLP).
* Aprendizaje Supervisado (Clasificación, Regresión).
* Sistemas de Recomendación.
* Base de Conocimientos / Base de Datos Nutricional Contextualizada.

**Backend:**
* **Lenguaje:** Python.
* **Framework Web:** Flask / FastAPI (recomendados) o Node.js + Express.
* **Base de Datos:** supabase (para perfiles, recetas, logs).
* **API Telegram:** `python-telegram-bot` o similar.
* *(Opcional) API WhatsApp:* Twilio API / Meta Cloud API.

Combatir la malnutrición y promover la alimentación saludable y económica en comunidades vulnerables, ayudando a las personas a aprovechar los alimentos disponibles en casa y mejorar sus hábitos alimenticios sin gastar más[cite: 1].

## 2. Interfaces de Usuario

La aplicación interactuará con los usuarios a través de dos canales principales:

* **Bot de Telegram:** Un bot conversacional en Telegram permitirá a los usuarios interactuar con el asistente de IA.
* **Chat Web:** Una interfaz de chat simple embebida en una página web (puede ser HTML básico) ofrecerá una alternativa de acceso.

## 3. Flujo General de Interacción

1.  **Inicio de Interacción:** El usuario inicia una conversación a través del bot de Telegram o el chat web.
2.  **Registro/Perfil (Opcional pero recomendado):** Para personalizar las recomendaciones, se podría implementar un registro básico donde el usuario indique edad, peso, condiciones especiales (diabetes, hipertensión, etc.), presupuesto y tamaño del hogar[cite: 4, 6, 38]. Esta información se almacena de forma segura.
3.  **Consulta del Usuario:** El usuario realiza una consulta, por ejemplo:
    * Ingresando los ingredientes que tiene disponibles ("Tengo arroz, lenteja y plátano, ¿qué puedo hacer?")[cite: 2, 25].
    * Solicitando un plan de comidas semanal ("Menú para 7 días con $50.000 COP")[cite: 5].
    * Haciendo preguntas nutricionales ("¿Qué debo comer si soy diabético?")[cite: 6].
4.  **Procesamiento Backend:**
    * La consulta llega al backend de la aplicación (Python).
    * **Registro de Consulta:** La consulta del usuario (tanto de Telegram como del chat web) se guarda en una base de datos (ej. PostgreSQL [cite: 13] o Firestore) para análisis futuros o auditoría.
    * **Procesamiento NLP:** El texto de la consulta se procesa utilizando modelos de Procesamiento de Lenguaje Natural (NLP) como DistilBERT o FLAN-T5 para entender la intención y extraer entidades clave (ingredientes, condición médica, etc.)[cite: 14, 25, 37].
    * **Lógica de IA:**
        * **Recetas:** Si se piden recetas, el sistema busca en su base de datos nutricional contextualizada [cite: 39] o utiliza modelos de clasificación/recomendación (Random Forest, KNN, MLP [cite: 29, 38]) para sugerir opciones basadas en los ingredientes, perfil del usuario y reglas nutricionales (sin gas, sin fritura, etc.)[cite: 3, 8].
        * **Plan Semanal:** Genera un plan y lista de mercado basada en presupuesto y perfil[cite: 4].
        * **Consulta Nutricional:** Responde dudas usando la base de conocimientos y modelos de IA adaptados al perfil del usuario[cite: 6, 8].
5.  **Respuesta al Usuario:** El backend envía la respuesta formateada (receta, plan, consejo) al canal original (Telegram o chat web).
6.  **Panel Comunitario (Opcional):** La información agregada y anonimizada puede alimentar un panel para instituciones (alcaldía, fundaciones) mostrando tendencias nutricionales, zonas de riesgo, etc[cite: 11, 12].

## 4. Funcionalidades Principales Detalladas

* **Asistente de Menú Personalizado:** Sugiere recetas nutritivas basadas en ingredientes disponibles, con opciones específicas (sin gas, sin fritura, sin desperdicio)[cite: 2, 3].
* **Planificador de Comidas Semanal:** Genera menú y lista de mercado económica y saludable según presupuesto y tamaño del hogar[cite: 4].
* **Asistente Nutricional con IA:** Responde dudas sobre alimentación y salud (diabetes, niños, etc.), adaptándose al perfil del usuario mediante reglas nutricionales y aprendizaje automático[cite: 6, 7, 8, 35].
* **Modo Offline/WhatsApp/SMS:** Se contempla la posibilidad de funcionar vía WhatsApp [cite: 9] o incluso SMS [cite: 10] para zonas con baja conectividad.
* **Panel Comunitario/Institucional:** Visualización de datos agregados para entidades colaboradoras[cite: 11, 12].
* **Registro de Consultas:** Almacenamiento de todas las interacciones de los usuarios desde Telegram y el chat web.

## 5. Tecnologías Sugeridas

* **Backend:** Python (con frameworks como Flask o FastAPI). Node.js + Express también es una opción[cite: 13].
* **Frontend App (si se desarrolla nativa):** Flutter / React Native[cite: 13]. Para el chat web: HTML, CSS, JavaScript simple.
* **Base de Datos:** PostgreSQL [cite: 13] o Firebase/Firestore [cite: 13] (para almacenar perfiles de usuario, recetas, y el *log de consultas*).
* **Motor IA:**
    * **NLP:** Modelos ligeros como DistilBERT, FLAN-T5, GPT-Neo, Llama 2 7B[cite: 14, 26, 37]. Librerías como spaCy, NLTK, Transformers (Hugging Face).
    * **Clasificación/Recomendación:** Scikit-learn (Random Forest, KNN, Regresión Logística), LightGBM, redes neuronales simples (MLP) con Keras/TensorFlow/PyTorch[cite: 14, 29, 38].
* **Integración Telegram:** Librerías como `python-telegram-bot`.
* **Integración WhatsApp (Opcional):** Twilio API / Meta Cloud API[cite: 14].

## 6. Metodología de IA

* **NLP:** Para interpretar las consultas de los usuarios en lenguaje natural[cite: 25, 37].
* **Aprendizaje Supervisado (Clasificación/Regresión):** Para personalizar recomendaciones basadas en el perfil del usuario (salud, presupuesto) y clasificar recetas[cite: 28, 38].
* **Base de Datos Nutricional Contextualizada:** Un repositorio clave con recetas validadas y adaptadas cultural y económicamente[cite: 39].
* **NO se requieren CNNs (Redes Neuronales Convolucionales)** a menos que se añada funcionalidad de reconocimiento de imágenes de alimentos[cite: 21, 30].

## 7. MVP Inicial Sugerido (Adaptado)

1.  Registro básico de usuario (opcional, pero útil para personalización)[cite: 14].
2.  Módulo de recetas según ingredientes disponibles[cite: 14].
3.  Integración con **Telegram** y **Chat Web Básico**.
4.  **Sistema de logging** para guardar consultas de ambos canales.
5.  Backend en Python con lógica IA básica (NLP + recomendación simple).
6.  Base de datos para usuarios (si aplica) y logs.

Este flujo y conjunto de características proporcionan una base sólida para que un desarrollador comience la implementación, integrando las funcionalidades del documento NutriVeci con los requisitos específicos de despliegue en Telegram, web y el registro de consultas.

## 8. Esquema de Base de Datos (Supabase)

A continuación se detalla el esquema de la base de datos para NutriVeci, implementado en Supabase:

### Tablas Principales

**users** - Perfiles de usuarios:
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  telegram_id VARCHAR UNIQUE,  -- ID único de Telegram (si aplica)
  web_id VARCHAR UNIQUE,       -- ID único para usuarios web (si aplica)
  name VARCHAR,
  age INTEGER,
  weight FLOAT,
  height FLOAT,
  household_size INTEGER,      -- Tamaño del hogar (número de personas)
  budget FLOAT,                -- Presupuesto disponible para alimentación
  restrictions VARCHAR[],      -- Array de restricciones alimenticias
  location VARCHAR,            -- Ubicación/región 
  CONSTRAINT requires_one_id CHECK (telegram_id IS NOT NULL OR web_id IS NOT NULL)
);

-- Triggers para actualizar automáticamente updated_at
CREATE TRIGGER set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION trigger_set_updated_at();
```

**health_conditions** - Condiciones de salud de los usuarios:
```sql
CREATE TABLE health_conditions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  condition_type VARCHAR NOT NULL, -- diabetes, hipertensión, etc.
  severity VARCHAR,                -- leve, moderada, severa
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  notes TEXT
);
```

**ingredients** - Catálogo de ingredientes:
```sql
CREATE TABLE ingredients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR NOT NULL UNIQUE,
  category VARCHAR NOT NULL, -- verduras, frutas, proteínas, etc.
  nutritional_value JSONB,   -- valores nutricionales (proteínas, carbohidratos, etc.)
  seasonal BOOLEAN,          -- si es un ingrediente de temporada
  price_category VARCHAR,    -- económico, medio, premium
  region VARCHAR[]           -- regiones donde es común
);
```

**recipes** - Recetas disponibles:
```sql
CREATE TABLE recipes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  name VARCHAR NOT NULL,
  description TEXT,
  preparation_steps TEXT[] NOT NULL,
  cooking_time INTEGER,      -- tiempo en minutos
  difficulty VARCHAR,        -- fácil, medio, difícil
  servings INTEGER,
  tags VARCHAR[],            -- etiquetas como "sin_fritura", "económico", etc.
  nutritional_info JSONB,    -- información nutricional
  estimated_cost FLOAT,      -- costo estimado 
  image_url VARCHAR,
  healthy_score INTEGER      -- puntuación de salubridad (1-100)
);
```

**recipe_ingredients** - Relación muchos a muchos entre recetas e ingredientes:
```sql
CREATE TABLE recipe_ingredients (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
  ingredient_id UUID REFERENCES ingredients(id) ON DELETE CASCADE,
  quantity FLOAT NOT NULL,
  unit VARCHAR NOT NULL,     -- g, kg, unidad, etc.
  UNIQUE(recipe_id, ingredient_id)
);
```

**meal_plans** - Planes de comida semanales:
```sql
CREATE TABLE meal_plans (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  start_date DATE,
  end_date DATE,
  budget FLOAT,
  notes TEXT
);
```

**meal_plan_items** - Elementos individuales de un plan de comidas:
```sql
CREATE TABLE meal_plan_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
  recipe_id UUID REFERENCES recipes(id) ON DELETE SET NULL,
  day_of_week INTEGER,       -- 1-7 (lunes a domingo)
  meal_type VARCHAR,         -- desayuno, almuerzo, cena, merienda
  notes TEXT
);
```

**shopping_lists** - Listas de compra generadas:
```sql
CREATE TABLE shopping_lists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  meal_plan_id UUID REFERENCES meal_plans(id) ON DELETE CASCADE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  estimated_cost FLOAT,
  notes TEXT
);
```

**shopping_list_items** - Elementos de la lista de compra:
```sql
CREATE TABLE shopping_list_items (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  shopping_list_id UUID REFERENCES shopping_lists(id) ON DELETE CASCADE,
  ingredient_id UUID REFERENCES ingredients(id) ON DELETE CASCADE,
  quantity FLOAT,
  unit VARCHAR,
  estimated_price FLOAT,
  purchased BOOLEAN DEFAULT FALSE
);
```

### Tablas para Logging y Analítica

**interaction_logs** - Registro de todas las interacciones con usuarios:
```sql
CREATE TABLE interaction_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  source VARCHAR NOT NULL,   -- 'telegram', 'web', 'whatsapp', etc.
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  query TEXT NOT NULL,       -- consulta textual del usuario
  intent VARCHAR,            -- intención identificada
  entities JSONB,            -- entidades extraídas (ingredientes, condiciones, etc.)
  response_type VARCHAR,     -- tipo de respuesta (receta, plan, consejo, etc.)
  response_id UUID,          -- ID del recurso recomendado (receta, plan, etc.)
  session_id VARCHAR,        -- ID de sesión para agrupar interacciones
  response_time INTEGER,     -- tiempo de respuesta en ms
  feedback JSONB             -- retroalimentación del usuario (si existe)
);
```

**nutritional_knowledge_base** - Base de conocimientos nutricionales:
```sql
CREATE TABLE nutritional_knowledge_base (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  question_pattern TEXT NOT NULL,
  answer TEXT NOT NULL,
  category VARCHAR,
  tags VARCHAR[],
  health_conditions VARCHAR[],
  source_reference TEXT,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**community_analytics** - Analítica para el panel comunitario (agregada y anonimizada):
```sql
CREATE TABLE community_analytics (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  region VARCHAR,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  metric_type VARCHAR NOT NULL,  -- 'consultas_por_tipo', 'recetas_populares', etc.
  metric_value JSONB NOT NULL,   -- datos agregados 
  timeframe VARCHAR              -- 'daily', 'weekly', 'monthly'
);
```

### Índices para Optimización

```sql
-- Índices para búsqueda de recetas por ingredientes
CREATE INDEX idx_recipe_ingredients_ingredient_id ON recipe_ingredients(ingredient_id);
CREATE INDEX idx_recipe_ingredients_recipe_id ON recipe_ingredients(recipe_id);

-- Índices para búsqueda de recetas por tags
CREATE INDEX idx_recipes_tags ON recipes USING GIN(tags);

-- Índices para consultas de logs
CREATE INDEX idx_interaction_logs_timestamp ON interaction_logs(timestamp);
CREATE INDEX idx_interaction_logs_user_id ON interaction_logs(user_id);
CREATE INDEX idx_interaction_logs_intent ON interaction_logs(intent);

-- Índice para búsqueda de texto completo en recetas
CREATE INDEX idx_recipes_full_text ON recipes USING GIN(to_tsvector('spanish', name || ' ' || description));

-- Índice para búsqueda en base de conocimientos
CREATE INDEX idx_knowledge_base_full_text ON nutritional_knowledge_base 
USING GIN(to_tsvector('spanish', question_pattern || ' ' || answer));
```

### Políticas de Seguridad (RLS)

```sql
-- Ejemplo de políticas de Row Level Security para proteger datos de usuarios
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY users_policy ON users
  USING (id = auth.uid() OR auth.role() = 'admin');

-- Política para logs de interacción
ALTER TABLE interaction_logs ENABLE ROW LEVEL SECURITY;
CREATE POLICY logs_select_policy ON interaction_logs
  FOR SELECT USING (user_id = auth.uid() OR auth.role() = 'admin');
```

## 9. Estructura de Carpetas del Proyecto

La siguiente estructura de carpetas está diseñada para una implementación en Python (FastAPI) con integración de Telegram y chat web:

```
/nutriveci
│
├── /backend                   # Código del backend
│   ├── /api                   # Endpoints de la API REST
│   │   ├── __init__.py
│   │   ├── auth.py            # Autenticación y usuarios
│   │   ├── recipes.py         # Endpoints para recetas
│   │   ├── meal_plans.py      # Endpoints para planes de comida
│   │   ├── ingredients.py     # Endpoints para ingredientes
│   │   └── analytics.py       # Endpoints para analytics
│   │
│   ├── /core                  # Lógica central de la aplicación
│   │   ├── __init__.py
│   │   ├── config.py          # Configuración de la aplicación
│   │   ├── security.py        # Funciones de seguridad
│   │   └── dependencies.py    # Dependencias compartidas
│   │
│   ├── /db                    # Acceso a la base de datos
│   │   ├── __init__.py
│   │   ├── supabase.py        # Cliente de Supabase
│   │   ├── models.py          # Modelos Pydantic
│   │   ├── crud.py            # Operaciones CRUD
│   │   └── schemas/           # Esquemas de validación
│   │
│   ├── /ai                    # Módulos de inteligencia artificial
│   │   ├── __init__.py
│   │   ├── nlp_processor.py   # Procesamiento de lenguaje natural
│   │   ├── recipe_recommender.py  # Sistema de recomendación
│   │   ├── meal_planner.py    # Planificador de comidas
│   │   ├── nutritional_advisor.py # Asistente nutricional
│   │   └── models/            # Modelos entrenados o Fine-tuned
│   │
│   ├── /bots                  # Integraciones de bots
│   │   ├── __init__.py
│   │   ├── telegram_bot.py    # Bot de Telegram
│   │   └── whatsapp_bot.py    # Bot de WhatsApp (opcional)
│   │
│   ├── /logging               # Sistema de logging
│   │   ├── __init__.py
│   │   ├── logger.py          # Configuración del logger
│   │   └── analytics.py       # Analítica de datos
│   │
│   ├── main.py                # Punto de entrada principal
│   ├── requirements.txt       # Dependencias de Python
│   └── Dockerfile             # Configuración para contenedorización
│
├── /frontend                  # Frontend para chat web
│   ├── /public                # Archivos estáticos
│   │   ├── index.html
│   │   ├── css/
│   │   ├── js/
│   │   └── assets/            # Imágenes, iconos, etc.
│   │
│   ├── /src                   # Código fuente (si se usa framework)
│   │   ├── components/
│   │   ├── services/
│   │   └── utils/
│   │
│   ├── package.json           # Si se usa npm/yarn
│   └── README.md
│
├── /data                      # Datos e información nutricional
│   ├── /seed_data             # Datos iniciales para la base de datos
│   │   ├── ingredients.json
│   │   ├── recipes.json
│   │   └── nutritional_knowledge.json
│   │
│   └── /datasets              # Conjuntos de datos para entrenar modelos
│
├── /docs                      # Documentación
│   ├── API.md
│   ├── deployment.md
│   └── user_guide.md
│
├── /tests                     # Pruebas automatizadas
│   ├── /unit
│   ├── /integration
│   └── /e2e
│
├── /scripts                   # Scripts útiles
│   ├── setup_db.py            # Configuración inicial de la base de datos
│   ├── seed_data.py           # Poblado de datos iniciales
│   └── deploy.sh              # Script de despliegue
│
├── docker-compose.yml         # Configuración para Docker Compose
├── .env.example               # Ejemplo de variables de entorno
├── README.md                  # Documentación general
└── LICENSE                    # Licencia del proyecto
```

Esta estructura de carpetas proporciona una organización clara y modular para el proyecto NutriVeci, facilitando el desarrollo, mantenimiento y escalabilidad del sistema. La separación de responsabilidades entre backend, frontend, datos y pruebas permite un desarrollo eficiente y colaborativo.