from utils.value_checker import ValueChecker


class ValorUnitarioLiquidoChecker(ValueChecker):
    check_name = "valor_unitario_liquido"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_unitario_liquido" in item.keys() and item["valor_unitario_liquido"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_unitario_liquido']):
                        return False, f"Valor unitário líquido ({item['valor_unitario_liquido']}) não é do tipo float"
                    item['valor_unitario_liquido'] = self.normalize_value(item['valor_unitario_liquido'])
        return True, None
