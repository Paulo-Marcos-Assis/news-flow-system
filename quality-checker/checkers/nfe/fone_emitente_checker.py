from checkers.base_quali_checker import BaseQualiChecker

class FoneEmitenteChecker(BaseQualiChecker):
    check_name = "fone_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "fone_emitente" in record['nfe'].keys() and record['nfe']["fone_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["fone_emitente"],255):
                return False, f"Fone Emitente ({record['nfe']['fone_emitente']}) fora do tamanho permitido."
        return True,None