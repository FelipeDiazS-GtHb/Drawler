from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from control_interno.router import router as notas_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos las rutas de control interno
app.include_router(notas_router, prefix="/api/control-interno")