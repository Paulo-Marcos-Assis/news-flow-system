from checkers.base_quali_checker import BaseQualiChecker


class NumeroSequencialItemChecker(BaseQualiChecker):
    check_name = "numero_sequencial_item"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_licitacao" in record:
            items_to_check = record["item_licitacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("numero_sequencial_item") not in ("indefinido", "null", None):
                    if not self.is_valid_integer(item["numero_sequencial_item"]):
                        return False, f"('item_licitacao') Número sequencial do item ({item['numero_sequencial_item']}) inválido."
                    item["numero_sequencial_item"] = int(item["numero_sequencial_item"])

        return True, None