# Guía paso a paso: Ejecutar el chat web con modelo de lenguaje

Este documento resume los pasos necesarios para ejecutar el chat web ubicado en la carpeta `web` usando el modelo de lenguaje definido en `backend/api/nlp.py`. El objetivo es que puedas hacer preguntas desde el chat y recibir respuestas simples generadas por el modelo de lenguaje.

---

## Paso 1: Verificar dependencias de Python

Asegúrate de tener todas las dependencias instaladas en tu entorno virtual:

```bash
# Activa el entorno virtual (si no está activo)
.\.venv\Scripts\Activate

# Instala las dependencias del backend
pip install -r requirements.txt

# Instala el cliente de Supabase si no está
pip install supabase
```

---

## Paso 2: Configura las variables de entorno

Revisa el archivo `.env` en la raíz del proyecto. Debe contener, al menos:

```
API_PORT=8080
JWT_ALGORITHM=HS256
HF_TOKEN=tu_token_de_huggingface
# ...otras variables necesarias para Supabase y seguridad
```

Asegúrate de que el puerto (`API_PORT`) y el token de HuggingFace (`HF_TOKEN`) estén correctamente configurados.

---

## Paso 3: Ejecutar el backend (FastAPI)

Desde la raíz del proyecto:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

- Si hay errores, revisa la consola y corrige dependencias o variables de entorno.
- Si el backend inicia correctamente, abre [http://localhost:8080/docs](http://localhost:8080/docs) para probar los endpoints.

---

## Paso 4: Servir el frontend (chat web)

Abre una nueva terminal, navega a la carpeta `web` y sirve los archivos estáticos en otro puerto (por ejemplo, 3000):

```bash
cd web
python -m http.server 3000
```

Abre [http://localhost:3000](http://localhost:3000) en tu navegador y abre el chat.

---

## Paso 5: Probar el flujo completo

- Escribe un mensaje en el chat web.
- Debería enviarse una petición POST a `http://localhost:8080/nlp/interpret`.
- El backend debe responder con una respuesta generada por el modelo HuggingFace.

---

## Notas y solución de problemas

- Si ves `net::ERR_CONNECTION_REFUSED`, asegúrate de que el backend esté corriendo en el puerto 8080 y sin errores.
- Si ves `501 Unsupported method ('POST')`, asegúrate de NO estar usando `python -m http.server 8080` para el backend.
- Si ves `ModuleNotFoundError`, instala la dependencia faltante en el entorno virtual.
- Si el modelo de HuggingFace no responde, revisa el valor de `HF_TOKEN` y tu conexión a internet.

---

## Siguiente paso

¿Quieres que ejecute el flujo completo y te muestre el resultado del chat web con el modelo de lenguaje?
