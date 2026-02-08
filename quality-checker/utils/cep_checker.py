from abc import ABC
from checkers.base_quali_checker import BaseQualiChecker


class CepChecker(BaseQualiChecker, ABC):

    def cep_check(self, cep):
        # Garante a manipulação de uma String
        cep_str = str(cep)
        if len(cep_str) != 8:
            # Tira '-' caso tenha 
            cep_str = cep_str.replace("-", "")

        if len(cep_str) == 8 and cep_str.isdigit():
            return cep_str

        return None
