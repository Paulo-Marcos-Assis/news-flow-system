from ..base_extractor import BaseExtractor

class TabelaTextosExtractor(BaseExtractor):
    field_name = "nome_arquivo"
    scope = "documento"

    def extract(self, record):
        """
        Processa a listTextos e retorna uma lista de dicionários,
        onde cada dicionário é um texto/anexo.
        """
        textos_processados = []
        for texto_bruto in record.get('listTextos', []):
            texto_limpo = {
                "denominacao": texto_bruto.get("denominacao"),
                #"link": texto_bruto.get("link") TODO: ATUALMENTE RETORNAM como null, para evitar exceção no verifier estou comentando mas após verificação com suporte da API Epublica pode-se voltar a ter esse campo
            }
            textos_processados.append(texto_limpo)
        
        return textos_processados