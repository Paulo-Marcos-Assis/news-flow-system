from utils.date_checker import DateChecker


class DataExigibilidadeChecker(DateChecker):
    check_name = "data_exigibilidade"
    table_name = "pagamento_empenho"
    
    def check(self, record):
        if "pagamento_empenho" in record and record['pagamento_empenho'].get("data_exigibilidade") not in ("indefinido", "null", None):
            date = record['pagamento_empenho']["data_exigibilidade"]
            if not self.is_valid_date(date, allow_future_date=True):
                return False, f"('pagamento_empenho') Data de exigibilidade do empenho ({date}) inválida."
            record['pagamento_empenho']["data_exigibilidade"] = self.return_str_date(date, allow_future_date=True)

        return True, None