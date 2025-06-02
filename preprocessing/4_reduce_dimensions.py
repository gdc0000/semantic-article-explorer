# preprocessing/4_reduce_dimensions.py
import pandas as pd
import numpy as np
from umap import UMAP
import yaml
import logging

from pathlib import Path

# Get the parent directory of the current script
# parent_dir = Path(__file__).parent.parent parent_dir / 

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path= "config.yaml"):
    """Loads the YAML configuration file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def load_embeddings(file_path):
    """Loads embeddings from a .npy file."""
    try:
        embeddings = np.load(file_path)
        logging.info(f"Embeddings loaded from {file_path}. Shape: {embeddings.shape}")
        return embeddings
    except FileNotFoundError:
        logging.error(f"Embeddings file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading embeddings: {e}")
        raise

def load_processed_data(file_path):
    """Loads processed data (metadata) from a Parquet file."""
    try:
        df = pd.read_parquet(file_path)
        logging.info(f"Processed data loaded from {file_path}. Shape: {df.shape}")
        return df
    except FileNotFoundError:
        logging.error(f"Processed data file not found: {file_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading processed data: {e}")
        raise

def reduce_dimensions_umap(embeddings, umap_params):
    """
    Reduces dimensionality of embeddings using UMAP.
    """
    if embeddings.shape[0] == 0:
        logging.warning("No embeddings provided for dimensionality reduction.")
        return None

    try:
        reducer = UMAP(
            n_neighbors=umap_params['n_neighbors'],
            min_dist=umap_params['min_dist'],
            n_components=umap_params['n_components'],
            metric=umap_params['metric'],
            random_state=umap_params.get('random_state', 42), # Ensure reproducibility
            verbose=True
        )
        logging.info(f"Starting UMAP dimensionality reduction to {umap_params['n_components']} components...")
        reduced_embeddings = reducer.fit_transform(embeddings)
        logging.info(f"UMAP reduction complete. Reduced shape: {reduced_embeddings.shape}")
        return reduced_embeddings
    except Exception as e:
        logging.error(f"Error during UMAP dimensionality reduction: {e}")
        raise

def add_coordinates_to_dataframe(df, reduced_embeddings, n_components):
    """
    Adds the reduced dimension coordinates (x, y, possibly z) to the DataFrame.
    """
    if reduced_embeddings is None or df.shape[0] != reduced_embeddings.shape[0]:
        logging.error("Mismatch in DataFrame rows and reduced embeddings or no embeddings.")
        return df # Return original df

    df['x'] = reduced_embeddings[:, 0]
    df['y'] = reduced_embeddings[:, 1]
    if n_components == 3 and reduced_embeddings.shape[1] == 3:
        df['z'] = reduced_embeddings[:, 2]
    elif n_components == 3 and reduced_embeddings.shape[1] != 3:
        logging.warning("Requested 3D UMAP but got different number of components. Z-coordinate will not be added.")

    logging.info("Added UMAP coordinates (x, y" + (", z" if n_components == 3 and 'z' in df.columns else "") + ") to DataFrame.")
    return df

def save_data_with_coordinates(df, file_path):
    """Saves the DataFrame (now with coordinates) back to Parquet."""
    try:
        df.to_parquet(file_path, index=False)
        logging.info(f"DataFrame with coordinates saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving DataFrame with coordinates: {e}")
        raise

def main():
    """Main function to orchestrate dimensionality reduction."""
    logging.info("Starting dimensionality reduction process...")
    config = load_config()
    paths_config = config['paths']
    umap_config = config['umap_params']

    embeddings = load_embeddings(paths_config['embeddings'])
    if embeddings is None or embeddings.shape[0] == 0:
        logging.warning("No embeddings loaded. Cannot perform dimensionality reduction.")
        return

    df_processed = load_processed_data(paths_config['processed_data'])
    if df_processed.empty:
        logging.warning("Processed data is empty. Cannot add coordinates.")
        return

    if len(df_processed) != len(embeddings):
        logging.error(f"Mismatch between number of records in processed data ({len(df_processed)}) and number of embeddings ({len(embeddings)}). Aborting.")
        return

    reduced_embeddings = reduce_dimensions_umap(embeddings, umap_config)

    if reduced_embeddings is not None:
        df_with_coords = add_coordinates_to_dataframe(df_processed, reduced_embeddings, umap_config['n_components'])
        save_data_with_coordinates(df_with_coords, paths_config['processed_data']) # Overwrite with new columns
        logging.info("Dimensionality reduction process finished successfully.")
    else:
        logging.warning("Dimensionality reduction failed or produced no output.")


if __name__ == "__main__":
    main()