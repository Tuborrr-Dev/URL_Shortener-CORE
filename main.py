from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api.routes import (
    router,
)  # this isnt done in the main.py file because we want to keep the main.py file clean and organized

app = FastAPI(title="URL Shortener API", version="1.0.0")

# Parse allowed origins from comma-separated CORS_ORIGINS env var
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(router)
