from checkers.base_quali_checker import BaseQualiChecker

class FormaPgtoChecker(BaseQualiChecker):
    check_name = "forma_pgto"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "forma_pgto" in record['nfe'].keys() and record['nfe']["forma_pgto"] not in ("indefinido","null",None,""):
            if not self.is_valid_integer(record['nfe']['forma_pgto']):
                return False, f"Forma pagamento ({record['nfe']['forma_pgto']}) inválida"
            
        return True,None