from ..base_extractor import BaseExtractor


class DataValidadeExtractor(BaseExtractor):
    field_name = "data_validade"
    scope = "inidonea"

    def extract(self, record):
        inidoneidade_data = record.get('inidoneidade', {})
        return inidoneidade_data.get('data_fim_prazo')

