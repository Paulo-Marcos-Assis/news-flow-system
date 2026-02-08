import logging
from typing import List
from utils.load_save_data import load_csv_data

def load_golden_descriptions(file_path: str, sample_size: int = None) -> List[str]:
    """
    Carrega o dataset golden e extrai as descrições.
    """
    logging.info(f"Carregando descrições do dataset golden de: {file_path}")
    df = load_csv_data(file_path)
    if 'description' not in df.columns:
        logging.error("A coluna 'description' não foi encontrada no CSV.")
        return []
    
    if sample_size:
        logging.info(f"Realizando amostragem de {sample_size} registros.")
        df = df.sample(n=sample_size, random_state=42)

    descriptions = df['description'].dropna().tolist()
    logging.info(f"{len(descriptions)} descrições carregadas do dataset.")
    return descriptions
