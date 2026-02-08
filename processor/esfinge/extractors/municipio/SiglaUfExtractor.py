from ..base_extractor import BaseExtractor
from typing import List, Set, Optional, Union
import logging

class SiglaUfExtractor(BaseExtractor):
    field_name = "sigla_uf"
    scope = "municipio"
    possible_fields = [
        "municipio.sigla_uf"
    ]

    def get_nested_value(self, record: dict, path: str) -> Optional[str]:
        """Obtém valor de campos aninhados usando notação com ponto"""
        keys = path.split('.')
        value = record
        try:
            for key in keys:
                value = value.get(key)
                if value is None:
                    return None
            return str(value).strip() if value else None
        except (AttributeError, KeyError, TypeError) as e:
            if hasattr(self, 'logger'):
                self.logger.debug(f"Erro ao acessar campo aninhado {path}: {str(e)}")
            return None

    def extract(self, record: dict) -> Union[List[str], None]:
        values = set()

        try:
            for field in self.possible_fields:
                try:
                    value = self.get_nested_value(record, field)
                    if value:
                        values.add(value)
                except Exception as e:
                    if hasattr(self, 'logger'):
                        self.logger.warning(f"Erro ao processar campo '{field}': {str(e)}")
                    continue

            return list(values) if values else None

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Erro inesperado em NomePessoaExtractor: {str(e)}")
            return None