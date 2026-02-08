from utils.value_checker import ValueChecker


class ValorDescontoChecker(ValueChecker):
    check_name = "valor_desconto"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_desconto" in item.keys() and item["valor_desconto"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_desconto']):
                        return False, f"Valor do desconto ({item['valor_desconto']}) não é do tipo double"
                    item['valor_desconto'] = self.normalize_value(item['valor_desconto'])
        return True, None
