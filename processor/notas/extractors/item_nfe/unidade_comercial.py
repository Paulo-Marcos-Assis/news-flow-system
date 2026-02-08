import re
import unicodedata
from ..base_extractor import BaseExtractor
from ..utils.unit_substitutions import SUBSTITUICOES

class UnidadeComercialExtractor(BaseExtractor):
    field_name = "unidade_comercial"
    scope = "item"

    def extract(self, record):
        raw_value = record.get("UNIDADE_COMERCIAL")

        if not raw_value:
            return None

        value = self._normalize(raw_value)
        return value

    def _normalize(self, text):
        # 1. Minúsculo e sem acento
        text = text.strip().lower()
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

        # 2. Remove caracteres especiais
        text = re.sub(r"[^a-z0-9\s]", "", text)

        # 3. Aplica substituições
        for pattern, replacement in SUBSTITUICOES.items():
            text = re.sub(pattern, replacement, text)

        # 4. Remove espaços extras
        return re.sub(r"\s+", "", text)
