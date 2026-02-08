from utils.date_checker import DateChecker

class DataUltimaExecucaoChecker(DateChecker):
    check_name = "data_ultima_execucao"
    table_name = "alerta"

    def check(self, record):
        if "alerta" in record.keys() and "data_ultima_execucao" in record['alerta'].keys() and record['alerta']["data_ultima_execucao"] not in ("indefinido","null",None,""): 
            date = record['alerta']['data_ultima_execucao']
            if not self.is_valid_date(date):
                return False, f"Data ultima execucao ({record['alerta']['data_ultima_execucao']}) inválida."
            record['alerta']['data_ultima_execucao'] = self.return_str_date(date)
        return True,None
