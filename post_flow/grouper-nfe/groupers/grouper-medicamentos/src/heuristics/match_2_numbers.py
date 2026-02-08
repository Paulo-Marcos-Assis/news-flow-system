import re
import logging
from typing import List, Dict

def extrair_numeros(texto: str) -> List[str]:
    """
    Extrai todos os números únicos de uma string.
    """
    try:
        numeros_encontrados = re.findall(r'\d+', texto)
        return list(numeros_encontrados)
    except Exception as e:
        logging.error(f"Erro ao extrair números do texto: '{texto}'. Erro: {e}")
        return []

def contar_matches_de_numeros(texto: str, numeros: List[str]) -> int:
    """
    Conta quantos números de uma lista estão presentes no texto.
    """
    count = 0
    try:
        for num in numeros:
            if re.search(r'\b' + re.escape(num) + r'\b', texto):
                count += 1
        return count
    except Exception as e:
        logging.error(f"Erro ao contar matches de números no texto: '{texto}'. Erro: {e}")
        return 0

def apply_number_heuristic(description: str, candidates: List[Dict]) -> List[Dict]:
    """
    Aplica a heurística flexível de correspondência de números a uma única descrição e seus candidatos.
    """
    logging.info(f"--- Iniciando Heurística de Números para: '{description}' ---")
    
    target_numbers = extrair_numeros(description)
    if not target_numbers:
        logging.info("Nenhum número encontrado na descrição. Mantendo todos os candidatos.")
        return candidates
    
    logging.info(f"Números alvo extraídos da descrição: {target_numbers}")

    # Lógica de 2+ números
    if len(target_numbers) >= 2:
        logging.info(f"Tentando correspondência com 2 ou mais números de {target_numbers}.")
        filtered_candidates = []
        for candidate in candidates:
            info_str = candidate.get('info', '')
            matches = contar_matches_de_numeros(info_str, target_numbers)
            if matches >= 2:
                logging.debug(f"Candidato mantido (match >= 2): {candidate.get('registro')} com info: {info_str}")
                filtered_candidates.append(candidate)
        
        if filtered_candidates:
            logging.info(f"Heurística de 2+ números encontrou {len(filtered_candidates)} correspondências.")
            logging.info("--- Fim da Heurística de Números ---")
            return filtered_candidates
        else:
            logging.info("Nenhuma correspondência encontrada com a lógica de 2+ números.")

    # Fallback para lógica de 1 número (se a de 2+ falhou ou se só havia 1 número)
    logging.info(f"Tentando correspondência com pelo menos 1 número de {target_numbers}.")
    filtered_candidates = []
    # Create a single regex for efficiency
    padrao_regex = r'\b(' + '|'.join(map(re.escape, target_numbers)) + r')\b'
    for candidate in candidates:
        info_str = candidate.get('info', '')
        if re.search(padrao_regex, info_str):
            logging.debug(f"Candidato mantido (match >= 1): {candidate.get('registro')} com info: {info_str}")
            filtered_candidates.append(candidate)

    if not filtered_candidates:
        logging.warning("Nenhuma correspondência de números encontrada. Mantendo todos os candidatos originais para evitar perda.")
        logging.info("--- Fim da Heurística de Números ---")
        return candidates

    logging.info(f"Heurística de 1+ número encontrou {len(filtered_candidates)} correspondências.")
    logging.info("--- Fim da Heurística de Números ---")
    return filtered_candidates
