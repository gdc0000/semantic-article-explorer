# search_engine.py

import numpy as np
import logging
from app import data_manager

# --------------------------
# Configure logging format
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# --------------------------
# Load all required resources once at import
# --------------------------
config = data_manager.load_config()
df_articles = data_manager.load_processed_records(config['paths']['processed_data'])
faiss_index = data_manager.load_faiss_index(config)
embedding_model = data_manager.load_embedding_model(config)

# Settings from config
query_prefix = config.get('embedding_model', {}).get('query_prefix', "")
top_k = config['app_settings']['default_top_k']


# ==========================
# MAIN SEARCH FUNCTION
# ==========================
def search_articles(query: str = None, article_id: int = None) -> list[dict]:
    """
    Performs semantic search either using a text query or an existing article ID.
    Returns a list of similar article dictionaries.
    """
    # --- Get the embedding for the query or the article ---
    if query:
        query_embedding = embed_text(query)
    elif article_id is not None:
        text = extract_article_text(article_id)
        query_embedding = embed_text(text)
        logging.info(f"Embedding generated for article ID {article_id}")
    else:
        raise ValueError("Either a text query or an article_id must be provided.")

    # --- Abort if the embedding failed ---
    if query_embedding is None:
        return []

    # --- Run similarity search in the FAISS index ---
    distances, indices = search_faiss_index(query_embedding, faiss_index, top_k=top_k + 1)
    if indices is None or len(indices) == 0:
        return []

    # --- Convert index positions to article IDs ---
    similar_ids = [df_articles.iloc[idx]['id'] for idx in indices]

    # --- Exclude the original article if searching by article_id ---
    if article_id is not None:
        similar_ids = [i for i in similar_ids if i != article_id]

    # --- Limit to top_k and return matching records ---
    top_ids = similar_ids[:top_k]
    results_df = df_articles[df_articles['id'].isin(top_ids)]

    logging.info(f"Found {len(results_df)} similar articles: {top_ids}")
    return results_df.to_dict(orient='records')



# ==========================
# TEXT EMBEDDING FUNCTION
# ==========================
def embed_text(text: str) -> np.ndarray:
    """
    Converts input text into an embedding using the model.
    Adds prefix if specified in config (e.g., for e5 models).
    """
    if not embedding_model:
        logging.error("Embedding model is not loaded.")
        return None

    try:
        full_text = query_prefix + text
        embedding = embedding_model.encode([full_text])  # encode expects list
        logging.info(f"Text embedded successfully. Shape: {embedding.shape}")
        return embedding.astype(np.float32)  # FAISS requires float32
    except Exception as e:
        logging.error(f"Failed to embed text: {e}")
        return None


# ==========================
# FAISS SEARCH FUNCTION
# ==========================
def search_faiss_index(query_embedding: np.ndarray, index, top_k: int = 10):
    """
    Performs nearest-neighbor search in FAISS index using the input embedding.
    Returns distances and indices of top_k matches.
    """
    if query_embedding is None:
        logging.warning("No embedding provided.")
        return None, None

    if not index:
        logging.error("FAISS index is not loaded.")
        return None, None

    if index.ntotal == 0:
        logging.warning("FAISS index is empty.")
        return np.array([]), np.array([])

    try:
        # Ensure embedding is 2D
        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(query_embedding, axis=0)

        distances, indices = index.search(query_embedding, top_k)
        logging.info(f"FAISS search returned {len(indices[0])} results.")
        return distances[0], indices[0]
    except Exception as e:
        logging.error(f"Error during FAISS search: {e}")
        return None, None


# ==========================
# ARTICLE TEXT EXTRACTION
# ==========================
def extract_article_text(article_id: str) -> str:
    """
    Concatenates title and abstract of the article to create a searchable string.
    """
    print(f"\n🔍 CERCO articolo con id = {article_id}")
    print(f"🧠 Tipo di article_id: {type(article_id)}")

    filtered = df_articles[df_articles['id'] == int(article_id)]
    print(f"🎯 Match trovati: {len(filtered)}")
    print(filtered)

    if filtered.empty:
        raise ValueError(f"❌ No article found with ID {article_id}")

    # return filtered.iloc[0]['title'] + ". " + filtered.iloc[0]['abstract']

    
    row = df_articles[df_articles['id'] == str(article_id)].iloc[0]
    matches = df_articles[df_articles['id'] == str(article_id)]
    if matches.empty:
        raise ValueError(f"No article found with ID {article_id}")
    row = matches.iloc[0]

    return " ".join([str(row.get(field, "")) for field in ['title', 'abstract']])
