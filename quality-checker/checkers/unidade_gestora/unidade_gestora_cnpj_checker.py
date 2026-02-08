from utils.cnpj_checker import CnpjChecker


class UnidadeGestoraCnpjChecker(CnpjChecker):
    check_name = "cnpj"
    table_name = "unidade_gestora"

    def check(self, record):
        if "unidade_gestora" in record:
            ugs_to_check = record['unidade_gestora']
            if not isinstance(ugs_to_check, list):
                ugs_to_check = [ugs_to_check]

            for ug in ugs_to_check:
                if isinstance(ug, dict) and ug.get('cnpj') not in ("indefinido", "null", None):
                    # Checa CNJP e remove símbolos, caso tenha
                    checked_cnpj = self.cnpj_check(ug['cnpj'])
                    if checked_cnpj is None:
                        return False, f"CNPJ ({ug['cnpj']}) inválido."
                    if not self.is_varchar(checked_cnpj, 20):
                        return False, f"CNPJ ({ug['cnpj']} -> {checked_cnpj}) tamanho inválido (varchar20)."
                    ug["cnpj"] = checked_cnpj
        return True, None

