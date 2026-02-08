import re

from ..base_extractor import BaseExtractor
from service_essentials.utils.utils import Utils

class ValorPrevistoExtractor(BaseExtractor):
    field = "valor_previsto"

    def extract_from_heuristic(self, record):
        texto = Utils.extrair_primeira_pagina(record.get("texto", ""))
        texto_normalizado = Utils.normalize_text(texto)

        pattern = r"\bvalor\b"
        match = re.search(pattern, texto_normalizado)

        if match:
            texto_valor_previsto = texto_normalizado[match.end():match.end() + 75]
            pattern_valor = r"\d{1,3}(?:\.\d{3})*,\d{2}"
            valor_previsto = re.search(pattern_valor, texto_valor_previsto)

            if valor_previsto:
                return valor_previsto.group()

        return None

    def extract_from_model(self, record):
        pass