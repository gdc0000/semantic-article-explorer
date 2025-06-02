# app/search_engine.py
import numpy as np
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def embed_query(query_text, model, query_prefix=""):
    """
    Generates an embedding for a single query string using the provided model.
    Adds an optional prefix (e.g., for e5 models).
    """
    if not model:
        logging.error("Embedding model not provided to embed_query.")
        return None
    try:
        # Add prefix if provided (e.g., "query: " for e5 models)
        text_to_embed = query_prefix + query_text if query_prefix else query_text
        query_embedding = model.encode([text_to_embed]) # model.encode expects a list
        logging.info(f"Query '{query_text}' embedded successfully. Shape: {query_embedding.shape}")
        return query_embedding.astype(np.float32) # Ensure float32 for FAISS
    except Exception as e:
        logging.error(f"Error embedding query '{query_text}': {e}")
        return None

def search_faiss_index(query_embedding, index, top_k=10):
    """
    Searches the FAISS index for the top_k nearest neighbors to the query_embedding.
    Returns distances and indices of the neighbors.
    """
    if query_embedding is None:
        logging.warning("Query embedding is None. Cannot search.")
        return None, None
    if not index:
        logging.error("FAISS index not provided to search_faiss_index.")
        return None, None
    if index.ntotal == 0:
        logging.warning("FAISS index is empty. Cannot perform search.")
        return np.array([]), np.array([])

    try:
        # Ensure query_embedding is 2D (batch of 1)
        if query_embedding.ndim == 1:
            query_embedding = np.expand_dims(query_embedding, axis=0)

        distances, indices = index.search(query_embedding, top_k)
        logging.info(f"FAISS search complete. Found {len(indices[0])} neighbors.")
        # distances and indices are 2D arrays (batch_size, top_k), extract first row
        return distances[0], indices[0]
    except Exception as e:
        logging.error(f"Error searching FAISS index: {e}")
        return None, None

# Example usage (conceptual, would be called from app.py)
# config = data_manager.load_config()
# if config:
#   embedding_model = data_manager.load_embedding_model(config)
#   faiss_index = data_manager.load_faiss_index(config)
#   if embedding_model and faiss_index:
#       query = "machine learning applications"
#       query_prefix = config.get('embedding_model', {}).get('query_prefix', "")
#       q_embedding = embed_query(query, embedding_model, query_prefix)
#       if q_embedding is not None:
#           distances, neighbor_indices = search_faiss_index(q_embedding, faiss_index, top_k=5)
#           # Process results...