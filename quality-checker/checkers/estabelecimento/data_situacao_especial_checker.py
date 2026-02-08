from utils.date_checker import DateChecker

class DataSituacaoEspecialChecker(DateChecker):
    check_name = "data_situacao_especial"
    table_name = "estabelecimento"

    def check(self, record):
        if "estabelecimento" in record.keys() and "data_situacao_especial" in record['estabelecimento'].keys() and record['estabelecimento']['data_situacao_especial'] not in ("indefinido","null",None,""):
            date = record['estabelecimento']['data_situacao_especial']
            if not self.is_valid_date(date):
                return False, f"Data de situação especial ({record['estabelecimento']['data_situacao_especial']}) inválida."
            record['estabelecimento']['data_situacao_especial'] = self.return_str_date(date)
        return True,None
