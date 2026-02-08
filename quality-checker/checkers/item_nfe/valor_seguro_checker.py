from utils.value_checker import ValueChecker


class ValorSeguroChecker(ValueChecker):
    check_name = "valor_seguro"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_seguro" in item.keys() and item["valor_seguro"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_seguro']):
                        return False, f"Valor do seguro ({item['valor_seguro']}) não é do tipo float"
                    item['valor_seguro'] = self.normalize_value(item['valor_seguro'])
        return True, None
