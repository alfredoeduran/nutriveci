# NutriVeci

Asistente nutricional inteligente para combatir la malnutrición y promover la alimentación saludable y económica en comunidades vulnerables.

## Descripción

NutriVeci es una aplicación que ayuda a las personas a aprovechar los alimentos disponibles en casa y mejorar sus hábitos alimenticios sin gastar más. A través de un asistente nutricional basado en IA, la aplicación ofrece:

- **Recomendación de recetas** basadas en ingredientes disponibles
- **Planes de comida semanales** adaptados al presupuesto
- **Consejos nutricionales** personalizados según condiciones de salud
- **Lista de compras** optimizadas para minimizar gastos

## Interfaces

- Bot de Telegram
- Chat web

## Tecnologías

- **Backend**: Python (FastAPI)
- **Base de datos**: Supabase
- **IA/ML**: Procesamiento de Lenguaje Natural, Sistemas de Recomendación
- **Frontend**: HTML/CSS/JavaScript
- **Bot**: API de Telegram

## Estructura del Proyecto

```
/nutriveci
│
├── /backend                   # Código del backend
├── /frontend                  # Frontend para chat web
├── /data                      # Datos e información nutricional
├── /docs                      # Documentación
├── /tests                     # Pruebas automatizadas
└── /scripts                   # Scripts útiles
```

## Instalación y Configuración

### Requisitos previos

- Python 3.8+
- Node.js (para el frontend)
- Cuenta en Supabase
- Bot de Telegram registrado

### Configuración del entorno

1. Clonar el repositorio
   ```
   git clone https://github.com/tu-usuario/nutriveci.git
   cd nutriveci
   ```

2. Configurar entorno virtual de Python
   ```
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   .\venv\Scripts\activate   # Windows
   ```

3. Instalar dependencias
   ```
   pip install -r backend/requirements.txt
   ```

4. Configurar variables de entorno
   ```
   cp .env.example .env
   # Editar .env con las credenciales necesarias
   ```

## Uso (Instrucciones para usuarios)

_Por completar durante el desarrollo_

## Contribuir

_Por completar durante el desarrollo_

## Licencia

_Por definir_ 