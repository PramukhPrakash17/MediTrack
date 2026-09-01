from fastapi import FastAPI
from .api.xray_controller import router as xray_router

app = FastAPI()
app.include_router(xray_router)
