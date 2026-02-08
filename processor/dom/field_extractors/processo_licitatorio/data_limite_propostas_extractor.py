import re
from datetime import datetime

from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils

class DataLimitePropostasExtractor(BaseExtractor):
    field = "data_limite_propostas"

    patterns = [
        r"abertura*?sessao publica?",
        r"fim*?recebimento*?proposta?",
        r"entrega.*?proposta?",
        r"envelopes.*?recebidos?",
        r"apresentacao.*?proposta?",
        r"proposta.*?habilitacao?",
        r"propostas.*?:?",
        r"data.{0,5}encerramento"
    ]

    meses_num = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }

    def extract_from_heuristic(self, record):
        # texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        # texto_normalizado = Utils.normalize_text(texto)

        # for pattern in self.patterns:
        #     match = re.search(pattern, texto_normalizado)

        #     if match:
        #         texto_recebimento = texto_normalizado[match.end():match.end() + 100]
        #         pos_recebimento = texto_recebimento.find("ate")

        #         if pos_recebimento > -1:
        #             limite_recebimento = texto_recebimento[pos_recebimento:]

        #             pattern_data = r'\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b' 

        #             match_data_limite = re.search(pattern_data, limite_recebimento)

        #             if match_data_limite:
        #                 return match_data_limite.group()
                    
        #         pos_recebimento = texto_recebimento.find("dia")

        #         if pos_recebimento > -1:
        #             limite_recebimento = texto_recebimento[pos_recebimento:]

        #             pattern_data = r'\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b'

        #             match_data_limite = re.search(pattern_data, limite_recebimento)

        #             if match_data_limite:
        #                 return match_data_limite.group()

        # return None


        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        for pattern in self.patterns:
            matches = re.finditer(pattern, texto_normalizado)

            for match in matches:
                if match:

                    ponto = texto_normalizado.find(".", match.end())
                    texto_recebimento = texto_normalizado[match.end():max(match.end()+150, ponto)]
                    
                    pattern_data = r'\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})'

                    datas = re.findall(pattern_data, texto_recebimento)

                    if datas:
                        datas.sort(key=lambda data_str: datetime.strptime(data_str, "%d/%m/%Y"))
                        return datas[-1]
                    
                    # =============================================
                    pattern_data_extenso = r"\b(\d{1,2})\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})\b"
                    
                    datas = re.findall(pattern_data_extenso, texto_recebimento)
                    datas = [f"{data[0]}/{self.meses_num[data[1]]}/{data[2]}" for data in datas]

                    if datas:
                        datas.sort(key=lambda data_str: datetime.strptime(data_str, "%d/%m/%Y"))
                        return datas[-1]
                    # =============================================

        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        prompt = f"""
Você é especialista na análise de documentos de licitações públicas do Brasil. Sua função é extrair informações específicas de forma precisa e direta.
Analise o texto fonte fonte e extraia a data LIMITE (prazo final) para o envio/acolhimento das propostas.

A data que você procura está frequentemente associada a termos como: "Data limite para o recebimento das propostas", "Encerramento do prazo de envio", "Recebimento das propostas até o dia", 
"Acolhimento das propostas até às HH:MM do dia DD/MM/AAAA", "Prazo final para entrega da proposta" ou "As propostas serão recebidas até"

Regras de Extração:
1.  Delimitação da Data: Não confunda a data limite com a data de início do recebimento ou, mais importante, com a data de abertura da sessão pública.
1.  Extração Explícita: Extraia apenas a data que estiver explicitamente mencionada no texto. Não deduza, interprete ou calcule datas.
2.  Formatos de Data: A data no texto pode aparecer em formatos como `dd/mm/aaaa`, `dd-mm-aaaa` ou por extenso (ex: "24 de outubro de 2025").
3.  Normalização Obrigatória: Independentemente do formato original, a data extraída deve ser normalizada para o formato `DD-MM-YYYY`.
4.  Informação Ausente: Se a data limite para o envio de propostas não for encontrada ou não estiver clara no texto, retorne a palavra `null`.
5.  Formato de Saída: Sua resposta deve ser exclusivamente o texto da data no formato `DD-MM-YYYY` ou a palavra `null`. Não inclua nenhuma outra palavra, explicação ou pontuação.

### Exemplos de Entrada e Saída:

# Exemplo 1: Data limite

Texto Fonte:
PREGÃO ELETRÔNICO Nº 001/2025. Início do envio: 01/11/2025. Recebimento das propostas até o dia 10/11/2025 às 09:00h. Abertura da Sessão: 10/11/2025 às 09:01h.

Saída:
10/11/2025

# Exemplo 2: Data por extenso

Texto Fonte:
TOMADA DE PREÇOS Nº 005/2025. O prazo final para entrega da proposta será o dia 5 de dezembro de 2025. A abertura dos envelopes ocorrerá em seguida.

Saída:
05-12-2025

# Exemplo 3: Caso Nulo (Apenas data de abertura)

Texto Fonte:
CONCORRÊNCIA PÚBLICA Nº 002/2025. Data da Sessão de Abertura: 15/12/2025 às 10h00min (horário de Brasília). O edital pode ser retirado no site...

Saída:
null

# Exemplo 4: Data em formato de período

Texto Fonte:
PREGÃO Nº 007/2025. Período para envio da proposta: de 01-12-2025 até 15-12-2025. Abertura da disputa: 16/12/2025.

Saída:
15/12/2025

### Fim dos Exemplos

# Texto Fonte
{texto_normalizado[:4000]}
"""

        response = Utils.ask_model(self, prompt, self.field)
        if response.get(self.field, None) != 'null':
            return response.get(self.field, None)
        return