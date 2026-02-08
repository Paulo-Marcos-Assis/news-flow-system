from checkers.base_quali_checker import BaseQualiChecker


class ClassificacaoChecker(BaseQualiChecker):
    check_name = "classificacao"
    table_name = "cotacao"

    def check(self, record):
        if "cotacao" in record:
            items_to_check = record["cotacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("classificacao") not in ("indefinido", "null", None):
                    if not self.is_valid_smallint(item["classificacao"]):
                        return False, f"('cotacao') Classificação ({item['classificacao']}) inválida."
                    item["classificacao"] = int(item["classificacao"])

        return True, None