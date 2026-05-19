import sys
import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure backend module can be imported
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.routes import chat, health, documents
from backend.app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="Vietnamese Legal AI", version="2.0.0")

# Setup CORS
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Include routers
app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Vietnamese Legal AI Agent API (LangGraph Version)"}


@app.get("/health")
async def root_health():
    return await health.health_endpoint()
