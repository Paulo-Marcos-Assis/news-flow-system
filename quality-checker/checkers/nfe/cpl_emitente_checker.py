from checkers.base_quali_checker import BaseQualiChecker

class CplEmitenteChecker(BaseQualiChecker):
    check_name = "cpl_emitente"
    table_name = "tipo_licitacao"

    def check(self, record):
        if "nfe" in record.keys() and "cpl_emitente" in record['nfe'].keys() and record['nfe']["cpl_emitente"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["cpl_emitente"],100):
                return False, f"CPL emitente ({record['nfe']['cpl_emitente']}) fora do tamanho permitido."
        return True,None