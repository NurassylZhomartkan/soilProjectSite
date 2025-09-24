from fastapi import FastAPI
from .api.routers.external import router as external_router

app = FastAPI(
    title="Soil Moisturizing Data Hub",
    description="Сервис для работы с данными влажности почвы",
    version="1.0.0",
)

app.include_router(external_router)

@app.get("/")
async def root():
    return {"message": "Hello, Soil Moisturizing Data Hub!"}
