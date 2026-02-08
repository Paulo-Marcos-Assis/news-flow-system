from checkers.base_quali_checker import BaseQualiChecker


class VencedorChecker(BaseQualiChecker):
    check_name = "vencedor"
    table_name = "cotacao"

    def check(self, record):
        if "cotacao" in record:
            items_to_check = record["cotacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("vencedor") not in ("indefinido", "null", None):
                    if not self.is_bool(item["vencedor"]):
                        return False, f"('cotacao') Vencedor ({item['vencedor']}) inválido."

        return True, None