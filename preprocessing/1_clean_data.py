# preprocessing/1_clean_data.py
import json
import pandas as pd
import yaml
import re
import logging
from pathlib import Path

# Get the parent directory of the current script
# parent_dir = Path(__file__).parent.parent parent_dir / 

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path= "config.yaml"):
    """Loads the YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found at {config_path}")
        raise
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        raise

def load_raw_data(file_path= "data/raw_records.json"):
    """
    Loads raw data from a JSON file.
    Assumes a list of dictionaries.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logging.info(f"Successfully loaded {len(data)} records from {file_path}")
        return data
    except FileNotFoundError:
        logging.error(f"Raw data file not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from {file_path}. Ensure it's a valid JSON list.")
        return []
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading raw data: {e}")
        return []

def validate_record(record, required_fields=['id', 'title', 'abstract']):
    """
    Validates a single record to ensure it has required fields and they are not empty.
    """
    for field in required_fields:
        if field not in record or not record[field]:
            # logging.warning(f"Record missing or has empty required field '{field}': {record.get('id', 'Unknown ID')}")
            return False
    return True

def normalize_text(text):
    """
    Basic text normalization: lowercase, remove extra whitespace.
    """
    if not isinstance(text, str):
        return "" # Return empty string for non-string inputs (e.g. NaN)
    text = text.lower()
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_data(raw_data, text_fields_to_normalize=['title', 'abstract']):
    """
    Cleans and normalizes the raw data.
    - Validates records.
    - Normalizes specified text fields.
    - Fills missing 'year' and 'journal' with placeholders.
    """
    cleaned_records = []
    valid_count = 0
    invalid_count = 0

    for record in raw_data:
        if not validate_record(record):
            invalid_count += 1
            logging.debug(f"Skipping invalid record: {record.get('id', 'Unknown ID')}")
            continue

        cleaned_record = record.copy() # Avoid modifying original dict in list

        for field in text_fields_to_normalize:
            if field in cleaned_record:
                cleaned_record[field] = normalize_text(cleaned_record[field])

        # Ensure 'year' and 'journal' exist, fill with defaults if not
        # Convert year to integer if possible, otherwise keep as is or use a placeholder
        year_val = cleaned_record.get('year')
        try:
            cleaned_record['year'] = int(year_val) if year_val else 0 # 0 or None as placeholder
        except (ValueError, TypeError):
            cleaned_record['year'] = 0 # Placeholder for unparseable years

        cleaned_record['journal'] = cleaned_record.get('journal', 'Unknown Journal')
        if not cleaned_record['journal']: # Handle empty string journal
             cleaned_record['journal'] = 'Unknown Journal'


        cleaned_records.append(cleaned_record)
        valid_count += 1

    logging.info(f"Data cleaning complete. Valid records: {valid_count}, Invalid/skipped records: {invalid_count}")
    return pd.DataFrame(cleaned_records)


def save_processed_data(df, file_path):
    """Saves the processed DataFrame to a Parquet file."""
    try:
        df.to_parquet(file_path, index=False)
        logging.info(f"Processed data saved to {file_path}")
    except Exception as e:
        logging.error(f"Error saving processed data to Parquet: {e}")
        raise

def main():
    """Main function to orchestrate data cleaning."""
    logging.info("Starting data cleaning process...")
    config = load_config()
    paths = config['paths']

    raw_data = load_raw_data(paths['raw_data'])
    if not raw_data:
        logging.warning("No raw data loaded. Exiting.")
        return

    df_processed = clean_data(raw_data, config['embedding_model']['text_fields_to_embed'])

    if df_processed.empty:
        logging.warning("No valid data after cleaning. Output file will not be created.")
        return

    save_processed_data(df_processed, paths['processed_data'])
    logging.info("Data cleaning process finished successfully.")

if __name__ == "__main__":
    main()