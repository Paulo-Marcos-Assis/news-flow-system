from utils.value_checker import ValueChecker


class ValorLiquidacaoChecker(ValueChecker):
    check_name = "valor_liquidacao"
    table_name = "liquidacao"

    def check(self, record):
        if "liquidacao" in record and record["liquidacao"].get("valor_liquidacao") not in ("indefinido", "null", None):
            if not self.value_check(record["liquidacao"]["valor_liquidacao"]):
                return False, f"('liquidacao') Valor de liquidação ({record['liquidacao']['valor_liquidacao']}) inválido."
            record["liquidacao"]["valor_liquidacao"] = float(self.normalize_value(record["liquidacao"]["valor_liquidacao"]))

        return True, None