from checkers.base_quali_checker import BaseQualiChecker


class CnaeChecker(BaseQualiChecker):
    check_name = "cnae"
    table_name = "cnae"

    def check(self, record):
        if "cnae" in record.keys() and "cnae" in record['cnae'].keys() and record["cnae"]["cnae"] not in ("indefinido", "null", None):
            if not self.is_valid_integer(record['cnae']['cnae']):
                return False, f"CNAE {record['cnae']['cnae']} não é um número inteiro válido."
            record['cnae']['cnae'] = int(record['cnae']['cnae'])

        return True, None