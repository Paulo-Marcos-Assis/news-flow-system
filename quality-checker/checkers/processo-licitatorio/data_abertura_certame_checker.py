from utils.date_checker import DateChecker

class DataAberturaCertameChecker(DateChecker):
    check_name = "data_abertura_certame"
    table_name = "processo_licitatorio"

    def check(self, record):
        if "processo_licitatorio" in record.keys() and "data_abertura_certame" in record['processo_licitatorio'].keys() and record['processo_licitatorio']["data_abertura_certame"] not in ("indefinido","null",None,""): 
            date = record['processo_licitatorio']['data_abertura_certame']
            if not self.is_valid_date(date, allow_future_date=True):
                return False, f"Data abertura certame ({record['processo_licitatorio']['data_abertura_certame']}) inválida."
            record['processo_licitatorio']['data_abertura_certame'] = self.return_str_date(date, allow_future_date=True)
        return True,None
