from ..base_extractor import BaseExtractor

class DataFimVigenciaExtractor(BaseExtractor):
    field_name = "data_fim_vigencia"
    scope = "convenio"

    def extract(self, record):
        convenio_data = record.get('convenio', {})
        return convenio_data.get('data_fim_vigencia')
