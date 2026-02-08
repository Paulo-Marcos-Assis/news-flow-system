from utils.value_checker import ValueChecker


class QtItemCotadoChecker(ValueChecker):
    check_name = "qt_item_cotado"
    table_name = "cotacao"

    def check(self, record):
        if "cotacao" in record:
            items_to_check = record["cotacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("qt_item_cotado") not in ("indefinido", "null", None):
                    if not self.value_check(item["qt_item_cotado"]):
                        return False, f"('cotacao') Quantidade do item cotado ({item['qt_item_cotado']}) inválida."
                    item["qt_item_cotado"] = float(self.normalize_value(item["qt_item_cotado"]))

        return True, None