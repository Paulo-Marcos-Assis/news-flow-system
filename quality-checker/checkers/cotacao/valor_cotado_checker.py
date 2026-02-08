from utils.value_checker import ValueChecker


class ValorCotadoChecker(ValueChecker):
    check_name = "valor_cotado"
    table_name = "cotacao"

    def check(self, record):
        if "cotacao" in record:
            items_to_check = record["cotacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("valor_cotado") not in ("indefinido", "null", None):
                    if not self.value_check(item["valor_cotado"]):
                        return False, f"('cotacao') Valor cotado ({item['valor_cotado']}) inválido."
                    item["valor_cotado"] = float(self.normalize_value(item["valor_cotado"]))

        return True, None