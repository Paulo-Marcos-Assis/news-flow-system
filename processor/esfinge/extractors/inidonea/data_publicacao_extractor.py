from ..base_extractor import BaseExtractor


class DataPublicacaoExtractor(BaseExtractor):
    field_name = "data_publicacao"
    scope = "inidonea"

    def extract(self, record):
        inidoneidade_data = record.get('inidoneidade', {})
        return inidoneidade_data.get('data_publicacao')

