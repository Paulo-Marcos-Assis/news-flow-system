from utils.date_checker import DateChecker


class DataHomologacaoChecker(DateChecker):
    check_name = "data_homologacao"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_licitacao" in record:
            items_to_check = record["item_licitacao"]
            if not isinstance(items_to_check, list):
                items_to_check = [items_to_check]

            for item in items_to_check:
                if isinstance(item, dict) and item.get("data_homologacao") not in ("indefinido", "null", None):
                    if not self.is_valid_date(item["data_homologacao"]):
                        return False, f"('item_licitacao') Data de homologação ({item['data_homologacao']}) inválida."
                    item["data_homologacao"] = self.return_str_date(item["data_homologacao"])
        
        return True, None