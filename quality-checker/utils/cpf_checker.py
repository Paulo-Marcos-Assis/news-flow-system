from abc import ABC

from checkers.base_quali_checker import BaseQualiChecker
from validate_docbr import CPF


class CpfChecker(BaseQualiChecker, ABC):

    def cpf_check(self, cpf):
        cpf_validator = CPF()
        cpf_str = str(cpf).replace('.', '').replace('-', '').strip()
        # Pad with leading zeros if needed (CPF has 11 digits)
        if len(cpf_str) < 11:
            cpf_str = cpf_str.zfill(11)
        if cpf_validator.validate(cpf_str):
            return cpf_str

        return None
