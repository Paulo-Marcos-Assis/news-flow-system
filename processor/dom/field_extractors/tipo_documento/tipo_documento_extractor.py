from service_essentials.utils.utils import Utils
from ..base_extractor import BaseExtractor
import re

class TipoDocumentoExtractor(BaseExtractor):
    field = "tipo_documento"

    tipos_documentos = {
        "resolve adjudicar"                   : "Termo de Adjudicação",

        r'errata\s+do\s+(.{0,20}?)\s+termo\s+aditivo' : "Retificação de Termo Aditivo",

        "termo aditivo"                       : "Termo Aditivo",

        "termo de credenciamento"             : "Termo de Credenciamento",

        "errata de edital"                    : "Retificação de Edital",
        "errata do edital"                    : "Retificação de Edital",
        "errata ao edital"                    : "Retificação de Edital",

        "retificacao de termo de homologacao" : "Retificação de Homologação",
        "retificacao do termo de homologacao" : "Retificação de Homologação",
        "retificacao termo de homologacao"    : "Retificação de Homologação",

        r'termo\s+de\s+formalizacao(.{0,10}?)retificacao'         : "Retificação de Termo de Formalização",

        r'aviso\s+de\s+contratacao\s+direta(.{0,10}?)retificacao' : "Retificação de Contratação Direta",

        "termo de formalizacao"               : "Termo de Formalização",
        "formalizacao de demanda"             : "Termo de Formalização",
        "formalizacao da demanda"             : "Termo de Formalização",

        "errata"                              : "Retificação de Aviso de Licitação",
        "retificacao"                         : "Retificação de Aviso de Licitação",
        "nova data de abertura"               : "Retificação de Aviso de Licitação",
        "prorrogacao de prazo"                : "Retificação de Aviso de Licitação",
        "retificado"                          : "Retificação de Aviso de Licitação",
        "aviso de nova data de abertura"      : "Retificação de Aviso de Licitação",
        "aviso de licitacao retificado"       : "Retificação de Aviso de Licitação",

        "termo de anulação"                   : "Termo de Anulação",
        "aviso de revogacao"                  : "Termo de Anulação",
        "termo de anulacao"                   : "Termo de Anulação",
        "anular o processo"                   : "Termo de Anulação",
        "extrato de amnulação"                : "Termo de Anulação",

        "ratifico o processo"                 : "Termo de Ratificação",
        "termo de ratificacao"                : "Termo de Ratificação",

        "extrato do contrato"                 : "Extrato de Contrato",
        "extrato de contrato"                 : "Extrato de Contrato",
        "extrato termo de contrato"           : "Extrato de Contrato",
        "extrato decorrente do contrato"      : "Extrato de Contrato",
        "extrato contrato"                    : "Extrato de Contrato",

        "licitacao deserta"                   : "Ata de Licitação Fracassada",
        "ata fracassad"                       : "Ata de Licitação Fracassada",

        "aviso de licitacao"                  : "Aviso de Licitação",
        "aviso de pregao"                     : "Aviso de Licitação",
        "extrato de processo"                 : "Aviso de Licitação",
        "extrato de licitacao"                : "Aviso de Licitação",
        "extrato de edital"                   : "Aviso de Licitação",
        "minuta de edital"                    : "Aviso de Licitação",
        "publica edital"                      : "Aviso de Licitação",
        "intencao de contratar"               : "Aviso de Licitação",
        "que fara"                            : "Aviso de Licitação",
        "que realizara"                       : "Aviso de Licitação",
        "que ira realizar"                    : "Aviso de Licitação",
        "que se encontra aberto"              : "Aviso de Licitação",
        "acha-se aberto"                      : "Aviso de Licitação",
        "fara aquisição"                      : "Aviso de Licitação",

        "atas de registro de preco"           : "Ata de Registro de Preços",
        "ata de registro de preco"            : "Ata de Registro de Preços",
        "ata registro de preços"              : "Ata de Registro de Preços",
        
        "documento de formalizacao"           : "Termo de Formalização",

        "aviso de dispensa"                   : "Aviso de Dispensa",
        "extrato de dispensa"                 : "Aviso de Dispensa",

        "aviso de inexigibilidade"            : "Aviso de Inexigibilidade",
        "extrato de inexigibilidade"          : "Aviso de Inexigibilidade",

        "ato de contratacao direta"           : "Ato de Contratação Direta",
        "contratacao direta"                  : "Ato de Contratação Direta",

        "termo de homologacao e adjudicacao"  : "Termo de Homologação e Adjudicação",
        "termo de homologacao"                : "Termo de Homologação",

        "dispensa de licitacao"               : "Dispensa de Licitação",
        "dispensa"                            : "Dispensa de Licitação",

        "inexigibilidade de licitacao"        : "Inexigibilidade de Licitação",
        "inexigibilidade"                     : "Inexigibilidade de Licitação",

        "edital"                              : "Edital",

        "esclarecimentos"                     : "Ata de Solicitações",
        "impugnacoes"                         : "Ata de Solicitações",

        "ata"                                 : "Ata de Sessão Pública",
        
        "termo de referencia"                 : "Termo de Referência"
    }

    def extract_from_heuristic(self, record):
        titulo_normalizado = Utils.normalize_text(record.get("titulo", ""))

        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        for keywords, tipo in self.tipos_documentos.items():
            regex = re.search(keywords, texto_normalizado) or re.search(keywords, titulo_normalizado)
            if keywords in titulo_normalizado or keywords in texto_normalizado or regex:
                return tipo

        return None

    def extract_from_model(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        titulo = Utils.extrair_primeira_pagina(record.get("titulo", ""))
        titulo_normalizado = Utils.normalize_text(titulo)

        prompt = f"""
Você é um especialista em licitação brasileira. Sua tarefa é analisar o título e o texto fonte para classificar o documento em UMA das categorias a seguir: '{sorted(set(self.tipos_documentos.values()))}'.

# Regras:
1.  Correspondência com a Categoria: Sua resposta deve ser um dos tipos EXATOS da lista fornecida. Se o texto do documento contiver uma variação (ex: "Extrato Contratual"), sua resposta ainda deve ser o termo correspondente da lista ("EXTRATO DE CONTRATO").
2.  Sem Inferência: A classificação deve ser baseada apenas na presença clara de um dos tipos no texto. Não deduza ou interprete.
3.  Formato da Saída:
    - Se um tipo for identificado, responda APENAS com o nome da categoria da lista.
    - Se nenhum tipo da lista for claramente identificado, responda exatamente "null".

### Exemplos de Entrada e Saída:

# Exemplo 1
Texto fonte: extrato termo de rescisão amigável
Saída esperada: null

# Exemplo 2
Texto fonte: termo de homologacao e adjudicacao de processo licitatorio
Saída esperada: "Termo de Homologação e Adjudicação"

# Exemplo 3
Texto fonte: termo aditivo n 1 ao contrato de prestacao de servicos
Saída esperada: "Termo Aditivo"

### Fim dos Exemplos
    
# Titulo Fonte:
{titulo_normalizado}

# Texto Fonte:
{texto_normalizado[:4000]}
"""

        response = Utils.ask_model(self, prompt, self.field)

        tipo = response.get(self.field, None)

        if tipo in self.tipos_documentos:
            return self.tipos_documentos.get(tipo)

        # return response.get(self.field, None)
        return None