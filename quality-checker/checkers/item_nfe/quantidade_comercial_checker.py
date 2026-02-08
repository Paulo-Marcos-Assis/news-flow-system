from utils.value_checker import ValueChecker


class QuantidadeComercialChecker(ValueChecker):
    check_name = "quantidade_comercial"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "quantidade_comercial" in item.keys() and item["quantidade_comercial"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['quantidade_comercial']):
                        return False, f"Quantidade comercial ({item['quantidade_comercial']}) não é do tipo float"
                    item['quantidade_comercial'] = self.normalize_value(item['quantidade_comercial'])
        return True, None
