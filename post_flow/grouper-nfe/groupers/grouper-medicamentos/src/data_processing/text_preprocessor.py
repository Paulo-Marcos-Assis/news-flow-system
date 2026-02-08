import logging
from typing import List, Dict, Any

def preprocess_candidates(ner_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Recebe a lista de candidatos brutos do NER e a retorna, pois os dados já estão estruturados.
    Esta função existe para manter a consistência do pipeline, mas não realiza mais transformações.
    """
    logging.info(f"Pré-processando {len(ner_candidates)} candidatos do NER (pass-through).")
    # No-op: Os dados do NER já estão no formato de dicionário estruturado.
    return ner_candidates
