from utils.date_checker import DateChecker


class DataPagamentoChecker(DateChecker):
    check_name = "data_pagamento"
    table_name = "pagamento_empenho"
    
    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("data_pagamento") not in ("indefinido", "null", None):
            date = record['pagamento_empenho']["data_pagamento"]
            if not self.is_valid_date(date):
                return False, f"('pagamento_empenho') Data de pagamento do empenho ({date}) inválida."
            record['pagamento_empenho']["data_pagamento"] = self.return_str_date(date)

        return True, None