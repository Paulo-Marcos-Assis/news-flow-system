from decimal import Decimal, InvalidOperation
from ...base_extractor import BaseExtractor, DEFAULT_VALUE

class ValorLiquidacaoExtractor(BaseExtractor):
    """
    Extracts the monetary value of 'valorNotaFiscal' and converts it to a
    lossless Decimal type, assuming a Brazilian currency format.
    """
    field_name = "valor_liquidacao"

    def extract(self, record):
        """
        Extracts 'valorNotaFiscal', cleans it assuming Brazilian number format
        (e.g., "1.234,56"), and converts it to a Decimal type.
        """
        valor_original = record.get("notaFiscalEletronica", {}).get("valorNotaFiscal")

        if valor_original is None or str(valor_original).strip() == '':
            return DEFAULT_VALUE

        valor_str = str(valor_original).strip()

        # In Brazilian format, '.' is a thousands separator and ',' is for decimals.
        # To convert to a standard Decimal, we remove thousand separators
        # and then replace the decimal comma with a dot.
        # Example: "1.234,56" -> "1234,56" -> "1234.56"
        valor_para_decimal = valor_str.replace('.', '').replace(',', '.')
        
        try:
            return float(Decimal(valor_para_decimal))
        except InvalidOperation:
            # If conversion fails, the string is not a valid number after cleaning.
            # This can happen with non-numeric values like "N/A" or unexpected formats.
            # We return the default value as a fallback.
            return DEFAULT_VALUE