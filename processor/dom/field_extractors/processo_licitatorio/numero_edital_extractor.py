from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils
import re

class NumeroEditalExtractor(BaseExtractor):
    field = "numero_edital"

    modalidades_licitacao = {
        "convite": "Convite",
        "tomada": "Tomada de Preços",
        "concorrencia": "Concorrência",
        "leilao": "Leilão",
        "concurso": "Concurso",
        "pregao": "Pregão Presencial/Eletrônico",
        "dispensa": "Dispensa de Licitação",
        "inexigibilidade": "Inexigibilidade de Licitação"
    }

    def extract_from_heuristic(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = record.get("titulo", "")
        titulo_normalizado = Utils.normalize_text(titulo)

        pattern = r'(?<!\d/)\b\d+(?:/[A-Za-z]+)?/\d{4}\b'

        matches_texto = re.finditer(pattern, texto_normalizado)

        for match in matches_texto:
            numero = match.group()
            texto_numero = texto_normalizado[max(0, match.start() - 45):match.end()]

            for keywords, modalidade in self.modalidades_licitacao.items():
                if keywords in texto_numero:
                    return re.search(re.escape(numero), texto, re.IGNORECASE).group()

        matches_titulo = re.finditer(pattern, titulo_normalizado)

        for match in matches_titulo:
            numero = match.group()
            texto_numero = titulo_normalizado[max(0, match.start() - 40):match.end()]

            for keywords, modalidade in self.modalidades_licitacao.items():
                if keywords in texto_numero:
                    return re.search(re.escape(numero), titulo, re.IGNORECASE).group()

        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = Utils.extrair_primeira_pagina(record.get("titulo", ""))
        titulo_normalizado = Utils.normalize_text(titulo)

        pattern = r'(?<!\d/)\b\d+(?:/[A-Za-z]+)?/\d{4}\b'

        prompt = f"""
Aja como um especialista em extração de dados de documentos de licitação brasileiros. Sua tarefa é identificar e extrair o Número do Edital.

# Regras de Extração:
1.  Busca por Contexto: Primeiro, localize o número que está diretamente associado a palavras-chave que identificam um edital, como "Edital", "Pregão Eletrônico", "Concorrência", "Tomada de Preços", "Convite".
2.  Validação de Formato (Regex): O número encontrado na etapa 1 DEVE corresponder à seguinte expressão regular: `{pattern}`. Este padrão busca por um número seguido de uma barra e um ano de quatro dígitos (ex: "58/2025" ou "85/2024").
3.  Regra de Exclusão: Ignore ativamente qualquer número que, mesmo correspondendo ao regex, esteja claramente identificado como "Processo nº" ou "Processo Administrativo nº".
4.  Saída:
    - Se um número que satisfaz todas as regras for encontrado, responda APENAS com o número (ex: "58/2025").
    - Se nenhum número satisfizer todas as regras, responda exatamente "null".

### Exemplos de Entrada e Saída:
Exemplo 1: Número do Edital no Título

Título Fonte:
AVISO DE LICITAÇÃO - PREGÃO ELETRÔNICO Nº 025/2025

Texto Fonte:
Objeto: [...]. A licitação rege-se pelo Edital e pela Lei 14.133. Referente ao Processo Administrativo nº 100/2025.

Saída:
025/2025

# Exemplo 2: Número do Edital no Texto

Título Fonte:
AVISO DE ABERTURA DE LICITAÇÃO

Texto Fonte:
A Prefeitura torna pública a abertura da Concorrência nº 005/2024. Esta licitação obedece ao Processo nº 030/2024.

Saída:
005/2024

# Exemplo 3: Apenas Processo (Caso Nulo)

Título Fonte:
EXTRATO DE CONTRATO Nº 001/2025

Texto Fonte:
Contratante: [...]. Contratada: [...]. Originado do Processo nº 050/2025. Vigência: 12 meses.

Saída:
null

### Fim dos Exemplos

# Título Fonte:
{titulo_normalizado}

# Texto Fonte:
{texto_normalizado[:4000]}
"""

        response = Utils.ask_model(self,prompt,self.field)
        if response.get(self.field, None) != "null":
            return response.get(self.field, None)
        return None