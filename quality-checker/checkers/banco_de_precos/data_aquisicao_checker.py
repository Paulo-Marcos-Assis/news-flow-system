from utils.date_checker import DateChecker

class DataAquisicaoChecker(DateChecker):
    check_name = "data_aquisicao"
    table_name = "banco_de_precos"

    def check(self, record):
        if "banco_de_precos" in record.keys() and "data_aquisicao" in record['banco_de_precos'].keys() and record['banco_de_precos']["data_aquisicao"] not in ("indefinido","null",None,""): 
            date = record['banco_de_precos']['data_aquisicao']
            if not self.is_valid_date(date):
                return False, f"Data aquisicao  ({record['banco_de_precos']['data_aquisicao']}) inválida."
            record['banco_de_precos']['data_aquisicao'] = self.return_str_date(date)
        return True,None
