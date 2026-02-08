from checkers.base_quali_checker import BaseQualiChecker


class NumeroItemChecker(BaseQualiChecker):
    check_name = "numero_item"
    table_name = "cotacao"

    def check(self, record):
        if "cotacao" in record:
            items_to_check = record["cotacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("numero_item") not in ("indefinido", "null", None):
                    if not self.is_valid_integer(item["numero_item"]):
                        return False, f"('cotacao') Número do item ({item['numero_item']}) inválido."
                    item["numero_item"] = int(item["numero_item"])

        return True, None