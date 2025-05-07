from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
import os
from dotenv import load_dotenv

# Cargar variables de entorno
project_root = Path(__file__).resolve().parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Depuración: mostrar los valores críticos
for var in ["SUPABASE_URL", "SUPABASE_KEY", "SUPABASE_JWT_SECRET", "TELEGRAM_BOT_TOKEN", "HF_TOKEN", "GOOGLE_API_KEY"]:
    print(f"[DEBUG] {var}: ", os.getenv(var))

# Importar routers
from backend.api import users, auth, preferences, ingredients, recipes, admin, nlp

# Crear aplicación FastAPI
app = FastAPI(
    title="NutriVeci API",
    description="API para el asistente nutricional NutriVeci",
    version="0.1.0",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],  # Frontend local
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta de salud
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Incluir routers de API con prefijo /api
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(preferences.router, prefix="/api")
app.include_router(ingredients.router, prefix="/api")
app.include_router(recipes.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(nlp.router, prefix="/api")

# Montar archivos estáticos
web_dir = project_root / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

# Servir index.html para rutas no encontradas
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    # Si la ruta comienza con /api, devolver 404
    if full_path.startswith("api/"):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found"}
        )
    
    # Para otras rutas, servir el index.html
    index_path = web_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    
    return JSONResponse(
        status_code=404,
        content={"detail": "Not Found"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True) 