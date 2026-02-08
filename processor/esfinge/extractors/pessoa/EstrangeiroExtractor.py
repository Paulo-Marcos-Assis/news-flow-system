from ..base_extractor import BaseExtractor


class EstrangeiroExtractor(BaseExtractor):
    field_name = "estrangeiro"
    scope = "pessoa"

    def extract(self, record):
        data = record.get('participante_licitacao', {})
        id_tipo_pessoa = data.get('id_tipo_pessoa')
        if id_tipo_pessoa is not None:
            return str(id_tipo_pessoa) in ('3', '4')
        return None
