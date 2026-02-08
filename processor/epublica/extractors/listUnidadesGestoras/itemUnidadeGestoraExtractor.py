from ..base_extractor import BaseExtractor

class TabelaUnidadeGestoraExtractor(BaseExtractor):
    field_name = "unidade_gestora_completa"
    scope = "unidade_gestora"

    def extract(self, record):
        """
        Processa a listUnidadesGestoras e retorna uma lista de dicionários.
        """
        unidades_processadas = []
        for ug_bruta in record.get('listUnidadesGestoras', []):
            ug_limpa = {
                "cod_ug": ug_bruta.get("codigo"),
                "nome_ug": ug_bruta.get("denominacao") # Corrigido de "unidade_gestora" para "denominacao"
            }
            unidades_processadas.append(ug_limpa)

        return unidades_processadas