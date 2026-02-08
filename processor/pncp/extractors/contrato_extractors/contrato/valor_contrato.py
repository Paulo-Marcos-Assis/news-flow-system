from decimal import Decimal, InvalidOperation
from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class ValorContratoExtractor(BaseExtractor):
    field_name = "valor_contrato"

    def extract(self, record):
        # Extracts the 'valorGlobal' field.
        valor_original = record.get("valorGlobal")

        if valor_original is None or str(valor_original).strip() == '':
            return DEFAULT_VALUE

        valor_str = str(valor_original).strip()

        # Handles Brazilian currency format
        valor_para_decimal = valor_str.replace('.', '').replace(',', '.')
        
        try:
            return float(Decimal(valor_para_decimal))
        except InvalidOperation:
            return DEFAULT_VALUE

