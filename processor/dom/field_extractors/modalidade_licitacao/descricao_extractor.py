from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils


class ModalidadeExtractor(BaseExtractor):
    field = "descricao"

    modalidades_licitacao = {
        "convite": "Convite",
        "tomada de preco": "Tomada de Preços",
        "concorrencia": "Concorrência",
        "leilao": "Leilão",
        "pregao eletronico": "Pregão Eletrônico",
        "pregao presencial": "Pregão Presencial",
        "inexigibilidade": "Inexigibilidade de Licitação",
        "dispensa": "Dispensa de Licitação",
        "chamada publica": "Chamada Pública",
        "concurso": "Concurso"
    }


    def extract_from_heuristic(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = record.get("titulo", "")
        titulo_normalizado = Utils.normalize_text(titulo)

        for keywords, modalidade in self.modalidades_licitacao.items():
            if keywords in titulo_normalizado or keywords in texto_normalizado:
                return modalidade

        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = Utils.extrair_primeira_pagina(record.get("titulo", ""))
        titulo_normalizado = Utils.normalize_text(titulo)

        prompt = f"""
Aja como um especialista em licitação brasileira. Sua tarefa é classificar o documento abaixo em UMA das seguintes modalidades: {sorted(set(self.modalidades_licitacao.values()))}.

# Regras:
1.  Prioridade: A modalidade principal é geralmente a primeira a ser mencionada de forma destacada no texto. Procure por termos como "AVISO DE LICITAÇÃO - PREGÃO ELETRÔNICO" ou "Modalidade: Concorrência".
2.  Escolha Única: Sua resposta deve ser apenas UMA das modalidades da lista.
3.  Sem Inferência: A classificação deve ser baseada estritamente no texto fornecido. Não interprete ou deduza.
4.  Formato da Saída:
    - Se uma modalidade da lista for identificada, responda APENAS com o nome EXATO dela (ex: "Pregão Eletrônico").
    - Caso nenhuma das modalidades da lista seja encontrada no texto, responda exatamente "null".

### Exemplos de Entrada e Saída:

# Exemplo 1:

Texto fonte:
PREGÃO ELETRÔNICO N.º 08/2024

Saída:
Pregão Eletrônico

# Exemplo 2

Texto fonte: 
Concorrência Nº 2/2024 PROCESSO ADMINISTRATIVO Nº 24/2024

Saída:
Concorrência

# Exemplo 3

Texto fonte:
INEXIGIBILIDADE Nº. 01/2024

Saída:
Inexigibilidade de Licitação

### Fim dos Exemplos

# Texto fonte:
{texto_normalizado}
"""[:4000]

        response = Utils.ask_model(self, prompt, self.field)

        modalidade = response.get(self.field, None)

        return modalidade
