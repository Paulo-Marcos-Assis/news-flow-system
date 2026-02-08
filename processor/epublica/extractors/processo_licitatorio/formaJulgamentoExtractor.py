from ..base_extractor import BaseExtractor

#VAI PAR AO BANCO DINÂMICO - aka OrientDB

class FormaJulgamentoExtractor(BaseExtractor):
    field_name = "julgamento" 
    scope = "processo_licitatorio" 

    def extract(self, record):
        return record.get("licitacao", {}).get("formaJulgamento")