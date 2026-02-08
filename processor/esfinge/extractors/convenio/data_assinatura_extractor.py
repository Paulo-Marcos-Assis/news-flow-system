from ..base_extractor import BaseExtractor

class DataAssinaturaConvenioExtractor(BaseExtractor):
    field_name = "data_assinatura"
    scope = "convenio"

    def extract(self, record):
        convenio_data = record.get('convenio', {})
        return convenio_data.get('data_assinatura')
