from utils.value_checker import ValueChecker


class QtdItemLicitacaoChecker(ValueChecker):
    check_name = "qtd_item_licitacao"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_licitacao" in record:
            items_to_check = record["item_licitacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("qtd_item_licitacao") not in ("indefinido", "null", None):
                    if not self.value_check(item["qtd_item_licitacao"]):
                        return False, f"('item_licitacao') Quantidade do item da licitação ({item['qtd_item_licitacao']}) inválida."
                    item["qtd_item_licitacao"] = self.normalize_value(item["qtd_item_licitacao"])

        return True, None