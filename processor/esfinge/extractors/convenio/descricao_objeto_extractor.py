from ..base_extractor import BaseExtractor

class DescricaoObjetoExtractor(BaseExtractor):
    field_name = "descricao_objeto"
    scope = "convenio"

    def extract(self, record):
        convenio_data = record.get('convenio', {})
        return convenio_data.get('descricao_objeto')
