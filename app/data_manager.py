import pandas as pd
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import yaml
import logging
import os
from pathlib import Path

# Get the parent directory of the current script
parent_dir = Path(__file__).parent.parent

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_config(config_path=parent_dir / "config.yaml"):
    """Loads the YAML configuration file."""
    if not os.path.exists(config_path):
        logging.error(f"Configuration file not found at {config_path}")
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise


def load_processed_records(file_path):
    """Loads the processed article records (metadata + UMAP coordinates) from Parquet."""
    if not os.path.exists(file_path):
        logging.error(f"Processed records file not found: {file_path}")
        raise FileNotFoundError(f"Processed records file not found: {file_path}")
    try:
        df = pd.read_parquet(file_path)

        # Check for required columns
        required_cols = ['id', 'title', 'abstract', 'x', 'y']
        config = load_config()
        if config and config['app_settings']['plot_dimensions'] == 3:
            required_cols.append('z')

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            msg = f"Processed records missing columns: {', '.join(missing_cols)}"
            logging.error(msg)
            raise ValueError(msg)

        logging.info(f"Processed records loaded from {file_path}. Shape: {df.shape}")
        return df
    except Exception as e:
        logging.error(f"Error loading processed records: {e}")
        raise


def load_faiss_index(_config):
    """Loads the FAISS index."""
    file_path = _config['paths']['faiss_index']
    if not os.path.exists(file_path):
        logging.error(f"FAISS index file not found: {file_path}")
        raise FileNotFoundError(f"FAISS index file not found: {file_path}")
    try:
        index = faiss.read_index(file_path)
        logging.info(f"FAISS index loaded from {file_path}. Vectors: {index.ntotal}")
        return index
    except Exception as e:
        logging.error(f"Error loading FAISS index: {e}")
        raise


def load_embedding_model(_config):
    """Loads the SentenceTransformer model specified in the config."""
    model_name = _config['embedding_model']['name']
    try:
        model = SentenceTransformer(model_name)
        logging.info(f"SentenceTransformer model '{model_name}' loaded.")
        return model
    except Exception as e:
        logging.error(f"Error loading model '{model_name}': {e}")
        raise


def load_embeddings_array(_config):
    """Loads the full embeddings array. Use with caution for large datasets."""
    file_path = _config['paths']['embeddings']
    if not os.path.exists(file_path):
        logging.warning(f"Embeddings file not found: {file_path}")
        return None
    try:
        embeddings = np.load(file_path)
        logging.info(f"Embeddings loaded from {file_path}. Shape: {embeddings.shape}")
        return embeddings
    except Exception as e:
        logging.error(f"Error loading embeddings array: {e}")
        return None
