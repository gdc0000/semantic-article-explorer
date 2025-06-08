# backend/main.py

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Schema per la richiesta
class SearchRequest(BaseModel):
    query: str

# Schema per la risposta
class SearchResponse(BaseModel):
    results: list[str]

# Endpoint di prova
@app.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    dummy_results = [f"Risultato fittizio per: {request.query}"]
    return SearchResponse(results=dummy_results)
