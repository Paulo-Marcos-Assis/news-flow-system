from utils.date_checker import DateChecker

class DataSituacaoChecker(DateChecker):
    check_name = "data_situacao"
    table_name = "estabelecimento"

    def check(self, record):
        if "estabelecimento" in record.keys() and "data_situacao" in record['estabelecimento'].keys() and record['estabelecimento']['data_situacao'] not in ("indefinido","null",None,""):
            date = record['estabelecimento']['data_situacao']
            if not self.is_valid_date(date):
                return False, f"Data situacao({record['estabelecimento']['data_situacao']}) inválida."
            record['estabelecimento']['data_situacao'] = self.return_str_date(date)
        return True,None
