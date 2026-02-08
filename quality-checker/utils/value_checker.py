from abc import ABC

from checkers.base_quali_checker import BaseQualiChecker


class ValueChecker(BaseQualiChecker, ABC):

    def value_check(self, value, can_be_negative: bool = False) -> bool:
        # Replace comma with dot for decimal separator
        if isinstance(value, str):
            value = value.replace(',', '.')
        
        if not self.is_double(value):
            return False

        value_float = float(value)
        if not can_be_negative and value_float < 0:
            return False

        return True

    def normalize_value(self, value) -> str:
        """Convert comma decimal separator to dot and return normalized string."""
        if isinstance(value, str):
            return value.replace(',', '.')
        return str(value)
