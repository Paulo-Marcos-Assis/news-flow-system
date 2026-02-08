from ..base_extractor import BaseExtractor

class ListEmpenhosExtractor(BaseExtractor):

    field_name = "empenhos"
    scope = "empenho"

    def extract(self, record):
        """
        Processa a 'listEmpenhos' e retorna uma lista de dicionários,
        onde cada dicionário representa um empenho.
        Retorna uma lista vazia se 'listEmpenhos' não existir no registro.
        """
        empenhos_processados = []

        for empenho_bruto in record.get('listEmpenhos', []):
            empenho_limpo = {
                "emissao": empenho_bruto.get("emissao"),
                "num_empenho": empenho_bruto.get("numero"),
                "descricao": empenho_bruto.get("objetoResumido"),
                "especie": empenho_bruto.get("especie"),
                "id_categoria_economica_despesa": empenho_bruto.get("categoria"),
                "contrato": empenho_bruto.get("contrato"), #onde no banco?
                "licitacao": empenho_bruto.get("licitacao"),#id_processo_licitatorio?
                #"recurso_diaria": empenho_bruto.get("recursoDiaria"),#onde no banco?
            }
            empenhos_processados.append(empenho_limpo)
        
        return empenhos_processados