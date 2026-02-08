from utils.value_checker import ValueChecker


class ValorContratoChecker(ValueChecker):
    check_name = "valor_contrato"
    table_name = "contrato"

    def check(self, record):
        if "contrato" in record and record["contrato"].get("valor_contrato") not in ("indefinido", "null", None):
            if not self.value_check(record["contrato"]["valor_contrato"], can_be_negative=True):
                return False, f"('contrato') Valor do contrato ({record['contrato']['valor_contrato']}) inválido."
            record["contrato"]["valor_contrato"] = float(self.normalize_value(record["contrato"]["valor_contrato"]))

        return True, None