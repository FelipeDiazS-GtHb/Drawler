from fastapi import APIRouter

# Importamos los sub-routers modulares que acabamos de crear
from .router_eyc import router as eyc_router
from .router_invasivos import router as invasivos_router
from .router_rutero import router as rutero_router

router = APIRouter()

# Agrupamos todos los endpoints en el router principal
router.include_router(eyc_router, tags=["Notas EYC"])
router.include_router(invasivos_router, tags=["Medios Invasivos"])
router.include_router(rutero_router, tags=["Rutero"])