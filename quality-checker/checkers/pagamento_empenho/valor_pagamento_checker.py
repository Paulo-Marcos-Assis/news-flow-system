from utils.value_checker import ValueChecker


class ValorPagamentoChecker(ValueChecker):
    check_name = "valor_pagamento"
    table_name = "pagamento_empenho"
    
    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("valor_pagamento") not in ("indefinido", "null", None):
            value = record['pagamento_empenho']["valor_pagamento"]
            if not self.value_check(value):
                return False, f"('pagamento_empenho') Valor de pagamento do empenho ({value}) inválido."
            record['pagamento_empenho']["valor_pagamento"] = float(self.normalize_value(value))
            
        return True, None