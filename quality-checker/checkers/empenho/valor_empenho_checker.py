from utils.value_checker import ValueChecker


class ValorEmpenhoChecker(ValueChecker):
    check_name = "valor_empenho"
    table_name = "empenho"

    def check(self, record):
        if "empenho" in record and record["empenho"].get("valor_empenho") not in ("indefinido", "null", None):
            valor_empenho = record["empenho"]["valor_empenho"]
            if not self.value_check(valor_empenho):
                return False, f"('empenho') Valor do empenho ({valor_empenho}) inválido."
            record["empenho"]["valor_empenho"] = self.normalize_value(valor_empenho)

        return True, None