import re

from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils

class DataInicioPropostasExtractor(BaseExtractor):
    field= "data_inicio_propostas"

    def extract_from_heuristic(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        pattern = r"recebimento.*?propostas?"
        match = re.search(pattern, texto_normalizado)

        if match:
            texto_recebimento = texto_normalizado[match.end():match.end() + 75]
            pos_recebimento = texto_recebimento.find("ate")

            if pos_recebimento > -1:
                inicio_recebimento = texto_recebimento[:pos_recebimento]  

                pattern_data = r'\b(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})\b'

                match_data_inicio = re.search(pattern_data, inicio_recebimento)

                if match_data_inicio:
                    return match_data_inicio.group()

        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        prompt = f"""
Você é um especialista em documentos de licitações públicas do Brasil. Sua função é extrair informações específicas de forma precisa e direta.
Analise o texto fonte e extraia a data de início do período para envio/acolhimento das propostas.

A data que você procura está frequentemente associada a termos como: "Início do acolhimento das propostas", "Abertura do prazo para envio das propostas", "Entrega da Proposta: a partir de",
"Data de início do recebimento das propostas" ou "Período para envio da proposta: de DD/MM/AAAA até..."

Regras de Extração e dicas:
1.  Delimitação da Data Alvo: Não confunda esta data com a data de abertura da sessão pública, data de publicação do edital ou data limite para entrega. Você deve encontrar o início do prazo.
2.  Extração Explícita: Extraia apenas a data que estiver explicitamente mencionada no texto. Não deduza, interprete ou calcule datas.
3.  Formatos de Data: A data no texto pode aparecer em formatos como `dd/mm/aaaa`, `dd-mm-aaaa` ou por extenso (ex: "24 de outubro de 2025").
4.  Normalização Obrigatória: Independentemente do formato original, a data extraída deve ser normalizada para o formato `DD-MM-YYYY`.
5.  Informação Ausente: Se a data de início do envio de propostas não for encontrada ou não estiver clara no texto, retorne a palavra `null`.
6.  Formato de Saída: Sua resposta deve ser exclusivamente o texto da data


### Exemplos de Entrada e Saída:

# Exemplo 1: Data com separador /

Texto Fonte:
AVISO DE PREGÃO ELETRÔNICO Nº 123/2025. Objeto: [...]. Início do acolhimento das propostas: 28/10/2025 às 08:00h. Abertura da Sessão: 10/11/2025 às 09:00h.

Saída:
28/10/2025

# Exemplo 2: Data por extenso

Texto Fonte:
TOMADA DE PREÇOS Nº 005/2025. Entrega da Proposta: a partir de 4 de novembro de 2025. Data da sessão pública: 20 de novembro de 2025.

Saída:
04/11/2025

# Exemplo 3: Caso Nulo (Apenas data de abertura)

Texto Fonte:
CONCORRÊNCIA PÚBLICA Nº 002/2025. Data da Sessão: 15/12/2025 às 10h00min (horário de Brasília). O edital pode ser retirado no site...

Saída:
null

# Exemplo 4: Data em formato de período

Texto Fonte:
PREGÃO Nº 007/2025. Período para envio da proposta: de 01-12-2025 até 15-12-2025. Abertura: 16/12/2025.

Saída:
01/12/2025

### Fim dos Exemplos

# Texto Fonte
{texto_normalizado[:4000]}
"""



#         prompt = f"""
# - Papel: Você é um especialista em licitação brasileira.
# - Tarefa: Analise o texto fonte {texto_normalizado} e identifique se ele contém a data de início de envio das propostas.
# - Regras:
#     1. Padrão: a data de início de envio das propostas possui o padrão \b(\d{2}\/\d{2}\/\d{4}|\d{2}-\d{2}-\d{4})\b.
#     2. Sem inferência: extraia apenas informações explícitas. Não deduza, interprete ou complete.
#     3. Extração exata: mantenha o texto como está, sem alterar ortografia, pontuação ou capitalização.
#     4. Campos opcionais: se a informação não estiver clara ou presente, retorne null.
#"""

#         prompt = f"""
# Você é um especialista em licitação brasileira.
#
# A partir do seguinte texto, extraia a data e a hora de início de envio das propostas de licitação no # Contexto.
#
# - Texto: {texto_normalizado}
#
# - Data de início de envio das propostas [string|null] \b(\d{2}\/\d{2}\/\d{4}|\d{2}-\d{2}-\d{4})\b
#
# # Regras
# - Sem inferência: extraia apenas informações explícitas. Não deduza, interprete ou complete.
# - Extração exata: mantenha o texto como está, sem alterar ortografia, pontuação ou capitalização.
# - Campos opcionais: se a informação não estiver clara ou presente, retorne null.
# - Formatos obrigatórios: respeite os formatos definidos. Se estiver incorreto, retorne null.
#
# # Contexto
# """

        response = Utils.ask_model(self, prompt, self.field)
        if response.get(self.field, None) != 'null':
            return response.get(self.field, None)
        return