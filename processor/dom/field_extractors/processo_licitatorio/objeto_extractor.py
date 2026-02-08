import re
import os

from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils

class ObjetoExtractor(BaseExtractor):
    field = "objeto"

    def extract_from_heuristic(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        pattern = r"\b(credenciamento|locacao|execucao|objeto|finalidade|objetivo|contratacao de)"
        matches = re.finditer(pattern, texto_normalizado)

        for match in matches:
            if match:
                pos_ponto = texto_normalizado.find('. ', match.start())

                if pos_ponto - match.end() > 50: 
                    objeto = texto_normalizado[match.start():pos_ponto].strip()
                    return objeto

        return None
    
        # ======================================================================================================================================================================
        # pattern = r"\b(objeto|finalidade|objetivo|lavra)\b"
        # pattern = r"\b(aquisicao|contratacao|registro de precos|credenciamento|prestacao|locacao|fornecimento|execucao|prestacao de servico|objeto|finalidade|objetivo|lavra)"
        # ======================================================================================================================================================================
        
        # texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        # texto_normalizado = Utils.normalize_text(texto)

        # pattern = r"\b(aquisicao|contratacao|registro de precos|credenciamento|prestacao|locacao|fornecimento|execucao|prestacao de servico|objeto|finalidade|objetivo|lavra)"
        # matches = re.finditer(pattern, texto_normalizado)

        # objetos = []
        # for match in matches:

        #     if match:
        #         pos_ponto = texto_normalizado.find('. ', match.start())

        #         if pos_ponto > match.end():
        #             objeto = texto_normalizado[match.end() + 1:pos_ponto].strip()

        #             if len(objeto) > 50:
        #                 objetos.append(objeto)

        # if objetos:
        #     objetos.sort(key = lambda x: len(x), reverse=True)
        #     return objetos[0]
         
        # return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        prompt = f"""
Você é um especialista em licitação brasileira. Sua tarefa é analisar o texto fonte abaixo e extrair o objeto do processo licitatório.

# Regras e Dicas:
1.  Ponto de Partida: O objeto é quase sempre introduzido por palavras-chave. Procure por termos como "Objeto:", "O objeto da presente licitação é:", "constitui objeto desta licitação a", "cujo objeto é a".
2.  Delimitação do Fim: A descrição do objeto geralmente termina quando um novo tópico administrativo começa. Pare a extração antes de encontrar termos como "Valor Estimado:", "Valor Máximo:", "Data e Hora:", "Local:", "Critério de Julgamento:", "Prazo de Entrega:", ou quando o parágrafo sobre o objeto claramente termina.
3.  Extração Literal: Mantenha o texto extraído exatamente como está no original, sem alterar ortografia, pontuação ou capitalização.
4.  Sem Inferência: Extraia apenas as informações explícitas. Não deduza, interprete ou complete o texto.
5.  Formato da Saída:
    - Se o objeto for encontrado, responda APENAS com o texto do objeto.
    - Se a informação não estiver clara ou presente, responda exatamente "null".

# TEXTO FONTE:
{texto_normalizado[:4000]}
"""
        
        response = Utils.ask_model(self, prompt, self.field, model="gemma3:4b")
        if response.get(self.field, None) != "null":
            return response.get(self.field, None)
        return None