from utils.date_checker import DateChecker

class DataInicioAtividadeChecker(DateChecker):
    check_name = "data_inicio_atividade"
    table_name = "estabelecimento"

    def check(self, record):
        if "estabelecimento" in record.keys() and "data_inicio_atividade" in record['estabelecimento'].keys() and record['estabelecimento']['data_inicio_atividade'] not in ("indefinido","null",None,""):
            date = record['estabelecimento']['data_inicio_atividade']
            if not self.is_valid_date(date):
                return False, f"Data de inicio atividade({record['estabelecimento']['data_inicio_atividade']}) inválida."
            record['estabelecimento']["data_inicio_atividade"] = self.return_str_date(date)
        return True,None
