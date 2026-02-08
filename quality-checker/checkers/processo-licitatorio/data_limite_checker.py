from utils.date_checker import DateChecker

class DataLimiteChecker(DateChecker):
    check_name = "data_limite"
    table_name = "processo_licitatorio"

    def check(self, record):
        if "processo_licitatorio" in record.keys() and "data_limite" in record['processo_licitatorio'].keys() and record['processo_licitatorio']["data_limite"] not in ("indefinido","null",None,""): 
            date = record['processo_licitatorio']['data_limite']
            if not self.is_valid_date(date, allow_future_date=True):
                return False, f"Data limite ({record['processo_licitatorio']['data_limite']}) inválida."
            record['processo_licitatorio']['data_limite'] = self.return_str_date(date, allow_future_date=True)
        return True,None
