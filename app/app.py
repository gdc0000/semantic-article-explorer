from fastapi import APIRouter
from pydantic import BaseModel
from app.search_engine import search_articles
from fastapi.responses import FileResponse
import os

router = APIRouter()

class Article(BaseModel):
    id: int
    title: str
    abstract: str
    x: float
    y: float

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    results: list[Article]

@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest):
    """
    Endpoint principale per la ricerca semantica.
    Riceve una query e restituisce i record completi degli articoli più simili.
    """
    matched_articles = search_articles(request.query)
    return SearchResponse(results=matched_articles)

@router.get("/raw-data")
def get_raw_data():
    filepath = os.path.join("data", "raw_records.json")
    return FileResponse(filepath, media_type="application/json")