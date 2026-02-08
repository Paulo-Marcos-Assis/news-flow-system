import logging
import re
import time
from typing import Tuple, Dict, Any
import json
import os

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama


def parse_model_output(output: str) -> Tuple[str, str]:
    """
    Extrai o conteúdo das tags <think> e <answer> da saída do modelo.
    Prioriza a extração de id_grupo se presente na tag <answer>.
    """
    reasoning_match = re.search(r"<think>(.*?)</think>", output, re.DOTALL | re.IGNORECASE)
    answer_match = re.search(r"<answer>(.*?)</answer>", output, re.DOTALL | re.IGNORECASE)

    think = reasoning_match.group(1).strip() if reasoning_match else ""
    answer = "0" # Default answer

    if answer_match:
        extracted_answer = answer_match.group(1).strip()
        # Try to find an integer (id_grupo) in the answer
        id_grupo_match = re.search(r'\b(\d+)\b', extracted_answer)
        if id_grupo_match:
            answer = id_grupo_match.group(1)
        else:
            answer = extracted_answer # Fallback to the full extracted answer if no integer found
    
    if not reasoning_match and not answer_match:
        logging.warning("Não foi possível parsear a saída do modelo. Nenhuma tag <think> ou <answer> encontrada. Usando estratégia de fallback.")
        think, answer = _parse_fallback_strategy(output)

    return think, answer


def _parse_fallback_strategy(output: str) -> Tuple[str, str]:
    """
    Estratégia de parsing de fallback quando as tags <think> e <answer> estão ausentes.
    Tenta encontrar um número (id_grupo) na saída.
    """
    # Tenta encontrar qualquer número na saída como fallback para id_grupo
    matches = re.findall(r'\b(\d+)\b', output)
    
    if matches:
        answer = matches[-1] # Pega o último número encontrado
        think = f"Fallback: Resposta (id_grupo) extraída da saída bruta. Saída completa: {output.strip()}"
    else:
        think = f"Fallback: Nenhuma resposta (id_grupo) encontrada. Saída completa: {output.strip()}"
        answer = "0"
        
    return think, answer

def get_llm_link(description: str, candidates: list, llm: ChatOllama, prompt_template: str) -> Tuple[str, str, Dict[str, Any]]:
    """
    Realiza o entity linking usando o LLM para uma única descrição.
    Retorna a resposta final, o processo de pensamento e as métricas.
    """
    logging.info(f"Realizando o linking com LLM para: {description}")

    metrics = {
        'latency': 0,
        'input_tokens': 0,
        'output_tokens': 0,
        'total_tokens': 0
    }

    if not candidates:
        think = "LLM não foi chamado: Nenhum candidato foi fornecido."
        logging.info(think)
        return "0", think, metrics

    # Verifica se todos os candidatos têm o mesmo id_grupo
    all_id_grupos = set()
    for cand in candidates:
        id_grupo = cand.get('id_grupo')
        if isinstance(id_grupo, list) and id_grupo:
            all_id_grupos.add(str(id_grupo[0]))
        elif id_grupo:
            all_id_grupos.add(str(id_grupo))

    if len(all_id_grupos) == 1:
        final_answer = all_id_grupos.pop()
        think = "LLM não foi chamado: Todos os candidatos pertencem ao mesmo id_grupo."
        logging.info(think)
        return final_answer, think, metrics

    if len(candidates) == 1:
        candidate = candidates[0]
        id_grupo = candidate.get('id_grupo')
        if isinstance(id_grupo, list) and id_grupo:
            final_answer = str(id_grupo[0])
        else:
            final_answer = str(id_grupo) if id_grupo else "0"
        
        think = "LLM não foi chamado: Apenas um candidato estava disponível."
        logging.info(think)
        return final_answer, think, metrics

    candidates_str = str(candidates).replace(", ", ",\n")
    prompt = prompt_template.format(description=description, candidates=candidates_str)
    response_content = ""

    try:
        start_time = time.time()
        response = llm.invoke([HumanMessage(content=prompt)])
        end_time = time.time()
        
        metrics['latency'] = end_time - start_time
        response_content = response.content

        usage_info = response.usage_metadata
        if usage_info:
            metrics['input_tokens'] = usage_info.get('input_tokens', 0)
            metrics['output_tokens'] = usage_info.get('output_tokens', 0)
            metrics['total_tokens'] = usage_info.get('total_tokens', 0)

        logging.info(f"LLM response: {response_content}")
        
    except Exception as e:
        logging.error(f"Erro ao chamar o modelo para a descrição '{description}': {e}")
        response_content = ""

    think, final_answer = parse_model_output(response_content)

    logging.info(f"Explicabilidade: {think}")
    logging.info(f"Resposta Final: {final_answer}")
    
    return final_answer, think, metrics