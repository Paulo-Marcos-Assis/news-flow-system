from checkers.base_quali_checker import BaseQualiChecker

class SituacaoNfeChecker(BaseQualiChecker):
    check_name = "situacao_nfe"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "situacao_nfe" in record['nfe'].keys() and record['nfe']["situacao_nfe"] not in ("indefinido","null",None,""):
            if not self.is_valid_integer(record['nfe']['situacao_nfe']):
                return False, f"Situação NFe ({record['nfe']['situacao_nfe']}) inválida"
            
        return True,None