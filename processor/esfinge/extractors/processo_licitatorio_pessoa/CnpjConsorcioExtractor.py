from ..base_extractor import BaseExtractor


class CnpjConsorcioExtractor(BaseExtractor):
    field_name = "cnpj_consorcio"
    scope = "processo_licitatorio_pessoa"

    def extract(self, record):
        data = record.get('participante_licitacao', {})
        value = data.get('codigo_cnpj_consorcio')
        if value:
            return value
        return None
