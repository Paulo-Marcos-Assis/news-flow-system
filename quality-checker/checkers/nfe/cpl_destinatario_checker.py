from checkers.base_quali_checker import BaseQualiChecker

class CplDestinatarioChecker(BaseQualiChecker):
    check_name = "cpl_destinatario"
    table_name = "tipo_licitacao"
    
    def check(self, record):
        if "nfe" in record.keys() and "cpl_destinatario" in record['nfe'].keys() and record['nfe']["cpl_destinatario"] not in ("indefinido","null",None,""): 
            if not self.is_varchar(record['nfe']["cpl_destinatario"], 100):
                return False, f"CPL destinatário ({record['nfe']['cpl_destinatario']}) fora do tamanho permitido."
        return True,None