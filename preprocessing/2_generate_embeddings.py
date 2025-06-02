# preprocessing/2_generate_embeddings.py
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import yaml
import logging
import torch # For checking CUDA availability
from pathlib import Path

# Get the parent directory of the current script
# parent_dir = Path(__file__).parent.parent parent_dir /

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path= "config.yaml"):
    """Loads the YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_processed_data(file_path):
    """Loads processed data from a Parquet file."""
    try:
        df = pd.read_parquet(file_path)
        logging.info(f"Successfully loaded {len(df)} records from {file_path}")
        return df
    except FileNotFoundError:
        logging.error(f"Processed data file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading processed data: {e}")
        raise

def prepare_text_for_embedding(df, text_fields, passage_prefix=""):
    """
    Prepares text for embedding by concatenating specified fields.
    Adds an optional prefix (e.g., for e5 models).
    """
    if not text_fields:
        logging.error("No text fields specified for embedding in config.")
        raise ValueError("text_fields_to_embed cannot be empty.")

    # Ensure all specified text fields exist, fill NaNs with empty strings
    for field in text_fields:
        if field not in df.columns:
            logging.warning(f"Text field '{field}' not found in DataFrame. It will be ignored.")
            # Or raise an error: raise KeyError(f"Text field '{field}' not found.")
            df[field] = "" # Add empty column to prevent error in apply
        else:
            df[field] = df[field].fillna('')


    # Concatenate text fields
    # Using .astype(str) to handle potential non-string types after fillna
    texts_to_embed = df[text_fields].astype(str).agg(' '.join, axis=1).tolist()

    # Add prefix if provided
    if passage_prefix:
        texts_to_embed = [passage_prefix + text for text in texts_to_embed]

    logging.info(f"Prepared {len(texts_to_embed)} texts for embedding.")
    return texts_to_embed

def generate_embeddings(texts, model_name, batch_size, device):
    """
    Generates embeddings for a list of texts using a SentenceTransformer model.
    """
    try:
        model = SentenceTransformer(model_name, device=device)
        logging.info(f"SentenceTransformer model '{model_name}' loaded on {device}.")
    except Exception as e:
        logging.error(f"Error loading SentenceTransformer model '{model_name}': {e}")
        raise

    logging.info(f"Generating embeddings for {len(texts)} texts (batch size: {batch_size})...")
    embeddings = model.encode(texts, batch_size=batch_size, show_progress_bar=True)
    logging.info(f"Embeddings generated. Shape: {embeddings.shape}")
    return embeddings

def save_embeddings(embeddings, file_path):
    """Saves embeddings to a .npy file."""
    try:
        np.save(file_path, embeddings)
        logging.info(f"Embeddings saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving embeddings: {e}")
        raise

def main():
    """Main function to orchestrate embedding generation."""
    logging.info("Starting embedding generation process...")
    config = load_config()
    paths_config = config['paths']
    model_config = config['embedding_model']

    df_processed = load_processed_data(paths_config['processed_data'])
    if df_processed.empty:
        logging.warning("Processed data is empty. No embeddings will be generated.")
        return

    # Determine device for SentenceTransformer
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logging.info(f"Using device: {device}")

    passage_prefix = model_config.get('passage_prefix', "") # Get prefix, default to empty if not specified
    texts_to_embed = prepare_text_for_embedding(df_processed, model_config['text_fields_to_embed'], passage_prefix)

    if not texts_to_embed:
        logging.warning("No texts to embed after preparation. Exiting.")
        return

    embeddings = generate_embeddings(
        texts_to_embed,
        model_config['name'],
        model_config['batch_size'],
        device
    )

    save_embeddings(embeddings, paths_config['embeddings'])
    logging.info("Embedding generation process finished successfully.")

if __name__ == "__main__":
    main()