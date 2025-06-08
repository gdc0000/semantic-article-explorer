# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.app import router as search_router

app = FastAPI()

# CORS per permettere chiamate dal frontend React (localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Includi le rotte definite in app/app.py
app.include_router(search_router, prefix="", include_in_schema=True)
