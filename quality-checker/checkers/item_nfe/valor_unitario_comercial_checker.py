from utils.value_checker import ValueChecker


class ValorUnitarioComercialChecker(ValueChecker):
    check_name = "valor_unitario_comercial"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_unitario_comercial" in item.keys() and item["valor_unitario_comercial"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_unitario_comercial']):
                        return False, f"Valor unitário comercial ({item['valor_unitario_comercial']}) não é do tipo float"
                    item['valor_unitario_comercial'] = self.normalize_value(item['valor_unitario_comercial'])
        return True, None
