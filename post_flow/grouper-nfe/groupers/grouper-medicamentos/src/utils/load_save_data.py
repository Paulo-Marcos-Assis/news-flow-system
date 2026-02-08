import pandas as pd
import logging
import sys
import os
import json

def load_csv_data(path: str) -> pd.DataFrame:
    """
    Loads data from a CSV file into a pandas DataFrame.

    Args:
        path (str): The path to the CSV file.

    Returns:
        pd.DataFrame: The loaded DataFrame.
    """
    try:
        logging.info(f"Loading data from: {path}")
        df = pd.read_csv(path)
        logging.info("Data loaded successfully.")
        return df
    except FileNotFoundError:
        logging.error(f"Error: File not found at {path}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An error occurred while loading the data: {e}")
        sys.exit(1)

def save_dataframe_to_csv(df: pd.DataFrame, output_path: str):
    """
    Saves the DataFrame to a CSV file.

    Args:
        df (pd.DataFrame): The DataFrame to save.
        path (str): The path to save the file to.
    """
    try:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        logging.info(f"Saving cleaned data to: {output_path}")
        df.to_csv(output_path, index=False, encoding='utf-8')
        logging.info("Data saved successfully.")
    except Exception as e:
        logging.error(f"Failed to save data to {output_path}: {e}")
        sys.exit(1)

def save_json_data(data: list, output_path: str):
    """
    Saves a list of dictionaries to a JSON file.
    """
    try:
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        logging.info(f"Salvando dados JSON em: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logging.info("Dados JSON salvos com sucesso.")
    except Exception as e:
        logging.error(f"Falha ao salvar dados JSON em {output_path}: {e}")
        sys.exit(1)