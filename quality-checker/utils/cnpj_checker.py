from abc import ABC
from checkers.base_quali_checker import BaseQualiChecker
from validate_docbr import CNPJ


class CnpjChecker(BaseQualiChecker, ABC):

    def cnpj_check(self, cnpj):
        cnpj_validator = CNPJ()
        cnpj_string = str(cnpj).replace(".", "").replace("-", "").replace("/", "").strip()
        # Pad with leading zeros if needed (CNPJ has 14 digits)
        if len(cnpj_string) < 14:
            cnpj_string = cnpj_string.zfill(14)
        if cnpj_validator.validate(cnpj_string):
            return cnpj_string

        return None
