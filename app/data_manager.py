# app/data_manager.py
import streamlit as st
import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import yaml
import logging
import os # For checking file existence
from pathlib import Path

# Get the parent directory of the current script
parent_dir = Path(__file__).parent.parent

# Configure basic logging (useful for Streamlit if run directly, though Streamlit has its own logging)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@st.cache_data # Caches the output of this function
def load_config(config_path=parent_dir / "config.yaml"):
    """Loads the YAML configuration file."""
    if not os.path.exists(config_path):
        st.error(f"Configuration file not found at {config_path}")
        return None
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        logging.error(f"Error loading configuration: {e}")
        return None

@st.cache_data # Caches the DataFrame
def load_processed_records(file_path):
    """Loads the processed article records (metadata + UMAP coordinates) from Parquet."""
    if not os.path.exists(file_path):
        st.error(f"Processed records file not found: {file_path}")
        return pd.DataFrame() # Return empty DataFrame
    try:
        df = pd.read_parquet(file_path)
        # Ensure essential columns for visualization exist
        required_cols = ['id', 'title', 'abstract', 'x', 'y']
        config = load_config()
        if config and config['app_settings']['plot_dimensions'] == 3:
            required_cols.append('z')

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Processed records are missing required columns for visualization: {', '.join(missing_cols)}. Please re-run preprocessing.")
            return pd.DataFrame()

        logging.info(f"Processed records loaded successfully from {file_path}. Shape: {df.shape}")
        return df
    except Exception as e:
        st.error(f"Error loading processed records: {e}")
        logging.error(f"Error loading processed records: {e}")
        return pd.DataFrame()

@st.cache_resource # Caches the FAISS index object
def load_faiss_index(_config): # Pass config to use its path
    """Loads the FAISS index."""
    file_path = _config['paths']['faiss_index']
    if not os.path.exists(file_path):
        st.error(f"FAISS index file not found: {file_path}")
        return None
    try:
        index = faiss.read_index(file_path)
        logging.info(f"FAISS index loaded successfully from {file_path}. Contains {index.ntotal} vectors.")
        return index
    except Exception as e:
        st.error(f"Error loading FAISS index: {e}")
        logging.error(f"Error loading FAISS index: {e}")
        return None

@st.cache_resource # Caches the SentenceTransformer model
def load_embedding_model(_config): # Pass config to use its model name
    """Loads the SentenceTransformer model specified in the config."""
    model_name = _config['embedding_model']['name']
    try:
        model = SentenceTransformer(model_name)
        logging.info(f"SentenceTransformer model '{model_name}' loaded successfully.")
        return model
    except Exception as e:
        st.error(f"Error loading embedding model '{model_name}': {e}")
        logging.error(f"Error loading embedding model '{model_name}': {e}")
        return None

# Optional: Load full embeddings if needed by some part of the app,
# though typically search uses the index and query embedding.
# For very large embeddings, consider memory mapping if direct access is needed.
@st.cache_data
def load_embeddings_array(_config):
    """Loads the full embeddings array. Use with caution for large datasets."""
    file_path = _config['paths']['embeddings']
    if not os.path.exists(file_path):
        st.warning(f"Embeddings .npy file not found: {file_path}. Full embeddings not available.")
        return None
    try:
        embeddings = np.load(file_path)
        logging.info(f"Full embeddings array loaded from {file_path}. Shape: {embeddings.shape}")
        return embeddings
    except Exception as e:
        st.error(f"Error loading embeddings array: {e}")
        logging.error(f"Error loading embeddings array: {e}")
        return None

# Example of how these might be called in app.py:
# config = load_config()
# if config:
#     df_articles = load_processed_records(config['paths']['processed_data'])
#     faiss_index = load_faiss_index(config)
#     embedding_model = load_embedding_model(config)