from utils.value_checker import ValueChecker


class ValorTotalLiquidoChecker(ValueChecker):
    check_name = "valor_total_liquido"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if 'valor_total_liquido' in item.keys() and item['valor_total_liquido'] not in (None, "null", "indefinido"):
                    if not self.value_check(item['valor_total_liquido']):
                        return False, f"Valor total líquido ({item['valor_total_liquido']}) não é do tipo float)"
                    item['valor_total_liquido'] = self.normalize_value(item['valor_total_liquido'])
        return True, None
