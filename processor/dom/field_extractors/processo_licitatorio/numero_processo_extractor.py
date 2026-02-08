from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils
import re

class NumeroProcessoExtractor(BaseExtractor):
    field = "numero_processo"

    def extract_from_heuristic(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = record.get("titulo", "")
        titulo_normalizado = Utils.normalize_text(titulo)

        pattern = r'(?<!\d/)\b\d+(?:/[A-Za-z]+)?/\d{4}\b'

        matches_titulo = re.finditer(pattern, titulo_normalizado)

        for match in matches_titulo:
            numero = match.group()
            texto_numero = titulo_normalizado[max(0, match.start() - 40):match.end()]

            if "processo" in texto_numero:
                return re.search(re.escape(numero), titulo, re.IGNORECASE).group()

        matches_texto = re.finditer(pattern, texto_normalizado)

        for match in matches_texto:
            numero = match.group()
            texto_numero = texto_normalizado[max(0, match.start() - 40):match.end()]

            if "processo" in texto_numero:
                return re.search(re.escape(numero), texto, re.IGNORECASE).group()

        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = Utils.extrair_primeira_pagina(record.get("titulo", ""))
        titulo_normalizado = Utils.normalize_text(titulo)

        pattern = r'(?<!\d/)\b\d+(?:/[A-Za-z]+)?/\d{4}\b'
        
        prompt = f"""
Aja como um especialista em extração de dados de documentos de licitação brasileiros. 
Sua tarefa é identificar e extrair o número do processo licitatório ou administrativo a partir do título e do texto fornecidos.

# Regras:
1.  O número do processo geralmente segue padrões como "Nº 40/2025". Procure por números associados a palavras-chave como "Processo" ou "Processo Administrativo".
2.  Use a seguinte expressão regular para validar o formato do número: '{pattern}'. Dê prioridade a números que correspondam a esses padrões.
3.  Não invente ou deduza informações. A extração deve ser literal do texto.
4.  Se o número for encontrado, responda APENAS com o número extraído (ex: "63/2025").
5.  Se nenhum número correspondente às regras for encontrado no título ou no texto, responda exatamente "null".

### Exemplos de Entrada e Saída:

# Exemplo 1: Número no texto

Título Fonte:
PREGÃO ELETRÔNICO Nº 123/2025

Texto Fonte:
Objeto: [...]. A presente licitação rege-se pela Lei 14.133/2021. Processo Administrativo nº 46/2025. Data da sessão: 10/11/2025.

Saída:
46/2025

# Exemplo 2: Número no título

Título Fonte:
AVISO DE LICITAÇÃO - PREGÃO Nº 002/2025 - PROCESSO Nº 034/2025

Texto Fonte:
A Prefeitura Municipal torna público o Pregão nº 002/2025. Objeto: aquisição de materiais.

Saída:
034/2025

# Exemplo 3: Apenas número da licitação (Caso Nulo)

Título Fonte:
TOMADA DE PREÇOS Nº 005/2025

Texto Fonte:
A comissão de licitação informa a abertura da Tomada de Preços nº 005/2025. O edital está disponível no site.

Saída:
null

### Fim dos Exemplos

# Título Fonte:
{titulo_normalizado}

# Texto Fonte:
{texto_normalizado}
"""[:4000]

        response = Utils.ask_model(self,prompt,self.field)
        if response.get(self.field, None) != "null":
            return response.get(self.field, None)
        return None