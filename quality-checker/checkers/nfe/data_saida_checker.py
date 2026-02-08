from utils.date_checker import DateChecker

class DataSaidaChecker(DateChecker):
    check_name = "data_saida"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "data_saida" in record['nfe'].keys() and record['nfe']["data_saida"] not in ("indefinido","null",None,""): 
            date = record['nfe']['data_saida']
            if not self.is_valid_date(date):
                return False, f"Data saída  ({record['nfe']['data_saida']}) inválida."
            
            if not self.period_check("2007-01-01" , "2026-01-31" , date):
                return False, f"Data saída  ({record['nfe']['data_saida']}) fora do periodo previsto."
            
            record['nfe']['data_saida'] = self.return_str_date(date)
        return True,None