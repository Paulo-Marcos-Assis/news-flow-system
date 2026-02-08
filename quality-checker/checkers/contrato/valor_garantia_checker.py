from utils.value_checker import ValueChecker


class ValorGarantiaChecker(ValueChecker):
    check_name = "valor_garantia"
    table_name = "contrato"

    def check(self, record):
        if "contrato" in record and record["contrato"].get("valor_garantia") not in ("indefinido", "null", None):
            if not self.value_check(record["contrato"]["valor_garantia"]):
                return False, f"('contrato') Valor da garantia ({record['contrato']['valor_garantia']}) inválido."
            record["contrato"]["valor_garantia"] = float(self.normalize_value(record["contrato"]["valor_garantia"]))

        return True, None