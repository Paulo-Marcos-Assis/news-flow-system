from ..base_extractor import BaseExtractor

class ValorConvenioExtractor(BaseExtractor):
    field_name = "valor_convenio"
    scope = "convenio"

    def extract(self, record):
        convenio_data = record.get('convenio', {})
        return convenio_data.get('valor_convenio')
