from checkers.base_quali_checker import BaseQualiChecker

class ChaveAcessoChecker(BaseQualiChecker):
    check_name = "chave_acesso"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "chave_acesso" in record['nfe'].keys() and record['nfe']["chave_acesso"] not in ("indefinido","null",None,""):
            if not record['nfe']["chave_acesso"].isdigit():
                return False, f"Chave acesso ({record['nfe']['chave_acesso']}) inválida."
        return True,None