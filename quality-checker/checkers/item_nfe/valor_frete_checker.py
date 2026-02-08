from utils.value_checker import ValueChecker


class ValorFreteChecker(ValueChecker):
    check_name = "valor_frete"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_frete" in item.keys() and item["valor_frete"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_frete']):
                        return False, f"Valor do frete ({item['valor_frete']}) não é do tipo float"
                    item['valor_frete'] = self.normalize_value(item['valor_frete'])
        return True, None
