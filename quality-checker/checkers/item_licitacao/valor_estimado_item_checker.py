from utils.value_checker import ValueChecker


class ValorEstimadoItemChecker(ValueChecker):
    check_name = "valor_estimado_item"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_licitacao" in record:
            items_to_check = record["item_licitacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("valor_estimado_item") not in ("indefinido", "null", None):
                    if not self.value_check(item["valor_estimado_item"]):
                        return False, f"('item_licitacao') Valor estimado do item ({item['valor_estimado_item']}) inválido."
                    normalized = self.normalize_value(item["valor_estimado_item"])
                    # Remove value if it's 0
                    if normalized == 0 or normalized == 0.0:
                        del item["valor_estimado_item"]
                    else:
                        item["valor_estimado_item"] = normalized

        return True, None