from ..base_extractor import BaseExtractor

class TabelaUnidadeGestoraExtractor(BaseExtractor):
    field_name = "unidade_gestora_completa"
    scope = "unidade_gestora"

    def extract(self, record):
        
        unidades_processadas = []
        for ug_bruta in record.get('listUnidadesGestoras', []):
            ug_limpa = {
                "cod_ug": ug_bruta.get("codigo"),
                "nome_ug": ug_bruta.get("denominacao")
            }
            unidades_processadas.append(ug_limpa)

        return unidades_processadas