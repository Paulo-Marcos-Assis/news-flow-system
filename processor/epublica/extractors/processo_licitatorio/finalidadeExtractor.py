from ..base_extractor import BaseExtractor

#VAI PAR AO BANCO DINÂMICO - aka OrientDB

class FinalidadeExtractor(BaseExtractor):
    field_name = "finalidade" 
    scope = "processo_licitatorio" 

    def extract(self, record):
        return record.get("licitacao", {}).get("finalidade")
