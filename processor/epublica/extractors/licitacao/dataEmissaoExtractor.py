from ..base_extractor import BaseExtractor

class DataEmissaoExtractor(BaseExtractor):
    field_name = "data_emissao" #"data_emissao" no json retornado pela API
    scope = "documento" #"licitacao" no json retornado pela API

    def extract(self, record):
        pass
        return record.get("licitacao", {}).get("dataEmissao")