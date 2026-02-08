import re

from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils
from datetime import datetime

class DataAberturaPropostasExtractor(BaseExtractor):
    field = "data_abertura_propostas"

    patterns = [
        r"abertura*?sessao?",
        r"abertura*?envelope?",
        r"inicio*?recebimento*?proposta?",
        r"entrega.*?proposta?",
        r"envelopes.*?recebidos?",
        r"apresentacao.*?proposta?",
        r"proposta.*?habilitacao?",
        r"propostas.*?:?",
        r"data.{0,5}abertura"
    ]

    meses_num = {
        'janeiro': '01', 'fevereiro': '02', 'março': '03', 'abril': '04',
        'maio': '05', 'junho': '06', 'julho': '07', 'agosto': '08',
        'setembro': '09', 'outubro': '10', 'novembro': '11', 'dezembro': '12'
    }

    def extract_from_heuristic(self, record):
        # texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        # texto_normalizado = Utils.normalize_text(texto)

        # pattern = r"abertura.*?propostas?"
        # match = re.search(pattern, texto_normalizado)

        # if match:
        #     texto_abertura_proposta = texto_normalizado[match.end():match.end() + 75]

        #     pattern_data = r'\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b'

        #     match_data_abertura = re.search(pattern_data, texto_abertura_proposta)

        #     if match_data_abertura:
        #         return match_data_abertura.group()

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
                    
                    # ===================================
                    pattern_data_extenso = r"\b(\d{1,2})\s+de\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)\s+de\s+(\d{4})\b"
                    
                    datas = re.findall(pattern_data_extenso, texto_recebimento)
                    datas = [f"{data[0]}/{self.meses_num[data[1]]}/{data[2]}" for data in datas]

                    if datas:
                        datas.sort(key=lambda data_str: datetime.strptime(data_str, "%d/%m/%Y"))
                        return datas[-1]
                    # ===================================
        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        prompt = f"""
Aja como um especialista em licitação brasileira. Sua tarefa é extrair a Data de Abertura das Propostas do texto abaixo e formatá-la como DD/MM/AAAA.

# Regras e Dicas:
1.  Foco na Data Correta: A data que você deve extrair é a da "Sessão Pública" ou "Abertura das Propostas". Ela é geralmente encontrada após termos como "Abertura das Propostas:", "Data da Sessão:", "Data de Abertura:", "recebimento de propostas até o dia", "data do certame".
2.  Normalização Obrigatória: Você DEVE converter a data encontrada para o formato DD/MM/AAAA.
    - Se estiver por extenso (ex: "28 de outubro de 2025"), converta para "28/10/2025".
    - Se usar outros separadores (ex: "28.10.2025"), converta para "28/10/2025".
3.  Ignorar Horário: Extraia apenas a data. Ignore qualquer informação de horário que a acompanhe (ex: "às 09h00min").
4.  Ignorar Outras Datas: O texto pode conter outras datas (data de publicação, data da assinatura, etc). Ignore-as e foque apenas na data de abertura do certame.
5.  Formato da Saída:
    - Se a data for encontrada e normalizada, responda APENAS com a data no formato DD/MM/AAAA.
    - Se a data não for encontrada, responda exatamente "null".

### Exemplos de Entrada e Saída:

Exemplo 1: Data por extenso

Texto Fonte:
TOMADA DE PREÇOS N° 002/2025. O recebimento dos envelopes ocorrerá até o dia 4 de novembro de 2025, com a abertura da sessão pública na mesma data.

Saída:
04/11/2025

Exemplo 2: Data com separador

Texto Fonte:
INEGIXIBILIDADE N° 67/2025. Data de abertura do certame: 17/03/2025. Local: Sala de Reuniões.

Saída:
17/03/2025

Exemplo 3: Data com outro separador

Texto Fonte:
CONCORRÊNCIA PÚBLICA N° 003/2025. Data de abertura do certame: 20.12.2025.

Saída:
20/12/2025

Exemplo 3: Nenhuma data de abertura encontrada

Texto Fonte:
EXTRATO DE CONTRATO N° 123/2025. Partes: União e Empresa XYZ. Objeto: [...]. Data da Assinatura: 10/10/2025. Vigência: 12 meses.

Saída:
null

### Fim dos Exemplos

# Texto Fonte:
{texto_normalizado[:4000]}
"""

        response = Utils.ask_model(self, prompt, self.field)
        if response.get(self.field, None) != "null":
            return response.get(self.field, None)
        return None