from utils.date_checker import DateChecker

class DataEmissaoChecker(DateChecker):
    check_name = "data_emissao"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "data_emissao" in record['nfe'].keys() and record['nfe']["data_emissao"] not in ("indefinido","null",None,""): 
            date = record['nfe']['data_emissao']
            if not self.is_valid_date(date):
                return False, f"Data emissao ({record['nfe']['data_emissao']}) inválida."
            
            # Checa período válido para a data
            if not self.period_check("2007-01-01" , "2025-12-31" , date):
                return False, f"Data emissao  ({record['nfe']['data_emissao']}) fora do periodo previsto."
            
            record['nfe']['data_emissao'] = self.return_str_date(date)
        return True,None