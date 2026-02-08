from checkers.base_quali_checker import BaseQualiChecker

class NumSerieNfeChecker(BaseQualiChecker):
    check_name = "num_serie_nfe"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "num_serie_nfe" in record['nfe'].keys() and record['nfe']["num_serie_nfe"] not in ("indefinido","null",None,""):
            if not self.is_valid_integer(record['nfe']['num_serie_nfe']):
                return False, f"Série da NFe ({record['nfe']['num_serie_nfe']}) inválida"
            
        return True,None