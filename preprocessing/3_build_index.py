# preprocessing/3_build_index.py
import numpy as np
import faiss
import yaml
import logging

from pathlib import Path

# Get the parent directory of the current script
parent_dir = Path(__file__).parent.parent

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path=parent_dir / "config.yaml"):
    """Loads the YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_embeddings(file_path):
    """Loads embeddings from a .npy file."""
    try:
        embeddings = np.load(file_path)
        # FAISS expects float32
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        logging.info(f"Embeddings loaded from {file_path}. Shape: {embeddings.shape}")
        return embeddings
    except FileNotFoundError:
        logging.error(f"Embeddings file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading embeddings: {e}")
        raise

def build_faiss_index(embeddings, index_type="IndexFlatL2"):
    """
    Builds a FAISS index from embeddings.
    index_type: A string like "IndexFlatL2", "IndexFlatIP", or a factory string.
    """
    if embeddings.shape[0] == 0:
        logging.warning("No embeddings provided to build index.")
        return None

    dimension = embeddings.shape[1]
    try:
        # For simple index types like IndexFlatL2 or IndexFlatIP
        if index_type == "IndexFlatL2":
            index = faiss.IndexFlatL2(dimension)
        elif index_type == "IndexFlatIP":
            index = faiss.IndexFlatIP(dimension)
        else:
            # For more complex indices specified by a factory string
            # e.g., "IVF256,Flat" or "PCA64,IVF256,PQ8"
            # This requires training if it's not a flat index.
            # For simplicity, this example focuses on flat indices.
            # If using a factory string for non-flat indices, you'd need:
            # if not index.is_trained: index.train(embeddings)
            index = faiss.index_factory(dimension, index_type)
            logging.info(f"Using FAISS index factory for type: {index_type}")


        if not index.is_trained and index_type not in ["IndexFlatL2", "IndexFlatIP"]: # Flat indices don't need training
             logging.info(f"Training FAISS index of type {index_type}...")
             index.train(embeddings)
             logging.info("FAISS index training complete.")


        index.add(embeddings)
        logging.info(f"FAISS index built with {index.ntotal} vectors. Index type: {index_type}")
        return index
    except Exception as e:
        logging.error(f"Error building FAISS index: {e}")
        raise

def save_faiss_index(index, file_path):
    """Saves the FAISS index to a file."""
    if index is None:
        logging.warning("FAISS index is None, nothing to save.")
        return
    try:
        faiss.write_index(index, file_path)
        logging.info(f"FAISS index saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving FAISS index: {e}")
        raise

def main():
    """Main function to orchestrate FAISS index building."""
    logging.info("Starting FAISS index building process...")
    config = load_config()
    paths_config = config['paths']
    faiss_config = config['faiss_params']

    embeddings = load_embeddings(paths_config['embeddings'])
    if embeddings is None or embeddings.shape[0] == 0:
        logging.warning("No embeddings loaded. Cannot build FAISS index.")
        return

    faiss_index = build_faiss_index(embeddings, faiss_config['index_type'])
    save_faiss_index(faiss_index, paths_config['faiss_index'])
    logging.info("FAISS index building process finished successfully.")

if __name__ == "__main__":
    main()