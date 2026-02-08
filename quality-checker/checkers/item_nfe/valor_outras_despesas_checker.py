from utils.value_checker import ValueChecker


class ValorOutrasDespesasChecker(ValueChecker):
    check_name = "valor_outras_despesas"
    table_name = "item_licitacao"

    def check(self, record):
        if "item_nfe" in record.keys():
            for item in record['item_nfe']:
                if "valor_outras_despesas" in item.keys() and item["valor_outras_despesas"] not in ("indefinido","null",None,""):
                    if not self.value_check(item['valor_outras_despesas']):
                        return False, f"Valor de outras despesas ({item['valor_outras_despesas']}) não é do tipo float"
                    item['valor_outras_despesas'] = self.normalize_value(item['valor_outras_despesas'])
        return True, None
