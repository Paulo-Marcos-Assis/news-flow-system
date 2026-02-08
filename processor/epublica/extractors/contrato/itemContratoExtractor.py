from ..base_extractor import BaseExtractor

class ListContratoExtractor(BaseExtractor):

    field_name = "contratos" 
    scope = "contrato"

    def extract(self, record):
        """
        Processa a 'listContratos' e retorna uma lista de dicionários,
        onde cada dicionário representa um contrato.
        Retorna uma lista vazia se 'listContratos' não existir.
        """
        contratos_processados = []

        for contrato_bruto in record.get('listContratos', []):
            contrato_limpo = {
                "numero_contrato": contrato_bruto.get("numero"),
                "data_assinatura": contrato_bruto.get("assinatura"),
                "inicio_vigencia": contrato_bruto.get("inicioVigencia"), #Vai pro dinâmico
                "data_vencimento": contrato_bruto.get("vencimento"),
                "valor_contrato": contrato_bruto.get("valorTotal"),
                "descricao_objetivo": contrato_bruto.get("objetoResumido"),
            }
            contratos_processados.append(contrato_limpo)
        
        return contratos_processados