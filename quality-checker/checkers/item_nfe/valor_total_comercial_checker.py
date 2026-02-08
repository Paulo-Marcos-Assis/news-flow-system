from utils.value_checker import ValueChecker


class ValorTotalComercialChecker(ValueChecker):
    check_name = "valor_total_comercial"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_total_comercial" in item.keys() and item["valor_total_comercial"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_total_comercial']):
                        return False, f"Valor total comercial ({item['valor_total_comercial']}) não é do tipo float"
                    item['valor_total_comercial'] = self.normalize_value(item['valor_total_comercial'])
        return True, None
