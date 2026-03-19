from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.chat_routes import router as chat_router
from db.database import init_semantic_memory_table

app = FastAPI(
    title="BhutanStay AI API",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.on_event("startup")
def startup():
    init_semantic_memory_table()
    print("[app] Semantic memory table initialized.")