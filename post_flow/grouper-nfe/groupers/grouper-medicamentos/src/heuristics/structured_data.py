import logging
import re
import json
import copy
import os
from src.utils.get_config import get_data_paths

class DrugDataProcessor:
    """
    Uma classe para processar e deduplicar dados de medicamentos já estruturados.
    """
    def __init__(self):
        """
        Inicializa o processador.
        """
        logging.info("Inicializando o DrugDataProcessor...")
        logging.info("DrugDataProcessor inicializado. A estruturação de dados não é mais necessária.")

    def _deduplicate(self, structured_data: dict) -> dict:
        """
        Remove candidatos duplicados com base em todos os campos, exceto 'registro' e 'id_grupo'.
        """
        deduplicated_data = {}
        for drug_key, candidates_list in structured_data.items():
            logging.info(f"--- Iniciando Deduplicação para '{drug_key}' com {len(candidates_list)} candidatos ---")
            
            seen_keys = {} # Store the key and the registro of the first item seen
            unique_candidates = []
            
            for i, candidate_dict in enumerate(candidates_list):
                dedupe_key_items = []
                for k, v in candidate_dict.items():
                    if k not in ['registro', 'id_grupo', 'id', 'score', 'info']:
                        if isinstance(v, list):
                            dedupe_key_items.append((k, tuple(v)))
                        else:
                            dedupe_key_items.append((k, v))
                
                dedupe_key = frozenset(dedupe_key_items)
                
                # Log the key for the first candidate for debugging
                if i == 0:
                    logging.debug(f"Exemplo de chave de deduplicação (do primeiro candidato): {dict(dedupe_key)}")

                if dedupe_key not in seen_keys:
                    seen_keys[dedupe_key] = candidate_dict.get('registro')
                    unique_candidates.append(candidate_dict)
                else:
                    original_registro = seen_keys[dedupe_key]
                    logging.info(f"Candidato duplicado descartado: registro {candidate_dict.get('registro')} é um duplicado do registro {original_registro}.")

            logging.info(f"Deduplicação para '{drug_key}' finalizada: {len(candidates_list)} candidatos originais -> {len(unique_candidates)} únicos.")
            deduplicated_data[drug_key] = unique_candidates
        logging.info("--- Fim da Deduplicação ---")
        return deduplicated_data

    def run_pipeline(self, raw_data: dict) -> dict:
        """
        Executa o pipeline completo de deduplicação.
        
        Args:
            raw_data: O dicionário com os dados brutos (já estruturados).
            
        Returns:
            O dicionário final com os dados processados.
        """
        logging.info("--- INICIANDO PIPELINE DE DADOS ESTRUTURADOS (DEDUPLICAÇÃO) ---")
        
        final_data = self._deduplicate(raw_data)
        
        logging.info("--- PIPELINE DE DADOS ESTRUTURADOS FINALIZADO ---")
        return final_data

