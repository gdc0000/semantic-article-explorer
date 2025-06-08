# app/app.py

from fastapi import APIRouter
from pydantic import BaseModel
from app.search_engine import search_articles

# Crea un router da includere in FastAPI
router = APIRouter()

# Modello della richiesta: accetta una stringa 'query'
class SearchRequest(BaseModel):
    query: str

# Modello della risposta: restituisce una lista di stringhe
class SearchResponse(BaseModel):
    results: list[str]

# Rotta POST /search
@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    Endpoint principale per la ricerca semantica.
    Riceve una query e restituisce i titoli degli articoli più simili.
    """
    results = search_articles(request.query)
    return SearchResponse(results=results)
